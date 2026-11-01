// Complete original1073, no rewritten callee, all878 imports denied.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory, file] = process.argv.slice(2);
const prepared = await prepareFull135(directory, ['incoming_damage']);
const text = await fs.readFile(file, 'utf8');
if (Buffer.byteLength(text) > 32 * 1024 * 1024) throw Error('Input budget');
const cases = JSON.parse(text), keys = ['capacity','count','group','head','id','input','ops','storage'];
if (!cases.length || cases.length > 1000) throw Error('Case budget');
const offsets = {armor_1392_bits:1568, armor_cap_1572_bits:1572, nearby_reduction_1444_bits:1624,
 hp_1528_bits:1440, shield_1532_bits:1444, barrier_1536_bits:1448, shield_source_1344:1344,
 shield_source_remaining_1348_bits:1348, reserve_768_bits:768, absorbed_740_bits:740,
 maximum_shield_744_bits:744, last_hit_1648_bits:1652};
const number = x => {const d = new DataView(new ArrayBuffer(4)); d.setUint32(0,x,true); return d.getFloat32(0,true);};
let host, instances = 0, calls = 0, maxMemory = 0;
for (const c of cases) {
 if (Object.keys(c).sort().join() !== keys.join()) throw Error('Inputs must not carry expectations/results');
 if (c.id % 8 === 0) {host = await prepared.fresh(); instances++;}
 const {memory, allocate, roles, hostCalls} = host, s = c.input;
 const d = () => new DataView(memory.buffer), bytes = () => new Uint8Array(memory.buffer);
 const r = p => d().getUint32(p,true), w = (p,x) => d().setUint32(p,x,true);
 const G = allocate(8192), Q = c.capacity ? allocate(c.capacity * 48,4) : 1;
 const g = (o,x) => w(G+o,x), b = (o,x) => d().setUint8(G+o,x);
 if (c.capacity !== c.storage.length || c.capacity > 1024 || c.ops.length > 600) throw Error('Domain budget');
 c.storage.forEach((row,j) => {if (row.length !== 96) throw Error('Full48 input'); bytes().set(Buffer.from(row,'hex'),Q+j*48);});
 g(968,c.capacity);g(972,Q);g(976,c.head);g(980,c.count);
 b(360,1);b(361,1);d().setBigUint64(G+1336,999n,true);g(1432,1);g(1536,s.max_hp_bits);
 b(2587,s.phase_2579);b(2576,s.protection_2568);b(2582,s.mode_2574);b(2578,s.minimum_one_2578);g(2540,s.wave_2532);
 for (const [key,o] of Object.entries(offsets)) g(o,s[key]);
 d().setFloat64(G+992,s.incoming_total_992,true);
 const names = Buffer.from(s.map_id,'ascii'), P = allocate(Math.max(1,names.length),1);bytes().set(names,P);g(184,P);g(188,names.length);
 const M = allocate(128 * 16);g(1880,128);g(1884,M);g(1888,0);
 const stages = [];
 function slice(p,n) {if (!Number.isInteger(n) || n < 0 || p < 0 || p+n > memory.buffer.byteLength) throw Error('Physical bounds');return Buffer.from(bytes().slice(p,p+n)).toString('hex');}
 function string(p,n) {if (n > 1048576) throw Error('String budget');slice(p,n);return new TextDecoder('utf-8',{fatal:true}).decode(bytes().slice(p,p+n));}
 for (const op of c.ops) {
  if (Object.keys(op).sort().join() !== 'amount_bits,category,critical,now_bits') throw Error('Action keyset');
  g(2352,op.now_bits);const before = bytes().slice(G,G+2592);
  roles.incoming_damage(G,number(op.amount_bits),0n,op.critical,op.category,0);calls++;
  if (hostCalls.length) throw Error('Original attempted denied host');
  const capacity = r(G+968), ptr = r(G+972), head = r(G+976), count = r(G+980);
  if (capacity > 2048 || count > capacity || (capacity && head >= capacity)) throw Error('History bounds');
  const storage = Array.from({length:capacity},(_,j) => slice(ptr+j*48,48));
  const active = Array.from({length:count},(_,j) => {const slot = (head+j)%capacity, q = ptr+slot*48;
   return {slot, raw_hex:storage[slot], strings:[0,8,16].map(o => string(r(q+o),r(q+o+4)))};});
  const scalar = {};for (const [key,o] of Object.entries(offsets)) scalar[key] = r(G+o);
  scalar.incoming_total_992_bits = d().getBigUint64(G+992,true).toString(16).padStart(16,'0');scalar.phase_2579 = bytes()[G+2587];
  const changes = [], old = new DataView(before.buffer,before.byteOffset,before.byteLength);
  for (let o=0;o<2592;o+=4) if (old.getUint32(o,true)!==r(G+o)) changes.push([o,r(G+o)]);
  const mp = r(G+1884), mc = r(G+1880), ml = r(G+1888), np = r(G+1896), nc = r(G+1892), nl = r(G+1900);
  if (mc > 4096 || ml > mc || nc > 4096 || nl > nc) throw Error('Message bounds');
  const packets = Array.from({length:ml},(_,j) => {const q=mp+j*16;return {opcode:d().getUint16(q+12,true),capacity:r(q),raw_hex:slice(r(q+4),r(q+8))};});
  const notifications = Array.from({length:nl},(_,j) => {const q=np+j*12;return {capacity:r(q),raw_hex:slice(r(q+4),r(q+8))};});
  stages.push({header:{capacity,head,count},history_pointer:ptr,storage,active,scalar,raw_game2592_hex:slice(G,2592),game_changes:changes,
   packets,notifications,message_metadata_backing_hex:slice(mp,mc*16),notification_metadata_backing_hex:slice(np,nc*12)});
 }
 maxMemory = Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,stages})+'\n');
}
await fs.writeFile(`${directory}/incoming-history135-runtime.json`,JSON.stringify({cases:cases.length,calls,
 fresh_instances:instances,max_memory_bytes:maxMemory,all_callees_unchanged:true,original_functions:[1073],
 allocator:91941,denied_imports:878,host_calls:0,memory_pages:512,app_start_called:false,
 network_used:false,user_saves_accessed:false,only_input_keys:keys},null,2)+'\n');
