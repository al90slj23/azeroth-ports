// Full968 opcode199 ACK on an inlineGame; typed partialApp component only.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const hash=x=>createHash('sha256').update(x).digest('hex');
const[directory,configPath,phase]=process.argv.slice(2),config=JSON.parse(await fs.readFile(configPath,'utf8'));
if(!['setup','cases'].includes(phase)||!process.execArgv.includes('--wasm-max-mem-pages=4096'))throw Error('Phase/256MiB cap');
const manifest=JSON.parse(await fs.readFile(`${directory}/manifest.json`,'utf8'));
if(manifest.kind!=='full968-default-localroute-typed-partialApp-component'||manifest.original_wasm_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2')throw Error('Source identity');
const raw=await fs.readFile(`${directory}/${manifest.module_file}`),snapshot=await fs.readFile(config.snapshot_path);
if(hash(raw)!==manifest.module_sha256||hash(snapshot)!==config.snapshot_sha256||snapshot.length>256*1024*1024||snapshot.length%65536)throw Error('Artifact identity/budget');
const mod=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(mod);
if(imports.length!==878||imports.some(x=>x.kind!=='function'))throw Error('Host surface');
let context=null;
if(phase==='cases'){const contextRaw=await fs.readFile(`${directory}/setup-context.json`);if(hash(contextRaw)!==config.context_sha256)throw Error('Frozen setup context');context=JSON.parse(contextRaw);}
let cases=[null];if(phase==='cases'){const bytes=await fs.readFile(config.input_path);if(hash(bytes)!==config.input_sha256)throw Error('Input identity');cases=JSON.parse(bytes);if(!cases.length||cases.length>128)throw Error('Case budget');}
let maxMemory=0,targetCalls=0,setup6730=0,setup1089=0;
for(const c of cases){
 if(c&&Object.keys(c).sort().join()!=='id,opcode,patch_words,payload_hex')throw Error('Input-only keys');
 const bindings={},hostCalls=[];for(const m of imports){bindings[m.module]??={};bindings[m.module][m.name]=()=>{hostCalls.push(m.name);throw Error('878 original imports denied');};}
 const ex=(await WebAssembly.instantiate(mod,bindings)).exports,memory=ex.memory,stack=ex.research_player_motion135_stack;
 if(stack.value!==1048576||memory.buffer.byteLength>snapshot.length)throw Error('Original mutable globals/memory');
 if(memory.buffer.byteLength<snapshot.length)memory.grow((snapshot.length-memory.buffer.byteLength)/65536);
 new Uint8Array(memory.buffer).set(snapshot);if(hash(new Uint8Array(memory.buffer))!==config.snapshot_sha256)throw Error('Snapshot restoration');
 const d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 const App=config.app_pointer,G=App+16,R=u(App+5116),oldRef=u(R),appOriginal=hex(App,5168);
 if(R!==config.world_pointer)throw Error('Genuine cached world owner');
 // Exactly4253 known empty tags; no A5 byte is promoted to a valid App field.
 d().setBigUint64(App+16,2n,true);d().setBigUint64(App+2608,2n,true);
 ex.research_player_dispatch135_cached_construct(G,App);setup6730++;
 if(d().getBigUint64(G,true)===2n||u(G+2348)!==R||u(R)!==oldRef+1||stack.value!==1048576)throw Error('Full6730 inlineGame/owner');
 ex.research_player_dispatch135_begin_run(G);setup1089++;
 if(b()[G+2587]!==1||b()[G+2582]!==0||d().getBigUint64(App+2608,true)!==2n||u(G+2348)!==R||stack.value!==1048576)throw Error('Full1089/default route');
 const P=ex.__wbindgen_malloc(24,4)>>>0;if(!P||P+24>memory.buffer.byteLength||stack.value!==1048576)throw Error('Owned payload allocation');
 const setup={kind:'original-setup-observation-explicit-input-not-independent-constructor',App,G,world_pointer:R,old_world_refcount:oldRef,world_refcount:u(R),
  game2592_hex:hex(G,2592),app5168_hex:hex(App,5168),app_original5168_hex:appOriginal,world124_hex:hex(R,124),
  full_setup_functions:[6730,1089],setup_target968_calls:0,original_host_calls:hostCalls.length,stack:stack.value,
  declared_app_tags:{inline_game_pre6730:'2',network2608:'2'},completeApp_producer:false,worldRc_forged:false,externref_forged:false};
 if(hostCalls.length)throw Error('Setup host attempted');
 if(phase==='setup'){await fs.writeFile(`${directory}/setup-context.json`,JSON.stringify(setup,null,2)+'\n');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);continue;}
 if(JSON.stringify(setup)!==JSON.stringify(context))throw Error('Full6730/1089 setup not identical to frozen pre968 observation');
 const allowed=new Set([416,420,424,428,432,436,448,452,456,460,1644,1744,1748,1752,1756,1760,1764,1768,1772,1776,1780,2352]);
 for(const[o,v]of c.patch_words){if(!allowed.has(o))throw Error('Patch scope');w(G+o,v);}
 const payload=Buffer.from(c.payload_hex,'hex');if(payload.length<5||payload.length>13||c.opcode!==199)throw Error('Canonical packedGUID+u32ACK');b().set(payload,P);
 const appBefore=hex(App,5168),gameBefore=hex(G,2592),worldBefore=hex(R,124),arrayHashes=config.world_ranges.map(([p,n])=>hash(b().subarray(p,p+n)));
 function queue(){const capacity=u(G+1880),pointer=u(G+1884),count=u(G+1888);if(count>capacity||capacity>4096)throw Error('Queue budget');return{capacity,pointer,count,rows:Array.from({length:count},(_,j)=>{const p=pointer+j*16,n=u(p+8);if(n>u(p)||n>1048576)throw Error('Packet budget');return[d().getUint16(p+12,true),hex(u(p+4),n)];})};}
 const prefix=queue();ex.research_player_motion135_motion_dispatch(App,0,0,c.opcode,P,payload.length);targetCalls++;
 const final=queue();if(hostCalls.length||stack.value!==1048576||worldBefore!==hex(R,124)||config.world_ranges.some(([p,n],j)=>hash(b().subarray(p,p+n))!==arrayHashes[j]))throw Error('Target stack/host/world mutation');
 if(JSON.stringify(prefix.rows)!==JSON.stringify(final.rows.slice(0,prefix.count))||prefix.pointer!==final.pointer||prefix.capacity!==final.capacity)throw Error('Queue prefix/owner mutation');
 process.stdout.write(JSON.stringify({id:c.id,game_before_hex:gameBefore,game_after_hex:hex(G,2592),app_before_hex:appBefore,app_after_hex:hex(App,5168),packets:final.rows.slice(prefix.count),
  queue_before:{capacity:prefix.capacity,pointer:prefix.pointer,count:prefix.count},queue_after:{capacity:final.capacity,pointer:final.pointer,count:final.count},world_before_hex:worldBefore,world_after_hex:hex(R,124),
  stack_after:stack.value,host_calls:0,full_target_function:968,setup_functions:[6730,1089],same_inline_G:G,route:[0,0],partialApp_fixture:true})+'\n');
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/${phase}-runtime.json`,JSON.stringify({phase,cases:cases.length,full6730_calls:setup6730,full1089_calls:setup1089,full968_calls:targetCalls,host_calls:0,denied_imports:878,
 memory_page_cap:4096,max_memory_bytes:maxMemory,snapshot_restored:true,original_bodies_modified:false,worldRc_forged:false,externref_forged:false,completeApp_producer:false,natural1371Game_install:false,
 target_opcode:199,mode2582:0,owner_route:0,peer:0,default_network_tag2608:2,app_entry_called:false,user_saves_accessed:false,network_used:false},null,2)+'\n');
