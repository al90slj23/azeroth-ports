// Unchanged full947/G2424; typed input, independent query-world, declared snapshot locale.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {packAiWorld135} from './ai_world135_packing.mjs';
const [dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=4096'))throw Error('256MiB research cap required');
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(hash(original)!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||hash(changed)!==manifest.module_sha256||input.length>4194304)throw Error('Source/input identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const before=sections(original),after=sections(changed);
if(before.map(s=>s.kind).join()!==after.map(s=>s.kind).join()||before.some(s=>s.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Original nonexport bytes changed');});
const oldExports=exportsOf(original,before.find(s=>s.kind===7)),newExports=exportsOf(changed,after.find(s=>s.kind===7));
const allowed=[{name:'research135_spawn_tick',kind:0,index:947},{name:'research135_event_stack0',kind:3,index:0}];
if(JSON.stringify(newExports.slice(0,oldExports.length))!==JSON.stringify(oldExports)||JSON.stringify(newExports.slice(oldExports.length))!==JSON.stringify(allowed))throw Error('Private export surface');
const snapshotPath=new URL('../evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory',import.meta.url),snapshot=await fs.readFile(snapshotPath);if(hash(snapshot)!=='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf')throw Error('Declared context SHA');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>64)throw Error('Import/case profile');
const number=word=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,word,true);return v.getFloat32(0,true);};
let hostCalls=0,peak=0;const callCounts={},stackChecks=[];
async function run(c){
 const bindings={};for(const item of imports){bindings[item.module]??={};bindings[item.module][item.name]=()=>{hostCalls++;throw Error('Denied original host '+item.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research135_event_stack0;
 if(memory.buffer.byteLength<snapshot.length)memory.grow((snapshot.length-memory.buffer.byteLength)/65536);new Uint8Array(memory.buffer).set(snapshot);if(hash(new Uint8Array(memory.buffer))!==hash(snapshot))throw Error('Snapshot restore');
 const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Precall stack');let returned=false;try{const result=fn(...args);returned=true;return result;}finally{const after=stack.value;stackChecks.push({case_id:c.id,index,before,after,returned});if(before!==after)throw Error('Stack not restored');}}
 function allocate(n,align=8){if(n<1||n>4194304)throw Error('Allocation budget');const p=call(91941,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>268435456)throw Error('Memory budget');bytes().fill(0,p,p+n);return p;}
 const locale=()=>{const words=Array.from({length:6},(_,j)=>r(14384320+j*4)),once=bytes()[14384344],effective=words[0]?words[1]:words[2];if(once!==3||effective!==c.locale.language_index||words[3]!==14||words[5]!==14)throw Error('Preserved locale input');return{words,once,effective,header:hex(14384320,25)};};const localeBefore=locale();
 const world=await packAiWorld135({memory,allocate},c.world),G=allocate(8192),s=c.input;
 const name=allocate(6,1);bytes().set(Buffer.from('elwynn'),name);w(G+184,name);w(G+188,6);w(G+2348,world.R);
 function vector(value,capOff,ptrOff,countOff,stride){const p=value.storage.length?allocate(value.storage.length*stride):stride===56?8:4;
  value.storage.forEach((row,j)=>{if(row.length!==stride)throw Error('Physical row stride');bytes().set(row.map(x=>x===null?c.unknown_poison:x),p+j*stride);});
  w(G+capOff,value.storage.length);w(G+ptrOff,p);w(G+countOff,value.count);
 }
 vector(s.pickups,1868,1872,1876,56);w(G+2352,s.now_bits);w(G+2408,s.counter);s.rng_words.forEach((word,j)=>w(G+1720+j*4,word));
 // Valid empty transport vector; original50798 owns any allocation/growth.
 w(G+1880,0);w(G+1884,4);w(G+1888,0);
 w(G+1892,0);w(G+1896,4);w(G+1900,0);w(G+2412,c.message_sequence);
 const f=c.frame;vector(c.units,1784,1788,1792,424);
 for(const[o,word]of c.initial_scalars)w(G+o,word);
 for(const[o,key]of[[2416,'budget_bits'],[2420,'kill_cost_bits'],[2516,'zone_multiplier_bits'],[400,'victory_field400'],[2540,'members']])w(G+o,f[key]);
 if(f.endless_start_bits!==null)w(G+404,f.endless_start_bits);
 bytes()[G+387]=f.difficulty;bytes()[G+2582]=f.mode;bytes()[G+2568]=f.endless_flag;bytes()[G+2586]=s.last_event2586;
 f.player_xyz.forEach((v,j)=>w(G+1416+j*4,v));f.previous_player_xyz.forEach((v,j)=>w(G+2428+j*4,v));f.velocity_xy.forEach((v,j)=>w(G+1736+j*4,v));
 w(G+2352,s.now_bits);w(G+2408,s.counter);s.rng_words.forEach((v,j)=>w(G+1720+j*4,v));w(G+2412,c.message_sequence);w(G+1432,c.level);d().setBigUint64(G+1336,BigInt(c.player_guid),true);w(G+2424,s.next_event2424_bits);
 if(c.distance_map){const q=c.distance_map,body=allocate(q.values_u16.length*2,2),rc=allocate(28);q.values_u16.forEach((v,j)=>d().setUint16(body+j*2,v,true));[1,1,q.values_u16.length,body,q.values_u16.length,q.start_index,q.field24].forEach((v,j)=>w(rc+j*4,v));w(G+2368,rc);}
 const ownerPointers=[];const ownedGUIDs=new Set();for(const owner of c.guardians){const U=r(G+1788)+owner.unit_index*424,guid=d().getBigUint64(U+112,true).toString();if(guid!==owner.guid||ownedGUIDs.has(guid)||r(U+64)!==3||r(U+72)!==3||owner.capacity!==3||owner.timers_bits.length!==3)throw Error('Guardian GUID owner');ownedGUIDs.add(guid);const pointer=allocate(12,4);owner.timers_bits.forEach((v,j)=>w(pointer+j*4,v));w(U+68,pointer);ownerPointers.push({unit_index:owner.unit_index,guid,pointer});}
 const gameBefore=hex(G,2592);call(947,e.research135_spawn_tick,G,number(f.dt_bits));callCounts[947]=(callCounts[947]??0)+1;
 function capture(capOff,ptrOff,countOff,stride){const capacity=r(G+capOff),p=r(G+ptrOff),count=r(G+countOff);if(count>capacity||capacity>4096||p+capacity*stride>memory.buffer.byteLength)throw Error('Vector bounds');return{capacity,count,storage:Array.from({length:capacity},(_,j)=>hex(p+j*stride,stride))};}
 const n=r(G+1888),p=r(G+1884);if(n>128||r(G+1880)<n)throw Error('Packet bound');
 const packets=Array.from({length:n},(_,j)=>{const q=p+j*16,k=r(q+8),b=r(q+4);if(k>r(q)||k>1048576||b+k>memory.buffer.byteLength)throw Error('Packet payload');return{opcode:d().getUint16(q+12,true),payload_hex:hex(b,k)};});
 const result={pickups:capture(1868,1872,1876,56),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),counter:r(G+2408),message_sequence:r(G+2412),packets,notifications_count:r(G+1900)};
 Object.assign(result,{next_event2424_bits:r(G+2424),last_event2586:bytes()[G+2586],budget_bits:r(G+2416),kill_cost_bits:r(G+2420),velocity_xy:[r(G+1736),r(G+1740)],previous_player_xyz:[0,1,2].map(j=>r(G+2428+j*4)),units:capture(1784,1788,1792,424),other_clocks:Object.fromEntries([2440,2444,2448,2456,2460].map(o=>[o,r(G+o)]))});
 const guardianObservations=ownerPointers.map(({unit_index,guid,pointer})=>{const U=r(G+1788)+unit_index*424;if(d().getBigUint64(U+112,true).toString()!==guid||r(U+68)!==pointer||r(U+64)!==3||r(U+72)!==3)throw Error('Guardian owner detached');return{unit_index,guid,capacity:3,timers_bits:[0,1,2].map(j=>r(pointer+j*4)),ability_pointer:r(U+76),header_pointer:r(U+96),ability_records44_hex:[0,1,2].map(j=>hex(r(U+76)+j*44,44)),header28_hex:hex(r(U+96),28)};});result.guardian_cooldowns=guardianObservations;
 const localeAfter=locale();if(JSON.stringify(localeBefore)!==JSON.stringify(localeAfter))throw Error('Locale mutated');
 world.verify();if(hostCalls)throw Error('Denied host attempted');peak=Math.max(peak,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,result,game_before2592_hex:gameBefore,game_after2592_hex:hex(G,2592),locale_prestate:localeBefore,locale_poststate:localeAfter})+'\n');
}
for(const c of cases){await run(c);if(global.gc)global.gc();}
await fs.writeFile(dir+'/event-wave135-runtime.json',JSON.stringify({cases:cases.length,functions:callCounts,fresh_instances:cases.length,max_memory_bytes:peak,memory_cap_bytes:268435456,actual_host_calls:hostCalls,denied_imports:878,stack_checks:stackChecks,stack_all_restored:stackChecks.every(x=>x.before===x.after&&x.returned),original_function_bodies_unchanged:true,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false,original_memory_snapshot_read:true,context_snapshot_sha256:hash(snapshot),locale_once_injected:false,locale_selected_input_explicit:true},null,2)+'\n');
