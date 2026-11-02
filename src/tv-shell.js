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
loading.append(el('h1','Ready. Set. Race.'),el('div',null,'tv-track'));
const loadTitle=el('p','Starting the game…'),loadTime=el('p'),loadNote=el('p','Keep this screen open. First launch may take a little longer.'),loadMarks=el('ol');loadNote.className='tv-note';loading.append(loadTitle,loadTime,loadNote,loadMarks);
const retry=el('button','Retry startup');retry.hidden=true;retry.onclick=()=>location.reload();loading.append(retry);document.body.append(loading);
const launchButton=el('button','Controllers & TV menu');launchButton.id='k64-menu-button';launchButton.onclick=()=>show('main');document.body.append(launchButton);
const heldKeys=new Map();
let alertNode=null,liveNodes=new Map(),previousVirtual=Array(4).fill(null);
function notice(message){if(alertNode)alertNode.textContent=message;}
function safely(fn){return ()=>{try{fn();}catch(e){notice(e.message);}};}
function button(parent,label,fn,primary=false){const b=el('button',label,primary?'tv-primary':'');b.type='button';b.setAttribute('aria-label',label);b.dataset.action=label;b.onclick=safely(fn);parent.append(b);return b;}
function focusFirst(preferred){panel.scrollTop=0;const buttons=[...panel.querySelectorAll('button:not(:disabled)')];(buttons.find(b=>b.dataset.action===preferred)||buttons[0])?.focus();}
function pageHeader(title){
 const top=el('div',null,'tv-topline');top.append(el('span','KART64 TV','tv-brand'),el('span',ready?'Game paused':'Controller setup','tv-status'));panel.append(top,el('h1',title));
}
function controllerDiagram(id){
 const ns='http://www.w3.org/2000/svg',svg=document.createElementNS(ns,'svg');svg.setAttribute('viewBox','0 0 400 190');svg.setAttribute('aria-hidden','true');svg.classList.add('tv-pad-svg');
 const shape=(tag,attrs,parent=svg)=>{const node=document.createElementNS(ns,tag);for(const [k,v] of Object.entries(attrs))node.setAttribute(k,v);parent.append(node);return node;};
 shape('path',{d:'M94 35 Q65 30 48 60 L23 139 Q16 168 38 175 Q57 181 78 146 L102 119 L298 119 L322 146 Q343 181 362 175 Q384 168 377 139 L352 60 Q335 30 306 35 Z',class:'pad-shell'});
 for(const [i,x,y,w,h] of [[6,76,14,57,14],[7,267,14,57,14],[4,70,30,62,12],[5,268,30,62,12]])shape('rect',{x,y,width:w,height:h,rx:5,class:'pad-input','data-button':i});
 for(const [i,x,y] of [[0,305,98],[1,331,73],[2,279,73],[3,305,48]]){shape('circle',{cx:x,cy:y,r:15,class:'pad-input','data-button':i});const t=shape('text',{x,y:y+1});t.textContent=C.buttonName(id,0)==='Cross'?['×','○','□','△'][i]:['A','B','X','Y'][i];}
 for(const [i,x,y] of [[12,91,50],[13,91,88],[14,72,69],[15,110,69]])shape('rect',{x,y,width:17,height:17,rx:3,class:'pad-input','data-button':i});
 for(const [i,x,y] of [[8,170,63],[9,230,63],[16,200,49]])shape('circle',{cx:x,cy:y,r:i===16?9:6,class:'pad-input','data-button':i});
 for(const [i,x] of [[0,145],[1,255]]){shape('circle',{cx:x,cy:116,r:21,class:'pad-input','data-button':i+10});shape('circle',{cx:x,cy:116,r:9,class:'stick-dot','data-stick':i});}
 return svg;
}
function updateDiagram(svg,p){
 for(const node of svg.querySelectorAll('[data-button]'))node.classList.toggle('is-held',!!p.buttons[+node.dataset.button]?.pressed);
 for(const node of svg.querySelectorAll('[data-stick]')){const i=+node.dataset.stick;node.setAttribute('cx',(i?255:145)+(p.axes[i*2]||0)*11);node.setAttribute('cy',116+(p.axes[i*2+1]||0)*11);}
}
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
 const preferred=panel.dataset.page===page?document.activeElement?.dataset.action:null;
 capture=null;liveNodes=new Map();panel.replaceChildren();panel.dataset.page=page;
 pageHeader(({main:'Pit stop',controllers:'Controllers & player assignments',settings:'Sound & display',exit:'Leave this game?'})[page]||'Kart64 TV');
 alertNode=el('p',reason,'tv-alert');alertNode.setAttribute('role','status');panel.append(alertNode);
 if(page==='main'){
  panel.append(el('p',ready?'Take a breather. Your game is paused.':'Set up your controllers, then head to the starting grid.','tv-note'));
  const grid=el('div',null,'tv-menu-grid');panel.append(grid);
  button(grid,ready?'Resume game':'Back to game setup',closeMenu,true);
  button(grid,'Controllers & bindings',()=>show('controllers'));
  button(grid,'Sound & display',()=>show('settings'));
  if(ready)button(grid,'Exit game…',()=>show('exit'));
  if(hub.missing().length)button(panel,'Continue with connected controllers',()=>{hub.acceptConnected();render('Disconnected players are no longer being watched. Resume when ready.');});
  panel.append(el('p','D-pad to move · A / Cross to select · Back returns here. Your custom bindings only affect gameplay.','tv-note'));
 }else if(page==='controllers'){
  panel.append(el('p','Press a button or move a stick to test it. Choose a player slot, or make the controls your own.','tv-note'));
  if(!adapterOK)panel.append(el('p','This browser prevents the input adapter. Testing is available, but remapping is disabled.','tv-alert'));
  const list=hub.list();
  if(!list.some(p=>p.connected))panel.append(el('p','No controller detected. Pair Xbox or PS5 in TV settings, then press a button.'));
  const controllerGrid=el('div',null,'tv-controllers-grid');panel.append(controllerGrid);
  for(const r of list){
   const card=el('div',null,'tv-card');controllerGrid.append(card);card.append(el('h2',r.connected?(r.slot===null?'Unassigned':'Player '+(r.slot+1)):'Disconnected'),el('p',r.id,'tv-controller-name'));
   if(!r.connected)continue;
   const diagram=controllerDiagram(r.id);card.append(diagram);
   const live=el('p','Waiting for input…','tv-live');card.append(live);liveNodes.set(r.key,{node:live,diagram});
   const bar=el('div',null,'tv-bar');card.append(bar);
   const assign=button(bar,'Assign player '+(r.slot===null?'1':((r.slot+1)%4)+1),()=>{hub.assign(r.key,r.slot===null?0:(r.slot+1)%4);render();});assign.dataset.action='assign:'+r.key;
   const remap=button(bar,'Change bindings',()=>renderBindings(r.key));remap.disabled=!adapterOK;remap.dataset.action='bind:'+r.key;
   const reset=button(bar,'Reset bindings',()=>{hub.reset(r.key);render('Default bindings restored.');});reset.dataset.action='reset:'+r.key;
  }
  if(!storage)panel.append(el('p','Browser storage is unavailable. Binding changes will only last for this session.','tv-alert'));
  panel.append(el('p','Saved on this TV. After re-pairing identical controllers, check their player slots. Multiplayer compatibility varies by device.','tv-note'));
  button(panel,'Back',()=>show('main'));
 }else if(page==='settings'){
  const groups=el('div',null,'tv-settings-grid'),sound=el('div',null,'tv-card'),display=el('div',null,'tv-card');groups.append(sound,display);panel.append(groups);
  sound.append(el('h2','Game volume'),el('strong',Math.round(settings.volume*100)+'%','tv-volume'));
  const meter=el('div',null,'tv-volume-track'),fill=el('span');fill.style.width=settings.volume*100+'%';meter.append(fill);sound.append(meter);
  const bar=el('div',null,'tv-bar');sound.append(bar);
  button(bar,'Volume −',()=>setVolume(-.1));button(bar,'Volume +',()=>setVolume(.1));
  const mute=button(sound,settings.volume?'Mute':'Unmute',()=>{settings.volume=settings.volume?0:1;engine.volume(settings.volume);saveSettings();render();});mute.dataset.action='mute';
  display.append(el('h2','Picture detail'),el('p','Choose the balance that feels best on your TV.','tv-note'));
  const grid=el('div',null,'tv-scale-options');display.append(grid);
  for(const n of [.5,.75,1]){
   const label=(settings.resolution===n?'Selected: ':'')+Math.round(n*100)+'% render scale';
   const choice=button(grid,label,()=>{if(ready)engine.resolution(n);settings.resolution=n;saveSettings();render();});
   choice.setAttribute('aria-label',label);choice.setAttribute('aria-pressed',String(settings.resolution===n));choice.dataset.action='scale-'+n;
   choice.replaceChildren(el('span',Math.round(n*100)+'%'),el('small',n===.5?'Lower detail':n===.75?'Balanced':'Full detail'));
  }
  display.append(el('p','This changes game rendering, not your TV output. Lower detail may run better on slower TVs.','tv-note'));
  button(panel,'Back',()=>show('main'));
 }else if(page==='exit'){
  panel.append(el('p','Your current race will end. Game save files will be saved before you return to the launcher. You cannot resume this race later.'));
  button(panel,'Stay in game',()=>show('main'),true);
  button(panel,'Save & exit',async()=>{
   if(exiting)return;exiting=true;notice('Saving…');
   try{await Promise.race([engine.flush(),new Promise((_,reject)=>setTimeout(()=>reject(Error('Saving timed out. Stay in game and retry.')),15000))]);location.href=location.pathname.includes('/game/')?'../assets/launch.html':location.pathname;}
   catch(e){notice('Could not save. Exit cancelled: '+e.message);}finally{exiting=false;}
  });
 }
 focusFirst(preferred);
}
function setVolume(delta){settings.volume=Math.round(Math.max(0,Math.min(1,settings.volume+delta))*10)/10;engine.volume(settings.volume);saveSettings();render();}
let bindingGroup='buttons';
function renderBindings(key){
 const r=hub.list().find(x=>x.key===key);if(!r?.connected){show('controllers');return;}
 const preferred=panel.dataset.page==='bindings'?document.activeElement?.dataset.action:null;
 page='bindings';capture=null;panel.replaceChildren();panel.dataset.page=page;pageHeader('Controller bindings');
 panel.append(el('p',r.id,'tv-controller-name'));
 const tabs=el('div',null,'tv-tabs');panel.append(tabs);
 for(const [group,label] of [['buttons','Buttons'],['extras','D-pad & clicks'],['sticks','Sticks & deadzone']]){const tab=button(tabs,label,()=>{bindingGroup=group;renderBindings(key);});tab.setAttribute('aria-pressed',String(bindingGroup===group));}
 alertNode=el('p','Choose an input, then press or move its replacement.','tv-alert');alertNode.setAttribute('role','status');panel.append(alertNode);
 const profile=hub.profile(key),grid=el('div',null,'tv-bindings-grid');panel.append(grid);
 if(bindingGroup!=='sticks')for(let i=bindingGroup==='extras'?10:0;i<(bindingGroup==='extras'?17:10);i++){
  const row=el('div',null,'tv-binding');const xbox=C.buttonName('Xbox',i),ps=C.buttonName('DualSense',i);row.append(el('span',xbox===ps?xbox:xbox+' / '+ps));
  const input=button(row,C.buttonName(r.id,profile.buttons[i]),()=>beginCapture(key,'button',i));input.dataset.action='binding-'+i;grid.append(row);
 }
 else{
  for(let i=0;i<4;i++){
   const row=el('div',null,'tv-binding');row.append(el('span',['Left stick · horizontal','Left stick · vertical','Right stick · horizontal','Right stick · vertical'][i]));
   const input=button(row,'Axis '+profile.axes[i].index+(profile.axes[i].invert?' · inverted':''),()=>beginCapture(key,'axis',i));input.dataset.action='axis-'+i;grid.append(row);
  }
  const zone=el('div',null,'tv-card');zone.style.marginTop='20px';zone.append(el('h2','Stick deadzone'),el('p','Ignore small movements when the stick is centred. Increase this if your kart drifts on its own.','tv-note'));
  const deadzone=button(zone,'Deadzone: '+Math.round(profile.deadzone*100)+'%',()=>{const p=hub.profile(key);p.deadzone=profile.deadzone>=.3?0:Math.round((profile.deadzone+.05)*100)/100;hub.setProfile(key,p);renderBindings(key);});deadzone.dataset.action='deadzone';panel.append(zone);
 }
 const footer=el('div',null,'tv-footer');panel.append(footer);button(footer,'Back to controllers',()=>show('controllers'));focusFirst(preferred);
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
 if(t-lastPanelPaint>150){for(const [key,view] of liveNodes){const r=hub.list().find(r=>r.key===key);if(r?.connected){updateDiagram(view.diagram,r.raw);view.node.textContent='Buttons: '+(r.raw.buttons.map((b,i)=>b.pressed?C.buttonName(r.id,i):null).filter(Boolean).join(', ')||'none')+'\nAxes: '+r.raw.axes.map(a=>a.toFixed(2)).join('  ');}}lastPanelPaint=t;}
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
