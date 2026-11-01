// Actual complete0.134.0 function914; only research export section is changed.
// All host APIs are denied; neither application start export is called.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';

const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['damage']);
const cases=JSON.parse(await fs.readFile(casefile,'utf8'));
if(!cases.length||cases.length>2048)throw Error('Fixture count outside budget');
const scalar=new DataView(new ArrayBuffer(4));
const number=bits=>{scalar.setUint32(0,bits>>>0,true);return scalar.getFloat32(0,true);};
let host=null,instances=0,attemptedHostCalls=[],maxMemory=0;
for(let n=0;n<cases.length;++n) {
  if(n%32===0){host=await prepared.fresh();++instances;}
  const c=cases[n],{memory,allocate,roles,hostCalls}=host;
  const G=allocate(5000),U=allocate(424);
  let v=new DataView(memory.buffer);
  const w=(p,b)=>v.setUint32(p,b>>>0,true),r=p=>v.getUint32(p,true);
  const idAt=definition=>{
    const p=r(definition+12),length=r(definition+16);
    return Buffer.from(memory.buffer,p,length).toString('utf8');
  };
  // Source-initialized table and enemy definition are checked before use.
  const table=[];
  for(let i=0;i<114;++i){const p=5463472+i*88;table.push([idAt(p),r(p+44)]);}
  if(!table.some(([id,spell])=>id==='fireball'&&spell===133)
      ||!table.some(([id,spell])=>id==='cleave'&&spell===845))throw Error('Current declaration bindings differ');
  // The definition's complete bytes are independently pinned by the checker;
  // no speculative name/field layout is used to construct its address here.
  if(!Buffer.from(memory.buffer,5411616,72).equals(Buffer.from(c.enemy_definition_hex,'hex')))
    throw Error('Current72B enemy definition differs');
  w(G+1780,U);w(G+1784,1);v.setUint8(G+2579,c.phase??1);
  w(G+2344,c.now_bits);w(G+1360,0x42c80000);w(G+1364,0x3f800000);
  w(G+1376,0x40000000);w(G+1520,1);v.setUint8(G+360,1);v.setUint8(G+361,1);
  v.setBigUint64(U+112,1n,true);w(U+288,c.hp_bits);w(U+292,c.max_hp_bits);
  w(U+244,-1);w(U+64,-1);w(U+40,-1);w(U+284,5411616);
  c.rng.forEach((b,i)=>w(G+1712+4*i,b));
  for(const [offset,b]of Object.entries(c.unit_overrides||{}))w(U+Number(offset),b);
  for(const [offset,b]of Object.entries(c.state_overrides||{}))w(G+Number(offset),b);
  if(c.items?.length){
    const pointer=allocate(c.items.length*8,4);v=new DataView(memory.buffer);
    w(G+2020,pointer);w(G+2024,c.items.length);
    c.items.forEach(([tag,b],i)=>{w(pointer+8*i,tag);w(pointer+8*i+4,b);});
  }
  if(c.spell_modifiers?.length){
    const pointer=allocate(c.spell_modifiers.length*36,4);v=new DataView(memory.buffer);
    w(G+2044,pointer);w(G+2048,c.spell_modifiers.length);
    for(let i=0;i<c.spell_modifiers.length;++i){
      const [tag,id,b12,b16]=c.spell_modifiers[i],raw=Buffer.from(id,'utf8');
      const p=allocate(Math.max(1,raw.length),1);v=new DataView(memory.buffer);
      new Uint8Array(memory.buffer,p,raw.length).set(raw);
      const record=pointer+36*i;w(record,tag);w(record+4,p);w(record+8,raw.length);
      w(record+12,b12);w(record+16,b16);
    }
  }
  const result={id:c.id};const hostStart=hostCalls.length;
  try{
    roles.damage(G,BigInt(c.target_id??1),number(c.amount_bits),c.spell_id??133,2,0,0);
    result.completed=true;
  }catch(error){result.completed=false;result.error_class=error.constructor.name;result.error=String(error);}
  v=new DataView(memory.buffer);
  for(const [key,offset]of Object.entries({hp_bits:288,marker:0,duration_bits:344,
      afflicted_240:240,death_time_bits:4,movement_time_bits:340}))result[key]=r(U+offset);
  result.accounted_total_bits=v.getBigUint64(G+984,true).toString(16).padStart(16,'0');
  result.rng=Array.from({length:4},(_,i)=>r(G+1712+4*i));
  result.host_calls=hostCalls.slice(hostStart);attemptedHostCalls.push(...result.host_calls);
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  if(result.host_calls.length)throw Error('Host call attempted; inspect controlled panic separately');
  process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/combat134-runtime.json`,JSON.stringify({
  case_count:cases.length,fresh_instances:instances,fresh_instance_every:32,
  original_function:914,original_full_function_executed:true,original_allocator:91940,
  actual_host_calls:attemptedHostCalls,import_count:878,max_memory_bytes:maxMemory,
  memory_limit_pages:512,node:process.version,full_game_started:false,network_used:false,
  user_saves_accessed:false,application_start_called:false,
},null,2)+'\n');
