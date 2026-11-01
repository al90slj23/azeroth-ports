// Private absent-companion fixture: complete6730(cache hit)->1089.
// Explicit App slot discriminants only; no post-constructor/vector/phase edits.
// Original2922 is statically traced separately, not executed by this host.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareWorldSnapshot135} from './world_snapshot135_host.mjs';
const [directory,configPath]=process.argv.slice(2);
const config=JSON.parse(await fs.readFile(configPath,'utf8'));
if(Object.keys(config).sort().join()!=='app_pointer,input_path,input_sha256,model_snapshot_sha256,snapshot_path,snapshot_sha256,world_pointer')throw Error('Config exact keys');
const inputRaw=await fs.readFile(config.input_path);
if(createHash('sha256').update(inputRaw).digest('hex')!==config.input_sha256)throw Error('Input SHA');
const cases=JSON.parse(inputRaw),keys='app_lcg_seed_u64,class_byte,companion_tags,object_id_u64,race_byte,region_index';
if(!cases.length||cases.length>64)throw Error('Case budget');
const prepared=await prepareWorldSnapshot135(directory,['cached_construct','begin_run']);
const layouts={companions:[2108,2112,2116,88],units:[1784,1788,1792,424],pickups:[1868,1872,1876,56],special:[1916,1920,1924,40],windows:[1964,1968,1972,8],boundaries:[2120,2124,2128,8]};
let hostCount=0,maxMemory=0,originalCalls=0,packetCount=0,notificationCount=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input'||Object.keys(c.input).sort().join()!==keys)throw Error('Expected/labels/diagnostics forbidden');
 const s=c.input;if(s.region_index!==0||!Number.isInteger(s.class_byte)||s.class_byte<0||s.class_byte>255||!Number.isInteger(s.race_byte)||s.race_byte<0||s.race_byte>255)throw Error('Declared profile input domain');
 const host=await prepared.restore(config.snapshot_path,config.snapshot_sha256),{memory,roles,allocate,hostCalls}=host;
 const d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),u=p=>d().getUint32(p,true);
 const App=config.app_pointer,R=u(App+5116);if(R!==config.world_pointer)throw Error('Genuine cache pointer');
 const raw=(p,n)=>{if(!Number.isInteger(p)||!Number.isInteger(n)||p<0||n<0||p+n>memory.buffer.byteLength)throw Error('Physical bounds');return Buffer.from(b().slice(p,p+n)).toString('hex');};
 const beforeRefcount=u(R),G=allocate(8192,8);b().fill(0xa5,G,G+8192);
 const appBeforeHex=raw(App,5168),worldBeforeHex=raw(R,124);
 d().setBigUint64(App+4928,BigInt(s.app_lcg_seed_u64),true);b()[App+3720]=s.class_byte;b()[App+3721]=s.race_byte;d().setBigUint64(App+3552,BigInt(s.object_id_u64),true);
 if(JSON.stringify(s.companion_tags)!=='[255,255]')throw Error('Explicit absent companion declarations required');
 b()[App+3604]=s.companion_tags[0];b()[App+3612]=s.companion_tags[1];
 const declaredAppHex=raw(App,5168);
 function queue(capOffset,ptrOffset,lenOffset,stride,packets){
  const capacity=u(G+capOffset),pointer=u(G+ptrOffset),count=u(G+lenOffset);
  if(capacity>4096||count>capacity)throw Error('Queue bounds');
  const active=Array.from({length:count},(_,j)=>{const q=pointer+j*stride,cap=u(q),p=u(q+4),n=u(q+8);if(n>cap||cap>1048576)throw Error('Payload bounds');
   const value={capacity:cap,pointer:p,length:n,payload_hex:raw(p,n),backing_hex:raw(p,cap),metadata_hex:raw(q,stride)};if(packets)value.opcode=d().getUint16(q+12,true);return value;});
  return {capacity,pointer,count,metadata_backing_hex:raw(pointer,capacity*stride),active};
 }
 function capture(){
  const vectors={};for(const [name,[co,po,no,stride]]of Object.entries(layouts)){
   const capacity=u(G+co),pointer=u(G+po),count=u(G+no);if(capacity>4096||count>capacity)throw Error('Vector bounds');
   vectors[name]={capacity,pointer,count,stride,storage:Array.from({length:capacity},(_,j)=>raw(pointer+j*stride,stride))};
  }
  return {phase2587:b()[G+2587],counter2408:u(G+2408),rng_words:[0,1,2,3].map(j=>u(G+1720+j*4)),player_xyz:[0,1,2].map(j=>u(G+1416+j*4)),vectors,
   packets:queue(1880,1884,1888,16,true),notifications:queue(1892,1896,1900,12,false),raw_game2592_hex:raw(G,2592),raw_app5168_hex:raw(App,5168),raw_world_rc124_hex:raw(R,124),
   world_cache_pointer:u(App+5116),game_world_pointer:u(G+2348),app_lcg_seed_u64:d().getBigUint64(App+4928,true).toString(),world_refcount:u(R),stack:host.stackPointer,memory_bytes:memory.buffer.byteLength};
 }
 roles.cached_construct(G,App);originalCalls++;
 const constructor=capture();if(constructor.phase2587!==0||constructor.world_cache_pointer!==R||constructor.game_world_pointer!==R||constructor.world_refcount!==beforeRefcount+1)throw Error('Real constructor/cache ownership boundary');
 if(Object.values(constructor.vectors).some(x=>x.count!==0||x.capacity!==0))throw Error('Declared empty vector constructor');
 if(b()[G+244]!==255||b()[G+252]!==255)throw Error('6730/1560 did not preserve actual absent companion tags');
 roles.begin_run(G);originalCalls++;const final=capture();
 if(final.world_cache_pointer!==R||final.game_world_pointer!==R||final.world_refcount!==constructor.world_refcount)throw Error('Original world ownership changed');
 if(hostCalls.length)throw Error('Denied original host attempted');
 const packetPrefix=constructor.packets.active.map(x=>({opcode:x.opcode,payload_hex:x.payload_hex})),notificationPrefix=constructor.notifications.active.map(x=>x.payload_hex);
 const packetAll=final.packets.active.map(x=>({opcode:x.opcode,payload_hex:x.payload_hex})),notificationAll=final.notifications.active.map(x=>x.payload_hex);
 if(JSON.stringify(packetAll.slice(0,packetPrefix.length))!==JSON.stringify(packetPrefix)||JSON.stringify(notificationAll.slice(0,notificationPrefix.length))!==JSON.stringify(notificationPrefix))throw Error('Constructor queue prefix mutated');
 const projection={phase2587:final.phase2587,counter2408:final.counter2408,rng_words:final.rng_words,player_xyz:final.player_xyz,
  ...Object.fromEntries(Object.entries(final.vectors).map(([name,x])=>[name,{capacity:x.capacity,count:x.count,storage:x.storage}])),
  packets:packetAll.slice(packetPrefix.length),notifications_utf8_hex:notificationAll.slice(notificationPrefix.length)};
 packetCount+=projection.packets.length;notificationCount+=projection.notifications_utf8_hex.length;hostCount+=hostCalls.length;maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,projection,constructor_prefix:{packets:packetPrefix,notifications_utf8_hex:notificationPrefix},raw:{App,G,world_pointer:R,app_before_declared_hex:appBeforeHex,app_after_declared_hex:declaredAppHex,world_before_hex:worldBeforeHex,constructor,final},calls:host.calls,snapshot:host.snapshot})+'\n');
}
await fs.writeFile(`${directory}/opening-handoff135-runtime.json`,JSON.stringify({cases:cases.length,full_original6730_calls:cases.length,full_original1089_calls:cases.length,original_calls:originalCalls,full_snapshot_restores:cases.length,
 opening_packet_count:packetCount,opening_notification_count:notificationCount,max_memory_bytes:maxMemory,memory_cap_bytes:256*1024*1024,denied_imports:878,host_calls:hostCount,
 original_callees_preserved:true,only_export_section_changed:true,appstart_called:false,network_used:false,user_saves_accessed:false,fresh_bootstraps:0,new_mainloop_frames:0,once_written:false,world_rc_forged:false},null,2)+'\n');
