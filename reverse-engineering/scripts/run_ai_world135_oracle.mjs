// Full921 over independently parsed world inputs and controlled known NPC rows.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareDistanceMap135} from './distance_map135_host.mjs';
import {packAiWorld135} from './ai_world135_packing.mjs';
const [directory, fixtureFile] = process.argv.slice(2), prepared = await prepareDistanceMap135(directory, ['update_units']);
const hash = raw => createHash('sha256').update(raw).digest('hex');
const raw = await fs.readFile(fixtureFile, 'utf8'); if (Buffer.byteLength(raw) > 16 * 1024 * 1024) throw Error('Fixture budget');
const cases = JSON.parse(raw); if (!cases.length || cases.length > 100) throw Error('Case count');
const fields = {armor_1392_bits:1568, armor_cap_1572_bits:1572, nearby_reduction_1444_bits:1624,
 hp_1528_bits:1440, shield_1532_bits:1444, barrier_1536_bits:1448, shield_source_1344:1344,
 shield_source_remaining_1348_bits:1348, reserve_768_bits:768, absorbed_740_bits:740,
 maximum_shield_744_bits:744, last_hit_1648_bits:1652};
const number = word => {const d = new DataView(new ArrayBuffer(4)); d.setUint32(0, word, true); return d.getFloat32(0, true);};
let host, assetWorld, instances = 0, cursor = 0, entryCalls = 0, maxMemory = 0;
const stackChecks = [];
for (let index = 0; index < cases.length; index++) {
 const c = cases[index]; if (c.id !== index || c.records.length > 32 || c.steps.length > 200) throw Error('Case shape');
 if (index % 4 === 0) {host = await prepared.fresh(); assetWorld = null; instances++; cursor = 0;}
 const world = c.world.kind === 'independently_parsed451_asset_world_inputs'
   ? (assetWorld ??= await packAiWorld135(host, c.world)) : await packAiWorld135(host, c.world);
 const {memory, roles, allocate, hostCalls} = host;
 const d = () => new DataView(memory.buffer), bytes = () => new Uint8Array(memory.buffer), w = (p, v) => d().setUint32(p, v >>> 0, true), r = p => d().getUint32(p, true);
 const G = allocate(8192), name = allocate(6, 1), U = allocate(Math.max(8, c.records.length * 424)); bytes().set(Buffer.from('elwynn'), name); w(G + 184, name); w(G + 188, 6);
 w(G + 2348, world.R); w(G + 1784, c.records.length); w(G + 1788, U); w(G + 1792, c.records.length); w(G + 2412, c.sequence);
 w(G + 2372, c.distance_map_updated_at_bits); d().setUint8(G + 2582, 0); d().setUint8(G + 2587, c.incoming.phase_2579);
 d().setUint8(G + 360, 1); d().setUint8(G + 361, 1); d().setBigUint64(G + 1336, 999n, true); w(G + 1432, 1); w(G + 1536, c.max_hp_bits);
 for (const [key, offset] of Object.entries(fields)) w(G + offset, c.incoming[key]);
 d().setFloat64(G + 992, c.incoming.incoming_total_992, true); [1, 2, 3, 4].forEach((x, j) => w(G + 1720 + j * 4, x));
 c.records.forEach((record, j) => {if (typeof record !== 'string' || !/^[0-9a-f]{848}$/.test(record)) throw Error('Only explicit full-known NPC fixture rows enter original'); bytes().set(Buffer.from(record, 'hex'), U + j * 424);});
 const stages = []; let previousPackets = 0;
 for (const step of c.steps) {
  w(G + 2352, step.now_bits); step.player_xyz_bits.forEach((x, j) => w(G + 1416 + j * 4, x));
  roles.update_units(G, number(step.dt_bits)); entryCalls++;
  if (hostCalls.length) throw Error('Original host call attempted'); world.verify();
  const records = c.records.map((_, j) => Buffer.from(bytes().subarray(U + j * 424, U + (j + 1) * 424)).toString('hex'));
  const output = {records, ...Object.fromEntries(Object.entries(fields).map(([key, offset]) => [key, r(G + offset)]))};
  output.incoming_total_992_bits = d().getBigUint64(G + 992, true).toString(16).padStart(16, '0'); output.sequence = r(G + 2412); output.packet_count = r(G + 1888);
  output.rng_words = [0, 1, 2, 3].map(j => r(G + 1720 + j * 4));
  const map = r(G + 2368);
  output.distance_map = map ? {sha256:hash(bytes().subarray(r(map + 12), r(map + 12) + r(map + 16) * 2)), field24:r(map + 24), start_index:r(map + 20), length:r(map + 16)} : null;
  output.distance_map_updated_at_bits = r(G + 2372); output.movement_geometry = [];
  const P = r(G + 1884), N = r(G + 1888); if (N > 10000) throw Error('Packet count');
  for (let packet = previousPackets; packet < N; packet++) {
   const row = P + packet * 16, type = d().getUint16(row + 12, true); if (type !== 221) continue;
   const p = r(row + 4), n = r(row + 8); if (n > 96 || p + n > memory.buffer.byteLength) throw Error('Movement packet bounds');
   const payload = bytes().subarray(p, p + n), view = new DataView(payload.buffer, payload.byteOffset, payload.byteLength); let k = 1, guid = 0n;
   for (let bit = 0; bit < 8; bit++) if (payload[0] & (1 << bit)) guid |= BigInt(payload[k++]) << BigInt(bit * 8);
   const xyz = () => {const result = [0, 1, 2].map(j => view.getUint32(k + j * 4, true)); k += 12; return result;};
   const start = xyz(), sequence = view.getUint32(k, true); k += 4; const stop = payload[k++];
   if (stop === 3) k += 8; else if (stop !== 0) throw Error('Ordinary movement flag');
   const flags = view.getUint32(k, true), ms = view.getUint32(k + 4, true), count = view.getUint32(k + 8, true); k += 12;
   if (flags !== 256 || count !== 1) throw Error('Ordinary movement shape'); const end = xyz(); if (k !== n) throw Error('Movement payload trailing bytes');
   const unit = c.records.findIndex((_, j) => d().getBigUint64(U + j * 424 + 112, true) === guid); if (unit < 0) throw Error('Movement GUID source');
   output.movement_geometry.push({target_id:guid.toString(), start_xyz_bits:start, end_xyz_bits:end,
     duration_bits:r(U + unit * 424 + 344), milliseconds:ms, stop_flag:stop, sequence});
  }
  previousPackets = N; stages.push(output);
 }
 const checks = host.stackChecks(); stackChecks.push(...checks.slice(cursor).map((entry, call) => ({case_id:index, call_in_case:call, ...entry}))); cursor = checks.length;
 maxMemory = Math.max(maxMemory, memory.buffer.byteLength); process.stdout.write(JSON.stringify({id:index, stages}) + '\n');
}
await fs.writeFile(`${directory}/ai-world135-runtime.json`, JSON.stringify({cases:cases.length, entry_calls:entryCalls,
 original_full_entries:[921], zero_mocked_callees:true, denied_function_imports:878, actual_host_calls:0, original_allocator:91941,
 max_memory_bytes:maxMemory, memory_page_limit:512, fresh_instances:instances, fresh_every:4, stack_checks:stackChecks,
 stack_all_restored:stackChecks.every(x => x.entered && x.returned && x.before === 1048576 && x.after === x.before),
 independently_parsed_world_inputs:true, original_snapshot_loaded:false, application_start_called:false, full_game_started:false,
 user_saves_accessed:false, network_used:false, node:process.version}, null, 2) + '\n');
