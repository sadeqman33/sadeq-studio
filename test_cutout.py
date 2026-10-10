import copy,hashlib,json,math,os,struct,subprocess,tempfile,threading,unittest
from pathlib import Path
from unittest.mock import patch
from http.server import ThreadingHTTPServer
import cutout as co,server,workflow

class CutoutTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.old=server.DATA;server.DATA=self.root/'data';src=self.root/'source';src.mkdir();self.source=src/'selfie.mp4';self.source.write_bytes(b'original source')
        self.p=server.create('اختبار العزل',str(src));self.a=self.p['assets'][0]
        self.p['timeline']=[{'id':'first','asset':self.a['id'],'start':1.,'end':2.,'text':'نص','motion':'pop','textY':45,'textStart':.1,'textEnd':.8,'mute':False}];server.save(self.p)
        self.payload={'work_id':self.p['active_work_id'],'base_fingerprint':server.edit_fingerprint(self.p),'clip_id':'first','mode':'color','color':'#112233'}
    def tearDown(self):server.DATA=self.old;self.temp.cleanup()
    def fake_process(self,a,start,end,out,*args):out.mkdir(parents=True);f=out/'processed.mp4';f.write_bytes(b'derivative');return f,{'duration':end-start,'width':480,'height':640,'audio':True,'hdr':False}
    def test_guard_rejects_wrong_work_stale_edit_invalid_mode_without_writing(self):
        before=(server.DATA/self.p['id']/'project.json').read_bytes()
        with patch.object(co,'ready',return_value=True):
            for change in [{'work_id':'0'*12},{'base_fingerprint':'stale'},{'clip_id':'missing'},{'mode':'unknown'},{'color':'red;run'}]:
                with self.subTest(change=change),self.assertRaises(ValueError):server.prepare_cutout(self.p,{**self.payload,**change})
        self.assertEqual(before,(server.DATA/self.p['id']/'project.json').read_bytes())
    def test_non_destructive_work_scoped_derivative_undo_and_rescan(self):
        original=self.source.read_bytes();memory=copy.deepcopy(self.p['project_memory']);project=self.p['id']
        http=ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();client=workflow.StudioClient('http://127.0.0.1:'+str(http.server_port))
        try:
            with patch.object(co,'ready',return_value=True),patch.object(co,'process',side_effect=self.fake_process),patch.object(server,'probe',return_value={'duration':5,'width':480,'height':640,'audio':True,'hdr':False}):
                spec=server.prepare_cutout(self.p,self.payload);server.apply_cutout(project,spec,{})
                updated=server.project(project);clip=updated['timeline'][0];derived=next(a for a in updated['assets'] if a['id']==clip['asset'])
                self.assertTrue(derived['derived']);self.assertEqual(derived['derived_from'],self.a['id']);self.assertEqual((derived['source_start'],derived['source_end']),(1,2));self.assertEqual((clip['start'],clip['end']),(0,1));self.assertEqual(clip['textStart'],.1);self.assertEqual(clip['textEnd'],.8);self.assertEqual(clip['motion'],'pop');self.assertEqual(updated['active_work_id'],self.payload['work_id']);self.assertEqual(updated['project_memory'],memory)
                scanned=client.call('/api/rescan',{'id':project});self.assertIn(derived['id'],[a['id'] for a in scanned['assets']]);self.assertEqual(scanned['timeline'][0]['asset'],derived['id'])
                # Rescan checkpoints do not change the edit; work undo recovers source cuts.
                undone=client.call('/api/undo',{'id':project});self.assertEqual(undone['timeline'],self.p['timeline'])
            self.assertEqual(self.source.read_bytes(),original)
        finally:http.shutdown();http.server_close();thread.join()
    def test_source_change_during_processing_never_replaces_a_timeline(self):
        before=copy.deepcopy(self.p['timeline'])
        def changed(*args):result=self.fake_process(*args);self.source.write_bytes(b'changed source content');return result
        with patch.object(co,'ready',return_value=True),patch.object(co,'process',side_effect=changed):
            spec=server.prepare_cutout(self.p,self.payload)
            with self.assertRaisesRegex(ValueError,'تغيّرت'):server.apply_cutout(self.p['id'],spec,{})
        self.assertEqual(server.project(self.p['id'])['timeline'],before)
    def test_error_leaves_source_timeline_and_memory_unchanged(self):
        before=(server.DATA/self.p['id']/'project.json').read_bytes();original=self.source.read_bytes()
        with patch.object(co,'ready',return_value=True),patch.object(co,'process',side_effect=ValueError('No person detected')):
            spec=server.prepare_cutout(self.p,self.payload)
            with self.assertRaisesRegex(ValueError,'No person'):server.apply_cutout(self.p['id'],spec,{})
        self.assertEqual(before,(server.DATA/self.p['id']/'project.json').read_bytes());self.assertEqual(original,self.source.read_bytes())

@unittest.skipUnless(co.ready() and os.environ.get('SADEQ_CUTOUT_TEST_IMAGE'),'local cutout runtime and an explicitly supplied test portrait required')
class RealCutoutTests(unittest.TestCase):
    def test_real_color_and_blur_inference_keep_audio_duration_source_and_silent_video(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'person.mp4';image=os.environ['SADEQ_CUTOUT_TEST_IMAGE']
            server.command(['ffmpeg','-v','error','-loop','1','-i',image,'-f','lavfi','-i','sine=frequency=880:duration=1','-t','1','-vf','scale=320:-2,setsar=1','-c:v','libx264','-c:a','aac','-pix_fmt','yuv420p','-shortest','-y',str(source)])
            original=hashlib.sha256(source.read_bytes()).hexdigest();asset={'path':str(source)}
            out,meta=co.process(asset,.1,.7,root/'color','color','#112233',server.probe,server.FFMPEG,{})
            self.assertAlmostEqual(meta['duration'],.6,delta=.04);self.assertTrue(meta['audio']);self.assertLessEqual(meta['width'],720);self.assertLessEqual(meta['height'],1280)
            raw=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True).stdout
            self.assertLess(sum(abs(a-b) for a,b in zip(raw[:3],[17,34,51])),18)
            pcm=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-vn','-ac','1','-ar','16000','-f','s16le','pipe:1'],capture_output=True,check=True).stdout;samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm);self.assertGreater(math.sqrt(sum(s*s for s in samples)/len(samples))/32768,.03)
            result=json.loads(out.with_name('result.json').read_text());self.assertGreater(result['foreground_range'][1],.05);self.assertEqual(result['frames'],18)
            silent=root/'silent.mp4';server.command(['ffmpeg','-v','error','-i',str(source),'-an','-c:v','copy','-y',str(silent)])
            blurred,meta=co.process({'path':str(silent)},0,.3,root/'blur','blur','#112233',server.probe,server.FFMPEG,{})
            self.assertFalse(meta['audio']);self.assertAlmostEqual(meta['duration'],.3,delta=.04);self.assertGreater(blurred.stat().st_size,1000)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),original)
if __name__=='__main__':unittest.main()
