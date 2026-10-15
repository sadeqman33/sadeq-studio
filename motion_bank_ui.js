/* Local bank UI: reference browsing and explicit, undoable layer application. */
let bankData=null,bankScope=null,bankPreviewFrame=0;
const bankFamilyNames={auto:'اختيار متنوّع',calm:'هادئ',punch:'قوي',onetake:'لقطة واحدة',editorial:'تحريري'};
const bankRoleNames={text:'نص',caption:'كابشن',card:'كرت',camera:'كاميرا',transition:'انتقال',rule:'قاعدة قص'};
async function openMotionBank(){
 if(!P)return;bankData=await api('/api/motion-bank');bankScope={id:P.id,work_id:P.active_work_id};
 $('bankProject').textContent='تفضيلاتك محفوظة لكل المشاريع · '+(selectedLayers().length?'المحدد: '+selectedLayers().map(l=>l.name).join('، '):'حدد طبقة من التايم لاين حتى تطبّق حركة');
 $('bankFamily').innerHTML=Object.entries(bankFamilyNames).map(([id,name])=>`<option value="${id}">${name}</option>`).join('');
 $('bankPlanResult').textContent='اختار عائلة حتى نجهّز اقتراح للفيديو. الخطة ما تغيّر التايم لاين.';
 const recent=bankData.state.history.filter(h=>h.project_id===P.id&&h.work_id===P.active_work_id).at(-1);if(recent)showBankPlan(recent);
 renderBank();$('motionBankDialog').showModal();
}
function renderBank(){
 const q=$('bankSearch').value.trim().toLowerCase(),filter=$('bankFilter').value,state=bankData.state;
 const rows=bankData.catalog.filter(m=>(m.name+' '+m.id+' '+m.n+' '+m.desc).toLowerCase().includes(q)&&
  (filter==='all'||filter==='native'&&m.native_types.length||filter==='on'&&state.on.includes(m.id)||filter==='off'&&state.off.includes(m.id)||filter===m.role));
 $('bankCount').textContent=rows.length+' / '+bankData.catalog.length+' حركة · '+bankData.catalog.filter(m=>m.native_types.length).length+' مرتبطة بالطبقات';
 $('bankCards').innerHTML=rows.map(m=>`<article class="bank-card"><div class="bank-card-title"><b>${m.n}. ${esc(m.name)}</b><span>${esc(bankRoleNames[m.role])}</span></div><video preload="none" controls muted loop playsinline aria-label="معاينة المصدر: ${esc(m.name)}" poster="/motion-bank/posters/${String(m.n).padStart(2,'0')}.jpg" src="/motion-bank/previews/${String(m.n).padStart(2,'0')}.mp4"></video><p>${esc(m.desc)}</p><small>${m.native_types.length?'تنفيذ Studio للطبقات · '+(m.native_types.length>1?'نص وصورة وأيقونة':'نص فقط'):'مرجع للمونتاج · يحتاج ترتيب مشاهد أو بيانات إضافية'}</small><div class="bank-buttons"><button data-bank-pref="on" data-bank-id="${m.id}" aria-pressed="${state.on.includes(m.id)}">★ أفضّلها</button><button data-bank-pref="off" data-bank-id="${m.id}" aria-pressed="${state.off.includes(m.id)}">استبعدها</button></div>${m.native_types.length?`<div class="bank-buttons"><button data-bank-demo="${m.id}">جرّب حركة Studio</button><button data-bank-apply="${m.id}">طبّق على المحدد</button></div>`:''}<a href="${esc(m.source.url||'https://github.com/majedphotos/video-ad-editor')}" target="_blank" rel="noopener noreferrer">مصدر الفكرة ↗</a></article>`).join('');
 for(const b of $('bankCards').querySelectorAll('[data-bank-pref]'))b.onclick=task(async()=>{
  const id=b.dataset.bankId,kind=b.dataset.bankPref,on=state.on.filter(x=>x!==id),off=state.off.filter(x=>x!==id);
  if(!state[kind].includes(id))(kind==='on'?on:off).push(id);
  const result=await api('/api/motion-bank',{action:'preferences',revision:state.revision,on,off});bankData.state=result.state;renderBank();
 });
 for(const b of $('bankCards').querySelectorAll('[data-bank-apply]'))b.onclick=()=>applyBankMotion(b.dataset.bankApply);
 for(const b of $('bankCards').querySelectorAll('[data-bank-demo]'))b.onclick=()=>demoBankMotion(b.dataset.bankDemo);
 for(const video of $('bankCards').querySelectorAll('video'))video.onplay=()=>{for(const other of $('bankCards').querySelectorAll('video'))if(other!==video)other.pause()};
}
function applyBankMotion(id){
 if(!P||P.id!==bankScope.id||P.active_work_id!==bankScope.work_id){toast('الفيديو تغيّر؛ افتح البنك من جديد');return}
 const rows=selectedLayers(),entry=bankData.catalog.find(m=>m.id===id);
 if(lastJob||pendingMutations){toast('انتظر العملية الحالية');return}
 if(!rows.length){toast('حدد طبقة نص أو أيقونة على التايم لاين أولاً');return}
 if(rows.some(l=>l.locked||!entry.native_types.includes(l.type))){toast('الاختيار بيه طبقة مقفولة أو نوع ما يدعم هالحركة');return}
 for(const l of rows)Object.assign(l,{bankMotion:id,motion:'plain',enterDuration:.7,exitDuration:.24,exitMotion:'fade'});
 advancedRenderer();markDirty();$('motionBankDialog').close();renderLayersUI();if(selectedLayer)selectLayer(selectedLayer,false);
 const first=rows[0];seek(first.start+Math.min(.4,(first.end-first.start)/2));toast('انطبقت «'+entry.name+'» على '+rows.length+' طبقة؛ احفظ التعديلات');
}
function demoBankMotion(id){
 cancelAnimationFrame(bankPreviewFrame);const entry=bankData.catalog.find(m=>m.id===id),node=$('bankDemoLayer');
 const l={type:'text',text:id==='counter'?'85%':'صادق ستوديو',start:0,end:3,x:50,y:50,width:85,fontSize:90,font:'Hacen Beirut',color:'#ffffff',opacity:1,motion:'plain',bankMotion:id,enterDuration:.7,exitMotion:'fade',exitDuration:.24};
 $('bankDemoTitle').textContent=entry.name+' · التنفيذ داخل Studio';$('bankDemo').hidden=false;
 const began=performance.now();function paint(now){const t=((now-began)/1000)%3.5;Object.assign(node.style,StudioLayers.style(l,t,$('bankDemoStage').clientWidth));StudioBank.paintText(node,l,t);bankPreviewFrame=requestAnimationFrame(paint)}bankPreviewFrame=requestAnimationFrame(paint);
}
function showBankPlan(plan){
 const names=ids=>ids.map(id=>{const m=bankData.catalog.find(m=>m.id===id);return `${m.n}. ${m.name}${m.native_types.length?'':' (مرجع مونتاج)'}`}).join('، ')||'ماكو اختيار متاح';
 $('bankPlanResult').textContent=`${bankFamilyNames[plan.family]}\nأساسيات: ${names(plan.core)}\nلمسات: ${names(plan.accents)}\n${plan.note}`;
}
function bindMotionBank(){
 $('openMotionBank').onclick=task(openMotionBank);$('layerBankOpen').onclick=task(openMotionBank);
 $('bankClose').onclick=()=>$('motionBankDialog').close();$('motionBankDialog').onclose=()=>{cancelAnimationFrame(bankPreviewFrame);$('bankDemo').hidden=true;for(const v of $('bankCards').querySelectorAll('video'))v.pause()};
 $('bankSearch').oninput=renderBank;$('bankFilter').onchange=renderBank;
 $('layerBankClear').onclick=()=>{if(lastJob)return;const rows=selectedLayers();if(rows.some(l=>l.locked))return;for(const l of rows)delete l.bankMotion;markDirty();renderLayersUI();if(selectedLayer)selectLayer(selectedLayer,false)};
 $('bankMakePlan').onclick=task(async()=>{
  if(P.id!==bankScope.id||P.active_work_id!==bankScope.work_id)throw Error('الفيديو تغيّر؛ افتح البنك من جديد');
  const d={...bankScope,action:'plan',revision:bankData.state.revision,title:P.work_list?.find(w=>w.id===P.active_work_id)?.title||P.name,family:$('bankFamily').value,native_only:$('bankNativeOnly').checked,cues:[...$('bankCues').selectedOptions].map(o=>o.value)};
  const result=await api('/api/motion-bank',d);bankData.state=result.state;showBankPlan(result.plan);
 });
}
