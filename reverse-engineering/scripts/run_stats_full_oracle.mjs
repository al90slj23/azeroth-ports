// Execute actual original1573 and all original internal callees. The research
// module differs solely by additional exports. Every host import throws; no
// application start, UI, save, clock, network or imported function is invoked.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [runDirectory,originalPath,casesFile] = process.argv.slice(2);
const hash=b=>createHash('sha256').update(b).digest('hex');
const originalSHA='067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c';
const manifest=JSON.parse(await fs.readFile(`${runDirectory}/manifest.json`,'utf8'));
const original=await fs.readFile(originalPath),bytes=await fs.readFile(`${runDirectory}/${manifest.module_file}`);
if(hash(original)!==originalSHA||manifest.original_wasm_sha256!==originalSHA||hash(bytes)!==manifest.module_sha256||bytes.length>92_000_000)
  throw new Error('Original or research module identity differs');
function leb(raw,p){let n=0,s=0;while(p<raw.length&&s<=28){const c=raw[p++];n+=(c&127)*2**s;if(c<128)return[n,p];s+=7;}throw new Error('Bad LEB');}
function sections(raw){
  if(raw.subarray(0,8).toString('hex')!=='0061736d01000000')throw new Error('Bad WASM');
  const result=[];let p=8;
  while(p<raw.length){const start=p,kind=raw[p++],[size,first]=leb(raw,p),end=first+size;if(end>raw.length)throw new Error('Bad section');result.push({kind,start,end});p=end;}
  return result;
}
const old=sections(original),now=sections(bytes);
if(old.map(x=>x.kind).join()!==now.map(x=>x.kind).join()||old.some(x=>x.kind===8))throw new Error('Implicit start or section changes forbidden');
for(let i=0;i<old.length;i++)if(old[i].kind!==7&&!original.subarray(old[i].start,old[i].end).equals(bytes.subarray(now[i].start,now[i].end)))throw new Error('Changed original nonexport section');
const module=await WebAssembly.compile(bytes),imports=WebAssembly.Module.imports(module),hostCalls=[];
const importObject={};
for(const item of imports){
  if(item.kind!=='function')throw new Error('Nonfunction import forbidden');
  importObject[item.module]??={};importObject[item.module][item.name]=()=>{hostCalls.push(`${item.module}.${item.name}`);throw new Error('Denied original host call');};
}
const source=await fs.readFile(casesFile,'utf8');if(source.length>32*1024*1024)throw new Error('Fixture budget exceeded');
let ex,memory,d,mem,caseCount=0,instanceCount=0;
const fresh=async()=>{ex=(await WebAssembly.instantiate(module,importObject)).exports;memory=ex.memory;instanceCount++;};
const refresh=()=>{d=new DataView(memory.buffer);mem=new Uint8Array(memory.buffer);};
const allocate=n=>{
  if(n===0)return 8;
  const p=ex.research_f106495(n,8)>>>0;refresh();
  if(p===0||p+n>memory.buffer.byteLength||memory.buffer.byteLength>32*1024*1024)throw new Error('Original allocation outside budget');
  mem.fill(0,p,p+n);return p;
};
const u32=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw new Error('Invalid u32');d.setUint32(p,x,true);};
const u8=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw new Error('Invalid u8 source');d.setUint8(p,x&255);};
for(const line of source.split('\n')){
  if(!line)continue;
  if(caseCount%64===0)await fresh();
  if(++caseCount>20000)throw new Error('Fixture count exceeded');
  const c=JSON.parse(line),s=c.input,G=allocate(5000);
  const vector=(entries,stride,ptrOffset,lenOffset,write)=>{
    entries??=[];if(entries.length>4096)throw new Error('Vector budget exceeded');
    const p=allocate(entries.length*stride);u32(G+ptrOffset,p);u32(G+lenOffset,entries.length);
    entries.forEach((e,i)=>write(p+i*stride,e));
  };
  u8(G+360,s.class_byte??1);u8(G+361,s.race_byte??1);u32(G+1336,s.level??1);
  u32(G+1176,s.old_max_hp_bits??0);u32(G+1344,s.current_hp_bits??0);u32(G+2064,s.now_bits??0);
  u32(G+268,s.conditional268_bits??0);u8(G+2294,s.flag2294??0);u32(G+1456,s.previous_speed_bits??0x40e00000);
  d.setBigUint64(G+1152,1n,true);
  vector(s.passives,8,1504,1508,(p,e)=>{u32(p,e.tag);u32(p+4,e.value_bits);});
  vector(s.item_modifiers,8,1012,1016,(p,e)=>{u8(p,e.tag);u32(p+4,e.value_bits);});
  vector(s.adjustments,16,1480,1484,(p,e)=>{const def=allocate(40);u32(p,def);u32(p+4,e.value_bits);u32(def+32,e.definition32_bits??0);u8(def+36,e.tag);});
  vector(s.owned_skills,8,172,176,(p,e)=>{const def=allocate(32),raw=new TextEncoder().encode(e[0]);if(raw.length>128)throw new Error('Skill ID budget exceeded');const name=allocate(raw.length);mem.set(raw,name);u32(p,def);u8(p+4,e[1]);u32(def+24,name);u32(def+28,raw.length);});
  vector(s.timed_definitions,36,1036,1040,(p,e)=>{u32(p,e.kind);u32(p+20,e.value20_bits);u8(p+32,e.modifier_tag);});
  vector(s.timed_records,12,500,504,(p,e)=>{u32(p,e.definition_index);u32(p+4,e.stack_count);u32(p+8,e.expires_bits);});
  vector(s.live_effects,32,1516,1520,(p,e)=>{u32(p+8,e.kind);u32(p+12,e.value_bits);u32(p+20,e.spell_id);u32(p+24,e.expires_bits);});
  // Original3736 builds a real BTree from an empty map; original47820 builds a
  // real movement packet if speed differs. Their callees are not substituted.
  ex.research_f1573(G);refresh();
  const derived={};for(let offset=1176;offset<=1260;offset+=4)derived[offset]=d.getUint32(G+offset,true);
  const tree=d.getUint32(G+2188,true),keys=tree?[0,1,2].map(i=>d.getUint16(tree+52+i*2,true)):[];
  if(!tree||d.getUint16(tree+50,true)!==3||keys.join()!=='22,28,1109')throw new Error('Unexpected original field BTree');
  const output={id:c.id,derived_bits:derived,current_hp_bits:d.getUint32(G+1344,true),
    object_fields:{22:d.getUint32(tree+4,true),28:d.getUint32(tree+8,true),1109:d.getUint32(tree+12,true)},
    speed_bits:d.getUint32(G+1456,true),speed_sequence:d.getUint32(G+1452,true),
    movement_queue_count:d.getUint32(G+1696,true),host_calls:hostCalls.length,
    original_internal_callees:true,memory_bytes:memory.buffer.byteLength,instance_count:instanceCount};
  if(hostCalls.length)throw new Error('Host call attempted');
  process.stdout.write(JSON.stringify(output)+'\n');
}
