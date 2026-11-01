// Owned local full-app observation; all original bindings are real browser APIs.
import fs from 'node:fs/promises';import path from 'node:path';import http from 'node:http';import {createHash} from 'node:crypto';import {spawn,execFileSync} from 'node:child_process';import {createInterface} from 'node:readline';import {createRequire} from 'node:module';
const config=JSON.parse(await fs.readFile(process.argv[2],'utf8')),out=config.directory,hash=x=>createHash('sha256').update(x).digest('hex');
const packageRaw=await fs.readFile(path.join(config.playwright_path,'package.json'));
if(hash(packageRaw)!==config.playwright_package_sha256||JSON.parse(packageRaw).version!==config.playwright_version||hash(await fs.readFile(config.chrome_path))!==config.chrome_sha256)throw Error('Frozen browser tool identity');
const {chromium}=createRequire(import.meta.url)(config.playwright_path);
let server,bs,browser,context,worker,origin,pending,watchdog,capture,result,error,status='setup',finished=false,assetQueue=Promise.resolve();
const events=[],requests=[],blocked=[],errors=[],logs=[];const began=Date.now();
function pgid(pid){try{return Number(execFileSync('/bin/ps',['-o','pgid=','-p',String(pid)],{encoding:'utf8'}).trim())||null;}catch{return null;}}
async function journal(){await fs.writeFile(path.join(out,'runtime.json'),JSON.stringify({status,error,result,events,requests,blocked,errors,logs,pid:process.pid,browser_pid:bs?.process().pid,worker_pid:worker?.pid,elapsed_ms:Date.now()-began},null,2)+'\n');}
async function stop(child,label){if(!child)return;if(child.exitCode===null&&child.signalCode===null){child.kill('SIGTERM');await Promise.race([new Promise(r=>child.once('exit',r)),new Promise(r=>setTimeout(r,2000))]);if(child.exitCode===null&&child.signalCode===null){child.kill('SIGKILL');await new Promise(r=>child.once('exit',r));}}events.push({label,pid:child.pid,exit_code:child.exitCode,signal:child.signalCode});}
async function close(){if(finished)return;finished=true;clearTimeout(watchdog);await context?.close().catch(()=>{});await browser?.close().catch(()=>{});await bs?.close().catch(()=>{});await stop(bs?.process(),'browser_terminal');if(worker){worker.stdin.end();await stop(worker,'worker_terminal');}if(capture?.handle)await capture.handle.close();if(server)await new Promise(r=>server.close(r));await journal();}
process.on('SIGTERM',()=>{status='outer_deadline';void close().finally(()=>process.exit(124));});
try{
 const original=await fs.readFile(config.original_path),glue=await fs.readFile(config.glue_path),aux=await fs.readFile(config.aux_path),font=await fs.readFile(config.font_path),index=await fs.readFile(config.name_index_path),script=await fs.readFile(new URL('./browser_full_app135.mjs',import.meta.url));
 if(hash(original)!==config.original_sha256||hash(glue)!==config.glue_sha256||hash(glue.subarray(0,config.glue_prefix_bytes))!==config.official_glue_sha256||hash(aux)!==config.aux_sha256||hash(font)!==config.font_sha256||font.length!==config.font_bytes||hash(index)!==config.name_index_sha256)throw Error('Frozen route identity');
 worker=spawn(config.python_path,[config.asset_worker_script,'--asset-worker',process.argv[2]],{stdio:['pipe','pipe','pipe'],env:{...process.env,PYTHONUNBUFFERED:'1'}});
 events.push({label:'worker_started',pid:worker.pid,pgid:pgid(worker.pid)});
 let readyResolve,readyReject;const ready=new Promise((r,j)=>{readyResolve=r;readyReject=j;});let stderr='';worker.stderr.on('data',x=>stderr+=x);
 createInterface({input:worker.stdout}).on('line',line=>{try{const value=JSON.parse(line);if(value.worker_ready){readyResolve();return;}if(!pending)throw Error('Unexpected worker response');const p=pending;pending=null;p.resolve(value);}catch(e){readyReject(e);pending?.reject(e);pending=null;}});
 worker.on('exit',(code,signal)=>{if(!finished){const e=Error(`Worker ${code}/${signal}: ${stderr}`);readyReject(e);pending?.reject(e);pending=null;}});await ready;
 const html='<!doctype html><meta charset="utf-8"><style>html,body{margin:0;overflow:hidden}canvas{width:100vw;height:100vh;outline:none}</style><canvas id="benilla" tabindex="0" width="960" height="540"></canvas>';
 const routes=new Map([['/',['text/html',Buffer.from(html)]],['/original.wasm',['application/wasm',original]],['/bridge.mjs',['text/javascript',glue]],['/observe.mjs',['text/javascript',script]],['/data/__index',['application/json',index]],['/data/fonts/azs_sc.ttf',['font/ttf',font]],['/snippets/benilla-app-e11f90d5572a787b/inline0.js',['text/javascript',aux]]]);
 server=http.createServer(async(req,res)=>{const url=new URL(req.url,origin),row={method:req.method,path:url.pathname};requests.push(row);try{
  if(!['127.0.0.1','::ffff:127.0.0.1'].includes(req.socket.remoteAddress)||url.origin!==origin||url.search){row.status=403;res.writeHead(403);res.end();return;}
  if(req.method==='POST'&&url.pathname==='/capture/original_app.memory'){
   const offset=Number(req.headers['x-capture-offset']),total=Number(req.headers['x-capture-total']);if(!Number.isSafeInteger(offset)||!Number.isSafeInteger(total)||total<1||total>config.memory_cap_bytes)throw Error('Capture budget');
   if(!capture){if(offset!==0)throw Error('Capture offset');capture={bytes:0,total,hash:createHash('sha256'),handle:await fs.open(path.join(out,'original_app.memory'),'wx')};}
   if(capture.total!==total||capture.bytes!==offset)throw Error('Capture ordering');let bytes=0;
   for await(const chunk of req){bytes+=chunk.length;if(bytes>config.capture_chunk_bytes||capture.bytes+chunk.length>total)throw Error('Capture chunk budget');capture.hash.update(chunk);await capture.handle.write(chunk);capture.bytes+=chunk.length;}
   const value={bytes:capture.bytes,complete:capture.bytes===total};if(value.complete){value.sha256=capture.hash.digest('hex');await capture.handle.close();capture.handle=null;capture.sha256=value.sha256;}
   row.status=200;res.writeHead(200,{'Content-Type':'application/json'});res.end(JSON.stringify(value));return;
  }
  if(req.method!=='GET'){row.status=403;res.writeHead(403);res.end();return;}
  let route=routes.get(url.pathname);
  if(!route&&url.pathname.startsWith('/data/')){
   const requestPath=decodeURIComponent(url.pathname.slice(6));const queued=assetQueue.then(()=>new Promise((resolve,reject)=>{if(pending)throw Error('Asset worker serialization');pending={resolve,reject};worker.stdin.write(JSON.stringify({path:requestPath})+'\n');}));assetQueue=queued;const value=await queued;row.asset=value;
   if(value.status!==200){row.status=value.status;res.writeHead(value.status);res.end(value.error||value.reason||'Missing');return;}const raw=await fs.readFile(value.file);if(hash(raw)!==value.sha256||raw.length!==value.bytes)throw Error('Actual asset drift');route=['application/octet-stream',raw];
  }
  if(!route){row.status=404;res.writeHead(404);res.end();return;}row.status=200;row.bytes=route[1].length;res.writeHead(200,{'Content-Type':route[0],'Content-Length':route[1].length,'Cache-Control':'no-store','Content-Security-Policy':"default-src 'none';script-src 'self' 'wasm-unsafe-eval';style-src 'unsafe-inline';img-src 'self' data: blob:;connect-src 'self';worker-src 'none';base-uri 'none';form-action 'none'"});res.end(route[1]);
 }catch(e){row.status=500;row.error=String(e);if(!res.headersSent)res.writeHead(500);res.end(String(e));}});
 server.on('upgrade',(req,socket)=>{blocked.push({kind:'websocket_upgrade',url:req.url});socket.destroy();});
 await new Promise((r,j)=>{server.once('error',j);server.listen(0,'127.0.0.1',r);});origin='http://127.0.0.1:'+server.address().port;
 bs=await chromium.launchServer({headless:true,executablePath:config.chrome_path,downloadsPath:path.join(out,'browser-artifacts'),proxy:{server:'http://127.0.0.1:9',bypass:'127.0.0.1,localhost,[::1]'},args:[...config.browser_extra_args,'--js-flags=--wasm-max-mem-pages='+config.memory_page_cap+' --max-old-space-size=512','--disable-background-networking','--disable-quic','--host-resolver-rules=EXCLUDE 127.0.0.1, EXCLUDE localhost, EXCLUDE [::1], MAP * ~NOTFOUND'],timeout:20000});
 events.push({label:'browser_started',pid:bs.process().pid,pgid:pgid(bs.process().pid),spawnargs:bs.process().spawnargs});browser=await chromium.connect(bs.wsEndpoint());context=await browser.newContext({viewport:{width:960,height:540},acceptDownloads:false,serviceWorkers:'block'});
 await context.route('**/*',async route=>{if(new URL(route.request().url()).origin!==origin){blocked.push({kind:'external_request',url:route.request().url()});await route.abort();}else await route.continue();});
 const page=await context.newPage();page.on('pageerror',e=>errors.push(String(e.stack||e)));page.on('console',x=>{if(logs.length<1000)logs.push({type:x.type(),text:x.text()});});page.on('download',()=>blocked.push({kind:'download'}));
 page.setDefaultTimeout(90000);watchdog=setTimeout(()=>{status='browser_deadline';error='Owned90s browser deadline';void close().finally(()=>process.exit(124));},90000);
 await page.goto(origin,{waitUntil:'domcontentloaded',timeout:15000});status='running';await journal();
 result=await page.evaluate(async c=>await(await import('/observe.mjs')).observeFullApp135(c),config);status=result.status;
 await page.screenshot({path:path.join(out,'original-app.png')});
 const rendererErrors=errors.length>0||logs.some(x=>x.type==='error'&&/panicked|createBuffer failed|device lost/i.test(x.text));
 result.renderer_observation_status=rendererErrors?'renderer_boundary_preserved':'no_renderer_error_reported_not_visual_acceptance';
 if(rendererErrors&&status==='observed_original_app_and_complete_idle_tick')status='observed_App_idle_tick_with_renderer_boundary';
 if(blocked.length)throw Error('A blocked external/network action was attempted');
}catch(e){status='failed_preserved';error=String(e.stack||e);process.exitCode=1;}
finally{await close();}
process.stdout.write(JSON.stringify({directory:out,status,error,contexts:result?.contexts.length,frames:result?.frames.length,memory_bytes:result?.memory_bytes})+'\n');
