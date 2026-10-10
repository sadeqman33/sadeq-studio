"""Per-source analysis identity and offline speech runner. No source-file writes."""
import hashlib, json, os, subprocess, time
from pathlib import Path

VERSION='library-0.3'
FIELDS=['summary','topics','visual_style','visible_text','speech_notes','uncertainties']
VIDEO_SCHEMA={'type':'object','properties':{k:({'type':'string'} if k=='summary' else {'type':'array','items':{'type':'string'}}) for k in FIELDS},'required':FIELDS,'additionalProperties':False}

def fingerprint(asset):
    f=Path(asset['path']); s=f.stat()
    return hashlib.sha256(json.dumps([VERSION,str(f.resolve()),s.st_size,s.st_mtime_ns]).encode()).hexdigest()

def targets(p,ids=None,all_videos=False):
    # First-ever project analysis always includes every linked source, regardless of selection.
    if not p.get('analysis_at') or all_videos: return list(p['assets'])
    if not isinstance(ids,list) or not ids: raise ValueError('علّم الفيديوات اللي تريد تحللها من المكتبة، أو اختار تحليل الكل')
    known={a['id'] for a in p['assets']}
    if any(i not in known for i in ids): raise ValueError('فيديو مو مربوط بهالمشروع')
    return [a for a in p['assets'] if a['id'] in set(ids)]

def current_record(p,a):
    r=p.get('video_analyses',{}).get(a['id'])
    try: return r if r and r.get('fingerprint')==fingerprint(a) else None
    except OSError: return None

def transcribe(root,folder,asset,meta,j):
    if not meta['audio']:
        return {'status':'no_audio','segments':[],'uncertain':[],'engine':None,'reviewed':False}
    python=Path(os.environ.get('SADEQ_ASR_PYTHON',str(root/'.venv-asr/bin/python')))
    if not python.exists(): raise ValueError('محرك التفريغ المحلي يحتاج تهيئة: شغّل setup-transcription.command')
    output=folder/'transcript.json'; progress=folder/'speech-progress.json'; log=folder/'speech.log'
    for f in [output,progress]:
        if f.exists(): f.unlink()
    env={**os.environ,'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'}
    with log.open('w') as stream:
        proc=subprocess.Popen([str(python),str(root/'speech_worker.py'),asset['path'],str(folder)],stdout=stream,stderr=stream,env=env)
        started=time.time()
        while proc.poll() is None:
            if progress.exists():
                try:
                    info=json.loads(progress.read_text()); j['message']=j.get('prefix','')+' · '+info['message']
                except (ValueError,OSError,KeyError): pass
            if time.time()-started>max(1800,meta['duration']*4):
                proc.kill(); proc.wait(); raise ValueError('تفريغ المقطع أخذ وقت طويل؛ تگدر تعيد المحاولة ويكمل من المحفوظ')
            time.sleep(.3)
    if proc.returncode or not output.exists(): raise ValueError('فشل التفريغ المحلي: '+log.read_text()[-800:])
    return json.loads(output.read_text())

def timestamp(s):
    return f'{int(s//3600):02d}:{int(s//60)%60:02d}:{s%60:06.3f}'

def transcript_text(record):
    t=record['transcript']
    header='تفريغ آلي يحتاج مراجعة · '+t['status']+'\n'
    return header+'\n'.join(f"[{timestamp(s['start'])} → {timestamp(s['end'])}] {s['text']}" for s in t['segments'])

def transcript_srt(record):
    return '\n\n'.join(f"{i+1}\n{timestamp(s['start']).replace('.',',')} --> {timestamp(s['end']).replace('.',',')}\n{s['text']}" for i,s in enumerate(record['transcript']['segments']))+'\n'
