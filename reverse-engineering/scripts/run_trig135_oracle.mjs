// Full original11428/11503; no libm replacement or application start.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory, file] = process.argv.slice(2);
const prepared = await prepareFull135(directory, ['sin_angle', 'cos_angle']);
const text = await fs.readFile(file, 'utf8');
if (Buffer.byteLength(text) > 8 * 1024 * 1024) throw Error('Fixture byte budget');
const rows = text.trim().split('\n').map(JSON.parse);
if (!rows.length || rows.length > 20000) throw Error('Fixture count budget');
const host = await prepared.fresh(), d = new DataView(new ArrayBuffer(4));
for (let i = 0; i < rows.length; ++i) {
  if (rows[i].id !== i) throw Error('Case order');
  d.setUint32(0, rows[i].bits, true); const angle = d.getFloat32(0, true);
  d.setFloat32(0, host.roles.sin_angle(angle), true); const sin_bits = d.getUint32(0, true);
  d.setFloat32(0, host.roles.cos_angle(angle), true); const cos_bits = d.getUint32(0, true);
  if (host.hostCalls.length) throw Error('Original host API attempted');
  process.stdout.write(JSON.stringify({id: i, sin_bits, cos_bits}) + '\n');
}
await fs.writeFile(`${directory}/trig135-runtime.json`, JSON.stringify({cases: rows.length,
  original_entries: [11428, 11503], original_entry_calls: rows.length * 2, original_internal_callees_preserved: true,
  host_calls: 0, denied_host_imports: 878, max_memory_bytes: host.memory.buffer.byteLength,
  application_start_called: false, full_game_started: false, user_saves_accessed: false,
  network_used: false, node: process.version}, null, 2) + '\n');
