"""Saved per-work output dimensions and cadence, shared by both renderers."""
def settings(p,value=None):
    value=p.get('export_settings',{}) if value is None else value
    if not isinstance(value,dict) or set(value)-{'resolution','fps'}:raise ValueError('إعدادات التصدير غير صالحة')
    resolution=value.get('resolution','1080');fps=value.get('fps',30)
    if resolution not in ['1080','4k'] or isinstance(fps,bool) or fps not in [30,60]:raise ValueError('اختار 1080 أو 4K، و30 أو60 فريم')
    if p.get('renderer')=='basic' and (resolution!='1080' or fps!=30):raise ValueError('4K و60 فريم يحتاج Remotion أو Hyperframes')
    return {'resolution':resolution,'fps':int(fps)}

def dimensions(p):
    s=settings(p);short=2160 if s['resolution']=='4k' else 1080
    return (short*16//9,short,s['fps']) if p.get('ratio')=='16:9' else (short,short*16//9,s['fps'])
