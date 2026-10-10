"""Original Iraqi creative-review rubric and observed-outcome analytics.
Concepts informed by the three repositories in skills/iraqi-video-review/references/research-notes.md.
No pretrained foreign virality models, copied upstream code, or calibrated probabilities.
"""
import copy, hashlib, json, math, re, uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
VERSION='iraq-creative-review-0.2'
CRITERIA={
    'hook':('وضوح البداية',25),
    'value':('الفائدة للجمهور',20),
    'iraqi_fit':('ملاءمة الجمهور العراقي',15),
    'clarity':('وضوح الصورة والنص',15),
    'proof':('الدليل والثقة',10),
    'cta':('الخطوة المطلوبة',10),
    'audio':('وضوح الكلام والصوت',5),
}
MARKET_DEFAULT={'platform':'instagram','distribution':'organic','objective':'awareness','segment':'','account':'','location':'العراق','script':'','script_source':'draft'}
PLATFORMS={'instagram','tiktok','facebook','youtube'}
OBJECTIVES={'awareness','messages','leads','sales'}

def finite(v,name,maximum=None):
    if isinstance(v,bool): raise ValueError(name+' لازم رقم')
    try: x=float(v)
    except (TypeError,ValueError): raise ValueError(name+' لازم رقم')
    if not math.isfinite(x) or x<0 or (maximum is not None and x>maximum): raise ValueError(name+' غير صالح')
    return x

def market(data=None):
    if data is not None and not isinstance(data,dict): raise ValueError('معلومات الجمهور غير صالحة')
    m={**MARKET_DEFAULT,**(data or {})}
    if m['platform'] not in PLATFORMS or m['distribution'] not in {'organic','paid'} or m['objective'] not in OBJECTIVES: raise ValueError('المنصة أو الهدف غير صالح')
    if m['script_source'] not in {'draft','verified_transcript'}: raise ValueError('نوع النص غير صالح')
    for k,size in [('segment',500),('account',120),('location',120),('script',12000)]: m[k]=str(m[k])[:size]
    return {k:m[k] for k in MARKET_DEFAULT}

def fingerprint(p):
    import project_memory as pm
    # Scores are tied to the same edit, source files, identity and audience context.
    assets={a['id']:a['path'] for a in p['assets']}
    source_state={}
    for c in p['timeline']:
        path=assets.get(c['asset'])
        try:
            stat=Path(path).stat(); source_state[c['asset']]={'path':path,'size':stat.st_size,'mtime_ns':stat.st_mtime_ns}
        except (OSError,TypeError): source_state[c['asset']]={'path':path,'missing':True}
    voice_asset=next((a for a in p.get('voiceover_assets',[]) if a['id']==p.get('voiceover',{}).get('asset')),None)
    if voice_asset:
        try:
            stat=Path(voice_asset['path']).stat();source_state['voiceover']={'size':stat.st_size,'mtime_ns':stat.st_mtime_ns}
        except OSError:source_state['voiceover']={'missing':True}
    obj={'typography':p.get('typography',{'font':'Hacen Beirut','style':'classic'}),'voiceover':p.get('voiceover',{}),'voiceover_assets':[{k:a.get(k) for k in ['id','sha256']} for a in p.get('voiceover_assets',[]) if a['id']==p.get('voiceover',{}).get('asset')],'renderer':p.get('renderer','basic'),'motion_style':p.get('motion_style','plain'),'source_state':source_state,'timeline':p['timeline'],'sources':{c['asset']:assets.get(c['asset']) for c in p['timeline']},'ratio':p.get('ratio','9:16'),'profile':p['profile'],'market':market(p.get('market')),'project_identity':pm.effective(p),'project_notes':pm.memory(p).get('notes',''),'approved_references':p.get('approved_reference_ids',[])}
    return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True,allow_nan=False).encode()).hexdigest()

ITEM={'type':'object','properties':{'score':{'type':['integer','null']},'reason':{'type':'string'},'evidence':{'type':'array','items':{'type':'string'}}},'required':['score','reason','evidence'],'additionalProperties':False}
REVIEW_SCHEMA={'type':'object','properties':{
    'summary':{'type':'string'},
    'criteria':{'type':'object','properties':{k:copy.deepcopy(ITEM) for k in CRITERIA},'required':list(CRITERIA),'additionalProperties':False},
    'fixes':{'type':'array','items':{'type':'object','properties':{'time':{'type':'number'},'change':{'type':'string'},'why':{'type':'string'}},'required':['time','change','why'],'additionalProperties':False}},
    'hook_variants':{'type':'array','items':{'type':'string'}},
    'missing':{'type':'array','items':{'type':'string'}}},
    'required':['summary','criteria','fixes','hook_variants','missing'],'additionalProperties':False}

REVIEW_INSTRUCTIONS='''Review this exact edit for the specified Iraqi audience and objective. Iraq is not one homogeneous audience: use the given segment and location; if absent mark this missing. Iraqi Arabic is a writing preference, not proof of what people in the footage say. Use natural Iraqi wording, avoid forced slang or stereotypes. Treat local relevance as a creative hypothesis, not empirical Iraqi performance evidence. All weights/grades are an editorial rubric, not a trained model.
Evaluate hook, relevant value, audience fit, readable visual/text, evidenced claims/trust, appropriate next action, audio clarity. Score 0 to 5 or null when evidence is insufficient. Do not compute or state an aggregate grade or coverage in your summary; the app computes those from your criteria. 0 weak, 3 adequate, 5 particularly strong in the available evidence. Each scored criterion MUST cite supplied evidence IDs. You have image samples and local audio technical measurements, not audible speech. Audio clarity MUST be null. Visible text is not a speech transcript. Supplied draft script is proposed copy; verified_transcript is user-supplied reviewed text, still not audio listening. Never fabricate dialogue, Iraqi delivery terms, IQD price, COD, discounts, reviews, guarantees or product benefits. Use only verified project facts; identify ambiguities. For sales optimize qualified purchase action and real proof; for messages/leads optimize qualified inquiries; organic awareness can prioritize meaningful shares/saves. Never equate views or shares with sales. Do not add a fabricated trend, ideal posting time, engagement forecast, virality percentage, probability, or confidence percentage. Propose up to 3 genuinely different hook angles and up to 3 precise edits at times within this timeline, justified by observed weaknesses. No arbitrary fast-cut or video-duration rule. Frame sequence permits limited comparisons, not full temporal/audio analysis. If supplied video is merely an interface test, label review accordingly. Evidence IDs must be taken literally from the supplied manifest.'''

def finalize(raw,evidence,duration,fp,audience_known=False):
    allowed={e['id'] for e in evidence}; result={'summary':str(raw.get('summary',''))[:2500],'criteria':{},'fixes':[], 'hook_variants':[str(s)[:350] for s in raw.get('hook_variants',[])[:3]],'missing':[str(s)[:600] for s in raw.get('missing',[])[:15]],'fingerprint':fp,'version':VERSION,'probability':None,'calibrated':False}
    earned=possible=0
    for key,(label,weight) in CRITERIA.items():
        item=raw.get('criteria',{}).get(key,{})
        score=item.get('score'); refs=[x for x in item.get('evidence',[]) if x in allowed]
        if score is not None and (isinstance(score,bool) or not isinstance(score,int) or not 0<=score<=5): raise ValueError('درجة الإيجنت غير صالحة: '+key)
        if not refs or key=='audio' or (key=='iraqi_fit' and not audience_known): score=None
        reason=str(item.get('reason',''))[:1800]
        if key=='iraqi_fit' and not audience_known: reason='حدد جمهورك العراقي حتى نقيم ملاءمة الرسالة إلهم؛ ملف الستايل وحده ما يثبت الجمهور.'
        if key=='audio': reason='ما سمعنا الكلام بهالتقييم؛ فحص وجود الصوت ومستواه وحده ما يثبت وضوحه أو لهجته.'
        result['criteria'][key]={'label':label,'weight':weight,'score':score,'reason':reason,'evidence':refs}
        if score is not None: earned+=weight*score/5; possible+=weight
    result['coverage']=possible
    # Avoid a deceptively strong aggregate from only one observed criterion.
    result['score']=round(100*earned/possible,1) if possible>=50 else None
    for f in raw.get('fixes',[])[:3]:
        t=finite(f.get('time'), 'توقيت التعديل', duration)
        result['fixes'].append({'time':t,'change':str(f.get('change',''))[:1000],'why':str(f.get('why',''))[:1000]})
    result['at']=datetime.now(ZoneInfo('Asia/Baghdad')).isoformat()
    return result

def optional_num(data,key,maximum=None,integer=False):
    v=data.get(key)
    if v is None or v=='': return None
    n=finite(v,key,maximum)
    if integer and n!=int(n): raise ValueError(key+' لازم عدد صحيح')
    return int(n) if integer else n

def outcome(data,p):
    versions={e['version'] for e in p.get('exports',[])}
    if data.get('export_version') not in versions: raise ValueError('اختار تصدير معروف حتى نربط النتيجة بنفس الفيديو')
    m=market(data.get('market',p.get('market')))
    # This is one fixed-age snapshot of one post; cumulative updates replace it.
    post_key=str(data.get('post_key','')).strip()[:200]
    if not post_key: raise ValueError('اكتب رابط أو معرف المنشور')
    published=datetime.fromisoformat(str(data.get('published_at','')))
    if published.tzinfo is None: published=published.replace(tzinfo=ZoneInfo('Asia/Baghdad'))
    if published>datetime.now(ZoneInfo('Asia/Baghdad')): raise ValueError('تاريخ النشر بالمستقبل')
    window=optional_num(data,'window_hours')
    if window is None or window<=0: raise ValueError('حدد عمر القياس بالساعات')
    age=(datetime.now(ZoneInfo('Asia/Baghdad'))-published).total_seconds()/3600
    if window>age+.05: raise ValueError('عمر القياس أكبر من عمر المنشور؛ راجع تاريخ النشر والساعات')
    views=optional_num(data,'views',integer=True)
    if views is None: raise ValueError('حدد عدد المشاهدات، حتى لو 0')
    r={'id':str(data.get('record_id') or uuid.uuid4().hex[:12]),'post_key':post_key,'export_version':data['export_version'],'published_at':published.isoformat(),'window_hours':window,'views':views,'market':m,'currency':'IQD','source':'user_reported','updated_at':datetime.now(ZoneInfo('Asia/Baghdad')).isoformat()}
    r['market']['script']=''
    for k in ['likes','comments','shares','saves','followers','qualified_messages','leads','orders','impressions','clicks']:
        r[k]=optional_num(data,k,integer=True)
    for k in ['spend_iqd','revenue_iqd','avg_watch_seconds']: r[k]=optional_num(data,k)
    r['completion_pct']=optional_num(data,'completion_pct',100)
    duration=next(e['duration'] for e in p['exports'] if e['version']==r['export_version'])
    if r['avg_watch_seconds'] is not None and duration>0: r['avg_watch_ratio']=r['avg_watch_seconds']/duration # replay can exceed 1
    else: r['avg_watch_ratio']=None
    if m['distribution']=='organic' and (r['spend_iqd'] or 0)>0: raise ValueError('عندك صرف؛ اختار إعلان مدفوع حتى ما نخلط النتائج')
    r['metrics']=metrics(r)
    return r

def metrics(r):
    out={}
    for field in ['likes','comments','shares','saves','qualified_messages','leads','orders']:
        out[field+'_per_1000_views']=round(r[field]/r['views']*1000,3) if r.get(field) is not None and r.get('views',0)>0 else None
    out['views_per_follower']=round(r['views']/r['followers'],3) if (r.get('followers') or 0)>0 else None
    out['ctr_pct']=round(r['clicks']/r['impressions']*100,3) if r.get('clicks') is not None and (r.get('impressions') or 0)>0 else None
    for field in ['qualified_messages','leads','orders']:
        out['cost_per_'+field+'_iqd']=round(r['spend_iqd']/r[field],2) if r['market']['distribution']=='paid' and r.get('spend_iqd') is not None and (r.get(field) or 0)>0 else None
    out['roas']=round(r['revenue_iqd']/r['spend_iqd'],3) if r['market']['distribution']=='paid' and r.get('revenue_iqd') is not None and (r.get('spend_iqd') or 0)>0 else None
    return out

def comparison(records,market_data):
    m=market(market_data)
    if not m['segment'].strip() or not m['account'].strip(): return []
    # Segment, platform, distribution, objective, country and exact observation-age cohort.
    matching=[r for r in records if all(r['market'].get(k)==m[k] for k in ['platform','distribution','objective','segment','location','account'])]
    cohorts={}
    for r in matching: cohorts.setdefault(r['window_hours'],[]).append(r)
    result=[]
    field={'sales':'orders_per_1000_views','leads':'leads_per_1000_views','messages':'qualified_messages_per_1000_views','awareness':'shares_per_1000_views'}[m['objective']]
    for hours,rs in sorted(cohorts.items()):
        distinct={(r['market']['platform'],r['post_key']):r for r in rs} # one post per cohort
        values=[r['metrics'][field] for r in distinct.values() if r['metrics'].get(field) is not None]
        median=None
        if values:
            v=sorted(values); mid=len(v)//2; median=v[mid] if len(v)%2 else (v[mid-1]+v[mid])/2
        result.append({'window_hours':hours,'n_posts':len(distinct),'n_with_metric':len(values),'metric':field,'median':median,'status':'descriptive_only','probability':None})
    return result
