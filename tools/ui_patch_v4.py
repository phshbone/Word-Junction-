from pathlib import Path
import re

p=Path('index.html')
s=p.read_text()

repls=[
("<div class=\"build-marker\" id=\"buildMarker\">two-card-junction-v4</div>","<div class=\"build-marker\" id=\"buildMarker\">two-card-junction-v5</div>"),
("function displayPair(){const a=state.data?.anchor,r=current();return state.reversed?{top:r,bottom:a}:{top:a,bottom:r}}",
 "function displayPair(){const r=current(),base=state.data?.anchor,ctx=r?.anchorSense,a=ctx?{...base,...ctx}:base;return state.reversed?{top:r,bottom:a}:{top:a,bottom:r}}"),
("els.senseNotice.textContent=state.senseNotice||'';els.senseNotice.classList.toggle('show',!!state.senseNotice);els.senseNotice.classList.toggle('opposite',opp);\nif(r){const rel=current();",
 "const rel=current(),notice=state.senseNotice||rel?.senseNote||'';els.senseNotice.textContent=notice;els.senseNotice.classList.toggle('show',!!notice);els.senseNotice.classList.toggle('opposite',opp);\nif(r){"),
("'Open English WordNet 2025 + Word Junctions ranking. Each card shows the exact sense used by this relationship.'",
 "'Open English WordNet 2025 + Word Junctions ranking across same-part-of-speech senses. Each card shows the exact sense used by this relationship.'"),
]
for old,new in repls:
    if old not in s:
        raise SystemExit(f'patch source not found: {old[:90]}')
    s=s.replace(old,new,1)

p.write_text(s)

sw=Path('sw.js')
w=sw.read_text()
w=re.sub(r'word-junctions-v\d+','word-junctions-v12',w,count=1)
sw.write_text(w)

s=p.read_text()
assert 'two-card-junction-v5' in s
assert 'r?.anchorSense' in s
assert "rel?.senseNote" in s
print('Contextual sense frontend patch PASS')
