import json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import server,hyperframes_bridge as hf
class MotionPresetTests(unittest.TestCase):
    def test_all_presets_keep_timing_and_deterministic_seek_in_preview(self):
        js="""const m=require('./motion.js');for(const mode of ['plain','kinetic','paper','fade','pop','blur']){const c={text:'نص عربي',motion:mode,textStart:.2,textEnd:1.8},e={style:{setProperty(){}},dataset:{}};m.apply(e,c,{},0,2);if(+e.style.opacity!==0)throw Error('early '+mode);m.apply(e,c,{},1,2);if(+e.style.opacity!==1)throw Error('hold '+mode);const hold=JSON.stringify(e.style);m.apply(e,c,{},1.9,2);if(+e.style.opacity!==0)throw Error('late '+mode);m.apply(e,c,{},1,2);if(JSON.stringify(e.style)!==hold)throw Error('seek '+mode)}if(m.state(.05,2,'pop').scale===m.state(.05,2,'fade').scale)throw Error('pop not distinct');if(!m.state(.05,2,'blur').blur)throw Error('focus not distinct');"""
        subprocess.run(['node','-e',js],cwd=server.ROOT,check=True)
    @unittest.skipUnless(hf.ready(),'local Hyperframes/GSAP required')
    def test_hyperframes_real_gsap_seek_matches_preview_for_every_preset(self):
        with tempfile.TemporaryDirectory() as t:
            modes=['plain','kinetic','paper','fade','pop','blur'];p={'ratio':'9:16','profile':{'colors':['#ffffff','#bb9955']},'assets':[{'id':'a','path':str(Path(t)/'source.mp4')}],'timeline':[{'asset':'a','start':0,'end':2,'text':'نص','motion':m,'textStart':.2,'textEnd':1.8} for m in modes]}
            with patch('render_runtime.cached_clip'):
                folder,*_=hf.compile_project(p,Path(t),lambda _: {'audio':False,'hdr':False,'width':1080,'height':1920},lambda *_:None,server.FONT)
            js="""const fs=require('fs'),vm=require('vm'),gsap=require('gsap').gsap,m=require('./motion.js');const html=fs.readFileSync(process.argv[1],'utf8'),script=html.split('<script>')[1].split('</script>')[0],els={};const context={gsap,StudioMotion:m,window:{},document:{getElementById(id){return els[id]??=( {style:{}})}}};vm.runInNewContext(script,context);const tl=context.window.__timelines.sadeq,modes=['plain','kinetic','paper','fade','pop','blur'];for(let i=0;i<modes.length;i++){for(const t of [.1,.8,1.5,.1]){tl.seek(i*2+.2+t,false);const s=m.state(t,1.6,modes[i]),e=els['text-'+i].style;if(Math.abs(e.opacity-s.opacity)>.0001)throw Error('opacity '+modes[i]);if(e.transform!==`translateY(${s.y}em) scale(${s.scale}) rotate(${s.rotate}deg)`&&modes[i]!=='plain'){// GSAP rounds proxy values; compare numeric components below.
const numbers=e.transform.match(/-?[0-9.]+/g).map(Number);if(Math.abs(numbers[0]-s.y)>.0001||Math.abs(numbers[1]-s.scale)>.0001)throw Error('transform '+modes[i]);}
if(Math.abs(parseFloat(e.filter.slice(5))-s.blur)>.0001)throw Error('blur '+modes[i]);}}tl.kill();gsap.ticker.sleep();"""
            subprocess.run(['node','-e',js,str(folder/'index.html')],cwd=server.ROOT,check=True,timeout=15)
if __name__=='__main__':unittest.main()
