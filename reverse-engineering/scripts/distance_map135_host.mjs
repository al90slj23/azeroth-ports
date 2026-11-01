// Private distance-map fixture: unchanged921 + original allocator.
// global0 is only read inside this host; callers never receive its object.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

const sourceSHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2';
const digest = value => createHash('sha256').update(value).digest('hex');
const rolesAllowed = Object.freeze({update_units:921});
const stackExport = 'research135_distance_stack0';
const originalPath = new URL('../originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm', import.meta.url);
function leb(raw, p) {
  let n = 0, shift = 0;
  while (p < raw.length && shift <= 28) {const b = raw[p++]; n += (b & 127) * 2 ** shift; if (b < 128) return [n, p]; shift += 7;}
  throw Error('Malformed LEB');
}
function sections(raw) {
  if (raw.subarray(0, 8).toString('hex') !== '0061736d01000000') throw Error('Invalid WASM');
  const result = []; let p = 8;
  while (p < raw.length) {const start = p, kind = raw[p++], [size, begin] = leb(raw, p), end = begin + size;
    if (end > raw.length) throw Error('Section outside module'); result.push({kind, start, begin, end}); p = end;}
  return result;
}
function exportsOf(raw, section) {
  let [count, p] = leb(raw, section.begin); const result = [];
  for (let i = 0; i < count; i++) {const [n, begin] = leb(raw, p); p = begin + n;
    if (p >= section.end) throw Error('Export bounds'); const name = raw.subarray(begin, p).toString('utf8');
    const kind = raw[p++], [index, end] = leb(raw, p); p = end; result.push({name, kind, index});}
  if (p !== section.end) throw Error('Export boundary'); return result;
}
export async function prepareDistanceMap135(directory, requiredRoles) {
  if (!process.execArgv.includes('--wasm-max-mem-pages=512')) throw Error('Explicit32MiB memory cap required');
  if (JSON.stringify([...requiredRoles].sort()) !== JSON.stringify(Object.keys(rolesAllowed).sort())) throw Error('Exact private one-role surface required');
  const manifest = JSON.parse(await fs.readFile(`${directory}/manifest.json`, 'utf8'));
  if (manifest.module_file !== 'research135-exports.wasm' || manifest.version !== '0.135.1' || manifest.build !== '0898d5e3') throw Error('Wrong profile');
  const original = await fs.readFile(originalPath), changed = await fs.readFile(`${directory}/${manifest.module_file}`);
  if (original.length !== 90959080 || digest(original) !== sourceSHA || manifest.original_wasm_sha256 !== sourceSHA
      || changed.length > 92000000 || digest(changed) !== manifest.module_sha256) throw Error('Source identity');
  const before = sections(original), after = sections(changed);
  if (before.map(x => x.kind).join() !== after.map(x => x.kind).join() || before.some(x => x.kind === 8)) throw Error('Section/start profile');
  for (let i = 0; i < before.length; i++) {
    const a = before[i], b = after[i];
    if (a.kind !== 7 && !original.subarray(a.start, a.end).equals(changed.subarray(b.start, b.end))) throw Error('Nonexport bytes changed');
  }
  // Verify the global0 type/mutability/init directly from unchanged section6.
  const gs = before.find(s => s.kind === 6), [, startGlobal] = leb(original, gs.begin);
  if (original.subarray(startGlobal, startGlobal + 3).toString('hex') !== '7f0141') throw Error('Global0 type/init');
  const [stackInitial, globalEnd] = leb(original, startGlobal + 3);
  if (stackInitial !== 1048576 || original[globalEnd] !== 0x0b) throw Error('Global0 stack initial');
  const oldExports = exportsOf(original, before.find(s => s.kind === 7)), newExports = exportsOf(changed, after.find(s => s.kind === 7));
  if (JSON.stringify(oldExports) !== JSON.stringify(newExports.slice(0, oldExports.length))) throw Error('Original export prefix changed');
  const expected = Object.entries(rolesAllowed).map(([role, index]) => ({name:`research135_${role}`, kind:0, index}));
  expected.push({name:stackExport, kind:3, index:0});
  const added = newExports.slice(oldExports.length);
  if (JSON.stringify(added) !== JSON.stringify(expected)) throw Error('Private export surface differs');
  if (manifest.private_stack_export?.name !== stackExport || manifest.private_stack_export?.index !== 0 || manifest.roles.length !== 1
      || manifest.roles.some(r => rolesAllowed[r.role] !== r.index)) throw Error('Private manifest surface differs');
  if (!oldExports.some(x => x.name === '__wbindgen_malloc' && x.kind === 0 && x.index === 91941)) throw Error('Allocator export identity');
  const module = await WebAssembly.compile(changed), imports = WebAssembly.Module.imports(module);
  if (imports.length !== 878 || imports.some(x => x.kind !== 'function')) throw Error('Import profile');
  return {manifest, async fresh() {
    const hostCalls = [], bindings = {}, stackChecks = [];
    for (const item of imports) {bindings[item.module] ??= {}; bindings[item.module][item.name] = () => {
      hostCalls.push(`${item.module}.${item.name}`); throw Error('Original host call denied');};}
    const instance = await WebAssembly.instantiate(module, bindings), ex = instance.exports, memory = ex.memory, stack = ex[stackExport];
    if (!(memory instanceof WebAssembly.Memory) || !(stack instanceof WebAssembly.Global) || stack.value !== 1048576
        || typeof ex.__wbindgen_malloc !== 'function' || requiredRoles.some(role => typeof ex[`research135_${role}`] !== 'function')) throw Error('Runtime surface');
    const guarded = (role, fn) => (...args) => {
      const before = stack.value; let returned = false;
      if (before !== 1048576) {
        stackChecks.push({role, before, after:before, returned:false, entered:false});
        throw Error(`Original call denied at unexpected stack: ${role}`);
      }
      try {const result = fn(...args); returned = true; return result;}
      finally {const after = stack.value; stackChecks.push({role, before, after, returned, entered:true});
        if (before !== after || before !== 1048576) throw Error(`Original stack restoration failed: ${role}`);}
    };
    const roles = Object.freeze(Object.fromEntries(requiredRoles.map(role => [role, guarded(role, ex[`research135_${role}`])])));
    const allocateOriginal = guarded('__wbindgen_malloc', ex.__wbindgen_malloc);
    return Object.freeze({roles, memory, hostCalls,
      stackChecks: () => stackChecks.map(entry => Object.freeze({...entry})),
      allocate(size, alignment = 8) {
      if (!Number.isInteger(size) || size < 1 || size > 4194304 || ![1, 2, 4, 8, 16].includes(alignment)) throw Error('Allocation fixture budget');
      const p = allocateOriginal(size, alignment) >>> 0;
      if (!p || p + size > memory.buffer.byteLength || memory.buffer.byteLength > 32 * 1024 * 1024) throw Error('Allocation memory budget');
      new Uint8Array(memory.buffer, p, size).fill(0); return p;
    }});
  }};
}
