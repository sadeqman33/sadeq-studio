import copy, hashlib, json, subprocess, tempfile, unittest
from pathlib import Path
import server
import iraqi_review as iq

class MotionTests(unittest.TestCase):
    def test_seek_reentrant_and_validation(self):
        js="""const m=require('./motion.js');const a=m.state(.12,2,'paper');m.state(1.3,2,'paper');if(JSON.stringify(a)!==JSON.stringify(m.state(.12,2,'paper')))throw Error('seek drift');if(m.state(0,2,'paper').opacity!==0||m.state(1,2,'paper').opacity!==1||m.state(2,2,'paper').opacity!==0)throw Error('bad envelope');if(m.mode({motion:'plain'},{motion_style:'paper'})!=='plain'||m.mode({motion:'inherit'},{motion_style:'paper'})!=='paper')throw Error('override');"""
        subprocess.run(['node','-e',js],cwd=server.ROOT,check=True)
        p={'assets':[],'timeline':[],'profile':server.DEFAULT}
        f=iq.fingerprint(p);p['motion_style']='paper';self.assertNotEqual(f,iq.fingerprint(p))
        with self.assertRaisesRegex(ValueError,'حركة'):
            server.validate_timeline(p,[{'motion':'unknown'}])

    def test_real_export_alpha_audio_and_original(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);src=root/'source';src.mkdir();old=server.DATA;server.DATA=root/'data'
            try:
                clip=src/'test.mp4'
                server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=320x240:r=30:d=3','-f','lavfi','-i','sine=frequency=440:duration=3','-c:v','libx264','-c:a','aac','-shortest','-y',str(clip)])
                original=hashlib.sha256(clip.read_bytes()).hexdigest();p=server.create('اختبار الحركة',str(src));asset=p['assets'][0]['id']
                p['motion_style']='paper';p['timeline']=[{'id':'a','asset':asset,'start':0,'end':1.2,'text':'تعلّم بطريقتك','motion':'inherit','mute':False},{'id':'b','asset':asset,'start':1.2,'end':2.4,'text':'فكرتك تتحرك','motion':'kinetic','mute':False}];server.save(p)
                server.export(p['id'],{});e=server.project(p['id'])['exports'][-1];out=Path(e['path']);self.assertAlmostEqual(e['duration'],2.4,delta=.12);self.assertTrue(server.probe(out)['audio'])
                def frame(time):
                    return subprocess.run([server.FFMPEG,'-v','error','-ss',str(time),'-i',str(out),'-frames:v','1','-vf','crop=500:200:70:790','-f','rawvideo','-pix_fmt','rgb24','pipe:1'],capture_output=True,check=True).stdout
                opening,hold=frame(0),frame(.6);self.assertEqual(len(opening),300000);self.assertGreater(sum(abs(x-y) for x,y in zip(opening,hold))/len(hold),15)
                import struct,math
                pcm=subprocess.run([server.FFMPEG,'-v','error','-i',str(out),'-vn','-f','s16le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout
                samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
                self.assertGreater(math.sqrt(sum(x*x for x in samples)/len(samples))/32768,.03)
                self.assertEqual(hashlib.sha256(clip.read_bytes()).hexdigest(),original)
                # Preserve a deliberate local interface demo when requested by the smoke run.
                import os,shutil
                if os.environ.get('SADEQ_MOTION_DEMO'):
                    dest=Path(os.environ['SADEQ_MOTION_DEMO']);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out,dest)
            finally:server.DATA=old

if __name__=='__main__':unittest.main()
