'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function setup(language = 'zh-CN', initial = {}) {
  const calls = [];
  const listeners = {};
  class Store {
    constructor() { this.data = new Map(Object.entries(initial)); }
    getItem(k) { return this.data.has(k) ? this.data.get(k) : null; }
    setItem(k, v) { this.data.set(String(k), String(v)); }
    removeItem(k) { this.data.delete(String(k)); }
  }
  class Xhr {
    open(...args) { calls.push(['xhr', this, args]); return 'original-open'; }
  }
  class CustomEvent { constructor(type, props) { Object.assign(this, props, { type }); } }
  const localStorage = new Store();
  const window = {
    localStorage,
    fetch: (...args) => { calls.push(['fetch', args]); return 'original-fetch'; },
    addEventListener: (type, fn) => (listeners[type] ||= []).push(fn),
    dispatchEvent: event => { calls.push(['event', event]); },
  };
  const context = { window, navigator: { language }, location: {
    hostname: '127.0.0.1', origin: 'http://127.0.0.1:47615', href: 'http://127.0.0.1:47615/' },
    Storage: Store, XMLHttpRequest: Xhr, Request, URL, CustomEvent,
  };
  vm.runInNewContext(fs.readFileSync(require.resolve('../web/android-localization.js'), 'utf8'), context);
  return { api: window.AzerothAndroidLocalization, window, calls, Xhr, localStorage, listeners };
}

test('Simplified Chinese resources use three narrow alternate paths in fetch and sync XHR', () => {
  const h = setup();
  const path = '/data/interface/framexml/globalstrings.lua?v=0234f7949c75';
  const expected = 'http://127.0.0.1:47615/android-zh-CN' + path;
  const options = { headers: { 'X-Test': 'preserved' }, credentials: 'same-origin', cache: 'no-cache' };
  assert.equal(h.window.fetch(path, options), 'original-fetch');
  assert.equal(h.calls[0][1][0], expected); assert.equal(h.calls[0][1][1], options);
  const xhr = new h.Xhr();
  assert.equal(xhr.open('GET', path, false, 'user', 'pass'), 'original-open');
  assert.equal(h.calls[1][1], xhr);
  assert.deepEqual(Array.from(h.calls[1][2]), ['GET', expected, false, 'user', 'pass']);
  assert.ok(h.api.rewriteResourceUrl('/data/dbfilesclient/areatable.dbc').includes('/android-zh-CN/data/'));
  assert.ok(h.api.rewriteResourceUrl('/data/dbfilesclient/map.dbc').includes('/android-zh-CN/data/'));
});

for (const locale of ['en', 'en-US', 'zh-TW', 'zh-Hant', 'ja-JP']) {
  test(`browser preference ${locale} keeps original resources`, () => {
    const h = setup(locale);
    const path = '/data/dbfilesclient/map.dbc';
    assert.equal(h.api.rewriteResourceUrl(path), path);
  });
}

test('exact explicit game language wins over navigator, without changing the stored value', () => {
  const h = setup('zh-CN', { 'rogue.language': 'en\n', 'rogue.characters': 'sealed-save' });
  const path = '/data/dbfilesclient/map.dbc';
  assert.equal(h.api.rewriteResourceUrl(path), path);
  h.localStorage.setItem('rogue.language', '"zh"');
  assert.ok(h.api.rewriteResourceUrl(path).includes('/android-zh-CN/'));
  assert.equal(h.localStorage.getItem('rogue.language'), '"zh"');
  assert.equal(h.localStorage.getItem('rogue.characters'), 'sealed-save');
  const notice = h.calls.find(c => c[0] === 'event')[1];
  assert.equal(notice.type, 'az-language-resource-change');
  assert.equal(notice.detail.requiresRestart, true);
});

test('other resource paths, external hosts and modifying HTTP methods remain untouched', () => {
  const h = setup();
  for (const path of ['/wenilla_bg.wasm', '/data/dbfilesclient/spell.dbc', '/data/interface/framexml/chatframe.lua',
    'https://wow.aethus.pl/data/dbfilesclient/map.dbc', 'http://127.0.0.1:9999/data/dbfilesclient/map.dbc']) {
    assert.equal(h.api.rewriteResourceUrl(path), path);
  }
  const body = new Uint8Array([4,5,6]);
  const options = { method: 'POST', body, headers: { 'Content-Type': 'application/octet-stream' } };
  h.window.fetch('/data/dbfilesclient/map.dbc', options);
  assert.equal(h.calls[0][1][0], '/data/dbfilesclient/map.dbc');
  assert.equal(h.calls[0][1][1], options); assert.equal(options.body, body);
  const xhr = new h.Xhr(); xhr.open('POST', '/data/dbfilesclient/map.dbc', false);
  assert.equal(h.calls[1][2][1], '/data/dbfilesclient/map.dbc');
});

test('Request fetch inputs preserve headers, method, credentials, cache and caller options', () => {
  const h = setup();
  const req = new Request('http://127.0.0.1:47615/data/dbfilesclient/map.dbc', {
    method: 'HEAD', headers: { 'X-Resource-Test': 'kept' }, credentials: 'include', cache: 'no-store',
  });
  const options = { redirect: 'error' };
  h.window.fetch(req, options);
  const [mapped, actualOptions] = h.calls[0][1];
  assert.equal(mapped.url, 'http://127.0.0.1:47615/android-zh-CN/data/dbfilesclient/map.dbc');
  assert.equal(mapped.method, 'HEAD'); assert.equal(mapped.headers.get('X-Resource-Test'), 'kept');
  assert.equal(mapped.credentials, 'include'); assert.equal(mapped.cache, 'no-store');
  assert.equal(actualOptions, options);
});

test('verified original IDs zh and en override opposite navigator preferences', () => {
  const chinese = setup('en-US', { 'rogue.language': 'zh' });
  assert.equal(chinese.api.getLocale(), 'zh');
  assert.equal(chinese.api.usesChineseResources(), true);
  const english = setup('zh-CN', { 'rogue.language': 'en' });
  assert.equal(english.api.getLocale(), 'en');
  assert.equal(english.api.usesChineseResources(), false);
  const obsoleteCandidate = setup('en-US', { 'benilla:/benilla-config/language': 'zh' });
  assert.equal(obsoleteCandidate.api.usesChineseResources(), false);
});

test('same-page game language changes emit one restart notice and never rewrite language or saves', () => {
  const h = setup('en-US', { 'rogue.language': 'en', 'rogue.characters': 'RSE1:untouched' });
  h.localStorage.setItem('rogue.language', 'zh');
  h.localStorage.setItem('rogue.language', 'zh');
  h.localStorage.setItem('benilla:/benilla-config/language', 'en');
  h.localStorage.setItem('rogue.characters', 'RSE1:original-save-update');
  let notices = h.calls.filter(c => c[0] === 'event');
  assert.equal(notices.length, 1);
  assert.equal(notices[0][1].detail.locale, 'zh');
  assert.equal(notices[0][1].detail.requiresRestart, true);
  assert.equal(h.localStorage.getItem('rogue.language'), 'zh');
  assert.equal(h.localStorage.getItem('rogue.characters'), 'RSE1:original-save-update');
  h.localStorage.setItem('rogue.language', 'en');
  notices = h.calls.filter(c => c[0] === 'event');
  assert.equal(notices.length, 2); assert.equal(notices[1][1].detail.locale, 'en');
  assert.equal(h.api.usesChineseResources(), false);
});
