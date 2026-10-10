// Portable local browser/font discovery; source media stays on the machine.
const fs=require('fs'),path=require('path'),os=require('os');
const {chromium}=require(process.env.SADEQ_PLAYWRIGHT || 'playwright');
const fontDir=process.env.SADEQ_FONT_DIR || path.join(os.homedir(),'Library','Fonts');
function fontPath(){return process.env.SADEQ_FONT_HACEN || path.join(fontDir,'Hacen Beirut.ttf');}
function launchOptions(){
 const chrome=process.env.SADEQ_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
 return {headless:true,...(fs.existsSync(chrome)?{executablePath:chrome}:{})};
}
module.exports={chromium,fontPath,launchOptions};
