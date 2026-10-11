/* Original shared independent-layer geometry and timed motion. */
(function(root){
 const motion=typeof module!=='undefined'?require('./motion.js'):root.StudioMotion;
 function style(l,t,w=1080){
  const d=Math.max(.05,l.end-l.start),s=motion.state(Math.max(0,t-l.start),d,l.motion||'plain',('enterDuration' in l||'exitDuration' in l||'exitMotion' in l)?l:undefined);
  const active=l.enabled!==false&&t>=l.start&&t<l.end;
  return {position:'absolute',left:l.x+'%',top:l.y+'%',width:l.width+'%',opacity:active?s.opacity*(l.opacity??1):0,transform:`translate(-50%,-50%) translateY(${s.y}em) scale(${s.scale}) rotate(${(l.rotation||0)+s.rotate}deg)`,filter:`blur(${s.blur}em)`,fontSize:(l.fontSize||64)*w/1080+'px',fontFamily:l.font==='Alexandria'?'LayerAlexandria':'LayerHacen',color:l.color||'#ffffff',textAlign:'center',direction:'rtl',lineHeight:1.4,whiteSpace:'pre-wrap',overflowWrap:'anywhere',textShadow:l.type==='text'?'0 2px 8px #0008':'none',background:l.type==='text'&&l.motion==='paper'?'#f0eee6':'transparent',padding:l.type==='text'&&l.motion==='paper'?'.15em .3em':'0',boxSizing:'border-box'};
 }
 const api={style};if(typeof module!=='undefined')module.exports=api;else root.StudioLayers=api;
})(typeof window!=='undefined'?window:globalThis);
