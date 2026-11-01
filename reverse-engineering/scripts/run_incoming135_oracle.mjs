// Fixed135 complete effectivearmor27375/incoming1073; every host import throws.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtureFile]=process.argv.slice(2);
const prepared=await prepareFull135(directory,['effective_armor','incoming_damage']);
const text=await fs.readFile(fixtureFile,'utf8');if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture byte budget');
const cases=text.trim().split('\n').map(JSON.parse);if(!cases.length||cases.length>12000)throw Error('Fixture count budget');
const offsets={armor_1392_bits:1568,armor_cap_1572_bits:1572,nearby_reduction_1444_bits:1624,
 hp_1528_bits:1440,shield_1532_bits:1444,barrier_1536_bits:1448,shield_source_1344:1344,
 shield_source_remaining_1348_bits:1348,reserve_768_bits:768,absorbed_740_bits:740,
 maximum_shield_744_bits:744,last_hit_1648_bits:1652};
let host,instances=0,maxMemory=0,hostCount=0;
const number=x=>{const b=new DataView(new ArrayBuffer(4));b.setUint32(0,x,true);return b.getFloat32(0,true);};
const bits=x=>{const b=new DataView(new ArrayBuffer(4));b.setFloat32(0,x,true);return b.getUint32(0,true);};
for(let i=0;i<cases.length;i++){
 const c=cases[i],s=c.input;if(c.id!==i)throw Error('Case identity/order');
 if(i%32===0){host=await prepared.fresh();instances++;}
 const {roles,memory,allocate,hostCalls}=host,G=allocate(8192);
 const view=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer);
 const w=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw Error('u32 fixture');view().setUint32(p,x,true);};
 const b=(p,x)=>{if(!Number.isInteger(x)||x<0||x>255)throw Error('u8 fixture');view().setUint8(p,x);};
 const read=p=>view().getUint32(p,true);
 const string=Buffer.from(s.map_id,'ascii'),name=allocate(Math.max(1,string.length),1);bytes().set(string,name);w(G+184,name);w(G+188,string.length);
 b(G+360,1);b(G+361,1);view().setBigUint64(G+1336,999n,true);
 w(G+1432,1);w(G+1536,c.max_hp_bits);w(G+2352,s.now_bits);w(G+2540,s.wave_2532);
 b(G+2587,s.phase_2579);b(G+2576,s.protection_2568);b(G+2582,s.mode_2574);b(G+2578,s.minimum_one_2578);
 w(G+1416,s.player_x_1504_bits);w(G+1420,s.player_y_1508_bits);
 for(const [key,offset]of Object.entries(offsets))w(G+offset,s[key]);
 view().setFloat64(G+992,s.incoming_total_992,true);
 const vector=(rows,stride,cap,ptr,len,write)=>{
  if(rows.length>512)throw Error('Vector budget');
  const p=allocate(Math.max(8,rows.length*stride));if(cap!==null)w(G+cap,rows.length);w(G+ptr,p);w(G+len,rows.length);
  rows.forEach((x,j)=>write(p+j*stride,x));
 };
 vector(s.units,424,1784,1788,1792,(p,u)=>{
  w(p,u.marker);w(p+40,0xffffffff);w(p+64,0xffffffff);w(p+244,0xffffffff);w(p+284,5415572);
  view().setBigUint64(p+112,BigInt(u.target_id),true);w(p+288,0x447a0000);w(p+292,0x447a0000);
  for(const [offset,key]of [[316,'start_x_bits'],[320,'start_y_bits'],[328,'end_x_bits'],[332,'end_y_bits'],[340,'movement_time_bits'],[344,'movement_duration_bits']])w(p+offset,u[key]);
 });
 vector(s.buffs,32,1704,1708,1712,(p,x)=>{w(p+8,x.tag);w(p+12,x.value12_bits);w(p+20,x.spell_id);w(p+24,x.expires24_bits);});
 vector(s.modifiers,36,2048,2052,2056,(p,x)=>{w(p,x.tag);b(p+4,x.byte4);b(p+5,x.byte5);});
 let result;
 if(c.kind==='armor')result={id:i,effective_armor_bits:bits(roles.effective_armor(G))};
 else{
  roles.incoming_damage(G,number(c.amount_bits),BigInt(c.source_guid),c.attack_kind,0,0);
  result={id:i};for(const [key,offset]of Object.entries(offsets))result[key]=read(G+offset);
  result.incoming_total_992_bits=view().getBigUint64(G+992,true).toString(16).padStart(16,'0');result.phase2579=view().getUint8(G+2587);
 }
 if(hostCalls.length)throw Error('Original host API attempted');hostCount+=hostCalls.length;
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/incoming135-runtime.json`,JSON.stringify({case_count:cases.length,
 original_functions:[27375,1073],original_internal_callees_unchanged:true,original_allocator:91941,
 fresh_instances:instances,fresh_every:32,max_memory_bytes:maxMemory,actual_host_calls:hostCount,
 denied_function_imports:878,memory_page_cap:512,node:process.version,application_start_called:false,
 full_game_started:false,user_saves_accessed:false,network_used:false},null,2)+'\n');
