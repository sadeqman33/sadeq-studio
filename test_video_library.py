import copy, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import server, video_library as vl
from speech_worker import clean_segments

class LibraryTests(unittest.TestCase):
    def test_information_file_without_linked_video(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); doc=root/'brief.md'; doc.write_text('Project facts: education for store owners.'); old=server.DATA; server.DATA=root/'data'
            try:
                p=server.create('Info',str(doc)); prompts=[]
                def agent(pid,prompt,schema,frames,j):
                    prompts.append(prompt); return copy.deepcopy(server.DEFAULT)
                with patch.object(server,'ask_agent',side_effect=agent): server.analyze(p['id'],{},[],True)
                self.assertTrue(server.project(p['id'])['analysis_at']); self.assertIn('education for store owners',prompts[0])
            finally: server.DATA=old

    def test_scope_and_zero_selection(self):
        p={'assets':[{'id':'a'},{'id':'b'}],'analysis_at':None}
        self.assertEqual(vl.targets(p,['b']),p['assets'])
        p['analysis_at']=1
        self.assertEqual(vl.targets(p,['b']),[p['assets'][1]])
        self.assertEqual(vl.targets(p,[],True),p['assets'])
        with self.assertRaises(ValueError): vl.targets(p,[])
        with self.assertRaises(ValueError): vl.targets(p,['foreign'])

    def test_every_video_cache_increment_and_failure_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); src=root/'source'; src.mkdir(); old=server.DATA; server.DATA=root/'data'
            try:
                for name in ['one','two','three']:
                    server.command([server.FFMPEG,'-v','error','-f','lavfi','-i','color=c=navy:s=160x120:d=0.6','-c:v','libx264','-y',str(src/(name+'.mp4'))])
                p=server.create('Test',str(src)); ids=[a['id'] for a in p['assets']]; calls=[]
                def agent(pid,prompt,schema,frames,j):
                    calls.append((schema,len(frames),prompt))
                    if schema==vl.VIDEO_SCHEMA: return {k:('video summary' if k=='summary' else []) for k in vl.FIELDS}
                    out=copy.deepcopy(server.DEFAULT); out['summary']='Combined source evidence'; return out
                with patch.object(server,'ask_agent',side_effect=agent):
                    server.analyze(p['id'],{},[ids[0]])
                    p=server.project(p['id']); self.assertEqual(len(p['video_analyses']),3)
                    self.assertEqual(sum(s==vl.VIDEO_SCHEMA for s,_,_ in calls),3)
                    self.assertTrue(all(r['transcript']['status']=='no_audio' for r in p['video_analyses'].values()))
                    calls.clear(); server.analyze(p['id'],{},[ids[1]])
                    self.assertEqual(len(calls),0) # Unchanged sources and project memory need no model calls.
                    self.assertEqual(server.project(p['id'])['last_analysis']['requested'],[ids[1]])
                    changed=Path(p['assets'][1]['path']); st=changed.stat(); os.utime(changed,ns=(st.st_atime_ns,st.st_mtime_ns+1000000000))
                    self.assertEqual(server.public_project(server.project(p['id']))['assets'][1]['analysis_status'],'stale')
                    calls.clear(); server.analyze(p['id'],{},[ids[1]])
                    self.assertEqual(sum(s==vl.VIDEO_SCHEMA for s,_,_ in calls),1)
                # Fail a changed video; the other source records remain intact and the saved transcript can retry.
                st=changed.stat(); os.utime(changed,ns=(st.st_atime_ns,st.st_mtime_ns+1000000000))
                def broken(pid,prompt,schema,frames,j):
                    if schema==vl.VIDEO_SCHEMA: raise ValueError('temporary model failure')
                    return agent(pid,prompt,schema,frames,j)
                with patch.object(server,'ask_agent',side_effect=broken):
                    with self.assertRaises(ValueError): server.analyze(p['id'],{},[ids[1]])
                p=server.project(p['id']); self.assertEqual(p['video_analyses'][ids[1]]['status'],'error')
                self.assertEqual(p['video_analyses'][ids[0]]['status'],'complete')
                with patch.object(server,'ask_agent',side_effect=agent),patch.object(vl,'transcribe',side_effect=AssertionError('do not repeat saved speech')):
                    server.analyze(p['id'],{},[ids[1]])
                self.assertEqual(server.project(p['id'])['video_analyses'][ids[1]]['status'],'complete')
            finally: server.DATA=old

    def test_speech_uncertainty_and_source_timecodes(self):
        raw=[{'start':1,'end':2,'text':'مرحبا','no_speech_prob':.01,'avg_logprob':-.2,'words':[{'start':1,'end':2,'word':'مرحبا'}]},
             {'start':3,'end':4,'text':'hallucination','no_speech_prob':.9},
             {'start':5,'end':6,'text':'over silence'}]
        good,bad=clean_segments(raw,20,30,[(21,22),(23,24)])
        self.assertEqual(good[0]['start'],21); self.assertEqual(good[0]['words'][0]['end'],22)
        self.assertTrue(good[0]['needs_review']); self.assertEqual(len(bad),2)
        r={'transcript':{'status':'transcribed','segments':good}}
        self.assertIn('00:00:21,000 --> 00:00:22,000',vl.transcript_srt(r))
        self.assertIn('مرحبا',vl.transcript_text(r))

if __name__=='__main__': unittest.main()
