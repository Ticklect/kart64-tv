'use strict';
const fs=require('node:fs/promises'),path=require('node:path');
const {safeRuntimeName,canCheckDeclaredSize,readPinnedResponse}=require('./runtime.cjs');
const {patchPackagedPage,patchGlue,lowerImportedSharedMemory}=require('./web-patch.cjs');
const pins=require('./runtime-pins.json');
async function build(stage){
 const dest=path.resolve(stage);const st=await fs.stat(dest);if(!st.isDirectory()||(await fs.readdir(dest)).length)throw Error('Build folder must be a new empty directory.');
 for(const spec of pins.files){
  const name=safeRuntimeName(spec.file);const url=new URL(name==='index.html'?'':name,pins.source);
  if(url.origin!=='https://eddmann.com')throw Error('Invalid runtime source');
  console.log('Preparing '+name);const r=await fetch(url,{signal:AbortSignal.timeout(120000)});
  if(!r.ok)throw Error('Runtime download failed (HTTP '+r.status+').');
  const declared=Number(r.headers.get('content-length'));if(declared&&canCheckDeclaredSize(r.headers.get('content-encoding'))&&declared!==spec.size)throw Error('Runtime integrity check failed.');
  let b=await readPinnedResponse(r,spec);
  if(name==='index.html')b=Buffer.from(patchPackagedPage(b.toString('utf8')));
  if(name==='Spaghettify.js')b=Buffer.from(patchGlue(b.toString('utf8')));
  if(name==='Spaghettify.wasm')b=lowerImportedSharedMemory(b);
  const file=path.join(dest,...name.split('/'));await fs.mkdir(path.dirname(file),{recursive:true});await fs.writeFile(file,b,{flag:'wx'});
 }
 await fs.copyFile(path.join(__dirname,'diagnostics.js'),path.join(dest,'diagnostics.js'));
 await fs.copyFile(path.join(__dirname,'..','assets','kart64-256.png'),path.join(dest,'kart64-icon.png'));
 const xml='<?xml version="1.0" encoding="UTF-8"?>\n<widget xmlns="http://www.w3.org/ns/widgets" xmlns:tizen="http://tizen.org/ns/widgets" id="http://localhost/kart64-tv" version="0.1.0" viewmodes="fullscreen">\n<tizen:application id="KART64TV01.Kart64" package="KART64TV01" required_version="6.5"/>\n<content src="index.html"/><icon src="kart64-icon.png"/><name>Kart64 TV</name>\n<tizen:profile name="tv"/><tizen:setting screen-orientation="landscape" context-menu="disable" background-support="disable" encryption="disable" install-location="auto" hwkey-event="enable"/>\n</widget>\n';
 await fs.writeFile(path.join(dest,'config.xml'),xml,{flag:'wx'});console.log('Runtime prepared.');
}
if(require.main===module){if(process.argv.length!==3){console.error('Usage: node build-runtime.cjs <empty-output-folder>');process.exitCode=2}else build(process.argv[2]).catch(e=>{console.error('Build failed: '+e.message);process.exitCode=1})}module.exports={build};
