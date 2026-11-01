// Private unchanged135922/1076/2244/21455, explicit controlled owners, noApp.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [dir,inputFile]=process.argv.slice(2),hash=x=>createHash('sha256').update(x).digest('hex');
if(!process.execArgv.includes('--wasm-max-mem-pages=512')||!process.execArgv.includes('--max-old-space-size=512'))throw Error('32MiB/512MiB budgets required');
const m=JSON.parse(await fs.readFile(dir+'/manifest.json','utf8')),raw=await fs.readFile(new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm',import.meta.url)),changed=await fs.readFile(dir+'/'+m.module_file),input=await fs.readFile(inputFile,'utf8');
if(hash(raw)!=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'||hash(changed)!==m.module_sha256||Buffer.byteLength(input)>4194304)throw Error('Identity/input budget');
function leb(b,p){let n=0,s=0;while(p<b.length&&s<=28){const v=b[p++];n+=(v&127)*2**s;if(v<128)return[n,p];s+=7;}throw Error('LEB');}
function sections(b){let p=8,out=[];while(p<b.length){const start=p,kind=b[p++],[n,a]=leb(b,p),end=a+n;if(end>b.length)throw Error('Section');out.push({start,kind,a,end});p=end;}return out;}
function exportsOf(b,s){let[n,p]=leb(b,s.a),out=[];while(n--){const[k,a]=leb(b,p);p=a+k;const name=b.subarray(a,p).toString(),kind=b[p++],[index,end]=leb(b,p);p=end;out.push({name,kind,index});}if(p!==s.end)throw Error('Export boundary');return out;}
const before=sections(raw),after=sections(changed);if(before.map(x=>x.kind).join()!==after.map(x=>x.kind).join()||before.some(x=>x.kind===8))throw Error('Sections/start');
before.forEach((s,j)=>{const t=after[j];if(s.kind!==7&&!raw.subarray(s.start,s.end).equals(changed.subarray(t.start,t.end)))throw Error('Nonexport mutation');});
const prior=exportsOf(raw,before.find(s=>s.kind===7)),next=exportsOf(changed,after.find(s=>s.kind===7)),allowed=[['cast',922],['owned',1076],['effect',2244],['merge',21455]].map(([n,index])=>({name:'demo135_'+n,kind:0,index}));allowed.push({name:'demo135_stack0',kind:3,index:0});
if(JSON.stringify(next)!==JSON.stringify([...prior,...allowed]))throw Error('Private surface');
const module=await WebAssembly.compile(changed),imports=WebAssembly.Module.imports(module),cases=input.trim().split('\n').filter(Boolean).map(JSON.parse);if(imports.length!==878||imports.some(x=>x.kind!=='function')||!cases.length||cases.length>256)throw Error('Import/corpus bounds');
const number=w=>{const b=new ArrayBuffer(4),d=new DataView(b);d.setUint32(0,w,true);return d.getFloat32(0,true);};
let actualHostCalls=0,peak=0,outputBytes=0,completed=0,failure=null;const calls={},checks=[];
try{for(const c of cases){
 const bindings={};for(const i of imports){bindings[i.module]??={};bindings[i.module][i.name]=()=>{actualHostCalls++;throw Error('Denied original host '+i.name);};}
 const e=(await WebAssembly.instantiate(module,bindings)).exports,memory=e.memory,stack=e.demo135_stack0;
 const d=()=>new DataView(memory.buffer),bytes=()=>new Uint8Array(memory.buffer),w=(p,x)=>d().setUint32(p,x>>>0,true),r=p=>d().getUint32(p,true),hex=(p,n)=>Buffer.from(bytes().slice(p,p+n)).toString('hex');
 function call(index,fn,...args){const before=stack.value;if(before!==1048576)throw Error('Unexpected stack');let returned=false;try{const v=fn(...args);returned=true;calls[index]=(calls[index]??0)+1;return v;}finally{checks.push({case_id:c.id,index,before,after:stack.value,returned});if(returned&&before!==stack.value)throw Error('Stack restoration');}}
 function allocate(n,align=8){if(n<1||n>4194304)throw Error('Single allocation');const p=call(91941,e.__wbindgen_malloc,n,align)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory cap');bytes().fill(0,p,p+n);return p;}
 const stages=[];
 if(c.mode==='merge'){
  const P=allocate(16,4);c.words.forEach((v,j)=>w(P+j*4,v));
  for(const op of c.ops){const before=hex(P,16);call(21455,e.demo135_merge,P,number(op.strength_bits),number(op.deadline_bits),number(op.now_bits));stages.push({words:[0,1,2,3].map(j=>r(P+j*4)),before16_hex:before,after16_hex:hex(P,16)});}
 }else{
  const s=c.input,G=allocate(8192),U=c.units424.length?allocate(c.units424.length*424):4;
  if(c.units424.length>24||c.ops.length>16)throw Error('Fixture shape');
  c.units424.forEach((row,j)=>{if(row.length!==424)throw Error('Unit424');bytes().set(row.map(v=>v===null?c.unknown_poison:v),U+j*424);});w(G+1784,c.units424.length);w(G+1788,U);w(G+1792,c.units424.length);
  for(const [ptr,len]of[[2028,2032],[2052,2056],[600,604],[648,652]]){w(G+ptr,4);w(G+len,0);}
  for(const [cap,ptr,len]of[[1656,1660,1664],[1880,1884,1888],[1892,1896,1900]]){w(G+cap,0);w(G+ptr,4);w(G+len,0);}
  s.player_xy.forEach((v,j)=>w(G+1416+j*4,v));bytes()[G+360]=c.class_byte;bytes()[G+361]=1;bytes()[G+2582]=1;bytes()[G+2587]=s.phase;bytes()[G+908]=s.context908;
  d().setBigUint64(G+1336,BigInt(s.source_id),true);d().setBigUint64(G+776,BigInt(s.current_target_id),true);
  if(s.fixture_derived23){if(Object.keys(s.fixture_derived23).length!==23)throw Error('Explicit derived23 fragment');for(const[o,v]of Object.entries(s.fixture_derived23))w(G+Number(o),v);}
  for(const[o,key]of[[1536,'max_hp_bits'],[1440,'current_hp_bits'],[1540,'damage_multiplier_bits'],[1544,'cooldown_multiplier_bits'],[1548,'critical_chance_bits'],[1552,'critical_multiplier_bits'],[1580,'area_multiplier_bits']])w(G+o,s[key]);
  w(G+1592,s.extra_targets);w(G+1628,c.timer1628_bits);s.rng_words.forEach((v,j)=>w(G+1720+j*4,v));
  const A=allocate(80,4);bytes().set(Buffer.from(c.owned_hex,'hex'),A);w(G+1656,1);w(G+1660,A);w(G+1664,1);bytes().set(Buffer.from(c.basic_hex,'hex'),G+1256);
  for(const def of[c.definition,c.basic_definition])if(hex(def.pointer,88)!==def.definition_hex)throw Error('Static definition guard');
  const effect=allocate(12,4);w(effect,11);
  function tree(){const root=r(G+2476),depth=r(G+2480),fields=[],seen=new Set();if(!root)return{};if(depth>4)throw Error('Tree depth');function walk(p,level){if(!p||p+76>memory.buffer.byteLength||seen.has(p)||seen.size>128)throw Error('Tree');seen.add(p);const n=d().getUint16(p+50,true);if(n>11)throw Error('Tree count');for(let j=0;j<n;j++){if(level)walk(r(p+76+j*4),level-1);fields.push([d().getUint16(p+52+j*2,true),r(p+4+j*4)]);}if(level)walk(r(p+76+n*4),level-1);}walk(root,depth);return Object.fromEntries(fields);}
  function packets(){const n=r(G+1888),p=r(G+1884);if(n>256||n>r(G+1880))throw Error('Packet count');return Array.from({length:n},(_,j)=>{const q=p+j*16,n=r(q+8),b=r(q+4);if(n>r(q)||n>1048576||b+n>memory.buffer.byteLength)throw Error('Packet owner');return{opcode:d().getUint16(q+12,true),payload_hex:hex(b,n)};});}
  function aura(p){if(p.opcode!==169)return false;const b=Buffer.from(p.payload_hex,'hex');if(b.length<8||b.readUInt32LE()!==1||b[4]!==0||b[5]!==0)return false;let a=7;for(let j=0;j<8;j++)if(b[6]>>j&1)a++;if(a>=b.length)return false;const n=b[a++],keys=[];if(n>16||a+n*4>b.length)return false;for(let j=0;j<n;j++){const mask=b.readUInt32LE(a+j*4);for(let k=0;k<32;k++)if(mask>>>k&1)keys.push(j*32+k);}return keys.length===3&&keys.some(k=>k>=79&&k<=94)&&keys.some(k=>k>=99&&k<=100)&&keys.some(k=>k>=121&&k<=124);}
  function snapshot(){return{hp_bits:c.units424.map((_,j)=>r(U+j*424+288)),markers:c.units424.map((_,j)=>r(U+j*424)),rng_words:[0,1,2,3].map(j=>r(G+1720+j*4)),accounted_total_hex:d().getBigUint64(G+984,true).toString(16).padStart(16,'0'),attempted_spell_sets:[672,684,732].map(o=>{const p=r(G+o),n=r(G+o+4);if(n>1024)throw Error('Ledger');return Array.from({length:n},(_,j)=>r(p+j*4));}),owned_words:Array.from({length:20},(_,j)=>r(A+j*4)),basic_words:Array.from({length:20},(_,j)=>r(G+1256+j*4)),current_hp_bits:r(G+1440),player_fields:tree(),timer1628_bits:r(G+1628),debuffs:c.units424.map((_,j)=>{const p=U+j*424;return{guid:d().getBigUint64(p+112,true).toString(),marker:r(p),words128_140:[0,1,2,3].map(j=>r(p+128+j*4)),spell360:r(p+360),duration364_bits:r(p+364),aura_slots168:Array.from({length:16},(_,j)=>r(p+168+j*4)),ability_count240:r(p+240)};}),aura_packets:packets().filter(aura)};}
  for(const op of c.ops){w(G+2352,op.now_bits);const before=hex(G,8192);let success;
   if(op.kind==='effect'){w(effect+4,op.strength_bits);w(effect+8,op.duration_bits);call(2244,e.demo135_effect,G,BigInt(op.target_guid),effect,number(0),op.spell_id);}
   else if(op.kind==='cast')success=call(922,e.demo135_cast,G,A);
   else if(op.kind==='owned')call(1076,e.demo135_owned,G,number(op.dt_bits));
   else throw Error('Operation');
   stages.push({kind:op.kind,...(success===undefined?{}:{success}),projection:snapshot(),raw_units424_hex:c.units424.map((_,j)=>hex(U+j*424,424)),Game_before8192_hex:before,Game_after8192_hex:hex(G,8192),all_packets:packets()});
  }
 }
 peak=Math.max(peak,memory.buffer.byteLength);const line=JSON.stringify({id:c.id,stages})+'\n';outputBytes+=Buffer.byteLength(line);if(Buffer.byteLength(line)>2097152||outputBytes>33554432)throw Error('Output budget');process.stdout.write(line);completed++;if(global.gc)global.gc();
}}catch(error){failure=String(error);throw error;}finally{await fs.writeFile(dir+'/runtime.json',JSON.stringify({cases:cases.length,completed_cases:completed,fresh_instances:completed,calls,actual_host_calls:actualHostCalls,denied_imports:878,memory_cap_bytes:33554432,maximum_memory_bytes:peak,output_bytes:outputBytes,stack_checks:checks,stack_all_restored:checks.every(x=>x.returned&&x.before===1048576&&x.after===x.before),original_callees_unchanged:true,application_start_called:false,network_used:false,user_saves_accessed:false,original_memory_snapshot_read:false,failure},null,2)+'\n');}
