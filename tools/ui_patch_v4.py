from pathlib import Path
import re

p=Path('index.html')
s=p.read_text()

# Typography and card chrome.
s=s.replace('.word{font-family:Georgia,"Times New Roman",serif;font-size:clamp(44px,8.5vw,70px);', '.word{font-family:Georgia,"Times New Roman",serif;font-size:clamp(42px,8vw,66px);', 1)
s=s.replace('.word-row{display:flex;align-items:flex-start;gap:14px;justify-content:space-between}', '.word-row{display:block}.card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:5px}', 1)
s=s.replace('.card-controls{display:flex;gap:8px;flex:0 0 auto}', '.card-controls{display:flex;gap:8px;flex:0 0 auto}', 1)

# Replace the simple junction styling with a larger explanation hub.
old_junction='.junction{height:88px;position:relative;display:flex;align-items:center;justify-content:center}.junction-pipe{position:absolute;top:-1px;bottom:-1px;width:9px;border-radius:8px;background:var(--teal);box-shadow:0 0 0 4px rgba(13,145,136,.08)}.junction.opposite .junction-pipe{background:var(--gold);box-shadow:0 0 0 4px rgba(223,160,18,.09)}.junction-pipe:before,.junction-pipe:after{content:"";position:absolute;top:39px;width:42px;height:9px;border-radius:8px;background:inherit}.junction-pipe:before{right:4px}.junction-pipe:after{left:4px}.relation-badge{position:relative;z-index:2;background:rgba(248,244,235,.98);border:0;border-radius:12px;padding:6px 11px;color:var(--ink);font-weight:900;font-size:12px;letter-spacing:.01em;box-shadow:none;pointer-events:none;user-select:none}.connection-box{margin-top:18px;background:var(--teal-soft);padding:14px 16px;border-radius:16px;color:#23595a;font-weight:800;line-height:1.45}.connection-box.opposite{background:var(--gold-soft);color:#765311}.boundary{margin-top:11px;color:#5d6b6b;line-height:1.5;font-size:14px}'
new_junction='.junction{min-height:154px;position:relative;display:grid;grid-template-columns:minmax(0,1fr) 112px minmax(0,1fr);align-items:center;gap:10px;padding:18px 0}.junction-pipe{position:absolute;top:-1px;bottom:-1px;left:50%;transform:translateX(-50%);width:9px;border-radius:8px;background:var(--teal);box-shadow:0 0 0 4px rgba(13,145,136,.08)}.junction.opposite .junction-pipe{background:var(--gold);box-shadow:0 0 0 4px rgba(223,160,18,.09)}.junction-pipe:before,.junction-pipe:after{content:"";position:absolute;top:50%;width:54px;height:9px;border-radius:8px;background:inherit}.junction-pipe:before{right:4px}.junction-pipe:after{left:4px}.relation-badge{grid-column:2;position:relative;z-index:3;justify-self:center;background:rgba(248,244,235,.98);border:1px solid rgba(13,63,78,.09);border-radius:14px;padding:8px 12px;color:var(--ink);font-weight:900;font-size:12px;letter-spacing:.01em;box-shadow:var(--soft);pointer-events:none;user-select:none;text-align:center}.explain-card{position:relative;z-index:2;min-height:92px;border:1px solid rgba(13,145,136,.22);background:rgba(221,242,238,.72);border-radius:17px;padding:12px 13px;color:#285b5b;box-shadow:var(--soft);line-height:1.42}.explain-card.opposite{border-color:rgba(223,160,18,.28);background:rgba(255,240,191,.72);color:#755313}.explain-card strong{display:block;color:var(--ink);font-size:11px;letter-spacing:.09em;text-transform:uppercase;margin-bottom:5px}.explain-card p{margin:0;font-size:13px}.explain-card.hidden{display:none}.grammar-note{grid-column:1/-1;position:relative;z-index:2;margin:0 auto;max-width:520px;border:1px solid rgba(13,63,78,.13);background:rgba(255,253,250,.86);border-radius:15px;padding:9px 12px;color:#526668;font-size:12px;line-height:1.4}.grammar-note.hidden{display:none}.connection-box,.boundary{display:none}.related-extra{max-height:0;overflow:hidden;opacity:0;transition:max-height .3s ease,opacity .2s ease}.related-extra.open{max-height:380px;opacity:1}.expand-btn{border:1px solid rgba(13,63,78,.13);background:#fff;border-radius:13px;color:var(--ink);padding:8px 11px;font-weight:900;cursor:pointer}.action-row{margin-top:18px}'
if old_junction not in s: raise SystemExit('junction css source not found')
s=s.replace(old_junction,new_junction,1)

# Mobile refinements: smaller words, stacked explanation cards.
s=s.replace('.junction{height:76px}.junction-pipe:before,.junction-pipe:after{top:33px;width:34px}.relation-badge{font-size:12px;padding:8px 13px}.word{font-size:clamp(40px,10vw,54px)}', '.junction{min-height:220px;grid-template-columns:1fr 88px 1fr;gap:7px;padding:14px 0}.junction-pipe:before,.junction-pipe:after{width:38px}.relation-badge{font-size:11px;padding:7px 9px}.explain-card{padding:10px 11px;min-height:110px}.explain-card p{font-size:12px}.grammar-note{font-size:11.5px}.word{font-size:clamp(38px,9vw,50px)}', 1)

# Rebuild card markup so controls live in the header line and the lower card can collapse.
old_anchor='<div class="flip-shell"><article class="word-card" id="anchorCard"><div class="word-label" id="anchorLabel">Today\'s word</div><div class="word-row"><div><div class="word" id="anchorWord">practical</div><div class="part" id="anchorPart">adjective</div></div><div class="card-controls"><button class="mini-btn" id="speakAnchor" aria-label="Hear anchor word" title="Hear word">🔊</button><button class="mini-btn" id="changeAnchor" aria-label="Branch to a connected word" title="Branch to a connected word">↻</button></div></div><p class="definition" id="anchorDefinition">Loading…</p><div class="sense-notice" id="senseNotice"></div></article></div>'
new_anchor='<div class="flip-shell"><article class="word-card" id="anchorCard"><div class="card-head"><div class="word-label" id="anchorLabel">Today\'s word</div><div class="card-controls"><button class="mini-btn" id="speakAnchor" aria-label="Hear anchor word" title="Hear word">🔊</button><button class="mini-btn" id="changeAnchor" aria-label="Another word connected to the lower card" title="Change only this card">↻</button></div></div><div class="word-row"><div class="word" id="anchorWord">practical</div><div class="part" id="anchorPart">adjective</div></div><p class="definition" id="anchorDefinition">Loading…</p><div class="sense-notice" id="senseNotice"></div></article></div>'
if old_anchor not in s: raise SystemExit('anchor markup source not found')
s=s.replace(old_anchor,new_anchor,1)

old_mid='<div class="junction" id="junction"><div class="junction-pipe"></div><div class="relation-badge" id="relationshipPill" aria-label="Relationship label">Finding connection…</div></div>'
new_mid='<div class="junction" id="junction"><div class="junction-pipe"></div><div class="explain-card" id="connectCard"><strong>How they connect</strong><p id="connectText"></p></div><div class="relation-badge" id="relationshipPill" aria-label="Relationship label">Finding connection…</div><div class="explain-card" id="boundaryCard"><strong>Where they differ</strong><p id="boundaryText"></p></div><div class="grammar-note hidden" id="grammarNote"></div></div>'
s=s.replace(old_mid,new_mid,1)

old_related='<div class="flip-shell"><article class="word-card" id="relatedCard"><div class="word-label" id="relatedLabel">Related word</div><div class="word-row"><div><div class="word" id="relatedWord">—</div><div class="part" id="relatedPart"></div></div><div class="card-controls"><button class="mini-btn" id="speakRelated" aria-label="Hear related word" title="Hear word">🔊</button><button class="mini-btn" id="changeRelated" aria-label="Another connection" title="Another connection">↻</button></div></div><p class="definition" id="relatedDefinition"></p><div class="connection-box" id="connectionNote"></div><div class="boundary" id="difference"></div><div class="action-row"><button class="small-action" id="hearBtn">🔊 Hear it</button><button class="small-action" id="exampleBtn">▤ Examples</button><button class="small-action" id="saveBtn">♡ Save</button></div><div class="primary-row"><button class="primary" id="exploreBtn">Make this my word →</button><button class="secondary" id="anotherBtn" aria-label="Another connection" title="Another connection">↻</button></div></article></div>'
new_related='<div class="flip-shell"><article class="word-card" id="relatedCard"><div class="card-head"><div class="word-label" id="relatedLabel">Related word</div><div class="card-controls"><button class="mini-btn" id="speakRelated" aria-label="Hear related word" title="Hear word">🔊</button><button class="mini-btn" id="changeRelated" aria-label="Another word connected to the upper card" title="Change only this card">↻</button><button class="expand-btn" id="expandRelated" aria-expanded="false" title="Show more">More</button></div></div><div class="word-row"><div class="word" id="relatedWord">—</div><div class="part" id="relatedPart"></div></div><p class="definition" id="relatedDefinition"></p><div class="connection-box" id="connectionNote"></div><div class="boundary" id="difference"></div><div class="related-extra" id="relatedExtra"><div class="action-row"><button class="small-action" id="hearBtn">🔊 Hear it</button><button class="small-action" id="exampleBtn">▤ Examples</button><button class="small-action" id="saveBtn">♡ Save</button></div></div></article></div>'
if old_related not in s: raise SystemExit('related markup source not found')
s=s.replace(old_related,new_related,1)

s=s.replace('<div class="build-marker" id="buildMarker">two-card-junction-v3</div>', '<div class="build-marker" id="buildMarker">two-card-junction-v4</div>', 1)

# JS element map additions.
s=s.replace("difference:$('#difference'),junction:$('#junction'),relatedLabel:$('#relatedLabel')", "difference:$('#difference'),junction:$('#junction'),relatedLabel:$('#relatedLabel'),connectText:$('#connectText'),boundaryText:$('#boundaryText'),connectCard:$('#connectCard'),boundaryCard:$('#boundaryCard'),grammarNote:$('#grammarNote'),relatedExtra:$('#relatedExtra'),expandRelated:$('#expandRelated')", 1)

# Add grammar helper immediately before render.
needle='function animateCard(card,fn){if(matchMedia(\'(prefers-reduced-motion: reduce)\').matches){fn();return Promise.resolve()}return new Promise(resolve=>{card.classList.add(\'flipping\');setTimeout(()=>{fn();requestAnimationFrame(()=>{card.classList.remove(\'flipping\');setTimeout(resolve,260)})},220)})}\n'
helper="function grammarText(a,r){if(!a||!r||!a.pos||!r.pos||a.pos===r.pos)return '';const pa=a.pos.toLowerCase(),pr=r.pos.toLowerCase();return `How they work in a sentence: ${a.word} is ${/^[aeiou]/.test(pa)?'an':'a'} ${pa}; ${r.word} is ${/^[aeiou]/.test(pr)?'an':'a'} ${pr}. That grammatical difference limits where they can substitute for each other.`}\n"
if needle not in s: raise SystemExit('animate helper source not found')
s=s.replace(needle,needle+helper,1)

# Patch render to populate junction explanation cards and keep old hidden fields for compatibility.
old_fragment="els.connectionNote.classList.toggle('opposite',opp);els.exploreBtn.classList.toggle('opposite',opp);"
new_fragment="els.connectionNote.classList.toggle('opposite',opp);els.connectCard.classList.toggle('opposite',opp);els.boundaryCard.classList.toggle('opposite',opp);"
if old_fragment not in s: raise SystemExit('render style fragment not found')
s=s.replace(old_fragment,new_fragment,1)

s=s.replace("els.relationshipPill.textContent=rel?.label||(opp?'Opposite in this sense':'Connected in this sense');els.connectionNote.textContent=rel?.connection||'';els.difference.textContent=rel?.distinction||'';els.exploreBtn.disabled=false;$('#changeAnchor').disabled=false;$('#changeRelated').disabled=false;els.anotherBtn.disabled=false;", "els.relationshipPill.textContent=rel?.label||(opp?'Opposite in this sense':'Connected in this sense');els.connectionNote.textContent=rel?.connection||'';els.difference.textContent=rel?.distinction||'';els.connectText.textContent=rel?.connection||'These words are linked in this exact dictionary sense.';els.boundaryText.textContent=rel?.distinction||'This connection applies to this sense rather than every use of either word.';const gram=grammarText(a,r);els.grammarNote.textContent=gram;els.grammarNote.classList.toggle('hidden',!gram);$('#changeAnchor').disabled=false;$('#changeRelated').disabled=false;", 1)

s=s.replace("els.relationshipPill.textContent='No connection found';els.connectionNote.textContent='Try the other direction or choose another word.';els.difference.textContent='';els.exploreBtn.disabled=true;$('#changeAnchor').disabled=true;els.anotherBtn.disabled=true;", "els.relationshipPill.textContent='No connection found';els.connectionNote.textContent='Try the other direction or choose another word.';els.difference.textContent='';els.connectText.textContent='Try the other direction or choose another word.';els.boundaryText.textContent='';els.grammarNote.classList.add('hidden');$('#changeAnchor').disabled=true;", 1)

# Remove obsolete explore wiring and add collapsible lower-card controls.
s=s.replace("els.exploreBtn.onclick=explore;", "", 1)
s=s.replace("els.anotherBtn.onclick=another;", "", 1)
s=s.replace("$('#searchForm').onsubmit=submitSearch;", "els.expandRelated.onclick=()=>{const open=els.relatedExtra.classList.toggle('open');els.expandRelated.textContent=open?'Less':'More';els.expandRelated.setAttribute('aria-expanded',String(open))};$('#searchForm').onsubmit=submitSearch;", 1)

# Remove stale JS references if any remain in render disabled state.
s=s.replace("els.anotherBtn.disabled=true;", "", 1)
s=s.replace("els.exploreBtn.disabled=true;", "", 1)
s=s.replace("els.exploreBtn.disabled=false;", "", 1)
s=s.replace("els.anotherBtn.disabled=false;", "", 1)
s=s.replace("els.exploreBtn.classList.toggle('opposite',opp);", "", 1)

p.write_text(s)

sw=Path('sw.js')
w=sw.read_text()
w=re.sub(r'word-junctions-v\d+','word-junctions-v11',w,count=1)
sw.write_text(w)

# Validation.
s=p.read_text()
for marker in ['two-card-junction-v4','id="connectCard"','id="boundaryCard"','id="grammarNote"','id="expandRelated"','function grammarText(a,r)']:
    assert marker in s, marker
assert 'Make this my word' not in s
assert 'id="anotherBtn"' not in s
assert 'font-size:clamp(38px,9vw,50px)' in s
print('UI v4 compact junction patch PASS')
