#!/usr/bin/env python3
"""Author post-capture readback; zero model/original execution,not independentreview."""
from pathlib import Path
import ast,hashlib,json,struct
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'evidence/death139-oracle-20261102T052717.430579Z'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def u(raw,o):return struct.unpack_from('<I',raw,o)[0]
def save(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
comp=json.loads((P/'comparison.json').read_text());expected=json.loads((P/'expected.json').read_text());actual=[json.loads(x)for x in(P/'stdout.jsonl').read_text().splitlines()]
assert comp['source_before']==comp['source_after']
for name,h in comp['source_before'].items():assert sha(ROOT/name)==h==sha(P/'source-snapshot'/name)
for name,h in comp['artifacts'].items():assert sha(P/name)==h
m=json.loads((P/'manifest.json').read_text());tree=ast.parse((ROOT/'reconstruction/core_spec/death139.py').read_text());decl=next(x for x in tree.body if isinstance(x,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='DEFAULT72_139'for t in x.targets));literal=bytes.fromhex(decl.value.args[0].value)
assert literal.hex()==m['ordinary72_hex']and len(literal)==72 and u(literal,56)==1 and u(literal,60)==0x3f800000 and literal[68]==0
known=unknown=unknown_nonzero=0;unchanged_unknown432=unchanged_unknown56=0;sourcewords=0;deaths=xp_events=coin_events=0;packetbytes=0
for e,a in zip(expected,actual,strict=True):
 assert e['id']==a['id']and len(e['natural_producer_expected'])==len(a['answers'])==4
 for ep,ob in zip(e['natural_producer_expected'],a['answers'],strict=True):
  for key in(set(ep)|set(ob))-{'records432_cells','records432_hex'}:assert ep.get(key)==ob.get(key),(e['id'],key)
  for row,hx in zip(ep['records432_cells'],ob['records432_hex'],strict=True):
   raw=bytes.fromhex(hx);assert len(row)==len(raw)==432
   for j,v in enumerate(row):
    if v is None:unknown+=1;unknown_nonzero+=raw[j]!=0
    else:known+=1;assert v==raw[j]
 previousNPC=[bytes.fromhex(x)for x in a['answers'][-1]['records432_hex']];previousPickup=[]
 for stage,(ep,ob,game,diag)in enumerate(zip(e['expected'],a['cast_stages'],a['cast_raw_games'],e['model_diagnostic'],strict=True)):
  pre=bytes.fromhex(game['before_hex']);post=bytes.fromhex(game['after_hex']);assert len(pre)==len(post)==2592
  for off in(176,600,648,1972,1984,2032,2044,2056):assert u(pre,off)==u(post,off)==0;sourcewords+=2
  assert pre[770]==post[770]==0 and pre[908]&1==post[908]&1==0 and u(pre,1664)==u(post,1664)==1
  assert u(pre,1440)==u(pre,1536)==u(post,1440)==u(post,1536)
  for i,(row,hx)in enumerate(zip(ep['records432_cells'],ob['records432_hex'],strict=True)):
   raw=bytes.fromhex(hx)
   for j,v in enumerate(row):
    if v is None:assert raw[j]==previousNPC[i][j];unchanged_unknown432+=1
   previousNPC[i]=raw
  currentPickup=[bytes.fromhex(x)for x in ob['pickups56_hex']]
  for i,row in enumerate(ep['pickups56_cells']):
   if i>=len(previousPickup):continue
   for j,v in enumerate(row):
    if v is None:assert currentPickup[i][j]==previousPickup[i][j];unchanged_unknown56+=1
  previousPickup=currentPickup
  for hit in diag['hits']:
   deaths+=hit['dead']
   for event in hit['reward_events']:
    xp_events+=event[0]=='XP';coin_events+=event[0]=='currency'
  packetbytes+=sum(len(packet[1])//2 for packet in ep['known_packets'])
result=dict(kind='author_postcapture_readback_not_independentreview',script_sha256=sha(__file__),formal_comparison_sha256=sha(P/'comparison.json'),current_model72_bound_to_actual139data=True,actual_producer_stages=56,producer_known432_bytes=known,producer_unknown432_bytes=unknown,producer_unknown_nonzero_observation=unknown_nonzero,all_original_producer_outputs_match_stored_expectations=True,persistent_unknown432_bytes_unchanged=unchanged_unknown432,persistent_unknown56_bytes_unchanged=unchanged_unknown56,empty_source_raw_words_validated=sourcewords,source_zeros_not_written_by_this_reader=True,source_fields_are_explicit_component_contract_not_full_producer_recovery=True,accepted_deaths=deaths,XP_events=xp_events,currency_events=coin_events,known_packet_bytes=packetbytes,new_original_calls=0,new_model_calls=0,complete_packet_stream=False)
save(P/'postcapture-readback.json',result);print(json.dumps(dict(path=str(P/'postcapture-readback.json'),sha256=sha(P/'postcapture-readback.json'),result=result)))
