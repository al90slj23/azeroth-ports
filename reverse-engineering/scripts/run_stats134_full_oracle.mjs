// Complete current0.134.0 original1513 with unchanged internal callees.
// No application start; all878 host imports throw; synthetic state only.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';
const [directory,casesFile]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['recalculate_stats']);
const source=await fs.readFile(casesFile,'utf8');
if(source.length>32*1024*1024)throw new Error('Fixture budget exceeded');
let host,ex,memory,d,mem,caseCount=0,instanceCount=0;
const fresh=async()=>{host=await prepared.fresh();memory=host.memory;ex=host.roles;instanceCount++;};
const refresh=()=>{d=new DataView(memory.buffer);mem=new Uint8Array(memory.buffer);};
const allocate=n=>{const p=host.allocate(Math.max(n,8));refresh();return p;};
const u32=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw new Error('Invalid u32');d.setUint32(p,x,true);};
const u8=(p,x)=>{if(!Number.isInteger(x)||x<0||x>0xffffffff)throw new Error('Invalid u8 source');d.setUint8(p,x&255);};
for(const line of source.split('\n')){
  if(!line)continue;
  if(caseCount%64===0)await fresh();
  if(++caseCount>20000)throw new Error('Fixture count exceeded');
  const c=JSON.parse(line),s=c.input,G=allocate(8192);
  const vector=(entries,stride,ptrOffset,lenOffset,write)=>{
    entries??=[];if(entries.length>4096)throw new Error('Vector budget exceeded');
    const p=allocate(entries.length*stride);u32(G+ptrOffset,p);u32(G+lenOffset,entries.length);
    entries.forEach((e,i)=>write(p+i*stride,e));
  };
  u8(G+360,s.class_byte??1);u8(G+361,s.race_byte??1);u32(G+1520,s.level??1);
  u32(G+1360,s.old_max_hp_bits??0);u32(G+1528,s.current_hp_bits??0);u32(G+2344,s.now_bits??0);
  u32(G+268,s.conditional268_bits??0);u8(G+2574,s.flag2574??0);u32(G+1644,s.previous_speed_bits??0x40e00000);
  d.setBigUint64(G+1336,1n,true);
  for(const offset of [1532,1536,768])u32(G+offset,s[`pool${offset}_bits`]??0);
  u32(G+1344,s.conditional1344_id??0);u32(G+1348,s.conditional1348_bits??0);
  vector(s.passives,8,1692,1696,(p,e)=>{u32(p,e.tag);u32(p+4,e.value_bits);});
  vector(s.item_modifiers,8,2020,2024,(p,e)=>{u8(p,e.tag);u32(p+4,e.value_bits);});
  vector(s.adjustments,16,1668,1672,(p,e)=>{const def=allocate(40);u32(p,def);u32(p+4,e.value_bits);u32(def+32,e.definition32_bits??0);u8(def+36,e.tag);});
  vector(s.owned_skills,8,172,176,(p,e)=>{const def=allocate(40),raw=new TextEncoder().encode(e[0]);if(raw.length>128)throw new Error('Skill ID budget exceeded');const name=allocate(raw.length);mem.set(raw,name);u32(p,def);u8(p+4,e[1]);u32(def+32,name);u32(def+36,raw.length);});
  vector(s.timed_definitions,36,2044,2048,(p,e)=>{u32(p,e.kind);u32(p+20,e.value20_bits);u8(p+32,e.modifier_tag);});
  vector(s.timed_records,12,600,604,(p,e)=>{u32(p,e.definition_index);u32(p+4,e.stack_count);u32(p+8,e.expires_bits);});
  vector(s.live_effects,32,1704,1708,(p,e)=>{u32(p+8,e.kind);u32(p+12,e.value_bits);u32(p+20,e.spell_id);u32(p+24,e.expires_bits);});
  // Original3735 builds a real BTree from an empty map; original48065 builds a
  // real movement packet if speed differs. Their callees are not substituted.
  ex.recalculate_stats(G);refresh();
  const derived={};for(let offset=1360;offset<=1444;offset+=4)derived[offset]=d.getUint32(G+offset,true);
  const tree=d.getUint32(G+2468,true),keys=tree?[0,1,2].map(i=>d.getUint16(tree+52+i*2,true)):[];
  if(!tree||d.getUint16(tree+50,true)!==3||keys.join()!=='22,28,1109')throw new Error('Unexpected original field BTree');
  const output={id:c.id,derived_bits:derived,current_hp_bits:d.getUint32(G+1528,true),
    object_fields:{22:d.getUint32(tree+4,true),28:d.getUint32(tree+8,true),1109:d.getUint32(tree+12,true)},
    auxiliary_bits:Object.fromEntries([1532,1536,1348,768].map(o=>[o,d.getUint32(G+o,true)])),
    speed_bits:d.getUint32(G+1644,true),speed_sequence:d.getUint32(G+1640,true),
    movement_queue_count:d.getUint32(G+1880,true),host_calls:host.hostCalls.length,
    original_internal_callees:true,memory_bytes:memory.buffer.byteLength,instance_count:instanceCount};
  if(host.hostCalls.length)throw new Error('Host call attempted');
  process.stdout.write(JSON.stringify(output)+'\n');
}
