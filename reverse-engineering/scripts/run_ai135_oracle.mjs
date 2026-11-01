// Complete fixed135 update_units921, every internal callee unchanged.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtureFile]=process.argv.slice(2),prepared=await prepareFull135(directory,['update_units']);
const text=await fs.readFile(fixtureFile,'utf8');if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture byte budget');
const cases=text.trim().split('\n').map(JSON.parse);if(cases.length>12000)throw Error('Case budget');
const offsets={armor_1392_bits:1568,armor_cap_1572_bits:1572,nearby_reduction_1444_bits:1624,
 hp_1528_bits:1440,shield_1532_bits:1444,barrier_1536_bits:1448,shield_source_1344:1344,
 shield_source_remaining_1348_bits:1348,reserve_768_bits:768,absorbed_740_bits:740,
 maximum_shield_744_bits:744,last_hit_1648_bits:1652};
const number=x=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,x,true);return d.getFloat32(0,true);};
let host,instances=0,maxMemory=0,count=0;
for(let i=0;i<cases.length;i++){
 const c=cases[i],s=c.input.incoming;if(c.id!==i)throw Error('Case identity');
 if(c.input.other_incoming_sources_absent!==true||c.input.incoming_item_effects.length)throw Error('Unmodeled incoming source domain');
 if(i%24===0){host=await prepared.fresh();instances++;}
 const {memory,roles,allocate,hostCalls}=host,G=allocate(8192),V=allocate(128);
 const d=()=>new DataView(memory.buffer),w=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw Error('u32');d().setUint32(p,x,true);};
 const b=(p,x)=>d().setUint8(p,x),read=p=>d().getUint32(p,true);
 const name=Buffer.from(s.map_id,'ascii'),N=allocate(Math.max(1,name.length),1);new Uint8Array(memory.buffer).set(name,N);w(G+184,N);w(G+188,name.length);
 w(G+2348,V);w(V+32,0xffffffff);w(V+56,0xffffffff);w(V+120,1);
 b(G+360,1);b(G+361,1);d().setBigUint64(G+1336,999n,true);w(G+1432,1);w(G+1536,c.max_hp_bits);w(G+2540,s.wave_2532);
 b(G+2587,s.phase_2579);b(G+2576,s.protection_2568);b(G+2582,s.mode_2574);b(G+2578,s.minimum_one_2578);w(G+2528,0);
 for(const [key,offset]of Object.entries(offsets))w(G+offset,s[key]);d().setFloat64(G+992,s.incoming_total_992,true);
 const records=c.input.records;if(records.length>512)throw Error('Unit budget');
 const U=allocate(Math.max(8,records.length*424));w(G+1784,records.length);w(G+1788,U);w(G+1792,records.length);
 records.forEach((x,j)=>{if(!/^[0-9a-f]{848}$/.test(x))throw Error('424B input');new Uint8Array(memory.buffer).set(Buffer.from(x,'hex'),U+j*424);});
 const vector=(rows,stride,cap,ptr,len,write)=>{const p=allocate(Math.max(8,rows.length*stride));w(G+cap,rows.length);w(G+ptr,p);w(G+len,rows.length);rows.forEach((x,j)=>write(p+j*stride,x));};
 vector(s.buffs,32,1704,1708,1712,(p,x)=>{w(p+8,x.tag);w(p+12,x.value12_bits);w(p+20,x.spell_id);w(p+24,x.expires24_bits);});
 vector(s.modifiers,36,2048,2052,2056,(p,x)=>{w(p,x.tag);b(p+4,x.byte4);b(p+5,x.byte5);});
 const steps=[];
 for(const step of c.steps){
  w(G+2352,step.now_bits);step.player_xyz_bits.forEach((x,j)=>w(G+1416+j*4,x));
  roles.update_units(G,number(step.dt_bits));
  const output={records:records.map((_,j)=>Buffer.from(new Uint8Array(memory.buffer,U+j*424,424)).toString('hex'))};
  for(const [key,offset]of Object.entries(offsets))output[key]=read(G+offset);
  output.incoming_total_992_bits=d().getBigUint64(G+992,true).toString(16).padStart(16,'0');output.phase2579=d().getUint8(G+2587);
  output.queued_packets=read(G+1888);output.world_reference=read(V);steps.push(output);count++;
 }
 if(hostCalls.length)throw Error('Original host call attempted');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:i,steps})+'\n');
}
await fs.writeFile(`${directory}/ai135-runtime.json`,JSON.stringify({case_count:cases.length,steps:count,
 original_function:921,original_internal_callees_unchanged:true,original_allocator:91941,fresh_instances:instances,
 fresh_every:24,max_memory_bytes:maxMemory,actual_host_calls:0,denied_function_imports:878,memory_page_cap:512,
 node:process.version,application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false},null,2)+'\n');
