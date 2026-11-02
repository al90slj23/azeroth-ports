#!/usr/bin/env python3
"""Source-bound138 entry baseline for139 migration;0 target executions.

The fourteen stages are anchored to the actual138 App880 call window plus
previously independently guarded138 roles. Other combat/network bindings use
their actual callers, signatures and body fields, never same-number inference.
"""
from datetime import datetime,timezone
from pathlib import Path
import ast,hashlib,json,sqlite3
from map_core135_to136 import load
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261101T201508.341687Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c60161d991ce97a9a4a9d3866b5e629d9e38f0fab8364c051faae8d01945b11b'
PROFILE=ROOT/'evidence/wasm0138-profile-20261101T202038.814151Z'
STAGES=(('player',2086),('extra',917),('owned_effects',973),('hits',1754),
 ('area',3756),('effects',915),('deadline',38039),('secondary',2596),
 ('ai',919),('collect',2862),('claims',2567),('spawn',946),('special',2359),('terminal',49086))
EXTRA=(('application_tick',880),('constructor',1571),('cached_world_construct',6760),
 ('opening',1087),('stats',1512),('owned_tick',1232),('cast',916),('player_aura',1155),
 ('select_ability',1072),('outgoing_damage',913),('incoming_damage',1057),
 ('proc_event',980),('fatal_transition',5613),('network_decode',965),
 ('player_motion',2327),('network_peer_route_helper',2077))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
 before=sha(Path(__file__));model=load(SOURCE,SOURCE_SHA,175576)
 manifest=json.loads((PROFILE/'manifest.json').read_text());assert manifest['original_sha256']==SOURCE_SHA and manifest['identities_preserved']
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('engine139-baseline138-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row
 records={};texts={};read_bytes=0
 with(PROFILE/'official-0.138.0-full.wat').open('rb')as stream:
  for role,index in STAGES+EXTRA:
   if index in records:continue
   row=dict(db.execute('select * from functions where idx=?',(index,)).fetchone());size=row['wat_end']-row['wat_start'];assert size<=6000000 and read_bytes+size<=18000000
   stream.seek(row['wat_start']);wat=stream.read(size);assert wat.startswith(f'  (func (;{index};)'.encode());read_bytes+=size
   assert model['ranges'][index]==(row['body_start'],row['body_end'],row['body_bytes'])
   signature=model['signatures'][index];texts[index]=wat.decode().splitlines();(out/f'138-{index}.wat').write_bytes(wat)
   records[index]=dict(index=index,params_hex=signature[0].hex(),results_hex=signature[1].hex(),body_sha256=model['hashes'][index],wat_sha256=hashlib.sha256(wat).hexdigest(),**row,
    direct_calls=[dict(value)for value in db.execute('select callee,wat_line,wat_offset from calls where caller=? order by wat_offset',(index,))])
 main_lines=texts[880];window=main_lines[49831:49870]
 actual=[int(line.strip().split()[1])for line in window if line.strip().startswith('call ')]
 assert actual==[index for _,index in STAGES]
 assert any('offset=2579'in line for line in window)
 assert records[1057]['params_hex']=='7f7d7e7f7f7f' and records[1057]['results_hex']==''
 assert 1057 in [row['callee']for row in records[919]['direct_calls']]
 assert 5613 in [row['callee']for row in records[1057]['direct_calls']]
 assert 980 in [row['callee']for row in records[1057]['direct_calls']]
 assert all(term in'\n'.join(texts[1057])for term in('f32.store offset=1440','i32.const 968','f64.store offset=992'))
 assert {2327,2077}<=set(row['callee']for row in records[965]['direct_calls'])
 assert records[2327]['params_hex']=='7f7f7d' and records[2327]['results_hex']=='7f'
 #Pin the existing13 semantic-role guards without importing production code.
 guarded={}
 for filename in('flow138_contract.py','flow138_consumers_contract.py'):
  tree=ast.parse((ROOT/'reconstruction/core_spec'/filename).read_text())
  for node in tree.body:
   if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='ROLES'for t in node.targets):guarded.update(ast.literal_eval(node.value))
 for role,(index,params,results,digest)in guarded.items():
  assert model['hashes'][index]==digest and tuple(x.hex()for x in model['signatures'][index])==(params,results)
 entries=[]
 for role,index in STAGES+EXTRA:
  status='actual14stage_App880_callwindow'if(role,index)in STAGES else'previous138_role_guard'if role in guarded else'actual_caller_signature_and_field_anchor'
  entries.append(dict(role=role,baseline_version='0.138.0',binding=records[index],identity_anchor=status,
   new139_index=None,new139_acceptance=False))
 result=dict(kind='source_bound138_baseline_for139_static_incremental_map',version='0.138.0',build='382771e6c',source=str(SOURCE.relative_to(ROOT)),source_sha256=SOURCE_SHA,
  source_bytes=len(model['raw']),defined_functions=175576,function_imports=878,profile=str(PROFILE.relative_to(ROOT)),profile_manifest_sha256=sha(PROFILE/'manifest.json'),entries=entries,
  app14window=dict(function=880,relative_first_line=49832,relative_last_line=49870,calls=actual,lines=[dict(line=j+49832,instruction=line.strip())for j,line in enumerate(window)]),
  script_sha256=before,wat_seek_bytes=read_bytes,full_WAT_scanned=False,original_executions=0,model_executions=0,old_acceptance_transferred=False,
  limitations=['This binds138 source locations only;no139 functions inferred fromsameindex','network_peer_route_helper is a caller-boundhelper,not a claimthatallpeerstate semantics are restored','Mapping acceptance anddata comparison requirefrozen139 source/profile','The14stage window is one explicitApp branch,not completeApp880 orallUI/network/rendering behavior'])
 path=out/'baseline.json';path.write_text(json.dumps(result,indent=2)+'\n');assert sha(Path(__file__))==before
 print(json.dumps(dict(directory=str(out),baseline_sha256=sha(path),entries=len(entries),wat_seek_bytes=read_bytes,original_executions=0)))
if __name__=='__main__':main()
