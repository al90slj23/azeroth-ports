// Lossless JSON capture CAS v1. No target module or producer is imported here.
import fs from 'node:fs/promises';
import path from 'node:path';
import {writeSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createGzip} from 'node:zlib';
import {Writable} from 'node:stream';
import {pipeline} from 'node:stream/promises';
export const CAS_PROTOCOL='opening-combat135-cas-v1';
export const CAS_MARKER='$cas135_blob_v1';
export const CAS_LIMITS=Object.freeze({cases:1,actions_per_case:1200,controlled_frames_per_case:1000,capture_records:15204,
 logical_record_bytes:8388608,logical_output_bytes:17179869184,index_record_bytes:2097152,
 index_uncompressed_bytes:1073741824,compressed_output_bytes:268435456,
 blob_bytes:16777216,unique_blob_bytes:1073741824,blob_files:65536,
 blob_index_record_bytes:2097152,blob_index_bytes:268435456,blob_references_bytes:33554432,
 encoding_depth:128,encoding_nodes_per_record:1048576,write_concurrency:16,
 string_cache_bytes:67108864,string_cache_entries:8192,owned_deadline_seconds:180});
const digest=b=>createHash('sha256').update(b).digest('hex');
const jsonBytes=value=>Buffer.from(JSON.stringify(value),'utf8');
const assert=(condition,label)=>{if(!condition)throw Error(label);};
const marker=value=>Object.freeze({[CAS_MARKER]:value.sha256,bytes:value.bytes});
async function writeAll(handle,raw){let offset=0;while(offset<raw.length){const{bytesWritten}=await handle.write(raw,offset,raw.length-offset);assert(bytesWritten>0,'CAS file write no progress');offset+=bytesWritten;}}

// Validate the ORIGINAL record before writing any of its CAS nodes. In
// particular a user value cannot masquerade as a reference after encoding.
function validateOriginal(value,limits,active=new Set(),depth=0,state={nodes:0}){
 assert(++state.nodes<=limits.encoding_nodes_per_record&&depth<=limits.encoding_depth,'CAS original tree budget');
 if(typeof value==='string'){assert(!/[\uD800-\uDFFF]/u.test(value),'CAS unsupported unpaired UTF16 surrogate');return;}
 if(value===null||typeof value==='boolean'||value===undefined)return;
 if(typeof value==='number'){assert(Number.isFinite(value),'CAS unsupported nonfinite Number');return;}
 assert(typeof value==='object'&&!active.has(value),'CAS unsupported value/cycle');
 assert(Array.isArray(value)||Object.getPrototypeOf(value)===Object.prototype||Object.getPrototypeOf(value)===null,'CAS unsupported object prototype');
 assert(!Object.hasOwn(value,CAS_MARKER),'CAS reserved marker in original capture');active.add(value);
 for(const key of Object.keys(value)){assert(!/[\uD800-\uDFFF]/u.test(key),'CAS unsupported unpaired UTF16 key');validateOriginal(value[key],limits,active,depth+1,state);}
 active.delete(value);
}
function childReferences(value){
 const found=new Map();
 function walk(node){
  if(node===null||typeof node!=='object')return;
  if(Object.hasOwn(node,CAS_MARKER)){
   assert(Object.keys(node).length===2&&typeof node[CAS_MARKER]==='string'&&Number.isSafeInteger(node.bytes),'CAS internal reference shape');
   const key=node[CAS_MARKER],old=found.get(key);if(old){assert(old.bytes===node.bytes,'CAS internal reference size');old.count++;}
   else found.set(key,{sha256:key,bytes:node.bytes,count:1});return;
  }
  for(const key of Object.keys(node))walk(node[key]);
 }
 walk(value);return[...found.values()];
}

export async function createCaptureCASOutput(directory,limits=CAS_LIMITS){
 assert(JSON.stringify(limits)===JSON.stringify(CAS_LIMITS),'CAS fixed budget contract');
 const resolved=path.resolve(directory);assert(resolved.startsWith('/Volumes/RuiRui4TB/'),'CAS evidence must be on4T');
 const blobDirectory=path.join(resolved,'cas-blobs');await fs.mkdir(blobDirectory,{recursive:false});
 const blobIndexPath=path.join(resolved,'blob-index.jsonl'),referencesPath=path.join(resolved,'blob-references.jsonl');
 const blobIndex=await fs.open(blobIndexPath,'wx');
 const entries=new Map(),stringCache=new Map(),pending=new Set();let cacheBytes=0,writeFailure=null;
 let uniqueBytes=0,blobIndexBytes=0,referenceBytes=0,recordIndex=0,indexBytes=0,compressedBytes=0,logicalBytes=0,maxLogical=0,maxIndex=0,maxBlob=0,maxBlobIndexRecord=0;
 let blobReferences=0;const started=Date.now(),indexHash=createHash('sha256'),gzipHash=createHash('sha256'),logicalHash=createHash('sha256'),blobIndexHash=createHash('sha256'),referenceHash=createHash('sha256');
 const queued=[];let activeWrites=0;
 function pump(){
  while(activeWrites<limits.write_concurrency&&queued.length){const task=queued.shift();activeWrites++;
   fs.writeFile(path.join(blobDirectory,task.file),task.raw,{flag:'wx'}).then(task.resolve,task.reject).finally(()=>{activeWrites--;pump();});}
 }
 function schedule(raw,file){
  const promise=new Promise((resolve,reject)=>queued.push({raw,file,resolve,reject}));pending.add(promise);
  promise.then(()=>pending.delete(promise),error=>{pending.delete(promise);writeFailure??=error;});pump();return promise;
 }
 async function settle(){while(pending.size)await Promise.all([...pending]);if(writeFailure)throw writeFailure;}
 function touch(entry){entry.total_logical_references++;entry.last_record_index=recordIndex;blobReferences++;}
 function put(encoded,newEntries){
  const raw=jsonBytes(encoded),size=raw.length;assert(size<=limits.blob_bytes,'CAS single16MiB blob budget');const sha256=digest(raw);
  let entry=entries.get(sha256);
  if(entry){assert(entry.bytes===size,'CAS SHA size disagreement');touch(entry);return marker(entry);}
  assert(entries.size<limits.blob_files,'CAS unique file65536 budget: files='+entries.size+', record='+recordIndex);
  assert(uniqueBytes+size<=limits.unique_blob_bytes,'CAS unique bytes1GiB budget: bytes='+(uniqueBytes+size)+', record='+recordIndex);
  const file=sha256+'.json',children=childReferences(encoded);
  for(const child of children){const known=entries.get(child.sha256);assert(known&&known.bytes===child.bytes,'CAS child must precede parent');}
  entry={sha256,bytes:size,file,first_record_index:recordIndex,last_record_index:recordIndex,total_logical_references:0};entries.set(sha256,entry);uniqueBytes+=size;maxBlob=Math.max(maxBlob,size);touch(entry);
  const indexLine=Buffer.concat([jsonBytes({sha256,bytes:size,file:'cas-blobs/'+file,first_record_index:recordIndex,child_refs:children}),Buffer.from('\n')]);
  assert(indexLine.length<=limits.blob_index_record_bytes,'CAS blob index record budget');newEntries.push(indexLine);schedule(raw,file);return marker(entry);
 }
 function encode(node,newEntries,depth=0){
  assert(depth<=limits.encoding_depth,'CAS encode depth');
  if(typeof node==='string'){
   const old=stringCache.get(node);
   if(old){touch(entries.get(old.value[CAS_MARKER]));return old;}
   const raw=jsonBytes(node),logical=raw.length;
   if(logical<512)return{value:node,logical};
   const value=put(node,newEntries),result={value,logical};
   const size=node.length*2;
   if(size<=limits.string_cache_bytes){
    while(stringCache.size&&(cacheBytes+size>limits.string_cache_bytes||stringCache.size>=limits.string_cache_entries)){
     const key=stringCache.keys().next().value;cacheBytes-=key.length*2;stringCache.delete(key);
    }
    stringCache.set(node,result);cacheBytes+=size;
   }
   return result;
  }
  if(node===null||typeof node!=='object')return{value:node,logical:jsonBytes(node).length};
  let encoded,logical=2,count=0;
  if(Array.isArray(node)){
   encoded=[];
   for(const item of node){const child=encode(item===undefined?null:item,newEntries,depth+1);encoded.push(child.value);logical+=child.logical+(count++?1:0);}
  }else{
   encoded=Object.create(null);
   for(const key of Object.keys(node)){
    if(node[key]===undefined)continue; // Identical to original JSON.stringify object semantics.
    const child=encode(node[key],newEntries,depth+1);encoded[key]=child.value;logical+=jsonBytes(key).length+1+child.logical+(count++?1:0);
   }
  }
  return{value:logical>=512?put(encoded,newEntries):encoded,logical};
 }
 const sink=new Writable({write(chunk,encoding,done){
  try{assert(compressedBytes+chunk.length<=limits.compressed_output_bytes,'CAS gzip256MiB budget');
   let offset=0;while(offset<chunk.length){const n=writeSync(1,chunk,offset,chunk.length-offset);assert(n>0,'CAS stdout no progress');offset+=n;}
   compressedBytes+=chunk.length;gzipHash.update(chunk);done();
  }catch(error){done(error);}}});
 const gzip=createGzip({level:6}),outputDone=pipeline(gzip,sink);let outputFailure=null;outputDone.catch(error=>{outputFailure=error;});
 async function emit(value){
  assert(Date.now()-started<limits.owned_deadline_seconds*1000,'CAS180s elapsed budget');if(outputFailure)throw outputFailure;if(writeFailure)throw writeFailure;
  assert(recordIndex<limits.capture_records,'CAS15204 capture record budget');
  validateOriginal(value,limits);assert(value&&typeof value==='object'&&!Array.isArray(value),'CAS logical record object required');
  assert(typeof value.record_kind==='string'&&Number.isSafeInteger(value.id)&&value.id>=0,'CAS logical record identity');
  const raw=Buffer.concat([jsonBytes(value),Buffer.from('\n')]);
  assert(raw.length<=limits.logical_record_bytes,'CAS logical record8MiB budget: bytes='+raw.length+', record='+recordIndex);
  assert(logicalBytes+raw.length<=limits.logical_output_bytes,'CAS logical output16GiB budget: bytes='+(logicalBytes+raw.length)+', record='+recordIndex);
  const newEntries=[],encoded=encode(value,newEntries);assert(encoded.logical+1===raw.length,'CAS logical size reconstruction');
  const envelope={cas_protocol:CAS_PROTOCOL,record_index:recordIndex,record_kind:value.record_kind,id:value.id,logical_bytes:raw.length,logical_sha256:digest(raw),capture:encoded.value};
  const line=Buffer.concat([jsonBytes(envelope),Buffer.from('\n')]);assert(line.length<=limits.index_record_bytes&&indexBytes+line.length<=limits.index_uncompressed_bytes,'CAS index2MiB/1GiB budget');
  await settle();
  for(const indexLine of newEntries){assert(blobIndexBytes+indexLine.length<=limits.blob_index_bytes,'CAS blob index256MiB budget');await writeAll(blobIndex,indexLine);blobIndexBytes+=indexLine.length;maxBlobIndexRecord=Math.max(maxBlobIndexRecord,indexLine.length);blobIndexHash.update(indexLine);}
  await new Promise((resolve,reject)=>gzip.write(line,error=>error?reject(error):resolve()));if(outputFailure)throw outputFailure;
  indexBytes+=line.length;indexHash.update(line);logicalBytes+=raw.length;logicalHash.update(raw);maxLogical=Math.max(maxLogical,raw.length);maxIndex=Math.max(maxIndex,line.length);recordIndex++;
 }
 async function finish(){
  await settle();await blobIndex.close();gzip.end();await outputDone;
  const refs=await fs.open(referencesPath,'wx');
  try{for(const entry of entries.values()){
   const line=Buffer.concat([jsonBytes({sha256:entry.sha256,bytes:entry.bytes,first_record_index:entry.first_record_index,last_record_index:entry.last_record_index,total_logical_references:entry.total_logical_references}),Buffer.from('\n')]);
   assert(referenceBytes+line.length<=limits.blob_references_bytes,'CAS reference index32MiB budget');await writeAll(refs,line);referenceBytes+=line.length;referenceHash.update(line);
  }}finally{await refs.close();}
  return{protocol:CAS_PROTOCOL,encoding:'bottom_up_JSON_nodes_original_logical_size_at_least512B',marker:CAS_MARKER,
   blob_directory:'cas-blobs',blob_index_file:'blob-index.jsonl',blob_references_file:'blob-references.jsonl',
   records:recordIndex,logical_bytes:logicalBytes,logical_sha256:logicalHash.digest('hex'),maximum_logical_record_bytes:maxLogical,
   index_uncompressed_bytes:indexBytes,index_uncompressed_sha256:indexHash.digest('hex'),compressed_bytes:compressedBytes,compressed_sha256:gzipHash.digest('hex'),maximum_index_record_bytes:maxIndex,
   unique_blobs:entries.size,unique_blob_bytes:uniqueBytes,maximum_blob_bytes:maxBlob,total_logical_blob_references:blobReferences,
   blob_index_bytes:blobIndexBytes,blob_index_sha256:blobIndexHash.digest('hex'),maximum_blob_index_record_bytes:maxBlobIndexRecord,
   blob_references_bytes:referenceBytes,blob_references_sha256:referenceHash.digest('hex'),limits,
   original_reserved_marker_rejected_before_encoding:true,unpaired_UTF16_rejected:true,all_original_capture_fields_preserved:true,property_order_and_Number_values_preserved:true,
   blob_files_uncompressed:true,child_refs_are_direct_encoded_edges:true,logical_reference_counts_include_expanded_blob_edges:true};
 }
 return{emit,finish};
}
