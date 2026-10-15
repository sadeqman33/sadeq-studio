"""Local motion catalog, preferences and reproducible per-work plans. No timeline writes."""
import copy, hashlib, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FAMILIES=['calm','punch','onetake','editorial']
CUES=['number','list','price','cta','contrast','emphasis','reveal','tech','hit']
SUPPORTED={'blurIn','riseUp','wordDrop','rubberPop','scrollReveal','wordPath','focus','caption','highlight','shine','ctaPulse','strokeFill','typewriter','wordSwap','counter','decrypt'}
IMAGE_SUPPORTED={'blurIn','riseUp','wordDrop','rubberPop','shine','ctaPulse'}
def catalog():
    rows=json.loads((ROOT/'motion-bank/catalog.json').read_text())['moves']
    for row in rows:
        row['native_types']=['text','image','icon'] if row['id'] in IMAGE_SUPPORTED else ['text'] if row['id'] in SUPPORTED else []
        row['integration']='layer' if row['native_types'] else 'reference'
    return rows

def read(data):
    path=data/'motion-bank/state.json'
    return json.loads(path.read_text()) if path.exists() else {'revision':0,'on':[],'off':[],'history':[]}

def public(data):return {'catalog':catalog(),'state':read(data),'families':FAMILIES,'cues':CUES}

def validate_preferences(d):
    ids={m['id'] for m in catalog()};out={}
    for key in ['on','off']:
        rows=d.get(key,[])
        if not isinstance(rows,list) or any(not isinstance(x,str) or x not in ids for x in rows):raise ValueError('اختيار حركة غير صالح')
        out[key]=list(dict.fromkeys(rows))
    if set(out['on'])&set(out['off']):raise ValueError('الحركة ما تصير مفضلة ومستبعدة بنفس الوقت')
    return out

def plan(state,d):
    family=d.get('family','auto');cues=d.get('cues',[]);title=d.get('title','')
    if family not in ['auto']+FAMILIES:raise ValueError('عائلة الحركة غير صالحة')
    if not isinstance(title,str) or len(title)>100:raise ValueError('عنوان الخطة لحد 100 حرف')
    if not isinstance(cues,list) or any(not isinstance(c,str) or c not in CUES for c in cues):raise ValueError('إشارة حركة غير صالحة')
    native=d.get('native_only',False)
    if not isinstance(native,bool):raise ValueError('خيار التنفيذ غير صالح')
    history=state.get('history',[]);recent=history[-3:]
    if family=='auto':family=min(FAMILIES,key=lambda f:sum(p['family']==f for p in recent))
    rows=[m for m in catalog() if m['id'] not in state['off'] and (not native or m['native_types'])]
    used={x for p in recent for x in p.get('core',[])};chosen=[]
    def score(m):
        salt=f'{title}|{len(history)}|{m["id"]}'
        return (m['id'] in used,m['id'] not in state['on'],family not in m['families'],hashlib.sha256(salt.encode()).hexdigest())
    slots=[('text',),('transition',),('camera','card')]
    for roles in slots:
        candidates=[m for m in rows if m['role'] in roles and m['id'] not in chosen]
        if candidates:chosen.append(min(candidates,key=score)['id'])
    accents=sorted([m for m in rows if m['id'] not in chosen and set(m['cues'])&set(cues)],key=score)[:2]
    return {'title':title.strip(),'family':family,'cues':list(dict.fromkeys(cues)),'core':chosen,'accents':[m['id'] for m in accents],
            'rules':[m['id'] for m in rows if m['role']=='rule'],'native_only':native,'project_id':d.get('id'),'work_id':d.get('work_id'),'at':time.time(),
            'note':'خطة اقتراح فقط؛ ما تغيّر التايم لاين. العناصر المرجعية تحتاج تنفيذ مونتاج مستقل.'}

def update(data,d):
    state=read(data)
    if type(d.get('revision')) is not int or d['revision']!=state['revision']:raise ValueError('بنك الحركات تغيّر؛ افتحه من جديد قبل الحفظ')
    action=d.get('action');new=copy.deepcopy(state)
    if action=='preferences':new.update(validate_preferences(d))
    elif action=='plan':new['history']=(state['history']+[plan(state,d)])[-100:]
    else:raise ValueError('عملية بنك غير صالحة')
    new['revision']+=1;path=data/'motion-bank/state.json';path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(new,ensure_ascii=False,indent=2));tmp.replace(path)
    return {'state':new,'plan':new['history'][-1] if action=='plan' else None}
