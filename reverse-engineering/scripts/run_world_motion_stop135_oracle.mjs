// Real immutable snapshot world input, complete17119 including17217/16340.
import fs from 'node:fs/promises';
import {createHash}from'node:crypto';
const hash=x=>createHash('sha256').update(x).digest('hex');
const[directory,inputPath]=process.argv.slice(2),manifest=JSON.parse(await fs.readFile(`${directory}/manifest.json`,'utf8'));
if(manifest.kind!=='snapshot_world_full17119_not_world_constructor'||manifest.original_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||!process.execArgv.includes('--wasm-max-mem-pages=4096'))throw Error('World/source/cap admission');
const changed=await fs.readFile(`${directory}/${manifest.module_file}`),input=await fs.readFile(inputPath);if(hash(changed)!==manifest.module_sha256||input.length>33554432)throw Error('Module/input identity');
const config=JSON.parse(input);if(Object.keys(config).sort().join()!=='cases,expected_world_digest,snapshot_path,snapshot_sha256,world_ranges,world_rc')throw Error('Input-only config');
const snapshot=await fs.readFile(config.snapshot_path);if(snapshot.length%65536||snapshot.length>268435456||hash(snapshot)!==config.snapshot_sha256)throw Error('Snapshot identity/cap');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),surface=WebAssembly.Module.exports(module);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||surface.at(-2).name!=='research_world_motion_stop135_stop'||surface.at(-1).name!=='research_world_motion_stop135_stack0')throw Error('Private surface');
if(!config.cases.length||config.cases.length>128||config.world_ranges.length>10000)throw Error('Case/range budget');
let calls=0,instances=0,guards=0,maxMemory=0,worldDigestBytes=0;
for(const c of config.cases){
 if(Object.keys(c).sort().join()!=='counts,id,now_bits,packet_capacity,prefix,sequence,storage')throw Error('Input-only case');
 if(global.gc)global.gc();const bindings={},hosts=[];for(const x of imports){bindings[x.module]??={};bindings[x.module][x.name]=()=>{hosts.push(x.name);throw Error('Original host denied');};}
 const ex=(await WebAssembly.instantiate(module,bindings)).exports,memory=ex.memory,stack=ex.research_world_motion_stop135_stack0;instances++;
 if(stack.value!==1048576||memory.buffer.byteLength>snapshot.length)throw Error('Fresh globals/memory');
 if(memory.buffer.byteLength<snapshot.length)memory.grow((snapshot.length-memory.buffer.byteLength)/65536);
 new Uint8Array(memory.buffer).set(snapshot);if(hash(new Uint8Array(memory.buffer))!==config.snapshot_sha256)throw Error('Whole snapshot restoration');
 const d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),r=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),hex=(p,n)=>{if(!Number.isInteger(p)||!Number.isInteger(n)||p<0||n<0||p+n>memory.buffer.byteLength)throw Error('Physical capture bounds');return Buffer.from(b().slice(p,p+n)).toString('hex');};
 function call(index,fn,...args){const sp=stack.value;if(sp!==1048576)throw Error('Original stack entry');const value=fn(...args);guards++;if(stack.value!==sp||hosts.length||memory.buffer.byteLength>268435456)throw Error('Original returned stack/host/cap');return value;}
 function alloc(n,fill=0xa5){if(!Number.isInteger(n)||n<0||n>4194304)throw Error('Allocation input');const p=call(91941,ex.__wbindgen_malloc,Math.max(n,8),8)>>>0;if(!p||p+Math.max(n,8)>memory.buffer.byteLength)throw Error('Allocation output');b().fill(fill,p,p+Math.max(n,8));return p;}
 function digestWorld(){const h=createHash('sha256');let total=0;for(const[p,n]of config.world_ranges){if(!Number.isInteger(p)||!Number.isInteger(n)||p<0||n<=0||p+n>memory.buffer.byteLength)throw Error('World range');const header=Buffer.alloc(8);header.writeUInt32LE(p,0);header.writeUInt32LE(n,4);h.update(header);h.update(b().subarray(p,p+n));total+=n;}return{sha256:h.digest('hex'),bytes:total};}
 const G=alloc(8192);w(G+2348,config.world_rc);w(G+2352,c.now_bits);w(G+2412,c.sequence);const vectors={};
 for(const[name,stride,base]of[['units',424,1784],['auxiliary',112,656],['claims',88,2108]]){
  const rows=c.storage[name],count=c.counts[name];if(!Array.isArray(rows)||rows.length>512||count>rows.length||count<0)throw Error('Source vector shape');
  const p=rows.length?alloc(rows.length*stride):4;w(G+base,rows.length);w(G+base+4,p);w(G+base+8,count);
  rows.forEach((value,j)=>{const raw=Buffer.from(value,'hex');if(raw.length!==stride)throw Error('Source stride');b().set(raw,p+j*stride);});vectors[name]={p,stride,capacity:rows.length,base};
 }
 if(c.prefix.length>c.packet_capacity||c.packet_capacity>4096)throw Error('Packet prefix vector');
 const M=c.packet_capacity?alloc(c.packet_capacity*16):4;w(G+1880,c.packet_capacity);w(G+1884,M);w(G+1888,c.prefix.length);
 for(let j=0;j<c.prefix.length;j++){const prefix=c.prefix[j],raw=Buffer.from(prefix.payload_hex,'hex');if(raw.length>prefix.capacity||prefix.capacity>65536)throw Error('Prefix payload');const p=alloc(prefix.capacity);b().set(raw,p);const q=M+j*16;w(q,prefix.capacity);w(q+4,p);w(q+8,raw.length);d().setUint16(q+12,prefix.opcode,true);}
 function queue(){const capacity=r(G+1880),p=r(G+1884),count=r(G+1888);if(count>capacity||capacity>4096)throw Error('Queue bounds');return{capacity,pointer:p,count,active_metadata_hex:hex(p,count*16),packets:Array.from({length:count},(_,j)=>{const q=p+j*16,n=r(q+8);if(n>r(q)||n>65536)throw Error('Packet bound');return{opcode:d().getUint16(q+12,true),capacity:r(q),payload_hex:hex(r(q+4),n)};})};}
 const before={raw_game2592_hex:hex(G,2592),vectors:Object.fromEntries(Object.entries(vectors).map(([name,v])=>[name,{count:r(G+v.base+8),storage:Array.from({length:v.capacity},(_,j)=>hex(v.p+j*v.stride,v.stride))}])),queue:queue(),world:digestWorld()};
 if(before.world.sha256!==config.expected_world_digest)throw Error('Real world input changed before target');
 call(17119,ex.research_world_motion_stop135_stop,G);calls++;
 const after={raw_game2592_hex:hex(G,2592),vectors:Object.fromEntries(Object.entries(vectors).map(([name,v])=>[name,{count:r(G+v.base+8),storage:Array.from({length:v.capacity},(_,j)=>hex(v.p+j*v.stride,v.stride))}])),queue:queue(),world:digestWorld()};
 if(after.world.sha256!==before.world.sha256)throw Error('World consumer mutated source');
 if(after.queue.active_metadata_hex.slice(0,before.queue.count*32)!==before.queue.active_metadata_hex||JSON.stringify(after.queue.packets.slice(0,before.queue.count))!==JSON.stringify(before.queue.packets))throw Error('Prefix changed');
 process.stdout.write(JSON.stringify({id:c.id,full17119:true,before,after,stack_after:stack.value,host_calls:hosts.length,world_rc:r(G+2348),snapshot_bytes:snapshot.length})+'\n');
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);worldDigestBytes+=after.world.bytes;
}
await fs.writeFile(`${directory}/runtime.json`,JSON.stringify({cases:config.cases.length,full17119_calls:calls,fresh_instances:instances,stack_guards:guards,all_stack_returns:true,max_memory_bytes:maxMemory,memory_page_cap:4096,heap_cap_mib:512,actual_host_calls:0,denied_imports:878,world_bytes_hashed_per_side_total:worldDigestBytes,whole_snapshot_sha256:config.snapshot_sha256,snapshot_restored:true,snapshot_is_observed_input:true,fresh_world_constructed:false,original_callees_unchanged:true,externref_table_restored:false,app_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
