import base64, copy, hashlib, json, tempfile, unittest
from pathlib import Path
import layers, server, workflow, video_works
import test_workflow as fixtures

class LayerTests(fixtures.WorkflowTests):
    # Reuse isolated HTTP/source fixture; do not repeat inherited tests here.
    test_chat_plan_reuses_identity_without_nested_agent_and_real_export=None
    test_guards_prevent_stale_or_wrong_project_plans=None
    test_uninitialized_duplicate_and_source_change=None
    def image(self,color='red',kind='image'):
        file=self.root/(color+'.png')
        server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c='+color+':s=24x24','-frames:v','1','-pix_fmt','rgba','-threads','1','-y',str(file)])
        context=self.client.context(self.p['id'],[])
        return self.client.call('/api/layer-import',{'id':self.p['id'],'work_id':context['active_work_id'],'base_fingerprint':context['base_fingerprint'],'image':base64.b64encode(file.read_bytes()).decode(),'name':file.name,'kind':kind})['asset']
    def layer(self,kind='text',**kwargs):
        return {'id':'aabbccdd','type':kind,'start':0,'end':.7,**({'text':'صادق','font':'Hacen Beirut'} if kind=='text' else {}),**kwargs}
    def submit(self,items):
        plan=self.plan();plan.update(renderer='hyperframes',ratio='9:16',layers=items);plan['clips'][0].update(start=0,end=1,text='')
        return self.client.call('/api/agent-plan',plan)
    def test_independent_layers_save_edit_undo_and_shared_imports(self):
        red=self.image();first=self.submit([self.layer(),self.layer('image',id='ccddeeff',asset=red['id'])]);ctx=self.client.context(self.p['id'],[])
        second=self.submit([]);p=server.project(self.p['id']);self.assertEqual(p['layers'],[])
        self.client.call('/api/work-open',{'id':p['id'],'work_id':first['work_id'],'base_fingerprint':self.client.context(p['id'],[])['base_fingerprint']})
        ctx=self.client.context(p['id'],[]);items=copy.deepcopy(ctx['layers']);items[0]['text']='صادق ستوديو';items[1]['x']=25
        self.client.call('/api/save',{'id':p['id'],'work_id':first['work_id'],'timeline':ctx['timeline'],'layers':items,'renderer':'hyperframes'})
        edited=server.project(p['id']);self.assertEqual(edited['layers'][0]['text'],'صادق ستوديو')
        self.assertNotEqual(ctx['base_fingerprint'],self.client.context(p['id'],[])['base_fingerprint'])
        restored=self.client.call('/api/undo',{'id':p['id']});self.assertEqual(restored['layers'][0]['text'],'صادق');self.assertEqual(restored['overlay_assets'][0]['id'],red['id'])
        fresh=self.client.context(p['id'],[])
        manual=self.client.call('/api/work-new',{'id':p['id'],'title':'فارغ','base_fingerprint':fresh['base_fingerprint']})
        self.assertEqual(manual['layers'],[]);self.assertEqual(manual['timeline'],[])
        self.client.call('/api/work-open',{'id':p['id'],'work_id':first['work_id'],'base_fingerprint':self.client.context(p['id'],[])['base_fingerprint']})
        self.assertEqual(self.client.context(p['id'],[])['layers'][0]['text'],'صادق')
        self.assertEqual(hashlib.sha256(Path(self.p['assets'][0]['path']).read_bytes()).hexdigest(),self.original)
    def test_validation_import_guards_and_source_integrity(self):
        with self.assertRaises(ValueError):self.submit([self.layer('image',asset='unknown')])
        with self.assertRaises(ValueError):self.submit([self.layer(rotation=float('nan'))])
        red=self.image();p=server.project(self.p['id']);items=layers.validate(p,[self.layer('icon',asset=red['id'])]);folder=self.root/'freeze';folder.mkdir();layers.freeze({**p,'layers':items},folder)
        self.assertTrue((folder/('layer-'+red['id']+'.png')).exists())
        Path(red['path']).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'تغيّرت'):layers.freeze({**p,'layers':items},folder)
        with self.assertRaises(ValueError):self.client.call('/api/layer-import',{'id':p['id'],'work_id':'foreign','base_fingerprint':'stale','name':'x.png','image':'bad'})
        ctx=self.client.context(p['id'],[])
        with self.assertRaises(ValueError):self.client.call('/api/layer-import',{'id':p['id'],'work_id':ctx['active_work_id'],'base_fingerprint':ctx['base_fingerprint'],'name':'x.svg','image':base64.b64encode(b'<svg/>').decode()})
    def test_real_two_engines_render_overlapping_timed_layers(self):
        red=self.image();green=self.image('lime','icon')
        items=[self.layer('image',asset=red['id'],x=25,y=25,width=20),self.layer('icon',id='bbccddee',asset=green['id'],x=75,y=25,width=10,start=.5,end=1),self.layer(id='ddeeffaa',text='صادق ستوديو',start=.1,end=.9,y=65)]
        self.submit(items)
        for engine in ['hyperframes','remotion']:
            p=server.project(self.p['id']);p['renderer']=engine;server.save(p);server.export(p['id'],{})
            p=server.project(p['id']);file=Path(p['exports'][-1]['path']);meta=server.probe(file);self.assertEqual((meta['width'],meta['height']),(1080,1920));self.assertAlmostEqual(meta['duration'],1,delta=.15)
            def pixel(t,x,y):
                import subprocess
                r=subprocess.run([server.FFMPEG,'-v','error','-ss',str(t),'-i',str(file),'-frames:v','1','-vf',f'crop=2:2:{x}:{y}','-pix_fmt','rgb24','-f','rawvideo','-'],capture_output=True,check=True)
                return tuple(r.stdout[:3])
            r=pixel(.4,270,480);g0=pixel(.3,810,480);g1=pixel(.7,810,480)
            self.assertGreater(r[0],180,engine);self.assertLess(r[1],70,engine)
            self.assertLess(g0[1],80,engine);self.assertGreater(g1[1],180,engine)
        self.assertEqual(hashlib.sha256(Path(self.p['assets'][0]['path']).read_bytes()).hexdigest(),self.original)

if __name__=='__main__':unittest.main()
