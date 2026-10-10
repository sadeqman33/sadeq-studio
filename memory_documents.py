"""Readable project memory, synchronized editable fields, and evidence appendices.

JSON holds typed state. Markdown fields/notes can be edited locally; such edits
pin user direction. Missing markers never destroy an externally edited document.
"""
import copy, hashlib, re, time
from pathlib import Path
import project_memory as pm

FILES={'PROJECT.md':['about','purpose','offers','audience'],
       'STYLE.md':['style','voice','avoid'], 'LEARNINGS.md':['notes']}
TITLES={'PROJECT.md':'تعريف المشروع ومعرفته','STYLE.md':'دليل الستايل','LEARNINGS.md':'التعلّمات والمراجع'}

def digest(text): return hashlib.sha256(text.encode()).hexdigest()
def marker(key): return re.compile(r'<!-- sadeq:'+key+r' -->\n(.*?)\n<!-- /sadeq:'+key+r' -->',re.S)
def block(key,value): return f'<!-- sadeq:{key} -->\n{value}\n<!-- /sadeq:{key} -->'
def values(p): return {**pm.effective(p),'notes':pm.memory(p).get('notes','')}

def parse(name,text):
    if name not in FILES or len(text)>32_000_000: raise ValueError('ملف ذاكرة غير صالح أو كبير جداً')
    out={}
    for key in FILES[name]:
        matches=marker(key).findall(text)
        if len(matches)!=1: raise ValueError(f'{name}: حافظ على علامتي الحقل {key} حتى نكدر نزامن التعديل')
        value=matches[0].strip()
        if len(value)>(12000 if key=='notes' else 6000): raise ValueError('حقل ذاكرة طويل جداً: '+key)
        out[key]=value
    if len(marker('generated').findall(text))!=1: raise ValueError(name+': قسم المصادر غير صالح؛ الملف محفوظ بدون تغيير')
    return out

def import_edits(p,folder):
    """Validate all changed files before applying any fields; return warnings."""
    state=p.get('memory_documents',{}); edits={}; changed=[]; warnings=[]
    for name in FILES:
        base=state.get(name,{'values':values(p)})
        file=folder/name
        if not file.exists(): continue
        try:
            if file.stat().st_size>32_000_000: raise ValueError(name+': الملف كبير جداً')
            text=file.read_text()
            if digest(text)==base.get('hash'): continue
            data=parse(name,text)
            edits.update({k:v for k,v in data.items() if v!=base.get('values',{}).get(k,'') and v!=values(p).get(k,'')})
            changed.append(name)
        except (ValueError,OSError,UnicodeError) as e: warnings.append(str(e))
    if warnings: return False,warnings
    if not changed: return False,[]
    m=pm.memory(p); overrides=copy.deepcopy(m.get('overrides',{}))
    for key,value in edits.items():
        if key!='notes': overrides[key]=value
    if any(k!='notes' for k in edits): pm.pin(p,overrides)
    if 'notes' in edits: pm.set_notes(p,edits['notes'],kind='markdown_edit')
    m=pm.memory(p)
    if edits: m['learning_log']=(m.get('learning_log',[])+[{'at':time.time(),'kind':'markdown_import','files':changed,'fields':list(edits)}])[-30:]
    p['project_memory']=m
    return True,[]

def list_lines(items): return '\n'.join('- '+str(x).replace('\n','\n  ') for x in items) or '- بعد ماكو معلومات محفوظة.'
def approved(p):
    ids=set(p.get('approved_reference_ids',[])); assets={a['id']:a for a in p['assets']}
    return [{'id':i,'name':assets[i]['name'],'path':assets[i]['path']} for i in sorted(ids) if i in assets]

def reference_context(p):
    out=[]
    for a in approved(p):
        record=p.get('video_analyses',{}).get(a['id'],{})
        out.append({**a,'analysis_status':record.get('status','pending'),'analysis':record.get('analysis'),
                    'fingerprint':record.get('fingerprint')})
    return out

def generated(p,name,folder):
    m=pm.memory(p); f=p.get('profile',{}); refs=approved(p)
    header=f'نسخة الذاكرة: {m["revision"]}\n\nحقول مثبّتة من المستخدم: '+(', '.join(pm.LABELS[k] for k in m['overrides']) or 'لا يوجد')+'\n\n'
    if name=='PROJECT.md':
        complete=sum(r.get('status')=='complete' for r in p.get('video_analyses',{}).values())
        return header+'## نطاق المعرفة\n\n'+f'تحليل محفوظ لـ {complete} من {len(p["assets"])} فيديو. الصور عينات ثابتة؛ تفريغ الكلام آلي ويحتاج مراجعة.\n\n'+ '## وصف المشروع من المعرفة المحفوظة\n\n'+str(f.get('summary',''))+'\n\n## الحقائق المحفوظة حسب الأدلة\n\n'+list_lines(f.get('facts',[]))+'\n\n## مصادر المعلومات\n\n'+list_lines(m['learned'].get('evidence',[]))+'\n\n## معلومات تحتاج تأكيد\n\n'+list_lines(m['learned'].get('uncertainties',[]))+'\n\n## ملفات المعلومات المرتبطة\n\n'+list_lines(x['path'] for x in p.get('knowledge_documents',{}).get('manifest',[]))
    if name=='STYLE.md':
        return header+'## إعدادات التنفيذ الحالية\n\n'+list_lines([f'الألوان: {", ".join(f.get("colors",[]))}',f'الخط: {f.get("font", "Hacen Beirut")}',f'حركة النص: {p.get("motion_style","plain")}',f'الإيقاع: {f.get("pace", "غير محدد")}'])+'\n\n## قواعد بصرية محفوظة من التحليل\n\n'+list_lines(f.get('visual_rules',[]))+'\n\n## مراجع الستايل اللي اعتمدها المستخدم\n\n'+(list_lines(a['name']+' — '+a['path'] for a in refs) if refs else 'بعد ماكو فيديو معتمد كمرجع ستايل. وجود فيديو بمجلد export وحده ما يعتبر اعتماد.')+'\n\nاعتماد المرجع يحدد التفضيل البصري؛ ما يثبت صحة الكلام أو الادعاءات التجارية داخله.'
    entries=[]
    for r in p.get('video_analyses',{}).values():
        if not r.get('analysis'): continue
        a=r['analysis']; t=r.get('transcript',{}); title=str(r.get('name',r.get('asset','')))
        sections=[f'### {title}',str(a.get('summary',''))]
        for key,label in [('topics','المحتوى والأفكار'),('visual_style','الستايل المرصود'),('visible_text','النص الظاهر'),('speech_notes','ملاحظات الكلام'),('uncertainties','غير المؤكد')]:
            if a.get(key): sections.append('#### '+label+'\n\n'+list_lines(a[key]))
        sections.append('حالة الكلام: '+str(t.get('status','pending'))+'؛ عدد المقاطع: '+str(len(t.get('segments',[]))))
        sections.append('بصمة المصدر وقت التحليل: '+str(r.get('fingerprint','غير متوفرة')))
        if r.get('folder'):
            source=Path(r['folder'])
            if source.is_relative_to(folder):
                relative=source.relative_to(folder).as_posix()
                sections.append(f'[التفريغ TXT]({relative}/transcript.txt) · [التفريغ SRT]({relative}/transcript.srt)')
        entries.append('\n\n'.join(sections))
    labels={'user_edit':'تعديل يدوي على الهوية','evidence_update':'تحديث من الأدلة','markdown_import':'استيراد تعديل من ملف MD','markdown_edit':'تعديل الملاحظات من ملف MD','user_notes':'تعديل ملاحظات المشروع'}
    log=[labels.get(x['kind'],str(x['kind'])) for x in m.get('learning_log',[])]
    outcomes=[]
    for r in p.get('results',[])[-20:]: outcomes.append(f'{r.get("post_key", "منشور")} — {r.get("views", "غير متوفر")} مشاهدة بعد {r.get("window_hours", "؟")} ساعة؛ أرقام مدخلة، مو توقع انتشار.')
    return header+'## سجل تحديث المعرفة\n\n'+list_lines(log)+'\n\n## نتائج منشورات محفوظة\n\n'+list_lines(outcomes)+'\n\n## أفكار مقترحة حسب المعرفة الحالية\n\n'+list_lines(f.get('ideas',[]))+'\n\n## تقارير الفيديوات المحفوظة\n\n'+'\n\n'.join(entries)

def publish(p,folder):
    """Refresh generated sections, preserve local prose, and atomically write changes."""
    data=values(p); state={}; warnings=[]
    for name,fields in FILES.items():
        file=folder/name
        if file.exists():
            text=file.read_text()
            try: parse(name,text)
            except ValueError as e:
                warnings.append(str(e)); state[name]=p.get('memory_documents',{}).get(name,{}); continue
        else:
            text=f'# {TITLES[name]} — {p["name"]}\n\nهوية مستقلة للمشروع `{p["id"]}`.\n\n'
            text+='عدّل النص داخل علامات الحقول أو الملاحظات. التعديل يتحفظ كتوجيه من عندك عند فتح المشروع. حافظ على العلامات؛ أقسام المصادر تتحدّث من المعرفة المحفوظة. اترك الحقل فارغاً للرجوع لتحليل الإيجنت.\n\n'
            for key in fields:
                text+='## '+('ملاحظات وتفضيلات معتمدة من عندك' if key=='notes' else pm.LABELS[key])+'\n\n'+block(key,'')+'\n\n'
            text+=block('generated','')+'\n'
        for key in fields: text=marker(key).sub(lambda _:block(key,data[key]),text)
        text=marker('generated').sub(lambda _:block('generated',generated(p,name,folder)),text)
        if not file.exists() or file.read_text()!=text:
            temp=file.with_suffix('.md.tmp');temp.write_text(text);temp.replace(file)
        state[name]={'hash':digest(text),'values':{k:data[k] for k in fields}}
    p['memory_documents']=state
    return warnings
