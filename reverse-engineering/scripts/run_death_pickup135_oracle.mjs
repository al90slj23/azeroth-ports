// Full original922/1754 ->914/1417 ->2862/4630/1512/2159.
// No application entry; all original host imports throw.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,casesFile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['cast','process_hits','collect_pickups']);
const text=await fs.readFile(casesFile,'utf8');
if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture byte budget');
const cases=text.trim().split('\n').filter(Boolean).map(JSON.parse);
if(!cases.length||cases.length>3000)throw Error('Fixture count budget');
let host,instances=0,calls=0,maxMemory=0,actualHostCalls=0;
for(let index=0;index<cases.length;++index){
  if(index%16===0){host=await prepared.fresh();instances++;}
  const c=cases[index],s=c.level,t=s.stats,src=s.sources;
  if(c.id!==index)throw Error('Case identity/order');
  const {memory,allocate,roles,hostCalls}=host;
  const view=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer);
  const u32=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw Error('u32');view().setUint32(p,x,true);};
  const u8=(p,x)=>{if(!Number.isInteger(x)||x<0||x>255)throw Error('u8');view().setUint8(p,x);};
  const read32=p=>view().getUint32(p,true);
  const G=allocate(8192);
  for(const [cap,ptr,len,align] of [[1656,1660,1664,4],[1904,1908,1912,4],
    [1952,1956,1960,4],[2024,2028,2032,4],[2048,2052,2056,4],
    [2084,2088,2092,4],[2096,2100,2104,4],[1892,1896,1900,4]]){
    u32(G+cap,0);u32(G+ptr,align);u32(G+len,0);
  }
  for(const [offset,value] of Object.entries(s.derived_bits))u32(G+Number(offset),value);
  u8(G+360,t.class_byte);u8(G+361,t.race_byte);u8(G+2582,t.flag2574);
  u32(G+1536,t.old_max_hp_bits);u32(G+1440,t.current_hp_bits);u32(G+2352,t.now_bits);
  u32(G+1648,t.previous_speed_bits);u32(G+268,t.conditional268_bits);
  for(const [oldOffset,newOffset] of [[1532,1444],[1536,1448],[768,768]])u32(G+newOffset,t[`pool${oldOffset}_bits`]);
  u32(G+1344,t.conditional1344_id);u32(G+1348,t.conditional1348_bits);u32(G+756,s.pool756_bits);
  u32(G+1432,s.progression.level);u32(G+1436,s.progression.xp);u32(G+2376,s.progression.pending_upgrades);
  for(const name of ['phase2587','selection_kind2585','flags2576','gate2572','flags2573'])u8(G+Number(name.match(/\d+/)[0]),s[name]);
  u8(G+387,s.heal_gate387);u8(G+275,s.choice_inputs.flag275);u8(G+2581,s.choice_inputs.flag2581);
  u8(G+2566,0);u32(G+2400,s.generation_counter2400);
  s.rng_words.forEach((x,i)=>u32(G+1720+i*4,x));
  view().setBigUint64(G+1336,999n,true);
  if(Object.keys(s.player_fields).length)throw Error('Initial logical tree must be explicitly empty');
  const vector=(entries,stride,cap,ptr,len,write)=>{
    if(!Array.isArray(entries)||entries.length>128)throw Error('Vector budget');
    if(!entries.length)return;
    const p=allocate(entries.length*stride,4);if(cap!==null)u32(G+cap,entries.length);
    u32(G+ptr,p);u32(G+len,entries.length);entries.forEach((entry,i)=>write(p+i*stride,entry));
  };
  vector(src.passives,8,null,1696,1700,(p,e)=>{u32(p,e.tag);u32(p+4,e.value_bits);});
  vector(src.item_modifiers,8,2024,2028,2032,(p,e)=>{u8(p,e.tag);u32(p+4,e.value_bits);});
  vector(src.adjustments,16,null,1672,1676,(p,e)=>{const def=allocate(40);u32(p,def);u32(p+4,e.value_bits);u32(def+32,e.definition32_bits);u8(def+36,e.tag);});
  vector(src.owned_skills,8,null,172,176,(p,e)=>{const def=allocate(40),raw=Buffer.from(e[0],'ascii'),name=allocate(Math.max(raw.length,1));bytes().set(raw,name);u32(p,def);u8(p+4,e[1]);u32(def+32,name);u32(def+36,raw.length);});
  vector(src.definitions,36,2048,2052,2056,(p,e)=>{
    u32(p,e.kind);u32(p+4,e.value4_bits);u32(p+20,e.value20_bits);u8(p+32,e.modifier_tag);
    if(e.kind===42){const obj=allocate(64);u8(obj+41,e.summon_state41);u32(p+4,obj);}
  });
  vector(src.timed_records,12,null,600,604,(p,e)=>{u32(p,e.definition_index);u32(p+4,e.stack_count);u32(p+8,e.expires_bits);});
  vector(src.live_effects,32,null,1708,1712,(p,e)=>{u32(p+8,e.kind);u32(p+12,e.value_bits);u32(p+20,e.spell_id);u32(p+24,e.expires_bits);});
  vector(s.choice_inputs.owned,80,1656,1660,1664,(p,e)=>{const raw=Buffer.from(e.record_hex,'hex');if(raw.length!==80)throw Error('owned80B');bytes().set(raw,p);});
  const writeString=(p,value,capacity)=>{const raw=Buffer.from(value,'ascii');if(raw.length>128)throw Error('ID budget');const name=allocate(Math.max(raw.length,1));bytes().set(raw,name);if(capacity){u32(p,raw.length);u32(p+4,name);u32(p+8,raw.length);}else{u32(p,name);u32(p+4,raw.length);}};
  vector(s.choice_inputs.blocked_ids,8,2084,2088,2092,(p,e)=>writeString(p,e,false));
  vector(s.choice_inputs.banished_keys,12,2096,2100,2104,(p,e)=>writeString(p,e,true));
  const span=(p,n,max)=>{if(p<0||n<0||n>max||p+n>memory.buffer.byteLength)throw Error('Read budget');return new Uint8Array(memory.buffer,p,n);};
  const id=(p,n)=>Buffer.from(span(p,n,128)).toString('ascii');
  const candidates=()=>{
    const n=read32(G+1912),p=read32(G+1908);if(n>4)throw Error('Candidate budget');
    return Array.from({length:n},(_,i)=>{const a=p+i*80,tag=read32(a+60),r={variant:'',tier:read32(a+76),ability_id:'',owned_index:0,kinds:[],gold:0};
      if(tag===0x80000000){r.variant='new';r.ability_id=id(read32(a+64),read32(a+68));}
      else if(tag<0x80000000||tag===0x80000001){r.variant='upgrade';r.owned_index=read32(a+72);const def=read32(read32(G+1660)+r.owned_index*80);r.ability_id=id(read32(def+12),read32(def+16));r.kinds=Array.from(span(read32(a+64),read32(a+68),5));}
      else if(tag===0x80000004){r.variant='gold';r.gold=read32(a+64);}else throw Error('Candidate variant');return r;
    });
  };
  const tree=()=>{
    const root=read32(G+2476),depth=read32(G+2480);if(!root)return{};if(depth>4)throw Error('Tree depth budget');
    const fields=[],seen=new Set();
    const walk=(p,level)=>{if(!p||p+76>memory.buffer.byteLength||seen.has(p)||seen.size>128)throw Error('Tree node bounds');seen.add(p);const n=view().getUint16(p+50,true);if(n>11)throw Error('Node count');for(let j=0;j<n;++j){if(level)walk(read32(p+76+j*4),level-1);fields.push([view().getUint16(p+52+j*2,true),read32(p+4+j*4)]);}if(level)walk(read32(p+76+n*4),level-1);};
    walk(root,depth);return Object.fromEntries(fields);
  };

  const cs=c.control,cast=c.cast;
  u32(G+1416,cs.player_xyz[0]);u32(G+1420,cs.player_xyz[1]);u32(G+1424,cs.player_xyz[2]);
  u32(G+1704,src.live_effects.length);
  u32(G+1456,cs.currency.gold);u32(G+1100,cs.currency.earned);
  u32(G+2528,cs.currency.local_peer);u32(G+2540,cs.currency.member_count);
  const region=Buffer.from('elwynn','ascii'),regionPtr=allocate(region.length,1);bytes().set(region,regionPtr);u32(G+184,regionPtr);u32(G+188,region.length);
  const qinit=(queue,capacity,base)=>{const p=allocate(Math.max(8,capacity*8),4);u32(G+base,capacity);u32(G+base+4,p);u32(G+base+8,queue.length);queue.forEach((e,i)=>{u32(p+i*8,e[0]);u32(p+i*8+4,e[1]);});};
  qinit(cs.currency.queue,cs.currency.queue_capacity,2156);qinit(cs.xp_queue,cs.xp_queue_capacity,2144);
  const rp=allocate(Math.max(8,cs.capacity*56),8);u32(G+1868,cs.capacity);u32(G+1872,rp);u32(G+1876,cs.pickup_hex.length);cs.pickup_hex.forEach((raw,j)=>bytes().set(Buffer.from(raw,'hex'),rp+j*56));
  u32(G+2408,cs.spawn_counter);u32(G+2412,cs.message_sequence);u32(G+2420,cs.kill_cost_bits);
  const V=allocate(128);u32(G+2348,V);u8(V+120,1);u32(V+116,0);u32(V+32,0xffffffff);u32(V+56,0xffffffff);
  const U=allocate(Math.max(1,cast.units.length)*424);u32(G+1784,cast.units.length);u32(G+1788,U);u32(G+1792,cast.units.length);
  cast.units.forEach((u,j)=>{const p=U+j*424;view().setBigUint64(p+112,BigInt(u.guid),true);u32(p,u.marker);for(const [o,k]of[[40,'kind_40'],[64,'kind_64'],[244,'elite_244'],[416,'elite_416']])u32(p+o,u[k]>>>0);u32(p+284,u.definition_pointer);u32(p+288,u.hp_bits);u32(p+292,u.max_hp_bits);u32(p+372,u.priority_until372_bits);u32(p+408,u.phase_until408_bits);u32(p+412,u.phase_until412_bits);view().setBigUint64(p+32,BigInt(u.linked_id),true);u32(p+340,u.movement_time_bits);u32(p+344,u.duration_bits);for(const [o,v]of[[316,u.from_xyz],[328,u.to_xyz]])v.forEach((x,k)=>u32(p+o+k*4,x));});
  const number=bits=>{const a=new DataView(new ArrayBuffer(4));a.setUint32(0,bits,true);return a.getFloat32(0,true);};
  let A=0;
  if(c.mode==='cast'){
    const def=c.definition;if(Buffer.from(span(def.pointer,88,88)).toString('hex')!==c.definition_hex)throw Error('Definition identity');
    A=allocate(80);bytes().set(Buffer.from(c.owned_hex,'hex'),A);u32(G+1656,1);u32(G+1660,A);u32(G+1664,1);
    u8(G+908,cast.context908);view().setBigUint64(G+776,BigInt(cast.current_target_id),true);
    for(const [o,k]of[[1540,'damage_multiplier_bits'],[1544,'cooldown_multiplier_bits'],[1548,'critical_chance_bits'],[1552,'critical_multiplier_bits'],[1580,'area_multiplier_bits']])u32(G+o,cast[k]);u32(G+1592,cast.extra_targets);
  }
  const qread=base=>{const p=read32(G+base+4),n=read32(G+base+8);if(n>128)throw Error('queue budget');return Array.from({length:n},(_,i)=>[read32(p+i*8),read32(p+i*8+4)]);};
  const snapshot=()=>{
    const p=read32(G+1872),n=read32(G+1876);if(n>128)throw Error('Pickup budget');
    const hp=read32(G+1848),hn=read32(G+1852);if(hn>128)throw Error('Hit budget');
    return {units:cast.units.map((_,j)=>{const p=U+j*424;return {hp_bits:read32(p+288),marker:read32(p),duration_bits:read32(p+344),movement_time_bits:read32(p+340),death_time_bits:read32(p+4),afflicted:read32(p+240),from_xyz:[0,1,2].map(k=>read32(p+316+k*4)),to_xyz:[0,1,2].map(k=>read32(p+328+k*4))};}),
      rng_words:[0,1,2,3].map(j=>read32(G+1720+j*4)),accounted_total_hex:view().getBigUint64(G+984,true).toString(16).padStart(16,'0'),
      pickup_words:Array.from({length:n},(_,j)=>Array.from({length:14},(_,k)=>read32(p+j*56+k*4))),capacity:read32(G+1868),spawn_counter:read32(G+2408),message_sequence:read32(G+2412),kill_cost_bits:read32(G+2420),
      progression:{level:read32(G+1432),xp:read32(G+1436),pending_upgrades:read32(G+2376)},derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,read32(G+1536+j*4)])),current_hp_bits:read32(G+1440),auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,read32(G+o)])),speed_bits:read32(G+1648),player_fields:tree(),
      phase2587:view().getUint8(G+2587),selection_kind2585:view().getUint8(G+2585),generation_counter2400:read32(G+2400),candidates:candidates(),gold:read32(G+1456),earned:read32(G+1100),currency_queue:qread(2156),currency_queue_capacity:read32(G+2156),xp_queue:qread(2144),xp_queue_capacity:read32(G+2144),
      queued:Array.from({length:hn},(_,j)=>{const q=hp+j*112;return {target_id:view().getBigUint64(q+64,true).toString(),source_id:view().getBigUint64(q+72,true).toString(),due_bits:read32(q+92),spell_id:read32(q+96),damage_bits:read32(q+100),critical:view().getUint8(q+104),school:view().getUint8(q+106),context908:view().getUint8(q+105)};})};
  };
  const stages=[];
  for(const op of c.ops){u32(G+2352,op.now_bits);if(op.kind==='cast')roles.cast(G,A);else if(op.kind==='process')roles.process_hits(G);else if(op.kind==='collect')roles.collect_pickups(G);else throw Error('Operation');calls++;if(hostCalls.length)throw Error('Original host import attempted');stages.push(snapshot());}
  process.stdout.write(JSON.stringify({id:index,stages})+'\n');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);actualHostCalls+=hostCalls.length;
}
await fs.writeFile(`${directory}/death-pickup135-runtime.json`,JSON.stringify({case_count:cases.length,entry_calls:calls,full_original_functions:[922,1754,914,1417,1821,2862,28796,4630,2159,1512],fresh_instances:instances,fresh_every:16,max_memory_bytes:maxMemory,actual_host_calls:actualHostCalls,denied_function_imports:878,original_allocator:91941,memory_page_cap:512,node:process.version,application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false},null,2)+'\n');
