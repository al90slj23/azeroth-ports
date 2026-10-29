'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const crypto = require('node:crypto');
const { once } = require('node:events');
const { attachCoopProxy } = require('./coop-proxy');

const ORIGIN = 'http://127.0.0.1:47615';
const KEY = 'dGhlIHNhbXBsZSBub25jZQ==';
const ACCEPT = crypto.createHash('sha1').update(KEY + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');

async function fixture(t, { onUpgrade, onRequest, timeout = 1000 } = {}) {
  const upstream = http.createServer(onRequest || ((req, res) => { res.writeHead(200); res.end('lobbies'); }));
  const upstreamSockets = new Set();
  upstream.on('connection', (socket) => { upstreamSockets.add(socket); socket.once('close', () => upstreamSockets.delete(socket)); });
  if (onUpgrade) upstream.on('upgrade', onUpgrade);
  upstream.listen(0, '127.0.0.1');
  await once(upstream, 'listening');
  let relay;
  const local = http.createServer((req, res) => {
    if (relay.handleRequest(req, res)) return;
    res.writeHead(404); res.end();
  });
  const forwarded = [];
  relay = attachCoopProxy(local, {
    localOrigin: ORIGIN, handshakeTimeoutMs: timeout,
    request(options, cb) {
      forwarded.push(options);
      return http.request({ ...options, protocol: 'http:', hostname: '127.0.0.1', port: upstream.address().port }, cb);
    },
  });
  local.listen(0, '127.0.0.1');
  await once(local, 'listening');
  t.after(async () => {
    relay.close();
    for (const socket of upstreamSockets) socket.destroy();
    await Promise.all([new Promise((r) => local.close(r)), new Promise((r) => upstream.close(r))]);
  });
  return { local, relay, forwarded, port: local.address().port };
}

function request(port, target, { method = 'GET', headers = {} } = {}) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port, path: target, method, headers }, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks).toString() }));
    });
    req.on('error', reject); req.end();
  });
}

function upgrade(port, target, origin = ORIGIN) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port, path: target, headers: {
      connection: 'Upgrade', upgrade: 'websocket', 'sec-websocket-version': '13',
      'sec-websocket-key': KEY, origin,
    } });
    req.on('upgrade', (response, socket, head) => resolve({ response, socket, head }));
    req.on('response', (response) => { response.resume(); resolve({ response }); });
    req.on('error', reject); req.end();
  });
}

test('relays the WebSocket handshake and both directions including bytes after the headers', async (t) => {
  const f = await fixture(t, { onUpgrade(req, socket, head) {
    assert.equal(req.url, '/coop/lobby/ABC123?version=0.120.5');
    assert.equal(req.headers.host, 'wow.aethus.pl');
    assert.equal(req.headers.origin, ORIGIN);
    socket.write(`HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: ${ACCEPT}\r\n\r\nearly`);
    if (head.length) socket.write(head);
    socket.on('data', (data) => socket.write(data));
  } });
  const result = await upgrade(f.port, '/coop/lobby/ABC123?version=0.120.5');
  assert.equal(result.response.statusCode, 101);
  assert.equal(result.response.headers['sec-websocket-accept'], ACCEPT);
  const chunks = [result.head];
  result.socket.on('data', (data) => chunks.push(data));
  result.socket.write(Buffer.from([0x82, 0x02, 0xaa, 0xbb]));
  const deadline = Date.now() + 1000;
  while (Buffer.concat(chunks).length < 9 && Date.now() < deadline) await new Promise((r) => setTimeout(r, 5));
  assert.deepEqual(Buffer.concat(chunks), Buffer.concat([Buffer.from('early'), Buffer.from([0x82, 0x02, 0xaa, 0xbb])]));
  const closed = once(result.socket, 'close');
  f.relay.close();
  await closed;
});

test('co-op HTTP requests use the fixed upstream without forwarding local credentials', async (t) => {
  const f = await fixture(t, { onRequest(req, res) {
    assert.equal(req.url, '/coop/lobby/?version=1');
    assert.equal(req.headers.host, 'wow.aethus.pl');
    assert.equal(req.headers.cookie, undefined);
    assert.equal(req.headers.authorization, undefined);
    res.writeHead(200, { 'Content-Type': 'application/json', 'Set-Cookie': 'ignore=me' });
    res.end('{"lobbies":[]}');
  } });
  assert.deepEqual(await request(f.port, '/coop/lobby/?version=1', { headers: {
    origin: ORIGIN, cookie: 'private=secret', authorization: 'Bearer secret',
  } }), { status: 200, body: '{"lobbies":[]}' });
  assert.equal(f.forwarded[0].hostname, 'wow.aethus.pl');
  assert.equal(f.forwarded[0].protocol, 'https:');
});

test('rejects unrelated paths, traversal and foreign browser origins without an upstream request', async (t) => {
  const f = await fixture(t);
  for (const target of ['/presence', '/coopish', '/coop/../secret', '/coop/%2e%2e/secret', '/coop/%2fsecret', '//evil.test/coop']) {
    assert.equal((await request(f.port, target)).status, 404, target);
    assert.equal((await upgrade(f.port, target)).response.statusCode, 404, target);
  }
  assert.equal((await upgrade(f.port, '/coop/lobby/', 'https://unrelated.example')).response.statusCode, 403);
  assert.equal((await request(f.port, '/coop', { headers: { origin: 'https://unrelated.example' } })).status, 403);
  assert.equal((await request(f.port, '/coop', { method: 'POST' })).status, 405);
  assert.equal(f.forwarded.length, 0);
});

test('upstream rejection and stalled upgrade produce bounded failures', async (t) => {
  const rejected = await fixture(t, { onUpgrade(req, socket) {
    socket.end('HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n');
  } });
  assert.equal((await upgrade(rejected.port, '/coop')).response.statusCode, 403);
  const stalled = await fixture(t, { timeout: 40, onUpgrade() {} });
  assert.equal((await upgrade(stalled.port, '/coop/lobby/')).response.statusCode, 504);
});
