/* Android-only controls over real engine CVars. renderScale is deferred by the
 * unmodified engine. No CSS resolution trick or global animation throttling. */
(function () {
  'use strict';
  const STORAGE_KEY = 'azeroth.android.performance.v2';
  const POSITION_KEY = 'azeroth.android.performance.position.v1';
  const CONFIG_KEY = 'benilla:/benilla-config/config.toml';
  const HUD_MIGRATION_KEY = 'azeroth.android.hud-compact.v3';
  const LEGACY_HUD_MIGRATION_KEY = 'azeroth.android.hud-compact.v2';
  const PRESETS = Object.freeze({
    cool: { resolution: 50, distance: 177, detail: 0 },
    balanced: { resolution: 75, distance: 300, detail: 1 },
    clear: { resolution: 100, distance: 420, detail: 2 },
  });
  const ORIGINAL = Object.freeze({ resolution: 100, distance: 420, detail: 2 });
  const THERMAL_NAMES = ['正常', '轻度发热', '中度发热', '严重发热', '临界过热', '紧急过热', '即将关机'];
  function number(value, fallback, min, max, step) {
    if (value === null || value === '' || typeof value === 'boolean') return fallback;
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, Math.round(n / step) * step)) : fallback;
  }
  function normalize(value) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) value = ORIGINAL;
    const result = {
      resolution: number(value.resolution, ORIGINAL.resolution, 50, 100, 5),
      distance: number(value.distance, ORIGINAL.distance, 177, 420, 1),
      detail: number(value.detail, ORIGINAL.detail, 0, 2, 1),
    };
    // HUD scale is independent of the 3D render scale; the touch adapter may supply it.
    if (value.hudScale !== undefined) result.hudScale = number(value.hudScale, 100, 50, 100, 5);
    return result;
  }
  function cvars(settings) {
    const s = normalize(settings);
    const out = {
      renderScale: (s.resolution / 100).toFixed(2), farclip: String(s.distance),
      WorldDetail: String(s.detail), spellEffectLevel: String(s.detail),
      weatherDensity: String([0, 1, 3][s.detail]), ffxGlow: s.detail === 0 ? '0' : '1',
      // Preserve the upstream Android GPU compiler workaround, even in the clear preset.
      pbr_lite: '1', pipe_warm: '0',
    };
    if (s.hudScale !== undefined) out.hudScale = (s.hudScale / 100).toFixed(2);
    return out;
  }
  function scopedCvars(settings, fields) {
    const all = cvars(settings), selected = {};
    const map = { resolution: ['renderScale'], distance: ['farclip'],
      detail: ['WorldDetail','spellEffectLevel','weatherDensity','ffxGlow'], hudScale: ['hudScale'] };
    for (const field of fields) for (const key of map[field] || []) if (all[key] !== undefined) selected[key] = all[key];
    if (fields.some(field => field !== 'hudScale')) { selected.pbr_lite = '1'; selected.pipe_warm = '0'; }
    return selected;
  }
  function configCvar(text, wanted) {
    let section = '';
    for (const line of text.split('\n')) {
      const header = /^\s*\[([^\]]+)\]\s*(?:#.*)?$/.exec(line);
      if (header) { section = header[1]; continue; }
      if (section !== 'cvars') continue;
      const row = /^\s*(?:"([A-Za-z][A-Za-z0-9_]*)"|'([A-Za-z][A-Za-z0-9_]*)'|([A-Za-z][A-Za-z0-9_]*))\s*=\s*(.*)$/.exec(line);
      if (row && (row[1] || row[2] || row[3]).toLowerCase() === wanted.toLowerCase()) {
        const value = row[4].replace(/\s+#.*$/, '').trim();
        return { found: true, value: value.replace(/^(["'])(.*)\1$/, '$2') };
      }
    }
    return { found: false, value: null };
  }
  function shouldCompactHud(hud, legacyMarker) {
    if (!hud.found) return true;
    const scale = Number(hud.value);
    // A default 100% CVar is commonly already saved by the original client. The
    // v2 marker identifies its former 75% adapter default. Other custom sizes win.
    return Number.isFinite(scale) && (scale === 1 || (scale === 0.75 && Boolean(legacyMarker)));
  }
  function mergeConfig(text, values) {
    if (typeof text !== 'string' || text.length > 1024 * 1024) throw new Error('Invalid config');
    const lines = text.split('\n');
    let section = '', start = -1, end = lines.length;
    for (let i = 0; i < lines.length; i++) {
      const match = /^\s*\[([^\]]+)\]\s*(?:#.*)?$/.exec(lines[i]);
      if (!match) continue;
      if (section === 'cvars') { end = i; break; }
      section = match[1]; if (section === 'cvars') start = i;
    }
    if (start < 0) { if (lines.at(-1) !== '') lines.push(''); lines.push('[cvars]'); start = lines.length - 1; end = lines.length; }
    const allowed = new Set(['renderScale', 'farclip', 'WorldDetail', 'spellEffectLevel', 'weatherDensity', 'ffxGlow', 'pbr_lite', 'pipe_warm', 'hudScale']);
    const remaining = new Map(Object.entries(values).filter(([key, value]) => allowed.has(key) && /^[0-9]+(?:\.[0-9]+)?$/.test(String(value))));
    const lower = new Map([...remaining.keys()].map(key => [key.toLowerCase(), key]));
    for (let i = start + 1; i < end; i++) {
      const match = /^\s*(?:"([A-Za-z][A-Za-z0-9_]*)"|'([A-Za-z][A-Za-z0-9_]*)'|([A-Za-z][A-Za-z0-9_]*))\s*=/.exec(lines[i]);
      if (!match) continue;
      const key = lower.get((match[1] || match[2] || match[3]).toLowerCase());
      if (!key) continue;
      lines[i] = `${key} = ${JSON.stringify(String(values[key]))}`;
      remaining.delete(key);
    }
    lines.splice(end, 0, ...[...remaining].map(([key, value]) => `${key} = ${JSON.stringify(String(value))}`));
    return lines.join('\n');
  }
  function thermal(value) {
    if (!value || typeof value !== 'object') value = {};
    const temp = typeof value.batteryCelsius === 'number' && Number.isFinite(value.batteryCelsius)
      && value.batteryCelsius >= -40 && value.batteryCelsius <= 100 ? value.batteryCelsius : null;
    const status = Number.isInteger(value.thermalStatus) && value.thermalStatus >= 0
      && value.thermalStatus <= 6 ? value.thermalStatus : -1;
    return { batteryCelsius: temp, thermalStatus: status };
  }
  // The packaging overlay routes only the engine's animation-frame imports
  // through this gate. The browser's global rAF and DOM/timer callbacks stay native.
  function createFrameGate({ request, cancel, now, performanceObject }) {
    let paused = false, pauseStarted = 0, pausedDuration = 0, nextId = 1;
    const jobs = new Map();
    function schedule(job) {
      job.nativeId = request(job.target, timestamp => {
        job.nativeId = null;
        if (!jobs.has(job.id) || paused) return;
        jobs.delete(job.id);
        job.callback(timestamp - pausedDuration);
      });
    }
    function requestFrame(target, callback) {
      if (typeof callback !== 'function') throw new TypeError('Animation frame callback must be callable');
      // winit stores this opaque value as a signed integer. Do not collide with a
      // still-pending handle if a very long-lived session wraps the counter.
      while (jobs.has(nextId)) nextId = nextId >= 0x7ffffffe ? 1 : nextId + 1;
      const id = nextId; nextId = nextId >= 0x7ffffffe ? 1 : nextId + 1;
      const job = { id, target, callback, nativeId: null };
      jobs.set(id, job);
      if (!paused) {
        try { schedule(job); } catch (error) { jobs.delete(id); throw error; }
      }
      return id;
    }
    function cancelFrame(target, id) {
      const job = jobs.get(id);
      if (!job || job.target !== target) return;
      jobs.delete(id);
      if (job.nativeId !== null) cancel(job.target, job.nativeId);
    }
    function setPanelOpen(open) {
      open = Boolean(open);
      if (open === paused) return;
      if (open) {
        pauseStarted = now(); paused = true;
        for (const job of jobs.values()) {
          if (job.nativeId !== null) { cancel(job.target, job.nativeId); job.nativeId = null; }
        }
      } else {
        pausedDuration += Math.max(0, now() - pauseStarted); paused = false;
        for (const job of jobs.values()) if (job.nativeId === null) schedule(job);
      }
    }
    return Object.freeze({
      requestFrame, cancelFrame, setPanelOpen,
      monotonicNow(target) {
        // Date.now supplies save/export timestamps; only the engine's monotonic
        // performance clock is frozen so a closed panel cannot cause catch-up.
        return target === performanceObject ? (paused ? pauseStarted : now()) - pausedDuration : target.now();
      },
      isPaused: () => paused,
      pendingCount: () => jobs.size,
    });
  }
  const api = { STORAGE_KEY, POSITION_KEY, CONFIG_KEY, HUD_MIGRATION_KEY, LEGACY_HUD_MIGRATION_KEY, PRESETS, ORIGINAL, normalize, cvars, scopedCvars, configCvar, shouldCompactHud, mergeConfig, thermal, THERMAL_NAMES, createFrameGate };
  if (typeof module === 'object' && module.exports) { module.exports = api; return; }
  if (typeof window === 'undefined' || window.top !== window
      || !['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) return;
  const frameGate = createFrameGate({
    request: (target, callback) => target.requestAnimationFrame(callback),
    cancel: (target, id) => target.cancelAnimationFrame(id),
    now: typeof window.performance?.now === 'function' ? window.performance.now.bind(window.performance) : Date.now,
    performanceObject: window.performance,
  });
  window.AzerothAndroidPause = frameGate;
  let saved = null, pendingBoot = false, appliedThisBoot = false, bootConfigError = false;
  let hudMigrationApplied = false, bootOptionsChecked = false;
  const knownFields = ['resolution','distance','detail','hudScale'];
  let pendingFields = new Set();
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw); saved = normalize(parsed); pendingBoot = parsed.pending !== false;
      if (pendingBoot) pendingFields = new Set(Array.isArray(parsed.pendingFields)
        ? parsed.pendingFields.filter(field => knownFields.includes(field))
        : knownFields.filter(field => field !== 'hudScale' || saved.hudScale !== undefined));
    }
  } catch (_) {}
  const startup = saved ? { ...saved } : { ...ORIGINAL };
  // Read the actual HUD preference, rather than assuming a previously selected preset owns it.
  try {
    const hud = configCvar(localStorage.getItem(CONFIG_KEY) || '', 'hudScale');
    const current = Number(hud.value);
    if (!pendingFields.has('hudScale')) startup.hudScale = hud.found && Number.isFinite(current) && current > 0 && current <= 3 ? Math.round(current * 100) : 100;
  } catch (_) { if (startup.hudScale === undefined) startup.hudScale = 100; }
  let draft = { ...startup };
  // Called by the Android overlay of rogue.js immediately after its original Android defaults.
  // Consume user changes once. The independent v3 compact-HUD migration also runs once and never
  // replaces other custom HUD sizes or changes the other graphics by default.
  window.__azerothAndroidPerformance = {
    applyBootOptions() {
      if (bootOptionsChecked) return;
      let values = {}, bootEnv = {}, migrate = false, original;
      try {
        original = localStorage.getItem(CONFIG_KEY) || '';
        // Upstream seeds farclip=420 on every load. Reapply the actual persisted CVar,
        // not an old preset, so the player's later in-game distance preference wins.
        const persistedFarclip = configCvar(original, 'farclip');
        const farclip = Number(persistedFarclip.value);
        if (persistedFarclip.found && Number.isFinite(farclip) && farclip >= 177 && farclip <= 777) bootEnv.farclip = String(farclip);
        const marker = localStorage.getItem(HUD_MIGRATION_KEY);
        if (!marker) {
          migrate = true;
          if (shouldCompactHud(configCvar(original, 'hudScale'), localStorage.getItem(LEGACY_HUD_MIGRATION_KEY)) && !pendingFields.has('hudScale')) values.hudScale = '0.50';
        }
        if (pendingBoot) values = { ...values, ...scopedCvars(startup, [...pendingFields]) };
        if (Object.keys(values).length) localStorage.setItem(CONFIG_KEY, mergeConfig(original, values));
        if (pendingBoot) localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...startup, pending: false, pendingFields: [] }));
        if (migrate) localStorage.setItem(HUD_MIGRATION_KEY, 'done');
      } catch (_) { bootConfigError = true; return; }
      if (Object.keys(bootEnv).length || Object.keys(values).length) window.__wenilla_env = { ...(window.__wenilla_env || {}), ...bootEnv, ...values };
      hudMigrationApplied = migrate && values.hudScale === '0.50' && !pendingFields.has('hudScale');
      if (hudMigrationApplied) { startup.hudScale = 50; draft.hudScale = 50; }
      appliedThisBoot = pendingBoot; pendingBoot = false; pendingFields.clear(); bootOptionsChecked = true;
      document.dispatchEvent(new Event('az-performance-applied'));
    },
  };
  function equal(a, b) { return JSON.stringify(normalize(a)) === JSON.stringify(normalize(b)); }
  function mount() {
    if (document.getElementById('az-mobile-tools')) return;
    const root = document.createElement('div'); root.id = 'az-mobile-tools';
    root.innerHTML = `<style>
      #az-mobile-tools{--az-gold:#dfbd70;--az-edge:#75603b;color:#eee1c5;font:14px/1.45 Georgia,"Noto Serif CJK SC",serif;position:fixed;inset:0;z-index:2147483000;pointer-events:none}
      #az-mobile-tools *{box-sizing:border-box}#az-mobile-tools button,#az-mobile-tools input{font:inherit;accent-color:var(--az-gold)}
      #az-mobile-tools button{min-height:44px;cursor:pointer;color:#eee1c5;background:#292217;border:1px solid var(--az-edge);border-radius:5px;padding:9px 12px;touch-action:manipulation}#az-mobile-tools button:active{background:#4c3d24}#az-mobile-tools button:focus-visible,#az-mobile-tools input:focus-visible{outline:2px solid #f3d99a;outline-offset:2px}
      #az-mobile-tools .az-float{position:absolute;top:max(12px,env(safe-area-inset-top));right:max(12px,env(safe-area-inset-right));min-width:76px;min-height:48px;pointer-events:auto;touch-action:none;box-shadow:0 2px 8px #0009;color:var(--az-gold);font-size:13px;line-height:1.3;padding:6px 10px}#az-mobile-tools .az-float strong{display:block;font-size:13px;font-weight:normal;color:#eee1c5}
      #az-mobile-tools .az-panel{position:absolute;right:max(12px,env(safe-area-inset-right));top:max(12px,env(safe-area-inset-top));width:min(370px,calc(100vw - 24px));max-height:calc(100dvh - 24px - env(safe-area-inset-top) - env(safe-area-inset-bottom));overflow-y:auto;overscroll-behavior:contain;touch-action:pan-y;pointer-events:auto;padding:14px 16px 16px;background:#17140ff5;border:1px solid #947441;border-radius:8px;box-shadow:0 6px 30px #000b}
      #az-mobile-tools [hidden]{display:none!important}#az-mobile-tools h2{font-size:19px;line-height:1.3;font-weight:normal;color:var(--az-gold);margin:0}#az-mobile-tools .az-header{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:10px}#az-mobile-tools .az-close{font-size:14px;padding:7px 10px}
      #az-mobile-tools .az-temperature{display:flex;justify-content:space-between;align-items:baseline;gap:12px;padding:10px 0;border-top:1px solid #54432b;border-bottom:1px solid #54432b;margin:10px 0 12px}#az-mobile-tools .az-reading{font-size:25px;color:#f0d79d;white-space:nowrap}
      #az-mobile-tools .az-caption{font-size:12px;color:#c2b494;margin:4px 0 10px}#az-mobile-tools .az-touch-controls{margin:10px 0;padding-bottom:12px;border-bottom:1px solid #54432b}#az-mobile-tools .az-touch-controls h3{font-size:14px;font-weight:normal;margin:0 0 7px;color:#dfbd70}#az-mobile-tools .az-touch-row{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:6px 0}#az-mobile-tools .az-touch-row button{padding:8px 4px;font-size:13px}#az-mobile-tools .az-presets{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0 16px}#az-mobile-tools button[aria-pressed=true]{border-color:#eccb87;background:#514023;color:#fff0cc}
      #az-mobile-tools label{display:block;margin:14px 0 3px}#az-mobile-tools .az-value{float:right;color:#f0d79d}#az-mobile-tools input[type=range]{width:100%;height:44px;margin:0;touch-action:pan-y}#az-mobile-tools .az-note{color:#d6c29a;font-size:13px;margin:10px 0}#az-mobile-tools .az-status{min-height:38px;color:#e3c985;font-size:13px;margin:12px 0 6px}#az-mobile-tools .az-restart{width:100%}#az-mobile-tools .az-confirm{border-top:1px solid #75603b;padding-top:10px;margin-top:10px}#az-mobile-tools .az-confirm p{margin:0 0 10px}#az-mobile-tools .az-actions{display:flex;gap:8px}#az-mobile-tools .az-actions button{flex:1}#az-mobile-tools .az-danger{color:#ffd0b0;border-color:#9e6951}
      @media(max-height:400px){#az-mobile-tools .az-panel{padding:10px 14px}#az-mobile-tools .az-temperature{padding:6px 0}}
    </style>
    <button type="button" class="az-float" aria-label="打开快捷操作与性能面板，可拖动位置" aria-expanded="false"><span>快捷</span><strong>温度 --</strong></button>
    <section class="az-panel" role="dialog" aria-modal="true" aria-labelledby="az-perf-title" hidden>
      <div class="az-header"><h2 id="az-perf-title">快捷操作与性能</h2><button type="button" class="az-close" aria-label="关闭性能面板">收起</button></div>
      <p class="az-caption">快捷窗打开时暂停本机游戏，收起后继续。联机时其他玩家不会暂停。</p>\n      <div class="az-touch-controls" hidden><h3>常用操作</h3><div class="az-touch-row"><button type="button" data-shortcut="character">角色</button><button type="button" data-shortcut="talents">天赋</button><button type="button" data-shortcut="pause">暂停菜单</button></div><div class="az-touch-row"><button type="button" data-shortcut="enemyNameplates">切换敌方血条</button><button type="button" data-shortcut="allNameplates">切换全部血条</button><button type="button" data-shortcut="friendNameplates">切换友方血条</button></div><div class="az-touch-row"><button type="button" data-touch-mode="play">正常操作</button><button type="button" data-touch-mode="menu">拖动列表</button><button type="button" data-touch-mode="inspect">查看详情</button></div><p class="az-caption">列表模式可上下拖动菜单；详情模式点击技能或装备查看提示。战斗前切回正常操作。</p></div>
      <div class="az-temperature"><div>电池温度<br><span class="az-thermal">系统热状态：不可用</span></div><div class="az-reading">-- °C</div></div>
      <p class="az-caption">显示系统提供的电池温度，有延迟，并非 CPU／GPU 温度。Chrome 模式无法读取。</p>
      <div class="az-presets"><button type="button" data-preset="cool">节能</button><button type="button" data-preset="balanced">均衡</button><button type="button" data-preset="clear">清晰</button></div>
      <label for="az-perf-hud">HUD 大小（含首领血条）<span class="az-value" data-value="hudScale"></span></label><input id="az-perf-hud" type="range" min="50" max="100" step="5" data-setting="hudScale">
      <p class="az-caption">同时影响时钟、技能及其他 HUD。只调整界面大小，不改变 3D 清晰度。</p>
      <label for="az-perf-resolution">3D 分辨率<span class="az-value" data-value="resolution"></span></label><input id="az-perf-resolution" type="range" min="50" max="100" step="5" data-setting="resolution">
      <p class="az-caption">降低实际 3D 渲染像素，界面文字保持清晰。</p>
      <label for="az-perf-distance">景物距离<span class="az-value" data-value="distance"></span></label><input id="az-perf-distance" type="range" min="177" max="420" step="3" data-setting="distance">
      <label for="az-perf-detail">样式与特效<span class="az-value" data-value="detail"></span></label><input id="az-perf-detail" type="range" min="0" max="2" step="1" data-setting="detail">
      <p class="az-caption">同时调整环境、法术、天气和辉光；保留手机轻量着色器。</p>
      <p class="az-note">节能会降低画质和负载，不能保证手机不发热。持续明显发热时请暂停，让手机散热。</p>
      <p class="az-status" role="status" aria-live="polite"></p>
      <button type="button" class="az-restart">重启游戏以应用</button>
      <div class="az-confirm" hidden><p>重启会结束当前对局。请先结束对局并回到主菜单；不会删除账号存档。</p><div class="az-actions"><button type="button" class="az-cancel">暂不重启</button><button type="button" class="az-danger">结束本局并重启</button></div></div>
    </section>`;
    document.body.appendChild(root);
    const find = selector => root.querySelector(selector);
    const floating = find('.az-float'), panel = find('.az-panel'), status = find('.az-status'), confirm = find('.az-confirm');
    // Do not let game window listeners consume gestures intended for these DOM controls.
    for (const type of ['pointerdown','pointermove','pointerup','pointercancel','mousedown','mouseup','click','dblclick','wheel','touchstart','touchmove','touchend','keydown','keyup']) root.addEventListener(type, e => e.stopPropagation(), { passive: type === 'wheel' || type.startsWith('touch') });
    function setOpen(open) {
      // Idempotent frame suspension never toggles the original Escape menu, so
      // opening over an already-paused game cannot accidentally resume it.
      frameGate.setPanelOpen(open);
      root.style.pointerEvents = open ? 'auto' : 'none';
      panel.hidden = !open; floating.hidden = open; floating.setAttribute('aria-expanded', String(open)); confirm.hidden = true;
      if (open) { updateThermal(); updateTouchMode(); find('.az-close').focus({ preventScroll: true }); }
      else document.getElementById('benilla')?.focus({ preventScroll: true });
    }
    function render(message) {
      for (const input of root.querySelectorAll('[data-setting]')) input.value = draft[input.dataset.setting];
      find('[data-value=resolution]').textContent = `${draft.resolution}%`;
      find('[data-value=hudScale]').textContent = `${draft.hudScale === undefined ? 100 : draft.hudScale}%`;
      find('[data-value=distance]').textContent = `${Math.round(draft.distance / 420 * 100)}%`;
      find('[data-value=detail]').textContent = ['简洁 · 33%','标准 · 66%','细致 · 100%'][draft.detail];
      for (const button of root.querySelectorAll('[data-preset]')) button.setAttribute('aria-pressed', String(['resolution','distance','detail'].every(key => draft[key] === PRESETS[button.dataset.preset][key])));
      status.textContent = message || (bootConfigError ? '启动配置写入失败，请检查浏览器存储。' : pendingBoot ? '已保存。下次启动生效；当前对局尚未更改画质。' : appliedThisBoot && equal(draft, startup) ? '本次启动已读取此配置，可在游戏内继续调整。' : hudMigrationApplied ? '已选择 50% 紧凑 HUD；其他画质沿用游戏设置。' : '当前沿用游戏画质设置。选定方案会保存，下次启动生效。');
    }
    function persist(fields = []) {
      for (const field of fields) if (knownFields.includes(field)) pendingFields.add(field);
      draft = normalize(draft);
      try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...draft, pending: pendingFields.size > 0, pendingFields: [...pendingFields] })); saved = { ...draft }; pendingBoot = pendingFields.size > 0; render(); return true; }
      catch (_) { render('无法保存：浏览器存储不可用。配置未保存，也不会重启。'); return false; }
    }
    function updateTouchMode() {
      const touch = window.AzerothAndroidTouch;
      find('.az-touch-controls').hidden = !touch;
      if (!touch) return;
      for (const button of root.querySelectorAll('[data-touch-mode]')) button.setAttribute('aria-pressed', String(button.dataset.touchMode === touch.getMode()));
    }
    for (const button of root.querySelectorAll('[data-touch-mode]')) button.addEventListener('click', () => {
      window.AzerothAndroidTouch?.setMode(button.dataset.touchMode); updateTouchMode(); setOpen(false);
    });
    for (const button of root.querySelectorAll('[data-shortcut]')) button.addEventListener('click', () => {
      window.AzerothAndroidTouch?.sendShortcut(button.dataset.shortcut); setOpen(false);
    });
    window.addEventListener('az-touch-mode', updateTouchMode);
    document.addEventListener('az-touch-mode', updateTouchMode);
    updateTouchMode();
    find('.az-close').addEventListener('click', () => setOpen(false));
    for (const button of root.querySelectorAll('[data-preset]')) button.addEventListener('click', () => { draft = { ...PRESETS[button.dataset.preset], ...(draft.hudScale === undefined ? {} : { hudScale: draft.hudScale }) }; confirm.hidden = true; persist(['resolution','distance','detail']); });
    for (const input of root.querySelectorAll('[data-setting]')) {
      input.addEventListener('input', () => { draft[input.dataset.setting] = Number(input.value); render('松开后保存，下次启动生效。'); });
      input.addEventListener('change', () => { confirm.hidden = true; persist([input.dataset.setting]); });
    }
    find('.az-restart').addEventListener('click', () => { if (persist()) { confirm.hidden = false; find('.az-cancel').focus({ preventScroll: true }); } });
    find('.az-cancel').addEventListener('click', () => { confirm.hidden = true; });
    find('.az-danger').addEventListener('click', () => { if (persist()) location.reload(); });
    panel.addEventListener('keydown', e => { if (e.key === 'Escape') { e.preventDefault(); setOpen(false); } });
    let drag = null, suppressClick = false;
    function place(x, y) {
      x = Math.max(8, Math.min(innerWidth - floating.offsetWidth - 8, x)); y = Math.max(8, Math.min(innerHeight - floating.offsetHeight - 8, y));
      floating.style.left = `${x}px`; floating.style.top = `${y}px`; floating.style.right = 'auto'; return { x, y };
    }
    try { const pos = JSON.parse(localStorage.getItem(POSITION_KEY)); if (pos && Number.isFinite(pos.x) && Number.isFinite(pos.y)) place(pos.x, pos.y); } catch (_) {}
    floating.addEventListener('pointerdown', e => {
      if (!e.isPrimary || e.button !== 0) return;
      const rect = floating.getBoundingClientRect(); drag = { id:e.pointerId, x:e.clientX, y:e.clientY, left:rect.left, top:rect.top, moved:false };
      suppressClick = false; floating.setPointerCapture(e.pointerId);
    });
    floating.addEventListener('pointermove', e => {
      if (!drag || e.pointerId !== drag.id) return; const dx=e.clientX-drag.x, dy=e.clientY-drag.y;
      if (Math.hypot(dx,dy)>6) drag.moved=true; if (drag.moved) place(drag.left+dx,drag.top+dy);
    });
    function endDrag(e) {
      if (!drag || e.pointerId !== drag.id) return; suppressClick=drag.moved;
      if (drag.moved) { const r=floating.getBoundingClientRect(); try {localStorage.setItem(POSITION_KEY,JSON.stringify({x:r.left,y:r.top}));}catch(_){} } drag=null;
    }
    floating.addEventListener('pointerup',endDrag); floating.addEventListener('pointercancel',endDrag);
    floating.addEventListener('click',()=>{if(suppressClick){suppressClick=false;return;}setOpen(true);});
    window.addEventListener('resize',()=>{if(floating.style.left){const r=floating.getBoundingClientRect();place(r.left,r.top);}});
    function updateThermal() {
      let info={}; try {if(typeof window.AndroidHost?.getThermalInfo==='function') info=JSON.parse(window.AndroidHost.getThermalInfo());}catch(_){}
      const value=thermal(info), reading=value.batteryCelsius===null?'--':value.batteryCelsius.toFixed(1);
      floating.querySelector('strong').textContent=value.batteryCelsius===null?'温度不可用':`${reading} °C`;
      find('.az-reading').textContent=`${reading} °C`; find('.az-thermal').textContent=`系统热状态：${value.thermalStatus<0?'不可用':THERMAL_NAMES[value.thermalStatus]}`;
      floating.style.borderColor=value.thermalStatus>=3?'#d38b62':'';
    }
    updateThermal(); setInterval(()=>{if(!document.hidden)updateThermal();},5000);
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)updateThermal();});
    document.addEventListener('az-performance-applied',()=>render()); render();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
