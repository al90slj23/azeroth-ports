'use strict';

// Adapted from https://github.com/myslithell/azeroth-survivors/blob/
// a65664af64f4377159463cd128424eeb6f132102/mac/main.js (local wrapper only).
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.wasm': 'application/wasm',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.svg': 'image/svg+xml',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
};

function isInside(root, candidate) {
  return candidate.startsWith(root + path.sep);
}

function finish(res, status, headers = {}) {
  if (res.destroyed || res.writableEnded) return;
  res.writeHead(status, { 'Content-Length': '0', ...headers });
  res.end();
}

function createStaticServer({ root, requestHandler }) {
  const directory = fs.realpathSync(root);
  if (!fs.statSync(directory).isDirectory()) {
    throw new Error('The game resource path must be a directory.');
  }

  async function handle(req, res) {
    if (requestHandler && requestHandler(req, res)) return;
    if (req.method !== 'GET' && req.method !== 'HEAD') {
      finish(res, 405, { Allow: 'GET, HEAD' });
      return;
    }

    let name;
    try {
      // An origin-form request keeps a request URL from selecting a different host.
      if (!req.url || !req.url.startsWith('/')) throw new Error('Invalid URL');
      const parsed = new URL(req.url, 'http://127.0.0.1');
      if (parsed.origin !== 'http://127.0.0.1') throw new Error('Invalid origin');
      name = decodeURIComponent(parsed.pathname);
      if (name.includes('\0')) throw new Error('Invalid path');
    } catch {
      finish(res, 400);
      return;
    }
    if (name === '/') name = '/index.html';

    const candidate = path.resolve(directory, '.' + name);
    if (!isInside(directory, candidate)) {
      finish(res, 404);
      return;
    }

    let file;
    let stat;
    try {
      // Confine symbolic links as well as lexical '..' segments to the bundled files.
      file = await fs.promises.realpath(candidate);
      if (!isInside(directory, file)) {
        finish(res, 404);
        return;
      }
      stat = await fs.promises.stat(file);
      if (!stat.isFile()) {
        finish(res, 404);
        return;
      }
    } catch (error) {
      finish(res, ['ENOENT', 'ENOTDIR', 'EACCES', 'ELOOP'].includes(error.code) ? 404 : 500);
      return;
    }

    const headers = {
      'Content-Type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream',
      'Content-Length': String(stat.size),
      'X-Content-Type-Options': 'nosniff',
      'Cache-Control': name.startsWith('/data/') && name !== '/data/__index'
        ? 'max-age=31536000, immutable' : 'no-cache',
    };
    if (req.method === 'HEAD') {
      res.writeHead(200, headers);
      res.end();
      return;
    }

    const stream = fs.createReadStream(file);
    stream.once('error', (error) => {
      if (res.headersSent) res.destroy(error);
      else finish(res, 500);
    });
    res.once('close', () => stream.destroy());
    stream.once('open', () => {
      if (res.destroyed) {
        stream.destroy();
        return;
      }
      res.writeHead(200, headers);
      stream.pipe(res);
    });
  }

  return http.createServer((req, res) => {
    handle(req, res).catch(() => {
      if (res.headersSent) res.destroy();
      else finish(res, 500);
    });
  });
}

module.exports = { createStaticServer };
