/* Sadeq Studio native adaptations. Deterministic frame clock, whole Arabic words.
   Reference catalog/previews: third-party/majed-motion-bank (MIT). */
(function(root){
 const supported=['blurIn','riseUp','wordDrop','rubberPop','scrollReveal','wordPath','focus','caption','highlight','shine','ctaPulse','strokeFill','typewriter','wordSwap','counter','decrypt'];
 const images=['blurIn','riseUp','wordDrop','rubberPop','shine','ctaPulse'];
 const clamp=x=>Math.max(0,Math.min(1,x)),ease=x=>1-Math.pow(1-clamp(x),3);
 const spring=x=>x>=1?1:1-Math.exp(-7*x)*Math.cos(11*x);
 function frame(l,t){const d=Math.max(.05,l.end-l.start),local=clamp((t-l.start)/d)*d,span=Math.max(.001,Math.min(l.enterDuration??.7,d*.5));return {d,local,span,k:clamp(local/span)}}
 function style(l,t){
  const m=l.bankMotion,{k,local}=frame(l,t),p=ease(k),s={clipPath:'none',backgroundImage:'none',backgroundSize:'auto',backgroundPosition:'0% 0%',WebkitTextStroke:'0px transparent'};
  let x=0,y=0,z=1,r=0,blur=0;
  if(m==='blurIn'){blur=(1-p)*.25;z=1+.1*(1-p)}
  if(m==='riseUp'){y=(1-p)*.65;s.clipPath=`inset(${(1-p)*100}% 0 0 0)`}
  if(m==='rubberPop'){z=.65+.35*spring(k)}
  if(m==='wordDrop')y=-(1-spring(k))*.9;
  if(m==='wordPath'){x=(1-p)*.75;y=-Math.sin(p*Math.PI)*.35;r=(1-p)*-8}
  if(m==='ctaPulse')z=1+.035*Math.sin(local*2*Math.PI)*p;
  if(m==='shine'){s.backgroundImage='linear-gradient(110deg,transparent 25%,#ffffff50 48%,transparent 70%)';s.backgroundSize='300% 100%';s.backgroundPosition=`${100-((local%2)/2)*200}% 0%`}
  if(m==='highlight'){s.backgroundImage='linear-gradient(#f2bb4870,#f2bb4870)';s.backgroundSize=`${p*100}% 35%`;s.backgroundPosition='right 85%';s.backgroundRepeat='no-repeat'}
  if(m==='strokeFill'){s.WebkitTextStroke=`.018em ${l.color||'#ffffff'}`;s.color=k<.45?'transparent':l.color||'#ffffff'}
  s.transform=`translate(-50%,-50%) translate(${x}em,${y}em) scale(${z}) rotate(${(l.rotation||0)+r}deg)`;s.filter=`blur(${blur}em)`+(m==='shine'?` brightness(${1+.35*Math.max(0,Math.sin(local*Math.PI))})`:'');
  return s;
 }
 function runs(l,t){
  if(!l.bankMotion||l.type!=='text')return null;
  const m=l.bankMotion,{local,span,k,d}=frame(l,t),text=l.text||'',words=text.split(/(\s+)/),nonempty=words.filter(w=>w.trim()),n=Math.max(1,nonempty.length);
  if(m==='counter'){
   // Animate only an unambiguous number; retain arbitrary prices/claims verbatim.
   if(!/^\s*[+-]?\d+(\.\d+)?\s*%?\s*$/.test(text))return [{text,style:{}}];
   const decimals=(text.match(/\.(\d+)/)||[])[1]?.length||0,value=Number(text.replace('%','').trim());
   return [{text:k>=1?text:(value*ease(k)).toFixed(Math.min(6,decimals))+(text.includes('%')?'%':''),style:{}}];
  }
  if(m==='wordSwap'){const i=Math.min(n-1,Math.floor(local/Math.max(.1,d/n)));return [{text:nonempty[i]||'',style:{}}]}
  if(m==='decrypt'){
   const pool='ابتثجحخدذرزسشصضطظعفقكلمنهوي',chars=[...text],settled=Math.floor(k*chars.length),f=Math.floor(local*18);
   return [{text:chars.map((c,i)=>/\s/.test(c)||i<settled||k>=1?c:pool[((f*17+i*13)%pool.length)]).join(''),style:{}}];
  }
  if(!['typewriter','scrollReveal','caption','focus','wordDrop','riseUp','wordPath'].includes(m))return [{text,style:{}}];
  let i=-1;const current=Math.min(n-1,Math.floor(local/Math.max(.1,d/n)));
  return words.map(word=>{
   if(!word.trim())return {text:word,style:{whiteSpace:'pre-wrap'}};
   i++;const q=clamp((local-i*span*.6/n)/(span*.4)),p=ease(q);let s={display:'inline-block'};
   if(m==='typewriter')s.visibility=local>=i*span/n?'visible':'hidden';
   if(m==='scrollReveal')s.opacity=.12+.88*p;
   if(m==='caption'){s.background=i===current?'#cb984f':'transparent';s.borderRadius='.15em';s.color=i===current?'#171411':l.color||'#ffffff'}
   if(m==='focus'){s.filter=`blur(${i===current?0:.035}em)`;s.opacity=i===current?1:.55}
   if(m==='riseUp'){s.transform=`translateY(${(1-p)*.65}em)`;s.opacity=p}
   if(m==='wordDrop'){s.transform=`translateY(${-(1-spring(q))*.7}em)`;s.opacity=p}
   if(m==='wordPath'){s.transform=`translate(${(1-p)*.5}em,${-Math.sin(p*Math.PI)*.25}em)`;s.opacity=p}
   return {text:word,style:s};
  });
 }
 function paintText(node,l,t){
  const parts=runs(l,t);
  if(!parts){if(node.textContent!==l.text||node.dataset.bankText){node.textContent=l.text;delete node.dataset.bankText}return}
  node.dataset.bankText='1';while(node.childNodes.length>parts.length)node.lastChild.remove();
  parts.forEach((p,i)=>{let el=node.childNodes[i];if(!el||el.nodeType!==1){const span=document.createElement('span');if(el)el.replaceWith(span);else node.append(span);el=span}el.textContent=p.text;el.style.cssText='';Object.assign(el.style,p.style)});
 }
 const api={supported,images,style,runs,paintText};if(typeof module!=='undefined')module.exports=api;else root.StudioBank=api;
})(typeof window!=='undefined'?window:globalThis);
