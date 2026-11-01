#!/usr/bin/env python3
"""Independent frozen-model/action and two lossless-storage review; no WASM execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,gc,hashlib,json,re,struct,sys
from dataclasses import replace
sys.dont_write_bytecode=True
from review_gameplay_phase135 import ROOT,ORIGINAL,ORIGINAL_SHA,sha,strict,norm,sections,bodies,core_closure,load_checker,moving_guids,uint
DEFAULT='full0135-oracle-20261101T082927.606617Z'
ROLE_BINDINGS={'initial_game':(1560,'7f7f7f',''),'player_tick':(2088,'7f7d',''),'process_hits':(1754,'7f',''),'area_tick':(3757,'7f',''),'update_units':(921,'7f7d',''),'collect_pickups':(2862,'7f',''),'spawn_tick':(947,'7f7d',''),'select_ability':(1072,'7f7f',''),'effect_tick':(915,'7f7d',''),
 'auto_cast':(916,'7f7d',''),'owned_effect_tick':(975,'7f7d',''),'deadline_tick':(38007,'7f',''),'secondary_hits':(2602,'7f',''),
 'claim_tick':(2573,'7f',''),'special_tick':(2376,'7f',''),'terminal_tick':(49037,'7f','')}
INPUT_KEYS={'id','input','region_id','controlled_phase1','zeroed_unit_capacity','zeroed_area_capacity','actions'}
TAIL_KINDS=('extra','owned_effects','deadline','secondary','claims','special','terminal')
TAIL_ORDER=('player','extra','owned_effects','hits','area','effects','deadline','secondary','ai','collect','claims','spawn','special','terminal')


def compare(want,actual,path,counts):
 counts['nodes']+=1
 if want is None:
  assert re.search(r'\.pickup_words\[\d+\]\[1\]$|\.live_words\[\d+\]\[(3|4)\]$',path),path
  assert type(actual)is int and 0<=actual<=0xffffffff,path;counts['explicit_unwritten_words']+=1;return
 assert type(want)==type(actual),(path,type(want),type(actual))
 if isinstance(want,dict):
  assert want.keys()==actual.keys(),path
  for k in want:compare(want[k],actual[k],path+'.'+k,counts)
 elif isinstance(want,list):
  assert len(want)==len(actual),(path,len(want),len(actual))
  for i,(w,a)in enumerate(zip(want,actual)):compare(w,a,path+f'[{i}]',counts)
 else:assert want==actual,(path,want,actual)


def words_guard(p):
 for r in p['pickup_words']:
  if r[1]is None:assert r[0]==0 and r[2]in(0,1),r
 for r in p['live_words']:
  if r[3]is None:assert r[2]==12 and r[5]==1020,r
  if r[4]is None:assert r[2]in(7,8,9)or(r[2]==12 and r[5]==1020),r
 tag=p['game_tag'];assert type(tag)is str and str(int(tag))==tag and 0<=int(tag)<1<<64


def exports(raw,sec):
 n,p=uint(raw,sec[2]);out=[]
 for _ in range(n):
  size,p=uint(raw,p);name=raw[p:p+size].decode();p+=size;kind=raw[p];p+=1;index,p=uint(raw,p);out.append((name,kind,index))
 assert p==sec[3];return out


def signatures(raw,sec):
 n,p=uint(raw,next(s for s in sec if s[0]==1)[2]);types=[]
 for _ in range(n):
  assert raw[p]==0x60;p+=1;pn,p=uint(raw,p);ps=raw[p:p+pn].hex();p+=pn;rn,p=uint(raw,p);rs=raw[p:p+rn].hex();p+=rn;types.append((ps,rs))
 n,p=uint(raw,next(s for s in sec if s[0]==3)[2]);decl=[]
 for _ in range(n):t,p=uint(raw,p);decl.append(t)
 return lambda i:types[decl[i-878]]


def lossless(storage,delta,local,label):
 last=-1
 for index,value in delta:
  assert type(index)is int and last<index<len(storage)//4
  assert type(value)is int and 0<=value<=0xffffffff
  assert struct.unpack_from('<I',storage,index*4)[0]!=value,'Redundant '+label+' delta'
  struct.pack_into('<I',storage,index*4,value);last=index;local[label+'_delta_words']+=1


def records_by_guid(rows):return {struct.unpack_from('<Q',bytes.fromhex(r),112)[0]:bytes.fromhex(r)for r in rows}
def u(raw,o):return struct.unpack_from('<I',raw,o)[0]
def ff(bits):return struct.unpack('<f',struct.pack('<I',bits))[0]
def addbits(a,b):return struct.unpack('<I',struct.pack('<f',ff(a)+ff(b)))[0]


def verify_area_tick_storage(prior,old_count,now_bits,current,new_count,local):
 # Independent bytearray memmove mirrors3757 stable sequential removals,
 # including intermediate inactive tail copies, then only64/72 timer writes.
 b=bytearray(prior);count=old_count;index=0;expired=0
 while index<count:
  if ff(now_bits)>=ff(struct.unpack_from('<I',b,index*88+80)[0]):
   if index<count-1:
    b[index*88:(count-1)*88]=b[(index+1)*88:count*88];local['area_expiry_memmoves']+=1
   count-=1;expired+=1
  else:index+=1
 for j in range(count):
  p=j*88;remaining=struct.unpack_from('<I',b,p+72)[0];due=struct.unpack_from('<I',b,p+64)[0]
  if remaining and ff(due)<=ff(now_bits):
   interval=struct.unpack_from('<I',b,p+68)[0];struct.pack_into('<I',b,p+72,remaining-1);struct.pack_into('<I',b,p+64,addbits(due,interval));local['area_due_ticks']+=1
 assert count==new_count and b==current,'Independent full128 area compaction/tick mismatch'
 local['area_expirations']+=expired


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--batch',default=DEFAULT);parser.add_argument('--output');parser.add_argument('--preliminary',action='store_true');args=parser.parse_args()
 batch=Path(args.batch);batch=batch if batch.is_absolute()else ROOT/'evidence'/args.batch
 out=Path(args.output).resolve()if args.output else ROOT/'evidence'/datetime.now(timezone.utc).strftime('headless-tail0135-'+('preliminary-'if args.preliminary else'independent-review-')+'%Y%m%dT%H%M%S.%fZ');out.mkdir(parents=True,exist_ok=True)
 receipt_path=batch/'headless135-comparison.json';receipt=json.loads(receipt_path.read_text());frozen=receipt['source_sha256_before'];assert frozen==receipt['source_sha256_after'];snap=batch/'source-snapshot';drift={}
 for name,digest in frozen.items():
  assert sha(snap/name)==digest
  if sha(ROOT/name)!=digest:drift[name]=dict(frozen=digest,current=sha(ROOT/name))
 closure=core_closure(snap,('headless135.py',));assert set(closure)<=frozen.keys()
 for name,digest in receipt['artifacts'].items():assert sha(batch/name)==digest
 raw=ORIGINAL.read_bytes();assert hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA;ss=sections(raw);bb=bodies(raw,ss);signature=signatures(raw,ss)
 module=(batch/'research135-exports.wasm').read_bytes();ms=sections(module);assert [(k,x)for k,x,_,_ in ss if k!=7]==[(k,x)for k,x,_,_ in ms if k!=7];assert not any(k==8 for k,*_ in ss)
 manifest=json.loads((batch/'manifest.json').read_text());has_area=any(r['role']=='area_tick'for r in manifest['roles']);has_effects=any(r['role']=='effect_tick'for r in manifest['roles']);has_tail=any(r['role']=='deadline_tick'for r in manifest['roles']);roles=dict(ROLE_BINDINGS)
 if not has_tail:
  for k in('auto_cast','owned_effect_tick','deadline_tick','secondary_hits','claim_tick','special_tick','terminal_tick'):del roles[k]
 if not has_area:del roles['area_tick']
 if not has_effects:del roles['effect_tick']
 assert manifest['denied_function_import_count']==878 and {r['role']for r in manifest['roles']}==roles.keys()
 for r in manifest['roles']:
  i,params,results=roles[r['role']];assert(i,params,results)==(r['index'],r['parameters_hex'],r['results_hex']);assert signature(i)==(params,results)
  a,b=bb[i-878];assert(a,b)==(r['body_start'],r['body_end']);assert hashlib.sha256(raw[a:b]).hexdigest()==r['body_sha256']
 oldex=exports(raw,next(s for s in ss if s[0]==7));newex=exports(module,next(s for s in ms if s[0]==7));assert newex[:len(oldex)]==oldex;assert newex[len(oldex):]==[(r['export'],0,r['index'])for r in manifest['roles']]
 del raw,module,ss,ms,bb
 before={name:sha(snap/name)for name in frozen};author=load_checker(snap,'check_headless135.py','review_headless135_frozen_checker')
 with (batch/'headless135-fixtures.jsonl').open()as stream:first=json.loads(next(stream));budget=first.get('frame_budget',400)
 del first
 regenerated=author.corpus(False,frame_budget=budget);metadata=[]
 with (batch/'headless135-fixtures.jsonl').open()as stream:
  for expected_fixture in regenerated:
   fixture=json.loads(next(stream));assert strict(fixture,expected_fixture),'Fixed-policy corpus regeneration differs'
   metadata.append({k:v for k,v in fixture.items()if k!='expected'})
  assert not stream.read().strip()
 del regenerated,fixture,expected_fixture;gc.collect();budgets={f.get('frame_budget',250)for f in metadata};assert len(budgets)==1
 input_rows=[json.loads(x)for x in(batch/'headless135-inputs.jsonl').read_text().splitlines()]
 assert len(input_rows)==len(metadata)
 for inp,fixed in zip(input_rows,metadata):
  assert 'expected'not in inp
  if not args.preliminary:assert set(inp)==INPUT_KEYS
  assert strict({k:inp[k]for k in INPUT_KEYS},{k:fixed[k]for k in INPUT_KEYS})
 assert receipt['process']['command'][-1]==str(batch/'headless135-inputs.jsonl')
 runner=(snap/'scripts/run_headless135_oracle.mjs').read_text();assert '.expected'not in runner and 'headless135-fixtures'not in runner
 input_schema=dict(keys=sorted(input_rows[0]),strict_seven_field_whitelist=all(set(x)==INPUT_KEYS for x in input_rows),
  no_expected_projection_in_inputs=True,node_command_consumes_input_artifact_only=True,
  result_metadata_in_original_heap=any(set(x)-INPUT_KEYS for x in input_rows),preliminary_only=args.preliminary)
 if not args.preliminary:
  assert "const inputKeys = ['id','input','region_id','controlled_phase1','zeroed_unit_capacity','zeroed_area_capacity','actions'].sort();"in runner
  assert 'JSON.stringify(Object.keys(c).sort()) !== JSON.stringify(inputKeys)'in runner
  development=ROOT/'evidence/full0135-oracle-20261101T082530.697942Z';dev_receipt=json.loads((development/'headless135-comparison.json').read_text())
  changed_sources={k for k,v in frozen.items()if dev_receipt['source_sha256_before'][k]!=v}
  assert changed_sources=={'scripts/check_headless135.py','scripts/run_headless135_oracle.mjs'}
  artifact_identity={}
  for name in('headless135-fixtures.jsonl','headless135-results.jsonl','research135-exports.wasm'):
   assert sha(development/name)==sha(batch/name)
   artifact_identity[name]=dict(bytes=(batch/name).stat().st_size,sha256=sha(batch/name),byte_identical_to_development=True)
  input_schema.update(Node_asserts_exact_keys=True,development_receipt=str((development/'headless135-comparison.json').relative_to(ROOT)),
   development_receipt_sha256=sha(development/'headless135-comparison.json'),changed_source_names=sorted(changed_sources),
   expected_actual_module_unchanged=artifact_identity,development_metadata_leak_not_used_as_final_evidence=True)
 assert [x['id']for x in metadata]==list(range(8));assert[int(f['input']['seed_u64'])for f in metadata]==list(range(8))
 observed_stream=(batch/'headless135-results.jsonl').open();fixture_stream=(batch/'headless135-fixtures.jsonl').open()
 sidecar_mirrors={name:json.loads((batch/('headless135-unmodeled-'+name+'-fields.json')).read_text())for name in('player','effect','tail')}if has_tail else{}
 counts=Counter();cases=[];unknowns=[];unknown_effects=[];unknown_tail=[];expected_kinds=TAIL_ORDER if has_tail else(('player','hits','area','effects','ai','collect','spawn')if has_effects else(('player','hits','area','ai','collect','spawn')if has_area else('player','hits','ai','collect','spawn')))
 if has_effects:
  prior_batch=ROOT/'evidence'/('full0135-oracle-20261101T072329.149731Z'if has_tail else'full0135-oracle-20261101T064308.759593Z');prior_stream=(prior_batch/'headless135-fixtures.jsonl').open()
  prior_receipt=json.loads((prior_batch/'headless135-comparison.json').read_text());assert sha(prior_batch/'headless135-fixtures.jsonl')==prior_receipt['artifacts']['headless135-fixtures.jsonl']
 for meta in metadata:
  fixture=json.loads(next(fixture_stream));actual=json.loads(next(observed_stream));assert actual['id']==fixture['id']==meta['id']
  if has_effects:
   new,old=fixture,json.loads(next(prior_stream))
   assert strict({k:v for k,v in new.items()if k!='expected'},{k:v for k,v in old.items()if k!='expected'}),'Original8seedactions/boundaries changed'
   omitted_fields={'tail_state','timed916_count'}if has_tail else{'effect_state'};omitted_kinds=set(TAIL_KINDS)if has_tail else{'effects'}
   projected=[dict(kind=v['kind'],projection={k:x for k,x in v['projection'].items()if k not in omitted_fields})for v in new['expected']if v['kind']not in omitted_kinds];assert strict(projected,old['expected']),'Preexistingmodel expected changed'
   del old,projected,new
  inp=dict(fixture['input']);inp['seed_u64']=int(inp['seed_u64']);inp['object_id_u64']=int(inp['object_id_u64']);kw=dict(flat_height_bits=inp['flat_height_bits'],zeroed_unit_storage_resolved=True)
  if has_area:kw['zeroed_area_storage_resolved']=True
  state=author.resolve_controlled_entry(author.from_initial(author.initialize_empty_profile(author.ConstructorInput135(**inp)),**kw),phase1_entry_explicitly_resolved=True)
  storage=bytearray(128*424);area_storage=bytearray(128*88);at=0;stages=[];local=Counter();max_units=max_areas=0;selection_frames=[];area_spells=set();previous=norm(author.projection(state))
  for action in fixture['actions']:
   if action['kind']=='frame':
    state,current,status=author.step_frame(state,action['dt_bits']);assert status=='ordered_frame_projection';assert tuple(k for k,_ in current)==expected_kinds
   else:
    assert action['kind']=='select';cards=state.collection.level.candidates;policy=next((i for i,c in enumerate(cards)if c.variant=='upgrade'),0);assert action['index']==policy,'Coverage-aware selection policy detected'
    state,status=author.select(state,action['index']);current=(('select',state),);selection_frames.append(state.frames)
   for kind,model in current:
    o=actual['stages'][at];expected=norm(author.projection(model));assert kind==o['kind'];words_guard(expected);compare(expected,o['projection'],f'case{fixture["id"]}.stage{at}',counts)
    if has_effects:
     e=expected['effect_state'];assert e['clock2364_bits']==0 and e['effect_counter2356']==0 and e['action_sequence1644']==1 and e['player_action_tag416']==0
     assert e['delayed56']==e['effects120']==dict(capacity=0,records_hex=[]);assert e['player_xyz']==list(model.collection.player_xyz)
     side=o['unmodeled_effect_fields'];assert set(side)=={'inactive_action_payload_words','delayed_pointer','effect120_pointer','player_facing_bits'};assert len(side['inactive_action_payload_words'])==5 and all(type(x)is int and 0<=x<=0xffffffff for x in(*side['inactive_action_payload_words'],side['delayed_pointer'],side['effect120_pointer'],side['player_facing_bits']));unknown_effects.append(dict(case=fixture['id'],stage=at,fields=side))
    if has_tail:
     t=expected['tail_state'];assert set(t)=={'active84','deadline32','secondary112','claims88','special40','field400','flag2568','gate2579'}
     for name in('active84','deadline32','secondary112','claims88','special40'):
      assert t[name]==dict(capacity=0,records_hex=[])
      assert getattr(model.tail,name+'_count')==0 and getattr(model.tail,name+'_storage')==()
     assert t['field400']==t['flag2568']==t['gate2579']==expected['timed916_count']==0
     if kind=='owned_effects':
      for item in model.collection.level.choice_inputs.owned:assert bytes.fromhex(sys.modules['core_spec.headless135'].RAW_BY_POINTER[item.record.definition_pointer])[84]!=11
     side=o['unmodeled_tail_fields'];assert set(side)=={'resource975_words','vector_pointers'}and len(side['resource975_words'])==31
     assert set(side['vector_pointers'])=={'648','1836','1860','2112','1920'}
     assert all(type(w)is int and 0<=w<=0xffffffff for w in(*side['resource975_words'],*side['vector_pointers'].values()))
     unknown_tail.append(dict(case=fixture['id'],stage=at,fields=side));local['tail_empty_vector_stage_observations']+=5;local['inactive975_words_observed_not_predicted']+=31;local['tail_pointers_observed_not_predicted']+=5
     local['inactive975_nonzero_word_observations']+=sum(w!=0 for w in side['resource975_words']);local['tail_nonzero_pointer_observations']+=sum(w!=0 for w in side['vector_pointers'].values())
    prior=bytes(storage);prior_area=bytes(area_storage);lossless(storage,o['unit_storage_delta_words'],local,'unit');modeled=b''.join(bytes.fromhex(r)for r in model.unit_storage);assert len(modeled)==len(storage)and modeled==storage;assert sha_bytes(storage)==expected['unit_storage_sha256']==o['projection']['unit_storage_sha256']
    records=o['projection']['records'];max_units=max(max_units,len(records));assert b''.join(bytes.fromhex(r)for r in records)==storage[:len(records)*424]
    if has_area:
     lossless(area_storage,o['area_storage_delta_words'],local,'area');modeled_area=b''.join(bytes.fromhex(r)for r in model.area_storage);assert len(modeled_area)==len(area_storage)and modeled_area==area_storage;assert sha_bytes(area_storage)==expected['area_storage_sha256']==o['projection']['area_storage_sha256']
     areas=o['projection']['area_records'];max_areas=max(max_areas,len(areas));assert b''.join(bytes.fromhex(r)for r in areas)==area_storage[:len(areas)*88]
     old_count=len(previous['area_records']);area_spells.update(u(bytes.fromhex(r),60)for r in areas)
     if kind=='area':verify_area_tick_storage(prior_area,old_count,expected['now_bits'],area_storage,len(areas),local)
     if kind=='player':
      assert len(areas)>=old_count
      for slot in range(old_count,len(areas)):
       local['area_births']+=1;old=prior_area[slot*88:(slot+1)*88];new=area_storage[slot*88:(slot+1)*88];unwritten=(*range(8,24),85,86,87);assert all(old[b]==new[b]for b in unwritten);local['area_unwritten_append_bytes_checked']+=19
       if struct.unpack_from('<Q',old,24)[0]:local['previously_used_area_slot_reuses']+=1;local['area_reused_nonzero_unwritten_bytes']+=sum(old[b]!=0 for b in unwritten)
     local['full_area_backing_bytes_checked']+=len(area_storage)
    if kind=='spawn':
     for slot in range(len(previous['records']),len(records)):
      old_guid=struct.unpack_from('<Q',prior,slot*424+112)[0]
      if old_guid:
       local['previously_used_unit_slot_reuses']+=1;unwritten=(*range(4,8),*range(12,16),*range(20,112),*range(248,280),*range(419,424));assert all(storage[slot*424+b]==prior[slot*424+b]for b in unwritten);local['nonzero_unwritten_bytes_in_reused_unit_slots']+=sum(prior[slot*424+b]!=0 for b in unwritten)
      if struct.unpack_from('<I',prior,slot*424+4)[0]:assert struct.unpack_from('<I',storage,slot*424+4)[0]==struct.unpack_from('<I',prior,slot*424+4)[0];local['nonzero_stale_death_word_slot_reuses']+=1
    # Independent counter accounting across the full ordered six-entry chain.
    if has_area:
     delta=(expected['spawn_counter']-previous['spawn_counter'])&0xffffffff
     if kind=='spawn':births=len(records)-len(previous['records']);assert delta==births;local['npc_births']+=births
     elif kind in('player','hits','area'):
      pickups=len(expected['pickup_words'])-len(previous['pickup_words']);births=len(expected['area_records'])-len(previous['area_records'])if kind=='player'else 0;assert pickups>=0 and births>=0;assert delta==pickups+births,(fixture['id'],at,kind,delta,pickups,births);local['pickup_births_'+kind]+=pickups
     else:assert delta==0
     if delta:local['counter_changes_'+kind]+=1
     if expected['rng_words']!=previous['rng_words']:local['rng_changes_'+kind]+=1
    if kind in('player','hits','area'):
     oldunits=records_by_guid(previous['records']);newunits=records_by_guid(records)
     for guid,n in newunits.items():
      if guid in oldunits and u(oldunits[guid],0)==0 and u(n,0)==1:
       local['deaths_'+kind]+=1
       if kind=='area':assert n[120:128]==oldunits[guid][120:128];local['area_death_slow_fields_preserved']+=1
      if kind=='area'and guid in oldunits and n[120:128]!=oldunits[guid][120:128]:assert u(n,0)!=1;local['area_slow_writes']+=1
    if kind=='collect'and expected['phase2587']==2:local['natural_choice_pauses']+=1;local['moving_npcs_at_choice_pause']+=len(moving_guids(records,expected['now_bits']))
    if kind=='select'and expected['phase2587']==1:local['choice_resumes']+=1;local['moving_npcs_at_choice_resume']+=len(moving_guids(records,expected['now_bits']))
    local['stages']+=1;local['full_unit_backing_bytes_checked']+=len(storage);local['active_unit_record_bytes_checked']+=len(records)*424
    stages.append(dict(kind=kind,projection=expected));unknowns.append(o['unmodeled_player_fields']);previous=expected;at+=1
  assert at==len(actual['stages']);assert strict(fixture['expected'],stages),'Action replay differs from storedexpected'
  next_state,_,next_status=author.step_frame(state,author.f.from_float(.1))
  if fixture['boundary']=='pending_selected_ability':assert next_status=='pending_selected_ability'and next_state==state
  else:assert fixture['boundary']=='frame_budget'and state.frames==fixture.get('frame_budget',250)
  assert state.frames==fixture['independent_frames']and state.selections==fixture['independent_selections']
  cases.append(dict(id=fixture['id'],seed=inp['seed_u64'],frames=state.frames,selections=state.selections,boundary=fixture['boundary'],final_level=state.collection.level.progression.level,max_active_units=max_units,max_active_areas=max_areas,area_spell_ids=sorted(area_spells),selection_frames=selection_frames,original_compared_frames_after_last_selection=state.frames-selection_frames[-1]if selection_frames else None,next_model_status=next_status,next_frame_original_executed=False,**local));print(json.dumps(dict(case=fixture['id'],frames=state.frames,stages=at,boundary=fixture['boundary'])),flush=True)
  if has_tail:
   for name,field in(('player','unmodeled_player_fields'),('effect','unmodeled_effect_fields'),('tail','unmodeled_tail_fields')):
    assert strict(sidecar_mirrors[name][fixture['id']],dict(id=actual['id'],stages=[s[field]for s in actual['stages']]))
 assert not observed_stream.read().strip()and not fixture_stream.read().strip()
 if has_effects:assert not prior_stream.read().strip()
 assert sum(c['stages']for c in cases)==receipt['stages'];assert sum(c['frames']for c in cases)==receipt['frames'];assert sum(c['selections']for c in cases)==receipt['selections'];assert receipt['runtime']['original_entry_calls']==receipt['stages']+len(cases)
 assert before=={n:sha(snap/n)for n in frozen};assert receipt['runtime']['host_calls']==0 and receipt['process']['exit_code']==0 and not receipt['runtime']['application_start_called']and not receipt['runtime']['network_used']
 totals=Counter()
 for c in cases:
  for k,v in c.items():
   if isinstance(v,int)and k not in('id','seed','frames','selections','final_level','max_active_units','max_active_areas','original_compared_frames_after_last_selection'):totals[k]+=v
 if has_tail:
  ctor_batch=ROOT/'evidence/full0135-oracle-20261101T081314.600878Z';ctor_receipt=json.loads((ctor_batch/'terminal-transition135-comparison.json').read_text())
  for name in('reconstruction/core_spec/initial_state135.py','reconstruction/core_spec/initial_state135_data.py'):
   assert ctor_receipt['source_sha256_before'][name]==frozen[name]
  ctor_fixtures=json.loads((ctor_batch/'terminal-transition135-fixtures.json').read_text())
  ctor_observed=[json.loads(x)for x in(ctor_batch/'terminal-transition135-results.jsonl').read_text().splitlines()]
  assert sha(ctor_batch/'terminal-transition135-results.jsonl')==ctor_receipt['artifacts']['terminal-transition135-results.jsonl']
  ctor_profiles={}
  for c,o in zip(ctor_fixtures,ctor_observed):
   inp={k:int(v)if k in('seed_u64','object_id_u64')else v for k,v in c['input'].items()};initial=author.initialize_empty_profile(author.ConstructorInput135(**inp))
   state=author.from_initial(initial,flat_height_bits=inp['flat_height_bits'],zeroed_unit_storage_resolved=True,zeroed_area_storage_resolved=True)
   actual_sequence=u(bytes.fromhex(o['constructor_raw_g2592_hex']),1644);assert state.action_sequence1644==actual_sequence==(2 if inp['race_byte']==4 else 1)
   ctor_profiles[(inp['class_byte'],inp['race_byte'])]=actual_sequence
  assert len(ctor_profiles)==72
  ctor_sequence=dict(cross_receipt='evidence/full0135-oracle-20261101T081314.600878Z/terminal-transition135-comparison.json',cross_receipt_sha256=sha(ctor_batch/'terminal-transition135-comparison.json'),
   actual_constructor_cases_checked=len(ctor_fixtures),unique_class_race_profiles=72,NightElf_action_sequence=2,other_races_action_sequence=1,
   additional_original_calls_in_this_review=0)
  hm=sys.modules['core_spec.headless135'];tm=sys.modules['core_spec.headless_tail135'];guard_cases=[]
  base=author.resolve_controlled_entry(author.from_initial(author.initialize_empty_profile(author.ConstructorInput135(8,1,0,1,42,0)),flat_height_bits=0,zeroed_unit_storage_resolved=True,zeroed_area_storage_resolved=True),phase1_entry_explicitly_resolved=True)
  def rejected(name,call):
   try:call()
   except(NotImplementedError,ValueError,TypeError)as error:guard_cases.append(dict(name=name,rejected=True,reason=str(error)))
   else:raise AssertionError('Unknown tail domain accepted:'+name)
  rejected('916-nonempty-timed',lambda:tm.guard_extra916((bytes(12).hex(),),0))
  rejected('916-nonempty-active84',lambda:tm.guard_extra916((),1))
  rejected('916-unknown-sources',lambda:tm.guard_extra916(None,0))
  rejected('2376-nonempty-unprotected40',lambda:tm.guard_special2376(1,0))
  tm.guard_special2376(1,1);guard_cases.append(dict(name='2376-protected-outer-block',accepted_exact_gate=True))
  raw=bytearray(32);struct.pack_into('<QII',raw,0,1,0,123)
  rejected('38007-canonical-packets-not-connected',lambda:hm._tail_phase(replace(base,tail=replace(base.tail,deadline32_storage=(raw.hex(),),deadline32_count=1)),'deadline',0))
  raw112=bytearray(112);struct.pack_into('<III',raw112,100,author.f.from_float(100),0,author.f.from_float(1))
  rejected('2602-active-due-not-connected',lambda:hm._tail_phase(replace(base,tail=replace(base.tail,secondary112_storage=(raw112.hex(),),secondary112_count=1)),'secondary',0))
  rejected('2573-running-nonempty-claims',lambda:hm._tail_phase(replace(base,tail=replace(base.tail,claims88_storage=(bytes(88).hex(),),claims88_count=1)),'claims',0))
  rejected('49037-true-path-not-connected',lambda:hm._tail_phase(replace(base,tail=replace(base.tail,field400=1)),'terminal',0))
 else:ctor_sequence={}
 result=dict(version='0.135.1',build='0898d5e3',reviewed_receipt=str(receipt_path.relative_to(ROOT)),reviewed_receipt_sha256=sha(receipt_path),original_sha256=ORIGINAL_SHA,source_files=len(frozen),core_init_import_closure=closure,current_source_drift=drift,roles=manifest['roles'],cases=cases,totals=dict(totals),comparison=dict(counts),boundaries=dict(Counter(c['boundary']for c in cases)),frame_budget=next(iter(budgets)),all_nonexport_sections_identical=True,original_exports_preserved_and_exact_expected_roles_added=True,independent_model_regeneration_and_action_replay=True,lossless_original_unit_and_area_storage_reconstructed=has_area,original_executed=False,author_source_modified=False,reviewer_script_sha256=sha(Path(__file__)),unmodeled_player_key_stage_occurrences=len(unknowns),unmodeled_effect_field_stage_occurrences=len(unknown_effects),unmodeled_tail_field_stage_occurrences=len(unknown_tail),new_independent915_empty_domain_verified=has_effects,prior8seed_actions_and_legacy_expected_unchanged=has_effects,input_isolation=input_schema,constructor_action_sequence_crosscheck=ctor_sequence,preliminary=args.preliminary,limitations=receipt['limitations'],coverage_notes=['Onlyactualevents inthese8seeds arecounted; standalonearea693/frame573/terminal416 metrics are notimported.','All128NPC424B and128area88B slots reconstructed fromordered losslessu32deltas, independentlyhashchecked at every stage.','Independentarea sequential expiry memmoves preserveinactive intermediate tails; thenone64/72 tick update perliveentry.','Append19B reusechecks are exact, but nonzero unwritten reuse is claimedonlyif observed count ispositive.','Next model frame aftera budget stop isobservational only andhasnooriginaloutput inthisbatch.','Only documented pickup/live words accept unspecifiedu32;area/NPCbacking have nomask.','Fiveadditionaltailvectors areactuallycapacity0/count0 atallcomparedstages;nonemptyfullbacking andactivecontinuations are notclaimed.','916timed/extra empty,975noexecution11,2376empty40 and49037falseguard areexactdomains,notnewactivegameplaycoverage.','31resourcewordsand5pointersremainunpredictedsidecars;zero isnotassumed andnonearewrittenbacktotheoriginal.'],conclusion='Controlled same-G ordinary+seven-area 14-entry tail slice passes numeric replay; complete880, genuinephaseentry andwholegame remain unproven.')
 if has_effects:(out/'unmodeled-effect-fields-observed.json').write_text(json.dumps(unknown_effects,indent=2)+'\n')
 if has_tail:(out/'unmodeled-tail-fields-observed.json').write_text(json.dumps(unknown_tail,indent=2)+'\n')
 if has_tail:result['pure_tail_scope_guards']=guard_cases
 (out/'reviewer-source.py').write_bytes(Path(__file__).read_bytes());(out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
 if not args.preliminary:
  (ROOT/'reports/2026-11-01-headless-tail0135-independent-review.json').write_text(json.dumps(dict(result,evidence_directory=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json')),indent=2)+'\n')
  (ROOT/'reports/2026-11-01-headless-tail0135-independent-review.md').write_text('# Headless tail135 independent review\n\n'+f'Fixed0.135.1/0898d5e3: {len(cases)} seeds, {receipt["frames"]} frames, {receipt["stages"]} stages and {receipt["selections"]} natural selections; strict snapshot-model corpus regeneration/action replay and retained original comparisons passed. No original execution or author-source edit.\n\n'+f'All {len(frozen)} source snapshots, {len(closure)} core modules including package init, exact {len(roles)} role signatures/bodySHA and non-export original bytes passed. Both 128-slot storages are independently reconstructed losslessly at every stage; area expiry/tick byte transformations are separately reproduced.\n\n'+'Actual-event totals: `'+json.dumps(dict(totals),sort_keys=True)+'`.\n\n'+'Boundaries: `'+json.dumps(result['boundaries'])+'`; fixed first-upgrade-else-first policy retained. Post-selection original frames and next-model-only status are listed per seed in review.json. No extra original frame after an unknown or budget boundary is implied.\n\n'+'Original Node reads strict seven input fields; expected projections and outcome metadata stay outside its input. After stripping seven new stages and tail/timed fields, legacy072329expected and fixedactions remain unchanged. Five tail vectors are capacity0/count0 at every stage; 31 inactive975words and5pointers are retained as observations, never predictedzero or copiedback. 916/975/2602/2573/2376/49037active continuations are not claimed. Constructor sequence NightElf2/other1 is separately checked against existing416originalconstructors/72class-race profiles, with no new originalcalls.\n\n'+'Masks remain limited to declared pickup arrival and inactive live words; full NPC424/area88 backing bytes are strict. Physical packets/ECS/rendering and complete880/genuineentry remain unresolved.\n\n'+'Receipt: `'+str((out/'review.json').relative_to(ROOT))+'`\n')
 print(json.dumps(dict(directory=str(out),receipt_sha256=sha(receipt_path),review_sha256=sha(out/'review.json'),stages=receipt['stages'],source_files=len(frozen),core_files=len(closure),drift=list(drift),totals=dict(totals)),indent=2))


def sha_bytes(data):return hashlib.sha256(data).hexdigest()
if __name__=='__main__':main()
