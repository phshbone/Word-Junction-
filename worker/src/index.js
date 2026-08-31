import { normalizeWord, rankCandidates, chooseRelationLabel } from './rank.js';

const JSON_HEADERS = {
  'content-type':'application/json; charset=utf-8',
  'cache-control':'public, max-age=300',
  'access-control-allow-origin':'*',
  'access-control-allow-methods':'GET,OPTIONS',
};
const LEXICAL_BUCKETS = 8192;

function json(data, status=200, extra={}) {
  return new Response(JSON.stringify(data), {status, headers:{...JSON_HEADERS,...extra}});
}
function posName(pos='') {
  return ({n:'noun',v:'verb',a:'adjective',s:'adjective',r:'adverb'})[pos] || pos || 'word';
}
function termUri(word){ return `/c/en/${normalizeWord(word).replace(/\s+/g,'_')}`; }

function fnv1a(text='') {
  let h=2166136261;
  for (const ch of text) {
    h ^= ch.codePointAt(0);
    h = Math.imul(h, 16777619) >>> 0;
  }
  return h >>> 0;
}
function bucketFor(word) {
  return `b${String(fnv1a(normalizeWord(word)) % LEXICAL_BUCKETS).padStart(4,'0')}`;
}

async function shardSenses(db, word) {
  const norm=normalizeWord(word);
  const row=await db.prepare('SELECT payload_json FROM lexical_shards WHERE bucket=?')
    .bind(bucketFor(norm)).first();
  if (!row?.payload_json) return [];
  try {
    const payload=JSON.parse(row.payload_json);
    return (payload[norm]||[]).map(s=>({
      sense_id:s.id,
      synset_id:s.ss,
      lemma:s.l,
      pos:s.p,
      definition:s.d||'',
      examples:s.e||[],
      synonyms:s.syn||[],
      antonyms:s.ant||[]
    }));
  } catch {
    return [];
  }
}

async function legacySenses(db, word) {
  try {
    const q = await db.prepare(`SELECT sense_id,synset_id,lemma,pos,definition,examples_json
      FROM senses WHERE lemma_norm=? ORDER BY id LIMIT 12`).bind(normalizeWord(word)).all();
    return (q.results||[]).map(s=>({...s,examples:JSON.parse(s.examples_json||'[]'),synonyms:[],antonyms:[]}));
  } catch {
    return [];
  }
}

async function getSenses(db, word) {
  const sharded=await shardSenses(db,word);
  return sharded.length?sharded:legacySenses(db,word);
}

function synonymCandidates(sense) {
  return (sense.synonyms||[]).map(([word,pos]) => ({
    word,pos,sourcePos:sense.pos,sameSynset:true,directSynonym:true,samePos:pos===sense.pos,sameSense:true
  }));
}
function antonymCandidates(sense) {
  return (sense.antonyms||[]).map(([word,pos]) => ({
    word,pos,sourcePos:sense.pos,directAntonym:true,samePos:pos===sense.pos,sameSense:true
  }));
}

function lexicalCandidates(senses, mode) {
  const map=new Map();
  for (const sense of senses) {
    const items=mode==='opposite' ? antonymCandidates(sense) : synonymCandidates(sense);
    for (const c of items) {
      const key=normalizeWord(c.word);
      if (!key) continue;
      const old=map.get(key);
      map.set(key, old ? {
        ...old,
        directSynonym:Boolean(old.directSynonym||c.directSynonym),
        directAntonym:Boolean(old.directAntonym||c.directAntonym),
        sameSynset:Boolean(old.sameSynset||c.sameSynset),
        samePos:Boolean(old.samePos||c.samePos),
        sameSense:Boolean(old.sameSense||c.sameSense),
      } : c);
    }
  }
  return [...map.values()];
}

async function conceptRelated(env, word) {
  const norm = normalizeWord(word);
  const cached = await env.DB.prepare('SELECT payload_json,fetched_at FROM concept_cache WHERE term_norm=?').bind(norm).first();
  const maxAge = 60*60*24*30;
  if (cached && (Date.now()/1000 - cached.fetched_at) < maxAge) {
    try { return JSON.parse(cached.payload_json); } catch {}
  }
  const base = env.CONCEPTNET_BASE || 'https://api.conceptnet.io';
  const url = `${base}/related${termUri(norm)}?filter=/c/en&limit=30`;
  const r = await fetch(url, {headers:{accept:'application/json'}});
  if (!r.ok) return [];
  const body = await r.json();
  const items = (body.related||[]).map(x => ({
    word:(x['@id']||'').replace('/c/en/','').replaceAll('_',' '),
    conceptWeight:Number(x.weight)||0
  })).filter(x=>x.word && normalizeWord(x.word)!==norm);
  await env.DB.prepare(`INSERT INTO concept_cache(term_norm,payload_json,fetched_at) VALUES(?,?,?)
    ON CONFLICT(term_norm) DO UPDATE SET payload_json=excluded.payload_json,fetched_at=excluded.fetched_at`)
    .bind(norm, JSON.stringify(items), Math.floor(Date.now()/1000)).run();
  return items;
}

async function definitionFor(db, word, preferredPos='') {
  const senses = await getSenses(db, word);
  if (!senses.length) return null;
  const s = senses.find(x=>x.pos===preferredPos) || senses[0];
  return {word:s.lemma,pos:posName(s.pos),definition:s.definition,examples:s.examples||[],senseId:s.sense_id};
}

async function pairNote(db, anchor, target, relationType) {
  return db.prepare(`SELECT connection,distinction,examples_json,confidence FROM pair_notes
    WHERE anchor_norm=? AND target_norm=? AND relation_type=?`)
    .bind(normalizeWord(anchor),normalizeWord(target),relationType).first();
}

function genericExplanation(anchor, target, mode, candidate) {
  if (mode==='opposite') return {
    connection:`${anchor} and ${target} point in contrasting directions.`,
    distinction:`They are useful opposites in this sense, but context still determines whether either word fits naturally.`
  };
  if (candidate.sameSynset) return {
    connection:`${anchor} and ${target} share this meaning closely.`,
    distinction:`Even close synonyms can differ in tone, frequency, emphasis, or the situations where a speaker naturally chooses them.`
  };
  return {
    connection:`${anchor} and ${target} are semantically related in this sense.`,
    distinction:`They are related, not automatically interchangeable; their exact fit depends on meaning and context.`
  };
}

async function lookup(env, word, mode='similar') {
  const norm = normalizeWord(word);
  if (!norm || norm.length>80) return {error:'Enter a word or short phrase.'};
  const senses = await getSenses(env.DB, norm);
  if (!senses.length) return {error:`“${word}” is not in the loaded Open English WordNet dataset.`};

  const relationKey=mode==='opposite' ? 'antonyms' : 'synonyms';
  const anchorSense=senses.find(s=>Array.isArray(s[relationKey]) && s[relationKey].length) || senses[0];
  let candidates=lexicalCandidates(senses,mode);

  if (mode==='similar') {
    const cn = await conceptRelated(env, norm).catch(()=>[]);
    const map = new Map(candidates.map(c=>[normalizeWord(c.word),c]));
    for (const c of cn) {
      const key=normalizeWord(c.word); const old=map.get(key)||{};
      map.set(key,{...c,...old,word:old.word||c.word,conceptWeight:Math.max(old.conceptWeight||0,c.conceptWeight||0)});
    }
    candidates=[...map.values()];
  }

  const ranked=rankCandidates(candidates,{anchor:norm}).slice(0,12);
  const decorated=[];
  for (const c of ranked) {
    const d=await definitionFor(env.DB,c.word,c.sourcePos||anchorSense.pos);
    if (!d) continue;
    const note=await pairNote(env.DB,norm,c.word,mode);
    const generic=genericExplanation(anchorSense.lemma,d.word,mode,c);
    decorated.push({
      word:d.word,pos:d.pos,definition:d.definition,
      label:chooseRelationLabel(mode,c),score:Math.round(c.score*10)/10,
      connection:note?.connection||generic.connection,
      distinction:note?.distinction||generic.distinction,
      examples:note?JSON.parse(note.examples_json||'[]'):d.examples.slice(0,2),
      curated:Boolean(note)
    });
  }

  return {
    query:norm,
    mode,
    anchor:{word:anchorSense.lemma,pos:posName(anchorSense.pos),definition:anchorSense.definition,examples:(anchorSense.examples||[]).slice(0,2),senseId:anchorSense.sense_id},
    alternatives:decorated,
    senses:senses.slice(0,8).map(s=>({senseId:s.sense_id,pos:posName(s.pos),definition:s.definition})),
    senseCount:senses.length,
    source:{dictionary:'Open English WordNet 2025',relatedness:'ConceptNet enrichment + Word Junction ranking'}
  };
}

export default {
  async fetch(request, env) {
    if (request.method==='OPTIONS') return new Response(null,{status:204,headers:JSON_HEADERS});
    const url=new URL(request.url);
    if (url.pathname==='/health') {
      let entries=0; let shards=0;
      try {
        const r=await env.DB.prepare('SELECT COUNT(*) AS shards, COALESCE(SUM(entry_count),0) AS entries FROM lexical_shards').first();
        shards=r?.shards||0; entries=r?.entries||0;
      } catch {}
      return json({ok:true,service:'word-junction-lexical',entries,shards});
    }
    if (url.pathname==='/lookup') {
      const result=await lookup(env,url.searchParams.get('word')||'',url.searchParams.get('mode')==='opposite'?'opposite':'similar');
      return result.error?json(result,404):json(result);
    }
    return json({name:'Word Junction Lexical Service',routes:['/health','/lookup?word=clear&mode=similar']});
  }
};
