// Deterministic seek-and-capture of original HTML overlays; no external services.
const fs=require('fs'),path=require('path'),{spawn}=require('child_process');
const {once}=require('events');
const {chromium,fontPath,launchOptions}=require('./browser_runtime.cjs');
(async()=>{
 const p=JSON.parse(fs.readFileSync(process.argv[2],'utf8')),out=process.argv[3];
 const [width,height]=p.ratio==='16:9'?[1280,720]:[720,1280];
 const browser=await chromium.launch(launchOptions());
 try{
  const page=await browser.newPage({viewport:{width,height},deviceScaleFactor:1});
  await page.route('**/*',r=>r.abort());
  const font=fs.readFileSync(fontPath()).toString('base64');
  await page.setContent(`<style>@font-face{font-family:Brand;src:url(data:font/ttf;base64,${font})}body{margin:0;background:transparent}*{box-sizing:border-box}#text{position:absolute;left:7%;right:12%;font:52px/1.45 Brand;text-align:center;direction:rtl;text-shadow:0 2px 8px #000,0 0 3px #000;white-space:pre-wrap;overflow-wrap:anywhere}${fs.readFileSync(path.join(__dirname,'motion.css'),'utf8')}</style><div id="text"></div>`);
  await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'motion.js'),'utf8')});
  await page.evaluate(()=>document.fonts.ready);
  for(let i=0;i<p.timeline.length;i++){
   const c=p.timeline[i],m=require('./motion.js').mode(c,p);if(!c.text||m==='plain')continue;
   const d=c.end-c.start,frames=Math.ceil(d*30),brand={profile:{colors:p.profile?.colors||[]},motion_style:p.motion_style};
   const encoder=spawn('ffmpeg',['-v','error','-f','image2pipe','-framerate','30','-i','pipe:0','-an','-c:v','qtrle','-pix_fmt','argb','-y',`${out}/motion-${i}.mov`]);
   let error='';encoder.stderr.on('data',b=>error+=b);encoder.stdin.on('error',()=>{});
   const finished=new Promise((resolve,reject)=>{encoder.on('error',reject);encoder.on('close',code=>code===0?resolve():reject(Error(error||'overlay encoder failed')))});
   // Handle rejection while frames are still rendering; await again below.
   finished.catch(()=>{});
   for(let f=0;f<frames;f++){
    await page.evaluate(({p,c,t,d})=>StudioMotion.apply(document.getElementById('text'),c,p,t,d),{p:brand,c,t:f/30,d});
    const png=await page.screenshot({omitBackground:true});
    if(encoder.exitCode!==null)throw Error(error||'overlay encoder stopped');
    if(!encoder.stdin.write(png))await Promise.race([once(encoder.stdin,'drain'),finished]);
   }
   encoder.stdin.end();await finished;
  }
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
