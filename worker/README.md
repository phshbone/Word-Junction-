# Word Junction lexical service

This is the independent lexical backend for Word Junction.

## Sources

- **Open English WordNet 2025** is the dictionary/sense/synonym/antonym foundation.
- **ConceptNet** is an open-data semantic enrichment source. It is isolated behind one provider function so a self-hosted ConceptNet mirror can replace the public endpoint without changing the app API.
- **Word Junction ranking** prefers direct lexical relations, same sense, same part of speech, modern/useful terms, and curated pair notes.

## API

- `GET /health`
- `GET /lookup?word=clear&mode=similar`
- `GET /lookup?word=clear&mode=opposite`

## D1 setup

1. Create D1 database `word-junction`.
2. Apply `schema.sql`.
3. Install Python package `wn` and run `tools/build_oewn_sql.py` to generate the OEWN seed SQL.
4. Import the generated SQL into D1.
5. Copy `wrangler.toml.example` to `wrangler.toml`, insert the database id, and deploy.

The public ConceptNet endpoint is not a proprietary dependency: its code is Apache-2.0 and its data is CC BY-SA 4.0. The provider boundary exists so Word Junction can later host its own ConceptNet data/embeddings if desired.
