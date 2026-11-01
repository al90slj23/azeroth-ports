// Complete original2376 first-expiry NPC producer, explicit locale input, no App start.
import fs from 'node:fs/promises';import{createHash}from'node:crypto';
const[dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Explicit32MiB cap');
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),raw=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(hash(raw)!==manifest.module_sha256||manifest.original_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||manifest.entry.index!==2376||manifest.entry.body_sha256!=='6b985b23a141a82085f021e7bedf0247ea2a61a99bda05cf820e38a369be29ff'||input.length>4194304)throw Error('Original module/input identity');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(v=>v.kind!=='function')||cases.length>512)throw Error('878/bounded case domain');
const MASK=(1n<<64n)-1n,rot=(x,n)=>((x<<BigInt(n))|(x>>BigInt(64-n)))&MASK;
function sip13(text,k0,k1){
 const bytes=Buffer.concat([Buffer.from(text,'utf8'),Buffer.from([255])]);
 let v0=k0^0x736f6d6570736575n,v1=k1^0x646f72616e646f6dn,v2=k0^0x6c7967656e657261n,v3=k1^0x7465646279746573n;
 function round(){v0=(v0+v1)&MASK;v1=rot(v1,13)^v0;v0=rot(v0,32);v2=(v2+v3)&MASK;v3=rot(v3,16)^v2;v0=(v0+v3)&MASK;v3=rot(v3,21)^v0;v2=(v2+v1)&MASK;v1=rot(v1,17)^v2;v2=rot(v2,32);}
 let at=0;for(;at+8<=bytes.length;at+=8){const m=bytes.readBigUInt64LE(at);v3^=m;round();v0^=m;}
 let last=BigInt(bytes.length&255)<<56n;for(let j=at;j<bytes.length;j++)last|=BigInt(bytes[j])<<BigInt(8*(j-at));
 v3^=last;round();v0^=last;v2^=255n;round();round();round();return(v0^v1^v2^v3)&MASK;
}
let calls=0,hostCalls=0,peak=0,packetsTotal=0,unknownCellsPreserved=0; const stackChecks=[];const localeReceipts=[];
for(const c of cases){
 if(c.id!==calls||Object.keys(c).sort().join()!=='id,input')throw Error('Input-only case shape/order');
 const bind={};for(const v of imports){bind[v.module]??={};bind[v.module][v.name]=()=>{hostCalls++;throw Error('Denied original host '+v.name);};}
 const ins=await WebAssembly.instantiate(module,bind),e=ins.exports,memory=e.memory;
 const b=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),u=p=>d().getUint32(p,true),w=(p,n)=>d().setUint32(p,n>>>0,true),hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 function alloc(n,align=4){if(n<1||n>4194304)throw Error('Single fixture allocation budget');const p=e.__wbindgen_malloc(n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Allocation/memory budget');b().fill(0xa5,p,p+n);return p;}
 function text(value){const raw=Buffer.from(value,'utf8');if(!raw.length||raw.length>4096||raw.includes(0))throw Error('Explicit nonempty name');const p=alloc(raw.length,1);b().set(raw,p);return[p,raw.length];}
 const guards=[],guard=(p,n)=>guards.push({p,n,sha256:hash(b().slice(p,p+n))});
 const names=c.input.locale.names,k0=0x0123456789abcdefn,k1=0xfedcba9876543210n;
 if(!names.length||names.length>128||new Set(names.map(v=>v[0])).size!==names.length)throw Error('Explicit locale dictionary shape');
 let buckets=16;while(buckets-buckets/8<names.length)buckets*=2;
 const table=alloc(14*32,8),mapReceipts=[],localePointers=new Set();
 for(let i=0;i<14;i++){
  const block=alloc(buckets*20+buckets+8,8),ctrl=block+buckets*20,slotReceipts=[];
  if(localePointers.has(block))throw Error('Distinct locale RawTable ownership');localePointers.add(block);
  b().fill(255,ctrl,ctrl+buckets+8);
  for(const[key,value]of names){
   const digest=sip13(key,k0,k1),lo=Number(digest&0xffffffffn)>>>0,fingerprint=lo>>>25,mask=buckets-1;
   let probe=lo&mask,step=0,slot=-1;
   while(slot<0){for(let offset=0;offset<8;offset++){const candidate=(probe+offset)&mask;if(b()[ctrl+candidate]===255){slot=candidate;break;}}if(slot<0){step+=8;probe=(probe+step)&mask;if(step>buckets*2)throw Error('HashMap probe capacity');}}
   b()[ctrl+slot]=fingerprint;if(slot<8)b()[ctrl+buckets+slot]=fingerprint;
   const kp=text(key),vp=text(value),at=ctrl-20*(slot+1);
   if(localePointers.has(kp[0])||localePointers.has(vp[0]))throw Error('Distinct locale string allocations');localePointers.add(kp[0]);localePointers.add(vp[0]);
   w(at,kp[1]);w(at+4,kp[0]);w(at+8,kp[1]);w(at+12,vp[0]);w(at+16,vp[1]);guard(kp[0],kp[1]);guard(vp[0],vp[1]);
   slotReceipts.push({key,slot,fingerprint,hash64_hex:digest.toString(16).padStart(16,'0'),key_capacity:kp[1],key_pointer:kp[0],value_pointer:vp[0]});
  }
  const p=table+i*32;w(p,ctrl);w(p+4,buckets-1);w(p+8,buckets-buckets/8-names.length);w(p+12,names.length);d().setBigUint64(p+16,k0,true);d().setBigUint64(p+24,k1,true);
  guard(block,buckets*20+buckets+8);mapReceipts.push({index:i,block,ctrl,slots:slotReceipts});
 }
 // Complete initialized Once<Vec<HashMap>> is an explicit typed input. No
 // callee or lookup result is patched; actual19964/27372 perform every lookup.
 w(14384320,0);w(14384324,0);w(14384328,0);w(14384332,14);w(14384336,table);w(14384340,14);d().setUint8(14384344,3);
 guard(table,14*32);guard(14384320,25);

 const s=c.input.state.special,source=c.input.original_special_storage,v=c.input.state,G=alloc(2592,8);
 b().fill(0,G,G+2592);const g=(o,x)=>w(G+o,x),Q=alloc(Math.max(1,source.length)*40,8);
 const unitSource=c.input.original_unit_storage,U=alloc(Math.max(1,unitSource.length)*424,8),M=alloc(16*16,8);
 const checkConcrete=(physical,logical,stride)=>{
  if(physical.length!==logical.length)throw Error('Physical/logical capacity differs');
  physical.forEach((value,j)=>{const concrete=Buffer.from(value,'hex'),row=typeof logical[j]==='string'?[...Buffer.from(logical[j],'hex')]:logical[j];
   if(concrete.length!==stride||row.length!==stride)throw Error('Exact input record width');
   for(let k=0;k<stride;k++)if(row[k]!==null&&row[k]!==concrete[k])throw Error('Known input cell differs');});
 };
 checkConcrete(source,s.storage,40);checkConcrete(unitSource,v.units.storage,424);
 if(s.count>source.length||v.units.count>unitSource.length)throw Error('Active prefix budget');
 source.forEach((value,j)=>b().set(Buffer.from(value,'hex'),Q+j*40));
 unitSource.forEach((value,j)=>b().set(Buffer.from(value,'hex'),U+j*424));
 const zone=text('elwynn');g(184,zone[0]);g(188,zone[1]);
 for(const[o,x]of[[2352,s.now_bits],[1416,v.player_xyz_bits[0]],[1420,v.player_xyz_bits[1]],[1424,v.player_xyz_bits[2]],
 [392,s.selected392],[396,s.target396],[2392,s.announcement_time2392_bits],[1432,v.level1432],[2516,v.zone_multiplier_bits],
 [2540,v.members],[1092,v.field1092],[400,v.victory400],[404,v.endless_start404_bits],[2408,v.counter]])g(o,x);
 for(const[o,x]of[[2576,s.protection2576],[2564,s.navigation2564],[2565,s.announced2565],
 [387,v.difficulty],[2582,v.mode],[2568,v.endless_flag2568]])d().setUint8(G+o,x);
 d().setBigUint64(G+1336,BigInt(v.player_guid),true);v.rng_words.forEach((x,j)=>g(1720+j*4,x));
 g(1916,source.length);g(1920,Q);g(1924,s.count);g(1784,unitSource.length);g(1788,U);g(1792,v.units.count);
 g(1880,16);g(1884,M);g(1888,0);
 const before=b().slice(G,G+2592),stackBefore=e.research_special2376_stack.value;
 if(stackBefore!==1048576)throw Error('Precall stack');e.special2376_135_tick(G);calls++;
 const stackAfter=e.research_special2376_stack.value;if(stackBefore!==stackAfter)throw Error('Original stack restoration');
 stackChecks.push({id:c.id,before:stackBefore,after:stackAfter,returned:true});
 const specialStorage=source.map((_,j)=>hex(Q+j*40,40)),capacity=u(G+1784),unitPointer=u(G+1788),count=u(G+1792);
 if(count>capacity||capacity>128||unitPointer+capacity*424>memory.buffer.byteLength)throw Error('Actual NPC vec bounds');
 const unitStorage=Array.from({length:capacity},(_,j)=>hex(unitPointer+j*424,424)),cooldowns=[],timerPointers=new Set();
 for(let j=0;j<v.units.count;j++)if(unitStorage[j]!==unitSource[j])throw Error('Existing full NPC prefix mutated');
 for(let j=count;j<unitSource.length;j++)if(unitStorage[j]!==unitSource[j])throw Error('Unused input NPC capacity mutated');
 for(let j=0;j<source.length;j++){
  if(specialStorage[j].slice(72)!==source[j].slice(72))throw Error('Special unknown padding changed');
  const old=Buffer.from(source[j],'hex'),oldMarker=old.readBigUInt64LE(),due=j<s.count&&!s.protection2576&&oldMarker===0n&&
   (()=>{const scratch=new DataView(old.buffer,old.byteOffset,old.byteLength);const clock=new DataView(new ArrayBuffer(4));clock.setUint32(0,s.now_bits,true);return clock.getFloat32(0,true)>=scratch.getFloat32(32,true);})();
  if(!due&&specialStorage[j]!==source[j])throw Error('Undue/active full special bytes mutated');
 }
 for(let j=v.units.count;j<count;j++){
  const at=unitPointer+j*424,n=u(at+64),ptr=u(at+68),len=u(at+72);
  if(n!==3||len!==n||!ptr||ptr%4||ptr+len*4>memory.buffer.byteLength||timerPointers.has(ptr)
    ||(ptr<unitPointer+capacity*424&&ptr+len*4>unitPointer))throw Error('Distinct valid owned special timer allocation');timerPointers.add(ptr);
  cooldowns.push({unit_index:j,guid:d().getBigUint64(at+112,true).toString(),capacity:n,timers_bits:Array.from({length:len},(_,k)=>u(ptr+k*4)),
    ability_pointer:u(at+76),header_pointer:u(at+96),pointer:ptr,
    ability_records44_hex:Array.from({length:len},(_,k)=>hex(u(at+76)+k*44,44)),header28_hex:hex(u(at+96),28)});
 }
 const packets=[];for(let j=0;j<u(G+1888);j++){
  const at=u(G+1884)+j*16,cap=u(at),ptr=u(at+4),n=u(at+8);if(j>=16||n>cap||cap>16384||!ptr||ptr+n>memory.buffer.byteLength)throw Error('Packet bounds');
  packets.push([d().getUint16(at+12,true),hex(ptr,n)]);packetsTotal++;
 }
 const allowed=o=>(o>=392&&o<400)||(o>=1720&&o<1736)||(o>=1784&&o<1796)||(o>=1880&&o<1892)||(o>=2392&&o<2396)||(o>=2408&&o<2412)||o===2565;
 const gameChanges=[];for(let i=0;i<2592;i++)if(before[i]!==b()[G+i]){if(!allowed(i))throw Error('Unexpected Game write '+i);gameChanges.push([i,b()[G+i]]);}
 for(const item of guards)if(hash(b().slice(item.p,item.p+item.n))!==item.sha256)throw Error('Initialized locale input mutated');
 if(hostCalls||memory.buffer.byteLength>33554432||u(G+1916)!==source.length||u(G+1920)!==Q)throw Error('Host/memory/special ownership boundary');
 peak=Math.max(peak,memory.buffer.byteLength);
 const answer={special:{storage:specialStorage,count:u(G+1924),selected392:u(G+392),target396:u(G+396),
  navigation2564:d().getUint8(G+2564),announced2565:d().getUint8(G+2565),announcement_time2392_bits:u(G+2392)},
  units:{capacity,count,storage:unitStorage},rng_words:[0,1,2,3].map(j=>u(G+1720+j*4)),counter:u(G+2408),
  cooldowns:cooldowns.map(({pointer,...value})=>value),packets};
 localeReceipts.push({id:c.id,language:c.input.locale.label,entries:names.length,buckets,distinct_tables:14,
  source_preserved:true,cold_initializer_recovered:false});
 process.stdout.write(JSON.stringify({id:c.id,answer,stack_before:stackBefore,stack_after:stackAfter,
  physical_timer_pointers:cooldowns.map(x=>x.pointer),game_changes:gameChanges})+'\n');
}
const runtime={cases:cases.length,calls,fresh_instances:cases.length,actual_host_calls:hostCalls,denied_imports:878,
 peak_memory_bytes:peak,packets:packetsTotal,locale_inputs:localeReceipts,stack_checks:stackChecks,stack_all_restored:stackChecks.every(x=>x.before===1048576&&x.after===x.before),
 full_original2376:true,unchanged1525_callee:true,original_application_start:false,network_used:false,user_saves_accessed:false,shared52_roles_changed:false};
const runtimeRaw=JSON.stringify(runtime)+'\n';if(Buffer.byteLength(runtimeRaw)>4194304)throw Error('Runtime budget');
await fs.writeFile(dir+'/special2376_spawn135-runtime.json',runtimeRaw);
