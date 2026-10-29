'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync(new URL('../web/android-bridge.js', `file://${__filename}`), 'utf8');
function environment(href = 'http://127.0.0.1:47615/') {
  const constructed = [];
  const listeners = {};
  class NativeSocket {
    static OPEN = 1;
    constructor(...args) { constructed.push(args); }
  }
  const location = new URL(href);
  const window = {WebSocket: NativeSocket};
  window.top = window;
  const context = {window, location, URL, document: {
    addEventListener: (name, callback) => listeners[name] = callback,
  }, console};
  vm.runInNewContext(source, context);
  return {window, context, constructed, listeners, NativeSocket};
}

test('the original lobby route reaches the fixed official TLS endpoint', () => {
  const e = environment();
  const socket = new e.window.WebSocket('ws://127.0.0.1:47615/coop/lobby/?version=0.126.0');
  assert.deepEqual(e.constructed[0], ['wss://wow.aethus.pl/coop/lobby/?version=0.126.0']);
  assert.equal(socket instanceof e.NativeSocket, true);
  assert.equal(e.window.WebSocket.OPEN, 1);
});

test('game relays, other ports and other routes retain their original destinations and protocols', () => {
  const e = environment();
  new e.window.WebSocket('wss://coop.aethus.pl:2053/coop/relay2/', ['game']);
  new e.window.WebSocket('ws://127.0.0.1:12345/coop/lobby/');
  new e.window.WebSocket('ws://127.0.0.1:47615/unrelated');
  assert.deepEqual(e.constructed, [
    ['wss://coop.aethus.pl:2053/coop/relay2/', ['game']],
    ['ws://127.0.0.1:12345/coop/lobby/'],
    ['ws://127.0.0.1:47615/unrelated'],
  ]);
});

test('adapter does not modify a nonlocal website', () => {
  const e = environment('https://wow.aethus.pl/');
  assert.equal(e.window.WebSocket, e.NativeSocket);
  assert.equal(e.listeners.click, undefined);
});

test('save export only intercepts same-origin .sav blobs when the Android bridge exists', async () => {
  const e = environment();
  const exports = [];
  let prevented = false;
  e.window.AndroidHost = {exportSave: (...args) => exports.push(args)};
  e.context.fetch = async () => ({blob: async () => ({size: 10})});
  e.context.FileReader = class {
    readAsDataURL() { this.result = 'data:application/octet-stream;base64,UlNFMTo='; this.onload(); }
  };
  const eventFor = (href, download) => ({preventDefault: () => prevented = true,
    target: {closest: () => ({href, download})}});
  await e.listeners.click(eventFor('blob:https://unrelated.example/1', 'save.sav'));
  assert.equal(prevented, false);
  await e.listeners.click(eventFor('blob:http://127.0.0.1:47615/1', 'addon.zip'));
  assert.equal(prevented, false);
  await e.listeners.click(eventFor('blob:http://127.0.0.1:47615/1', 'save.sav'));
  assert.equal(prevented, true);
  assert.deepEqual(exports, [['save.sav', 'UlNFMTo=']]);
});
