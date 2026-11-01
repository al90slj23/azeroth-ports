// Owned natural game-entry host. Inputs use the browser; original memory is read only.
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {createHash} from 'node:crypto';
import {spawn, execFileSync} from 'node:child_process';
import {createInterface} from 'node:readline';
import {createRequire} from 'node:module';

const configPath = path.resolve(process.argv[2]);
const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
const out = path.resolve(config.directory), temporary = path.join(out, 'tmp');
const hash = value => createHash('sha256').update(value).digest('hex');
const json = value => JSON.stringify(value, (_, item) => typeof item === 'bigint' ? item.toString() : item, 2) + '\n';
const pause = milliseconds => new Promise(resolve => setTimeout(resolve, milliseconds));
async function hashFile(file) {
  const digest = createHash('sha256');
  for await (const chunk of createReadStream(file)) digest.update(chunk);
  return digest.digest('hex');
}
function bounded(promise, milliseconds, label) {
  let timer;
  return Promise.race([promise, new Promise((_, reject) => { timer = setTimeout(() => reject(Error(label)), milliseconds); })])
    .finally(() => clearTimeout(timer));
}
function pgid(pid) {
  try { return Number(execFileSync('/bin/ps', ['-o', 'pgid=', '-p', String(pid)], {encoding: 'utf8'}).trim()) || null; }
  catch { return null; }
}

let server, deadProxy, bs, browser, context, page, worker, origin, pending, watchdog, capture, result, error,observationReceipt;
let status = 'setup', closing = null, assetQueue = Promise.resolve(), networkBoundary = false, shutdown = false;
const began = Date.now(), events = [], requests = [], blocked = [], errors = [], logs = [], inputs = [], observations = [];
const passiveRequests = [], trustedInputEvents = [], sockets = new Set(), proxySockets = new Set(), assets = new Map();
let assetBytes = 0, lastControl = null, screenshotCount = 0, journalQueue = Promise.resolve();
let assetsInFlight=0,lastAssetActivity=Date.now();
const innerMilliseconds = config.inner_deadline_seconds * 1000;
// Leave room for bounded owned-process cleanup inside the configured inner deadline.
const executionDeadline = began + innerMilliseconds - 6500;
async function atomicJSON(name, value) {
  const target = path.join(out, name), temporaryFile = target + '.tmp-' + process.pid;
  await fs.writeFile(temporaryFile, json(value));
  await fs.rename(temporaryFile, target);
}
function journal() {
  journalQueue = journalQueue.catch(() => {}).then(async () => {
    await atomicJSON('owned-hosts.json', {events: events.filter(row => ['worker_started', 'browser_started'].includes(row.label))});
    await atomicJSON('runtime.json', {
    status, error, result, events, requests, passive_requests: passiveRequests, blocked, errors, logs, inputs,
    control_observations: observations, last_control: lastControl, trusted_input_events: trustedInputEvents,
    network_boundary: networkBoundary, capture: capture ? {bytes: capture.bytes, total: capture.total, complete: capture.complete, sha256: capture.sha256} : null,
    pid: process.pid, browser_pid: bs?.process().pid, worker_pid: worker?.pid, elapsed_ms: Date.now() - began,
    inner_deadline_seconds: config.inner_deadline_seconds, cleanup_reserve_ms: 6500,
    playwright_request_interception_installed: false,
    pre_upload_observation_receipt:observationReceipt,
    assets_in_flight:assetsInFlight,last_asset_activity_ms:lastAssetActivity-began,
    });
  });
  return journalQueue;
}
async function stop(child, label) {
  if (!child) return;
  if (child.exitCode === null && child.signalCode === null) {
    child.kill('SIGTERM');
    await bounded(new Promise(resolve => child.once('exit', resolve)), 900, 'Owned TERM wait').catch(() => {});
    if (child.exitCode === null && child.signalCode === null) {
      child.kill('SIGKILL');
      await bounded(new Promise(resolve => child.once('exit', resolve)), 900, 'Owned KILL wait').catch(() => {});
    }
  }
  events.push({label, pid: child.pid, pgid: pgid(child.pid), exit_code: child.exitCode, signal: child.signalCode});
}
async function close() {
  if (closing) return closing;
  shutdown = true;
  closing = (async () => {
    clearTimeout(watchdog);
    pending?.reject(Error('Owned host is closing')); pending = null;
    worker?.stdin.end();
    await Promise.allSettled([
      context ? bounded(context.close(), 1200, 'Context close deadline') : Promise.resolve(),
      browser ? bounded(browser.close(), 1200, 'Browser connection close deadline') : Promise.resolve(),
      bs ? bounded(bs.close(), 1200, 'Browser server close deadline') : Promise.resolve(),
    ]);
    await Promise.allSettled([stop(bs?.process(), 'browser_terminal'), stop(worker, 'worker_terminal')]);
    for (const socket of [...sockets, ...proxySockets]) socket.destroy();
    await Promise.allSettled([server, deadProxy].filter(Boolean).map(value => bounded(new Promise(resolve => value.close(resolve)), 800, 'Owned HTTP close deadline')));
    if (capture?.handle) { await capture.handle.close().catch(() => {}); capture.handle = null; }
    await journal();
  })();
  return closing;
}
process.on('SIGTERM', () => {
  status = 'outer_deadline'; error ??= 'Owned host received SIGTERM';
  void close().finally(() => process.exit(124));
});

async function control() {
  if (!page || page.isClosed()) throw Error('Original observation page is closed');
  const remaining = executionDeadline-Date.now();
  if (remaining <= 0) throw Error('Owned execution deadline before control read');
  // Real startup/render work can occupy the browser thread for several seconds.
  // Keep this single read pending under the owned overall deadline; a short
  // observation timeout must not terminate a still-live original operation.
  const state = await bounded(page.evaluate(() => ({
    control: globalThis.__gameEntry135Control?.status() ?? null,
    task: globalThis.__gameEntry135TaskOutcome ?? null,
  })), remaining, 'Owned execution deadline while reading control status');
  lastControl = state;
  return state;
}
function recordControl(stage, state) { observations.push({stage, elapsed_ms: Date.now() - began, ...state}); }
async function requestStop(reason) {
  if (!page || page.isClosed()) return false;
  return bounded(page.evaluate(value => {
    if (!globalThis.__gameEntry135Control) return false;
    globalThis.__gameEntry135Control.requestStop(value); return true;
  }, reason), 2000, 'Observer stop request deadline');
}
async function waitControl(predicate, milliseconds, stage) {
  const until = Math.min(Date.now() + milliseconds, executionDeadline);
  events.push({label:'control_wait_started',stage,elapsed_ms:Date.now()-began});
  await journal();
  let state;
  while (Date.now() < until && !shutdown) {
    state = await control();
    if (state.task?.done && !state.task.ok) throw Error('Original observation task rejected: ' + state.task.error);
    if (predicate(state.control) || state.control?.finished || state.task?.done || state.control?.error || networkBoundary) break;
    await pause(100);
  }
  if (!state) throw Error('No control status before ' + stage + ' deadline');
  recordControl(stage, state); await journal(); return state;
}
async function screenshot(name) {
  if (!page || page.isClosed() || shutdown) return false;
  try {
    await bounded(page.screenshot({path: path.join(out, name), timeout: 5000}), 5500, 'Screenshot deadline');
    events.push({label: 'screenshot_saved', name, elapsed_ms: Date.now() - began}); screenshotCount++; return true;
  } catch (exception) {
    events.push({label: 'screenshot_boundary', name, error: String(exception)}); return false;
  }
}
function external(kind, url, method) {
  blocked.push({kind, url, ...(method ? {method} : {}), elapsed_ms: Date.now() - began});
  networkBoundary = true;
  if (!shutdown) void requestStop('non_loopback_network_boundary').catch(() => {});
}
function proxyRejected(kind, url, method) {
  // Chromium also uses this process-wide proxy before any game page exists.
  // A rejection is a hard egress block, not proof of a game-origin request.
  // Page/WebSocket requests are attributed separately by the passive context.
  blocked.push({kind, url, method, elapsed_ms: Date.now()-began,
    provenance: 'browser_process_unattributed', forwarded: false, response: 'owned_proxy_denied'});
}
async function writeAll(handle, bytes) {
  let written = 0;
  while (written < bytes.length) {
    const value = await handle.write(bytes, written, bytes.length - written);
    if (!value.bytesWritten) throw Error('Capture file write made no progress');
    written += value.bytesWritten;
  }
}

try {
  if (!out.startsWith('/Volumes/RuiRui4TB/') || path.resolve(await fs.realpath(out)) !== out || !Number.isInteger(innerMilliseconds) || innerMilliseconds < 15000 || innerMilliseconds > 240000)
    throw Error('Owned 4T directory/deadline guard');
  if (config.memory_page_cap !== 32768 || config.memory_cap_bytes !== 2 * 1024 * 1024 * 1024 || config.browser_heap_mib !== 768 || config.capture_chunk_bytes !== 1024 * 1024)
    throw Error('Declared game-entry memory/capture domain differs');
  await fs.mkdir(temporary, {recursive: true});
  await fs.mkdir(path.join(out, 'browser-artifacts'), {recursive: true});
  process.env.TMPDIR = temporary;
  watchdog = setTimeout(() => {
    status = 'inner_deadline'; error ??= 'Owned game-entry execution deadline; cleanup reserve retained';
    void close().finally(() => process.exit(124));
  }, Math.max(1, executionDeadline - Date.now()));

  const packageRaw = await fs.readFile(path.join(config.playwright_path, 'package.json'));
  if (hash(packageRaw) !== config.playwright_package_sha256 || JSON.parse(packageRaw).version !== config.playwright_version ||
      await hashFile(config.chrome_path) !== config.chrome_sha256 || await hashFile(config.original_path) !== config.original_sha256 ||
      await hashFile(config.node_path) !== config.node_sha256 || await hashFile(config.python_path) !== config.python_sha256)
    throw Error('Frozen official/browser/runtime identity');
  const [module, glue, aux, font, index, script] = await Promise.all([
    config.module_path, config.glue_path, config.aux_path, config.font_path, config.name_index_path, config.observer_script_path,
  ].map(file => fs.readFile(file)));
  if (hash(module) !== config.module_sha256 || hash(glue) !== config.glue_sha256 ||
      hash(glue.subarray(0, config.glue_prefix_bytes)) !== config.official_glue_sha256 ||
      hash(aux) !== config.aux_sha256 || hash(font) !== config.font_sha256 || font.length !== config.font_bytes ||
      hash(index) !== config.name_index_sha256 || hash(script) !== config.observer_script_sha256)
    throw Error('Frozen original/module/route/observer identity');
  const {chromium} = createRequire(import.meta.url)(config.playwright_path);
  worker = spawn(config.python_path, [config.asset_worker_script, '--asset-worker', configPath], {
    stdio: ['pipe', 'pipe', 'pipe'], env: {...process.env, TMPDIR: temporary, PYTHONUNBUFFERED: '1', PYTHONDONTWRITEBYTECODE: '1'},
  });
  events.push({label: 'worker_started', pid: worker.pid, pgid: pgid(worker.pid)});
  let readyResolve, readyReject, workerStderr = '';
  const ready = new Promise((resolve, reject) => { readyResolve = resolve; readyReject = reject; });
  worker.stderr.on('data', bytes => { workerStderr = (workerStderr + bytes).slice(-65536); });
  createInterface({input: worker.stdout}).on('line', line => {
    try {
      const value = JSON.parse(line);
      if (value.worker_ready) { readyResolve(); return; }
      if (!pending) throw Error('Unexpected asset worker response');
      const row = pending; pending = null; row.resolve(value);
    } catch (exception) { readyReject(exception); pending?.reject(exception); pending = null; }
  });
  worker.on('error', exception => { readyReject(exception); pending?.reject(exception); pending = null; });
  worker.stdin.on('error', exception => { readyReject(exception); pending?.reject(exception); pending = null; });
  worker.on('exit', (code, signal) => {
    if (!shutdown) {
      const exception = Error(`Asset worker ${code}/${signal}: ${workerStderr}`);
      readyReject(exception); pending?.reject(exception); pending = null;
      events.push({label: 'unexpected_worker_exit', code, signal, error: String(exception)});
    }
  });
  await journal();
  await bounded(ready, 20000, 'Asset worker startup deadline');
  const html = '<!doctype html><meta charset="utf-8"><style>html,body{margin:0;overflow:hidden}canvas{width:100vw;height:100vh;outline:none}</style><canvas id="benilla" tabindex="0" width="960" height="540"></canvas>';
  const routes = new Map([
    ['/', ['text/html', Buffer.from(html)]], ['/original.wasm', ['application/wasm', module]],
    ['/bridge.mjs', ['text/javascript', glue]], ['/observe.mjs', ['text/javascript', script]],
    ['/data/__index', ['application/json', index]], ['/data/fonts/azs_sc.ttf', ['font/ttf', font]],
    ['/snippets/benilla-app-e11f90d5572a787b/inline0.js', ['text/javascript', aux]],
  ]);
  const policy = "default-src 'none';script-src 'self' 'wasm-unsafe-eval';style-src 'unsafe-inline';img-src 'self' data: blob:;connect-src 'self';worker-src 'none';base-uri 'none';form-action 'none';object-src 'none'";
  server = http.createServer(async (req, res) => {
    const row = {method: req.method, path: req.url}; requests.push(row);
    if(req.url.startsWith('/data/')){
      assetsInFlight++;lastAssetActivity=Date.now();let accounted=false;
      const complete=()=>{if(!accounted){accounted=true;assetsInFlight--;lastAssetActivity=Date.now();}};
      res.once('finish',complete);res.once('close',complete);
    }
    try {
      const url = new URL(req.url, origin); row.path = url.pathname;
      if (shutdown || !['127.0.0.1', '::ffff:127.0.0.1'].includes(req.socket.remoteAddress) || url.origin !== origin || req.headers.host !== new URL(origin).host || url.search)
        throw Error('Owned loopback HTTP request guard');
      req.setTimeout(30000, () => req.destroy(Error('Owned request body deadline')));
      if(req.method==='POST'&&url.pathname==='/capture/observation.json'){
        if(observationReceipt)throw Error('Pre-upload observation is write-once');
        const chunks=[];let length=0;
        for await(const chunk of req){length+=chunk.length;if(length>16*1024*1024)throw Error('Observation metadata byte budget');chunks.push(chunk);}
        const raw=Buffer.concat(chunks),value=JSON.parse(raw.toString('utf8'));
        if(value.original_sha256!==config.original_sha256||value.module_sha256!==config.module_sha256||value.kind!=='original_UI_Game_observation_saved_before_bulk_capture_not_independent_model')throw Error('Observation metadata identity');
        await fs.writeFile(path.join(out,'observation-before-upload.json'),raw,{flag:'wx'});
        observationReceipt={bytes:raw.length,sha256:hash(raw),persisted_before_bulk_memory_upload:true};
        row.status=200;row.bytes=raw.length;res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(observationReceipt));await journal();return;
      }
      if (req.method === 'POST' && url.pathname === '/capture/original_game.memory') {
        const offset = Number(req.headers['x-capture-offset']), total = Number(req.headers['x-capture-total']);
        if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(total) || offset < 0 || total < 1 || total > config.memory_cap_bytes)
          throw Error('Capture offset/total budget');
        if (!capture) {
          if (offset !== 0) throw Error('Capture first offset');
          capture = {bytes: 0, total, complete: false, busy: false, hash: createHash('sha256'), handle: await fs.open(path.join(out, 'original_game.memory'), 'wx')};
        }
        if (capture.busy || capture.complete || capture.total !== total || capture.bytes !== offset) throw Error('Capture sequential ownership/order');
        capture.busy = true;
        try {
          let received = 0;
          for await (const chunk of req) {
            received += chunk.length;
            if (received > config.capture_chunk_bytes || capture.bytes + chunk.length > total) throw Error('Capture chunk budget');
            await writeAll(capture.handle, chunk); capture.hash.update(chunk); capture.bytes += chunk.length;
          }
          if (!received || received !== Math.min(config.capture_chunk_bytes, total - offset)) throw Error('Capture chunk length');
          capture.complete = capture.bytes === total;
          if (capture.complete) { capture.sha256 = capture.hash.digest('hex'); await capture.handle.close(); capture.handle = null; }
          const value = {bytes: capture.bytes, complete: capture.complete, ...(capture.complete ? {sha256: capture.sha256} : {})};
          row.status = 200; row.bytes = received; res.writeHead(200, {'Content-Type': 'application/json', 'Cache-Control': 'no-store'}); res.end(JSON.stringify(value));
        } finally { capture.busy = false; }
        return;
      }
      if (req.method !== 'GET') { row.status = 403; res.writeHead(403); res.end(); return; }
      let route = routes.get(url.pathname);
      if (!route && url.pathname.startsWith('/data/')) {
        const requestPath = decodeURIComponent(url.pathname.slice(6));
        const queued = assetQueue.then(() => new Promise((resolve, reject) => {
          if (pending || shutdown || worker.exitCode !== null || worker.signalCode !== null) { reject(Error('Asset worker serialization/liveness')); return; }
          pending = {resolve, reject};
          worker.stdin.write(JSON.stringify({path: requestPath}) + '\n', exception => { if (exception) { pending?.reject(exception); pending = null; } });
        }));
        assetQueue = queued.catch(() => {});
        const value = await queued; row.asset = value;
        if (value.status !== 200) { row.status = value.status; res.writeHead(value.status); res.end(value.error || value.reason || 'Missing'); return; }
        if (!Number.isSafeInteger(value.bytes) || value.bytes < 0) throw Error('Actual asset byte length');
        if (!assets.has(requestPath)) {
          if (assets.size + 1 > config.asset_file_budget || assetBytes + value.bytes > config.asset_decoded_byte_budget) throw Error('Declared asset delivery budget');
          assets.set(requestPath, value.sha256); assetBytes += value.bytes;
        }
        const raw = await fs.readFile(value.file);
        if (hash(raw) !== value.sha256 || raw.length !== value.bytes) throw Error('Actual asset identity drift');
        route = ['application/octet-stream', raw];
      }
      if (!route) { row.status = 404; res.writeHead(404); res.end(); return; }
      row.status = 200; row.bytes = route[1].length;
      res.writeHead(200, {'Content-Type': route[0], 'Content-Length': route[1].length, 'Cache-Control': 'no-store', 'Content-Security-Policy': policy}); res.end(route[1]);
    } catch (exception) {
      row.status = 500; row.error = String(exception);
      if (!res.headersSent) res.writeHead(500); if (!res.destroyed) res.end(String(exception));
    }
  });
  server.headersTimeout = 10000; server.requestTimeout = 30000; server.keepAliveTimeout = 1000;
  server.on('connection', socket => { sockets.add(socket); socket.on('close', () => sockets.delete(socket)); });
  server.on('upgrade', (req, socket) => { blocked.push({kind: 'loopback_websocket_upgrade_closed', url: req.url}); socket.destroy(); });
  server.on('clientError', (exception, socket) => { events.push({label: 'loopback_client_error', error: String(exception)}); socket.destroy(); });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  origin = 'http://127.0.0.1:' + server.address().port;
  // This owned proxy never connects to a destination. Loopback resource/capture
  // traffic bypasses it and never passes through Playwright/CDP interception.
  deadProxy = http.createServer((req, res) => { proxyRejected('owned_proxy_rejected_http', req.url, req.method); res.writeHead(502); res.end(); });
  deadProxy.on('connection', socket => { proxySockets.add(socket); socket.on('close', () => proxySockets.delete(socket)); socket.on('error', () => {}); });
  deadProxy.on('connect', (req, socket) => { proxyRejected('owned_proxy_rejected_connect', req.url, req.method); socket.end('HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\nContent-Length: 0\r\n\r\n'); });
  deadProxy.on('upgrade', (req, socket) => { proxyRejected('owned_proxy_rejected_upgrade', req.url, req.method); socket.destroy(); });
  deadProxy.headersTimeout = 5000; deadProxy.requestTimeout = 5000;
  await new Promise((resolve, reject) => { deadProxy.once('error', reject); deadProxy.listen(0, '127.0.0.1', resolve); });
  bs = await chromium.launchServer({
    headless: true, executablePath: config.chrome_path, downloadsPath: path.join(out, 'browser-artifacts'),
    env: {...process.env, TMPDIR: temporary, TMP: temporary, TEMP: temporary},
    proxy: {server: 'http://127.0.0.1:' + deadProxy.address().port, bypass: '127.0.0.1,localhost,[::1]'},
    args: [...config.browser_extra_args,
      '--js-flags=--wasm-max-mem-pages=' + config.memory_page_cap + ' --max-old-space-size=' + config.browser_heap_mib,
      '--disable-background-networking', '--disable-component-update', '--disable-sync', '--no-first-run', '--disable-default-apps', '--metrics-recording-only', '--disable-domain-reliability',
      '--disable-quic', '--force-webrtc-ip-handling-policy=disable_non_proxied_udp',
      '--host-resolver-rules=EXCLUDE 127.0.0.1, EXCLUDE localhost, EXCLUDE [::1], MAP * ~NOTFOUND'],
    timeout: 20000,
  });
  events.push({label: 'browser_started', pid: bs.process().pid, pgid: pgid(bs.process().pid), spawnargs: bs.process().spawnargs, proxy: 'owned_nonforwarding_loopback', origin});
  await journal();
  browser = await chromium.connect(bs.wsEndpoint());
  context = await browser.newContext({viewport: {width: 960, height: 540}, acceptDownloads: false, serviceWorkers: 'block'});
  context.on('request', req => {
    let url; try { url = new URL(req.url()); } catch { return; }
    if (['http:', 'https:', 'ws:', 'wss:'].includes(url.protocol) && url.origin !== origin) {
      passiveRequests.push({method: req.method(), url: req.url(), elapsed_ms: Date.now() - began});
      external('non_loopback_browser_request', req.url(), req.method());
    }
  });
  context.on('page', value => {
    if (page && value !== page) { blocked.push({kind: 'popup_closed', url: value.url()}); void value.close().catch(() => {}); }
  });
  await context.addInitScript(() => {
    globalThis.__gameEntry135TrustedInputEvents = [];
    for (const type of ['pointerdown', 'pointerup', 'click', 'keydown', 'keyup']) addEventListener(type, event => {
      if (globalThis.__gameEntry135TrustedInputEvents.length < 100) globalThis.__gameEntry135TrustedInputEvents.push({
        type, isTrusted: event.isTrusted, key: event.key ?? null, code: event.code ?? null,
        x: event.clientX ?? null, y: event.clientY ?? null, button: event.button ?? null, time: performance.now(),
      });
    }, {capture: true});
  });
  page = await context.newPage();
  page.on('pageerror', exception => errors.push(String(exception.stack || exception)));
  page.on('console', row => { if (logs.length < 1000) logs.push({type: row.type(), text: row.text()}); });
  page.on('download', download => { blocked.push({kind: 'download_cancelled'}); void download.cancel().catch(() => {}); });
  page.on('websocket', socket => { if (new URL(socket.url()).origin !== origin) external('non_loopback_browser_websocket', socket.url()); });
  page.setDefaultTimeout(10000);
  await page.goto(origin, {waitUntil: 'domcontentloaded', timeout: 15000});
  status = 'running'; await journal();
  await page.evaluate(c => {
    globalThis.__gameEntry135TaskOutcome = {done: false};
    globalThis.__gameEntry135Task = import('/observe.mjs').then(module => module.observeGameEntry135(c));
    globalThis.__gameEntry135Task.then(
      () => { globalThis.__gameEntry135TaskOutcome = {done: true, ok: true}; },
      exception => { globalThis.__gameEntry135TaskOutcome = {done: true, ok: false, error: String(exception.stack || exception)}; },
    );
  }, config);
  const readyState = await waitControl(value => value?.ready === true, 60000, 'before_trusted_start_click');
  if (readyState.control?.ready && !readyState.control.finished && !readyState.task?.done && !readyState.control.error && !networkBoundary) {
    if (!await screenshot('menu-ready.png')) throw Error('Menu screenshot boundary before trusted click');
    inputs.push({action: 'mouse_click', x: 475, y: 490, elapsed_ms: Date.now() - began, before: readyState.control, injection: 'Playwright mouse protocol; no WASM write or command injection'});
    await page.mouse.click(475, 490);
    const entered = await waitControl(value => value?.game_present === true, 45000, 'after_trusted_start_click');
    await screenshot('after-enter.png');
    if (entered.control?.game_present && !entered.control.running && !entered.control.finished && !entered.task?.done && !entered.control.error && !networkBoundary) {
      // Game installation precedes scene loading. Do not send movement while
      // the real client is still consuming map textures/models, or press Enter
      // without evidence that it is a start binding rather than chat focus.
      const installedAt=Date.now(),settleUntil=Math.min(installedAt+60000,executionDeadline-45000);
      events.push({label:'waiting_for_scene_asset_quiet',elapsed_ms:Date.now()-began});await journal();
      while(Date.now()<settleUntil&&!shutdown&&(Date.now()-installedAt<10000||assetsInFlight!==0||Date.now()-lastAssetActivity<3000))await pause(100);
      const quiet=assetsInFlight===0&&Date.now()-lastAssetActivity>=3000;
      events.push({label:'scene_asset_quiet_observation',quiet,assets_in_flight:assetsInFlight,quiet_ms:Date.now()-lastAssetActivity,elapsed_ms:Date.now()-began});await journal();
      if(!quiet)throw Error('Scene assets did not settle within declared entry budget');
      if(requests.some(row=>row.path.startsWith('/data/')&&row.status!==200))throw Error('Actual scene asset failure preserved before movement');
      if(errors.length)throw Error('Original renderer error preserved before movement');
      await screenshot('scene-before-movement.png');
      inputs.push({action:'mouse_click',x:480,y:270,elapsed_ms:Date.now()-began,purpose:'Focus real canvas after scene asset quiet'});
      await page.mouse.click(480,270);
      inputs.push({action: 'keyboard_hold', key: 'w', requested_duration_ms: 1500, elapsed_ms: Date.now() - began});
      await page.keyboard.down('w');
      try { await pause(1500); } finally { if (!page.isClosed()) await page.keyboard.up('w'); }
      const moved = await control(); recordControl('after_scene_quiet_and_trusted_W', moved);await journal();
      await screenshot('after-move.png');
      if (!moved.control?.running && !moved.control?.finished && !moved.task?.done) await requestStop('trusted_input_completed_without_running');
    } else if (!entered.control?.game_present && !entered.control?.finished && !entered.task?.done) {
      await requestStop('trusted_start_click_without_Game');
    }
  } else if (!readyState.control?.finished && !readyState.task?.done) {
    await requestStop(networkBoundary ? 'non_loopback_network_boundary' : 'menu_readiness_boundary');
  }
  const remaining = executionDeadline - Date.now();
  if (remaining <= 0) throw Error('No task/capture time left inside execution budget');
  result = await bounded(page.evaluate(async () => await globalThis.__gameEntry135Task), remaining, 'Original task/capture completion deadline');
  if (!result || typeof result.status !== 'string') throw Error('Original observation task returned no structured result');
  status = result.status;
  recordControl('task_completed', await control());
  trustedInputEvents.push(...await page.evaluate(() => globalThis.__gameEntry135TrustedInputEvents ?? []));
  await screenshot('original-game.png');
  const rendererErrors = errors.length > 0 || logs.some(row => row.type === 'error' && /panicked|createBuffer failed|device lost/i.test(row.text));
  result.renderer_observation_status = rendererErrors ? 'renderer_boundary_preserved' : 'no_renderer_error_reported_not_visual_acceptance';
  result.network_observation_status = networkBoundary ? 'non_loopback_attempt_preserved_boundary' : 'no_non_loopback_request_observed_CSP_attempts_separate';
  if (networkBoundary) status = 'network_boundary_preserved';
  else if (rendererErrors && status === 'observed_natural_Game_running_complete880_returns') status = 'observed_Game_running_with_renderer_boundary';
  if (capture && !capture.complete) throw Error('Original task ended with incomplete memory capture');
} catch (exception) {
  status = 'failed_preserved'; error = String(exception.stack || exception); process.exitCode = 1;
  if (page && !page.isClosed() && !shutdown) {
    await requestStop('owned_runner_boundary').catch(() => {});
    try { trustedInputEvents.push(...await bounded(page.evaluate(() => globalThis.__gameEntry135TrustedInputEvents ?? []), 1000, 'Input evidence read deadline')); } catch {}
    await screenshot(screenshotCount ? 'original-game.png' : 'entry-boundary.png');
  }
} finally { await close(); }
process.stdout.write(JSON.stringify({directory: out, status, error, contexts: result?.contexts?.length, frames: result?.frames?.length,
  running_returns: result?.running_complete880_returns, memory_bytes: result?.memory_bytes, input_actions: inputs.length, network_boundary: networkBoundary}) + '\n');
