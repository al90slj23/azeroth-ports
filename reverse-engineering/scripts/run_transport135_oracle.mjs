// Six unchanged Web32 transport entries. Typed76B cell, no App or clock stub.
import fs from'node:fs/promises';import{createHash}from'node:crypto';
const[dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Explicit32MiB cap');
const m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),raw=await fs.readFile(dir+'/'+m.module_file);
if(hash(raw)!==m.module_sha256||m.original_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||m.roles.map(x=>x.index).join()!=='28425,52236,45626,21513,47313,176109')throw Error('Private source/role identity');
const mod=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(mod),cases=JSON.parse(await fs.readFile(inputFile,'utf8'));
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>128)throw Error('Import/case budget');
let calls=0,peak=0,hostCalls=0;const callCounts={};
for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input')throw Error('Input-only case shape');
 const{initial,operations}=c.input;if(Object.keys(c.input).sort().join()!=='initial,operations'||operations.length>80)throw Error('Input-only bounded operations');
 const bindings={};for(const x of imports){bindings[x.module]??={};bindings[x.module][x.name]=()=>{hostCalls++;throw Error('All878 hosts denied');};}
 const ins=await WebAssembly.instantiate(mod,bindings),ex=ins.exports,memory=ex.memory;
 const b=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),u=p=>d().getUint32(p,true),w=(p,n)=>d().setUint32(p,n>>>0,true);
 function alloc(n,align=4){if(!Number.isInteger(n)||n<1||n>4194304)throw Error('Single4MiB allocation cap');const p=ex.__wbindgen_malloc(n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('32MiB cap');b().fill(0xa5,p,p+n);return p;}
 const hex=(p,n)=>Buffer.from(b().slice(p,p+n)).toString('hex');
 function bytesAt(hexValue){const raw=Buffer.from(hexValue,'hex');if(raw.length>4096)throw Error('Bytepayload cap');const p=raw.length?alloc(raw.length,1):1;if(raw.length)b().set(raw,p);return{p,n:raw.length};}
 function vecBytes(at,hexValue,optional=false){if(hexValue===null){if(!optional)throw Error('Required payload');w(at,0xffffffff);return;}const{p,n}=bytesAt(hexValue);w(at,n);w(at+4,p);w(at+8,n);}
 function readBytes(at,optional=false){const cap=u(at);if(optional&&cap===0xffffffff)return null;const p=u(at+4),n=u(at+8);if(cap>4096||n>cap||p+n>memory.buffer.byteLength)throw Error('Typed payload header');return{capacity:cap,length:n,hex:hex(p,n),pointer:p};}
 function stripPointer(v){if(v===null)return null;const{pointer,...logical}=v;return logical;}
 function rows88(at,rows){const n=rows.length;if(n>64)throw Error('rows88 cap');const p=n?alloc(n*88):4;w(at,n);w(at+4,p);w(at+8,n);for(let j=0;j<n;j++){const r=rows[j],q=p+j*88;if(r.required.length!==3||r.optional.length!==4)throw Error('rows88 typed shape');r.required.forEach((v,k)=>vecBytes(q+k*12,v));r.optional.forEach((v,k)=>vecBytes(q+36+k*12,v,true));w(q+84,r.word84);}return p;}
 function readRows88(at){const cap=u(at);if(cap===0xffffffff)return null;const p=u(at+4),n=u(at+8);if(cap>64||n>cap||p+88*cap>memory.buffer.byteLength)throw Error('rows88 output cap');const rows=[];for(let j=0;j<n;j++){const q=p+j*88;rows.push({required:Array.from({length:3},(_,k)=>stripPointer(readBytes(q+k*12))),optional:Array.from({length:4},(_,k)=>stripPointer(readBytes(q+36+k*12,true))),word84:u(q+84)});}return{capacity:cap,count:n,rows,pointer:p};}
 function rows12(at,rows){const n=rows.length;if(n>64||rows.some(v=>v.length!==24))throw Error('rows12 typed shape');const p=n?alloc(n*12):4;w(at,n);w(at+4,p);w(at+8,n);rows.forEach((v,j)=>b().set(Buffer.from(v,'hex'),p+j*12));return p;}
 function readRows12(at){const cap=u(at);if(cap===0xffffffff)return null;const p=u(at+4),n=u(at+8);if(cap>64||n>cap||p+12*cap>memory.buffer.byteLength)throw Error('rows12 output cap');return{capacity:cap,count:n,hex:hex(p,n*12),pointer:p};}
 function commands(at,rows,count){const cap=rows.length;if(cap>64||count>cap)throw Error('commands typed cap');const p=cap?alloc(cap*232,8):8;w(at,cap);w(at+4,p);w(at+8,count);rows.forEach((r,j)=>{if(r!==null){if(r.length!==464)throw Error('Exact232 bytes');b().set(Buffer.from(r,'hex'),p+j*232);}});}
 function readCommands(at){const cap=u(at),p=u(at+4),count=u(at+8);if(cap>64||count>cap||p+cap*232>memory.buffer.byteLength)throw Error('Command output cap');return{capacity:cap,count,backing_hex:hex(p,cap*232),pointer:p};}
 const cell=alloc(76),transport=alloc(24,8);w(cell,initial.strong);w(cell+4,initial.weak);d().setUint8(cell+8,initial.borrow);
 const ring=initial.ring,cap=ring.storage.length,ptr=cap?alloc(cap*12):4;w(cell+12,cap);w(cell+16,ptr);w(cell+20,ring.head);w(cell+24,ring.count);
 ring.storage.forEach((v,j)=>{if(v!==null)vecBytes(ptr+j*12,v);});
 commands(cell+28,initial.commands.storage,initial.commands.count);vecBytes(cell+40,initial.snapshot,true);
 if(initial.rows88===null)w(cell+52,0xffffffff);else rows88(cell+52,initial.rows88);
 if(initial.rows12===null)w(cell+64,0xffffffff);else rows12(cell+64,initial.rows12);
 w(transport+8,0xffffffff);w(transport+16,cell);d().setUint8(transport+20,0);d().setUint8(transport+21,0);
 function project(){
  const cap=u(cell+12),p=u(cell+16),head=u(cell+20),count=u(cell+24);if(cap>256||count>cap||cap&&head>=cap||p+cap*12>memory.buffer.byteLength)throw Error('Ring projection budget');
  const slots=[];for(let j=0;j<cap;j++){try{slots.push(stripPointer(readBytes(p+j*12)));}catch{slots.push(null);}}
  const r88=readRows88(cell+52),r12=readRows12(cell+64),cmd=readCommands(cell+28);
  return{strong:u(cell),weak:u(cell+4),borrow:d().getUint8(cell+8),timer_absent:u(transport+8)===0xffffffff,
   ring:{capacity:cap,head,count,slots,raw_backing_hex:hex(p,cap*12)},snapshot:stripPointer(readBytes(cell+40,true)),
   rows88:r88===null?null:(({pointer,...x})=>x)(r88),rows12:r12===null?null:(({pointer,...x})=>x)(r12),commands:(({pointer,...x})=>x)(cmd)};
 }
 const stages=[];
 for(const op of operations){
  const name=op.kind,cellBefore=Buffer.from(b().slice(cell,cell+76)),trBefore=hex(transport,24);let moved=null,sourcePreserved=true,deepCopyDistinct=true,answer=null;
  const snapshots=[];const guard=(p,n)=>snapshots.push({p,n,h:hash(b().slice(p,p+n))});
  if(name==='send'||name==='snapshot'){
   const{p,n}=bytesAt(op.hex);guard(p,n);ex[name==='send'?'transport135_send':'transport135_snapshot'](transport,p,n);
   if(n){const dest=name==='snapshot'?u(cell+44):(()=>{const cap=u(cell+12),head=u(cell+20),count=u(cell+24),index=(head+count-1)%cap;return u(u(cell+16)+index*12+4);})();if(dest===p)deepCopyDistinct=false;}
  }else if(name==='rows88'){
   const h=alloc(12),p=rows88(h,op.rows);guard(p,op.rows.length*88);
   const sourcePointers=[];for(let j=0;j<op.rows.length;j++)for(let k=0;k<7;k++){const q=p+j*88+k*12;if(k>=3&&u(q)===0xffffffff)continue;const v=readBytes(q);guard(v.pointer,v.length);sourcePointers.push({row:j,field:k,p:v.pointer,n:v.length});}
   ex.transport135_rows88(transport,p,op.rows.length);const dest=u(cell+56);for(const v of sourcePointers)if(v.n&&u(dest+v.row*88+v.field*12+4)===v.p)deepCopyDistinct=false;
  }else if(name==='rows12'){
   const h=alloc(12),p=rows12(h,op.rows);guard(p,op.rows.length*12);ex.transport135_rows12(transport,p,op.rows.length);
   if(op.rows.length&&u(cell+68)===p)deepCopyDistinct=false;
  }else if(name==='poll'){
   const h=alloc(12),before=readCommands(cell+28);ex.transport135_poll(h,transport);moved=readCommands(h);
   if(moved.pointer!==before.pointer||moved.backing_hex!==before.backing_hex)throw Error('Command vector move did not preserve allocation');
   if(u(cell+28)!==0||u(cell+32)!==8||u(cell+36)!==0)throw Error('Command empty Vec sentinel differs');
   moved=(({pointer,...x})=>x)(moved);
  }else if(name==='false')answer=ex.transport135_false(transport);
  else throw Error('Unapproved operation');
  calls++;callCounts[name]=(callCounts[name]??0)+1;
  for(const s of snapshots)if(hash(b().slice(s.p,s.p+s.n))!==s.h)sourcePreserved=false;
  if(!sourcePreserved||!deepCopyDistinct||trBefore!==hex(transport,24))throw Error('Source/deepcopy/transport invariant');
  const allowed=name==='send'?[8,...Array.from({length:16},(_,i)=>12+i)]:name==='snapshot'?[8,...Array.from({length:12},(_,i)=>40+i)]:name==='rows88'?[8,...Array.from({length:12},(_,i)=>52+i)]:name==='rows12'?[8,...Array.from({length:12},(_,i)=>64+i)]:name==='poll'?[8,...Array.from({length:12},(_,i)=>28+i)]:[];
  for(let j=0;j<76;j++)if(!allowed.includes(j)&&cellBefore[j]!==b()[cell+j])throw Error('Method mutated unrelated cell bytes');
  stages.push({kind:name,state:project(),moved,answer,raw_cell76_hex:hex(cell,76),raw_transport24_hex:hex(transport,24),
   raw_rows88_backing_hex:u(cell+52)===0xffffffff?null:hex(u(cell+56),u(cell+52)*88),
   source_preserved:sourcePreserved,deep_copy_distinct:deepCopyDistinct,unrelated_cell_bytes_preserved:true});
 }
 peak=Math.max(peak,memory.buffer.byteLength);if(hostCalls||memory.buffer.byteLength>33554432)throw Error('Host/memory cap');
 process.stdout.write(JSON.stringify({id:c.id,stages,memory_bytes:memory.buffer.byteLength})+'\n');
}
await fs.writeFile(dir+'/transport135-runtime.json',JSON.stringify({cases:cases.length,calls,call_counts:callCounts,peak_memory_bytes:peak,denied_imports:878,actual_host_calls:hostCalls,
 fresh_instances:cases.length,node:process.version,memory_page_cap:512,cell_bytes:76,transport_bytes:24,default_flags20_21:[0,0],timer_tag8:4294967295,
 appstart_called:false,network_used:false,snapshot_input_used:false,user_saves_accessed:false,shared52_whitelist_changed:false},null,2)+'\n');
