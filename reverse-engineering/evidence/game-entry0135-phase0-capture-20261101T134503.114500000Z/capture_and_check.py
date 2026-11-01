#!/usr/bin/env python3
"""Read fixed real phase0 snapshot with fixed reader CLI; never execute original."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
INPUT=ROOT/'evidence/game-entry0135-probe-20261101T134058.996329Z'
SOURCE=ROOT/'scripts/game_entry135_capture.py'
SOURCE_SHA='a71c5f71a7d92d2e4a3b73f767c4618d8774b9ff827bb70856aff3049c48bfc0'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb')as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()
before=sha(SOURCE);assert before==SOURCE_SHA
receipt_path=INPUT/'receipt.json';receipt_sha=sha(receipt_path)
receipt=json.loads(receipt_path.read_text());runtime=receipt['runtime'];result=runtime['result']
snapshot=INPUT/'original_game.memory';expected=runtime['capture']
snapshot_sha=sha(snapshot);snapshot_bytes=snapshot.stat().st_size
assert snapshot_sha==expected['sha256']==result['capture']['sha256']
assert snapshot_bytes==expected['bytes']==expected['total']==718995456
assert expected['complete']and result['capture']['complete']
header=result['contexts'][0]['final'];assert header['App']==22624720 and header['game']['phase']==0
assert header['memory_bytes']==snapshot_bytes and result['final_header_from_same_frozen_copy']
assert result['capture_synchronously_copied_unshared_memory']
output=OUT/'capture.json';stdout=OUT/'cli.stdout';stderr=OUT/'cli.stderr'
assert not any(p.exists()for p in(output,stdout,stderr,OUT/'summary.json'))
command=[sys.executable,'-B',str(SOURCE),'--snapshot',str(snapshot),'--app','22624720','--output',str(output)]
started=time.monotonic()
with stdout.open('xb')as so,stderr.open('xb')as se:
 process=subprocess.run(command,stdout=so,stderr=se,timeout=90)
elapsed=time.monotonic()-started
summary=dict(kind='real_coherent_phase0_snapshot_reader_check_not_running_game_acceptance',
 command=command,exit_code=process.returncode,elapsed_seconds=elapsed,
 input_receipt_path=str(receipt_path),input_receipt_sha256=receipt_sha,
 snapshot_path=str(snapshot),snapshot_bytes=snapshot_bytes,snapshot_sha256=snapshot_sha,
 snapshot_identity_matches_receipt=True,source_sha256_before=before,source_sha256_after=sha(SOURCE),
 source_unchanged=sha(SOURCE)==before,original_functions_executed_by_this_check=0,
 new_original_cases=0,new_independent_frames=0,
 producer_receipt_status=receipt['status'],producer_running_returns=result['running_complete880_returns'],
 producer_complete880_returns=result['confirmed_complete880_returns'],
 producer_same_frozen_header=header,
 producer_asset_file_budget_failure_is_not_repaired_here=True,
 producer_renderer_boundary_is_not_repaired_here=True)
if process.returncode==0:
 c=json.loads(output.read_text())
 assert c['input_snapshot_sha256']==snapshot_sha and c['input_snapshot_path']==str(snapshot)
 assert c['App']==header['App']and c['game_tag_u64']==header['game_tag_u64']
 assert c['scalar_words']['world_rc2348']==header['game']['world_rc']
 assert c['flags']['phase2587']==header['game']['phase']
 assert c['scalar_words']['clock2352_bits']==header['game']['clock_bits']
 def vector(v):return {k:v[k]for k in('status','error','capacity','pointer','count','stride','head','capacity_semantics')if k in v}
 def grid(v):
  info=vector(v)
  for k in('present','tag56','origin_xy_bits_width','capacity_unrestored','sentinel'):
   if k in v:info[k]=v[k]
  for k in('raw_f32_values_hex','raw_backing_hex'):
   if k in v:info[k+'_bytes']=len(v[k])//2
  return info
 world=c.get('world',{});body=world.get('partial_observations',world)
 world_summary={k:world[k]for k in('status','error')if k in world}
 world_summary.update({k:body[k]for k in('pointer','app_cache_pointer','strong_observed','weak_observed','fallback_bits','flat_byte')if k in body})
 for k in('tiles36','bounds16'):
  if k in body:world_summary[k]=vector(body[k])
 for k in('nav','primary','secondary'):
  if k in body:world_summary[k]=grid(body[k])
 tiles=body.get('terrain_chunks',[])
 world_summary['terrain_tiles_observed']=len(tiles)
 world_summary['terrain_chunk_capacities']=[v['capacity']for v in tiles]
 world_summary['terrain_chunk_counts']=[v['count']for v in tiles]
 chunks=[chunk for tile in tiles for chunk in tile['active']]
 world_summary['terrain_active_chunks_observed']=len(chunks)
 world_summary['terrain_vertex_counts_distinct']=sorted({chunk['vertex_count']for chunk in chunks})
 world_summary['terrain_vertex_capacities_distinct']=sorted({chunk['vertex_capacity']for chunk in chunks})
 transport=c.get('transport',{});transport_summary={k:transport[k]for k in('status','error','holder_pointer','vtable','cell_pointer','optional_snapshot_and_rows_metadata_only')if k in transport}
 if 'ring'in transport:
  transport_summary['ring']=vector(transport['ring'])
  transport_summary['ring']['payload_count']=len(transport['ring']['logical_payloads'])
 if 'commands232'in transport:transport_summary['commands232']=vector(transport['commands232'])
 tree=c.get('player_keyed_tree',{})
 tree_summary={k:tree[k]for k in('status','error','root','depth','modeled_keys')if k in tree}
 if 'nodes'in tree:tree_summary['node_count']=len(tree['nodes'])
 if 'ordered_items'in tree:tree_summary['key_count']=len(tree['ordered_items'])
 if 'unmodeled_keys'in tree:tree_summary['unmodeled_key_ids']=list(tree['unmodeled_keys'])
 scalars=c['scalar_words'];flags=c['flags']
 summary.update(capture_path=str(output),capture_sha256=sha(output),capture_json_bytes=output.stat().st_size,
  capture_status=c['status'],capture_complete_for_declared_schema=c['capture_complete_for_declared_schema'],
  capture_boundaries=c['boundaries'],reader_copied_source_bytes=c['source_bytes_copied_with_duplicates'],
  running_gate=c['running_gate'],player=dict(
   class_byte=flags['class360'],race_byte=flags['race361'],source_guid_u64=c['source_guid_u64'],
   xyz_bits=[scalars[k]for k in('player_x_bits','player_y_bits','player_z_bits')],
   xyz=[struct.unpack('<f',struct.pack('<I',scalars[k]))[0]for k in('player_x_bits','player_y_bits','player_z_bits')],
   level=scalars['level1432'],xp=scalars['xp1436'],hp_bits=scalars['hp1440_bits'],gold=scalars['gold1456'],
   rng_words=c['rng_words'],keyed_tree=tree_summary),
  vectors={name:vector(value)for name,value in c['vectors'].items()},world=world_summary,
  transport=transport_summary,ability_definitions=[{k:v for k,v in row.items()if k in('status','error','definition_pointer','ability_id_hex','execution_kind')}for row in c['ability_definitions']],
  actual_running_game_validated=False)
assert sha(SOURCE)==SOURCE_SHA and sha(receipt_path)==receipt_sha
(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'summary':str(OUT/'summary.json'),'summary_sha256':sha(OUT/'summary.json'),
 'capture_complete_for_declared_schema':summary.get('capture_complete_for_declared_schema'),
 'capture_boundaries':summary.get('capture_boundaries'),'world':summary.get('world'),
 'player':summary.get('player'),'transport':summary.get('transport')},indent=2))
