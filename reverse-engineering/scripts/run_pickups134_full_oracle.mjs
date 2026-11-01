// Complete original1417/2862 and reached internal callees; no app start.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';
const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['spawn_pickup','collect_pickups']);
const cases=JSON.parse(await fs.readFile(casefile,'utf8'));
if(!cases.length||cases.length>4096)throw Error('Fixture count budget');
let host,instances=0,maxMemory=0;
for(let index=0;index<cases.length;++index){
  if(index%32===0){host=await prepared.fresh();++instances;}
  const c=cases[index];if(c.id!==index)throw Error('Fixture order');
  const {roles,memory,allocate,hostCalls}=host,G=allocate(8192),V=allocate(128),XYZ=allocate(12,4);
  let v=new DataView(memory.buffer);const w=(p,x)=>v.setUint32(p,x>>>0,true),f=(p,x)=>v.setFloat32(p,x,true);
  const capacity=c.state.capacity;
  let records=0;
  if(capacity){records=allocate(capacity*56,8);v=new DataView(memory.buffer);
    new Uint8Array(memory.buffer,records,capacity*56).fill(0xa5);
    c.record_hex.forEach((raw,i)=>new Uint8Array(memory.buffer,records+i*56,56).set(Buffer.from(raw,'hex')));
  }
  v.setUint8(G+360,1);v.setUint8(G+361,1);v.setBigUint64(G+1336,999n,true);
  f(G+1360,100);f(G+1528,100);w(G+1520,c.level);w(G+1524,c.xp);w(G+2368,c.pending);
  v.setUint8(G+2579,c.phase);w(G+2340,V);v.setUint8(V+120,1);f(V+116,0);w(V+56,-1);
  for(const [name,offset]of Object.entries({now_bits:2344,player_x_bits:1504,player_y_bits:1508,
    player_z_bits:1512,radius_bits:1384,xp_multiplier_bits:1388,spawn_counter:2400,message_sequence:2404}))w(G+offset,c.state[name]);
  w(G+1860,capacity);w(G+1864,records);w(G+1868,c.record_hex.length);
  c.rng.forEach((x,i)=>w(G+1712+4*i,x));
  if(c.operation==='append'){
    c.placement.forEach((x,i)=>w(XYZ+4*i,x));roles.spawn_pickup(G,0,c.amount,XYZ);
  }else if(c.operation==='step')roles.collect_pickups(G);
  else throw Error('Unknown operation');
  v=new DataView(memory.buffer);const r=p=>v.getUint32(p,true),count=r(G+1868),pointer=r(G+1864);
  if(count>128||pointer+count*56>memory.buffer.byteLength)throw Error('Result vector bound');
  const result={id:index,capacity:r(G+1860),count,spawn_counter:r(G+2400),message_sequence:r(G+2404),
    level:r(G+1520),xp:r(G+1524),pending:r(G+2368),phase:v.getUint8(G+2579),
    rng:Array.from({length:4},(_,i)=>r(G+1712+4*i)),
    records_words:Array.from({length:count},(_,i)=>Array.from({length:14},(_,j)=>r(pointer+56*i+4*j))),
    observed_message_count:r(G+1880)};
  if(hostCalls.length)throw Error('Host API attempted');
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/pickups134-runtime.json`,JSON.stringify({case_count:cases.length,
  actual_original_functions:[1417,2862],reached_original_callees_unchanged:true,original_allocator:91940,
  fresh_instances:instances,fresh_instance_every:32,max_memory_bytes:maxMemory,memory_limit_pages:512,
  denied_function_imports:878,actual_host_calls:0,node:process.version,application_start_called:false,
  full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
