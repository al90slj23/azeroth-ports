// Full original1560, its producer helpers and1512; no application entry.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';
const [directory,fixtureFile]=process.argv.slice(2),prepared=await prepareFull135(directory,['initial_game']);
const text=await fs.readFile(fixtureFile,'utf8');if(text.length>4*1024*1024)throw Error('Fixture bytes');
const rows=text.trim().split('\n').filter(Boolean).map(JSON.parse);if(rows.length<1||rows.length>1024)throw Error('Fixture count');
let host,instances=0,maxMemory=0;
for(let i=0;i<rows.length;i++){
 if(i%16===0){host=await prepared.fresh();instances++;}
 const c=rows[i];if(c.id!==i)throw Error('Case order');const s=c.input,{memory,allocate,roles,hostCalls}=host;
 const view=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),u32=(p,x)=>view().setUint32(p,x>>>0,true),r=p=>view().getUint32(p,true),u8=(p,x)=>view().setUint8(p,x);
 const G=allocate(8192),P=allocate(376),V=allocate(128),region=Buffer.from(c.region_id,'ascii'),name=allocate(Math.max(region.length,1),1);
 bytes().set(region,name);u32(P+156,4);u32(P+168,name);u32(P+172,region.length);view().setBigUint64(P+176,BigInt(s.object_id_u64),true);view().setBigUint64(P+184,BigInt(s.seed_u64),true);u8(P+344,s.class_byte);u8(P+345,s.race_byte);
 u8(V+120,1);u32(V+116,s.flat_height_bits);u32(V+56,0xffffffff);u32(V+32,0xffffffff);
 roles.initial_game(G,P,V);if(hostCalls.length)throw Error('Original host import attempted');if(r(G+1912)!==0)throw Error('Unmodeled constructor candidate records');
 const tree=()=>{const root=r(G+2476),depth=r(G+2480);if(!root)return{};if(depth>4)throw Error('Tree depth');const items=[],seen=new Set();const walk=(p,l)=>{if(!p||p+76>memory.buffer.byteLength||seen.has(p)||seen.size>64)throw Error('Tree bounds');seen.add(p);const n=view().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(l)walk(r(p+76+j*4),l-1);items.push([view().getUint16(p+52+j*2,true),r(p+4+j*4)]);}if(l)walk(r(p+76+n*4),l-1);};walk(root,depth);return Object.fromEntries(items);};
 const n=r(G+1664),a=r(G+1660);if(n>128)throw Error('Owned bound');
 const projection={progression:{level:r(G+1432),xp:r(G+1436),pending_upgrades:r(G+2376)},derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,r(G+1536+j*4)])),current_hp_bits:r(G+1440),auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,r(G+o)])),speed_bits:r(G+1648),player_fields:tree(),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),candidates:[],phase2587:view().getUint8(G+2587),selection_kind2585:view().getUint8(G+2585),generation_counter2400:r(G+2400),
  owned_records_hex:Array.from({length:n},(_,j)=>Buffer.from(bytes().subarray(a+j*80,a+j*80+80)).toString('hex')),racial_record_hex:Buffer.from(bytes().subarray(G+1256,G+1336)).toString('hex'),player_xyz:[1416,1420,1424].map(o=>r(G+o)),source_id:view().getBigUint64(G+1336,true).toString(),timer1628_bits:r(G+1628),spawn_counter:r(G+2408),message_sequence:r(G+2412),kill_cost_bits:r(G+2420),game_tag:view().getBigUint64(G,true).toString(),member_count:r(G+2540),initial_scalar_words:Object.fromEntries([488,740,744,1652,2416,2424,2428,2432,2436,2440,2444,2448,2452,2456,2460,2464,2468,2472,2516].map(o=>[o,r(G+o)])),initial_byte_flags:Object.fromEntries([772,2568,2572,2573,2576,2578,2581,2583].map(o=>[o,view().getUint8(G+o)])),now_bits:r(G+2352),mode2582:view().getUint8(G+2582),owned_capacity:r(G+1656),owned_count:n,
  source_counts:{passives:r(G+1700),adjustments:r(G+1676),item_modifiers:r(G+2032),owned_skills:r(G+176),timed_records:r(G+604),definitions:r(G+2056),live_effects:r(G+1712),ability_modifiers:r(G+2044),active84:r(G+652)},unit_count:r(G+1792),pickup_count:r(G+1876),gold:r(G+1456),earned:r(G+1100),flags772:view().getUint8(G+772),context908:view().getUint8(G+908),extra_cast1596_bits:r(G+1596)};
 process.stdout.write(JSON.stringify({id:i,projection,raw_g2592_hex:Buffer.from(bytes().subarray(G,G+2592)).toString('hex')})+'\n');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
}
await fs.writeFile(`${directory}/initial135-runtime.json`,JSON.stringify({cases:rows.length,fresh_instances:instances,fresh_every:16,max_memory_bytes:maxMemory,actual_host_calls:0,denied_function_imports:878,original_allocator:91941,memory_page_cap:512,full_original_constructor:1560,application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false,node:process.version},null,2)+'\n');
