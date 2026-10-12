// Local Remotion render runner. Fixed entry point; no user code is evaluated.
const fs=require('fs'),path=require('path');
const {bundle}=require('@remotion/bundler');
const {renderMedia,selectComposition}=require('@remotion/renderer');
const {concurrency,encoding}=require('./performance.cjs');
const {spawnSync}=require('child_process');
(async()=>{
 const folder=path.resolve(process.argv[2]),root=path.resolve(__dirname,'..');
 const props=JSON.parse(fs.readFileSync(path.join(folder,'props.json'),'utf8'));
 const workers=concurrency(props.width,props.height);
 const report=data=>console.log('SADEQ_RENDER '+JSON.stringify(data));
 const ffmpeg=path.join(root,'node_modules','@remotion','compositor-darwin-'+process.arch,'ffmpeg');
 const native=process.platform==='darwin'&&process.env.SADEQ_RENDER_HARDWARE!=='0'&&fs.existsSync(ffmpeg)&&
  spawnSync(ffmpeg,['-v','error','-i',path.join(folder,'public',props.clips[0].src),'-frames:v','1','-an','-c:v','h264_videotoolbox','-f','null','-'],{
   timeout:10000,env:{...process.env,DYLD_LIBRARY_PATH:path.dirname(ffmpeg)}
  }).status===0;
 report({phase:'bundle',concurrency:workers,encoding_mode:native?'videotoolbox':'software'});
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'index.jsx'),rootDir:root,
  publicDir:path.join(folder,'public'),outDir:path.join(folder,'bundle'),enableCaching:true,
  symlinkPublicDir:true,askAIEnabled:false,keyboardShortcutsEnabled:false});
 const chrome=process.env.SADEQ_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 const browserExecutable=fs.existsSync(chrome)?chrome:undefined;
 const composition=await selectComposition({serveUrl,id:'SadeqTimeline',inputProps:props,browserExecutable});
 let last=0;
 const renderStarted=Date.now();let framesDone=null;
 const render=quality=>renderMedia({composition,serveUrl,inputProps:props,codec:'h264',
  outputLocation:path.join(folder,'video.mp4'),browserExecutable,concurrency:workers,
  pixelFormat:'yuv420p',...quality,muted:true,logLevel:'warn',
  onProgress:({progress,renderedFrames,encodedFrames})=>{
   const now=Date.now();if(now-last<500&&progress<1)return;last=now;
   if(progress===1&&framesDone===null)framesDone=Date.now();
   report({phase:renderedFrames<props.durationInFrames?'frames':'encode',progress:Math.round(progress*1000)/10,
    rendered_frames:renderedFrames,encoded_frames:encodedFrames,total_frames:props.durationInFrames});
  }});
 try{await render(encoding(props.width,props.height,props.fps,native));}
 catch(error){
  if(!native||!/(videotoolbox|hardware|encoder|ffmpeg)/i.test(error.message))throw error;
  console.warn('Native encoder unavailable; retrying with software H.264.',error.message);
  report({phase:'frames',progress:0,encoding_mode:'software'});
  await render(encoding(props.width,props.height,props.fps,false));
 }
 fs.writeFileSync(path.join(folder,'runner-timing.json'),JSON.stringify({renderSeconds:(Date.now()-renderStarted)/1000,postFramesSeconds:framesDone===null?null:(Date.now()-framesDone)/1000}));
 // Dedicated one-shot process: renderMedia has finalized the MP4. Let its
 // asynchronous cleanup run, then release lingering bundler/network timers.
 await new Promise(resolve=>setTimeout(resolve,250));
 process.exit(0);
})().catch(e=>{console.error(e);process.exit(1);});
