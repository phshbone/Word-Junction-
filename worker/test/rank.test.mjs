import assert from 'node:assert/strict';
import {rankCandidates,normalizeWord,chooseRelationLabel} from '../src/rank.js';

assert.equal(normalizeWord('  Clear   Thinking '),'clear thinking');

const ranked=rankCandidates([
  {word:'lucid',directSynonym:true,sameSynset:true,samePos:true,sameSense:true,definition:'clear'},
  {word:'pellucid',directSynonym:true,sameSynset:true,samePos:true,sameSense:true,definition:'clear',obscure:true},
  {word:'transparent',conceptWeight:.7,samePos:true,definition:'allows light through'},
  {word:'clarify',directSynonym:true,sameSense:true,crossPos:true,pos:'v'}
],{anchor:'clear'});

assert.equal(ranked[0].word,'lucid');
assert.ok(ranked.findIndex(x=>x.word==='clarify') > ranked.findIndex(x=>x.word==='transparent'));
assert.equal(chooseRelationLabel('similar',ranked[0]),'Same sense');
assert.equal(chooseRelationLabel('similar',{directSynonym:true}),'Synonyms in this sense');
assert.equal(chooseRelationLabel('opposite',{directAntonym:true}),'Opposite in this sense');
console.log('rank tests passed');
