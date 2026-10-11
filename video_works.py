"""Independent editable videos sharing one project's identity and media library."""
import copy, hashlib, json, re, time, uuid

DEFAULTS={'layers':[],'timeline':[],'ratio':'9:16','renderer':'basic','motion_style':'plain',
          'typography':{'font':'Hacen Beirut','style':'classic'},'voiceover':{},'market':{},
          'draft_reason':'','draft_origin':'manual','draft_memory_revision':None}

def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,ensure_ascii=False,indent=2));tmp.replace(path)

def state(p):
    return {**{k:copy.deepcopy(p.get(k,v)) for k,v in DEFAULTS.items()},
            'profile_colors':copy.deepcopy(p.get('profile',{}).get('colors',['#f2eee5','#cb984f']))}

def title(p,fallback='فيديو جديد'):
    reason=str(p.get('draft_reason','')).strip()
    return (reason.splitlines()[0][:100] if reason else fallback)

def find(p,wid):
    if not isinstance(wid,str) or not re.fullmatch('[a-f0-9]{12}',wid):raise ValueError('فيديو غير معروف')
    row=next((w for w in p.get('video_works',[]) if w['id']==wid),None)
    if not row:raise ValueError('الفيديو مو مربوط بهالمشروع')
    return row

def snapshot(folder,wid):return folder/'works'/wid/'edit.json'

def begin(p,folder,name='',wid=None,edit=None,at=None):
    wid=wid or uuid.uuid4().hex[:12];now=at or time.time()
    row={'id':wid,'title':str(name or title(p))[:100],'created':now,'updated':now}
    p.setdefault('video_works',[]).append(row)
    write(snapshot(folder,wid),edit if edit is not None else state(p))
    p['active_work_id']=wid
    return row

def ensure(p,folder):
    """Migrate legacy frozen exports once; never rewrite the original exports."""
    changed=False;p.setdefault('video_works',[])
    known={w['id'] for w in p['video_works']};active=p.get('active_work_id')
    for e in p.get('exports',[]):
        if e.get('work_id') in known:continue
        if not isinstance(e.get('version'),str) or not re.fullmatch('[A-Za-z0-9_-]{1,80}',e['version']):continue
        source=folder/'exports'/e['version']/'edit.json'
        if not source.is_file():continue
        try:old=json.loads(source.read_text())
        except (OSError,ValueError):
            warning='تعذّر قراءة مسودة النسخة '+e['version']
            if warning not in p.setdefault('work_warnings',[]):p['work_warnings'].append(warning);changed=True
            continue
        if not isinstance(old,dict) or old.get('id')!=p['id'] or not isinstance(old.get('timeline'),list):continue
        wid=hashlib.sha256(e['version'].encode()).hexdigest()[:12]
        if wid not in known:
            begin(p,folder,title(old,'فيديو محفوظ · '+e['version']),wid,state(old),e.get('at'))
            known.add(wid)
        e['work_id']=wid;changed=True
    p['active_work_id']=active
    if active not in known and p.get('timeline'):
        match=next((w['id'] for w in reversed(p['video_works']) if json.loads(snapshot(folder,w['id']).read_text())==state(p)),None)
        if match:p['active_work_id']=match
        else:begin(p,folder,title(p,'المسودة الحالية'))
        changed=True
    return changed

def checkpoint(p,folder,record_history=True):
    wid=p.get('active_work_id')
    if not wid:
        if not p.get('timeline'):return
        wid=begin(p,folder)['id']
    row=find(p,wid);path=snapshot(folder,wid);new=state(p)
    if path.exists():
        old=json.loads(path.read_text())
        if old==new:return
        if record_history:write(path.parent/'history'/f'{time.time_ns()}.json',old)
    write(path,new);row['updated']=time.time()

def restore(p,edit):
    for k,v in DEFAULTS.items():p[k]=copy.deepcopy(edit.get(k,v))
    p['profile']['colors']=copy.deepcopy(edit['profile_colors'])

def open_work(p,folder,wid):
    row=find(p,wid);path=snapshot(folder,wid)
    if not path.is_file():raise ValueError('مسودة الفيديو مو موجودة')
    edit=json.loads(path.read_text());restore(p,edit);p['active_work_id']=wid
    return row

def undo(p,folder,validate=None):
    wid=p.get('active_work_id');find(p,wid)
    files=sorted((snapshot(folder,wid).parent/'history').glob('*.json'))
    if not files:raise ValueError('ماكو تعديل سابق لهالفيديو')
    edit=json.loads(files[-1].read_text());restore(p,edit)
    if validate:validate(p)
    # Preserve the undone state as recoverable history, outside the undo stack.
    old=json.loads(snapshot(folder,wid).read_text())
    write(snapshot(folder,wid).parent/'undone'/f'{time.time_ns()}.json',old)
    write(snapshot(folder,wid),edit);files[-1].unlink()

def rows(p):
    out=[]
    for w in reversed(p.get('video_works',[])):
        exports=[e for e in p.get('exports',[]) if e.get('work_id')==w['id']]
        out.append({**w,'active':w['id']==p.get('active_work_id'),'export_count':len(exports),
                    'latest_export':exports[-1] if exports else None})
    return out
