// Restricted harness for the fixed original module with additive exports.
// No original start or application export is returned. Every host import throws.
import fs from 'node:fs/promises';
import {createHash} from 'node:crypto';

export const originalSHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c';
export const digest = raw => createHash('sha256').update(raw).digest('hex');
const allowedFunctions = new Set([1065, 1573, 3231, 933, 934, 917, 25242, 32475, 85387, 106495, 71577]);

function leb(raw, p) {
  let value = 0, shift = 0;
  while (p < raw.length && shift <= 28) {
    const c = raw[p++]; value += (c & 127) * 2 ** shift;
    if (c < 128) return [value, p];
    shift += 7;
  }
  throw new Error('Malformed bounded LEB');
}

function sectionList(raw) {
  if (raw.subarray(0, 8).toString('hex') !== '0061736d01000000') throw new Error('Invalid WASM header');
  let p = 8; const result = [];
  while (p < raw.length) {
    const start = p, kind = raw[p++], [size, first] = leb(raw, p), end = first + size;
    if (end > raw.length) throw new Error('Section outside WASM');
    result.push({kind, start, first, end}); p = end;
  }
  return result;
}

function exportList(raw, section) {
  const [count, first] = leb(raw, section.first); let p = first; const result = [];
  for (let i = 0; i < count; ++i) {
    const [size, begin] = leb(raw, p); p = begin + size;
    if (p + 1 > section.end) throw new Error('Export outside section');
    const name = raw.subarray(begin, p).toString('utf8'), kind = raw[p++], [index, end] = leb(raw, p);
    result.push({name, kind, index}); p = end;
  }
  if (p !== section.end) throw new Error('Export section end differs');
  return result;
}

export async function prepareOriginalFunctions(runDirectory, originalPath, requiredFunctions) {
  if (!process.execArgv.includes('--wasm-max-mem-pages=512')) throw new Error('Explicit32MiB WASM runtime cap required');
  if (!requiredFunctions.length || requiredFunctions.some(x => !allowedFunctions.has(x)))
    throw new Error('Function outside admitted research set');
  const manifest = JSON.parse(await fs.readFile(`${runDirectory}/manifest.json`, 'utf8'));
  if (manifest.module_file !== 'research-exports.wasm') throw new Error('Unexpected research filename');
  const original = await fs.readFile(originalPath), changed = await fs.readFile(`${runDirectory}/research-exports.wasm`);
  if (digest(original) !== originalSHA || manifest.original_wasm_sha256 !== originalSHA
      || changed.length > 92_000_000 || digest(changed) !== manifest.module_sha256)
    throw new Error('Original/research SHA differs');
  const a = sectionList(original), b = sectionList(changed);
  if (a.map(x => x.kind).join() !== b.map(x => x.kind).join() || a.some(x => x.kind === 8))
    throw new Error('Section profile or implicit start differs');
  for (let i = 0; i < a.length; ++i)
    if (a[i].kind !== 7 && !original.subarray(a[i].start, a[i].end).equals(changed.subarray(b[i].start, b[i].end)))
      throw new Error('Nonexport original section changed');
  const exportsBefore = exportList(original, a.find(x => x.kind === 7));
  const exportsAfter = exportList(changed, b.find(x => x.kind === 7));
  if (JSON.stringify(exportsBefore) !== JSON.stringify(exportsAfter.slice(0, exportsBefore.length)))
    throw new Error('Existing exports changed');
  const added = exportsAfter.slice(exportsBefore.length);
  if (added.length !== manifest.research_functions.length
      || added.some((x, i) => x.kind !== 0 || x.name !== `research_f${x.index}`
                    || x.index !== manifest.research_functions[i] || !allowedFunctions.has(x.index))
      || new Set(added.map(x => x.name)).size !== added.length
      || requiredFunctions.some(index => !added.some(x => x.index === index)))
    throw new Error('Research exports differ');
  const module = await WebAssembly.compile(changed), imports = WebAssembly.Module.imports(module);
  if (imports.some(x => x.kind !== 'function')) throw new Error('Nonfunction host import forbidden');
  return {manifest, importCount: imports.length, async instantiate() {
    const hostCalls = [], importObject = {};
    for (const item of imports) {
      importObject[item.module] ??= {};
      importObject[item.module][item.name] = () => {
        hostCalls.push(`${item.module}.${item.name}`);
        throw new Error('Original host call denied');
      };
    }
    const instance = await WebAssembly.instantiate(module, importObject);
    const functions = Object.freeze(Object.fromEntries(requiredFunctions.map(i => [i, instance.exports[`research_f${i}`]])));
    if (Object.values(functions).some(x => typeof x !== 'function')
        || !(instance.exports.memory instanceof WebAssembly.Memory)) throw new Error('Invalid runtime surface');
    return {functions, memory: instance.exports.memory, hostCalls};
  }};
}
