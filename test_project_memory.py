import copy, json, tempfile, threading, unittest, urllib.request
from pathlib import Path
from unittest.mock import patch
import server, project_memory as pm, video_library as vl

def learned(**fields):
    return {**{k:'' for k in pm.FIELDS},'evidence':['brief.md'],'uncertainties':[],**fields}

class MemoryTests(unittest.TestCase):
    def test_api_save_and_timeline_undo_do_not_erase_identity(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); doc=root/'brief.md';doc.write_text('reference');old=server.DATA;server.DATA=root/'data'
            http=server.ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
            try:
                p=server.create('Academy',str(doc));p['profile']['summary']='Latest learned identity';p['analysis_at']=1;pm.learn(p,learned(about='Education',purpose='Initial purpose'),'seed');server.save(p)
                def post(path,data):
                    request=urllib.request.Request(f'http://127.0.0.1:{http.server_port}'+path,data=json.dumps({'id':p['id'],**data}).encode(),headers={'Content-Type':'application/json'})
                    return json.load(urllib.request.urlopen(request))
                post('/api/memory-save',{'memory_overrides':{'purpose':'تعليم أصحاب المتاجر','style':'نص قصير'}})
                stale=copy.deepcopy(server.DEFAULT);stale['summary']='old browser identity'
                post('/api/save',{'timeline':[],'profile':stale,'ratio':'9:16'})
                restored=post('/api/undo',{})
                self.assertEqual(restored['profile']['summary'],'Latest learned identity')
                self.assertEqual(restored['memory_view']['identity']['purpose'],'تعليم أصحاب المتاجر')
                self.assertEqual(restored['analysis_at'],1)
                self.assertEqual(server.project(p['id'])['project_memory']['overrides']['style'],'نص قصير')
            finally:
                http.shutdown();http.server_close();thread.join();server.DATA=old

    def test_user_direction_survives_learning_and_isolation(self):
        p={'id':'123456abcdef','name':'Academy','profile':copy.deepcopy(server.DEFAULT),'analysis_at':1}
        pm.learn(p,learned(about='دورات ذكاء اصطناعي',purpose='هدف مستنتج',style='ستايل مرجعي'),'a')
        pm.pin(p,{'purpose':'تعليم أصحاب المتاجر صناعة المحتوى','style':'خلفية خمرية ونصوص قصيرة'})
        pm.learn(p,learned(purpose='تغيير من النموذج',style='لون آخر'),'b')
        self.assertEqual(pm.effective(p)['purpose'],'تعليم أصحاب المتاجر صناعة المحتوى')
        self.assertEqual(pm.effective(p)['style'],'خلفية خمرية ونصوص قصيرة')
        p.update(assets=[],timeline=[])
        before=server.iq.fingerprint(p);pm.pin(p,{'purpose':'هدف جديد'})
        self.assertNotEqual(server.iq.fingerprint(p),before)
        other={'id':'abcdef123456','name':'Farm','profile':copy.deepcopy(server.DEFAULT)}
        self.assertNotIn('تعليم أصحاب المتاجر',pm.wrap(other,'make video'))
        with self.assertRaises(ValueError): pm.pin(p,{'foreign':'x'})

    def test_every_agent_receives_persisted_memory(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); doc=root/'brief.md'; doc.write_text('Academy reference'); old=server.DATA; server.DATA=root/'data'
            try:
                p=server.create('Academy',str(doc)); pm.pin(p,{'purpose':'تعليم صناعة المحتوى','offers':'دورات تطبيقية'}); server.save(p)
                captured=[]
                class Process:
                    returncode=0
                    def communicate(self,prompt,timeout):
                        captured.append(prompt); server.write(server.DATA/p['id']/'agent/result.json',{'ok':True})
                with patch.object(server,'CODEX','mock-codex'),patch.object(server.subprocess,'Popen',return_value=Process()):
                    server.ask_agent(p['id'],'Make a new video',{'type':'object'},[],{})
                self.assertIn('تعليم صناعة المحتوى',captured[0]); self.assertIn('user_pinned_fields',captured[0])
                self.assertIn('Do not re-learn the project',captured[0]); self.assertIn(p['id'],captured[0])
                self.assertEqual(server.read(server.DATA/p['id']/'memory.json')['effective']['offers'],'دورات تطبيقية')
            finally: server.DATA=old

    def test_repeat_draft_uses_memory_without_project_reanalysis(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); src=root/'source';src.mkdir();old=server.DATA;server.DATA=root/'data'
            try:
                clip=src/'clip.mp4';server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=160x120:d=1','-c:v','libx264','-y',str(clip)])
                p=server.create('Academy',str(src));a=p['assets'][0];a.update(server.probe(clip));folder=server.DATA/p['id']/'cached';folder.mkdir(parents=True)
                record={'asset':a['id'],'name':a['name'],'fingerprint':vl.fingerprint(a),'status':'complete','folder':str(folder),'analysis':{'summary':'saved footage'},'transcript':{'status':'no_audio','segments':[]}}
                p['video_analyses']={a['id']:record};p['analysis_at']=1;pm.learn(p,learned(purpose='تعليم عملي'),'seed');pm.pin(p,{'style':'خلفية خمرية'});server.save(p)
                memory_before=copy.deepcopy(server.project(p['id'])['project_memory']);calls=[]
                def agent(pid,prompt,schema,frames,j):
                    calls.append(schema);self.assertEqual(schema,server.PLAN_SCHEMA)
                    return {'reason':'Uses saved identity','clips':[{'asset':a['id'],'start':0,'end':.8,'text':'تعلّم'}]}
                with patch.object(server,'ask_agent',side_effect=agent),patch.object(server,'analyze_one',side_effect=AssertionError('old video reanalysis')),patch.object(server,'learn_memory',side_effect=AssertionError('project relearning')),patch.object(server,'doc_text',side_effect=AssertionError('document reread')):
                    server.draft(p['id'],'new video',{},[a['id']]);server.draft(p['id'],'another video',{},[a['id']])
                self.assertEqual(len(calls),2);saved=server.project(p['id']);self.assertEqual(saved['project_memory'],memory_before);self.assertEqual(saved['draft_memory_revision'],memory_before['revision'])
            finally: server.DATA=old

if __name__=='__main__': unittest.main()
