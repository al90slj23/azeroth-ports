// Complete139 query entries on the corrected v2 world; all882 hosts denied.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {once} from 'node:events';
const[dir,file]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--max-old-space-size=512')||!process.execArgv.includes('--wasm-max-mem-pages=4096'))throw Error('Explicit heap/memory caps');
const m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),cfgRaw=await fs.readFile(file),cfg=JSON.parse(cfgRaw),input=await fs.readFile(cfg.input_file);
if(Object.keys(cfg).sort().join()!=='input_file,input_sha256,snapshot_file,snapshot_sha256,source_ranges_file,source_ranges_sha256,world_rc'||input.length>33554432||hash(input)!==cfg.input_sha256)throw Error('Input config');
const original=await fs.readFile(new URL('../originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm',import.meta.url)),changed=await fs.readFile(dir+'/'+m.module_file);
if(hash(original)!=='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'||hash(changed)!==m.module_sha256||m.only_changed_section!==7)throw Error('Module identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const x=b[p++];n+=(x&127)*2**s;if(x<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){const a=[];let p=8;while(p<b.length){const start=p,k=b[p++],[n,a0]=leb(b,p),end=a0+n;if(end>b.length)throw Error('Section');a.push({k,start,a:a0,end});p=end;}return a;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const a=[];while(n--){const[l,q]=leb(b,p);p=q+l;const name=b.subarray(q,p).toString(),kind=b[p++],[index,z]=leb(b,p);p=z;a.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return a;}
const old=sections(original),fresh=sections(changed);if(old.map(x=>x.k).join()!==fresh.map(x=>x.k).join()||old.some(x=>x.k===8))throw Error('Sections/start');
old.forEach((x,i)=>{if(x.k!==7&&!original.subarray(x.start,x.end).equals(changed.subarray(fresh[i].start,fresh[i].end)))throw Error('Nonexport mutation');});
const oldEx=exportsOf(original,old.find(x=>x.k===7)),newEx=exportsOf(changed,fresh.find(x=>x.k===7));
const wanted=Object.values(m.roles).map(x=>({name:x.export,kind:0,index:x.index})).concat({name:m.stack_export,kind:3,index:0});
if(JSON.stringify(newEx.slice(0,oldEx.length))!==JSON.stringify(oldEx)||JSON.stringify(newEx.slice(oldEx.length))!==JSON.stringify(wanted))throw Error('Export identities');
if(m.roles.world_height.index!==29912||m.roles.terrain_height.index!==18742||m.roles.nearest_height.index!==23333)throw Error('Role binding');
const snap=await fs.readFile(cfg.snapshot_file),rangeRaw=await fs.readFile(cfg.source_ranges_file),ranges=JSON.parse(rangeRaw);
if(hash(snap)!==cfg.snapshot_sha256||hash(snap)!=='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'||snap.length!==111804416||cfg.world_rc!==20544696||hash(rangeRaw)!==cfg.source_ranges_sha256)throw Error('Healthy v2 snapshot/ranges');
const cases=JSON.parse(input);if(!Array.isArray(cases)||!cases.length||cases.length>12000)throw Error('Case bounds');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module);
if(imports.length!==882||imports.some(x=>x.kind!=='function')||JSON.stringify(imports.map(({module,name})=>({module,name})))!==JSON.stringify(m.original_imports.map(({module,name})=>({module,name}))))throw Error('Exact882 import surface');
let e,memory,stack,instances=0,calls=0,allocations=0,stackGuards=0,traps=0,hostCalls=0,peak=0,outputBytes=0;
const entryCalls=[],worldChecks=[];let O;
const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),num=x=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,x,true);return v.getFloat32(0,true);};
function verifyWorld(){for(const x of ranges){if(x.offset<0||x.bytes<0||x.offset+x.bytes>memory.buffer.byteLength||hash(new Uint8Array(memory.buffer,x.offset,x.bytes))!==x.sha256)throw Error('World range mutation');}worldChecks.push({instance:instances,ranges:ranges.length,unchanged:true});}
function alloc(n){if(!Number.isInteger(n)||n<4||n>4194304||stack.value!==1048576)throw Error('Allocator input');const p=e.__wbindgen_malloc(n,8)>>>0;allocations++;stackGuards++;if(!p||p+n>memory.buffer.byteLength||stack.value!==1048576||memory.buffer.byteLength>268435456)throw Error('Allocator/stack/cap');return p;}
async function restore(){const bindings={};for(const x of imports){bindings[x.module]??={};bindings[x.module][x.name]=()=>{hostCalls++;throw Error('Original host denied '+x.name);};}e=(await WebAssembly.instantiate(module,bindings)).exports;memory=e.memory;stack=e[m.stack_export];instances++;if(stack.value!==1048576||memory.buffer.byteLength>snap.length)throw Error('Fresh stack/size');memory.grow((snap.length-memory.buffer.byteLength)/65536);bytes().set(snap);if(hash(bytes())!==cfg.snapshot_sha256)throw Error('Full snapshot restore');verifyWorld();O=alloc(16);}
function invoke(role,...args){if(stack.value!==1048576)throw Error('Entry stack');let returned=false;const record={role,index:m.roles[role].index,before:stack.value};try{e[m.roles[role].export](...args);returned=true;}finally{calls++;stackGuards++;record.after=stack.value;record.returned=returned;entryCalls.push(record);if(returned&&stack.value!==1048576)throw Error('Return stack');}}
await restore();
for(const c of cases){
 let answer;
 if(c.kind==='height'){
  const output={};for(const role of['terrain_height','world_height']){bytes().fill(0xa5,O,O+16);invoke(role,O,cfg.world_rc+8,num(c.x_bits),num(c.y_bits));output[role]={found:u(O)===1,value_bits:u(O+4),output16_hex:Buffer.from(bytes().subarray(O,O+16)).toString('hex')};}
  answer={id:c.id,kind:c.kind,entry_status:'returned',output};
 }else if(c.kind==='nearest'){
  const s=c.raster;if(!s||s.values_bits.length>4096||!Number.isInteger(s.width)||s.width<0||s.width>4096)throw Error('Raster bounds');
  const Q=alloc(36),P=alloc(Math.max(4,s.values_bits.length*4));bytes().fill(0xa5,Q,Q+36);w(Q+16,P);w(Q+20,s.values_bits.length);w(Q+24,s.origin_xy_bits[0]);w(Q+28,s.origin_xy_bits[1]);w(Q+32,s.width);s.values_bits.forEach((v,j)=>w(P+j*4,v));bytes().fill(0xa5,O,O+16);
  let trapped=false;
  try{invoke('nearest_height',O,Q,num(c.x_bits),num(c.y_bits));}catch(x){if(!(x instanceof WebAssembly.RuntimeError)||x.message!=='unreachable')throw x;trapped=true;traps++;}
  answer={id:c.id,kind:c.kind,entry_status:trapped?'bounds_trap':'returned',output16_hex:Buffer.from(bytes().subarray(O,O+16)).toString('hex')};
  if(!trapped)answer.output={found:u(O)===1,xyz_words:Array.from({length:3},(_,j)=>u(O+4+4*j))};
  if(trapped){verifyWorld();await restore();}
 }else throw Error('Unknown query');
 if(hostCalls)throw Error('Denied host called');peak=Math.max(peak,memory.buffer.byteLength);const line=JSON.stringify(answer)+'\n';if(Buffer.byteLength(line)>16384||(outputBytes+=Buffer.byteLength(line))>67108864)throw Error('Output bound');if(!process.stdout.write(line))await once(process.stdout,'drain');
}
verifyWorld();
await fs.writeFile(dir+'/runtime.json',JSON.stringify({version:'0.139.0',build:'f79c5e2b4',cases:cases.length,full_query_calls:calls,allocations,fresh_instances:instances,stack_guards:stackGuards,entry_calls:entryCalls,world_checks:worldChecks,bounds_traps:traps,host_calls:hostCalls,denied_imports:882,peak_memory_bytes:peak,output_bytes:outputBytes,source_sha256:hash(original),module_sha256:hash(changed),input_sha256:hash(input),snapshot_sha256:hash(snap),range_sha256:hash(rangeRaw),original_callees_unchanged:true,only_export_section7_changed:true,externref_state_restored:false,natural_bootstrap_executed:false,native_executed:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
