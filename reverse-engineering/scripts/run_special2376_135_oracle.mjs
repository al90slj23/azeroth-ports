// Private complete2376; all878 original hosts denied, no shared host or App.
import fs from 'node:fs/promises';import{createHash}from'node:crypto';
const[dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Explicit32MiB cap');
const m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),raw=await fs.readFile(dir+'/'+m.module_file),input=await fs.readFile(inputFile);
if(hash(raw)!==m.module_sha256||m.entry.index!==2376||m.entry.body_sha256!=='6b985b23a141a82085f021e7bedf0247ea2a61a99bda05cf820e38a369be29ff'||input.length>4194304)throw Error('Original/input identity/budget');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(v=>v.kind!=='function')||!cases.length||cases.length>512)throw Error('Bounded878 import-only corpus');
let hostCalls=0,calls=0,peak=0,packetCount=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input'||c.id!==calls)throw Error('Input-only case shape/order');
 const bindings={};for(const v of imports){bindings[v.module]??={};bindings[v.module][v.name]=()=>{hostCalls++;throw Error('Denied original host '+v.name);};}
 const instance=await WebAssembly.instantiate(module,bindings),e=instance.exports,memory=e.memory;
 const b=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v>>>0,true);
 const hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 function alloc(n,alignment=4){if(n<1||n>4194304)throw Error('Single allocation budget');const p=e.__wbindgen_malloc(n,alignment)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Allocator bounds');b().fill(0xa5,p,p+n);return p;}
 const s=c.input,G=alloc(2592,8),Q=alloc(Math.max(1,s.storage.length)*40,8),M=alloc(8*16,4),g=(o,v)=>w(G+o,v);
 if(s.storage.length>512||s.count>s.storage.length)throw Error('special40 prefix budget');
 s.storage.forEach((raw,j)=>{if(raw.length!==80)throw Error('Exact40 bytes');b().set(Buffer.from(raw,'hex'),Q+j*40);});
 for(const[o,v]of[[2352,s.now_bits],[1416,s.player_xy_bits[0]],[1420,s.player_xy_bits[1]],[392,s.selected392],[396,s.target396],[2392,s.announcement_time2392_bits]])g(o,v);
 for(const[o,v]of[[2576,s.protection2576],[2564,s.navigation2564],[2565,s.announced2565]])d().setUint8(G+o,v);
 g(1916,s.storage.length);g(1920,Q);g(1924,s.count);g(1880,8);g(1884,M);g(1888,0);
 const before=b().slice(G,G+2592),stackBefore=e.research_special2376_stack.value;
 e.special2376_135_tick(G);calls++;
 const stackAfter=e.research_special2376_stack.value;if(stackBefore!==stackAfter)throw Error('Original stack not restored');
 const changes=[];for(let j=0;j<2592;j++)if(before[j]!==b()[G+j])changes.push([j,b()[G+j]]);
 const count=u(G+1888),packets=[];if(count>8||u(G+1884)!==M||u(G+1880)!==8)throw Error('Packet capacity unexpected');
 for(let j=0;j<count;j++){const p=M+j*16,capacity=u(p),ptr=u(p+4),len=u(p+8);if(len>capacity||capacity>4096||ptr+len>memory.buffer.byteLength)throw Error('Payload budget');packets.push([d().getUint16(p+12,true),capacity,hex(ptr,len)]);packetCount++;}
 const answer={storage:s.storage.map((_,j)=>hex(Q+j*40,40)),count:u(G+1924),selected392:u(G+392),target396:u(G+396),announced2565:d().getUint8(G+2565),announcement_time2392_bits:u(G+2392),packets,game_changes:changes};
 if(u(G+1916)!==s.storage.length||u(G+1920)!==Q)throw Error('Original special backing moved');
 if(hostCalls||memory.buffer.byteLength>33554432)throw Error('Host/memory boundary');peak=Math.max(peak,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,answer,stack_before:stackBefore,stack_after:stackAfter})+'\n');
}
await fs.writeFile(dir+'/special2376_135-runtime.json',JSON.stringify({cases:cases.length,calls,full_original_entry2376:calls,actual_host_calls:hostCalls,denied_imports:878,fresh_instances:cases.length,peak_memory_bytes:peak,packets:packetCount,memory_page_cap:512,original_application_start:false,shared52_roles_changed:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
