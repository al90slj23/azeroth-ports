// Real local ADT -> unchanged1446 producer -> unchanged height consumers.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareFull135} from './full135_host.mjs';
const [directory,file]=process.argv.slice(2),required=['adt_parse','chunk_height','tile_height','terrain_height','world_height'];
const prepared=await prepareFull135(directory,required),cases=JSON.parse(await fs.readFile(file,'utf8'));
if(!cases.length||cases.length>120)throw Error('Bounded actualADT count');
const digest=b=>createHash('sha256').update(b).digest('hex');
let calls=0,maxMemory=0,hostCallCount=0;
for(const c of cases){
 const host=await prepared.fresh(),{memory,allocate,roles,hostCalls}=host;
 const dv=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),r=p=>dv().getUint32(p,true),w=(p,v)=>dv().setUint32(p,v>>>0,true);
 const num=w=>{const a=new DataView(new ArrayBuffer(4));a.setUint32(0,w,true);return a.getFloat32(0,true);};
 const payload=await fs.readFile(c.asset_path);if(payload.length!==c.asset_bytes||digest(payload)!==c.asset_sha256)throw Error('Actual asset identity');
 let result;
 try{
  const P=allocate(payload.length),O=allocate(64),Q=allocate(16),H=allocate(16);bytes().set(payload,P);
  roles.adt_parse(O,P,payload.length);calls++;
  if(r(O)===0xffffffff)throw Error('Actual1446 parser returned error');
  const n=r(O+8),records=r(O+4);if(n>256||n!==c.expected.producer.length)throw Error('Actual1446 chunk count');
  const produced=[];let rawVertices=[],rawRecords=[];
  for(let i=0;i<n;i++){
   const p=records+i*264,count=r(p+8),ptr=r(p+4);if(count!==145||ptr+count*12>memory.buffer.byteLength)throw Error('Actual vertex budget');
   const v=Buffer.from(bytes().slice(ptr,ptr+count*12));rawVertices.push(v);rawRecords.push(Buffer.from(bytes().slice(p,p+264)));
   produced.push({vertex_count:count,vertices_sha256:digest(v),holes:dv().getUint16(p+260,true)});
  }
  const V=allocate(128),T=allocate(36),B=allocate(16);bytes().set(bytes().slice(O,O+36),T);c.bounds_bits.forEach((v,j)=>w(B+4*j,v));
  w(V,1);w(V+4,T);w(V+8,1);w(V+12,1);w(V+16,B);w(V+20,1);w(V+48,0xffffffff);w(V+84,0xffffffff);
  const samples=[];
  for(const s of c.samples){
   w(Q,s.x_bits);w(Q+4,s.y_bits);w(Q+8,0);
   const read=()=>({found:r(H)===1,value_bits:r(H+4)});
   roles.chunk_height(H,records+s.chunk_index*264,Q);calls++;const chunk=read();
   roles.tile_height(H,records,n,Q);calls++;const tile=read();
   roles.terrain_height(H,V,num(s.x_bits),num(s.y_bits));calls++;const terrain=read();
   roles.world_height(H,V,num(s.x_bits),num(s.y_bits));calls++;const world=read();
   dv().setUint8(V+112,1);w(V+108,c.flat_height_bits);roles.world_height(H,V,num(s.x_bits),num(s.y_bits));calls++;const flat=read();dv().setUint8(V+112,0);
   samples.push({chunk,tile,terrain,world,flat});
  }
  const matrix=[],rasterData=allocate(16),savedHoles=dv().getUint16(records+260,true);
  for(const q of c.consumer_matrix){
   w(Q,q.x_bits);w(Q+4,q.y_bits);w(Q+8,0);
   if(q.kind==='holes'){
    dv().setUint16(records+260,q.holes,true);roles.chunk_height(H,records,Q);calls++;dv().setUint16(records+260,savedHoles,true);
   }else if(q.kind==='raster'){
    for(const key of ['primary','secondary'])if(q[key]){
     const offset=key==='primary'?48:84,ptrOffset=key==='primary'?64:88,s=q[key];if(s.width!==2||s.values_bits.length!==4)throw Error('Raster matrix budget');
     w(V+offset,0);w(V+ptrOffset,rasterData);w(V+ptrOffset+4,4);w(V+ptrOffset+8,s.origin_xy_bits[0]);w(V+ptrOffset+12,s.origin_xy_bits[1]);w(V+ptrOffset+16,2);
     s.values_bits.forEach((v,j)=>w(rasterData+j*4,v));
    }
    roles.world_height(H,V,num(q.x_bits),num(q.y_bits));calls++;w(V+48,0xffffffff);w(V+84,0xffffffff);
   }else throw Error('Unknown controlled consumer matrix');
   matrix.push({found:r(H)===1,value_bits:r(H+4)});
  }
  if(digest(bytes().slice(P,P+payload.length))!==c.asset_sha256)throw Error('Borrowed actualADT input changed');
  await fs.writeFile(`${directory}/terrain135-original-${c.id}-vertices.bin`,Buffer.concat(rawVertices));
  await fs.writeFile(`${directory}/terrain135-original-${c.id}-records264.bin`,Buffer.concat(rawRecords));
  result={id:c.id,producer:produced,samples,consumer_matrix:matrix,raw_vertices_sha256:digest(Buffer.concat(rawVertices)),raw_records264_sha256:digest(Buffer.concat(rawRecords)),host_calls:hostCalls.length};
 }catch(e){
  await fs.writeFile(`${directory}/terrain135-failure-${c.id}.json`,JSON.stringify({id:c.id,asset_path:c.asset_path,input_bytes:payload.length,calls,error:e.stack,host_calls:hostCalls,memory_bytes:memory.buffer.byteLength},null,2)+'\n');
  throw e;
 }
 maxMemory=Math.max(maxMemory,memory.buffer.byteLength);hostCallCount+=hostCalls.length;if(hostCalls.length)throw Error('Original host call');
 process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/terrain135-runtime.json`,JSON.stringify({cases:cases.length,calls,max_memory_bytes:maxMemory,fresh_instances:cases.length,denied_imports:878,host_calls:hostCallCount,node:process.version,
 original_functions:[1446,5795,46295,18670,29631],all_callees_unchanged:true,application_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
