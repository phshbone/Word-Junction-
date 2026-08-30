#!/usr/bin/env python3
"""Build D1-compatible SQL chunks from Open English WordNet via the `wn` package.

Examples:
  python -m pip install "wn>=1.1,<2"
  python tools/build_oewn_sql.py --lexicon oewn:2025 --out-dir build/oewn
  python tools/build_oewn_sql.py --limit 250 --out-dir build/smoke

The first run downloads OEWN through wn if it is not already installed.
Output intentionally contains no BEGIN/COMMIT wrappers because Cloudflare D1's
bulk-import guidance recommends importing plain SQL statements.
"""
import argparse
import json
import sys
from pathlib import Path


def q(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def norm(value):
    return " ".join(str(value).strip().lower().split())


class ChunkWriter:
    def __init__(self, out_dir: Path, max_statements: int):
        self.out_dir = out_dir
        self.max_statements = max(100, max_statements)
        self.index = 0
        self.count = 0
        self.total = 0
        self.handle = None
        out_dir.mkdir(parents=True, exist_ok=True)

    def _open(self):
        self.index += 1
        path = self.out_dir / f"oewn-{self.index:04d}.sql"
        self.handle = path.open("w", encoding="utf-8")
        self.count = 0

    def write(self, statement: str):
        if self.handle is None or self.count >= self.max_statements:
            if self.handle is not None:
                self.handle.close()
            self._open()
        self.handle.write(statement.rstrip(";\n") + ";\n")
        self.count += 1
        self.total += 1

    def close(self):
        if self.handle is not None:
            self.handle.close()


def load_wordnet(lexicon):
    try:
        import wn
    except ImportError:
        raise SystemExit('Install dependency first: python -m pip install "wn>=1.1,<2"')
    try:
        return wn.Wordnet(lexicon)
    except Exception:
        print(f"Downloading {lexicon}...", file=sys.stderr)
        wn.download(lexicon)
        return wn.Wordnet(lexicon)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexicon", default="oewn:2025")
    ap.add_argument("--out-dir", default="build/oewn")
    ap.add_argument("--chunk-statements", type=int, default=12000)
    ap.add_argument("--limit", type=int, default=0, help="Limit senses for CI smoke tests; 0 means all")
    args = ap.parse_args()

    net = load_wordnet(args.lexicon)
    writer = ChunkWriter(Path(args.out_dir), args.chunk_statements)
    seen_members = set()
    seen_relations = set()
    sense_count = 0
    member_count = 0
    antonym_count = 0

    try:
        for sense in net.senses():
            if args.limit and sense_count >= args.limit:
                break

            word = sense.word()
            synset = sense.synset()
            lemma = word.lemma()
            pos = word.pos
            definition = synset.definition() or ""
            examples = sense.examples() or synset.examples() or []

            values = [
                lemma,
                norm(lemma),
                pos,
                sense.id,
                synset.id,
                definition,
                json.dumps(examples, ensure_ascii=False),
                "oewn-2025",
            ]
            writer.write(
                "INSERT OR IGNORE INTO senses"
                "(lemma,lemma_norm,pos,sense_id,synset_id,definition,examples_json,source) VALUES"
                f"({','.join(map(q, values))})"
            )
            sense_count += 1

            for member in synset.words():
                member_lemma = member.lemma()
                key = (synset.id, norm(member_lemma), member.pos)
                if key in seen_members:
                    continue
                seen_members.add(key)
                writer.write(
                    "INSERT OR IGNORE INTO sense_members"
                    "(synset_id,lemma,lemma_norm,pos) VALUES"
                    f"({','.join(map(q, [synset.id, member_lemma, norm(member_lemma), member.pos]))})"
                )
                member_count += 1

            for target in sense.get_related("antonym"):
                target_word = target.word()
                target_lemma = target_word.lemma()
                key = (sense.id, norm(target_lemma), "antonym")
                if key in seen_relations:
                    continue
                seen_relations.add(key)
                writer.write(
                    "INSERT OR IGNORE INTO relations"
                    "(source_sense_id,target_lemma,target_norm,target_pos,relation_type,weight,source) VALUES"
                    f"({','.join(map(q, [sense.id, target_lemma, norm(target_lemma), target_word.pos, 'antonym']))},1.0,{q('oewn-2025')})"
                )
                antonym_count += 1
    finally:
        writer.close()

    manifest = {
        "lexicon": args.lexicon,
        "senses": sense_count,
        "sense_members": member_count,
        "antonym_relations": antonym_count,
        "statements": writer.total,
        "chunks": writer.index,
    }
    manifest_path = Path(args.out_dir) / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
