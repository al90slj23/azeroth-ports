// Full ORIGINAL1065 on invented empty-state fixtures. All host imports throw.
// Research export changes only; no original application/start export is called.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

const [runDirectory, originalPath, fixturesPath] = process.argv.slice(2);
const hash = b => createHash('sha256').update(b).digest('hex');
const manifest = JSON.parse(await fs.readFile(`${runDirectory}/manifest.json`, 'utf8'));
const original = await fs.readFile(originalPath);
const bytes = await fs.readFile(`${runDirectory}/${manifest.module_file}`);
if (hash(original) !== manifest.original_wasm_sha256 || hash(bytes) !== manifest.module_sha256)
  throw new Error('Original/research module identity differs');
function u32(raw, p) {
  let n = 0, shift = 0;
  while (p < raw.length && shift <= 28) {
    const c = raw[p++]; n += (c & 127) * 2 ** shift;
    if (c < 128) return [n, p];
    shift += 7;
  }
  throw new Error('Invalid LEB');
}
function sections(raw) {
  let p = 8; const out = [];
  while (p < raw.length) {
    const start = p, kind = raw[p++], [size, first] = u32(raw, p), end = first + size;
    if (end > raw.length) throw new Error('Invalid section');
    out.push({kind, start, end}); p = end;
  }
  return out;
}
const a = sections(original), b = sections(bytes);
if (a.map(x => x.kind).join() !== b.map(x => x.kind).join() || a.some(x => x.kind === 8))
  throw new Error('Implicit start/section changes forbidden');
for (let i = 0; i < a.length; i++)
  if (a[i].kind !== 7 && !original.subarray(a[i].start, a[i].end).equals(bytes.subarray(b[i].start, b[i].end)))
    throw new Error('Original nonexport bytes changed');
const module = await WebAssembly.compile(bytes), imports = {}, hostCalls = [];
for (const item of WebAssembly.Module.imports(module)) {
  if (item.kind !== 'function') throw new Error('Only denied function imports admitted');
  imports[item.module] ??= {};
  imports[item.module][item.name] = () => {
    hostCalls.push(`${item.module}.${item.name}`);
    throw new Error('Denied original host import');
  };
}
const instance = await WebAssembly.instantiate(module, imports);
const {memory, research_f106495: allocate, research_f1065: choose} = instance.exports;
const alloc = (size, alignment = 4) => {
  const p = allocate(size, alignment) >>> 0;
  if (!p || p + size > memory.buffer.byteLength) throw new Error('Fixture allocation failed');
  new Uint8Array(memory.buffer, p, size).fill(0);
  return p;
};
const fixtures = JSON.parse(await fs.readFile(fixturesPath, 'utf8')), results = [];
let failure = null;
for (const fixture of fixtures) {
  try {
    const state = alloc(5000, 8), owned = alloc(80), candidate = alloc(80);
    const view = () => new DataView(memory.buffer);
    const set = (o, value) => view().setUint32(state + o, value, true);
    view().setUint8(state + 360, 1); view().setUint8(state + 361, 1);
    set(1336, 1); view().setBigUint64(state + 1152, 1n, true);
    view().setUint8(state + 2299, fixture.phase);
    view().setUint8(state + 2297, 0);
    view().setUint8(state + 2294, 0);
    set(2088, 1);
    if (fixture.variant === 'upgrade') {
      new Uint8Array(memory.buffer).set(Buffer.from(fixture.input_hex, 'hex'), owned);
      set(1464, 1); set(1468, owned); set(1472, 1);
      const kinds = alloc(Math.max(1, fixture.kinds.length), 1);
      new Uint8Array(memory.buffer).set(fixture.kinds, kinds);
      view().setUint32(candidate + 60, fixture.kinds.length, true);
      view().setUint32(candidate + 64, kinds, true);
      view().setUint32(candidate + 68, fixture.kinds.length, true);
      view().setUint32(candidate + 72, fixture.owned_index, true);
      view().setUint32(candidate + 76, fixture.tier, true);
    } else if (fixture.variant === 'new') {
      view().setUint32(candidate + 60, 0x80000000, true);
      view().setUint32(candidate + 64, view().getUint32(1719492 + 12, true), true);
      view().setUint32(candidate + 68, view().getUint32(1719492 + 16, true), true);
      view().setUint32(candidate + 76, 0, true);
    } else throw new Error('Unknown fixture variant');
    set(1712, 1); set(1716, candidate); set(1720, 1);
    choose(state, 0);
    const ownedPointer = view().getUint32(state + 1468, true);
    const result = {id: fixture.id,
      record_hex: Buffer.from(new Uint8Array(memory.buffer, ownedPointer, 80)).toString('hex'),
      owned_count: view().getUint32(state + 1472, true),
      phase2299: view().getUint8(state + 2299),
      selection_kind2297: view().getUint8(state + 2297),
      pending2088: view().getUint32(state + 2088, true),
      candidate_count1720: view().getUint32(state + 1720, true)};
    results.push(result);
    if (JSON.stringify(result) !== JSON.stringify(fixture.expected))
      throw new Error(`Original/model mismatch for fixture${fixture.id}`);
  } catch (error) {
    failure = {fixture_id: fixture.id, message: String(error), stack: error.stack}; break;
  }
}
const receipt = {scope: 'Actual full original1065 and original internal callees, invented empty-state fixtures.',
  original_wasm_sha256: manifest.original_wasm_sha256, research_module_sha256: manifest.module_sha256,
  original1065_executed: true, original_allocator_executed: true,
  full_game_started: false, original_start_exports_called: false,
  host_calls: hostCalls, results, failure, fixture_count: fixtures.length,
  qualification: 'This executes a complete original function in the original module with added exports. It does not start the game or prove every1065 state/path.'};
await fs.writeFile(`${runDirectory}/full-card-apply-probe.json`, JSON.stringify(receipt, null, 2) + '\n');
process.stdout.write(JSON.stringify({passed: !failure, fixtures_completed: results.length,
  host_calls: hostCalls.length, receipt: `${runDirectory}/full-card-apply-probe.json`, failure}) + '\n');
if (failure) process.exitCode = 1;
