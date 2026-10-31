// Run only the exported original pure function from a host-free micro-module.
// No game startup, WebSocket, file import, user save, clock or graphics binding.
import fs from 'node:fs/promises';

const [wasmFile, casesFile] = process.argv.slice(2);
const bytes = await fs.readFile(wasmFile);
if (bytes.length > 1024 * 1024) throw new Error('Unexpected micro-module size');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length !== 0) throw new Error('Host imports forbidden');
const exports = WebAssembly.Module.exports(module).map(e => e.name).sort();
if (exports.join(',') !== 'memory,upgrade') throw new Error('Unexpected oracle exports');
const instance = await WebAssembly.instantiate(module, {});
const memory = instance.exports.memory;
if (memory.buffer.byteLength !== 82 * 65536) throw new Error('Unexpected oracle memory budget');
const data = new Uint8Array(memory.buffer);
const view = new DataView(memory.buffer);
const result = new DataView(new ArrayBuffer(4));
const STATE = 1024, DEFINITION = 2048, IDENTIFIER = 4096;
const source = await fs.readFile(casesFile, 'utf8');
if (source.length > 16 * 1024 * 1024) throw new Error('Fixture budget exceeded');
let count = 0;
for (const line of source.split('\n')) {
  if (!line) continue;
  if (++count > 50000) throw new Error('Fixture-count budget exceeded');
  const c = JSON.parse(line), s = c.state;
  data.fill(0, STATE, STATE + 80);
  data.fill(0, DEFINITION, DEFINITION + 88);
  view.setUint32(STATE, DEFINITION, true);
  view.setUint32(STATE + 16, s.field16_bits >>> 0, true);
  view.setUint32(STATE + 20, s.field20_u32 >>> 0, true);
  view.setUint32(STATE + 24, s.field24_bits >>> 0, true);
  view.setUint32(STATE + 28, s.field28_bits >>> 0, true);
  for (let i = 0; i < 5; i++) view.setUint32(STATE + 32 + 4 * i, s.counts[i] >>> 0, true);
  if (!/^(?:[a-f0-9]{2})*$/.test(s.definition_id_hex) || s.definition_id_hex.length > 512)
    throw new Error('Invalid local fixture identifier');
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
