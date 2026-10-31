// Execute only original35684 in a no-import, no-start single-body micro-WASM.
// radius_composition applies the extracted934 callsite in JS/f32 around that
// helper. It never executes the original934 or the complete game.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

const [wasmFile, casesFile, manifestFile] = process.argv.slice(2);
const bytes = await fs.readFile(wasmFile);
const manifest = JSON.parse(await fs.readFile(manifestFile, 'utf8'));
const hash = buffer => createHash('sha256').update(buffer).digest('hex');
const bodyHash = '31ccd3fd72d9691629a6df855cf68a38be6fc19ca2679165bf2fa0e368a63162';
if (bytes.length > 1024 || hash(bytes) !== manifest.module_sha256)
  throw new Error('Micro-module identity/size differs');
if (manifest.original_wasm_sha256 !== '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
    || manifest.body_sha256 !== bodyHash || manifest.original_function_index !== 35684)
  throw new Error('Original source identity differs');
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
  throw new Error('Invalid micro-module header');
const sections = [];
let p = 8, bodyCount = 0;
while (p < bytes.length) {
  const kind = bytes[p++];
  const [size, begin] = leb(p), end = begin + size;
  if (end > bytes.length) throw new Error('Invalid section bounds');
  sections.push(kind);
  if (kind === 10) {
    const [count, q] = leb(begin);
    if (count !== 1) throw new Error('Only one body permitted');
    const [length, start] = leb(q);
    if (length !== 364 || start + length !== end || hash(bytes.subarray(start, end)) !== bodyHash)
      throw new Error('Original body changed or unexpected extra code');
    bodyCount = count;
  }
  if (kind === 5 && bytes.subarray(begin, end).toString('hex') !== '01010101')
    throw new Error('Memory must be exactly one fixed page');
  if (kind === 6 && bytes.subarray(begin, end).toString('hex') !== '017f004180080b')
    throw new Error('Global0 must be fixed immutable i32(1024)');
  p = end;
}
if (p !== bytes.length || sections.join(',') !== '1,3,5,6,7,10' || bodyCount !== 1)
  throw new Error('Unexpected sections; imports/start/data/table forbidden');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length !== 0) throw new Error('Imports forbidden');
const exports = WebAssembly.Module.exports(module);
if (exports.map(e => `${e.name}:${e.kind}`).join(',') !== 'log1p_helper:function')
  throw new Error('Unexpected oracle exports');
const instance = await WebAssembly.instantiate(module, {});
const value = new DataView(new ArrayBuffer(4));
const toNumber = bits => { value.setUint32(0, bits, true); return value.getFloat32(0, true); };
const source = await fs.readFile(casesFile, 'utf8');
if (source.length > 16 * 1024 * 1024) throw new Error('Fixture size budget exceeded');
let count = 0;
for (const line of source.split('\n')) {
  if (!line) continue;
  if (++count > 50000) throw new Error('Fixture count budget exceeded');
  const c = JSON.parse(line);
  if (!['helper', 'radius_composition'].includes(c.mode)) throw new Error('Unknown comparison mode');
  if (!Number.isInteger(c.input_bits) || c.input_bits < 0 || c.input_bits > 0xffffffff)
    throw new Error('Invalid input bits');
  if (c.id !== count - 1) throw new Error('Case order differs');
  const input = toNumber(c.input_bits);
  let result;
  if (c.mode === 'helper') {
    result = instance.exports.log1p_helper(input);
  } else if (!(input <= 70)) {
    const scaled = Math.fround(Math.fround(input + Math.fround(-70)) / Math.fround(10));
    const compressed = instance.exports.log1p_helper(scaled);
    result = Math.fround(Math.fround(compressed * Math.fround(10)) + Math.fround(70));
  } else {
    result = input;
  }
  value.setFloat32(0, result, true);
  process.stdout.write(JSON.stringify({id: c.id, bits: value.getUint32(0, true)}) + '\n');
}
