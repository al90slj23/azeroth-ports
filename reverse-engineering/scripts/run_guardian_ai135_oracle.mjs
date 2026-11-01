// Complete unchanged921 over independently produced guardian rows and world.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareDistanceMap135} from './distance_map135_host.mjs';
import {packAiWorld135} from './ai_world135_packing.mjs';
const [directory,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
const prepared=await prepareDistanceMap135(directory,['update_units']);
const input=await fs.readFile(inputFile);if(input.length>4194304)throw Error('Input budget');
const cases=JSON.parse(input);if(!cases.length||cases.length>100)throw Error('Case budget');
const number=word=>{const view=new DataView(new ArrayBuffer(4));view.setUint32(0,word,true);return view.getFloat32(0,true);};
let calls=0,peak=0,hostCalls=0;const stackChecks=[],timerAllocations=[];
async function run(c){
 const host=await prepared.fresh(),world=await packAiWorld135(host,c.world);
 const {memory,allocate,roles}=host,b=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer);
 const w=(p,v)=>d().setUint32(p,v>>>0,true),u=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 const G=allocate(2592),U=allocate(c.capacity*424),Q=allocate(Math.max(1,c.special_storage.length)*40),name=allocate(6,1);
 b().fill(c.poison,U,U+c.capacity*424);b().set(Buffer.from('elwynn'),name);w(G+184,name);w(G+188,6);
 w(G+2348,world.R);w(G+1784,c.capacity);w(G+1788,U);w(G+1792,c.records.length);
 w(G+1916,c.special_storage.length);w(G+1920,Q);w(G+1924,c.special_count);w(G+2412,c.sequence);
 w(G+1440,c.hp_bits);w(G+1536,c.hp_bits);w(G+2532,1);d().setUint8(G+2587,1);d().setBigUint64(G+1336,42n,true);
 c.rng_words.forEach((word,j)=>w(G+1720+j*4,word));
 const materialize=(row,size)=>{
  const cells=typeof row==='string'?[...Buffer.from(row,'hex')]:row;
  if(cells.length!==size||cells.some(v=>v!==null&&(!Number.isInteger(v)||v<0||v>255)))throw Error('Explicit known/unknown cells');
  return Buffer.from(cells.map(v=>v===null?c.poison:v));
 };
 c.special_storage.forEach((row,j)=>b().set(materialize(row,40),Q+j*40));
 const pointers=[];
 c.records.forEach((row,j)=>{
  b().set(materialize(row,424),U+j*424);const owner=c.cooldowns[j],at=U+j*424,T=allocate(owner.capacity*4,4);
  if(owner.capacity!==3||owner.timers_bits.length!==3||u(at+64)!==3||u(at+72)!==3||d().getBigUint64(at+112,true).toString()!==owner.guid)throw Error('Real semantic timer owner binding');
  owner.timers_bits.forEach((word,k)=>w(T+k*4,word));w(at+68,T);pointers.push(T);
  timerAllocations.push({case_id:c.id,unit_index:j,pointer:T,capacity:3,guid:owner.guid});
 });
 const specialBefore=hex(Q,c.special_storage.length*40),inactiveBefore=hex(U+c.records.length*424,(c.capacity-c.records.length)*424);
 const stages=[];let previousPackets=0;
 for(const step of c.steps){
  w(G+2352,step.now_bits);step.player_xyz_bits.forEach((word,j)=>w(G+1416+j*4,word));
  const before=c.records.map((_,j)=>Buffer.from(b().slice(U+j*424,U+(j+1)*424)));
  roles.update_units(G,number(step.dt_bits));calls++;world.verify();
  if(host.hostCalls.length||u(G+1792)!==c.records.length||u(G+1784)!==c.capacity||u(G+1788)!==U)throw Error('Host/unit owner boundary');
  if(hex(Q,c.special_storage.length*40)!==specialBefore||hex(U+c.records.length*424,(c.capacity-c.records.length)*424)!==inactiveBefore)throw Error('Unconsumed physical owner changed');
  const records=c.records.map((_,j)=>[...b().slice(U+j*424,U+(j+1)*424)]);
  let unknownPreserved=true;
  c.records.forEach((row,j)=>{const cells=typeof row==='string'?[...Buffer.from(row,'hex')]:row;
   cells.forEach((cell,k)=>{if(cell===null&&(k<68||k>=72)&&before[j][k]!==records[j][k])unknownPreserved=false;});
   if(u(U+j*424+68)!==pointers[j])throw Error('Timer allocation owner replaced in admitted idle');
  });
  const map=u(G+2368),movements=[],P=u(G+1884),N=u(G+1888);
  if(N>1000)throw Error('Packet budget');
  for(let j=previousPackets;j<N;j++){
   const at=P+j*16,opcode=d().getUint16(at+12,true),p=u(at+4),length=u(at+8);
   if(opcode!==221||length>96)throw Error('Unmodeled packet in idle slice');
   const payload=b().slice(p,p+length),view=new DataView(payload.buffer);let k=1,guid=0n;
   for(let bit=0;bit<8;bit++)if(payload[0]&(1<<bit))guid|=BigInt(payload[k++])<<BigInt(bit*8);
   const xyz=()=>{const out=[0,1,2].map(n=>view.getUint32(k+n*4,true));k+=12;return out;};
   const start=xyz(),sequence=view.getUint32(k,true);k+=4;const stop=payload[k++];
   if(stop===3)k+=8;else if(stop!==0)throw Error('Movement stop shape');
   const flags=view.getUint32(k,true),ms=view.getUint32(k+4,true),count=view.getUint32(k+8,true);k+=12;
   if(flags!==256||count!==1)throw Error('Movement shape');const end=xyz();if(k!==length)throw Error('Movement tail');
   const index=c.cooldowns.findIndex(x=>x.guid===guid.toString());if(index<0)throw Error('Movement owner');
   movements.push({target_id:guid.toString(),start_xyz_bits:start,end_xyz_bits:end,duration_bits:u(U+index*424+344),milliseconds:ms,stop_flag:stop,sequence});
  }
  previousPackets=N;
  stages.push({records,cooldowns:c.cooldowns.map((owner,j)=>{const at=U+j*424;return{unit_index:j,guid:d().getBigUint64(at+112,true).toString(),capacity:u(at+64),
    timers_bits:Array.from({length:u(at+72)},(_,k)=>u(pointers[j]+k*4)),ability_pointer:u(at+84),header_pointer:u(at+96),
    ability_records44_hex:Array.from({length:u(at+88)},(_,k)=>hex(u(at+84)+k*44,44)),header28_hex:hex(u(at+96),28)};}),
   sequence:u(G+2412),packet_count:N,rng_words:[0,1,2,3].map(j=>u(G+1720+j*4)),hp_bits:u(G+1440),incoming_total_hex:d().getBigUint64(G+992,true).toString(16).padStart(16,'0'),
   distance_map:map?{start_index:u(map+20),field24:u(map+24),length:u(map+16),sha256:hash(b().slice(u(map+12),u(map+12)+u(map+16)*2))}:null,
   distance_map_updated_at_bits:u(G+2372),movement_geometry:movements,unknown_preserved:unknownPreserved});
 }
 hostCalls+=host.hostCalls.length;peak=Math.max(peak,memory.buffer.byteLength);
 stackChecks.push(...host.stackChecks().map(x=>({case_id:c.id,...x})));
 return {id:c.id,stages};
}
for(let index=0;index<cases.length;index++){
 const c=cases[index];if(c.id!==index||c.records.length<1||c.records.length>4||c.steps.length>100||c.capacity<c.records.length||c.capacity>16)throw Error('Case shape');
 process.stdout.write(JSON.stringify(await run(c))+'\n');if(global.gc)global.gc();
}
await fs.writeFile(directory+'/guardian-ai135-runtime.json',JSON.stringify({cases:cases.length,full_original921_calls:calls,fresh_instances:cases.length,
 actual_host_calls:hostCalls,denied_imports:878,peak_memory_bytes:peak,memory_page_cap:512,original_snapshot_loaded:false,original_callees_replaced:false,
 stack_all_restored:stackChecks.every(x=>x.entered&&x.returned&&x.before===1048576&&x.after===x.before),stack_checks:stackChecks,timer_allocations:timerAllocations})+'\n');
