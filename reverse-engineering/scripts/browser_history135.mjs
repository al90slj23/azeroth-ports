// Browser-only actual inputs/capture; independent expectations never arrive.
import {resource135GetImports,resource135BindOnly} from '/bridge.mjs';
const hex = a => Array.from(a,x=>x.toString(16).padStart(2,'0')).join('');
const number = x => {const d=new DataView(new ArrayBuffer(4));d.setUint32(0,x,true);return d.getFloat32(0,true);};
const offsets = {armor_1392_bits:1568,armor_cap_1572_bits:1572,nearby_reduction_1444_bits:1624,
 hp_1528_bits:1440,shield_1532_bits:1444,barrier_1536_bits:1448,shield_source_1344:1344,
 shield_source_remaining_1348_bits:1348,reserve_768_bits:768,absorbed_740_bits:740,
 maximum_shield_744_bits:744,last_hit_1648_bits:1652};

export async function runBrowserHistory135(config) {
 globalThis.__wenilla_data_base=location.origin+'/data';globalThis.__wenilla_data_layout='static';globalThis.__wenilla_data_stamp='';
 let capVerified=false;try{new WebAssembly.Memory({initial:2049,maximum:2049});}catch(e){if(e instanceof RangeError)capVerified=true;else throw e;}
 if(!capVerified)throw Error('V8 memory limit not enforced');
 const input=await(await fetch('/fixtures.json')).json();
 const binary=await(await fetch('/browser.wasm')).arrayBuffer();
 if(hex(new Uint8Array(await crypto.subtle.digest('SHA-256',binary)))!==config.wasm_sha256)throw Error('Original module hash');
 const module=await WebAssembly.compile(binary),surface=WebAssembly.Module.imports(module);
 if(surface.length!==878||surface.some((v,i)=>v.name!==config.imports[i].name||v.module!==config.imports[i].module||v.kind!=='function'))throw Error('Imports differ');
 const importsLog=[],entryCalls=[],results=[];let maxMemory=0;
 for(const c of input){
  if(Object.keys(c).sort().join()!=='capacity,count,group,head,id,input,ops,storage')throw Error('Original input keyset/expected leak');
  let activeEntry=null;const actual=resource135GetImports(),bindings={};
  for(const m of config.imports){const fn=actual[m.module]?.[m.name];if(typeof fn!=='function')throw Error('Official binding missing');bindings[m.module]??={};
   bindings[m.module][m.name]=function(...args){const e={case_id:c.id,id:m.id,module:m.module,name:m.name,allowed:m.allowed,entry_name:activeEntry?.name??'externref_import_init',entry_sequence:activeEntry?.sequence??null};importsLog.push(e);
    if(!m.allowed)throw Error('Resource embedding denied import '+m.id);try{const x=fn(...args);e.return_type=typeof x;return x;}catch(error){e.threw=String(error);throw error;}};
  }
  const instance=await WebAssembly.instantiate(module,bindings),ex=resource135BindOnly(instance,module),memory=ex.memory;
  const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),r=p=>d().getUint32(p,true),w=(p,x)=>d().setUint32(p,x,true);
  function call(name,...args){if(!['__wbindgen_malloc','research135_incoming_damage'].includes(name))throw Error('Disallowed original entry');
   const e={case_id:c.id,sequence:entryCalls.length,name,args:args.map(x=>typeof x==='bigint'?String(x):x),once_before:bytes()[14384480],memory_before:memory.buffer.byteLength};entryCalls.push(e);activeEntry=e;
   try{const ret=ex[name](...args);e.returned=true;e.once_after=bytes()[14384480];e.memory_after=memory.buffer.byteLength;maxMemory=Math.max(maxMemory,memory.buffer.byteLength);if(memory.buffer.byteLength>config.memory_cap_bytes)throw Error('Memory budget');return ret;}finally{activeEntry=null;}}
  bindings['./wenilla_bg.js'].__wbindgen_init_externref_table();
  const allocate=(n,a=8)=>{if(n<1||n>4194304)throw Error('Allocation budget');const p=call('__wbindgen_malloc',n,a)>>>0;if(!p||p+n>memory.buffer.byteLength)throw Error('Allocation bounds');bytes().fill(0,p,p+n);return p;};
  const s=c.input,G=allocate(8192),Q=c.capacity?allocate(c.capacity*48,4):1,g=(o,x)=>w(G+o,x),b=(o,x)=>d().setUint8(G+o,x);
  c.storage.forEach((row,j)=>bytes().set(Uint8Array.from(row.match(/../g),v=>parseInt(v,16)),Q+j*48));g(968,c.capacity);g(972,Q);g(976,c.head);g(980,c.count);
  b(360,1);b(361,1);d().setBigUint64(G+1336,999n,true);g(1432,1);g(1536,s.max_hp_bits);b(2587,s.phase_2579);b(2576,s.protection_2568);b(2582,s.mode_2574);b(2578,s.minimum_one_2578);g(2540,s.wave_2532);
  for(const[k,o]of Object.entries(offsets))g(o,s[k]);d().setFloat64(G+992,s.incoming_total_992,true);
  const name=new TextEncoder().encode(s.map_id),N=allocate(Math.max(1,name.length),1);bytes().set(name,N);g(184,N);g(188,name.length);
  const M=allocate(128*16);g(1880,128);g(1884,M);g(1888,0);
  const slice=(p,n)=>{if(!Number.isInteger(n)||n<0||p<0||p+n>memory.buffer.byteLength)throw Error('Physical bounds');return bytes().slice(p,p+n);};
  const str=(p,n)=>{if(n>1048576)throw Error('String budget');return new TextDecoder('utf-8',{fatal:true}).decode(slice(p,n));};
  const stages=[];
  for(const op of c.ops){
   if(Object.keys(op).sort().join()!=='amount_bits,category,critical,now_bits,spell_id')throw Error('Action keyset');
   g(2352,op.now_bits);const before=slice(G,2592);
   call('research135_incoming_damage',G,number(op.amount_bits),0n,op.critical,op.category,op.spell_id);
   const capacity=r(G+968),ptr=r(G+972),head=r(G+976),count=r(G+980);if(capacity>2048||count>capacity||(capacity&&head>=capacity))throw Error('History header');
   const storage=Array.from({length:capacity},(_,j)=>hex(slice(ptr+j*48,48)));
   const active=Array.from({length:count},(_,j)=>{const slot=(head+j)%capacity,p=ptr+slot*48;return{slot,raw_hex:storage[slot],strings:[0,8,16].map(o=>str(r(p+o),r(p+o+4)))};});
   const scalar={};for(const[k,o]of Object.entries(offsets))scalar[k]=r(G+o);scalar.incoming_total_992_bits=d().getBigUint64(G+992,true).toString(16).padStart(16,'0');scalar.phase_2579=bytes()[G+2587];
   const changes=[],old=new DataView(before.buffer,before.byteOffset,before.byteLength);for(let o=0;o<2592;o+=4)if(old.getUint32(o,true)!==r(G+o))changes.push([o,r(G+o)]);
   const mp=r(G+1884),mc=r(G+1880),ml=r(G+1888),np=r(G+1896),nc=r(G+1892),nl=r(G+1900);if(mc>4096||ml>mc||nc>4096||nl>nc)throw Error('Message bounds');
   const packets=Array.from({length:ml},(_,j)=>{const p=mp+j*16;return{opcode:d().getUint16(p+12,true),capacity:r(p),raw_hex:hex(slice(r(p+4),r(p+8)))};});
   const notifications=Array.from({length:nl},(_,j)=>{const p=np+j*12;return{capacity:r(p),raw_hex:hex(slice(r(p+4),r(p+8)))};});
   stages.push({header:{capacity,head,count},history_pointer:ptr,storage,active,scalar,raw_game2592_hex:hex(slice(G,2592)),game_changes:changes,packets,notifications,
    message_metadata_backing_hex:hex(slice(mp,mc*16)),notification_metadata_backing_hex:hex(slice(np,nc*12))});
  }
  results.push({id:c.id,stages});
 }
 return {status:'captured',cases:results.length,stages:results.reduce((n,r)=>n+r.stages.length,0),results,imports:importsLog,entry_calls:entryCalls,
  cap_verified:capVerified,max_memory_bytes:maxMemory,appstart_exports_called:false,finalizer_called:false,
  native_self:self===window,native_xhr:XMLHttpRequest.prototype.constructor===XMLHttpRequest,
  local_storage_keys:Object.keys(localStorage),indexeddb_databases:await indexedDB.databases()};
}
