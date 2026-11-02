// New component reader: fresh full1560 then explicit controlled1072 entries.
// No App, externref, snapshot, natural selection producer or original output
// is installed as input. Source header results never feed subsequent setup.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,inputFile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['initial_game','select_ability']);
const rows=JSON.parse(await fs.readFile(inputFile,'utf8'));
if(rows.length<1||rows.length>32)throw Error('Bounded case count');
let maxMemory=0,full1560=0,full1072=0;
for(const row of rows){
 const host=await prepared.fresh(),{memory,allocate,roles,hostCalls}=host;
 const dv=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer);
 const w=(p,v)=>dv().setUint32(p,v>>>0,true),r=p=>dv().getUint32(p,true);
 const G=allocate(2592),P=allocate(376),V=allocate(128),zone=Buffer.from(row.region_id),Z=allocate(zone.length,1);
 bytes().set(zone,Z);w(P+156,4);w(P+168,Z);w(P+172,zone.length);
 dv().setBigUint64(P+176,BigInt(row.object_id),true);dv().setBigUint64(P+184,BigInt(row.seed),true);
 dv().setUint8(P+344,row.class_byte);dv().setUint8(P+345,row.race_byte);
 dv().setUint8(V+120,1);w(V+116,row.flat_height_bits);w(V+32,0xffffffff);w(V+56,0xffffffff);
 const profileSources=()=>({ranked_count160:r(P+160),ranked_flag164:dv().getUint8(P+164),equipped19:Array.from({length:19},(_,i)=>r(P+260+i*4))});
 const profileBefore=profileSources();
 roles.initial_game(G,P,V);full1560++;
 const headers=()=>Object.fromEntries([2024,2028,2032,2048,2052,2056].map(o=>[o,r(G+o)]));
 const stages=[{role:1560,headers:headers(),ring968:[968,972,976,980].map(o=>r(G+o))}];
 for(const card of row.selections){
  if(!['upgrade','new','gold'].includes(card.variant))throw Error('Controlled card branch');
  const C=allocate(80);
  if(card.variant==='upgrade'){
   const K=allocate(Math.max(1,card.kinds.length),1);bytes().set(card.kinds,K);
   w(C+60,card.kinds.length);w(C+64,K);w(C+68,card.kinds.length);w(C+72,card.owned_index);
  }else if(card.variant==='new'){
   const A=card.definition_pointer;w(C+60,0x80000000);w(C+64,r(A+12));w(C+68,r(A+16));
  }else{w(C+60,0x80000004);w(C+64,card.gold);}
  w(C+76,card.tier);w(G+1904,1);w(G+1908,C);w(G+1912,1);
  // Explicit component input: full1072 needs a real phase2/kind0 candidate.
  // The natural XP/menu producer is not claimed by this header experiment.
  dv().setUint8(G+2587,2);dv().setUint8(G+2585,0);w(G+2376,1);
  roles.select_ability(G,0);full1072++;
  stages.push({role:1072,headers:headers(),phase2587:dv().getUint8(G+2587)});
 }
 if(hostCalls.length)throw Error('Host callback');
 process.stdout.write(JSON.stringify({id:row.id,stages,profileBefore,profileAfter:profileSources()})+'\n');
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/callback-source-owner-runtime.json`,JSON.stringify({cases:rows.length,fresh_instances:rows.length,full1560,full1072,max_memory_bytes:maxMemory,memory_cap_bytes:33554432,actual_host_calls:0,denied_imports:878,original_snapshot_loaded:false,application_start_called:false,externref_fabricated:false,source_headers_readonly:true,controlled_selection_entry:true,stack_guard_export:false},null,2)+'\n');
