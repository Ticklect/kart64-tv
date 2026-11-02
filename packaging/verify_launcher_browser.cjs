// Local launcher navigation checks; no game files, network discovery or TV access.
'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const server=http.createServer((req,res)=>{
 const name=decodeURIComponent(req.url.split('?')[0]);
 res.setHeader('Cross-Origin-Opener-Policy','same-origin');res.setHeader('Cross-Origin-Embedder-Policy','require-corp');
 if(name==='/report')return res.end('OK');
 if(name==='/game/ready.json'){res.setHeader('Content-Type','application/json');return res.end('{}');}
 if(name==='/game/index.html'){res.setHeader('Content-Type','text/html');return res.end('<h1>Game destination</h1>');}
 if(!name.startsWith('/assets/')||name.includes('..')||name.includes('\\'))return res.writeHead(404).end();
 const file=name.slice(8);let source;
 if(['tv-controls.js','tv-theme.js','tv-shell.css'].includes(file))source=path.join(root,'src',file);
 else if(['launch.html','launcher.js'].includes(file))source=path.join(root,'android/app/src/main/assets',file);
 else return res.writeHead(404).end();
 res.setHeader('Content-Type',file.endsWith('.html')?'text/html':file.endsWith('.css')?'text/css':'application/javascript');fs.createReadStream(source).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||undefined,args:['--enable-unsafe-swiftshader']});
 try{
  const url='http://127.0.0.1:'+server.address().port+'/assets/launch.html';
  const p=await browser.newPage({viewport:{width:1280,height:720}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(()=>{
   window.__pad={index:0,id:'Xbox Wireless Controller',connected:true,mapping:'standard',timestamp:1,axes:[0,0,0,0],buttons:Array.from({length:17},()=>({value:0,pressed:false}))};
   Object.defineProperty(navigator,'getGamepads',{value:()=>[__pad]});
  });
  await p.goto(url);await p.getByRole('button',{name:'Play game',exact:true}).waitFor();
  await p.waitForFunction(()=>document.activeElement.id==='play');
  for(const direction of [14,15,'left-stick','right-stick']){
   await p.locator('#play').focus();
   await p.evaluate(direction=>{if(typeof direction==='number')__pad.buttons[direction]={pressed:true,value:1};else __pad.axes[0]=direction==='left-stick'?-.8:.8;},direction);
   await p.waitForFunction(()=>document.activeElement.id==='controllers',null,{timeout:2000});
   await p.evaluate(()=>{__pad.axes[0]=0;for(const b of __pad.buttons){b.pressed=false;b.value=0;}});await p.waitForTimeout(80);
  }
  await p.evaluate(()=>__pad.id='Sony DualSense Wireless Controller');
  await p.evaluate(()=>__pad.buttons[0]={pressed:true,value:1});
  await p.waitForURL('**/game/index.html?setup=1');
  await p.goto(url);await p.getByRole('button',{name:'Play game',exact:true}).waitFor();
  assert.equal(await p.evaluate(()=>document.body.classList.contains('k64-native-theme')),false,'Missing optional theme must keep fallback labels');
  await p.keyboard.press('ArrowRight');await p.waitForFunction(()=>document.activeElement.id==='controllers');
  await p.keyboard.press('ArrowLeft');await p.waitForFunction(()=>document.activeElement.id==='play');
  await p.keyboard.press('Enter');await p.waitForURL('**/game/index.html?autostart=1');
  const missing=await browser.newPage();await missing.route('**/game/ready.json',r=>r.fulfill({status:404,body:'Not installed'}));
  await missing.goto(url);await missing.getByText(/Your game files are not installed yet/).waitFor();
  assert.equal(await missing.locator('#play').isVisible(),false);await missing.close();
  const unsupported=await browser.newPage();await unsupported.addInitScript(()=>HTMLCanvasElement.prototype.getContext=()=>null);
  await unsupported.goto(url);await unsupported.getByText('This TV lacks a browser feature required by the game.').waitFor();await unsupported.close();
  assert.deepEqual(errors,[]);console.log('PASS: launcher horizontal D-pad/stick, PS5 confirm, keyboard play/setup, missing-art fallback, missing-game and unsupported-device states.');
 }finally{await browser.close();server.close();}
})().catch(e=>{console.error(e);server.close();process.exitCode=1});
