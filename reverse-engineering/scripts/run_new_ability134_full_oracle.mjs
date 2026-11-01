// New-ability candidates through complete current1073 and all reached callees.
// No helper replacement, no application start, every878 host import throws.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';

const [moduleDirectory,caseFile,outputDirectory]=process.argv.slice(2);
const prepared=await prepareFull134(moduleDirectory,['select_ability']);
const text=await fs.readFile(caseFile,'utf8');
if(text.length>32*1024*1024)throw new Error('Fixture byte budget exceeded');
const cases=text.trim().split('\n').filter(Boolean).map(JSON.parse);
if(!cases.length||cases.length>12000)throw new Error('Fixture count outside budget');
let session,instances=0,maxMemory=0,hostTotal=0;
for(let i=0;i<cases.length;++i) {
  if(i%32===0){session=await prepared.fresh();++instances;}
  const c=cases[i];
  if(c.id!==i||c.modifiers.length>64||c.owned_hex.length>8)throw new Error('Fixture profile differs');
  const {memory,allocate,roles,hostCalls}=session;
  const v=()=>new DataView(memory.buffer),u32=(p,n)=>v().setUint32(p,n>>>0,true),u8=(p,n)=>v().setUint8(p,n&255);
  const bytes=(p,n)=>new Uint8Array(memory.buffer,p,n);
  const G=allocate(8192),candidate=allocate(80),def=c.definition_pointer;
  const baseline=Buffer.from(c.definition_raw88_hex,'hex');
  if(baseline.length!==88||!Buffer.from(bytes(def,88)).equals(baseline))throw new Error('Current definition source differs');
  const namePtr=v().getUint32(def+12,true),nameLen=v().getUint32(def+16,true);
  if(Buffer.from(bytes(namePtr,nameLen)).toString('ascii')!==c.ability_id)throw new Error('Current definition ID differs');
  const string=raw=>{const b=Buffer.from(raw,'hex'),p=allocate(Math.max(1,b.length),1);bytes(p,b.length).set(b);return[p,b.length];};
  const override=c.definition_override;
  if(override) {
    for(const [key,offset,kind]of [['execution_kind',84,'byte'],['school',85,'byte'],['effect_tag',0,'word'],['base_damage_bits',48,'word']])
      if(Object.hasOwn(override,key))(kind==='byte'?u8:u32)(def+offset,override[key]);
    if(Object.hasOwn(override,'kinds')){const p=allocate(Math.max(1,override.kinds.length),1);bytes(p,override.kinds.length).set(override.kinds);u32(def+36,p);u32(def+40,override.kinds.length);}
  }
  u8(G+360,1);u8(G+361,1);u32(G+1520,1);u8(G+2579,c.phase);u8(G+2577,c.selection_kind);
  u8(G+2574,0);u32(G+2368,1);
  if(c.owned_hex.length) {
    const p=allocate(c.owned_hex.length*80);
    for(let j=0;j<c.owned_hex.length;++j){const raw=Buffer.from(c.owned_hex[j],'hex');if(raw.length!==80)throw new Error('Owned record size differs');bytes(p+j*80,80).set(raw);}
    u32(G+1652,c.owned_hex.length);u32(G+1656,p);u32(G+1660,c.owned_hex.length);
  }
  if(c.modifiers.length) {
    const p=allocate(c.modifiers.length*20,4);
    for(let j=0;j<c.modifiers.length;++j) {
      const m=c.modifiers[j],a=p+j*20;u8(a,m.filter_tag);u8(a+1,m.filter_value);u8(a+12,m.kind);u32(a+16,m.value_bits);
      if((m.filter_tag&255)===1){const[q,n]=string(m.ability_id_hex);u32(a+4,q);u32(a+8,n);}
      else if((m.filter_tag&255)===2) {
        if(m.ability_ids_hex.length>32)throw new Error('Filter list budget exceeded');
        const list=allocate(Math.max(1,m.ability_ids_hex.length*8),4);
        for(let k=0;k<m.ability_ids_hex.length;++k){const[q,n]=string(m.ability_ids_hex[k]);u32(list+k*8,q);u32(list+k*8+4,n);}
        u32(a+4,list);u32(a+8,m.ability_ids_hex.length);
      }
    }
    u32(G+2028,c.modifiers.length);u32(G+2032,p);u32(G+2036,c.modifiers.length);
  }
  u32(candidate+60,0x80000000);u32(candidate+64,namePtr);u32(candidate+68,nameLen);u32(candidate+76,c.tier);
  u32(G+1896,1);u32(G+1900,candidate);u32(G+1904,1);
  roles.select_ability(G,c.choice_index);
  if(hostCalls.length)throw new Error('Original attempted a host call');
  hostTotal+=hostCalls.length;
  const pointer=v().getUint32(G+1656,true),count=v().getUint32(G+1660,true);
  if(count>9||(count&&(!pointer||pointer+count*80>memory.buffer.byteLength)))throw new Error('Owned vector outside fixture domain');
  const records=[];for(let j=0;j<count;++j)records.push(Buffer.from(bytes(pointer+j*80,80)).toString('hex'));
  const result={id:i,owned_records_hex:records,owned_count1660:count,phase2579:v().getUint8(G+2579),
    selection_kind2577:v().getUint8(G+2577),pending2368:v().getUint32(G+2368,true),
    candidate_count1904:v().getUint32(G+1904,true),host_calls:hostCalls.length};
  maxMemory=Math.max(maxMemory,memory.buffer.byteLength);
  bytes(def,88).set(baseline);
  if(!Buffer.from(bytes(def,88)).equals(baseline))throw new Error('Synthetic definition patch was not restored');
  process.stdout.write(JSON.stringify(result)+'\n');
}
await fs.writeFile(`${outputDirectory}/runtime.json`,JSON.stringify({version:'0.134.0',build:'983346a7',
  complete_original1073_executed:true,original_internal_callees:true,dependency_shims:[],actual_host_calls:hostTotal,
  denied_function_imports:878,original_allocator_index:91940,application_start_called:false,full_game_started:false,
  cases:cases.length,fresh_instances:instances,maximum_memory_bytes:maxMemory,memory_page_cap:512,
  scope:'Synthetic explicit new-ability candidate/modifier snapshots; current1073 append and reached original tail execute.'},null,2)+'\n');
