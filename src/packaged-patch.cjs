'use strict';

function replaceOnce(source,from,to){
 if(source.split(from).length!==2)throw Error('Unexpected packaged startup: '+from.slice(0,60));
 return source.replace(from,to);
}

// Only the pinned runtime is supported. Its .data bundle contains /torch
// extraction recipes, which a PC-prepared .o2r installation never needs.
function skipExtractionPreload(source){
 const start='if(!Module["expectedDataFileDownloads"])';
 const end=';var programArgs=[];';
 const a=source.indexOf(start),b=source.indexOf(end);
 if(a<0||b<=a||source.indexOf(start,a+1)!==-1||source.indexOf(end,b+1)!==-1)throw Error('Unexpected extraction preloader');
 const section=source.slice(a,b);
 const names=[...section.matchAll(/filename:"([^"]+)"/g)].map(x=>x[1]);
 if(names.length!==129||names.some(name=>!name.startsWith('/torch/'))||!section.endsWith('remote_package_size:7967812})})()'))throw Error('Unexpected extraction preload contents');
 let result=source.slice(0,a)+source.slice(b+1);
 result=replaceOnce(result,'var response=await readAsync(binaryFile);','var response=await(globalThis.Kart64Boot?Kart64Boot.readInstalledFile("Spaghettify.wasm",()=>readAsync(binaryFile)):readAsync(binaryFile));');
 return replaceOnce(result,'IDBFS.loadRemoteEntry(store,path,','(globalThis.Kart64Boot?Kart64Boot.loadRestoredEntry.bind(null,src,IDBFS):IDBFS.loadRemoteEntry)(store,path,');
}

function patchPackagedStartup(html){
 html=replaceOnce(html,'<script>\nconst ROM_SHA1', '<script src="packaged-boot.js"></script>\n<script>\nconst ROM_SHA1');
 html=replaceOnce(html,"  const r = await fetch(name);\n  if (!r.ok) throw new Error(name + ': HTTP ' + r.status);\n  FS.writeFile('/data/' + name, new Uint8Array(await r.arrayBuffer()), {canOwn:true});", "  const bytes = await Kart64Boot.readAsset(name);\n  FS.writeFile('/data/' + name, new Uint8Array(bytes), {canOwn:true});");
 html=replaceOnce(html,"await fetch('courses.json', { cache: 'no-cache' })","await Kart64Boot.fetchInstalled('courses.json', { cache: 'no-cache' })");
 html=replaceOnce(html,"await fetch(course.archive, { cache: 'no-cache' })","await Kart64Boot.fetchInstalled(course.archive, { cache: 'no-cache' })");
 html=replaceOnce(html,"packTx('readonly', st => st.getKey('current')).then(k => {\n  if (k) getPack().then(p => { installedPack = p?.name || null; showPack(); });\n}).catch(() => {});","const packPresence = packTx('readonly', st => st.getKey('current')).then(k => {\n  if (k) getPack().then(p => { installedPack = p?.name || null; showPack(); });\n  return !!k;\n}).catch(() => true);");
 html=replaceOnce(html,'async function installPack() {','async function installPack() {\n  const packChanged = !!pendingPack || removePack;');
 html=replaceOnce(html,'  const pack = await getPack().catch(() => null);','  const pack = await Kart64Boot.loadTexturePack(packPresence, packChanged, getPack);');
 const start="        if (!have('config.yml')) {";
 const end='        // Persist config/saves/extracted assets.';
 const a=html.indexOf(start),b=html.indexOf(end);
 if(a<0||b<=a||html.indexOf(start,a+1)!==-1||html.indexOf(end,b+1)!==-1)throw Error('Unexpected packaged setup');
 html=html.slice(0,a)+`        Kart64Boot.mark('storage-restored');
        say('Loading installed game data…');
        await Kart64Boot.prepareGame(FS, fetchInto, installPack, installCourses);
        Kart64Boot.mark('assets-ready');
        say('Starting the game…');
        overlay.classList.add('hidden');
`+html.slice(b);
 html=replaceOnce(html,"if (set) for (const k of Object.keys(set.entries)) if (/^\\/data\\/mods(\\/|$)/.test(k)) delete set.entries[k];",'if (set) for (const k of Object.keys(set.entries)) if (!Kart64Boot.persistentPath(k)) delete set.entries[k];');
 html=replaceOnce(html,"    FS.syncfs(true, async () => {","    Kart64Boot.mark('storage-restore-start');\n    FS.syncfs(true, async (storageError) => {\n      if (storageError) { say('Could not restore saved data. Reload to try again.', true); return; }");
 html=replaceOnce(html,"  onRuntimeInitialized: () => { runtimeReady = true; },","  onRuntimeInitialized: () => { runtimeReady = true; Kart64Boot.mark('runtime-ready'); },");
 html=replaceOnce(html,"  preRun: [function() {","  preRun: [function() {\n    Kart64Boot.mark('runtime-loaded');");
 html=replaceOnce(html,"    FS.mkdir('/data');","    FS.mkdir('/data');\n    Kart64Boot.configureStorage(IDBFS);");
 html=replaceOnce(html,"startBtn.onclick = () => {","startBtn.onclick = () => {\n  Kart64Boot.start();\n  say('Loading game engine…');");
 html=replaceOnce(html,'  if (extracting) { clearInterval(extracting);',"  if (!window.__kartBootReady) { window.__kartBootReady = true; Kart64Boot.mark('engine-ready'); }\n  if (extracting) { clearInterval(extracting);");
 return html;
}

module.exports={skipExtractionPreload,patchPackagedStartup};
