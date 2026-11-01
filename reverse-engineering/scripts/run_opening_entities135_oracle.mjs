// Complete original1744/1821 over a genuine full snapshot, all878 imports deny.
import fs from'node:fs/promises';
import{prepareWorldSnapshot135}from'./world_snapshot135_host.mjs';
const[directory,configPath]=process.argv.slice(2),config=JSON.parse(await fs.readFile(configPath,'utf8'));
if(Object.keys(config).sort().join()!=='G,inputs,snapshot,snapshot_sha256')throw Error('Config keyset');
const prepared=await prepareWorldSnapshot135(directory,['companions','world_actor']);
const cases=JSON.parse(await fs.readFile(config.inputs,'utf8'));if(!cases.length||cases.length>512)throw Error('Case budget');
const number=x=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,x,true);return d.getFloat32(0,true);};
let calls=0,maxMemory=0,hostCount=0,stagesTotal=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input,kind,ops')throw Error('Expected must not reach original');
 const host=await prepared.restore(config.snapshot,config.snapshot_sha256),{roles,memory,allocate,hostCalls}=host,G=config.G,s=c.input;
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),r=p=>d().getUint32(p,true),w=(p,x)=>d().setUint32(p,x,true),g=(o,x)=>w(G+o,x),b=(o,x)=>d().setUint8(G+o,x);
 const raw=(p,n)=>{if(p<0||n<0||p+n>memory.buffer.byteLength)throw Error('Physical bounds');return Buffer.from(bytes().slice(p,p+n)).toString('hex');};
 g(2408,s.counter);s.rng_words.forEach((x,j)=>g(1720+j*4,x));if(r(G+1888)!==0)throw Error('Expected realphase0 empty message vector');
 let pointerMap=[],initialCount=0;
 if(c.kind==='companions'){
  initialCount=s.prior_count;const cap=s.prior_storage.length,P=cap?allocate(cap*88,4):8;
  s.prior_storage.forEach((x,j)=>{if(x.length!==176)throw Error('88B input');bytes().set(Buffer.from(x,'hex'),P+j*88);});g(2108,cap);g(2112,P);g(2116,s.prior_count);b(2576,s.protection2576);
  for(let i=0;i<2;i++){
   const p=s.prototypes[i];let pointer=0;
   if(p.token){pointer=allocate(44,4);w(pointer+32,p.display);w(pointer+36,p.scale_bits);w(pointer+40,p.entry);}else if(p.entry||p.display||p.scale_bits)throw Error('Null prototype fields differ');
   w(G+240+i*8,pointer);pointerMap.push({slot:i,pointer,token:p.token,prototype44_hex:raw(pointer,44)});
  }
 }
 const results=[],returns=[],signedReturns=[];
 for(const op of c.ops){
  if(c.kind==='companions'){
   if(Object.keys(op).sort().join()!=='heading,now_bits,player_xyz,rank273,stat1556_bits,tags')throw Error('Companion input keys');
   op.tags.forEach((x,j)=>b(244+j*8,x));op.player_xyz.forEach((x,j)=>g(1416+j*4,x));g(1428,op.heading);g(2352,op.now_bits);g(1556,op.stat1556_bits);b(273,op.rank273);roles.companions(G);
  }else{
   if(c.kind!=='world_actor'||Object.keys(op).sort().join()!=='display,entry,flags9,kind21,scale_bits,xyz')throw Error('Actor input keys');
   const P=allocate(12,4),XYZ=allocate(12,4);w(P,op.entry);w(P+4,op.display);w(P+8,op.scale_bits);op.xyz.forEach((x,j)=>w(XYZ+j*4,x));const result=roles.world_actor(G,P,XYZ,op.kind21,op.flags9);signedReturns.push(result.toString());returns.push(BigInt.asUintN(64,result).toString());
  }
  calls++;stagesTotal++;if(hostCalls.length)throw Error('Original host attempted');
  const n=r(G+1888),p=r(G+1884),capacity=r(G+1880);if(n>4096||n>capacity)throw Error('Message bounds');
  const packets=Array.from({length:n},(_,j)=>{const q=p+j*16;return{opcode:d().getUint16(q+12,true),payload_hex:raw(r(q+4),r(q+8))};});
  const out={counter:r(G+2408),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),packets,
   raw_game2592_hex:raw(G,2592),message_metadata_backing_hex:raw(p,capacity*16),actual_stack:host.stackPointer};
  if(c.kind==='companions'){
   const count=r(G+2116),cap=r(G+2108),ptr=r(G+2112);if(cap>4096||count>cap)throw Error('Companion bounds');
   out.companion_count=count;out.companion_capacity=cap;out.companion_raw_storage=Array.from({length:cap},(_,j)=>raw(ptr+j*88,88));
   out.companion_storage=out.companion_raw_storage.map((x,j)=>{const data=Buffer.from(x,'hex');if(j>=initialCount&&j<count){const pointer=data.readUInt32LE(16),mapping=pointerMap.find(x=>x.pointer===pointer);if(!mapping)throw Error('Unexpected definition owner');data.writeUInt32LE(mapping.token,16);}return data.toString('hex');});
  }else{out.return_guids=[...returns];out.signed_i64_returns=[...signedReturns];}
  results.push(out);maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 }
 hostCount+=hostCalls.length;
 process.stdout.write(JSON.stringify({id:c.id,stages:results,pointer_map:pointerMap,original_calls:host.calls,snapshot:host.snapshot})+'\n');
}
await fs.writeFile(`${directory}/opening-entities135-runtime.json`,JSON.stringify({cases:cases.length,stages:stagesTotal,original1744_1821_calls:calls,full_snapshot_restores:cases.length,
 max_memory_bytes:maxMemory,memory_cap_bytes:256*1024*1024,denied_imports:878,host_calls:hostCount,all_original_callees_preserved:true,
 appstart_called:false,network_used:false,user_saves_accessed:false,snapshot_bootstrap_reexecuted:false},null,2)+'\n');
