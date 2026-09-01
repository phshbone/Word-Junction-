# Word Junction content quality rules

These rules govern the Similar/Opposite learning experience. The goal is to teach a defensible relationship between the two words on screen, not to maximize the number of returned words.

## 1. One sense, one connection, one difference, one usage example

The core learning unit is deliberately narrow:

1. one exact sense of the anchor word
2. one defensible connected word
3. one clear statement of how they overlap
4. one clear statement of where the relationship stops
5. one concrete usage example when source material provides one

Do not turn a card into a dictionary dump. Depth beats breadth.

## 2. The displayed definition must be the relationship sense

A word can have many meanings. Word Junction must show the exact Open English WordNet sense that produced the synonym or antonym relationship.

Bad example: showing **air** as “an intangible quality” while pairing it with **aerate** because of the fresh-air sense.

Rule: relationship sense first; never choose a convenient first definition after the pair has already been selected.

## 3. Say “in this sense” when only one meaning overlaps

Never imply that two entire words are synonymous merely because one sense overlaps.

Preferred framing:
- “In this sense, both words can mean…”
- “This pairing uses one specific noun sense of motion.”
- “The words overlap here, but that does not make them interchangeable in every use.”

This is especially important for familiar words with many meanings. A surprising legitimate sense is a feature, not a problem, as long as the active sense is explicit.

## 4. Similar/Opposite compares the same part of speech

For the main learning modes, noun compares with noun, verb with verb, adjective with adjective, and adverb with adverb.

Cross-part-of-speech associations belong in a future Related/Word Family experience, not in Similar/Opposite.

## 5. Exact lexical evidence beats broad relatedness

Priority for Similar:
1. same Open English WordNet synset
2. direct lexical synonym evidence
3. curated pair note

Priority for Opposite:
1. direct Open English WordNet antonym relation
2. curated pair note

ConceptNet is not used to manufacture synonyms or antonyms. It may later support a separate Related Ideas mode.

## 6. Fewer correct pairs are better than more questionable pairs

If a word has no defensible same-POS synonym or antonym for the displayed sense, return no alternative rather than a merely associated word.

## 7. Labels describe the relationship narrowly

Preferred labels:
- Same sense
- Synonyms in this sense
- Opposite in this sense
- Related in this sense

Avoid labels such as “very close in meaning” when the system cannot explain what that closeness consists of.

## 8. Generic text must not invent nuance

Word Junction may safely explain the shared dictionary sense or direct antonym relation. It must not claim differences in tone, frequency, formality, emphasis, register, or normal usage unless a curated pair note specifically supports that claim.

For an uncurated same-synset pair, explain the shared sense and the boundary: the relationship applies here, not automatically to every use of either word.

## 9. Curated pair notes are the teaching layer

A curated pair note may add:
- how the words overlap
- where they differ
- register/formality
- typical contexts
- interchangeability limits
- concrete examples

Curated notes override generic relationship text for that exact pair and relation type.

## 10. Definitions and examples stay source-grounded

Definitions and source examples come from Open English WordNet unless explicitly marked as Word Junction-authored material. Do not silently rewrite a definition into a new factual claim.

## 11. Sense ambiguity should be visible, not hidden

The API keeps available senses in the response and reports which sense is active. When a word has multiple meanings, the learning text should make clear that the displayed relationship belongs to one particular sense.

A future UI may allow the user to switch senses. Until then, the default sense should be the earliest WordNet sense that has a defensible relationship in the selected mode.

## 12. Prefer memorable mental bridges

Among equally defensible pairs, prefer the pair that creates a useful mental bridge for a learner rather than the pair that merely increases lexical coverage.

The goal is not “show more synonyms.” The goal is “make one connection stick.”

## 13. Quality regression fixtures

The content test set should include polysemous words and tempting bad matches, including at minimum:
- air
- simple
- motion
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
- the explanation says “in this sense” when appropriate
- no generic text invents unsupported nuance
- the pair teaches one usable connection rather than dumping multiple meanings
