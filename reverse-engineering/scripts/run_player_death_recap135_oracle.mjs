// Full fresh1367 on an explicit borrowed history48 ring; all host imports denied.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const[dir,configPath]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('Explicit32MiB/512MiB caps');
const config=JSON.parse(await fs.readFile(configPath,'utf8')),manifest=JSON.parse(await fs.readFile(`${dir}/manifest.json`,'utf8'));
const raw=await fs.readFile(`${dir}/${manifest.module_file}`),inputRaw=await fs.readFile(config.input_path);
if(hash(raw)!==manifest.module_sha256||hash(inputRaw)!==config.input_sha256||manifest.entry.index!==1367||inputRaw.length>4194304)throw Error('Frozen identity/budget');
const mod=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(mod),cases=JSON.parse(inputRaw);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>256)throw Error('Host/case budget');
let done=0,hosts=0,maximum=0,stackChecks=0,error=null;
try{for(const c of cases){
 if(Object.keys(c).sort().join()!=='history,id,reference_time_bits'||c.id!==done)throw Error('Input-only keys');
 if(global.gc)global.gc();const bindings={},hostCalls=[];for(const m of imports){bindings[m.module]??={};bindings[m.module][m.name]=()=>{hosts++;hostCalls.push(m.name);throw Error('878 imports denied');};}
 const ex=(await WebAssembly.instantiate(mod,bindings)).exports,memory=ex.memory,stack=ex.research135_death_recap_stack0;
 const d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 const alloc=(n,align=4)=>{if(stack.value!==1048576)throw Error('Allocation stack');const p=ex.__wbindgen_malloc(n,align)>>>0;stackChecks++;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432||stack.value!==1048576)throw Error('Allocation budget');return p;};
 const h=c.history;if(h.capacity>512||h.rows48_hex.length!==h.capacity||h.strings.length!==h.capacity||h.count>h.capacity||h.head>=(h.capacity||1))throw Error('Ring shape');
 const H=alloc(16),P=alloc(Math.max(1,h.capacity*48),8),O=alloc(12);b().fill(0x5a,O,O+12);
 w(H,h.capacity);w(H+4,P);w(H+8,h.head);w(H+12,h.count);const strings=[];
 for(let i=0;i<h.capacity;i++){
  const row=Buffer.from(h.rows48_hex[i],'hex');if(row.length!==48)throw Error('Stride');b().set(row,P+i*48);
  if(h.strings[i]===null)continue;
  if(h.strings[i].length!==3)throw Error('Three resolved UTF8 slices');
  for(let j=0;j<3;j++){const bytes=Buffer.from(h.strings[i][j],'utf8');if(bytes.length>4096||u(P+i*48+j*8+4)!==bytes.length)throw Error('UTF8 length');const at=alloc(Math.max(1,bytes.length),1);b().set(bytes,at);w(P+i*48+j*8,at);strings.push({pointer:at,bytes:bytes.length,before:hex(at,bytes.length)});}
 }
 const headerBefore=hex(H,16),rowsBefore=hex(P,h.capacity*48),time=new DataView(new ArrayBuffer(4));time.setUint32(0,c.reference_time_bits,true);
 ex.research135_death_recap1367(O,H,time.getFloat32(0,true));stackChecks++;
 if(stack.value!==1048576||hostCalls.length||headerBefore!==hex(H,16)||rowsBefore!==hex(P,h.capacity*48)||strings.some(x=>x.before!==hex(x.pointer,x.bytes)))throw Error('Read-only input/stack/host');
 const capacity=u(O),pointer=u(O+4),length=u(O+8);if(length>capacity||capacity>1048576||pointer+capacity>memory.buffer.byteLength)throw Error('Output budget');
 process.stdout.write(JSON.stringify({id:c.id,capacity,length,raw_hex:hex(pointer,length),output_backing_hex:hex(pointer,capacity),history_header_before_hex:headerBefore,history_header_after_hex:hex(H,16),history_storage_before_hex:rowsBefore,history_storage_after_hex:hex(P,h.capacity*48),strings_unchanged:strings.length,stack_after:stack.value,host_calls:0,full_original_function:1367,memory_bytes:memory.buffer.byteLength})+'\n');done++;maximum=Math.max(maximum,memory.buffer.byteLength);
}}catch(e){error=String(e);throw e;}finally{await fs.writeFile(`${dir}/runtime.json`,JSON.stringify({version:'0.135.1',actual_build:'90898d5e3',cases:cases.length,completed_cases:done,full1367_calls:done,fresh_instances:done,host_calls:hosts,denied_imports:878,max_memory_bytes:maximum,memory_cap_bytes:33554432,stack_checks:stackChecks,old_snapshot_loaded:false,App_or_Game_constructed:false,history_producer_executed:false,explicit_borrowed_history_input:true,original_bodies_modified:false,user_saves_accessed:false,network_used:false,error},null,2)+'\n');}
