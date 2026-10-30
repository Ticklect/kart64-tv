const {test}=require('node:test');
const assert=require('node:assert/strict');
const {persistentPath,prepareGame,createTrace,readInstalledFile,getRemoteSaveSet}=require('../src/packaged-boot.js');
const {skipExtractionPreload,patchPackagedStartup}=require('../src/packaged-patch.cjs');
const vm=require('node:vm');

test('keeps saves and settings while excluding installed assets from storage sync',()=>{
 for(const path of ['/data/save.bin','/data/config.json','/data/saves/slot1','/data'])assert.equal(persistentPath(path),true,path);
 for(const path of ['/data/mk64.o2r','/data/spaghetti.o2r','/data/config.yml','/data/baserom.us.z64','/data/yamls/us/a.yml','/data/meta/a','/data/mods/pack.o2r'])assert.equal(persistentPath(path),false,path);
 assert.equal(persistentPath('/data/yamls-save.bin'),true);
});

test('loads both installed archives concurrently without extraction recipes',async()=>{
 const files=new Set(),calls=[],pending=[];
 const fs={analyzePath:p=>({exists:files.has(p)})};
 const fetchInto=name=>{calls.push(name);return new Promise(resolve=>pending.push(()=>{files.add('/data/'+name);resolve()}))};
 const ready=prepareGame(fs,fetchInto,async()=>calls.push('pack'),async()=>calls.push('courses'));
 assert.deepEqual(calls.slice(0,2),['spaghetti.o2r','mk64.o2r']);
 pending.forEach(resolve=>resolve());await ready;
 assert.deepEqual(calls,['spaghetti.o2r','mk64.o2r','pack','courses']);
});

test('fails startup when installed game data is absent instead of requesting a ROM on the TV',async()=>{
 await assert.rejects(prepareGame({analyzePath:()=>({exists:false})},async()=>{},async()=>{},async()=>{}),/installed game data/i);
});

test('boot trace records actual stage durations and resets each launch',()=>{
 let now=20;const trace=createTrace(()=>now);
 trace.start();now=120;trace.mark('runtime-loaded');now=190;trace.mark('engine-ready');
 assert.deepEqual(trace.snapshot(),[{name:'start',ms:0},{name:'runtime-loaded',ms:100},{name:'engine-ready',ms:170}]);
 trace.snapshot().push({name:'external',ms:0});assert.equal(trace.snapshot().length,3);
 now=1000;trace.start();assert.deepEqual(trace.snapshot(),[{name:'start',ms:0}]);
});

test('removes the extraction-only preload and still executes the runtime',()=>{
 const files=Array.from({length:129},(_,i)=>`{filename:"/torch/${i}.yml"}`).join(',');
 const script=`var Module={};if(!Module["expectedDataFileDownloads"])Module.expectedDataFileDownloads=0;(()=>{function loadPackage() { throw Error('Extraction download ran'); }loadPackage({files:[${files}],remote_package_size:7967812})})();var programArgs=[];async function getWasmBinary(binaryFile){var response=await readAsync(binaryFile);}globalThis.runtimeRan=true;`;
 const context={};vm.runInNewContext(skipExtractionPreload(script),context);
 assert.equal(context.runtimeRan,true);
 assert.throws(()=>skipExtractionPreload(script.replace('/torch/0.yml','/game/required.bin')),/contents/);
 assert.throws(()=>skipExtractionPreload(script.replace('7967812','1234')),/contents/);
 assert.throws(()=>skipExtractionPreload(script+script),/preloader/);
 assert.throws(()=>patchPackagedStartup('<html>changed upstream</html>'),/Unexpected/);
});

test('reads packaged files through the native TV reader and closes the handle',async()=>{
 const bytes=new Uint8Array([0,97,115,109]).buffer;let closed=false,opened;
 const filesystem={openFile(path,mode){opened=[path,mode];return {readBlobNonBlocking(ok){ok(new Blob([bytes]))},close(){closed=true}}}};
 const result=await readInstalledFile('Spaghettify.wasm',()=>{throw Error('Slow fallback used')},filesystem);
 assert.deepEqual(new Uint8Array(result),new Uint8Array(bytes));
 assert.deepEqual(opened,['wgt-package/Spaghettify.wasm','r']);assert.equal(closed,true);
});

test('falls back on unsupported native APIs and never accepts an arbitrary TV path',async()=>{
 const bytes=new Uint8Array([1]).buffer;let closed=false;
 const filesystem={openFile(){return {readBlobNonBlocking(ok,error){error(Error('Read failed'))},close(){closed=true}}}};
 assert.equal(await readInstalledFile('mk64.o2r',async()=>bytes,filesystem),bytes);assert.equal(closed,true);
 assert.equal(await readInstalledFile('mk64.o2r',async()=>bytes,null),bytes);
 await assert.rejects(readInstalledFile('../private.txt',async()=>bytes,filesystem),/package path/);
 await assert.rejects(readInstalledFile('documents/private.txt',async()=>bytes,filesystem),/package path/);
});

test('bulk storage lookup skips extraction entries and preserves save timestamps',async()=>{
 const timestamp=new Date(12345),gets=[];let transaction;
 const values={'/data/default.sav':{timestamp,contents:new Uint8Array([1])},'/data/spaghettify.cfg.json':{timestamp},'/data/mk64.o2r':{timestamp},'/data/yamls/recipe.yml':{timestamp}};
 const store={getAllKeys(){const request={};queueMicrotask(()=>{request.result=Object.keys(values);request.onsuccess();queueMicrotask(()=>transaction.oncomplete())});return request},get(path){gets.push(path);const request={};queueMicrotask(()=>{request.result=values[path];request.onsuccess()});return request}};
 const db={transaction(){transaction={objectStore:()=>store};return transaction}};
 const idbfs={DB_STORE_NAME:'FILE_DATA',getDB(name,callback){assert.equal(name,'/data');callback(null,db)}};
 const result=await new Promise((resolve,reject)=>getRemoteSaveSet(idbfs,{mountpoint:'/data'},(error,set)=>error?reject(error):resolve(set),()=>{throw Error('Cursor fallback used')}));
 assert.deepEqual(gets,['/data/default.sav','/data/spaghettify.cfg.json']);
 assert.deepEqual(result.entries,{'/data/default.sav':{timestamp},'/data/spaghettify.cfg.json':{timestamp}});
 assert.equal(result.db,db);assert.equal(result.type,'remote');
});

test('storage failures never become an empty successful save restore',async()=>{
 let calls=0;
 getRemoteSaveSet({getDB(name,callback){callback(Error('Storage unavailable'))}}, {mountpoint:'/data'},error=>{calls++;assert.match(error.message,/unavailable/)});
 assert.equal(calls,1);
 let fallback=false;
 const idbfs={DB_STORE_NAME:'FILE_DATA',getDB(name,callback){callback(null,{transaction(){return {objectStore:()=>({})}}})}};
 getRemoteSaveSet(idbfs,{mountpoint:'/data'},()=>{},()=>{fallback=true});
 assert.equal(fallback,true);
});

test('a failed metadata transaction reports one error even if completion follows',async()=>{
 let count=0,transaction;
 const store={getAllKeys(){queueMicrotask(()=>{transaction.onerror({target:{error:Error('Read failed')},preventDefault(){}});transaction.oncomplete()});return {}}};
 const idbfs={DB_STORE_NAME:'FILE_DATA',getDB(name,callback){callback(null,{transaction(){transaction={objectStore:()=>store};return transaction}})}};
 await new Promise(resolve=>getRemoteSaveSet(idbfs,{mountpoint:'/data'},error=>{count++;assert.match(error.message,/Read failed/);resolve()}));
 assert.equal(count,1);
});
