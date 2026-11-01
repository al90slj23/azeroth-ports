// Controlled original instruction slices, never the full933/934 or original game.
import fs from 'node:fs/promises';
const [moduleFile, casesFile] = process.argv.slice(2);
const bytes = await fs.readFile(moduleFile);
if (bytes.length > 16384) throw Error('Module size bound');
const module = await WebAssembly.compile(bytes);
if (WebAssembly.Module.imports(module).length) throw Error('Imports forbidden');
const x = (await WebAssembly.instantiate(module, {})).exports;
if (Object.keys(x).sort().join(',') !== 'base,cap,category_guard,critical,death,hp,memory,modifiers,wire') throw Error('Exports differ');
if (x.memory.buffer.byteLength !== 32*65536) throw Error('Memory bound');
const view = new DataView(x.memory.buffer), S=1024, U=8192, A=4096;
const w=(at,v)=>view.setUint32(at,v>>>0,true), r=at=>view.getUint32(at,true);
const val=new DataView(new ArrayBuffer(4));
const number=b=>{val.setUint32(0,b>>>0,true);return val.getFloat32(0,true)};
const invoke=(name,bits=0)=>x[name](S,1n,number(bits),0,0,0,0)>>>0;
function setup(c) {
  new Uint8Array(x.memory.buffer).fill(0);
  for (const [i,v] of [.5,.5,1,1,1,1,.5].entries()) view.setFloat32(1577964+i*4,v,true);
  if (!c.state) return;
  const s=c.state;
  w(S+1596,U);w(S+1600,s.units.length);w(S+1012,32768);w(S+1016,s.items.length);
  w(S+2064,s.now_bits);w(S+1348,s.shield_bits);view.setUint8(S+2299,s.running_2299);
  view.setFloat64(S+824,s.accounted_total,true);
  const offsets={hp_bits:288,max_hp_bits:292,marker:0,kind_40:40,linked_id_32:32,kind_64:64,
    elite_244:244,elite_412:412,afflicted_240:240,control_until_124_bits:124,control_until_376_bits:376,
    control_until_384_bits:384,additive_144_bits:144,additive_until_148_bits:148,additive_152_bits:152,
    additive_until_156_bits:156,additive_160_bits:160,additive_until_164_bits:164,additive_364_bits:364,
    phase_until_404_bits:404,phase_until_408_bits:408,movement_duration_344_bits:344,
    movement_time_340_bits:340,death_time_4_bits:4};
  s.units.forEach((u,i)=>{const at=U+i*416;for(const [key,off] of Object.entries(offsets)) {
    if(key==='linked_id_32')view.setBigUint64(at+off,BigInt(u[key]),true);else w(at+off,u[key]);
  }view.setBigUint64(at+112,BigInt(u.target_id),true)});
  s.items.forEach((item,i)=>{view.setUint8(32768+i*8,item.tag);w(32772+i*8,item.value_bits)});
}
const source=await fs.readFile(casesFile,'utf8');
if(source.length>32*1024*1024)throw Error('Case byte bound');
let count=0;
for(const line of source.split('\n')) {
  if(!line)continue;if(++count>30000)throw Error('Case bound');
  const c=JSON.parse(line);setup(c);let out={id:c.id};
  if(c.mode==='base') {
    const [d,a,b,k,h,hc,p]=c.input;
    w(A,U);w(U+48,d);view.setUint8(U+84,k);w(A+12,a);w(A+52,b);w(A+72,hc);w(S+1176,h);w(S+1180,p);
    out.bits=x.base(S,A)>>>0;
  } else if(c.mode==='critical') {
    w(S+2100,c.base);w(S+1188,c.probability);w(S+1192,c.multiplier);
    c.rng.forEach((v,i)=>w(S+1528+i*4,v));out.bits=x.critical(S,A)>>>0;
    out.critical=!!r(S+2104);out.rng=Array.from({length:4},(_,i)=>r(S+1528+4*i));
  } else if(c.mode==='category') {
    view.setUint8(U+84,c.category);out.allowed=!!invoke('category_guard');
  } else if(c.mode==='cap') {w(U+292,c.max_hp);out.bits=invoke('cap',c.amount);
  } else if(c.mode==='wire') {out.encoded=invoke('wire',c.hp);
  } else if(c.mode==='resolve') {
    let amount=x.modifiers(S,BigInt(c.target_id),number(c.amount),0,0,0,0)>>>0;
    const target=c.state.units.find(u=>u.target_id===c.target_id);
    if(target.kind_40===3&&target.linked_id_32===0)amount=invoke('cap',amount);
    out.modified_bits=amount;
    const skipped=target.kind_40===3&&target.linked_id_32===0&&number(amount)===0;
    out.applied=!skipped;
    if(!skipped)out.damage_bits=invoke('hp',amount);
    out.new_hp_bits=r(U+288);out.accounted_total_bits=view.getBigUint64(S+824,true).toString(16).padStart(16,'0');
    out.encoded=invoke('wire',out.new_hp_bits);
    out.dead=number(out.new_hp_bits)<=0;
    if(out.dead&&!skipped)invoke('death',c.state.now_bits);
    out.marker=r(U);out.afflicted_240=r(U+240);out.duration_bits=r(U+344);
    out.death_time_bits=r(U+4);out.movement_time_bits=r(U+340);
  } else throw Error('Unknown mode');
  process.stdout.write(JSON.stringify(out)+'\n');
}
