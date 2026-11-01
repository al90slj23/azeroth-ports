#!/usr/bin/env python3
"""Targeted snapshot-owner regression; synthetic 128KiB input, no game calls."""
from pathlib import Path
import argparse,hashlib,json,struct,subprocess,sys
from datetime import datetime,timezone
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
OUT=(a.output or ROOT/'evidence'/datetime.now(timezone.utc).strftime('game-entry0135-reader-check-%Y%m%dT%H%M%S.%fZ')).resolve()
if not OUT.is_relative_to(Path('/Volumes/RuiRui4TB').resolve()):raise ValueError('4T research output required')
OUT.mkdir(parents=True,exist_ok=False)
sys.path.insert(0,str(ROOT/'scripts'))
import game_entry135_capture as reader
FILES=('scripts/check_game_entry135_capture.py','scripts/game_entry135_capture.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
before={p:sha(ROOT/p)for p in FILES}
A=256;G=A+16;b=bytearray(131072)
def u(p,x):struct.pack_into('<I',b,p,x)
u(G+1256,16384);u(16384+12,16640);u(16384+16,3);b[16640:16643]=b'abc'
u(A+4768,20480);u(A+4772,1495776);u(20480+16,20736)
u(G+2348,24576)
for offset in(32,56,92):u(24576+offset,0xffffffff)
b[24576+120]=1;u(G+2352,0x3f800000);b[G+2587]=1
raw=bytes(b);expected=reader.capture_game_entry135(raw,A)
assert expected['capture_complete_for_declared_schema']
checks={'immutable_bytes_accepted':True}
for label,view in(
 ('byte_view',memoryview(raw)),('signed_byte_view',memoryview(raw).cast('b')),
 ('char_view',memoryview(raw).cast('c')),('nested_view',memoryview(memoryview(raw))),
 ('contiguous_byte_slice',memoryview(raw)[:])):
 assert reader.capture_game_entry135(view,A)==expected,label
 checks[label+'_same_projection']=True
def reject(label,value):
 try:reader.capture_game_entry135(value,A)
 except TypeError as exc:checks[label]=str(exc)
 else:raise AssertionError(label+' accepted')
reject('bytearray_rejected',b)
reject('writable_view_rejected',memoryview(b))
reject('readonly_mutable_owner_rejected',memoryview(b).toreadonly())
reject('nested_readonly_mutable_owner_rejected',memoryview(memoryview(b).toreadonly()))
reject('readonly_noncontiguous_bytes_view_rejected',memoryview(raw)[::2])
reject('readonly_nonbyte_view_rejected',memoryview(raw).cast('I'))
# The prior counterexample mutated the owner on the first hashing operation.
# Rejection now happens before that operation and before any projection.
real_hash=hashlib.sha256;events=[]
def scheduled_hash(data=b'',*args,**kwargs):
 if not events:u(G+2352,0x40000000);events.append('owner_mutated')
 return real_hash(data,*args,**kwargs)
try:
 reader.hashlib.sha256=scheduled_hash
 reject('scheduled_prior_counterexample_rejected',memoryview(b).toreadonly())
finally:reader.hashlib.sha256=real_hash
assert not events and bytes(b)==raw
checks['prior_alias_counterexample_rejected_before_any_hash_or_owner_mutation']=True
snapshot=OUT/'tiny-synthetic.memory';snapshot.write_bytes(raw)
cli_path=OUT/'tiny-synthetic-cli-capture.json'
process=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/game_entry135_capture.py'),
 '--snapshot',str(snapshot),'--app',str(A),'--output',str(cli_path)],capture_output=True,timeout=15)
assert process.returncode==0,process.stderr.decode()
cli=json.loads(cli_path.read_text())
assert cli['capture_complete_for_declared_schema']
assert cli['input_snapshot_sha256']==sha(snapshot)
assert cli['scalar_words']['clock2352_bits']==cli['running_gate']['clock2352_bits']==0x3f800000
checks['cli_path_read_bytes_compatible']=True
schema_path=OUT/'schema.json';schema_path.write_text(json.dumps(reader.capture_schema135(),indent=2)+'\n')
after={p:sha(ROOT/p)for p in FILES};assert before==after
report=dict(kind='immutable_owner_regression_synthetic_only',checks=checks,
 checker_sha256=sha(__file__),
 source_sha256_before=before,source_sha256_after=after,sources_unchanged_during_check=True,
 schema_sha256=sha(schema_path),synthetic_bytes=len(raw),synthetic_snapshot_sha256=sha(snapshot),
 prior_counterexample_evidence='game-entry0135-independent-review-20261101T132657.322250000Z/review-checks.json',
 original_calls=0,original_cases=0,independent_game_frames=0,actual_active_game_snapshot_validated=False)
report_path=OUT/'regression-checks.json';report_path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'evidence':str(OUT),'regression_sha256':sha(report_path),
 'schema_sha256':sha(schema_path),'capture_source_sha256':sha(ROOT/'scripts/game_entry135_capture.py'),
 'checks':checks},indent=2))
