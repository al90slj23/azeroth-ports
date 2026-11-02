// Fresh loopback-only research origin. Never bind the user's game/profile.
import{entry139GetImports,entry139BindOnly}from'/bridge.mjs';
const hex=a=>Array.from(a,x=>x.toString(16).padStart(2,'0')).join('');
export async function runEntryWorld139(c){
 const imports=[],entries=[],snapshots=[];let active=null,currentMemory=null,App=0,G=0,error=null;
 globalThis.__wenilla_data_base=location.origin+'/data';globalThis.__wenilla_data_layout='static';globalThis.__wenilla_data_stamp='';
 if(Object.keys(localStorage).length||Object.keys(sessionStorage).length||(await indexedDB.databases()).length)throw Error('Origin not empty');
 let cap=false;try{new WebAssembly.Memory({initial:c.memory_page_cap+1,maximum:c.memory_page_cap+1});}catch(e){if(e instanceof RangeError)cap=true;else throw e;}if(!cap)throw Error('V8 page cap not enforced');
 const raw=await(await fetch('/entry.wasm')).arrayBuffer(),hash=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)));if(hash!==c.wasm_sha256)throw Error('Frozen module identity');
 const mod=await WebAssembly.compile(raw),surface=WebAssembly.Module.imports(mod);if(surface.length!==882)throw Error('Import surface');
 const real=entry139GetImports(),bindings={};
 for(const m of c.imports){if(surface[m.id].name!==m.name||surface[m.id].module!==m.module||surface[m.id].kind!=='function')throw Error('Import identity');
  const fn=real[m.module]?.[m.name];if(typeof fn!=='function')throw Error('Official import missing');bindings[m.module]??={};
  bindings[m.module][m.name]=function(...args){const row={id:m.id,name:m.name,allowed:m.allowed,entry:active?.name??'externref_initialization'};imports.push(row);
   if(!m.allowed)throw Error('Denied original import '+m.id+':'+m.name);
   if(m.name==='__wbg_getItem_4f09713b84e02011'){row.storage_key=new TextDecoder().decode(new Uint8Array(currentMemory.buffer,args[2],args[3]));row.storage_has_key=localStorage.getItem(row.storage_key)!==null;}
   try{const out=fn(...args);row.return_type=typeof out;return out;}catch(e){row.error=String(e);throw e;}};
 }
 const ins=await WebAssembly.instantiate(mod,bindings),ex=entry139BindOnly(ins,mod),memory=ex.memory;currentMemory=memory;
 if(ex.entry139_stack0.value!==1048576)throw Error('139 initial stack');
 const b=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),r=p=>d().getUint32(p,true),w=(p,x)=>d().setUint32(p,x>>>0,true);
 const permitted=new Set([...c.roles.map(x=>x.name),'__wbindgen_malloc']);let maxMemory=memory.buffer.byteLength;
 function call(name,...args){if(!permitted.has(name))throw Error('Unapproved entry');const row={name,args:args.map(x=>typeof x==='bigint'?String(x):x),sequence:entries.length,memory_before:memory.buffer.byteLength,stack_before:ex.entry139_stack0.value};entries.push(row);active=row;
  try{const result=ex[name](...args);row.returned=true;row.stack_after=ex.entry139_stack0.value;if(row.stack_after!==row.stack_before)throw Error('139 original stack not restored');row.memory_after=memory.buffer.byteLength;maxMemory=Math.max(maxMemory,memory.buffer.byteLength);if(maxMemory>c.memory_cap_bytes)throw Error('Memory cap');return result;}
  catch(e){row.error=String(e);row.stack=String(e.stack);throw e;}finally{active=null;}}
 bindings['./wenilla_bg.js'].__wbindgen_init_externref_table();
 function alloc(n,fill=0){if(n<1||n>65536)throw Error('Explicit input allocation limit');const p=call('__wbindgen_malloc',n,8)>>>0;if(!p||p+n>memory.buffer.byteLength)throw Error('Allocation bounds');b().fill(fill,p,p+n);return p;}
 async function snapshot(label,full=false){
  const p=App?r(App+5116):0,row={label,memory_bytes:memory.buffer.byteLength,App,G,app5168_hex:App?hex(b().slice(App,App+5168)):null,
   game2592_hex:G?hex(b().slice(G,G+2592)):null,world_rc_pointer:p,world_rc124_hex:p&&p+124<=memory.buffer.byteLength?hex(b().slice(p,p+124)):null,
   phase2587:G?b()[G+2587]:null,npc_count:G?r(G+1792):null,pickup_count:G?r(G+1876):null,storage_keys:Object.keys(localStorage)};
  // Entire memory preserves real pointer targets/raw geometry/queues; no guessed projection.
  const total=memory.buffer.byteLength;let artifact;
  if(!full){snapshots.push(row);return row;}
  for(let offset=0;offset<total;offset+=c.capture_chunk_bytes){const response=await fetch('/capture/'+label+'.memory',{method:'POST',
    headers:{'Content-Type':'application/octet-stream','X-Capture-Offset':String(offset),'X-Capture-Total':String(total)},body:b().subarray(offset,Math.min(total,offset+c.capture_chunk_bytes))});
   if(!response.ok)throw Error('Raw memory capture failed '+response.status);artifact=await response.json();}
  if(!artifact.complete||artifact.bytes!==total)throw Error('Incomplete full-memory artifact');row.memory_artifact=artifact;snapshots.push(row);return row;
 }
 try{
  App=alloc(c.app_input.allocation_bytes,c.app_input.initial_poison);G=alloc(8192,c.app_input.initial_poison);
  // Explicit372 live bytes of previously scoped empty selected376 input, an explicit research profile input; not natural menu/App production. Companion tags below come from actual2945.
  const P=App+3376;b().fill(0,P,P+376);const name=new TextEncoder().encode(c.selected_profile_input.region_id),np=alloc(name.length);b().set(name,np);
  w(P+156,4);w(P+168,np);w(P+172,name.length);d().setBigUint64(P+176,BigInt(c.selected_profile_input.object_id_u64),true);
  b()[P+344]=c.selected_profile_input.class_byte;b()[P+345]=c.selected_profile_input.race_byte;d().setBigUint64(App+4928,BigInt(c.selected_profile_input.app_lcg_seed_u64),true);
  w(App+5116,0);d().setBigUint64(App+4776,0n,true);w(App+5163,c.app_input.flags5163_u32);
  // Exact1394339 vtable and declared research transport layout; not fullApp production.6786 uses original vtable+32 →177894, constant0.
  const transport=alloc(24),cell=alloc(64);w(cell,1);w(cell+4,1);w(cell+32,8);w(cell+40,0xffffffff);w(transport+8,0xffffffff);w(transport+16,cell);w(App+4768,transport);w(App+4772,1410440);
  snapshots.push({label:'declared_input_before_account',App,G,app5168_hex:hex(b().slice(App,App+5168)),selected376_hex:hex(b().slice(P,P+376)),world_cache5116:r(App+5116),storage_keys:Object.keys(localStorage)});
  call('entry139_load_account',App+4160);await snapshot('after_real_account2917');
  const slots=alloc(16,0xa5);call('entry139_companion_selection',slots,App+4160);
  if(b()[slots+4]!==255||b()[slots+12]!==255)throw Error('Empty-account absent companion producer boundary');
  b().set(b().slice(slots,slots+16),P+224);await snapshot('after_real_companion_selection2945');
  call('entry139_construct_world_game',G,App);const world=await snapshot('after_real_world6786',true);
  const resourceStatus=await(await fetch('/asset-status')).json();world.resource_status=resourceStatus;
  if(resourceStatus.non200.length)throw Error('Actual asset service boundary;1108 not entered: '+JSON.stringify(resourceStatus.non200));
  if(d().getBigUint64(G,true)===2n||!world.world_rc_pointer||!world.world_rc124_hex)throw Error('6786 did not produce a real game/world');
  if(r(G+2348)!==world.world_rc_pointer)throw Error('Game does not own exact producer world Rc');
  // Direct original1108 component, preserving all internal opening calls and real world.
  call('entry139_begin_run',G);await snapshot('after_real_begin1108',true);
 }catch(e){error={message:String(e),stack:String(e.stack),stage:entries.at(-1)?.name};try{await snapshot('error_stop');}catch(capture){error.capture_error=String(capture);}}
 return{status:error?'stopped_at_boundary':'original_entry_returned',error,entries,imports,snapshots,max_memory_bytes:Math.max(maxMemory,memory.buffer.byteLength),
  page_cap_negative_checked:cap,all_storage_keys:Object.keys(localStorage),session_keys:Object.keys(sessionStorage),indexeddb_databases:await indexedDB.databases(),
  appstart_exports_called:false,finalizer_called:false,selected_profile_producer_complete:false,independent_model_cases:0};
}
