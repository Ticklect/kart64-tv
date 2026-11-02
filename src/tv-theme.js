/* Menu text uses the player's locally prepared sprite font when available. */
(function(root){
'use strict';
let pending;
function label(node,text){
 node.replaceChildren();node.setAttribute('aria-label',text);
 const fallback=document.createElement('span');fallback.className='tv-text-fallback';fallback.textContent=text;
 const native=document.createElement('span');native.className='tv-game-text';native.setAttribute('aria-hidden','true');
 for(const char of text.toUpperCase()){
  const glyph=document.createElement('i');glyph.className=char===' '?'tv-letter-space':'tv-letter';glyph.dataset.char=char;native.append(glyph);
 }
 node.append(fallback,native);return node;
}
function load(href){
 if(pending)return pending;
 pending=new Promise(resolve=>{
  const sheet=document.createElement('link');sheet.rel='stylesheet';sheet.href=href+(href.includes('?')?'&':'?')+'skin='+Date.now();sheet.dataset.privateGameTheme='true';
  sheet.onload=()=>{const masks=CSS.supports('mask-image','url("")')||CSS.supports('-webkit-mask-image','url("")');const loaded=masks&&getComputedStyle(document.body).getPropertyValue('--mk-theme-version').trim()==='1';document.body.classList.toggle('k64-native-theme',loaded);resolve(loaded);};
  sheet.onerror=()=>resolve(false);document.head.append(sheet);
 });return pending;
}
root.Kart64Theme={label,load};
})(window);
