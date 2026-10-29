'use strict';

// Opt-in touch tools for the original canvas UI. The normal mode never consumes
// gameplay touches, so the original sticks, camera and multitouch remain intact.
(() => {
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) return;
  const MODES = new Set(['play', 'menu', 'inspect']);
  let mode = 'play';
  let gesture = null;
  let suppressClickUntil = 0;
  let mouseDown = null;
  let keyboardRelease = null;
  const timers = new Set();
  const later = (callback, ms) => {
    const id = setTimeout(() => { timers.delete(id); callback(); }, ms);
    timers.add(id);
  };
  const canvasFor = (target) => target?.tagName === 'CANVAS' ? target : null;
  const stop = (event) => { event.preventDefault(); event.stopImmediatePropagation(); };
  const point = (event) => ({ x: event.clientX, y: event.clientY });

  // The original client can render a fixed-size canvas whose CSS size differs
  // from its physical size. winit already multiplies these coordinates by DPR;
  // compensate here only in its input getters, leaving trusted DOM events and
  // all native touch IDs intact. The same factor applies to offset and movement.
  function canvasCoordinate(event, axis, original) {
    // A coalesced native PointerEvent can have no target/currentTarget at all.
    // In that case use the known original game canvas, but never reinterpret a
    // real DOM target (the floating controls must retain normal coordinates).
    const target = event?.target;
    if (target != null && !canvasFor(target)) return original;
    let canvas = canvasFor(target) || canvasFor(event?.currentTarget);
    if (!canvas && target == null && event?.currentTarget == null
        && ['mouse', 'touch', 'pen'].includes(event?.pointerType)) {
      canvas = canvasFor(document.getElementById('benilla'));
    }
    if (!canvas || !Number.isFinite(original) || !['x', 'y'].includes(axis)
        || typeof canvas.getBoundingClientRect !== 'function') return original;
    const dimension = axis === 'x' ? 'width' : 'height';
    const dpr = Number(window.devicePixelRatio);
    const rect = canvas.getBoundingClientRect();
    if (!Number.isFinite(dpr) || dpr <= 0 || !rect
        || !Number.isFinite(rect[dimension]) || rect[dimension] <= 0
        || !Number.isFinite(canvas[dimension]) || canvas[dimension] <= 0) return original;
    const factor = canvas[dimension] / (rect[dimension] * dpr);
    const mapped = original * factor;
    return Number.isFinite(factor) && factor > 0 && Number.isFinite(mapped) ? mapped : original;
  }

  function mouse(canvas, type, at, buttons = 0) {
    if (!canvas?.isConnected) return;
    // Pointer events are what winit's web backend listens for. Also send the
    // compatibility mouse event for an engine UI listener that uses MouseEvent.
    const options = { view: window, bubbles: true, cancelable: true, composed: true,
      clientX: at.x, clientY: at.y, button: type === 'pointermove' ? -1 : 0, buttons,
      pointerId: 1, pointerType: 'mouse', isPrimary: true };
    const pointer = new PointerEvent(type, options);
    if (type === 'pointermove') {
      // Synthetic events have no browser coalescing history. winit consumes
      // getCoalescedEvents() directly when it exists, so an empty native result
      // would silently discard the hover. Affect this synthetic instance only.
      Object.defineProperty(pointer, 'getCoalescedEvents', { value: () => [pointer] });
    }
    canvas.dispatchEvent(pointer);
    const legacy = { pointermove: 'mousemove', pointerdown: 'mousedown', pointerup: 'mouseup' }[type];
    if (legacy) canvas.dispatchEvent(new MouseEvent(legacy, { ...options, button: 0 }));
  }
  function hover(canvas, at) {
    mouse(canvas, 'pointermove', at);
  }
  function release() {
    if (mouseDown) mouse(mouseDown.canvas, 'pointerup', mouseDown.at);
    mouseDown = null;
  }
  function tap(canvas, at) {
    release();
    hover(canvas, at);
    mouseDown = { canvas, at };
    mouse(canvas, 'pointerdown', at, 1);
    // Do not press and release inside one frame: the engine samples buttons on
    // its next frame, and short synthetic clicks otherwise disappear.
    const pending = mouseDown;
    later(() => { if (mouseDown === pending) release(); }, 80);
  }
  function setMode(next) {
    if (!MODES.has(next)) throw new TypeError('Unknown Android touch mode');
    release(); gesture = null; mode = next;
    window.dispatchEvent(new CustomEvent('azeroth-touch-mode', { detail: { mode } }));
    window.dispatchEvent(new CustomEvent('az-touch-mode', { detail: { mode } }));
    updateModeBadge();
    return mode;
  }

  window.addEventListener('pointerdown', (event) => {
    if (mode === 'play' || event.pointerType !== 'touch') return;
    const canvas = canvasFor(event.target);
    if (!canvas) return;
    stop(event);
    suppressClickUntil = performance.now() + 900;
    if (gesture) return;
    gesture = { canvas, id: event.pointerId, start: point(event), last: point(event), dragged: false };
    hover(canvas, gesture.start);
  }, { capture: true, passive: false });

  window.addEventListener('pointermove', (event) => {
    if (mode === 'play' || event.pointerType !== 'touch' || !canvasFor(event.target)) return;
    stop(event);
    if (!gesture || gesture.id !== event.pointerId) return;
    const at = point(event);
    const dx = at.x - gesture.start.x;
    const dy = at.y - gesture.start.y;
    if (Math.hypot(dx, dy) > 10) gesture.dragged = true;
    hover(gesture.canvas, at);
    if (mode === 'menu' && gesture.dragged && Math.abs(dy) > Math.abs(dx)) {
      gesture.canvas.dispatchEvent(new WheelEvent('wheel', {
        view: window, bubbles: true, cancelable: true, clientX: at.x, clientY: at.y,
        deltaX: 0, deltaY: gesture.last.y - at.y, deltaMode: 0,
      }));
    }
    gesture.last = at;
  }, { capture: true, passive: false });

  function end(event) {
    if (mode === 'play' || event.pointerType !== 'touch' || !canvasFor(event.target)) return;
    stop(event);
    suppressClickUntil = performance.now() + 900;
    if (!gesture || gesture.id !== event.pointerId) return;
    const active = gesture; gesture = null;
    if (event.type !== 'pointercancel' && mode === 'menu' && !active.dragged) tap(active.canvas, point(event));
    else if (event.type !== 'pointercancel') hover(active.canvas, point(event));
  }
  window.addEventListener('pointerup', end, { capture: true, passive: false });
  window.addEventListener('pointercancel', end, { capture: true, passive: false });
  for (const type of ['touchstart', 'touchmove', 'touchend', 'touchcancel']) {
    window.addEventListener(type, (event) => {
      if (mode !== 'play' && canvasFor(event.target)) stop(event);
    }, { capture: true, passive: false });
  }
  window.addEventListener('click', (event) => {
    if (canvasFor(event.target) && performance.now() < suppressClickUntil) stop(event);
  }, { capture: true, passive: false });
  window.addEventListener('blur', () => { release(); keyboardRelease?.(); gesture = null; });
  document.addEventListener('visibilitychange', () => { if (document.hidden) { release(); keyboardRelease?.(); gesture = null; } });

  function sendShortcut(name) {
    const shortcut = {
      character: ['c', 'KeyC', 67], talents: ['n', 'KeyN', 78],
      pause: ['Escape', 'Escape', 27], map: ['m', 'KeyM', 77], backpack: ['b', 'KeyB', 66],
      enemyNameplates: ['v', 'KeyV', 86],
      allNameplates: ['v', 'KeyV', 86, 'Control'],
      friendNameplates: ['V', 'KeyV', 86, 'Shift'],
    }[name];
    if (!shortcut) return false;
    const canvas = document.querySelector('canvas');
    if (!canvas) return false;
    keyboardRelease?.();
    const active = document.activeElement;
    if (active && /^(INPUT|TEXTAREA|SELECT)$/.test(active.tagName)) active.blur();
    canvas.focus({ preventScroll: true });
    const [key, code, keyCode, modifier] = shortcut;
    const modifierCode = modifier === 'Control' ? 'ControlLeft' : 'ShiftLeft';
    const modifierKeyCode = modifier === 'Control' ? 17 : 16;
    const send = (type, eventKey, eventCode, numericCode, modifierHeld) => {
      const event = new KeyboardEvent(type, {
        key: eventKey, code: eventCode, keyCode: numericCode, which: numericCode,
        ctrlKey: modifierHeld && modifier === 'Control',
        shiftKey: modifierHeld && modifier === 'Shift',
        location: eventCode === modifierCode ? 1 : 0,
        bubbles: true, cancelable: true,
      });
      // Keep Ctrl+V entirely inside the game input path; it is a nameplate
      // binding, never a request to paste into a browser or the IME field.
      if (modifier === 'Control') event.preventDefault();
      canvas.dispatchEvent(event);
    };
    if (modifier) send('keydown', modifier, modifierCode, modifierKeyCode, true);
    send('keydown', key, code, keyCode, !!modifier);
    let released = false;
    const finish = () => {
      if (released) return;
      released = true;
      send('keyup', key, code, keyCode, !!modifier);
      if (modifier) send('keyup', modifier, modifierCode, modifierKeyCode, false);
      if (keyboardRelease === finish) keyboardRelease = null;
    };
    keyboardRelease = finish;
    later(finish, 80);
    return true;
  }

  let modeBadge;
  function updateModeBadge() {
    if (!document.body) return;
    if (!modeBadge) {
      modeBadge = document.createElement('button');
      modeBadge.id = 'az-touch-mode-toast';
      modeBadge.type = 'button';
      modeBadge.style.cssText = 'position:fixed;z-index:2147483645;left:50%;top:max(8px,env(safe-area-inset-top));transform:translateX(-50%);min-height:44px;padding:7px 14px;border:1px solid #b89549;border-radius:5px;background:#21190df2;color:#ffe3a1;font:14px sans-serif;touch-action:manipulation;box-shadow:0 2px 9px #0009;';
      modeBadge.addEventListener('click', () => setMode('play'));
      document.body.append(modeBadge);
    }
    modeBadge.hidden = mode === 'play';
    modeBadge.textContent = (mode === 'menu' ? '列表拖动中' : '详情查看中') + ' · 恢复正常操作';
    modeBadge.setAttribute('aria-label', modeBadge.textContent);
  }
  document.addEventListener('DOMContentLoaded', updateModeBadge, { once: true });

  window.AzerothAndroidTouch = Object.freeze({ setMode, getMode: () => mode, sendShortcut, canvasCoordinate });
})();
