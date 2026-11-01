// Full original137 damage913; numeric projection only, no App/EXE/network.
import fs from 'node:fs/promises';import {createHash}from'node:crypto';
const[dir,inputFile]=process.argv.slice(2),hash=x=>createHash('sha256').update(x).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Explicit32MiB cap');
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),raw=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(manifest.original_sha256!=='20ec9a2b5182a72e13ca11668ff0aab17e9dc54a10b923b546708ab85e3fe1c8'||manifest.entry.index!==913||hash(raw)!==manifest.module_sha256||input.length>4194304)throw Error('137 source/input identity');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>512)throw Error('Private budget');
let hostCalls=0,peak=0,calls=0;const stackChecks=[];const number=x=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,x,true);return v.getFloat32(0,true);};
for(const c of cases){
 const bindings={};for(const v of imports){bindings[v.module]??={};bindings[v.module][v.name]=()=>{hostCalls++;throw Error('Original import denied '+v.name);};}
 const instance=await WebAssembly.instantiate(module,bindings),e=instance.exports,memory=e.memory,stack=e.research137_stack0;
 if(!(stack instanceof WebAssembly.Global)||stack.value!==1048576)throw Error('137 initial stack');
 const b=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),w=(p,n)=>d().setUint32(p,n>>>0,true),u=p=>d().getUint32(p,true);
 const guard=(role,fn,...args)=>{const before=stack.value;if(before!==1048576)throw Error('Stack before');let returned=false;
  try{const r=fn(...args);returned=true;return r;}finally{stackChecks.push({id:c.id,role,before,after:stack.value,returned});if(stack.value!==before)throw Error('Stack after');}};
 const alloc=n=>{if(!Number.isInteger(n)||n<1||n>4194304)throw Error('Allocation bound');const p=guard('allocator91933',e.__wbindgen_malloc,n,8)>>>0;
  if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');b().fill(0,p,p+n);return p;};
 const s=c.state,G=alloc(8192),U=alloc(Math.max(1,s.units432_hex.length)*432);
 if(s.units432_hex.length>128||c.operations.length>16||JSON.stringify(s.sources)!==JSON.stringify({items2028:[],spells2052:[],other_procs_absent:true}))throw Error('Explicit quiet source domain');
 const originalDef=Buffer.from(manifest.npc_definition.raw72_hex,'hex');if(!Buffer.from(b().subarray(manifest.npc_definition.pointer,manifest.npc_definition.pointer+72)).equals(originalDef))throw Error('Actual137 declaration bytes');
 s.units432_hex.forEach((row,j)=>{const r=Buffer.from(row,'hex');if(r.length!==432)throw Error('432B units');b().set(r,U+j*432);});
 w(G+1784,s.units432_hex.length);w(G+1788,U);w(G+1792,s.units432_hex.length);w(G+2352,s.now_bits);d().setUint8(G+2587,s.phase2587);
 d().setBigUint64(G+984,BigInt(s.accounted_total_bits),true);s.rng_words.forEach((v,j)=>w(G+1720+j*4,v));
 d().setUint8(G+360,1);d().setUint8(G+361,1);d().setBigUint64(G+1336,999n,true);w(G+1440,0x43fa0000);w(G+1536,0x43fa0000);
 for(const off of[2028,2052,600,648,1660,1884,1896,1812,1824,1836,1848,1860,1872,1908,1920,1968,2112,2124])w(G+off,8);
 const answers=[];
 for(const op of c.operations){
  guard('damage913',e.research137_damage913,G,BigInt(op.target_id),number(op.amount_bits),op.spell_id,op.school,op.critical,op.context);calls++;
  if(hostCalls||memory.buffer.byteLength>33554432)throw Error('Quiet original boundary');
  answers.push({units432_hex:s.units432_hex.map((_,j)=>Buffer.from(b().subarray(U+j*432,U+(j+1)*432)).toString('hex')),
   accounted_total_bits:d().getBigUint64(G+984,true).toString(),rng_words:[0,1,2,3].map(j=>u(G+1720+j*4))});
 }
 peak=Math.max(peak,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:c.id,answers})+'\n');
}
const runtime={version:'0.137.0',build:'d171b8f9f',cases:cases.length,full_original913_calls:calls,fresh_instances:cases.length,actual_host_calls:hostCalls,
 denied_imports:878,peak_memory_bytes:peak,stack_checks:stackChecks,stack_all_restored:stackChecks.every(x=>x.returned&&x.before===1048576&&x.after===x.before),
 application_start_called:false,windows_exe_executed:false,network_used:false,user_saves_accessed:false,original_full_callees_preserved:true,shared52_roles_changed:false};
await fs.writeFile(dir+'/runtime.json',JSON.stringify(runtime)+'\n');
