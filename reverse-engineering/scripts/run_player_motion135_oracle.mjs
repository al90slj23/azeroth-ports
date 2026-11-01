// Full original2328 on the genuine after_begin snapshot; no application boot.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const hash=x=>createHash('sha256').update(x).digest('hex');
const [directory,configPath]=process.argv.slice(2),config=JSON.parse(await fs.readFile(configPath,'utf8'));
if(!process.execArgv.includes('--wasm-max-mem-pages=4096'))throw Error('Explicit256MiB cap required');
const manifest=JSON.parse(await fs.readFile(`${directory}/manifest.json`,'utf8'));
if(manifest.kind!=='player-motion135-snapshot-consumer-not-freshGame'||manifest.original_wasm_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2')throw Error('Original identity');
const moduleRaw=await fs.readFile(`${directory}/${manifest.module_file}`),inputRaw=await fs.readFile(config.input_path),snapshot=await fs.readFile(config.snapshot_path);
if(hash(moduleRaw)!==manifest.module_sha256||hash(inputRaw)!==config.input_sha256||hash(snapshot)!==config.snapshot_sha256||snapshot.length>256*1024*1024||snapshot.length%65536)throw Error('Frozen bytes/budget');
const module=await WebAssembly.compile(moduleRaw),imports=WebAssembly.Module.imports(module);
if(imports.length!==878||imports.some(x=>x.kind!=='function'))throw Error('Host surface');
const cases=JSON.parse(inputRaw);if(!cases.length||cases.length>128)throw Error('Bounded case count');
let maxMemory=0,hostCount=0,originalCalls=0;
const allowedPatches=new Set([416,420,424,428,432,436,440,444,448,452,456,460,1644,1744,1748,1752,1756,1760,1764,1768,1772,1776,1780,2352,2496,2500]);
for(const c of cases){
 if(Object.keys(c).sort().join()!=='facing_bits,id,patch_words,xyz_bits')throw Error('Input-only keyset');
 const bindings={},hostCalls=[];
 for(const m of imports){bindings[m.module]??={};bindings[m.module][m.name]=()=>{hostCalls.push(`${m.module}.${m.name}`);throw Error('All original host imports denied');};}
 const ex=(await WebAssembly.instantiate(module,bindings)).exports,memory=ex.memory,stack=ex.research_player_motion135_stack;
 if(!(memory instanceof WebAssembly.Memory)||!(stack instanceof WebAssembly.Global)||stack.value!==1048576||memory.buffer.byteLength>snapshot.length)throw Error('Mutable global/fresh memory');
 const initialMemory=memory.buffer.byteLength;if(memory.buffer.byteLength<snapshot.length)memory.grow((snapshot.length-memory.buffer.byteLength)/65536);
 new Uint8Array(memory.buffer).set(snapshot);if(hash(new Uint8Array(memory.buffer))!==config.snapshot_sha256)throw Error('Full snapshot restoration');
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true);
 const G=config.game_pointer,R=u(G+2348);
 if(R!==config.world_pointer||bytes()[G+2587]!==1||u(G+464)!==0)throw Error('Real Game/world/phase boundary');
 const allocate=(n,align=4)=>{const p=ex.__wbindgen_malloc(n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>256*1024*1024||stack.value!==1048576)throw Error('Owned allocator boundary');return p;};
 const P=allocate(12);c.xyz_bits.forEach((v,j)=>w(P+4*j,v));
 for(const [offset,value] of c.patch_words){if(!allowedPatches.has(offset)||!Number.isInteger(value)||value<0||value>0xffffffff)throw Error('Declared scalar domain');w(G+offset,value);}
 const before=Buffer.from(bytes().slice(G,G+8192)),worldBefore=Buffer.from(bytes().slice(R,R+124));
 const geometryHashes=config.world_ranges.map(([p,n])=>hash(bytes().subarray(p,p+n)));
 function queue(){const cap=u(G+1880),ptr=u(G+1884),count=u(G+1888);if(count>cap||cap>4096)throw Error('Queue count/capacity');return{cap,ptr,count,rows:Array.from({length:count},(_,j)=>{const p=ptr+j*16,n=u(p+8),capacity=u(p);if(n>capacity||capacity>1048576)throw Error('Payload count');return[ d().getUint16(p+12,true),Buffer.from(bytes().subarray(u(p+4),u(p+4)+n)).toString('hex') ];})};}
 const prefix=queue(),inputView=new DataView(new ArrayBuffer(4));inputView.setUint32(0,c.facing_bits,true);
 const ret=ex.research_player_motion135_move_player(G,P,inputView.getFloat32(0,true));originalCalls++;
 const after=Buffer.from(bytes().slice(G,G+8192)),final=queue();
 if(stack.value!==1048576||hostCalls.length||!Buffer.from(bytes().slice(R,R+124)).equals(worldBefore))throw Error('Original stack/host/world record mutation');
 if(config.world_ranges.some(([p,n],j)=>hash(bytes().subarray(p,p+n))!==geometryHashes[j]))throw Error('Original geometry backing mutated');
 if(JSON.stringify(final.rows.slice(0,prefix.count))!==JSON.stringify(prefix.rows))throw Error('Existing packet prefix mutated');
 const changed=[];for(let i=0;i<8192;i++)if(before[i]!==after[i])changed.push(i);
 process.stdout.write(JSON.stringify({id:c.id,return_value:ret,game_before_hex:before.toString('hex'),game_after_hex:after.toString('hex'),changed_bytes:changed,
  packets:final.rows.slice(prefix.count),queue_before:{capacity:prefix.cap,pointer:prefix.ptr,count:prefix.count},queue_after:{capacity:final.cap,pointer:final.ptr,count:final.count},
  world_before_hex:worldBefore.toString('hex'),world_after_hex:Buffer.from(bytes().slice(R,R+124)).toString('hex'),geometry_ranges_unchanged:config.world_ranges.length,
  stack_after:stack.value,host_calls:hostCalls.length,snapshot:{sha256:config.snapshot_sha256,bytes:snapshot.length,initial_memory_bytes:initialMemory,restored_memory_bytes:memory.buffer.byteLength},full_original_function:2328})+'\n');
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);hostCount+=hostCalls.length;
}
await fs.writeFile(`${directory}/runtime.json`,JSON.stringify({cases:cases.length,original_calls:originalCalls,original_function:2328,host_calls:hostCount,
 denied_imports:878,memory_page_cap:4096,max_memory_bytes:maxMemory,snapshot_restored:true,freshGame:false,worldRc_forged:false,
 original_body_modified:false,app_entry_called:false,user_saves_accessed:false,network_used:false,node:process.version},null,2)+'\n');
