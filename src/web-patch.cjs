// Bounded compatibility experiment for the browser port; not a general Wasm editor.
function leb(b,at,end){let value=0,shift=0;for(let i=0;i<5&&at<end;i++){const v=b[at++];value+=(v&127)*2**shift;if(!(v&128))return [value,at];shift+=7;}throw Error('Invalid LEB');}
function lowerImportedSharedMemory(input){
 const b=Buffer.from(input);if(b.length<8||b.subarray(0,8).toString('hex')!=='0061736d01000000')throw Error('Invalid Wasm');
 let p=8,patched=0;
 while(p<b.length){const id=b[p++];let size;[size,p]=leb(b,p,b.length);const end=p+size;if(end>b.length)throw Error('Truncated section');
  if(id===2){let count;[count,p]=leb(b,p,end);
   for(let i=0;i<count;i++){
    for(let n=0;n<2;n++){let len;[len,p]=leb(b,p,end);p+=len;if(p>end)throw Error('Invalid import name');}
    if(p>=end)throw Error('Invalid import');const kind=b[p++];
    if(kind===0){[,p]=leb(b,p,end);}
    else if(kind===1){p++;let flags;[flags,p]=leb(b,p,end);[,p]=leb(b,p,end);if(flags&1)[,p]=leb(b,p,end);}
    else if(kind===2){let flags,min,max;[flags,p]=leb(b,p,end);let start=p;[min,p]=leb(b,p,end);if(flags&1)[max,p]=leb(b,p,end);
     if(flags!==3||min!==8192||max!==32768||p-start<2||b[start]!==0x80||b[start+1]!==0x40)throw Error('Unexpected imported memory');
     b[start+1]=0x21;patched++;
    }else if(kind===3){p+=2;}else throw Error('Unsupported import kind');
   }
   if(p!==end)throw Error('Invalid import section length');
  }
  p=end;
 }
 if(patched!==1)throw Error('Expected one shared memory import');return b;
}
function patchGlue(s){
 for(const [old,replacement] of [['var INITIAL_MEMORY=536870912;','var INITIAL_MEMORY=276824064;'],['var pthreadPoolSize=16;','var pthreadPoolSize=2;'],['function _eglSwapBuffers(dpy,surface){','function _eglSwapBuffers(dpy,surface){if(!ENVIRONMENT_IS_PTHREAD)globalThis.__kartFrameSwaps=(globalThis.__kartFrameSwaps||0)+1;']]){
  if(s.split(old).length!==2)throw Error('Unexpected browser glue');s=s.replace(old,replacement);
 }return s;
}
function patchArchiveLoading(html){
 const old="FS.writeFile('/data/' + name, new Uint8Array(await r.arrayBuffer()));";
 const replacement="FS.writeFile('/data/' + name, new Uint8Array(await r.arrayBuffer()), {canOwn:true});";
 if(html.split(old).length!==2)throw Error('Unexpected browser archive loader');return html.replace(old,replacement);
}
function patchFirstRunNotice(html){
 const old=`<small id="blurb">Your ROM never leaves this device: it is verified and converted
  locally, the game's assets are extracted in your browser and cached in browser
  storage. Nothing is uploaded. <b>First run takes about a minute</b>; later visits
  boot instantly.</small>`;
 if(html.split(old).length!==2)throw Error('Unexpected first-run notice');
 return html.replace(old,'<small id="blurb">Your game data was prepared on your computer and installed on this TV. Starting the game can take several minutes.</small>');
}
function patchPackagedPage(html){
 html=patchFirstRunNotice(html);
 html=patchArchiveLoading(html);
 const end='</script>\n</body>\n</html>';
 if(html.split(end).length!==2)throw Error('Unexpected page ending');
 html=html.replace(end,'</script>\n<script src="diagnostics.js"></script>\n</body>\n</html>');
 const focusAnchor = "  startBtn.classList.remove('hidden');\n  if (!(navigator.maxTouchPoints > 0))";
 if(html.split(focusAnchor).length!==2)throw Error('Unexpected Start button setup');
 html=html.replace(focusAnchor,"  startBtn.classList.remove('hidden');\n  startBtn.focus();\n  if (!(navigator.maxTouchPoints > 0))");
 const replacements=[
  ["const isolated = self.crossOriginIsolated && typeof SharedArrayBuffer !== 'undefined';","const isolated = typeof SharedArrayBuffer !== 'undefined';"],
  ["const onLocalhost = ['localhost', '127.0.0.1'].includes(location.hostname);","const onLocalhost = true;"],
  ["if (!have('mk64.o2r') && qp.has('prebuilt') && onLocalhost) {","if (!have('mk64.o2r')) {"]
 ];
 for(const [old,replacement] of replacements){if(html.split(old).length!==2)throw Error('Unexpected browser page');html=html.replace(old,replacement);}
 return html;
}
module.exports={lowerImportedSharedMemory,patchGlue,patchArchiveLoading,patchFirstRunNotice,patchPackagedPage};
