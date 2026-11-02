// Intact currentWASM25511, only added exports; no original mainloop/App calls.
import fs from'node:fs/promises';import{createHash}from'node:crypto';
const[dir,configFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--max-old-space-size=512')||!process.execArgv.includes('--wasm-max-mem-pages=1024'))throw Error('Explicit heap/memory caps');
const cfg=JSON.parse(await fs.readFile(configFile,'utf8')),m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),raw=await fs.readFile(dir+'/'+m.wasm_module_file),input=await fs.readFile(cfg.input_file);
if(hash(raw)!==m.wasm_module_sha256||hash(input)!==cfg.input_sha256||input.length>1048576||m.wasm_sha256!=='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299')throw Error('Identity/input budget');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module),bindings={};let host=0;
if(imports.length!==882||imports.some(v=>v.kind!=='function')||JSON.stringify(imports.map(({module,name})=>({module,name})))!==JSON.stringify(m.wasm_original_imports.map(({module,name})=>({module,name}))))throw Error('882 imports');
for(const v of imports){bindings[v.module]??={};bindings[v.module][v.name]=()=>{host++;throw Error('Deniedhost '+v.name);};}
const e=(await WebAssembly.instantiate(module,bindings)).exports,mem=e.memory,SP=e.research139_upgrade_stack,STATE=0x1000100,PAGE=STATE&~4095,fields=[32,16,20,24,28];
if(mem.buffer.byteLength>33554432||SP.value!==1048576)throw Error('Memory/SP');mem.grow((33554432-mem.buffer.byteLength)/65536);const b=new Uint8Array(mem.buffer),d=new DataView(mem.buffer),hex=(p,n)=>Buffer.from(b.subarray(p,p+n)).toString('hex');
for(const def of m.definitions)if(hex(def.wasm_va,88)!==def.wasm88_hex)throw Error('Original definition changed');
for(let k=0;k<5;k++)for(let j=0;j<5;j++)if(d.getUint32(m.wasm_tables[k]+4*j,true)!==m.tables[k][j])throw Error('Original table changed');
const outsideHash=hash(Buffer.concat([b.subarray(0,PAGE),b.subarray(PAGE+4096)])),cases=JSON.parse(input),f32bits=v=>{const z=new ArrayBuffer(4),w=new DataView(z);w.setFloat32(0,v,true);return w.getUint32(0,true);};let calls=0,error=null;const returns=[];
try{for(const c of cases){
 if(Object.keys(c).sort().join()!=='definition_index,id,input_word,kind,label,tier'||!Number.isInteger(c.kind)||c.kind<0||c.kind>4||!Number.isInteger(c.tier)||c.tier<0||c.tier>4||!Number.isInteger(c.definition_index)||c.definition_index<0||c.definition_index>=114||!Number.isInteger(c.input_word)||c.input_word<0||c.input_word>0xffffffff||c.id!==calls)throw Error('Typed bounded inputs');
 b.fill(0xa5,PAGE,PAGE+4096);for(let j=0;j<64;j++){b[STATE-64+j]=(j*13+c.id*7+3)&255;b[STATE+80+j]=(j*17+c.id*11+9)&255;}
 d.setUint32(STATE+fields[c.kind],c.input_word,true);if(c.kind===2)d.setUint32(STATE,m.definitions[c.definition_index].wasm_va,true);const before=hex(PAGE,4096);if(SP.value!==1048576)throw Error('SP before');
 let returned=false;try{const value=e.research139_upgrade25511(STATE,c.kind,c.tier);returned=true;calls++;if(before!==hex(PAGE,4096)||SP.value!==1048576)throw Error('Pure function mutated fixture/SP');process.stdout.write(JSON.stringify({id:c.id,result_bits:f32bits(value),owner_page_unchanged:true,stack_before:1048576,stack_after:SP.value})+'\n');}finally{returns.push({case:c.id,returned,stack:SP.value});}
}}catch(x){error=String(x);throw x;}finally{
 const unchanged=outsideHash===hash(Buffer.concat([b.subarray(0,PAGE),b.subarray(PAGE+4096)]));await fs.writeFile(dir+'/wasm-runtime.json',JSON.stringify({kind:'intact_current139_fullWASM25511_export_only',full25511_calls:calls,fresh_instances:1,imports_denied:882,actual_host_calls:host,memory_bytes:mem.buffer.byteLength,memory_cap_bytes:67108864,heap_cap_mib:512,owner_page_each_call_unchanged:true,outside_owner_page_batch_hash_unchanged:unchanged,returns,full_mainloop_calls:0,Windows_application_executions:0,error},null,2)+'\n');if(!unchanged)throw Error('Outside owner-page mutation');
}
