// Controlled full-original1573 execution with synthetic state. All host calls
// throw. Neither original start export is called. No game UI/network/save APIs.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

const [runDirectory, originalPath] = process.argv.slice(2);
const hash = b => createHash('sha256').update(b).digest('hex');
const originalSHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c';
const manifest = JSON.parse(await fs.readFile(`${runDirectory}/manifest.json`, 'utf8'));
const original = await fs.readFile(originalPath);
const bytes = await fs.readFile(`${runDirectory}/${manifest.module_file}`);
if (hash(original) !== originalSHA || manifest.original_wasm_sha256 !== originalSHA
    || hash(bytes) !== manifest.module_sha256 || bytes.length > 92_000_000)
  throw new Error('Original/research module identity differs');
function readU32(raw, p) {
  let n = 0, shift = 0;
  while (p < raw.length && shift <= 28) {
    const c = raw[p++]; n += (c & 127) * 2 ** shift;
    if (c < 128) return [n, p];
    shift += 7;
  }
  throw new Error('Malformed LEB');
}
function sections(raw) {
  if (raw.subarray(0, 8).toString('hex') !== '0061736d01000000') throw new Error('Bad header');
  let p = 8; const result = [];
  while (p < raw.length) {
    const start = p, kind = raw[p++], [size, first] = readU32(raw, p), end = first + size;
    if (end > raw.length) throw new Error('Bad section bound');
    result.push({kind, start, first, end}); p = end;
  }
  return result;
}
const oldSections = sections(original), newSections = sections(bytes);
if (oldSections.map(s => s.kind).join() !== newSections.map(s => s.kind).join()
    || oldSections.some(s => s.kind === 8)) throw new Error('Implicit start or section changes forbidden');
for (let i = 0; i < oldSections.length; ++i) {
  const a = oldSections[i], b = newSections[i];
  if (a.kind !== 7 && !original.subarray(a.start, a.end).equals(bytes.subarray(b.start, b.end)))
    throw new Error(`Changed original nonexport section${a.kind}`);
}
const module = await WebAssembly.compile(bytes);
const importObject = {}, hostCalls = [];
for (const item of WebAssembly.Module.imports(module)) {
  if (item.kind !== 'function') throw new Error('Nonfunction host import forbidden');
  importObject[item.module] ??= {};
  importObject[item.module][item.name] = () => {
    hostCalls.push(`${item.module}.${item.name}`);
    throw new Error('Denied original host import');
  };
}
const instance = await WebAssembly.instantiate(module, importObject);
const {memory, research_f1573: recalculate, research_f106495: allocate} = instance.exports;
if (!(memory instanceof WebAssembly.Memory) || typeof recalculate !== 'function' || typeof allocate !== 'function')
  throw new Error('Research exports missing');
const pointer = allocate(5000, 8) >>> 0;
if (pointer === 0 || pointer + 5000 > memory.buffer.byteLength) throw new Error('Synthetic allocation failed');
new Uint8Array(memory.buffer, pointer, 5000).fill(0);
let view = new DataView(memory.buffer);
view.setUint8(pointer + 360, 1); // Original fallback warrior selector.
view.setUint8(pointer + 361, 1); // Original fallback human selector.
view.setUint32(pointer + 1336, 1, true);
view.setUint8(pointer + 2299, 1);
view.setBigUint64(pointer + 1152, 1n, true);
recalculate(pointer);
view = new DataView(memory.buffer);
const outputs = {};
for (let offset = 1176; offset <= 1260; offset += 4)
  outputs[offset] = view.getUint32(pointer + offset, true);
outputs[1344] = view.getUint32(pointer + 1344, true);
const receipt = {scope: 'Actual original1573 and original internal callees in full research module, synthetic empty state. No start exports or host functions called.',
  original_sha256: originalSHA, research_module_sha256: hash(bytes),
  original_function1573_executed: true, original_allocator_executed: true,
  full_game_started: false, denied_host_imports: WebAssembly.Module.imports(module).length,
  actual_host_calls: hostCalls, synthetic_state_pointer: pointer,
  memory_bytes: memory.buffer.byteLength, output_bits_by_offset: outputs,
  packet_queue_count1696: view.getUint32(pointer + 1696, true),
  field_map_root2188: view.getUint32(pointer + 2188, true)};
if (hostCalls.length) throw new Error('A host call was attempted');
await fs.writeFile(`${runDirectory}/full-stats-probe.json`, JSON.stringify(receipt, null, 2) + '\n');
process.stdout.write(JSON.stringify({passed: true, original1573_executed: true,
  host_calls: hostCalls.length, memory_bytes: memory.buffer.byteLength,
  receipt: `${runDirectory}/full-stats-probe.json`}) + '\n');
