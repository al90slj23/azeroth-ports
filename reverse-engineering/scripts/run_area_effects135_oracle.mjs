// Full original922→3757→914→2244; no original bodies/callees are replaced.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtureFile]=process.argv.slice(2),prepared=await prepareFull135(directory,['cast','area_tick']);
const text=await fs.readFile(fixtureFile,'utf8');if(Buffer.byteLength(text)>64*1024*1024)throw Error('Fixture byte budget');
const cases=JSON.parse(text);if(!cases.length||cases.length>3000)throw Error('Fixture budget');
const OFF=[0,4,40,64,120,124,144,148,152,156,160,164,240,244,288,292,316,320,324,328,332,336,340,344,356,368,372,380,388,408,412,416];
let host,instances=0,maxMemory=0,calls=0;
for(let index=0;index<cases.length;index++){
 if(index%16===0){host=await prepared.fresh();instances++;}
 const c=cases[index],s=c.input;if(c.id!==index)throw Error('Case order');
 const {roles,memory,allocate,hostCalls}=host,G=allocate(8192),V=allocate(128),U=allocate(Math.max(1,s.unit_hex.length)*424),A=allocate(80),E=allocate(128*88);
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),w=(p,x)=>d().setUint32(p,x>>>0,true),r=p=>d().getUint32(p,true);
 const g=(o,x)=>w(G+o,x),num=x=>{const q=new DataView(new ArrayBuffer(4));q.setUint32(0,x,true);return q.getFloat32(0,true);};
 g(2348,V);w(V+32,0xffffffff);w(V+56,0xffffffff);w(V+116,s.height_bits);d().setUint8(V+120,1);
 g(1784,s.unit_hex.length);g(1788,U);g(1792,s.unit_hex.length);s.unit_hex.forEach((h,j)=>bytes().set(Buffer.from(h,'hex'),U+j*424));
 g(1796,128);g(1800,E);g(1804,c.initial_areas.length);c.initial_areas.forEach((h,j)=>bytes().set(Buffer.from(h,'hex'),E+j*88));
 g(1416,s.player_xy[0]);g(1420,s.player_xy[1]);g(1424,s.height_bits);g(2408,s.counter);
 d().setBigUint64(G+1336,BigInt(s.source_id),true);d().setUint8(G+2587,1);d().setUint8(G+360,1);d().setUint8(G+361,1);g(1432,1);g(488,s.busy488);d().setUint8(G+908,s.context908);
 for(const [o,k]of[[1536,'max_hp_bits'],[1440,'current_hp_bits'],[1540,'damage_multiplier_bits'],[1548,'critical_chance_bits'],[1552,'critical_multiplier_bits'],[1580,'area_multiplier_bits']])g(o,s[k]);
 s.rng_words.forEach((x,j)=>g(1720+4*j,x));
 let P=0;
 if(s.death_zone!==undefined){
  const name=allocate(s.zone_id.length);bytes().set(Buffer.from(s.zone_id),name);g(184,name);g(188,s.zone_id.length);
  P=allocate(128*56);new Uint8Array(memory.buffer,P,128*56).fill(0xa5);g(1868,128);g(1872,P);g(1876,0);g(2412,19);g(2420,0x40200000);
 }
 const snapshot=()=>{const n=r(G+1804),p=r(G+1800);if(n>128||p+n*88>memory.buffer.byteLength)throw Error('Area vector budget');
  const result={area_records:Array.from({length:n},(_,j)=>Buffer.from(bytes().slice(p+j*88,p+(j+1)*88)).toString('hex')),counter:r(G+2408),
   unit_words:s.unit_hex.map((_,j)=>OFF.map(o=>r(U+j*424+o))),rng_words:[0,1,2,3].map(j=>r(G+1720+4*j)),
   accounted_total_hex:d().getBigUint64(G+984,true).toString(16).padStart(16,'0'),player_hp_bits:r(G+1440),
   attempted_spell_sets:[672,684,732].map(o=>{const n=r(G+o+4),p=r(G+o);if(n>128)throw Error('Ledger budget');return Array.from({length:n},(_,j)=>r(p+j*4));})};
  if(P){const n=r(G+1876),p=r(G+1872);if(n>128)throw Error('Pickup budget');result.pickup_hex=Array.from({length:n},(_,j)=>Buffer.from(bytes().slice(p+j*56,p+(j+1)*56)).toString('hex'));result.message_sequence=r(G+2412);result.kill_cost_bits=r(G+2420);}
  return result;};
 const stages=[];
 for(const op of c.ops){
  g(2352,op.now_bits);let success=null;
  for(const [name,value]of Object.entries(op.cast_changes||{})){
   const offset={damage_multiplier_bits:1540,critical_chance_bits:1548,critical_multiplier_bits:1552,area_multiplier_bits:1580}[name];
   if(offset===undefined)throw Error('Unknown explicit profile change');g(offset,value);
  }
  if(op.kind==='cast'){
   if(Buffer.from(bytes().slice(op.definition.pointer,op.definition.pointer+88)).toString('hex')!==op.definition.raw88_hex)throw Error('Definition identity');
   const len=r(G+1804),p=r(G+1800);if(len>=128)throw Error('Append capacity');bytes().set(Buffer.from(op.slot_hex,'hex'),p+len*88);
   bytes().set(Buffer.from(op.owned_hex,'hex'),A);success=roles.cast(G,A);
  }else roles.area_tick(G);
  calls++;if(hostCalls.length)throw Error('Original host import attempted');stages.push({success,snapshot:snapshot()});
 }
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:index,stages})+'\n');
}
await fs.writeFile(`${directory}/area-effects135-runtime.json`,JSON.stringify({cases:cases.length,calls,fresh_instances:instances,max_memory_bytes:maxMemory,
 full_original_functions:[922,3757],unchanged_internal_callees:[13151,27562,2825,85719,914,2244],denied_imports:878,host_calls:0,
 original_allocator:91941,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false,node:process.version},null,2)+'\n');
