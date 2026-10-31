// Run only unchanged32475, with a replacement panic trap and self-made memory.
// Neither the original entropy initializer nor the complete game is loaded.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

const [wasmFile, casesFile, manifestFile] = process.argv.slice(2);
const bytes = await fs.readFile(wasmFile);
const manifest = JSON.parse(await fs.readFile(manifestFile, 'utf8'));
const hash = value => createHash('sha256').update(value).digest('hex');
const bodyHash = '479e1d7542e72a4768f5148d6f2fba741286751e87095bbd90669007e6a2b473';
if (bytes.length > 1024 * 1024 || hash(bytes) !== manifest.module_sha256 ||
    manifest.original_wasm_sha256 !== '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c' ||
    manifest.original_body_sha256 !== bodyHash || manifest.original_function_index !== 32475)
  throw new Error('Pinned original/module identity differs');
function leb(position) {
  let value = 0, shift = 0;
  while (position < bytes.length && shift <= 28) {
    const byte = bytes[position++];
    value += (byte & 127) * 2 ** shift;
    if (byte < 128) return [value, position];
    shift += 7;
  }
  throw new Error('Malformed bounded unsigned LEB');
}
if (bytes.subarray(0, 8).toString('hex') !== '0061736d01000000')
  throw new Error('Unexpected WASM header');
let p = 8;
const sections = [];
const known = {
  1: '0260037f7d7d017d60037f7f7f00',
  5: '01010101',
  7: '020572616e676500dbfd01066d656d6f72790200'
};
while (p < bytes.length) {
  const kind = bytes[p++];
  const [size, begin] = leb(p), end = begin + size;
  if (end > bytes.length) throw new Error('Section outside module');
  sections.push(kind);
  if (kind === 3) {
    const [count, start] = leb(begin);
    if (count !== 121710 || end - start !== count) throw new Error('Wrong declaration count');
    for (let i = 0; i < count; i++)
      if (bytes[start + i] !== (i === 32475 ? 0 : 1)) throw new Error('Unexpected function signature');
  } else if (kind === 10) {
    const [count, start] = leb(begin);
    if (count !== 121710) throw new Error('Wrong code body count');
    let q = start;
    for (let i = 0; i < count; i++) {
      const [length, bodyStart] = leb(q);
      q = bodyStart + length;
      if (q > end) throw new Error('Body outside code section');
      const body = bytes.subarray(bodyStart, q);
      if (i === 32475 ? length !== 399 || hash(body) !== bodyHash : body.toString('hex') !== '00000b')
        throw new Error('Original body differs or unexpected nontrap body');
    }
    if (q !== end) throw new Error('Code section boundary differs');
  } else if (!(kind in known) || bytes.subarray(begin, end).toString('hex') !== known[kind]) {
    throw new Error('Unexpected facility or section payload');
  }
  p = end;
}
if (p !== bytes.length || sections.join(',') !== '1,3,5,7,10')
  throw new Error('Imports/start/table/data/globals forbidden');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length !== 0 ||
    WebAssembly.Module.exports(module).map(x => `${x.name}:${x.kind}`).join(',') !== 'range:function,memory:memory')
  throw new Error('Unexpected imports/exports');
const instance = await WebAssembly.instantiate(module, {});
const memory = new Uint8Array(instance.exports.memory.buffer);
if (memory.length !== 65536) throw new Error('Memory must be one fixed page');
memory.fill(0xa5);
const stateOffset = 256;
const view = new DataView(memory.buffer);
const scalar = new DataView(new ArrayBuffer(4));
const toNumber = bits => {scalar.setUint32(0, bits, true); return scalar.getFloat32(0, true);};
const toBits = value => {scalar.setFloat32(0, value, true); return scalar.getUint32(0, true);};
const getState = () => [0, 1, 2, 3].map(i => view.getUint32(stateOffset + 4 * i, true));
const uint = x => Number.isInteger(x) && x >= 0 && x <= 0xffffffff;
function canary() {
  for (let i = 0; i < memory.length; i++)
    if ((i < stateOffset || i >= stateOffset + 16) && memory[i] !== 0xa5)
      throw new Error(`Memory write outside the synthetic four words at ${i}`);
}
const input = await fs.readFile(casesFile, 'utf8');
if (input.length > 16 * 1024 * 1024) throw new Error('Fixture budget exceeded');
let count = 0;
for (const line of input.split('\n')) {
  if (!line) continue;
  const c = JSON.parse(line);
  if (c.id !== count++ || count > 50000 || !uint(c.low_bits) || !uint(c.high_bits))
    throw new Error('Invalid case identity/bits/count');
  if (c.state !== undefined) {
    if (!Array.isArray(c.state) || c.state.length !== 4 || !c.state.every(uint)) throw new Error('Invalid state');
    c.state.forEach((word, i) => view.setUint32(stateOffset + 4 * i, word, true));
    canary();
  }
  let bits = null, trap = false;
  try {
    bits = toBits(instance.exports.range(stateOffset, toNumber(c.low_bits), toNumber(c.high_bits)));
  } catch (error) {
    if (!(error instanceof WebAssembly.RuntimeError) || !/unreachable/.test(error.message)) throw error;
    trap = true;
  }
  process.stdout.write(JSON.stringify({id: c.id, bits, trap, state: getState()}) + '\n');
}
canary();
if (instance.exports.memory.buffer.byteLength !== 65536) throw new Error('Memory size changed');
process.stderr.write(JSON.stringify({cases: count, whole_memory_canary_passed: true,
  globals: [], full_game_started: false}) + '\n');
