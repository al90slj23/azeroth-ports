// Full original8751 and947 with real flat-height29631 and actual trig/spawn.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtureFile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['spawn_position','spawn_tick','atan_heading','atan2_heading']);
const cases=JSON.parse(await fs.readFile(fixtureFile,'utf8'));
let host,instances=0,maxMemory=0;
const num=x=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,x,true);return v.getFloat32(0,true);};
for(let i=0;i<cases.length;++i){
 const c=cases[i],s=c.input;if(c.id!==i)throw Error('Case order');
 if(i%16===0){host=await prepared.fresh();instances++;}
 const {roles,memory,allocate,hostCalls}=host;
 if(c.kind==='atan'||c.kind==='atan2'){
  const buffer=new ArrayBuffer(4),dv=new DataView(buffer);
  const value=c.kind==='atan'?roles.atan_heading(num(s.bits)):roles.atan2_heading(num(s.y),num(s.x));
  dv.setFloat32(0,value,true);if(hostCalls.length)throw Error('Original host API attempted');
  process.stdout.write(JSON.stringify({id:i,result:{bits:dv.getUint32(0,true)}})+'\n');
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);continue;
 }
 const G=allocate(8192),V=allocate(128),name=allocate(c.zone_id.length),output=allocate(16);
 let view=new DataView(memory.buffer);
 const u=(o,x)=>view.setUint32(G+o,x>>>0,true),r=o=>view.getUint32(G+o,true);
 new Uint8Array(memory.buffer,name,c.zone_id.length).set(Buffer.from(c.zone_id));u(184,name);u(188,c.zone_id.length);u(2348,V);
 view.setUint8(V+120,1);view.setUint32(V+116,s.flat_height_bits,true);view.setInt32(V+32,-1,true);view.setInt32(V+56,-1,true);
 s.player_xyz.forEach((x,j)=>u(1416+4*j,x));s.velocity_xy.forEach((x,j)=>u(1736+4*j,x));s.rng_words.forEach((x,j)=>u(1720+4*j,x));
 let result;
 if(c.kind==='position'){
  roles.spawn_position(output,G,num(s.low_radius_bits),num(s.high_radius_bits),num(s.bias_probability_bits));view=new DataView(memory.buffer);
  result={position_bits:[0,1,2].map(j=>view.getUint32(output+4*j,true)),rng_words:[0,1,2,3].map(j=>r(1720+4*j))};
 }else{
  const units=allocate(128*424);view=new DataView(memory.buffer);u(1784,128);u(1788,units);u(1792,c.unit_records?.length??0);
  (c.unit_records??[]).forEach((hex,j)=>new Uint8Array(memory.buffer,units+j*424,424).set(Buffer.from(hex,'hex')));
  u(2352,c.now_bits);u(2416,c.budget_bits);u(2420,c.kill_cost_bits);u(2516,c.zone_multiplier_bits??0x3f800000);u(2456,5);
  for(const offset of[2424,2440,2444,2448,2460])u(offset,0x7f800000);
  view.setUint8(G+2582,c.mode??0);view.setUint8(G+2568,c.endless_flag??0);u(2540,c.members??1);view.setUint8(G+387,c.difficulty??0);
  u(400,c.victory_field400??0);u(404,c.endless_start_bits??0);u(2408,c.counter??0);
  u(1432,1);u(1440,0x42c80000);u(1536,0x42c80000);
  view.setBigUint64(G+1336,999n,true);(c.previous_player_xyz??s.player_xyz).forEach((x,j)=>u(2428+4*j,x));
  roles.spawn_tick(G,num(c.dt_bits));view=new DataView(memory.buffer);
  const count=r(1792),ptr=r(1788);if(count>128)throw Error('Spawn count budget');
  result={budget_bits:r(2416),kill_cost_bits:r(2420),count,counter:r(2408),rng_words:[0,1,2,3].map(j=>r(1720+4*j)),
    velocity_xy:[r(1736),r(1740)],record_hex:Array.from({length:count},(_,j)=>Buffer.from(memory.buffer,ptr+j*424,424).toString('hex'))};
 }
 if(hostCalls.length)throw Error('Original host API attempted');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:i,result})+'\n');
}
await fs.writeFile(`${directory}/spawn-motion135-runtime.json`,JSON.stringify({cases:cases.length,functions:[34787,42475,8751,947],
 original_internal_callees_unchanged:true,host_calls:0,denied_imports:878,fresh_instances:instances,max_memory_bytes:maxMemory,
 original_allocator:91941,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
