from pathlib import Path
import re

p = Path('worker/src/index.js')
s = p.read_text()

if "const MAX_EVERYDAY_SENSES = 3;" not in s:
    s = s.replace("const MAX_ALTERNATIVES = 24;", "const MAX_ALTERNATIVES = 12;\nconst MAX_EVERYDAY_SENSES = 3;")

new = """function pooledCandidates(senses, mode) {
  const primary=chooseAnchorSense(senses,mode);
  const anchorPos=primary.pos;
  const allSamePosSenses=senses.filter(s=>s.pos===anchorPos);
  const primaryPosIndex=Math.max(0,allSamePosSenses.findIndex(s=>s.sense_id===primary.sense_id));

  // Word Junctions is a teaching tool, not a thesaurus dump. Stay within the
  // first few same-part-of-speech senses by default. If WordNet's first usable
  // sense is already farther down the list, keep that exact sense but do not
  // fan out across several other rare/specialized senses automatically.
  const everydaySenses=primaryPosIndex<MAX_EVERYDAY_SENSES
    ? allSamePosSenses.slice(0,MAX_EVERYDAY_SENSES)
    : [primary];
  if (!everydaySenses.some(s=>s.sense_id===primary.sense_id)) everydaySenses.unshift(primary);

  const candidates=[];
  everydaySenses.forEach((sense)=>{
    const posIndex=Math.max(0,allSamePosSenses.findIndex(s=>s.sense_id===sense.sense_id));
    for (const candidate of candidatesForSense(sense,mode)) {
      candidates.push({
        ...candidate,
        sourceSenseOrder:posIndex,
        primarySense:sense.sense_id===primary.sense_id,
      });
    }
  });

  const ranked=rankCandidates(candidates,{anchor:primary.lemma})
    .map(c=>({...c,
      // Exact current-sense relationships dominate. Nearby everyday senses can
      // supplement a thin pool, but later senses pay a steep pedagogical cost.
      score:c.score + (c.primarySense?80:Math.max(-90,8-(c.sourceSenseOrder*28)))
    }))
    .sort((a,b)=>b.score-a.score || a.word.localeCompare(b.word));

  const best=ranked[0]?.score ?? -Infinity;
  const deduped=[];
  const seen=new Set();
  for (const candidate of ranked) {
    const key=normalizeWord(candidate.word);
    if (!key || seen.has(key)) continue;
    // Do not keep technically valid but pedagogically distant leftovers merely
    // to make the list longer. They can reappear if that sense becomes primary.
    if (!candidate.primarySense && candidate.score < best-70) continue;
    seen.add(key);
    deduped.push(candidate);
    if (deduped.length>=MAX_ALTERNATIVES) break;
  }
  return {primary, samePosSenses:everydaySenses, candidates:deduped};
}

"""

pattern = r"function pooledCandidates\(senses, mode\) \{.*?\n\}\n\n(?=async function exactTargetSense)"
s, count = re.subn(pattern, new, s, count=1, flags=re.S)
if count != 1:
    raise SystemExit(f'pooledCandidates patch count was {count}')

if "pedagogicalSenseGate:true" not in s:
    s = s.replace("multiSensePool:true,", "multiSensePool:true,\n      pedagogicalSenseGate:true,\n      maxAutomaticSenseBreadth:MAX_EVERYDAY_SENSES,")

s = s.replace(
    "relatedness:'Exact WordNet lexical relationships across ranked same-part-of-speech senses + Word Junction ranking'",
    "relatedness:'Exact WordNet lexical relationships across ranked everyday same-part-of-speech senses + Word Junction teaching-quality gate'"
)

p.write_text(s)
print('Tightened lexical sense gate')
