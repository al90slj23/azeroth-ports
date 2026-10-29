'use strict';

// Separate Simplified Chinese variants for the original English system-message
// and zone-name resources. The original core and original data index stay intact.
(() => {
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) return;
  const STORAGE_KEYS = ['rogue.language'];
  const RESOURCES = new Set([
    '/data/interface/framexml/globalstrings.lua',
    '/data/dbfilesclient/areatable.dbc',
    '/data/dbfilesclient/map.dbc',
  ]);
  const PREFIX = '/android-zh-CN';
  const nativeFetch = window.fetch;

  function normalize(value) {
    if (typeof value !== 'string') return '';
    let text = value.trim();
    try {
      const parsed = JSON.parse(text);
      if (typeof parsed === 'string') text = parsed;
    } catch (_) { /* The game's state file may be a bare language code. */ }
    return text.trim().replace(/_/g, '-').toLowerCase();
  }
  function getLocale() {
    try {
      for (const key of STORAGE_KEYS) {
        const value = normalize(window.localStorage.getItem(key));
        if (value) return value;
      }
    } catch (_) { /* Unavailable storage falls back to the browser language. */ }
    return normalize(navigator.language);
  }
  function usesChineseResources() {
    // The original game's Simplified Chinese language ID is "zh". A traditional
    // Chinese browser preference remains untouched unless the player picks zh.
    return /^(?:zh|zhcn|zh-cn|zh-sg|zh-hans(?:-[a-z0-9]+)?)$/.test(getLocale());
  }
  function rewriteResourceUrl(address) {
    if (!usesChineseResources()) return address;
    try {
      const url = new URL(address, location.href);
      if (url.origin !== location.origin || url.username || url.password) return address;
      const path = decodeURIComponent(url.pathname).toLowerCase();
      if (!RESOURCES.has(path)) return address;
      url.pathname = PREFIX + path;
      return url.href;
    } catch (_) { return address; }
  }

  if (typeof nativeFetch === 'function') {
    window.fetch = function (input, init) {
      const isRequest = typeof Request !== 'undefined' && input instanceof Request;
      const method = String(init?.method || (isRequest ? input.method : 'GET')).toUpperCase();
      if (method !== 'GET' && method !== 'HEAD') return nativeFetch.call(this, input, init);
      const original = isRequest ? input.url : input;
      const mapped = rewriteResourceUrl(original);
      if (mapped === original) return nativeFetch.call(this, input, init);
      // Request copies preserve method/headers/credentials/cache/signal; init is
      // still passed through unchanged, including any caller's explicit options.
      return nativeFetch.call(this, isRequest ? new Request(mapped, input) : mapped, init);
    };
  }
  if (typeof XMLHttpRequest !== 'undefined') {
    const open = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function (...args) {
      if (/^(?:GET|HEAD)$/i.test(String(args[0]))) args[1] = rewriteResourceUrl(args[1]);
      // The async argument is never changed. The original game uses synchronous
      // XHR, while boot.js prefetches the same URLs through fetch for cache hits.
      return open.apply(this, args);
    };
  }

  let previousLocale = getLocale();
  function languageChanged() {
    const locale = getLocale();
    if (locale === previousLocale) return;
    previousLocale = locale;
    window.dispatchEvent(new CustomEvent('az-language-resource-change', {
      detail: { locale, requiresRestart: true },
    }));
  }
  window.addEventListener('storage', (event) => {
    if (event.key === null || STORAGE_KEYS.includes(event.key)) languageChanged();
  });
  if (typeof Storage !== 'undefined') {
    for (const method of ['setItem', 'removeItem']) {
      const original = Storage.prototype[method];
      Storage.prototype[method] = function (...args) {
        const result = original.apply(this, args);
        // Browser storage events do not fire in the writing page. Observe only
        // the exact language key; never read, transform, or write any save data.
        if (this === window.localStorage && STORAGE_KEYS.includes(String(args[0]))) languageChanged();
        return result;
      };
    }
  }
  window.AzerothAndroidLocalization = Object.freeze({ getLocale, usesChineseResources, rewriteResourceUrl });
})();
