import base64, copy, hashlib, json, math, struct, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import server
import voiceover as vo
import hyperframes_bridge as hf

class VoiceoverTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.old=server.DATA;server.DATA=self.root/'data'
        source=self.root/'source';source.mkdir();self.p=server.create('تعليق تجريبي',str(source))
    def tearDown(self):
        server.DATA=self.old;self.tmp.cleanup()
    def audio(self):
        f=self.root/'تعليق.wav'
        # Real trimmed interval is tone; leading/trailing silence detect wrong trimming.
        server.command(['ffmpeg','-v','error','-f','lavfi','-i',"aevalsrc=if(between(t\\,0.25\\,0.75)\\,0.15*sin(2*PI*660*t)\\,0):s=48000:d=1",'-ac','2','-y',str(f)])
        return f
    def import_audio(self):
        f=self.audio();original=hashlib.sha256(f.read_bytes()).hexdigest()
        asset=vo.import_audio({'audio':base64.b64encode(f.read_bytes()).decode(),'name':'../../تعليق.wav'},server.DATA/self.p['id'],server.FFPROBE,server.FFMPEG,server.command)
        self.assertEqual(hashlib.sha256(f.read_bytes()).hexdigest(),original)
        self.assertEqual(asset['name'],'تعليق.wav');self.assertTrue(Path(asset['path']).is_relative_to(server.DATA/self.p['id']))
        return asset
    def test_validation_and_project_isolation(self):
        a=self.import_audio();self.p['voiceover_assets']=[a]
        v={**vo.DEFAULT,'enabled':True,'asset':a['id'],'trimStart':.25,'trimEnd':.75}
        self.assertEqual(vo.settings(self.p,v)['trimEnd'],.75)
        for change in [{'trimStart':.8},{'trimEnd':2},{'offset':-1},{'gain':2},{'offset':float('nan')},{'originalGain':float('inf')},{'enabled':'yes'},{'asset':'foreign'}]:
            with self.assertRaises(ValueError):vo.settings(self.p,{**v,**change})
        with self.assertRaises(ValueError):vo.settings({'voiceover_assets':[]},v)
        for payload in [{'audio':'invalid','name':'a.wav'},{'audio':base64.b64encode(b'garbage').decode(),'name':'a.wav'},{'audio':base64.b64encode(b'x').decode(),'name':'a.py'}]:
            with self.assertRaises(ValueError):vo.import_audio(payload,server.DATA/self.p['id'],server.FFPROBE,server.FFMPEG,server.command)
        self.assertEqual(len(list((server.DATA/self.p['id']/'voiceovers').iterdir())),1)

    def test_script_uses_saved_identity_without_reanalysis(self):
        self.p['project_memory']['overrides']={'about':'أكاديمية تعليمية'};self.p['voiceover']={**vo.DEFAULT,'voice':'صوت دافئ','direction':'مطمئن'};server.save(self.p)
        with patch.object(server,'ask_agent',return_value={'text':'ابدأ خطوة بخطوة.','direction':'دافئ وهادئ','uncertainties':['العرض بعده يحتاج تأكيد']}) as agent,patch.object(server,'analyze') as analyze:
            server.prepare_voiceover(self.p['id'],'خلّي المبتدئ يتحمّس',{})
        analyze.assert_not_called();args=agent.call_args.args
        self.assertIn('صوت دافئ',args[1]);self.assertEqual(args[3],[])
        saved=server.project(self.p['id']);self.assertEqual(saved['voiceover']['text'],'ابدأ خطوة بخطوة.')
        self.assertEqual(saved['project_memory']['overrides'],{'about':'أكاديمية تعليمية'})
        self.assertFalse(saved['voiceover']['enabled'])

    def render_check(self,engine):
        folder=Path(self.p['source']);clip=folder/'clip.mp4'
        server.command(['ffmpeg','-v','error','-f','lavfi','-i','color=c=navy:s=180x320:r=30:d=2','-f','lavfi','-i','sine=frequency=440:duration=2','-c:v','libx264','-c:a','aac','-shortest','-y',str(clip)])
        before=hashlib.sha256(clip.read_bytes()).hexdigest();a=self.import_audio()
        self.p['assets']=server.scan(folder);self.p['voiceover_assets']=[a]
        self.p['voiceover']={**vo.DEFAULT,'enabled':True,'asset':a['id'],'trimStart':.25,'trimEnd':.75,'offset':.6,'gain':.6,'originalGain':0}
        self.p['renderer']=engine;self.p['timeline']=[{'id':'c','asset':self.p['assets'][0]['id'],'start':0,'end':2,'text':'','mute':engine=='hyperframes'}]
        server.save(self.p);server.export(self.p['id'],{});e=server.project(self.p['id'])['exports'][-1];out=Path(e['path'])
        self.assertAlmostEqual(e['duration'],2,delta=.06);self.assertTrue(server.probe(out)['audio'])
        pcm=subprocess.run(['ffmpeg','-v','error','-i',str(out),'-vn','-f','s16le','-ac','1','-ar','16000','pipe:1'],capture_output=True,check=True).stdout
        samples=struct.unpack('<'+'h'*(len(pcm)//2),pcm)
        def rms(start,end):
            values=samples[int(start*16000):int(end*16000)];return math.sqrt(sum(x*x for x in values)/len(values))/32768
        self.assertLess(rms(.1,.45),.001);self.assertGreater(rms(.7,1),.03);self.assertLess(rms(1.3,1.8),.001)
        self.assertEqual(hashlib.sha256(clip.read_bytes()).hexdigest(),before)
        self.assertEqual(hashlib.sha256((out.parent/'voiceover.wav').read_bytes()).hexdigest(),a['sha256'])
        snapshot=json.loads((out.parent/'voiceover.json').read_text());self.assertEqual(snapshot['settings']['offset'],.6);self.assertFalse(snapshot['truncated'])
    def test_real_basic_export_audio_timing_and_originals(self):self.render_check('basic')
    @unittest.skipUnless(hf.ready(),'local Hyperframes required')
    def test_real_hyperframes_silent_footage_with_voice(self):self.render_check('hyperframes')

    def test_disabled_voice_and_invalid_offset(self):
        with patch.object(server,'command') as command:
            vo.mix_export(self.p,self.root,2,server.FFMPEG,command,{})
        command.assert_not_called()
        a=self.import_audio();self.p['voiceover_assets']=[a];self.p['voiceover']={**vo.DEFAULT,'asset':a['id'],'enabled':True,'trimEnd':1,'offset':3}
        with self.assertRaisesRegex(ValueError,'بعد نهاية'):vo.mix_export(self.p,self.root,2,server.FFMPEG,server.command,{})

if __name__=='__main__':unittest.main()
