// Full947 due elite clock; every original callee retained and host import denied.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtureFile]=process.argv.slice(2),prepared=await prepareFull135(directory,['spawn_boss','spawn_tick']);
const cases=JSON.parse(await fs.readFile(fixtureFile,'utf8'));
const num=x=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,x,true);return v.getFloat32(0,true);};
let host,instances=0,maxMemory=0;
for(let i=0;i<cases.length;i++){
 const c=cases[i],s=c.input;if(c.id!==i)throw Error('Case order');
 if(i%12===0){host=await prepared.fresh();instances++;}
 const {roles,memory,allocate,hostCalls}=host;
 const G=allocate(8192),V=allocate(128),U=allocate(128*424),name=allocate(c.zone_id.length);
 let d=new DataView(memory.buffer);const w=(o,x)=>d.setUint32(G+o,x>>>0,true),r=o=>d.getUint32(G+o,true);
 new Uint8Array(memory.buffer,name,c.zone_id.length).set(Buffer.from(c.zone_id));w(184,name);w(188,c.zone_id.length);w(2348,V);
 d.setUint8(V+120,1);d.setUint32(V+116,s.flat_height_bits,true);d.setInt32(V+32,-1,true);d.setInt32(V+56,-1,true);
 w(1784,128);w(1788,U);w(1792,s.unit_records?.length??0);
 (s.unit_records??[]).forEach((hex,j)=>new Uint8Array(memory.buffer,U+j*424,424).set(Buffer.from(hex,'hex')));
 if(c.kind==='boss')new Uint8Array(memory.buffer,U,424).set(Buffer.from(s.initial_slot_hex,'hex'));
 w(2352,s.now_bits);w(2516,s.zone_multiplier_bits);d.setUint8(G+387,s.difficulty);d.setUint8(G+2582,s.mode);
 w(2540,s.members);w(400,s.victory_field400);w(404,s.endless_start_bits);d.setUint8(G+2568,s.endless_flag);w(2408,s.counter);
 s.player_xyz.forEach((x,j)=>w(1416+4*j,x));s.velocity_xy.forEach((x,j)=>w(1736+4*j,x));s.rng_words.forEach((x,j)=>w(1720+4*j,x));
 w(1432,1);w(1440,0x42c80000);w(1536,0x42c80000);d.setBigUint64(G+1336,999n,true);
 if(c.kind==='boss')roles.spawn_boss(G,c.definition_pointer,num(s.scalar_bits));
 else{
  w(2416,s.budget_bits);w(2420,s.kill_cost_bits);w(2456,c.next_boss_index);w(2460,c.next_endless_bits);
  for(const o of[2424,2444,2448])w(o,0x7f800000);w(2440,c.next_elite_bits);
  s.previous_player_xyz.forEach((x,j)=>w(2428+4*j,x));roles.spawn_tick(G,num(s.dt_bits));
 }
 d=new DataView(memory.buffer);const count=r(1792),ptr=r(1788);if(count>128)throw Error('Unit bound');
 const timers=[];const records=Array.from({length:count},(_,j)=>{
  const record=ptr+j*424,n=d.getUint32(record+244,true);const raw=Buffer.from(new Uint8Array(memory.buffer,record,424));
  if(n!==0xffffffff){if(n>20)throw Error('Boss clock bound');const t=d.getUint32(record+248,true);
   if(t+n*4>memory.buffer.byteLength)throw Error('Boss clock pointer');timers.push(Array.from({length:n},(_,k)=>d.getUint32(t+k*4,true)));
   raw.writeUInt32LE(0,248);
  }
  return raw.toString('hex');
 });
 const result={count,counter:r(2408),rng_words:[0,1,2,3].map(j=>r(1720+4*j)),record_hex:records,timers_bits:timers};
 if(c.kind==='tick')Object.assign(result,{budget_bits:r(2416),kill_cost_bits:r(2420),velocity_xy:[r(1736),r(1740)],next_elite_bits:r(2440)});
 if(hostCalls.length)throw Error('Host API attempted');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:i,result})+'\n');
}
await fs.writeFile(`${directory}/spawn-elite135-runtime.json`,JSON.stringify({cases:cases.length,functions:[947],host_calls:0,denied_imports:878,
 fresh_instances:instances,max_memory_bytes:maxMemory,original_allocator:91941,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
