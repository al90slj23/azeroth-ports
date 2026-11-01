// Invoke only the byte-identical official 0.134.0 function25368 in a micro-module.
// Node reads these local research artifacts; the WASM has no host imports/start.
import fs from 'node:fs/promises';
import crypto from 'node:crypto';

const [wasmFile, casesFile, expectedModuleSha, expectedCasesSha] = process.argv.slice(2);
function requireValue(value, message) { if (!value) throw new Error(message); }
function digest(value) { return crypto.createHash('sha256').update(value).digest('hex'); }
function u32(value) { return Number.isInteger(value) && value >= 0 && value <= 0xffffffff; }
const bytes = await fs.readFile(wasmFile);
requireValue(bytes.length < 1024 * 1024 && digest(bytes) === expectedModuleSha, 'Micro-module identity differs');
const source = await fs.readFile(casesFile);
requireValue(source.length < 16 * 1024 * 1024 && digest(source) === expectedCasesSha, 'Corpus identity differs');
const module = await WebAssembly.compile(bytes);
requireValue(WebAssembly.Module.imports(module).length === 0, 'Host imports forbidden');
requireValue(JSON.stringify(WebAssembly.Module.exports(module).map(e => [e.name, e.kind]).sort()) ===
  JSON.stringify([['memory', 'memory'], ['upgrade', 'function']]), 'Unexpected oracle exports');
const instance = await WebAssembly.instantiate(module, {});
const memory = instance.exports.memory;
requireValue(memory.buffer.byteLength === 83 * 65536, 'Unexpected oracle memory budget');
const data = new Uint8Array(memory.buffer), view = new DataView(memory.buffer);
const result = new DataView(new ArrayBuffer(4));
const STATE = 1024, DEFINITION = 2048, IDENTIFIER = 4096;
let count = 0;
for (const line of source.toString('utf8').split('\n')) {
  if (!line) continue;
  requireValue(++count <= 50000, 'Fixture-count budget exceeded');
  const c = JSON.parse(line), s = c.state;
  requireValue(c.id === count - 1 && Number.isInteger(c.kind) && c.kind >= 0 && c.kind <= 4 &&
    Number.isInteger(c.tier) && (c.tier === -1 || (c.tier >= 0 && c.tier <= 5)), 'Invalid fixture domain/order');
  requireValue(Array.isArray(s.counts) && s.counts.length === 5 && s.counts.every(u32) &&
    [s.field16_bits, s.field20_u32, s.field24_bits, s.field28_bits].every(u32) &&
    Number.isInteger(s.definition_kind) && s.definition_kind >= 0 && s.definition_kind <= 255,
    'Invalid fixture state');
  requireValue(typeof s.definition_id_hex === 'string' && /^(?:[a-f0-9]{2})*$/.test(s.definition_id_hex) &&
    s.definition_id_hex.length <= 512, 'Invalid fixture identifier');
  data.fill(0, STATE, STATE + 80);
  data.fill(0, DEFINITION, DEFINITION + 88);
  data.fill(0, IDENTIFIER, IDENTIFIER + 256);
  view.setUint32(STATE, DEFINITION, true);
  view.setUint32(STATE + 16, s.field16_bits, true);
  view.setUint32(STATE + 20, s.field20_u32, true);
  view.setUint32(STATE + 24, s.field24_bits, true);
  view.setUint32(STATE + 28, s.field28_bits, true);
  for (let i = 0; i < 5; i++) view.setUint32(STATE + 32 + 4 * i, s.counts[i], true);
  const identifier = Buffer.from(s.definition_id_hex, 'hex');
  data.set(identifier, IDENTIFIER);
  view.setUint32(DEFINITION + 12, IDENTIFIER, true);
  view.setUint32(DEFINITION + 16, identifier.length, true);
  view.setUint8(DEFINITION + 84, s.definition_kind);
  try {
    const value = instance.exports.upgrade(STATE, c.kind, c.tier);
    result.setFloat32(0, value, true);
    process.stdout.write(JSON.stringify({id: c.id, bits: result.getUint32(0, true)}) + '\n');
  } catch (error) {
    if (!(error instanceof WebAssembly.RuntimeError)) throw error;
    process.stdout.write(JSON.stringify({id: c.id, trapped: true}) + '\n');
  }
}
requireValue(count === 11560, 'Fixture coverage differs');
requireValue(digest(await fs.readFile(wasmFile)) === expectedModuleSha &&
  digest(await fs.readFile(casesFile)) === expectedCasesSha, 'Oracle artifacts changed during execution');
