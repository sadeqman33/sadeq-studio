import hashlib, json, subprocess, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import server, media_previews
import test_workflow as fixtures

class TimelineGeometryTests(unittest.TestCase):
 def test_anchor_packed_overlap_frame_precision_and_group_bounds(self):
  js=r"""
const assert=require('node:assert/strict'),g=require('./timeline_geometry.js');
const screen=230,time=8,pps=120,scroll=g.anchoredScroll(time,pps,screen);assert.equal(110+time*pps-scroll,screen);
const rows=[{id:'a',start:1,end:2},{id:'b',start:2,end:3},{id:'c',start:1.5,end:2.5}];
const lanes=g.lanes(rows);assert.equal(lanes.length,2);assert.equal(lanes.flat().length,3);for(const row of lanes)for(let i=1;i<row.length;i++)assert.ok(row[i-1].end<=row[i].start);
assert.equal(g.lanes(rows,true).length,3);assert.equal(g.frame(.51,30),15/30);assert.equal(g.frame(11,60,10),10);
const moved=g.shift(rows,20,5,30);assert.equal(Math.max(...moved.map(l=>l.end)),5);assert.equal(moved[1].start-moved[0].start,1);assert.equal(rows[0].start,1);
assert.throws(()=>g.shift([{...rows[0],locked:true}],1,10,30));
assert.equal(g.shift([rows[0]],.92,10,30,[3],.1)[0].end,3);
assert.equal(g.trim(rows[0],'start',3,10,30).start,2-1/30);assert.equal(g.trim(rows[0],'end',1,10,30).end,1+1/30);
assert.equal(g.nearest(1.02,[1,2],.05),1);
"""
  subprocess.run(['node','-e',js],cwd=server.ROOT,check=True)

class TimelineMediaTests(fixtures.WorkflowTests):
 test_chat_plan_reuses_identity_without_nested_agent_and_real_export=None
 test_guards_prevent_stale_or_wrong_project_plans=None
 test_uninitialized_duplicate_and_source_change=None
 def test_saved_track_lock_and_private_previews_cache_source_ranges(self):
  plan=self.plan();plan['renderer']='remotion';plan['layers']=[{'id':'aabbccdd','type':'text','text':'صادق','start':0,'end':.8,'locked':True,'track':'title'}]
  r=self.client.call('/api/agent-plan',plan);p=server.project(self.p['id']);aid=p['assets'][0]['id']
  saved=self.client.call('/api/save',{'id':p['id'],'work_id':r['work_id'],'timeline':p['timeline'],'layers':p['layers'],'renderer':'remotion'})
  self.assertTrue(saved['layers'][0]['locked']);self.assertEqual(saved['layers'][0]['track'],'title')
  result=self.client.call('/api/timeline-media/'+p['id']+'/'+aid+'?start=0&end=.8')
  self.assertEqual(len(result['thumbnails']),3);self.assertFalse(result['has_audio']);self.assertEqual(result['peaks'],[])
  real_run=subprocess.run
  def cached_run(cmd,*args,**kwargs):
   if Path(cmd[0]).name=='ffmpeg':raise AssertionError('cache should reuse')
   return real_run(cmd,*args,**kwargs)
  with patch.object(media_previews.subprocess,'run',side_effect=cached_run):
   cached=self.client.call('/api/timeline-media/'+p['id']+'/'+aid+'?start=0&end=.8')
  self.assertEqual(cached['key'],result['key'])
  tone=self.root/'tone.mp4'
  server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=160x240:r=30:d=1','-f','lavfi','-i','sine=frequency=440:duration=1','-c:v','libx264','-c:a','aac','-shortest','-y',str(tone)])
  ctx=self.client.context(p['id'],[])
  linked=self.client.call('/api/video-link',{'id':p['id'],'work_id':r['work_id'],'base_fingerprint':ctx['base_fingerprint'],'source':str(tone)})
  audio=self.client.call('/api/timeline-media/'+p['id']+'/'+linked['asset_id']+'?start=0&end=.8')
  self.assertTrue(audio['has_audio']);self.assertGreater(max(audio['peaks']),.8)
  shorter=self.client.call('/api/timeline-media/'+p['id']+'/'+aid+'?start=.2&end=.6');self.assertNotEqual(shorter['key'],result['key'])
  for suffix in ['?start=-1&end=.8','?start=0&end=100','?start=nan&end=1','?kind=bad']:
   with self.assertRaises(ValueError):self.client.call('/api/timeline-media/'+p['id']+'/'+aid+suffix)
  with self.assertRaises(ValueError):self.client.call('/api/timeline-media/'+p['id']+'/foreign?start=0&end=.8')
  self.assertEqual(hashlib.sha256(Path(self.p['assets'][0]['path']).read_bytes()).hexdigest(),self.original)
 def test_invalid_track_or_lock_reject_without_overwriting_draft(self):
  for fields in [{'locked':'yes'},{'track':'unknown'}]:
   plan=self.plan();plan['layers']=[{'id':'aabbccdd','type':'text','text':'صادق','end':.5,**fields}]
   with self.assertRaises(ValueError):self.client.call('/api/agent-plan',plan)
  self.assertEqual(server.project(self.p['id'])['timeline'],[])

if __name__=='__main__':unittest.main()
