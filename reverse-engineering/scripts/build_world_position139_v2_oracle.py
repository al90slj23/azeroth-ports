#!/usr/bin/env python3
"""Re-admit the identical original139 exportmodule, no behavior pass transfer.

Only independent Python rule13563 changed. The targetbinary is byteidentical
with the previously wasm-validated originalmodule; Node compiles it fresh.
No new static-validator process isneeded for identicalbytes. The failed45s
redundant validator preparation remains recorded separately.
"""
import hashlib,json
from build_world_position139_oracle import ROOT,SOURCE,SOURCE_SHA,sha,save,missing,binary_identity,export_entries
PRIOR=ROOT/'evidence/world-position139-oracle-20261102T035151.444640Z'
MODULE_SHA='6988ceb9689c8c8389aa88cb5cd19cfca174b7b20d95512f7d8912fa334cf271'

def build(out):
 original=SOURCE.read_bytes();assert hashlib.sha256(original).hexdigest()==SOURCE_SHA
 prior=json.loads((PRIOR/'manifest.json').read_text());old=(PRIOR/prior['module_file']).read_bytes();assert hashlib.sha256(old).hexdigest()==MODULE_SHA==prior['module_sha256']and prior['source_sha256']==SOURCE_SHA
 validator=json.loads((PRIOR/'validator-terminal.json').read_text());assert validator['exit_code']==0 and validator['pid_missing']and validator['pgid_missing']
 a,ranges=binary_identity(original);b,_=binary_identity(old);assert not a['implicit_start_section']
 for x,y in zip(a['sections'],b['sections']):
  assert x['kind']==y['kind']
  if x['kind']!=7:assert original[x['start']:x['end']]==old[y['start']:y['end']]
 before,_=export_entries(original,next(s for s in a['sections']if s['kind']==7));after,_=export_entries(old,next(s for s in b['sections']if s['kind']==7));added=[('research139_position_spawn',0,8740),('research139_position_random',0,13563),('research139_position_stack0',3,0)];assert after==before+added
 for row in prior['roles']:
  start,end,_=ranges[row['index']];assert hashlib.sha256(original[start:end]).hexdigest()==row['body_sha256']
 module=out/'world-position139-v2-original.wasm';module.write_bytes(old);assert sha(module)==MODULE_SHA
 manifest=dict(prior);manifest.update(module_file=module.name,module_sha256=MODULE_SHA,kind='identical_original139_binary_admission_reused_independent_rule_v2',
  validator=dict(reused_for_identical_binary=True,source=str(PRIOR/'validator-terminal.json'),source_sha256=sha(PRIOR/'validator-terminal.json'),prior_receipt=validator),prior_manifest_sha256=sha(PRIOR/'manifest.json'),new_static_validator_processes=0,Node_fresh_compile_required=True,old_model_acceptance_transferred=False)
 save(out/'manifest.json',manifest);return manifest
