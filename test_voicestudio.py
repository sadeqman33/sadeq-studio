import base64, copy, json, os, tempfile, threading, unittest, urllib.error, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
import server, voiceover as vo, voicestudio_bridge as vs
from test_voiceover import VoiceoverTests

class BridgeTests(unittest.TestCase):
 def test_loopback_only(self):
  for url in ['https://example.com','http://127.0.0.1.evil.com:3900','http://user:pass@localhost:3900','http://localhost:3900/path','http://localhost:3900?x=1']:
   with patch.dict(os.environ,{'SADEQ_VOICESTUDIO_URL':url}),self.assertRaises(ValueError):vs.endpoint()
 def test_missing_or_wrong_model_never_generates(self):
  with patch.object(vs,'status',return_value={'ready':False,'message':'موديل ناقص'}),patch.object(vs,'request') as request:
   with self.assertRaisesRegex(ValueError,'ناقص'):vs.generate('مرحبا')
   request.assert_not_called()
 def test_voice_validation_and_payload(self):
  state={'ready':True,'voices':[{'id':'default'}]}
  with patch.object(vs,'status',return_value=state),patch.object(vs,'request',return_value=b'RIFFxxxxWAVEaudio') as request:
   with self.assertRaises(ValueError):vs.generate('مرحبا','foreign')
   payload,provenance=vs.generate('مرحبا','default','هادئ')
   request.assert_called_once();self.assertEqual(request.call_args.args[1]['language'],'ar');self.assertEqual(provenance['model'],vs.MODEL)
   self.assertTrue(payload['audio'])
 def test_readiness_and_profile_inventory(self):
  values={'/health':{'version':'0.5.7'},'/v1/audio/voices':{'voices':[{'voice_id':'x','name':'صوتي','type':'profile'},{'voice_id':'alloy','type':'openai_alias'}]},'/engines/tts':{'active':vs.ENGINE,'active_model':vs.MODEL,'backends':[{'id':vs.ENGINE,'available':True}]},'/models':{'models':[{'repo_id':vs.MODEL,'installed':True}]}}
  with patch.object(vs,'request',side_effect=lambda path:values[path]):
   self.assertTrue(vs.status()['ready']);self.assertEqual([v['id'] for v in vs.status()['voices']],['default','x'])
   values['/engines/tts']['active_model']='other';self.assertFalse(vs.status()['ready'])
 def test_http_audio_errors_and_no_redirect(self):
  class H(BaseHTTPRequestHandler):
   def log_message(self,*a):pass
   def do_GET(self):
    if self.path=='/redirect':self.send_response(302);self.send_header('Location','http://example.com');self.end_headers()
    elif self.path=='/denied':self.send_response(401);self.end_headers()
    else:self.send_response(200);self.end_headers();self.wfile.write(b'{"error":"not audio"}')
  http=ThreadingHTTPServer(('127.0.0.1',0),H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
  try:
   with patch.dict(os.environ,{'SADEQ_VOICESTUDIO_URL':f'http://127.0.0.1:{http.server_port}'}):
    for path in ['/redirect','/denied','/invalid']:
     with self.assertRaises(ValueError):vs.request(path,audio=True)
  finally:http.shutdown();http.server_close();thread.join()

class GenerationTests(VoiceoverTests):
 # Reuse only isolated setup/audio helpers, not unrelated render cases.
 test_validation_and_project_isolation=None
 test_script_uses_saved_identity_without_reanalysis=None
 test_real_basic_export_audio_timing_and_originals=None
 test_real_hyperframes_silent_footage_with_voice=None
 test_disabled_voice_and_invalid_offset=None
 def spec(self):
  p=server.project(self.p['id']);return {'work_id':p.get('active_work_id'),'base_fingerprint':server.edit_fingerprint(p),'text':'مرحبا','direction':'هادئ','voice':'default'}
 def generated(self):
  return {'audio':base64.b64encode(self.audio().read_bytes()).decode(),'name':'VoiceStudio.wav'}, {'model':vs.MODEL,'provider':'VoiceStudio'}
 def test_generation_preserves_existing_audio_and_settings(self):
  a=self.import_audio();self.p['voiceover_assets']=[a];self.p['voiceover']={**vo.DEFAULT,'asset':a['id'],'trimEnd':1,'enabled':True,'offset':.4,'gain':.6,'originalGain':.7};server.save(self.p)
  spec=self.spec()
  with patch.object(vs,'generate',return_value=self.generated()):server.generate_voiceover(self.p['id'],spec,{})
  p=server.project(self.p['id']);self.assertEqual(len(p['voiceover_assets']),2);self.assertTrue(Path(a['path']).is_file())
  self.assertEqual(p['voiceover']['offset'],.4);self.assertEqual(p['voiceover']['originalGain'],.7);self.assertEqual(p['voiceover']['gain'],.6)
  self.assertEqual(p['voiceover_assets'][-1]['provider_hint'],'voicestudio')
 def test_generation_failure_preserves_draft(self):
  before=copy.deepcopy(server.project(self.p['id']))
  with patch.object(vs,'generate',side_effect=ValueError('failed')),self.assertRaises(ValueError):server.generate_voiceover(self.p['id'],self.spec(),{})
  self.assertEqual(server.project(self.p['id']),before)
 def test_changed_work_does_not_attach_recording(self):
  spec=self.spec();spec['work_id']='different';j={}
  with patch.object(vs,'generate',return_value=self.generated()),self.assertRaisesRegex(ValueError,'تغيّرت'):server.generate_voiceover(self.p['id'],spec,j)
  self.assertTrue(Path(j['generated_path']).is_file());self.assertFalse(server.project(self.p['id']).get('voiceover_assets'))

class RouteTests(unittest.TestCase):
 def test_generate_requires_fresh_work_and_explicit_text(self):
  import workflow
  with tempfile.TemporaryDirectory() as folder:
   old=server.DATA;server.DATA=Path(folder)/'data';source=Path(folder)/'source';source.mkdir();p=server.create('اختبار الربط',str(source));p['voiceover']={**vo.DEFAULT,'text':'مرحبا'};server.save(p)
   http=ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start();client=workflow.StudioClient('http://127.0.0.1:'+str(http.server_port))
   try:
    data={'id':p['id'],'work_id':p.get('active_work_id'),'base_fingerprint':server.edit_fingerprint(server.project(p['id']))}
    with patch.object(server,'run_job',return_value={'running':True}) as job:
     with self.assertRaises(ValueError):client.call('/api/voiceover-generate',{**data,'work_id':'foreign'})
     job.assert_not_called()
     with self.assertRaises(ValueError):client.call('/api/voiceover-generate',{**data,'base_fingerprint':'stale'})
     job.assert_not_called();client.call('/api/voiceover-generate',data);job.assert_called_once()
   finally:http.shutdown();http.server_close();thread.join();server.DATA=old

if __name__=='__main__':unittest.main()
