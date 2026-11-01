// Full original1072 including original1512/4600, swept4630 and regenerated2159.
// No application entry; all original host imports throw.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,casesFile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['select_ability']);
const text=await fs.readFile(casesFile,'utf8');
if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture byte budget');
const cases=text.trim().split('\n').filter(Boolean).map(JSON.parse);
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
  const cs=c.control;
  u32(G+2380,cs.pending_kind1);u32(G+2384,cs.pending_kind2);
  u32(G+1416,cs.player_x_bits);u32(G+1420,cs.player_y_bits);view().setBigUint64(G,BigInt(cs.game_tag),true);
  u32(G+1704,src.live_effects.length);
  u32(G+1456,cs.currency.gold);u32(G+1100,cs.currency.earned);
  u32(G+2528,cs.currency.local_peer);u32(G+2540,cs.currency.member_count);
  const region=Buffer.from(cs.region_id,'ascii'),regionPtr=allocate(Math.max(1,region.length),1);bytes().set(region,regionPtr);u32(G+184,regionPtr);u32(G+188,region.length);
  const qinit=(queue,capacity,base)=>{const p=allocate(Math.max(8,capacity*8),4);u32(G+base,capacity);u32(G+base+4,p);u32(G+base+8,queue.length);queue.forEach((e,i)=>{u32(p+i*8,e[0]);u32(p+i*8+4,e[1]);});};
  qinit(cs.currency.queue,cs.currency.queue_capacity,2156);qinit(cs.xp_queue,cs.xp_queue_capacity,2144);
  const pickupCount=cs.pickup_hex.length;
  if(pickupCount){const p=allocate(pickupCount*56,8);u32(G+1868,pickupCount);u32(G+1872,p);u32(G+1876,pickupCount);cs.pickup_hex.forEach((raw,i)=>{const b=Buffer.from(raw,'hex');if(b.length!==56)throw Error('Pickup56B');bytes().set(b,p+i*56);});}
  if(cs.modifiers.length){const p=allocate(cs.modifiers.length*20,4);u32(G+2036,cs.modifiers.length);u32(G+2040,p);u32(G+2044,cs.modifiers.length);cs.modifiers.forEach((m,i)=>{const a=p+i*20;u8(a,m.filter_tag);u8(a+1,m.filter_value);u8(a+12,m.kind);u32(a+16,m.value_bits);if(m.filter_tag===1){const raw=Buffer.from(m.ability_id_hex,'hex'),n=allocate(Math.max(1,raw.length),1);bytes().set(raw,n);u32(a+4,n);u32(a+8,raw.length);}if(m.filter_tag===2){const list=allocate(Math.max(8,m.ability_ids_hex.length*8),4);m.ability_ids_hex.forEach((raw,j)=>{const b=Buffer.from(raw,'hex'),n=allocate(Math.max(1,b.length),1);bytes().set(b,n);u32(list+j*8,n);u32(list+j*8+4,b.length);});u32(a+4,list);u32(a+8,m.ability_ids_hex.length);}});}
  const candidate=allocate(80),card=c.card;
  if(card.variant==='new'){const def=cs.definition_pointer;u32(candidate+60,0x80000000);u32(candidate+64,read32(def+12));u32(candidate+68,read32(def+16));}
  else if(card.variant==='upgrade'){const p=allocate(Math.max(1,card.kinds.length),1);bytes().set(card.kinds,p);u32(candidate+60,card.kinds.length);u32(candidate+64,p);u32(candidate+68,card.kinds.length);u32(candidate+72,card.owned_index);}
  else if(card.variant==='gold'){u32(candidate+60,0x80000004);u32(candidate+64,card.gold);}else throw Error('Candidate variant');
  u32(candidate+76,card.tier);u32(G+1904,1);u32(G+1908,candidate);u32(G+1912,1);
  const qread=base=>{const p=read32(G+base+4),n=read32(G+base+8);if(n>64)throw Error('queue budget');return Array.from({length:n},(_,i)=>[read32(p+i*8),read32(p+i*8+4)]);};
  for(let step=0;step<c.choice_indices.length;++step){
    if(c.choice_indices.length>12)throw Error('Call sequence budget');
    roles.select_ability(G,c.choice_indices[step]);calls++;
    if(hostCalls.length)throw Error('Original host call attempted');
    const op=read32(G+1660),on=read32(G+1664),lp=read32(G+1708),ln=read32(G+1712),rp=read32(G+1872),rn=read32(G+1876);
    if(on>16||ln>64||rn>64)throw Error('Projection budget');
    const allPlayerFields=tree();
    const numericKeys=new Set([22,28,34,716,717,1109,1176]);
    const numericFields=Object.fromEntries(Object.entries(allPlayerFields).filter(([key])=>numericKeys.has(Number(key))));
    const unmodeledPlayerFields=Object.fromEntries(Object.entries(allPlayerFields).filter(([key])=>!numericKeys.has(Number(key))));
    const result={progression:{level:read32(G+1432),xp:read32(G+1436),pending_upgrades:read32(G+2376)},
      derived_bits:Object.fromEntries(Array.from({length:23},(_,i)=>[1536+i*4,read32(G+1536+i*4)])),
      current_hp_bits:read32(G+1440),auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,read32(G+o)])),
      speed_bits:read32(G+1648),player_fields:numericFields,rng_words:[0,1,2,3].map(i=>read32(G+1720+i*4)),
      candidates:candidates(),phase2587:view().getUint8(G+2587),selection_kind2585:view().getUint8(G+2585),generation_counter2400:read32(G+2400),
      owned_records_hex:Array.from({length:on},(_,i)=>Buffer.from(span(op+i*80,80,80)).toString('hex')),
      pending_kind1:read32(G+2380),pending_kind2:read32(G+2384),
      remaining_pickups_hex:Array.from({length:rn},(_,i)=>Buffer.from(span(rp+i*56,56,56)).toString('hex')),
      game_tag:Number(view().getBigUint64(G,true)),flag2581:view().getUint8(G+2581),flags2573:view().getUint8(G+2573),
      live_effects:Array.from({length:ln},(_,i)=>{const p=lp+i*32;return{kind:read32(p+8),value_bits:read32(p+12),spell_id:read32(p+20),expires_bits:read32(p+24)};}),
      gold:read32(G+1456),earned:read32(G+1100),currency_queue:qread(2156),currency_queue_capacity:read32(G+2156),xp_queue:qread(2144),xp_queue_capacity:read32(G+2144)};
    process.stdout.write(JSON.stringify({id:index,step,projection:result,unmodeled_player_fields:unmodeledPlayerFields})+'\n');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);actualHostCalls+=hostCalls.length;
  }
}
await fs.writeFile(`${directory}/selection-cycle135-runtime.json`,JSON.stringify({case_count:cases.length,entry_calls:calls,original_entry:1072,
  unchanged_callees:[1512,4600,4630,2159],fresh_instances:instances,fresh_instance_every:16,maximum_memory_bytes:maxMemory,actual_host_calls:actualHostCalls,
  denied_function_imports:878,original_allocator:91941,memory_page_cap:512,node:process.version,application_start_called:false,full_game_started:false,
  network_used:false,user_saves_accessed:false},null,2)+'\n');
