"""Local voice-over assets, editable timing and offline export mixing.

Generation uses the separate local VoiceStudio bridge. Mixing and imports stay local.
"""
import base64, binascii, hashlib, json, math, subprocess, time, uuid
from pathlib import Path

MAX_BYTES=20*1024*1024
MAX_SECONDS=600
DEFAULT={'text':'','dialect':'عراقية','voice':'','voiceProfile':'default','direction':'','enabled':False,
         'asset':None,'trimStart':0,'trimEnd':0,'offset':0,'gain':1,'originalGain':1}
SCHEMA={'type':'object','properties':{'text':{'type':'string'},'direction':{'type':'string'},'uncertainties':{'type':'array','items':{'type':'string'}}},'required':['text','direction','uncertainties'],'additionalProperties':False}

def settings(p,raw=None):
    raw=p.get('voiceover',{}) if raw is None else raw
    if not isinstance(raw,dict): raise ValueError('إعدادات التعليق الصوتي غير صالحة')
    out={**DEFAULT,**{k:v for k,v in raw.items() if k in DEFAULT}}
    for k,limit in [('text',6000),('dialect',120),('voice',160),('voiceProfile',160),('direction',1200)]:
        if not isinstance(out[k],str) or len(out[k])>limit: raise ValueError('نص أو إعداد التعليق طويل أو غير صالح')
    if not isinstance(out['enabled'],bool): raise ValueError('اختيار التعليق الصوتي غير صالح')
    for k,limit in [('trimStart',MAX_SECONDS),('trimEnd',MAX_SECONDS),('offset',MAX_SECONDS),('gain',1),('originalGain',1)]:
        try: n=float(out[k])
        except (ValueError,TypeError): raise ValueError('توقيت أو مستوى الصوت غير صالح')
        if not math.isfinite(n) or not 0<=n<=limit: raise ValueError('توقيت أو مستوى الصوت خارج الحدود')
        out[k]=n
    asset=next((a for a in p.get('voiceover_assets',[]) if a['id']==out['asset']),None)
    if out['asset'] is not None:
        if not asset: raise ValueError('ملف التعليق مو مربوط بهالمشروع')
        if not 0<=out['trimStart']<out['trimEnd']<=asset['duration']+.001: raise ValueError('قص التعليق لازم يكون داخل مدة الصوت')
        out['trimEnd']=min(out['trimEnd'],asset['duration'])
    elif out['enabled']: raise ValueError('استورد ملف التعليق أولاً')
    return out

def active(p):
    v=settings(p)
    if not v['enabled']: return None
    asset=next(a for a in p['voiceover_assets'] if a['id']==v['asset'])
    if not Path(asset['path']).is_file(): raise ValueError('ملف التعليق الصوتي مو موجود؛ استورده مرة ثانية')
    return v,asset

def audio_duration(path,ffprobe):
    r=subprocess.run([ffprobe,'-v','error','-show_format','-show_streams','-of','json',str(path)],capture_output=True,text=True,timeout=25)
    if r.returncode: raise ValueError('ما قدرت أقرأ ملف الصوت')
    d=json.loads(r.stdout)
    if any(s['codec_type']=='video' for s in d['streams']) or not any(s['codec_type']=='audio' for s in d['streams']): raise ValueError('اختار ملف صوت MP3 / WAV / M4A، مو فيديو')
    duration=float(d['format'].get('duration',0))
    if not math.isfinite(duration) or not 0<duration<=MAX_SECONDS: raise ValueError('التعليق لازم يكون بين صفر و10 دقايق')
    return duration

def import_audio(payload,folder,ffprobe,ffmpeg,command):
    try: data=base64.b64decode(payload['audio'],validate=True)
    except (KeyError,TypeError,binascii.Error): raise ValueError('ملف الصوت ما وصل بصورة صحيحة')
    if not 0<len(data)<=MAX_BYTES: raise ValueError('ملف الصوت لازم يكون أقل من 20 MB')
    name=str(payload.get('name','تعليق صوتي')).replace('\\','/').split('/')[-1][:200]
    if Path(name).suffix.lower() not in {'.mp3','.wav','.m4a','.aac','.ogg','.flac'}: raise ValueError('اختار ملف صوت MP3 / WAV / M4A / AAC / OGG / FLAC')
    asset_id=uuid.uuid4().hex[:16]; dest=folder/'voiceovers'/asset_id; dest.mkdir(parents=True)
    src=dest/('original'+Path(name).suffix.lower()); src.write_bytes(data)
    try:
        audio_duration(src,ffprobe)
        target=dest/'audio.wav'
        command([ffmpeg,'-v','error','-i',str(src),'-map','0:a:0','-vn','-t',str(MAX_SECONDS),'-ac','2','-ar','48000','-c:a','pcm_s16le','-y',str(target)],180)
        duration=audio_duration(target,ffprobe)
    except Exception:
        # Failed new imports are private disposable staging files, never originals.
        import shutil
        shutil.rmtree(dest)
        raise
    return {'id':asset_id,'name':name,'path':str(target),'duration':duration,
            'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'at':time.time(),
            'source':'manual_import','provider_hint':'local_file','kind':'music' if payload.get('kind')=='music' else 'voiceover'}

def mix_export(p,out,total,ffmpeg,command,j,has_audio=True):
    selected=active(p)
    if not selected: return
    v,asset=selected
    if v['offset']>=total: raise ValueError('بداية التعليق بعد نهاية الفيديو؛ عدّل توقيته')
    j['message']='أمزج الموسيقى وأخففها تحت كلامك…' if asset.get('kind')=='music' else 'أمزج التعليق الصوتي ويه نسختك محلياً…'
    final=out/'final.mp4'; mixed=out/'with-voiceover.mp4'
    # Render length is fixed by video. Never extend footage or silently speed speech.
    # Freeze local audio and editable settings next to this version's composition.
    import shutil
    frozen=out/'voiceover.wav'; shutil.copy2(asset['path'],frozen)
    (out/'voiceover.json').write_text(json.dumps({'settings':v,'asset':{k:x for k,x in asset.items() if k!='path'},'video_duration':total,'truncated':v['offset']+v['trimEnd']-v['trimStart']>total+.001},ensure_ascii=False,indent=2))
    start,end=v['trimStart'],v['trimEnd']; delay=round(v['offset']*48000)
    # Both renderers emit an audio track, including silence for muted footage.
    original='0:a' if has_audio else '2:a'
    filters=f'[{original}]volume={v["originalGain"]},apad[original];[1:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,volume={v["gain"]},adelay={delay}S:all=1,apad[vo];[original][vo]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95:level=false:latency=1[a]'
    if asset.get('kind')=='music':
        audible=min(end-start,total-v['offset']); fade=max(0,audible-.6)
        filters=f'[{original}]volume={v["originalGain"]},apad,asplit=2[original][key];[1:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS,volume={v["gain"]},afade=t=in:d=0.35,afade=t=out:st={fade}:d=0.6,adelay={delay}S:all=1,apad[bed];[bed][key]sidechaincompress=threshold=0.035:ratio=3:attack=25:release=220[duck];[original][duck]amix=inputs=2:duration=longest:normalize=0,alimiter=limit=0.95:level=false:latency=1[a]'
    cmd=[ffmpeg,'-v','error','-i',str(final),'-i',str(frozen)]
    if not has_audio: cmd+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
    command(cmd+['-filter_complex',filters,'-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-ar','48000','-ac','2','-t',str(total),'-movflags','+faststart','-y',str(mixed)],180)
    mixed.replace(final)
