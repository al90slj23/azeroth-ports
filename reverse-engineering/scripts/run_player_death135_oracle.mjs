// Original1560 setup, complete5620 or1073. Inputs never carry expected output.
import fs from 'node:fs/promises';
import {createHash}from'node:crypto';
const hash=x=>createHash('sha256').update(x).digest('hex');
const[directory,inputPath]=process.argv.slice(2),manifest=JSON.parse(await fs.readFile(`${directory}/manifest.json`,'utf8'));
if(manifest.original_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Fixed source/memory cap');
const raw=await fs.readFile(`${directory}/${manifest.module_file}`);if(hash(raw)!==manifest.module_sha256)throw Error('Module SHA');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module);if(imports.length!==878||imports.some(x=>x.kind!=='function'))throw Error('878 imported functions only');
const input=await fs.readFile(inputPath);if(input.length>33554432)throw Error('Input budget');const cases=JSON.parse(input);if(!cases.length||cases.length>256)throw Error('Case budget');
let calls5620=0,calls1073=0,constructors=0,guards=0,maxMemory=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!=='amount_bits,hero,id,kind,left,model_state,source_guid,starting_hp_bits,taken_before_bits')throw Error('Input-only keys');
 const bindings={},hosts=[];for(const x of imports){bindings[x.module]??={};bindings[x.module][x.name]=()=>{hosts.push(x.name);throw Error('Host denied');};}
 const ex=(await WebAssembly.instantiate(module,bindings)).exports,memory=ex.memory,stack=ex.research_death135_stack0;
 const d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),r=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 function call(fn,...args){const sp=stack.value;if(sp!==1048576)throw Error('Stack entry');const v=fn(...args);guards++;if(stack.value!==sp||memory.buffer.byteLength>33554432||hosts.length)throw Error('Stack/host/cap');return v;}
 function alloc(n){const p=call(ex.__wbindgen_malloc,Math.max(n,8),8)>>>0;if(!p||p+Math.max(n,8)>memory.buffer.byteLength)throw Error('Allocation');b().fill(0,p,p+Math.max(n,8));return p;}
 const s=c.model_state,G=alloc(8192),P=alloc(376),V=alloc(128),name=Buffer.from('elwynn'),N=alloc(name.length);b().set(name,N);
 w(P+156,4);w(P+168,N);w(P+172,name.length);d().setBigUint64(P+176,BigInt(s.source_id),true);d().setBigUint64(P+184,1n,true);b()[P+344]=s.class_byte;b()[P+345]=s.race_byte;
 b()[V+120]=Number(s.flat_height_enabled);w(V+116,s.flat_height_bits);w(V+56,0xffffffff);w(V+32,0xffffffff);call(ex.research_death135_constructor1560,G,P,V);constructors++;
 const constructorRaw=hex(G,2592);if(r(G+1712)||r(G+2056)||r(G+2032)||r(G+1632)||r(G+1792)||r(G+664)||r(G+2116))throw Error('Actual constructor domain nonempty');
 const innateKind=r(r(G+1256));if(innateKind===12)throw Error('Innate revival active');
 const hero=Buffer.from(c.hero),H=alloc(hero.length);b().set(hero,H);w(G+220,H);w(G+224,hero.length);
 for(const[o,v]of s.counters)w(G+o,v);w(G+2352,s.now_bits);w(G+1644,s.action_sequence1644);w(G+2412,s.movement_sequence2412);w(G+1440,c.starting_hp_bits);w(G+1568,0);
 d().setBigUint64(G+984,BigInt(s.damage984_f64_bits),true);d().setBigUint64(G+992,BigInt(c.taken_before_bits),true);b()[G+2587]=1;b()[G+2567]=c.left;b()[G+2582]=0;b()[G+2578]=0;
 const vectors={};for(const[key,stride,base]of[['units',424,1784],['auxiliary',112,656],['claims',88,2108]]){
  const storage=s[key+'_storage'],count=s[key+'_count'];if(!storage.length){vectors[key]={base,stride,p:r(G+base+4),capacity:0};continue;}
  const p=alloc(storage.length*stride);w(G+base,storage.length);w(G+base+4,p);w(G+base+8,count);for(let j=0;j<storage.length;j++){const value=Buffer.from(storage[j],'hex');if(value.length!==stride)throw Error('Stride');b().set(value,p+j*stride);}vectors[key]={base,stride,p,capacity:storage.length};
 }
 function queues(){
  const packets=[];for(let i=0;i<r(G+1888);i++){const p=r(G+1884)+i*16,n=r(p+8);if(n>65536||n>r(p))throw Error('Packet bound');packets.push({opcode:d().getUint16(p+12,true),capacity:r(p),payload_hex:hex(r(p+4),n)});}
  const notifications=[];for(let i=0;i<r(G+1900);i++){const p=r(G+1896)+i*12,n=r(p+8);if(n>65536||n>r(p))throw Error('Notification bound');notifications.push({capacity:r(p),payload_hex:hex(r(p+4),n)});}
  return{packets,notifications,packet_capacity:r(G+1880),packet_count:r(G+1888),notification_capacity:r(G+1892),notification_count:r(G+1900)};
 }
 function history(){const cap=r(G+968),p=r(G+972),head=r(G+976),count=r(G+980);if(cap>4096||count>cap)throw Error('History domain');return{capacity:cap,head,count,active:Array.from({length:count},(_,j)=>{const q=p+((head+j)%cap)*48;return{raw_hex:hex(q,48),strings:[0,8,16].map(o=>new TextDecoder('utf8',{fatal:true}).decode(b().subarray(r(q+o),r(q+o)+r(q+o+4))))};})};}
 const beforeRaw=b().slice(G,G+2592),before={raw_game2592_hex:hex(G,2592),...queues(),history:history()};
 if(c.kind==='helper'){if(c.starting_hp_bits!==0)throw Error('Direct5620 receives normalized HP0');call(ex.research_death135_death5620,G);calls5620++;}
 else if(c.kind==='incoming'){const dv=new DataView(new ArrayBuffer(4));dv.setUint32(0,c.amount_bits,true);call(ex.research_death135_incoming1073,G,dv.getFloat32(0,true),BigInt(c.source_guid),0,0,0);calls1073++;}
 else throw Error('Target kind');
 const changes=[];for(let o=0;o<2592;o++)if(beforeRaw[o]!==b()[G+o])changes.push([o,b()[G+o]]);
 const keyed={};const node=r(G+2476),depth=r(G+2480);if(node&&depth===0){const count=d().getUint16(node+50,true);for(let j=0;j<count;j++)keyed[d().getUint16(node+52+j*2,true)]=r(node+4+j*4);}
 process.stdout.write(JSON.stringify({id:c.id,kind:c.kind,constructor_raw_game2592_hex:constructorRaw,constructor_innate_kind:innateKind,before,after:{raw_game2592_hex:hex(G,2592),...queues(),history:history(),vectors:Object.fromEntries(Object.entries(vectors).map(([k,v])=>[k,{count:r(G+v.base+8),storage:Array.from({length:v.capacity},(_,j)=>hex(v.p+j*v.stride,v.stride))}])),keyed_fields:keyed},changed_bytes:changes,stack_after:stack.value,host_calls:hosts.length})+'\n');
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/runtime.json`,JSON.stringify({cases:cases.length,full1560_calls:constructors,full5620_direct_calls:calls5620,full1073_calls:calls1073,nested5620_on_static_fatal_path:calls1073,nested_callee_count_instrumented:false,actual_host_calls:0,denied_imports:878,fresh_instances:cases.length,max_memory_bytes:maxMemory,memory_page_cap:512,heap_cap_mib:512,stack_guards:guards,all_stack_returns:true,original_bodies_unchanged:true,app_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
