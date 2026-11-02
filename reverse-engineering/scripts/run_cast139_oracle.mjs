// Complete original139922; synthetic quiet Game, no snapshot/App/start/host.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [dir, configFile] = process.argv.slice(2), hash = x => createHash('sha256').update(x).digest('hex');
if (!process.execArgv.includes('--wasm-max-mem-pages=512') || !process.execArgv.includes('--max-old-space-size=512')) throw Error('Explicit32MiB/512MiB caps');
const m = JSON.parse(await fs.readFile(dir+'/manifest.json')), config = JSON.parse(await fs.readFile(configFile));
const raw = await fs.readFile(dir+'/'+m.module_file), input = await fs.readFile(config.inputs);
if (m.original_sha256 !== '71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299' || m.entry.index !== 922 || m.entry.signature.join(':') !== '7f7f:7f'
    || m.version !== '0.139.0' || m.build !== 'f79c5e2b4' || m.only_changed_section !== 7 || m.implicit_start !== false
    || hash(raw) !== m.module_sha256 || hash(input) !== config.inputs_sha256 || input.length > 16777216) throw Error('Frozen139 cast identity');
const module = await WebAssembly.compile(raw), imports = WebAssembly.Module.imports(module), cases = JSON.parse(input);
if (imports.length !== 882 || imports.some(x=>x.kind !== 'function') || JSON.stringify(imports.map(({module,name})=>({module,name}))) !== JSON.stringify(m.original_imports.map(({module,name})=>({module,name}))) || cases.length > 512) throw Error('Exact882 deny surface');
let hostCalls = 0, peak = 0, calls = 0, observationBytes = 0, outputBytes = 0;
const stackChecks = [], f32 = n => {const a=new DataView(new ArrayBuffer(4));a.setUint32(0,n,true);return a.getFloat32(0,true);};
const observation = await fs.open(dir+'/observations.jsonl', 'wx');
for (const c of cases) {
  const bindings = {};
  for (const v of imports) {bindings[v.module]??={};bindings[v.module][v.name]=()=>{hostCalls++;throw Error('Denied '+v.name);};}
  const e = (await WebAssembly.instantiate(module, bindings)).exports, memory=e.memory, stack=e.research139_cast_stack0;
  const d=()=>new DataView(memory.buffer), b=()=>new Uint8Array(memory.buffer), u=p=>d().getUint32(p,true), w=(p,v)=>d().setUint32(p,v>>>0,true), hex=(p,n)=>Buffer.from(b().subarray(p,p+n)).toString('hex');
  const guard = (role,fn,...args) => {
    const before=stack.value;if(before!==1048576)throw Error('Stack before');let returned=false;
    try {const value=fn(...args);returned=true;return value;}
    finally {stackChecks.push({case:c.id,role,before,after:stack.value,returned});if(stack.value!==before)throw Error('Stack after');}
  };
  const alloc=n=>{if(n<1||n>1048576)throw Error('Allocation bound');const p=guard('malloc93344',e.__wbindgen_malloc,n,8)>>>0;
    if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Memory cap');b().fill(0,p,p+n);return p;};
  const s=c.state, G=alloc(8192), U=alloc(Math.max(1,s.units432_hex.length)*432), A=alloc(80);
  if (s.units432_hex.length>64 || c.repeats<1 || c.repeats>8) throw Error('Finite fixture shape');
  if (hex(m.definition.pointer,88)!==m.definition.raw88_hex)throw Error('Real definition88 unchanged');
  const owned=Buffer.from(c.owned80_hex,'hex');if(owned.length!==80||owned.readUInt32LE(0)!==m.definition.pointer)throw Error('Owned80 domain');b().set(owned,A);
  s.units432_hex.forEach((h,j)=>{const row=Buffer.from(h,'hex');if(row.length!==432)throw Error('Unit432');b().set(row,U+j*432);});
  for(const off of [2028,2052,600,648,1660,1884,1896,1812,1824,1836,1848,1860,1872,1908,1920,1968,2112,2124])w(G+off,8);
  w(G+1784,s.units432_hex.length);w(G+1788,U);w(G+1792,s.units432_hex.length);
  w(G+2352,s.now_bits);b()[G+2587]=s.phase2587;b()[G+360]=1;b()[G+361]=1;
  d().setBigUint64(G+984,BigInt(s.accounted_total_bits),true);d().setBigUint64(G+1336,BigInt(s.source_id),true);
  s.rng_words.forEach((v,j)=>w(G+1720+4*j,v));s.player_xyz.forEach((v,j)=>w(G+1416+4*j,v));
  for(const [off,key]of [[1536,'max_hp_bits'],[1540,'damage_multiplier_bits'],[1548,'critical_chance_bits'],[1552,'critical_multiplier_bits'],[1592,'extra_targets']])w(G+off,s[key]);
  w(G+1440,s.max_hp_bits);w(G+1544,0x3f800000);w(G+1580,0x3f800000);
  w(G+552,s.suppress_primary_attempt?1:0);
  const sets=[[664,668,672],[676,680,684],[724,728,732]];
  sets.forEach(([cap,ptr,count],j)=>{const values=s.spell_sets[j],p=values.length?alloc(values.length*4):8;w(G+cap,values.length);w(G+ptr,p);w(G+count,values.length);values.forEach((v,k)=>w(p+4*k,v));});
  const before=hex(G,2592), answers=[];let packetCursor=0;
  for(let k=0;k<c.repeats;k++){
    const success=guard('cast922',e.research139_cast922,G,A);calls++;
    if(hostCalls||memory.buffer.byteLength>33554432||hex(A,80)!==c.owned80_hex)throw Error('Quiet cast boundary');
    const spellSets=sets.map(([,ptr,count])=>{const n=u(G+count),p=u(G+ptr);if(n>128)throw Error('Set budget');return Array.from({length:n},(_,j)=>u(p+j*4));});
    const packets=[];const n=u(G+1888),p=u(G+1884);if(n>128)throw Error('Packet budget');
    for(let j=0;j<n;j++){const q=p+j*16,len=u(q+8);if(len>4096||len>u(q))throw Error('Payload bounds');packets.push([d().getUint16(q+12,true),hex(u(q+4),len)]);}
    const observed=JSON.stringify({id:c.id,stage:k,game_pointer:G,unit_pointer:U,game_before2592_hex:before,game_after2592_hex:hex(G,2592),packets,owned80_hex:hex(A,80)})+'\n';
    observationBytes+=Buffer.byteLength(observed);if(observationBytes>16777216)throw Error('Observation16MiB budget');await observation.write(observed);
    const launch306=packets.slice(packetCursor).filter(x=>x[0]===306);packetCursor=packets.length;
    answers.push({success,units432_hex:s.units432_hex.map((_,j)=>hex(U+j*432,432)),rng_words:[0,1,2,3].map(j=>u(G+1720+4*j)),accounted_total_bits:d().getBigUint64(G+984,true).toString(),spell_sets:spellSets,owned80_hex:hex(A,80),launch306_packets:launch306});
  }
  peak=Math.max(peak,memory.buffer.byteLength);const line=JSON.stringify({id:c.id,answers})+'\n';outputBytes+=Buffer.byteLength(line);if(outputBytes>16777216)throw Error('Output16MiB cap');process.stdout.write(line);
}
await observation.close();
await fs.writeFile(dir+'/runtime.json',JSON.stringify({version:'0.139.0',build:'f79c5e2b4',full922_calls:calls,fresh_instances:cases.length,snapshot_restores:0,denied_imports:882,actual_host_calls:hostCalls,peak_memory_bytes:peak,memory_cap_bytes:33554432,observation_bytes:observationBytes,output_bytes:outputBytes,stack_checks:stackChecks,all_normal_returns:stackChecks.every(x=>x.returned&&x.before===1048576&&x.after===x.before),natural_App:false,native_execution:false,complete_games:0})+'\n');
