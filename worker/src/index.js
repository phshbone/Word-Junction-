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

function unpackRelation(entry) {
  if (!Array.isArray(entry)) return {word:'',pos:'',targetSenseId:null,targetSynsetId:null};
  return {
    word:entry[0]||'',
    pos:entry[1]||'',
    targetSenseId:entry[2]||null,
    targetSynsetId:entry[3]||null,
  };
}

function synonymCandidates(sense) {
  return (sense.synonyms||[]).map(entry => {
    const rel=unpackRelation(entry);
    return {
      ...rel,
      sourceSenseId:sense.sense_id,
      sourceSynsetId:sense.synset_id,
      sourcePos:sense.pos,
      directSynonym:true,
      sameSynset:true,
      samePos:rel.pos===sense.pos,
      sameSense:true,
      crossPos:rel.pos!==sense.pos,
    };
  });
}
function antonymCandidates(sense) {
  return (sense.antonyms||[]).map(entry => {
    const rel=unpackRelation(entry);
    return {
      ...rel,
      sourceSenseId:sense.sense_id,
      sourceSynsetId:sense.synset_id,
      sourcePos:sense.pos,
      directAntonym:true,
      samePos:rel.pos===sense.pos,
      sameSense:true,
      crossPos:rel.pos!==sense.pos,
    };
  });
}

function candidatesForSense(sense, mode) {
  const items=mode==='opposite' ? antonymCandidates(sense) : synonymCandidates(sense);
  const samePos=items.filter(c=>c.samePos);
  return samePos.length?samePos:[];
}

function chooseAnchorSense(senses, mode) {
  return senses.find(s=>candidatesForSense(s,mode).length) || senses[0];
}

async function exactTargetSense(db, candidate) {
  const senses=await getSenses(db,candidate.word);
  if (!senses.length) return null;

  if (candidate.targetSenseId) {
    const bySense=senses.find(s=>s.sense_id===candidate.targetSenseId);
    if (bySense) return bySense;
  }
  if (candidate.targetSynsetId) {
    const bySynset=senses.find(s=>s.synset_id===candidate.targetSynsetId);
    if (bySynset) return bySynset;
  }
  if (candidate.sameSynset && candidate.sourceSynsetId) {
    const same=senses.find(s=>s.synset_id===candidate.sourceSynsetId);
    if (same) return same;
  }
  return senses.find(s=>s.pos===candidate.sourcePos) || null;
}

async function pairNote(db, anchor, target, relationType) {
  return db.prepare(`SELECT connection,distinction,examples_json,confidence FROM pair_notes
    WHERE anchor_norm=? AND target_norm=? AND relation_type=?`)
    .bind(normalizeWord(anchor),normalizeWord(target),relationType).first();
}

function cleanGloss(text='') {
  return String(text).trim().replace(/[.;:]$/,'');
}

function plainExplanation(anchorSense, targetSense, mode, candidate, anchorSenseCount=1) {
  const anchor=anchorSense.lemma;
  const target=targetSense.lemma;
  const anchorGloss=cleanGloss(anchorSense.definition);
  const targetGloss=cleanGloss(targetSense.definition);
  const pos=posName(anchorSense.pos);
  const multiSense=anchorSenseCount>1;

  if (mode==='opposite') {
    return {
      connection:`In this sense, ${anchor} and ${target} point in opposite directions.`,
      distinction:multiSense
        ? `This pairing uses one specific ${pos} sense of ${anchor}; it does not apply to every meaning of the word.`
        : `The opposition applies to the meanings shown here, not automatically to every possible use of either word.`
    };
  }

  if (candidate.sameSynset) {
    return {
      connection:anchorGloss
        ? `In this sense, both ${anchor} and ${target} can mean “${anchorGloss}.”`
        : `In this sense, ${anchor} and ${target} share the same dictionary meaning.`,
      distinction:multiSense
        ? `This is one specific ${pos} sense of ${anchor}. The words overlap here, but that does not make them interchangeable in every use.`
        : `The words overlap in this exact sense, but that does not make them interchangeable in every use.`
    };
  }

  return {
    connection:`In this sense, ${anchor} and ${target} are connected in meaning.`,
    distinction:multiSense
      ? `This pairing uses one specific ${pos} sense of ${anchor}; the relationship may not hold for its other meanings.`
      : `They are related here, but not automatically interchangeable.`
  };
}

async function lookup(env, word, mode='similar') {
  const norm = normalizeWord(word);
  if (!norm || norm.length>80) return {error:'Enter a word or short phrase.'};
  const senses = await getSenses(env.DB, norm);
  if (!senses.length) return {error:`“${word}” is not in the loaded Open English WordNet dataset.`};

  const anchorSense=chooseAnchorSense(senses,mode);
  const anchorSenseIndex=Math.max(0,senses.findIndex(s=>s.sense_id===anchorSense.sense_id));
  let candidates=candidatesForSense(anchorSense,mode);
  candidates=rankCandidates(candidates,{anchor:norm}).slice(0,12);

  const decorated=[];
  for (const c of candidates) {
    const targetSenses=await getSenses(env.DB,c.word);
    const targetSense=await exactTargetSense(env.DB,c);
    if (!targetSense) continue;
    if (targetSense.pos!==anchorSense.pos) continue;

    const note=await pairNote(env.DB,norm,c.word,mode);
    const generic=plainExplanation(anchorSense,targetSense,mode,c,senses.length);
    const sourceExamples=[...(anchorSense.examples||[]),...(targetSense.examples||[])].filter(Boolean);
    const examples=note?JSON.parse(note.examples_json||'[]'):(targetSense.examples||[]).slice(0,2);
    decorated.push({
      word:targetSense.lemma,
      pos:posName(targetSense.pos),
      definition:targetSense.definition,
      senseId:targetSense.sense_id,
      synsetId:targetSense.synset_id,
      senseNumber:Math.max(1,targetSenses.findIndex(s=>s.sense_id===targetSense.sense_id)+1),
      senseCount:targetSenses.length,
      label:chooseRelationLabel(mode,c),
      score:Math.round(c.score*10)/10,
      connection:note?.connection||generic.connection,
      distinction:note?.distinction||generic.distinction,
      examples,
      usageExample:(examples[0]||sourceExamples[0]||''),
      curated:Boolean(note),
      evidence:c.sameSynset?'same-synset':(c.directAntonym?'direct-antonym':'lexical')
    });
  }

  return {
    query:norm,
    mode,
    anchor:{
      word:anchorSense.lemma,
      pos:posName(anchorSense.pos),
      definition:anchorSense.definition,
      examples:(anchorSense.examples||[]).slice(0,2),
      senseId:anchorSense.sense_id,
      synsetId:anchorSense.synset_id,
      senseNumber:anchorSenseIndex+1,
      senseCount:senses.length,
      senseNotice:senses.length>1?`This is one of ${senses.length} senses listed for ${anchorSense.lemma}.`:null,
    },
    alternatives:decorated,
    senses:senses.slice(0,8).map((s,i)=>({senseId:s.sense_id,pos:posName(s.pos),definition:s.definition,senseNumber:i+1})),
    senseCount:senses.length,
    quality:{
      samePartOfSpeechOnly:true,
      exactSenseDefinitions:true,
      conceptNetUsed:false,
      unsupportedNuanceSuppressed:true,
      oneSenseOneConnection:true,
    },
    source:{dictionary:'Open English WordNet 2025',relatedness:'Exact WordNet lexical relationships + Word Junction ranking'}
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
