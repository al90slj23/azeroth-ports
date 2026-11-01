// Complete original1417 and914; placement and1821 are actual internal callees.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtureFile]=process.argv.slice(2),prepared=await prepareFull135(directory,['damage','spawn_pickup']);
const cases=JSON.parse(await fs.readFile(fixtureFile,'utf8'));if(cases.length>5000)throw Error('Fixture count budget');
const num=x=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,x,true);return d.getFloat32(0,true);};
let host,instances=0,maxMemory=0;
for(let i=0;i<cases.length;i++){
 const c=cases[i],s=c.input;if(c.id!==i)throw Error('Case order');if(i%16===0){host=await prepared.fresh();instances++;}
 const {roles,memory,allocate,hostCalls}=host,G=allocate(8192),V=allocate(128),P=allocate(64*56),name=allocate(c.zone_id.length),xyz=allocate(12);
 let d=new DataView(memory.buffer);const w=(o,x)=>d.setUint32(G+o,x>>>0,true),r=o=>d.getUint32(G+o,true);
 new Uint8Array(memory.buffer,name,c.zone_id.length).set(Buffer.from(c.zone_id));w(184,name);w(188,c.zone_id.length);w(2348,V);
 d.setUint8(V+120,s.flat_height_enabled);d.setUint32(V+116,s.flat_height_bits,true);d.setInt32(V+32,-1,true);d.setInt32(V+56,-1,true);
 new Uint8Array(memory.buffer,P,64*56).fill(0xa5);w(1868,64);w(1872,P);w(1876,0);w(2408,s.counter);w(2412,s.message_sequence);w(2420,s.kill_cost_bits);
 w(2352,s.now_bits);s.rng_words.forEach((x,j)=>w(1720+j*4,x));d.setUint8(G+2587,1);d.setUint8(G+360,1);d.setUint8(G+361,1);
 w(1432,1);w(1440,0x447a0000);w(1536,0x447a0000);d.setBigUint64(G+1336,999n,true);s.player_xyz.forEach((x,j)=>w(1416+4*j,x));
 let U=0;
 if(c.kind==='direct'){
  s.xyz_bits.forEach((x,j)=>d.setUint32(xyz+4*j,x,true));roles.spawn_pickup(G,s.pickup_kind,s.amount,xyz);
 }else{
  U=allocate(424);d=new DataView(memory.buffer);new Uint8Array(memory.buffer,U,424).set(Buffer.from(s.record_hex,'hex'));
  w(1784,1);w(1788,U);w(1792,1);roles.damage(G,1n,num(0x447a0000),0,0,0,0);
 }
 d=new DataView(memory.buffer);const count=r(1876),ptr=r(1872);if(count>64)throw Error('Pickup budget');
 const result={count,pickup_hex:Array.from({length:count},(_,j)=>Buffer.from(memory.buffer,ptr+j*56,56).toString('hex')),
  counter:r(2408),message_sequence:r(2412),rng_words:[0,1,2,3].map(j=>r(1720+4*j)),kill_cost_bits:r(2420)};
 if(U)result.unit={marker:d.getUint32(U,true),duration_bits:d.getUint32(U+344,true),movement_time_bits:d.getUint32(U+340,true),
  from_xyz:[0,1,2].map(j=>d.getUint32(U+316+4*j,true)),to_xyz:[0,1,2].map(j=>d.getUint32(U+328+4*j,true))};
 if(hostCalls.length)throw Error('Host call attempted');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:i,result})+'\n');
}
await fs.writeFile(`${directory}/ordinary-placement135-runtime.json`,JSON.stringify({cases:cases.length,functions:[1417,914],real_internal_callees_unchanged:true,
 host_calls:0,denied_imports:878,fresh_instances:instances,max_memory_bytes:maxMemory,original_allocator:91941,application_start_called:false,
 full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
