import assert from 'node:assert/strict';
import {rankCandidates,normalizeWord,chooseRelationLabel} from '../src/rank.js';
assert.equal(normalizeWord('  Clear   Thinking '),'clear thinking');
const ranked=rankCandidates([
  {word:'lucid',directSynonym:true,sameSynset:true,samePos:true,definition:'clear'},
  {word:'pellucid',directSynonym:true,sameSynset:true,samePos:true,definition:'clear',obscure:true},
  {word:'transparent',conceptWeight:.7,samePos:true,definition:'allows light through'}
],{anchor:'clear'});
assert.equal(ranked[0].word,'lucid');
assert.equal(chooseRelationLabel('similar',ranked[0]),'Very close in meaning');
assert.equal(chooseRelationLabel('opposite',{directAntonym:true}),'Direct opposite');
console.log('rank tests passed');
