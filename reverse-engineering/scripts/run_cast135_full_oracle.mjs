// Fixed135 complete target query/cast/auto-cast/hit consumers; no body replacement.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['cast','auto_cast','process_hits','query_targets']);
const raw=await fs.readFile(casefile,'utf8');if(raw.length>32*1024*1024)throw Error('Fixture byte budget');
const cases=raw.trim().split('\n').map(JSON.parse);if(!cases.length||cases.length>10000)throw Error('Fixture count budget');
let host,instances=0,maxMemory=0;
for(let i=0;i<cases.length;i++){
 if(i%24===0){host=await prepared.fresh();instances++;}
 const c=cases[i];if(c.id!==i)throw Error('Case ID/order differs');const s=c.input;
 const {roles,memory,allocate,hostCalls}=host,G=allocate(8192),U=allocate(Math.max(1,s.units.length)*424);
 let d=new DataView(memory.buffer);let bytes=new Uint8Array(memory.buffer);
 const refresh=()=>{d=new DataView(memory.buffer);bytes=new Uint8Array(memory.buffer);};
 const w=(p,x)=>d.setUint32(p,x>>>0,true),r=p=>d.getUint32(p,true),number=bits=>{const x=new DataView(new ArrayBuffer(4));x.setUint32(0,bits,true);return x.getFloat32(0,true);};
 const alloc=n=>{const p=allocate(n);refresh();return p;};
 w(G+1788,U);w(G+1792,s.units.length);w(G+2352,s.now_bits);w(G+1416,s.player_xy[0]);w(G+1420,s.player_xy[1]);
 s.units.forEach((u,j)=>{const p=U+j*424;d.setBigUint64(p+112,BigInt(u.guid),true);w(p,u.marker);w(p+40,u.kind_40);w(p+64,u.kind_64);w(p+244,u.elite_244);w(p+416,u.elite_416);w(p+284,5415572);w(p+288,u.hp_bits);w(p+292,u.max_hp_bits);w(p+372,u.priority_until372_bits);w(p+408,u.phase_until408_bits);w(p+412,u.phase_until412_bits);d.setBigUint64(p+32,BigInt(u.linked_id),true);w(p+340,u.movement_time_bits);w(p+344,u.duration_bits);for(const [off,v]of[[316,u.from_xy],[328,u.to_xy]]){w(p+off,v[0]);w(p+off+4,v[1]);}});
 if(c.mode==='query'){
  const out=alloc(16),center=alloc(12),excluded=alloc(Math.max(8,s.excluded.length*8));w(center,s.player_xy[0]);w(center+4,s.player_xy[1]);s.excluded.forEach((v,j)=>d.setBigUint64(excluded+j*8,BigInt(v),true));
  roles.query_targets(out,G,center,number(s.query_radius_bits),excluded,s.excluded.length);refresh();
  const p=r(out+4),n=r(out+8);if(n>s.units.length||p+n*8>memory.buffer.byteLength)throw Error('Query result bound');
  process.stdout.write(JSON.stringify({id:i,targets:Array.from({length:n},(_,j)=>d.getBigUint64(p+j*8,true).toString())})+'\n');
 }else{
  const automatic=c.mode.startsWith('auto'),many=c.mode==='auto-many';
  const definitions=many?c.definitions:[c.definition],owned=many?c.owned_hex_list:[c.owned_hex],nactive=definitions.length;
  const A=alloc(nactive*80),T=alloc(nactive*84);
  definitions.forEach((def,j)=>{if(Buffer.from(bytes.subarray(def.pointer,def.pointer+88)).toString('hex')!==(many?c.definition_hex_list[j]:c.definition_hex))throw Error('Actual135 definition identity differs');
   const record=Buffer.from(owned[j],'hex');if(record.length!==80)throw Error('Owned80B budget');bytes.set(record,A+j*80);bytes.set(record,T+j*84);w(T+j*84+80,many?c.override_bits_list[j]:s.override_bits);});
  w(G+1656,nactive);w(G+1660,A);w(G+1664,nactive);w(G+644,nactive);w(G+648,T);w(G+652,automatic?nactive:0);
  d.setUint8(G+2587,s.phase);d.setUint8(G+908,s.context908);d.setBigUint64(G+1336,BigInt(s.source_id),true);d.setBigUint64(G+776,BigInt(s.current_target_id),true);
  for(const [offset,key]of[[1536,'max_hp_bits'],[1440,'current_hp_bits'],[1540,'damage_multiplier_bits'],[1544,'cooldown_multiplier_bits'],[1548,'critical_chance_bits'],[1552,'critical_multiplier_bits'],[1580,'area_multiplier_bits']])w(G+offset,s[key]);
  w(G+1592,s.extra_targets);s.rng_words.forEach((v,j)=>w(G+1720+j*4,v));
  const snapshot=()=>{refresh();const n=r(G+1852),p=r(G+1848);if(n>4096||p+n*112>memory.buffer.byteLength)throw Error('Queued record bound');
   const queued=Array.from({length:n},(_,j)=>{const q=p+j*112;return{target_id:d.getBigUint64(q+64,true).toString(),source_id:d.getBigUint64(q+72,true).toString(),due_bits:r(q+92),spell_id:r(q+96),damage_bits:r(q+100),critical:d.getUint8(q+104),school:d.getUint8(q+106),context908:d.getUint8(q+105)}});
   const lists=[672,684,732].map(poff=>{const p=r(G+poff),n=r(G+poff+4);if(n>1024)throw Error('Spell set budget');return Array.from({length:n},(_,j)=>r(p+j*4))});
   return{hp_bits:s.units.map((_,j)=>r(U+j*424+288)),markers:s.units.map((_,j)=>r(U+j*424)),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),accounted_total_hex:d.getBigUint64(G+984,true).toString(16).padStart(16,'0'),queued,attempted_spell_sets:lists,active_remaining_bits:many?Array.from({length:nactive},(_,j)=>r(T+j*84+8)):(automatic?r(T+8):null)};};
  const stages=[];
  if(automatic){
   for(const dt of c.dt_bits){roles.auto_cast(G,number(dt));stages.push({kind:'auto',snapshot:snapshot()});}
  }else{const success=roles.cast(G,A);stages.push({kind:'cast',success,snapshot:snapshot()});}
  for(const now of c.process_at_bits){w(G+2352,now);roles.process_hits(G);stages.push({kind:'process',snapshot:snapshot()});}
  process.stdout.write(JSON.stringify({id:i,stages})+'\n');
 }
 if(hostCalls.length)throw Error('Original host call attempted');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/cast135-runtime.json`,JSON.stringify({cases:cases.length,fresh_instances:instances,fresh_every:24,max_memory_bytes:maxMemory,memory_page_limit:512,actual_host_calls:0,denied_function_imports:878,original_allocator:91941,original_full_functions:[922,916,1754,27562],unchanged_callees:true,application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false,node:process.version},null,2)+'\n');
