"""Isolated CPU MediaPipe worker; streams decoded frames without retaining a video in RAM."""
import json,math,os,signal,subprocess,sys
from pathlib import Path
import cv2,numpy as np,mediapipe as mp

def main(spec_file):
    spec=json.loads(Path(spec_file).read_text());output=Path(spec['output']);ffmpeg=spec['ffmpeg'];length=spec['end']-spec['start']
    # FFmpeg autorotates phone footage before a bounded 720p decode.
    vf="scale=w='if(gte(iw,ih),min(1280,iw),-2)':h='if(gte(iw,ih),-2,min(1280,ih))',scale=w='if(lte(iw,ih),min(720,iw),-2)':h='if(lte(iw,ih),-2,min(720,ih))',setsar=1,fps=30"
    frame_png=output.with_name('first.png')
    subprocess.run([ffmpeg,'-v','error','-ss',str(spec['start']),'-i',spec['source'],'-frames:v','1','-vf',vf,'-y',str(frame_png)],check=True,timeout=45)
    sample=cv2.imread(str(frame_png));height,width=sample.shape[:2];frame_bytes=width*height*3
    frames=max(1,math.ceil(length*30-1e-6));video=output.with_name('silent.mp4');children=[]
    def stop(*_):
        for child in children:
            if child.poll() is None:child.terminate()
        raise SystemExit(1)
    signal.signal(signal.SIGTERM,stop)
    options=mp.tasks.vision.ImageSegmenterOptions(base_options=mp.tasks.BaseOptions(model_asset_path=spec['model']),running_mode=mp.tasks.vision.RunningMode.VIDEO,output_category_mask=False,output_confidence_masks=True)
    with output.with_name('ffmpeg.log').open('w') as log,mp.tasks.vision.ImageSegmenter.create_from_options(options) as segmenter:
        decoder=subprocess.Popen([ffmpeg,'-v','error','-ss',str(spec['start']),'-i',spec['source'],'-t',str(length),'-vf',vf,'-f','rawvideo','-pix_fmt','rgb24','pipe:1'],stdout=subprocess.PIPE,stderr=log);children.append(decoder)
        encoder=subprocess.Popen([ffmpeg,'-v','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{width}x{height}','-r','30','-i','pipe:0','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart','-y',str(video)],stdin=subprocess.PIPE,stderr=log);children.append(encoder)
        color=np.array([int(spec['color'][i:i+2],16) for i in (1,3,5)],dtype=np.float32);count=0;coverage=[]
        try:
            while count<frames:
                raw=decoder.stdout.read(frame_bytes)
                if not raw:break
                if len(raw)!=frame_bytes:raise ValueError('Incomplete decoded frame')
                rgb=np.frombuffer(raw,dtype=np.uint8).reshape(height,width,3).copy()
                result=segmenter.segment_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb),round(count*1000/30))
                masks=result.confidence_masks
                # Selfie's single confidence mask is foreground; multiclass has separate channels.
                mask=masks[1 if len(masks)>1 else 0].numpy_view().copy();mask=cv2.resize(mask,(width,height));mask=np.clip((mask-.15)/.7,0,1);mask=cv2.GaussianBlur(mask,(0,0),.8);alpha=mask[...,None]
                coverage.append(float(np.mean(mask>.5)))
                bg=cv2.GaussianBlur(rgb,(0,0),max(6,min(width,height)/30)).astype(np.float32) if spec['mode']=='blur' else color
                composite=np.clip(rgb.astype(np.float32)*alpha+bg*(1-alpha),0,255).astype(np.uint8)
                encoder.stdin.write(composite.tobytes());count+=1
                if count==1 or count%10==0:
                    progress=output.with_name('progress.json');tmp=progress.with_suffix('.tmp');tmp.write_text(json.dumps({'frame':count,'total':frames}));tmp.replace(progress)
            encoder.stdin.close();encoder.wait(timeout=90);decoder.stdout.close();decoder.wait(timeout=20)
            if encoder.returncode or decoder.returncode or count<frames-1:raise ValueError('Video stream processing failed')
            if not coverage or max(coverage)<.005:raise ValueError('No foreground person detected; source unchanged')
        finally:
            for child in children:
                if child.poll() is None:child.terminate();child.wait(timeout=10)
    subprocess.run([ffmpeg,'-v','error','-i',str(video),'-ss',str(spec['start']),'-i',spec['source'],'-map','0:v:0','-map','1:a:0?','-c:v','copy','-c:a','aac','-af','apad','-t',str(length),'-movflags','+faststart','-y',str(output)],check=True,timeout=90)
    output.with_name('result.json').write_text(json.dumps({'frames':count,'width':width,'height':height,'foreground_range':[min(coverage),max(coverage)],'engine':spec['version'],'audio':'original source, trimmed'},indent=2))
if __name__=='__main__':main(sys.argv[1])
