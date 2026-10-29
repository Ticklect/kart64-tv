(function(root){
'use strict';
const KEY='kart64.diagnostics.v3';
function createRecorder(o){
 const now=o.now,storage=o.storage;let active=false,engaged=false,boot=null,raceStart=null,raceMin=null,racePeak=null,nonRaceSince=null;
 let data={launches:0,lastBootMs:null,racesStarted:0,racesFinished:0,availableMemoryBytes:null,totalMemoryBytes:null,wasmMemoryBytes:null,systemCpuLoad:null,gpuLoad:null,temperatureC:null,animationCallbackHz:null,swapRate:null,recentBoots:[],recentRaces:[]};
 try{let old=JSON.parse(storage.getItem(KEY)||'null');if(old&&typeof old==='object')for(const k of ['launches','lastBootMs','racesStarted','racesFinished'])if(Number.isFinite(old[k])&&old[k]>=0)data[k]=old[k];for(const k of ['recentBoots','recentRaces'])if(Array.isArray(old?.[k]))data[k]=old[k].slice(-20)}catch(e){}
 const persist=()=>{try{storage.setItem(KEY,JSON.stringify(data))}catch(e){}};
 return {markInput(){engaged=true},start(){data.launches++;boot=now();persist()},ready(){if(boot!==null){data.lastBootMs=Math.max(0,now()-boot);data.recentBoots.push({durationMs:data.lastBootMs});data.recentBoots=data.recentBoots.slice(-20);boot=null;persist()}},sample(x){
  if(x.callbackMs>0&&Number.isFinite(x.callbackMs)){data.animationCallbackHz=Math.round(10000/x.callbackMs)/10}
  if(x.memory){data.totalMemoryBytes=Number.isFinite(x.memory.total)?x.memory.total:null;data.availableMemoryBytes=Number.isFinite(x.memory.available)?x.memory.available:null}
  if(Number.isFinite(x.wasmMemoryBytes))data.wasmMemoryBytes=x.wasmMemoryBytes;
  data.systemCpuLoad=Number.isFinite(x.cpu)?x.cpu:null;data.swapRate=Number.isFinite(x.swapRate)?x.swapRate:null;
  let s=x.state;let racing=s&&s.gamestate===4&&s.race===3&&s.hudUp; if(racing&&!active&&engaged){data.racesStarted++;active=true;raceStart=now();raceMin=null;racePeak=null;persist()}
  if(active&&Number.isFinite(data.availableMemoryBytes))raceMin=raceMin===null?data.availableMemoryBytes:Math.min(raceMin,data.availableMemoryBytes);
  if(active&&Number.isFinite(data.systemCpuLoad))racePeak=racePeak===null?data.systemCpuLoad:Math.max(racePeak,data.systemCpuLoad);
  if(s&&s.gamestate===4&&s.race===5&&active){data.racesFinished++;data.recentRaces.push({durationMs:Math.max(0,now()-raceStart),minAvailableMemoryBytes:raceMin,peakSystemCpuLoad:racePeak});data.recentRaces=data.recentRaces.slice(-20);active=false;engaged=false;persist()}
  if(s&&s.gamestate!==4){if(nonRaceSince===null)nonRaceSince=now();if(now()-nonRaceSince>20000&&active){active=false;engaged=false}}else nonRaceSince=null;
 },persist,snapshot(){return Object.assign({},data)}};
}
if(typeof module!=='undefined'&&module.exports){module.exports={createRecorder};return}
const r=createRecorder({storage:localStorage,now:()=>performance.now()});root.__kartDiagnostics=r;
let started=false,ready=false,lastFrame=0,sum=0,count=0,cpu=null,cpuPending=false,cpuStarted=0,lastSwaps=null,lastSwapTime=null;
const start=document.getElementById('start');if(start)start.addEventListener('click',()=>{if(!started){started=true;r.start()}},true);
const panel=document.createElement('details');panel.style.cssText='position:fixed;right:8px;top:8px;z-index:10000;background:rgba(0,0,0,.82);color:#fff;font:22px sans-serif;padding:12px;border-radius:6px;max-width:500px';
const summary=document.createElement('summary');summary.textContent='Diagnostics (L3 + R3)';summary.style.cursor='pointer';panel.appendChild(summary);const body=document.createElement('pre');body.style.cssText='font:18px/1.45 monospace;white-space:pre-wrap;margin:8px 0 0';panel.appendChild(body);document.body.appendChild(panel);
let chordHeld=false;function tick(t){if(lastFrame&&t>lastFrame&&t-lastFrame<2000){sum+=t-lastFrame;count++}lastFrame=t;try{let pads=navigator.getGamepads?navigator.getGamepads():[];let list=Array.from(pads);if(document.getElementById('overlay').classList.contains('hidden')&&list.some(p=>p&&(p.buttons.some(b=>b.pressed)||p.axes?.some(a=>Math.abs(a)>.6))))r.markInput();let chord=list.some(p=>p&&p.buttons[10]?.pressed&&p.buttons[11]?.pressed);if(chord&&!chordHeld)panel.open=!panel.open;chordHeld=chord}catch(e){}requestAnimationFrame(tick)}requestAnimationFrame(tick);
addEventListener('keydown',e=>{if(document.getElementById('overlay').classList.contains('hidden')&&e.code!=='F8')r.markInput();if(e.code==='F8'&&!e.repeat){panel.open=!panel.open;e.preventDefault()}});
function num(v,unit){return Number.isFinite(v)?(v/1048576).toFixed(0)+' MB':unit||'unavailable'}
setInterval(()=>{
 let state=null,mem=null,wasm=null;try{if(typeof readState==='function')state=readState()}catch(e){}
 if(state&&!ready){ready=true;r.ready()}
 try{if(typeof tizen!=='undefined'&&tizen.systeminfo){mem={total:tizen.systeminfo.getTotalMemory(),available:tizen.systeminfo.getAvailableMemory()};if(cpuPending&&performance.now()-cpuStarted>5000){cpuPending=false;cpu=null}if(!cpuPending){cpuPending=true;cpuStarted=performance.now();tizen.systeminfo.getPropertyValue('CPU',x=>{cpu=Number.isFinite(x.load)?x.load:null;cpuPending=false},()=>{cpu=null;cpuPending=false})}}}catch(e){cpu=null;cpuPending=false}
 try{if(typeof HEAPU8!=='undefined')wasm=HEAPU8.byteLength}catch(e){}
 let swaps=root.__kartFrameSwaps, t=performance.now(), swapRate=(Number.isFinite(swaps)&&lastSwaps!==null&&t>lastSwapTime)?Math.round((swaps-lastSwaps)*10000/(t-lastSwapTime))/10:null;lastSwaps=Number.isFinite(swaps)?swaps:null;lastSwapTime=t;
 r.sample({state,memory:mem,wasmMemoryBytes:wasm,cpu,swapRate,callbackMs:count?sum/count:null});sum=0;count=0;let d=r.snapshot();
 body.textContent='Launches: '+d.launches+'\nLast boot: '+(d.lastBootMs===null?'unavailable':(d.lastBootMs/1000).toFixed(1)+' s')+'\nRaces started / finished: '+d.racesStarted+' / '+d.racesFinished+'\nLast race duration: '+(d.recentRaces.length?(d.recentRaces[d.recentRaces.length-1].durationMs/1000).toFixed(1)+' s':'unavailable')+'\nAnimation callbacks: '+(d.animationCallbackHz===null?'unavailable':d.animationCallbackHz+'/s (not game FPS)')+'\nGame buffer swaps: '+(d.swapRate===null?'unavailable':d.swapRate+'/s')+'\nTV memory free / total: '+num(d.availableMemoryBytes)+' / '+num(d.totalMemoryBytes)+'\nWasm allocation: '+num(d.wasmMemoryBytes)+'\nSystem CPU: '+(d.systemCpuLoad===null?'unavailable':(d.systemCpuLoad*100).toFixed(1)+'%')+'\nGPU load: unavailable\nTemperature: unavailable';
 r.persist();
},5000);
addEventListener('pagehide',()=>r.persist());
})(typeof window!=='undefined'?window:globalThis);
