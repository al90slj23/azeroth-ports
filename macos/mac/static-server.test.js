'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const { once } = require('node:events');
const { createStaticServer } = require('./static-server');

function request(port, requestPath, method = 'GET') {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port, path: requestPath, method }, (res) => {
      const chunks = [];
      res.on('data', (chunk) => chunks.push(chunk));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) }));
      res.on('error', reject);
    });
    req.on('error', reject);
    req.end();
  });
}

test('bundled game files serve without exposing files outside the resource directory', async (t) => {
  const temporary = await fs.mkdtemp(path.join(os.tmpdir(), 'azeroth-static-test-'));
  const root = path.join(temporary, 'www');
  await fs.mkdir(path.join(root, 'data'), { recursive: true });
  await fs.writeFile(path.join(root, 'index.html'), '<h1>Game</h1>');
  await fs.writeFile(path.join(root, 'client.wasm'), Buffer.from([0, 97, 115, 109]));
  await fs.writeFile(path.join(root, 'data', 'map'), 'terrain');
  await fs.writeFile(path.join(root, 'data', '__index'), 'manifest');
  await fs.writeFile(path.join(temporary, 'secret'), 'outside');
  await fs.symlink(path.join(temporary, 'secret'), path.join(root, 'outside-link'));

  const server = createStaticServer({ root });
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    await fs.rm(temporary, { recursive: true, force: true });
  });
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = server.address().port;

  await t.test('serves entry page, query-versioned WASM and HEAD metadata', async () => {
    const entry = await request(port, '/?v=e0e2410c');
    assert.equal(entry.status, 200);
    assert.equal(entry.body.toString(), '<h1>Game</h1>');
    assert.match(entry.headers['content-type'], /^text\/html/);
    const wasm = await request(port, '/client.wasm?v=e0e2410c');
    assert.equal(wasm.status, 200);
    assert.equal(wasm.headers['content-type'], 'application/wasm');
    assert.deepEqual(wasm.body, Buffer.from([0, 97, 115, 109]));
    const head = await request(port, '/client.wasm?v=e0e2410c', 'HEAD');
    assert.equal(head.status, 200);
    assert.equal(head.headers['content-length'], '4');
    assert.equal(head.body.length, 0);
  });

  await t.test('retains game asset cache rules', async () => {
    const data = await request(port, '/data/map');
    assert.equal(data.headers['cache-control'], 'max-age=31536000, immutable');
    const index = await request(port, '/data/__index');
    assert.equal(index.headers['cache-control'], 'no-cache');
  });

  await t.test('rejects malformed encodings and NUL paths and stays available', async () => {
    assert.equal((await request(port, '/%')).status, 400);
    assert.equal((await request(port, '/%00')).status, 400);
    assert.equal((await request(port, '/')).status, 200);
  });

  await t.test('rejects encoded traversal, external symlinks and directory reads', async () => {
    for (const unsafe of ['/%2e%2e%2fsecret', '/data/..%2f..%2fsecret', '/outside-link', '/data/', '/missing']) {
      assert.equal((await request(port, unsafe)).status, 404, unsafe);
    }
  });

  await t.test('rejects unsupported methods', async () => {
    const result = await request(port, '/', 'POST');
    assert.equal(result.status, 405);
    assert.equal(result.headers.allow, 'GET, HEAD');
    assert.equal(result.body.length, 0);
  });
});
