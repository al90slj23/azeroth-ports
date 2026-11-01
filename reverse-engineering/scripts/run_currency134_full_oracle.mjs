// Full original2862, including original31731/28795 and all reached callees.
// Only the approved collect_pickups export is used. No app start or host APIs.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';

if(process.version!=='v22.23.4'||!process.execArgv.includes('--max-old-space-size=512')
    ||!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('Pinned runtime/limits required');
const [directory,casefile]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['collect_pickups']);
if(prepared.manifest.roles.length!==1||prepared.manifest.roles[0].role!=='collect_pickups')throw Error('One export only');
const cases=JSON.parse(await fs.readFile(casefile,'utf8'));
if(!cases.length||cases.length>4096)throw Error('Fixture budget');
let host,instances=0,maxMemory=0,totalCalls=0,treeInserts=0,existingUpdates=0;
for(let index=0;index<cases.length;++index){
  if(index%32===0){host=await prepared.fresh();++instances;}
  const c=cases[index];if(c.id!==index)throw Error('Fixture order');
  const {roles,memory,allocate,hostCalls}=host;
  const G=allocate(8192),recordPointer=allocate(c.pickup_capacity*56,8),messagePointer=allocate(32*16,4);
  const q=c.currency.queue;
  const queuePointer=c.currency.queue_capacity?allocate(c.currency.queue_capacity*8,4):4;
  const region=Buffer.from(c.region_id,'utf8'),regionPointer=region.length?allocate(region.length,1):1;
  let v=new DataView(memory.buffer);
  const w=(p,x)=>v.setUint32(p,x>>>0,true),r=p=>v.getUint32(p,true);
  if(region.length)new Uint8Array(memory.buffer,regionPointer,region.length).set(region);
  w(G+184,regionPointer);w(G+188,region.length);
  w(G+1100,c.currency.earned);w(G+1384,c.radius_bits);w(G+1408,c.currency.multiplier_bits);
  w(G+1504,c.player_xy[0]);w(G+1508,c.player_xy[1]);
  w(G+1520,120);w(G+1544,c.currency.gold);
  w(G+1860,c.pickup_capacity);w(G+1864,recordPointer);w(G+1868,0);
  w(G+1872,32);w(G+1876,messagePointer);w(G+1880,0);
  w(G+2148,c.currency.queue_capacity);w(G+2152,queuePointer);w(G+2156,q.length);
  q.forEach((row,i)=>{w(queuePointer+i*8,row[0]);w(queuePointer+i*8+4,row[1]);});
  w(G+2344,c.now_bits);w(G+2520,c.currency.local_peer);w(G+2532,c.currency.member_count);
  v.setUint8(G+2574,c.currency.mode);v.setUint8(G+2579,c.phase);
  c.rng.forEach((word,i)=>w(G+1712+4*i,word));
  function treeFields(){
    const root=r(G+2468),depth=r(G+2472);if(!root)return {fields:[],present:false,depth};
    if(depth>4)throw Error('Tree depth fixture budget');
    const fields=[],seen=new Set();
    function walk(node,level){
      if(!node||node+76>memory.buffer.byteLength||seen.has(node)||seen.size>128)throw Error('Tree node bounds');
      seen.add(node);const n=v.getUint16(node+50,true);if(n>11)throw Error('Tree node count');
      if(level&&node+76+(n+1)*4>memory.buffer.byteLength)throw Error('Tree child bounds');
      for(let j=0;j<n;++j){if(level)walk(r(node+76+4*j),level-1);
        fields.push([v.getUint16(node+52+2*j,true),r(node+4+4*j)]);}
      if(level)walk(r(node+76+4*n),level-1);
    }
    walk(root,depth);return {fields,present:true,depth};
  }
  function snapshot(){
    v=new DataView(memory.buffer);
    const count=r(G+1868),rp=r(G+1864),qn=r(G+2156),qp=r(G+2152),mn=r(G+1880),mp=r(G+1876);
    if(count>64||qn>64||mn>64||rp+count*56>memory.buffer.byteLength
        ||(qn&&qp+qn*8>memory.buffer.byteLength)||mp+mn*16>memory.buffer.byteLength)throw Error('Vector fixture bounds');
    const tree=treeFields(),messages=[];
    for(let j=0;j<mn;++j){const p=mp+j*16,len=r(p+8),opcode=v.getUint16(p+12,true),payload=r(p+4);
      if(len!==8||opcode!==170||payload+8>memory.buffer.byteLength)throw Error('Unexpected currency message');
      messages.push({opcode,length:len,guid_hex:v.getBigUint64(payload,true).toString(16).padStart(16,'0')});}
    return {gold:r(G+1544),earned:r(G+1100),queue_capacity:r(G+2148),queue_count:qn,
      queue_entries:Array.from({length:qn},(_,j)=>[r(qp+j*8),r(qp+j*8+4)]),
      player_fields:tree.fields,tree_present:tree.present,tree_depth:tree.depth,
      pickup_capacity:r(G+1860),pickup_count:count,
      record_hex:Array.from({length:count},(_,j)=>Buffer.from(memory.buffer,rp+j*56,56).toString('hex')),
      rng:Array.from({length:4},(_,j)=>r(G+1712+4*j)),messages,phase:v.getUint8(G+2579)};
  }
  function loadRecords(hexes){
    v=new DataView(memory.buffer);w(G+1868,hexes.length);
    hexes.forEach((raw,j)=>new Uint8Array(memory.buffer,recordPointer+j*56,56).set(Buffer.from(raw,'hex')));
  }
  const result={id:index};
  if(c.warmup_record_hex){
    w(G+1384,0x41100000);loadRecords([c.warmup_record_hex]);
    roles.collect_pickups(G);++totalCalls;result.after_warmup=snapshot();
    v=new DataView(memory.buffer);w(G+1384,c.radius_bits);
  }
  const before=treeFields();result.before_target_tree_present=before.present;
  if(before.present)++existingUpdates;else ++treeInserts;
  loadRecords(c.record_hex);roles.collect_pickups(G);++totalCalls;result.after_collection=snapshot();
  if(hostCalls.length)throw Error('Host API attempted');
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${directory}/currency134-runtime.json`,JSON.stringify({case_count:cases.length,
  actual_original_entry:2862,original_currency_callees:[31731,28795],original_callees_unchanged:true,
  original_allocator:91940,added_research_exports:['collect_pickups'],entry_calls:totalCalls,
  target_calls_with_preexisting_tree:existingUpdates,target_calls_with_empty_tree:treeInserts,
  fresh_instances:instances,fresh_instance_every:32,max_memory_bytes:maxMemory,memory_limit_pages:512,
  denied_function_imports:878,actual_host_calls:0,node:process.version,
  full_game_started:false,application_start_called:false,network_used:false,user_saves_accessed:false},null,2)+'\n');
