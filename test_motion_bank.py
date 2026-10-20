import copy,json,subprocess,tempfile,unittest,urllib.request,urllib.error
from pathlib import Path
import motion_bank as mb,layers,server,workflow
from test_workflow import WorkflowTests

class BankUnitTests(unittest.TestCase):
 def test_catalog_previews_and_exclusions(self):
  rows=mb.catalog();self.assertEqual(len(rows),100);self.assertEqual(len({m['id'] for m in rows}),100)
  self.assertEqual(len([m for m in rows if m['native_types']]),16)
  for m in rows:
   self.assertTrue((mb.ROOT/'motion-bank'/m['preview']).is_file())
   self.assertTrue((mb.ROOT/f"motion-bank/posters/{m['n']:02d}.jpg").is_file())
  self.assertFalse(next(m for m in rows if m['id']=='orbit')['native_types'])
  self.assertFalse(next(m for m in rows if m['id']=='echoStack')['native_types'])
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);state=mb.update(root,{'action':'preferences','revision':0,'on':['riseUp'],'off':['glitch']})['state']
   with self.assertRaises(ValueError):mb.update(root,{'action':'preferences','revision':0,'on':[],'off':[]})
   with self.assertRaises(ValueError):mb.validate_preferences({'on':['riseUp'],'off':['riseUp']})
   with self.assertRaises(ValueError):mb.validate_preferences({'on':[{}]})
   for i in range(8):
    state=mb.update(root,{'action':'plan','revision':state['revision'],'title':'نص','native_only':True,'cues':['emphasis']})['state']
    plan=state['history'][-1];self.assertTrue(set(plan['core']+plan['accents'])<=mb.SUPPORTED);self.assertNotIn('glitch',plan['core'])
   self.assertNotEqual(state['history'][-1]['core'],state['history'][-2]['core'])
   empty=mb.plan({'on':[],'off':[m['id'] for m in rows],'history':[]},{})
   self.assertEqual(empty['core'],[]);self.assertEqual(empty['accents'],[])
 def test_layer_schema_and_deterministic_clock(self):
  l={'id':'aabbccdd','type':'text','text':'صادق ستوديو','start':0,'end':2,'bankMotion':'riseUp'}
  self.assertEqual(layers.validate({},[l])[0]['bankMotion'],'riseUp')
  for bad in ['jcut','unknown',{},None]:
   with self.assertRaises(ValueError):layers.validate({},[{**l,'bankMotion':bad}])
  with self.assertRaises(ValueError):layers.validate({'overlay_assets':[{'id':'test'}]},[{**l,'type':'icon','asset':'test','bankMotion':'caption'}])
  code="""const assert=require('assert'),bank=require('./bank_motion'),layers=require('./layers');
const l={type:'text',text:'صادق ستوديو',start:0,end:2,x:50,y:65,width:70,fontSize:64};
for(const m of bank.supported){for(const time of [0,.01,.2,.5,1,1.99,2,3]){const row={...l,bankMotion:m},a=JSON.stringify([layers.style(row,time),bank.runs(row,time)]);assert(!a.includes('NaN'));assert(!a.includes('Infinity'));assert.strictEqual(a,JSON.stringify([layers.style(row,time),bank.runs(row,time)]));assert.equal(layers.style(row,time).top,'65%');}}
assert.equal(layers.style({...l,bankMotion:'riseUp'},2).opacity,0);
for(const m of bank.supported.filter(x=>x!=='wordSwap')){const text=bank.runs({...l,bankMotion:m},1.99).map(r=>r.text).join('');assert.equal(text,l.text,m);}
assert.equal(bank.runs({...l,text:'85%',bankMotion:'counter'},1.99)[0].text,'85%');
assert.equal(bank.runs({...l,text:'سعره 85 ألف',bankMotion:'counter'},.1)[0].text,'سعره 85 ألف');
"""
  subprocess.run([server.hf.node(),'-e',code],cwd=mb.ROOT,check=True)

class BankHTTPTests(WorkflowTests):
 test_chat_plan_reuses_identity_without_nested_agent_and_real_export=None
 test_guards_prevent_stale_or_wrong_project_plans=None
 test_uninitialized_duplicate_and_source_change=None
 def test_preferences_plan_scope_and_apply_roundtrip(self):
  before=copy.deepcopy(server.project(self.p['id']));bank=self.client.call('/api/motion-bank');self.assertEqual(len(bank['catalog']),100)
  self.client.call('/api/motion-bank',{'action':'preferences','revision':0,'on':['riseUp'],'off':['glitch']})
  self.assertEqual(server.project(self.p['id']),before)
  with self.assertRaises(ValueError):self.client.call('/api/motion-bank',{'id':self.p['id'],'work_id':'foreign','action':'plan','revision':1})
  plan=self.plan();plan.update(renderer='remotion',layers=[{'id':'aabbccdd','type':'text','text':'صادق ستوديو','start':0,'end':.9,'bankMotion':'riseUp'}]);result=self.client.call('/api/agent-plan',plan)
  context=self.client.context(self.p['id'],[]);self.assertEqual(context['layers'][0]['bankMotion'],'riseUp')
  before=copy.deepcopy(server.project(self.p['id']))
  self.client.call('/api/motion-bank',{'id':self.p['id'],'work_id':result['work_id'],'action':'plan','revision':1,'native_only':True})
  self.assertEqual(server.project(self.p['id']),before)
  self.assertEqual(self.client.context(self.p['id'],[])['motion_bank']['preferences']['off'],['glitch'])
 def test_expanded_gallery_media_routes(self):
  base='http://127.0.0.1:'+str(self.http.server_port)
  for n in [1,50,51,99,100]:
   for folder,ext in [('previews','mp4'),('posters','jpg')]:
    with urllib.request.urlopen(f'{base}/motion-bank/{folder}/{n:02d}.{ext}') as response:
     self.assertEqual(response.status,200);self.assertGreater(len(response.read()),100)
  for path in ['/motion-bank/previews/101.mp4','/motion-bank/previews/00.mp4','/motion-bank/posters/100.mp4']:
   with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(base+path)
   self.assertEqual(e.exception.code,404)
  health=self.client.call('/api/health');self.assertEqual(health['motion_bank']['catalog'],100)
  self.assertEqual(health['studio_version'],'0.19.2')
 def test_real_both_engines(self):
  plan=self.plan();plan.update(renderer='remotion',ratio='9:16',layers=[{'id':'aabbccdd','type':'text','text':'صادق ستوديو','start':0,'end':1,'x':50,'y':50,'fontSize':160,'bankMotion':'riseUp','enterDuration':.6}]);plan['clips'][0].update(start=0,end=1,text='')
  self.client.call('/api/agent-plan',plan)
  for engine in ['remotion','hyperframes']:
   p=server.project(self.p['id']);p['renderer']=engine;server.save(p);server.export(p['id'],{})
   p=server.project(p['id']);file=Path(p['exports'][-1]['path']);meta=server.probe(file)
   self.assertEqual((meta['width'],meta['height']),(1080,1920));self.assertAlmostEqual(meta['duration'],1,delta=.12)
   def pixels(t):
    return subprocess.run([server.FFMPEG,'-v','error','-ss',str(t),'-i',str(file),'-frames:v','1','-vf','scale=108:192','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
   start=pixels(0);middle=pixels(.6);self.assertNotEqual(start,middle,engine)
   bright=lambda b:sum(min(b[i:i+3])>160 for i in range(0,len(b),3))
   self.assertGreater(bright(middle),bright(start)+5,engine)

if __name__=='__main__':unittest.main()
