const {test}=require('node:test'),a=require('node:assert/strict');
const {createEngine}=require('../src/tv-engine.js');
test('only resumes a loop paused by this menu and rejects unavailable pause hooks',()=>{
 let paused=0,resumed=0;const m={pauseMainLoop(){paused++},resumeMainLoop(){resumed++}};
 const engine=createEngine({module:()=>m,loop:()=>({func(){}})});
 engine.resume();a.equal(resumed,0);engine.pause();engine.pause();a.equal(paused,1);engine.resume();a.equal(resumed,1);
 const bad=createEngine({module:()=>({}),loop:()=>null});a.throws(()=>bad.pause(),/pause/i);a.equal(bad.paused(),false);
});
test('exit waits for save sync and propagates storage errors',async()=>{
 let callback;const engine=createEngine({fs:()=>({syncfs(populate,cb){a.equal(populate,false);callback=cb;}})});
 let done=false;const result=engine.flush().then(()=>done=true);await Promise.resolve();a.equal(done,false);callback(null);await result;a.equal(done,true);
 const fail=engine.flush();callback(Error('disk full'));await a.rejects(fail,/disk full/);
});
test('display resolution is bounded to supported choices',()=>{
 const calls=[];const engine=createEngine({module:()=>({_Kart64_SetResolution:n=>calls.push(n)})});
 engine.resolution(.75);a.deepEqual(calls,[.75]);a.throws(()=>engine.resolution(4));a.deepEqual(calls,[.75]);
});
