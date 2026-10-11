"""Original Sadeq timeline adapter for local, pinned Remotion rendering.

Only structured edit data enters our fixed React composition. No generated code,
remote media, cloud deployment or changes to source footage.
"""
import json, math, subprocess
from pathlib import Path
import hyperframes_bridge as hf
import layers as ly

ROOT=Path(__file__).resolve().parent
VERSION='4.0.534'
FPS=30

def ready():
    for package in ['remotion','@remotion/bundler','@remotion/renderer']:
        file=ROOT/'node_modules'/package/'package.json'
        if not file.exists() or json.loads(file.read_text()).get('version')!=VERSION:return False
    return True

def frame_plan(p):
    """Round cumulative boundaries, so many clips never accumulate timing drift."""
    elapsed=0; end_frame=0; clips=[]
    for i,c in enumerate(p['timeline']):
        duration=c['end']-c['start']
        if not math.isfinite(duration) or duration<1/FPS:raise ValueError('Remotion يحتاج كل مقطع بطول إطار واحد على الأقل (1/30 ثانية)')
        elapsed+=duration; boundary=round(elapsed*FPS)
        clips.append({**c,'src':f'clip-{i}.mp4','from':end_frame,'frames':boundary-end_frame})
        end_frame=boundary
    if not clips:raise ValueError('ضيف مقاطع للتايم لاين')
    w,h=(1920,1080) if p.get('ratio')=='16:9' else (1080,1920)
    return {'width':w,'height':h,'fps':FPS,'durationInFrames':end_frame,
            'clips':clips,'profile':{'colors':p.get('profile',{}).get('colors',[])},
            'typography':p.get('typography',{}),'motion_style':p.get('motion_style','plain')}

def prepare(p,out,probe,command,font,j):
    if not ready():raise ValueError('Remotion يحتاج إعداد: شغّل setup-remotion.command')
    props=frame_plan(p); assets={a['id']:a for a in p['assets']}
    metas=[]
    for c in props['clips']:
        source=Path(assets[c['asset']]['path']); meta=probe(source)
        if meta['hdr']:raise ValueError('المقطع HDR؛ حوّله إلى SDR قبل تصدير Remotion')
        metas.append((source,meta))
    folder=out/'remotion';public=folder/'public';public.mkdir(parents=True)
    # Private font bytes remain in this local export directory, never in a package.
    (public/'brand.ttf').write_bytes(font.read_bytes())
    for i,(c,(source,meta)) in enumerate(zip(props['clips'],metas)):
        j['message']=f'أجهّز مقاطع Remotion: {i+1} / {len(metas)}'
        duration=c['frames']/FPS
        cmd=['ffmpeg','-v','error','-ss',str(c['start']),'-i',str(source)]
        silent=c.get('mute',False) or not meta['audio']
        if silent:cmd+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
        cmd+=['-t',str(duration),'-vf',f'scale={props["width"]}:{props["height"]}:force_original_aspect_ratio=decrease,pad={props["width"]}:{props["height"]}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=0.05',
              '-map','0:v:0','-map','1:a:0' if silent else '0:a:0','-af','apad',
              '-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
              '-c:a','aac','-ar','48000','-ac','2','-movflags','+faststart','-y',str(public/c['src'])]
        command(cmd,max(180,int(duration*15)))
    props['layers']=ly.freeze(p,public)
    (folder/'props.json').write_text(json.dumps(props,ensure_ascii=False,indent=2))
    (folder/'manifest.json').write_text(json.dumps({'engine':'remotion','version':VERSION,
        'memory_revision':p.get('draft_memory_revision'),'work_id':p.get('active_work_id'),
        'source_clips':p['timeline'],'durationInFrames':props['durationInFrames'],'fps':FPS},ensure_ascii=False,indent=2))
    return folder,props

def render(p,out,probe,command,font,j):
    folder,props=prepare(p,out,probe,command,font,j)
    log=out/'remotion.log';total=props['durationInFrames']/FPS
    j['message']='Remotion يرسم الفيديو محلياً بدقة 1080…'
    with log.open('w') as stream:
        try:
            result=subprocess.run([hf.node(),str(ROOT/'remotion/render.cjs'),str(folder)],
                cwd=ROOT,env=hf.environment(),stdout=stream,stderr=subprocess.STDOUT,
                timeout=max(600,int(total*45)))
        except subprocess.TimeoutExpired:raise ValueError('تصدير Remotion تجاوز الوقت؛ المسودة والتفاصيل محفوظة')
    if result.returncode or not (folder/'video.mp4').exists():
        raise ValueError('Remotion ما كمل التصدير: '+log.read_text(errors='replace')[-1200:])
    # Retain cut/muted source audio independently of React video decoding.
    (folder/'concat.txt').write_text('\n'.join(f"file 'public/{c['src']}'" for c in props['clips']))
    command(['ffmpeg','-v','error','-f','concat','-safe','0','-i',str(folder/'concat.txt'),
             '-vn','-c:a','aac','-ar','48000','-ac','2','-t',str(total),'-y',str(folder/'source-audio.m4a')],180)
    command(['ffmpeg','-v','error','-i',str(folder/'video.mp4'),'-i',str(folder/'source-audio.m4a'),
             '-map','0:v:0','-map','1:a:0','-c','copy','-t',str(total),'-movflags','+faststart',
             '-y',str(out/'final.mp4')],180)
    return props['width'],props['height'],total
