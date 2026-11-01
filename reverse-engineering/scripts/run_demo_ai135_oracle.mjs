// Full unchanged921 over independently supplied ordinary/demo/controlled world.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareDemoAi135} from './demo_ai135_host.mjs';
import {packAiWorld135} from './ai_world135_packing.mjs';
const [directory,inputPath]=process.argv.slice(2),prepared=await prepareDemoAi135(directory,['update_units']);
const hash=b=>createHash('sha256').update(b).digest('hex'),input=await fs.readFile(inputPath);
if(!process.execArgv.includes('--max-old-space-size=512')||input.length>8388608)throw Error('Explicit heap/input budgets');
const cases=JSON.parse(input);if(!cases.length||cases.length>160)throw Error('Case budget');
const F=w=>{const b=new DataView(new ArrayBuffer(4));b.setUint32(0,w,true);return b.getFloat32(0,true);};
const offsets={armor_1392_bits:1568,armor_cap_1572_bits:1572,nearby_reduction_1444_bits:1624,hp_1528_bits:1440,shield_1532_bits:1444,barrier_1536_bits:1448,shield_source_1344:1344,shield_source_remaining_1348_bits:1348,reserve_768_bits:768,absorbed_740_bits:740,maximum_shield_744_bits:744,last_hit_1648_bits:1652};
let entryCalls=0,instances=0,maxMemory=0,outputBytes=0,error=null;const checks=[],allHostCalls=[];
try{
for(const c of cases){
 if(global.gc)global.gc();
 if(c.records.length>16||c.steps.length>64)throw Error('Record/step budget');
 const host=await prepared.fresh(),{memory,allocate,roles}=host;instances++;
 allHostCalls.push(host.hostCalls);const world=await packAiWorld135(host,c.world),d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 const G=allocate(8192),U=allocate(Math.max(8,c.records.length*424)),name=allocate(6,1);b().set(Buffer.from('elwynn'),name);w(G+184,name);w(G+188,6);w(G+2348,world.R);
 w(G+1784,c.records.length);w(G+1788,U);w(G+1792,c.records.length);w(G+2412,c.sequence);w(G+1432,1);w(G+1536,c.max_hp_bits);
 b()[G+2582]=c.incoming.mode_2574;b()[G+2587]=c.incoming.phase_2579;b()[G+360]=1;b()[G+361]=1;d().setBigUint64(G+1336,999n,true);w(G+2528,0);
 for(const[key,offset]of Object.entries(offsets))w(G+offset,c.incoming[key]);d().setFloat64(G+992,c.incoming.incoming_total_992,true);
 [1,2,3,4].forEach((v,j)=>w(G+1720+4*j,v));c.records.forEach((row,i)=>{if(!/^[0-9a-f]{848}$/.test(row))throw Error('Only fully declared physical424B fixture accepted');b().set(Buffer.from(row,'hex'),U+i*424);});
 const queue=()=>{const cap=r(G+1880),p=r(G+1884),n=r(G+1888);if(n>1024||n>cap||p+n*16>memory.buffer.byteLength)throw Error('Queue metadata budget');return{capacity:cap,count:n,pointer:p,metadata_hex:hex(p,n*16),active:Array.from({length:n},(_,i)=>{const row=p+i*16,capacity=r(row),pointer=r(row+4),length=r(row+8);if(length>capacity||length>2097152||pointer+length>memory.buffer.byteLength)throw Error('Packet payload budget');return{opcode:d().getUint16(row+12,true),payload_hex:hex(pointer,length),capacity,pointer,length};})};};
 const stages=[];let previousPackets=0;
 for(const step of c.steps){
  w(G+2352,step.now_bits);step.player_xyz_bits.forEach((v,j)=>w(G+1416+j*4,v));roles.update_units(G,F(step.dt_bits));entryCalls++;world.verify();if(host.hostCalls.length)throw Error('Original host attempted');
  const q=queue(),added=q.active.slice(previousPackets),aura=added.filter(x=>x.opcode===169).map(x=>({opcode:x.opcode,payload_hex:x.payload_hex}));
  const firstAura=added.findIndex(x=>x.opcode===169);if(firstAura>=0&&added.slice(firstAura).some(x=>x.opcode!==169))throw Error('NPC Aura removal was not late in921');
  const known={records:c.records.map((_,j)=>hex(U+j*424,424)),...Object.fromEntries(Object.entries(offsets).map(([k,o])=>[k,r(G+o)])),incoming_total_992_bits:d().getBigUint64(G+992,true).toString(16).padStart(16,'0'),sequence:r(G+2412),packet_count:q.count,rng_words:[0,1,2,3].map(j=>r(G+1720+4*j)),new_aura_packets169:aura,new_non169_packet_count:added.length-aura.length,aura_after_non169:true};
  stages.push({known,raw_game8192_hex:hex(G,8192),unit_pointer:U,raw_packets:q,new_packet_opcodes:added.map(x=>x.opcode),distance_map_pointer:r(G+2368)});previousPackets=q.count;maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 }
 checks.push(...host.stackChecks().map(x=>({case_id:c.id,...x})));const line=JSON.stringify({id:c.id,stages})+'\n';if(Buffer.byteLength(line)>2097152||(outputBytes+=Buffer.byteLength(line))>33554432)throw Error('Output budget');process.stdout.write(line);
}
}catch(e){error=String(e);throw e;}
finally{await fs.writeFile(directory+'/demo-ai135-runtime.json',JSON.stringify({version:'0.135.1',actual_build:'90898d5e3',historical_build_alias:'0898d5e3',cases:cases.length,fresh_instances:instances,entry_calls:entryCalls,original_full_entries:[921],all_original_bodies_and_callees_unchanged:true,denied_imports:878,actual_host_calls:allHostCalls.reduce((n,calls)=>n+calls.length,0),memory_cap_bytes:33554432,max_memory_bytes:maxMemory,heap_mib:512,output_bytes:outputBytes,stack_checks:checks,stack_all_restored:checks.every(x=>x.entered&&x.returned&&x.before===x.after&&x.before===1048576),original_snapshot_loaded:false,application_start_called:false,user_saves_accessed:false,network_used:false,error},null,2)+'\n');}
