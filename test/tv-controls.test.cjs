const {test}=require('node:test');
const a=require('node:assert/strict');
const {createHub,defaultProfile,validateProfile,buttonName}=require('../src/tv-controls.js');
function pad(index=0,id='Xbox Wireless Controller') {return {index,id,connected:true,mapping:'standard',timestamp:1,buttons:Array.from({length:17},()=>({pressed:false,touched:false,value:0})),axes:[0,0,0,0]};}
function store(){const data={};return {getItem:k=>data[k]||null,setItem:(k,v)=>data[k]=v};}
test('remaps actual virtual input without changing the raw controller',()=>{
 const hub=createHub({storage:store()}),raw=pad();hub.update([raw]);
 const profile=defaultProfile();profile.buttons[0]=2;profile.axes[0]={index:1,invert:true};
 hub.setProfile(hub.list()[0].key,profile);hub.update([raw]);raw.buttons[2]={pressed:true,value:1};raw.axes[1]=.75;
 const out=hub.update([raw])[0];a.equal(out.buttons[0].pressed,true);a.equal(out.axes[0],-.75);
 a.equal(raw.buttons[0].pressed,false);a.equal(raw.axes[0],0);
});
test('profiles persist, validate and reset rather than accepting invalid bindings',()=>{
 const storage=store(),hub=createHub({storage});hub.update([pad()]);const key=hub.list()[0].key;
 const profile=defaultProfile();profile.buttons[0]=3;hub.setProfile(key,profile);
 const next=createHub({storage});a.equal(next.update([pad()])[0].buttons.length,17);a.equal(next.profile(key).buttons[0],3);
 const invalid=defaultProfile();invalid.buttons[0]=-1;a.throws(()=>validateProfile(invalid));
 invalid.buttons[0]=100;a.throws(()=>validateProfile(invalid));
 invalid.buttons[0]=0;invalid.deadzone=NaN;a.throws(()=>validateProfile(invalid));
 next.reset(key);a.equal(next.profile(key).buttons[0],0);
});
test('player assignment swaps occupied slots and survives reconnect without auto-resume',()=>{
 const hub=createHub({storage:store()}),one=pad(0),two=pad(1,'DualSense Wireless Controller');
 hub.update([one,two]);const keys=hub.list().map(p=>p.key);hub.assign(keys[1],0);
 let out=hub.update([one,two]);a.equal(out[0].id,two.id);a.equal(out[1].id,one.id);
 hub.arm();hub.update([null,two]);a.equal(hub.missing().length,1);
 hub.update([one,two]);a.equal(hub.missing().length,0);a.equal(hub.needsResume(),true);
 hub.acknowledge();a.equal(hub.needsResume(),false);
});
test('menu input is neutral and release gate prevents a held confirm accelerating on resume',()=>{
 const hub=createHub({storage:store()}),raw=pad();raw.buttons[0]={pressed:true,value:1};raw.axes[0]=.8;
 hub.setBlocked(true);let out=hub.update([raw])[0];a.equal(out.buttons[0].value,0);a.equal(out.axes[0],0);
 hub.setBlocked(false);out=hub.update([raw])[0];a.equal(out.buttons[0].pressed,false);
 raw.buttons[0]={pressed:false,value:0};raw.axes[0]=0;hub.update([raw]);
 raw.buttons[0]={pressed:true,value:1};a.equal(hub.update([raw])[0].buttons[0].pressed,true);
});
test('four slots, deadzones, malformed stored data and family-specific labels',()=>{
 const hub=createHub({storage:{getItem:()=>'{broken',setItem(){}}});
 const out=hub.update([0,1,2,3,4].map(i=>pad(i)));a.equal(out.length,4);a.equal(hub.list().filter(p=>p.slot!==null).length,4);
 a.throws(()=>hub.assign(hub.list()[0].key,4));
 a.equal(buttonName('DualSense',0),'Cross');a.equal(buttonName('Xbox',0),'A');
 const raw=pad();raw.axes[0]=.08;a.equal(hub.update([raw])[0].axes[0],0);
});
test('editing one connected controller keeps the saved bindings of absent controllers',()=>{
 const storage=store(),first=createHub({storage});first.update([pad(),pad(1,'DualSense')]);
 const key=first.list()[1].key,p=defaultProfile();p.buttons[0]=3;first.setProfile(key,p);
 const second=createHub({storage});second.update([pad()]);second.reset(second.list()[0].key);
 const third=createHub({storage});third.update([pad(),pad(1,'DualSense')]);
 a.equal(third.profile(key).buttons[0],3);
});
test('virtual state timestamps advance when input is neutralised even if hardware is still held',()=>{
 const hub=createHub({storage:store()}),raw=pad();
 const initial=hub.update([raw])[0].timestamp;
 raw.buttons[0]={pressed:true,value:1};const pressed=hub.update([raw])[0].timestamp;a.ok(pressed>initial);
 hub.setBlocked(true);const blocked=hub.update([raw])[0];a.equal(blocked.buttons[0].value,0);a.ok(blocked.timestamp>pressed);
 a.equal(raw.timestamp,1);
});
