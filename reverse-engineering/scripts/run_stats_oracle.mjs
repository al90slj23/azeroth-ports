// Original1573 body only, with WASM allocation shims and every other callee trap.
// All memory is synthetic. No imports, game entry, network, user-save or host call.
import fs from 'node:fs/promises';
const [wasmFile,casesFile] = process.argv.slice(2);
const bytes = await fs.readFile(wasmFile);
if (bytes.length > 2*1024*1024) throw new Error('Oracle module budget exceeded');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length) throw new Error('Host imports forbidden');
const expected = ['allocations:global','frees:global','heap:global','memory:memory','recalculate:function','reserves:global','stack:global'];
if (WebAssembly.Module.exports(module).map(e=>`${e.name}:${e.kind}`).sort().join(',')!==expected.join(',')) throw new Error('Unexpected exports');
const instance = await WebAssembly.instantiate(module,{}), ex = instance.exports;
const mem = new Uint8Array(ex.memory.buffer), d = new DataView(mem.buffer);
const BASE = 0x1000000, TREE = BASE+4096, ARENA = BASE+8192;
const u32=(p,x)=> { if (!Number.isInteger(x)||x<0||x>0xffffffff) throw new Error('Invalid u32'); d.setUint32(p,x,true); };
const u8=(p,x)=>u32check(x)&&d.setUint8(p,x&255);
const u32check=x=> { if (!Number.isInteger(x)||x<0||x>0xffffffff) throw new Error('Invalid u32'); return true; };
const source=await fs.readFile(casesFile,'utf8');
if (source.length > 32*1024*1024) throw new Error('Fixture budget exceeded');
let caseCount=0;
for (const line of source.split('\n')) {
  if (!line) continue;
  if (++caseCount>20000) throw new Error('Fixture count exceeded');
  const c=JSON.parse(line), s=c.input;
  mem.fill(0,BASE,BASE+1024*1024);
  ex.heap.value=0x1800000; ex.stack.value=0x1f00000;
  ex.allocations.value=0;ex.reserves.value=0;ex.frees.value=0;
  let next=ARENA;
  const alloc=n=> { const p=next;next=(next+n+7)&~7;if(next>BASE+1024*1024)throw new Error('Fixture memory exceeded');return p; };
  const vector=(entries,stride,ptrOffset,lenOffset,write)=> {
    entries??=[];if(entries.length>4096)throw new Error('Vector budget exceeded');
    const p=alloc(entries.length*stride);u32(BASE+ptrOffset,p);u32(BASE+lenOffset,entries.length);
    entries.forEach((e,i)=>write(p+i*stride,e));
  };
  u8(BASE+360,s.class_byte??1);u8(BASE+361,s.race_byte??1);u32(BASE+1336,s.level??1);
  u32(BASE+1176,s.old_max_hp_bits??0);u32(BASE+1344,s.current_hp_bits??0);
  u32(BASE+2064,s.now_bits??0);u32(BASE+268,s.conditional268_bits??0);u8(BASE+2294,s.flag2294??0);
  // This fixture deliberately excludes message construction47820 and queue
  // growth65040. Matching the independently predicted speed bypasses that path.
  u32(BASE+1456,c.oracle_speed_bits);
  vector(s.passives,8,1504,1508,(p,e)=>{u32(p,e.tag);u32(p+4,e.value_bits);});
  vector(s.item_modifiers,8,1012,1016,(p,e)=>{u8(p,e.tag);u32(p+4,e.value_bits);});
  vector(s.adjustments,16,1480,1484,(p,e)=>{
    const def=alloc(40);u32(p,def);u32(p+4,e.value_bits);u32(def+32,e.definition32_bits??0);u8(def+36,e.tag);
  });
  vector(s.owned_skills,8,172,176,(p,e)=>{
    const def=alloc(32),raw=new TextEncoder().encode(e[0]);if(raw.length>128)throw new Error('Skill ID exceeded');
    const name=alloc(raw.length);mem.set(raw,name);u32(p,def);u8(p+4,e[1]);u32(def+24,name);u32(def+28,raw.length);
  });
  vector(s.timed_definitions,36,1036,1040,(p,e)=>{u32(p,e.kind);u32(p+20,e.value20_bits);u8(p+32,e.modifier_tag);});
  vector(s.timed_records,12,500,504,(p,e)=>{u32(p,e.definition_index);u32(p+4,e.stack_count);u32(p+8,e.expires_bits);});
  vector(s.live_effects,32,1516,1520,(p,e)=>{u32(p+8,e.kind);u32(p+12,e.value_bits);u32(p+20,e.spell_id);u32(p+24,e.expires_bits);});
  // Synthetic single-leaf BTree with the three exact keys already present.
  // Original1573 traverses and writes the values; insertion3736 stays a trap.
  u32(BASE+2188,TREE);u32(BASE+2192,0);d.setUint16(TREE+50,3,true);
  [22,28,1109].forEach((key,i)=>d.setUint16(TREE+52+2*i,key,true));
  ex.recalculate(BASE);
  const derived={};for(let offset=1176;offset<=1260;offset+=4)derived[offset]=d.getUint32(BASE+offset,true);
  const output={id:c.id,derived_bits:derived,current_hp_bits:d.getUint32(BASE+1344,true),
    object_fields:{22:d.getUint32(TREE+4,true),28:d.getUint32(TREE+8,true),1109:d.getUint32(TREE+12,true)},
    speed_bits:d.getUint32(BASE+1456,true),allocation_calls:ex.allocations.value,
    reserve_calls:ex.reserves.value,free_calls:ex.frees.value};
  // The range contains22 4B locations. Each is actually written by1573.
  process.stdout.write(JSON.stringify(output)+'\n');
}
