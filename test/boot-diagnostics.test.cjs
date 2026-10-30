const {test}=require('node:test');
const assert=require('node:assert/strict');
const {createRecorder}=require('../src/diagnostics.js');
test('keeps completed boot stages alongside the measured launch time',()=>{
 let time=100;const storage={getItem:()=>null,setItem:()=>{}};
 const recorder=createRecorder({now:()=>time,storage});
 recorder.start();time=400;
 recorder.ready([{name:'start',ms:0},{name:'storage-restored',ms:100},{name:'engine-ready',ms:300}]);
 const boot=recorder.snapshot().recentBoots[0];
 assert.equal(boot.durationMs,300);
 assert.deepEqual(boot.stages,[{name:'start',ms:0},{name:'storage-restored',ms:100},{name:'engine-ready',ms:300}]);
});
