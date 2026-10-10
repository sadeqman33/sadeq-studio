"""Local configurable typography. Font files are never distributed."""
import os
from pathlib import Path
FONT_DIR=Path(os.environ.get('SADEQ_FONT_DIR',str(Path.home()/'Library/Fonts'))).expanduser()
FONTS={'Hacen Beirut':Path(os.environ.get('SADEQ_FONT_HACEN',str(FONT_DIR/'Hacen Beirut.ttf'))).expanduser(),
       'Alexandria':Path(os.environ.get('SADEQ_FONT_ALEXANDRIA',str(FONT_DIR/'Alexandria-VariableFont_wght.ttf'))).expanduser()}
def settings(raw=None):
 raw=raw or {}; font=raw.get('font','Hacen Beirut'); style=raw.get('style','classic')
 if font not in FONTS or style not in ['classic','academy']: raise ValueError('الخط أو ستايل النص غير صالح')
 if not FONTS[font].is_file(): raise ValueError('الخط المختار مو موجود على الجهاز')
 return {'font':font,'style':style}
def font(p): return FONTS[settings(p.get('typography'))['font']]
