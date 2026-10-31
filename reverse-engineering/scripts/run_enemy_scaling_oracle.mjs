// Only the two pure arithmetic exports in an isolated, host-free micro-WASM.
import fs from 'node:fs/promises';

const [wasmFile, casesFile] = process.argv.slice(2);
const bytes = await fs.readFile(wasmFile);
if (bytes.length > 1024) throw new Error('Micro-module size budget exceeded');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length !== 0) throw new Error('Imports forbidden');
const exports = WebAssembly.Module.exports(module);
if (exports.map(e => `${e.name}:${e.kind}`).sort().join(',') !== 'elite_growth:function,normal_growth:function')
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
  if (!['elite_growth', 'normal_growth'].includes(c.export)) throw new Error('Unknown export');
  for (const bits of [c.time_bits, c.zone_bits])
    if (!Number.isInteger(bits) || bits < 0 || bits > 0xffffffff) throw new Error('Invalid input bits');
  const result = instance.exports[c.export](toNumber(c.time_bits), toNumber(c.zone_bits));
  value.setFloat32(0, result, true);
  process.stdout.write(JSON.stringify({id: c.id, bits: value.getUint32(0, true)}) + '\n');
}
