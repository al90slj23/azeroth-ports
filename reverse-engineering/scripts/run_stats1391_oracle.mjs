// Complete fixed1391_1542, unchanged callees, explicit synthetic input sources.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {once} from 'node:events';
const[dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--max-old-space-size=512')||!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Explicit32MiB/512MiB caps');
const SOURCE_SHA='8831b4a21314cefd0b9f56dcb5681ac822a9ee30770ab1acae473f9e8f2aec71';
const m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),original=await fs.readFile(new URL('../originals/official-release-v2-20261102T133059.984802Z/latest-wenilla_bg.wasm',import.meta.url)),changed=await fs.readFile(dir+'/'+m.module_file),input=await fs.readFile(inputFile);
const prepared=JSON.parse(await fs.readFile(dir+'/prepared.json','utf8'));if(hash(input)!==prepared.artifacts['fixtures.jsonl']||hash(changed)!==prepared.artifacts[m.module_file])throw Error('Frozen SHA');
if(hash(original)!==SOURCE_SHA||hash(changed)!==m.module_sha256||input.length>33554432||m.entry.index!==1542||m.entry.body_sha256!=='97ec7ef75ba04560c5235f0892cce1e9da30ced32c5aad5120f97e9d080d6df8')throw Error('Original/module/input identities');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const x=b[p++];n+=(x&127)*2**s;if(x<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){const out=[];let p=8;while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const a=sections(original),b=sections(changed);if(a.map(s=>s.kind).join()!==b.map(s=>s.kind).join()||a.some(s=>s.kind===8))throw Error('Section/start');
a.forEach((s,i)=>{if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(b[i].start,b[i].end)))throw Error('Nonexport change');});
const old=exportsOf(original,a.find(s=>s.kind===7)),all=exportsOf(changed,b.find(s=>s.kind===7));if(JSON.stringify(all.slice(0,old.length))!==JSON.stringify(old)||JSON.stringify(all.slice(old.length))!==JSON.stringify([{name:'research1391_stats1542',kind:0,index:1542},{name:'research1391_stats_stack0',kind:3,index:0}]))throw Error('Export surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module);if(imports.length!==882||imports.some(x=>x.kind!=='function'))throw Error('Imports');
if(m.function_imports!==882||m.implicit_start!==false||m.allocator_index!==93365||m.allocator_type_index!==6||m.allocator_signature.join(':')!=='7f7f:7f'||JSON.stringify(imports.map(({module,name})=>({module,name})))!==JSON.stringify(m.original_imports.map(({module,name})=>({module,name}))))throw Error('Exact139 ABI/import names');
const cases=input.toString().trim().split('\n').filter(Boolean).map(JSON.parse);if(!cases.length||cases.length>12000)throw Error('Case budget');
let e,memory,stack,instances=0,calls=0,hostCalls=0,peak=0,outputBytes=0,stackGuards=0,error=null;
const stackReturns=[];
const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),r=p=>d().getUint32(p,true),w=(p,v)=>{if(!Number.isInteger(v)||v<0||v>0xffffffff)throw Error('u32');d().setUint32(p,v,true);},hex=(p,n)=>Buffer.from(bytes().subarray(p,p+n)).toString('hex');
function call(idx,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Stack before');let returned=false;try{const v=fn(...args);returned=true;return v;}finally{stackGuards++;if(stack.value!==before)throw Error('Stack after');if(idx===1542)stackReturns.push({case:calls,before,after:stack.value,returned});}}
function alloc(n){n=Math.max(8,n);if(!Number.isInteger(n)||n>4194304)throw Error('Allocation bound');const p=call(93365,e.__wbindgen_malloc,n,8)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('WASM cap');bytes().fill(0,p,p+n);return p;}
try{for(const c of cases){
 if(c.id!==calls)throw Error('IDs/order');
 if(calls%32===0){if(global.gc)global.gc();const bindings={};for(const x of imports){bindings[x.module]??={};bindings[x.module][x.name]=()=>{hostCalls++;throw Error('Host denied '+x.name);};}e=(await WebAssembly.instantiate(module,bindings)).exports;memory=e.memory;stack=e.research1391_stats_stack0;instances++;if(stack.value!==1048576)throw Error('Fresh stack');}
 const s=c.input,G=alloc(8192),vector=(entries,stride,ptr,len,write)=>{entries??=[];if(entries.length>4096)throw Error('Vector budget');const p=alloc(entries.length*stride);w(G+ptr-4,entries.length);w(G+ptr,p);w(G+len,entries.length);entries.forEach((x,i)=>write(p+stride*i,x));};
 bytes()[G+360]=s.class_byte&255;bytes()[G+361]=s.race_byte&255;w(G+1432,s.level);w(G+1536,s.old_max_hp_bits);w(G+1440,s.current_hp_bits);w(G+2352,s.now_bits);w(G+268,s.conditional268_bits);bytes()[G+2582]=s.flag2574&255;w(G+1648,s.previous_speed_bits);d().setBigUint64(G+1336,1n,true);
 for(const[name,offset]of[['pool1532_bits',1444],['pool1536_bits',1448],['pool768_bits',764],['conditional1344_id',1344],['conditional1348_bits',1348]])w(G+offset,s[name]);
 w(G+1884,4);
 vector(s.passives,8,1696,1700,(p,x)=>{w(p,x.tag);w(p+4,x.value_bits);});
 vector(s.item_modifiers,8,2028,2032,(p,x)=>{bytes()[p]=x.tag&255;w(p+4,x.value_bits);});
 vector(s.adjustments,16,1672,1676,(p,x)=>{const a=alloc(40);w(p,a);w(p+4,x.value_bits);w(a+32,x.definition32_bits);bytes()[a+36]=x.tag&255;});
 vector(s.owned_skills,8,172,176,(p,x)=>{const a=alloc(40),raw=new TextEncoder().encode(x[0]);if(raw.length>128)throw Error('ID bound');const text=alloc(raw.length);bytes().set(raw,text);w(p,a);bytes()[p+4]=x[1]&255;w(a+32,text);w(a+36,raw.length);});
 vector(s.timed_definitions,36,2052,2056,(p,x)=>{w(p,x.kind);w(p+20,x.value20_bits);bytes()[p+32]=x.modifier_tag&255;});
 vector(s.timed_records,12,596,600,(p,x)=>{w(p,x.definition_index);w(p+4,x.stack_count);w(p+8,x.expires_bits);});
 vector(s.live_effects,32,1708,1712,(p,x)=>{w(p+8,x.kind);w(p+12,x.value_bits);w(p+20,x.spell_id);w(p+24,x.expires_bits);});
 call(1542,e.research1391_stats1542,G);calls++;
 const tree=r(G+2476);if(!tree||r(G+2480)!==0||d().getUint16(tree+50,true)!==3)throw Error('Output BTree shape');const keys=[0,1,2].map(i=>d().getUint16(tree+52+2*i,true));if(keys.join()!=='22,28,1109')throw Error('Output keys');
 const q={id:c.id,derived_bits:Object.fromEntries(Array.from({length:23},(_,i)=>[1536+4*i,r(G+1536+4*i)])),current_hp_bits:r(G+1440),auxiliary_bits:Object.fromEntries([1444,1448,1348,764].map(o=>[o,r(G+o)])),object_fields:Object.fromEntries(keys.map((k,i)=>[k,r(tree+4+4*i)])),speed_bits:r(G+1648),speed_sequence:r(G+1644),movement_queue_count:r(G+1888),raw_game2592_hex:hex(G,2592)};
 const line=JSON.stringify(q)+'\n';if(Buffer.byteLength(line)>16384||(outputBytes+=Buffer.byteLength(line))>134217728)throw Error('Output bound');if(!process.stdout.write(line))await once(process.stdout,'drain');
 peak=Math.max(peak,memory.buffer.byteLength);if(hostCalls||peak>33554432)throw Error('Host/WASM guard');
}}
catch(x){error=String(x);throw x;}
finally{await fs.writeFile(dir+'/runtime.json',JSON.stringify({version:'0.139.1',actual_build:'b89633f9b',cases:cases.length,completed_cases:calls,full1542_calls:calls,fresh_instances:instances,actual_host_calls:hostCalls,denied_imports:882,peak_memory_bytes:peak,memory_cap_bytes:33554432,heap_cap_mib:512,output_bytes:outputBytes,stack_guards:stackGuards,stats_stack_returns:stackReturns,stack_all_restored:stackReturns.every(x=>x.returned&&x.before===x.after&&x.after===1048576),denied_import_surface:imports,denied_import_surface_sha256:hash(Buffer.from(JSON.stringify(imports))),original_function_bodies_unchanged:true,network_used:false,user_saves_accessed:false,original_snapshot_loaded:false,error},null,2)+'\n');}
