// Complete official0.135.1 function2159 with every original callee unchanged.
// Synthetic allocated state, mode1, flag2566=0; no app start; every host throws.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,casesFile]=process.argv.slice(2);
if(!directory||!casesFile)throw Error('Expected approved module directory and corpus');
const prepared=await prepareFull135(directory,['generate_choices']);
const text=await fs.readFile(casesFile,'utf8');
if(Buffer.byteLength(text)>32*1024*1024)throw Error('Candidate fixture byte budget');
const cases=text.trim().split('\n').filter(Boolean).map(JSON.parse);
if(!cases.length||cases.length>6000)throw Error('Candidate fixture count budget');
let host,instances=0,maxMemory=0,actualHostCalls=0;
const encoder=new TextEncoder();
for(let index=0;index<cases.length;++index){
  if(index%32===0){host=await prepared.fresh();++instances;}
  const c=cases[index],s=c.input;
  if(c.id!==index)throw Error('Fixture identity/order differs');
  const {memory,allocate,roles,hostCalls}=host;
  const view=()=>new DataView(memory.buffer);
  const bytes=()=>new Uint8Array(memory.buffer);
  const u32=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw Error('Invalid u32');view().setUint32(p,x,true);};
  const u8=(p,x)=>{if(!Number.isInteger(x)||x<0||x>255)throw Error('Invalid u8');view().setUint8(p,x);};
  const read32=p=>view().getUint32(p,true);
  const checkedSpan=(pointer,length,maximum)=>{
    if(!Number.isInteger(pointer)||!Number.isInteger(length)||pointer<0||length<0||length>maximum||pointer+length>memory.buffer.byteLength)
      throw Error('Original metadata span exceeds limits');
    return new Uint8Array(memory.buffer,pointer,length);
  };
  const readId=(pointer,length)=>{
    const result=Buffer.from(checkedSpan(pointer,length,128)).toString('ascii');
    if(!/^[a-z][a-z0-9_]*$/.test(result))throw Error('Original ability ID differs from finite domain');
    return result;
  };
  const G=allocate(8192);
  // All zero-length vectors use valid aligned dangling pointers. Nonempty
  // vectors below receive original allocator storage and exact capacities.
  for(const [cap,ptr,len,align] of [[1656,1660,1664,4],[1904,1908,1912,4],
    [1952,1956,1960,4],[2024,2028,2032,4],[2048,2052,2056,4],
    [2084,2088,2092,4],[2096,2100,2104,4],[1892,1896,1900,4]]){
    u32(G+cap,0);u32(G+ptr,align);u32(G+len,0);
  }
  u8(G+360,s.class_byte);u8(G+361,1);
  u32(G+1432,s.level);u32(G+1584,s.luck_bits);u32(G+1544,s.cooldown_bits);
  u8(G+275,s.flag275);u8(G+2581,s.flag2573);
  u8(G+2582,1);u8(G+2566,0);u8(G+2587,s.phase);u8(G+2585,255);
  u32(G+2400,s.generation_counter);
  if(s.rng_words.length!==4)throw Error('Four RNG words required');
  s.rng_words.forEach((x,i)=>u32(G+1720+i*4,x));
  const vector=(entries,stride,cap,ptr,len,write)=>{
    if(!Array.isArray(entries)||entries.length>128)throw Error('Vector fixture budget');
    if(!entries.length)return;
    const p=allocate(entries.length*stride,4);
    u32(G+cap,entries.length);u32(G+ptr,p);u32(G+len,entries.length);
    entries.forEach((entry,i)=>write(p+i*stride,entry));
  };
  const writeString=(p,value,capacity)=>{
    if(typeof value!=='string'||!/^(?:rank:)?[a-z][a-z0-9_]*$/.test(value))throw Error('Invalid fixture ID/key');
    const raw=encoder.encode(value);if(raw.length>128)throw Error('Fixture ID byte budget');
    const name=allocate(raw.length,1);bytes().set(raw,name);
    if(capacity){u32(p,raw.length);u32(p+4,name);u32(p+8,raw.length);}
    else{u32(p,name);u32(p+4,raw.length);}
  };
  vector(s.owned,80,1656,1660,1664,(p,item)=>{
    const raw=Buffer.from(item.record_hex,'hex');
    if(raw.length!==80||!/^[0-9a-f]{160}$/.test(item.record_hex))throw Error('Exact owned80B fixture required');
    bytes().set(raw,p);
    const def=read32(p);
    if(def<5467428||def>=5477460||(def-5467428)%88!==0)throw Error('Owned definition outside pinned table');
    if(readId(read32(def+12),read32(def+16))!==item.ability_id)throw Error('Owned definition ID differs');
  });
  vector(s.blocked_ids,8,2084,2088,2092,(p,id)=>writeString(p,id,false));
  vector(s.banished_keys,12,2096,2100,2104,(p,key)=>writeString(p,key,true));
  vector(s.effects,8,2024,2028,2032,(p,e)=>{u8(p,e.kind);u32(p+4,e.value_bits);});
  vector(s.summons,36,2048,2052,2056,(p,e)=>{
    u32(p,e.tag);
    if(e.tag===42){const object=allocate(64);u8(object+41,e.state41);u32(p+4,object);}
  });
  roles.generate_choices(G,0,s.third_arg);
  if(hostCalls.length)throw Error('Original attempted host API');
  const count=read32(G+1912),pointer=read32(G+1908);
  if(count<1||count>4)throw Error('Candidate count outside ordinary domain');
  checkedSpan(pointer,count*80,320);
  const candidates=[];
  for(let i=0;i<count;++i){
    const p=pointer+i*80,tag=read32(p+60),candidate={variant:'',tier:read32(p+76),ability_id:'',owned_index:0,kinds:[],gold:0};
    if(tag===0x80000000){
      candidate.variant='new';candidate.ability_id=readId(read32(p+64),read32(p+68));
    }else if(tag<0x80000000||tag===0x80000001){
      candidate.variant='upgrade';candidate.owned_index=read32(p+72);
      const n=read32(G+1664),ownedPointer=read32(G+1660);
      if(candidate.owned_index>=n)throw Error('Upgrade owned index outside original vector');
      const def=read32(ownedPointer+candidate.owned_index*80);
      candidate.ability_id=readId(read32(def+12),read32(def+16));
      candidate.kinds=Array.from(checkedSpan(read32(p+64),read32(p+68),5));
      if(candidate.kinds.some(k=>k>4))throw Error('Upgrade kind outside recovered domain');
    }else if(tag===0x80000004){
      candidate.variant='gold';candidate.gold=read32(p+64);
    }else throw Error(`Unspecified candidate variant0x${tag.toString(16)}`);
    if(candidate.tier>4)throw Error('Candidate tier outside recovered domain');
    candidates.push(candidate);
  }
  const result={id:index,candidates,rng_words:[0,1,2,3].map(i=>read32(G+1720+i*4)),
    phase2587:view().getUint8(G+2587),selection_kind2585:view().getUint8(G+2585),
    generation_counter2400:read32(G+2400),candidate_count1912:count,
    host_calls:hostCalls.length,memory_bytes:memory.buffer.byteLength,instance_count:instances};
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);actualHostCalls+=hostCalls.length;
  process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/candidates135-runtime.json`,JSON.stringify({
  version:'0.135.1',build:'0898d5e3',original_function:2159,complete_original2159_executed:true,
  original_internal_callees_unchanged:true,original_allocator:91941,dependency_shims:[],
  case_count:cases.length,fresh_instances:instances,fresh_instance_every:32,fresh_allocated_game_state_per_case:true,
  maximum_memory_bytes:maxMemory,memory_limit_pages:512,actual_host_calls:actualHostCalls,
  denied_function_imports:878,node:process.version,mode2582:1,flag2566:0,
  application_start_called:false,full_game_started:false,network_used:false,user_saves_accessed:false,
  scope:'Ordinary kind0 candidate metadata, RNG and three phase/counter fields; allocated UI strings are not compared.'
},null,2)+'\n');
