// Full1063 nonfatal controlled fixtures. No application start or host API.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';
const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['incoming_damage']);
const cases=JSON.parse(await fs.readFile(casefile,'utf8'));
if(!cases.length||cases.length>512)throw Error('Fixture count outside budget');
const scalar=new DataView(new ArrayBuffer(4));
const number=b=>{scalar.setUint32(0,b,true);return scalar.getFloat32(0,true);};
const offsets={armor_1392_bits:1392,hp_1528_bits:1528,shield_1532_bits:1532,barrier_1536_bits:1536,
 shield_source_1344:1344,shield_source_remaining_1348_bits:1348,reserve_768_bits:768,
 absorbed_740_bits:740,maximum_shield_744_bits:744,last_hit_1648_bits:1648};
let host,instances=0,maxMemory=0;
for(let i=0;i<cases.length;++i){
  const c=cases[i];if(c.id!==i)throw Error('Fixture order');
  if(i%32===0){host=await prepared.fresh();++instances;}
  const {roles,memory,allocate,hostCalls}=host,G=allocate(5000);
  const raw=Buffer.from(c.map_id,'utf8'),p=allocate(Math.max(raw.length,1),1);
  new Uint8Array(memory.buffer,p,raw.length).set(raw);
  let v=new DataView(memory.buffer);const w=(offset,b)=>v.setUint32(G+offset,b>>>0,true);
  w(184,p);w(188,raw.length);v.setUint8(G+360,1);v.setUint8(G+361,1);
  v.setBigUint64(G+1336,1n,true);w(1360,c.max_hp_bits);w(1520,1);w(2344,c.state.now_bits);
  v.setUint8(G+2579,c.state.phase_2579);v.setUint8(G+2568,c.state.protection_2568);
  v.setUint8(G+2574,c.state.mode_2574);w(2532,c.state.wave_2532);
  for(const [name,offset]of Object.entries(offsets))w(offset,c.state[name]);
  roles.incoming_damage(G,number(c.amount_bits),0n,0,0,0);
  v=new DataView(memory.buffer);const actual={id:i};
  for(const [name,offset]of Object.entries(offsets))actual[name]=v.getUint32(G+offset,true);
  actual.incoming_total_992_bits=v.getBigUint64(G+992,true).toString(16).padStart(16,'0');
  actual.phase2579=v.getUint8(G+2579);
  if(hostCalls.length)throw Error('Original host API attempted');
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  process.stdout.write(JSON.stringify(actual)+'\n');
}
await fs.writeFile(`${directory}/incoming134-runtime.json`,JSON.stringify({
  case_count:cases.length,original_function:1063,original_full_function_executed:true,
  original_internal_callees_unchanged:true,original_allocator:91940,
  fresh_instances:instances,fresh_instance_every:32,max_memory_bytes:maxMemory,
  denied_function_imports:878,actual_host_calls:0,memory_limit_pages:512,node:process.version,
  full_game_started:false,application_start_called:false,network_used:false,user_saves_accessed:false,
},null,2)+'\n');
