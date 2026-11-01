// One real1560 constructor, then controlled2088/1754/3757/915/921/2862/947/1072.
// Phase1 is an explicit research fixture boundary, NOT completed1089/resource boot.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareFull135} from './full135_host.mjs';
const [directory, file] = process.argv.slice(2);
const required = ['initial_game', 'player_tick', 'process_hits', 'area_tick', 'effect_tick', 'update_units', 'collect_pickups', 'spawn_tick', 'select_ability'];
const prepared = await prepareFull135(directory, required);
const text = await fs.readFile(file, 'utf8'); if (Buffer.byteLength(text) > 128 * 1024 * 1024) throw Error('Fixture bytes');
const cases = text.trim().split('\n').map(JSON.parse); if (!cases.length || cases.length > 48) throw Error('Fixture count');
let totalCalls = 0, maxMemory = 0;
for (let index = 0; index < cases.length; index++) {
  const c = cases[index]; if (c.id !== index || c.controlled_phase1 !== true || c.zeroed_unit_capacity !== 128 || c.zeroed_area_capacity !== 128) throw Error('Explicit fixture boundaries');
  const host = await prepared.fresh(), {roles, memory, allocate, hostCalls} = host;
  const d = () => new DataView(memory.buffer), bytes = () => new Uint8Array(memory.buffer);
  const w = (p, x) => d().setUint32(p, x >>> 0, true), r = p => d().getUint32(p, true), b = (p, x) => d().setUint8(p, x);
  const G = allocate(8192), P = allocate(376), V = allocate(128);
  const name = Buffer.from(c.region_id, 'ascii'), N = allocate(name.length, 1); bytes().set(name, N);
  w(P + 156, 4); w(P + 168, N); w(P + 172, name.length);
  d().setBigUint64(P + 176, BigInt(c.input.object_id_u64), true); d().setBigUint64(P + 184, BigInt(c.input.seed_u64), true);
  b(P + 344, c.input.class_byte); b(P + 345, c.input.race_byte);
  b(V + 120, 1); w(V + 116, c.input.flat_height_bits); w(V + 32, 0xffffffff); w(V + 56, 0xffffffff);
  roles.initial_game(G, P, V); totalCalls++;
  if (r(G + 1792) !== 0) throw Error('Constructor must have no units before entry');
  const U = allocate(128 * 424); w(G + 1784, 128); w(G + 1788, U);
  if (r(G + 1804) !== 0) throw Error('Constructor must have no areas before entry');
  const A = allocate(128 * 88); w(G + 1796, 128); w(G + 1800, A);
  // Only storage resource and controlled phase are supplied externally. Actual
  //skill/racial records, RNG, stats, timers and positions remain constructor outputs.
  b(G + 2587, 1);
  let previousStorage = Buffer.alloc(128 * 424);
  let previousAreaStorage = Buffer.alloc(128 * 88);
  const span = (p, size, limit) => {if (size < 0 || size > limit || p + size > memory.buffer.byteLength) throw Error('Span bound'); return bytes().subarray(p, p + size);};
  const id = (p, n) => Buffer.from(span(p, n, 128)).toString('ascii');
  const tree = () => {
    const root = r(G + 2476), depth = r(G + 2480); if (!root) return {};
    if (depth > 5) throw Error('Tree depth'); const result = [], seen = new Set();
    const walk = (p, level) => {if (!p || seen.has(p) || seen.size > 256) throw Error('Tree bound'); seen.add(p);
      const n = d().getUint16(p + 50, true); if (n > 11) throw Error('Tree node count');
      for (let j = 0; j < n; j++) {if (level) walk(r(p + 76 + j * 4), level - 1); result.push([d().getUint16(p + 52 + j * 2, true), r(p + 4 + j * 4)]);}
      if (level) walk(r(p + 76 + n * 4), level - 1);}; walk(root, depth); return Object.fromEntries(result);
  };
  const candidates = () => {
    const p = r(G + 1908), n = r(G + 1912); if (n > 4) throw Error('Candidate count');
    return Array.from({length: n}, (_, j) => {const q = p + j * 80, tag = r(q + 60);
      const v = {variant: '', tier: r(q + 76), ability_id: '', owned_index: 0, kinds: [], gold: 0};
      if (tag === 0x80000000) {v.variant = 'new'; v.ability_id = id(r(q + 64), r(q + 68));}
      else if (tag < 0x80000000 || tag === 0x80000001) {v.variant = 'upgrade'; v.owned_index = r(q + 72);
        const definition = r(r(G + 1660) + v.owned_index * 80); v.ability_id = id(r(definition + 12), r(definition + 16)); v.kinds = Array.from(span(r(q + 64), r(q + 68), 5));}
      else if (tag === 0x80000004) {v.variant = 'gold'; v.gold = r(q + 64);} else throw Error('Candidate variant'); return v;});
  };
  const queue = base => {const p = r(G + base + 4), n = r(G + base + 8); if (n > 2048) throw Error('Forward queue count'); return Array.from({length: n}, (_, j) => [r(p + j * 8), r(p + j * 8 + 4)]);};
  const snapshot = () => {
    const allFields = tree(), keys = new Set([22, 28, 34, 716, 717, 1109, 1176]);
    const unmodeled_player_fields = Object.fromEntries(Object.entries(allFields).filter(([key]) => !keys.has(Number(key))));
    const count = r(G + 1792), p = r(G + 1788), on = r(G + 1664), op = r(G + 1660), ln = r(G + 1712), lp = r(G + 1708), pn = r(G + 1876), pp = r(G + 1872), hn = r(G + 1852), hp = r(G + 1848);
    if (count > 128 || on > 32 || ln > 64 || pn > 256 || hn > 4096) throw Error('Projection budget');
    const storage = Buffer.from(span(p, 128 * 424, 128 * 424)), unit_storage_delta_words = [];
    for (let word = 0; word < storage.length / 4; word++) {
      const value = storage.readUInt32LE(word * 4);
      if (value !== previousStorage.readUInt32LE(word * 4)) unit_storage_delta_words.push([word, value]);
    }
    previousStorage = storage;
    const an = r(G + 1804), ap = r(G + 1800);
    if (an > 128 || r(G + 1796) !== 128) throw Error('Area capacity');
    const areaStorage = Buffer.from(span(ap, 128 * 88, 128 * 88)), area_storage_delta_words = [];
    for (let word = 0; word < areaStorage.length / 4; word++) {
      const value = areaStorage.readUInt32LE(word * 4);
      if (value !== previousAreaStorage.readUInt32LE(word * 4)) area_storage_delta_words.push([word, value]);
    }
    previousAreaStorage = areaStorage;
    const effectVector = (base, stride) => {
      const n = r(G + base + 8), p = r(G + base + 4), capacity = r(G + base);
      if (n > capacity || capacity > 256) throw Error('Effect vector budget');
      return {capacity, records_hex: Array.from({length: n}, (_, j) => Buffer.from(span(p + j * stride, stride, stride)).toString('hex'))};
    };
    const projection = {progression: {level: r(G + 1432), xp: r(G + 1436), pending_upgrades: r(G + 2376)},
      derived_bits: Object.fromEntries(Array.from({length: 23}, (_, j) => [1536 + j * 4, r(G + 1536 + j * 4)])),
      current_hp_bits: r(G + 1440), auxiliary_bits: Object.fromEntries([1444, 1448, 1348, 768, 756].map(o => [o, r(G + o)])),
      speed_bits: r(G + 1648), player_fields: Object.fromEntries(Object.entries(allFields).filter(([key]) => keys.has(Number(key)))),
      rng_words: [0, 1, 2, 3].map(j => r(G + 1720 + j * 4)), candidates: candidates(),
      phase2587: d().getUint8(G + 2587), selection_kind2585: d().getUint8(G + 2585), generation_counter2400: r(G + 2400),
      records: Array.from({length: count}, (_, j) => Buffer.from(span(p + j * 424, 424, 424)).toString('hex')),
      racial_record_hex: Buffer.from(span(G + 1256, 80, 80)).toString('hex'),
      owned_records_hex: Array.from({length: on}, (_, j) => Buffer.from(span(op + j * 80, 80, 80)).toString('hex')),
      timer1628_bits: r(G + 1628), budget_bits: r(G + 2416), velocity_xy: [r(G + 1736), r(G + 1740)], previous_player_xyz: [r(G + 2428), r(G + 2432), r(G + 2436)], now_bits: r(G + 2352),
      unit_storage_sha256: createHash('sha256').update(storage).digest('hex'),
      area_records: Array.from({length: an}, (_, j) => Buffer.from(span(ap + j * 88, 88, 88)).toString('hex')),
      area_storage_sha256: createHash('sha256').update(areaStorage).digest('hex'),
      area_capacity: r(G + 1796),
      pickup_words: Array.from({length: pn}, (_, j) => Array.from({length: 14}, (_, k) => r(pp + j * 56 + k * 4))), pickup_capacity: r(G + 1868),
      spawn_counter: r(G + 2408), message_sequence: r(G + 2412), kill_cost_bits: r(G + 2420),
      live_words: Array.from({length: ln}, (_, j) => Array.from({length: 8}, (_, k) => r(lp + j * 32 + k * 4))),
      outgoing_total_hex: d().getBigUint64(G + 984, true).toString(16).padStart(16, '0'), incoming_total_hex: d().getBigUint64(G + 992, true).toString(16).padStart(16, '0'), last_hit_bits: r(G + 1652),
      absorbed740_bits: r(G + 740), maximum_shield744_bits: r(G + 744),
      queued: Array.from({length: hn}, (_, j) => {const q = hp + j * 112; return {target_id: d().getBigUint64(q + 64, true).toString(), source_id: d().getBigUint64(q + 72, true).toString(), due_bits: r(q + 92), spell_id: r(q + 96), damage_bits: r(q + 100), critical: d().getUint8(q + 104), school: d().getUint8(q + 106), context908: d().getUint8(q + 105)};}),
      attempted_spell_sets: [672, 684, 732].map(offset => {const p = r(G + offset), n = r(G + offset + 4); if (n > 256) throw Error('Spell ledger'); return Array.from({length: n}, (_, j) => r(p + j * 4));}),
      gold: r(G + 1456), earned: r(G + 1100), xp_queue: queue(2144), xp_queue_capacity: r(G + 2144), currency_queue: queue(2156), currency_queue_capacity: r(G + 2156), game_tag: d().getBigUint64(G, true).toString(),
      auxiliary_motion_count: r(G + 664), claim_count: r(G + 2116),
      effect_state: {clock2364_bits: r(G + 2364), effect_counter2356: r(G + 2356), action_sequence1644: r(G + 1644),
        player_action_tag416: r(G + 416), player_xyz: [r(G + 1416), r(G + 1420), r(G + 1424)],
        delayed56: effectVector(1820, 56), effects120: effectVector(1808, 120)}};
    const unmodeled_effect_fields = {inactive_action_payload_words: [420, 424, 428, 432, 436].map(o => r(G + o)),
      delayed_pointer: r(G + 1824), effect120_pointer: r(G + 1812), player_facing_bits: r(G + 1428)};
    return {projection, unmodeled_player_fields, unmodeled_effect_fields, unit_storage_delta_words, area_storage_delta_words};
  };
  const stages = [];
  const number = bits => {const v = new DataView(new ArrayBuffer(4)); v.setUint32(0, bits, true); return v.getFloat32(0, true);};
  for (const action of c.actions) {
    if (action.kind === 'frame') {
      if (d().getUint8(G + 2587) !== 1) throw Error('Frame called outside running phase');
      d().setFloat32(G + 2352, d().getFloat32(G + 2352, true) + number(action.dt_bits), true);
      for (const [kind, role] of [['player', 'player_tick'], ['hits', 'process_hits'], ['area', 'area_tick'], ['effects', 'effect_tick'], ['ai', 'update_units'], ['collect', 'collect_pickups'], ['spawn', 'spawn_tick']]) {
        if (kind === 'collect' && (r(G + 664) || r(G + 2116))) throw Error('Unrestored auxiliary movement/claim producer');
        if (kind === 'player' || kind === 'effects' || kind === 'ai' || kind === 'spawn') roles[role](G, number(action.dt_bits)); else roles[role](G);
        totalCalls++; if (hostCalls.length) throw Error('Original host import attempted'); stages.push({kind, ...snapshot()});
      }
    } else if (action.kind === 'select') {if (r(G + 664) || r(G + 2116)) throw Error('Unrestored auxiliary movement/claim producer'); roles.select_ability(G, action.index); totalCalls++; stages.push({kind: 'select', ...snapshot()});}
    else throw Error('Action');
  }
  if (hostCalls.length) throw Error('Original host import attempted');
  process.stdout.write(JSON.stringify({id: index, stages}) + '\n'); maxMemory = Math.max(maxMemory, memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/headless135-runtime.json`, JSON.stringify({cases: cases.length, original_entry_calls: totalCalls,
  original_functions: [1560, 2088, 1754, 3757, 915, 921, 2862, 947, 1072], host_calls: 0, denied_imports: 878,
  max_memory_bytes: maxMemory, memory_page_limit: 512, original_allocator: 91941, node: process.version,
  application_start_called: false, network_used: false, user_saves_accessed: false, full_game_started: false,
  controlled_phase1_boundary: true, zeroed_unit_storage_capacity: 128, zeroed_area_storage_capacity: 128}, null, 2) + '\n');
