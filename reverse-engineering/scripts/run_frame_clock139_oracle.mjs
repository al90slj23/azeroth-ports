// Original884 contiguous clock-prefix micro-module. Never a full884 call.
import fs from'node:fs/promises';import{createHash}from'node:crypto';import{once}from'node:events';
const[dir,configFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--max-old-space-size=512')||!process.execArgv.includes('--wasm-max-mem-pages=64'))throw Error('Explicit512MiB/4MiB caps');
const cfg=JSON.parse(await fs.readFile(configFile,'utf8')),m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),raw=await fs.readFile(dir+'/'+m.module_file),input=await fs.readFile(cfg.input_file);
if(hash(raw)!==m.module_sha256||hash(input)!==cfg.input_sha256||input.length>1048576||m.source_sha256!=='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'||m.kind!=='original_contiguous_instruction_prefix_micro_module_not_full884')throw Error('Frozenidentity');
const cases=JSON.parse(input);if(!cases.length||cases.length>2048)throw Error('Casebudget');
const mod=await WebAssembly.compile(raw);if(WebAssembly.Module.imports(mod).length)throw Error('Microexpects0imports');
const e=(await WebAssembly.instantiate(mod,{})).exports,b=new Uint8Array(e.memory.buffer),d=new DataView(e.memory.buffer),P=131072;
if(b.length!==2097152||e.stack.value!==1048576)throw Error('Memory/stack');
const hex=(p,n)=>Buffer.from(b.subarray(p,p+n)).toString('hex');
function f64(h){if(!/^[0-9a-f]{16}$/.test(h))throw Error('F64hex');const a=new ArrayBuffer(8),v=new DataView(a);v.setBigUint64(0,BigInt('0x'+h),true);return v.getFloat64(0,true);}
function f32bits(v){const a=new ArrayBuffer(4),w=new DataView(a);w.setFloat32(0,v,true);return w.getUint32(0,true);}
let calls=0,error=null,output=0;const returns=[];
try{for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,initial_previous_hex,initial_tag_hex,label,now_hexes'||!Number.isInteger(c.id)||c.id<0||c.id>=cases.length||!Array.isArray(c.now_hexes)||!c.now_hexes.length||c.now_hexes.length>64)throw Error('Input-onlyschema');
 b.fill(0);for(let i=0;i<64;i++){b[P-64+i]=(i*13+c.id*31+7)&255;b[P+16+i]=(i*17+c.id*29+11)&255;}
 if(!/^[0-9a-f]{16}$/.test(c.initial_tag_hex)||!/^[0-9a-f]{16}$/.test(c.initial_previous_hex))throw Error('Ownerhex');
 d.setBigUint64(P,BigInt('0x'+c.initial_tag_hex),true);d.setBigUint64(P+8,BigInt('0x'+c.initial_previous_hex),true);e.stack.value=1048576;
 const before=hex(P-64,144),lowHash=hash(b.subarray(0,P)),highHash=hash(b.subarray(P+16)),steps=[];
 for(const now of c.now_hexes){const stackBefore=e.stack.value;let returned=false;try{const dt=e.sample(P,f64(now));returned=true;calls++;steps.push({dt_bits:f32bits(dt),owner16_hex:hex(P,16),low64_hex:hex(P-64,64),high64_hex:hex(P+16,64),outside_owner_unchanged:lowHash===hash(b.subarray(0,P))&&highHash===hash(b.subarray(P+16)),stack_before:stackBefore,stack_after:e.stack.value});}finally{returns.push({case:c.id,before:stackBefore,after:e.stack.value,returned});}}
 const line=JSON.stringify({id:c.id,before_owner_and_canaries144_hex:before,steps})+'\n';output+=Buffer.byteLength(line);if(output>16777216)throw Error('Outputbudget');if(!process.stdout.write(line))await once(process.stdout,'drain');
}}catch(x){error=String(x);throw x;}finally{
 await fs.writeFile(dir+'/runtime.json',JSON.stringify({kind:m.kind,micro_prefix_calls:calls,full884_calls:0,original_function_entry_calls:0,imports:0,host_calls:0,instances:1,memory_bytes:b.length,memory_cap_bytes:4194304,heap_cap_mib:512,external_stack_reset:'beforeeachcaseonly;nonebetweenconsecutivesteps',prefix_stack_subtraction_preserved:10704,returns,error},null,2)+'\n');
}
