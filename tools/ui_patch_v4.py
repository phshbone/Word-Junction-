from pathlib import Path
import re

p=Path('index.html')
s=p.read_text()
old="function displayPair(){const r=current(),base=state.data?.anchor,ctx=r?.anchorSense,a=ctx?{...base,...ctx}:base;return state.reversed?{top:r,bottom:a}:{top:a,bottom:r}}"
new="function displayPair(){const r=current(),base=state.data?.anchor,ctx=r?.anchorSense,a=ctx?{...base,...ctx,word:base?.word||state.data?.query}:base;return state.reversed?{top:r,bottom:a}:{top:a,bottom:r}}"
if old not in s:
    raise SystemExit('displayPair source not found')
s=s.replace(old,new,1)
p.write_text(s)

sw=Path('sw.js')
w=sw.read_text()
w=re.sub(r'word-junctions-v\\d+','word-junctions-v13',w,count=1)
sw.write_text(w)

s=p.read_text()
assert 'word:base?.word||state.data?.query' in s
assert 'two-card-junction-v5' in s
print('Fixed-card refresh hardening PASS')
