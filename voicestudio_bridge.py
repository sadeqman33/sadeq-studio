"""VoiceStudio's separate loopback service; never upload to a hosted provider."""
import base64, json, os, socket, urllib.error, urllib.parse, urllib.request

MODEL='mlx-community/VoxCPM2-8bit'
ENGINE='mlx-audio'
MAX_AUDIO=20*1024*1024

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        raise ValueError('VoiceStudio رجّع تحويل لرابط آخر؛ التوليد المحلي توقف')

def endpoint():
    url=os.environ.get('SADEQ_VOICESTUDIO_URL','http://127.0.0.1:3900').rstrip('/')
    p=urllib.parse.urlsplit(url)
    if p.scheme!='http' or p.hostname not in ('127.0.0.1','localhost','::1') or p.username or p.password or p.path or p.query or p.fragment:
        raise ValueError('ربط VoiceStudio لازم يكون عنوان localhost فقط')
    return url

def request(path,payload=None,timeout=15,audio=False):
    headers={'Accept':'audio/wav' if audio else 'application/json'}
    token=os.environ.get('SADEQ_VOICESTUDIO_API_KEY')
    if token:headers['Authorization']='Bearer '+token
    data=None
    if payload is not None:data=json.dumps(payload,ensure_ascii=False).encode();headers['Content-Type']='application/json'
    req=urllib.request.Request(endpoint()+path,data=data,headers=headers)
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect()).open(req,timeout=timeout) as r:
            limit=MAX_AUDIO if audio else 4*1024*1024
            raw=r.read(limit+1)
            if len(raw)>limit:raise ValueError('نتيجة VoiceStudio أكبر من الحد؛ قصّر النص')
            if audio:
                if not (raw[:4]==b'RIFF' and raw[8:12]==b'WAVE'):raise ValueError('VoiceStudio ما رجّع ملف WAV صالح')
                return raw
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        if e.code in (401,403):raise ValueError('VoiceStudio يحتاج مصادقة محلية؛ راجع إعداد الربط') from e
        detail=e.read(2000).decode(errors='replace')
        raise ValueError(f'VoiceStudio توقف ({e.code}): {detail[:500]}') from e
    except (urllib.error.URLError,TimeoutError,socket.timeout) as e:
        raise ValueError('VoiceStudio غير متصل أو انتهت مهلة الانتظار؛ افتح التطبيق وافحصه قبل إعادة التوليد') from e

def status():
    result={'connected':False,'ready':False,'provider':'VoiceStudio','model':MODEL,'engine':ENGINE,'voices':[]}
    try:
        health=request('/health');inventory=request('/v1/audio/voices');engines=request('/engines/tts');models=request('/models')
        installed=any(m.get('repo_id')==MODEL and m.get('installed') for m in models.get('models',[]))
        engine=next((e for e in engines.get('backends',[]) if e.get('id')==ENGINE),{})
        selected=engines.get('active')==ENGINE and engines.get('active_model')==MODEL
        ready=bool(installed and selected and engine.get('available'))
        voices=[{'id':'default','name':'صوت مولّد · بدون تقليد شخص'}]
        voices += [{'id':v['voice_id'],'name':str(v.get('name',v['voice_id']))[:160]} for v in inventory.get('voices',[]) if v.get('type')=='profile' and isinstance(v.get('voice_id'),str)]
        result.update(connected=True,ready=ready,installed=bool(installed),selected=selected,voices=voices,device=engine.get('effective_device'),version=health.get('version'),message='جاهز · VoxCPM2 على جهازك' if ready else 'VoiceStudio متصل؛ ثبّت واختر VoxCPM2-8bit عبر محرّك MLX-Audio')
    except (ValueError,KeyError,TypeError) as e:result['message']=str(e)
    return result

def generate(text,voice='default',direction=''):
    if not isinstance(text,str) or not text.strip() or len(text)>4096:raise ValueError('اكتب نص تعليق من 1 إلى 4096 حرف')
    if not isinstance(direction,str) or len(direction)>1600:raise ValueError('توجيه الأداء طويل أو غير صالح')
    state=status()
    if not state['ready']:raise ValueError(state['message'])
    if voice not in {v['id'] for v in state['voices']}:raise ValueError('اختار صوت موجود داخل VoiceStudio')
    raw=request('/v1/audio/speech',{'model':ENGINE,'voice':voice,'input':text.strip(),'language':'ar','instruct':direction,'response_format':'wav','seed':42},timeout=900,audio=True)
    return {'name':'VoiceStudio.wav','audio':base64.b64encode(raw).decode(),'kind':'voiceover'}, {'provider':'VoiceStudio','model':MODEL,'engine':ENGINE,'voice':voice,'text':text.strip(),'direction':direction,'language':'ar','seed':42}
