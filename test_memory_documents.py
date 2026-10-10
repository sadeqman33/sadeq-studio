import copy,json,tempfile,threading,unittest,urllib.request
from pathlib import Path
from unittest.mock import patch
import server,project_memory as pm,memory_documents as md,video_library as vl
from test_project_memory import learned

class MarkdownMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.old=server.DATA;server.DATA=self.root/'data'
        doc=self.root/'brief.md';doc.write_text('original reference');self.doc=doc
        self.p=server.create('الأكاديمية',str(doc));pm.learn(self.p,learned(about='تعليم',purpose='هدف من التحليل',style='نص قليل'),'seed');server.save(self.p)
        self.folder=server.DATA/self.p['id']
    def tearDown(self): server.DATA=self.old;self.temp.cleanup()
    def edit(self,name,key,value):
        file=self.folder/name;text=file.read_text();file.write_text(md.marker(key).sub(lambda _:md.block(key,value),text))
    def test_markdown_roundtrip_pins_notes_backups_and_isolation(self):
        self.assertEqual(set(x.name for x in self.folder.glob('*.md')),set(md.FILES))
        self.edit('PROJECT.md','purpose','تعليم أصحاب المتاجر');self.edit('LEARNINGS.md','notes','خفف الحركة وخلي وقت للقراءة')
        p=server.project(self.p['id']);self.assertEqual(pm.effective(p)['purpose'],'تعليم أصحاب المتاجر');self.assertIn('وقت للقراءة',pm.wrap(p,'new video'))
        pm.learn(p,learned(purpose='اقتراح آخر',style='تحديث'),'new');server.save(p)
        self.assertEqual(md.parse('PROJECT.md',(self.folder/'PROJECT.md').read_text())['purpose'],'تعليم أصحاب المتاجر')
        self.assertTrue(list((self.folder/'memory-history').glob('*/PROJECT.md')))
        times={n:(self.folder/n).stat().st_mtime_ns for n in md.FILES};before=copy.deepcopy(server.project(p['id'])['project_memory'])
        server.save(server.project(p['id']));self.assertEqual(before,server.project(p['id'])['project_memory']);self.assertEqual(times,{n:(self.folder/n).stat().st_mtime_ns for n in md.FILES})
        other=server.create('مزرعة',str(self.doc));self.assertNotIn('أصحاب المتاجر',pm.wrap(other,'new video'));self.assertNotIn('وقت للقراءة',pm.wrap(other,'new video'));self.assertEqual(self.doc.read_text(),'original reference')
    def test_malformed_file_preserves_all_pending_edits(self):
        file=self.folder/'STYLE.md';valid=file.read_text();file.write_text(valid.replace('<!-- /sadeq:style -->','missing marker'))
        self.edit('PROJECT.md','offers','دورة تطبيقية');pending=(self.folder/'PROJECT.md').read_text()
        p=server.project(self.p['id']);self.assertTrue(p['memory_document_warnings']);server.save(p)
        self.assertEqual(file.read_text(),valid.replace('<!-- /sadeq:style -->','missing marker'));self.assertEqual((self.folder/'PROJECT.md').read_text(),pending)
        file.write_text(valid);p=server.project(p['id']);self.assertFalse(p.get('memory_document_warnings'));self.assertEqual(pm.effective(p)['offers'],'دورة تطبيقية')
    def test_api_conflict_and_stale_timeline_do_not_erase_external_edit(self):
        http=server.ThreadingHTTPServer(('127.0.0.1',0),server.H);thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
        def post(path,data):
            req=urllib.request.Request(f'http://127.0.0.1:{http.server_port}'+path,data=json.dumps({'id':self.p['id'],**data}).encode(),headers={'Content-Type':'application/json'})
            return json.load(urllib.request.urlopen(req))
        try:
            old_revision=pm.memory(self.p)['revision'];self.edit('PROJECT.md','purpose','هدف من تعديل الملف')
            post('/api/save',{'timeline':[],'ratio':'9:16','memory_overrides':{}})
            self.assertEqual(pm.effective(server.project(self.p['id']))['purpose'],'هدف من تعديل الملف')
            with self.assertRaises(urllib.error.HTTPError):post('/api/memory-save',{'memory_revision':old_revision,'memory_overrides':{'purpose':'نسخة قديمة'}})
            data=json.load(urllib.request.urlopen(f'http://127.0.0.1:{http.server_port}/api/memory-documents/'+self.p['id']));self.assertEqual(len(data['files']),3)
        finally:http.shutdown();http.server_close();thread.join()
    def test_references_are_style_only_and_analyzed_once(self):
        src=self.root/'source';src.mkdir()
        for name in ['source','reference']:
            server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=160x120:d=1','-c:v','libx264','-y',str(src/(name+'.mp4'))])
        p=server.create('مشروع',str(src));source=next(a for a in p['assets'] if a['name']=='source.mp4');ref=next(a for a in p['assets'] if a['name']=='reference.mp4')
        for a in p['assets']:a.update(server.probe(Path(a['path'])))
        def record(a):return {'asset':a['id'],'name':a['name'],'status':'complete','fingerprint':vl.fingerprint(a),'analysis':{'summary':'saved','visual_style':['خلفية ورقية']},'transcript':{'status':'no_audio','segments':[]}}
        p['video_analyses']={source['id']:record(source)};p['analysis_at']=1;p['approved_reference_ids']=[ref['id']];pm.learn(p,learned(),'seed');server.save(p)
        calls=[]
        def analyze(pid,a,j):
            calls.append(a['id']);server.store_video(pid,a,record(a))
        def agent(pid,prompt,schema,frames,j):
            self.assertEqual(schema,server.PLAN_SCHEMA);self.assertIn('خلفية ورقية',pm.wrap(server.project(pid),prompt))
            # Only the explicitly selected source is offered as a clip asset.
            meta=json.loads(prompt.split('\nAssets: ')[-1]);self.assertEqual([a['id'] for a in meta],[source['id']])
            return {'reason':'saved style','clips':[{'asset':source['id'],'start':0,'end':.7,'text':'تعلّم'}]}
        with patch.object(server,'analyze_one',side_effect=analyze),patch.object(server,'ask_agent',side_effect=agent),patch.object(server,'learn_memory',side_effect=AssertionError('whole project relearned')):
            server.draft(p['id'],'video',{},[source['id']]);server.draft(p['id'],'another',{},[source['id']])
        self.assertEqual(calls,[ref['id']]);self.assertIn('reference.mp4',(server.DATA/p['id']/'STYLE.md').read_text())

if __name__=='__main__':unittest.main()
