"""Private derived-media cache and observable local render subprocesses."""
import hashlib, json, os, shutil, signal, subprocess, time, uuid
from pathlib import Path

PREFIX='SADEQ_RENDER '
CACHE_LIMIT=8*1024**3

def phase(job,name,message):
    now=time.monotonic()
    if '_phase_started' in job:
        timings=job.setdefault('timings',{})
        old=job['phase'];timings[old]=round(timings.get(old,0)+now-job['_phase_started'],3)
    job.update(phase=name,message=message,_phase_started=now)
    for key in ['progress','rendered_frames','encoded_frames','total_frames']:
        job.pop(key,None)

def finish(job):
    if '_phase_started' in job:
        started=job.pop('_phase_started');name=job['phase'];timings=job.setdefault('timings',{})
        timings[name]=round(timings.get(name,0)+time.monotonic()-started,3)
    job.pop('progress',None)

def clip_filter(meta,width,height,fps,pad_tail=False):
    # Fit in the browser at final output size. Never encode/decode upscaled
    # camera frames twice; the final graphics still render at full resolution.
    w=max(2,min(width,int(meta['width']))//2*2)
    h=max(2,min(height,int(meta['height']))//2*2)
    value=f'scale={w}:{h}:force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1,fps={fps}'
    return value+(',tpad=stop_mode=clone:stop_duration=0.05' if pad_tail else '')

def cached_clip(source,target,cmd,command,timeout,cache,job):
    """Key every media-affecting option; text-only edits reuse immutable clips."""
    source=Path(source);target=Path(target);cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    stat=source.stat();signature=(stat.st_size,stat.st_mtime_ns)
    recipe={'version':1,'source':str(source.resolve()),'signature':signature,'command':cmd[:-1]}
    key=hashlib.sha256(json.dumps(recipe,sort_keys=True).encode()).hexdigest()
    hit=cache/(key+'.mp4');stats=job.setdefault('clip_cache',{'hits':0,'misses':0})
    if not hit.exists() or not hit.stat().st_size:
        temp=cache/(key+'.'+uuid.uuid4().hex+'.tmp.mp4')
        try:
            command([*cmd[:-1],str(temp)],timeout)
            after=source.stat()
            if (after.st_size,after.st_mtime_ns)!=signature:
                raise ValueError('المقطع الأصلي تغيّر أثناء التصدير؛ جرّب النسخة الحالية')
            if not temp.exists() or not temp.stat().st_size:raise ValueError('تحضير المقطع ما أنتج ملف فيديو')
            temp.replace(hit);stats['misses']+=1
        finally:temp.unlink(missing_ok=True)
    else:stats['hits']+=1
    target.unlink(missing_ok=True)
    try:os.link(hit,target)
    except OSError:shutil.copy2(hit,target)
    os.utime(hit,None)
    # Only disposable derived cache entries; exports and originals are retained.
    files=sorted(cache.glob('*.mp4'),key=lambda f:f.stat().st_mtime)
    size=sum(f.stat().st_size for f in files)
    for f in files:
        if size<=CACHE_LIMIT:break
        if f==hit:continue
        size-=f.stat().st_size;f.unlink()

def event(job,line):
    if not line.startswith(PREFIX):return
    try:data=json.loads(line[len(PREFIX):])
    except (ValueError,TypeError):return
    name=data.get('phase')
    if name in ['bundle','frames','encode'] and name!=job.get('phase'):
        phase(job,name,{'bundle':'أجهّز محرك الرسم…','frames':'أرسم الفريمات وطبقاتها…','encode':'أضغط الفيديو وأجهّز الملف…'}[name])
    progress=data.get('progress')
    if isinstance(progress,(int,float)) and not isinstance(progress,bool) and 0<=progress<=100:
        job['progress']=round(progress,1)
    for key in ['rendered_frames','encoded_frames','total_frames','concurrency']:
        value=data.get(key)
        if isinstance(value,int) and value>=0:job[key]=value
    if data.get('encoding_mode') in ['videotoolbox','software']:job['encoding_mode']=data['encoding_mode']
    if name=='frames' and job.get('total_frames'):
        job['message']=f'أرسم الفريمات: {job.get("rendered_frames",0)} / {job["total_frames"]} · {job.get("progress",0):g}%'

def monitored(cmd,log,job,timeout,cwd=None,env=None):
    """Tail bounded local progress, keep full diagnostics, kill children on timeout."""
    log=Path(log);started=time.monotonic();pending=''
    with log.open('w') as output,log.open() as reader:
        proc=subprocess.Popen(cmd,cwd=cwd,env=env,stdout=output,stderr=subprocess.STDOUT,
                              start_new_session=os.name!='nt')
        try:
            while True:
                pending+=reader.read()
                lines=pending.split('\n');pending=lines.pop()
                for line in lines:event(job,line)
                if proc.poll() is not None:
                    pending+=reader.read()
                    for line in pending.splitlines():event(job,line)
                    return proc.returncode
                if time.monotonic()-started>timeout:raise subprocess.TimeoutExpired(cmd,timeout)
                time.sleep(.25)
        except BaseException:
            if proc.poll() is None:
                if os.name!='nt':os.killpg(proc.pid,signal.SIGKILL)
                else:proc.kill()
            proc.wait();raise
