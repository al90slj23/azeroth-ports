// Controlled full-original933 execution with synthetic state. All host calls
// throw. Neither original start export is called. No game UI/network/save APIs.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

const [runDirectory, originalPath, casesFile, resultFile] = process.argv.slice(2);
const hash = b => createHash('sha256').update(b).digest('hex');
const originalSHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c';
const manifest = JSON.parse(await fs.readFile(`${runDirectory}/manifest.json`, 'utf8'));
const original = await fs.readFile(originalPath);
const bytes = await fs.readFile(`${runDirectory}/${manifest.module_file}`);
if (hash(original) !== originalSHA || manifest.original_wasm_sha256 !== originalSHA
    || hash(bytes) !== manifest.module_sha256 || bytes.length > 92_000_000)
  throw new Error('Original/research module identity differs');
function readU32(raw, p) {
  let n = 0, shift = 0;
  while (p < raw.length && shift <= 28) {
    const c = raw[p++]; n += (c & 127) * 2 ** shift;
    if (c < 128) return [n, p];
    shift += 7;
  }
  throw new Error('Malformed LEB');
}
function sections(raw) {
  if (raw.subarray(0, 8).toString('hex') !== '0061736d01000000') throw new Error('Bad header');
  let p = 8; const result = [];
  while (p < raw.length) {
    const start = p, kind = raw[p++], [size, first] = readU32(raw, p), end = first + size;
    if (end > raw.length) throw new Error('Bad section bound');
    result.push({kind, start, first, end}); p = end;
  }
  return result;
}
const oldSections = sections(original), newSections = sections(bytes);
if (oldSections.map(s => s.kind).join() !== newSections.map(s => s.kind).join()
    || oldSections.some(s => s.kind === 8)) throw new Error('Implicit start or section changes forbidden');
for (let i = 0; i < oldSections.length; ++i) {
  const a = oldSections[i], b = newSections[i];
  if (a.kind !== 7 && !original.subarray(a.start, a.end).equals(bytes.subarray(b.start, b.end)))
    throw new Error(`Changed original nonexport section${a.kind}`);
}
const module = await WebAssembly.compile(bytes);
const importObject = {}, hostCalls = [];
for (const item of WebAssembly.Module.imports(module)) {
  if (item.kind !== 'function') throw new Error('Nonfunction host import forbidden');
  importObject[item.module] ??= {};
  importObject[item.module][item.name] = () => {
    hostCalls.push(`${item.module}.${item.name}`);
    throw new Error('Denied original host import');
  };
}
const scalar = new DataView(new ArrayBuffer(4));
const number = b => { scalar.setUint32(0,b>>>0,true); return scalar.getFloat32(0,true); };
const cases = JSON.parse(await fs.readFile(casesFile,'utf8'));
if(cases.length>2000)throw Error('Case bound');
const outputs=[];
for(const c of cases) {
  const instance = await WebAssembly.instantiate(module, importObject);
  const {memory, research_f933: damage, research_f106495: allocate} = instance.exports;
  if (!(memory instanceof WebAssembly.Memory) || typeof damage !== 'function' || typeof allocate !== 'function')
    throw Error('Research exports missing');
  const G=allocate(5000,8)>>>0,U=allocate(416,8)>>>0;
  if(!G||!U)throw Error('Original allocation failed');
  new Uint8Array(memory.buffer,G,5000).fill(0);
  new Uint8Array(memory.buffer,U,416).fill(0);
  let v=new DataView(memory.buffer);
  const w=(p,b)=>v.setUint32(p,b>>>0,true);
  w(G+1596,U);w(G+1600,1);v.setUint8(G+2299,1);w(G+2064,c.now_bits);
  w(G+1176,0x42c80000);w(G+1180,0x3f800000);w(G+1192,0x40000000);
  w(G+1336,1);w(G+1152,1);v.setUint8(G+360,1);v.setUint8(G+361,1);
  v.setBigUint64(U+112,1n,true);w(U+288,c.hp_bits);w(U+292,c.max_hp_bits);
  w(U+244,-1);w(U+64,-1);w(U+40,-1);w(U+284,1667680);
  c.rng.forEach((b,i)=>w(G+1528+i*4,b));
  for(const [offset,b] of Object.entries(c.unit_overrides||{}))w(U+Number(offset),b);
  for(const [offset,b] of Object.entries(c.state_overrides||{}))w(G+Number(offset),b);
  if(c.items?.length) {
    const itemPointer=allocate(c.items.length*8,4)>>>0;
    v=new DataView(memory.buffer);
    w(G+1012,itemPointer);w(G+1016,c.items.length);
    c.items.forEach(([tag,b],i)=>{w(itemPointer+i*8,tag);w(itemPointer+i*8+4,b)});
  }
  const out={id:c.id};
  try { damage(G,1n,number(c.amount_bits),133,2,0,0);out.completed=true; }
  catch(e){out.completed=false;out.error=String(e);out.stack=e.stack;}
  v=new DataView(memory.buffer);
  const r=p=>v.getUint32(p,true);
  for(const [key,off] of Object.entries({hp_bits:288,marker:0,duration_bits:344,afflicted_240:240,death_time_bits:4,movement_time_bits:340}))out[key]=r(U+off);
  out.accounted_total_bits=v.getBigUint64(G+824,true).toString(16).padStart(16,'0');
  out.rng=Array.from({length:4},(_,i)=>r(G+1528+4*i));
  out.packet_queue_count=r(G+1696);out.xp_orb_count=r(G+1804);out.drop_count=r(G+1768);out.memory_bytes=memory.buffer.byteLength;
  out.state_pointer=G;out.unit_pointer=U;outputs.push(out);
  if(hostCalls.length)throw Error('Host call attempted');
}
const receipt={original_wasm_sha256:originalSHA,module_sha256:hash(bytes),
  scope:'Actual full original933 with synthetic allocated state; original internal callees retained. No application start or host API called.',
  original_full_933_executed:true,original_allocator_executed:true,actual_host_calls:hostCalls,
  import_count:WebAssembly.Module.imports(module).length,full_game_started:false,network_used:false,user_saves_accessed:false,
  case_count:outputs.length,completed:outputs.filter(x=>x.completed).length,outputs};
await fs.writeFile(resultFile,JSON.stringify(receipt,null,2)+'\n');
process.stdout.write(JSON.stringify({case_count:outputs.length,completed:receipt.completed,host_calls:hostCalls.length,result_file:resultFile})+'\n');
