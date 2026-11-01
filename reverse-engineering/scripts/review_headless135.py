#!/usr/bin/env python3
"""Independent frozen-model/action and two lossless-storage review; no WASM execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,hashlib,json,re,struct,sys
sys.dont_write_bytecode=True
from review_gameplay_phase135 import ROOT,ORIGINAL,ORIGINAL_SHA,sha,strict,norm,sections,bodies,core_closure,load_checker,moving_guids,uint
DEFAULT='full0135-oracle-20261101T064308.759593Z'
ROLE_BINDINGS={'initial_game':(1560,'7f7f7f',''),'player_tick':(2088,'7f7d',''),'process_hits':(1754,'7f',''),'area_tick':(3757,'7f',''),'update_units':(921,'7f7d',''),'collect_pickups':(2862,'7f',''),'spawn_tick':(947,'7f7d',''),'select_ability':(1072,'7f7f','')}


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
 parser=argparse.ArgumentParser();parser.add_argument('--batch',default=DEFAULT);parser.add_argument('--output');args=parser.parse_args()
 batch=Path(args.batch);batch=batch if batch.is_absolute()else ROOT/'evidence'/args.batch
 out=Path(args.output).resolve()if args.output else ROOT/'evidence'/datetime.now(timezone.utc).strftime('headless-area0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir(parents=True,exist_ok=True)
 receipt_path=batch/'headless135-comparison.json';receipt=json.loads(receipt_path.read_text());frozen=receipt['source_sha256_before'];assert frozen==receipt['source_sha256_after'];snap=batch/'source-snapshot';drift={}
 for name,digest in frozen.items():
  assert sha(snap/name)==digest
  if sha(ROOT/name)!=digest:drift[name]=dict(frozen=digest,current=sha(ROOT/name))
 closure=core_closure(snap,('headless135.py',));assert set(closure)<=frozen.keys()
 for name,digest in receipt['artifacts'].items():assert sha(batch/name)==digest
 raw=ORIGINAL.read_bytes();assert hashlib.sha256(raw).hexdigest()==ORIGINAL_SHA;ss=sections(raw);bb=bodies(raw,ss);signature=signatures(raw,ss)
 module=(batch/'research135-exports.wasm').read_bytes();ms=sections(module);assert [(k,x)for k,x,_,_ in ss if k!=7]==[(k,x)for k,x,_,_ in ms if k!=7];assert not any(k==8 for k,*_ in ss)
 manifest=json.loads((batch/'manifest.json').read_text());has_area=any(r['role']=='area_tick'for r in manifest['roles']);roles=dict(ROLE_BINDINGS)
 if not has_area:del roles['area_tick']
 assert manifest['denied_function_import_count']==878 and {r['role']for r in manifest['roles']}==roles.keys()
 for r in manifest['roles']:
  i,params,results=roles[r['role']];assert(i,params,results)==(r['index'],r['parameters_hex'],r['results_hex']);assert signature(i)==(params,results)
  a,b=bb[i-878];assert(a,b)==(r['body_start'],r['body_end']);assert hashlib.sha256(raw[a:b]).hexdigest()==r['body_sha256']
 oldex=exports(raw,next(s for s in ss if s[0]==7));newex=exports(module,next(s for s in ms if s[0]==7));assert newex[:len(oldex)]==oldex;assert newex[len(oldex):]==[(r['export'],0,r['index'])for r in manifest['roles']]
 del raw,module,ss,ms,bb
 before={name:sha(snap/name)for name in frozen};author=load_checker(snap,'check_headless135.py','review_headless135_frozen_checker')
 fixtures=[json.loads(x)for x in(batch/'headless135-fixtures.jsonl').read_text().splitlines()];budgets={f.get('frame_budget',250)for f in fixtures};assert len(budgets)==1
 regenerated=author.corpus(False,frame_budget=next(iter(budgets)));assert strict(fixtures,regenerated),'Fixed-policy corpus regeneration differs'
 observed=[json.loads(x)for x in(batch/'headless135-results.jsonl').read_text().splitlines()];assert [x['id']for x in observed]==list(range(8));assert[int(f['input']['seed_u64'])for f in fixtures]==list(range(8))
 counts=Counter();cases=[];unknowns=[];expected_kinds=('player','hits','area','ai','collect','spawn')if has_area else('player','hits','ai','collect','spawn')
 for fixture,actual in zip(fixtures,observed):
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
 assert sum(c['stages']for c in cases)==receipt['stages'];assert sum(c['frames']for c in cases)==receipt['frames'];assert sum(c['selections']for c in cases)==receipt['selections'];assert receipt['runtime']['original_entry_calls']==receipt['stages']+len(cases)
 assert before=={n:sha(snap/n)for n in frozen};assert receipt['runtime']['host_calls']==0 and receipt['process']['exit_code']==0 and not receipt['runtime']['application_start_called']and not receipt['runtime']['network_used']
 totals=Counter()
 for c in cases:
  for k,v in c.items():
   if isinstance(v,int)and k not in('id','seed','frames','selections','final_level','max_active_units','max_active_areas','original_compared_frames_after_last_selection'):totals[k]+=v
 result=dict(version='0.135.1',build='0898d5e3',reviewed_receipt=str(receipt_path.relative_to(ROOT)),reviewed_receipt_sha256=sha(receipt_path),original_sha256=ORIGINAL_SHA,source_files=len(frozen),core_init_import_closure=closure,current_source_drift=drift,roles=manifest['roles'],cases=cases,totals=dict(totals),comparison=dict(counts),boundaries=dict(Counter(c['boundary']for c in cases)),frame_budget=next(iter(budgets)),all_nonexport_sections_identical=True,original_exports_preserved_and_exact_expected_roles_added=True,independent_model_regeneration_and_action_replay=True,lossless_original_unit_and_area_storage_reconstructed=has_area,original_executed=False,author_source_modified=False,reviewer_script_sha256=sha(Path(__file__)),unmodeled_player_key_stage_occurrences=len(unknowns),limitations=receipt['limitations'],coverage_notes=['Onlyactualevents inthese8seeds arecounted; standalonearea693case metrics are notimported.','All128NPC424B and128area88B slots reconstructed fromordered losslessu32deltas, independentlyhashchecked at every stage.','Independentarea sequential expiry memmoves preserveinactive intermediate tails; thenone64/72 tick update perliveentry.','Append19B reusechecks are exact, but nonzero unwritten reuse is claimedonlyif observed count ispositive.','Next model frame aftera budget stop isobservational only andhasnooriginaloutput inthisbatch.','Only documented pickup/live words accept unspecifiedu32;area/NPCbacking have nomask.'],conclusion='Controlled same-G ordinary+seven-area gameplay slice passes; complete880, genuinephaseentry andwholegame remain unproven.')
 (out/'reviewer-source.py').write_bytes(Path(__file__).read_bytes());(out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
 (ROOT/'reports/2026-11-01-headless-area0135-independent-review.json').write_text(json.dumps(dict(result,evidence_directory=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json')),indent=2)+'\n')
 (ROOT/'reports/2026-11-01-headless-area0135-independent-review.md').write_text('# Headless area135 independent review\n\n'+f'Fixed0.135.1/0898d5e3: {len(cases)} seeds, {receipt["frames"]} frames, {receipt["stages"]} stages and {receipt["selections"]} natural selections; strict snapshot-model corpus regeneration/action replay and retained original comparisons passed. No original execution or author-source edit.\n\n'+f'All {len(frozen)} source snapshots, {len(closure)} core modules including package init, exact {len(roles)} role signatures/bodySHA and non-export original bytes passed. Both 128-slot storages are independently reconstructed losslessly at every stage; area expiry/tick byte transformations are separately reproduced.\n\n'+'Actual-event totals: `'+json.dumps(dict(totals),sort_keys=True)+'`.\n\n'+'Boundaries: `'+json.dumps(result['boundaries'])+'`; fixed first-upgrade-else-first policy retained. Post-selection original frames and next-model-only status are listed per seed in review.json. No extra original frame after an unknown or budget boundary is implied.\n\n'+'Masks remain limited to declared pickup arrival and inactive live words; full NPC424/area88 backing bytes are strict. Physical packets/ECS/rendering and complete880/genuineentry remain unresolved.\n\n'+'Receipt: `'+str((out/'review.json').relative_to(ROOT))+'`\n')
 print(json.dumps(dict(directory=str(out),receipt_sha256=sha(receipt_path),review_sha256=sha(out/'review.json'),stages=receipt['stages'],source_files=len(frozen),core_files=len(closure),drift=list(drift),totals=dict(totals)),indent=2))


def sha_bytes(data):return hashlib.sha256(data).hexdigest()
if __name__=='__main__':main()
