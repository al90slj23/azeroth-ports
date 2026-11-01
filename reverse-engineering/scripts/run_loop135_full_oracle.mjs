// Full original0.135.1 tick880 / raw-command1371; no original body is replaced.
import fs from 'node:fs/promises';
import {prepareFull135} from './full135_host.mjs';

const [directory,casefile]=process.argv.slice(2);
const cases=JSON.parse(await fs.readFile(casefile,'utf8'));
const prepared=await prepareFull135(directory,['tick','command']);
let fixture,fresh=0,maximum=0,tickCalls=0,commandCalls=0;
const bits64Buffer=new ArrayBuffer(8),bits64View=new DataView(bits64Buffer);
function number64(bits){bits64View.setBigUint64(0,BigInt(bits),true);return bits64View.getFloat64(0,true);}
for(const c of cases){
  if(c.id%32===0){fixture=await prepared.fresh();fresh++;}
  const context=fixture.allocate(16384),game=context+16;
  let view=new DataView(fixture.memory.buffer);
  view.setBigUint64(context,BigInt(c.clock.previous_marker),true);
  view.setBigUint64(context+8,BigInt(c.clock.previous_time_bits),true);
  view.setBigUint64(game,BigInt(c.clock.game_discriminant),true);
  // Original880 skips its optional transport trait-object block at this niche.
  // Zero denotes a present transport and is not a valid empty-context default.
  view.setInt32(context+4748,-1,true);
  // Original880's outer session-role enum uses2 for its absent variant.
  view.setBigUint64(context+2608,2n,true);
  // A real original transport implementation, not a replacement function:
  // constructor4253 binds vtable1495776; method+20 is original45626. Its
  // empty RefCell queue drains to an empty232B-record vector without hosts.
  const transportCell=fixture.allocate(64),transport=fixture.allocate(24);
  view=new DataView(fixture.memory.buffer);
  view.setUint32(transportCell,1,true);view.setUint32(transportCell+4,1,true);
  view.setUint32(transportCell+32,8,true);view.setInt32(transportCell+40,-1,true);
  view.setInt32(transport+8,-1,true);view.setUint32(transport+16,transportCell,true);
  view.setUint32(context+4768,transport,true);view.setUint32(context+4772,1495776,true);
  // Original880's0.2-second serialized-snapshot guard. That independent
  // snapshot is already up-to-date in this controlled clock fixture.
  view.setFloat64(context+4840,number64(c.now_bits),true);
  // Initial terminal states have already delivered their one-shot end callback.
  // Newly reached terminal states remain outside this no-host fixture domain.
  view.setUint8(context+5166,c.clock.mode===0?c.clock.phase:c.clock.global_phase);
  view.setUint32(game+2352,c.clock.simulation_clock_bits,true);
  view.setUint8(game+2582,c.clock.mode);view.setUint8(game+2587,c.clock.phase);
  view.setUint8(game+2588,c.clock.global_phase);
  // Explicit synthetic positive health, levelcap, no queues/units/world claims.
  view.setUint32(game+1440,0x42c80000,true);view.setUint32(game+1536,0x42c80000,true);
  view.setUint32(game+1432,120,true);
  // This real mainloop guard omits947/2376 only; all other reached bodies remain.
  view.setUint8(game+2579,c.skip_spawn?1:0);
  const before=new Uint8Array(fixture.memory.buffer,context,16384).slice();
  let error=null,errorStack=null;
  try {
    if(c.kind==='pause'){
      const command=fixture.allocate(16);view=new DataView(fixture.memory.buffer);
      view.setUint32(command,7,true);view.setUint8(command+4,c.payload_byte);
      fixture.roles.command(context,command);commandCalls++;
    }else if(c.kind==='tick'){
      fixture.roles.tick(context,number64(c.now_bits));tickCalls++;
    }else throw new Error('Unapproved fixture kind');
  }catch(caught){error=String(caught);errorStack=caught.stack;}
  view=new DataView(fixture.memory.buffer);
  const row={id:c.id,kind:c.kind,previous_marker:view.getBigUint64(context,true).toString(),
    previous_time_bits:view.getBigUint64(context+8,true).toString(),
    simulation_clock_bits:view.getUint32(game+2352,true),phase:view.getUint8(game+2587),
    global_phase:view.getUint8(game+2588),actual_host_calls:fixture.hostCalls.length};
  if(c.inspect_mutations){
    const after=new Uint8Array(fixture.memory.buffer,context,16384);
    row.changed_context_bytes=[];
    for(let i=0;i<after.length;i++)if(before[i]!==after[i])row.changed_context_bytes.push([i,before[i],after[i]]);
  }
  if(error){row.error=error;row.error_stack=errorStack;}
  console.log(JSON.stringify(row));
  maximum=Math.max(maximum,fixture.memory.buffer.byteLength);
  if(error||fixture.hostCalls.length)throw new Error('Controlled original entry failed; see retained row');
}
await fs.writeFile(`${directory}/loop135-runtime.json`,JSON.stringify({case_count:cases.length,
  tick_calls:tickCalls,command_calls:commandCalls,fresh_instances:fresh,fresh_instance_every:32,
  maximum_memory_bytes:maximum,memory_page_cap:512,actual_host_calls:0,denied_function_imports:878,
  original_entries:{tick:880,command:1371},original_internal_callees_unchanged:true,
  application_start_called:false,full_game_started:false,user_saves_accessed:false,network_used:false,
  fixture_scope:'Synthetic zero queues/units, positive health, level120, real2579 skip-spawn guard; absent outer session/optional transport and original queue implementation; serialized snapshot current, initial end callback already handled.'},null,2)+'\n');
