(function(root){
'use strict';
function createEngine(options={}){
 const getModule=options.module||(()=>root.Module),getLoop=options.loop||(()=>typeof MainLoop!=='undefined'?MainLoop:null),getFS=options.fs||(()=>typeof FS!=='undefined'?FS:null);
 let ownsPause=false,gain=null,audioNode=null,volume=1;
 function sound(){
  try{
  const audio=getModule()?.__ringAudio;if(!audio?.node)return false;
  if(audioNode!==audio.node){
   gain=audio.ctx.createGain();audio.node.disconnect();audio.node.connect(gain);gain.connect(audio.ctx.destination);audioNode=audio.node;
  }
  gain.gain.setValueAtTime(ownsPause?0:volume,audio.ctx.currentTime);return true;
  }catch(e){return false;}
 }
 return {
  paused:()=>ownsPause,
  pause(){
   if(ownsPause)return;
   const m=getModule();if(!m?.pauseMainLoop||!m?.resumeMainLoop||!getLoop()?.func)throw Error('The game pause hook is not ready.');
   m.pauseMainLoop();ownsPause=true;sound();
  },
  resume(){if(!ownsPause)return;getModule().resumeMainLoop();ownsPause=false;sound();},
  volume(value){if(!Number.isFinite(value)||value<0||value>1)throw Error('Volume must be 0–100%.');volume=value;return sound();},
  resolution(value){if(![.5,.75,1].includes(value))throw Error('Unsupported render resolution.');const fn=getModule()?._Kart64_SetResolution;if(typeof fn!=='function')throw Error('Display settings are not ready.');fn(value);},
  flush(){return new Promise((resolve,reject)=>{const fs=getFS();if(!fs?.syncfs)return reject(Error('Saved data is not ready.'));fs.syncfs(false,error=>error?reject(error):resolve());});}
 };
}
if(typeof module!=='undefined'&&module.exports)module.exports={createEngine};else root.Kart64Engine={createEngine};
})(typeof window!=='undefined'?window:globalThis);
