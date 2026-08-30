#!/usr/bin/env python3
"""Build D1-compatible SQL from Open English WordNet via the `wn` Python package.

Usage:
  python -m pip install wn
  python tools/build_oewn_sql.py --lexicon oewn:2025 --out oewn-seed.sql

The first run downloads OEWN through wn if it is not already installed.
"""
import argparse, json, sys
from pathlib import Path

def q(s):
    if s is None:
        return 'NULL'
    return "'" + str(s).replace("'", "''") + "'"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--lexicon',default='oewn:2025')
    ap.add_argument('--out',default='oewn-seed.sql')
    args=ap.parse_args()
    try:
        import wn
    except ImportError:
        raise SystemExit('Install dependency first: python -m pip install wn')
    try:
        net=wn.Wordnet(args.lexicon)
    except Exception:
        print(f'Downloading {args.lexicon}...',file=sys.stderr)
        wn.download(args.lexicon)
        net=wn.Wordnet(args.lexicon)
    out=Path(args.out)
    with out.open('w',encoding='utf-8') as f:
        f.write('BEGIN TRANSACTION;\n')
        seen_members=set(); seen_rel=set()
        for sense in net.senses():
            word=sense.word(); lemma=word.lemma(); pos=word.pos; syn=sense.synset(); definition=syn.definition() or ''
            examples=sense.examples() or syn.examples() or []
            vals=[lemma,lemma.lower(),pos,sense.id,syn.id,definition,json.dumps(examples,ensure_ascii=False),'oewn-2025']
            f.write('INSERT OR IGNORE INTO senses(lemma,lemma_norm,pos,sense_id,synset_id,definition,examples_json,source) VALUES(%s,%s,%s,%s,%s,%s,%s,%s);\n' % tuple(map(q,vals)))
            for member in syn.words():
                m=member.lemma(); key=(syn.id,m.lower(),member.pos)
                if key not in seen_members:
                    seen_members.add(key)
                    f.write('INSERT OR IGNORE INTO sense_members(synset_id,lemma,lemma_norm,pos) VALUES(%s,%s,%s,%s);\n' % tuple(map(q,[syn.id,m,m.lower(),member.pos])))
            for target in sense.get_related('antonym'):
                tw=target.word(); key=(sense.id,tw.lemma().lower(),'antonym')
                if key not in seen_rel:
                    seen_rel.add(key)
                    f.write('INSERT OR IGNORE INTO relations(source_sense_id,target_lemma,target_norm,target_pos,relation_type,weight,source) VALUES(%s,%s,%s,%s,%s,1.0,%s);\n' % tuple(map(q,[sense.id,tw.lemma(),tw.lemma().lower(),tw.pos,'antonym','oewn-2025'])))
        f.write('COMMIT;\n')
    print(out)
if __name__=='__main__':
    main()
