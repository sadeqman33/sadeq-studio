/* Pure timeline geometry: frame precision, anchored zoom and independent rows. */
(function(root){
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 function frame(t,fps,total=Infinity){return clamp(Math.round(t*fps)/fps,0,total)}
 function anchoredScroll(time,pps,screenX,label=110){return Math.max(0,label+time*pps-screenX)}
 function lanes(rows,expanded=false){
  if(expanded)return rows.map(l=>[l]);
  const result=[],ends=[];
  for(const l of [...rows].sort((a,b)=>a.start-b.start||a.end-b.end)){
   let i=ends.findIndex(t=>t<=l.start+1e-8);if(i<0)i=result.length;
   (result[i]||=[]).push(l);ends[i]=l.end;
  }return result;
 }
 function nearest(t,targets,threshold){let best=t,d=threshold;for(const x of targets){const delta=Math.abs(t-x);if(delta<d){d=delta;best=x}}return best}
 function shift(rows,delta,total,fps,targets=[],threshold=0){
  if(!rows.length||rows.some(l=>l.locked)||!Number.isFinite(delta))throw Error('اختار طبقات غير مقفولة');
  const first=Math.min(...rows.map(l=>l.start)),last=Math.max(...rows.map(l=>l.end));
  if(last-first>total+1e-8)throw Error('المجموعة أطول من الفيديو');
  delta=frame(Math.max(0,first+delta),fps)-first;
  const a=nearest(first+delta,targets,threshold)-(first+delta),b=nearest(last+delta,targets,threshold)-(last+delta);
  if(a||b)delta+=!a?b:!b?a:Math.abs(a)<=Math.abs(b)?a:b;
  delta=clamp(delta,-first,total-last);
  return rows.map(l=>({...structuredClone(l),start:+(l.start+delta).toFixed(6),end:+(l.end+delta).toFixed(6)}));
 }
 function trim(l,edge,time,total,fps,targets=[],threshold=0){
  if(l.locked)throw Error('الطبقة مقفولة');const next=structuredClone(l),step=1/fps;
  time=frame(nearest(time,targets,threshold),fps,total);
  if(edge==='start')next.start=clamp(time,0,l.end-step);else next.end=clamp(time,l.start+step,total);
  return next;
 }
 const api={clamp,frame,anchoredScroll,lanes,nearest,shift,trim};
 if(typeof module!=='undefined')module.exports=api;root.TimelineGeometry=api;
})(typeof window!=='undefined'?window:globalThis);
