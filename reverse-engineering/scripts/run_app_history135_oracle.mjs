import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';
const [directory]=process.argv.slice(2),sha=x=>createHash('sha256').update(x).digest('hex');
const manifest=JSON.parse(await fs.readFile(`${directory}/manifest.json`,'utf8'));
const raw=await fs.readFile(`${directory}/${manifest.module_file}`);if(sha(raw)!==manifest.module_sha256)throw Error('Module hash');
const mod=await WebAssembly.compile(raw),surface=WebAssembly.Module.imports(mod);if(surface.length!==878)throw Error('Imports');
const cases=JSON.parse(await fs.readFile(`${directory}/inputs.json`,'utf8'));let calls=0,peak=0,hosts=0;
for(const c of cases){
 if(Object.keys(c).sort().join()!=='id,input'||Object.keys(c.input).sort().join()!=='offset,poison,warm_bytes')throw Error('Input shape');
 const imports={};for(const s of surface){imports[s.module]??={};imports[s.module][s.name]=()=>{hosts++;throw Error('Denied '+s.name);};}
 const instance=await WebAssembly.instantiate(mod,imports),ex=instance.exports,memory=ex.memory,d=()=>new DataView(memory.buffer),b=()=>new Uint8Array(memory.buffer);
 const alloc=n=>{if(n<1||n>4194304)throw Error('Allocation');const p=ex.__wbindgen_malloc(n,8)>>>0;if(!p||p+n>memory.buffer.byteLength||memory.buffer.byteLength>33554432)throw Error('Allocation budget');return p;};
 if(c.input.warm_bytes)alloc(c.input.warm_bytes);
 const p=alloc(512);b().fill(c.input.poison,p,p+512);const out=p+64+c.input.offset;
 ex.history135_empty(out);calls++;const initialized=Buffer.from(b().slice(p,p+512)).toString('hex');
 ex.history135_drop(out);calls++;const dropped=Buffer.from(b().slice(p,p+512)).toString('hex');
 if(d().getUint8(14523256)!==0)throw Error('Fresh seed global must be original uninitialized');
 ex.history135_seed();calls++;const seeded=Buffer.from(b().slice(14523240,14523257)).toString('hex');
 const ep=alloc(16);b().fill(0xa5,ep,ep+16);ex.history135_entropy(ep);calls++;
 const entropy=Buffer.from(b().slice(ep,ep+16)).toString('hex');
 if(ex.history135_stack.value!==1048576||hosts)throw Error('Stack/host');
 peak=Math.max(peak,memory.buffer.byteLength);
 process.stdout.write(JSON.stringify({id:c.id,initialized,dropped,seeded,entropy,stack:ex.history135_stack.value,memory_bytes:memory.buffer.byteLength,host_calls:hosts})+'\n');
}
await fs.writeFile(`${directory}/runtime.json`,JSON.stringify({cases:cases.length,original_calls:calls,by_role:{53845:cases.length,28797:cases.length,60416:cases.length,81334:cases.length},peak_memory_bytes:peak,memory_cap_bytes:33554432,denied_imports:878,host_calls:hosts,global_or_once_injected:false,address_dependent_seed_second_word_predicted:false},null,2)+'\n');
