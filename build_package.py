"""Package only standalone reviewed source; never bundle local project data."""
import json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FILES=['build_package.py','AGENTS.md','.gitignore','server.py','app.js','index.html','style.css','caption.cjs','browser_runtime.cjs','start.command','README.md','COPYRIGHT','SOURCE.json','plugin.json','package.json','package-lock.json','requirements.txt','iraqi_review.py','video_library.py','speech_worker.py','requirements-transcription.txt','setup-transcription.command','logo.png','project_memory.py','motion.js','motion.css','motion.cjs','memory_documents.py','hyperframes_bridge.py','voiceover.py','workflow.py','typography.py','video_works.py','setup-hyperframes.command']
def build():
    manifest=json.loads((ROOT/'plugin.json').read_text())
    overlay=json.loads((ROOT/'.codex-plugin/plugin.json').read_text())
    assert manifest['name']=='sadeq-studio'
    assert all(overlay[k]==manifest[k] for k in ['name','version','author'])
    assert overlay['interface']==manifest['extensions']['com.openai']['interface']
    files=[ROOT/n for n in FILES]+list(ROOT.glob('test_*.py'))
    for folder in ['skills','third-party','.codex-plugin']:
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file())
    dist=ROOT/'dist';dist.mkdir(exist_ok=True)
    archive=dist/f"sadeq-studio-{manifest['version']}.zip"
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(set(files)):
            if p.is_symlink(): raise ValueError('Symlink not allowed in package')
            if '__pycache__' in p.parts or p.suffix=='.pyc': continue
            z.write(p,'sadeq-studio/'+str(p.relative_to(ROOT)))
    print(archive)
    return archive
if __name__=='__main__':build()
