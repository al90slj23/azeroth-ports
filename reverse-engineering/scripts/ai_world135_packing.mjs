// Component query-equivalent world layout from independently parsed assets.
// No original memory/snapshot input; unconsumed metadata is synthetic fixture0.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const digest = raw => createHash('sha256').update(raw).digest('hex');
const cache = new Map();
export async function packAiWorld135(host, description) {
  const {memory, allocate} = host, d = () => new DataView(memory.buffer), bytes = () => new Uint8Array(memory.buffer);
  const w = (p, v) => d().setUint32(p, v >>> 0, true);
  const R = allocate(124), arrays = [];
  w(R, 1); w(R + 4, 1); w(R + 12, 4); w(R + 24, 4);
  w(R + 32, 0xffffffff); w(R + 56, 0xffffffff); w(R + 92, 0xffffffff);
  w(R + 116, description.fallback_height_bits); bytes()[R + 120] = description.flat_height_bits === null ? 0 : 1;
  if (description.flat_height_bits !== null) w(R + 116, description.flat_height_bits);
  const copy = (raw, align = 8) => {const p = allocate(Math.max(1, raw.length), align); bytes().set(raw, p); arrays.push({p, bytes:raw.length, sha256:digest(raw)}); return p;};
  const raster = (raw, tag, pointer, length, origin, width, xy, n) => {
    const p = copy(raw); w(R + tag, 0); w(R + pointer, p); w(R + length, raw.length / 4);
    w(R + origin, xy[0]); w(R + origin + 4, xy[1]); w(R + width, n);
  };
  if (description.kind === 'independently_parsed451_asset_world_inputs') {
    const input = {};
    for (const [name, entry] of Object.entries(description.artifacts)) {
      const key = `${entry.path}\0${entry.sha256}`; let raw = cache.get(key);
      if (!raw) {raw = await fs.readFile(entry.path); if (raw.length > 5 * 1024 * 1024 || digest(raw) !== entry.sha256) throw Error('Independent asset artifact identity'); cache.set(key, raw);}
      input[name] = raw;
    }
    const raw = input['terrain-query.bin'], view = new DataView(raw.buffer, raw.byteOffset, raw.byteLength); let offset = 0;
    const get = () => {const value = view.getUint32(offset, true); offset += 4; return value;};
    const count = get(); if (count !== 9) throw Error('Default terrain tile domain');
    const T = allocate(count * 36), B = allocate(count * 16);
    w(R + 8, count); w(R + 12, T); w(R + 16, count); w(R + 20, count); w(R + 24, B); w(R + 28, count);
    for (let tile = 0; tile < count; tile++) {
      for (let j = 0; j < 4; j++) w(B + tile * 16 + j * 4, get());
      const n = get(); if (n !== 256) throw Error('Canonical terrain chunks');
      const C = allocate(n * 264), V = allocate(n * 145 * 12);
      w(T + tile * 36, n); w(T + tile * 36 + 4, C); w(T + tile * 36 + 8, n);
      for (let chunk = 0; chunk < n; chunk++) {
        const holes = view.getUint16(offset, true); offset += 2; const vertices = get(); if (vertices !== 145) throw Error('Canonical145 vertices');
        const q = C + chunk * 264, v = V + chunk * 145 * 12;
        w(q, 145); w(q + 4, v); w(q + 8, 145); d().setUint16(q + 260, holes, true);
        bytes().set(raw.subarray(offset, offset + 145 * 12), v); offset += 145 * 12;
      }
      arrays.push({p:C, bytes:n * 264, sha256:digest(bytes().subarray(C, C + n * 264))},
        {p:V, bytes:n * 145 * 12, sha256:digest(bytes().subarray(V, V + n * 145 * 12))});
    }
    if (offset !== raw.length) throw Error('Terrain binary trailing/missing bytes');
    const nav = input['navigation.bin'], p = copy(nav, 1);
    w(R + 32, nav.length); w(R + 36, p); w(R + 40, nav.length); w(R + 44, description.origin_xy_bits[0]); w(R + 48, description.origin_xy_bits[1]); w(R + 52, description.nav_width);
    raster(input['secondary-height.u32le'], 92, 96, 100, 104, 112, description.origin_xy_bits, description.secondary_width);
  } else if (description.kind === 'controlled_query_world') {
    const nav = description.nav;
    if (nav) {const raw = Buffer.from(nav.hex, 'hex'), p = copy(raw, 1); w(R + 32, raw.length); w(R + 36, p); w(R + 40, raw.length); w(R + 44, nav.origin_xy_bits[0]); w(R + 48, nav.origin_xy_bits[1]); w(R + 52, nav.width);}
    const primary = description.primary;
    if (primary) {const raw = Buffer.alloc(primary.values_bits.length * 4); primary.values_bits.forEach((v, i) => raw.writeUInt32LE(v, i * 4)); raster(raw, 56, 72, 76, 80, 88, primary.origin_xy_bits, primary.width);}
  } else throw Error('Explicit world input kind required');
  return {R, arrays, verify() {for (const entry of arrays) if (digest(bytes().subarray(entry.p, entry.p + entry.bytes)) !== entry.sha256) throw Error('Original mutated independent geometry arrays');}};
}
