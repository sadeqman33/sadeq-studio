// Original Sadeq composition: structured clips and plain text, never agent JSX.
import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Composition,OffthreadVideo,Sequence,cancelRender,continueRender,delayRender,getInputProps,registerRoot,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import motion from '../motion.js';
import layerStyles from '../layers.js';
import {Img} from 'remotion';
import '../motion.css';

const Caption=({clip,project,index})=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig();
 const style={setProperty(key,value){this[key]=value;}};
 motion.apply({style,dataset:{}},clip,project,frame/fps,clip.frames/fps);
 delete style.setProperty;
 const academy=project.typography?.style==='academy';
 const colors=(project.profile.colors||[]).filter(c=>/^#[a-f0-9]{6}$/i.test(c));
 const dark=colors.slice().sort((a,b)=>parseInt(a.slice(1),16)-parseInt(b.slice(1),16))[0]||'#2b0710';
 const hook=academy&&index===0;
 if(academy){style.color='#fff';style['--brand-dark']=dark;}
 return <div className={'caption '+(hook?'academy-hook':'')} data-motion={motion.mode(clip,project)} style={{position:'absolute',left:academy?'8%':'7%',right:'12%',fontFamily:'Brand',fontSize:academy?(hook?88:68):78,fontWeight:academy?750:400,lineHeight:1.45,textAlign:'center',direction:'rtl',whiteSpace:'pre-wrap',overflowWrap:'anywhere',textShadow:'0 2px 8px #000,0 0 3px #000',...style}}>{clip.text}</div>;
};

const Layer=({layer,index,width})=>{const frame=useCurrentFrame(),{fps}=useVideoConfig();return <div style={{...layerStyles.style(layer,frame/fps,width),zIndex:10+index}}>{layer.type==='text'?layer.text:<Img src={staticFile(layer.src)} style={{width:'100%',display:'block'}}/>}</div>;};

const Timeline=(project)=>{
 const [handle]=useState(()=>delayRender('Loading local Arabic font'));
 useEffect(()=>{
  let mounted=true;
  const font=new FontFace('Brand',`url(${staticFile('brand.ttf')})`);
  const fonts=[font,...[...new Set((project.layers||[]).filter(l=>l.type==='text').map(l=>l.font))].map(name=>new FontFace(name==='Alexandria'?'LayerAlexandria':'LayerHacen',`url(${staticFile(name==='Alexandria'?'layer-alexandria.ttf':'layer-hacen.ttf')})`))];
  Promise.all(fonts.map(f=>f.load())).then(loaded=>{loaded.forEach(f=>document.fonts.add(f));if(mounted)continueRender(handle);}).catch(cancelRender);
  return ()=>{mounted=false;};
 },[handle]);
 return <AbsoluteFill style={{backgroundColor:'#000'}}>{project.clips.map((clip,i)=><Sequence key={i} from={clip.from} durationInFrames={clip.frames}>
  <AbsoluteFill><OffthreadVideo src={staticFile(clip.src)} muted style={{width:'100%',height:'100%',objectFit:'contain'}}/></AbsoluteFill>
  {clip.text?<Caption clip={clip} project={project} index={i}/>:null}
 </Sequence>)}{(project.layers||[]).map((l,i)=><Layer key={l.id} layer={l} index={i} width={project.width}/>)}</AbsoluteFill>;
};

const Root=()=>{
 const p=getInputProps();
 return <Composition id="SadeqTimeline" component={Timeline} width={p.width||1080} height={p.height||1920} fps={30} durationInFrames={p.durationInFrames||30} defaultProps={p}/>;
};
registerRoot(Root);
