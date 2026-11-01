// Complete unchanged922/1076/2088; learned Battle Shout80, not a racial slot.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const[dir,inputFile]=process.argv.slice(2),hash=b=>createHash('sha256').update(b).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512'))throw Error('32MiB cap required');
const sourceSHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2';
const manifest=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8'));
const original=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url));
const changed=await fs.readFile(dir+'/'+manifest.module_file),input=await fs.readFile(inputFile);
if(hash(original)!==sourceSHA||hash(changed)!==manifest.module_sha256||input.length>4194304)throw Error('Source/input identity');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a);const out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export end');return out;}
const before=sections(original),after=sections(changed);
if(before.map(s=>s.kind).join()!==after.map(s=>s.kind).join()||before.some(s=>s.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!original.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Original nonexport bytes changed');});
const oldExports=exportsOf(original,before.find(s=>s.kind===7)),newExports=exportsOf(changed,after.find(s=>s.kind===7));
const allowed=[{name:'research135_cast',kind:0,index:922},{name:'research135_owned_tick',kind:0,index:1076},{name:'research135_player_tick',kind:0,index:2088},{name:'research135_battle_stack0',kind:3,index:0}];
if(JSON.stringify(newExports.slice(0,oldExports.length))!==JSON.stringify(oldExports)||JSON.stringify(newExports.slice(oldExports.length))!==JSON.stringify(allowed))throw Error('Private export surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=JSON.parse(input);
if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>1000)throw Error('Import/case profile');
const number=word=>{const v=new DataView(new ArrayBuffer(4));v.setUint32(0,word,true);return v.getFloat32(0,true);};
let hostCalls=0,peak=0;const callCounts={},stackChecks=[],opaqueRetained=[];
async function run(c){
 const bindings={};for(const item of imports){bindings[item.module]??={};bindings[item.module][item.name]=()=>{hostCalls++;throw Error('Denied original host '+item.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.research135_battle_stack0;
 const bytes=()=>new Uint8Array(memory.buffer),d=()=>new DataView(memory.buffer),w=(p,v)=>d().setUint32(p,v>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Precall stack');let returned=false;try{const result=fn(...args);returned=true;return result;}finally{const after=stack.value;stackChecks.push({case_id:c.id,index,before,after,returned});if(before!==after)throw Error('Stack not restored');}}
 function allocate(n,align=8){if(n<1||n>4194304)throw Error('Allocation budget');const p=call(91941,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory budget');bytes().fill(0,p,p+n);return p;}
 const s=c.level,t=s.stats,G=allocate(8192),U=allocate(Math.max(1,c.cast.units.length)*424),A=allocate(Math.max(1,c.owned_hex.length)*80),L=allocate(128*32),R=allocate(128);
 for(const key of ['passives','adjustments','item_modifiers','owned_skills','timed_records','definitions'])if(s.sources[key].length)throw Error('Explicit empty nonlive source domain');
 w(G+2348,R);w(R+32,0xffffffff);w(R+56,0xffffffff);w(R+120,1);
 for(const[cap,ptr,len,align]of[[1904,1908,1912,4],[1952,1956,1960,4],[2024,2028,2032,4],[2048,2052,2056,4],[2084,2088,2092,4],[2096,2100,2104,4],[1892,1896,1900,4]]){w(G+cap,0);w(G+ptr,align);w(G+len,0);}
 for(const[o,v]of Object.entries(s.derived_bits))w(G+Number(o),v);
 bytes()[G+360]=t.class_byte;bytes()[G+361]=t.race_byte;bytes()[G+2582]=t.flag2574;bytes()[G+2587]=s.phase2587;bytes()[G+387]=s.heal_gate387;bytes()[G+908]=c.context908;
 w(G+1440,t.current_hp_bits);w(G+1536,t.old_max_hp_bits);w(G+1648,t.previous_speed_bits);w(G+268,t.conditional268_bits);w(G+1344,t.conditional1344_id);w(G+1348,t.conditional1348_bits);
 w(G+1444,t.pool1532_bits);w(G+1448,t.pool1536_bits);w(G+768,t.pool768_bits);w(G+756,s.pool756_bits);w(G+1432,s.progression.level);w(G+1652,c.last_hit_bits);w(G+1628,c.timer1628_bits);w(G+488,c.busy488);
 d().setBigUint64(G+1336,BigInt(c.cast.source_id),true);d().setBigUint64(G+776,BigInt(c.cast.current_target_id),true);
 c.cast.player_xy.forEach((word,j)=>w(G+1416+j*4,word));w(G+1424,c.player_z_bits);s.rng_words.forEach((word,j)=>w(G+1720+j*4,word));
 w(G+2412,c.sequence);w(G+1644,c.action_sequence);w(G+2356,c.effect_counter);
 const initialFields=Object.entries(s.player_fields).map(([k,v])=>[Number(k),v]).sort((a,b)=>a[0]-b[0]);
 if(initialFields.length){if(initialFields.length>11)throw Error('Explicit single-leaf input tree budget');const p=allocate(76,4);d().setUint16(p+50,initialFields.length,true);initialFields.forEach(([key,value],j)=>{d().setUint16(p+52+j*2,key,true);w(p+4+j*4,value);});w(G+2476,p);w(G+2480,0);w(G+2484,initialFields.length);}
 c.cast.units.forEach((unit,j)=>{const p=U+j*424;d().setBigUint64(p+112,BigInt(unit.guid),true);d().setBigUint64(p+32,BigInt(unit.linked_id),true);
  for(const[o,key]of[[0,'marker'],[40,'kind_40'],[64,'kind_64'],[244,'elite_244'],[288,'hp_bits'],[292,'max_hp_bits'],[372,'priority_until372_bits'],[408,'phase_until408_bits'],[412,'phase_until412_bits'],[340,'movement_time_bits'],[344,'duration_bits']])w(p+o,unit[key]);
  bytes()[p+416]=unit.elite_416;for(const[o,xy]of[[316,unit.from_xy],[328,unit.to_xy]])xy.forEach((word,k)=>w(p+o+k*4,word));});
 w(G+1784,c.cast.units.length);w(G+1788,U);w(G+1792,c.cast.units.length);w(G+1656,c.owned_hex.length);w(G+1660,A);w(G+1664,c.owned_hex.length);
 c.owned_hex.forEach((row,j)=>bytes().set(Buffer.from(row,'hex'),A+j*80));bytes().set(Buffer.from(c.basic_hex,'hex'),G+1256);
 if(hex(c.definition_pointer,88)!==c.definition88_hex||c.definition_pointer!==5467956)throw Error('Battle Shout original definition identity');
 w(G+1704,128);w(G+1708,L);w(G+1712,c.live_records.length);c.live_records.forEach((row,j)=>bytes().set(Buffer.from(row,'hex'),L+j*32));
 c.initial_unknown.forEach(([index,offset])=>w(L+index*32+offset,c.unknown_poison));
 for(const[index,offset]of[[0,672],[1,684],[2,732]]){const ledger=c.attempts[index];if(ledger.length){const p=allocate(ledger.length*4,4);ledger.forEach((word,j)=>w(p+j*4,word));w(G+offset-4,ledger.length);w(G+offset,p);w(G+offset+4,ledger.length);}}
 const tree=()=>{const root=r(G+2476),depth=r(G+2480),out={},seen=new Set();if(!root)return out;function walk(p,level){if(!p||seen.has(p)||seen.size>512||level>5)throw Error('Tree budget');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(level)walk(r(p+76+j*4),level-1);const key=d().getUint16(p+52+j*2,true);if([22,28,1109].includes(key))out[key]=r(p+4+j*4);}if(level)walk(r(p+76+n*4),level-1);}walk(root,depth);return out;};
 const stages=[];
 for(const op of c.ops){
  w(G+2352,op.now_bits);let success=null;
  if(op.kind==='cast'){success=call(922,e.research135_cast,G,A+c.battle_index*80);callCounts[922]=(callCounts[922]??0)+1;}
  else if(op.kind==='owned'){call(1076,e.research135_owned_tick,G,number(op.dt_bits));callCounts[1076]=(callCounts[1076]??0)+1;}
  else if(op.kind==='player'){call(2088,e.research135_player_tick,G,number(op.dt_bits));callCounts[2088]=(callCounts[2088]??0)+1;}
  else throw Error('Operation');
  const p=r(G+1708),n=r(G+1712);if(n>128)throw Error('Live count');
  stages.push({success,live_records:Array.from({length:n},(_,j)=>hex(p+j*32,32)),owned_hex:c.owned_hex.map((_,j)=>hex(A+j*80,80)),basic_hex:hex(G+1256,80),
   derived_bits:Object.fromEntries(Array.from({length:23},(_,j)=>[1536+j*4,r(G+1536+j*4)])),current_hp_bits:r(G+1440),
   auxiliary_bits:Object.fromEntries([1444,1448,1348,768,756].map(o=>[o,r(G+o)])),shield_source:r(G+1344),speed_bits:r(G+1648),player_fields:tree(),
   rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),attempted_spell_sets:[672,684,732].map(offset=>{const ptr=r(G+offset),count=r(G+offset+4);if(count>128)throw Error('Attempt set count');return Array.from({length:count},(_,j)=>r(ptr+j*4));}),
   timer1628_bits:r(G+1628),message_sequence:r(G+2412),action_sequence:r(G+1644),effect_counter:r(G+2356)});
  if(hostCalls)throw Error('Original host attempted');
 }
 peak=Math.max(peak,memory.buffer.byteLength);return{id:c.id,stages};
}
for(let index=0;index<cases.length;index++){if(cases[index].id!==index)throw Error('Case order');process.stdout.write(JSON.stringify(await run(cases[index]))+'\n');if(global.gc)global.gc();}
await fs.writeFile(dir+'/battle-shout135-runtime.json',JSON.stringify({cases:cases.length,fresh_instances:cases.length,full_original_calls:callCounts,actual_host_calls:hostCalls,denied_imports:878,peak_memory_bytes:peak,memory_page_cap:512,
 stack_all_restored:stackChecks.every(s=>s.returned&&s.before===1048576&&s.after===s.before),stack_checks:stackChecks,original_callees_replaced:false,original_application_start:false,original_snapshot_loaded:false})+'\n');
