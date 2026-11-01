// Separate snapshot restoration,256MiB/878denied. Never boot/resource host.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const digest=x=>createHash('sha256').update(x).digest('hex');
const originalSHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2';
const surface=Object.freeze({world_height:29631,terrain_height:18670,nearest_height:23181,spawn_position:8751,random_position:13516,cached_construct:6730,begin_run:1089,companions:1744,world_actor:1821});
function leb(raw,p){let n=0,s=0;while(p<raw.length&&s<=28){const b=raw[p++];n+=(b&127)*2**s;if(b<128)return[n,p];s+=7;}throw Error('LEB bounds');}
function sections(raw){if(raw.subarray(0,8).toString('hex')!=='0061736d01000000')throw Error('WASM header');let p=8;const out=[];while(p<raw.length){const start=p,kind=raw[p++],[n,begin]=leb(raw,p);p=begin+n;if(p>raw.length)throw Error('Section bounds');out.push({kind,start,begin,end:p});}return out;}
function exportsOf(raw,s){let[n,p]=leb(raw,s.begin);const out=[];for(let i=0;i<n;i++){const[len,b]=leb(raw,p);p=b+len;const name=raw.subarray(b,p).toString('utf8'),kind=raw[p++],[index,end]=leb(raw,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export boundary');return out;}

export async function prepareWorldSnapshot135(directory,requiredRoles){
 if(!process.execArgv.includes('--wasm-max-mem-pages=4096'))throw Error('Explicit separate256MiB cap required');
 if(!requiredRoles.length||requiredRoles.some(x=>!Object.hasOwn(surface,x)))throw Error('Unapproved world role');
 const manifest=JSON.parse(await fs.readFile(`${directory}/manifest.json`,'utf8'));
 if(manifest.kind!=='snapshot-derived-world-consumers-not-bootstrap'||manifest.memory_page_cap!==4096||manifest.original_wasm_sha256!==originalSHA)throw Error('Snapshot manifest domain');
 const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url)),changed=await fs.readFile(`${directory}/${manifest.module_file}`);
 if(original.length!==90959080||digest(original)!==originalSHA||digest(changed)!==manifest.module_sha256)throw Error('Original/module identity');
 const old=sections(original),fresh=sections(changed);if(old.map(x=>x.kind).join()!==fresh.map(x=>x.kind).join()||old.some(x=>x.kind===8))throw Error('Section/start profile');
 for(let i=0;i<old.length;i++)if(old[i].kind!==7&&!original.subarray(old[i].start,old[i].end).equals(changed.subarray(fresh[i].start,fresh[i].end)))throw Error('Nonexport source mutation');
 const globals=old.find(x=>x.kind===6);if(original.subarray(globals.begin,globals.end).toString('hex')!=='017f01418080c0000b')throw Error('Mutable global profile');
 const priorExports=exportsOf(original,old.find(x=>x.kind===7)),nowExports=exportsOf(changed,fresh.find(x=>x.kind===7));
 if(JSON.stringify(priorExports)!==JSON.stringify(nowExports.slice(0,priorExports.length)))throw Error('Original exports changed');
 const adds=nowExports.slice(priorExports.length),last=adds.at(-1);
 if(adds.length!==manifest.roles.length+1||last.name!=='research_snapshot135_stack'||last.kind!==3||last.index!==0)throw Error('Stack export');
 if(adds.slice(0,-1).some((x,i)=>x.kind!==0||x.name!==manifest.roles[i].export||x.index!==surface[manifest.roles[i].role])||requiredRoles.some(x=>!manifest.roles.some(y=>y.role===x)))throw Error('Role export');
 const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module);if(imports.length!==878||imports.some(x=>x.kind!=='function'))throw Error('Host surface');
 const cached=new Map();
 return {manifest,async restore(snapshotPath,snapshotSHA){
  const key=snapshotPath+'\0'+snapshotSHA;let snapshot=cached.get(key);
  if(!snapshot){snapshot=await fs.readFile(snapshotPath);if(snapshot.length%65536||snapshot.length>256*1024*1024||digest(snapshot)!==snapshotSHA)throw Error('Snapshot identity/size');cached.set(key,snapshot);}
  const bindings={},hostCalls=[],calls=[];
  for(const m of imports){bindings[m.module]??={};bindings[m.module][m.name]=()=>{hostCalls.push(`${m.module}.${m.name}`);throw Error('Snapshot original host import denied');};}
  const instance=await WebAssembly.instantiate(module,bindings),ex=instance.exports,memory=ex.memory,stack=ex.research_snapshot135_stack;
  if(!(memory instanceof WebAssembly.Memory)||!(stack instanceof WebAssembly.Global)||stack.value!==1048576||memory.buffer.byteLength>snapshot.length)throw Error('Fresh mutable stack/memory');
  const initialMemoryBytes=memory.buffer.byteLength,pages=(snapshot.length-memory.buffer.byteLength)/65536;if(pages)memory.grow(pages);
  new Uint8Array(memory.buffer).set(snapshot);
  if(memory.buffer.byteLength!==snapshot.length||digest(new Uint8Array(memory.buffer))!==snapshotSHA||stack.value!==1048576)throw Error('Complete linear memory restoration');
  const roles=Object.freeze(Object.fromEntries(requiredRoles.map(role=>[role,function(...args){
   const before=stack.value,e={role,index:surface[role],stack_before:before};calls.push(e);if(before!==1048576)throw Error('Precall stack differs');
   try{const ret=ex[`research_snapshot135_${role}`](...args);e.returned=true;e.stack_after=stack.value;if(stack.value!==before)throw Error('Returned original stack differs');return ret;}
   catch(error){e.returned=false;e.stack_after=stack.value;e.error=String(error);throw error;}
  }])));
  return {roles,memory,hostCalls,calls,get stackPointer(){return stack.value;},
   snapshot:{path:snapshotPath,sha256:snapshotSHA,bytes:snapshot.length,initial_memory_bytes:initialMemoryBytes,restored_memory_bytes:memory.buffer.byteLength,mutable_globals:1,stack_before:1048576,stack_after:stack.value,bootstrap_reexecuted:false,externref_table_restored:false},
   allocate(size,alignment=8){
    if(!Number.isInteger(size)||size<1||size>4194304||![1,2,4,8,16].includes(alignment)||stack.value!==1048576)throw Error('Snapshot allocation domain');
    const before=memory.buffer.byteLength,p=ex.__wbindgen_malloc(size,alignment)>>>0;
    calls.push({role:'original_allocator',index:91941,size,alignment,pointer:p,stack_after:stack.value,memory_before:before,memory_after:memory.buffer.byteLength});
    if(!p||p+size>memory.buffer.byteLength||memory.buffer.byteLength>256*1024*1024||stack.value!==1048576)throw Error('Allocator/stack/memory budget');
    return p;
   }};
 }};
}
