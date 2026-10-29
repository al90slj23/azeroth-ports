'use strict';

// The unmodified web client derives /coop URLs from location.host. Keep game assets
// and saves on their existing loopback origin, but relay only co-op traffic to Aethus.
const https = require('node:https');

const UPSTREAM = new URL('https://wow.aethus.pl');
const LOCAL_ORIGIN = 'http://127.0.0.1:47615';
const HTTP_HEADERS = ['accept', 'accept-language', 'user-agent'];
const WS_HEADERS = [
  ...HTTP_HEADERS, 'sec-websocket-key', 'sec-websocket-version',
  'sec-websocket-protocol', 'sec-websocket-extensions',
];
const RESPONSE_HEADERS = ['content-type', 'content-length', 'cache-control', 'expires', 'pragma'];
const UPGRADE_HEADERS = ['sec-websocket-accept', 'sec-websocket-protocol', 'sec-websocket-extensions'];

function coopPath(target) {
  if (typeof target !== 'string' || target.length > 4096 || /[\x00-\x20\x7f#]/.test(target)) return null;
  const rawPath = target.split('?')[0];
  // Do not let URL normalization, encoded separators or a request target choose a host/path.
  if (!/^\/coop(?:\/[A-Za-z0-9_.-]+)*\/?$/.test(rawPath)
      || rawPath.split('/').some((part) => part === '.' || part === '..')) return null;
  return target;
}

function pick(headers, names) {
  const result = {};
  for (const name of names) {
    if (headers[name] !== undefined) result[name] = headers[name];
  }
  return result;
}

function rejectSocket(socket, status) {
  if (socket.destroyed) return;
  const reason = { 400: 'Bad Request', 403: 'Forbidden', 404: 'Not Found', 405: 'Method Not Allowed',
    502: 'Bad Gateway', 503: 'Service Unavailable', 504: 'Gateway Timeout' }[status] || 'Upstream Error';
  socket.end(`HTTP/1.1 ${status} ${reason}\r\nConnection: close\r\nContent-Length: 0\r\n\r\n`);
}

function rejectResponse(res, status) {
  if (res.destroyed || res.writableEnded) return;
  if (res.headersSent) return res.destroy();
  res.writeHead(status, { 'Content-Length': '0', 'Cache-Control': 'no-store' });
  res.end();
}

/**
 * Attach WebSocket upgrades; pass handleRequest to the static server before file handling.
 * `request` is an injectable transport for local tests. Runtime destinations are fixed here.
 */
function attachCoopProxy(server, {
  localOrigin = LOCAL_ORIGIN,
  request = https.request,
  handshakeTimeoutMs = 15000,
} = {}) {
  if (new URL(localOrigin).origin !== localOrigin) throw new Error('Expected a local origin without a path.');
  const pending = new Set();
  const sockets = new Set();
  let closed = false;

  function allowedOrigin(req) {
    // Browser requests must belong to this app, not another page probing loopback.
    return req.headers.origin === undefined || req.headers.origin === localOrigin;
  }

  function upstreamOptions(req, target, upgrade) {
    const headers = pick(req.headers, upgrade ? WS_HEADERS : HTTP_HEADERS);
    headers.host = UPSTREAM.host;
    if (req.headers.origin !== undefined) headers.origin = req.headers.origin;
    if (upgrade) {
      headers.connection = 'Upgrade';
      headers.upgrade = 'websocket';
    }
    return {
      protocol: UPSTREAM.protocol, hostname: UPSTREAM.hostname, port: 443,
      method: req.method, path: target, headers,
    };
  }

  function trackRequest(upstream) {
    pending.add(upstream);
    upstream.once('close', () => pending.delete(upstream));
    return upstream;
  }

  function trackSocket(socket) {
    sockets.add(socket);
    socket.once('close', () => sockets.delete(socket));
  }

  function handleRequest(req, res) {
    const target = coopPath(req.url);
    if (!target) return false;
    if (closed) { rejectResponse(res, 503); return true; }
    if (!allowedOrigin(req)) { rejectResponse(res, 403); return true; }
    if (req.method !== 'GET' && req.method !== 'HEAD') { rejectResponse(res, 405); return true; }
    let upstream;
    try {
      upstream = trackRequest(request(upstreamOptions(req, target, false), (response) => {
        upstream.setTimeout(0);
        res.writeHead(response.statusCode, pick(response.headers, RESPONSE_HEADERS));
        response.once('error', () => res.destroy());
        response.pipe(res);
      }));
      upstream.setTimeout(handshakeTimeoutMs, () => {
        rejectResponse(res, 504);
        upstream.destroy();
      });
      upstream.once('error', () => rejectResponse(res, 502));
      res.once('close', () => upstream.destroy());
      upstream.end();
    } catch {
      upstream?.destroy();
      rejectResponse(res, 502);
    }
    return true;
  }

  function handleUpgrade(req, socket, head) {
    if (closed) { rejectSocket(socket, 503); return; }
    const target = coopPath(req.url);
    if (!target) { rejectSocket(socket, 404); return; }
    if (!allowedOrigin(req)) { rejectSocket(socket, 403); return; }
    if (req.method !== 'GET' || req.headers.upgrade?.toLowerCase() !== 'websocket'
        || req.headers['sec-websocket-version'] !== '13'
        || !/^[A-Za-z0-9+/]{22}==$/.test(req.headers['sec-websocket-key'] || '')) {
      rejectSocket(socket, 400);
      return;
    }
    let upstream;
    let remote;
    let connected = false;
    socket.once('error', () => { upstream?.destroy(); remote?.destroy(); });
    socket.once('close', () => { upstream?.destroy(); remote?.destroy(); });
    try {
      upstream = trackRequest(request(upstreamOptions(req, target, true)));
      upstream.setTimeout(handshakeTimeoutMs, () => {
        rejectSocket(socket, 504);
        upstream.destroy();
      });
      upstream.once('error', () => {
        if (connected) socket.destroy();
        else rejectSocket(socket, 502);
      });
      upstream.once('response', (response) => {
        response.resume();
        rejectSocket(socket, response.statusCode >= 400 && response.statusCode <= 599 ? response.statusCode : 502);
      });
      upstream.once('upgrade', (response, upstreamSocket, upstreamHead) => {
        remote = upstreamSocket;
        upstream.setTimeout(0);
        remote.setTimeout(0);
        if (socket.destroyed || closed) { remote.destroy(); return; }
        connected = true;
        const headers = pick(response.headers, UPGRADE_HEADERS);
        const lines = ['HTTP/1.1 101 Switching Protocols', 'Connection: Upgrade', 'Upgrade: websocket'];
        for (const [name, value] of Object.entries(headers)) lines.push(`${name}: ${value}`);
        socket.write(lines.join('\r\n') + '\r\n\r\n');
        if (upstreamHead.length) socket.write(upstreamHead);
        if (head.length) remote.write(head);
        trackSocket(socket);
        trackSocket(remote);
        remote.once('error', () => socket.destroy());
        remote.once('close', () => socket.destroy());
        socket.pipe(remote).pipe(socket);
      });
      upstream.end();
    } catch {
      upstream?.destroy();
      rejectSocket(socket, 502);
    }
  }

  function close() {
    if (closed) return;
    closed = true;
    server.removeListener('upgrade', handleUpgrade);
    for (const req of pending) req.destroy();
    for (const socket of sockets) socket.destroy();
    pending.clear();
    sockets.clear();
  }

  server.on('upgrade', handleUpgrade);
  server.once('close', close);
  return { handleRequest, close };
}

module.exports = { attachCoopProxy };
