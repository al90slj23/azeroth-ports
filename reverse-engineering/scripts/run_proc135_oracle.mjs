// Complete984/8157/914/922/2862 entries; all callees unchanged,878 imports throw.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['proc_event','proc_gate','damage','cast','collect_pickups']);
const text=await fs.readFile(casefile,'utf8');if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture bytes');
const cases=text.trim().split('\n').map(JSON.parse);if(cases.length>5000)throw Error('Case budget');
const num=x=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,x,true);return d.getFloat32(0,true);};
let host,instances=0,calls=0,maxMemory=0;
for(let i=0;i<cases.length;i++){
 const c=cases[i],s=c.level,t=s.stats,src=s.sources;if(c.id!==i)throw Error('Case order');
 if(i%24===0){host=await prepared.fresh();instances++;}
 const {memory,roles,allocate,hostCalls}=host,G=allocate(8192);
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),w=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw Error('u32');d().setUint32(p,x,true);};
 const b=(p,x)=>d().setUint8(p,x),r=p=>d().getUint32(p,true);
 for(const [offset,value]of Object.entries(s.derived_bits))w(G+Number(offset),value);
 b(G+360,t.class_byte);b(G+361,t.race_byte);b(G+2582,t.flag2574);b(G+387,s.heal_gate387);b(G+2587,s.phase2587);
 w(G+1536,t.old_max_hp_bits);w(G+1440,t.current_hp_bits);w(G+2352,t.now_bits);w(G+1648,t.previous_speed_bits);w(G+268,t.conditional268_bits);
 for(const [old,current]of[[1532,1444],[1536,1448],[768,768]])w(G+current,t[`pool${old}_bits`]);
 w(G+1344,t.conditional1344_id);w(G+1348,t.conditional1348_bits);w(G+756,s.pool756_bits);w(G+1432,s.progression.level);w(G+1436,s.progression.xp);
 s.rng_words.forEach((x,j)=>w(G+1720+j*4,x));
 d().setBigUint64(G+1336,999n,true);if(Object.keys(s.player_fields).length)throw Error('Initial tree must be empty');
 const vector=(rows,stride,cap,ptr,len,write)=>{if(rows.length>128)throw Error('Vector bound');const p=allocate(Math.max(8,rows.length*stride));if(cap!==null)w(G+cap,rows.length);w(G+ptr,p);w(G+len,rows.length);rows.forEach((x,j)=>write(p+j*stride,x));return p;};
 vector(src.passives,8,null,1696,1700,(p,x)=>{w(p,x.tag);w(p+4,x.value_bits);});
 vector(src.item_modifiers,8,2024,2028,2032,(p,x)=>{b(p,x.tag);w(p+4,x.value_bits);});
 vector(src.adjustments,16,null,1672,1676,(p,x)=>{const q=allocate(40);w(p,q);w(p+4,x.value_bits);w(q+32,x.definition32_bits);b(q+36,x.tag);});
 if(src.owned_skills.length||src.live_effects.length)throw Error('Unhandled source domain');
 const D=vector(c.definitions36,36,2048,2052,2056,(p,x)=>{const raw=Buffer.from(x,'hex');if(raw.length!==36)throw Error('Definition36');bytes().set(raw,p);});
 vector(src.timed_records,12,596,600,604,(p,x)=>{w(p,x.definition_index);w(p+4,x.stack_count);w(p+8,x.expires_bits);});
 for(const [cap,ptr,len]of[[1656,1660,1664],[1844,1848,1852],[1868,1872,1876],[2144,2148,2152],[2156,2160,2164]]){w(G+cap,0);w(G+ptr,8);w(G+len,0);}
 const cast=c.cast,units=cast?.units??[{guid:'1',hp_bits:0x49742400,max_hp_bits:0x49742400,marker:0,kind_40:-1,kind_64:-1,elite_244:-1,elite_416:0,definition_pointer:5415572,from_xy:[0,0],to_xy:[0,0],movement_time_bits:0,duration_bits:0}];
 const U=vector(units,424,1784,1788,1792,(p,x)=>{
  d().setBigUint64(p+112,BigInt(x.guid),true);w(p,x.marker);for(const [o,k]of[[40,'kind_40'],[64,'kind_64'],[244,'elite_244'],[416,'elite_416']])w(p+o,x[k]>>>0);
  w(p+284,x.definition_pointer);w(p+288,x.hp_bits);w(p+292,x.max_hp_bits);w(p+340,x.movement_time_bits);w(p+344,x.duration_bits);
  for(const [o,xy]of[[316,x.from_xy],[328,x.to_xy]]){w(p+o,xy[0]);w(p+o+4,xy[1]);}
 });
 const name=allocate(6,1);bytes().set(Buffer.from('elwynn'),name);w(G+184,name);w(G+188,6);w(G+2540,1);
 const V=allocate(128);w(G+2348,V);b(V+120,1);w(V+32,0xffffffff);w(V+56,0xffffffff);
 let A=0;
 if(c.kind==='cast'){
  cast.player_xy.forEach((x,j)=>w(G+1416+j*4,x));
  for(const [o,k]of[[1540,'damage_multiplier_bits'],[1544,'cooldown_multiplier_bits'],[1548,'critical_chance_bits'],[1552,'critical_multiplier_bits'],[1580,'area_multiplier_bits']])w(G+o,cast[k]);
  w(G+1592,cast.extra_targets);cast.rng_words.forEach((x,j)=>w(G+1720+j*4,x));
  if(Buffer.from(bytes().subarray(c.definition.pointer,c.definition.pointer+88)).toString('hex')!==c.definition_hex)throw Error('Real cast definition differs');
  A=allocate(80);bytes().set(Buffer.from(c.owned_hex,'hex'),A);w(G+1656,1);w(G+1660,A);w(G+1664,1);
 }
 const tree=()=>{const fields=[],seen=new Set();const walk=(p,depth)=>{if(!p||p+76>memory.buffer.byteLength||seen.has(p)||seen.size>128)throw Error('Tree bounds');seen.add(p);const n=d().getUint16(p+50,true);if(n>11||depth>4)throw Error('Tree shape');for(let j=0;j<n;j++){if(depth)walk(r(p+76+j*4),depth-1);fields.push([d().getUint16(p+52+j*2,true),r(p+4+j*4)]);}if(depth)walk(r(p+76+n*4),depth-1);};const root=r(G+2476);if(root)walk(root,r(G+2480));return Object.fromEntries(fields);};
 const snapshot=()=>{const p=r(G+600),n=r(G+604);if(n>128||p+n*12>memory.buffer.byteLength)throw Error('Timed bound');
  return{derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,r(G+1536+j*4)])),current_hp_bits:r(G+1440),
   auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,r(G+o)])),speed_bits:r(G+1648),player_fields:tree(),
   timed_words:Array.from({length:n},(_,j)=>[r(p+j*12),r(p+j*12+4),r(p+j*12+8)]),
   definitions36:c.definitions36.map((_,j)=>Buffer.from(bytes().subarray(D+j*36,D+j*36+36)).toString('hex')),
   unit_hp_bits:units.map((_,j)=>r(U+j*424+288)),markers:units.map((_,j)=>r(U+j*424)),
   accounted_total_hex:d().getBigUint64(G+984,true).toString(16).padStart(16,'0'),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4))};};
 const stages=[];
 for(const op of c.ops){
  w(G+2352,op.now_bits);
  if(op.kind==='gate'){const q=allocate(16);bytes().set(Buffer.from(op.gate_hex,'hex'),q);const e=allocate(36);bytes().set(Buffer.from(op.event_hex,'hex'),e);stages.push({matches:roles.proc_gate(G,q,e)});}
  else if(op.kind==='event'){const e=allocate(36);bytes().set(Buffer.from(op.event_hex,'hex'),e);roles.proc_event(G,e,0);stages.push(snapshot());}
  else if(op.kind==='damage'){roles.damage(G,BigInt(op.target_id),num(op.amount_bits),op.spell_id,0,0,0);stages.push(snapshot());}
  else if(op.kind==='cast'){roles.cast(G,A);stages.push(snapshot());}
  else if(op.kind==='collect'){roles.collect_pickups(G);stages.push(snapshot());}
  else throw Error('Operation');calls++;
 }
 if(hostCalls.length)throw Error('Host call attempted');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:i,stages})+'\n');
}
await fs.writeFile(`${directory}/proc135-runtime.json`,JSON.stringify({cases:cases.length,entry_calls:calls,
 original_functions:[984,8157,914,922,2862],original_internal_callees_unchanged:true,original_allocator:91941,
 fresh_every:24,fresh_instances:instances,max_memory_bytes:maxMemory,actual_host_calls:0,denied_imports:878,
 application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false,node:process.version},null,2)+'\n');
