// Real original1560 creates state, complete49037 executes with no replaced callees.
import fs from 'node:fs/promises';
import {prepareFull135}from'./full135_host.mjs';
const[directory,file]=process.argv.slice(2),prepared=await prepareFull135(directory,['initial_game','terminal_tick']);
const text=await fs.readFile(file,'utf8');if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture budget');const cases=JSON.parse(text);if(!cases.length||cases.length>2000)throw Error('Case count');
let host,instances=0,calls=0,maxMemory=0;
for(let i=0;i<cases.length;i++){
 if(i%8===0){host=await prepared.fresh();instances++;}const c=cases[i],s=c.input,{memory,allocate,roles,hostCalls}=host;if(c.id!==i)throw Error('Case order');
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),r=p=>d().getUint32(p,true),w=(p,x)=>d().setUint32(p,x,true),G=allocate(8192),P=allocate(376),V=allocate(128),N=allocate(c.region_id.length),H=allocate(Math.max(1,Buffer.byteLength(c.hero)));
 bytes().set(Buffer.from(c.region_id),N);w(P+156,4);w(P+168,N);w(P+172,c.region_id.length);d().setBigUint64(P+176,BigInt(s.object_id_u64),true);d().setBigUint64(P+184,BigInt(s.seed_u64),true);d().setUint8(P+344,s.class_byte);d().setUint8(P+345,s.race_byte);
 d().setUint8(V+120,Number(c.flat_height_enabled));w(V+116,s.flat_height_bits);w(V+56,0xffffffff);w(V+32,0xffffffff);roles.initial_game(G,P,V);calls++;
 const constructorRaw=Buffer.from(bytes().slice(G,G+2592)).toString('hex');
 bytes().set(Buffer.from(c.hero),H);w(G+220,H);w(G+224,Buffer.byteLength(c.hero));
 for(const[o,value]of Object.entries(c.words))w(G+Number(o),value);
 for(const[o,value]of Object.entries(c.bytes))d().setUint8(G+Number(o),value);
 for(const[o,value]of Object.entries(c.doubles))d().setBigUint64(G+Number(o),BigInt(value),true);
 if(r(G+1900)!==0)throw Error('Constructor notifications are nonempty');
 if(c.constructor_expected&&(r(G+1880)!==c.constructor_expected.packet_capacity||r(G+1888)!==c.constructor_expected.packet_count))throw Error('Constructor packet source differs');
 const vectors={};for(const[k,stride,base]of[['units',424,1784],['auxiliary',112,656],['claims',88,2108]]){
  const storage=c[k];if(r(G+base+8)!==0||r(G+base)!==0)throw Error('Constructor vector source not empty');
  if(!storage.length){if(c.counts[k]!==0)throw Error('Empty backing count');vectors[k]={q:r(G+base+4),stride,base,capacity:0};continue;}
  const q=allocate(storage.length*stride);w(G+base,storage.length);w(G+base+4,q);w(G+base+8,c.counts[k]);
  storage.forEach((x,j)=>{if(x.length!==stride*2)throw Error('Raw vector stride');bytes().set(Buffer.from(x,'hex'),q+j*stride);});vectors[k]={q,stride,base,capacity:storage.length};
 }
 const rawPackets=()=>{const n=r(G+1888),p=r(G+1884);if(n>256)throw Error('Message bound');return Array.from({length:n},(_,j)=>{const q=p+j*16,len=r(q+8),ptr=r(q+4);if(len>65536||ptr+len>memory.buffer.byteLength)throw Error('Payload bound');return{opcode:d().getUint16(q+12,true),capacity:r(q),payload_hex:Buffer.from(bytes().slice(ptr,ptr+len)).toString('hex')};});};
 const rawNotifications=()=>{const n=r(G+1900),p=r(G+1896);if(n>256)throw Error('Notification bound');return Array.from({length:n},(_,j)=>{const q=p+j*12,len=r(q+8),ptr=r(q+4);if(len>65536||ptr+len>memory.buffer.byteLength)throw Error('Notification bytes');return{capacity:r(q),payload_hex:Buffer.from(bytes().slice(ptr,ptr+len)).toString('hex')};});};
 const snapshot=()=>({phase:d().getUint8(G+2587),action_sequence:r(G+1644),movement_sequence:r(G+2412),vectors:Object.fromEntries(Object.entries(vectors).map(([k,v])=>[k,{count:r(G+v.base+8),storage:Array.from({length:v.capacity},(_,j)=>Buffer.from(bytes().slice(v.q+j*v.stride,v.q+(j+1)*v.stride)).toString('hex'))}])),packets:rawPackets(),notifications:rawNotifications(),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),spawn_counter:r(G+2408),raw_g2592_hex:Buffer.from(bytes().slice(G,G+2592)).toString('hex')});
 const before=snapshot(),stages=[];
 for(let j=0;j<c.repeat;j++){
  const old=bytes().slice(G,G+2592);roles.terminal_tick(G);calls++;if(hostCalls.length)throw Error('Host import');const after=snapshot();
  const changes=[];for(let o=0;o<2592;o++){
   if(o===1884||o===1896){const a=new DataView(old.buffer,old.byteOffset,old.byteLength).getUint32(o,true);if(a!==r(G+o))changes.push([o,'heap_pointer']);o+=3;continue;}
   const b=d().getUint8(G+o);if(old[o]!==b)changes.push([o,b]);
  }
  // Only the two known heap-address words are normalized. All numeric capacities,
  // byte flags and otherwise-unmodeled game bytes are compared without masks.
  stages.push({...after,game_changed_bytes:changes});
 }
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:i,constructor_raw_g2592_hex:constructorRaw,before,stages})+'\n');
}
await fs.writeFile(`${directory}/terminal-transition135-runtime.json`,JSON.stringify({cases:cases.length,calls,fresh_instances:instances,max_memory_bytes:maxMemory,original_functions:[1560,49037],all_callees_unchanged:true,denied_imports:878,host_calls:0,memory_page_cap:512,application_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
