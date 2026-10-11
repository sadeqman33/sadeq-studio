/* Pure overlay interval operations. Timing estimates never claim ASR alignment. */
(function(root){
 function split(layer,time,id){if(!(time>layer.start&&time<layer.end))throw Error('حط المؤشر داخل مدة الطبقة');return [{...layer,end:time},{...layer,id,start:time}];}
 function words(layer,ids){
  const words=(layer.text||'').trim().split(/\s+/u).filter(Boolean);if(words.length<2)throw Error('اكتب جملة بيها كلمتين على الأقل');
  const total=words.reduce((n,w)=>n+Array.from(w).length,0);let at=layer.start;
  return words.map((text,i)=>{const end=i===words.length-1?layer.end:at+(layer.end-layer.start)*Array.from(text).length/total;const l={...layer,id:ids[i],text,name:text,start:at,end};at=end;return l});
 }
 const api={split,words};if(typeof module!=='undefined')module.exports=api;else root.TimelineTools=api;
})(typeof window!=='undefined'?window:globalThis);
