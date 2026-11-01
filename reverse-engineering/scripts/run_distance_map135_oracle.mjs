// Complete original921, zero unit vector, explicit nav/map fixture only.
import fs from 'node:fs/promises';
import {prepareDistanceMap135} from './distance_map135_host.mjs';
const [directory, fixtureFile] = process.argv.slice(2);
const prepared = await prepareDistanceMap135(directory, ['update_units']);
const raw = await fs.readFile(fixtureFile, 'utf8');
if (Buffer.byteLength(raw) > 16 * 1024 * 1024) throw Error('Fixture byte budget');
const cases = raw.trim().split('\n').map(JSON.parse);
if (!cases.length || cases.length > 500) throw Error('Fixture count budget');
let host, instances = 0, cursor = 0, maxMemory = 0, calls = 0;
const stackChecks = [];
for (let index = 0; index < cases.length; index++) {
  if (index % 8 === 0) {host = await prepared.fresh(); instances++; cursor = 0;}
  const c = cases[index];
  if (c.id !== index || c.ops.length > 32) throw Error('Case identity/budget');
  const {memory, roles, allocate, hostCalls} = host;
  const d = () => new DataView(memory.buffer), b = () => new Uint8Array(memory.buffer);
  const w = (p, x) => d().setUint32(p, x >>> 0, true), r = p => d().getUint32(p, true);
  const G = allocate(8192), W = allocate(124), name = allocate(6, 1);
  b().set(Buffer.from('elwynn'), name); w(G + 184, name); w(G + 188, 6);
  w(G + 2348, W); w(W, 1); w(W + 4, 1); w(W + 32, 0xffffffff); w(W + 56, 0xffffffff); w(W + 120, 0x3f800000);
  w(G + 1788, 8); w(G + 2372, c.updated_at_bits);
  if (c.nav !== null) {
    const grid = Buffer.from(c.nav.hex, 'hex');
    if (grid.length > 1048576 || c.nav.width > 1024 || c.nav.hex.length !== grid.length * 2) throw Error('Grid budget');
    const values = allocate(Math.max(1, grid.length), 1); b().set(grid, values);
    w(W + 32, grid.length); w(W + 36, values); w(W + 40, grid.length);
    w(W + 44, c.nav.origin_xy_bits[0]); w(W + 48, c.nav.origin_xy_bits[1]); w(W + 52, c.nav.width);
  }
  if (c.previous !== null) {
    const old = c.previous, n = old.values_u16.length;
    if (!n || n > 1048576) throw Error('Old map budget');
    const values = allocate(n * 2, 2), rc = allocate(28, 4);
    old.values_u16.forEach((x, i) => {if (!Number.isInteger(x) || x < 0 || x > 65535) throw Error('u16'); d().setUint16(values + i * 2, x, true);});
    [1, 1, n, values, n, old.start_index, old.field24].forEach((x, i) => w(rc + i * 4, x)); w(G + 2368, rc);
  }
  const stages = [];
  for (const op of c.ops) {
    w(G + 1416, op.player_xy_bits[0]); w(G + 1420, op.player_xy_bits[1]); w(G + 2352, op.now_bits);
    roles.update_units(G, 0.01); calls++;
    if (hostCalls.length) throw Error('Host call attempted');
    const rc = r(G + 2368); let map = null, rcCounts = null;
    if (rc) {
      const n = r(rc + 16), values = r(rc + 12);
      if (n > 1048576 || values + n * 2 > memory.buffer.byteLength) throw Error('Map result budget');
      map = {values_u16:Array.from({length:n}, (_, i) => d().getUint16(values + i * 2, true)), field24:r(rc + 24), start_index:r(rc + 20)};
      rcCounts = [r(rc), r(rc + 4)];
    }
    stages.push({distance_map:map, updated_at_bits:r(G + 2372), world_refcount:r(W), map_refcounts:rcCounts,
      unit_count:r(G + 1792), packet_count:r(G + 1888)});
  }
  const checks = host.stackChecks();
  stackChecks.push(...checks.slice(cursor).map((entry, call) => ({case_id:index, call_in_case:call, ...entry}))); cursor = checks.length;
  maxMemory = Math.max(maxMemory, memory.buffer.byteLength);
  process.stdout.write(JSON.stringify({id:index, stages}) + '\n');
}
await fs.writeFile(`${directory}/distance-map135-runtime.json`, JSON.stringify({cases:cases.length, entry_calls:calls,
  original_full_entries:[921], original_allocator:91941, unchanged_callees:true, fresh_instances:instances, fresh_every:8,
  max_memory_bytes:maxMemory, memory_page_limit:512, denied_function_imports:878, actual_host_calls:0,
  stack_checks:stackChecks, stack_all_restored:stackChecks.every(x => x.entered && x.returned && x.before === 1048576 && x.after === x.before),
  application_start_called:false, full_game_started:false, user_saves_accessed:false, network_used:false, node:process.version}, null, 2) + '\n');
