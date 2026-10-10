import copy, hashlib, json, math, struct, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import server
import hyperframes_bridge as hf

class HyperframesTests(unittest.TestCase):
    def test_timing_validation_and_preview_window(self):
        with tempfile.TemporaryDirectory() as t:
            src=Path(t)/'x.mp4';src.touch()
            p={'assets':[{'id':'a','path':str(src)}]}
            c={'asset':'a','start':0,'end':2,'text':'فكرة','textStart':.3,'textEnd':1.7}
            with patch.object(server,'probe',return_value={'duration':2}):
                server.validate_timeline(p,[c])
                for start,end in [(-1,1),(1,1),(0,3),(float('nan'),1),(0,float('inf'))]:
                    with self.assertRaises(ValueError): server.validate_timeline(p,[{**c,'textStart':start,'textEnd':end}])
            js="""const m=require('./motion.js'),el={style:{setProperty(){}},dataset:{}};const c={text:'فكرة',motion:'kinetic',textStart:.3,textEnd:1.7};m.apply(el,c,{},.1,2);if(el.style.opacity!==0)throw Error('early');m.apply(el,c,{},1,2);if(el.style.opacity!==1)throw Error('hold');m.apply(el,c,{},1.8,2);if(el.style.opacity!==0)throw Error('late');m.apply(el,c,{},1,2);if(el.style.opacity!==1)throw Error('seek');"""
            subprocess.run(['node','-e',js],cwd=server.ROOT,check=True)

    def test_production_keeps_plan_when_renderer_fails(self):
        events=[]
        with patch.object(server,'draft',side_effect=lambda *a,**kw:events.append(('draft',kw))),patch.object(server,'export',side_effect=ValueError('render failure')):
            with self.assertRaisesRegex(ValueError,'render failure'): server.produce('id','brief',{},['a'])
        self.assertEqual(events,[('draft',{'production':True})])

    @unittest.skipUnless(hf.ready(),'local Hyperframes dependencies required')
    def test_real_render_timing_muted_audio_and_originals(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'source';src.mkdir();old=server.DATA;server.DATA=root/'data'
            try:
                clip=src/'tone.mp4'
                server.command(['ffmpeg','-v','error','-f','lavfi','-i','color=c=navy:s=180x320:r=30:d=2','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-c:a','aac','-shortest','-y',str(clip)])
                original=hashlib.sha256(clip.read_bytes()).hexdigest();p=server.create('تجربة المحرك',str(src));aid=p['assets'][0]['id']
                p['renderer']='hyperframes';p['timeline']=[{'id':'a','asset':aid,'start':0,'end':1.2,'text':'فكرة تتحرك','motion':'paper','textY':45,'textStart':.2,'textEnd':1,'mute':False},{'id':'b','asset':aid,'start':0,'end':1.2,'text':'</script><img src=x>','motion':'kinetic','textY':45,'textStart':.2,'textEnd':1,'mute':True}];server.save(p)
                server.export(p['id'],{});e=server.project(p['id'])['exports'][-1];out=Path(e['path'])
                self.assertEqual((e['width'],e['height']),(1080,1920));self.assertAlmostEqual(e['duration'],2.4,delta=.06)
                self.assertEqual(e['engine_version'],hf.VERSION)
                html=(out.parent/'composition/index.html').read_text();self.assertIn('&lt;/script&gt;',html);self.assertNotIn('<img src=x>',html)
                self.assertNotIn('http://',html);self.assertNotIn('https://',html)
                def pixels(time):
                    return subprocess.run(['ffmpeg','-v','error','-ss',str(time),'-i',str(out),'-frames:v','1','-vf','crop=800:180:100:880','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True).stdout
                early,hold,late=pixels(0),pixels(.6),pixels(1.1)
                self.assertGreater(sum(abs(a-b) for a,b in zip(early,hold))/len(hold),20)
                self.assertLess(sum(abs(a-b) for a,b in zip(early,late))/len(late),2)
                pcm=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-vn','-f','s16le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout
                samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
                def rms(a,b):
                    values=samples[int(a*16000):int(b*16000)];return math.sqrt(sum(x*x for x in values)/len(values))/32768
                self.assertGreater(rms(.15,.9),.03);self.assertLess(rms(1.5,2.2),.001)
                self.assertEqual(hashlib.sha256(clip.read_bytes()).hexdigest(),original)
            finally: server.DATA=old

if __name__=='__main__':unittest.main()
