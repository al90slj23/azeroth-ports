#!/usr/bin/env python3
"""Private unmodified135922/1072/4600 exports and actual live32 provenance."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,sqlite3,subprocess,time
from wasm135_profile import ROOT,SOURCE,SOURCE_SHA,Reader,binary_identity,tool_identity
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ADDED=(('research135_live_cast922',0,922),('research135_live_select1072',0,1072),('research135_live_resume4600',0,4600),('research135_live_stack0',3,0))
def sha(p):
 with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def leb(n):
 b=bytearray()
 while True:
  x=n&127;n>>=7;b.append(x|(128 if n else 0))
  if not n:return bytes(b)
def exports(raw,sec):
 r=Reader(raw,sec['payload_start'],sec['end']);n=r.uint();start=r.pos;rows=[(r.name(),r.byte(),r.uint())for _ in range(n)];r.finish();return rows,start

def build(out):
 raw=SOURCE.read_bytes();assert len(raw)==90959080 and hashlib.sha256(raw).hexdigest()==SOURCE_SHA;identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section'];sec=next(x for x in sections if x['kind']==7);prior,start=exports(raw,sec);assert('__wbindgen_malloc',0,91941)in prior
 extra=b''
 for name,kind,idx in ADDED:n=name.encode();extra+=leb(len(n))+n+bytes((kind,))+leb(idx)
 payload=leb(len(prior)+len(ADDED))+raw[start:sec['end']]+extra;changed=raw[:sec['start']]+b'\7'+leb(len(payload))+payload+raw[sec['end']:];after,_=binary_identity(changed)
 assert[k['kind']for k in sections]==[k['kind']for k in after['sections']]
 for a,b in zip(sections,after['sections']):
  if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
 assert exports(changed,next(x for x in after['sections']if x['kind']==7))[0]==prior+list(ADDED)
 module=out/'live-owner135-original-exports.wasm';module.write_bytes(changed);functions=[]
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
  db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
  for idx in(922,1072,4600,65320,1073,2088):
   row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());assert ranges[idx][:2]==(row['body_start'],row['body_end'])and row['wat_end']-row['wat_start']<524288;stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);(out/f'{idx}.wat').write_bytes(text);functions.append(dict(row,signature=text.splitlines()[0].decode(),body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest(),WAT_sha256=hashlib.sha256(text).hexdigest()))
 tools=tool_identity();validator=Path(tools['tools']['wasm-validate']['path']);began=time.monotonic()
 with(out/'validation.stdout').open('wb')as stdout,(out/'validation.stderr').open('wb')as stderr:
  p=subprocess.Popen([str(validator),'--enable-all',str(module)],stdout=stdout,stderr=stderr,start_new_session=True)
  try:p.wait(timeout=45)
  finally:
   if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
 def missing(group=False):
  try:(os.killpg if group else os.kill)(p.pid,0)
  except ProcessLookupError:return True
  return False
 terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,deadline_seconds=45);save(out/'validator-owned.json',terminal);assert p.returncode==0 and terminal['pid_missing']and terminal['pgid_missing']
 m=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,original_bytes=len(raw),module_file=module.name,module_sha256=sha(module),added_exports=ADDED,only_changed_section=7,implicit_start=False,original_exports=prior,allocator_index=91941,denied_imports=878,memory_cap_bytes=33554432,stack_initial=1048576,functions=functions,validator=terminal,live_header=dict(capacity=1704,pointer=1708,count=1712,stride=32),Windows_executed=False,original_executed_by_builder=False)
 save(out/'manifest.json',m);return m
