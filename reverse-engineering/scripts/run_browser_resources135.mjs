// Separate embedding experiment: only audited real resource imports allowed.
import fs from'node:fs/promises';import path from'node:path';import http from'node:http';import{createHash}from'node:crypto';import{createRequire}from'node:module';
const config=JSON.parse(await fs.readFile(process.argv[2],'utf8')),out=config.directory,require=createRequire(import.meta.url),{chromium}=require(config.playwright_path);
const digest=x=>createHash('sha256').update(x).digest('hex');const requests=[],blocked=[],errors=[],lifecycle=[];let server,browserServer,browser,context,page,watchdog,finished=false;
let status='not_started',result=null,errorText=null;const began=Date.now(),runtimeFile=path.join(out,'browser-resource135-runtime.json');
const artifactRoot=path.join(out,'browser-artifacts');await fs.mkdir(artifactRoot,{recursive:true});
async function journal(){await fs.writeFile(runtimeFile,JSON.stringify({status,error:errorText,started_ms:began,elapsed_ms:Date.now()-began,process_pid:process.pid,
 browser_pid:browserServer?.process()?.pid,requests,blocked_requests:blocked,browser_errors:errors,lifecycle,result,
 embedding_separate_from_all878_denied_Node:true,allowed_resource_imports:config.imports.filter(x=>x.allowed),denied_other_import_count:config.imports.filter(x=>!x.allowed).length,
 new_headless_context:true,user_profile_used:false,user_tabs_used:false,external_network_permitted:false,asset_hashes:config.assets,source_glue_sha256:config.official_glue_sha256,
 appstart_called:false,full_game_started:false,downloads_performed:false,user_saves_accessed:false},null,2)+'\n');}
async function close(){
 if(finished)return;finished=true;if(watchdog)clearTimeout(watchdog);
 try{if(context)await context.close();lifecycle.push({event:'context_closed',at:Date.now()});}catch(e){lifecycle.push({event:'context_close_error',error:String(e)});}
 try{if(browser)await browser.close();}catch(e){lifecycle.push({event:'browser_connection_close_error',error:String(e)});}
 try{if(browserServer)await browserServer.close();}catch(e){lifecycle.push({event:'server_close_error',error:String(e)});}
 if(browserServer){const p=browserServer.process();lifecycle.push({event:'browser_process_final',pid:p.pid,exit_code:p.exitCode,signal_code:p.signalCode});if(p.exitCode===null&&p.signalCode===null){p.kill('SIGKILL');await new Promise(resolve=>p.once('exit',resolve));lifecycle.push({event:'browser_killed_and_waited',pid:p.pid,exit_code:p.exitCode,signal_code:p.signalCode});}}
 if(server)await new Promise(resolve=>server.close(resolve));lifecycle.push({event:'http_server_closed',at:Date.now()});await journal();
}
process.on('SIGTERM',()=>{status='interrupted';errorText='Owned outer deadline SIGTERM';void close().finally(()=>process.exit(124));});
try{
 const moduleBytes=await fs.readFile(config.wasm_path),bridge=await fs.readFile(config.glue_path),fixture=await fs.readFile(config.fixtures_path);
 if(digest(moduleBytes)!==config.wasm_sha256||digest(bridge)!==config.glue_sha256||digest(fixture)!==config.fixtures_sha256||digest(bridge.subarray(0,config.official_glue_prefix_bytes))!==config.official_glue_sha256)throw Error('Frozen served input identity');
 const routes=new Map([
  ['/',['text/html',Buffer.from('<!doctype html><meta charset="utf-8"><title>Fixed135 resource research</title><p>Isolated resource harness</p>')]],
  ['/bridge.mjs',['text/javascript',bridge]],['/case.mjs',['text/javascript',await fs.readFile(new URL('./browser_resource_case135.mjs',import.meta.url))]],
  ['/browser.wasm',['application/wasm',moduleBytes]],['/fixtures.json',['application/json',fixture]],
 ]);
 for(const[n,h]of Object.entries(config.assets)){const body=await fs.readFile(path.join(config.asset_root,n));if(digest(body)!==h)throw Error('Real resource asset identity');routes.set('/data/'+n,[n==='__index'?'application/json':'application/octet-stream',body]);}
 const aux=await fs.readFile(config.auxiliary_module.path);if(digest(aux)!==config.auxiliary_module.sha256)throw Error('Existing auxiliary module identity');routes.set(config.auxiliary_module.url,['text/javascript',aux]);
 let origin;
 server=http.createServer((req,res)=>{
  const url=new URL(req.url,origin),entry={method:req.method,url:url.href,path:url.pathname,at:Date.now()};requests.push(entry);
  if(url.origin!==origin||!['127.0.0.1','::ffff:127.0.0.1'].includes(req.socket.remoteAddress)||req.method!=='GET'){entry.status=403;res.writeHead(403);res.end();return;}
  const asset=routes.get(url.pathname);if(!asset||url.search){entry.status=404;res.writeHead(404);res.end();return;}
  entry.status=200;entry.bytes=asset[1].length;entry.sha256=digest(asset[1]);
  res.writeHead(200,{'Content-Type':asset[0],'Content-Length':asset[1].length,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
   'Content-Security-Policy':"default-src 'none'; script-src 'self' 'wasm-unsafe-eval'; connect-src 'self'; worker-src 'none'; base-uri 'none'; form-action 'none'"});res.end(asset[1]);
 });
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});origin='http://127.0.0.1:'+server.address().port;lifecycle.push({event:'http_listening',origin,pid:process.pid,at:Date.now()});
 browserServer=await chromium.launchServer({headless:true,executablePath:config.chrome_path,downloadsPath:artifactRoot,
  proxy:{server:'http://127.0.0.1:9',bypass:'127.0.0.1,localhost,[::1]'},
  args:['--js-flags=--wasm-max-mem-pages=2048 --max-old-space-size=512','--disable-background-networking','--disable-quic','--host-resolver-rules=EXCLUDE 127.0.0.1, EXCLUDE localhost, EXCLUDE [::1], MAP * ~NOTFOUND'],timeout:20000});
 lifecycle.push({event:'browser_started',pid:browserServer.process().pid,parent_pid:process.pid,spawnargs:browserServer.process().spawnargs,at:Date.now()});await journal();
 browser=await chromium.connect(browserServer.wsEndpoint());context=await browser.newContext({acceptDownloads:false,serviceWorkers:'block'});
 await context.route('**/*',async route=>{const url=new URL(route.request().url());if(url.origin!==origin){blocked.push({url:url.href,reason:'nonexact-loopback-origin'});await route.abort('blockedbyclient');}else await route.continue();});
 context.on('page',p=>{if(page&&p!==page){errors.push('Unexpected page');void p.close();}});
 page=await context.newPage();page.on('pageerror',e=>errors.push(String(e)));page.on('download',()=>{errors.push('Unexpected download');});
 page.setDefaultTimeout(30000);watchdog=setTimeout(()=>{status='timeout';errorText='Owned60s browser watchdog';void close().finally(()=>process.exit(124));},config.deadline_seconds*1000);
 await page.goto(origin+'/',{waitUntil:'domcontentloaded',timeout:15000});status='running';await journal();
 result=await page.evaluate(async c=>{const m=await import('/case.mjs');return await m.runBrowserResource135(c);},config);
 if(result.failures.length)throw Error('Independent known projection mismatch:'+result.failures.length);
 if(result.imports.some(x=>!x.allowed)||blocked.length||errors.length)throw Error('Unexpected import/network/browser error');
 if(!result.cap_verified||result.max_memory_bytes>config.memory_cap_bytes||result.appstart_exports_called||result.finalizer_called||result.local_storage_keys.length||result.indexeddb_databases.length)throw Error('Isolation contract');
 for(const name of Object.keys(config.assets))if(!requests.some(x=>x.path==='/data/'+name&&x.status===200&&x.sha256===config.assets[name]))throw Error('Actual resource request absent');
 status='passed';
}catch(error){status=status==='timeout'?status:'failed';errorText=String(error.stack||error);process.exitCode=1;}
finally{await close();}
process.stdout.write(JSON.stringify({status,error:errorText,directory:out,resource_requests:requests.filter(x=>x.path.startsWith('/data/')),cases:result?.cases,stages:result?.stages,mismatches:result?.failures?.length})+'\n');
