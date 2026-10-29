const {test}=require('node:test');const a=require('node:assert/strict');const {summarizeIntervals,measureCapabilities}=require('../benchmark/benchmark.js');
test('measures intervals without claiming game FPS',()=>{let r=summarizeIntervals([10,20,30]);a.equal(r.samples,3);a.equal(r.medianMs,20);a.equal(r.callbackRate,50);a.equal(r.kind,'animation_callback_rate');a.equal('fps' in r,false)});
test('reports empty samples explicitly',()=>a.equal(summarizeIntervals([]),null));
test('reports unavailable capabilities honestly',()=>{let r=measureCapabilities({webgl2:false,sharedArrayBuffer:false,sharedWasm:false,audioWorklet:false});a.equal(r.webgl2,false);a.equal(r.sharedWasm,false);a.equal(r.status,'missing-required-features')});
test('capabilities alone never promise playability',()=>{let r=measureCapabilities({webgl2:true,sharedArrayBuffer:true,sharedWasm:true,audioWorklet:true});a.equal(r.status,'features-present-untested');a.equal('predictedFps' in r,false)});
