// Complete original4630 presentation probe; natural19964→82070 cold locale.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [directory,casesFile]=process.argv.slice(2),hash=value=>createHash('sha256').update(value).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('Explicit32MiB/512MiB budgets');
const manifest=JSON.parse(await fs.readFile(directory+'/manifest.json','utf8'));
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(directory+'/'+manifest.module_file),text=await fs.readFile(casesFile,'utf8');
if(hash(original)!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||hash(changed)!==manifest.module_sha256||Buffer.byteLength(text)>4194304)throw Error('Source/module/fixture identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const before=sections(original),after=sections(changed);
if(before.map(s=>s.kind).join()!==after.map(s=>s.kind).join()||before.some(s=>s.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Nonexport original bytes changed');});
const oldExports=exportsOf(original,before.find(s=>s.kind===7)),newExports=exportsOf(changed,after.find(s=>s.kind===7));
const allowed=[{name:'research135_gain_experience',kind:0,index:4630},{name:'research135_level_banner_stack0',kind:3,index:0}];
if(JSON.stringify(newExports.slice(0,oldExports.length))!==JSON.stringify(oldExports)||JSON.stringify(newExports.slice(oldExports.length))!==JSON.stringify(allowed))throw Error('Private exports');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=text.trim().split('\n').filter(Boolean).map(JSON.parse);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>128)throw Error('Imports/case budget');
let host,instances=0,calls=0,maxMemory=0,actualHostCalls=0,outputBytes=0,failure=null;
const stackChecks=[];
async function fresh(caseId){
 const hostCalls=[],bindings={};for(const item of imports){bindings[item.module]??={};bindings[item.module][item.name]=()=>{hostCalls.push(item.module+'.'+item.name);actualHostCalls++;throw Error('Denied original host '+item.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research135_level_banner_stack0;
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Initial stack');let returned=false;try{const value=fn(...args);returned=true;return value;}finally{stackChecks.push({case_id:caseId,index,before,after:stack.value,returned});if(returned&&before!==stack.value)throw Error('Stack not restored');}}
 return{memory,hostCalls,roles:{gain_experience:(...args)=>call(4630,e.research135_gain_experience,...args)},allocate(size,alignment=8){if(!Number.isInteger(size)||size<1||size>4194304)throw Error('Allocation budget');const p=call(91941,e.__wbindgen_malloc,size,alignment)>>>0;if(!p||p+size>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');new Uint8Array(memory.buffer,p,size).fill(0);return p;}};
}
try{
for(let index=0;index<cases.length;++index){
  host=await fresh(index);instances++;
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
  u32(G+1880,0);u32(G+1884,4);u32(G+1888,0);
  u32(14384328,c.locale_default_index);u32(14384320,c.locale_override_enabled);u32(14384324,c.locale_override_index);
  if(view().getUint8(14384344)!==0)throw Error('Locale Once must be fresh original0');
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
    const p=read32(G+2476);if(!p)return{};if(read32(G+2480)!==0)throw Error('Declared six-key tree domain exceeded');
    const n=view().getUint16(p+50,true);if(n>11)throw Error('Leaf count budget');
    return Object.fromEntries(Array.from({length:n},(_,i)=>[view().getUint16(p+52+i*2,true),read32(p+4+i*4)]));
  };
  for(let step=0;step<c.amounts.length;++step){
    if(c.amounts.length>16)throw Error('Call sequence budget');
    const beforeG=Buffer.from(bytes().slice(G,G+8192)).toString('hex'),onceBefore=view().getUint8(14384344);
    roles.gain_experience(G,c.amounts[step]);calls++;
    if(hostCalls.length)throw Error('Original host call attempted');
    const result={progression:{level:read32(G+1432),xp:read32(G+1436),pending_upgrades:read32(G+2376)},
      derived_bits:Object.fromEntries(Array.from({length:23},(_,i)=>[1536+i*4,read32(G+1536+i*4)])),
      current_hp_bits:read32(G+1440),auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,read32(G+o)])),
      speed_bits:read32(G+1648),player_fields:tree(),rng_words:[0,1,2,3].map(i=>read32(G+1720+i*4)),
      candidates:candidates(),phase2587:view().getUint8(G+2587),selection_kind2585:view().getUint8(G+2585),generation_counter2400:read32(G+2400)};
    const n=read32(G+1888),p=read32(G+1884);if(n>512||n>read32(G+1880))throw Error('Packet vector budget');
    const packetRows=Array.from({length:n},(_,i)=>{const q=p+16*i,length=read32(q+8),capacity=read32(q),pointer=read32(q+4);if(length>capacity||length>1048576||pointer+length>memory.buffer.byteLength)throw Error('Packet owner bounds');return{opcode:view().getUint16(q+12,true),payload_hex:Buffer.from(bytes().slice(pointer,pointer+length)).toString('hex')};});
    const line=JSON.stringify({id:index,step,projection:result,packets150:packetRows.filter(row=>row.opcode===150),all_packet_opcodes:packetRows.map(row=>row.opcode),locale_once_before:onceBefore,locale_once_after:view().getUint8(14384344),Game_before8192_hex:beforeG,Game_after8192_hex:Buffer.from(bytes().slice(G,G+8192)).toString('hex')})+'\n';
    outputBytes+=Buffer.byteLength(line);if(Buffer.byteLength(line)>2097152||outputBytes>16777216)throw Error('Output budget');process.stdout.write(line);
    maxMemory=Math.max(maxMemory,memory.buffer.byteLength);actualHostCalls+=hostCalls.length;
  }
  if(global.gc)global.gc();
}
}catch(error){failure=String(error);throw error;}finally{
await fs.writeFile(directory+'/level-banner135-runtime.json',JSON.stringify({case_count:cases.length,entry_calls:calls,original_entry:4630,unchanged_callees:true,fresh_instances:instances,maximum_memory_bytes:maxMemory,actual_host_calls:actualHostCalls,denied_function_imports:878,memory_page_cap:512,output_bytes:outputBytes,stack_checks:stackChecks,stack_all_restored:stackChecks.every(x=>x.returned&&x.before===x.after),locale_Once_injected:false,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false,failure},null,2)+'\n');
}
