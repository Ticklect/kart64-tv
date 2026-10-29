'use strict';
function selectTarget(targets,port){
 if(!Array.isArray(targets))throw Error('Invalid TV debug target list');
 const matches=targets.filter(x=>x&&x.url==='file:///index.html'&&x.title==='Kart64 TV Check');
 if(matches.length!==1)throw Error('Expected one benchmark target');
 let u;try{u=new URL(matches[0].webSocketDebuggerUrl)}catch(e){throw Error('Invalid debug target')}
 if(u.protocol!=='ws:'||u.hostname!=='127.0.0.1'||Number(u.port)!==port||!u.pathname.startsWith('/devtools/page/')||u.username||u.password)throw Error('Invalid local debug target');return u.toString();
}
function parseValue(value){let data=JSON.parse(value);if(data===null)return null;if(!data||typeof data!=='object'||Array.isArray(data)||data.error)throw Error('TV benchmark failed');return data;}
async function collect(port){
 const r=await fetch('http://127.0.0.1:'+port+'/json/list',{signal:AbortSignal.timeout(5000)});if(!r.ok)throw Error('Could not inspect TV benchmark');
 const url=selectTarget(await r.json(),port);
 return new Promise((resolve,reject)=>{
  const ws=new WebSocket(url);let timer,interval,inFlight=false,done=false,id=0;
  function finish(err,value){if(done)return;done=true;clearTimeout(timer);clearInterval(interval);try{ws.close()}catch(e){}if(err)reject(err);else resolve(value)}
  timer=setTimeout(()=>finish(Error('TV benchmark timed out')),60000);
  ws.onopen=()=>{function poll(){if(inFlight)return;inFlight=true;ws.send(JSON.stringify({id:++id,method:'Runtime.evaluate',params:{expression:'JSON.stringify(window.__kartBenchmark || null)',returnByValue:true}}))}poll();interval=setInterval(poll,1000)};
  ws.onerror=()=>finish(Error('TV benchmark connection failed'));
  ws.onmessage=e=>{try{let message=JSON.parse(e.data);if(!message.id)return;inFlight=false;if(message.error)throw Error('TV benchmark inspection failed');let value=message.result?.result?.value;if(typeof value!=='string')throw Error('Invalid TV benchmark response');let result=parseValue(value);if(result)finish(null,result)}catch(err){finish(err)}};
 });
}
if(require.main===module){let port=Number(process.argv[2]);if(!Number.isInteger(port)||port<1024||port>65535){console.error('Invalid local port');process.exitCode=2}else collect(port).then(v=>console.log(JSON.stringify(v))).catch(e=>{console.error(e.message);process.exitCode=1})}
module.exports={selectTarget,parseValue,collect};
