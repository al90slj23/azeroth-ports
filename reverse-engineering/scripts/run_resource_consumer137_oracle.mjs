// Unchanged full13710291 including1514/1151/real locale initialization.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('32MiB WASM/512MiB heap required');
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T154517.001467Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(original.length!==90941108||hash(original)!=='20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8'||hash(changed)!==manifest.module_sha256||input.length>4194304)throw Error('Source/module/input identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const before=sections(original),after=sections(changed);
if(before.map(s=>s.kind).join()!==after.map(s=>s.kind).join()||before.some(s=>s.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Original nonexport bytes changed');});
const prior=exportsOf(original,before.find(s=>s.kind===7)),updated=exportsOf(changed,after.find(s=>s.kind===7));
const added=[{name:'research137_resource_effect10291',kind:0,index:10291},{name:'research137_resource_collect2862',kind:0,index:2862},{name:'research137_resource_consumer_stack0',kind:3,index:0}];
if(JSON.stringify(updated)!==JSON.stringify([...prior,...added]))throw Error('Private export surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>256)throw Error('Import/case profile');
let hostCalls=0,peak=0,instances=0,completedCases=0,runtimeError=null;const checks=[],calls={10291:0,2862:0},locales=[];
try{
for(const c of cases){
 const bindings={};for(const item of imports){bindings[item.module]??={};bindings[item.module][item.name]=()=>{hostCalls++;throw Error('Denied original host '+item.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research137_resource_consumer_stack0;
 instances++;
 const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Precall stack');let returned=false;try{const result=fn(...args);returned=true;return result;}catch(error){process.stderr.write(JSON.stringify({case_id:c.id,index,original_error:String(error),original_stack:error.stack,stack_before:before,stack_after:stack.value})+'\n');throw error;}finally{const after=stack.value;checks.push({case_id:c.id,index,before,after,returned});if(before!==after)throw Error('Stack not restored');}}
 function allocate(n,align=8){if(n<1||n>4194304)throw Error('Allocation budget');const p=call(91933,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');bytes().fill(0,p,p+n);return p;}
 const s=c.state,t=s.stats,G=allocate(8192);
 for(const[o,key]of[[1432,'level'],[1536,'old_max_hp_bits'],[1440,'current_hp_bits'],[2352,'now_bits'],[268,'conditional268_bits'],[1648,'previous_speed_bits'],[1444,'pool1532_bits'],[1448,'pool1536_bits'],[1344,'conditional1344_id'],[1348,'conditional1348_bits'],[764,'pool768_bits']])w(G+o,t[key]);
 bytes()[G+360]=t.class_byte;bytes()[G+361]=t.race_byte;bytes()[G+2582]=t.flag2574;bytes()[G+2587]=1;bytes()[G+387]=s.heal_gate387;
 for(const[key,word]of s.derived_bits)w(G+key,word);
 for(const key of ['passives','adjustments','item_modifiers','owned_skills','timed_records','timed_definitions'])if(t[key].length)throw Error('Nonempty external source outside explicit domain');
 // Empty source vectors are fixtures, not a claim of a full original constructor.
 for(const[cap,ptr,len,align]of[[168,172,176,4],[1668,1672,1676,4],[1692,1696,1700,4],[596,600,604,4],[2024,2028,2032,4],[2048,2052,2056,4],[2000,2004,2008,4],[1880,1884,1888,4],[1892,1896,1900,4]]){w(G+cap,0);w(G+ptr,align);w(G+len,0);}
 s.rng_words.forEach((word,j)=>w(G+1720+j*4,word));w(G+2408,s.counter2408);w(G+2412,s.message_sequence2412);w(G+1644,s.action_sequence1644);
 d().setBigUint64(G+1336,BigInt(c.player_guid),true);
 const fields=s.player_fields;if(fields.length>11)throw Error('Initial single-leaf keyed fixture budget');
 if(fields.length){const p=allocate(76,4);d().setUint16(p+50,fields.length,true);fields.forEach(([key,value],j)=>{d().setUint16(p+52+j*2,key,true);w(p+4+j*4,value);});w(G+2476,p);w(G+2480,0);w(G+2484,fields.length);}
 const live=s.live,L=live.storage.length?allocate(live.storage.length*32):4;w(G+1704,live.storage.length);w(G+1708,L);w(G+1712,live.count);
 live.storage.forEach((row,j)=>{if(row.length!==32)throw Error('Live32 stride');bytes().set(row.map(x=>x===null?c.unknown_poison:x),L+j*32);});
 const pickups=c.pickups??{storage:[],count:0},P=pickups.storage.length?allocate(pickups.storage.length*56):8;
 w(G+1868,pickups.storage.length);w(G+1872,P);w(G+1876,pickups.count);
 pickups.storage.forEach((row,j)=>{if(row.length!==56)throw Error('Pickup56 stride');bytes().set(row.map(x=>x===null?c.unknown_poison:x),P+j*56);});
 (c.player_xyz_bits??[0,0,0]).forEach((word,j)=>w(G+1416+j*4,word));w(G+2108,0);w(G+2112,8);w(G+2116,0);
 const tree=()=>{const root=r(G+2476),depth=r(G+2480),out={},seen=new Set();if(!root)return out;function walk(p,level){if(!p||seen.has(p)||seen.size>512||level>5)throw Error('Tree budget');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(level)walk(r(p+76+j*4),level-1);out[d().getUint16(p+52+j*2,true)]=r(p+4+j*4);}if(level)walk(r(p+76+n*4),level-1);}walk(root,depth);return out;};
 const queue=(offset,stride,opcode)=>{const cap=r(G+offset),p=r(G+offset+4),n=r(G+offset+8);if(n>1024||n>cap||p+n*stride>memory.buffer.byteLength)throw Error('Queue bound');return{capacity:cap,count:n,raw_hex:hex(p,n*stride),active:Array.from({length:n},(_,j)=>{const q=p+j*stride,k=r(q+8),b=r(q+4);if(k>r(q)||k>1048576||b+k>memory.buffer.byteLength)throw Error('Queue payload');return{...(opcode?{opcode:d().getUint16(q+12,true)}:{}),payload_hex:hex(b,k)};})};};
 const localeBefore=hex(14406920,28),stages=[];
 for(const op of c.operations){
  w(G+2352,op.now_bits);
  if(op.operation==='effect'){call(10291,e.research137_resource_effect10291,G,op.kind);calls[10291]++;}
  else if(op.operation==='collect'){call(2862,e.research137_resource_collect2862,G);calls[2862]++;}
  else throw Error('Unrecovered collection operation');
  const p=r(G+1708),capacity=r(G+1704),count=r(G+1712);if(count>capacity||capacity>4096||p+capacity*32>memory.buffer.byteLength)throw Error('Live result bounds');
  const keyed=tree(),auraCap=r(G+2000),auraCount=r(G+2008),auraPtr=r(G+2004);if(auraCount>256||auraCount>auraCap||auraPtr+auraCap*16>memory.buffer.byteLength)throw Error('Aura bounds');
  const selected={};for(const key of[22,28,1109])if(Object.hasOwn(keyed,key))selected[key]=keyed[key];
  const pickupCap=r(G+1868),pickupCount=r(G+1876),pickupPointer=r(G+1872);if(pickupCount>pickupCap||pickupCap>4096||pickupPointer+pickupCap*56>memory.buffer.byteLength)throw Error('Pickup result bounds');
  stages.push({known:{live:{capacity,count,storage:Array.from({length:capacity},(_,j)=>hex(p+j*32,32))},pickups:{capacity:pickupCap,count:pickupCount,storage:Array.from({length:pickupCap},(_,j)=>hex(pickupPointer+j*56,56))},destroy170_hex:queue(1880,16,true).active.filter(x=>x.opcode===170).map(x=>x.payload_hex),derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,r(G+1536+j*4)])),current_hp_bits:r(G+1440),speed_bits:r(G+1648),auxiliary_bits:Object.fromEntries([1444,1448,1348,764].map(o=>[o,r(G+o)])),player_fields:selected,rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),counter2408:r(G+2408),message_sequence2412:r(G+2412),action_sequence1644:r(G+1644)},
   raw_game8192_hex:hex(G,8192),raw_keyed_fields:keyed,raw_packets:queue(1880,16,true),raw_notifications:queue(1892,12,false),raw_aura16:{capacity:auraCap,count:auraCount,storage_hex:hex(auraPtr,auraCap*16)},locale_state_hex:hex(14406920,28)});
  if(hostCalls)throw Error('Denied host attempted');peak=Math.max(peak,memory.buffer.byteLength);
 }
 locales.push({id:c.id,before_hex:localeBefore,after_hex:hex(14406920,28),first_call_bootstrap_untouched:true});
 process.stdout.write(JSON.stringify({id:c.id,stages})+'\n');completedCases++;if(global.gc)global.gc();
}
}catch(error){runtimeError=String(error);throw error;}
finally{await fs.writeFile(dir+'/resource-consumer137-runtime.json',JSON.stringify({version:'0.137.0',build:'d171b8f9f',cases:cases.length,completed_cases:completedCases,full_original_calls:calls,fresh_instances:instances,max_memory_bytes:peak,memory_cap_bytes:33554432,actual_host_calls:hostCalls,denied_imports:878,stack_checks:checks,stack_all_restored:checks.every(x=>x.before===x.after&&x.returned),locales,original_function_bodies_unchanged:true,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false,original_memory_snapshot_read:false,once_or_locale_state_injected:false,error:runtimeError},null,2)+'\n');}
