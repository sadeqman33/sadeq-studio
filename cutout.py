"""Local selfie background processing. No footage uploads or source writes."""
import hashlib,json,math,os,re,subprocess,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent
VERSION='mediapipe-selfie-1'
MODEL_URL='https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_segmenter/float16/1/selfie_segmenter.tflite'
MODEL_SHA256='191ac9529ae506ee0beefa6b2c945a172dab9d07d1e802a290a4e4038226658b'
def python_path():return Path(os.environ.get('SADEQ_CUTOUT_PYTHON',str(ROOT/'.venv-cutout/bin/python'))).expanduser()
def model_path():return Path(os.environ.get('SADEQ_CUTOUT_MODEL',str(ROOT/'models/selfie_segmenter.tflite'))).expanduser()
def ready():
    model=model_path()
    return python_path().exists() and model.exists() and hashlib.sha256(model.read_bytes()).hexdigest()==MODEL_SHA256
def setup_model():
    path=model_path();path.parent.mkdir(parents=True,exist_ok=True)
    data=urllib.request.urlopen(MODEL_URL,timeout=60).read()
    if hashlib.sha256(data).hexdigest()!=MODEL_SHA256:raise ValueError('Selfie model checksum mismatch')
    temp=path.with_suffix('.tmp');temp.write_bytes(data);temp.replace(path)
    print('محرك عزل السيلفي المحلي جاهز')
def options(mode,color):
    if mode not in ['blur','color']:raise ValueError('اختار تمويه أو لون ثابت للخلفية')
    if not isinstance(color,str) or not re.fullmatch('#[a-fA-F0-9]{6}',color):raise ValueError('لون الخلفية غير صالح')
    return {'mode':mode,'color':color.lower()}
def process(asset,start,end,out,mode,color,probe,ffmpeg,j):
    if not ready():raise ValueError('جهّز عزل الخلفية عبر setup-cutout.command أولاً')
    opt=options(mode,color);start=float(start);end=float(end);meta=probe(Path(asset['path']))
    if not math.isfinite(start) or not math.isfinite(end) or not 0<=start<end<=meta['duration']+.001:raise ValueError('قص العزل خارج مدة المصدر')
    if end-start>120:raise ValueError('العزل لكل جزء لحد دقيقتين؛ قسّم المقطع أولاً')
    if meta.get('hdr'):raise ValueError('العزل يحتاج مصدر SDR؛ حوّل نسخة من HDR أولاً')
    out.mkdir(parents=True,exist_ok=True);spec={**opt,'source':asset['path'],'start':start,'end':end,'ffmpeg':ffmpeg,'model':str(model_path()),'output':str(out/'processed.mp4'),'version':VERSION}
    (out/'request.json').write_text(json.dumps(spec,ensure_ascii=False,allow_nan=False))
    env=os.environ.copy();env['MPLCONFIGDIR']=str(ROOT/'.cache-cutout/mpl');env['OMP_NUM_THREADS']='2'
    with (out/'worker.log').open('w') as log:
        worker=subprocess.Popen([str(python_path()),str(ROOT/'cutout_worker.py'),str(out/'request.json')],stdout=log,stderr=log,env=env)
        deadline=time.monotonic()+max(180,(end-start)*15)
        try:
            while worker.poll() is None:
                if time.monotonic()>deadline:raise ValueError('معالجة العزل أخذت أكثر من الوقت المحدد')
                progress=out/'progress.json'
                if progress.exists():
                    try:
                        p=json.loads(progress.read_text());j['message']=f"أعزل الشخص: {p['frame']} / {p['total']} إطار";j['progress']=min(99,round(p['frame']/p['total']*100))
                    except (ValueError,KeyError,ZeroDivisionError):pass
                time.sleep(.2)
            if worker.returncode:raise ValueError('معالجة العزل توقفت؛ شوف worker.log بالمجلد المحلي: '+str(out))
        finally:
            if worker.poll() is None:worker.terminate();worker.wait(timeout=10)
    result=probe(out/'processed.mp4')
    if abs(result['duration']-(end-start))>.08:raise ValueError('مدة نسخة العزل تختلف عن الجزء المختار')
    j['progress']=100
    return out/'processed.mp4',result
if __name__=='__main__':setup_model()
