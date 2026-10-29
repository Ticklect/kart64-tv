'use strict';const crypto=require('node:crypto');
function safeRuntimeName(n){if(typeof n!=='string'||!n||n.length>160||n.includes('\\')||n.startsWith('/')||n.split('/').some(p=>!p||p==='.'||p==='..'||!/^[A-Za-z0-9._-]+$/.test(p)))throw Error('Unsafe runtime path');return n;}
function verifyRuntime(b,p){if(!Buffer.isBuffer(b)||!p||!Number.isSafeInteger(p.size)||p.size!==b.length||typeof p.sha256!=='string'||crypto.createHash('sha256').update(b).digest('hex')!==p.sha256)throw Error('Runtime integrity check failed');return true;}
function canCheckDeclaredSize(encoding){return !encoding||encoding.toLowerCase()==='identity';}
async function readPinnedResponse(response,pin){
 if(!response.body||!Number.isSafeInteger(pin.size)||pin.size<0)throw Error('Runtime integrity check failed');
 const reader=response.body.getReader(),chunks=[];let total=0;
 try{while(true){const part=await reader.read();if(part.done)break;total+=part.value.byteLength;if(total>pin.size){await reader.cancel();throw Error('Runtime integrity check failed')}chunks.push(Buffer.from(part.value))}}finally{reader.releaseLock()}
 const result=Buffer.concat(chunks,total);verifyRuntime(result,pin);return result;
}
module.exports={safeRuntimeName,verifyRuntime,canCheckDeclaredSize,readPinnedResponse};
