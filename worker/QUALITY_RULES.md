# Word Junction content quality rules

These rules govern the Similar/Opposite learning experience. The goal is to teach a defensible relationship between the two words on screen, not to maximize the number of returned words.

## 1. The displayed definition must be the relationship sense

A word can have many meanings. Word Junction must show the exact Open English WordNet sense that produced the synonym or antonym relationship.

Bad example: showing **air** as “an intangible quality” while pairing it with **aerate** because of the fresh-air sense.

Rule: relationship sense first; never choose a convenient first definition after the pair has already been selected.

## 2. Similar/Opposite compares the same part of speech

For the main learning modes, noun compares with noun, verb with verb, adjective with adjective, and adverb with adverb.

Cross-part-of-speech associations belong in a future Related/Word Family experience, not in Similar/Opposite.

## 3. Exact lexical evidence beats broad relatedness

Priority for Similar:
1. same Open English WordNet synset
2. direct lexical synonym evidence
3. curated pair note

Priority for Opposite:
1. direct Open English WordNet antonym relation
2. curated pair note

ConceptNet is not used to manufacture synonyms or antonyms. It may later support a separate Related Ideas mode.

## 4. Fewer correct pairs are better than more questionable pairs

If a word has no defensible same-POS synonym or antonym for the displayed sense, return no alternative rather than a merely associated word.

## 5. Labels describe evidence, not vague closeness

Preferred labels:
- Same dictionary sense
- Direct synonym
- Direct opposite in this sense
- Related idea (reserved for a future mode)

Avoid labels such as “very close in meaning” when the system cannot explain what that closeness consists of.

## 6. Generic text must not invent nuance

Word Junction may safely explain the shared dictionary sense or direct antonym relation. It must not claim differences in tone, frequency, formality, emphasis, register, or normal usage unless a curated pair note specifically supports that claim.

For an uncurated same-synset pair, explain the shared sense and state that no finer distinction is being asserted yet.

## 7. Curated pair notes are the teaching layer

A curated pair note may add:
- how the words overlap
- where they differ
- register/formality
- typical contexts
- interchangeability limits
- concrete examples

Curated notes override generic relationship text for that exact pair and relation type.

## 8. Definitions and examples stay source-grounded

Definitions and source examples come from Open English WordNet unless explicitly marked as Word Junction-authored material. Do not silently rewrite a definition into a new factual claim.

## 9. Sense ambiguity should be visible, not hidden

The API keeps available senses in the response. A future UI may allow the user to switch senses. Until then, the default sense should be the earliest WordNet sense that has a defensible relationship in the selected mode.

## 10. Quality regression fixtures

The content test set should include polysemous words and tempting bad matches, including at minimum:
- air
- simple
- clear
- light
- bank
- fine
- mean
- hot
- run
- sound

For each fixture, verify:
- anchor definition matches the relationship sense
- target definition matches the target relationship sense
- part of speech matches
- the label accurately describes the evidence
- no generic text invents unsupported nuance
