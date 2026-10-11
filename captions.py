"""Map cached automatic source transcripts to editable global overlay times."""
import copy, math, uuid

def from_transcript(p,clip,record,mode='words'):
    if mode not in ['words','segments']:raise ValueError('اختار كلمات أو جمل')
    transcript=(record or {}).get('transcript',{})
    if transcript.get('status')!='transcribed':raise ValueError('ماكو تفريغ كلام كامل؛ استخدم التفريغ المحلي أولاً')
    offset=sum(c['end']-c['start'] for c in p['timeline'][:p['timeline'].index(clip)])
    items=[]
    for s in transcript.get('segments',[]):
        if mode=='words' and s['end']>clip['start'] and s['start']<clip['end'] and not s.get('words'):raise ValueError('هذا التفريغ ما بيه توقيت كلمات؛ اختار جمل أو قسّمها يدوياً')
        items.extend(s.get('words',[]) if mode=='words' else [s])
    layers=[]
    for item in items:
        text=str(item.get('text','')).strip();a=max(clip['start'],float(item['start']));b=min(clip['end'],float(item['end']))
        if not text or not math.isfinite(a+b) or b<=a:continue
        layers.append({'id':uuid.uuid4().hex[:12],'type':'text','name':('تفريغ آلي · '+text)[:100],'text':text,'start':round(offset+a-clip['start'],4),'end':round(offset+b-clip['start'],4),'x':50,'y':63,'width':75,'font':p.get('typography',{}).get('font','Hacen Beirut'),'fontSize':76,'color':'#ffffff','opacity':1,'rotation':0,'motion':'plain','enterDuration':0,'exitDuration':0,'exitMotion':'none','enabled':True})
    if not layers:raise ValueError('ماكو كلام بهالجزء حسب التفريغ المحفوظ')
    if len(p.get('layers',[]))+len(layers)>100:raise ValueError('راح تتجاوز 100 طبقة؛ قصّ جزء أقصر أو اختار جمل')
    return layers
