// Local REA extension: use the pinned library's real Evidence validation/digest.
// This is not the stock inspect_wasm_artifact provider and does not claim its admission passed.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pinned = JSON.parse(await fs.readFile(path.join(root, 'toolchain.json'), 'utf8'));
const installed = JSON.parse(await fs.readFile(path.join(root, '.toolchain/rea/node_modules/rea-agents/package.json'), 'utf8'));
const lock = JSON.parse(await fs.readFile(path.join(root, '.toolchain/rea/package-lock.json'), 'utf8'));
if (installed.version !== pinned.rea_version || lock.packages['node_modules/rea-agents'].integrity !== pinned.rea_tarball_integrity)
  throw new Error('Installed REA differs from the pinned package identity');
const { createEvidence, evidenceSchema } = await import(path.join(root, '.toolchain/rea/node_modules/rea-agents/dist/domain/evidence.js'));
const file = path.resolve(process.argv[2]);
const facts = JSON.parse(await fs.readFile(file, 'utf8'));
const original = await fs.readFile(facts.original_module.path);
if (createHash('sha256').update(original).digest('hex') !== facts.original_module.sha256) throw new Error('Original module identity changed');
const evidence = createEvidence({ path: facts.original_module.path, format: 'file', sha256: facts.original_module.sha256 },
  { id: 'azeroth-ports-local-wasm-focus', name: 'Azeroth Ports local streamed WASM research extension', version: '1+rea6.8.0+wabt1.0.42' },
  { operation: 'inspect_large_wasm_selected_functions',
    parameters: { function_indices: facts.selected_complete_functions.map(f => f.function_index), source_kind: 'complete-original-module' },
    result: facts, confidence: 'observed', authority: 'shipped-artifact',
    locations: facts.selected_complete_functions.map(f => ({kind: 'file-offset-range', start: f.body_start, end: f.body_end})),
    limitations: [
      'This explicitly identified local extension uses REA Evidence machinery and upstream WABT; stock REA inspect_wasm_artifact was not run on this oversized module.',
      'The complete original module was statically validated and decoded. Only the selected complete function slices and specified reference searches are retained in this focused result.',
      'WAT is decoded instructions, not original Rust source. Binary function indices, source digests and exact byte ranges are authoritative.',
      'Observed direct call instructions do not establish indirect callers, runtime reachability, time units, gameplay behavior or network delivery.',
      'No target execution, no game-file mutation and no implicit external network fetch occurred during analysis.'
    ] });
evidenceSchema.parse(evidence);
const output = path.join(path.dirname(file), 'rea-local-focused-evidence.json');
await fs.writeFile(output, JSON.stringify(evidence, null, 2) + '\n', {flag:'wx'});
console.log(JSON.stringify({evidence_id:evidence.evidence_id, provider:evidence.provider.id, output}));
