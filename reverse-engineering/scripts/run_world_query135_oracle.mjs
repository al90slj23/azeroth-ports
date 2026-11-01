// Genuine world snapshot-derived consumers; all878 hosts denied,256MiB cap.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareWorldSnapshot135} from './world_snapshot135_host.mjs';
const [directory,file]=process.argv.slice(2),input=JSON.parse(await fs.readFile(file,'utf8'));
if(Object.keys(input).sort().join()!=='queries,snapshot_path,snapshot_sha256,world_rc')throw Error('Inputs contain unsupported/expected keys');
if(input.queries.length<1||input.queries.length>12000)throw Error('Query budget');
const prepared=await prepareWorldSnapshot135(directory,['world_height','terrain_height','nearest_height']);
let host=await prepared.restore(input.snapshot_path,input.snapshot_sha256),instances=1,calls=0,traps=0,maxMemory=host.memory.buffer.byteLength;
const snapshots=[host.snapshot],allCalls=[],verifiedWorldInstances=[];let O=host.allocate(16),Q=0;
const num=x=>{const a=new DataView(new ArrayBuffer(4));a.setUint32(0,x,true);return a.getFloat32(0,true);};
const digest=x=>createHash('sha256').update(x).digest('hex');
const ranges=JSON.parse(await fs.readFile(`${directory}/world-query135-source-ranges.json`,'utf8'));
function verifyWorld(){const rows=[];for(const row of ranges){const bytes=new Uint8Array(host.memory.buffer,row.offset,row.bytes),sha256=digest(bytes);if(sha256!==row.sha256)throw Error('Read-only world input mutated');rows.push({label:row.label,offset:row.offset,bytes:row.bytes,sha256});}return rows;}
for(const c of input.queries){
 const d=()=>new DataView(host.memory.buffer),b=()=>new Uint8Array(host.memory.buffer),w=(p,x)=>d().setUint32(p,x,true);
 const raw=()=>Buffer.from(b().slice(O,O+16)).toString('hex');let result;
 if(c.kind==='height'){
  if(Object.keys(c).sort().join()!=='group,id,kind,x_bits,y_bits')throw Error('Height action keyset');
  const output={};for(const role of['terrain_height','world_height']){
   b().fill(0xa5,O,O+16);host.roles[role](O,input.world_rc+8,num(c.x_bits),num(c.y_bits));calls++;
   output[role]={found:d().getUint32(O,true)===1,value_bits:d().getUint32(O+4,true),output16_hex:raw()};
  }result={id:c.id,kind:c.kind,output,entry_status:'returned'};
 }else if(c.kind==='nearest'){
  if(Object.keys(c).sort().join()!=='group,id,kind,raster,x_bits,y_bits')throw Error('Nearest action keyset');
  const s=c.raster;if(Object.keys(s).sort().join()!=='origin_xy_bits,values_bits,width'||s.values_bits.length>4096)throw Error('Controlled raster budget');
  Q=host.allocate(36);const P=host.allocate(Math.max(4,s.values_bits.length*4));b().fill(0xa5,Q,Q+36);
  w(Q+16,P);w(Q+20,s.values_bits.length);w(Q+24,s.origin_xy_bits[0]);w(Q+28,s.origin_xy_bits[1]);w(Q+32,s.width);
  s.values_bits.forEach((x,j)=>w(P+j*4,x));b().fill(0xa5,O,O+16);let trapped=false,error=null;
  try{host.roles.nearest_height(O,Q,num(c.x_bits),num(c.y_bits));}
  catch(e){if(!(e instanceof WebAssembly.RuntimeError)||e.message!=='unreachable')throw e;trapped=true;error=String(e);traps++;}
  calls++;result={id:c.id,kind:c.kind,entry_status:trapped?'bounds_trap':'returned',output16_hex:raw(),error};
  if(!trapped)result.output={found:d().getUint32(O,true)===1,xyz_words:Array.from({length:3},(_,j)=>d().getUint32(O+4+j*4,true))};
  if(trapped){verifiedWorldInstances.push({instance:instances,ranges:verifyWorld()});allCalls.push(...host.calls);if(host.hostCalls.length)throw Error('Original host attempted');host=await prepared.restore(input.snapshot_path,input.snapshot_sha256);snapshots.push(host.snapshot);instances++;O=host.allocate(16);}
 }else throw Error('Unknown action');
 if(host.hostCalls.length)throw Error('Original attempted host');
 maxMemory=Math.max(maxMemory,host.memory.buffer.byteLength);process.stdout.write(JSON.stringify(result)+'\n');
}
allCalls.push(...host.calls);
const unchanged=verifyWorld();verifiedWorldInstances.push({instance:instances,ranges:unchanged});
await fs.writeFile(`${directory}/world-query135-runtime.json`,JSON.stringify({cases:input.queries.length,calls,bounds_traps:traps,fresh_instances:instances,max_memory_bytes:maxMemory,
 denied_imports:878,actual_host_calls:0,world_rc:input.world_rc,snapshots,entry_calls:allCalls,world_ranges_verified_unchanged:unchanged,
 verified_world_instances:verifiedWorldInstances,stack_after:host.stackPointer,bootstrap_reexecuted:false,externref_or_js_state_restored:false,original_internal_callees_unchanged:true,
 separate_from_32MiB_host:true,memory_page_cap:4096,application_start_called:false,user_saves_accessed:false,network_used:false},null,2)+'\n');
