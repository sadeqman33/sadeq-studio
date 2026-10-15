"""Explicit, user-started in-Studio creation. No changes to existing work edits."""
import copy, json, math, unicodedata, uuid

DEFAULTS={'preset':'product','pace':'balanced','duration':30,'captions':'pairs','features':True,'icons':True,'motion':'riseUp','font':'Hacen Beirut','position':'lower','audio':'original','ratio':'9:16','resolution':'1080','fps':30,'output':'render'}
CHOICES={'preset':['product','story','educational','montage'],'pace':['calm','balanced','energetic'],'duration':[15,30,45,60],'captions':['off','words','pairs'],'motion':['plain','riseUp','blurIn','rubberPop'],'font':['Hacen Beirut','Alexandria'],'position':['lower','middle'],'audio':['original','mute'],'ratio':['9:16','16:9'],'resolution':['1080','4k'],'fps':[30,60],'output':['render','draft']}

def settings(raw):
    if not isinstance(raw,dict) or set(raw)-set(DEFAULTS):raise ValueError('خيارات إنشاء الفيديو غير صالحة')
    value={**DEFAULTS,**raw}
    for key,options in CHOICES.items():
        if isinstance(value[key],bool) or value[key] not in options:raise ValueError('خيار غير صالح: '+key)
    for key in ['features','icons']:
        if not isinstance(value[key],bool):raise ValueError('خيار غير صالح: '+key)
    return value

def prepare(p,d):
    import server as s
    if p.get('active_work_id')!=d.get('work_id') or s.edit_fingerprint(p)!=d.get('base_fingerprint'):raise ValueError('الفيديو تغيّر؛ حدّث الصفحة قبل الإنشاء')
    if p.get('memory_document_warnings'):raise ValueError('صلّح ملفات ذاكرة المشروع قبل الإنشاء')
    ids=d.get('assets');known={a['id']:a for a in p['assets']}
    if not isinstance(ids,list) or not 1<=len(ids)<=12 or any(not isinstance(i,str) or i not in known for i in ids) or len(set(ids))!=len(ids):raise ValueError('اختار من مقطع إلى 12 مقطع من هالمشروع')
    request=d.get('request','')
    if not isinstance(request,str) or not request.strip() or len(request)>2000:raise ValueError('اكتب فكرة الفيديو، لحد 2000 حرف')
    opts=settings(d.get('settings',{}))
    if not s.CODEX:raise ValueError('الإيجنت يحتاج Codex CLI على هالجهاز')
    engine='remotion' if s.rm.ready() else 'hyperframes'
    if not (s.rm.ready() or s.hf.ready()):raise ValueError('جهّز محرك الفيديو من إعدادات Studio أولاً')
    if not s.typo.FONTS[opts['font']].is_file():raise ValueError('الخط المختار مو مثبت على الجهاز')
    return {'request':request.strip(),'assets':ids,'settings':opts,'renderer':engine,'fingerprints':{i:s.vl.fingerprint(known[i]) for i in ids}}

def clean(text):
    return ' '.join(''.join(ch for ch in text if not unicodedata.category(ch).startswith('P')).split())

def speech_layers(p,clip,record,opts,offset):
    transcript=(record or {}).get('transcript',{})
    if transcript.get('status')=='no_speech_detected':return []
    if transcript.get('status')!='transcribed':raise ValueError('الكابشن يحتاج تفريغ كلام ناجح؛ جرّب التفريغ أو اختار بدون كابشن')
    words=[]
    for segment in transcript.get('segments',[]):
        if segment['end']<=clip['start'] or segment['start']>=clip['end']:continue
        if not segment.get('words'):raise ValueError('التفريغ ما بيه توقيت كلمات؛ أعد التفريغ أو اختار بدون كابشن')
        for item in segment['words']:
            a=max(clip['start'],float(item['start']));b=min(clip['end'],float(item['end']));text=clean(str(item.get('text','')))
            if text and math.isfinite(a+b) and b>a:
                # A timestamp can contain multiple tokens; split without inventing words.
                tokens=text.split();step=(b-a)/len(tokens)
                words.extend((token,offset+a-clip['start']+k*step,offset+a-clip['start']+(k+1)*step) for k,token in enumerate(tokens))
    rows=[];size=2 if opts['captions']=='pairs' else 1
    while words:
        group=[words.pop(0)]
        if size==2 and words and 0<=words[0][1]-group[-1][2]<.35:group.append(words.pop(0))
        row=text_layer(' '.join(w[0] for w in group),group[0][1],group[-1][2],opts)
        row.update(name='كابشن آلي · '+row['text'],track='caption',fontSize=54,y=68,width=66,motion='fade',enterDuration=min(.12,(row['end']-row['start'])/3),exitDuration=min(.1,(row['end']-row['start'])/3))
        row.pop('bankMotion',None);rows.append(row)
    return rows

def text_layer(text,start,end,opts):
    row={'id':uuid.uuid4().hex[:12],'type':'text','name':'ميزة · '+text[:80],'track':'title','text':text,'start':start,'end':end,'x':50,'y':64 if opts['position']=='lower' else 48,'width':62,'font':opts['font'],'fontSize':66,'color':'#ffffff','motion':'plain','enterDuration':.32,'exitDuration':.18,'exitMotion':'fade','enabled':True}
    if opts['motion']!='plain':row['bankMotion']=opts['motion']
    return row

def assemble(p,result,opts,ids):
    import server as s
    clips=result.get('clips',[])
    if not isinstance(clips,list) or not 1<=len(clips)<=30 or any(c.get('asset') not in ids for c in clips):raise ValueError('الإيجنت لازم يستخدم مقاطعك المختارة فقط')
    candidate=copy.deepcopy(p);tl=[];layers=[];offset=0;known_icons={a['id'] for a in p.get('overlay_assets',[]) if a.get('kind')=='icon'}
    for c in clips:
        icon=c.get('icon','')
        if icon and icon not in known_icons:raise ValueError('أيقونة الإيجنت مو موجودة بالمشروع')
        row={k:v for k,v in c.items() if k!='icon'};row.update(id=uuid.uuid4().hex[:12],mute=opts['audio']=='mute',text='',motion='plain')
        tl.append(row)
    candidate['timeline']=tl;s.validate_timeline(candidate,tl)
    if sum(c['end']-c['start'] for c in tl)>90:raise ValueError('المسودة أطول من 90 ثانية؛ جرّب طلب أقصر')
    for source,clip in zip(clips,tl):
        length=clip['end']-clip['start'];feature=None
        if opts['features'] and source.get('text','').strip():
            feature=text_layer(source['text'].strip(),offset+source['textStart'],offset+source['textEnd'],opts);layers.append(feature)
            if opts['icons'] and source.get('icon'):
                feature.update(x=44,width=38)
                icon={'id':uuid.uuid4().hex[:12],'type':'icon','name':'أيقونة · '+source['text'][:70],'asset':source['icon'],'start':feature['start'],'end':feature['end'],'x':70,'y':feature['y'],'width':12,'motion':'plain','enterDuration':.32,'exitDuration':.18,'exitMotion':'fade','enabled':True}
                if opts['motion']!='plain':icon['bankMotion']=opts['motion']
                layers.append(icon)
        if opts['captions']!='off':
            asset=next(a for a in p['assets'] if a['id']==clip['asset'])
            if asset.get('audio',True):
                for caption in speech_layers(candidate,clip,s.vl.current_record(p,asset),opts,offset):
                    spans=[(caption['start'],caption['end'])]
                    if feature:spans=[(a,b) for a,b in [(caption['start'],min(caption['end'],feature['start'])),(max(caption['start'],feature['end']),caption['end'])] if b-a>.06]
                    for a,b in spans:
                        item=copy.deepcopy(caption);item.update(id=uuid.uuid4().hex[:12],start=a,end=b);layers.append(item)
        offset+=length
    candidate.update(layers=s.ly.validate(candidate,layers),ratio=opts['ratio'],renderer=p.get('renderer','remotion'),typography={'font':opts['font'],'style':'classic'},export_settings={'resolution':opts['resolution'],'fps':opts['fps']},motion_style='plain',creation_settings=opts)
    candidate['voiceover']=s.vo.settings(candidate);candidate['voiceover'].update(enabled=False,asset=None,trimStart=0,trimEnd=0,originalGain=1)
    return candidate

def run(pid,spec,j):
    import server as s
    opts=spec['settings'];ids=spec['assets'];j.update(stage='analysis',message='أراجع المقاطع المختارة ومعرفة المشروع…')
    p=s.project(pid)
    needed=set(ids)|set(p.get('approved_reference_ids',[]))
    for a in p['assets']:
        if a['id'] in needed:s.analyze_one(pid,a,j)
    p=s.project(pid)
    if not p.get('analysis_at'):
        with s.LOCK:
            p=s.project(pid);p['knowledge_documents']=s.cache_documents(p);p['analysis_at']=s.time.time();s.save(p)
    if not s.pm.memory(p).get('input_signature'):s.learn_memory(pid,j)
    p=s.project(pid);selected=[a for a in p['assets'] if a['id'] in ids]
    j.update(stage='planning',message='الإيجنت يرتّب القصة والكتابة حسب اختياراتك…')
    text,meta,frames=s.draft_context(p,j,selected);schema=copy.deepcopy(s.PRODUCTION_SCHEMA)
    icons=[{'id':a['id'],'name':a['name']} for a in p.get('overlay_assets',[]) if a.get('kind')=='icon'] if opts['icons'] else []
    schema['properties']['clips']['items']['properties']['icon']={'type':'string','enum':['']+[a['id'] for a in icons]};schema['properties']['clips']['items']['required'].append('icon')
    prompt=s.RULES+'\n'+s.se.RULES+'\nCreate a complete editable cut using only selected source ids. Preserve coherent speech. Respect user settings and saved identity. Duration is a target, not permission to cut a spoken word. Maximum 90 seconds/30 clips. Do not repeat footage to pad duration. Motion is provided by the selected layer preset, no camera moves or generated scenes. Text is a short verified feature label, NOT a speech caption. At most 8 words per feature. Use an empty label when it adds no value. If features=false, ALL text must be empty. textStart/textEnd are relative to each trimmed clip, must satisfy 0 <= textStart < textEnd <= end-start even for empty text. Keep feature durations brief so spoken captions have room. textY=64, motion=plain. Choose an icon ONLY if its meaning is clear and matches the feature, otherwise empty string. No invented assets.\n'+json.dumps({'settings':opts,'request':spec['request'],'profile':p['profile'],'assets':meta,'available_icons':icons},ensure_ascii=False)+'\nSaved evidence:\n'+text
    result=s.ask_agent(pid,prompt,schema,frames,j)
    j.update(stage='layers',message='أجهّز طبقات الكتابة والحركات والكابشن…')
    with s.LOCK:
        latest=s.project(pid)
        if spec['fingerprints']!={a['id']:s.vl.fingerprint(a) for a in latest['assets'] if a['id'] in ids}:raise ValueError('ملف مصدر تغيّر أثناء التخطيط؛ أعد الإنشاء')
        candidate=assemble(latest,result,opts,ids);candidate['renderer']=spec['renderer'];candidate.update(draft_reason=result['reason'],draft_origin='studio_agent',draft_memory_revision=s.pm.memory(latest)['revision'])
        s.history(latest);s.works.checkpoint(latest,s.DATA/pid);s.works.begin(candidate,s.DATA/pid,spec['request'][:100]);s.save(candidate)
    j['work_id']=candidate['active_work_id']
    if opts['output']=='render':
        j.update(stage='render',message='المسودة جاهزة؛ أصدّر الفيديو…');s.export(pid,j)
    j.update(stage='done',completion_message='فيديوك جاهز، وكل الطبقات قابلة للتعديل ✅' if opts['output']=='draft' else 'الفيديو وملف MP4 جاهزين ✅')
