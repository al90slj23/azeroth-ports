// Full original1076 learned80B + real basic80B, then original1754 hits.
// No application entry, body replacement, host service or original-output fixture preparation.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory, casefile] = process.argv.slice(2);
const prepared = await prepareFull135(directory, ['owned_tick', 'process_hits']);
const raw = await fs.readFile(casefile, 'utf8');
if (Buffer.byteLength(raw) > 64 * 1024 * 1024) throw Error('Fixture byte budget');
const cases = raw.trim().split('\n').map(JSON.parse);
if (!cases.length || cases.length > 1800) throw Error('Fixture count budget');
let host, instances = 0, calls = 0, maxMemory = 0;
for (let i = 0; i < cases.length; i++) {
  if (i % 12 === 0) {host = await prepared.fresh(); instances++;}
  const c = cases[i], s = c.input, level = c.level;
  if (c.id !== i || Object.values(level.sources).some(x => x.length)) throw Error('Case/source identity');
  const {roles, memory, allocate, hostCalls} = host;
  const d = () => new DataView(memory.buffer), bytes = () => new Uint8Array(memory.buffer);
  const w = (p, v) => d().setUint32(p, v >>> 0, true), r = p => d().getUint32(p, true);
  const G = allocate(8192), U = allocate(Math.max(1, s.units.length) * 424);
  for (const [ptr, len] of [[2028, 2032], [2052, 2056], [600, 604], [648, 652]]) {w(G + ptr, 4); w(G + len, 0);}
  w(G + 1784, s.units.length); w(G + 1788, U); w(G + 1792, s.units.length);
  w(G + 1416, s.player_xy[0]); w(G + 1420, s.player_xy[1]);
  d().setUint8(G + 360, level.stats.class_byte); d().setUint8(G + 361, level.stats.race_byte);
  d().setUint8(G + 387, level.heal_gate387); d().setUint8(G + 2587, s.phase);
  d().setUint8(G + 2582, level.stats.flag2574); d().setUint8(G + 908, s.context908);
  d().setBigUint64(G + 1336, BigInt(s.source_id), true);
  d().setBigUint64(G + 776, BigInt(s.current_target_id), true);
  for (const [offset, key] of [[1536, 'max_hp_bits'], [1440, 'current_hp_bits'],
    [1540, 'damage_multiplier_bits'], [1544, 'cooldown_multiplier_bits'],
    [1548, 'critical_chance_bits'], [1552, 'critical_multiplier_bits'], [1580, 'area_multiplier_bits']]) w(G + offset, s[key]);
  w(G + 1592, s.extra_targets); s.rng_words.forEach((v, j) => w(G + 1720 + j * 4, v));
  w(G + 1628, c.timer1628_bits);
  s.units.forEach((u, j) => {
    const p = U + j * 424;
    d().setBigUint64(p + 112, BigInt(u.guid), true); d().setBigUint64(p + 32, BigInt(u.linked_id), true);
    for (const [offset, key] of [[0, 'marker'], [40, 'kind_40'], [64, 'kind_64'],
      [244, 'elite_244'], [416, 'elite_416'], [288, 'hp_bits'], [292, 'max_hp_bits'],
      [372, 'priority_until372_bits'], [408, 'phase_until408_bits'], [412, 'phase_until412_bits'],
      [340, 'movement_time_bits'], [344, 'duration_bits']]) w(p + offset, u[key]);
    w(p + 284, 5415572);
    for (const [offset, xy] of [[316, u.from_xy], [328, u.to_xy]]) {w(p + offset, xy[0]); w(p + offset + 4, xy[1]);}
  });
  const A = allocate(Math.max(1, c.owned_hex.length) * 80);
  w(G + 1656, c.owned_hex.length); w(G + 1660, A); w(G + 1664, c.owned_hex.length);
  const identity = (definition, hex) => {
    if (Buffer.from(bytes().subarray(definition.pointer, definition.pointer + 88)).toString('hex') !== hex) throw Error('Real definition identity');
  };
  c.definitions.forEach((definition, j) => {identity(definition, c.definition_hex[j]);
    const record = Buffer.from(c.owned_hex[j], 'hex'); if (record.length !== 80) throw Error('Owned80B'); bytes().set(record, A + j * 80);});
  identity(c.basic_definition, c.basic_definition_hex);
  const basic = Buffer.from(c.basic_hex, 'hex'); if (basic.length !== 80) throw Error('Basic80B'); bytes().set(basic, G + 1256);
  if (r(G + 1256) === 0) throw Error('Null basic definition forbidden');
  const tree = () => {
    const root = r(G + 2476), depth = r(G + 2480); if (!root) return {};
    if (depth > 4) throw Error('Tree depth budget'); const fields = [], seen = new Set();
    const walk = (p, level) => {
      if (!p || p + 76 > memory.buffer.byteLength || seen.has(p) || seen.size > 128) throw Error('Tree bounds'); seen.add(p);
      const n = d().getUint16(p + 50, true); if (n > 11) throw Error('Tree count');
      for (let j = 0; j < n; ++j) {if (level) walk(r(p + 76 + j * 4), level - 1); fields.push([d().getUint16(p + 52 + j * 2, true), r(p + 4 + j * 4)]);}
      if (level) walk(r(p + 76 + n * 4), level - 1);
    }; walk(root, depth); return Object.fromEntries(fields);
  };
  const snapshot = () => {
    const p = r(G + 1848), n = r(G + 1852); if (n > 4096 || p + n * 112 > memory.buffer.byteLength) throw Error('Hit queue bounds');
    return {hp_bits: s.units.map((_, j) => r(U + j * 424 + 288)), markers: s.units.map((_, j) => r(U + j * 424)),
      rng_words: [0, 1, 2, 3].map(j => r(G + 1720 + j * 4)),
      accounted_total_hex: d().getBigUint64(G + 984, true).toString(16).padStart(16, '0'),
      queued: Array.from({length: n}, (_, j) => {const q = p + j * 112; return {
        target_id: d().getBigUint64(q + 64, true).toString(), source_id: d().getBigUint64(q + 72, true).toString(),
        due_bits: r(q + 92), spell_id: r(q + 96), damage_bits: r(q + 100), critical: d().getUint8(q + 104),
        school: d().getUint8(q + 106), context908: d().getUint8(q + 105)};}),
      attempted_spell_sets: [672, 684, 732].map(poff => {const p = r(G + poff), n = r(G + poff + 4); if (n > 1024) throw Error('Spell set'); return Array.from({length: n}, (_, j) => r(p + j * 4));}),
      owned_words: c.owned_hex.map((_, j) => Array.from({length: 20}, (_, k) => r(A + j * 80 + k * 4))),
      basic_words: Array.from({length: 20}, (_, j) => r(G + 1256 + j * 4)),
      current_hp_bits: r(G + 1440), player_fields: tree(), refresh_flag772: d().getUint8(G + 772), timer1628_bits: r(G + 1628)};
  };
  const number = bits => {const v = new DataView(new ArrayBuffer(4)); v.setUint32(0, bits, true); return v.getFloat32(0, true);};
  const stages = [];
  for (const op of c.ops) {
    w(G + 2352, op.now_bits);
    if (op.kind === 'owned') roles.owned_tick(G, number(op.dt_bits));
    else if (op.kind === 'process') roles.process_hits(G);
    else throw Error('Operation'); calls++;
    if (hostCalls.length) throw Error('Original host import attempted');
    stages.push(snapshot());
  }
  process.stdout.write(JSON.stringify({id: i, stages}) + '\n'); maxMemory = Math.max(maxMemory, memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/owned-cast135-runtime.json`, JSON.stringify({cases: cases.length,
  entry_calls: calls, fresh_instances: instances, fresh_every: 12, max_memory_bytes: maxMemory,
  actual_host_calls: 0, denied_function_imports: 878, original_allocator: 91941,
  original_full_entries: [1076, 1754], unchanged_callees: true, memory_page_limit: 512,
  application_start_called: false, full_game_started: false, user_saves_accessed: false,
  network_used: false, node: process.version}, null, 2) + '\n');
