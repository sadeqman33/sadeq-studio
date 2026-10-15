import copy, hashlib, json, unittest
from pathlib import Path
from unittest.mock import patch
import creation, server, video_library as vl, video_works as works
from test_workflow import WorkflowTests

class CreationTests(unittest.TestCase):
    setUp=WorkflowTests.setUp
    tearDown=WorkflowTests.tearDown
    def request(self,**opts):
        p=server.project(self.p['id'])
        return {'id':p['id'],'work_id':p.get('active_work_id'),'base_fingerprint':server.edit_fingerprint(p),'assets':[p['assets'][0]['id']],'request':'اعرض تفاصيل المنتج','settings':{**creation.DEFAULTS,'captions':'off','output':'draft',**opts}}
    def result(self,**changes):
        c={'asset':self.p['assets'][0]['id'],'start':0,'end':1,'text':'تفاصيل تفرق','motion':'plain','textY':64,'textStart':.3,'textEnd':.6,'icon':''};c.update(changes)
        return {'reason':'تسلسل بسيط من المقطع المختار','clips':[c]}
    def test_strict_options_stale_guard_and_busy(self):
        for bad in [{'fps':True},{'fps':24},{'features':'yes'},{'camera':'orbit'},{'captions':'invented'}]:
            with self.assertRaises(ValueError):creation.settings(bad)
        d=self.request();d['base_fingerprint']='old'
        with self.assertRaisesRegex(ValueError,'تغيّر'):creation.prepare(server.project(self.p['id']),d)
        d=self.request();d['assets']*=2
        with self.assertRaises(ValueError):creation.prepare(server.project(self.p['id']),d)
        d=self.request();server.JOBS[self.p['id']]={'running':True}
        with patch.object(creation,'run') as run:
            with self.assertRaisesRegex(ValueError,'يشتغل'):self.client.call('/api/create-video',d)
            run.assert_not_called()
    def test_captions_clean_group_suppress_and_icon_spacing(self):
        p=server.project(self.p['id']);a=p['assets'][0];a.update(server.probe(Path(a['path'])));a['audio']=True
        p['video_analyses'][a['id']]={'fingerprint':vl.fingerprint(a),'transcript':{'status':'transcribed','segments':[{'start':0,'end':1,'words':[{'start':0,'end':.2,'text':'هاي،'},{'start':.2,'end':.45,'text':'تفاصيل.'},{'start':.65,'end':.8,'text':'حلوة!'},{'start':.8,'end':1,'text':'كلش؟'}]}]}}
        p['overlay_assets']=[{'id':'abc123','name':'تفاصيل','kind':'icon'}]
        result=creation.assemble(p,self.result(icon='abc123'),creation.settings({}),[a['id']])
        caps=[l for l in result['layers'] if l.get('track')=='caption'];feature=next(l for l in result['layers'] if l.get('track')=='title');icon=next(l for l in result['layers'] if l['type']=='icon')
        self.assertEqual([l['text'] for l in caps],['هاي تفاصيل','حلوة كلش'])
        self.assertTrue(all(l['end']<=.3 or l['start']>=.6 for l in caps));self.assertEqual(icon['y'],feature['y'])
        self.assertEqual(icon['x']-icon['width']/2-(feature['x']+feature['width']/2),1)
        self.assertEqual(result['timeline'][0]['text'],'');self.assertFalse(result['voiceover']['enabled'])
        with self.assertRaisesRegex(ValueError,'أيقونة'):creation.assemble(p,self.result(icon='foreign'),creation.settings({}),[a['id']])
    def test_new_work_preserves_old_and_real_renderer(self):
        p=server.project(self.p['id']);aid=p['assets'][0]['id'];p['timeline']=[{'id':'aaaabbbb','asset':aid,'start':0,'end':.5,'text':'أصلي','mute':False}];p['layers']=[];server.save(p)
        oldid=p['active_work_id'];oldpath=works.snapshot(server.DATA/p['id'],oldid);oldbytes=oldpath.read_bytes()
        spec=creation.prepare(server.project(p['id']),self.request(resolution='1080',fps=30));calls=[]
        with patch.object(server,'analyze_one',side_effect=lambda pid,a,j:calls.append(a['id'])),patch.object(server,'learn_memory'),patch.object(server,'draft_context',return_value=('',[],[])),patch.object(server,'ask_agent',return_value=self.result()) as agent:
            j={};creation.run(p['id'],spec,j)
        now=server.project(p['id']);self.assertEqual(calls,[aid]);self.assertEqual(oldpath.read_bytes(),oldbytes);self.assertNotEqual(oldid,now['active_work_id']);self.assertEqual(now['draft_origin'],'studio_agent');self.assertEqual(j['stage'],'done');agent.assert_called_once()
        self.assertEqual(now['creation_settings']['output'],'draft')
        server.export(p['id'],{})
        now=server.project(p['id']);self.assertTrue(now['exports']);self.assertEqual(hashlib.sha256(Path(p['assets'][0]['path']).read_bytes()).hexdigest(),self.original)
    def test_bad_plan_does_not_create_work(self):
        p=server.project(self.p['id']);before=copy.deepcopy(p)
        with patch.object(server,'analyze_one'),patch.object(server,'learn_memory'),patch.object(server,'draft_context',return_value=('',[],[])),patch.object(server,'ask_agent',return_value=self.result(asset='foreign')):
            with self.assertRaises(ValueError):creation.run(p['id'],creation.prepare(p,self.request()),{})
        now=server.project(p['id']);self.assertEqual(now.get('active_work_id'),before.get('active_work_id'));self.assertEqual(now['timeline'],before['timeline'])

if __name__=='__main__':unittest.main()
