"""Local Silero VAD + MLX Whisper. Reads full audio; keeps timecodes in source seconds."""
import json, math, os, subprocess, sys
from pathlib import Path

def write(path,obj):
    tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(obj,ensure_ascii=False)); tmp.replace(path)

def clean_segments(raw,offset,duration,intervals):
    accepted=[]; uncertain=[]
    for seg in raw:
        text=seg.get('text','').strip(); start=max(0,float(seg['start'])+offset); end=min(duration,float(seg['end'])+offset)
        if not text or not math.isfinite(start+end) or end<=start: continue
        overlap=sum(max(0,min(end,b)-max(start,a)) for a,b in intervals)
        bad=(float(seg.get('no_speech_prob',0))>.6 or float(seg.get('avg_logprob',0))<-1 or float(seg.get('compression_ratio',0))>2.4 or overlap<min(.15,(end-start)*.2))
        item={'start':round(start,3),'end':round(end,3),'text':text,'words':[],'needs_review':True}
        item['asr_quality']={k:float(seg[k]) for k in ['avg_logprob','no_speech_prob','compression_ratio'] if k in seg and math.isfinite(float(seg[k]))}
        if bad:
            uncertain.append({**item,'reason':'ضعف دليل الكلام أو نتيجة التفريغ؛ ما نعتمد النص كحقيقة'}); continue
        for w in seg.get('words',[]):
            a=max(start,float(w['start'])+offset); b=min(end,float(w['end'])+offset)
            if b>a:
                word={'start':round(a,3),'end':round(b,3),'text':w['word'].strip()}
                if w.get('probability') is not None and math.isfinite(float(w['probability'])):word['asr_probability']=float(w['probability'])
                item['words'].append(word)
        accepted.append(item)
    return accepted,uncertain

def main():
    import numpy as np
    import torch
    from silero_vad import load_silero_vad, get_speech_timestamps
    src,folder=sys.argv[1],Path(sys.argv[2]); folder.mkdir(parents=True,exist_ok=True)
    pcm=folder/'audio.f32'; progress=folder/'speech-progress.json'; output=folder/'transcript.json'
    torch.set_num_threads(1)
    write(progress,{'message':'أستخرج الصوت الكامل محلياً…'})
    try:
        subprocess.run(['ffmpeg','-v','error','-i',src,'-vn','-ac','1','-ar','16000','-f','f32le','-y',str(pcm)],check=True,capture_output=True)
        if pcm.stat().st_size==0: raise ValueError('مسار الصوت فارغ')
        x=np.memmap(pcm,dtype=np.float32,mode='r'); duration=len(x)/16000
        # VAD examines the full soundtrack in bounded 5-minute blocks.
        vad=load_silero_vad(); intervals=[]
        for start in range(0,len(x),16000*300):
            write(progress,{'message':f'أفحص وجود الكلام: {start/16000:.0f} / {duration:.0f} ثانية'})
            for s in get_speech_timestamps(torch.from_numpy(np.array(x[start:start+16000*300])),vad,sampling_rate=16000,threshold=.5,min_speech_duration_ms=250,speech_pad_ms=120):
                intervals.append(((start+s['start'])/16000,(start+s['end'])/16000))
        result={'status':'no_speech_detected','segments':[],'uncertain':[],'engine':'Silero VAD + MLX Whisper large-v3-turbo','reviewed':False,'duration':duration,'speech_intervals':intervals,'coverage':'full_audio','language':None}
        if intervals:
            import mlx_whisper
            # Never fetch a model or send audio remotely from the worker.
            base=Path.home()/'.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots'
            models=[p for p in base.glob('*') if (p/'weights.safetensors').exists()]
            model=os.environ.get('SADEQ_ASR_MODEL') or (str(models[-1]) if models else None)
            if not model or not Path(model).exists(): raise ValueError('موديل الكلام المحلي مو موجود؛ شغّل setup-transcription.command')
            # Group speech with context, split at nearby silence, maximum ~28 seconds.
            windows=[]; a=None; b=None
            for lo,hi in intervals:
                if a is not None and lo-b<=1 and hi-a<=28: b=hi
                else:
                    if a is not None: windows.append((max(0,a-.2),min(duration,b+.2)))
                    a,b=lo,hi
                while b-a>28:
                    windows.append((max(0,a-.2),a+25)); a+=25
            if a is not None: windows.append((max(0,a-.2),min(duration,b+.2)))
            for i,(a,b) in enumerate(windows):
                write(progress,{'message':f'أفرّغ الكلام: {i+1} / {len(windows)} · {a:.0f} ثانية'})
                raw=mlx_whisper.transcribe(np.array(x[int(a*16000):int(b*16000)]),path_or_hf_repo=model,word_timestamps=True,condition_on_previous_text=False,temperature=0.0,no_speech_threshold=.6,hallucination_silence_threshold=2)
                good,bad=clean_segments(raw.get('segments',[]),a,duration,intervals)
                result['segments']+=good; result['uncertain']+=bad; result['language']=raw.get('language')
                # Partial checkpoints are inspectable, never mistaken for a complete transcript.
                write(folder/'transcript-partial.json',{**result,'status':'partial'})
            result['segments'].sort(key=lambda s:s['start'])
            result['status']='transcribed' if result['segments'] else 'speech_uncertain'
        write(output,result)
    finally:
        if pcm.exists(): pcm.unlink()

if __name__=='__main__': main()
