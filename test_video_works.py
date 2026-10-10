import copy, hashlib, json, tempfile, threading, unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
import server, workflow, project_memory as pm, video_works as works

class WorkTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.old=server.DATA;server.DATA=self.root/'data'
        source=self.root/'source';source.mkdir();self.clip=source/'clip.mp4'
        server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=160x240:r=30:d=1','-c:v','libx264','-y',str(self.clip)])
        self.hash=hashlib.sha256(self.clip.read_bytes()).hexdigest();self.p=server.create('مشروع اختبار',str(source));self.p['analysis_at']=1
        pm.pin(self.p,{'about':'هوية مشتركة','purpose':'هدف ثابت'});server.save(self.p)
        self.http=ThreadingHTTPServer(('127.0.0.1',0),server.H);self.thread=threading.Thread(target=self.http.serve_forever,daemon=True);self.thread.start()
        self.c=workflow.StudioClient('http://127.0.0.1:'+str(self.http.server_port))
    def tearDown(self):
        self.http.shutdown();self.http.server_close();self.thread.join();server.DATA=self.old;server.JOBS.pop(self.p['id'],None);self.tmp.cleanup()
    def plan(self,name,text):
        aid=self.p['assets'][0]['id'];ctx=self.c.context(self.p['id'],[aid]);d={k:ctx[k] for k in ['project_id','memory_revision','base_fingerprint','selected_assets','asset_fingerprints']}
        d.update(title=name,renderer='basic',clips=[{'asset':aid,'start':.1,'end':.8,'text':text,'motion':'plain'}]);return self.c.call('/api/agent-plan',d)
    def saved(self):return self.c.call('/api/project/'+self.p['id'])['project']
    def save_edit(self,p,text):
        tl=copy.deepcopy(p['timeline']);tl[0]['text']=text
        return self.c.call('/api/save',{'id':p['id'],'work_id':p['active_work_id'],'work_title':next(w['title'] for w in p['work_list'] if w['active']),'timeline':tl,'renderer':'basic'})
    def test_independent_creation_manual_edits_switch_undo_and_export(self):
        a=self.plan('فيديو أ','نص أ')['work_id'];p=self.save_edit(self.saved(),'نص أ معدل');server.export(p['id'],{})
        first_export=server.project(p['id'])['exports'][-1];self.assertEqual(first_export['work_id'],a)
        export_before=Path(first_export['path']).with_name('edit.json').read_bytes()
        b=self.plan('فيديو ب','نص ب')['work_id'];self.assertNotEqual(a,b)
        with self.assertRaisesRegex(ValueError,'ماكو تعديل'):self.c.call('/api/undo',{'id':p['id']})
        p=self.c.call('/api/work-open',{'id':p['id'],'work_id':a});self.assertEqual(p['timeline'][0]['text'],'نص أ معدل')
        self.assertEqual(p['project_memory']['overrides'],{'about':'هوية مشتركة','purpose':'هدف ثابت'})
        p=self.c.call('/api/undo',{'id':p['id']});self.assertEqual(p['timeline'][0]['text'],'نص أ')
        p=self.c.call('/api/work-open',{'id':p['id'],'work_id':b});self.assertEqual(p['timeline'][0]['text'],'نص ب')
        p=self.save_edit(p,'نص ب معدل');server.export(p['id'],{})
        self.assertEqual(server.project(p['id'])['exports'][-1]['work_id'],b)
        self.assertEqual(Path(first_export['path']).with_name('edit.json').read_bytes(),export_before)
        self.assertEqual(hashlib.sha256(self.clip.read_bytes()).hexdigest(),self.hash)
        p=self.c.call('/api/work-open',{'id':p['id'],'work_id':a});self.assertEqual(p['timeline'][0]['text'],'نص أ')
        self.assertEqual(len(p['work_list']),2)
    def test_migration_preserves_legacy_snapshots_and_current_knowledge(self):
        p=self.p;aid=p['assets'][0]['id'];folder=server.DATA/p['id'];exports=[];before={}
        for i in range(2):
            old=copy.deepcopy(p);old['timeline']=[{'id':str(i),'asset':aid,'start':0,'end':.8,'text':str(i)}];old['draft_reason']='قديم '+str(i)
            path=folder/'exports'/('legacy-'+str(i));path.mkdir(parents=True);server.write(path/'edit.json',old);before[i]=(path/'edit.json').read_bytes()
            exports.append({'version':'legacy-'+str(i),'path':str(path/'final.mp4'),'at':i+1,'duration':.8,'width':720,'height':1280})
        p['exports']=exports;server.save(p);p=server.project(p['id']);self.assertEqual(len(p['video_works']),2)
        self.assertTrue(all(e['work_id'] for e in p['exports']));self.assertEqual(server.project(p['id'])['video_works'],p['video_works'])
        for i,e in enumerate(p['exports']):
            restored=self.c.call('/api/work-open',{'id':p['id'],'work_id':e['work_id']});self.assertEqual(restored['timeline'][0]['text'],str(i))
            self.assertEqual(restored['project_memory']['overrides'],{'about':'هوية مشتركة','purpose':'هدف ثابت'})
            self.assertEqual((folder/'exports'/e['version']/'edit.json').read_bytes(),before[i])
    def test_wrong_work_busy_job_and_stale_switch_do_not_overwrite(self):
        a=self.plan('أ','أ')['work_id'];stale=self.saved();b=self.plan('ب','ب')['work_id']
        with self.assertRaisesRegex(ValueError,'تغيّر'):self.save_edit(stale,'قديم')
        with self.assertRaisesRegex(ValueError,'تغيّرت'):self.c.call('/api/work-open',{'id':self.p['id'],'work_id':a,'base_fingerprint':stale['edit_fingerprint']})
        with self.assertRaises(ValueError):self.c.call('/api/work-open',{'id':self.p['id'],'work_id':'ffffffffffff'})
        other=server.create('آخر',str(self.root));
        with self.assertRaises(ValueError):self.c.call('/api/work-open',{'id':other['id'],'work_id':a})
        server.JOBS[self.p['id']]={'running':True}
        with self.assertRaisesRegex(ValueError,'الحالية'):self.c.call('/api/work-open',{'id':self.p['id'],'work_id':a})
        server.JOBS.pop(self.p['id']);self.assertEqual(self.saved()['active_work_id'],b)
        p=self.c.call('/api/work-new',{'id':self.p['id'],'title':'مسودة فارغة'})
        self.assertEqual(p['timeline'],[]);self.assertFalse(p['voiceover']['enabled']);self.assertEqual(len(p['work_list']),3)

    def test_voice_typography_and_canvas_are_saved_per_video(self):
        a=self.plan('صوت وخط أ','أ')['work_id'];p=server.project(self.p['id'])
        sound=self.root/'voice.wav';server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','sine=frequency=440:duration=1','-y',str(sound)])
        p['voiceover_assets']=[{'id':'voice-test','path':str(sound),'duration':1,'sha256':hashlib.sha256(sound.read_bytes()).hexdigest()}]
        p['voiceover']={**server.vo.DEFAULT,'asset':'voice-test','enabled':True,'trimEnd':.5,'offset':.1,'gain':.4}
        server.save(p)
        b=self.plan('خط ب','ب')['work_id'];p=self.saved()
        self.c.call('/api/save',{'id':p['id'],'work_id':b,'timeline':p['timeline'],'renderer':'hyperframes','ratio':'16:9','typography':{'font':'Hacen Beirut','style':'academy'},'voiceover':{**p['voiceover'],'enabled':False,'gain':.9},'profile_colors':['#001122','#ffffff']})
        p=self.c.call('/api/work-open',{'id':p['id'],'work_id':a})
        self.assertTrue(p['voiceover']['enabled']);self.assertEqual(p['voiceover']['gain'],.4);self.assertEqual(p['ratio'],'9:16');self.assertEqual(p['typography']['style'],'classic')
        p=self.c.call('/api/work-open',{'id':p['id'],'work_id':b})
        self.assertFalse(p['voiceover']['enabled']);self.assertEqual(p['voiceover']['gain'],.9);self.assertEqual(p['ratio'],'16:9');self.assertEqual(p['typography']['style'],'academy');self.assertEqual(p['profile']['colors'],['#001122','#ffffff'])

if __name__=='__main__':unittest.main()
