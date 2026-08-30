#!/usr/bin/env python3
"""Build free-tier-friendly D1 SQL shards from Open English WordNet.

Each normalized lemma hashes to one of a fixed number of buckets. A bucket is
stored as one JSON row in D1, which keeps a complete OEWN import well below the
free plan's daily row-write ceiling while preserving arbitrary-word lookup.

Examples:
  python -m pip install "wn>=1.1,<2"
  python tools/build_oewn_sql.py --out-dir build/oewn
  python tools/build_oewn_sql.py --limit 300 --buckets 64 --out-dir build/smoke
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def q(value):
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def norm(value):
    return " ".join(str(value).strip().lower().split())


def fnv1a(text):
    h = 2166136261
    for ch in text:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def bucket_for(word, bucket_count):
    return f"b{fnv1a(norm(word)) % bucket_count:04d}"


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


def compact_sense(sense):
    word = sense.word()
    synset = sense.synset()
    lemma = word.lemma()
    synonyms = []
    seen = set()
    for member in synset.words():
        m = member.lemma()
        key = (norm(m), member.pos)
        if norm(m) == norm(lemma) or key in seen:
            continue
        seen.add(key)
        synonyms.append([m, member.pos])

    antonyms = []
    seen_ant = set()
    for target in sense.get_related("antonym"):
        tw = target.word()
        key = (norm(tw.lemma()), tw.pos)
        if key in seen_ant:
            continue
        seen_ant.add(key)
        antonyms.append([tw.lemma(), tw.pos])

    return {
        "l": lemma,
        "p": word.pos,
        "id": sense.id,
        "ss": synset.id,
        "d": synset.definition() or "",
        "e": (sense.examples() or synset.examples() or [])[:4],
        "syn": synonyms,
        "ant": antonyms,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lexicon", default="oewn:2025")
    ap.add_argument("--out-dir", default="build/oewn")
    ap.add_argument("--buckets", type=int, default=8192)
    ap.add_argument("--limit", type=int, default=0, help="Limit senses for CI smoke tests; 0 means all")
    args = ap.parse_args()
    if args.buckets < 16:
        raise SystemExit("--buckets must be at least 16")

    net = load_wordnet(args.lexicon)
    shards = defaultdict(dict)
    sense_count = 0
    lemma_count = 0
    synonym_links = 0
    antonym_links = 0

    for sense in net.senses():
        if args.limit and sense_count >= args.limit:
            break
        item = compact_sense(sense)
        key = norm(item["l"])
        bucket = bucket_for(key, args.buckets)
        if key not in shards[bucket]:
            shards[bucket][key] = []
            lemma_count += 1
        shards[bucket][key].append(item)
        synonym_links += len(item["syn"])
        antonym_links += len(item["ant"])
        sense_count += 1

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sql_path = out_dir / "oewn-shards.sql"
    max_payload = 0
    with sql_path.open("w", encoding="utf-8") as f:
        for bucket in sorted(shards):
            payload = json.dumps(shards[bucket], ensure_ascii=False, separators=(",", ":"))
            payload_bytes = len(payload.encode("utf-8"))
            max_payload = max(max_payload, payload_bytes)
            if payload_bytes >= 90000:
                raise SystemExit(
                    f"Bucket {bucket} is {payload_bytes} bytes; increase --buckets so each INSERT stays below D1's 100KB SQL limit"
                )
            statement = (
                "INSERT INTO lexical_shards(bucket,payload_json,entry_count,source) VALUES"
                f"({q(bucket)},{q(payload)},{len(shards[bucket])},{q('oewn-2025')}) "
                "ON CONFLICT(bucket) DO UPDATE SET payload_json=excluded.payload_json,"
                "entry_count=excluded.entry_count,source=excluded.source;\n"
            )
            f.write(statement)

    manifest = {
        "lexicon": args.lexicon,
        "bucket_count": args.buckets,
        "populated_buckets": len(shards),
        "senses": sense_count,
        "lemmas": lemma_count,
        "synonym_links": synonym_links,
        "antonym_links": antonym_links,
        "max_payload_bytes": max_payload,
        "sql_file": str(sql_path),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest))


if __name__ == "__main__":
    main()
