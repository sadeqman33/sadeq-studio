"""Independent structured text/image/icon overlays. Local sanitized media only."""
import base64, copy, hashlib, json, math, re, shutil, subprocess, uuid
from pathlib import Path
import typography
MAX_BYTES=8*1024*1024
MODES=['plain','kinetic','paper','fade','pop','blur']
def number(value,low,high,label):
    if isinstance(value,bool):raise ValueError('قيمة غير صالحة: '+label)
    try:n=float(value)
    except (ValueError,TypeError):raise ValueError('قيمة غير صالحة: '+label)
    if not math.isfinite(n) or not low<=n<=high:raise ValueError('قيمة خارج الحدود: '+label)
    return n

def validate(p,items):
    if not isinstance(items,list) or len(items)>100:raise ValueError('لحد 100 طبقة بكل فيديو')
    known={a['id']:a for a in p.get('overlay_assets',[])};seen=set();out=[]
    allowed={'id','type','name','text','asset','start','end','x','y','width','fontSize','font','color','opacity','rotation','motion','enabled'}
    for l in items:
        if not isinstance(l,dict) or set(l)-allowed:raise ValueError('إعداد طبقة غير مدعوم')
        key=l.get('id');kind=l.get('type')
        if not isinstance(key,str) or not re.fullmatch('[a-f0-9]{8,32}',key) or key in seen:raise ValueError('معرّف طبقة غير صالح أو مكرر')
        if kind not in ['text','image','icon']:raise ValueError('نوع طبقة غير صالح')
        seen.add(key);start=number(l.get('start',0),0,86400,'بداية الطبقة');end=number(l.get('end'),0,86400,'نهاية الطبقة')
        if end<=start:raise ValueError('نهاية الطبقة لازم بعد بدايتها')
        row={'id':key,'type':kind,'name':str(l.get('name') or ('نص' if kind=='text' else 'أيقونة' if kind=='icon' else 'صورة'))[:100],'start':start,'end':end,'x':number(l.get('x',50),0,100,'X'),'y':number(l.get('y',50),0,100,'Y'),'width':number(l.get('width',70 if kind=='text' else 30),1,100,'عرض الطبقة'),'opacity':number(l.get('opacity',1),0,1,'الشفافية'),'rotation':number(l.get('rotation',0),-180,180,'الدوران'),'motion':l.get('motion','plain'),'enabled':l.get('enabled',True)}
        if row['motion'] not in MODES or not isinstance(row['enabled'],bool):raise ValueError('حركة أو إظهار الطبقة غير صالح')
        if kind=='text':
            text=l.get('text','')
            if not isinstance(text,str) or len(text)>500:raise ValueError('نص الطبقة لحد 500 حرف')
            font=l.get('font',p.get('typography',{}).get('font','Hacen Beirut'))
            if font not in typography.FONTS or not typography.FONTS[font].is_file():raise ValueError('خط الطبقة مو موجود')
            color=l.get('color','#ffffff')
            if not isinstance(color,str) or not re.fullmatch('#[a-fA-F0-9]{6}',color):raise ValueError('لون طبقة غير صالح')
            row.update(text=text,font=font,color=color,fontSize=number(l.get('fontSize',64),16,240,'حجم الخط'))
        else:
            if l.get('asset') not in known:raise ValueError('صورة الطبقة مو مرتبطة بهالمشروع')
            row['asset']=l['asset']
        out.append(row)
    return out

def import_image(p,folder,data,command,ffprobe):
    name=str(data.get('name','image.png'));suffix=Path(name).suffix.lower()
    if suffix not in ['.png','.jpg','.jpeg','.webp']:raise ValueError('استورد PNG أو JPG أو WebP؛ الأيقونة تگدر تكون PNG شفافة')
    encoded=data.get('image')
    if not isinstance(encoded,str) or len(encoded)>MAX_BYTES*4//3+4:raise ValueError('الصورة أكبر من 8 MB')
    try:raw=base64.b64decode(encoded,validate=True)
    except (ValueError,TypeError):raise ValueError('الصورة غير صالحة')
    if not raw or len(raw)>MAX_BYTES:raise ValueError('الصورة فارغة أو أكبر من 8 MB')
    key=uuid.uuid4().hex[:12];dest=folder/'overlay-media';dest.mkdir(parents=True,exist_ok=True)
    temp=dest/(key+'-source'+suffix);png=dest/(key+'.png');temp.write_bytes(raw)
    try:
        result=subprocess.run([ffprobe,'-v','error','-show_streams','-of','json',str(temp)],capture_output=True,text=True,timeout=20)
        streams=json.loads(result.stdout).get('streams',[]) if result.returncode==0 else []
        if len(streams)!=1 or streams[0].get('codec_name') not in ['png','mjpeg','webp']:raise ValueError('الملف مو صورة مدعومة')
        w,h=streams[0].get('width',0),streams[0].get('height',0)
        if w<=0 or h<=0 or w*h>24_000_000:raise ValueError('أبعاد الصورة غير صالحة أو كبيرة')
        command(['ffmpeg','-v','error','-i',str(temp),'-frames:v','1','-vf','scale=min(4096\\,iw):min(4096\\,ih):force_original_aspect_ratio=decrease','-pix_fmt','rgba','-map_metadata','-1','-y',str(png)],45)
        row={'id':key,'name':Path(name).name[:160],'path':str(png),'sha256':hashlib.sha256(png.read_bytes()).hexdigest(),'kind':'icon' if data.get('kind')=='icon' else 'image'}
        return row
    except Exception:
        png.unlink(missing_ok=True);raise
    finally:
        if temp!=png:temp.unlink(missing_ok=True)

def freeze(p,folder):
    """Snapshot validated layers, media and per-layer fonts into a local render."""
    items=validate(p,p.get('layers',[]));assets={a['id']:a for a in p.get('overlay_assets',[])}
    for l in items:
        if l['type']!='text':
            a=assets[l['asset']];path=Path(a['path'])
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=a['sha256']:raise ValueError('صورة الطبقة تغيّرت؛ استوردها من جديد')
            l['src']='layer-'+a['id']+'.png';shutil.copy2(path,folder/l['src'])
    for font in {l['font'] for l in items if l['type']=='text'}:
        shutil.copy2(typography.FONTS[font],folder/('layer-hacen.ttf' if font=='Hacen Beirut' else 'layer-alexandria.ttf'))
    return items
