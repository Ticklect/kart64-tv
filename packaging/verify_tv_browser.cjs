// Explicit local-only integration check. Never distributes game files or contacts a TV.
'use strict';
const fs=require('node:fs'),path=require('node:path'),http=require('node:http'),assert=require('node:assert/strict');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=path.resolve(process.env.KART64_TEST_RUNTIME||'');
if(!process.env.KART64_TEST_RUNTIME||!fs.existsSync(path.join(base,'mk64.o2r')))throw Error('Set KART64_TEST_RUNTIME to a private prepared game directory.');
let pendingControl=null;
const server=http.createServer((req,res)=>{
 const requested=decodeURIComponent(req.url.split('?')[0]).slice(1);
 if(requested==='control'){res.setHeader('Content-Type','application/json');const value=pendingControl||{};pendingControl=null;return res.end(JSON.stringify(value));}
 const name=requested==='assets/launch.html'?'index.html':requested.replace(/^(?:game|assets)\//,'')||'index.html';
 if(name.includes('..')||name.includes('\\'))return res.writeHead(403).end();
 const file=path.join(base,name);if(!fs.existsSync(file)||!fs.statSync(file).isFile())return res.writeHead(404).end();
 res.setHeader('Cross-Origin-Opener-Policy','same-origin');res.setHeader('Cross-Origin-Embedder-Policy','require-corp');
 res.setHeader('Content-Type',name.endsWith('.html')?'text/html':name.endsWith('.css')?'text/css':name.endsWith('.js')?'application/javascript':name.endsWith('.wasm')?'application/wasm':'application/octet-stream');fs.createReadStream(file).pipe(res);
});
async function main(){
 await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_EXECUTABLE||undefined,args:['--enable-unsafe-swiftshader','--autoplay-policy=no-user-gesture-required']});
 try{
  const p=await browser.newPage({viewport:{width:1280,height:720}}),errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.addInitScript(()=>{
   const pad=(index,id)=>({id,index,mapping:'standard',connected:true,timestamp:1,buttons:Array.from({length:17},()=>({pressed:false,touched:false,value:0})),axes:[0,0,0,0]});
   Object.defineProperty(navigator,'maxTouchPoints',{configurable:true,value:5});
   window.__rawPads=[pad(0,'Xbox Wireless Controller'),pad(1,'DualSense Wireless Controller')];
   Object.defineProperty(navigator,'getGamepads',{configurable:true,value:()=>window.__rawPads});
   const original=AudioContext.prototype.createGain;AudioContext.prototype.createGain=function(){const node=original.call(this);window.__tvGain=node;return node;};
  });
  await p.goto('http://127.0.0.1:'+server.address().port+'/game/index.html?autostart=1');
  await p.waitForFunction(()=>!document.getElementById('k64-loading').hidden);
  await p.waitForFunction(()=>window.Kart64TV?.ready,{timeout:180000});
  assert.equal(await p.evaluate(()=>Kart64TV.hub.list().length),2);
  assert.equal(await p.evaluate(()=>document.body.classList.contains('touch')),false);
  await p.keyboard.press('Escape');await p.waitForFunction(()=>Kart64TV.open);
  pendingControl={back:true};await p.waitForTimeout(500);assert.equal(await p.evaluate(()=>Kart64TV.open),true,'Native Back plus browser Back must never resume the game');
  await p.waitForTimeout(150);const swaps=await p.evaluate(()=>window.__kartFrameSwaps);await p.waitForTimeout(400);
  assert.equal(await p.evaluate(()=>window.__kartFrameSwaps),swaps,'Game must actually stop while the menu is open');
  await p.keyboard.press('ArrowDown');await p.keyboard.press('Enter');
  await p.getByRole('heading',{name:'Controller select'}).waitFor();
  await p.getByRole('button',{name:'Change bindings',exact:true}).first().click();
  await p.locator('.tv-binding button').first().click();await p.waitForTimeout(100);
  await p.evaluate(()=>__rawPads[0].buttons[3]={pressed:true,value:1});
  await p.getByText('Binding saved.',{exact:true}).waitFor();
  await p.evaluate(()=>__rawPads[0].buttons[3]={pressed:false,value:0});
  assert.equal(await p.evaluate(()=>Kart64TV.hub.profile(Kart64TV.hub.list()[0].key).buttons[0]),3);
  await p.getByRole('button',{name:'Back to controllers'}).click();
  await p.getByRole('button',{name:'Assign player 2',exact:true}).click();
  assert.equal(await p.evaluate(()=>document.activeElement.textContent),'Assign player 3','Assignment focus must stay on the same controller');
  assert.equal(await p.evaluate(()=>navigator.getGamepads()[1].id),'Xbox Wireless Controller');
  await p.getByRole('button',{name:'Back',exact:true}).click();
  await p.getByRole('button',{name:'Sound & display'}).click();
  await p.getByRole('button',{name:'75% render scale',exact:true}).click();
  await p.getByRole('button',{name:'Volume −'}).click();
  await p.getByRole('button',{name:'Volume +',exact:true}).click();assert.equal(await p.evaluate(()=>document.activeElement.textContent.includes('Volume +')),true,'Volume controls must retain controller focus');
  await p.getByRole('button',{name:'Volume −'}).click();
  await p.getByRole('button',{name:'Back',exact:true}).click();
  await p.getByRole('button',{name:'Resume game',exact:true}).click();await p.waitForTimeout(400);
  assert.ok(await p.evaluate(()=>window.__kartFrameSwaps)>swaps);
  assert.ok(Math.abs(await p.evaluate(()=>__tvGain.gain.value)-.9)<.001);
  // UI controls stay on the physical layout after gameplay A has been rebound to Y.
  await p.keyboard.press('Escape');await p.evaluate(()=>__rawPads[0].buttons[13]={pressed:true,value:1});await p.waitForTimeout(80);
  await p.evaluate(()=>__rawPads[0].buttons[13]={pressed:false,value:0});await p.waitForTimeout(250);
  await p.evaluate(()=>__rawPads[0].buttons[0]={pressed:true,value:1});await p.getByRole('heading',{name:'Controller select'}).waitFor();
  await p.evaluate(()=>__rawPads[0].buttons[0]={pressed:false,value:0});await p.waitForTimeout(400);
  await p.keyboard.press('Escape');await p.evaluate(()=>__rawPads[0].buttons[0]={pressed:true,value:1});await p.waitForFunction(()=>!Kart64TV.open);
  assert.equal(await p.evaluate(()=>navigator.getGamepads()[1].buttons.some(b=>b.pressed)),false);
  await p.evaluate(()=>__rawPads[0].buttons[0]={pressed:false,value:0});await p.waitForTimeout(100);
  await p.evaluate(()=>__rawPads[0].buttons[3]={pressed:true,value:1});
  await p.waitForTimeout(100);assert.equal(await p.evaluate(()=>navigator.getGamepads()[1].buttons[0].pressed),true);
  await p.evaluate(()=>{__rawPads[0].buttons[3]={pressed:false,value:0};window.__gone=__rawPads[0];__rawPads[0]=null;});
  await p.waitForFunction(()=>Kart64TV.open);assert.equal(await p.evaluate(()=>Kart64TV.engine.paused()),true);
  await p.evaluate(()=>__rawPads[0]=window.__gone);await p.waitForTimeout(350);assert.equal(await p.evaluate(()=>Kart64TV.open),true);
  await p.getByRole('button',{name:'Resume game',exact:true}).click();
  await p.keyboard.press('Escape');
  await p.evaluate(()=>{window.__second=__rawPads[1];__rawPads[1]=null;});
  await p.getByRole('button',{name:'Continue with connected controllers',exact:true}).waitFor();
  await p.evaluate(()=>__rawPads[1]=window.__second);await p.waitForTimeout(200);
  await p.getByRole('button',{name:'Exit game…'}).click();
  await p.evaluate(()=>{window.__sync=FS.syncfs;FS.syncfs=(populate,cb)=>window.__pendingSave=cb;});
  await p.getByRole('button',{name:'Save & exit'}).click();await p.getByText('Saving…',{exact:true}).waitFor();
  await p.keyboard.press('Escape');assert.equal(await p.evaluate(()=>Kart64TV.open),true);
  await p.evaluate(()=>window.__pendingSave(Error('test write failure')));await p.getByText(/Exit cancelled: test write failure/).waitFor();
  assert.equal(await p.evaluate(()=>Kart64TV.engine.paused()),true);
  await p.evaluate(()=>{FS.syncfs=window.__sync;FS.writeFile('/data/tv-shell-browser-check.bin',new Uint8Array([8,6,4,2]));});
  await p.getByRole('button',{name:'Save & exit'}).click();await p.waitForURL('**/assets/launch.html');
  await p.locator('#start').click();await p.waitForFunction(()=>Kart64TV?.ready,{timeout:180000});
  assert.deepEqual(await p.evaluate(()=>Array.from(FS.readFile('/data/tv-shell-browser-check.bin'))),[8,6,4,2]);
  assert.equal(await p.evaluate(()=>Kart64TV.hub.profile(Kart64TV.hub.list()[0].key).buttons[0]),3);
  await p.evaluate(async()=>{FS.unlink('/data/tv-shell-browser-check.bin');await Kart64TV.engine.flush();});
  assert.deepEqual(errors,[]);
  const failed=await browser.newPage();await failed.route('**/Spaghettify.js',route=>route.abort());
  await failed.goto('http://127.0.0.1:'+server.address().port+'/game/index.html?autostart=1');
  const retry=failed.getByRole('button',{name:'Retry startup',exact:true});await retry.waitFor();
  assert.equal(await retry.evaluate(node=>node===document.activeElement),true,'Loading retry must be reachable with TV OK');await failed.close();
  console.log('PASS: actual game boot/loading, pause/resume buffer swaps, Xbox/PS5 synthetic input, UI remap and persistence, player swap, audio gain, render scale, disconnect/reconnect, failed exit protection and successful save round-trip.');
 }finally{await browser.close();server.close();}
}
main().catch(error=>{console.error(error);server.close();process.exitCode=1;});
