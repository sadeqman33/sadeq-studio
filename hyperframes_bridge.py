"""Local, pinned Hyperframes rendering of the editable Sadeq timeline.

Only trusted templates generate HTML; agent/user strings remain escaped text.
No source URLs, cloud renderer, remote scripts, TTS or generated claims.
"""
import html, json, os, shutil, subprocess
import layers as ly
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = '0.8.143'
CLI = ROOT/'node_modules/hyperframes/dist/cli.js'
BUNDLED_NODE = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'

def node():
    return os.environ.get('SADEQ_NODE', str(BUNDLED_NODE) if BUNDLED_NODE.exists() else shutil.which('node') or 'node')

def ready():
    manifest=ROOT/'node_modules/hyperframes/package.json'
    return manifest.exists() and json.loads(manifest.read_text()).get('version')==VERSION

def environment():
    return {**os.environ, 'HYPERFRAMES_NO_TELEMETRY':'1', 'DO_NOT_TRACK':'1',
            'HYPERFRAMES_NO_UPDATE_CHECK':'1', 'HYPERFRAMES_NO_AUTO_INSTALL':'1',
            'PATH':str(Path(node()).parent)+os.pathsep+os.environ.get('PATH','')}

def compile_project(p, out, probe, command, font):
    """Freeze trimmed media and an editable composition next to edit.json."""
    if not ready(): raise ValueError('محرك Hyperframes يحتاج إعداد: شغّل setup-hyperframes.command')
    folder=out/'composition'; folder.mkdir(parents=True)
    assets={a['id']:a for a in p['assets']}; videos=[]; captions=[]; timings=[]; total=0
    academy=p.get('typography',{}).get('style')=='academy'
    w,h=(1920,1080) if p.get('ratio')=='16:9' else (1080,1920)
    shutil.copy2(font,folder/'brand.ttf')  # private local render asset; excluded from distribution
    shutil.copy2(ROOT/'node_modules/gsap/dist/gsap.min.js',folder/'gsap.js')
    shutil.copy2(ROOT/'motion.css',folder/'motion.css')
    shutil.copy2(ROOT/'motion.js',folder/'motion.js')
    for i,c in enumerate(p['timeline']):
        a=assets[c['asset']]; meta=probe(Path(a['path'])); duration=c['end']-c['start']
        if meta['hdr']: raise ValueError('المقطع HDR؛ يحتاج تحويل Apple إلى SDR حتى نحافظ على ألوانه')
        # Freeze only requested ranges. Originals remain untouched. Zero gain is explicit.
        cmd=['ffmpeg','-v','error','-ss',str(c['start']),'-i',a['path'],'-t',str(duration),
             '-vf',f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,setsar=1,fps=30',
             '-map','0:v:0','-map','0:a:0?','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',
             '-c:a','aac','-ar','48000','-ac','2','-movflags','+faststart','-y',str(folder/f'clip-{i}.mp4')]
        command(cmd, max(180,int(duration*15)))
        audio=meta['audio'] and not c.get('mute',False)
        videos.append(f'<video id="video-{i}" class="clip footage" src="clip-{i}.mp4" data-start="{total}" data-duration="{duration}" data-track-index="0" data-volume="{1 if audio else 0}" '+('data-has-audio="true"' if audio else 'muted')+' playsinline></video>')
        start=c.get('textStart',0); end=c.get('textEnd',duration); d=end-start
        mode=c.get('motion','inherit'); mode=p.get('motion_style','plain') if mode=='inherit' else mode
        if c.get('text'):
            text=html.escape(c['text'])
            if academy and i==0:
                lines=c['text'].split('\n')
                text='<small class="academy-tag">الأكاديمية · AI</small>'+html.escape(lines[0])+('<br><span class="hook-accent">'+html.escape(' '.join(lines[1:]))+'</span>' if len(lines)>1 else '')
            captions.append(f'<div id="text-{i}" class="clip caption {"academy-hook" if academy and i==0 else ""}" data-motion="{mode}" data-start="{total+start}" data-duration="{d}" data-track-index="1" style="top:{c.get("textY",63)}%">{text}</div>')
            timings.append({'id':f'text-{i}','start':total+start,'duration':d,'mode':mode})
        total+=duration
    colors=[x for x in p.get('profile',{}).get('colors',[]) if isinstance(x,str) and len(x)==7 and x.startswith('#') and all(ch in '0123456789abcdefABCDEF' for ch in x[1:])]
    def lum(c):
        n=int(c[1:],16); return .2126*(n>>16)+.7152*((n>>8)&255)+.0722*(n&255)
    light=max(colors,key=lum) if colors else '#ffffff'; light=light if lum(light)>140 else '#ffffff'
    accent=colors[1] if len(colors)>1 else '#cb984f'; size=78 if w==1080 else 78
    script='''const tl=gsap.timeline({paused:true});
tl.to({}, {duration:DURATION});
for(const c of CAPTIONS){
 const el=document.getElementById(c.id), clock={time:0};
 const paint=()=>{const s=StudioMotion.state(clock.time,c.duration,c.mode);el.style.opacity=s.opacity;el.style.transform=`translateY(${s.y}em) scale(${s.scale}) rotate(${s.rotate}deg)`;el.style.filter=`blur(${s.blur}em)`;};
 tl.fromTo(clock,{time:0},{time:c.duration,duration:c.duration,ease:'none',immediateRender:false,onUpdate:paint},c.start);
}
window.__timelines={sadeq:tl};'''.replace('DURATION',str(total)).replace('CAPTIONS',json.dumps(timings))
    css=f'''@font-face{{font-family:Brand;src:url(brand.ttf)}}*{{box-sizing:border-box}}html,body{{margin:0;background:black}}#stage{{position:relative;width:{w}px;height:{h}px;overflow:hidden}}.footage{{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;z-index:0}}.caption{{position:absolute;left:7%;right:12%;font:{size}px/1.45 Brand;direction:rtl;text-align:center;white-space:pre-wrap;overflow-wrap:anywhere;text-shadow:0 2px 8px #000,0 0 3px #000;color:{light};--motion-accent:{accent};opacity:0;z-index:1}}.caption[data-motion="paper"]{{color:#211d19}}'''
    if academy:
        css+="@font-face{font-family:Brand;src:url(brand.ttf);font-weight:100 900}"
        dark=min(colors,key=lum) if colors else '#2B0710'
        css+=f""".caption{{left:8%;right:12%;font-size:68px;font-weight:750;line-height:1.35;color:#fff;text-shadow:0 3px 12px #000,0 0 5px #000;--brand-dark:{dark}}}.caption:after{{content:'';display:block;width:84px;height:8px;border-radius:4px;background:var(--brand-dark);box-shadow:0 0 0 1px #ffffff80;margin:12px auto 0}}.caption.academy-hook{{font-size:88px;font-weight:850;line-height:1.4}}.academy-hook:after{{display:none}}.academy-tag{{display:table;margin:0 auto 16px;padding:4px 18px;background:var(--brand-dark);color:#fff;border:1px solid #ffffff60;border-radius:8px;font-size:26px;font-weight:600;text-shadow:none}}.hook-accent{{display:inline-block;background:var(--brand-dark);padding:0 18px 10px;border-radius:12px;border-bottom:5px solid {light};text-shadow:none}}"""
    overlay_layers=ly.freeze(p,folder)
    shutil.copy2(ROOT/'layers.js',folder/'layers.js')
    layer_html=[]
    for i,l in enumerate(overlay_layers):
        content=html.escape(l['text']) if l['type']=='text' else '<img src="'+l['src']+'" style="width:100%;display:block">'
        layer_html.append(f'<div id="layer-{i}" data-start="{l["start"]}" data-duration="{l["end"]-l["start"]}" data-track-index="{i+2}" style="position:absolute;opacity:0;z-index:{i+10}">{content}</div>')
    css+='@font-face{font-family:LayerHacen;src:url(layer-hacen.ttf)}@font-face{font-family:LayerAlexandria;src:url(layer-alexandria.ttf)}'
    script+='\nfor(const [i,l] of '+json.dumps(overlay_layers,ensure_ascii=True).replace('<',r'\u003c')+'.entries()){const el=document.getElementById("layer-"+i),clock={time:0};const paint=()=>Object.assign(el.style,StudioLayers.style(l,clock.time,'+str(w)+'));paint();tl.fromTo(clock,{time:0},{time:'+str(total)+',duration:'+str(total)+',ease:"none",immediateRender:false,onUpdate:paint},0);}'
    composition=f'<!doctype html><html lang="ar"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'self\' data: blob:; script-src \'self\' \'unsafe-inline\'; style-src \'self\' \'unsafe-inline\'"><link rel="stylesheet" href="motion.css"><style>{css}</style></head><body><div id="stage" data-composition-id="sadeq" data-start="0" data-duration="{total}" data-width="{w}" data-height="{h}" data-fps="30">'+''.join(videos+captions+layer_html)+f'</div><script src="motion.js"></script><script src="layers.js"></script><script src="gsap.js"></script><script>{script}</script></body></html>'
    (folder/'index.html').write_text(composition)
    (folder/'manifest.json').write_text(json.dumps({'engine':'hyperframes','version':VERSION,'width':w,'height':h,'duration':total,'memory_revision':p.get('draft_memory_revision'),'approved_reference_ids':p.get('approved_reference_ids',[]),'source_clips':p['timeline']},ensure_ascii=False,indent=2))
    return folder,w,h,total

def render(p,out,probe,command,font,j):
    j['message']='أجهّز لقطات النسخة وطبقات النص بدقة 1080…'
    folder,w,h,total=compile_project(p,out,probe,command,font)
    j['message']='Hyperframes يرسم الفيديو محلياً ويحافظ على الصوت الأصلي…'
    args=[node(),str(CLI),'render',str(folder),'-o',str(out/'final.mp4'),'-f','30','-w','1','--quality','standard','--no-best-effort','--no-browser-gpu','--experimental-fast-capture=false']
    log=out/'hyperframes.log'
    with log.open('w') as stream:
        try:
            result=subprocess.run(args,stdout=stream,stderr=subprocess.STDOUT,env=environment(),timeout=max(600,int(total*40)))
        except subprocess.TimeoutExpired: raise ValueError('تصدير Hyperframes تجاوز الوقت؛ المسودة والتفاصيل محفوظة')
    if result.returncode or not (out/'final.mp4').exists():
        raise ValueError('Hyperframes ما كمل التصدير: '+log.read_text(errors='replace')[-1200:])
    tl=p['timeline']; source={a['id']:a for a in p['assets']}
    if tl and len({c['asset'] for c in tl})==1 and not any(c.get('mute') for c in tl):
        original=Path(source[tl[0]['asset']]['path']); meta=probe(original)
        continuous=abs(tl[0]['start'])<.001 and abs(tl[-1]['end']-meta['duration'])<.051 and all(abs(a['end']-b['start'])<.001 for a,b in zip(tl,tl[1:]))
        if continuous and meta['audio']:
            temp=out/'original-audio.mp4'
            command(['ffmpeg','-v','error','-i',str(out/'final.mp4'),'-i',str(original),'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart','-y',str(temp)],180)
            temp.replace(out/'final.mp4')
    return w,h,total
