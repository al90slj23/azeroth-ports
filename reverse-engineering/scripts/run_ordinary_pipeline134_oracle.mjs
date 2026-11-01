// Full original914 ->2862 ->4630; independent predicted times drive the probe.
// Source instructions/callees unchanged, application start and host APIs denied.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';
const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['damage','collect_pickups']);
const cases=JSON.parse(await fs.readFile(casefile,'utf8'));
if(!cases.length||cases.length>2048)throw Error('Case budget');
let host,instances=0,maxMemory=0;
for(let i=0;i<cases.length;++i){
  if(i%16===0){host=await prepared.fresh();++instances;}
  const c=cases[i];if(c.id!==i)throw Error('Case order');
  const {roles,memory,allocate,hostCalls}=host,G=allocate(8192),U=allocate(424),V=allocate(128),D=allocate(72,4);
  new Uint8Array(memory.buffer,D,72).set(Buffer.from(c.definition_hex,'hex'));
  let pointer=0;
  if(c.capacity){pointer=allocate(c.capacity*56,8);
    c.record_hex.forEach((raw,j)=>new Uint8Array(memory.buffer,pointer+j*56,56).set(Buffer.from(raw,'hex')));}
  let v=new DataView(memory.buffer);const w=(p,x)=>v.setUint32(p,x>>>0,true),f=(p,x)=>v.setFloat32(p,x,true),r=p=>v.getUint32(p,true);
  const number=bits=>{const temp=new DataView(new ArrayBuffer(4));temp.setUint32(0,bits,true);return temp.getFloat32(0,true);};
  v.setUint8(G+360,1);v.setUint8(G+361,1);v.setBigUint64(G+1336,999n,true);
  f(G+1360,100);f(G+1364,1);f(G+1376,2);w(G+1384,c.radius_bits);w(G+1388,c.xp_multiplier_bits);
  w(G+1504,c.position[0]);w(G+1508,c.position[1]);w(G+1512,c.position[2]);
  w(G+1520,c.level);w(G+1524,c.xp);w(G+2368,c.pending);f(G+1528,100);
  w(G+1780,U);w(G+1784,1);w(G+2340,V);w(G+2344,c.now_bits);v.setUint8(G+2579,1);
  w(G+1860,c.capacity);w(G+1864,pointer);w(G+1868,c.record_hex.length);
  w(G+2400,c.spawn_counter);w(G+2404,c.message_sequence);w(G+2412,c.accumulator_bits);
  c.rng.forEach((x,j)=>w(G+1712+4*j,x));v.setUint8(V+120,1);f(V+116,0);w(V+56,-1);
  w(U+40,-1);w(U+64,-1);w(U+244,-1);w(U+284,D);v.setBigUint64(U+112,1n,true);
  w(U+288,c.hp_bits);w(U+292,c.max_hp_bits);
  for(const offset of [316,328])c.position.forEach((x,j)=>w(U+offset+4*j,x));
  function snapshot(){
    v=new DataView(memory.buffer);const count=r(G+1868),p=r(G+1864);
    if(count>128||p+count*56>memory.buffer.byteLength)throw Error('Pickup bound');
    return {phase:v.getUint8(G+2579),level:r(G+1520),xp:r(G+1524),pending:r(G+2368),
      unit_hp_bits:r(U+288),unit_marker:r(U),unit_duration_bits:r(U+344),unit_death_time_bits:r(U+4),
      unit_movement_time_bits:r(U+340),unit_afflicted:r(U+240),
      accounted_total_bits:v.getBigUint64(G+984,true).toString(16).padStart(16,'0'),
      now_bits:r(G+2344),capacity:r(G+1860),count,spawn_counter:r(G+2400),message_sequence:r(G+2404),
      accumulator_bits:r(G+2412),rng:Array.from({length:4},(_,j)=>r(G+1712+4*j)),
      records_words:Array.from({length:count},(_,j)=>Array.from({length:14},(_,k)=>r(p+j*56+k*4)))};
  }
  roles.damage(G,1n,number(c.amount_bits),133,2,0,0);const result={id:i,after_death:snapshot()};
  v.setUint8(G+2579,c.collect_phase);
  roles.collect_pickups(G);result.after_attraction=snapshot();
  w(G+2344,c.before_arrival_bits);roles.collect_pickups(G);result.before_arrival=snapshot();
  w(G+2344,c.arrival_bits);roles.collect_pickups(G);result.at_arrival=snapshot();
  if(hostCalls.length)throw Error('Host API attempted');
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/ordinary-pipeline134-runtime.json`,JSON.stringify({case_count:cases.length,
  original_functions:[914,1417,1820,2862,4630],original_callees_unchanged:true,original_allocator:91940,
  fresh_instances:instances,fresh_instance_every:16,max_memory_bytes:maxMemory,memory_limit_pages:512,
  actual_host_calls:0,denied_function_imports:878,node:process.version,full_game_started:false,
  application_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
