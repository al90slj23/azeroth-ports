// Unchanged full13510298 including1512/1202/real locale initialization.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('32MiB WASM/512MiB heap required');
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(original.length!==90959080||hash(original)!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||hash(changed)!==manifest.module_sha256||input.length>4194304)throw Error('Source/module/input identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const before=sections(original),after=sections(changed);
if(before.map(s=>s.kind).join()!==after.map(s=>s.kind).join()||before.some(s=>s.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Original nonexport bytes changed');});
const prior=exportsOf(original,before.find(s=>s.kind===7)),updated=exportsOf(changed,after.find(s=>s.kind===7));
const added=[{name:'research135_resource_effect10298',kind:0,index:10298},{name:'research135_resource_collect2862',kind:0,index:2862},{name:'research135_resource_consumer_stack0',kind:3,index:0}];
if(JSON.stringify(updated)!==JSON.stringify([...prior,...added]))throw Error('Private export surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>128)throw Error('Import/case profile');
let hostCalls=0,peak=0,instances=0,calls=0,completed=0,outputBytes=0,failure=null;const checks=[];
try{for(const c of cases){
 const bindings={};for(const item of imports){bindings[item.module]??={};bindings[item.module][item.name]=()=>{hostCalls++;throw Error('Denied original host '+item.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research135_resource_consumer_stack0;
 instances++;
 const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Precall stack');let returned=false;try{const result=fn(...args);returned=true;return result;}catch(error){process.stderr.write(JSON.stringify({case_id:c.id,index,original_error:String(error),original_stack:error.stack,stack_before:before,stack_after:stack.value})+'\n');throw error;}finally{const after=stack.value;checks.push({case_id:c.id,index,before,after,returned});if(returned&&before!==after)throw Error('Stack not restored');}}
 function allocate(n,align=8){if(n<1||n>4194304)throw Error('Allocation budget');const p=call(91941,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');bytes().fill(0,p,p+n);return p;}

 const cs=c.control,rc=c.resource_context;
 const s=c.level,t=s.stats,src=s.sources,G=allocate(8192);
 const view=d,u32=w,read32=r,u8=(p,v)=>{if(!Number.isInteger(v)||v<0||v>255)throw Error('u8');bytes()[p]=v;};
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
  view().setBigUint64(G+1336,BigInt(rc.player_guid),true);
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

 w(G+1256,manifest.default_ability_pointer);
 if(rc.locale_code!=='en'||rc.aura_external_sources_absent!==true)throw Error('Explicit source/locale domain');
 if(r(14340336)!==rc.notification_next_id14340336)throw Error('Cold original notification owner differs; fixture must not overwrite it');
 w(G+1644,rc.action_sequence1644);
 function physicalVector(value,stride,cap,ptr,len,empty){const p=value.storage.length?allocate(value.storage.length*stride,4):empty;value.storage.forEach((row,j)=>{if(row.length!==stride)throw Error('Physical stride');bytes().set(row.map(x=>x===null?c.unknown_poison:x),p+j*stride);});w(G+cap,value.storage.length);w(G+ptr,p);w(G+len,value.count??value.storage.length);}
 physicalVector(rc.live,32,1704,1708,1712,4);physicalVector(rc.aura,16,2000,2004,2008,4);bytes()[G+2569]=rc.aura.initialized2569;
 physicalVector(c.pickups,56,1868,1872,1876,8);
 physicalVector({storage:[],count:0},424,1784,1788,1792,4);
 w(G+1880,0);w(G+1884,4);w(G+1888,0);w(G+2108,0);w(G+2112,8);w(G+2116,0);
 cs.player_xyz.forEach((word,j)=>w(G+1416+j*4,word));w(G+2408,cs.spawn_counter);w(G+2412,cs.message_sequence);w(G+2420,cs.kill_cost_bits);
 w(G+1456,cs.currency.gold);w(G+1100,cs.currency.earned);w(G+2528,cs.currency.local_peer);w(G+2540,cs.currency.member_count);
 const region=Buffer.from('elwynn'),regionPointer=allocate(region.length,1);bytes().set(region,regionPointer);w(G+184,regionPointer);w(G+188,region.length);
 function pairQueue(entries,capacity,base){const p=capacity?allocate(capacity*8,4):4;w(G+base,capacity);w(G+base+4,p);w(G+base+8,entries.length);entries.forEach((row,j)=>{w(p+8*j,row[0]);w(p+8*j+4,row[1]);});}
 pairQueue(cs.currency.queue,cs.currency.queue_capacity,2156);pairQueue(cs.xp_queue,cs.xp_queue_capacity,2144);
 const tree=()=>{const root=r(G+2476),depth=r(G+2480),out={},seen=new Set();if(!root)return out;function walk(p,level){if(!p||seen.has(p)||seen.size>512||level>5)throw Error('Tree budget');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(level)walk(r(p+76+j*4),level-1);out[d().getUint16(p+52+j*2,true)]=r(p+4+j*4);}if(level)walk(r(p+76+n*4),level-1);}walk(root,depth);return out;};
 function physicalCapture(cap,ptr,len,stride){const capacity=r(G+cap),count=r(G+len),p=r(G+ptr);if(count>capacity||capacity>4096||p+capacity*stride>memory.buffer.byteLength)throw Error('Physical owner bounds');return{capacity,count,storage:Array.from({length:capacity},(_,j)=>hex(p+j*stride,stride))};}
 function pairs(base){const p=r(G+base+4),n=r(G+base+8);if(n>r(G+base)||n>128)throw Error('Pair queue bound');return Array.from({length:n},(_,j)=>[r(p+8*j),r(p+8*j+4)]);}
 function queue(base,stride,opcode){const capacity=r(G+base),p=r(G+base+4),count=r(G+base+8);if(count>capacity||count>1024)throw Error('Queue bounds');return{capacity,count,active:Array.from({length:count},(_,j)=>{const q=p+j*stride,cap=r(q),size=r(q+8),data=r(q+4);if(size>cap||size>1048576||data+size>memory.buffer.byteLength)throw Error('Payload owner');return{...(opcode?{opcode:d().getUint16(q+12,true)}:{}),payload_hex:hex(data,size)};})};}
 const stages=[];
 for(const now of c.times_bits){w(G+2352,now);const before=hex(G,8192);call(2862,e.research135_resource_collect2862,G);calls++;if(hostCalls)throw Error('Denied host');
  const packets=queue(1880,16,true),notifications=queue(1892,12,false);
  const known={level:{progression:{level:r(G+1432),xp:r(G+1436),pending_upgrades:r(G+2376)},derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,r(G+1536+j*4)])),current_hp_bits:r(G+1440),auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,r(G+o)])),speed_bits:r(G+1648),player_fields:tree(),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),candidates:candidates(),phase2587:bytes()[G+2587],selection_kind2585:bytes()[G+2585],generation_counter2400:r(G+2400)},
   pickups:physicalCapture(1868,1872,1876,56),live:physicalCapture(1704,1708,1712,32),aura:{...physicalCapture(2000,2004,2008,16),initialized2569:bytes()[G+2569]},gold:r(G+1456),earned:r(G+1100),currency_queue:pairs(2156),currency_queue_capacity:r(G+2156),xp_queue:pairs(2144),xp_queue_capacity:r(G+2144),spawn_counter:r(G+2408),message_sequence:r(G+2412),action_sequence1644:r(G+1644),notification_next_id14340336:r(14340336),
   packets:packets.active.filter(row=>[170,306,226,150].includes(row.opcode)),notifications:notifications.active.map(row=>{const value=JSON.parse(Buffer.from(row.payload_hex,'hex').toString('utf8'));if(value.type==='banner')return{kind:'rune_raw',payload_hex:row.payload_hex};if(value.type==='choices'){if(!Array.isArray(value.choices))throw Error('Choices array');return{kind:'choices_known',type:value.type,offer:value.offer,why:value.why,level:value.level,gold:value.gold,candidate_kinds:value.choices.map(choice=>choice.kind),candidate_tiers:value.choices.map(choice=>choice.rarity)};}throw Error('Unmodeled notification type '+value.type);})};
  stages.push({known,raw_Game_before8192_hex:before,raw_Game_after8192_hex:hex(G,8192),raw_packets:packets,raw_notifications:notifications});peak=Math.max(peak,memory.buffer.byteLength);
 }
 const line=JSON.stringify({id:c.id,stages})+'\n';outputBytes+=Buffer.byteLength(line);if(Buffer.byteLength(line)>2097152||outputBytes>16777216)throw Error('Output budget');process.stdout.write(line);completed++;if(global.gc)global.gc();
}
}catch(error){failure=String(error);throw error;}finally{
 await fs.writeFile(dir+'/mixed-pickup135-runtime.json',JSON.stringify({version:'0.135.1',actual_build:'90898d5e3',cases:cases.length,completed_cases:completed,full2862_calls:calls,fresh_instances:instances,max_memory_bytes:peak,memory_cap_bytes:33554432,actual_host_calls:hostCalls,denied_imports:878,stack_checks:checks,stack_all_restored:checks.every(x=>x.before===x.after&&x.returned),output_bytes:outputBytes,notification_counter_written_by_fixture:false,locale_Once_injected:false,application_start_called:false,network_used:false,user_saves_accessed:false,original_function_bodies_unchanged:true,error:failure},null,2)+'\n');
}
