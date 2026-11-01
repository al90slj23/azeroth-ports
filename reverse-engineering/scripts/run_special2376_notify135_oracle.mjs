// Complete original2376 with explicit initialized locale tables; no cold locale producer claim.
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
let calls=0,hostCalls=0,peak=0,packetsTotal=0,unknownCellsPreserved=0;const localeReceipts=[];
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
 const s=c.input.state,source=c.input.original_storage,G=alloc(2592,8),Q=alloc(Math.max(1,source.length)*40,8),M=alloc(8*16),g=(o,v)=>w(G+o,v);
 if(source.length!==s.storage.length||source.length>512||s.count>source.length)throw Error('Full special backing prefix');
 source.forEach((value,j)=>{
  const concrete=Buffer.from(value,'hex'),logical=typeof s.storage[j]==='string'?[...Buffer.from(s.storage[j],'hex')]:s.storage[j];
  if(concrete.length!==40||logical.length!==40)throw Error('40B source layout');
  for(let k=0;k<40;k++){if(logical[k]===null){if(!(k>=8&&k<16||k>=36&&k<40))throw Error('Declared unknown mask');unknownCellsPreserved++;}else if(logical[k]!==concrete[k])throw Error('Known fixture byte differs from original physical input');}
  b().set(concrete,Q+j*40);
 });
 const zoneKeys=['elwynn','duskwood','wsg','ungoro','ab','feralas','arena','sm','av','brm','aq','naxx'];
 const zone=text(zoneKeys[c.input.zone]);g(184,zone[0]);g(188,zone[1]);
 for(const[o,v]of[[2352,s.now_bits],[1416,s.player_xy_bits[0]],[1420,s.player_xy_bits[1]],[392,s.selected392],[396,s.target396],[2392,s.announcement_time2392_bits]])g(o,v);
 for(const[o,v]of[[2576,s.protection2576],[2564,s.navigation2564],[2565,s.announced2565]])d().setUint8(G+o,v);
 g(1916,source.length);g(1920,Q);g(1924,s.count);g(1880,8);g(1884,M);g(1888,0);
 const before=b().slice(G,G+2592),stackBefore=e.research_special2376_stack.value;
 e.special2376_135_tick(G);calls++;
 const stackAfter=e.research_special2376_stack.value;if(stackBefore!==stackAfter)throw Error('Original stack restoration');
 const changes=[];for(let i=0;i<2592;i++)if(before[i]!==b()[G+i])changes.push([i,b()[G+i]]);
 const packets=[];for(let i=0;i<u(G+1888);i++){if(i>=8)throw Error('Packet count cap');const at=M+i*16,cap=u(at),p=u(at+4),n=u(at+8);if(n>cap||cap>16384||p+n>memory.buffer.byteLength)throw Error('Packet bytes cap');packets.push([d().getUint16(at+12,true),cap,hex(p,n)]);packetsTotal++;}
 for(const item of guards)if(hash(b().slice(item.p,item.p+item.n))!==item.sha256)throw Error('Initialized locale input mutated');
 const storage=source.map((value,j)=>{const observed=hex(Q+j*40,40);if(observed!==value)throw Error('40B backing changed in target-only continuation');return observed;});
 const answer={storage,count:u(G+1924),selected392:u(G+392),target396:u(G+396),announced2565:d().getUint8(G+2565),announcement_time2392_bits:u(G+2392),packets,game_changes:changes};
 if(hostCalls||memory.buffer.byteLength>33554432||u(G+1916)!==source.length||u(G+1920)!==Q)throw Error('Host/memory/physical40 owner boundary');peak=Math.max(peak,memory.buffer.byteLength);
 localeReceipts.push({id:c.id,locale:c.input.locale.label,entries:names.length,buckets,mask:buckets-1,k0_hex:k0.toString(16),k1_hex:k1.toString(16),initialized_once_flag:3,vec_count:14,source_preserved:true,distinct_map_and_string_allocations:true,maps:mapReceipts});
 process.stdout.write(JSON.stringify({id:c.id,answer,stack_before:stackBefore,stack_after:stackAfter})+'\n');
}
const runtime=JSON.stringify({cases:cases.length,calls,fresh_instances:cases.length,actual_host_calls:hostCalls,denied_imports:878,peak_memory_bytes:peak,packets:packetsTotal,unknown_input_cells_preserved:unknownCellsPreserved,locale_inputs:localeReceipts,locale_initializer_recovered:false,full_original2376:true,original_application_start:false,network_used:false,user_saves_accessed:false,shared52_roles_changed:false})+'\n';
if(Buffer.byteLength(runtime)>4194304)throw Error('4MiB runtime receipt budget');
await fs.writeFile(dir+'/special2376_notify135-runtime.json',runtime);
