// Complete unchanged922/4600/1072 with explicit controlled922 entry scratch+48.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const[dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('32MiB cap required');
const sourceSHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2';
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(hash(original)!==sourceSHA||hash(changed)!==manifest.module_sha256||input.length>4194304)throw Error('Source/input identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const before=sections(original),after=sections(changed);
if(before.map(s=>s.kind).join()!==after.map(s=>s.kind).join()||before.some(s=>s.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Original nonexport bytes changed');});
const oldExports=exportsOf(original,before.find(s=>s.kind===7)),newExports=exportsOf(changed,after.find(s=>s.kind===7));
const allowed=[{name:'research135_live_cast922',kind:0,index:922},{name:'research135_live_select1072',kind:0,index:1072},{name:'research135_live_resume4600',kind:0,index:4600},{name:'research135_live_stack0',kind:3,index:0}];
if(JSON.stringify(newExports.slice(0,oldExports.length))!==JSON.stringify(oldExports)||JSON.stringify(newExports.slice(oldExports.length))!==JSON.stringify(allowed))throw Error('Private export surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>256)throw Error('Import/case profile');
let calls=0,instances=0,hostCalls=0,peak=0,outputBytes=0,error=null;const stackChecks=[],entryCounts={};
try{for(const c of cases){
 if(global.gc)global.gc();const bindings={};for(const x of imports){bindings[x.module]??={};bindings[x.module][x.name]=()=>{hostCalls++;throw Error('Original host denied '+x.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research135_live_stack0;instances++;
 const d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 function call(idx,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Initial stack');let returned=false;try{const result=fn(...args);returned=true;return result;}finally{const after=stack.value;stackChecks.push({id:c.id,index:idx,before,after,returned});if(before!==after)throw Error('Stack restore');}}
 function alloc(n,align=8){if(!Number.isInteger(n)||n<1||n>4194304)throw Error('Alloc budget');const p=call(91941,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');b().fill(0,p,p+n);return p;}
 const s=c.level,t=s.stats,G=alloc(8192),A=alloc(80),U=alloc(424),R=alloc(128);w(G+2348,R);w(R+32,0xffffffff);w(R+56,0xffffffff);w(R+120,1);
 for(const key of ['passives','adjustments','item_modifiers','owned_skills','timed_records','definitions'])if(s.sources[key].length)throw Error('Empty other source domain');
 for(const[cap,ptr,len,align]of[[1656,1660,1664,4],[1904,1908,1912,4],[1952,1956,1960,4],[2024,2028,2032,4],[2048,2052,2056,4],[2084,2088,2092,4],[2096,2100,2104,4],[1892,1896,1900,4],[2000,2004,2008,4],[1880,1884,1888,4],[1868,1872,1876,8]]){w(G+cap,0);w(G+ptr,align);w(G+len,0);}
 for(const[o,v]of Object.entries(s.derived_bits))w(G+Number(o),v);b()[G+360]=t.class_byte;b()[G+361]=t.race_byte;b()[G+2582]=t.flag2574;b()[G+2587]=s.phase2587;b()[G+2585]=s.selection_kind2585;b()[G+387]=s.heal_gate387;b()[G+2576]=s.flags2576;b()[G+2572]=s.gate2572;b()[G+2573]=s.flags2573;b()[G+2581]=s.choice_inputs.flag2581;
 for(const[o,v]of[[1440,t.current_hp_bits],[1536,t.old_max_hp_bits],[1648,t.previous_speed_bits],[2352,t.now_bits],[1432,s.progression.level],[1436,s.progression.xp],[2376,s.progression.pending_upgrades],[2400,s.generation_counter2400],[1456,7],[1100,9],[2412,19],[1644,9],[268,t.conditional268_bits],[1344,t.conditional1344_id],[1348,t.conditional1348_bits],[1444,t.pool1532_bits],[1448,t.pool1536_bits],[768,t.pool768_bits],[756,s.pool756_bits]])w(G+o,v);
 s.rng_words.forEach((v,j)=>w(G+1720+4*j,v));d().setBigUint64(G+1336,42n,true);d().setBigUint64(G+776,1n,true);d().setBigUint64(U+112,1n,true);w(U+40,0xffffffff);w(U+64,0xffffffff);w(U+244,0xffffffff);w(U+288,0x42c80000);w(U+292,0x42c80000);w(U+316,0x3f800000);w(U+328,0x3f800000);w(G+1784,c.target_present?1:0);w(G+1788,U);w(G+1792,c.target_present?1:0);
 if(c.mode==='cast'){w(G+1656,1);w(G+1660,A);w(G+1664,1);}
 b().set(Buffer.from(c.cast_owned_hex,'hex'),A);b().set(Buffer.from(c.basic_hex,'hex'),G+1256);
 const cap=c.physical_live.storage.length;if(cap>128||c.physical_live.count>cap)throw Error('Live owner budget');const L=cap?alloc(cap*32):4;w(G+1704,cap);w(G+1708,L);w(G+1712,c.physical_live.count);c.physical_live.storage.forEach((row,i)=>{if(row.length!==32)throw Error('Live stride');b().set(row.map(v=>v===null?c.unknown_poison:v),L+i*32);});
 if(c.mode==='select'){
  const P=alloc(80);w(P+60,0x80000000);const def=5467428;w(P+64,r(def+12));w(P+68,r(def+16));w(P+76,1);w(G+1904,1);w(G+1908,P);w(G+1912,1);
 }
 if(hex(c.cast_definition_pointer,88)!==c.cast_definition88_hex)throw Error('Static caster declaration');
 const before=hex(G,8192);let success=null,scratch=null;
 if(c.mode==='cast'){
  const address=stack.value-240+48;
  if(!Number.isInteger(c.scratch_word16_bits)||c.scratch_word16_bits<0||c.scratch_word16_bits>0xffffffff||address<0||address+4>memory.buffer.byteLength)throw Error('Explicit922 scratch source');
  scratch={entry_stack:stack.value,frame_bytes:240,offset:48,address,prior_bits:r(address),declared_input_bits:c.scratch_word16_bits};
  w(address,c.scratch_word16_bits);scratch.before_call_bits=r(address);
 }
 if(c.mode==='cast'){success=call(922,e.research135_live_cast922,G,A);entryCounts[922]=(entryCounts[922]??0)+1;}
 else if(c.mode==='resume'){call(4600,e.research135_live_resume4600,G);entryCounts[4600]=(entryCounts[4600]??0)+1;}
 else if(c.mode==='select'){call(1072,e.research135_live_select1072,G,0);entryCounts[1072]=(entryCounts[1072]??0)+1;}else throw Error('Mode');calls++;
 if(hostCalls||memory.buffer.byteLength>33554432)throw Error('Original boundary');const lc=r(G+1704),lp=r(G+1708),ln=r(G+1712);if(ln>lc||lc>256||lp+lc*32>memory.buffer.byteLength)throw Error('Live capture');
 const queue=(base,stride,opcode)=>{const capacity=r(G+base),ptr=r(G+base+4),count=r(G+base+8);if(count>capacity||count>512)throw Error('Queue count');return{capacity,pointer:ptr,count,metadata_hex:hex(ptr,count*stride),active:Array.from({length:count},(_,j)=>{const p=ptr+j*stride,cap=r(p),data=r(p+4),n=r(p+8);if(n>cap||n>1048576||data+n>memory.buffer.byteLength)throw Error('Payload');return{capacity:cap,pointer:data,length:n,...(opcode?{opcode:d().getUint16(p+12,true)}:{}),payload_hex:hex(data,n)};})};};
 const fields=()=>{const root=r(G+2476),depth=r(G+2480),out={},seen=new Set();function walk(p,level){if(!p||seen.has(p)||seen.size>512||level>5)throw Error('BTree');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree nodes');for(let j=0;j<n;j++){if(level)walk(r(p+76+j*4),level-1);const k=d().getUint16(p+52+j*2,true);if([22,28,34,716,717,1109,1176].includes(k))out[k]=r(p+4+j*4);}if(level)walk(r(p+76+n*4),level-1);}if(root)walk(root,depth);return out;};
 const owned=r(G+1664),op=r(G+1660);if(owned>16)throw Error('Owned');const result={success,physical_live:{capacity:lc,count:ln,storage:Array.from({length:lc},(_,j)=>hex(lp+j*32,32))},derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+4*j,r(G+1536+4*j)])),current_hp_bits:r(G+1440),speed_bits:r(G+1648),player_fields:fields(),rng_words:[0,1,2,3].map(j=>r(G+1720+4*j)),phase2587:b()[G+2587],selection_kind2585:b()[G+2585],generation_counter2400:r(G+2400),owned_records_hex:Array.from({length:owned},(_,j)=>hex(op+j*80,80)),cast_owned_hex:hex(A,80),basic_hex:hex(G+1256,80),action_sequence1644:r(G+1644),message_sequence2412:r(G+2412)};
 if(scratch)scratch.after_call_bits=r(scratch.address);
 const line=JSON.stringify({id:c.id,result,controlled_scratch:scratch,raw_Game_before8192_hex:before,raw_Game_after8192_hex:hex(G,8192),live_pointer:lp,raw_packets:queue(1880,16,true),raw_notifications:queue(1892,12,false)})+'\n';if(Buffer.byteLength(line)>2097152||(outputBytes+=Buffer.byteLength(line))>16777216)throw Error('Output budget');process.stdout.write(line);peak=Math.max(peak,memory.buffer.byteLength);
}}
catch(e){error=String(e);throw e;}finally{await fs.writeFile(dir+'/runtime.json',JSON.stringify({cases:cases.length,fresh_instances:instances,full_calls:calls,entry_counts:entryCounts,actual_host_calls:hostCalls,denied_imports:878,peak_memory_bytes:peak,memory_cap_bytes:33554432,heap_mib:512,output_bytes:outputBytes,stack_checks:stackChecks,stack_all_restored:stackChecks.every(x=>x.returned&&x.before===x.after&&x.before===1048576),original_snapshot_loaded:false,application_start_called:false,user_saves_accessed:false,network_used:false,original_bodies_unchanged:true,error},null,2)+'\n');}
