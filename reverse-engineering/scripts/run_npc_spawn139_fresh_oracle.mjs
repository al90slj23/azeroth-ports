// Fresh1600 then four complete5719 calls; all882 imports denied, no snapshot.
import fs from'node:fs/promises';import{createHash}from'node:crypto';
const[dir,configPath]=process.argv.slice(2),hash=x=>createHash('sha256').update(x).digest('hex'),c=JSON.parse(await fs.readFile(configPath,'utf8')),m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('Separate32MiB/512MiB caps');
const wasm=await fs.readFile(dir+'/'+m.module_file),input=await fs.readFile(c.inputs);
if(hash(wasm)!==m.module_sha256||hash(input)!==c.inputs_sha256||m.source_sha256!=='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'||input.length>4194304||m.entry_index!==5719)throw Error('Frozen139 identity');
const module=await WebAssembly.compile(wasm),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);if(imports.length!==882||imports.some(x=>x.kind!=='function')||JSON.stringify(imports.map(({module,name})=>({module,name})))!==JSON.stringify(m.original_imports.map(({module,name})=>({module,name})))||cases.length>64)throw Error('Exact882 surface');
let hostCount=0,peak=0,calls=0,stackChecks=0,rawObservationBytes=0;
for(const x of cases){
 const bindings={};for(const v of imports){bindings[v.module]??={};bindings[v.module][v.name]=()=>{hostCount++;throw Error('Denied139 import '+v.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,mem=e.memory,stack=e.research139_spawn_stack0;if(stack.value!==1048576)throw Error('Initial memory/stack');
 const d=()=>new DataView(mem.buffer),b=()=>new Uint8Array(mem.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v,true),hex=(p,n)=>Buffer.from(b().subarray(p,p+n)).toString('hex');
 const guard=fn=>{if(stack.value!==1048576)throw Error('Stack before');const z=fn();if(stack.value!==1048576)throw Error('Stack after');stackChecks++;return z;};
 const alloc=n=>{const p=guard(()=>e.__wbindgen_malloc(n,8))>>>0;if(!p||p+n>mem.buffer.byteLength||mem.buffer.byteLength>33554432)throw Error('Allocation boundary');return p;};
 const G=alloc(8192),profile=alloc(376),V=alloc(128),N=alloc(8);b().fill(0xa5,G,G+8192);b().fill(0,profile,profile+376);b().fill(0x5a,V,V+128);b().set(Buffer.from('elwynn'),N);
 w(profile+156,4);w(profile+168,N);w(profile+172,6);d().setBigUint64(profile+176,0n,true);d().setBigUint64(profile+184,1n,true);b()[profile+344]=1;b()[profile+345]=1;b()[V+120]=1;w(V+116,0);w(V+56,0xffffffff);w(V+32,0xffffffff);
 const profileBefore=hex(profile,376),viewBefore=hex(V,128);guard(()=>e.research139_spawn_constructor1600(G,profile,V));
 if(profileBefore!==hex(profile,376)||viewBefore!==hex(V,128)||u(G+2348)!==V)throw Error('Freshconstructor profile/query identity');
 if(Object.keys(x).sort().join()!=='counter,id,initial_backing,player_xy,positions,rng_words'||x.positions.length!==4||![0,4].includes(x.initial_backing.length))throw Error('Input-only fourNPC domain');
 if(u(G+1792)!==0||u(G+1784)!==0||u(G+1788)!==8||u(G+1888)!==0||u(G+1432)!==1||d().getBigUint64(G+1336,true)!==0n||u(G+1416)!==x.player_xy[0]||u(G+1420)!==x.player_xy[1]||Buffer.from(b().subarray(u(G+184),u(G+184)+u(G+188))).toString()!=='elwynn')throw Error('Originalcontext/domain invariants');
 if(x.initial_backing.length){const U=alloc(4*432);x.initial_backing.forEach((s,j)=>{const a=Buffer.from(s,'hex');if(a.length!==432)throw Error('432B backing');b().set(a,U+j*432);});w(G+1784,4);w(G+1788,U);}
 const P=alloc(16),O=alloc(16);w(G+2408,x.counter);x.rng_words.forEach((v,j)=>w(G+1720+4*j,v));
 for(const[o,v]of[[2516,0x3f800000],[2540,1],[1432,1],[2352,0],[400,0]])w(G+o,v);b()[G+2582]=0;b()[G+387]=0;b()[G+2568]=0;
 const answers=[],rawGames=[];
 for(let index=0;index<4;index++){
  b().fill(0xa5,P,P+16);b().fill(0xa5,O,O+16);w(P,1);x.positions[index].forEach((v,j)=>w(P+4+4*j,v));guard(()=>e.research139_spawn5719(O,G,0,P));calls++;
  const capacity=u(G+1784),pointer=u(G+1788),count=u(G+1792);if(hostCount||capacity!==4||count!==index+1)throw Error('Actual4capacity/active count');
  const pc=u(G+1888),pp=u(G+1884);if(pc!==index+1||u(G+1880)>32)throw Error('Newpacket count');const packets=[];for(let j=0;j<pc;j++){const q=pp+j*16,n=u(q+8);if(n>u(q)||n>4096)throw Error('Payload budget');packets.push([d().getUint16(q+12,true),hex(u(q+4),n)]);}
  answers.push({success:d().getBigUint64(O,true)===1n,guid:d().getBigUint64(O+8,true).toString(),counter:u(G+2408),rng_words:[0,1,2,3].map(j=>u(G+1720+j*4)),capacity,count,records432_hex:Array.from({length:4},(_,j)=>hex(pointer+j*432,432)),HP288_bits:u(pointer+index*432+288),attack296_bits:u(pointer+index*432+296),packets});
  rawGames.push(hex(G,2592));rawObservationBytes+=2592;
 }
 process.stdout.write(JSON.stringify({id:x.id,answers,raw_games2592_hex:rawGames,stack_after:stack.value,phase2587:b()[G+2587]})+'\n');peak=Math.max(peak,mem.buffer.byteLength);
}
await fs.writeFile(dir+'/runtime.json',JSON.stringify({version:'0.139.0',build:'f79c5e2b4',full5719_calls:calls,fresh_instances:cases.length,full1600_calls:cases.length,snapshot_restores:0,denied_imports:882,actual_host_calls:hostCount,stack_checks:stackChecks,peak_memory_bytes:peak,memory_cap_bytes:33554432,raw_Game_observation_bytes:rawObservationBytes,only_export_section_changed:true,old_snapshot_loaded:false,naturalApp_claimed:false,borrowed_flat_query_input:true,fullworldRc_produced:false,independent_world_producer:false,native_executions:0,complete_games:0})+'\n');
