#!/usr/bin/env python3
"""Private full1395719 export; no original callee changes."""
import hashlib,json,os,signal,subprocess,time
from pathlib import Path
from build_combat139_oracle import ROOT,SOURCE,SOURCE_SHA,Reader,binary_identity,sha,save,unsigned,export_entries,tool_identity
BODY_SHA='8035b0969dab682144a748cb3b535602f50600763e83dadfcb4e62d45d3e3ed5'
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def build(out):
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section'];a,b,_=ranges[5719];assert hashlib.sha256(raw[a:b]).hexdigest()==BODY_SHA
 sec=next(s for s in sections if s['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
 for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
 sec=next(s for s in sections if s['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())];assert decl[5719-882]==2 and types[2]==('7f7f7f7f','')
 sec=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,sec);added=[('research139_spawn5719',0,5719),('research139_spawn_stack0',3,0)];extra=b''
 for name,kind,index in added:n=name.encode();extra+=unsigned(len(n))+n+bytes([kind])+unsigned(index)
 payload=unsigned(len(prior)+2)+raw[start:sec['end']]+extra;changed=raw[:sec['start']]+b'\7'+unsigned(len(payload))+payload+raw[sec['end']:];after,_=binary_identity(changed)
 for a,b in zip(sections,after['sections']):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
 module=out/'npc-spawn139-original.wasm';module.write_bytes(changed);v=Path(tool_identity()['tools']['wasm-validate']['path']);began=time.monotonic()
 with(out/'validation.stdout').open('wb')as so,(out/'validation.stderr').open('wb')as se:
  p=subprocess.Popen([str(v),'--enable-all',str(module)],stdout=so,stderr=se,start_new_session=True)
  try:p.wait(timeout=45)
  finally:
   if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True),seconds=time.monotonic()-began);assert p.returncode==0 and terminal['pid_missing']and terminal['pgid_missing'];save(out/'validator-terminal.json',terminal)
 m=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=module.name,module_sha256=sha(module),entry_index=5719,type_index=2,body_sha256=BODY_SHA,only_changed_section=7,added_exports=added,original_imports=identity['imports'],imports_denied=882,validator=terminal)
 save(out/'manifest.json',m);return m
