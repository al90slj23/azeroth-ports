// Unchanged complete1446; expected values are never present in this input.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {prepareFull135} from './full135_host.mjs';
const [directory,inputFile]=process.argv.slice(2),digest=b=>createHash('sha256').update(b).digest('hex');
const prepared=await prepareFull135(directory,['adt_parse']);
const cases=JSON.parse(await fs.readFile(inputFile,'utf8'));
if(!Array.isArray(cases)||cases.length<1||cases.length>32)throw Error('Bounded case count required');
let peak=0,calls=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input'||Object.keys(c.input).sort().join()!=='asset_bytes,asset_path,asset_sha256')throw Error('Input-only exact shape required');
 const data=await fs.readFile(c.input.asset_path);
 if(data.length!==c.input.asset_bytes||digest(data)!==c.input.asset_sha256)throw Error('Actual file identity');
 const host=await prepared.fresh(),{roles,memory,allocate,hostCalls}=host;
 const dv=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),r=p=>dv().getUint32(p,true);
 const p=allocate(data.length),out=allocate(64);bytes().set(data,p);
 const poisoned=new Uint8Array(memory.buffer,out,64);poisoned.fill(0xa5);
 try{
  roles.adt_parse(out,p,data.length);calls++;
  if(r(out)===0xffffffff)throw Error('Original1446 canonical input returned error');
  const vectors={};
  for(const [kind,offset]of[['m2',12],['wmo',24]]){
   const cap=r(out+offset),ptr=r(out+offset+4),len=r(out+offset+8);
   if(len>65536||cap<len||cap>131072||ptr+cap*44>memory.buffer.byteLength)throw Error('Placement output budget');
   const records=[];
   for(let j=0;j<len;j++){
    const at=ptr+j*44,n=r(at+8),s=r(at+4),scap=r(at);
    if(n>4096||scap<n||s+n>memory.buffer.byteLength)throw Error('String capture budget');
    const name=Buffer.from(bytes().slice(s,s+n));new TextDecoder('utf-8',{fatal:true}).decode(name);
    records.push({name_utf8_hex:name.toString('hex'),string_capacity:scap,scalar_words:Array.from({length:8},(_,i)=>r(at+12+i*4))});
   }
   const raw=Buffer.from(bytes().slice(ptr,ptr+cap*44));
   await fs.writeFile(`${directory}/placements135-${c.id}-${kind}-records44.bin`,raw);
   vectors[kind]={capacity:cap,length:len,records,raw_backing_sha256:digest(raw),raw_backing_bytes:raw.length};
  }
  if(digest(bytes().slice(p,p+data.length))!==c.input.asset_sha256)throw Error('Borrowed actual input mutated');
  if(hostCalls.length)throw Error('Host call rejected');
  peak=Math.max(peak,memory.buffer.byteLength);
  process.stdout.write(JSON.stringify({id:c.id,vectors,host_calls:hostCalls.length,input_unchanged:true})+'\n');
 }catch(e){
  await fs.writeFile(`${directory}/placements135-failure-${c.id}.json`,JSON.stringify({error:e.stack,hostCalls,calls,memory_bytes:memory.buffer.byteLength},null,2)+'\n');
  throw e;
 }
}
await fs.writeFile(`${directory}/placements135-runtime.json`,JSON.stringify({cases:cases.length,calls,peak_memory_bytes:peak,
 node:process.version,fresh_instances:cases.length,memory_cap_bytes:33554432,denied_imports:878,host_calls:0,
 complete_original_function:1446,allocator:91941,application_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
