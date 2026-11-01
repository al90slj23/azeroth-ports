#!/usr/bin/env python3
"""Static source/read-set arithmetic only. No model/original module imported."""
from pathlib import Path
import ast,hashlib,json
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
FILES=tuple('reconstruction/core_spec/'+name+'.py'for name in(
 'headless135','unit_records135','opening_npc_pickups135','spawn135','combat135',
 'combat134','cast135','cast_events135','area_effects135','ai135','ai_lifecycle135',
 'ordinary_placement135','effect_system135','movement_pause135'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before={p:sha(ROOT/p)for p in FILES}
def literal_assignment(file,name):
 tree=ast.parse((ROOT/file).read_text())
 for node in tree.body:
  if isinstance(node,ast.Assign)and any(isinstance(t,ast.Name)and t.id==name for t in node.targets):
   return ast.literal_eval(node.value)
 raise AssertionError(name)
ranges=literal_assignment('reconstruction/core_spec/opening_npc_pickups135.py','NPC_WRITTEN_RANGES')
known={i for start,size in ranges for i in range(start,start+size)}
unknown=set(range(424))-known
assert len(unknown)==129
reads=[dict(field=k,offset=v,width=4,source='unit_records135.decode_unit/FLOAT_FIELDS')for k,v in
 literal_assignment('reconstruction/core_spec/unit_records135.py','FLOAT_FIELDS').items()]
reads.extend(dict(field=k,offset=o,width=n,source='unit_records135.decode_unit')for k,o,n in(
 ('target_id',112,8),('linked_id_32',32,8),('marker',0,4),('kind_40',40,4),
 ('kind_64',64,4),('elite_244',244,4),('elite_416',416,1),('afflicted_240',240,4)))
reads.extend(dict(field=k,offset=o,width=n,source='unit_records135.decode_spatial')for k,o,n in(
 ('from_xy',316,8),('to_xy',328,8),('priority_until372_bits',372,4)))
read_bytes=set()
for row in reads:
 span=set(range(row['offset'],row['offset']+row['width']));read_bytes|=span
 row['constructor_unwritten_offsets']=sorted(span&unknown)
 row['constructor_fully_written']=not bool(span&unknown)
assert read_bytes&unknown==set(range(4,8))|set(range(32,40))
def spans(values):
 result=[]
 for value in sorted(values):
  if result and result[-1][0]+result[-1][1]==value:result[-1][1]+=1
  else:result.append([value,1])
 return result
symbols={}
for file in FILES:
 tree=ast.parse((ROOT/file).read_text())
 for node in tree.body:
  if isinstance(node,(ast.FunctionDef,ast.ClassDef)):
   symbols[file+':'+node.name]=dict(start=node.lineno,end=node.end_lineno)
after={p:sha(ROOT/p)for p in FILES};assert before==after
report=dict(kind='static_current_model_npc424_readset_not_full_original880_liveness',
 constructor_written_ranges=ranges,constructor_unwritten_ranges=spans(unknown),
 constructor_unwritten_bytes=len(unknown),decoder_read_fields=reads,
 decoder_unwritten_intersection_ranges=spans(read_bytes&unknown),
 decoder_unwritten_intersection_bytes=len(read_bytes&unknown),
 unwritten_not_read_by_decoder_ranges=spans(unknown-read_bytes),
 unwritten_not_read_by_decoder_bytes=len(unknown-read_bytes),
 source_sha256_before=before,source_sha256_after=after,source_symbols=symbols,
 sources_unchanged=True,checker_sha256=sha(Path(__file__)),model_imports=0,
 original_calls=0,game_frames=0,snapshots_read=0)
path=OUT/'static-readset.json';path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'evidence':str(OUT),'readset_sha256':sha(path),
 'constructor_unwritten_ranges':report['constructor_unwritten_ranges'],
 'decoder_unwritten_intersection_ranges':report['decoder_unwritten_intersection_ranges'],
 'unwritten_not_read_by_decoder_bytes':report['unwritten_not_read_by_decoder_bytes']},indent=2))
