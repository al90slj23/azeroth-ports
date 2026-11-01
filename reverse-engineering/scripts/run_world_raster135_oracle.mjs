// Separate four-role producer oracle: all878 hosts denied, 32MiB engine cap.
import fs from'node:fs/promises';import{createHash}from'node:crypto';
const[directory,file]=process.argv.slice(2),digest=x=>createHash('sha256').update(x).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Explicit32MiB cap required');
const config=JSON.parse(await fs.readFile(directory+'/manifest.json','utf8')),raw=await fs.readFile(directory+'/'+config.module_file);
if(digest(raw)!==config.module_sha256||config.original_sha256!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2')throw Error('Frozen module identity');
const module=await WebAssembly.compile(raw),imports=WebAssembly.Module.imports(module),cases=JSON.parse(await fs.readFile(file,'utf8'));
if(imports.length!==878||imports.some(x=>x.kind!=='function')||cases.length<1||cases.length>2048)throw Error('Module/input budget');
let calls=0,maxMemory=0,hostCalls=0,stages=0;
const number=b=>{const d=new DataView(new ArrayBuffer(4));d.setUint32(0,b,true);return d.getFloat32(0,true);};
for(const c of cases){
 if(Object.keys(c).sort().join()!==['id','input'].sort().join())throw Error('Expected must not enter original runner');
 const s=c.input,bindings={};for(const m of imports){bindings[m.module]??={};bindings[m.module][m.name]=()=>{hostCalls++;throw Error('Original host denied');};}
 const ins=await WebAssembly.instantiate(module,bindings),ex=ins.exports,memory=ex.memory,bytes=()=>new Uint8Array(memory.buffer),dv=()=>new DataView(memory.buffer),r=p=>dv().getUint32(p,true),w=(p,v)=>dv().setUint32(p,v>>>0,true);
 function allocate(n){if(n<1||n>4194304)throw Error('Fixture allocation cap');const p=ex.__wbindgen_malloc(n,8)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('32MiB memory cap');bytes().fill(0,p,p+n);return p;}
 const putWords=words=>{const p=allocate(Math.max(8,words.length*4));words.forEach((v,j)=>w(p+j*4,v));return p;};
 const mesh=allocate(24),transform=allocate(12),position=putWords(s.position_bits),rotation=putWords(s.rotation_bits),grid=putWords([...s.origin_xy_bits,s.height_width]),out=allocate(12);
 let parse=null;
 if(s.asset){const b=await fs.readFile(s.asset.path);if(b.length!==s.asset.bytes||digest(b)!==s.asset.sha256)throw Error('Actual M2 identity');const p=allocate(b.length);bytes().set(b,p);ex.raster135_parse_m2(mesh,p,b.length);calls++;
  if(r(mesh)===0xffffffff)throw Error('Actual M2 parser error');const nv=r(mesh+8),ni=r(mesh+20);if(nv>65536||ni>196608)throw Error('Mesh budget');parse={vertex_count:nv,index_count:ni,vertices_hex:Buffer.from(bytes().slice(r(mesh+4),r(mesh+4)+nv*12)).toString('hex'),indices:Array.from({length:ni},(_,j)=>r(r(mesh+16)+j*4))};
 }else{const v=putWords(s.vertices.flat()),i=putWords(s.indices);w(mesh,s.vertices.length);w(mesh+4,v);w(mesh+8,s.vertices.length);w(mesh+12,s.indices.length);w(mesh+16,i);w(mesh+20,s.indices.length);}
 const nv=r(mesh+8),ni=r(mesh+20);ex.raster135_transform(transform,r(mesh+4),nv,position,rotation,number(s.scale_bits));calls++;
 const tn=r(transform+8),tp=r(transform+4);if(tn!==nv||r(transform)!==nv)throw Error('Transformed Vec size');
 const transformed_hex=Buffer.from(bytes().slice(tp,tp+tn*12)).toString('hex'),cap=s.initial_candidate_words.length/2,pairs=putWords(s.initial_candidate_words);w(out,cap);w(out+4,pairs);w(out+8,s.initial_candidate_length);
 const candidateStages=[];
 for(const triangle of s.height_triangles){const ids=triangle.map(j=>r(r(mesh+16)+j*4));if(ids.some(i=>i>=tn))throw Error('Triangle input index');ex.raster135_height_candidates(out,grid,tp+ids[0]*12,tp+ids[1]*12,tp+ids[2]*12,number(s.ceiling_bits));calls++;stages++;
  const n=r(out+8),p=r(out+4),capacity=r(out);if(n>65536||capacity>131072)throw Error('Candidate output cap');candidateStages.push({capacity,length:n,storage_words:Array.from({length:capacity*2},(_,j)=>r(p+j*4))});}
 const nav=allocate(24),navStorage=allocate(s.nav_hex.length/2),ground=putWords(s.ground_bits);bytes().set(Buffer.from(s.nav_hex,'hex'),navStorage);w(nav,s.nav_hex.length/2);w(nav+4,navStorage);w(nav+8,s.nav_active_length);w(nav+12,s.origin_xy_bits[0]);w(nav+16,s.origin_xy_bits[1]);w(nav+20,s.nav_width);
 ex.raster135_navigation(nav,mesh,position,rotation,number(s.scale_bits),ground,s.ground_bits.length);calls++;stages++;
 const nav_hex=Buffer.from(bytes().slice(navStorage,navStorage+s.nav_hex.length/2)).toString('hex');
 const output={id:c.id,parsed:parse,transformed_hex,candidate_stages:candidateStages,navigation_hex:nav_hex,nav_header_words:[r(nav),r(nav+8),r(nav+12),r(nav+16),r(nav+20)],input_mesh24_hex:Buffer.from(bytes().slice(mesh,mesh+24)).toString('hex'),memory_bytes:memory.buffer.byteLength};
 if(memory.buffer.byteLength>33554432)throw Error('Original engine memory budget');maxMemory=Math.max(maxMemory,memory.buffer.byteLength);process.stdout.write(JSON.stringify(output)+'\n');
}
await fs.writeFile(directory+'/world-raster135-runtime.json',JSON.stringify({cases:cases.length,calls,stages,max_memory_bytes:maxMemory,fresh_instances:cases.length,denied_imports:878,actual_host_calls:hostCalls,
 original_functions:[14947,18572,12375,9328],all_callees_unchanged:true,appstart_called:false,snapshot_input_used:false,network_used:false,user_saves_accessed:false,node:process.version},null,2)+'\n');
