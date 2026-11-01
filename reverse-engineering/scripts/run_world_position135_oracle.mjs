// Full original8751/13516 over pinned snapshot-derived explicit geometry.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareWorldSnapshot135} from './world_snapshot135_host.mjs';
const [directory,configFile]=process.argv.slice(2),config=JSON.parse(await fs.readFile(configFile,'utf8'));
const hash=x=>createHash('sha256').update(x).digest('hex');
const raw=await fs.readFile(config.input_path);if(hash(raw)!==config.input_sha256||raw.length>32*1024*1024)throw Error('Frozen input identity/budget');
const cases=JSON.parse(raw),keys='group,id,input,kind,world';if(!cases.length||cases.length>300)throw Error('Case count');
const prepared=await prepareWorldSnapshot135(directory,['spawn_position','random_position']);
const number=x=>{const b=new DataView(new ArrayBuffer(4));b.setUint32(0,x,true);return b.getFloat32(0,true);};
let maxMemory=0,originalCalls=0,allocatorCalls=0,gameBytesChecked=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!==keys||!['spawn','random'].includes(c.kind))throw Error('Input-only keyset');
 const host=await prepared.restore(config.snapshot_path,config.snapshot_sha256),{memory,roles,allocate,hostCalls}=host;
 const d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer),u=p=>d().getUint32(p,true),w=(p,v)=>d().setUint32(p,v>>>0,true);
 const G=config.game_pointer,actualWorld=u(G+2348),initialWorld=b().slice(actualWorld,actualWorld+124),arrays=[];
 if(actualWorld!==config.world_pointer)throw Error('Real snapshot world identity');
 const alloc=(n,align=8)=>{allocatorCalls++;return allocate(n,align);};
 function controlled(desc){
  const R=alloc(124),bytes=b();bytes.fill(0,R,R+124);w(R,1);w(R+4,1);
  w(R+12,4);w(R+24,4);w(R+32,0xffffffff);w(R+56,0xffffffff);w(R+92,0xffffffff);
  w(R+116,desc.fallback_height_bits);bytes[R+120]=desc.flat_height_bits===null?0:1;
  if(desc.flat_height_bits!==null)w(R+116,desc.flat_height_bits);
  if(desc.nav){
   const n=Buffer.from(desc.nav.values_hex,'hex'),p=alloc(Math.max(8,n.length));b().set(n,p);w(R+32,n.length);w(R+36,p);w(R+40,n.length);
   w(R+44,desc.nav.origin_xy_bits[0]);w(R+48,desc.nav.origin_xy_bits[1]);w(R+52,desc.nav.width);arrays.push({p,n:n.length,sha256:hash(n)});
  }
  for(const[name,tag,ptr,len,origin,width]of[['primary',56,72,76,80,88],['secondary',92,96,100,104,112]]){
   const value=desc[name];if(!value)continue;const p=alloc(Math.max(8,value.values_bits.length*4));value.values_bits.forEach((x,j)=>w(p+j*4,x));
   w(R+tag,0);w(R+ptr,p);w(R+len,value.values_bits.length);w(R+origin,value.origin_xy_bits[0]);w(R+origin+4,value.origin_xy_bits[1]);w(R+width,value.width);
   arrays.push({p,n:value.values_bits.length*4,sha256:hash(b().subarray(p,p+value.values_bits.length*4))});
  }
  return R;
 }
 const R=c.world===null?actualWorld:controlled(c.world),state=c.input;
 if(state.zone!==0)throw Error('Current realworld and controlled corpus is explicitElwynn');
 w(G+2348,R);state.player_xyz.forEach((x,j)=>w(G+1416+j*4,x));state.velocity_xy.forEach((x,j)=>w(G+1736+j*4,x));state.rng_words.forEach((x,j)=>w(G+1720+j*4,x));
 if(state.distance_map){
  const map=state.distance_map,P=alloc(32),V=alloc(Math.max(8,map.values_u16.length*2),2);b().fill(0,P,P+32);w(P,1);w(P+4,1);
  map.values_u16.forEach((x,j)=>d().setUint16(V+j*2,x,true));w(P+8,map.values_u16.length);w(P+12,V);w(P+16,map.values_u16.length);w(P+24,map.field24);w(G+2368,P);
  arrays.push({p:V,n:map.values_u16.length*2,sha256:hash(b().subarray(V,V+map.values_u16.length*2))});
 }else w(G+2368,0);
 const O=alloc(16);b().fill(0xa5,O,O+16);const before=b().slice(G,G+2592),worldBefore=b().slice(R,R+124);
 if(c.kind==='spawn')roles.spawn_position(O,G,number(state.low_radius_bits),number(state.high_radius_bits),number(state.bias_probability_bits));
 else roles.random_position(O,G,number(state.low_radius_bits),number(state.high_radius_bits));originalCalls++;
 if(hostCalls.length||host.stackPointer!==1048576)throw Error('Host or stack boundary');
 const changes=[],old=new DataView(before.buffer,before.byteOffset,before.byteLength);
 for(let o=0;o<2592;o+=4){const prev=old.getUint32(o,true),value=u(G+o);if(prev!==value)changes.push([o,value]);}
 if(changes.some(([o])=>o<1720||o>1732))throw Error('Original sampler mutates unmodeledGame words');
 if(!Buffer.from(b().subarray(R,R+124)).equals(Buffer.from(worldBefore)))throw Error('Original mutates explicit world record');
 if(!Buffer.from(b().subarray(actualWorld,actualWorld+124)).equals(Buffer.from(initialWorld)))throw Error('Original real world record changed');
 for(const x of arrays)if(hash(b().subarray(x.p,x.p+x.n))!==x.sha256)throw Error('Original mutates explicit geometry/path arrays');
 const projection={position_bits:[0,1,2].map(j=>u(O+j*4)),rng_words:[0,1,2,3].map(j=>u(G+1720+j*4))};
 const expectedChanges=projection.rng_words.map((v,j)=>[1720+j*4,v]).filter(([o,v])=>old.getUint32(o,true)!==v);
 if(JSON.stringify(changes)!==JSON.stringify(expectedChanges))throw Error('Exact completeGame mutation domain');
 gameBytesChecked+=2592;maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,projection,raw_game_before_hex:Buffer.from(before).toString('hex'),raw_game_after_hex:Buffer.from(b().subarray(G,G+2592)).toString('hex'),
  game_changes:changes,world_record_before_hex:Buffer.from(worldBefore).toString('hex'),world_record_after_hex:Buffer.from(b().subarray(R,R+124)).toString('hex'),
  output16_hex:Buffer.from(b().subarray(O,O+16)).toString('hex'),arrays_unchanged:arrays,snapshot:host.snapshot,calls:host.calls,stack_after:host.stackPointer})+'\n');
}
await fs.writeFile(`${directory}/world-position135-runtime.json`,JSON.stringify({cases:cases.length,original_calls:originalCalls,allocator_calls:allocatorCalls,
 max_memory_bytes:maxMemory,game_bytes_invariance_checked:gameBytesChecked,host_calls:0,denied_function_imports:878,memory_page_cap:4096,
 snapshot_restore_domain:true,real_bootstrap_reexecuted:false,user_saves_accessed:false,network_used:false,stack_value:1048576,
 original_functions:[8751,13516],input_exact_keys:keys.split(','),input_contains_expected:false,node:process.version},null,2)+'\n');
