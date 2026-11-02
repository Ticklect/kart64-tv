(async()=>{
 for(const node of document.querySelectorAll('[data-native-text]'))Kart64Theme.label(node,node.textContent);
 Kart64Theme.load('../game/tv-game-theme.css');
 let shared=false;try{shared=new WebAssembly.Memory({initial:1,maximum:2,shared:true}).buffer instanceof SharedArrayBuffer}catch(e){}
 const gl=!!document.createElement('canvas').getContext('webgl2');
 const result={sharedWasm:shared,webgl2:gl,isolated:crossOriginIsolated,gamepads:typeof navigator.getGamepads==='function'};
 fetch('../report',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(result)}).catch(()=>{});
 document.getElementById('details').textContent='Shared memory: '+(shared?'available':'unavailable')+' · WebGL2: '+(gl?'available':'unavailable')+' · Browser gamepads: '+(result.gamepads?'API present; physical controllers need device testing':'unavailable');
 const state=document.getElementById('state');
 if(!shared||!gl||!crossOriginIsolated){state.textContent='This TV lacks a browser feature required by the game.';return;}
 let installed=false;try{installed=(await fetch('../game/ready.json')).ok}catch(e){}
 state.textContent=installed?'Ready to race.':'Your game files are not installed yet. Use the Windows app to prepare and transfer them.';
 if(!installed)return;
 const play=document.getElementById('play'),controls=document.getElementById('controllers');play.hidden=false;controls.hidden=false;
 play.onclick=()=>location.href='../game/index.html?autostart=1';controls.onclick=()=>location.href='../game/index.html?setup=1';play.focus();
 addEventListener('keydown',e=>{if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();(document.activeElement===play?controls:play).focus();}});
 let held=false;
 function tick(){let pads=[];try{pads=Array.from(navigator.getGamepads()||[]).filter(Boolean)}catch(e){}
  document.getElementById('pads').textContent=pads.length?pads.length+' controller'+(pads.length===1?'':'s')+' ready · '+pads.map(p=>Kart64Controls.buttonName(p.id,0)==='Cross'?'PlayStation':/xbox|xinput/i.test(p.id)?'Xbox':'Gamepad').join(' / '):'Waiting for a controller…';
  const p=pads.find(p=>p.buttons.some(b=>b.pressed)||p.axes.some(a=>Math.abs(a)>.6));
  if(p&&!held){if(p.buttons[12]?.pressed||p.buttons[13]?.pressed||p.buttons[14]?.pressed||p.buttons[15]?.pressed||Math.abs(p.axes[0])>.6||Math.abs(p.axes[1])>.6)(document.activeElement===play?controls:play).focus();else if(p.buttons[0]?.pressed)document.activeElement?.click();}
  held=!!p;requestAnimationFrame(tick);
 }requestAnimationFrame(tick);
})();
