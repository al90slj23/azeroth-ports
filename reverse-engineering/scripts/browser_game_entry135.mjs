// Natural UI entry observer. All original functions/bindings remain delegated.
import {fullApp135Start,fullApp135Exports} from '/bridge.mjs';

export async function observeGameEntry135(config){
 const imports=[],timers=[],contexts=[],frames=[],progress=[],commands=[],checkpoints=[],violations=[],observerBoundaries=[];
 const callbacks=new WeakMap(),hostCounts=new Uint32Array(878);
 const originalRAFHandles=new Set();let postFreezeRAFCancellation=null,metadataReceipt=null;
 let activeFrame=null,error=null,adapterInfo=null,initializationReturned=false,finalizerEntered=false;
 let stopped=null,finished=false,hostCalls=0,hostEvents=0,runningReturns=0,clockAdvances=0,lastRunningClock=null;
 const exports=()=>fullApp135Exports(),memory=()=>exports()?.memory;
 const stack=()=>exports()?.research_game_entry135_stack?.value??null;
 const scalar=x=>typeof x==='bigint'?x.toString():['number','string','boolean'].includes(typeof x)?x:typeof x;
 const hex=a=>Array.from(a,x=>x.toString(16).padStart(2,'0')).join('');
 function bytes(buffer,p,n){if(!Number.isSafeInteger(p)||!Number.isSafeInteger(n)||p<0||n<0||p+n>buffer.byteLength)throw Error('Read-only observer bounds');return new Uint8Array(buffer,p,n);}
 function header(App,buffer=memory()?.buffer){
  if(!buffer||App<16||App+5168>buffer.byteLength)throw Error('Observed App bounds');
  const d=new DataView(buffer),u=p=>d.getUint32(p,true),G=App+16,tag=d.getBigUint64(G,true),present=tag===0n;
  const base={App,Rc:App-16,strong:u(App-16),weak:u(App-12),borrow:d.getUint8(App-8),stack_observed:stack(),
   app_marker_u64:d.getBigUint64(App,true).toString(),app_previous_seconds:d.getBigUint64(App,true)===1n?d.getFloat64(App+8,true):null,
   game_tag_u64:tag.toString(),game_present:present,second_tag:u(App+2608),profile_tag:u(App+3376),
   transport_pointer:u(App+4768),transport_vtable:u(App+4772),world_cache:u(App+5116),
   app_lcg_u64:d.getBigUint64(App+4928,true).toString(),memory_bytes:buffer.byteLength};
  if(present){
   base.game={start_flag:d.getUint8(G+2575),mode:d.getUint8(G+2582),deny_flags:d.getUint8(G+2583),phase:d.getUint8(G+2587),global_phase:d.getUint8(G+2588),start_block:u(G+2528),
    clock_bits:u(G+2352),clock:d.getFloat32(G+2352,true),world_rc:u(G+2348),xyz_bits:[u(G+1416),u(G+1420),u(G+1424)],heading_bits:u(G+1428),
    units:u(G+1792),areas:u(G+1804),pickups:u(G+1876),candidates:u(G+1912),companions:u(G+2116)};
   base.running=(base.game.mode===0?base.game.phase:base.game.global_phase)===1;
  }else base.running=false;
  return base;
 }
 function checkpoint(label,App,buffer=memory().buffer){
  const d=new DataView(buffer),u=p=>d.getUint32(p,true),G=App+16,h=header(App,buffer);
  const row={label,frame:activeFrame?.index??null,header:h,app5168_hex:hex(bytes(buffer,App,5168)),vectors:[]};
  if(h.game_present){
   let total=0;
   for(const [name,offset,stride]of[['owned',1656,80],['live',1704,32],['units',1784,424],['areas',1796,88],['effects',1808,120],['delayed',1820,56],['deadline',1832,32],['hits',1844,112],['secondary',1856,112],['pickups',1868,56],['packets',1880,16],['notifications',1892,12],['candidates',1904,80],['special',1916,40],['windows',1964,8],['companions',2108,88],['boundaries',2120,8],['xp',2144,8],['currency',2156,8]]){
    const cap=u(G+offset),ptr=u(G+offset+4),len=u(G+offset+8),size=len*stride;
    const vector={name,cap,ptr,len,stride};
    if(len>cap)throw Error('Observed active vector length exceeds capacity');
    if(size<=config.checkpoint_byte_budget-total){vector.active_hex=hex(bytes(buffer,ptr,size));total+=size;}
    else vector.capture_boundary='Declared checkpoint-byte budget; no zero substitution';
    row.vectors.push(vector);
   }
   row.active_vector_bytes_copied=total;
  }
  checkpoints.push(row);
 }
 function queue(App){
  const buffer=memory().buffer,d=new DataView(buffer),u=p=>d.getUint32(p,true),T=u(App+4768);
  if(!T)return null;bytes(buffer,T,24);const C=u(T+16);if(!C)return null;bytes(buffer,C,76);
  const cap=u(C+28),ptr=u(C+32),len=u(C+36);if(len>cap)throw Error('Observed transport vector length exceeds capacity');
  if(!len)return null;
  if(commands.length>=config.command_observation_budget)return{recorded:false,len};
  const row={frame:frames.length,App,transport:T,cell:C,cap,ptr,len,entries:[],app_before_header:header(App)};
  for(let i=0;i<Math.min(len,config.command_rows_per_observation);i++){
   const p=ptr+232*i;row.entries.push({index:i,raw_tag:u(p),raw232_hex:hex(bytes(buffer,p,232)),nested_pointer_payloads:'Opaque; not inferred from possible pointer-looking words'});
  }
  row.all_rows_captured=row.entries.length===len;commands.push(row);return{recorded:true,index:commands.length-1,len};
 }
 function status(){
  let h=null;try{if(contexts.length&&memory())h=header(contexts.at(-1).App);}catch(e){return{ready:false,finished,error:String(e)};}
  return{ready:progress.some(x=>x.stage==='startup')&&!!h&&frames.some(x=>x.returned),App:h?.App??null,game_present:h?.game_present??false,running:h?.running??false,clock:h?.game?.clock??null,
   callback_returns:frames.filter(x=>x.returned).length,running_returns:runningReturns,clock_advances:clockAdvances,finished,error,stopped,progress};
 }
 globalThis.__gameEntry135Control=Object.freeze({status,requestStop(reason){stopped=String(reason);}});
 globalThis.__rogue_config={glue:'',bg:'',class:'',race:'',name:'',gender:''};
 globalThis.__wenilla_data_layout='static';globalThis.__wenilla_data_base=location.origin+'/data';globalThis.__wenilla_data_stamp='';
 globalThis.__wenilla_env={farclip:'420'};
 globalThis.__wenilla_progress=stage=>progress.push({stage,time:performance.now()});
 addEventListener('securitypolicyviolation',e=>{if(violations.length<100)violations.push({blockedURI:e.blockedURI,effectiveDirective:e.effectiveDirective,disposition:e.disposition});});
 if(Object.keys(localStorage).length||Object.keys(sessionStorage).length||(await indexedDB.databases()).length)throw Error('Origin is not fresh');
 function event(phase,id,name,args,returned){
  if(phase==='original_finalizer_entry'){finalizerEntered=true;return;}
  hostEvents++;if(phase==='before'){hostCalls++;hostCounts[id]++;}
  if(imports.length<config.host_detail_budget)imports.push({phase,id,name,frame:activeFrame?.index??null,args:args.map(scalar),returned:phase==='after'?scalar(returned):undefined});
  if(activeFrame&&phase==='after'&&id===681){activeFrame.original_now_values_ms??=[];activeFrame.original_now_values_ms.push(returned);}
  if(phase==='after'&&id===507&&typeof returned==='number')originalRAFHandles.add(returned);
  if(phase==='after'&&id===867&&args[1]===5305816&&typeof returned==='function'){
   const env=args[0]>>>0,d=new DataView(memory().buffer),Rc=d.getUint32(env+8,true),App=Rc+16;
   const identity={env,Rc,App,vtable:args[1]};callbacks.set(returned,identity);
   contexts.push({...identity,header:header(App),closure_env12_hex:hex(bytes(memory().buffer,env,12)),app5168_hex_at_cast:hex(bytes(memory().buffer,App,5168))});
  }
 }
 function wrapArguments(id,args){
  if(id!==517)return args;
  const index=args.findIndex(x=>typeof x==='function'&&callbacks.has(x));if(index<0)return args;
  const original=args[index],identity=callbacks.get(original),row={...identity,interval_ms:args.at(-1),returns:0,errors:[]};timers.push(row);
  const changed=args.slice();
  function observerBoundary(e,stage,frame=null){
   const detail={stage,frame:frame?.index??null,error:String(e.stack||e)};observerBoundaries.push(detail);
   if(frame)frame.observer_error=detail;
   error??='Research observer boundary: '+detail.error;stopped??='observer_boundary';clearInterval(row.timer_id);
  }
  changed[index]=function(...values){
   if(stopped||row.returns>=config.callback_budget){clearInterval(row.timer_id);return;}
   let frame;
   try{
    frame={index:frames.length,App:identity.App,before:header(identity.App)};
    frame.commands=queue(identity.App);frames.push(frame);activeFrame=frame;
   }catch(e){observerBoundary(e,'before_original_callback',frame);return;}
   try{const value=Reflect.apply(original,this,values);frame.returned=true;row.returns++;return value;}
   catch(e){frame.error=String(e.stack||e);row.errors.push(frame.error);error=frame.error;stopped='original_callback_boundary';clearInterval(row.timer_id);throw e;}
   finally{
    try{
     frame.after=header(identity.App);
     frame.confirmed_complete880_return=frame.before.borrow===0&&frame.returned===true&&frame.after.borrow===0&&frame.before.stack_observed!==null&&frame.before.stack_observed===frame.after.stack_observed;
     if(!frame.before.game_present&&frame.after.game_present)checkpoint('natural_Game_install',identity.App);
     if(frame.confirmed_complete880_return&&frame.after.running){
      runningReturns++;if(lastRunningClock!==null&&frame.after.game.clock>lastRunningClock)clockAdvances++;lastRunningClock=frame.after.game.clock;
      if(runningReturns===1)checkpoint('first_running_callback_return',identity.App);
      if(runningReturns>=config.running_return_budget&&clockAdvances>0)stopped='running_callback_budget_reached';
     }
    }catch(e){observerBoundary(e,'after_original_callback',frame);}
    activeFrame=null;
    if(row.returns>=config.callback_budget)stopped??='callback_budget_reached';
    if(stopped)clearInterval(row.timer_id);
   }
  };
  callbacks.set(changed[index],identity);row.wrapped_callback=changed[index];return changed;
 }
 function afterCall(id,args,value){
  if(id===517){const callback=args.find(x=>typeof x==='function'&&callbacks.has(x));if(callback){const identity=callbacks.get(callback);const row=timers.find(x=>x.App===identity.App&&x.timer_id===undefined);if(row)row.timer_id=value;}}
 }
 try{
  const adapter=await navigator.gpu?.requestAdapter();if(!adapter)throw Error('Actual GPU adapter missing');
  adapterInfo={vendor:adapter.info?.vendor,architecture:adapter.info?.architecture};if(adapterInfo.architecture!==config.expected_adapter_architecture)throw Error('GPU backend differs from frozen gate');
  let capped=false;try{new WebAssembly.Memory({initial:config.memory_page_cap+1,maximum:config.memory_page_cap+1});}catch(e){if(e instanceof RangeError)capped=true;else throw e;}if(!capped)throw Error('WASM page cap not enforced');
  const raw=await(await fetch('/original.wasm')).arrayBuffer(),digest=hex(new Uint8Array(await crypto.subtle.digest('SHA-256',raw)));
  if(digest!==config.module_sha256)throw Error('Private observer-module identity differs');
  const module=await WebAssembly.compile(raw);await fullApp135Start(module,event,wrapArguments,afterCall);initializationReturned=true;
  const until=performance.now()+config.observation_seconds*1000;
  while(performance.now()<until&&!stopped&&!error)await new Promise(r=>setTimeout(r,25));
  stopped??='observation_deadline';
 }catch(e){error=String(e.stack||e);stopped??='initialization_or_observer_boundary';}
 for(const timer of timers)if(timer.timer_id!==undefined)clearInterval(timer.timer_id);
 let capture=null,finalContexts=[],frozenStack=null;
 if(memory()&&contexts.length){
  const buffer=memory().buffer;if(!(buffer instanceof ArrayBuffer)||buffer.byteLength>config.memory_cap_bytes)throw Error('Unshared memory/copy budget');
  frozenStack=stack();const frozen=new Uint8Array(buffer).slice(),total=frozen.byteLength;
  finalContexts=contexts.map(x=>({...x,final:header(x.App,frozen.buffer)}));
  // Terminate observed renderer scheduling only AFTER the coherent copy. This
  // does not change any original frame or the captured memory. JS/externrefs,
  // future callbacks and destructor lifetime are not claimed to be restored.
  for(const handle of originalRAFHandles)cancelAnimationFrame(handle);
  postFreezeRAFCancellation={after_synchronous_memory_copy:true,original_import:507,
    observed_handles_cancelled:originalRAFHandles.size,original_frames_before_copy_unchanged:true,
    shutdown_or_Rc_destructor_equivalence_claimed:false};
  const preliminary={version:'0.135.1',build:'0898d5e3',original_sha256:config.original_sha256,module_sha256:config.module_sha256,
   kind:'original_UI_Game_observation_saved_before_bulk_capture_not_independent_model',error,stopped,
   adapterInfo,initializationReturned,original_finalizer_entered:finalizerEntered,
   contexts:finalContexts,frames,commands,checkpoints,progress,observerBoundaries,
   timers:timers.map(({wrapped_callback,...x})=>x),imports,hostCalls,hostEvents,host_import_calls:Array.from(hostCounts),
   security_policy_violations:violations,confirmed_complete880_returns:frames.filter(x=>x.confirmed_complete880_return).length,
   running_complete880_returns:runningReturns,clock_advances:clockAdvances,capture_stack_observed:frozenStack,
   snapshot_total_bytes:total,capture_synchronously_copied_unshared_memory:true,final_header_from_same_frozen_copy:true,
   post_freeze_RAF_cancellation:postFreezeRAFCancellation,bulk_memory_capture_complete:false,
   original_function_bodies_changed:false,wasm_memory_written_by_research:false,global_value_written_by_research:false,
   independent_model_cases:0,new_independent_mainloop_frames:0,complete_game:false};
  const metadata=await fetch('/capture/observation.json',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(preliminary)});
  if(!metadata.ok)throw Error('Pre-upload observation persistence failed '+metadata.status);metadataReceipt=await metadata.json();
  // One coherent byte copy, not asynchronous chunks of changing live memory.
  for(let offset=0;offset<total;offset+=config.capture_chunk_bytes){
   const response=await fetch('/capture/original_game.memory',{method:'POST',headers:{'X-Capture-Offset':String(offset),'X-Capture-Total':String(total)},body:frozen.subarray(offset,Math.min(total,offset+config.capture_chunk_bytes))});
   if(!response.ok)throw Error('Memory upload failed '+response.status);capture=await response.json();
  }
 }
 finished=true;
 const confirmed=frames.filter(x=>x.confirmed_complete880_return).length;
 return{status:error?'stopped_at_boundary':runningReturns>=config.running_return_budget&&clockAdvances>0?'observed_natural_Game_running_complete880_returns':'observed_before_active_Game_boundary',error,stopped,adapterInfo,initializationReturned,observerBoundaries,
  imports,hostCalls,hostEvents,host_import_calls:Array.from(hostCounts),import_detail_limit:config.host_detail_budget,import_details_truncated:hostEvents>imports.length,
  contexts:finalContexts,timers:timers.map(({wrapped_callback,...x})=>x),frames,commands,checkpoints,progress,security_policy_violations:violations,
  capture,capture_stack_observed:frozenStack,capture_synchronously_copied_unshared_memory:!!capture,final_header_from_same_frozen_copy:!!capture,
  pre_upload_observation_receipt:metadataReceipt,post_freeze_RAF_cancellation:postFreezeRAFCancellation,
  memory_bytes:memory()?.buffer.byteLength,original_finalizer_entered:finalizerEntered,confirmed_complete880_returns:confirmed,running_complete880_returns:runningReturns,clock_advances:clockAdvances,
  original_function_bodies_changed:false,export_section_added_mutable_global_read_by_research_only:true,wasm_memory_written_by_research:false,global_value_written_by_research:false,
  synthetic_App_Game_profile_world_or_command_injected:false,callback_wrapped_for_observation:true,callback_budget:config.callback_budget,running_return_budget:config.running_return_budget,
  local_storage_keys:Object.keys(localStorage),session_storage_keys:Object.keys(sessionStorage),indexeddb_databases:await indexedDB.databases(),
  user_profile_used:false,independent_model_cases:0,new_independent_mainloop_frames:0,complete_game:false};
}
