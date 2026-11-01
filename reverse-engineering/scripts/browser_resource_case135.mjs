// Runs only in a fresh research browser origin, never in a user's game/tab.
import{resource135GetImports,resource135BindOnly}from'/bridge.mjs';
const hex=bytes=>Array.from(bytes,x=>x.toString(16).padStart(2,'0')).join('');
const number=x=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,x,true);return d.getFloat32(0,true);};
const offsets={armor_1392_bits:1568,armor_cap_1572_bits:1572,nearby_reduction_1444_bits:1624,hp_1528_bits:1440,shield_1532_bits:1444,barrier_1536_bits:1448,shield_source_1344:1344,shield_source_remaining_1348_bits:1348,reserve_768_bits:768,absorbed_740_bits:740,maximum_shield_744_bits:744,last_hit_1648_bits:1652};

export async function runBrowserResource135(config){
 const importsLog=[],entryCalls=[],resourceProbes=[],results=[],failures=[];
 globalThis.__wenilla_data_base=location.origin+'/data';globalThis.__wenilla_data_layout='static';globalThis.__wenilla_data_stamp='';
 //Enforce the actual V8 page cap before invoking any original function.
 let capVerified=false;try{new WebAssembly.Memory({initial:2049,maximum:2049});}catch(error){if(error instanceof RangeError)capVerified=true;else throw error;}
 if(!capVerified)throw Error('Browser V8 did not enforce2048-page cap');
 const bytes=await(await fetch('/browser.wasm')).arrayBuffer(),moduleHash=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)));
 if(moduleHash!==config.wasm_sha256)throw Error('Browser WASM identity');const module=await WebAssembly.compile(bytes),surface=WebAssembly.Module.imports(module);
 if(surface.length!==878||surface.some((v,i)=>v.name!==config.imports[i].name||v.module!==config.imports[i].module||v.kind!=='function'))throw Error('Import surface');
 const cases=await(await fetch('/fixtures.json')).json();let maxMemory=0;
 for(const c of cases){
  let activeEntry=null;
  const actual=resource135GetImports(),bindings={};
  for(const meta of config.imports){const fn=actual[meta.module]?.[meta.name];if(typeof fn!=='function')throw Error('Official binding absent');bindings[meta.module]??={};
   bindings[meta.module][meta.name]=function(...args){const item={case_id:c.id,id:meta.id,module:meta.module,name:meta.name,allowed:meta.allowed,entry_name:activeEntry?.name??'externref_import_init',entry_sequence:activeEntry?.sequence??null};importsLog.push(item);
    if(!meta.allowed)throw Error('Resource embedding denied import '+meta.id+':'+meta.name);
    try{const ret=fn(...args);item.return_type=typeof ret;return ret;}catch(error){item.threw=String(error);throw error;}};
  }
  const instance=await WebAssembly.instantiate(module,bindings),ex=resource135BindOnly(instance,module),memory=ex.memory;
  const permitted=new Set(['resource135_spell_record','__wbindgen_malloc','research135_spawn_boss','research135_npc_action','research135_effect_tick']);
  function call(name,...args){
   if(!permitted.has(name)||name==='start'||name==='__wbindgen_start')throw Error('Forbidden application entry');
   const entry={case_id:c.id,sequence:entryCalls.length,name,args:args.map(x=>typeof x==='bigint'?String(x):x),once_before:new Uint8Array(memory.buffer)[14384480],memory_before:memory.buffer.byteLength};entryCalls.push(entry);activeEntry=entry;
   try{const result=ex[name](...args);entry.returned=true;entry.once_after=new Uint8Array(memory.buffer)[14384480];entry.memory_after=memory.buffer.byteLength;maxMemory=Math.max(maxMemory,memory.buffer.byteLength);if(memory.buffer.byteLength>config.memory_cap_bytes)throw Error('Original memory budget');return result;}
   finally{activeEntry=null;}
  }
  bindings['./wenilla_bg.js'].__wbindgen_init_externref_table();
  const d=()=>new DataView(memory.buffer),all=()=>new Uint8Array(memory.buffer),r=p=>d().getUint32(p,true),w=(p,x)=>d().setUint32(p,x>>>0,true);
  const beforeOnce=all()[14384480],names=[];
  function probeNames(){for(const[spell,expected]of Object.entries(config.names)){
   const ptr=call('resource135_spell_record',Number(spell));if(!ptr||ptr+24>memory.buffer.byteLength)throw Error('Real4546 record missing');
   const np=r(ptr+4),nl=r(ptr+8);if(nl>1024||np+nl>memory.buffer.byteLength)throw Error('Real4546 name bounds');const name=new TextDecoder('utf-8',{fatal:true}).decode(all().slice(np,np+nl));
   if(name!==expected)throw Error('Actual Spell.dbc parsed name differs');names.push({spell_id:Number(spell),name,record24_hex:hex(all().slice(ptr,ptr+24))});
  }}
  //One direct4546 resource probe first; the other two fresh instances leave
  //Once untouched until the realphase1 915→1073 call performs lazy loading.
  if(c.id===0)probeNames();
  const beforeHitOnce=all()[14384480];
  const allocate=n=>{if(n<1||n>1024*1024)throw Error('Fixture allocation');const p=call('__wbindgen_malloc',n,8)>>>0;if(!p||p+n>memory.buffer.byteLength)throw Error('Allocation bounds');all().fill(0,p,p+n);return p;};
  const s=c.boss,inc=c.incoming,G=allocate(8192),V=allocate(128),U=allocate(128*424),E=allocate(64*120),M=allocate(1024*16),N=allocate(c.zone_id.length);
  const g=(o,x)=>w(G+o,x),b=(o,x)=>d().setUint8(G+o,x),putHex=(p,h)=>all().set(Uint8Array.from(h.match(/../g),v=>parseInt(v,16)),p);
  all().set(new TextEncoder().encode(c.zone_id),N);g(184,N);g(188,c.zone_id.length);g(2348,V);w(V+32,0xffffffff);w(V+56,0xffffffff);w(V+116,s.flat_height_bits);all()[V+120]=1;
  g(1784,128);g(1788,U);g(1792,0);putHex(U,s.initial_slot_hex);g(1808,64);g(1812,E);g(1816,0);c.storage.forEach((h,j)=>putHex(E+j*120,h));
  g(1820,0);g(1824,8);g(1828,0);g(1880,1024);g(1884,M);g(1888,0);g(2356,c.effect_counter2356);g(2412,c.movement_sequence2412);g(1644,c.action_sequence1644);
  g(2352,s.now_bits);g(2516,s.zone_multiplier_bits);b(387,s.difficulty);b(2582,s.mode);g(2540,s.members);g(400,s.victory_field400);g(404,s.endless_start_bits);b(2568,s.endless_flag);g(2408,s.counter);
  s.player_xyz.forEach((x,j)=>g(1416+4*j,x));s.velocity_xy.forEach((x,j)=>g(1736+4*j,x));s.rng_words.forEach((x,j)=>g(1720+4*j,x));g(1432,1);g(1536,c.max_hp_bits);d().setBigUint64(G+1336,999n,true);
  b(360,1);b(361,1);b(2587,inc.phase_2579);b(2576,inc.protection_2568);b(2578,inc.minimum_one_2578);for(const[k,o]of Object.entries(offsets))g(o,inc[k]);d().setFloat64(G+992,inc.incoming_total_992,true);
  let packetCursor=0,jsonCursor=0;const stages=[],physical=[];
  function capture(label){
   const si=stages.length,n=r(G+1816),p=r(G+1812),up=r(G+1788);if(n>64||r(G+1792)!==1||r(G+1808)!==64||r(G+1828)!==0)throw Error('Original vector scope');
   const raw=all().slice(up,up+424),rv=new DataView(raw.buffer),tn=rv.getUint32(244,true),tp=rv.getUint32(248,true);if(tn>20||tp+tn*4>memory.buffer.byteLength)throw Error('Timer bounds');rv.setUint32(248,0,true);
   const output={label,storage:Array.from({length:64},(_,j)=>hex(all().slice(p+j*120,p+(j+1)*120))),length:n,units:[hex(raw)],timers_bits:Array.from({length:tn},(_,j)=>r(tp+j*4)),
    effect_counter2356:r(G+2356),movement_sequence2412:r(G+2412),action_sequence1644:r(G+1644),clock2364_bits:r(G+2364),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),spawn_counter2408:r(G+2408),phase2587:all()[G+2587]};
   for(const[k,o]of Object.entries(offsets))output[k]=r(G+o);output.incoming_total_992_bits=d().getBigUint64(G+992,true).toString(16).padStart(16,'0');
   if(r(G+1888)>1024||r(G+1900)>1024)throw Error('Packet/JSON budget');const packets=[];
   for(let j=0;j<r(G+1888);j++){const q=r(G+1884)+16*j,ptr=r(q+4),len=r(q+8);if(len>65536||ptr+len>memory.buffer.byteLength)throw Error('Packet bounds');packets.push({opcode:d().getUint16(q+12,true),payload_hex:hex(all().slice(ptr,ptr+len))});}
   const json=[];for(let j=0;j<r(G+1900);j++){const q=r(G+1896)+12*j,ptr=r(q+4),len=r(q+8);if(len>65536||ptr+len>memory.buffer.byteLength)throw Error('JSON bounds');json.push(new TextDecoder().decode(all().slice(ptr,ptr+len)));}
   output.new_packet_opcodes=label==='boss2785'?[]:packets.slice(packetCursor).map(x=>x.opcode);
   output.new_effect_json_events=label==='boss2785'?[]:json.slice(jsonCursor).map(x=>{const e=JSON.parse(x);if(e.type==='hz')return{type:e.type,id:e.id,kind:e.kind,shape:e.shape};if(e.type==='hzend')return{type:e.type,id:e.id};if(e.type==='hzt')return{type:e.type};return{type:e.type};});packetCursor=packets.length;jsonCursor=json.length;
   const unitCap=r(G+1784),messageCap=r(G+1880),notificationCap=r(G+1892),notificationPtr=r(G+1896);
   if(unitCap!==128||messageCap!==1024||notificationCap>1024||notificationPtr+notificationCap*12>memory.buffer.byteLength)throw Error('Full backing budget');
   physical.push({packets,effect_json:json,unit248_pointer:tp,full_storage_hex:hex(all().slice(p,p+64*120)),
    raw_G2592_hex:hex(all().slice(G,G+2592)),unit_full_backing_hex:hex(all().slice(up,up+unitCap*424)),timer_full_backing_hex:hex(all().slice(tp,tp+tn*4)),
    message_metadata_full_backing_hex:hex(all().slice(r(G+1884),r(G+1884)+messageCap*16)),
    notification_metadata_full_backing_hex:hex(all().slice(notificationPtr,notificationPtr+notificationCap*12))});
   const expected=c.expected[si];for(const k of Object.keys(expected)){
    if(k==='entry_status')continue;
    if(k==='storage'){
     for(let j=0;j<64;j++){const xb=Uint8Array.from(expected.storage[j].match(/../g),v=>parseInt(v,16)),yb=all().slice(p+j*120,p+(j+1)*120),mask=c.unspecified_storage_bytes[si][j];for(let o=0;o<120;o++)if(!mask.includes(o)&&xb[o]!==yb[o])failures.push({case_id:c.id,stage:si,field:`storage${j}+${o}`,expected:xb[o],actual:yb[o]});}
    }else if(k==='new_packet_opcodes'&&expected.entry_status==='pending_original_spell_database'){
     //Known geometry306 prefix remains exact; genuine1073 continuation may
     //append registry/combatlog packets that this component has not restored.
     if(JSON.stringify(output[k].slice(0,expected[k].length))!==JSON.stringify(expected[k]))failures.push({case_id:c.id,stage:si,field:k,expected:expected[k],actual:output[k]});
    }else if(k==='new_effect_json_events'&&expected.entry_status==='pending_original_spell_database'){
     if(JSON.stringify(output[k].slice(0,expected[k].length))!==JSON.stringify(expected[k]))failures.push({case_id:c.id,stage:si,field:k,expected:expected[k],actual:output[k]});
    }else if(JSON.stringify(output[k])!==JSON.stringify(expected[k]))failures.push({case_id:c.id,stage:si,field:k,expected:expected[k],actual:output[k]});
   }
   stages.push({...output,actual_entry_returned:true,model_status:expected.entry_status});
  }
  call('research135_spawn_boss',G,c.definition_pointer,number(s.scalar_bits));capture('boss2785');all()[V+120]=Number(c.flat_height_enabled);
  for(const op of c.ops){g(2352,op.now_bits);op.player_xyz_bits.forEach((x,j)=>g(1416+4*j,x));for(const[o,v]of Object.entries(op.unit_patch||{})){if(Number(o)===276)all()[U+276]=v;else w(U+Number(o),v);}
   if(op.kind==='produce')call('research135_npc_action',G,0,op.descriptor_pointer);else call('research135_effect_tick',G,number(op.dt_bits));capture(op.kind);
  }
  if(c.id!==0)probeNames();
  resourceProbes.push({case_id:c.id,probe_when:c.id===0?'before_game_hit':'after_cold_game_hit',before_once:beforeOnce,before_hit_once:beforeHitOnce,after_once:all()[14384480],records:names,memory_bytes:memory.buffer.byteLength});
  results.push({case_id:c.id,stages,physical,memory_bytes:memory.buffer.byteLength});
 }
 return{cases:results.length,stages:results.reduce((a,x)=>a+x.stages.length,0),failures,resource_probes:resourceProbes,results,imports:importsLog,entry_calls:entryCalls,
  cap_verified:capVerified,max_memory_bytes:maxMemory,wasm_page_cap:2048,appstart_exports_called:false,finalizer_called:false,original_glue_import_bodies_unchanged:true,
  native_self:typeof self!=='undefined'&&self===window,native_xhr:XMLHttpRequest.prototype.constructor===XMLHttpRequest,local_storage_keys:Object.keys(localStorage),indexeddb_databases:await indexedDB.databases()};
}
