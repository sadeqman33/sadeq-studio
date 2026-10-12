const os=require('os');
// Conservative browser fan-out: leave memory/CPU for video decoding and UI.
function concurrency(width,height,{cpus=os.availableParallelism?.()||os.cpus().length,memory=os.totalmem(),override=process.env.SADEQ_RENDER_CONCURRENCY}={}){
 const requested=Number(override);
 if(Number.isInteger(requested)&&requested>=1&&requested<=8)return requested;
 const fourK=width*height>1920*1080;
 return Math.max(1,Math.min(fourK?4:6,Math.floor(cpus/2),Math.floor(memory/(fourK?6:3)/1024**3)));
}
module.exports={concurrency};
function encoding(width,height,fps,hardware){
 if(!hardware)return {crf:18,x264Preset:'fast'};
 // High-rate H.264 on Apple's media engine; CRF is software-only.
 const fourK=width*height>1920*1080;
 return {hardwareAcceleration:'required',videoBitrate:(fourK?(fps===60?80:50):(fps===60?20:12))+'M'};
}
module.exports.encoding=encoding;
