// Local Remotion render runner. Fixed entry point; no user code is evaluated.
const fs=require('fs'),path=require('path');
const {bundle}=require('@remotion/bundler');
const {renderMedia,selectComposition}=require('@remotion/renderer');
(async()=>{
 const folder=path.resolve(process.argv[2]),root=path.resolve(__dirname,'..');
 const props=JSON.parse(fs.readFileSync(path.join(folder,'props.json'),'utf8'));
 const serveUrl=await bundle({entryPoint:path.join(__dirname,'index.jsx'),rootDir:root,
  publicDir:path.join(folder,'public'),outDir:path.join(folder,'bundle'),enableCaching:false,
  askAIEnabled:false,keyboardShortcutsEnabled:false});
 const chrome=process.env.SADEQ_CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 const browserExecutable=fs.existsSync(chrome)?chrome:undefined;
 const composition=await selectComposition({serveUrl,id:'SadeqTimeline',inputProps:props,browserExecutable});
 await renderMedia({composition,serveUrl,inputProps:props,codec:'h264',
  outputLocation:path.join(folder,'video.mp4'),browserExecutable,concurrency:1,
  pixelFormat:'yuv420p',crf:18,muted:true,logLevel:'warn',
  onProgress:({progress})=>console.log('Frames: '+Math.round(progress*100)+'%')});
})().catch(e=>{console.error(e);process.exit(1);});
