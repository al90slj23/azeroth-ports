// Host-free execution of original1065 fragments and original25242, not the game.
import fs from 'node:fs/promises';

const [moduleFile, casesFile] = process.argv.slice(2);
const bytes = await fs.readFile(moduleFile);
if (bytes.length > 1024 * 1024) throw new Error('Module budget exceeded');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length) throw new Error('Imports forbidden');
if (WebAssembly.Module.exports(module).map(x => x.name).sort().join(',') !== 'apply,initialize,memory')
  throw new Error('Unexpected exports');
const instance = await WebAssembly.instantiate(module, {});
const data = new Uint8Array(instance.exports.memory.buffer), view = new DataView(data.buffer);
if (data.length !== 82 * 65536) throw new Error('Memory budget differs');
const RECORD = 4096, CONTEXT = 8192, KINDS = 8208, DEFINITION = 12288, IDENTIFIER = 16384;
const source = await fs.readFile(casesFile, 'utf8');
if (source.length > 8 * 1024 * 1024) throw new Error('Fixture budget exceeded');
let count = 0;
for (const line of source.split('\n')) {
  if (!line) continue;
  if (++count > 20000) throw new Error('Fixture count exceeded');
  const c = JSON.parse(line);
  if (!/^[a-f0-9]{160}$/.test(c.record_hex) || !c.kinds.length || c.kinds.length > 20)
    throw new Error('Unexpected fixture');
  data.set(Buffer.from(c.record_hex, 'hex'), RECORD);
  data.fill(0, DEFINITION, DEFINITION + 88);
  const identifier = Buffer.from(c.definition_id_hex, 'hex');
  if (identifier.length > 128) throw new Error('Identifier budget exceeded');
  data.set(identifier, IDENTIFIER);
  view.setUint32(DEFINITION + 12, IDENTIFIER, true);
  view.setUint32(DEFINITION + 16, identifier.length, true);
  view.setUint8(DEFINITION + 84, c.definition_kind);
  data.set(c.kinds, KINDS);
  view.setUint32(CONTEXT, KINDS, true);
  view.setUint32(CONTEXT + 4, c.kinds.length, true);
  view.setUint32(CONTEXT + 8, c.tier, true);
  instance.exports.apply(RECORD, CONTEXT);
  process.stdout.write(JSON.stringify({id: c.id,
    record_hex: Buffer.from(data.slice(RECORD, RECORD + 80)).toString('hex')}) + '\n');
}
data.fill(0xa5, RECORD, RECORD + 80);
instance.exports.initialize(RECORD, DEFINITION);
process.stdout.write(JSON.stringify({initialization_hex:
  Buffer.from(data.slice(RECORD, RECORD + 80)).toString('hex')}) + '\n');
