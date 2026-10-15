/* Local editor navigation and direct manipulation. No agent or media upload. */
const TUI={scope:null,snap:true,follow:true,expanded:{},height:230,dragging:false,media:new Map(),queue:[],workers:0,mediaTick:0};
const timelineFPS=()=>P?.export_settings?.fps||30;
const TL_LABEL=110;
function applyTimelineHeight(){const extra=$('captionsPanel')?.open?142:0,h=Math.max(700,TUI.height+510)+extra;$('timelineBody').style.height=TUI.height+'px';document.querySelector('.editor-column').style.minHeight=h+'px';document.querySelector('.workspace').style.minHeight=h+'px'}
function syncTimelineView(){
 if(!P||TUI.scope===editorScope())return;TUI.scope=editorScope();
 let v={};try{v=JSON.parse(localStorage.getItem('sadeq-timeline:'+TUI.scope)||'{}')}catch{}
 timelineZoom=TimelineGeometry.clamp(Number(v.zoom)||1,.5,128);TUI.snap=v.snap!==false;TUI.follow=v.follow!==false;TUI.expanded=v.expanded||{};TUI.height=TimelineGeometry.clamp(Number(v.height)||230,150,500);
 applyTimelineHeight();$('timelineBody').scrollLeft=Number(v.scroll)||0;$('inlineTextEditor').hidden=true;
}
function rememberTimelineView(){if(!P)return;localStorage.setItem('sadeq-timeline:'+editorScope(),JSON.stringify({zoom:timelineZoom,height:TUI.height,snap:TUI.snap,follow:TUI.follow,expanded:TUI.expanded,scroll:$('timelineBody').scrollLeft}))}
function positionPlayhead(){
 if(!P)return;const h=$('playhead');h.style.left=(TL_LABEL+globalTime*pixelsPerSecond)+'px';h.setAttribute('aria-valuemax',duration());h.setAttribute('aria-valuenow',globalTime.toFixed(4));h.setAttribute('aria-valuetext',globalTime.toFixed(3)+' ثانية');
 $('playheadTime').textContent=fmt(globalTime)+':'+String(Math.floor((globalTime%1)*timelineFPS())).padStart(2,'0');
 if(playing&&TUI.follow&&!TUI.dragging){const body=$('timelineBody'),x=TL_LABEL+globalTime*pixelsPerSecond;if(x-body.scrollLeft>body.clientWidth-40||x-body.scrollLeft<TL_LABEL)body.scrollLeft=Math.max(0,x-body.clientWidth*.45)}
}
function timelineZoomTo(value,anchorTime=globalTime,screenX){
 if(!P)return;const body=$('timelineBody'),origin=()=>$('ruler').getBoundingClientRect().left-body.getBoundingClientRect().left+body.scrollLeft;screenX??=origin()+anchorTime*pixelsPerSecond-body.scrollLeft;
 timelineZoom=TimelineGeometry.clamp(value,.5,128);renderTimeline();body.scrollLeft=TimelineGeometry.anchoredScroll(anchorTime,pixelsPerSecond,screenX,origin());rememberTimelineView();
}
function timelineFitSelection(){
 if(!P)return;const rows=selectedLayers();let start,end;
 if(rows.length){start=Math.min(...rows.map(l=>l.start));end=Math.max(...rows.map(l=>l.end))}
 else{const i=P.timeline.findIndex(c=>c.id===selected);if(i<0)return;start=P.timeline.slice(0,i).reduce((n,c)=>n+c.end-c.start,0);end=start+P.timeline[i].end-P.timeline[i].start}
 const available=Math.max(100,$('timelineBody').clientWidth-TL_LABEL-24),fit=Math.max(.01,available/Math.max(.01,duration()));
 timelineZoomTo((available/Math.max(.2,end-start)*.86)/fit,start-((end-start)*.08),TL_LABEL); 
}
function pauseTimeline(){playing=false;$('video').pause();$('voicePreview').pause();$('play').textContent='▶'}
function timelineTimeAt(x){return TimelineGeometry.frame((x-$('ruler').getBoundingClientRect().left)/pixelsPerSecond,timelineFPS(),Math.max(0,duration()-1/timelineFPS()))}
function pointerGesture(e,node,move,end=()=>{},autoPan=false){
 e.preventDefault();e.stopPropagation();TUI.dragging=true;let latest=e,active=true,raf;
 const body=$('timelineBody');node.setPointerCapture?.(e.pointerId);document.body.classList.add('timeline-dragging');
 const tick=()=>{if(!active)return;if(autoPan){const r=body.getBoundingClientRect();if(latest.clientX>r.right-20)body.scrollLeft+=Math.min(28,(latest.clientX-r.right+20)*.55);else if(latest.clientX<r.left+TL_LABEL+16)body.scrollLeft-=Math.min(28,(r.left+TL_LABEL+16-latest.clientX)*.55)}move(latest);raf=requestAnimationFrame(tick)};
 const onMove=v=>{if(v.pointerId===e.pointerId)latest=v};
 const finish=v=>{if(v.pointerId!==e.pointerId)return;latest=v;move(latest);active=false;cancelAnimationFrame(raf);window.removeEventListener('pointermove',onMove);window.removeEventListener('pointerup',finish);window.removeEventListener('pointercancel',finish);if(node.hasPointerCapture?.(e.pointerId))node.releasePointerCapture(e.pointerId);TUI.dragging=false;document.body.classList.remove('timeline-dragging');end(v);rememberTimelineView()};
 window.addEventListener('pointermove',onMove);window.addEventListener('pointerup',finish);window.addEventListener('pointercancel',finish);raf=requestAnimationFrame(tick);
}
function dirtyGesture(){dirty=true;updateSaveState()}
function timelineTargets(exclude=new Set()){
 let t=0;const times=[0,duration(),globalTime];for(const c of P.timeline){t+=c.end-c.start;times.push(t)}
 for(const l of P.layers||[])if(!exclude.has(l.id))times.push(l.start,l.end);return times;
}
function layerGroup(l){return l.type==='text'?(l.track==='title'?'title':'caption'):l.type}
const TL_GROUPS={caption:'كابشن / كلمات',title:'عناوين / نصوص',image:'صور',icon:'أيقونات'};
function layerBarsHTML(rows){return rows.map(l=>`<button class="clip layer-bar ${layerSelection.has(l.id)?'selected':''} ${l.enabled===false?'layer-hidden':''} ${l.locked?'layer-locked':''} ${(l.end-l.start)*pixelsPerSecond<24?'compact':''}" data-layer="${l.id}" aria-pressed="${layerSelection.has(l.id)}" style="left:${l.start*pixelsPerSecond}px;width:${Math.max(3,(l.end-l.start)*pixelsPerSecond)}px" title="${esc(l.type==='text'?l.text:l.name)} · ${l.start.toFixed(2)}–${l.end.toFixed(2)}"><span class="layer-resize layer-resize-start" data-trim-edge="start"></span><span class="layer-bar-label">${esc(l.type==='text'?l.text||'نص فارغ':l.name)}</span><span class="layer-resize layer-resize-end" data-trim-edge="end"></span></button>`).join('')}
function drawLayerTracks(){
 const width=Math.max(100,duration()*pixelsPerSecond);$('legacyTextRow').hidden=!P.timeline.some(c=>c.text);
 $('layerTracks').innerHTML=Object.entries(TL_GROUPS).map(([key,label])=>{
  const rows=(P.layers||[]).filter(l=>layerGroup(l)===key);if(!rows.length)return '';
  const expanded=!!TUI.expanded[key],lanes=TimelineGeometry.lanes(rows,expanded);
  return `<div class="layer-group" data-group="${key}"><div class="layer-group-header"><button data-expand-group="${key}" aria-expanded="${expanded}">${expanded?'▾':'▸'} ${label} <small>${rows.length}</small></button></div>`+lanes.map((lane,i)=>`<div class="track layer-track"><div class="track-label">${expanded?`<span title="${esc(lane[0].name)}">${esc(lane[0].name)}</span><button data-row-eye="${lane[0].id}" title="إظهار أو إخفاء">${lane[0].enabled===false?'○':'◉'}</button><button data-row-lock="${lane[0].id}" title="قفل أو فتح">${lane[0].locked?'◆':'◇'}</button>`:`${label} ${lanes.length>1?i+1:''}`}</div><div class="layer-lane" style="width:${width}px">${layerBarsHTML(lane)}</div></div>`).join('')+'</div>';
 }).join('');
 for(const b of document.querySelectorAll('[data-layer]')){
  b.onclick=e=>{if(b.dataset.suppressClick==='true'){delete b.dataset.suppressClick;return}selectLayerFromClick(b.dataset.layer,e)};
  b.ondblclick=()=>openInlineText(b.dataset.layer);
  b.onpointerdown=e=>startLayerTiming(e,b);
 }
 document.querySelectorAll('[data-expand-group]').forEach(b=>b.onclick=()=>{TUI.expanded[b.dataset.expandGroup]=!TUI.expanded[b.dataset.expandGroup];renderLayersUI();rememberTimelineView()});
 document.querySelectorAll('[data-row-eye]').forEach(b=>b.onclick=()=>toggleLayerFlag(b.dataset.rowEye,'enabled'));
 document.querySelectorAll('[data-row-lock]').forEach(b=>b.onclick=()=>toggleLayerFlag(b.dataset.rowLock,'locked'));
 for(const lane of document.querySelectorAll('.layer-lane'))lane.onpointerdown=e=>{if(e.target!==lane||e.button!==0)return;if(e.shiftKey)startMarquee(e,lane);else{pauseTimeline();pointerGesture(e,lane,v=>seek(timelineTimeAt(v.clientX)),()=>{},true)}};
 syncQuickLayerBar();updatePreviewSelection();
}
function refreshLayerGeometry(){
 for(const b of document.querySelectorAll('[data-layer]')){const l=P.layers.find(l=>l.id===b.dataset.layer);if(l){b.style.left=l.start*pixelsPerSecond+'px';b.style.width=Math.max(3,(l.end-l.start)*pixelsPerSecond)+'px';b.title=(l.text||l.name)+' · '+l.start.toFixed(2)+'–'+l.end.toFixed(2)}}
 const l=P.layers.find(l=>l.id===selectedLayer);if(l){$('layerStart').value=l.start.toFixed(3);$('layerEnd').value=l.end.toFixed(3)}renderLayerPreview();
}
function startLayerTiming(e,b){
 if(lastJob||pendingMutations||e.button!==0||e.shiftKey||e.metaKey||e.ctrlKey)return;
 const l=P.layers.find(l=>l.id===b.dataset.layer);if(l.locked){selectLayer(l.id,false);return}
 const edge=e.target.closest('[data-trim-edge]')?.dataset.trimEdge;
 if(!layerSelection.has(l.id)||(edge&&layerSelection.size>1))selectLayer(l.id,false);
 b=document.querySelector(`[data-layer="${l.id}"]`);
 const rows=structuredClone(selectedLayers());if(rows.some(l=>l.locked)){toast('افتح قفل المجموعة قبل تحريكها');return}
 const before=JSON.stringify(rows),x=e.clientX,scroll=$('timelineBody').scrollLeft,targets=timelineTargets(new Set(rows.map(l=>l.id)));let moved=false;
 pointerGesture(e,b,v=>{const dx=v.clientX-x+$('timelineBody').scrollLeft-scroll;if(!moved&&Math.abs(dx)<3)return;moved=true;
  const delta=dx/pixelsPerSecond,tolerance=TUI.snap&&!v.altKey?7/pixelsPerSecond:0;
  try{replaceLayerRows(edge?[TimelineGeometry.trim(l,edge,l[edge]+delta,duration(),timelineFPS(),targets,tolerance)]:TimelineGeometry.shift(rows,delta,duration(),timelineFPS(),targets,tolerance));dirtyGesture();refreshLayerGeometry()}catch(e){toast(e.message)}
 },()=>{if(moved){b.dataset.suppressClick='true';if(JSON.stringify(selectedLayers())!==before)markDirty();renderLayersUI()}},true);
}
function startMarquee(e,lane){
 if(lastJob)return;const box=$('timelineMarquee'),origin={x:e.clientX,y:e.clientY},base=e.ctrlKey||e.metaKey?new Set(layerSelection):new Set();
 pointerGesture(e,lane,v=>{const r=$('timelineCanvas').getBoundingClientRect(),left=Math.min(origin.x,v.clientX),right=Math.max(origin.x,v.clientX),top=Math.min(origin.y,v.clientY),bottom=Math.max(origin.y,v.clientY);box.hidden=false;Object.assign(box.style,{left:left-r.left+'px',top:top-r.top+'px',width:right-left+'px',height:bottom-top+'px'});layerSelection=new Set(base);
  for(const b of document.querySelectorAll('[data-layer]')){const br=b.getBoundingClientRect();if(br.left<right&&br.right>left&&br.top<bottom&&br.bottom>top)layerSelection.add(b.dataset.layer);b.classList.toggle('selected',layerSelection.has(b.dataset.layer))}
 },()=>{box.hidden=true;const ids=[...layerSelection];if(ids.length){selectLayer(ids[0],false);layerSelection=new Set(ids);selectedLayer=ids[0];renderGroupEdit();renderLayersUI()}},true);
}
function toggleLayerFlag(id,key){if(lastJob||pendingMutations)return;const l=P.layers.find(l=>l.id===id);if(!l)return;l[key]=key==='enabled'?l.enabled===false:!l.locked;markDirty();renderLayersUI()}
function syncQuickLayerBar(){
 const rows=selectedLayers(),one=rows.length===1?rows[0]:null;const bar=$('quickLayerBar');bar.hidden=!rows.length;
 $('quickLayerName').textContent=one?(one.text||one.name):rows.length+' طبقات';
 if(document.activeElement!==$('quickLayerSize'))$('quickLayerSize').value=one?(one.type==='text'?one.fontSize:one.width):100;
 const range=rows.length>1?LayerGeometry.limits(groupScaleBase||rows):null;
 $('quickLayerSize').min=range?Math.ceil(range.min*100):one?.type==='text'?16:1;$('quickLayerSize').max=range?Math.floor(range.max*100):one?.type==='text'?240:100;
 $('quickLayerColor').hidden=!one||one.type!=='text';if(one?.type==='text')$('quickLayerColor').value=one.color;
 $('quickLayerMotion').hidden=!one;$('quickLayerExit').hidden=!one;if(one){$('quickLayerMotion').value=one.motion||'plain';$('quickLayerExit').value=one.exitMotion||one.motion||'plain'}
 const locked=rows.some(l=>l.locked);$('quickLayerLock').textContent=locked?'فتح القفل':'قفل';$('quickLayerLock').setAttribute('aria-pressed',locked);$('quickLayerHide').textContent=rows.every(l=>l.enabled===false)?'إظهار':'إخفاء';
 for(const id of ['quickLayerSize','quickLayerColor','quickLayerMotion','quickLayerExit','quickLayerCopy','quickLayerDelete'])$(id).disabled=lastJob||locked||pendingMutations>0;
 for(const id of ['quickLayerLock','quickLayerHide'])$(id).disabled=lastJob||pendingMutations>0;
 const fields=$('layerEdit');for(const input of fields.querySelectorAll('input,textarea,select,button:not(#singleLayer)'))input.disabled=lastJob||locked||pendingMutations>0;
 for(const b of document.querySelectorAll('[data-caption-delete]'))b.disabled=lastJob||P.layers.find(l=>l.id===b.dataset.captionDelete)?.locked===true;
}
function openInlineText(id){
 const l=P?.layers.find(l=>l.id===id);if(!l||l.type!=='text'||l.locked||lastJob)return;
 selectLayer(id);$('inlineTextEditor').dataset.editingLayer=id;$('inlineLayerText').value=l.text;$('inlineTextEditor').hidden=false;$('inlineLayerText').focus();$('inlineLayerText').select();
}
function updatePreviewSelection(){
 const box=$('previewSelectionBox'),frame=$('frame'),r=frame.getBoundingClientRect(),nodes=[...$('layerPreview').querySelectorAll('[data-layer-node]')].filter(n=>layerSelection.has(n.dataset.layerNode)&&n.style.display!=='none');
 if(!nodes.length||selectedLayers().some(l=>l.locked)){box.hidden=true;return}
 const bounds=nodes.map(n=>n.getBoundingClientRect()),left=Math.min(...bounds.map(b=>b.left)),top=Math.min(...bounds.map(b=>b.top)),right=Math.max(...bounds.map(b=>b.right)),bottom=Math.max(...bounds.map(b=>b.bottom));
 box.hidden=false;Object.assign(box.style,{left:left-r.left+'px',top:top-r.top+'px',width:right-left+'px',height:bottom-top+'px'});
}
function startPreviewSize(e,handle){
 if(lastJob||pendingMutations||e.button!==0)return;const rows=structuredClone(selectedLayers());if(!rows.length||rows.some(l=>l.locked))return;
 const r=$('previewSelectionBox').getBoundingClientRect(),cx=r.left+r.width/2,cy=r.top+r.height/2,d=Math.max(4,Math.hypot(e.clientX-cx,e.clientY-cy)),limits=LayerGeometry.limits(rows);let changed=false;
 pointerGesture(e,handle,v=>{const factor=TimelineGeometry.clamp(Math.hypot(v.clientX-cx,v.clientY-cy)/d,limits.min,limits.max);if(Math.abs(factor-1)<.002)return;replaceLayerRows(LayerGeometry.scale(rows,factor));changed=true;dirtyGesture();renderLayerPreview()},()=>{if(changed)markDirty();groupScaleBase=null;renderGroupEdit();syncQuickLayerBar()});
}
function startPreviewMove(e,node){
 const l=P?.layers.find(l=>l.id===node.dataset.layerNode);
 if(!l||l.locked||lastJob||pendingMutations||e.button!==0||e.shiftKey||e.metaKey||e.ctrlKey)return;
 if(!layerSelection.has(l.id))selectLayer(l.id,false);
 const rows=structuredClone(selectedLayers());if(rows.some(l=>l.locked))return;
 const x=e.clientX,y=e.clientY,r=$('frame').getBoundingClientRect();let moved=false;
 pointerGesture(e,node,v=>{if(Math.hypot(v.clientX-x,v.clientY-y)<2&&!moved)return;moved=true;replaceLayerRows(LayerGeometry.move(rows,(v.clientX-x)/r.width*100,(v.clientY-y)/r.height*100));dirtyGesture();groupScaleBase=null;renderLayerPreview()},()=>{if(moved)markDirty();const current=P.layers.find(l=>l.id===selectedLayer);if(current){$('layerX').value=current.x.toFixed(2);$('layerY').value=current.y.toFixed(2)}renderGroupEdit();syncQuickLayerBar()});
}
function waveSVG(peaks){if(!peaks?.length)return '';return '<svg class="timeline-wave" viewBox="0 0 '+peaks.length+' 24" preserveAspectRatio="none" aria-hidden="true"><path d="'+peaks.map((v,i)=>`M${i},${12-v*11}v${v*22}`).join(' ')+'"/></svg>'}
function requestTimelineMedia(a,start,end,kind='video'){
 const key=[P.id,a,start.toFixed(4),end.toFixed(4),kind].join(':');let entry=TUI.media.get(key);
 if(!entry){entry={state:'queued'};TUI.media.set(key,entry);TUI.queue.push({key,id:P.id,asset:a,start,end,kind,entry});pumpTimelineMedia()}return entry;
}
async function pumpTimelineMedia(){
 if(TUI.workers>=2||!TUI.queue.length||(lastJob&&['export','produce'].includes(activeJob?.kind)))return;const q=TUI.queue.shift();TUI.workers++;q.entry.state='loading';
 try{q.entry.data=await api(`/api/timeline-media/${q.id}/${q.asset}?start=${q.start}&end=${q.end}&kind=${q.kind}`);q.entry.state='ready'}catch(e){q.entry.state='error';q.entry.error=e.message}
 finally{TUI.workers--;scheduleTimelineMedia();pumpTimelineMedia()}
}
function scheduleTimelineMedia(){if(TUI.mediaTick)return;TUI.mediaTick=requestAnimationFrame(()=>{TUI.mediaTick=0;drawTimelineMedia()})}
function drawTimelineMedia(){
 if(!P)return;const body=$('timelineBody').getBoundingClientRect();
 for(const [i,c] of P.timeline.entries()){
  const node=document.querySelector(`[data-clip="${c.id}"]`);if(!node)continue;const r=node.getBoundingClientRect();if(r.right<body.left||r.left>body.right)continue;
  const entry=requestTimelineMedia(c.asset,c.start,c.end);if(entry.state!=='ready')continue;const d=entry.data;
  let thumbs=node.querySelector('.clip-thumbnails');if(!thumbs){thumbs=document.createElement('span');thumbs.className='clip-thumbnails';node.prepend(thumbs)}
  const urls=d.thumbnails||[];if(thumbs.dataset.key!==urls.join('|')){thumbs.replaceChildren(...urls.map(src=>{const img=document.createElement('img');img.src=src;img.alt='';img.loading='lazy';return img}));thumbs.dataset.key=urls.join('|')}
  const audio=$('audioTrack').children[i];if(audio&&audio.dataset.waveKey!==d.key){audio.innerHTML=waveSVG(d.peaks);audio.dataset.waveKey=d.key;audio.title=d.has_audio?'موجة صوت المصدر الفعلية':'المقطع بدون صوت'}
 }
 const v=P.voiceover,a=P.voiceover_assets?.find(a=>a.id===v?.asset),node=$('openVoiceTrack');
 if(a&&v.enabled&&node){const entry=requestTimelineMedia(a.id,v.trimStart,v.trimEnd,'voice');if(entry.state==='ready'&&node.dataset.waveKey!==entry.data.key){node.innerHTML=waveSVG(entry.data.peaks)+'<span>'+esc(a.name)+'</span>';node.dataset.waveKey=entry.data.key}}
}
function initTimelineUI(){
 $('ruler').onclick=null;
 for(const node of [$('playhead'),$('ruler')])node.onpointerdown=e=>{if(e.button!==0||!P?.timeline.length)return;pauseTimeline();$('playhead').focus({preventScroll:true});$('playhead').classList.add('scrubbing');pointerGesture(e,node,v=>seek(timelineTimeAt(v.clientX)),()=>{$('playhead').classList.remove('scrubbing')},true)};
 $('playhead').ondblclick=e=>{const b=[...document.querySelectorAll('[data-layer]')].find(b=>{const r=b.getBoundingClientRect();return e.clientX>=r.left&&e.clientX<=r.right&&e.clientY>=r.top&&e.clientY<=r.bottom});if(b)openInlineText(b.dataset.layer)};
 $('timelineBody').addEventListener('wheel',e=>{if(!P)return;if(e.ctrlKey||e.metaKey){e.preventDefault();const x=e.clientX-$('timelineBody').getBoundingClientRect().left,t=(e.clientX-$('ruler').getBoundingClientRect().left)/pixelsPerSecond;timelineZoomTo(timelineZoom*Math.exp(-e.deltaY*.008),t,x)}else if(e.shiftKey&&Math.abs(e.deltaY)>Math.abs(e.deltaX)){e.preventDefault();$('timelineBody').scrollLeft+=e.deltaY}},{passive:false});
 $('timelineBody').addEventListener('pointerdown',e=>{if(P&&!lastJob&&e.shiftKey&&e.button===0&&!e.target.closest('button,input,select,[data-layer],#playhead,#ruler'))startMarquee(e,$('timelineBody'))});
 $('timelineBody').onscroll=()=>{scheduleTimelineMedia();rememberTimelineView()};
 $('zoomIn').onclick=()=>timelineZoomTo(timelineZoom*1.2);$('zoomOut').onclick=()=>timelineZoomTo(timelineZoom/1.2);
 $('timelineZoomRange').oninput=()=>timelineZoomTo(2**+$('timelineZoomRange').value);
 $('fitTimeline').onclick=()=>{timelineZoomTo(1,0,TL_LABEL);$('timelineBody').scrollLeft=0};$('fitSelection').onclick=timelineFitSelection;
 $('timelineSnap').onclick=()=>{TUI.snap=!TUI.snap;$('timelineSnap').setAttribute('aria-pressed',TUI.snap);rememberTimelineView()};$('followPlayhead').onclick=()=>{TUI.follow=!TUI.follow;$('followPlayhead').setAttribute('aria-pressed',TUI.follow);rememberTimelineView()};
 $('timelineHeightHandle').onpointerdown=e=>{const y=e.clientY,height=$('timelineBody').clientHeight;pointerGesture(e,$('timelineHeightHandle'),v=>{TUI.height=TimelineGeometry.clamp(height+v.clientY-y,150,Math.min(500,innerHeight*.55));applyTimelineHeight()})};
 $('timelineHeightHandle').onkeydown=e=>{if(!['ArrowUp','ArrowDown'].includes(e.key))return;e.preventDefault();TUI.height=TimelineGeometry.clamp(TUI.height+(e.key==='ArrowDown'?20:-20),150,500);applyTimelineHeight();rememberTimelineView()};
 document.addEventListener('keydown',e=>{if(e.defaultPrevented||!P||e.isComposing||e.target.closest('input,textarea,select,[contenteditable],dialog')||TUI.dragging)return;
  if(e.metaKey||e.ctrlKey||e.altKey)return;let handled=true;
  if(e.key==='+'||e.key==='=')timelineZoomTo(timelineZoom*1.2);else if(e.key==='-')timelineZoomTo(timelineZoom/1.2);
  else if(e.key.toLowerCase()==='f')$('fitTimeline').click();else if(e.key.toLowerCase()==='n')$('timelineSnap').click();
  else if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){pauseTimeline();seek(e.key==='Home'?0:e.key==='End'?duration()-1/timelineFPS():globalTime+(e.key==='ArrowRight'?1:-1)*(e.shiftKey?10:1)/timelineFPS())}else handled=false;
  if(handled)e.preventDefault();
 });
 $('quickLayerCopy').onclick=()=>{if(lastJob||selectedLayers().some(l=>l.locked)||P.layers.length+layerSelection.size>100)return;const rows=selectedLayers().map(l=>({...structuredClone(l),id:newLayerId(),name:l.name+' · نسخة'}));P.layers.push(...rows);markDirty();layerSelection=new Set(rows.map(l=>l.id));selectedLayer=rows[0]?.id;renderLayersUI();renderGroupEdit()};
 $('quickLayerDelete').onclick=()=>$('deleteLayer').click();
 for(const [id,key] of [['quickLayerHide','enabled'],['quickLayerLock','locked']])$(id).onclick=()=>{if(lastJob)return;const rows=selectedLayers(),value=key==='enabled'?rows.every(l=>l.enabled===false):!rows.some(l=>l.locked);for(const l of rows)l[key]=value;markDirty();renderLayersUI()};
 $('quickLayerSize').oninput=()=>{const rows=selectedLayers();if(lastJob||rows.some(l=>l.locked))return;const n=+$('quickLayerSize').value;if(!Number.isFinite(n))return;if(rows.length===1){const l=rows[0];if(l.type==='text'&&n>=16&&n<=240)l.fontSize=n;else if(l.type!=='text'&&n>=1&&n<=100)l.width=n;else return}else{try{groupScaleBase||=structuredClone(rows);replaceLayerRows(LayerGeometry.scale(groupScaleBase,n/100))}catch{return}}if(rows.length===1){const l=rows[0];$(l.type==='text'?'layerFontSize':'layerWidth').value=n}markDirty();renderLayerPreview()};
 for(const [id,key] of [['quickLayerColor','color'],['quickLayerMotion','motion'],['quickLayerExit','exitMotion']])$(id).onchange=()=>{const rows=selectedLayers();if(rows.length!==1||rows[0].locked||lastJob)return;rows[0][key]=$(id).value;const field={color:'layerColor',motion:'layerMotion',exitMotion:'layerExitMotion'}[key];$(field).value=rows[0][key];markDirty();renderLayersUI()};
 $('inlineLayerText').oninput=()=>{const l=P?.layers.find(l=>l.id===$('inlineTextEditor').dataset.editingLayer);if(!l||l.locked||lastJob)return;l.text=$('inlineLayerText').value;markDirty('inline:'+l.id);renderLayersUI()};
 $('finishInlineText').onclick=()=>{$('inlineTextEditor').hidden=true;editHistory.group=null};$('inlineLayerText').onkeydown=e=>{if(e.key==='Escape'||e.key==='Enter'&&(e.metaKey||e.ctrlKey)){e.preventDefault();$('finishInlineText').click()}};
 for(const h of document.querySelectorAll('[data-size-corner]'))h.onpointerdown=e=>startPreviewSize(e,h);
}
