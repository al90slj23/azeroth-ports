// Owned bounded fresh browser + real MPQ file service; no other network endpoints.
import fs from'node:fs/promises';import path from'node:path';import http from'node:http';import{createHash}from'node:crypto';import{spawn}from'node:child_process';import{createInterface}from'node:readline';import{createRequire}from'node:module';
const config=JSON.parse(await fs.readFile(process.argv[2],'utf8')),out=config.directory,require=createRequire(import.meta.url),{chromium}=require(config.playwright_path),hash=x=>createHash('sha256').update(x).digest('hex');
let server,browserServer,browser,context,worker,watchdog,origin,result,error=null,status='setup',finished=false,workerPending=null,assetReady;
const lifecycle=[],requests=[],blocked=[],browserErrors=[],consoleLines=[],captures=[],captureWork=new Map();const started=Date.now();
async function journal(){await fs.writeFile(path.join(out,'entry-world135-runtime.json'),JSON.stringify({status,error,started_ms:started,elapsed_ms:Date.now()-started,pid:process.pid,browser_pid:browserServer?.process()?.pid,worker_pid:worker?.pid,
 lifecycle,requests,blocked,browserErrors,consoleLines,captures,result,source_glue_sha256:config.official_glue_sha256,external_network_permitted:false,user_profile_used:false,
 memory_cap_bytes:config.memory_cap_bytes,allowed_imports:config.imports.filter(x=>x.allowed),other_denied_imports:config.imports.filter(x=>!x.allowed).length},null,2)+'\n');}
async function stopChild(p,label){if(!p)return;if(p.exitCode===null&&p.signalCode===null){p.kill('SIGTERM');await Promise.race([new Promise(r=>p.once('exit',r)),new Promise(r=>setTimeout(r,2000))]);if(p.exitCode===null&&p.signalCode===null){p.kill('SIGKILL');await new Promise(r=>p.once('exit',r));}}lifecycle.push({event:label,pid:p.pid,exit_code:p.exitCode,signal_code:p.signalCode});}
async function close(){if(finished)return;finished=true;if(watchdog)clearTimeout(watchdog);
 try{await context?.close();}catch(e){lifecycle.push({event:'context_close_error',error:String(e)});}try{await browser?.close();}catch{}
 try{await browserServer?.close();}catch{}if(browserServer)await stopChild(browserServer.process(),'browser_final');
 if(worker){worker.stdin.end();await stopChild(worker,'asset_worker_final');}if(server)await new Promise(r=>server.close(r));lifecycle.push({event:'http_server_closed'});await journal();}
process.on('SIGTERM',()=>{status='outer_interrupted';error='Owned outer120s deadline';void close().finally(()=>process.exit(124));});
try{
 const wasm=await fs.readFile(config.wasm_path),glue=await fs.readFile(config.glue_path),index=await fs.readFile(config.name_index_path),aux=await fs.readFile(config.aux_path),caseScript=await fs.readFile(new URL('./browser_entry_world135.mjs',import.meta.url));
 if(hash(wasm)!==config.wasm_sha256||hash(glue)!==config.glue_sha256||hash(glue.subarray(0,config.official_glue_prefix_bytes))!==config.official_glue_sha256||hash(index)!==config.name_index_sha256||hash(aux)!==config.aux_sha256)throw Error('Frozen route identity');
 worker=spawn(config.python_path,[config.asset_worker_script,'--asset-worker',process.argv[2]],{stdio:['pipe','pipe','pipe'],env:{...process.env,PYTHONUNBUFFERED:'1'}});
 let readyResolve,readyReject;assetReady=new Promise((r,j)=>{readyResolve=r;readyReject=j;});let workerStderr='';worker.stderr.on('data',x=>{workerStderr+=x;});
 createInterface({input:worker.stdout}).on('line',line=>{try{const v=JSON.parse(line);if(v.worker_ready){readyResolve();return;}if(!workerPending)throw Error('Unsolicited asset response');const p=workerPending;workerPending=null;p.resolve(v);}catch(e){readyReject(e);workerPending?.reject(e);workerPending=null;}});
 worker.on('exit',(code,signal)=>{if(!finished){const e=Error('Asset worker exited '+code+'/'+signal+':'+workerStderr);readyReject(e);workerPending?.reject(e);workerPending=null;}});
 await assetReady;lifecycle.push({event:'asset_worker_ready',pid:worker.pid});
 function asset(pathname){if(workerPending)throw Error('Concurrent asset requests exceed serial fixture');return new Promise((resolve,reject)=>{workerPending={resolve,reject};worker.stdin.write(JSON.stringify({path:pathname})+'\n');});}
 const routes=new Map([['/',['text/html',Buffer.from('<!doctype html><meta charset="utf-8"><title>Fixed135 true-world probe</title>')]],['/bridge.mjs',['text/javascript',glue]],['/case.mjs',['text/javascript',caseScript]],['/entry.wasm',['application/wasm',wasm]],['/data/__index',['application/json',index]],['/snippets/benilla-app-e11f90d5572a787b/inline0.js',['text/javascript',aux]]]);
 server=http.createServer(async(req,res)=>{const url=new URL(req.url,origin),entry={method:req.method,path:url.pathname,url:url.href,at:Date.now()};requests.push(entry);
  try{
   if(url.origin!==origin||!['127.0.0.1','::ffff:127.0.0.1'].includes(req.socket.remoteAddress)||url.search){entry.status=403;res.writeHead(403);res.end();return;}
   if(req.method==='POST'&&/^\/capture\/[a-z0-9_]+\.memory$/.test(url.pathname)){
    const filename=url.pathname.split('/').at(-1),offset=Number(req.headers['x-capture-offset']),total=Number(req.headers['x-capture-total']);
    if(!Number.isSafeInteger(offset)||!Number.isSafeInteger(total)||offset<0||total<1||total>config.memory_cap_bytes||captures.some(x=>x.file===filename))throw Error('Capture input/budget');
    let state=captureWork.get(filename);if(!state){if(offset!==0||captureWork.size+captures.length>=5)throw Error('Capture count/order');state={file:filename,total,bytes:0,hash:createHash('sha256'),handle:await fs.open(path.join(out,filename),'wx')};captureWork.set(filename,state);}
    if(offset!==state.bytes||total!==state.total)throw Error('Capture chunk order/size');let bytes=0;
    for await(const chunk of req){bytes+=chunk.length;if(bytes>config.capture_chunk_bytes||state.bytes+chunk.length>total)throw Error('Capture chunk cap');state.hash.update(chunk);await state.handle.write(chunk);state.bytes+=chunk.length;}
    const cap={file:filename,bytes:state.bytes,complete:state.bytes===total};if(cap.complete){await state.handle.close();cap.sha256=state.hash.digest('hex');captures.push(cap);captureWork.delete(filename);}
    entry.status=200;entry.bytes=bytes;entry.capture_offset=offset;res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify(cap));if(cap.complete)await journal();return;
   }
   if(req.method!=='GET'){entry.status=403;res.writeHead(403);res.end();return;}
   if(url.pathname==='/asset-status'){entry.status=200;res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify({non200:requests.filter(x=>x.path.startsWith('/data/')&&x.status!==200).map(x=>({path:x.path,status:x.status,error:x.asset?.error||x.error||x.asset?.reason}))}));return;}
   let route=routes.get(url.pathname);
   if(!route&&url.pathname.startsWith('/data/')){const actual=await asset(decodeURIComponent(url.pathname.slice(6)));entry.asset=actual;if(actual.status!==200){entry.status=actual.status;res.writeHead(actual.status);res.end(actual.error||actual.reason||'Missing');return;}const bytes=await fs.readFile(actual.file);if(hash(bytes)!==actual.sha256||bytes.length!==actual.bytes)throw Error('Decoded MPQ served bytes drift');route=['application/octet-stream',bytes];}
   if(!route){entry.status=404;res.writeHead(404);res.end();return;}entry.status=200;entry.bytes=route[1].length;entry.sha256=hash(route[1]);
   res.writeHead(200,{'Content-Type':route[0],'Content-Length':route[1].length,'Cache-Control':'no-store','Content-Security-Policy':"default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'; worker-src 'none'; base-uri 'none'; form-action 'none'"});res.end(route[1]);
  }catch(e){entry.status=500;entry.error=String(e);if(!res.headersSent)res.writeHead(500);res.end(String(e));}});
 await new Promise((r,j)=>{server.once('error',j);server.listen(0,'127.0.0.1',r);});origin='http://127.0.0.1:'+server.address().port;lifecycle.push({event:'http_listening',origin});
 browserServer=await chromium.launchServer({headless:true,executablePath:config.chrome_path,downloadsPath:path.join(out,'browser-artifacts'),
  proxy:{server:'http://127.0.0.1:9',bypass:'127.0.0.1,localhost,[::1]'},args:['--js-flags=--wasm-max-mem-pages='+config.memory_page_cap+' --max-old-space-size=512','--disable-background-networking','--disable-quic','--host-resolver-rules=EXCLUDE 127.0.0.1, EXCLUDE localhost, EXCLUDE [::1], MAP * ~NOTFOUND'],timeout:20000});
 lifecycle.push({event:'browser_started',pid:browserServer.process().pid,spawnargs:browserServer.process().spawnargs});browser=await chromium.connect(browserServer.wsEndpoint());context=await browser.newContext({acceptDownloads:false,serviceWorkers:'block'});
 await context.route('**/*',async route=>{if(new URL(route.request().url()).origin!==origin){blocked.push(route.request().url());await route.abort('blockedbyclient');}else await route.continue();});
 const page=await context.newPage();page.on('pageerror',e=>browserErrors.push(String(e)));page.on('console',m=>consoleLines.push({type:m.type(),text:m.text()}));page.on('download',()=>browserErrors.push('Unexpected download'));
 page.setDefaultTimeout(95000);watchdog=setTimeout(()=>{status='browser_deadline';error='Owned90s browser deadline';void close().finally(()=>process.exit(124));},config.deadline_seconds*1000);
 await page.goto(origin+'/',{waitUntil:'domcontentloaded',timeout:15000});status='running';await journal();
 result=await page.evaluate(async c=>{const m=await import('/case.mjs');return await m.runEntryWorld135(c);},config);status=result.status;
 if(blocked.length||browserErrors.length)throw Error('External/browser error');if(result.appstart_exports_called||result.finalizer_called||result.all_storage_keys.length||result.session_keys.length||result.indexeddb_databases.length)throw Error('Isolation state changed');
}catch(e){status='failed_preserved';error=String(e.stack||e);process.exitCode=1;}
finally{await close();}
process.stdout.write(JSON.stringify({status,error,directory:out,original_result:result?.status,stopped_stage:result?.error?.stage,stopped_error:result?.error?.message,requests:requests.length,captures:captures.length})+'\n');
