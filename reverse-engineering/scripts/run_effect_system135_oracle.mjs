// Complete915 with every internal helper preserved; deny878 host imports.
import fs from 'node:fs/promises';
import {createHash}from'node:crypto';
import{prepareFull135}from'./full135_host.mjs';
const[directory,file]=process.argv.slice(2),prepared=await prepareFull135(directory,['effect_tick']);
const text=await fs.readFile(file,'utf8');if(Buffer.byteLength(text)>64*1024*1024)throw Error('Fixturebytes');const cases=JSON.parse(text);if(!cases.length||cases.length>3000)throw Error('Fixturecount');
let host,instances=0,maxMemory=0,calls=0,traps=0;
for(let i=0;i<cases.length;i++){
 if(!host||i%16===0){host=await prepared.fresh();instances++;}const c=cases[i],s=c.input;if(c.id!==i||s.effect_records120.length)throw Error('Case/domain');
 const{memory,allocate,roles,hostCalls}=host,G=allocate(8192),V=allocate(128),Q=allocate(32*56),U=allocate(Math.max(1,s.units.length)*424),M=allocate(128*16),N=allocate(c.zone_id.length);
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),w=(p,x)=>d().setUint32(p,x>>>0,true),r=p=>d().getUint32(p,true),g=(o,x)=>w(G+o,x);
 const number=x=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,x,true);return v.getFloat32(0,true);};
 bytes().set(Buffer.from(c.zone_id),N);g(184,N);g(188,c.zone_id.length);g(2348,V);w(V+32,0xffffffff);w(V+56,0xffffffff);w(V+116,s.flat_height_bits);d().setUint8(V+120,Number(s.flat_height_enabled));
 g(1820,32);g(1824,Q);g(1828,s.delayed_records.length);s.delayed_storage.forEach((x,j)=>bytes().set(Buffer.from(x,'hex'),Q+j*56));
 g(1808,0);g(1812,8);g(1816,0);g(1784,s.units.length);g(1788,U);g(1792,s.units.length);s.units.forEach((x,j)=>bytes().set(Buffer.from(x,'hex'),U+j*424));
 g(1880,128);g(1884,M);g(1888,0);g(2364,s.clock2364_bits);g(1644,s.action_sequence1644);g(2412,s.movement_sequence2412);
 s.player_xyz_bits.forEach((x,j)=>g(1416+4*j,x));s.player_action_words.forEach((x,j)=>g(416+4*j,x));s.rng_words.forEach((x,j)=>g(1720+4*j,x));g(2408,s.spawn_counter2408);
 d().setBigUint64(G+1336,BigInt(s.source_id),true);d().setUint8(G+2587,s.phase2587);d().setUint8(G+2582,s.mode2582);g(2528,s.local_peer2528);
 const stages=[],physical=[];let trappedCase=false;
 for(const op of c.ops){
  g(2352,op.now_bits);for(const[k,v]of Object.entries(op.changes||{})){if(k==='local_peer2528')g(2528,v);else if(k==='phase2587')d().setUint8(G+2587,v);else throw Error('Unknownchange');}
  let trapped=false;
  try{roles.effect_tick(G,number(op.dt_bits));}catch(error){if(!(error instanceof WebAssembly.RuntimeError)||error.message!=='unreachable')throw error;trapped=true;traps++;trappedCase=true;}
  calls++;if(hostCalls.length)throw Error('Originalhostimport');
  const n=r(G+1828),p=r(G+1824),len=r(G+1888),mp=r(G+1884);if(n>32||len>128||r(G+1820)!==32||r(G+1816)!==0)throw Error('Vectorbudget');
  const backing=Buffer.from(bytes().slice(p,p+32*56)),messages=Array.from({length:len},(_,j)=>{const q=mp+j*16,ptr=r(q+4),size=r(q+8);if(size>65536||ptr+size>memory.buffer.byteLength)throw Error('Messagebudget');return{opcode:d().getUint16(q+12,true),payload_hex:Buffer.from(bytes().slice(ptr,ptr+size)).toString('hex')};});
  stages.push({delayed_records:Array.from({length:n},(_,j)=>Buffer.from(bytes().slice(p+j*56,p+(j+1)*56)).toString('hex')),
   delayed_storage:Array.from({length:32},(_,j)=>backing.subarray(j*56,(j+1)*56).toString('hex')),delayed_storage_sha256:createHash('sha256').update(backing).digest('hex'),
   units:s.units.map((_,j)=>Buffer.from(bytes().slice(U+j*424,U+(j+1)*424)).toString('hex')),clock2364_bits:r(G+2364),action_sequence1644:r(G+1644),movement_sequence2412:r(G+2412),
   player_xyz_bits:[0,1,2].map(j=>r(G+1416+4*j)),player_action_words:Array.from({length:6},(_,j)=>r(G+416+4*j)),rng_words:[0,1,2,3].map(j=>r(G+1720+4*j)),spawn_counter2408:r(G+2408),effect120_count:r(G+1816),message_opcodes:messages.map(x=>x.opcode),entry_trap:trapped});
  physical.push(messages);
  if(trapped)break;
 }
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:i,stages,physical_message_payloads:physical})+'\n');if(trappedCase)host=null;
}
await fs.writeFile(`${directory}/effect-system135-runtime.json`,JSON.stringify({cases:cases.length,calls,expected_traps:traps,full_original_function:915,all_callees_unchanged:true,fresh_instances:instances,max_memory_bytes:maxMemory,
 denied_imports:878,host_calls:0,original_allocator:91941,node:process.version,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
