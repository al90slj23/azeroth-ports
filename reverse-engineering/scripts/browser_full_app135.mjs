// Whole original initialization in a fresh isolated origin; no memory writes.
import {fullApp135Start,fullApp135Exports} from '/bridge.mjs';
export async function observeFullApp135(config){
 const imports=[],timers=[],contexts=[],frames=[],progress=[];const callbacks=new WeakMap();
 let activeFrame=null,ex=null,error=null,adapterInfo=null,initializationReturned=false,finalizerEntered=false,hostCalls=0,hostEvents=0;
 globalThis.__rogue_config={glue:'',bg:'',class:'',race:'',name:'',gender:''};
 globalThis.__wenilla_data_layout='static';globalThis.__wenilla_data_base=location.origin+'/data';globalThis.__wenilla_data_stamp='';
 globalThis.__wenilla_env={farclip:'420'};
 globalThis.__wenilla_progress=stage=>progress.push({stage,time:performance.now()});
 if(Object.keys(localStorage).length||Object.keys(sessionStorage).length||(await indexedDB.databases()).length)throw Error('Origin is not fresh');
 const memory=()=>fullApp135Exports()?.memory;
 const u=p=>new DataView(memory().buffer).getUint32(p,true);
 const scalar=x=>typeof x==='bigint'?x.toString():typeof x==='number'||typeof x==='string'||typeof x==='boolean'?x:typeof x;
 function header(App,buffer=memory()?.buffer){
  if(!buffer||App<16||App+5168>buffer.byteLength)throw Error('Observed App outside memory');
  const d=new DataView(buffer),read=p=>d.getUint32(p,true),marker=d.getBigUint64(App,true);return{App,Rc:App-16,strong:read(App-16),weak:read(App-12),borrow:d.getUint8(App-8),borrow_padding_hex:Array.from(new Uint8Array(buffer,App-7,3),x=>x.toString(16).padStart(2,'0')).join(''),
   marker_u64:marker.toString(),previous_bits_u64:d.getBigUint64(App+8,true).toString(),clock_previous_active:marker===1n,previous_seconds:marker===1n?d.getFloat64(App+8,true):null,
   game_tag_u64:d.getBigUint64(App+16,true).toString(),second_tag:read(App+2608),profile_tag:read(App+3376),
   transport_pointer:read(App+4768),transport_vtable:read(App+4772),world_cache:read(App+5116),
   memory_bytes:buffer.byteLength};
 }
 function event(phase,id,name,args,returned){
  if(phase==='original_finalizer_entry'){finalizerEntered=true;return;}
  // Telemetry is bounded without throwing into a valid original callback.
  // The owned wall-clock/process/memory limits bound execution separately.
  hostEvents++;if(phase==='before')hostCalls++;
  if(imports.length<20000)imports.push({phase,id,name,frame:activeFrame?.index??null,args:args.map(scalar),returned:phase==='after'?scalar(returned):undefined});
  if(activeFrame&&phase==='after'&&id===681){activeFrame.original_now_values_ms??=[];activeFrame.original_now_values_ms.push(returned);}
  // Original4253 passes env12/vtable5305816 to this cast. The official
  // makeMutClosure state is private; observe actual arguments/return identity.
  if(phase==='after'&&id===867&&args[1]===5305816&&typeof returned==='function'){
   const env=args[0]>>>0,Rc=u(env+8),App=Rc+16;callbacks.set(returned,{env,Rc,App,vtable:args[1]});
   contexts.push({source:'actual_original_cast867_env12_plus8_AppRc',env,Rc,App,header:header(App),
    closure_env12_hex:Array.from(new Uint8Array(memory().buffer,env,12),x=>x.toString(16).padStart(2,'0')).join(''),
    app5168_hex_at_cast:Array.from(new Uint8Array(memory().buffer,App,5168),x=>x.toString(16).padStart(2,'0')).join('')});
  }
 }
 function wrapArguments(id,args){
  if(id!==517)return args;
  const index=args.findIndex(x=>typeof x==='function'&&callbacks.has(x));if(index<0)return args;
  const original=args[index],identity=callbacks.get(original),row={...identity,interval_ms:args.at(-1),returns:0,errors:[]};timers.push(row);
  const changed=args.slice();
  // Only the scheduling host callback is observed. The original JS closure,
  // its FnMut83825 and its complete880 callee run unchanged on every tick.
  changed[index]=function(...values){
   if(row.returns>=config.frame_budget){clearInterval(row.timer_id);return;}
   const frame={index:frames.length,App:identity.App,before:header(identity.App)};frames.push(frame);activeFrame=frame;
   try{const value=Reflect.apply(original,this,values);frame.returned=true;row.returns++;return value;}
   catch(e){frame.error=String(e.stack||e);row.errors.push(frame.error);error=frame.error;clearInterval(row.timer_id);throw e;}
   finally{frame.after=header(identity.App);
    frame.confirmed_complete880_return=frame.before.borrow===0&&frame.returned===true&&frame.after.borrow===0;
    frame.borrow_gate_status=frame.before.borrow!==0?'original_callback_skipped_or_boundary':frame.after.borrow!==0?'borrow_not_restored_boundary':'eligible_and_restored';
    activeFrame=null;if(row.returns>=config.frame_budget)clearInterval(row.timer_id);}
  };
  callbacks.set(changed[index],identity);row.wrapped_callback=changed[index];return changed;
 }
 function afterCall(id,args,value){
  if(id===517){const callback=args.find(x=>typeof x==='function'&&callbacks.has(x));
   if(callback){const identity=callbacks.get(callback);const row=timers.find(x=>x.App===identity.App&&x.timer_id===undefined);if(row)row.timer_id=value;}}
 }
 try{
  const adapter=await navigator.gpu?.requestAdapter();if(!adapter)throw Error('Actual GPU adapter missing');
  adapterInfo={vendor:adapter.info?.vendor,architecture:adapter.info?.architecture};if(adapterInfo.architecture!==config.expected_adapter_architecture)throw Error('Actual GPU backend differs from frozen gate');
  let cap=false;try{new WebAssembly.Memory({initial:config.memory_page_cap+1,maximum:config.memory_page_cap+1});}catch(e){if(e instanceof RangeError)cap=true;else throw e;}if(!cap)throw Error('WASM page cap not enforced');
  const raw=await(await fetch('/original.wasm')).arrayBuffer();const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)),x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==config.original_sha256)throw Error('Original identity differs');
  const mod=await WebAssembly.compile(raw);ex=await fullApp135Start(mod,event,wrapArguments,afterCall);initializationReturned=true;
  const until=performance.now()+config.observation_seconds*1000;
  while(performance.now()<until&&!timers.some(x=>x.returns>=config.frame_budget||x.errors.length))await new Promise(r=>setTimeout(r,50));
 }catch(e){error=String(e.stack||e);}
 ex=fullApp135Exports()||ex;
 for(const timer of timers)if(timer.timer_id!==undefined)clearInterval(timer.timer_id);
 let capture=null,final_contexts=[];
 if(ex?.memory&&contexts.length){
  const buffer=ex.memory.buffer;if(!(buffer instanceof ArrayBuffer)||buffer.byteLength>config.memory_cap_bytes)throw Error('Unshared memory/copy cap');
  // Single synchronous copy: live render futures may resume during uploads.
  const frozen=new Uint8Array(buffer).slice(),total=frozen.byteLength;
  final_contexts=contexts.map(x=>({...x,final:header(x.App,frozen.buffer)}));
  for(let offset=0;offset<total;offset+=config.capture_chunk_bytes){
   const response=await fetch('/capture/original_app.memory',{method:'POST',headers:{'X-Capture-Offset':String(offset),'X-Capture-Total':String(total)},body:frozen.subarray(offset,Math.min(total,offset+config.capture_chunk_bytes))});
   if(!response.ok)throw Error('Memory capture failed '+response.status);capture=await response.json();
  }
 }
 const confirmed=frames.filter(x=>x.confirmed_complete880_return).length;
 return{status:error?'stopped_at_boundary':confirmed?'observed_original_app_and_complete_idle_tick':'startup_observed_no_confirmed_tick',
  error,adapterInfo,initializationReturned,imports,hostCalls,hostEvents,import_detail_limit:20000,import_details_truncated:hostEvents>imports.length,contexts:final_contexts,timers:timers.map(({wrapped_callback,...x})=>x),frames,progress,capture,
  memory_bytes:ex?.memory?.buffer.byteLength,capture_synchronously_copied_unshared_memory:!!capture,final_header_from_same_frozen_copy:!!capture,
  original_finalizer_entered:finalizerEntered,original_appstart_called:initializationReturned||contexts.length?true:finalizerEntered?null:false,
  original_function_bodies_changed:false,wasm_memory_written_by_research:false,
  native_setInterval_callback_wrapped_for_observation:true,callback_budget:config.frame_budget,confirmed_complete880_returns:confirmed,callback_returns:frames.filter(x=>x.returned).length,
  local_storage_keys:Object.keys(localStorage),session_storage_keys:Object.keys(sessionStorage),indexeddb_databases:await indexedDB.databases(),
  user_profile_used:false,independent_model_cases:0,new_independent_mainloop_frames:0};
}
