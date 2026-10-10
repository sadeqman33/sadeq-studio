import copy, hashlib, json, math, struct, subprocess, tempfile, threading, unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import server, remotion_bridge as rm, workflow

class RemotionTests(unittest.TestCase):
    def test_cumulative_frame_boundaries_and_minimum_clip(self):
        p={'ratio':'16:9','timeline':[{'start':0,'end':.35,'text':'نص'} for _ in range(10)]}
        props=rm.frame_plan(p)
        self.assertEqual(props['durationInFrames'],105)
        self.assertEqual((props['width'],props['height']),(1920,1080))
        self.assertEqual(sum(c['frames'] for c in props['clips']),105)
        for a,b in zip(props['clips'],props['clips'][1:]):self.assertEqual(a['from']+a['frames'],b['from'])
        with self.assertRaises(ValueError):rm.frame_plan({'timeline':[{'start':0,'end':.001}]})

    def test_unavailable_renderer_does_not_change_edit(self):
        p={'timeline':[{'start':0,'end':1,'text':'مسودة'}]};before=copy.deepcopy(p)
        with tempfile.TemporaryDirectory() as t,patch.object(rm,'ready',return_value=False):
            with self.assertRaisesRegex(ValueError,'إعداد'):rm.prepare(p,Path(t),None,None,None,{})
        self.assertEqual(p,before)

    def test_agent_plan_and_manual_save_keep_selected_renderer(self):
        with tempfile.TemporaryDirectory() as t:
            old=server.DATA;server.DATA=Path(t)/'data';src=Path(t)/'source';src.mkdir();(src/'x.mp4').touch()
            http=ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                p=server.create('اختبار الربط',str(src));p['analysis_at']=1;server.save(p)
                client=workflow.StudioClient('http://127.0.0.1:'+str(http.server_port));aid=p['assets'][0]['id'];ctx=client.context(p['id'],[aid])
                plan={k:ctx[k] for k in ['project_id','memory_revision','base_fingerprint','selected_assets','asset_fingerprints']}
                plan.update(renderer='remotion',clips=[{'asset':aid,'start':0,'end':1,'text':'نص','textStart':.1,'textEnd':.8}])
                with patch.object(rm,'ready',return_value=False):
                    with self.assertRaisesRegex(ValueError,'Remotion'):client.call('/api/agent-plan',plan)
                self.assertEqual(server.project(p['id'])['timeline'],[])
                with patch.object(rm,'ready',return_value=True),patch.object(server,'probe',return_value={'duration':2}):
                    reply=client.call('/api/agent-plan',plan);saved=server.project(p['id'])
                    edit=client.call('/api/save',{'id':p['id'],'work_id':reply['work_id'],'timeline':saved['timeline'],'renderer':'remotion','typography':{'font':'Hacen Beirut','style':'academy'}})
                self.assertEqual(edit['renderer'],'remotion');self.assertEqual(edit['active_work_id'],reply['work_id'])
            finally:http.shutdown();http.server_close();thread.join();server.DATA=old

    @unittest.skipUnless(rm.ready(),'local Remotion dependencies required')
    def test_real_remotion_export_keeps_arabic_timing_audio_work_and_sources(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'source';src.mkdir();old=server.DATA;server.DATA=root/'data'
            try:
                source=src/'tone.mp4'
                server.command(['ffmpeg','-v','error','-f','lavfi','-i','color=c=navy:s=180x320:r=30:d=2','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-c:a','aac','-shortest','-y',str(source)])
                original=hashlib.sha256(source.read_bytes()).hexdigest();p=server.create('تجربة Remotion',str(src));aid=p['assets'][0]['id']
                p['renderer']='remotion';p['timeline']=[{'id':'a','asset':aid,'start':.1,'end':.9,'text':'فكرة تتحرك','motion':'plain','textY':45,'textStart':.1,'textEnd':.65,'mute':False},
                    {'id':'b','asset':aid,'start':.4,'end':1.2,'text':'</script><img src=x>','motion':'paper','textY':45,'textStart':.1,'textEnd':.65,'mute':True}]
                server.save(p);work=p['active_work_id'];server.export(p['id'],{})
                e=server.project(p['id'])['exports'][-1];out=Path(e['path'])
                self.assertEqual(e['engine'],'remotion');self.assertEqual(e['engine_version'],rm.VERSION);self.assertEqual(e['work_id'],work)
                self.assertEqual((e['width'],e['height']),(1080,1920));self.assertAlmostEqual(e['duration'],1.6,delta=.07)
                props=json.loads((out.parent/'remotion/props.json').read_text());self.assertEqual(props['clips'][1]['text'],'</script><img src=x>')
                self.assertEqual(json.loads(out.with_name('edit.json').read_text())['timeline'],p['timeline'])
                def pixels(time):return subprocess.run(['ffmpeg','-v','error','-ss',str(time),'-i',str(out),'-frames:v','1','-vf','crop=800:180:100:880','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True).stdout
                early,hold,late=pixels(0),pixels(.45),pixels(.75)
                self.assertGreater(sum(abs(a-b) for a,b in zip(early,hold))/len(hold),10)
                self.assertLess(sum(abs(a-b) for a,b in zip(early,late))/len(late),2)
                pcm=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-vn','-f','s16le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout
                samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
                def rms(a,b):
                    values=samples[int(a*16000):int(b*16000)];return math.sqrt(sum(x*x for x in values)/len(values))/32768
                self.assertGreater(rms(.15,.6),.03);self.assertLess(rms(1,1.5),.001)
                self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
            finally:server.DATA=old

if __name__=='__main__':unittest.main()
