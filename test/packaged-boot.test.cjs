const {test}=require('node:test');
const assert=require('node:assert/strict');
const {persistentPath,prepareGame,createTrace,readInstalledFile,getRemoteSaveSet,loadRestoredEntry,loadTexturePack}=require('../src/packaged-boot.js');
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
 const script=`var Module={};if(!Module["expectedDataFileDownloads"])Module.expectedDataFileDownloads=0;(()=>{function loadPackage() { throw Error('Extraction download ran'); }loadPackage({files:[${files}],remote_package_size:7967812})})();var programArgs=[];async function getWasmBinary(binaryFile){var response=await readAsync(binaryFile);}function restore(src,store,path){IDBFS.loadRemoteEntry(store,path,()=>{})}globalThis.runtimeRan=true;`;
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
 assert.equal(result.records['/data/default.sav'],values['/data/default.sav']);
 assert.equal(result.records['/data/mk64.o2r'],undefined);
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

test('the game archive reader returns its original buffer without wrapping it in a Response',async()=>{
 const bytes=new Uint8Array([64,1,2]).buffer;
 const window={tizen:{filesystem:{openFile(){return {readBlobNonBlocking(ok){ok({size:bytes.byteLength,arrayBuffer:async()=>bytes})},close(){}}}}}};
 const context={window,performance:{now:()=>0},setTimeout,clearTimeout,Blob,Response};
 vm.runInNewContext(require('node:fs').readFileSync(require.resolve('../src/packaged-boot.js'),'utf8'),context);
 assert.equal(await window.Kart64Boot.readAsset('mk64.o2r'),bytes);
});

test('restores a save from the metadata snapshot without reading it a second time',()=>{
 const entry={timestamp:new Date(12345),mode:33206,contents:new Uint8Array([1,64])};let restored;
 loadRestoredEntry({records:{'/data/default.sav':entry}},{loadRemoteEntry(){throw Error('Duplicate database read')}},{},'/data/default.sav',(error,value)=>{assert.equal(error,null);restored=value});
 assert.equal(restored,entry);
});

test('older metadata producers still use the original save reader and propagate its errors',()=>{
 const store={},failure=Error('Read failed');let called=false;
 const idbfs={loadRemoteEntry(actualStore,path,callback){assert.equal(actualStore,store);assert.equal(path,'/data/default.sav');called=true;callback(failure)}};
 loadRestoredEntry({entries:{}},idbfs,store,'/data/default.sav',error=>assert.equal(error,failure));assert.equal(called,true);
});

test('an explicitly empty texture-pack slot avoids reopening its database',async()=>{
 let reads=0;
 assert.equal(await loadTexturePack(Promise.resolve(false),false,async()=>{reads++;return {name:'pack'}}),null);
 assert.equal(reads,0);
});

test('selected, installed and unknown texture packs retain the normal loading path',async()=>{
 const pack={name:'chosen.o2r'};let reads=0;
 const read=async()=>{reads++;return pack};
 assert.equal(await loadTexturePack(Promise.resolve(false),true,read),pack);
 assert.equal(await loadTexturePack(Promise.resolve(true),false,read),pack);
 assert.equal(await loadTexturePack(Promise.reject(Error('Lookup failed')),false,read),pack);
 assert.equal(reads,3);
});
