'use strict';

// Android packaging adapter only. The original gameplay WASM stays byte-for-byte intact.
// The web client derives its lobby URL from location; route only that loopback route
// to the author's public service. Game relay URLs returned by that service are unchanged.
(() => {
  if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) return;
  const localOrigin = location.origin;
  const NativeWebSocket = window.WebSocket;
  window.WebSocket = class extends NativeWebSocket {
    constructor(address, protocols) {
      const target = new URL(address, location.href);
      if (['ws:', 'wss:'].includes(target.protocol)
          && target.hostname === location.hostname
          && target.port === location.port
          && /^\/coop(?:\/|$)/.test(target.pathname)) {
        target.protocol = 'wss:';
        target.hostname = 'wow.aethus.pl';
        target.port = '';
      }
      if (protocols === undefined) super(target.href);
      else super(target.href, protocols);
    }
  };

  // Android WebView does not save blob: downloads automatically. This narrowly adapts
  // the original game's .sav export to Android's user-selected document picker.
  // Chrome handles its own exports and has no AndroidHost bridge.
  document.addEventListener('click', async (event) => {
    if (window.top !== window || !window.AndroidHost
        || typeof window.AndroidHost.exportSave !== 'function') return;
    const anchor = event.target?.closest?.('a[download]');
    if (!anchor || !/\.sav$/i.test(anchor.download)
        || !anchor.href.startsWith(`blob:${localOrigin}/`)) return;
    event.preventDefault();
    try {
      const response = await fetch(anchor.href);
      const blob = await response.blob();
      if (blob.size > 8 * 1024 * 1024) throw new Error('Save exceeds 8 MB');
      const encoded = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onerror = reject;
        reader.onload = () => resolve(String(reader.result).split(',')[1]);
        reader.readAsDataURL(blob);
      });
      window.AndroidHost.exportSave(anchor.download, encoded);
    } catch (error) {
      console.error('Android save export failed:', error);
    }
  }, true);
})();
