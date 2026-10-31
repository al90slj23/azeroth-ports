// Only original85387 executes. Threshold/XP/guard modes recompose the selected
// original3231 instructions in JS with per-operation f32 rounding. Neither
// original3231 nor13409, nor their excluded side effects, are executed.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

const [wasmFile, casesFile, manifestFile] = process.argv.slice(2);
const bytes = await fs.readFile(wasmFile);
const manifest = JSON.parse(await fs.readFile(manifestFile, 'utf8'));
const hash = raw => createHash('sha256').update(raw).digest('hex');
const bodyHash = '3f9127d30eefb0c9bad49101460ed45df1f6069e63c42d87e351ffbb67151c36';
if (bytes.length > 1024 || hash(bytes) !== manifest.module_sha256
    || manifest.body_sha256 !== bodyHash || manifest.original_function_index !== 85387
    || manifest.original_wasm_sha256 !== '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c')
  throw new Error('Micro-module/source identity differs');
function leb(position) {
  let value = 0, shift = 0;
  while (position < bytes.length && shift <= 28) {
    const byte = bytes[position++]; value += (byte & 127) * 2 ** shift;
    if (byte < 128) return [value, position];
    shift += 7;
  }
  throw new Error('Malformed unsigned LEB');
}
if (bytes.subarray(0, 8).toString('hex') !== '0061736d01000000') throw new Error('Invalid WASM header');
let p = 8, bodyCount = 0;
const sections = [];
while (p < bytes.length) {
  const kind = bytes[p++], [size, begin] = leb(p), end = begin + size;
  if (end > bytes.length) throw new Error('Invalid section boundary');
  sections.push(kind);
  if (kind === 10) {
    const [count, q] = leb(begin), [length, start] = leb(q);
    if (count !== 1 || length !== 68 || start + length !== end || hash(bytes.subarray(start, end)) !== bodyHash)
      throw new Error('Original body changed or extra code found');
    bodyCount = count;
  }
  p = end;
}
if (p !== bytes.length || sections.join(',') !== '1,3,7,10' || bodyCount !== 1)
  throw new Error('Only types/functions/exports/code sections admitted');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length !== 0) throw new Error('Imports forbidden');
if (WebAssembly.Module.exports(module).map(e => `${e.name}:${e.kind}`).join(',') !== 'round85387:function')
  throw new Error('Unexpected oracle exports');
const instance = await WebAssembly.instantiate(module, {});
const view = new DataView(new ArrayBuffer(4));
const toNumber = bits => {view.setUint32(0, bits, true); return view.getFloat32(0, true);};
const toBits = value => {view.setFloat32(0, value, true); return view.getUint32(0, true);};
const uint = value => {
  if (!Number.isInteger(value) || value < 0 || value > 0xffffffff) throw new Error('Expected u32');
  return value;
};
const byte = value => {uint(value); if (value > 255) throw new Error('Expected byte'); return value;};
const round = value => instance.exports.round85387(value);
const sat = value => Number.isNaN(value) || value <= 0 ? 0 : value >= 0xffffffff ? 0xffffffff : Math.trunc(value);
function threshold(level) {
  uint(level);
  const n = Math.fround(level - Number(level !== 0));
  const linear = Math.fround(Math.fround(n * Math.fround(4)) + Math.fround(5));
  const quadratic = Math.fround(Math.fround(n * Math.fround(.35)) * n);
  return round(Math.fround(linear + quadratic));
}
const source = await fs.readFile(casesFile, 'utf8');
if (source.length > 16 * 1024 * 1024) throw new Error('Fixture size budget exceeded');
let count = 0;
for (const line of source.split('\n')) {
  if (!line) continue;
  if (++count > 60000) throw new Error('Fixture count budget exceeded');
  const c = JSON.parse(line);
  if (c.id !== count - 1) throw new Error('Case order differs');
  let result;
  if (c.mode === 'helper') {
    result = {bits: toBits(round(toNumber(uint(c.input_bits))))};
  } else if (c.mode === 'threshold_composition') {
    const value = threshold(c.level);
    result = {bits: toBits(value), threshold: sat(value)};
  } else if (c.mode === 'xp_projection_composition') {
    let level = uint(c.state.level), xp = (uint(c.state.xp) + uint(c.amount)) >>> 0;
    let pending = uint(c.state.pending_upgrades);
    const spent = [];
    while (level <= 98) {
      const needed = sat(threshold(level));
      if (xp < needed) break;
      ++level; xp = (xp - needed) >>> 0; pending = (pending + 1) >>> 0; spent.push(needed);
      if (spent.length > 99) throw new Error('Unexpected upgrade-loop length');
    }
    result = {state: {level, xp, pending_upgrades: pending}, levels_gained: spent.length, thresholds_spent: spent};
  } else if (c.mode === 'card_guard_composition') {
    const pending = uint(c.pending_upgrades), phase = byte(c.phase2299), flags = byte(c.flags2288);
    const gate = byte(c.gate2284), ready = byte(c.flags2285);
    result = {eligible: pending !== 0 && phase === 1 && !(flags & 1) && (gate !== 1 || !!(ready & 1))};
  } else {
    throw new Error('Unknown comparison mode');
  }
  process.stdout.write(JSON.stringify({id: c.id, ...result}) + '\n');
}
