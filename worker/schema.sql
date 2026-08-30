PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS senses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lemma TEXT NOT NULL,
  lemma_norm TEXT NOT NULL,
  pos TEXT NOT NULL,
  sense_id TEXT NOT NULL UNIQUE,
  synset_id TEXT NOT NULL,
  definition TEXT NOT NULL,
  examples_json TEXT NOT NULL DEFAULT '[]',
  source TEXT NOT NULL DEFAULT 'oewn-2025'
);
CREATE INDEX IF NOT EXISTS idx_senses_lemma ON senses(lemma_norm);
CREATE INDEX IF NOT EXISTS idx_senses_synset ON senses(synset_id);

CREATE TABLE IF NOT EXISTS sense_members (
  synset_id TEXT NOT NULL,
  lemma TEXT NOT NULL,
  lemma_norm TEXT NOT NULL,
  pos TEXT NOT NULL,
  PRIMARY KEY (synset_id, lemma_norm, pos)
);
CREATE INDEX IF NOT EXISTS idx_members_lemma ON sense_members(lemma_norm);

CREATE TABLE IF NOT EXISTS relations (
  source_sense_id TEXT NOT NULL,
  target_lemma TEXT NOT NULL,
  target_norm TEXT NOT NULL,
  target_pos TEXT,
  relation_type TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  source TEXT NOT NULL,
  PRIMARY KEY (source_sense_id, target_norm, relation_type, source)
);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relations(source_sense_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relations(target_norm);

CREATE TABLE IF NOT EXISTS pair_notes (
  anchor_norm TEXT NOT NULL,
  target_norm TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  connection TEXT NOT NULL,
  distinction TEXT NOT NULL,
  examples_json TEXT NOT NULL DEFAULT '[]',
  confidence REAL NOT NULL DEFAULT 1.0,
  source TEXT NOT NULL DEFAULT 'word-junction',
  PRIMARY KEY(anchor_norm, target_norm, relation_type)
);

CREATE TABLE IF NOT EXISTS concept_cache (
  term_norm TEXT PRIMARY KEY,
  payload_json TEXT NOT NULL,
  fetched_at INTEGER NOT NULL
);
