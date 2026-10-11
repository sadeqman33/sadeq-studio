/* Uniform transforms preserve relative spacing, timing and source references. */
(function(root){
 const centre=rows=>({x:(Math.min(...rows.map(l=>l.x))+Math.max(...rows.map(l=>l.x)))/2,y:(Math.min(...rows.map(l=>l.y))+Math.max(...rows.map(l=>l.y)))/2});
 function move(rows,dx,dy){
  if(!rows.length||![dx,dy].every(Number.isFinite))throw Error('مكان المجموعة غير صالح');
  dx=Math.max(-Math.min(...rows.map(l=>l.x)),Math.min(100-Math.max(...rows.map(l=>l.x)),dx));dy=Math.max(-Math.min(...rows.map(l=>l.y)),Math.min(100-Math.max(...rows.map(l=>l.y)),dy));
  return rows.map(l=>({...structuredClone(l),x:l.x+dx,y:l.y+dy}));
 }
 function limits(rows){const c=centre(rows);let min=.01,max=100;for(const l of rows){min=Math.max(min,1/l.width);max=Math.min(max,100/l.width);if(l.type==='text'){min=Math.max(min,16/l.fontSize);max=Math.min(max,240/l.fontSize)}for(const k of ['x','y']){const d=l[k]-c[k];if(d>0)max=Math.min(max,(100-c[k])/d);else if(d<0)max=Math.min(max,-c[k]/d)}}return {min,max}}
 function scale(rows,factor){
  if(!rows.length||!Number.isFinite(factor)||factor<=0)throw Error('حجم المجموعة غير صالح');const c=centre(rows),range=limits(rows);if(factor<range.min-1e-8||factor>range.max+1e-8)throw Error('الحجم يتجاوز حدود الطبقات؛ قلّل نسبة التكبير');
  return rows.map(l=>({...structuredClone(l),x:c.x+(l.x-c.x)*factor,y:c.y+(l.y-c.y)*factor,width:l.width*factor,...(l.type==='text'?{fontSize:l.fontSize*factor}:{})}));
 }
 const api={centre,move,scale,limits};if(typeof module!=='undefined')module.exports=api;root.LayerGeometry=api;
})(typeof window!=='undefined'?window:globalThis);
