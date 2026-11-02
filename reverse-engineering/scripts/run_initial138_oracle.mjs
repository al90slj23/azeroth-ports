// Full fresh1381571, explicit empty376 profile and borrowed flat query view.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [dir,configPath]=process.argv.slice(2),hash=x=>createHash('sha256').update(x).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('Explicit32MiB/512MiB caps');
const config=JSON.parse(await fs.readFile(configPath,'utf8')),manifest=JSON.parse(await fs.readFile(`${dir}/manifest.json`,'utf8'));
const original=await fs.readFile(new URL('../originals/official-release-20261101T201508.341687Z/latest-wenilla_bg.wasm',import.meta.url)),changed=await fs.readFile(`${dir}/${manifest.module_file}`),inputRaw=await fs.readFile(config.input_path);
if(hash(original)!=='c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b'||hash(changed)!==manifest.module_sha256||hash(inputRaw)!==config.input_sha256||inputRaw.length>4194304||manifest.entry.index!==1571||manifest.entry.body_sha256!=='37447d2eef76c4d93a5e2d2b5c0143ff8ef591e13fded44ee84e06bcb8d9a43e')throw Error('Frozen identities');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const x=b[p++];n+=(x&127)*2**s;if(x<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){const out=[];let p=8;while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const oldSections=sections(original),newSections=sections(changed);if(oldSections.map(s=>s.kind).join()!==newSections.map(s=>s.kind).join()||oldSections.some(s=>s.kind===8))throw Error('Section/start');
oldSections.forEach((s,i)=>{if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(newSections[i].start,newSections[i].end)))throw Error('Nonexport mutation');});
const old=exportsOf(original,oldSections.find(s=>s.kind===7)),all=exportsOf(changed,newSections.find(s=>s.kind===7));
if(JSON.stringify(all.slice(0,old.length))!==JSON.stringify(old)||JSON.stringify(all.slice(old.length))!==JSON.stringify([{name:'research138_initial1571',kind:0,index:1571},{name:'research138_initial_stack0',kind:3,index:0}]))throw Error('Export identity');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(inputRaw);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>512)throw Error('Host/case surface');
let completed=0,hostCount=0,peak=0,stackChecks=0,error=null;
try{for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input,region_id'||c.id!==completed||Object.keys(c.input).sort().join()!=='class_byte,flat_height_bits,object_id_u64,race_byte,region_index,seed_u64')throw Error('Input-only keyset');
 if(global.gc)global.gc();const hostCalls=[],bindings={};for(const m of imports){bindings[m.module]??={};bindings[m.module][m.name]=()=>{hostCalls.push(m.name);hostCount++;throw Error('878 original host imports denied');};}
 const ex=(await WebAssembly.instantiate(module,bindings)).exports,memory=ex.memory,stack=ex.research138_initial_stack0;
 if(stack.value!==1048576)throw Error('Fresh stack');
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function alloc(n,align=8,poison=0){if(stack.value!==1048576)throw Error('Allocator stack before');const p=ex.__wbindgen_malloc(n,align)>>>0;stackChecks++;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432||stack.value!==1048576)throw Error('Owned allocation');bytes().fill(poison,p,p+n);return p;}
 const s=c.input,G=alloc(8192,8,0xa5),P=alloc(376),V=alloc(128,8,0x5a),name=Buffer.from(c.region_id,'ascii'),N=alloc(Math.max(1,name.length),1);
 bytes().set(name,N);w(P+156,4);w(P+168,N);w(P+172,name.length);d().setBigUint64(P+176,BigInt(s.object_id_u64),true);d().setBigUint64(P+184,BigInt(s.seed_u64),true);bytes()[P+344]=s.class_byte;bytes()[P+345]=s.race_byte;
 // This is a borrowed flat-query input, not a forged Rc owner/bootstrap.
 //1571/29649 consume these fields on this path; header/inactive data stay5A.
 bytes()[V+120]=1;w(V+116,s.flat_height_bits);w(V+56,0xffffffff);w(V+32,0xffffffff);
 const profileBefore=hex(P,376),viewBefore=hex(V,128),outputBefore=hex(G,2592);
 ex.research138_initial1571(G,P,V);stackChecks++;
 if(stack.value!==1048576||hostCalls.length||u(G+2348)!==V||profileBefore!==hex(P,376)||viewBefore!==hex(V,128))throw Error('Constructor stack/host/input identity');
 function tree(){const root=u(G+2476),depth=u(G+2480);if(!root)return{};if(depth>4)throw Error('Tree depth');const entries=[],seen=new Set();function walk(p,l){if(!p||p+76>memory.buffer.byteLength||seen.has(p)||seen.size>64)throw Error('Tree bounds');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(l)walk(u(p+76+j*4),l-1);entries.push([d().getUint16(p+52+2*j,true),u(p+4+4*j)]);}if(l)walk(u(p+76+4*n),l-1);}walk(root,depth);return Object.fromEntries(entries);}
 const count=u(G+1664),ptr=u(G+1660);if(count>128||u(G+1912)!==0)throw Error('Owned/candidate domain');
 const packetCapacity=u(G+1880),packetCount=u(G+1888),packetPointer=u(G+1884);if(packetCount>packetCapacity||packetCapacity>32)throw Error('Constructor packet budget');
 const packets=Array.from({length:packetCount},(_,j)=>{const p=packetPointer+j*16,n=u(p+8);if(n>u(p)||n>64)throw Error('Constructor payload budget');return[d().getUint16(p+12,true),hex(u(p+4),n)];});
 const projection={progression:{level:u(G+1432),xp:u(G+1436),pending_upgrades:u(G+2376)},derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,u(G+1536+j*4)])),current_hp_bits:u(G+1440),
  auxiliary_bits:Object.fromEntries([1444,1448,1348,764,752].map(o=>[o,u(G+o)])),speed_bits:u(G+1648),player_fields:tree(),rng_words:[0,1,2,3].map(j=>u(G+1720+j*4)),candidates:[],phase2587:bytes()[G+2587],selection_kind2585:bytes()[G+2585],generation_counter2400:u(G+2400),
  owned_records_hex:Array.from({length:count},(_,j)=>hex(ptr+j*80,80)),racial_record_hex:hex(G+1256,80),player_xyz:[1416,1420,1424].map(o=>u(G+o)),source_id:d().getBigUint64(G+1336,true).toString(),timer1628_bits:u(G+1628),spawn_counter:u(G+2408),message_sequence:u(G+2412),kill_cost_bits:u(G+2420),game_tag:d().getBigUint64(G,true).toString(),member_count:u(G+2540),action_sequence1644:u(G+1644),movement_packets:packets,
  initial_scalar_words:Object.fromEntries([488,736,740,1652,2416,2424,2428,2432,2436,2440,2444,2448,2452,2456,2460,2464,2468,2472,2516].map(o=>[o,u(G+o)])),initial_byte_flags:Object.fromEntries([768,2568,2572,2573,2576,2578,2581,2583].map(o=>[o,bytes()[G+o]])),constructor_tags:Object.fromEntries([416,440,448,456,464,1744,1764].map(o=>[o,u(G+o)])),
  now_bits:u(G+2352),mode2582:bytes()[G+2582],owned_capacity:u(G+1656),owned_count:count,source_counts:{passives:u(G+1700),adjustments:u(G+1676),item_modifiers:u(G+2032),owned_skills:u(G+176),timed_records:u(G+600),definitions:u(G+2056),live_effects:u(G+1712),ability_modifiers:u(G+2044),active84:u(G+648)},unit_count:u(G+1792),pickup_count:u(G+1876),gold:u(G+1456),earned:u(G+1100),flags768:bytes()[G+768],context908:bytes()[G+908],extra_cast1596_bits:u(G+1596)};
 process.stdout.write(JSON.stringify({id:c.id,projection,raw_game2592_hex:hex(G,2592),output_before_hex:outputBefore,profile376_before_hex:profileBefore,profile376_after_hex:hex(P,376),query128_before_hex:viewBefore,query128_after_hex:hex(V,128),
  ownership:{G,profile:P,borrowed_query:V,game_query:u(G+2348),Rc_owner_producer_executed:false,App_produced:false},stack_after:stack.value,host_calls:hostCalls.length})+'\n');completed++;peak=Math.max(peak,memory.buffer.byteLength);
}}
catch(x){error=String(x);throw x;}
finally{await fs.writeFile(`${dir}/runtime.json`,JSON.stringify({version:'0.138.0',actual_build:'382771e6c',cases:cases.length,completed_cases:completed,full1571_calls:completed,fresh_instances:completed,actual_host_calls:hostCount,denied_imports:878,
 peak_memory_bytes:peak,memory_cap_bytes:33554432,stack_guards:stackChecks,initial_stack:1048576,only_export_section_changed:true,old_snapshot_loaded:false,App_produced:false,externref_forged:false,world_Rc_producer_executed:false,
 world_query_input:'Declared borrowedflatquery view;inactiveowner/header5A,notindependentworldproduction',application_start_called:false,phase1_started:false,user_saves_accessed:false,network_used:false,error},null,2)+'\n');}
