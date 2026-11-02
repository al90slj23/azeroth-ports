#!/usr/bin/env python3
"""Fresh1391600→full5719 exports, original functions/callees unchanged."""
import hashlib,os,signal,subprocess,time
from pathlib import Path
from build_npc_spawn139_oracle import ROOT,SOURCE,SOURCE_SHA,build as base_build,sha,save,missing,binary_identity,export_entries,unsigned,tool_identity

def build(out):
 m=base_build(out);original=SOURCE.read_bytes();identity,ranges=binary_identity(original);a,b,_=ranges[1600];assert hashlib.sha256(original[a:b]).hexdigest()=='17f2335fc31fe91be1509ffcabe89e56662b61cc2c684f862c54c681eb69b8b1'
 raw=(out/m['module_file']).read_bytes();identity,_=binary_identity(raw);ex=next(s for s in identity['sections']if s['kind']==7);prior,start=export_entries(raw,ex);name=b'research139_spawn_constructor1600';payload=unsigned(len(prior)+1)+raw[start:ex['end']]+unsigned(len(name))+name+b'\0'+unsigned(1600)
 changed=raw[:ex['start']]+b'\7'+unsigned(len(payload))+payload+raw[ex['end']:];after,_=binary_identity(changed);before,_=binary_identity(original)
 for x,y in zip(before['sections'],after['sections']):
  assert x['kind']==y['kind']
  if x['kind']!=7:assert original[x['start']:x['end']]==changed[y['start']:y['end']]
 module=out/'npc-spawn139-fresh-original.wasm';module.write_bytes(changed);v=Path(tool_identity()['tools']['wasm-validate']['path']);began=time.monotonic()
 with(out/'fresh-validation.stdout').open('wb')as so,(out/'fresh-validation.stderr').open('wb')as se:
  p=subprocess.Popen([str(v),'--enable-all',str(module)],stdout=so,stderr=se,start_new_session=True)
  try:p.wait(timeout=45)
  finally:
   if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True),seconds=time.monotonic()-began);assert p.returncode==0 and terminal['pid_missing']and terminal['pgid_missing'];save(out/'fresh-validator-terminal.json',terminal)
 m.update(module_file=module.name,module_sha256=sha(module),constructor1600_body_sha256=hashlib.sha256(original[a:b]).hexdigest(),constructor1600_added_export=name.decode(),fresh_validator=terminal,original_exports_extended_again_only_section7=True)
 save(out/'manifest.json',m);return m
