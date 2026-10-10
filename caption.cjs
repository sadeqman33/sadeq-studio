const fs=require('fs');
const {chromium,fontPath,launchOptions}=require('./browser_runtime.cjs');
(async()=>{
 const p=JSON.parse(fs.readFileSync(process.argv[2],'utf8')); const out=process.argv[3];
 const browser=await chromium.launch(launchOptions());
 const [width,height]=p.ratio==='16:9'?[1280,720]:[720,1280]; const page=await browser.newPage({viewport:{width,height}});
 const font=fs.readFileSync(fontPath()).toString('base64');
 const colors=p.profile.colors||[]; const lum=c=>{const n=parseInt(c.slice(1),16);return .2126*(n>>16)+.7152*((n>>8)&255)+.0722*(n&255)};const valid=colors.filter(c=>/^#[a-f0-9]{6}$/i.test(c)).sort((a,b)=>lum(b)-lum(a));const color=valid[0]&&lum(valid[0])>140?valid[0]:'#ffffff';
 await page.setContent(`<style>@font-face{font-family:Brand;src:url(data:font/ttf;base64,${font})}body{margin:0;background:transparent}#text{position:absolute;left:7%;right:12%;top:63%;font:52px/1.45 Brand;text-align:center;direction:rtl;color:${color};text-shadow:0 2px 8px #000,0 0 3px #000;white-space:pre-wrap;overflow-wrap:anywhere}</style><div id="text"></div>`);
 await page.evaluate(()=>document.fonts.ready);
 for(let i=0;i<p.timeline.length;i++){
   if(!p.timeline[i].text) continue;
   await page.locator('#text').evaluate((el,c)=>{el.textContent=c.text;el.style.top=(c.textY||63)+'%'},p.timeline[i]);
   await page.screenshot({path:`${out}/caption-${i}.png`,omitBackground:true});
 }
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
