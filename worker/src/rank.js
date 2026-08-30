const COMMON_POS = new Set(['n','v','a','s','r','noun','verb','adjective','adverb']);

export function normalizeWord(value='') {
  return value.trim().toLowerCase().replace(/\s+/g, ' ');
}

export function rankCandidate(candidate, context={}) {
  let score = 0;
  if (!candidate || !candidate.word) return -Infinity;
  const word = normalizeWord(candidate.word);
  if (!word || word === normalizeWord(context.anchor)) return -Infinity;
  if (candidate.directSynonym) score += 80;
  if (candidate.directAntonym) score += 95;
  if (candidate.sameSynset) score += 70;
  if (candidate.conceptWeight) score += Math.max(-20, Math.min(35, candidate.conceptWeight * 35));
  if (candidate.samePos) score += 16;
  if (candidate.sameSense) score += 22;
  if (candidate.definition) score += 8;
  if (candidate.frequency != null) score += Math.max(0, Math.min(22, candidate.frequency));
  if (candidate.multiword) score -= 5;
  if (candidate.obscure) score -= 28;
  if (candidate.archaic) score -= 45;
  if (candidate.technical && !context.allowTechnical) score -= 18;
  if (candidate.properNoun) score -= 40;
  if (candidate.pos && !COMMON_POS.has(candidate.pos)) score -= 4;
  return score;
}

export function rankCandidates(candidates, context={}) {
  return candidates.map(c => ({...c, score: rankCandidate(c, context)})).filter(c => Number.isFinite(c.score)).sort((a,b) => b.score - a.score || a.word.localeCompare(b.word));
}

export function chooseRelationLabel(mode, candidate) {
  if (mode === 'opposite') return candidate.directAntonym ? 'Direct opposite' : 'Contrasting meaning';
  if (candidate.sameSynset) return 'Very close in meaning';
  if (candidate.directSynonym) return 'Close synonym';
  return 'Related, not interchangeable';
}
