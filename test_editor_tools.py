import copy,hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import server,workflow,render_settings as rs,remotion_bridge as rm,hyperframes_bridge as hf
import test_workflow as fixtures

class EditorToolsTests(fixtures.WorkflowTests):
    test_chat_plan_reuses_identity_without_nested_agent_and_real_export=None
    test_guards_prevent_stale_or_wrong_project_plans=None
    test_uninitialized_duplicate_and_source_change=None
    def test_saved_undo_rejects_changed_work_and_stale_context(self):
        reply=self.client.call('/api/agent-plan',self.plan());p=server.project(self.p['id'])
        self.client.call('/api/save',{'id':p['id'],'work_id':reply['work_id'],'timeline':p['timeline'],'renderer':'remotion','export_settings':{'resolution':'4k','fps':60}})
        before=copy.deepcopy(server.project(p['id']));ctx=self.client.context(p['id'],[])
        for bad in [{'work_id':'a'*12},{'base_fingerprint':'stale'}]:
            with self.assertRaises(ValueError):self.client.call('/api/undo',{'id':p['id'],'work_id':reply['work_id'],'base_fingerprint':ctx['base_fingerprint'],**bad})
            self.assertEqual(server.project(p['id'])['export_settings'],before['export_settings'])
        restored=self.client.call('/api/undo',{'id':p['id'],'work_id':reply['work_id'],'base_fingerprint':ctx['base_fingerprint']})
        self.assertEqual(restored['export_settings'],{'resolution':'1080','fps':30})
        self.assertEqual(restored['memory_view']['revision'],before['project_memory']['revision'])

    def test_local_caption_times_guards_and_no_creative_agent(self):
        plan=self.plan();aid=plan['selected_assets'][0];plan.update(renderer='remotion',clips=[{'asset':aid,'start':0,'end':.3,'text':''},{'asset':aid,'start':.5,'end':1,'text':''}],export_settings={'resolution':'4k','fps':60})
        reply=self.client.call('/api/agent-plan',plan);p=server.project(self.p['id']);clip=p['timeline'][1];ctx=self.client.context(p['id'],[])
        payload={'id':p['id'],'work_id':reply['work_id'],'base_fingerprint':ctx['base_fingerprint'],'clip_id':clip['id']}
        speech={'status':'transcribed','segments':[{'start':.55,'end':.95,'text':'فكرة جميلة','words':[{'text':'فكرة','start':.55,'end':.7},{'text':'جميلة','start':.75,'end':.95}]}]}
        with patch.object(server.vl,'transcribe',return_value=speech),patch.object(server,'ask_agent',side_effect=AssertionError('no creative agent')):
            server.transcribe_only(p['id'],aid,{})
        payload['base_fingerprint']=self.client.context(p['id'],[])['base_fingerprint']
        before=copy.deepcopy(server.project(p['id'])['layers']);r=self.client.call('/api/caption-suggest',{**payload,'mode':'words'})
        self.assertTrue(r['automatic']);self.assertEqual([l['text'] for l in r['layers']],['فكرة','جميلة']);self.assertAlmostEqual(r['layers'][0]['start'],.35);self.assertAlmostEqual(r['layers'][1]['end'],.75)
        self.assertEqual(server.project(p['id'])['layers'],before)
        with self.assertRaises(ValueError):self.client.call('/api/caption-suggest',{**payload,'base_fingerprint':'stale'})
        ctx=self.client.context(p['id'],[]);p=server.project(p['id']);self.client.call('/api/save',{'id':p['id'],'work_id':reply['work_id'],'timeline':p['timeline'],'renderer':'remotion','layers':r['layers'],'export_settings':{'resolution':'4k','fps':60}})
        manual=self.client.call('/api/work-new',{'id':p['id'],'base_fingerprint':self.client.context(p['id'],[])['base_fingerprint']})
        self.client.call('/api/work-open',{'id':p['id'],'work_id':reply['work_id'],'base_fingerprint':self.client.context(p['id'],[])['base_fingerprint']})
        self.assertEqual(self.client.context(p['id'],[])['export_settings'],{'resolution':'4k','fps':60})
        self.assertEqual(hashlib.sha256(Path(self.p['assets'][0]['path']).read_bytes()).hexdigest(),self.original)
    def test_single_video_link_and_rescan_keep_manual_sources(self):
        ctx=self.client.context(self.p['id'],[]);source=self.root/'extra.mp4';source.write_bytes(Path(self.p['assets'][0]['path']).read_bytes());before=hashlib.sha256(source.read_bytes()).hexdigest()
        d={'id':self.p['id'],'work_id':ctx['active_work_id'],'base_fingerprint':ctx['base_fingerprint'],'source':str(source)}
        reply=self.client.call('/api/video-link',d);self.assertEqual(len(reply['project']['assets']),2)
        updated=self.client.call('/api/rescan',{'id':self.p['id']});self.assertIn(reply['asset_id'],[a['id'] for a in updated['assets']])
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)
        with self.assertRaises(ValueError):self.client.call('/api/video-link',{**d,'base_fingerprint':'bad'})
    def test_quality_boundaries_and_edit_operations(self):
        self.assertEqual(rs.dimensions({'ratio':'9:16','export_settings':{'resolution':'4k','fps':60}}),(2160,3840,60))
        self.assertEqual(rs.dimensions({'ratio':'16:9','export_settings':{'resolution':'4k','fps':30}}),(3840,2160,30))
        for bad in [{'resolution':'8k'},{'fps':True},{'fps':24},{'fps':60,'extra':1}]:
            with self.assertRaises(ValueError):rs.settings({},bad)
        with self.assertRaises(ValueError):rs.settings({'renderer':'basic'},{'resolution':'4k','fps':60})
        self.assertEqual(rm.frame_plan({'timeline':[{'start':0,'end':.02}], 'export_settings':{'fps':60}})['durationInFrames'],1)
        js="""const a=require('./timeline_tools.js'),m=require('./motion.js'),l={id:'aabbccdd',type:'text',start:2,end:5,text:'صادق ستوديو',x:40,motion:'pop'};const w=a.words(l,['aa','bb']);if(w.length!==2||w[0].start!==2||w[1].end!==5||w[1].text!=='ستوديو')throw Error('words');const [left,right]=a.split(l,3,'new');if(left.end!==3||right.start!==3||right.x!==40||l.end!==5)throw Error('split');const s=m.state(.1,2,'pop',{enterDuration:.5,exitDuration:.5,exitMotion:'blur'});if(s.scale>=1||s.opacity>=1)throw Error('entrance');if(m.state(1.95,2,'pop',{enterDuration:0,exitDuration:.5,exitMotion:'blur'}).blur<=0)throw Error('exit');"""
        subprocess.run(['node','-e',js],cwd=server.ROOT,check=True)
    @unittest.skipUnless(rm.ready() and hf.ready(),'both local engines required')
    def test_real_4k_30_and_60_in_both_ratios_and_engines(self):
        plan=self.plan();plan.update(renderer='remotion',clips=[{**plan['clips'][0],'start':0,'end':.4,'text':''}],layers=[{'id':'aabbccdd','type':'text','text':'صادق 4K','start':0,'end':.4,'font':'Hacen Beirut','motion':'pop','enterDuration':.1,'exitDuration':.1,'exitMotion':'fade'}]);self.client.call('/api/agent-plan',plan)
        for engine in ['remotion','hyperframes']:
            for fps,ratio in [(30,'9:16'),(60,'16:9')]:
                p=server.project(self.p['id']);p.update(renderer=engine,ratio=ratio,export_settings={'resolution':'4k','fps':fps});server.save(p);server.export(p['id'],{})
                e=server.project(p['id'])['exports'][-1];v=server.probe(Path(e['path']));self.assertEqual(v['fps'],fps);self.assertEqual((v['width'],v['height']),rs.dimensions(p)[:2]);self.assertAlmostEqual(v['duration'],.4,delta=.05)
                self.assertEqual(e['fps'],fps);self.assertEqual(e['resolution'],'4k')
        self.assertEqual(hashlib.sha256(Path(self.p['assets'][0]['path']).read_bytes()).hexdigest(),self.original)

if __name__=='__main__':unittest.main()
