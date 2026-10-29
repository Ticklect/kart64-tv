(function(root){
'use strict';
function summarizeIntervals(values){
 const a=values.filter(x=>typeof x==='number'&&Number.isFinite(x)&&x>0).sort((x,y)=>x-y);if(!a.length)return null;
 const m=Math.floor(a.length/2),median=a.length%2?a[m]:(a[m-1]+a[m])/2,mean=a.reduce((x,y)=>x+y,0)/a.length;
 return {kind:'animation_callback_rate',samples:a.length,medianMs:Math.round(median*10)/10,p95Ms:Math.round(a[Math.floor((a.length-1)*.95)]*10)/10,callbackRate:Math.round(10000/mean)/10};
}
function measureCapabilities(values){
 const result={webgl2:!!values.webgl2,sharedArrayBuffer:!!values.sharedArrayBuffer,sharedWasm:!!values.sharedWasm,audioWorklet:!!values.audioWorklet};
 result.status=Object.values(result).every(Boolean)?'features-present-untested':'missing-required-features';return result;
}
async function runBenchmark(canvas,onStatus){
 const status=onStatus||(()=>{});let gl=null,sharedWasm=false;
 try{gl=canvas.getContext('webgl2',{alpha:false,antialias:false});}catch(e){}
 try{const m=new WebAssembly.Memory({initial:1,maximum:1,shared:true});sharedWasm=m.buffer instanceof SharedArrayBuffer}catch(e){}
 const capabilities=measureCapabilities({webgl2:!!gl,sharedArrayBuffer:typeof SharedArrayBuffer!=='undefined',sharedWasm,audioWorklet:typeof AudioWorkletNode!=='undefined'});
 status('Measuring CPU…');let iterations=0,start=performance.now(),value=1;
 while(performance.now()-start<500){for(let i=0;i<5000;i++){value=(value*1664525+1013904223)>>>0;iterations++}await new Promise(r=>setTimeout(r,0));}
 const elapsed=performance.now()-start;const cpu={iterationsPerSecond:Math.round(iterations*1000/elapsed),durationMs:Math.round(elapsed)};
 if(!gl)return {version:1,capabilities,cpu,graphics:null};
 status('Measuring graphics…');
 function shader(type,source){const x=gl.createShader(type);gl.shaderSource(x,source);gl.compileShader(x);if(!gl.getShaderParameter(x,gl.COMPILE_STATUS))throw Error('Graphics shader could not compile');return x}
 const vs=shader(gl.VERTEX_SHADER,'#version 300 es\nvoid main(){vec2 p=vec2((gl_VertexID==1)?3.0:-1.0,(gl_VertexID==2)?3.0:-1.0);gl_Position=vec4(p,0,1);}');
 const fs=shader(gl.FRAGMENT_SHADER,'#version 300 es\nprecision mediump float;out vec4 color;void main(){vec2 p=gl_FragCoord.xy/vec2(640.,360.);float v=0.;for(int i=0;i<16;i++){v+=sin(p.x*float(i+1)+p.y)*0.02;}color=vec4(p.x,p.y,0.5+v,1.);}');
 const program=gl.createProgram();gl.attachShader(program,vs);gl.attachShader(program,fs);gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw Error('Graphics program could not link');gl.useProgram(program);gl.viewport(0,0,640,360);
 let intervals=[],last=null;const begin=performance.now();
 await new Promise((resolve,reject)=>{function frame(now){try{if(gl.isContextLost())throw Error('Graphics context lost');gl.drawArrays(gl.TRIANGLES,0,3);if(last!==null&&now>last)intervals.push(now-last);last=now;if(now-begin>=6000||intervals.length>=300)resolve();else requestAnimationFrame(frame)}catch(e){reject(e)}}requestAnimationFrame(frame)});
 gl.deleteProgram(program);gl.deleteShader(vs);gl.deleteShader(fs);
 return {version:1,capabilities,cpu,graphics:{resolution:'640x360',workload:'synthetic-webgl2-v1',timing:summarizeIntervals(intervals)}};
}
const api={summarizeIntervals,measureCapabilities,runBenchmark};if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.KartTVBenchmark=api;
})(typeof window!=='undefined'?window:globalThis);
