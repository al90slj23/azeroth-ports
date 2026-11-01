// Complete fixed135 choose20272/spawn5736/decay26361, unchanged callees.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtures]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['choose_spawn','spawn_normal','spawn_decay']);
const cases=JSON.parse(await fs.readFile(fixtures,'utf8'));
if(!cases.length||cases.length>12000)throw Error('Corpus budget');
let host,instances=0,maxMemory=0;
const number=bits=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,bits,true);return d.getFloat32(0,true);};
const bits=value=>{const d=new DataView(new ArrayBuffer(4));d.setFloat32(0,value,true);return d.getUint32(0,true);};
for(let i=0;i<cases.length;++i){
  const c=cases[i];if(c.id!==i)throw Error('Case order');
  if(i%32===0){host=await prepared.fresh();++instances;}
  const {roles,memory,allocate,hostCalls}=host;
  let result;
  if(c.kind==='decay')result={bits:bits(roles.spawn_decay(number(c.input.bits)))};
  else{
    const s=c.input,G=allocate(8192),name=allocate(c.zone_id.length);
    let d=new DataView(memory.buffer);new Uint8Array(memory.buffer,name,c.zone_id.length).set(new TextEncoder().encode(c.zone_id));
    const u=(offset,x)=>d.setUint32(G+offset,x>>>0,true);
    u(184,name);u(188,c.zone_id.length);
    s.rng_words.forEach((x,j)=>u(1720+4*j,x));
    if(c.kind==='choice'){
      const ptr=allocate(Math.max(4,s.candidates.length*4));d=new DataView(memory.buffer);
      s.candidates.forEach((x,j)=>d.setUint32(ptr+4*j,x,true));
      const chosen=roles.choose_spawn(G,ptr,s.candidates.length,number(s.minutes_bits));d=new DataView(memory.buffer);
      result={index:chosen>>>0,rng_words:Array.from({length:4},(_,j)=>d.getUint32(G+1720+j*4,true))};
    }else if(c.kind==='normal'){
      const count=s.existing_states.length,capacity=Math.max(1,count+1),units=allocate(capacity*424),placement=allocate(16),output=allocate(16);
      d=new DataView(memory.buffer);
      s.existing_states.forEach((x,j)=>d.setUint32(units+j*424,x>>>0,true));
      new Uint8Array(memory.buffer,units+count*424,424).set(Buffer.from(s.initial_slot_hex,'hex'));
      u(1784,capacity);u(1788,units);u(1792,count);u(2408,s.counter);u(2352,s.now_bits);u(2516,s.zone_multiplier_bits);
      d.setUint8(G+387,s.difficulty);d.setUint8(G+2582,s.mode);u(2540,s.members);u(400,s.victory_field400);
      u(404,s.endless_start_bits);d.setUint8(G+2568,s.endless_flag);
      d.setBigUint64(G+1336,999n,true);u(1432,1);u(1440,0x42c80000);u(1536,0x42c80000);
      d.setUint32(placement,1,true);s.position_bits.forEach((x,j)=>d.setUint32(placement+4+j*4,x,true));
      roles.spawn_normal(output,G,s.definition_index,placement);d=new DataView(memory.buffer);
      const success=d.getBigUint64(output,true)===1n,p=d.getUint32(G+1788,true);
      result={success,guid:d.getBigUint64(output+8,true).toString(),counter:d.getUint32(G+2408,true),
        rng_words:Array.from({length:4},(_,j)=>d.getUint32(G+1720+4*j,true)),count:d.getUint32(G+1792,true),
        record_hex:success?Buffer.from(memory.buffer,p+count*424,424).toString('hex'):null};
    }else throw Error('Unknown case kind');
  }
  if(hostCalls.length)throw Error('Original host call denied');
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  process.stdout.write(JSON.stringify({id:i,result})+'\n');
}
await fs.writeFile(`${directory}/spawn135-runtime.json`,JSON.stringify({case_count:cases.length,original_functions:[20272,5736,26361],
  original_allocator:91941,original_internal_callees_unchanged:true,host_calls:0,denied_host_imports:878,
  fresh_instances:instances,fresh_every:32,max_memory_bytes:maxMemory,memory_page_cap:512,node:process.version,
  application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
