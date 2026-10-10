/* Original Sadeq Studio motion runtime. Shared by preview and offline export. */
(function(root){
 const modes=['plain','kinetic','paper'];
 function mode(c,p){return modes.includes(c?.motion)?c.motion:(modes.includes(p?.motion_style)?p.motion_style:'plain')}
 function state(t,d,m){
  const ease=x=>1-Math.pow(1-Math.max(0,Math.min(1,x)),3);
  const enter=m==='plain'?Math.max(0,Math.min(1,t/.2)):ease(t/Math.min(.38,d/3));
  const exit=m==='plain'?1:ease((d-t)/Math.min(.24,d/3));
  return {opacity:Math.min(enter,exit),y:m==='plain'?0:(1-enter)*.5-(1-exit)*.16,scale:m==='paper'?.94+.06*enter:1,rotate:m==='paper'?-2*(1-enter):0};
 }
 function apply(el,c,p,t,d){
  const start=c?.textStart??0,end=c?.textEnd??d;const active=t>=start&&t<end;const m=mode(c,p),s=state(Math.max(0,t-start),Math.max(.05,end-start),m);if(!active)s.opacity=0;
  el.textContent=c?.text||'';el.dataset.motion=m;
  el.style.top=(c?.textY??63)+'%';el.style.opacity=s.opacity;
  el.style.transform=`translateY(${s.y}em) scale(${s.scale}) rotate(${s.rotate}deg)`;
  const cs=(p?.profile?.colors||[]).filter(x=>/^#[a-f0-9]{6}$/i.test(x));
  const lum=x=>{const n=parseInt(x.slice(1),16);return .2126*(n>>16)+.7152*((n>>8)&255)+.0722*(n&255)};
  const light=cs.slice().sort((a,b)=>lum(b)-lum(a))[0];
  el.style.color=m==='paper'?'#211d19':light&&lum(light)>140?light:'#ffffff';
  el.style.setProperty('--motion-accent',cs[1]||'#cb984f');
 }
 const api={mode,state,apply};if(typeof module!=='undefined')module.exports=api;else root.StudioMotion=api;
})(typeof window!=='undefined'?window:globalThis);
