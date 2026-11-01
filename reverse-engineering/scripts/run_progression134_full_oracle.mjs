// Complete current4630 with all reached original internal callees unchanged.
// Synthetic paused phase3 uses the real guard to skip next-choice2159 only.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';

const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['gain_experience']);
const raw=await fs.readFile(casefile,'utf8');
if(raw.length>8*1024*1024)throw Error('Corpus byte budget');
const cases=raw.trim().split('\n').filter(Boolean).map(JSON.parse);
if(!cases.length||cases.length>4000)throw Error('Corpus case budget');
let host=null,instances=0,maxMemory=0,hostCount=0;
for(let i=0;i<cases.length;++i){
  const c=cases[i];
  if(c.id!==i||[...Object.values(c.state),c.amount].some(x=>!Number.isInteger(x)||x<0||x>0xffffffff))
    throw Error('Invalid integer fixture');
  if(i%32===0){host=await prepared.fresh();++instances;}
  const {roles,memory,allocate,hostCalls}=host,G=allocate(5000);
  let v=new DataView(memory.buffer);
  v.setUint8(G+360,1);v.setUint8(G+361,1);
  v.setUint32(G+1520,c.state.level,true);v.setUint32(G+1524,c.state.xp,true);
  v.setUint32(G+2368,c.state.pending_upgrades,true);v.setUint8(G+2579,3);
  v.setBigUint64(G+1336,1n,true);
  roles.gain_experience(G,c.amount);
  v=new DataView(memory.buffer);
  if(hostCalls.length)throw Error('Original host API attempted');
  const state={level:v.getUint32(G+1520,true),xp:v.getUint32(G+1524,true),pending_upgrades:v.getUint32(G+2368,true)};
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);hostCount+=hostCalls.length;
  process.stdout.write(JSON.stringify({id:i,state,phase2579:v.getUint8(G+2579)})+'\n');
}
await fs.writeFile(`${directory}/progression134-runtime.json`,JSON.stringify({
  case_count:cases.length,original_function:4630,original_full_function_executed:true,
  original_internal_callees_unchanged:true,original_allocator:91940,dependency_shims:[],
  fresh_instances:instances,fresh_instance_every:32,max_memory_bytes:maxMemory,memory_limit_pages:512,
  actual_host_calls:hostCount,denied_function_imports:878,node:process.version,
  fixture_phase:3,next_choice2159_executed:false,full_game_started:false,
  application_start_called:false,network_used:false,user_saves_accessed:false,
},null,2)+'\n');
