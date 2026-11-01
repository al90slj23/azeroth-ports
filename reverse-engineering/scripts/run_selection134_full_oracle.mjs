// Complete original0.134.0 selection1073 including reached original callees.
// Synthetic empty auxiliary state; real0.134 field positions, no start/host.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';
const [directory,caseFile]=process.argv.slice(2),prepared=await prepareFull134(directory,['select_ability']);
const text=await fs.readFile(caseFile,'utf8');if(text.length>8*1024*1024)throw new Error('Fixture byte budget exceeded');
const fixtures=text.trim().split('\n').filter(Boolean).map(JSON.parse);
if(!fixtures.length||fixtures.length>2000)throw new Error('Fixture count outside budget');
let session,instances=0,maxMemory=0;
for(let i=0;i<fixtures.length;++i) {
  if(i%32===0){session=await prepared.fresh();++instances;}
  const c=fixtures[i];if(c.id!==i||c.kinds.length>32)throw new Error('Fixture profile differs');
  const {memory,allocate,roles,hostCalls}=session,G=allocate(8192),owned=allocate(80),candidate=allocate(80);
  const v=()=>new DataView(memory.buffer),u32=(p,value)=>v().setUint32(p,value>>>0,true),u8=(p,value)=>v().setUint8(p,value);
  const def=5463472,namePtr=v().getUint32(def+12,true),nameLen=v().getUint32(def+16,true);
  if(Buffer.from(new Uint8Array(memory.buffer,namePtr,nameLen)).toString()!=='cleave'||v().getUint8(def+84)!==5)throw new Error('Latest cleave definition differs');
  u8(G+360,1);u8(G+361,1);u32(G+1520,1);u8(G+2579,c.phase);u8(G+2577,0);u8(G+2574,0);u32(G+2368,1);
  if(c.variant==='upgrade') {
    const raw=Buffer.from(c.input_hex,'hex');if(raw.length!==80)throw new Error('Owned record size differs');
    new Uint8Array(memory.buffer,owned,80).set(raw);u32(G+1652,1);u32(G+1656,owned);u32(G+1660,1);
    const kinds=allocate(Math.max(1,c.kinds.length),1);new Uint8Array(memory.buffer,kinds,c.kinds.length).set(c.kinds);
    u32(candidate+60,c.kinds.length);u32(candidate+64,kinds);u32(candidate+68,c.kinds.length);
    u32(candidate+72,c.owned_index);u32(candidate+76,c.tier);
  } else if(c.variant==='new') {
    u32(candidate+60,0x80000000);u32(candidate+64,namePtr);u32(candidate+68,nameLen);u32(candidate+76,0);
  } else throw new Error('Unsupported fixture variant');
  u32(G+1896,1);u32(G+1900,candidate);u32(G+1904,1);
  roles.select_ability(G,0);
  if(hostCalls.length)throw new Error('Original attempted a host call');
  const p=v().getUint32(G+1656,true),count=v().getUint32(G+1660,true);
  if(count!==1||p+80>memory.buffer.byteLength)throw new Error('Result owned vector outside fixture domain');
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  const result={id:i,record_hex:Buffer.from(new Uint8Array(memory.buffer,p,80)).toString('hex'),owned_count:count,
    phase2579:v().getUint8(G+2579),selection_kind2577:v().getUint8(G+2577),pending2368:v().getUint32(G+2368,true),
    candidate_count1904:v().getUint32(G+1904,true)};
  process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/selection134-runtime.json`,JSON.stringify({version:'0.134.0',build:'983346a7',
  complete_original1073_executed:true,original_internal_callees:true,dependency_shims:[],
  actual_host_calls:0,denied_function_imports:878,application_start_called:false,full_game_started:false,
  cases:fixtures.length,fresh_instances:instances,maximum_memory_bytes:maxMemory,
  scope:'Synthetic empty auxiliaries and pending2368=1; candidate generation and nonempty modifiers/loot are not covered.'},null,2)+'\n');
