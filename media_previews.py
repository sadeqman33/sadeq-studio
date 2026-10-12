"""Private, cached source thumbnails and real amplitude envelopes for the editor."""
import array, hashlib, json, math, os, subprocess, threading, uuid
from pathlib import Path

LIMIT=threading.Semaphore(2)
def build(asset,start,end,folder,ffmpeg,has_audio,voice=False):
    source=Path(asset['path']);stat=source.stat();signature=(stat.st_size,stat.st_mtime_ns)
    if not all(math.isfinite(v) for v in [start,end]) or start<0 or end<=start or end-start>3600:
        raise ValueError('مدى صور التايم لاين لازم بين صفر وساعة')
    key=hashlib.sha256(json.dumps([1,str(source.resolve()),signature,start,end,voice]).encode()).hexdigest()
    dest=Path(folder)/key;cached=dest/'summary.json'
    with LIMIT:
        if cached.is_file():return json.loads(cached.read_text())
        dest.mkdir(parents=True,exist_ok=True);duration=end-start;peaks=[];thumbnails=[]
        def run(args,timeout=60):
            r=subprocess.run([ffmpeg,'-v','error',*args],capture_output=True,timeout=timeout)
            if r.returncode:raise ValueError('ما قدرت أجهّز صور أو صوت التايم لاين: '+r.stderr.decode(errors='replace')[-350:])
            return r.stdout
        if has_audio:
            pcm=run(['-ss',str(start),'-i',str(source),'-t',str(duration),'-vn','-ac','1','-ar','8000','-f','s16le','pipe:1'])
            samples=array.array('h');samples.frombytes(pcm)
            if os.sys.byteorder!='little':samples.byteswap()
            count=min(1200,max(64,math.ceil(duration*16)));stride=max(1,math.ceil(len(samples)/count))
            peaks=[max((abs(v) for v in samples[i:i+stride]),default=0)/32768 for i in range(0,len(samples),stride)]
            maximum=max(peaks,default=0)
            if maximum:peaks=[round(p/maximum,4) for p in peaks]
        if not voice:
            for i,fraction in enumerate([.12,.5,.88]):
                image=dest/f'{i}.jpg';temp=dest/(uuid.uuid4().hex+'.jpg')
                try:
                    run(['-ss',str(start+duration*fraction),'-i',str(source),'-frames:v','1','-vf','scale=160:90:force_original_aspect_ratio=decrease,pad=160:90:(ow-iw)/2:(oh-ih)/2:black','-threads','1','-y',str(temp)])
                    if not temp.is_file():raise ValueError('صورة المعاينة غير موجودة')
                    temp.replace(image);thumbnails.append(i)
                finally:temp.unlink(missing_ok=True)
        after=source.stat()
        if (after.st_size,after.st_mtime_ns)!=signature:raise ValueError('الفيديو تغيّر أثناء تحضير التايم لاين')
        result={'key':key,'peaks':peaks,'has_audio':has_audio,'thumbnails':thumbnails,'start':start,'end':end,'waveform':'normalized_source_peak_amplitude'}
        temp=dest/(uuid.uuid4().hex+'.json');temp.write_text(json.dumps(result));temp.replace(cached)
        return result
