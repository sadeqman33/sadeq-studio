import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
import render_runtime as rr
import server

class RenderPerformanceTests(unittest.TestCase):
    def test_prepared_ranges_reuse_and_invalidate_on_source_or_recipe_change(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'original.mp4';source.write_bytes(b'original')
            target=root/'clip.mp4';cache=root/'cache';calls=[];job={}
            def encode(cmd,timeout):calls.append(cmd);Path(cmd[-1]).write_bytes(b'prepared')
            cmd=['ffmpeg','-ss','1','-i',str(source),'-t','2','-vf','fps=60','-y',str(target)]
            rr.cached_clip(source,target,cmd,encode,1,cache,job)
            rr.cached_clip(source,root/'second.mp4',[*cmd[:-1],str(root/'second.mp4')],encode,1,cache,job)
            self.assertEqual(len(calls),1);self.assertEqual(job['clip_cache'],{'hits':1,'misses':1})
            changed=cmd.copy();changed[2]='2';rr.cached_clip(source,target,changed,encode,1,cache,job)
            changed=cmd.copy();changed[-3]='fps=30';rr.cached_clip(source,target,changed,encode,1,cache,job)
            source.write_bytes(b'new original');rr.cached_clip(source,target,cmd,encode,1,cache,job)
            self.assertEqual(len(calls),4);self.assertEqual(source.read_bytes(),b'new original')
            # Frozen exports survive eviction of disposable cached clips.
            for f in cache.glob('*.mp4'):f.unlink()
            self.assertEqual((root/'second.mp4').read_bytes(),b'prepared')

    def test_failed_preparation_and_mid_encode_source_change_never_cache(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);source=root/'source.mp4';source.write_bytes(b'original');cache=root/'cache'
            def changed(cmd,timeout):Path(cmd[-1]).write_bytes(b'prepared');source.write_bytes(b'changed source')
            with self.assertRaisesRegex(ValueError,'تغيّر'):rr.cached_clip(source,root/'clip.mp4',['ffmpeg',str(root/'clip.mp4')],changed,1,cache,{})
            self.assertEqual(list(cache.iterdir()),[])

    def test_no_intermediate_upscale_and_bounded_workers(self):
        self.assertIn('scale=1080:1920',rr.clip_filter({'width':1080,'height':1920},2160,3840,60))
        self.assertNotIn('pad=',rr.clip_filter({'width':1080,'height':1920},2160,3840,60))
        js="""const assert=require('assert'),{concurrency:c,encoding:e}=require('./remotion/performance.cjs');assert.equal(c(2160,3840,{cpus:16,memory:48*1024**3}),4);assert.equal(c(1080,1920,{cpus:16,memory:48*1024**3}),6);assert.equal(c(2160,3840,{cpus:2,memory:4*1024**3}),1);assert.equal(c(2160,3840,{override:'2'}),2);assert.equal(c(2160,3840,{cpus:16,memory:48*1024**3,override:'99'}),4);assert.equal(e(2160,3840,60,true).videoBitrate,'80M');assert.equal(e(1080,1920,30,true).videoBitrate,'12M');assert.equal(e(2160,3840,60,false).crf,18);assert.equal(e(2160,3840,60,true).crf,undefined);"""
        subprocess.run(['node','-e',js],cwd=server.ROOT,check=True)

    def test_subprocess_reports_actual_frames_and_timeout_reaps_it(self):
        with tempfile.TemporaryDirectory() as t:
            log=Path(t)/'render.log';job={}
            script='import json;print('+repr(rr.PREFIX)+"+json.dumps({'phase':'frames','progress':40,'rendered_frames':12,'encoded_frames':5,'total_frames':30}))"
            self.assertEqual(rr.monitored([sys.executable,'-c',script],log,job,3),0)
            self.assertEqual(job['progress'],40);self.assertEqual(job['rendered_frames'],12)
            rr.event(job,'SADEQ_RENDER broken json');rr.event(job,'Frames: 100%');self.assertEqual(job['progress'],40)
            rr.phase(job,'audio','audio');self.assertNotIn('progress',job);rr.finish(job);self.assertIn('frames',job['timings'])
            with self.assertRaises(subprocess.TimeoutExpired):rr.monitored([sys.executable,'-c','import time;time.sleep(10)'],log,{},.1)

if __name__=='__main__':unittest.main()
