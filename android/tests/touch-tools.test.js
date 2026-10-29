'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

function setup(hostname = '127.0.0.1', dpr = 2) {
  const listeners = {};
  const events = [];
  const timers = [];
  const dom = [];
  class Event {
    constructor(type, props = {}) { Object.assign(this, props, { type }); }
    preventDefault() { this.prevented = true; }
    stopImmediatePropagation() { this.stopped = true; }
  }
  const canvas = { tagName: 'CANVAS', isConnected: true, width: 1920, height: 1080,
    getBoundingClientRect: () => ({ width: 960, height: 540 }),
    dispatchEvent: e => { events.push(e); return true; }, focus: () => {} };
  const doc = { body: { append: x => dom.push(x) }, activeElement: null,
    addEventListener: () => {}, querySelector: () => canvas,
    getElementById: id => id === 'benilla' ? canvas : null,
    createElement: () => ({ style: {}, addEventListener() {}, setAttribute() {} }) };
  const win = { devicePixelRatio: dpr, addEventListener: (type, fn) => (listeners[type] ||= []).push(fn),
    dispatchEvent: e => { for (const fn of listeners[e.type] || []) fn(e); } };
  const context = { window: win, document: doc, location: { hostname }, performance: { now: () => 10 },
    PointerEvent: Event, MouseEvent: Event, WheelEvent: Event, CustomEvent: Event, KeyboardEvent: Event,
    setTimeout: fn => { timers.push(fn); return timers.length; }, clearTimeout: () => {}, console };
  vm.runInNewContext(fs.readFileSync(require.resolve('../web/android-touch.js'), 'utf8'), context);
  const emit = (type, x = 100, y = 100, target = canvas, extra = {}) => {
    const e = new Event(type, { target, clientX: x, clientY: y, pointerType: 'touch', pointerId: 7, ...extra });
    win.dispatchEvent(e); return e;
  };
  return { api: win.AzerothAndroidTouch, emit, events, timers, dom, canvas, window: win };
}

test('normal gameplay leaves touches, including multitouch, untouched', () => {
  const h = setup();
  assert.equal(h.api.getMode(), 'play');
  for (const type of ['pointerdown', 'pointermove', 'pointerup', 'touchstart', 'touchend']) {
    assert.equal(h.emit(type).prevented, undefined);
  }
  assert.equal(h.events.length, 0);
});

test('a menu tap produces a sampled mouse press and delayed release', () => {
  const h = setup(); h.api.setMode('menu');
  assert.equal(h.emit('pointerdown', 150, 90).prevented, true);
  h.emit('pointerup', 150, 90);
  assert.equal(h.events.filter(e => e.type === 'pointerdown').length, 1);
  assert.equal(h.events.filter(e => e.type === 'pointerup').length, 0);
  h.timers.shift()();
  assert.equal(h.events.filter(e => e.type === 'pointerup').length, 1);
  assert.equal(h.events.find(e => e.type === 'pointerdown').pointerType, 'mouse');
});

test('dragging list content scrolls in the finger direction and never clicks a row', () => {
  const h = setup(); h.api.setMode('menu');
  h.emit('pointerdown', 400, 300); h.emit('pointermove', 401, 260); h.emit('pointermove', 401, 200); h.emit('pointerup', 401, 200);
  assert.deepEqual(h.events.filter(e => e.type === 'wheel').map(e => e.deltaY), [40, 60]);
  assert.equal(h.events.filter(e => e.type === 'pointerdown').length, 0);
  assert.equal(h.events.filter(e => e.type === 'mousedown').length, 0);
});

test('inspection hovers without clicks or skill keys; DOM controls are untouched', () => {
  const h = setup(); h.api.setMode('inspect');
  h.emit('pointerdown'); h.emit('pointermove', 110, 140); h.emit('pointerup', 110, 140);
  assert.ok(h.events.some(e => e.type === 'pointermove'));
  assert.equal(h.events.some(e => /down|wheel/.test(e.type)), false);
  assert.equal(h.emit('pointerdown', 1, 1, { tagName: 'BUTTON' }).prevented, undefined);
  assert.equal(h.dom[0].hidden, false);
  h.api.setMode('play'); assert.equal(h.dom[0].hidden, true);
});

test('returning to normal mode releases an outstanding mouse button', () => {
  const h = setup(); h.api.setMode('menu'); h.emit('pointerdown'); h.emit('pointerup');
  h.api.setMode('play');
  assert.equal(h.events.filter(e => e.type === 'pointerup').length, 1);
  assert.equal(h.emit('pointerdown').prevented, undefined);
});

test('character and talent shortcuts use original bindings and balanced key releases', () => {
  const h = setup();
  assert.equal(h.api.sendShortcut('character'), true); h.timers.shift()();
  assert.equal(h.api.sendShortcut('talents'), true); h.timers.shift()();
  assert.deepEqual(h.events.map(e => [e.type, e.code]), [['keydown','KeyC'],['keyup','KeyC'],['keydown','KeyN'],['keyup','KeyN']]);
  assert.equal(h.api.sendShortcut('arbitrary'), false);
});

test('touch helpers never install on a remote page', () => {
  assert.equal(setup('untrusted.example').api, undefined);
});

for (const dpr of [1, 2, 3]) {
  test(`canvas input mapping compensates a fixed 1920x1080 canvas at DPR ${dpr}`, () => {
    const h = setup('127.0.0.1', dpr);
    const event = { target: h.canvas };
    assert.equal(h.api.canvasCoordinate(event, 'x', 480) * dpr, 960);
    assert.equal(h.api.canvasCoordinate(event, 'y', 270) * dpr, 540);
    assert.equal(h.api.canvasCoordinate(event, 'x', -6) * dpr, -12);
    assert.equal(h.api.canvasCoordinate(event, 'y', -9) * dpr, -18);
    assert.equal(event.target, h.canvas);
  });
}

test('canvas coordinate mapping leaves DOM targets, invalid dimensions and nonfinite values alone', () => {
  const h = setup();
  assert.equal(h.api.canvasCoordinate({ target: { tagName: 'BUTTON' } }, 'x', 125), 125);
  assert.equal(h.api.canvasCoordinate(null, 'x', 125), 125);
  assert.equal(h.api.canvasCoordinate({ target: h.canvas }, 'z', 125), 125);
  assert.equal(h.api.canvasCoordinate({ target: h.canvas }, 'x', Infinity), Infinity);
  h.canvas.getBoundingClientRect = () => ({ width: 0, height: NaN });
  assert.equal(h.api.canvasCoordinate({ target: h.canvas }, 'x', 125), 125);
  assert.equal(h.api.canvasCoordinate({ target: h.canvas }, 'y', 125), 125);
  h.canvas.getBoundingClientRect = () => ({ width: 960, height: 540 });
  h.canvas.width = Infinity;
  assert.equal(h.api.canvasCoordinate({ target: h.canvas }, 'x', 125), 125);
  for (const badDpr of [0, NaN, Infinity]) {
    const bad = setup('127.0.0.1', badDpr);
    assert.equal(bad.api.canvasCoordinate({ target: bad.canvas }, 'x', 125), 125);
  }
});

test('synthetic pointer hovers identify no changed button and contain their own coalesced sample', () => {
  const h = setup(); h.api.setMode('menu');
  h.emit('pointerdown', 100, 200); h.emit('pointerup', 100, 200); h.timers.shift()();
  for (const event of h.events.filter(e => e.type === 'pointermove')) {
    assert.equal(event.button, -1);
    assert.equal(event.buttons, 0);
    assert.equal(event.getCoalescedEvents().length, 1);
    assert.equal(event.getCoalescedEvents()[0], event);
  }
  for (const event of h.events.filter(e => ['pointerdown', 'pointerup'].includes(e.type))) {
    assert.equal(event.button, 0);
    assert.equal(Object.hasOwn(event, 'getCoalescedEvents'), false);
  }
  const native = h.emit('pointermove');
  assert.equal(Object.hasOwn(native, 'getCoalescedEvents'), false);
});

test('enemy, friendly and all nameplate bindings send balanced key and modifier sequences', () => {
  for (const [name, modifier, code] of [
    ['enemyNameplates', null, null],
    ['friendNameplates', 'Shift', 'ShiftLeft'],
    ['allNameplates', 'Control', 'ControlLeft'],
  ]) {
    const h = setup();
    assert.equal(h.api.sendShortcut(name), true);
    h.timers.shift()();
    assert.deepEqual(h.events.map(e => [e.type, e.code]), modifier ? [
      ['keydown', code], ['keydown', 'KeyV'], ['keyup', 'KeyV'], ['keyup', code],
    ] : [['keydown','KeyV'], ['keyup','KeyV']]);
    if (modifier) {
      const flag = modifier === 'Control' ? 'ctrlKey' : 'shiftKey';
      assert.deepEqual(h.events.map(e => e[flag]), [true, true, true, false]);
    }
    if (modifier === 'Control') assert.ok(h.events.every(e => e.prevented === true));
  }
});

test('rapid shortcuts and window blur release outstanding keys exactly once', () => {
  const h = setup();
  h.api.sendShortcut('allNameplates');
  h.api.sendShortcut('character');
  h.emit('blur');
  for (const callback of h.timers) callback();
  assert.deepEqual(h.events.map(e => [e.type, e.code]), [
    ['keydown','ControlLeft'],['keydown','KeyV'],['keyup','KeyV'],['keyup','ControlLeft'],
    ['keydown','KeyC'],['keyup','KeyC'],
  ]);
});

test('native coalesced pointer samples without targets use only the known game canvas', () => {
  const h = setup('127.0.0.1', 3);
  for (const pointerType of ['mouse', 'touch', 'pen']) {
    const sample = { target: null, currentTarget: null, pointerType };
    assert.equal(h.api.canvasCoordinate(sample, 'x', 480), 320);
    assert.equal(h.api.canvasCoordinate(sample, 'y', 270), 180);
    assert.equal(sample.target, null);
  }
  assert.equal(h.api.canvasCoordinate({ target: null, currentTarget: h.canvas }, 'x', 480), 320);
  assert.equal(h.api.canvasCoordinate({ target: { tagName: 'BUTTON' }, currentTarget: null, pointerType: 'mouse' }, 'x', 480), 480);
  assert.equal(h.api.canvasCoordinate({ target: { tagName: 'BUTTON' }, currentTarget: h.canvas, pointerType: 'mouse' }, 'x', 480), 480);
  assert.equal(h.api.canvasCoordinate({ target: null, currentTarget: null, pointerType: 'unknown' }, 'x', 480), 480);
  assert.equal(h.api.canvasCoordinate({ target: null, currentTarget: { tagName: 'BODY' }, pointerType: 'mouse' }, 'x', 480), 480);
});

test('all synthetic pointer, compatibility mouse and wheel events use the actual window view', () => {
  const h = setup('127.0.0.1', 3); h.api.setMode('menu');
  h.emit('pointerdown', 800, 300); h.emit('pointermove', 801, 240); h.emit('pointerup', 801, 240);
  h.emit('pointerdown', 800, 300); h.emit('pointerup', 800, 300); h.timers.shift()();
  const events = h.events.filter(e => ['pointermove','pointerdown','pointerup','mousemove','mousedown','mouseup','wheel'].includes(e.type));
  assert.ok(events.some(e => e.type === 'wheel'));
  assert.ok(events.some(e => e.type === 'pointerdown'));
  assert.ok(events.some(e => e.type === 'mousemove'));
  assert.ok(events.every(e => e.view === h.window));
});
