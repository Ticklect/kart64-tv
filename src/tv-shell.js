(function(root){
'use strict';
const C=root.Kart64Controls,engine=root.Kart64Engine.createEngine();
let storage;try{storage=root.localStorage;}catch(e){}
const hub=C.createHub({storage});
const nativePads=navigator.getGamepads?.bind(navigator)||(()=>[]);
let adapterOK=true;
try{Object.defineProperty(navigator,'getGamepads',{configurable:true,value:()=>hub.update(nativePads())});}catch(e){adapterOK=false;}
let prestartArmed=false;
let ready=false,open=false,page='main',capture=null,bootAt=null,bootMessage='',bootError=false,gamepadHeld=false,navAt=0,lastPanelPaint=0,exiting=false;
let settings={volume:1,resolution:1};
try{const s=JSON.parse(storage?.getItem('kart64.tv.settings.v1')||'{}');if(Number.isFinite(s.volume)&&s.volume>=0&&s.volume<=1)settings.volume=s.volume;if([.5,.75,1].includes(s.resolution))settings.resolution=s.resolution;}catch(e){}
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text)n.textContent=text;if(cls)n.className=cls;return n;};
const menu=el('section');menu.id='k64-tv';menu.hidden=true;menu.setAttribute('role','dialog');menu.setAttribute('aria-modal','true');menu.setAttribute('aria-label','Kart64 TV menu');
const panel=el('div',null,'tv-panel');menu.append(panel);document.body.append(menu);
const loading=el('section');loading.id='k64-loading';loading.hidden=true;loading.setAttribute('aria-label','Game loading');
loading.append(el('h1','KART64 TV'),el('div',null,'tv-track'));
const loadTitle=el('p','Starting the game…'),loadTime=el('p'),loadNote=el('p','First starts can take several minutes. This timer measures elapsed time; it is not a percentage.'),loadMarks=el('ol');loadNote.className='tv-note';loading.append(loadTitle,loadTime,loadNote,loadMarks);
const retry=el('button','Retry startup');retry.hidden=true;retry.onclick=()=>location.reload();loading.append(retry);document.body.append(loading);
const launchButton=el('button','Controllers & TV menu');launchButton.id='k64-menu-button';launchButton.onclick=()=>show('main');document.body.append(launchButton);
const heldKeys=new Map();
let alertNode=null,liveNodes=new Map(),previousVirtual=Array(4).fill(null);
function notice(message){if(alertNode)alertNode.textContent=message;}
function safely(fn){return ()=>{try{fn();}catch(e){notice(e.message);}};}
function button(parent,label,fn,primary=false){const b=el('button',label,primary?'tv-primary':'');b.type='button';b.onclick=safely(fn);parent.append(b);return b;}
function focusFirst(){panel.querySelector('button:not(:disabled)')?.focus();}
function saveSettings(){try{storage?.setItem('kart64.tv.settings.v1',JSON.stringify(settings));}catch(e){notice('Settings apply for this session but could not be saved.');}}
function show(next='main',reason=''){
 if(exiting){notice('Saving… please wait before leaving this screen.');return false;}
 if(ready&&!engine.paused()){
  try{engine.pause();}catch(e){bootMessage=e.message;launchButton.textContent='Pause unavailable — try again';return false;}
 }
 for(const e of heldKeys.values())document.getElementById('canvas')?.dispatchEvent(new KeyboardEvent('keyup',{key:e.key,code:e.code,keyCode:e.keyCode,which:e.which,bubbles:true}));heldKeys.clear();
 hub.setBlocked(true);open=true;page=next;menu.hidden=false;render(reason);return true;
}
function closeMenu(){
 if(exiting){notice('Saving… please wait.');return;}
 if(hub.missing().length){notice('A player controller is disconnected. Reconnect it, or choose Continue with connected controllers.');return;}
 capture=null;
 try{engine.resume();}catch(e){notice('Could not resume: '+e.message);return;}
 hub.acknowledge();hub.setBlocked(false);open=false;menu.hidden=true;prestartArmed=false;(ready?document.getElementById('canvas'):document.getElementById('start'))?.focus();
}
function render(reason=''){
 capture=null;liveNodes=new Map();panel.replaceChildren();panel.append(el('h1',ready?'PIT STOP':'KART64 TV'));
 alertNode=el('p',reason,'tv-alert');alertNode.setAttribute('role','status');panel.append(alertNode);
 if(page==='main'){
  panel.append(el('p',ready?'Game paused. Choose Resume when you are ready.':'Set up your controllers before starting.'));
  const grid=el('div',null,'tv-grid');panel.append(grid);
  button(grid,ready?'Resume game':'Back to game setup',closeMenu,true);
  button(grid,'Controllers & bindings',()=>show('controllers'));
  button(grid,'Sound & display',()=>show('settings'));
  if(ready)button(grid,'Exit game…',()=>show('exit'));
  if(hub.missing().length)button(panel,'Continue with connected controllers',()=>{hub.acceptConnected();render('Disconnected players are no longer being watched. Resume when ready.');});
  panel.append(el('p','TV remote: Back opens this menu. Controller: View + Menu (Xbox) or Create + Options (PS5). Keyboard: Esc. Menu navigation always uses the original D-pad / left stick and A / Cross; bindings affect gameplay only.','tv-note'));
 }else if(page==='controllers'){
  panel.append(el('h2','Controllers & player assignments'));
  panel.append(el('p','Press a button to reveal a paired controller. Assignments are browser player slots; test multiplayer on your device.','tv-note'));
  if(!adapterOK)panel.append(el('p','This browser prevents the input adapter. Testing is available, but remapping is disabled.','tv-alert'));
  const list=hub.list();
  if(!list.some(p=>p.connected))panel.append(el('p','No controller detected. Pair Xbox or PS5 in TV settings, then press a button.'));
  for(const r of list){
   const card=el('div',null,'tv-card');panel.append(card);card.append(el('h2',r.connected?(r.slot===null?'Unassigned':'Player '+(r.slot+1)):'Disconnected'),el('p',r.id));
   if(!r.connected)continue;
   const live=el('p','Waiting for input…','tv-live');card.append(live);liveNodes.set(r.key,live);
   const bar=el('div',null,'tv-bar');card.append(bar);
   button(bar,'Assign player '+(r.slot===null?'1':((r.slot+1)%4)+1),()=>{hub.assign(r.key,r.slot===null?0:(r.slot+1)%4);render();});
   const remap=button(bar,'Change bindings',()=>renderBindings(r.key));remap.disabled=!adapterOK;
   button(bar,'Reset bindings',()=>{hub.reset(r.key);render('Default bindings restored.');});
  }
  if(!storage)panel.append(el('p','Browser storage is unavailable. Binding changes will only last for this session.','tv-alert'));
  panel.append(el('p','Bindings are stored locally by browser controller ID and connection index. Identical controllers may need reassignment after pairing changes.','tv-note'));
  button(panel,'Back',()=>show('main'));
 }else if(page==='settings'){
  panel.append(el('h2','Sound'));
  const bar=el('div',null,'tv-bar');panel.append(bar);
  button(bar,'Volume −',()=>setVolume(-.1));bar.append(el('strong',Math.round(settings.volume*100)+'%'));button(bar,'Volume +',()=>setVolume(.1));
  button(panel,settings.volume?'Mute':'Unmute',()=>{settings.volume=settings.volume?0:1;engine.volume(settings.volume);saveSettings();render();});
  panel.append(el('h2','Display'));
  const grid=el('div',null,'tv-grid');panel.append(grid);
  for(const n of [.5,.75,1])button(grid,(settings.resolution===n?'Selected: ':'')+Math.round(n*100)+'% render scale',()=>{if(ready)engine.resolution(n);settings.resolution=n;saveSettings();render();});
  panel.append(el('p','Render scale changes internal resolution, not your TV output mode. Lower settings may improve performance; no FPS gain is guaranteed.','tv-note'));
  button(panel,'Back',()=>show('main'));
 }else if(page==='exit'){
  panel.append(el('h2','Leave this game?'),el('p','The current race will be abandoned. We will save the game’s current save files before returning to the launcher. This is not a mid-race save state.'));
  button(panel,'Stay in game',()=>show('main'),true);
  button(panel,'Save & exit',async()=>{
   if(exiting)return;exiting=true;notice('Saving…');
   try{await Promise.race([engine.flush(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Saving timed out. Stay in game and retry.')),15000))]);location.href=location.pathname.includes('/game/')?'../assets/launch.html':location.pathname;}
   catch(e){notice('Could not save. Exit cancelled: '+e.message);}finally{exiting=false;}
  });
 }
 focusFirst();
}
function setVolume(delta){settings.volume=Math.round(Math.max(0,Math.min(1,settings.volume+delta))*10)/10;engine.volume(settings.volume);saveSettings();render();}
function renderBindings(key){
 const r=hub.list().find(x=>x.key===key);if(!r?.connected){show('controllers');return;}
 page='bindings';capture=null;panel.replaceChildren();panel.append(el('h1','CONTROLLER BINDS'),el('p',r.id));
 alertNode=el('p','Choose a game input, then press its replacement physical button.','tv-alert');panel.append(alertNode);
 const profile=hub.profile(key);
 for(let i=0;i<17;i++){
  const row=el('div',null,'tv-binding');row.append(el('span',C.buttonName('Xbox',i)+' / '+C.buttonName('DualSense',i)));
  button(row,C.buttonName(r.id,profile.buttons[i]),()=>beginCapture(key,'button',i));panel.append(row);
 }
 for(let i=0;i<4;i++){
  const row=el('div',null,'tv-binding');row.append(el('span',['Left stick horizontal','Left stick vertical','Right stick horizontal','Right stick vertical'][i]));
  button(row,'Axis '+profile.axes[i].index+(profile.axes[i].invert?' (inverted)':''),()=>beginCapture(key,'axis',i));panel.append(row);
 }
 button(panel,'Deadzone: '+Math.round(profile.deadzone*100)+'%',()=>{const p=hub.profile(key);p.deadzone=profile.deadzone>=.3?0:Math.round((profile.deadzone+.05)*100)/100;hub.setProfile(key,p);renderBindings(key);});
 button(panel,'Back to controllers',()=>show('controllers'));focusFirst();
}
function beginCapture(key,kind,target){capture={key,kind,target,released:false,at:performance.now()};notice(kind==='button'?'Release all buttons, then press the replacement button. Back on the TV remote cancels.':'Centre the sticks, then move the replacement axis right or down. Back on the TV remote cancels.');}
function cancelCapture(){if(!capture)return false;const key=capture.key;capture=null;renderBindings(key);notice('Binding cancelled.');return true;}
function moveFocus(delta){const buttons=[...panel.querySelectorAll('button:not(:disabled)')];const n=buttons.indexOf(document.activeElement);buttons[(n+delta+buttons.length)%buttons.length]?.focus();}
function backAction(){if(cancelCapture())return;if(open||ready||!bootAt)show('main');}
function keydown(e){
 const back=['Escape','BrowserBack','GoBack','Backspace'].includes(e.key)||e.keyCode===10009;
 if(back||e.key==='F1'){
  e.preventDefault();e.stopImmediatePropagation();if(e.repeat)return;
  backAction();return;
 }
 if(!open){heldKeys.set(e.code,{key:e.key,code:e.code,keyCode:e.keyCode,which:e.which});return;}
 e.preventDefault();e.stopImmediatePropagation();if(capture)return;
 if(['ArrowDown','ArrowRight','Tab'].includes(e.key))moveFocus(e.shiftKey?-1:1);
 if(['ArrowUp','ArrowLeft'].includes(e.key))moveFocus(-1);
 if((e.key==='Enter'||e.key===' ')&&!e.repeat)document.activeElement?.click();
}
root.addEventListener('keydown',keydown,true);
root.addEventListener('keyup',e=>{heldKeys.delete(e.code);if(open){e.preventDefault();e.stopImmediatePropagation();}},true);
for(const type of ['gamepadconnected','gamepaddisconnected'])root.addEventListener(type,e=>{if(!e.__kartTV)e.stopImmediatePropagation();},true);
function publishVirtual(pads){
 for(let i=0;i<4;i++)if(previousVirtual[i]?.id!==pads[i]?.id){
  for(const [type,pad] of [['gamepaddisconnected',previousVirtual[i]],['gamepadconnected',pads[i]]])if(pad){const e=new Event(type);Object.defineProperty(e,'gamepad',{value:type==='gamepaddisconnected'?{...pad,connected:false}:pad});e.__kartTV=true;root.dispatchEvent(e);}
 }
 previousVirtual=pads;
}
function tick(t){
 let raw=[];try{raw=Array.from(nativePads()||[]);}catch(e){}
 const before=hub.list().filter(r=>r.connected).map(r=>r.key).join('|');const virtual=hub.update(raw);publishVirtual(virtual);
 if(ready&&hub.needsResume()&&!open)show('main','Controller disconnected. The game is paused. Reconnect it before resuming.');
 if(open&&['controllers','main'].includes(page)&&before!==hub.list().filter(r=>r.connected).map(r=>r.key).join('|'))render(hub.missing().length?'A controller disconnected. Reconnect it or continue with connected players.':'Controller connection updated. Resume when ready.');
 const pads=raw.filter(Boolean);
 if(!ready&&!open&&!bootAt){
  if(!pads.some(p=>p.buttons.some(b=>b.pressed)))prestartArmed=true;
  else if(prestartArmed&&pads.some(p=>p.buttons[0]?.pressed||p.buttons[9]?.pressed)){prestartArmed=false;document.getElementById('start')?.click();}
 }
 const chord=pads.some(p=>p.buttons[8]?.pressed&&p.buttons[9]?.pressed);
 if(chord&&!gamepadHeld){if(cancelCapture()){}else if(!open&&(ready||!bootAt))show('main');}
 gamepadHeld=chord;
 if(capture){
  const r=hub.list().find(r=>r.key===capture.key&&r.connected);
  if(!r){capture=null;show('controllers','Controller disconnected.');}
  else if(t-capture.at>15000){cancelCapture();notice('No input detected. Try again.');}
  else if(!capture.released){capture.released=!r.raw.buttons.some(b=>b.pressed)&&!r.raw.axes.some(a=>Math.abs(a)>.25);}
  else{
   const index=capture.kind==='button'?r.raw.buttons.findIndex(b=>b.pressed||b.value>.6):r.raw.axes.findIndex(a=>Math.abs(a)>.65);
   if(index>=0){const c=capture,profile=hub.profile(c.key);if(c.kind==='button')profile.buttons[c.target]=index;else profile.axes[c.target]={index,invert:r.raw.axes[index]<0};
    try{hub.setProfile(c.key,profile);renderBindings(c.key);notice(storage?'Binding saved.':'Binding applied for this session; browser storage is unavailable.');}catch(e){capture=null;notice(e.message);}
   }
  }
 }else if(open&&!chord&&t-navAt>220){
  const p=pads.find(p=>p.buttons.some(b=>b.pressed)||p.axes.some(a=>Math.abs(a)>.65));
  if(p){const b=p.buttons;if(b[12]?.pressed||b[14]?.pressed||p.axes[1]<-.65){moveFocus(-1);navAt=t;}else if(b[13]?.pressed||b[15]?.pressed||p.axes[1]>.65){moveFocus(1);navAt=t;}
   else if(b[0]?.pressed){document.activeElement?.click();navAt=t+180;}
   else if(b[1]?.pressed){show('main');navAt=t+180;}
  }
 }
 if(t-lastPanelPaint>150){for(const [key,node] of liveNodes){const r=hub.list().find(r=>r.key===key);if(r?.connected)node.textContent='Buttons: '+(r.raw.buttons.map((b,i)=>b.pressed?C.buttonName(r.id,i):null).filter(Boolean).join(', ')||'none')+'\nAxes: '+r.raw.axes.map(a=>a.toFixed(2)).join('  ');}lastPanelPaint=t;}
 requestAnimationFrame(tick);
}
requestAnimationFrame(tick);
let settingsApplied=false;
setInterval(()=>{
 const marks=root.Kart64Boot?.snapshot()||[];
 if(marks.length&&!bootAt){bootAt=performance.now();document.body.classList.add('k64-booting');}
 if(marks.some(m=>m.name==='engine-ready')&&!ready){
  ready=true;hub.arm();if(open)engine.pause();loading.hidden=true;document.body.classList.remove('k64-booting');launchButton.textContent='TV menu · Back / View + Menu';
 }
 if(ready){
  try{engine.volume(settings.volume);if(!settingsApplied){engine.resolution(settings.resolution);settingsApplied=true;}}catch(e){}
  return;
 }
 if(bootAt){loading.hidden=false;retry.hidden=!bootError;if(bootError&&!open)retry.focus();loadTitle.textContent=bootError?'Loading stopped: '+bootMessage:(bootMessage||'Starting the game…');loadTime.textContent=Math.floor((performance.now()-bootAt)/1000)+' seconds elapsed';loadMarks.replaceChildren(...marks.map(m=>el('li',m.name.replace(/-/g,' ')+' · '+(m.ms/1000).toFixed(1)+' s')));}
},250);
let polling=false;
async function hostControl(){
 if(!location.pathname.includes('/game/')||polling)return;polling=true;
 try{const r=await fetch('../control',{cache:'no-store'});if(r.ok){const command=await r.json();if(command.pause&&ready)show('main','Paused while the app was in the background.');else if(command.back)show('main','Paused by the TV remote.');}}catch(e){}finally{polling=false;}
}
setInterval(hostControl,200);
document.addEventListener('visibilitychange',()=>{if(ready&&document.hidden)show('main','Paused while the app is in the background.');if(!document.hidden)hostControl();});
root.addEventListener('blur',()=>{if(ready&&!open)show('main','Paused because the app lost focus.');});
root.Kart64TV={hub,engine,show,loadingMessage(message,bad){bootMessage=message;bootError=!!bad;},get ready(){return ready;},get open(){return open;}};
const qp=new URLSearchParams(location.search);
if(qp.has('setup'))show('controllers');
if(qp.has('autostart')){const timer=setInterval(()=>{const b=document.getElementById('start');if(b&&!b.classList.contains('hidden')){clearInterval(timer);b.click();}},100);}
})(window);
