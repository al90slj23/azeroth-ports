// Complete38553 on actual1600 owners. Only declared scheduled32 inputs patched.
import fs from'node:fs/promises';
import{createHash}from'node:crypto';
const[dir,cfgPath]=process.argv.slice(2),hash=x=>createHash('sha256').update(x).digest('hex');
const cfg=JSON.parse(await fs.readFile(cfgPath,'utf8')),m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
const raw=await fs.readFile(dir+'/'+m.module_file),input=await fs.readFile(cfg.input_file);
if(hash(raw)!==m.module_sha256||hash(input)!==cfg.input_sha256||m.source_sha256!=='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'||input.length>4194304)throw Error('Frozen identities');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('Memory budgets');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==882||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>128)throw Error('Import/case budget');
if(JSON.stringify(imports.map(({module,name})=>({module,name})))!==JSON.stringify(m.original_imports.map(({module,name})=>({module,name}))))throw Error('Import identity');
let host=0,instances=0,ctor=0,ticks=0,peak=0,error=null;const returns=[];
try{for(const c of cases){
 if(Object.keys(c).sort().join()!=='count,id,phase,storage32_hex,updates'||c.id!==instances||!Number.isInteger(c.count)||c.count<0||c.count>c.storage32_hex.length||c.storage32_hex.length>512||!Array.isArray(c.updates)||!c.updates.length||c.updates.length>32||![0,1,5].includes(c.phase))throw Error('Input schema');
 if(global.gc)global.gc();const bindings={};for(const x of imports){bindings[x.module]??={};bindings[x.module][x.name]=()=>{host++;throw Error('Deniedhost '+x.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,mem=e.memory,sp=e.research139_deadline_stack;instances++;
 const b=()=>new Uint8Array(mem.buffer),d=()=>new DataView(mem.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),hex=(p,n)=>Buffer.from(b().subarray(p,p+n)).toString('hex');
 function call(role,fn,...a){if(sp.value!==1048576)throw Error('SPbefore');let returned=false;try{const z=fn(...a);returned=true;return z;}finally{returns.push({case:c.id,role,before:1048576,after:sp.value,returned});if(sp.value!==1048576||mem.buffer.byteLength>33554432)throw Error('SP/memoryafter');}}
 function alloc(n){const p=call('malloc',e.__wbindgen_malloc,Math.max(1,n),8)>>>0;if(!p||p+n>mem.buffer.byteLength)throw Error('Allocation');return p;}
 const G=alloc(8192),P=alloc(376),V=alloc(128),N=alloc(6);b().fill(0xa5,G,G+8192);b().fill(0,P,P+376);b().fill(0x5a,V,V+128);b().set(Buffer.from('elwynn'),N);
 w(P+156,4);w(P+168,N);w(P+172,6);d().setBigUint64(P+176,0n,true);d().setBigUint64(P+184,1n,true);b()[P+344]=b()[P+345]=1;b()[V+120]=1;w(V+116,0);w(V+56,0xffffffff);w(V+32,0xffffffff);
 const profile=hex(P,376),view=hex(V,128);call('1600',e.research139_deadline_ctor,G,P,V);ctor++;
 if(u(G+1832)||u(G+1840)||u(G+1888))throw Error('Actual constructor source expected empty');
 const cap=c.storage32_hex.length,q=cap?alloc(cap*32):u(G+1836);
 if(cap){w(G+1832,cap);w(G+1836,q);for(let j=0;j<cap;j++){const s=c.storage32_hex[j];if(typeof s!=='string'||!/^[0-9a-f]{64}$/.test(s))throw Error('Record32');b().set(Buffer.from(s,'hex'),q+j*32);}}
 w(G+1840,c.count);b()[G+2587]=c.phase;
 function packets(){const n=u(G+1888),p=u(G+1884);if(n>1024||n>u(G+1880))throw Error('Packetcount');return Array.from({length:n},(_,i)=>{const r=p+16*i,k=u(r+8),a=u(r+4);if(k>u(r)||k>128||a+k>mem.buffer.byteLength)throw Error('Payload');return{opcode:d().getUint16(r+12,true),capacity:u(r),payload_hex:hex(a,k)};});}
 function capture(){return{raw_game2592_hex:hex(G,2592),count:u(G+1840),capacity:u(G+1832),storage:Array.from({length:cap},(_,j)=>hex(q+j*32,32)),packet_capacity:u(G+1880),packet_count:u(G+1888),packet_pointer:u(G+1884),packets:packets()};}
 const before=capture(),stages=[];
 for(const now of c.updates){if(!Number.isInteger(now)||now<0||now>0xffffffff)throw Error('Now32');w(G+2352,now);const inputGame=hex(G,2592);call('38553',e.research139_deadline_tick,G);ticks++;stages.push({now_bits:now,input_game2592_hex:inputGame,...capture()});}
 if(profile!==hex(P,376)||view!==hex(V,128)||host)throw Error('Borrowed input/host mutation');peak=Math.max(peak,mem.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,before,stages,profile_before_hex:profile,profile_after_hex:hex(P,376),query_before_hex:view,query_after_hex:hex(V,128),stack_after:sp.value})+'\n');
}}catch(x){error=String(x);throw x;}finally{
 await fs.writeFile(dir+'/runtime.json',JSON.stringify({version:'0.139.0',build:'f79c5e2b4',fresh_instances:instances,setup1600_calls:ctor,full38553_calls:ticks,returns,actual_host_calls:host,denied_imports:882,peak_memory_bytes:peak,memory_cap_bytes:33554432,snapshot_restores:0,only_export_section_changed:true,source_queue_fixtures:true,App_bootstrap:false,full_mainloop_frames:0,native_windows_execution:false,complete_games:0,error},null,2)+'\n');
}
