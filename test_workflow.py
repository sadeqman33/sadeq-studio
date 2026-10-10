import copy, hashlib, json, tempfile, threading, unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
from unittest.mock import patch
import server, workflow, project_memory as pm

class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.old=server.DATA; server.DATA=self.root/'data'
        source=self.root/'source'; source.mkdir(); clip=source/'clip.mp4'
        server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=160x240:r=30:d=1','-c:v','libx264','-y',str(clip)])
        self.original=hashlib.sha256(clip.read_bytes()).hexdigest()
        self.p=server.create('ترندي',str(source)); self.p['analysis_at']=1
        pm.pin(self.p,{'about':'متجر ترندي','style':'هادئ ودافئ'})
        pm.set_notes(self.p,'لا تستخدم أسعار غير مؤكدة'); server.save(self.p)
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.H)
        self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.client=workflow.StudioClient('http://127.0.0.1:'+str(self.http.server_port))
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join()
        server.DATA=self.old;server.JOBS.pop(self.p['id'],None);self.tmp.cleanup()
    def plan(self):
        aid=self.p['assets'][0]['id'];c=self.client.context(self.p['id'],[aid])
        return {k:c[k] for k in ['project_id','memory_revision','base_fingerprint','selected_assets','asset_fingerprints']} | {'renderer':'basic','reason':'طلب من المحادثة','clips':[{'asset':aid,'start':.1,'end':.8,'text':'اختيارك اليوم','motion':'plain'}]}
    def test_chat_plan_reuses_identity_without_nested_agent_and_real_export(self):
        plan=self.plan();before=copy.deepcopy(server.project(self.p['id'])['project_memory'])
        with patch.object(server,'ask_agent') as agent,patch.object(server,'analyze') as analyze:
            r=self.client.call('/api/agent-plan',plan);server.export(self.p['id'],{})
        agent.assert_not_called();analyze.assert_not_called()
        p=server.project(self.p['id']);self.assertEqual(p['project_memory'],before)
        self.assertEqual(r['clip_count'],1);self.assertEqual(p['draft_origin'],'calling_chat')
        self.assertAlmostEqual(p['exports'][-1]['duration'],.7,delta=.08)
        self.assertEqual(hashlib.sha256(Path(self.p['assets'][0]['path']).read_bytes()).hexdigest(),self.original)
        self.assertTrue(list((server.DATA/self.p['id']/'versions').glob('*.json')))
        self.assertIn('هادئ ودافئ',json.dumps(self.client.context(self.p['id'],[])['identity'],ensure_ascii=False))
    def test_guards_prevent_stale_or_wrong_project_plans(self):
        plan=self.plan();p=server.project(self.p['id']);pm.set_notes(p,'تصحيح جديد');server.save(p)
        with self.assertRaisesRegex(ValueError,'تغيّرت'):self.client.call('/api/agent-plan',plan)
        plan=self.plan();other=server.create('آخر',str(self.root));foreign=self.root/'other.mp4';foreign.write_bytes(Path(self.p['assets'][0]['path']).read_bytes());other['assets']=server.scan(self.root);server.save(other)
        bad=copy.deepcopy(plan);bad['clips'][0]['asset']=other['assets'][0]['id']
        with self.assertRaises(ValueError):self.client.call('/api/agent-plan',bad)
        server.JOBS[self.p['id']]={'running':True}
        with self.assertRaisesRegex(ValueError,'الحالية'):self.client.call('/api/agent-plan',plan)
        server.JOBS.pop(self.p['id']);self.client.call('/api/agent-plan',plan)
        with self.assertRaisesRegex(ValueError,'تغيّرت'):self.client.call('/api/agent-plan',plan)
    def test_uninitialized_duplicate_and_source_change(self):
        plan=self.plan();duplicate=server.create('ترندي ',str(Path(self.p['source'])))
        with self.assertRaisesRegex(ValueError,'مكرر'):self.client.resolve(' ترندي ')
        self.assertEqual(self.client.resolve(self.p['id'])['id'],self.p['id'])
        context=self.client.context(duplicate['id'],[]);self.assertFalse(context['initialized'])
        p=server.project(self.p['id']);p['analysis_at']=None;server.save(p)
        with self.assertRaisesRegex(ValueError,'أول مرة'):self.client.call('/api/agent-plan',plan)
        p['analysis_at']=1;server.save(p);plan=self.plan()
        clip=Path(self.p['assets'][0]['path']);clip.write_bytes(clip.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'اللقطات تغيّرت'):self.client.call('/api/agent-plan',plan)
        self.assertEqual(server.project(self.p['id'])['timeline'],[])

if __name__=='__main__':unittest.main()
