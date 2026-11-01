// Controlled actual914 -> actual2862 -> actual4630 observation. No application
// start or host APIs. This first probe records behavior; it is not a model test.
import fs from 'node:fs/promises';
import {prepareFull134} from './full134_host.mjs';
const [directory]=process.argv.slice(2);
const prepared=await prepareFull134(directory,['damage','collect_pickups']);
const host=await prepared.fresh(),{roles,memory,allocate,hostCalls}=host;
const G=allocate(8192),U=allocate(424),V=allocate(128);
let v=new DataView(memory.buffer);
const w=(p,x)=>v.setUint32(p,x>>>0,true),r=p=>v.getUint32(p,true),b=(p,x)=>v.setUint8(p,x);
const f=(p,x)=>v.setFloat32(p,x,true);
b(G+360,1);b(G+361,1);v.setBigUint64(G+1336,999n,true);
f(G+1360,100);f(G+1364,1);f(G+1376,2);f(G+1384,0);f(G+1388,1);
f(G+1504,-9396);f(G+1508,-633);f(G+1512,0);w(G+1520,120);f(G+1528,100);
w(G+1780,U);w(G+1784,1);w(G+2340,V);f(G+2344,10);b(G+2579,1);
[1,2,3,4].forEach((x,i)=>w(G+1712+4*i,x));
b(V+120,1);f(V+116,0);w(V+56,-1);
w(U+40,-1);w(U+64,-1);w(U+244,-1);w(U+284,5411616);
v.setBigUint64(U+112,1n,true);f(U+288,10);f(U+292,100);
for(const p of [316,328]){f(U+p,-9396);f(U+p+4,-633);f(U+p+8,0);}
function snapshot(){
  v=new DataView(memory.buffer);
  const count=r(G+1868),pointer=r(G+1864);
  if(count>100||pointer+count*56>memory.buffer.byteLength)throw Error('Pickup bounds');
  return{phase:r(G+2576)>>>24,level:r(G+1520),xp:r(G+1524),pending:r(G+2368),
    unit_hp_bits:r(U+288),unit_marker:r(U),now_bits:r(G+2344),spawn_counter:r(G+2400),
    scalar2412_bits:r(G+2412),rng:[0,1,2,3].map(i=>r(G+1712+4*i)),
    pickups:Array.from({length:count},(_,i)=>{
      const p=pointer+56*i,words=Array.from({length:14},(_,j)=>r(p+4*j));
      return{words,marker:words[0],arrival_bits:words[0]?words[1]:null,kind:words[2],amount:words[3],
        guid:v.getBigUint64(p+16,true).toString(16),raw56_hex:Buffer.from(memory.buffer,p,56).toString('hex')};
    })};
}
const result={method:'Observation only; no independent model comparison',original_source:prepared.manifest.original_wasm_sha256,
  original_functions:[914,2862,4630],fixture:{G_bytes:8192,world_bytes:128,unit_bytes:424,
    region:0,position:[-9396,-633,0],world_flat_gate:true,phase:1,initial_level:120,
    definition:5411616,initial_seed:[1,2,3,4]},before:snapshot()};
roles.damage(G,1n,20,133,2,0,0);result.after_death=snapshot();
roles.collect_pickups(G);result.after_attraction=snapshot();
const xp=result.after_attraction.pickups.find(x=>x.kind===0&&x.marker!==0);
if(!xp||xp.arrival_bits===null)throw Error('Expected attracted XP absent');
w(G+2344,xp.arrival_bits);roles.collect_pickups(G);result.at_arrival=snapshot();
if(hostCalls.length)throw Error('Host API attempted');
result.actual_host_calls=hostCalls;result.full_game_started=false;result.network_used=false;
result.user_saves_accessed=false;result.original_allocator=91940;result.memory_bytes=memory.buffer.byteLength;
await fs.writeFile(`${directory}/death-pickup134-probe.json`,JSON.stringify(result,null,2)+'\n');
process.stdout.write(JSON.stringify({result_file:`${directory}/death-pickup134-probe.json`,
  after_death_count:result.after_death.pickups.length,after_attraction_count:result.after_attraction.pickups.length,
  at_arrival_count:result.at_arrival.pickups.length,xp_at_arrival:result.at_arrival.xp,host_calls:hostCalls.length})+'\n');
