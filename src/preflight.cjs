'use strict';
const crypto=require('node:crypto');
const fs=require('node:fs');
const {stat}=require('node:fs/promises');
const {pipeline}=require('node:stream/promises');
const US_SHA1='579c48e211ae952530ffc8738709f078d5dd215e';
function assessDigest(digest){return {supported:typeof digest==='string'&&digest.toLowerCase()===US_SHA1};}
async function inspectRom(file){
 const info=await stat(file);if(!info.isFile())throw new Error('Choose a game file, not a directory.');
 const hash=crypto.createHash('sha1');await pipeline(fs.createReadStream(file),hash);
 return {...assessDigest(hash.digest('hex')),sizeBytes:info.size};
}
function assessTv({model,tizen}={}){
 const v=typeof tizen==='string'?/^(\d+)(?:\.(\d+))?$/.exec(tizen.trim()):null;
 if(!v)return {status:'unknown',reason:'TV software version not established; compatibility requires testing.'};
 const major=Number(v[1]),minor=Number(v[2]||0);
 if(major<6||(major===6&&minor<5))return {status:'below-minimum',reason:'This experimental package declares Tizen 6.5 as its minimum; older TVs have not been tested.'};
 if(typeof model==='string'&&model.trim().toUpperCase()==='UE50U8000FKXXU'&&major===9)return {status:'tested',reason:'One TV of this model and Tizen major version ran a single-player race; firmware and other features remain unverified.'};
 return {status:'untested',reason:'This model/version has not yet been verified. Passing the version check does not establish compatibility.'};
}
module.exports={assessDigest,inspectRom,assessTv};
