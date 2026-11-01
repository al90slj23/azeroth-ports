// New CAS protocol only: complete same real6730->1089 and unchanged14 tail entries.
// Controlled external clock scheduling is explicit. This is not full880/App.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createCaptureCASOutput,CAS_LIMITS} from './opening_combat135_cas.mjs';
const [directory,configFile]=process.argv.slice(2),hash=x=>createHash('sha256').update(x).digest('hex');
const SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2';
const SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf';
const STACK='research_opening_combat135_stack',PREFIX='research_opening_combat135_';
const surface=Object.freeze({cached_construct:6730,begin_run:1089,player_tick:2088,auto_cast:916,
  owned_effect_tick:975,process_hits:1754,area_tick:3757,effect_tick:915,deadline_tick:38007,
  secondary_hits:2602,update_units:921,collect_pickups:2862,claim_tick:2573,spawn_tick:947,
  special_tick:2376,terminal_tick:49037,select_ability:1072});
const stages=[['player','player_tick',true],['extra','auto_cast',true],['owned_effects','owned_effect_tick',true],
  ['hits','process_hits'],['area','area_tick'],['effects','effect_tick',true],['deadline','deadline_tick'],
  ['secondary','secondary_hits'],['ai','update_units',true],['collect','collect_pickups'],['claims','claim_tick'],
  ['spawn','spawn_tick',true],['special','special_tick'],['terminal','terminal_tick']];
const layouts={companions:[2108,2112,2116,88],units:[1784,1788,1792,424],areas:[1796,1800,1804,88],
  effects120:[1808,1812,1816,120],delayed56:[1820,1824,1828,56],deadline32:[1832,1836,1840,32],
  hits112:[1844,1848,1852,112],secondary112:[1856,1860,1864,112],pickups:[1868,1872,1876,56],
  candidates80:[1904,1908,1912,80],special:[1916,1920,1924,40],windows:[1964,1968,1972,8],
  boundaries:[2120,2124,2128,8],owned80:[1656,1660,1664,80],live32:[1704,1708,1712,32],
  timed12:[596,600,604,12],active84:[644,648,652,84],xp_queue8:[2144,2148,2152,8],currency_queue8:[2156,2160,2164,8]};
const exact=(value,keys,label)=>{if(Object.keys(value).sort().join()!==[...keys].sort().join())throw Error(label+' exact keys');};
const uint=(v,bits=32)=>{if(!Number.isInteger(v)||v<0||v>=2**bits)throw Error('Unsigned input');return v;};
function leb(raw,p){let n=0,s=0;while(p<raw.length&&s<=28){const b=raw[p++];n+=(b&127)*2**s;if(b<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(raw){if(raw.subarray(0,8).toString('hex')!=='0061736d01000000')throw Error('WASM');const a=[];let p=8;while(p<raw.length){const start=p,k=raw[p++],[n,begin]=leb(raw,p);p=begin+n;if(p>raw.length)throw Error('Section');a.push({k,start,begin,end:p});}return a;}
function exportsOf(raw,s){let[n,p]=leb(raw,s.begin);const a=[];for(let i=0;i<n;i++){const[l,b]=leb(raw,p);p=b+l;const name=raw.subarray(b,p).toString('utf8'),kind=raw[p++],[index,e]=leb(raw,p);p=e;a.push({name,kind,index});}if(p!==s.end)throw Error('Exports');return a;}
if(!process.execArgv.includes('--wasm-max-mem-pages=4096'))throw Error('Explicit256MiB research cap');
if(!process.execArgv.includes('--max-old-space-size=512'))throw Error('Explicit512MiB JS heap cap');
const config=JSON.parse(await fs.readFile(configFile,'utf8'));
exact(config,['snapshot_path','snapshot_sha256','app_pointer','world_pointer','input_path','input_sha256','clock_scheduler','locale'],'Config');
if(config.snapshot_sha256!==SNAPSHOT_SHA||config.app_pointer!==14549000||config.world_pointer!==26204808)throw Error('Admitted genuine snapshot binding');
if(config.clock_scheduler!=='explicit_external_f32_add_G2352_not_original880')throw Error('Explicit controlled clock scheduler required');
exact(config.locale,['kind','expected_language_index'],'Locale');
if(config.locale.kind!=='preserve_initialized_snapshot')throw Error('Locale input must preserve snapshot; no Once injection');
uint(config.locale.expected_language_index);if(config.locale.expected_language_index>=14)throw Error('Locale index');
const manifest=JSON.parse(await fs.readFile(directory+'/manifest.json','utf8'));
if(manifest.kind!=='fixed135-real-opening-plus-controlled14-tail-not-full880'||manifest.schema_version!==2||manifest.original_wasm_sha256!==SOURCE_SHA||manifest.memory_page_cap!==4096)throw Error('Private manifest');
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(directory+'/'+manifest.module_file),inputRaw=await fs.readFile(config.input_path);
if(original.length!==90959080||hash(original)!==SOURCE_SHA||hash(changed)!==manifest.module_sha256||hash(inputRaw)!==config.input_sha256||inputRaw.length>1048576)throw Error('Source/input hashes/budget');
const before=sections(original),after=sections(changed);if(before.map(s=>s.k).join()!==after.map(s=>s.k).join()||before.some(s=>s.k===8))throw Error('Sections/start');
for(let i=0;i<before.length;i++)if(before[i].k!==7&&!original.subarray(before[i].start,before[i].end).equals(changed.subarray(after[i].start,after[i].end)))throw Error('Nonexport change');
const oldExports=exportsOf(original,before.find(s=>s.k===7)),newExports=exportsOf(changed,after.find(s=>s.k===7));
if(JSON.stringify(oldExports)!==JSON.stringify(newExports.slice(0,oldExports.length)))throw Error('Old exports changed');
const added=newExports.slice(oldExports.length);if(added.length!==Object.keys(surface).length+1||manifest.roles.length!==Object.keys(surface).length)throw Error('Private export count');
for(let i=0;i<manifest.roles.length;i++){const r=manifest.roles[i],e=added[i];if(e.kind!==0||e.index!==surface[r.role]||r.index!==e.index||e.name!==PREFIX+r.role)throw Error('Role/export binding');}
const stackExport=added.at(-1);if(stackExport.kind!==3||stackExport.index!==0||stackExport.name!==STACK)throw Error('Stack export');
const snapshot=await fs.readFile(config.snapshot_path);if(snapshot.length%65536||snapshot.length>268435456||hash(snapshot)!==SNAPSHOT_SHA)throw Error('Snapshot hash/domain');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(inputRaw);
if(imports.length!==878||imports.some(v=>v.kind!=='function')||cases.length!==1)throw Error('878/exactly one controlled case');
const limits=CAS_LIMITS,output=await createCaptureCASOutput(directory);
let callsTotal=0,completedFrames=0,completedStages=0,peakMemory=0,boundaries=0;const caseReceipts=[];
const emit=value=>output.emit(value);
for(const c of cases){
 exact(c,['id','input','actions'],'Case');if(c.id!==caseReceipts.length||!Array.isArray(c.actions)||c.actions.length>limits.actions_per_case)throw Error('Case/action bounds');
 if(c.actions.filter(action=>action?.kind==='controlled_tail_frame').length>limits.controlled_frames_per_case)throw Error('650 controlled frame cap');
 exact(c.input,['class_byte','race_byte','region_index','app_lcg_seed_u64','object_id_u64','companion_tags'],'Opening input');
 const s=c.input;uint(s.class_byte,8);uint(s.race_byte,8);if(s.region_index!==0||JSON.stringify(s.companion_tags)!=='[255,255]')throw Error('Explicit Elwynn absent slots');
 for(const n of[s.app_lcg_seed_u64,s.object_id_u64])if(typeof n!=='string'||!/^[0-9]+$/.test(n)||BigInt(n)>=1n<<64n)throw Error('Explicit uint64 decimal');
 const bindings={},hostCalls=[],calls=[];
 for(const imp of imports){bindings[imp.module]??={};bindings[imp.module][imp.name]=()=>{hostCalls.push({module:imp.module,name:imp.name});throw Error('Original host denied '+imp.name);};}
 const instance=await WebAssembly.instantiate(module,bindings),ex=instance.exports,memory=ex.memory,stack=ex[STACK];
 if(!(memory instanceof WebAssembly.Memory)||!(stack instanceof WebAssembly.Global)||stack.value!==1048576||memory.buffer.byteLength>snapshot.length)throw Error('Fresh stack/memory');
 const initialMemory=memory.buffer.byteLength;if(memory.buffer.byteLength<snapshot.length)memory.grow((snapshot.length-memory.buffer.byteLength)/65536);
 new Uint8Array(memory.buffer).set(snapshot);if(hash(new Uint8Array(memory.buffer))!==SNAPSHOT_SHA)throw Error('Full snapshot restore');
 const b=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),u=p=>d().getUint32(p,true),byte=p=>d().getUint8(p);
 const span=(p,n,max=8388608)=>{if(!Number.isInteger(p)||!Number.isInteger(n)||p<0||n<0||n>max||p+n>memory.buffer.byteLength)throw Error('Physical capture bounds');return b().subarray(p,p+n);};
 const hex=(p,n,max)=>Buffer.from(span(p,n,max)).toString('hex');
 const invoke=(role,...args)=>{const item={role,index:surface[role],arguments:args,stack_before:stack.value};calls.push(item);callsTotal++;
   if(stack.value!==1048576)throw Error('Precall stack');try{const result=ex[PREFIX+role](...args);item.returned=true;item.stack_after=stack.value;
    if(stack.value!==1048576||hostCalls.length||memory.buffer.byteLength>268435456)throw Error('Stack/host/memory after call');return result;
   }catch(e){item.returned=false;item.stack_after=stack.value;item.error=String(e);throw e;}};
 const allocate=(n,alignment=8)=>{if(!Number.isInteger(n)||n<1||n>4194304||stack.value!==1048576)throw Error('Allocation input');
   const p=ex.__wbindgen_malloc(n,alignment)>>>0;calls.push({role:'original_allocator',index:91941,size:n,alignment,pointer:p,stack_after:stack.value});
   if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>268435456||stack.value!==1048576||hostCalls.length)throw Error('Allocator boundary');return p;};
 const locale=()=>{const words=Array.from({length:6},(_,i)=>u(14384320+i*4)),flag=byte(14384344),effective=words[0]?words[1]:words[2];
   if(flag!==3)throw Error('Locale Once uninitialized:548 cold host denied; no injection');
   if(words[3]!==14||words[5]!==14||effective>=14||effective!==config.locale.expected_language_index)throw Error('Explicit locale prestate differs');
   return{raw_once25_hex:hex(14384320,25),override_present14384320:words[0],override_index14384324:words[1],base_index14384328:words[2],
    effective_index:effective,vector_capacity:words[3],vector_pointer:words[4],vector_count:words[5],once_flag:flag,
    map_headers32_hex:Array.from({length:14},(_,i)=>hex(words[4]+32*i,32)),
    source:'Actual prestate; effective=(14384320!=0?14384324:14384328), fixed19964. No548 text read for expected.'};};
 const localeBefore=locale(),localeGuard=hash(Buffer.from(localeBefore.raw_once25_hex+localeBefore.map_headers32_hex.join(''),'hex'));
 const App=config.app_pointer,R=u(App+5116);if(R!==config.world_pointer)throw Error('Genuine cached world');
 const G=allocate(8192),r=o=>u(G+o);let lastPackets=[],lastNotifications=[];
 const vector=(layout)=>{const[co,po,no,stride]=layout,capacity=r(co),pointer=r(po),count=r(no);if(count>capacity||capacity>4096)throw Error('Actual vector budget');
   return{stride,capacity,pointer,count,storage:Array.from({length:capacity},(_,j)=>hex(pointer+j*stride,stride)),storage_sha256:hash(span(pointer,capacity*stride))};};
 const queue=(base,stride,packets)=>{const capacity=r(base),pointer=r(base+4),count=r(base+8);if(count>capacity||capacity>4096)throw Error('Queue budget');
   const active=Array.from({length:count},(_,i)=>{const p=pointer+i*stride,cap=u(p),q=u(p+4),n=u(p+8);if(n>cap||cap>1048576)throw Error('Payload budget');
    return{capacity:cap,pointer:q,length:n,payload_hex:hex(q,n),backing_hex:hex(q,cap),metadata_hex:hex(p,stride),...(packets?{opcode:d().getUint16(p+12,true)}:{})};});
   return{capacity,pointer,count,metadata_backing_hex:hex(pointer,capacity*stride),active};};
 const fields=()=>{const root=r(2476),depth=r(2480);if(!root)return{fields:{},nodes:[]};if(depth>5)throw Error('Tree depth');const pairs=[],nodes=[],seen=new Set();
   const walk=(p,h)=>{if(!p||seen.has(p)||seen.size>=256)throw Error('Tree graph');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree count');
    nodes.push({pointer:p,depth:h,raw_hex:hex(p,h?124:76)});for(let j=0;j<n;j++){if(h)walk(u(p+76+j*4),h-1);pairs.push([d().getUint16(p+52+j*2,true),u(p+4+j*4)]);}if(h)walk(u(p+76+n*4),h-1);};walk(root,depth);return{fields:Object.fromEntries(pairs),nodes};};
 // Same semantic decoder as run_headless135_oracle.mjs. The complete80B
 // vector/backing remains captured separately; pointer-owned IDs/kinds are
 // actually read here so a candidate/selection claim cannot omit payloads.
 const candidateId=(pointer,length)=>Buffer.from(span(pointer,length,128)).toString('ascii');
 const candidates=()=>{const pointer=r(1908),count=r(1912);if(count>4)throw Error('Candidate count');
   return Array.from({length:count},(_,j)=>{const q=pointer+j*80,tag=u(q+60);
    const value={variant:'',tier:u(q+76),ability_id:'',owned_index:0,kinds:[],gold:0};
    if(tag===0x80000000){value.variant='new';value.ability_id=candidateId(u(q+64),u(q+68));}
    else if(tag<0x80000000||tag===0x80000001){value.variant='upgrade';value.owned_index=u(q+72);
     const definition=u(r(1660)+value.owned_index*80);value.ability_id=candidateId(u(definition+12),u(definition+16));value.kinds=Array.from(span(u(q+64),u(q+68),5));}
    else if(tag===0x80000004){value.variant='gold';value.gold=u(q+64);}
    else throw Error('Candidate variant');return value;});};
 const delta=(old,current)=>{const prefix=old.length<=current.length&&JSON.stringify(current.slice(0,old.length))===JSON.stringify(old);return{prefix_preserved:prefix,previous_count:old.length,current_count:current.length,appended:prefix?current.slice(old.length):[],full_current:prefix?undefined:current};};
 const distanceMap=()=>{const pointer=r(2368);if(!pointer)return null;const raw_header28_hex=hex(pointer,28),capacity=u(pointer+8),values_pointer=u(pointer+12),count=u(pointer+16);
   if(count>capacity||capacity>1048576)throw Error('Actual distance-map u16 backing budget');
   const values_sha256=hash(span(values_pointer,count*2)),backing_u16le_sha256=hash(span(values_pointer,capacity*2));
   return{rc_pointer:pointer,raw_header28_hex,strong_count:u(pointer),weak_count:u(pointer+4),capacity,values_pointer,count,
    start_index:u(pointer+20),field24:u(pointer+24),reachable:u(pointer+24),values_sha256,values_u16le_sha256:values_sha256,
    backing_u16le_sha256,updated2372_bits:r(2372)};};
 // Fixed135 three-ability guardian declarations, already recovered in1525.
 // Physical timer ownership stays observational; comparison binds by GUID.
 const guardianDeclarations=new Map([[5484048,5477460],[5484076,5477592],[5484104,5477724]]);
 const unitCooldowns=()=>{const pointer=r(1788),count=r(1792),observations=[],guardians=[],timerPointers=new Set();
  for(let j=0;j<count;j++){const at=pointer+j*424,capacity=u(at+64),guid=d().getBigUint64(at+112,true).toString();
   const owner={unit_index:j,guid,tag64:capacity,raw_unit_header64_100_hex:hex(at+64,36)};
   if(capacity===0xffffffff){observations.push({...owner,variant:'none',pointer_dereferenced:false});continue;}
   const timerPointer=u(at+68),length=u(at+72),abilityPointer=u(at+76),abilityCount=u(at+80),
    abilitySlicePointer=u(at+84),abilitySliceCount=u(at+88),headerPointer=u(at+96);
   if(length>capacity||capacity>4096||!timerPointer||timerPointer%4||timerPointers.has(timerPointer))throw Error('Owned unit cooldown Vec bounds/ownership');
   const backing=span(timerPointer,capacity*4);timerPointers.add(timerPointer);
   if(timerPointer<pointer+r(1784)*424&&timerPointer+capacity*4>pointer)throw Error('Owned cooldown backing aliases unit Vec');
   if(abilityCount>4096||abilitySliceCount>4096)throw Error('Static unit ability slice bounds');
   const timers_bits=Array.from({length},(_,k)=>u(timerPointer+k*4)),ability_records44_hex=Array.from({length:abilityCount},(_,k)=>hex(abilityPointer+k*44,44));
   const header28_hex=hex(headerPointer,28);
   observations.push({...owner,variant:'timers',capacity,pointer:timerPointer,count:length,pointer_dereferenced:true,
    raw_timer_vec12_hex:hex(at+64,12),timers_bits,backing_hex:Buffer.from(backing).toString('hex'),backing_sha256:hash(backing),
    ability_pointer:abilityPointer,ability_count:abilityCount,ability_records44_hex,
    ability_slice_pointer:abilitySlicePointer,ability_slice_count:abilitySliceCount,
    ability_slice_records44_hex:Array.from({length:abilitySliceCount},(_,k)=>hex(abilitySlicePointer+k*44,44)),
    header_pointer:headerPointer,header28_hex});
   if(capacity!==3||length!==3||abilityCount!==3||abilitySliceCount!==3||abilitySlicePointer!==abilityPointer||guardianDeclarations.get(headerPointer)!==abilityPointer)
    throw Error('Unrecovered active unit cooldown family; no payload mask admission');
   guardians.push({unit_index:j,guid,capacity,timers_bits,ability_pointer:abilityPointer,header_pointer:headerPointer,ability_records44_hex,header28_hex});
  }
  return{observations,guardians};};
 const capture=()=>{const vectors=Object.fromEntries(Object.entries(layouts).map(([n,l])=>[n,vector(l)])),packets=queue(1880,16,true),notifications=queue(1892,12,false),keyed=fields(),cooldowns=unitCooldowns();
   const pa=packets.active.map(x=>({opcode:x.opcode,payload_hex:x.payload_hex})),na=notifications.active.map(x=>x.payload_hex),newPackets=delta(lastPackets,pa),newNotifications=delta(lastNotifications,na);lastPackets=pa;lastNotifications=na;
   if(r(2348)!==R||u(App+5116)!==R)throw Error('Real world owner changed');
   const map=Buffer.from(span(r(184),r(188),128)).toString('utf8');
   return{raw_game2592_hex:hex(G,2592),vectors,unit_cooldowns:cooldowns.observations,packets,notifications,new_packets:newPackets,new_notifications:newNotifications,
    player_keyed_tree:keyed,projection:{phase2587:byte(G+2587),selection_kind2585:byte(G+2585),generation_counter2400:r(2400),field1092:r(1092),mode2582:byte(G+2582),
     candidates:candidates(),guardian_cooldowns:cooldowns.guardians,now_bits:r(2352),rng_words:[0,1,2,3].map(i=>r(1720+i*4)),
     spawn_counter:r(2408),message_sequence:r(2412),kill_cost_bits:r(2420),next_resource2444_bits:r(2444),next_event2424_bits:r(2424),last_event2586:byte(G+2586),next_supply2448_bits:r(2448),source_id:d().getBigUint64(G+1336,true).toString(),
     map_id_utf8:map,player_xyz:[r(1416),r(1420),r(1424)],velocity_xy:[r(1736),r(1740)],previous_player_xyz:[r(2428),r(2432),r(2436)],
     progression:{level:r(1432),xp:r(1436),pending_upgrades:r(2376)},current_hp_bits:r(1440),
     derived_bits:Object.fromEntries(Array.from({length:23},(_,i)=>[1536+i*4,r(1536+i*4)])),player_fields:keyed.fields,
     racial_record_hex:hex(G+1256,80),owned_records_hex:vectors.owned80.storage.slice(0,vectors.owned80.count),
     records:vectors.units.storage.slice(0,vectors.units.count),area_records:vectors.areas.storage.slice(0,vectors.areas.count),
     unit_storage:vectors.units.storage,area_storage:vectors.areas.storage,pickup_storage:vectors.pickups.storage,
     pickup_words:vectors.pickups.storage.slice(0,vectors.pickups.count).map(row=>{const raw=Buffer.from(row,'hex');return Array.from({length:14},(_,i)=>raw.readUInt32LE(i*4));}),
     timer1628_bits:r(1628),budget_bits:r(2416),gold:r(1456),earned:r(1100),
     outgoing_total_hex:d().getBigUint64(G+984,true).toString(16).padStart(16,'0'),incoming_total_hex:d().getBigUint64(G+992,true).toString(16).padStart(16,'0'),
     last_hit_bits:r(1652),absorbed740_bits:r(740),maximum_shield744_bits:r(744),
     special:{selected392:r(392),target396:r(396),navigation2564:byte(G+2564),announced2565:byte(G+2565),announcement_time2392_bits:r(2392)},
     distance_map:distanceMap(),distance_map_updated_at_bits:r(2372),
     effect:{clock2364_bits:r(2364),effect_counter2356:r(2356),action_sequence1644:r(1644),player_action_tag416:r(416)},
     tail_flags:{field400:r(400),protection2576:byte(G+2576),flag2568:byte(G+2568),gate2579:byte(G+2579)}},
    ownership:{App,G,game_world_pointer:r(2348),app_cache_pointer:u(App+5116),raw_world_rc124_hex:hex(R,124),world_refcount:u(R),
     raw_app5168_hex:hex(App,5168)},stack:stack.value,memory_bytes:memory.buffer.byteLength};};
 const appBefore=hex(App,5168),refBefore=u(R),navigationInput=byte(App+5165);d().setBigUint64(App+4928,BigInt(s.app_lcg_seed_u64),true);
 b()[App+3720]=s.class_byte;b()[App+3721]=s.race_byte;d().setBigUint64(App+3552,BigInt(s.object_id_u64),true);
 b()[App+3604]=255;b()[App+3612]=255;const declaredApp=hex(App,5168);
 const answer={id:c.id,locale_prestate:localeBefore,app_before_declared_hex:appBefore,app_after_declared_hex:declaredApp,
  navigation_context:{app_byte5165:navigationInput,source:'Fixed6730 App5165 -> temporary2916 -> outputGame2564; snapshot context, not menu-default production.'},
  stage_count:0,boundary:null};
 await emit({record_kind:'case_start',...answer});
 try{
  invoke('cached_construct',G,App);const constructor=capture();await emit({record_kind:'constructor',id:c.id,...constructor});if(constructor.projection.phase2587!==0||r(2348)!==R||u(R)!==refBefore+1)throw Error('Real constructor ownership/phase');
  if(byte(G+244)!==255||byte(G+252)!==255)throw Error('Actual absent companion tags were not preserved');
  for(const name of['companions','units','pickups','special','windows','boundaries'])if(constructor.vectors[name].count||constructor.vectors[name].capacity)throw Error('Genuine empty constructor vectors');
  invoke('begin_run',G);const opening=capture();await emit({record_kind:'opening',id:c.id,...opening});if(opening.projection.phase2587!==1||opening.projection.map_id_utf8!=='elwynn')throw Error('Real opening phase/map');
  let frame=0;
  for(let actionIndex=0;actionIndex<c.actions.length;actionIndex++){
   const action=c.actions[actionIndex];
   if(action.kind==='select'){
    exact(action,['kind','index'],'Selection action');uint(action.index);const clockBefore=r(2352);
    try{invoke('select_ability',G,action.index);const snapshot=capture();if(r(2352)!==clockBefore)throw Error('1072 unexpectedly advanced clock');
     await emit({record_kind:'stage',id:c.id,stage_index:answer.stage_count++,frame,action_index:actionIndex,kind:'select',role:'select_ability',entry_index:1072,input_index:action.index,...snapshot});completedStages++;}
    catch(error){answer.boundary={frame,action_index:actionIndex,kind:'select',role:'select_ability',entry_index:1072,input_index:action.index,error:String(error),stack:stack.value,host_calls:hostCalls};try{answer.boundary.capture=capture();}catch(captureError){answer.boundary.capture_error=String(captureError);}throw error;}
    continue;
   }
   exact(action,['kind','dt_bits'],'Controlled scheduler action');if(action.kind!=='controlled_tail_frame')throw Error('Only controlled14-stage tail or explicit selection actions admitted');uint(action.dt_bits);
   const scratch=new DataView(new ArrayBuffer(4));scratch.setUint32(0,action.dt_bits,true);const dt=scratch.getFloat32(0,true);
   if(!Number.isFinite(dt)||dt<0||dt>.1000000015||byte(G+2587)!==1)throw Error('Controlled finite/running delta');
   const oldBits=r(2352);d().setFloat32(G+2352,d().getFloat32(G+2352,true)+dt,true);
   await emit({record_kind:'clock_control',id:c.id,frame,action_index:actionIndex,kind:config.clock_scheduler,entry:'host_controlled_tail_scheduler',old_bits:oldBits,dt_bits:action.dt_bits,new_bits:r(2352),original880_called:false,only_external_game_write_offset:2352});
   for(const[kind,role,timed]of stages){
    try{if(timed)invoke(role,G,dt);else invoke(role,G);const snapshot=capture();await emit({record_kind:'stage',id:c.id,stage_index:answer.stage_count++,frame,action_index:actionIndex,kind,role,entry_index:surface[role],...snapshot});completedStages++;}
    catch(error){answer.boundary={frame,action_index:actionIndex,kind,role,entry_index:surface[role],error:String(error),stack:stack.value,host_calls:hostCalls};try{answer.boundary.capture=capture();}catch(captureError){answer.boundary.capture_error=String(captureError);}throw error;}
   }
   completedFrames++;frame++;
  }
 }catch(error){answer.boundary??={kind:'opening_or_scheduler',error:String(error),stack:stack.value,host_calls:hostCalls};boundaries++;}
 const localeAfter=locale();if(hash(Buffer.from(localeAfter.raw_once25_hex+localeAfter.map_headers32_hex.join(''),'hex'))!==localeGuard)throw Error('Preserved locale headers mutated');
 answer.locale_after=localeAfter;answer.locale_writes=0;answer.calls=calls;answer.host_calls=hostCalls;
 answer.snapshot={path:config.snapshot_path,sha256:SNAPSHOT_SHA,bytes:snapshot.length,initial_memory_bytes:initialMemory,restored:true,externref_table_restored:false,stack_initial:1048576};
 peakMemory=Math.max(peakMemory,memory.buffer.byteLength);caseReceipts.push({id:c.id,completed_stages:answer.stage_count,boundary:answer.boundary?{kind:answer.boundary.kind,error:answer.boundary.error}:null});await emit({record_kind:'case_end',...answer});
}
const casReceipt=await output.finish();
const runtime={kind:'real_opening_then_controlled14_tail_original_observation',schema_version:5,output_protocol:'bounded_stage_cas_jsonl_gzip',cases:cases.length,original_entry_calls:callsTotal,
 completed_controlled_tail_frames:completedFrames,completed_stages:completedStages,boundaries,case_receipts:caseReceipts,
 original_wasm_sha256:SOURCE_SHA,module_sha256:manifest.module_sha256,input_sha256:config.input_sha256,
 memory_page_cap:4096,peak_memory_bytes:peakMemory,denied_imports:878,host_imports_throw:true,
 stage_entries:stages.map(([kind,role])=>({kind,role,index:surface[role]})),
 selection_entry:{role:'select_ability',index:1072,signature:'(G:i32,input_index:i32)->void',advances_clock:false},
 budgets:limits,js_heap_cap_mib:512,output_compression:{format:'gzip',members:1,level:6,all_capture_fields_preserved:true,content_addressed:true},
 actual_opening_phase_used:true,constructor_phase_overwritten:false,preallocated_zero128_storage:false,
 world_rc_forged:false,locale_once_injected:false,locale_source:'Preserved initialized genuine snapshot; prestate index bound to explicit input.',
 controlled_clock_scheduler:config.clock_scheduler,full880_called:false,new_full880_frames:0,
 independent_model_validation_cases:0,network_used:false,user_saves_accessed:false,output_bytes:casReceipt.index_uncompressed_bytes,
 uncompressed_output_bytes:casReceipt.index_uncompressed_bytes,compressed_output_bytes:casReceipt.compressed_bytes,output_records:casReceipt.records,
 max_record_uncompressed_bytes:casReceipt.maximum_index_record_bytes,output_sha256:casReceipt.compressed_sha256,uncompressed_sha256:casReceipt.index_uncompressed_sha256,
 logical_output_bytes:casReceipt.logical_bytes,logical_output_sha256:casReceipt.logical_sha256,maximum_logical_record_bytes:casReceipt.maximum_logical_record_bytes,capture_cas:casReceipt,node:process.version};
await fs.writeFile(directory+'/opening-combat135-cas-runtime.json',JSON.stringify(runtime,null,2)+'\n');
if(boundaries)process.exitCode=2;
