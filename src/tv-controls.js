(function(root){
'use strict';
const KEY='kart64.tv.controllers.v1';
function buttonName(id,index){
 const ps=/dualsense|dualshock|playstation|054c|sony|wireless controller/i.test(id)&&!/xbox/i.test(id);
 return (ps?['Cross','Circle','Square','Triangle','L1','R1','L2','R2','Create','Options','L3','R3','D-pad up','D-pad down','D-pad left','D-pad right','PS']:['A','B','X','Y','LB','RB','LT','RT','View','Menu','L3','R3','D-pad up','D-pad down','D-pad left','D-pad right','Guide'])[index]||'Button '+index;
}
function defaultProfile(){return {buttons:Array.from({length:17},(_,i)=>i),axes:Array.from({length:4},(_,i)=>({index:i,invert:false})),deadzone:.15};}
function validateProfile(p){
 if(!p||!Array.isArray(p.buttons)||p.buttons.length!==17||p.buttons.some(n=>!Number.isInteger(n)||n<0||n>63)||!Array.isArray(p.axes)||p.axes.length!==4||p.axes.some(a=>!a||!Number.isInteger(a.index)||a.index<0||a.index>15||typeof a.invert!=='boolean')||!Number.isFinite(p.deadzone)||p.deadzone<0||p.deadzone>.5)throw Error('Invalid controller bindings.');
 return JSON.parse(JSON.stringify(p));
}
function createHub({storage}={}){
 let saved={};try{const s=JSON.parse(storage?.getItem(KEY)||'{}');if(s&&typeof s==='object'&&!Array.isArray(s))saved=s;}catch(e){}
 const records=new Map();let blocked=false,gate=false,armed=false,requiresResume=false,watched=new Set();
 const keyOf=p=>p.id+' @'+p.index;
 function persist(){
  const data={};
  for(const [key,r] of Object.entries(saved))try{if(r.slot===null||(Number.isInteger(r.slot)&&r.slot>=0&&r.slot<4))data[key]={profile:validateProfile(r.profile),slot:r.slot};}catch(e){}
  for(const [key,r] of records)data[key]={profile:r.profile,slot:r.slot};
  try{storage?.setItem(KEY,JSON.stringify(data));saved=data;}catch(e){throw Error('Could not save controller settings on this device.');}
 }
 function neutral(p){return !p.buttons?.some(b=>b.pressed||b.value>.5)&&!p.axes?.some(a=>Math.abs(a)>.25);}
 function update(pads){
  const present=new Set();
  for(const p of Array.from(pads||[])){
   if(!p||p.connected===false)continue;
   const key=keyOf(p);present.add(key);
   if(!records.has(key)){
    let profile=defaultProfile();try{if(saved[key]?.profile)profile=validateProfile(saved[key].profile);}catch(e){}
    const used=new Set([...records.values()].map(r=>r.slot));
    const pref=saved[key]?.slot;
    const slot=Number.isInteger(pref)&&pref>=0&&pref<4&&!used.has(pref)?pref:[0,1,2,3].find(n=>!used.has(n));
    records.set(key,{key,id:p.id,slot:slot===undefined?null:slot,profile,connected:true,raw:p});
   }
   const r=records.get(key);r.connected=true;r.raw=p;
   if(armed&&r.slot!==null)watched.add(key);
  }
  for(const [key,r] of records){r.connected=present.has(key);if(armed&&watched.has(key)&&!r.connected)requiresResume=true;}
  if(gate&&[...records.values()].filter(r=>r.connected&&r.slot!==null).every(r=>neutral(r.raw)))gate=false;
  const out=Array(4).fill(null);
  for(const r of records.values()){
   if(!r.connected||r.slot===null)continue;
   const p=r.raw,quiet=blocked||gate,profile=r.profile;
   const buttons=profile.buttons.map(i=>{
    const source=p.buttons[i],v=quiet?0:Math.max(0,Math.min(1,Number(source?.value)||(source?.pressed?1:0)));
    return {value:v,pressed:v>.5,touched:!quiet&&!!source?.touched};
   });
   const axes=profile.axes.map(a=>{let v=Number(p.axes[a.index])||0;return quiet||Math.abs(v)<profile.deadzone?0:Math.max(-1,Math.min(1,v))*(a.invert?-1:1);});
   // SDL skips unchanged timestamps. Neutralising inputs and remapping are
   // virtual state changes even when the physical controller is held still.
   const signature=JSON.stringify([r.slot,buttons.map(b=>b.value),axes]);
   if(signature!==r.signature){r.timestamp=Math.max(Number.isFinite(p.timestamp)?p.timestamp:0,(r.timestamp||0)+1);r.signature=signature;}
   out[r.slot]={id:p.id,index:r.slot,connected:true,mapping:'standard',timestamp:r.timestamp,buttons,axes};
  }
  return out;
 }
 return {
  update,
  list:()=>[...records.values()].map(r=>({key:r.key,id:r.id,slot:r.slot,connected:r.connected,raw:r.raw})),
  profile:key=>validateProfile(records.get(key)?.profile||defaultProfile()),
  setProfile(key,p){const r=records.get(key);if(!r)throw Error('Controller not connected.');r.profile=validateProfile(p);persist();gate=true;},
  reset(key){this.setProfile(key,defaultProfile());},
  assign(key,slot){
   if(!Number.isInteger(slot)||slot<0||slot>3)throw Error('Choose player 1–4.');
   const r=records.get(key);if(!r?.connected)throw Error('Controller not connected.');
   const other=[...records.values()].find(x=>x.key!==key&&x.slot===slot);
   if(other)other.slot=r.slot;r.slot=slot;persist();gate=true;
  },
  setBlocked(value){blocked=!!value;if(!blocked)gate=true;},
  arm(){armed=true;watched=new Set([...records.values()].filter(r=>r.connected&&r.slot!==null).map(r=>r.key));},
  missing:()=>[...watched].filter(key=>!records.get(key)?.connected),
  needsResume:()=>requiresResume,
  acknowledge(){requiresResume=false;},
  acceptConnected(){watched=new Set([...records.values()].filter(r=>r.connected&&r.slot!==null).map(r=>r.key));requiresResume=false;}
 };
}
const api={createHub,defaultProfile,validateProfile,buttonName};
if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.Kart64Controls=api;
})(typeof window!=='undefined'?window:globalThis);
