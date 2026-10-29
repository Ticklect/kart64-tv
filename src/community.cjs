'use strict';
const REQUIRED=['platform','model','osVersion','appVersion','scenario','rateType'];
function name(v,key){if(typeof v!=='string'||!v.trim()||v.length>80||!/^[A-Za-z0-9 ._-]+$/.test(v))throw new Error('Invalid '+key);return v.trim();}
function metric(v,key,min,max){if(v==null)return null;if(typeof v!=='number'||!Number.isFinite(v)||v<min||v>max)throw new Error('Invalid '+key);return v;}
function prepareReport(input,consent){
 if(consent!==true)throw new Error('Explicit consent is required');
 if(!input||typeof input!=='object'||Array.isArray(input))throw new Error('Invalid report');
 const out={};for(const key of REQUIRED)out[key]=name(input[key],key);
 if(!['tizen','webos','androidtv'].includes(out.platform))throw new Error('Invalid platform');
 if(out.rateType!=='buffer_swaps_per_second')throw new Error('Unsupported rendering metric');
 out.renderRate=metric(input.renderRate,'render rate',0,1000);
 out.cpuPercent=metric(input.cpuPercent,'CPU',0,100);
 out.freeMemoryMiB=metric(input.freeMemoryMiB,'memory',0,1048576);
 for(const k of ['gameBooted','raceCompleted']){if(typeof input[k]!=='boolean')throw new Error('Invalid '+k);out[k]=input[k]}
 return out;
}
function stats(nums){if(!nums.length)return null;const n=nums.slice().sort((a,b)=>a-b),i=Math.floor(n.length/2);return {min:n[0],median:n.length%2?n[i]:(n[i-1]+n[i])/2,max:n[n.length-1]};}
function summarize(reports,query){
 if(!Array.isArray(reports))throw new Error('Invalid reports');
 const keys=REQUIRED;for(const k of keys)name(query?.[k],k);
 let match=reports.filter(r=>r&&keys.every(k=>r[k]===query[k])).map(r=>prepareReport(r,true));
 return {reportCount:match.length,renderRate:stats(match.map(r=>r.renderRate).filter(Number.isFinite)),cpuPercent:stats(match.map(r=>r.cpuPercent).filter(Number.isFinite)),confidence:'insufficient-data'};
}
module.exports={prepareReport,summarize};
