// Unchanged full1371420; explicit packed query-world and56B backing fixtures.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {packAiWorld135} from './ai_world135_packing.mjs';
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
const added=[{name:'research137_resource_pickup1420',kind:0,index:1420},{name:'research137_resource_pickup_stack0',kind:3,index:0}];
if(JSON.stringify(updated)!==JSON.stringify([...prior,...added]))throw Error('Private export surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>256)throw Error('Import/case profile');
let hostCalls=0,peak=0;const checks=[];
for(const c of cases){
 const bindings={};for(const item of imports){bindings[item.module]??={};bindings[item.module][item.name]=()=>{hostCalls++;throw Error('Denied original host '+item.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research137_resource_pickup_stack0;
 const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Precall stack');let returned=false;try{const result=fn(...args);returned=true;return result;}finally{const after=stack.value;checks.push({case_id:c.id,index,before,after,returned});if(before!==after)throw Error('Stack not restored');}}
 function allocate(n,align=8){if(n<1||n>4194304)throw Error('Allocation budget');const p=call(91933,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');bytes().fill(0,p,p+n);return p;}
 const world=await packAiWorld135({memory,allocate},c.world),G=allocate(8192),s=c.input;
 const name=Buffer.from(c.map_id_utf8),M=allocate(name.length,1);bytes().set(name,M);w(G+184,M);w(G+188,name.length);w(G+2348,world.R);
 const v=s.pickups,buffer=v.storage.length?allocate(v.storage.length*56):8;
 if(!Number.isInteger(v.count)||v.count>v.storage.length||v.storage.length>4096)throw Error('Fixture vector bounds');
 v.storage.forEach((row,j)=>{if(row.length!==56||row.some(x=>x!==null&&(!Number.isInteger(x)||x<0||x>255)))throw Error('Physical row');bytes().set(row.map(x=>x===null?c.unknown_poison:x),buffer+j*56);});
 w(G+1868,v.storage.length);w(G+1872,buffer);w(G+1876,v.count);w(G+2352,s.now_bits);w(G+2408,s.counter);
 s.rng_words.forEach((word,j)=>w(G+1720+j*4,word));w(G+1880,0);w(G+1884,4);w(G+1888,0);
 w(G+1892,0);w(G+1896,4);w(G+1900,0);w(G+2412,c.message_sequence);
 const P=allocate(12,4);s.position_bits.forEach((word,j)=>w(P+j*4,word));const gameBefore=hex(G,8192);call(1420,e.research137_resource_pickup1420,G,s.kind,s.amount,P);
 const capacity=r(G+1868),pointer=r(G+1872),count=r(G+1876);
 if(count>capacity||capacity>4096||pointer+capacity*56>memory.buffer.byteLength)throw Error('Pickup result bounds');
 const n=r(G+1888),p=r(G+1884);if(n>128||r(G+1880)<n)throw Error('Packet bound');
 const packets=Array.from({length:n},(_,j)=>{const q=p+j*16,k=r(q+8),b=r(q+4);if(k>r(q)||k>1048576||b+k>memory.buffer.byteLength)throw Error('Packet payload');return{opcode:d().getUint16(q+12,true),payload_hex:hex(b,k)};});
 const result={pickups:{capacity,count,storage:Array.from({length:capacity},(_,j)=>hex(pointer+j*56,56))},rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),counter:r(G+2408),message_sequence:r(G+2412),packets,notifications_count:r(G+1900)};
 world.verify();if(hostCalls)throw Error('Denied host attempted');peak=Math.max(peak,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,result,game_before8192_hex:gameBefore,game_after8192_hex:hex(G,8192)})+'\n');
 if(global.gc)global.gc();
}
await fs.writeFile(dir+'/resource-pickup137-runtime.json',JSON.stringify({version:'0.137.0',build:'d171b8f9f',cases:cases.length,functions:{1420:cases.length},fresh_instances:cases.length,max_memory_bytes:peak,memory_cap_bytes:33554432,actual_host_calls:hostCalls,denied_imports:878,stack_checks:checks,stack_all_restored:checks.every(x=>x.before===x.after&&x.returned),original_function_bodies_unchanged:true,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false,original_memory_snapshot_read:false},null,2)+'\n');
