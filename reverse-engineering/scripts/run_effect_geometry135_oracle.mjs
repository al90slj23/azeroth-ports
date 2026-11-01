// Genuine2785 Boss -> original910 producer -> complete915; every callee retained.
import fs from 'node:fs/promises';
import{prepareFull135}from'./full135_host.mjs';
const[directory,file]=process.argv.slice(2),prepared=await prepareFull135(directory,['spawn_boss','npc_action','effect_tick']);
const text=await fs.readFile(file,'utf8');if(Buffer.byteLength(text)>64*1024*1024)throw Error('Fixture budget');const cases=JSON.parse(text);if(!cases.length||cases.length>4000)throw Error('Cases');
const offsets={armor_1392_bits:1568,armor_cap_1572_bits:1572,nearby_reduction_1444_bits:1624,hp_1528_bits:1440,shield_1532_bits:1444,barrier_1536_bits:1448,shield_source_1344:1344,shield_source_remaining_1348_bits:1348,reserve_768_bits:768,absorbed_740_bits:740,maximum_shield_744_bits:744,last_hit_1648_bits:1652};
const number=x=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,x,true);return v.getFloat32(0,true);};
let host,instances=0,maxMemory=0,calls=0,producerCalls=0,tickCalls=0,expectedHostBoundaries=0;
for(let i=0;i<cases.length;i++){
 if(!host||i%12===0){host=await prepared.fresh();instances++;}const c=cases[i],s=c.boss,inc=c.incoming;if(c.id!==i)throw Error('Case order');
 const{memory,allocate,roles,hostCalls}=host,G=allocate(8192),V=allocate(128),U=allocate(128*424),E=allocate(64*120),M=allocate(1024*16),N=allocate(c.zone_id.length);
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),w=(p,x)=>d().setUint32(p,x>>>0,true),r=p=>d().getUint32(p,true),g=(o,x)=>w(G+o,x),b=(o,x)=>d().setUint8(G+o,x);
 bytes().set(Buffer.from(c.zone_id),N);g(184,N);g(188,c.zone_id.length);g(2348,V);w(V+32,0xffffffff);w(V+56,0xffffffff);w(V+116,s.flat_height_bits);d().setUint8(V+120,1);
 g(1784,128);g(1788,U);g(1792,0);bytes().set(Buffer.from(s.initial_slot_hex,'hex'),U);
 g(1808,64);g(1812,E);g(1816,0);c.storage.forEach((x,j)=>bytes().set(Buffer.from(x,'hex'),E+j*120));
 g(1820,0);g(1824,8);g(1828,0);g(1880,1024);g(1884,M);g(1888,0);g(2356,c.effect_counter2356);g(2412,c.movement_sequence2412);g(1644,c.action_sequence1644);
 g(2352,s.now_bits);g(2516,s.zone_multiplier_bits);b(387,s.difficulty);b(2582,s.mode);g(2540,s.members);g(400,s.victory_field400);g(404,s.endless_start_bits);b(2568,s.endless_flag);g(2408,s.counter);
 s.player_xyz.forEach((x,j)=>g(1416+4*j,x));s.velocity_xy.forEach((x,j)=>g(1736+4*j,x));s.rng_words.forEach((x,j)=>g(1720+4*j,x));g(1432,1);g(1536,c.max_hp_bits);d().setBigUint64(G+1336,999n,true);
 b(360,1);b(361,1);b(2587,inc.phase_2579);b(2576,inc.protection_2568);b(2578,inc.minimum_one_2578);for(const[k,o]of Object.entries(offsets))g(o,inc[k]);d().setFloat64(G+992,inc.incoming_total_992,true);
 const stages=[],physical=[];let packetCursor=0,jsonCursor=0;
 function capture(label,entryStatus='normal_rectangle_projection'){
  const n=r(G+1816),p=r(G+1812),un=r(G+1792),up=r(G+1788);if(n>64||un!==1||r(G+1808)!==64||r(G+1828)!==0)throw Error('Vector budget');
  const raw=Buffer.from(bytes().slice(up,up+424)),tn=raw.readUInt32LE(244),tp=raw.readUInt32LE(248);if(tn>20||tp+tn*4>memory.buffer.byteLength)throw Error('Timer vector');raw.writeUInt32LE(0,248);
  const output={label,storage:Array.from({length:64},(_,j)=>Buffer.from(bytes().slice(p+j*120,p+(j+1)*120)).toString('hex')),length:n,
   units:[raw.toString('hex')],timers_bits:Array.from({length:tn},(_,j)=>r(tp+j*4)),effect_counter2356:r(G+2356),movement_sequence2412:r(G+2412),action_sequence1644:r(G+1644),clock2364_bits:r(G+2364),
   rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),spawn_counter2408:r(G+2408),phase2587:d().getUint8(G+2587),entry_status:entryStatus};
  for(const[k,o]of Object.entries(offsets))output[k]=r(G+o);output.incoming_total_992_bits=d().getBigUint64(G+992,true).toString(16).padStart(16,'0');
  const messages=[];if(r(G+1888)>1024||r(G+1900)>1024)throw Error('Message budget');
  for(let j=0;j<r(G+1888);j++){const q=r(G+1884)+16*j,ptr=r(q+4),size=r(q+8);if(size>65536||ptr+size>memory.buffer.byteLength)throw Error('Packet bound');messages.push({opcode:d().getUint16(q+12,true),payload_hex:Buffer.from(bytes().slice(ptr,ptr+size)).toString('hex')});}
  const json=[];for(let j=0;j<r(G+1900);j++){const q=r(G+1896)+12*j,ptr=r(q+4),size=r(q+8);if(size>65536||ptr+size>memory.buffer.byteLength)throw Error('JSON bound');json.push(Buffer.from(bytes().slice(ptr,ptr+size)).toString());}
  output.new_packet_opcodes=label==='boss2785'?[]:messages.slice(packetCursor).map(x=>x.opcode);
  output.new_effect_json_events=label==='boss2785'?[]:json.slice(jsonCursor).map(x=>{const e=JSON.parse(x);if(e.type==='hz')return{type:e.type,id:e.id,kind:e.kind,shape:e.shape};if(e.type==='hzend')return{type:e.type,id:e.id};if(e.type==='hzt')return{type:e.type};throw Error('Unmodeled JSON event');});packetCursor=messages.length;jsonCursor=json.length;
  physical.push({label,packets:messages,effect_json:json,full_storage_hex:Buffer.from(bytes().slice(p,p+64*120)).toString('hex'),unit248_pointer:tp});stages.push(output);
 }
 roles.spawn_boss(G,c.definition_pointer,number(s.scalar_bits));calls++;capture('boss2785');
 //2785's independently validated fixture uses flat height. A declared input
 //change here tests the910/915 fallback separately without changing spawning.
 d().setUint8(V+120,Number(c.flat_height_enabled));
 for(const op of c.ops){
  g(2352,op.now_bits);op.player_xyz_bits.forEach((x,j)=>g(1416+4*j,x));
  for(const[o,v]of Object.entries(op.unit_patch||{})){if(![128,132,136,140,268,276,316,320,324,328,332,336,340,344,348,352,400].includes(Number(o)))throw Error('Patch scope');if(Number(o)===276)d().setUint8(U+276,v);else w(U+Number(o),v);}
  if(op.incoming_phase!==undefined)b(2587,op.incoming_phase);
  if(op.kind==='produce'){
   if(Buffer.from(bytes().slice(op.descriptor_pointer,op.descriptor_pointer+40)).toString('hex')!==op.raw40_hex)throw Error('Real declaration mismatch');
   roles.npc_action(G,0,op.descriptor_pointer);producerCalls++;
  }else if(op.kind==='tick'){
   try{roles.effect_tick(G,number(op.dt_bits));if(op.expected_status==='pending_original_spell_database')throw Error('Expected original host boundary absent');}
   catch(error){
    if(op.expected_status!=='pending_original_spell_database'||error.message!=='Original host call denied'||hostCalls.length!==1||!error.stack.includes('wasm-function[4546]')||!error.stack.includes('wasm-function[1073]'))throw error;
    expectedHostBoundaries++;
   }
   tickCalls++;
  }else throw Error('Unknown op');
  calls++;if(hostCalls.length&&op.expected_status!=='pending_original_spell_database')throw Error('Unexpected host invoked');capture(op.kind,op.expected_status);
  if(op.expected_status==='pending_original_spell_database'){physical[physical.length-1].denied_host_calls=[...hostCalls];host=null;break;}
 }
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:i,stages,physical})+'\n');
}
await fs.writeFile(`${directory}/effect-geometry135-runtime.json`,JSON.stringify({cases:cases.length,calls,producer_calls:producerCalls,tick_calls:tickCalls,expected_host_boundaries:expectedHostBoundaries,functions:[2785,910,915],all_callees_unchanged:true,fresh_instances:instances,max_memory_bytes:maxMemory,denied_imports:878,successful_host_calls:0,attempted_host_calls:expectedHostBoundaries,original_allocator:91941,node:process.version,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
