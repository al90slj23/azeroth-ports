#!/usr/bin/env python3
"""Private fixed135 full947 export plus read-only stack; no body mutation."""
from pathlib import Path
import hashlib,json,os,signal,subprocess
from build_full135_oracle import ROOT,build,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import unsigned

def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def build_event_wave135():
 out,manifest=build(['spawn_tick']);path=out/manifest['module_file'];raw=path.read_bytes();s=next(x for x in section_list(raw)if x[0]==7);items,start=export_entries(raw,s);name=b'research135_event_stack0';payload=unsigned(len(items)+1)+raw[start:s[3]]+unsigned(len(name))+name+b'\x03'+unsigned(0);changed=raw[:s[1]]+b'\x07'+unsigned(len(payload))+payload+raw[s[3]:]
 for a,b in zip(section_list(raw),section_list(changed)):
  assert a[0]==b[0]
  if a[0]!=7:assert raw[a[1]:a[3]]==changed[b[1]:b[3]]
 path.write_bytes(changed);validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
 child=subprocess.Popen([str(validator),'--enable-all',str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True);(out/'event-validator-owned.json').write_text(json.dumps(dict(pid=child.pid,pgid=child.pid,deadline_seconds=45))+'\n')
 try:stdout,stderr=child.communicate(timeout=45)
 finally:
  try:os.killpg(child.pid,signal.SIGKILL)
  except ProcessLookupError:pass
  child.wait()
 (out/'event-validation.stdout').write_bytes(stdout);(out/'event-validation.stderr').write_bytes(stderr);assert child.returncode==0
 manifest.update(module_sha256=sha(path),private_stack_export=dict(name=name.decode(),index=0),all_callee_bodies_unchanged=True,context_memory_page_cap=4096);(out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');return out,manifest
