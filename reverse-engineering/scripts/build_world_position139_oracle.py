#!/usr/bin/env python3
"""Private full1398740/13563 original exports, healthyv2 context only."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
from build_combat139_oracle import ROOT,SOURCE,SOURCE_SHA,Reader,binary_identity,sha,save,unsigned,export_entries,tool_identity
ROLES={'spawn':(8740,'7f7f7d7d7d','35e2f8bf141c22a07857ff8327892bf7b6f971aea2d1ad0f705ba12dfa02af38'),
 'random':(13563,'7f7f7d7d','724158538ddf6fdcb38eb520beaa5ff8467952b418be3400132013b105a136ae')}
def missing(pid,group=False):
 try:(os.killpg if group else os.kill)(pid,0)
 except ProcessLookupError:return True
 return False
def build(out):
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
 sec=next(s for s in sections if s['kind']==6);assert raw[sec['payload_start']:sec['end']].hex()=='017f01418080c0000b'
 sec=next(s for s in sections if s['kind']==1);r=Reader(raw,sec['payload_start'],sec['end']);types=[]
 for _ in range(r.uint()):assert r.byte()==0x60;types.append((r.raw(r.uint()).hex(),r.raw(r.uint()).hex()))
 sec=next(s for s in sections if s['kind']==3);r=Reader(raw,sec['payload_start'],sec['end']);decl=[r.uint()for _ in range(r.uint())]
 ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex);extra=b'';added=[];roles=[]
 for role,(index,params,bodysha)in ROLES.items():
  a,b,_=ranges[index];assert hashlib.sha256(raw[a:b]).hexdigest()==bodysha and types[decl[index-882]]==(params,'')
  name='research139_position_'+role;n=name.encode();extra+=unsigned(len(n))+n+b'\0'+unsigned(index);added.append((name,0,index));roles.append(dict(role=role,index=index,body_sha256=bodysha,params_hex=params,type_index=decl[index-882],export=name))
 name='research139_position_stack0';n=name.encode();extra+=unsigned(len(n))+n+b'\3\0';added.append((name,3,0));payload=unsigned(len(prior)+len(added))+raw[start:ex['end']]+extra
 changed=raw[:ex['start']]+b'\7'+unsigned(len(payload))+payload+raw[ex['end']:];after,_=binary_identity(changed)
 for a,b in zip(sections,after['sections']):
  assert a['kind']==b['kind']
  if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
 assert export_entries(changed,next(s for s in after['sections']if s['kind']==7))[0]==prior+added
 module=out/'world-position139-original.wasm';module.write_bytes(changed);v=Path(tool_identity()['tools']['wasm-validate']['path']);began=time.monotonic()
 with(out/'validation.stdout').open('wb')as so,(out/'validation.stderr').open('wb')as se:
  p=subprocess.Popen([str(v),'--enable-all',str(module)],stdout=so,stderr=se,start_new_session=True)
  try:p.wait(timeout=45)
  finally:
   if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-began,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));assert p.returncode==0 and terminal['pid_missing']and terminal['pgid_missing'];save(out/'validator-terminal.json',terminal)
 manifest=dict(version='0.139.0',build='f79c5e2b4',source_sha256=SOURCE_SHA,module_file=module.name,module_sha256=sha(module),roles=roles,original_imports=identity['imports'],denied_imports=882,added_exports=added,only_changed_section=7,original_full_callees_preserved=True,validator=terminal)
 save(out/'manifest.json',manifest);return manifest
