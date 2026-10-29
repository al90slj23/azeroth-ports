'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { preparePendingProfile } = require('./profile-migration');

function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'azeroth-profile-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const source = path.join(root, 'azeroth-mac-source');
  const defaultProfile = path.join(root, 'Application Support', 'Azeroth Survivors');
  const pendingPath = path.join(root, 'pending-profile.json');
  fs.mkdirSync(path.join(source, 'Local Storage', 'leveldb'), { recursive: true });
  fs.writeFileSync(path.join(source, 'Local Storage', 'leveldb', '000001.log'), 'saved hero and Chinese language');
  fs.writeFileSync(path.join(source, 'Preferences'), '{"language":"zh"}');
  fs.writeFileSync(pendingPath, JSON.stringify({ source, pid: 12345 }));
  return { root, source, defaultProfile, pendingPath };
}

test('reuses the active source profile without copying or completing metadata', (t) => {
  const f = fixture(t);
  const before = fs.readFileSync(f.pendingPath, 'utf8');
  const checked = [];
  const result = preparePendingProfile({ ...f, isProcessAlive: (pid) => { checked.push(pid); return true; } });
  assert.deepEqual(checked, [12345]);
  assert.deepEqual(result, { profile: f.source, pending: true });
  assert.equal(fs.existsSync(f.defaultProfile), false);
  assert.equal(fs.readFileSync(f.pendingPath, 'utf8'), before);
});

test('copies a closed profile, preserves storage and source, and excludes transient files and caches', (t) => {
  const f = fixture(t);
  for (const name of ['Cache', 'Code Cache', 'GPUCache', 'DawnWebGPUCache', path.join('Service Worker', 'CacheStorage')]) {
    fs.mkdirSync(path.join(f.source, name), { recursive: true });
    fs.writeFileSync(path.join(f.source, name, 'cached-data'), 'not player data');
  }
  for (const name of ['SingletonLock', 'SingletonSocket', 'SingletonCookie', 'DevToolsActivePort']) {
    fs.writeFileSync(path.join(f.source, name), 'old process metadata');
  }
  fs.mkdirSync(path.join(f.source, 'IndexedDB'), { recursive: true });
  fs.writeFileSync(path.join(f.source, 'IndexedDB', 'addon'), 'installed addon');
  fs.mkdirSync(path.join(f.source, 'Network'), { recursive: true });
  fs.writeFileSync(path.join(f.source, 'Network', 'Cookies'), 'retained cookies');

  const result = preparePendingProfile({ ...f, isProcessAlive: () => false });
  assert.deepEqual(result, { profile: f.defaultProfile, pending: false, migrated: true });
  assert.equal(fs.readFileSync(path.join(f.defaultProfile, 'Local Storage', 'leveldb', '000001.log'), 'utf8'), 'saved hero and Chinese language');
  assert.equal(fs.readFileSync(path.join(f.defaultProfile, 'IndexedDB', 'addon'), 'utf8'), 'installed addon');
  assert.equal(fs.readFileSync(path.join(f.defaultProfile, 'Network', 'Cookies'), 'utf8'), 'retained cookies');
  assert.equal(fs.readFileSync(path.join(f.defaultProfile, 'Preferences'), 'utf8'), '{"language":"zh"}');
  for (const name of ['Cache', 'Code Cache', 'GPUCache', 'DawnWebGPUCache', path.join('Service Worker', 'CacheStorage'), 'SingletonLock', 'SingletonSocket', 'SingletonCookie', 'DevToolsActivePort']) {
    assert.equal(fs.existsSync(path.join(f.defaultProfile, name)), false, name);
    assert.equal(fs.existsSync(path.join(f.source, name)), true, `source remains: ${name}`);
  }
  const pending = JSON.parse(fs.readFileSync(f.pendingPath, 'utf8'));
  assert.equal(pending.completed, true);
  assert.equal(pending.destination, f.defaultProfile);
  assert.equal(pending.source, f.source);
  assert.equal(fs.existsSync(f.source), true);
  // A later launch uses the completed destination and never copies the source again.
  assert.deepEqual(preparePendingProfile({ ...f, isProcessAlive: () => { throw new Error('must not inspect completed source'); } }), { profile: f.defaultProfile, pending: false });
});

test('refuses to overwrite an existing player profile without changing either profile or metadata', (t) => {
  const f = fixture(t);
  fs.mkdirSync(path.join(f.defaultProfile, 'Local Storage'), { recursive: true });
  fs.writeFileSync(path.join(f.defaultProfile, 'Local Storage', 'existing-save'), 'keep my player');
  const before = fs.readFileSync(f.pendingPath, 'utf8');
  assert.throws(() => preparePendingProfile({ ...f, isProcessAlive: () => false }), /Existing player data will not be overwritten/);
  assert.equal(fs.readFileSync(path.join(f.defaultProfile, 'Local Storage', 'existing-save'), 'utf8'), 'keep my player');
  assert.equal(fs.existsSync(path.join(f.defaultProfile, 'Preferences')), false);
  assert.equal(fs.readFileSync(f.pendingPath, 'utf8'), before);
  assert.equal(fs.readFileSync(path.join(f.source, 'Local Storage', 'leveldb', '000001.log'), 'utf8'), 'saved hero and Chinese language');
});

test('rejects unrelated source directory names before mutation', (t) => {
  const f = fixture(t);
  const unrelated = path.join(f.root, 'other-app');
  fs.mkdirSync(unrelated);
  fs.writeFileSync(f.pendingPath, JSON.stringify({ source: unrelated, pid: 12345 }));
  assert.throws(() => preparePendingProfile({ ...f, isProcessAlive: () => false }), /existing azeroth-mac-/);
  assert.equal(fs.existsSync(f.defaultProfile), false);
});
