// Complete original922 kind9 racial self-buffs with real1512/1202.
// No application entry; all original host imports throw.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,casesFile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['cast']);
const text=await fs.readFile(casesFile,'utf8');
if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture byte budget');
const cases=JSON.parse(text);
if(!cases.length||cases.length>3000)throw Error('Fixture count budget');
let host,instances=0,calls=0,maxMemory=0,actualHostCalls=0;
for(let index=0;index<cases.length;++index){
  if(index%16===0){host=await prepared.fresh();instances++;}
  const c=cases[index],s=c.input,t=s.stats,src=s.sources;
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
  view().setBigUint64(G+1336,1n,true);
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
  const A=G+1256;bytes().set(Buffer.from(c.owned_hex,'hex'),A);u32(G+488,c.busy488);u8(G+908,c.cast.context908);
  const U=allocate(Math.max(1,c.cast.units.length)*424);u32(G+1784,c.cast.units.length);u32(G+1788,U);u32(G+1792,c.cast.units.length);
  c.cast.units.forEach((x,j)=>{const p=U+j*424;u32(p,x.marker);u32(p+40,0xffffffff);u32(p+64,0xffffffff);u32(p+244,0xffffffff);view().setBigUint64(p+112,BigInt(x.guid),true);u32(p+288,x.hp_bits);u32(p+292,x.max_hp_bits);u32(p+340,x.movement_time_bits);u32(p+344,x.duration_bits);x.from_xy.forEach((v,k)=>u32(p+316+k*4,v));x.to_xy.forEach((v,k)=>u32(p+328+k*4,v));});
  const L=allocate(128*32);u32(G+1704,128);u32(G+1708,L);u32(G+1712,c.live_records.length);
  c.live_records.forEach((hex,j)=>bytes().set(Buffer.from(hex,'hex'),L+j*32));
  if(Buffer.from(bytes().slice(c.definition.pointer,c.definition.pointer+88)).toString('hex')!==c.definition.raw88_hex)throw Error('Racial definition identity');
  const tree=()=>{const root=read32(G+2476),depth=read32(G+2480);if(!root)return{};const fields=[],seen=new Set();
   const walk=(p,level)=>{if(!p||p+76>memory.buffer.byteLength||seen.has(p)||seen.size>512||level>5)throw Error('Tree budget');seen.add(p);const n=view().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(level)walk(read32(p+76+j*4),level-1);const k=view().getUint16(p+52+j*2,true);if([22,28,1109].includes(k))fields.push([k,read32(p+4+j*4)]);}if(level)walk(read32(p+76+n*4),level-1);};walk(root,depth);return Object.fromEntries(fields);};
  const result=roles.cast(G,A);calls++;if(hostCalls.length)throw Error('Original host import attempted');
  const n=read32(G+1712),ptr=read32(G+1708);if(n>128)throw Error('Live budget');
  const output={success:result,live_records:Array.from({length:n},(_,j)=>Buffer.from(bytes().slice(ptr+j*32,ptr+(j+1)*32)).toString('hex')),
   derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,read32(G+1536+j*4)])),current_hp_bits:read32(G+1440),
   auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,read32(G+o)])),shield_source:read32(G+1344),speed_bits:read32(G+1648),
   player_fields:tree(),rng_words:[0,1,2,3].map(j=>read32(G+1720+4*j)),owned_hex:Buffer.from(bytes().slice(A,A+80)).toString('hex'),
   attempted_spell_sets:[672,684,732].map(off=>{const p=read32(G+off),n=read32(G+off+4);if(n>128)throw Error('Spell set budget');return Array.from({length:n},(_,j)=>read32(p+j*4));})};
  process.stdout.write(JSON.stringify({id:index,result:output})+'\n');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/racial-cast135-runtime.json`,JSON.stringify({cases:cases.length,entry_calls:calls,full_original_function:922,
 unchanged_callees:[1512,1202,29983,44446],racial_owned_actual_address:'G+1256',fresh_instances:instances,max_memory_bytes:maxMemory,host_calls:0,denied_imports:878,
 original_allocator:91941,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
