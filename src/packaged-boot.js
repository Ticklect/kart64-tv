(function(root){
'use strict';
function persistentPath(path){
 return !/^\/data\/(?:mods(?:\/|$)|yamls(?:\/|$)|meta(?:\/|$)|(?:mk64\.o2r|spaghetti\.o2r|config\.yml|baserom\.us\.z64)$)/.test(path);
}
async function prepareGame(fs,fetchInto,installPack,installCourses){
 const archives=['spaghetti.o2r','mk64.o2r'];
 await Promise.all(archives.map(name=>fs.analyzePath('/data/'+name).exists?undefined:fetchInto(name)));
 if(archives.some(name=>!fs.analyzePath('/data/'+name).exists))throw Error('The installed game data is missing. Reinstall the app from your computer.');
 root.Kart64Boot?.mark('archives-ready');
 await installPack();
 root.Kart64Boot?.mark('texture-pack-ready');
 await installCourses();
}
function createTrace(now){
 let start=null,marks=[];
 return {start(){start=now();marks=[{name:'start',ms:0}]},mark(name){if(start!==null&&marks.length<32)marks.push({name,ms:Math.max(0,now()-start)})},snapshot(){return marks.map(x=>({...x}))}};
}
function getRemoteSaveSet(idbfs,mount,callback,fallback=()=>callback(Error('Bulk storage reads are unavailable'))){
 idbfs.getDB(mount.mountpoint,(error,db)=>{
  if(error)return callback(error);
  let finished=false;
  const entries={};
  const done=(error,result)=>{if(!finished){finished=true;callback(error,result)}};
  try{
   const transaction=db.transaction([idbfs.DB_STORE_NAME],'readonly');
   const store=transaction.objectStore(idbfs.DB_STORE_NAME);
   if(typeof store.getAllKeys!=='function')return fallback(mount,callback);
   transaction.onerror=event=>{event.preventDefault();done(event.target.error||Error('Could not read saved data'))};
   transaction.onabort=()=>done(transaction.error||Error('Saved-data read was aborted'));
   transaction.oncomplete=()=>done(null,{type:'remote',db,entries});
   const request=store.getAllKeys();
   request.onsuccess=()=>{
    try{
     for(const path of request.result){
      if(typeof path!=='string'||!persistentPath(path))continue;
      const read=store.get(path);
      read.onsuccess=()=>{const value=read.result;if(value&&value.timestamp!==undefined)entries[path]={timestamp:value.timestamp}};
     }
    }catch(error){done(error)}
   };
  }catch(error){done(error)}
 });
}
const configuredStorage=new WeakSet();
function configureStorage(idbfs){
 if(configuredStorage.has(idbfs))return;
 const original=idbfs.getRemoteSet;
 idbfs.getRemoteSet=(mount,callback)=>getRemoteSaveSet(idbfs,mount,callback,original);
 configuredStorage.add(idbfs);
}
async function readInstalledFile(name,fallback,filesystem=root.tizen?.filesystem){
 if(!/^(?:Spaghettify\.wasm|mk64\.o2r|spaghetti\.o2r|courses\.json|courses\/(?:[A-Za-z0-9_-]+\/)*[A-Za-z0-9_.-]+\.o2r)$/.test(name))throw Error('Invalid package path');
 if(filesystem&&typeof filesystem.openFile==='function'){
  let handle,timer;
  try{
   handle=filesystem.openFile('wgt-package/'+name,'r');
   const blob=await new Promise((resolve,reject)=>{
    timer=setTimeout(()=>reject(Error('Package read timed out')),60000);
    if(typeof handle.readBlobNonBlocking==='function')handle.readBlobNonBlocking(resolve,reject);
    else resolve(handle.readBlob());
   });
   if(!blob||!Number.isFinite(blob.size)||blob.size<=0||blob.size>1073741824)throw Error('Invalid package file size');
   return await blob.arrayBuffer();
  }catch(error){/* Older TVs or unavailable privileges use the browser reader. */}
  finally{clearTimeout(timer);if(handle)try{handle.close()}catch(error){}}
 }
 return fallback();
}
async function fetchInstalled(name,options){
 const bytes=await readInstalledFile(name,async()=>{
  const response=await root.fetch(name,options);
  if(!response.ok)throw Error(name+': HTTP '+response.status);
  return response.arrayBuffer();
 });
 return new Response(bytes,{headers:{'Content-Type':name.endsWith('.json')?'application/json':'application/octet-stream'}});
}
const api={persistentPath,prepareGame,createTrace,readInstalledFile,fetchInstalled,getRemoteSaveSet,configureStorage};
if(typeof module!=='undefined'&&module.exports){module.exports=api;return}
const trace=createTrace(()=>performance.now());
root.Kart64Boot=Object.assign(api,trace);
})(typeof window!=='undefined'?window:globalThis);
