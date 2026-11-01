// Full1371 command7 → original35514/25472 and26200; no rewritten callee.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,caseFile]=process.argv.slice(2),prepared=await prepareFull135(directory,['command']);
const text=await fs.readFile(caseFile,'utf8');if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture bytes');
const cases=JSON.parse(text);if(!cases.length||cases.length>5000)throw Error('Case budget');
let host,instances=0,calls=0,maxMemory=0,movements=0;
for(let i=0;i<cases.length;i++){
 if(i%24===0){host=await prepared.fresh();instances++;}
 const c=cases[i];if(c.id!==i)throw Error('Case order');const {memory,allocate,roles,hostCalls}=host;
 const view=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),r=p=>view().getUint32(p,true),u=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw Error('u32');view().setUint32(p,x,true);};
 const C=allocate(8192),G=C+16,V=allocate(128),U=allocate(Math.max(424,c.records.length*424)),A=allocate(16);
 view().setBigUint64(G,BigInt(c.discriminant),true);u(G+2348,V);u(V+32,0xffffffff);u(V+56,0xffffffff);u(V+120,1);
 u(G+1784,c.records.length);u(G+1788,U);u(G+1792,c.records.length);c.records.forEach((x,j)=>{if(x.length!==848)throw Error('424B');bytes().set(Buffer.from(x,'hex'),U+j*424);});
 u(G+660,8);u(G+664,0);u(G+2112,8);u(G+2116,0);u(G+1884,4);u(G+1896,4);
 u(G+2412,c.sequence);view().setUint8(G+2582,c.mode);view().setUint8(G+2587,c.initial_phase);[1,2,3,4].forEach((x,j)=>u(G+1720+j*4,x));u(A,7);
 const projection=[],rawPackets=[];let previousPackets=0;
 for(const step of c.steps){
  u(G+2352,step.now_bits);view().setUint8(A+4,step.payload_byte);roles.command(C,A);calls++;
  const n=r(G+1888),p=r(G+1884);if(n>4096)throw Error('Packet budget');const events=[],payloads=[];
  for(let j=previousPackets;j<n;j++){
   const z=p+j*16,length=r(z+8),type=view().getUint16(z+12,true),payload=bytes().slice(r(z+4),r(z+4)+length);
   if(type!==221||length<18||length>64)throw Error('Unexpected movement packet');
   const mask=payload[0];let k=1,guid=0n;for(let b=0;b<8;b++)if(mask&(1<<b)){if(k>=length)throw Error('PackedGUID bounds');guid|=BigInt(payload[k++])<<BigInt(8*b);}
   if(k+17>length)throw Error('Packet header bounds');const d=new DataView(payload.buffer,payload.byteOffset,payload.byteLength),seq=d.getUint32(k+12,true),flag=payload[k+16];
   if(flag!==0&&flag!==1)throw Error('Stopflag');
   if((flag===1&&length!==k+17)||(flag===0&&length!==k+41))throw Error('Movement length');
   events.push({guid:guid.toString(),sequence:seq,stop_flag:flag});payloads.push({type,length,payload_hex:Buffer.from(payload).toString('hex')});movements++;
  }
  previousPackets=n;rawPackets.push(payloads);
  const ptr=r(G+1788),count=r(G+1792);if(count!==c.records.length)throw Error('NPC count changed');
  projection.push({phase:view().getUint8(G+2587),sequence:r(G+2412),records:Array.from({length:count},(_,j)=>Buffer.from(bytes().slice(ptr+j*424,ptr+(j+1)*424)).toString('hex')),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),events,packet_count:n,notifications:r(G+1900),auxiliary_count:r(G+664),claims_count:r(G+2116)});
 }
 if(hostCalls.length)throw Error('Original host import');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:i,projection,raw_packets:rawPackets})+'\n');
}
await fs.writeFile(`${directory}/movement-pause135-runtime.json`,JSON.stringify({cases:cases.length,command1371_calls:calls,movement221_packets:movements,original_callees:[35514,25472,26200,45845,27457,15916,45628],original_callees_unchanged:true,original_allocator:91941,fresh_instances:instances,max_memory_bytes:maxMemory,host_calls:0,denied_imports:878,memory_page_cap:512,application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false},null,2)+'\n');
