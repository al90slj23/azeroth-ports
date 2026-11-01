// Original3231 plus every reached original internal callee. Synthetic paused
// fixtures deliberately bypass2098 generation; no source instructions stubbed.
import fs from 'node:fs/promises';
import {prepareOriginalFunctions} from './full_function_host.mjs';

const [runDirectory, originalPath, casesFile] = process.argv.slice(2);
const prepared = await prepareOriginalFunctions(runDirectory, originalPath, [3231, 106495]);
const text = await fs.readFile(casesFile, 'utf8');
if (text.length > 8 * 1024 * 1024) throw new Error('Fixture byte budget exceeded');
const cases = text.trim().split('\n').filter(Boolean).map(JSON.parse);
if (!cases.length || cases.length > 4000) throw new Error('Fixture count budget exceeded');
let session, maximumMemory = 0, instances = 0, hostCount = 0;
for (let i = 0; i < cases.length; ++i) {
  const c = cases[i];
  if (c.id !== i || Object.values(c.state).some(x => !Number.isInteger(x) || x < 0 || x > 0xffffffff)
      || !Number.isInteger(c.amount) || c.amount < 0 || c.amount > 0xffffffff)
    throw new Error('Invalid fixture');
  if (i % 32 === 0) {session = await prepared.instantiate(); ++instances;}
  const {functions, memory, hostCalls} = session, g = functions[106495](5000, 8) >>> 0;
  if (!g || g + 5000 > memory.buffer.byteLength) throw new Error('Synthetic state allocation failed');
  new Uint8Array(memory.buffer, g, 5000).fill(0);
  let v = new DataView(memory.buffer);
  v.setUint8(g + 360, 1); v.setUint8(g + 361, 1);
  v.setUint32(g + 1336, c.state.level, true); v.setUint32(g + 1340, c.state.xp, true);
  v.setUint32(g + 2088, c.state.pending_upgrades, true);
  v.setUint8(g + 2299, 3); // Original3231 itself applies XP despite paused phase.
  v.setBigUint64(g + 1152, 1n, true);
  functions[3231](g, c.amount);
  v = new DataView(memory.buffer);
  if (hostCalls.length) throw new Error('Original attempted a host call');
  const state = {level: v.getUint32(g + 1336, true), xp: v.getUint32(g + 1340, true),
                 pending_upgrades: v.getUint32(g + 2088, true)};
  maximumMemory = Math.max(maximumMemory, memory.buffer.byteLength);
  process.stdout.write(JSON.stringify({id: i, state, phase2299: v.getUint8(g + 2299),
    oracle_scope: 'original3231 including reached internal callees; paused phase skips2098'}) + '\n');
  hostCount += hostCalls.length;
}
await fs.writeFile(`${runDirectory}/full-progression-runtime.json`, JSON.stringify({original3231_executed: true,
  original1573_reached_on_levelup: true, dependency_shims: [], actual_host_calls: hostCount,
  full_game_started: false, cases: cases.length, fresh_instances: instances,
  maximum_memory_bytes: maximumMemory, denied_function_imports: prepared.importCount,
  phase_fixture: 3, original2098_executed: false}, null, 2) + '\n');
