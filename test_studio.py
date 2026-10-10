import copy, hashlib, json, math, struct, subprocess, tempfile, unittest
from pathlib import Path
import server
class StudioTests(unittest.TestCase):
    def test_isolation_validation_export(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); source=root/'source'; source.mkdir(); old=server.DATA; server.DATA=root/'data'
            try:
                clip=source/'clip.mp4'
                server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=320x240:r=30:d=2','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-c:a','aac','-shortest','-y',str(clip)])
                before=hashlib.sha256(clip.read_bytes()).hexdigest()
                a=server.create('واحد',str(source)); b=server.create('اثنين',str(source))
                a['timeline']=[{'id':'cut1','asset':a['assets'][0]['id'],'start':0.2,'end':1.1,'text':'الأكاديمية العراقية','mute':False},{'id':'cut2','asset':a['assets'][0]['id'],'start':1.1,'end':1.9,'text':'تعلّم بطريقتك','mute':True}]
                server.validate_timeline(a,a['timeline']); server.save(a)
                bad=copy.deepcopy(a['timeline']); bad[0]['end']=10
                with self.assertRaises(ValueError): server.validate_timeline(a,bad)
                bad=copy.deepcopy(a['timeline']); bad[0]['asset']='unknown'
                with self.assertRaises(ValueError): server.validate_timeline(a,bad)
                self.assertEqual(server.project(b['id'])['timeline'],[])
                j={}; server.export(a['id'],j); result=server.project(a['id'])['exports'][-1]
                self.assertAlmostEqual(result['duration'],1.7,delta=.15)
                self.assertTrue(server.probe(Path(result['path']))['audio'])
                pcm=subprocess.run([server.FFMPEG,'-v','error','-ss','1.15','-t','0.3','-i',result['path'],'-vn','-f','s16le','-ac','1','-ar','48000','pipe:1'],capture_output=True,check=True).stdout
                values=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
                self.assertLess(math.sqrt(sum(x*x for x in values)/len(values))/32768,0.0001)
                self.assertEqual(hashlib.sha256(clip.read_bytes()).hexdigest(),before)
                print('export',result['duration'],result['width'],result['height'],'original unchanged')
            finally: server.DATA=old
if __name__=='__main__':unittest.main()
