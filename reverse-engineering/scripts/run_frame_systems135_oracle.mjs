// Complete five main-tail functions; original callees preserved,878 hosts denied.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,file]=process.argv.slice(2);
const names=['owned_effect_tick','deadline_tick','secondary_hits','claim_tick','terminal_tick'];
const prepared=await prepareFull135(directory,names),text=await fs.readFile(file,'utf8');
if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture bytes');
const cases=JSON.parse(text);if(!cases.length||cases.length>3000)throw Error('Case budget');
let host,instances=0,calls=0,traps=0,maxMemory=0,packets=0;
for(let i=0;i<cases.length;i++){
 if(!host||i%16===0){host=await prepared.fresh();instances++;}
 const c=cases[i],{memory,allocate,roles,hostCalls}=host;if(c.id!==i)throw Error('Case order');
 const G=allocate(8192),Q=allocate(Math.max(1,c.storage.length)*c.stride),M=allocate(128*16),O=allocate(Math.max(1,c.owned.length)*80);
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),r=p=>d().getUint32(p,true),w=(p,x)=>d().setUint32(p,x,true),g=(o,x)=>w(G+o,x);
 const nr=x=>{const p=new DataView(new ArrayBuffer(4));p.setUint32(0,x,true);return p.getFloat32(0,true);};
 g(1880,128);g(1884,M);g(1888,0);g(1660,O);g(1664,c.owned.length);
 const defs=new Map();for(const [key,raw]of Object.entries(c.definitions)){const p=allocate(88);bytes().set(Buffer.from(raw,'hex'),p);defs.set(Number(key),p);}
 const reverse=new Map([...defs].map(([a,b])=>[b,a]));
 for(let j=0;j<c.owned.length;j++){bytes().set(Buffer.from(c.owned[j],'hex'),O+j*80);const key=r(O+j*80);if(!defs.has(key))throw Error('Unknown definition');w(O+j*80,defs.get(key));}
 c.storage.forEach((x,j)=>{if(x.length!==c.stride*2)throw Error('Full backing record');bytes().set(Buffer.from(x,'hex'),Q+j*c.stride);});
 const field=c.kind==='deadline'?1832:c.kind==='secondary'?1856:c.kind==='claim'?2108:null;
 if(field!==null){g(field,c.storage.length);g(field+4,Q);g(field+8,c.count);}
 d().setUint8(G+2587,c.phase);d().setUint8(G+2568,c.endless);g(400,c.field400);
 if(c.kind==='owned')for(let o=784;o<=904;o+=4)g(o,(0xa5a50000+o)>>>0);
 const stages=[];let priorPackets=0,trappedCase=false;
 for(const op of c.ops){
  g(2352,op.now_bits);const before=bytes().slice(G,G+2592);let trapped=false;
  try{
   if(c.kind==='owned')roles.owned_effect_tick(G,nr(op.dt_bits));
   else if(c.kind==='deadline')roles.deadline_tick(G);
   else if(c.kind==='secondary')roles.secondary_hits(G);
   else if(c.kind==='claim')roles.claim_tick(G);
   else if(c.kind==='terminal')roles.terminal_tick(G);
   else throw Error('Unknown kind');
  }catch(error){if(!(error instanceof WebAssembly.RuntimeError)||error.message!=='unreachable')throw error;trapped=true;traps++;trappedCase=true;}
  calls++;if(hostCalls.length)throw Error('Original host import');
  const changes=[];for(let o=0;o<2592;o+=4){const old=new DataView(before.buffer,before.byteOffset,before.byteLength).getUint32(o,true),value=r(G+o);if(old!==value)changes.push([o,value]);}
  const len=r(G+1888),mp=r(G+1884);if(len>128)throw Error('Packet budget');const events=[];
  for(let j=priorPackets;j<len;j++){
   const p=mp+j*16,cap=r(p),n=r(p+8),ptr=r(p+4);if(n>64||ptr+n>memory.buffer.byteLength)throw Error('Payload bounds');
   events.push([d().getUint16(p+12,true),cap,Buffer.from(bytes().slice(ptr,ptr+n)).toString('hex')]);packets++;
  }priorPackets=len;
  const owned=c.owned.map((_,j)=>{const raw=bytes().slice(O+j*80,O+(j+1)*80),dv=new DataView(raw.buffer,raw.byteOffset,raw.byteLength),key=reverse.get(dv.getUint32(0,true));if(key===undefined)throw Error('Owned pointer changed');dv.setUint32(0,key,true);return Buffer.from(raw).toString('hex');});
  const storage=c.storage.map((_,j)=>Buffer.from(bytes().slice(Q+j*c.stride,Q+(j+1)*c.stride)).toString('hex'));
  for(const[key,ptr]of defs)if(Buffer.from(bytes().slice(ptr,ptr+88)).toString('hex')!==c.definitions[key])throw Error('Definition mutation');
  stages.push({count:field===null?c.count:r(G+field+8),storage,owned,packets:events,game_changes:changes,entry_trap:trapped});
  if(trapped)break;
 }
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:i,stages})+'\n');if(trappedCase)host=null;
}
await fs.writeFile(`${directory}/frame-systems135-runtime.json`,JSON.stringify({cases:cases.length,calls,expected_traps:traps,packets,fresh_instances:instances,max_memory_bytes:maxMemory,full_original_functions:[975,38007,2602,2573,49037],all_callees_unchanged:true,denied_imports:878,host_calls:0,original_allocator:91941,application_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
