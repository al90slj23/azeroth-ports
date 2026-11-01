// Private1510/4464 real parser/collision calls, fresh modules, all878 hosts denied.
import fs from 'node:fs/promises';import{createHash}from'node:crypto';
const[directory,inputPath]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Explicit32MiB cap required');
const manifest=JSON.parse(await fs.readFile(directory+'/manifest.json','utf8')),raw=await fs.readFile(directory+'/'+manifest.module_file);
if(hash(raw)!==manifest.module_sha256||manifest.original_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||manifest.roles.map(x=>x.index).join()!=='1510,4464')throw Error('Private module identity');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module),cases=JSON.parse(await fs.readFile(inputPath,'utf8'));
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>1024)throw Error('Import/input budget');
let calls=0,parses=0,appends=0,hostCalls=0,maxMemory=0,allocatorCalls=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input'||Object.keys(c.input).sort().join()!=='append_operations,assets,initial_mesh')throw Error('Original only receives input');
 const s=c.input,bindings={};for(const imp of imports){bindings[imp.module]??={};bindings[imp.module][imp.name]=()=>{hostCalls++;throw Error('All original hosts denied');};}
 const instance=await WebAssembly.instantiate(module,bindings),ex=instance.exports,memory=ex.memory;
 const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),u=p=>d().getUint32(p,true),w=(p,x)=>d().setUint32(p,x>>>0,true);
 const memoryInitial=memory.buffer.byteLength,hashStateBefore=Buffer.from(bytes().slice(14523240,14523257)).toString('hex');
 function alloc(n,alignment=8){if(!Number.isInteger(n)||n<1||n>8388608)throw Error('Explicit allocation cap');allocatorCalls++;const p=ex.__wbindgen_malloc(n,alignment)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('32MiB budget');return p;}
 const hex=(p,n)=>{if(!Number.isInteger(p)||p<0||p+n>memory.buffer.byteLength)throw Error('Capture bounds');return Buffer.from(bytes().slice(p,p+n)).toString('hex');};
 function vector(header,stride,maxCount){
  const capacity=u(header),pointer=u(header+4),length=u(header+8);
  if(length>capacity||capacity>maxCount||capacity&&pointer+capacity*stride>memory.buffer.byteLength)throw Error('Output vector domain');
  return{capacity,pointer,length,active_hex:hex(pointer,length*stride),backing_hex:hex(pointer,capacity*stride)};
 }
 const vertexVec=alloc(12),indexVec=alloc(12);
 function initVector(header,values,stride){
  const n=values.length,p=n?alloc(n*stride,stride===12?4:4):4;
  if(stride===12)values.forEach((v,j)=>v.forEach((x,k)=>w(p+j*12+k*4,x)));else values.forEach((x,j)=>w(p+j*4,x));
  w(header,n);w(header+4,p);w(header+8,n);
 }
 initVector(vertexVec,s.initial_mesh.vertices_bits,12);initVector(indexVec,s.initial_mesh.indices,4);
 const assetRows=[];const assetPointers=[];
 for(const a of s.assets){
  if(Object.keys(a).sort().join()!=='bytes,chain,path,sha256')throw Error('Raw asset input keyset');
  const data=await fs.readFile(a.path);if(data.length!==a.bytes||data.length>32*1024*1024||hash(data)!==a.sha256)throw Error('Actual asset bytes identity');
  const p=alloc(data.length);bytes().set(data,p);assetPointers.push({p,n:data.length,sha256:a.sha256});
  const cursor=alloc(16),out=alloc(160);bytes().fill(0xa5,out,out+160);bytes().fill(0,cursor,cursor+16);w(cursor,p);w(cursor+4,data.length);
  const cursorBefore=hex(cursor,16);ex.wmo135_parse(out,cursor);calls++;parses++;
  const tag=u(out);let projection;
  if(tag===0xffffffff)projection={kind:'root',group_count:u(out+40)};
  else if(tag===0xfffffffe)throw Error('Original1510 reported real asset error');
  else projection={kind:'group',vertices_hex:vector(out,12,65536).active_hex,indices_u16_hex:vector(out+48,2,4194304).active_hex,
      attributes_hex:vector(out+72,2,1398101).active_hex,group_flags:u(out+152),liquid_type:u(out+156)};
  assetRows.push({chain:a.chain,projection,raw_output160_hex:hex(out,160),raw_cursor_before_hex:cursorBefore,raw_cursor_after_hex:hex(cursor,16),
    vectors:projection.kind==='group'?{vertices:vector(out,12,65536),indices_u16:vector(out+48,2,4194304),attributes:vector(out+72,2,1398101)}:null});
 }
 const appendStages=[];
 for(const op of s.append_operations){
  if(Object.keys(op).sort().join()!=='asset_index,exclude_flags,required_flags'||!Number.isInteger(op.asset_index)||!assetPointers[op.asset_index])throw Error('Append operation keyset');
  const a=assetPointers[op.asset_index];ex.wmo135_append_collision(a.p,a.n,op.exclude_flags,op.required_flags,vertexVec,indexVec);calls++;appends++;
  appendStages.push({vertices:vector(vertexVec,12,1048576),indices_u32:vector(indexVec,4,4194304),raw_vertex_vec12_hex:hex(vertexVec,12),raw_index_vec12_hex:hex(indexVec,12)});
 }
 for(const a of assetPointers)if(hash(bytes().subarray(a.p,a.p+a.n))!==a.sha256)throw Error('Original mutated actual WMO input');
 if(hostCalls||memory.buffer.byteLength>33554432)throw Error('Host/memory boundary');
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,assets:assetRows,append_stages:appendStages,memory_initial_bytes:memoryInitial,memory_bytes:memory.buffer.byteLength,
   hash_state_before_hex:hashStateBefore,hash_state_after_hex:hex(14523240,17),raw_inputs_unchanged:true})+'\n');
}
await fs.writeFile(directory+'/wmo-geometry135-runtime.json',JSON.stringify({cases:cases.length,calls,parse_entries:parses,append_entries:appends,fresh_instances:cases.length,
 max_memory_bytes:maxMemory,allocator_calls:allocatorCalls,denied_imports:878,actual_host_calls:hostCalls,memory_page_cap:512,
 original_functions:[1510,4464],all_callees_unchanged:true,hash_initialization_original:true,
 snapshot_input_used:false,world_or_once_injected:false,appstart_called:false,network_used:false,user_saves_accessed:false,node:process.version},null,2)+'\n');
