// New full1351417 kind2 / full947 G2448; explicit independent-world fixtures.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {packAiWorld135} from './ai_world135_packing.mjs';
const [dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('32MiB cap required');
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(hash(original)!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||hash(changed)!==manifest.module_sha256||input.length>4194304)throw Error('Source/input identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const before=sections(original),after=sections(changed);
if(before.map(s=>s.kind).join()!==after.map(s=>s.kind).join()||before.some(s=>s.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Original nonexport bytes changed');});
const oldExports=exportsOf(original,before.find(s=>s.kind===7)),newExports=exportsOf(changed,after.find(s=>s.kind===7));
const allowed=[{name:'research135_spawn_pickup',kind:0,index:1417},{name:'research135_spawn_tick',kind:0,index:947},{name:'research135_resource_stack0',kind:3,index:0}];
if(JSON.stringify(newExports.slice(0,oldExports.length))!==JSON.stringify(oldExports)||JSON.stringify(newExports.slice(oldExports.length))!==JSON.stringify(allowed))throw Error('Private export surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>128)throw Error('Import/case profile');
const number=word=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,word,true);return v.getFloat32(0,true);};
let hostCalls=0,peak=0,outputBytes=0;const callCounts={},stackChecks=[];
async function run(c){
 const bindings={};for(const item of imports){bindings[item.module]??={};bindings[item.module][item.name]=()=>{hostCalls++;throw Error('Denied original host '+item.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research135_resource_stack0;
 const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Precall stack');let returned=false;try{const result=fn(...args);returned=true;return result;}finally{const after=stack.value;stackChecks.push({case_id:c.id,index,before,after,returned});if(returned&&before!==after)throw Error('Stack not restored');}}
 function allocate(n,align=8){if(n<1||n>4194304)throw Error('Allocation budget');const p=call(91941,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');bytes().fill(0,p,p+n);return p;}
 const world=await packAiWorld135({memory,allocate},c.world),G=allocate(8192),s=c.input;
 const mapName=Buffer.from(c.map_id_utf8),name=allocate(mapName.length,1);bytes().set(mapName,name);w(G+184,name);w(G+188,mapName.length);w(G+2348,world.R);
 function vector(value,capOff,ptrOff,countOff,stride){const p=value.storage.length?allocate(value.storage.length*stride):stride===56?8:4;
  value.storage.forEach((row,j)=>{if(row.length!==stride)throw Error('Physical row stride');bytes().set(row.map(x=>x===null?c.unknown_poison:x),p+j*stride);});
  w(G+capOff,value.storage.length);w(G+ptrOff,p);w(G+countOff,value.count);
 }
 vector(s.pickups,1868,1872,1876,56);w(G+2352,s.now_bits);w(G+2408,s.counter);s.rng_words.forEach((word,j)=>w(G+1720+j*4,word));
 // Valid empty transport vector; original50798 owns any allocation/growth.
 w(G+1880,0);w(G+1884,4);w(G+1888,0);
 w(G+1892,0);w(G+1896,4);w(G+1900,0);w(G+2412,c.message_sequence);
 bytes()[G+2582]=s.mode;w(G+2140,s.party_count2140);w(G+2548,s.excluded2548);
 const prePickupPointer=r(G+1872),prePickupCount=r(G+1876),oldPickupGUIDs=new Set(Array.from({length:prePickupCount},(_,j)=>d().getBigUint64(prePickupPointer+j*56+16,true).toString()));
 let gameBefore;
 if(c.operation==='produce'){
  const P=allocate(12,4);s.position_bits.forEach((word,j)=>w(P+j*4,word));
  gameBefore=hex(G,8192);call(1417,e.research135_spawn_pickup,G,2,s.amount,P);callCounts[1417]=(callCounts[1417]??0)+1;
 }else if(c.operation==='tick'){
  const f=c.frame;vector(c.units,1784,1788,1792,424);
  for(const [o,key]of[[2416,'budget_bits'],[2420,'kill_cost_bits'],[2516,'zone_multiplier_bits'],[400,'victory_field400'],[404,'endless_start_bits'],[2540,'members']])w(G+o,f[key]);
  bytes()[G+387]=f.difficulty;bytes()[G+2582]=f.mode;bytes()[G+2568]=f.endless_flag;
  f.player_xyz.forEach((word,j)=>w(G+1416+j*4,word));f.previous_player_xyz.forEach((word,j)=>w(G+2428+j*4,word));f.velocity_xy.forEach((word,j)=>w(G+1736+j*4,word));
  w(G+1432,c.level);d().setBigUint64(G+1336,BigInt(c.player_guid),true);
  // Actual constructor defaults; these are all future at explicit now40.
  for(const[o,word]of c.initial_scalars)w(G+o,word);
  w(G+2416,f.budget_bits);w(G+2420,f.kill_cost_bits);f.previous_player_xyz.forEach((word,j)=>w(G+2428+j*4,word));
  for(const[o,word]of Object.entries(c.other_clocks))w(G+Number(o),word);
  w(G+2448,s.next_supply2448_bits);bytes()[G+2582]=s.mode;w(G+2140,s.party_count2140);w(G+2548,s.excluded2548);
  const peers=c.peer_positions16;if(!Array.isArray(peers)||peers.length>64)throw Error('Explicit peer positions');
  const peerPointer=peers.length?allocate(peers.length*16):4;peers.forEach((row,j)=>{if(row.length!==4)throw Error('Peer16 layout');row.forEach((v,k)=>w(peerPointer+j*16+k*4,v));});
  w(G+2228,peers.length);w(G+2232,peerPointer);w(G+2236,peers.length);
  gameBefore=hex(G,8192);
  call(947,e.research135_spawn_tick,G,number(f.dt_bits));callCounts[947]=(callCounts[947]??0)+1;
 }else throw Error('Exact component operation required');
 function capture(capOff,ptrOff,countOff,stride){const capacity=r(G+capOff),p=r(G+ptrOff),count=r(G+countOff);if(count>capacity||capacity>4096||p+capacity*stride>memory.buffer.byteLength)throw Error('Vector bounds');return{capacity,count,storage:Array.from({length:capacity},(_,j)=>hex(p+j*stride,stride))};}
 const n=r(G+1888),p=r(G+1884);if(n>128||r(G+1880)<n)throw Error('Packet bound');
 const packets=Array.from({length:n},(_,j)=>{const q=p+j*16,k=r(q+8),b=r(q+4);if(k>r(q)||k>1048576||b+k>memory.buffer.byteLength)throw Error('Packet payload');return{opcode:d().getUint16(q+12,true),payload_hex:hex(b,k)};});
 const result={pickups:capture(1868,1872,1876,56),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),counter:r(G+2408),message_sequence:r(G+2412),packets,notifications_count:r(G+1900)};
 if(c.operation==='tick')Object.assign(result,{next_supply2448_bits:r(G+2448),budget_bits:r(G+2416),kill_cost_bits:r(G+2420),velocity_xy:[r(G+1736),r(G+1740)],previous_player_xyz:[0,1,2].map(j=>r(G+2428+j*4)),units:capture(1784,1788,1792,424),other_clocks:Object.fromEntries([2424,2440,2444,2456,2460].map(o=>[o,r(G+o)]))});
 const opaque=[],amountObservations=[];
 if(c.operation==='tick'&&prePickupCount){
  const q=r(G+1872),n=r(G+1876),delta=prePickupCount%4===0?176+224*Math.floor(prePickupCount/4):8+56*prePickupCount;
  for(let j=0;j<n;j++){const row=q+j*56,guid=d().getBigUint64(row+16,true).toString();
   if(r(row+8)===2&&!oldPickupGUIDs.has(guid)){
    const actual=r(row+12),derived=(prePickupPointer+delta)>>>0;if(actual!==derived)throw Error('Original G2448 amount iterator provenance differs');
    opaque.push({guid,offset:12,bytes:4,owner_symbol:'pickup56_owner_before2448',active_count:prePickupCount,byte_delta:delta,expression:'pre_owner_base+byte_delta modulo2^32'});
    amountObservations.push({guid,actual_word:actual,pre_owner_base:prePickupPointer,byte_delta:delta,derived_word:derived});
   }
  }
 }
 result.opaque_word_provenance=opaque;
 world.verify();if(hostCalls)throw Error('Denied host attempted');peak=Math.max(peak,memory.buffer.byteLength);
 const line=JSON.stringify({id:c.id,result,game_before8192_hex:gameBefore,game_after8192_hex:hex(G,8192),amount_observations:amountObservations})+'\n';outputBytes+=Buffer.byteLength(line);if(Buffer.byteLength(line)>2097152||outputBytes>16777216)throw Error('Capture budget');process.stdout.write(line);
}
let failure=null;
try{for(const c of cases){await run(c);if(global.gc)global.gc();}}catch(error){failure=String(error);throw error;}finally{
await fs.writeFile(dir+'/supply-kind2-runtime.json',JSON.stringify({cases:cases.length,functions:callCounts,fresh_instances:cases.length,max_memory_bytes:peak,memory_cap_bytes:33554432,actual_host_calls:hostCalls,denied_imports:878,stack_checks:stackChecks,stack_all_restored:stackChecks.every(x=>x.before===x.after&&x.returned),original_function_bodies_unchanged:true,application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false,original_memory_snapshot_read:false,output_bytes:outputBytes,amount_pointer_used_as_model_input:false,failure},null,2)+'\n');
}
