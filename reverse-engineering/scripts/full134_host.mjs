// Controlled current-version original module. Only approved research roles,
// memory and the original allocator are exposed. Every host import throws.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

export const original134SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52';
export const digest = value => createHash('sha256').update(value).digest('hex');
const roleIndices = Object.freeze({select_ability:1073,recalculate_stats:1513,finish_selection:4600,
  resolve_owned_ability:22287,auto_cast:916,cast:922,damage:914,gain_experience:4630,upgrade_value:25368});
const originalPath = new URL('../originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm',import.meta.url);
function leb(raw,p) {
  let n=0,shift=0;
  while(p<raw.length&&shift<=28) {const b=raw[p++];n+=(b&127)*2**shift;if(b<128)return[n,p];shift+=7;}
  throw new Error('Malformed LEB');
}
function sections(raw) {
  if(raw.subarray(0,8).toString('hex')!=='0061736d01000000')throw new Error('Invalid WASM');
  const result=[];let p=8;
  while(p<raw.length) {const start=p,kind=raw[p++],[size,begin]=leb(raw,p),end=begin+size;
    if(end>raw.length)throw new Error('Section outside module');result.push({kind,start,begin,end});p=end;}
  return result;
}
function exportsOf(raw,s) {
  let [count,p]=leb(raw,s.begin);const result=[];
  for(let i=0;i<count;++i) {const[n,b]=leb(raw,p);p=b+n;if(p>=s.end)throw new Error('Export outside section');
    const name=raw.subarray(b,p).toString('utf8'),kind=raw[p++],[index,end]=leb(raw,p);p=end;result.push({name,kind,index});}
  if(p!==s.end)throw new Error('Export boundary differs');return result;
}
export async function prepareFull134(directory,requiredRoles) {
  if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw new Error('Explicit32MiB memory cap required');
  if(!requiredRoles.length||requiredRoles.some(x=>!Object.hasOwn(roleIndices,x)))throw new Error('Unapproved research role');
  const manifest=JSON.parse(await fs.readFile(`${directory}/manifest.json`,'utf8'));
  if(manifest.module_file!=='research134-exports.wasm'||manifest.version!=='0.134.0'||manifest.build!=='983346a7')throw new Error('Wrong profile');
  const original=await fs.readFile(originalPath),changed=await fs.readFile(`${directory}/${manifest.module_file}`);
  if(original.length!==90953762||digest(original)!==original134SHA||manifest.original_wasm_sha256!==original134SHA
      ||changed.length>92_000_000||digest(changed)!==manifest.module_sha256)throw new Error('Source identity differs');
  const before=sections(original),after=sections(changed);
  if(before.map(x=>x.kind).join()!==after.map(x=>x.kind).join()||before.some(x=>x.kind===8))throw new Error('Section/start profile differs');
  for(let i=0;i<before.length;++i) {const a=before[i],b=after[i];
    if(a.kind!==7&&!original.subarray(a.start,a.end).equals(changed.subarray(b.start,b.end)))throw new Error('Nonexport source bytes changed');}
  const oldExports=exportsOf(original,before.find(x=>x.kind===7)),newExports=exportsOf(changed,after.find(x=>x.kind===7));
  if(JSON.stringify(oldExports)!==JSON.stringify(newExports.slice(0,oldExports.length)))throw new Error('Original exports changed');
  const added=newExports.slice(oldExports.length);
  if(added.length!==manifest.roles.length||new Set(added.map(x=>x.name)).size!==added.length
      ||added.some((x,i)=>x.kind!==0||x.name!==`research134_${manifest.roles[i].role}`
        ||x.index!==roleIndices[manifest.roles[i].role]||x.index!==manifest.roles[i].index)
      ||requiredRoles.some(role=>!added.some(x=>x.name===`research134_${role}`)))throw new Error('Research role bindings differ');
  if(!oldExports.some(x=>x.name==='__wbindgen_malloc'&&x.kind===0&&x.index===91940))throw new Error('Original allocator export differs');
  const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module);
  if(imports.length!==878||imports.some(x=>x.kind!=='function'))throw new Error('Host import profile differs');
  return {manifest,async fresh() {
    const hostCalls=[],bindings={};
    for(const item of imports) {bindings[item.module]??={};bindings[item.module][item.name]=()=>{
      hostCalls.push(`${item.module}.${item.name}`);throw new Error('Original host call denied');};}
    const instance=await WebAssembly.instantiate(module,bindings),ex=instance.exports,memory=ex.memory;
    const roles=Object.freeze(Object.fromEntries(requiredRoles.map(role=>[role,ex[`research134_${role}`]])));
    if(!(memory instanceof WebAssembly.Memory)||typeof ex.__wbindgen_malloc!=='function'
       ||Object.values(roles).some(x=>typeof x!=='function'))throw new Error('Runtime role surface differs');
    return {roles,memory,hostCalls,allocate(size,alignment=8) {
      if(!Number.isInteger(size)||size<1||size>1048576||![1,2,4,8,16].includes(alignment))throw new Error('Allocation input outside fixture budget');
      const p=ex.__wbindgen_malloc(size,alignment)>>>0;
      if(!p||p+size>memory.buffer.byteLength||memory.buffer.byteLength>32*1024*1024)throw new Error('Allocation outside memory budget');
      new Uint8Array(memory.buffer,p,size).fill(0);return p;
    }};
  }};
}
