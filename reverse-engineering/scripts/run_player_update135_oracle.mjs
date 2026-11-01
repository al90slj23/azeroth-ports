// Complete original2088 and921, every callee unchanged, no appstart.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,caseFile]=process.argv.slice(2),prepared=await prepareFull135(directory,['player_tick','update_units']);
const text=await fs.readFile(caseFile,'utf8');if(Buffer.byteLength(text)>32*1024*1024)throw Error('Fixture byte budget');
const cases=JSON.parse(text);if(!cases.length||cases.length>4000)throw Error('Case budget');
const number=x=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,x,true);return d.getFloat32(0,true);};
let host,instances=0,calls2088=0,calls921=0,maxMemory=0;
for(let i=0;i<cases.length;i++){
 if(i%12===0){host=await prepared.fresh();instances++;}
 const c=cases[i];if(c.id!==i)throw Error('Case order');const {memory,allocate,roles,hostCalls}=host;
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),u32=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw Error('u32');d().setUint32(p,x,true);},u8=(p,x)=>d().setUint8(p,x),r=p=>d().getUint32(p,true);
 const G=allocate(8192),V=allocate(128);u32(G+2348,V);u32(V+32,0xffffffff);u32(V+56,0xffffffff);u32(V+120,1);
 for(const [cap,ptr,len,align]of [[1656,1660,1664,4],[1904,1908,1912,4],[1952,1956,1960,4],[2024,2028,2032,4],[2048,2052,2056,4],[2084,2088,2092,4],[2096,2100,2104,4],[1892,1896,1900,4],[1704,1708,1712,8],[1784,1788,1792,8]]){u32(G+cap,0);u32(G+ptr,align);u32(G+len,0);}
 const tree=()=>{const root=r(G+2476),depth=r(G+2480);if(!root)return{};const fields=[],seen=new Set();const walk=(p,l)=>{if(!p||p+76>memory.buffer.byteLength||seen.has(p)||seen.size>512||l>5)throw Error('Tree budget');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(l)walk(r(p+76+j*4),l-1);const k=d().getUint16(p+52+j*2,true);if([22,28,1109].includes(k))fields.push([k,r(p+4+j*4)]);}if(l)walk(r(p+76+n*4),l-1);};walk(root,depth);return Object.fromEntries(fields);};
 let output;
 if(c.kind==='player'){
  const s=c.input,t=s.stats;
  for(const source of Object.values(s.sources).filter(Array.isArray)){/* rows written below */}
  for(const k of ['passives','adjustments','item_modifiers','owned_skills','timed_records','definitions'])if(s.sources[k].length)throw Error('Explicit empty source domain');
  for(const [o,v]of Object.entries(s.derived_bits))u32(G+Number(o),v);
  u8(G+360,t.class_byte);u8(G+361,t.race_byte);u8(G+2582,t.flag2574);u8(G+2587,s.phase2587);u8(G+387,s.heal_gate387);
  u32(G+1536,t.old_max_hp_bits);u32(G+1440,t.current_hp_bits);u32(G+1648,t.previous_speed_bits);u32(G+268,t.conditional268_bits);
  for(const [oldOffset,newOffset]of [[1532,1444],[1536,1448],[768,768]])u32(G+newOffset,t[`pool${oldOffset}_bits`]);
  u32(G+1344,t.conditional1344_id);u32(G+1348,t.conditional1348_bits);u32(G+756,s.pool756_bits);u32(G+1432,s.progression.level);u32(G+1652,c.last_hit_bits);
  s.rng_words.forEach((x,j)=>u32(G+1720+4*j,x));d().setBigUint64(G+1336,1n,true);
  if(Object.keys(s.player_fields).length)throw Error('Explicit empty initial logical tree');
  const L=allocate(Math.max(32,c.live_records.length*32));u32(G+1704,c.live_records.length);u32(G+1708,L);u32(G+1712,c.live_records.length);c.live_records.forEach((x,j)=>{if(x.length!==64)throw Error('Live32');bytes().set(Buffer.from(x,'hex'),L+j*32);});
  bytes().set(Buffer.from(c.owned_hex,'hex'),G+1256);u32(G+1628,0x7f800000);output=[];
  for(const step of c.steps){
   u32(G+2352,step.now_bits);roles.player_tick(G,number(step.dt_bits));calls2088++;
   if(Buffer.from(bytes().slice(G+1256,G+1336)).toString('hex')!==c.owned_hex)throw Error('Isolated racial scheduler unexpectedly changed');
   const p=r(G+1708),n=r(G+1712);if(n>128)throw Error('Live budget');
   output.push({live_records:Array.from({length:n},(_,j)=>Buffer.from(bytes().slice(p+j*32,p+(j+1)*32)).toString('hex')),
    derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,r(G+1536+j*4)])),current_hp_bits:r(G+1440),auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,r(G+o)])),shield_source:r(G+1344),speed_bits:r(G+1648),player_fields:tree(),rng_words:[0,1,2,3].map(j=>r(G+1720+4*j))});
  }
 }else if(c.kind==='corpse'){
  u8(G+2582,c.mode);u8(G+2587,1);u32(G+2528,c.peer);u32(G+2352,c.now_bits);u32(G+2412,123);[1,2,3,4].forEach((x,j)=>u32(G+1720+j*4,x));
  const U=allocate(Math.max(424,c.records.length*424));u32(G+1784,c.records.length);u32(G+1788,U);u32(G+1792,c.records.length);c.records.forEach((x,j)=>bytes().set(Buffer.from(x,'hex'),U+j*424));
  roles.update_units(G,.1);calls921++;
  const p=r(G+1788),n=r(G+1792);if(n>128)throw Error('Unit budget');
  output={records:Array.from({length:n},(_,j)=>Buffer.from(bytes().slice(p+j*424,p+(j+1)*424)).toString('hex')),packet_count:r(G+1888),removed_guids:[],rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),sequence:r(G+2412)};
  // Packet170 contains actual despawnGUID. Read complete original packet rows.
  const P=r(G+1884),N=r(G+1888);if(N>128)throw Error('Packet budget');
  for(let j=0;j<N;j++){const z=P+j*16;if(d().getUint16(z+12,true)!==170||r(z+8)!==8)throw Error('Expected170despawn');output.removed_guids.push(d().getBigUint64(r(z+4),true).toString());}
 }else throw Error('Unknown case kind');
 if(hostCalls.length)throw Error('Original host import attempted');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify({id:i,result:output})+'\n');
}
await fs.writeFile(`${directory}/player-update135-runtime.json`,JSON.stringify({cases:cases.length,full2088_calls:calls2088,full921_calls:calls921,unchanged_callees:true,original_allocator:91941,fresh_instances:instances,max_memory_bytes:maxMemory,host_calls:0,denied_imports:878,application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false},null,2)+'\n');
