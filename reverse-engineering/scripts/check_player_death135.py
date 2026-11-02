#!/usr/bin/env python3
"""Expected-first no-revival5620 component and fatal full1073 domain.

Only new files are written. Existing models/harnesses remain unchanged. Full1073
is compared at declared scalar/history/death outputs, not its unresolved source
registry or every Game byte. Direct5620 additionally checks all Game invariants.
"""
from dataclasses import asdict,replace
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_player_death135_oracle import build,ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.initial_state135 import ConstructorInput135,initialize_empty_profile
from core_spec.terminal_transition135 import TerminalInput135,COUNTER_KEYS,speed_packet226
from core_spec.player_death135 import FatalBoundary135,PlayerDeathState135,finish_no_revival_fatal135,UnknownPlayerDeath135
from core_spec.record_cells135 import cells135,UnknownRecordRead135
from core_spec.incoming135 import IncomingState135,resolve_incoming_prefix
from core_spec.incoming_history135 import from_raw_storage,append_incoming_history
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
def f64(value):return struct.unpack('<Q',struct.pack('<d',value))[0]
def unpack64(value):return struct.unpack('<d',struct.pack('<Q',value))[0]
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
def state_from_raw(value):
 s=dict(value)
 for name in('source_id','damage984_f64_bits','taken992_f64_bits'):s[name]=int(s[name])
 for name in('units_storage','auxiliary_storage','claims_storage'):s[name]=tuple(s[name])
 s['counters']=tuple(tuple(v)for v in s['counters']);return TerminalInput135(**s)
def source_files():
 files=set('scripts/'+n for n in('check_player_death135.py','build_player_death135_oracle.py','run_player_death135_oracle.mjs','build_full135_oracle.py','build_upgrade134_oracle.py','production_closure135.py','source_closure137.py'))
 files.update(production_sources135(ROOT,'core_spec.player_death135','core_spec.initial_state135','core_spec.incoming135','core_spec.incoming_history135'))
 while True:
  try:edges=verify_local_source_closure(sorted(files));return sorted(files),edges
  except AssertionError as e:
   pair=e.args[0]
   if not isinstance(pair,tuple)or len(pair)!=2 or not(ROOT/pair[1]).is_file()or pair[1]in files:raise
   files.add(pair[1])
def motion_record(kind,guid,*,moving=True,marker=0):
 stride,go,ao,bo,so,do=(424,112,316,328,340,344)if kind=='units'else(112,16,32,44,56,60)if kind=='auxiliary'else(88,24,44,56,68,72)
 raw=bytearray([0xa5]*stride)
 if kind=='units':struct.pack_into('<I',raw,0,marker)
 struct.pack_into('<Q',raw,go,guid)
 struct.pack_into('<3I',raw,ao,*(f.from_float(v)for v in(1,2,3)));struct.pack_into('<3I',raw,bo,*(f.from_float(v)for v in(5,8,11)))
 struct.pack_into('<2I',raw,so,f.from_float(9),f.from_float(2 if moving else 0));return raw.hex()
def corpus(pilot):
 cases=[]
 def add(group,*,kind='helper',left=1,moving=False,flat=True,now=10,hero='Hero',hp=1,amount=2,damage=12.5,taken=3.25,action=17,movement=31,counters=None):
  init=initialize_empty_profile(ConstructorInput135(8,1,0,1,42,f.from_float(7)));speed=init.level.stats.previous_speed_bits;prefix=[]
  if f.to_float(f.sub(speed,0x40e00000)&0x7fffffff)>f.to_float(0x3c23d70a):
   p=speed_packet226(42,1,speed);prefix=[dict(opcode=p[0],capacity=p[1],payload_hex=p[2])]
  values={o:0 for o,_ in COUNTER_KEYS};values[1432]=1;values.update(counters or{})
  storages={name:((motion_record(name,100+j),motion_record(name,200+j,moving=False)))if moving else() for j,name in enumerate(('units','auxiliary','claims'))}
  summary=TerminalInput135(0,1,0,f.from_float(now),action,movement,42,storages['units'],len(storages['units']),storages['auxiliary'],len(storages['auxiliary']),storages['claims'],len(storages['claims']),4 if prefix else 0,len(prefix),0,0,tuple(values.items()),f64(damage),f64(taken),8,1,0,hero,left,f.from_float(7),flat,True,True,'english_fallback')
  hp_before=f.from_float(hp) if kind=='incoming'else 0;amount_bits=f.from_float(amount)
  history=from_raw_storage([],0,0);incoming=None
  if kind=='incoming':
   incoming=resolve_incoming_prefix(IncomingState135(hp_1528_bits=hp_before,now_bits=summary.now_bits,incoming_total_992=taken),amount_bits,0)
   assert incoming.stage=='before_unresolved_death'
   summary_after=replace(summary,taken992_f64_bits=f64(incoming.state.incoming_total_992))
   history=append_incoming_history(from_raw_storage([],0,0),now_bits=summary.now_bits,damage_bits=incoming.amount_bits,absorbed_bits=incoming.absorbed_bits,hp_after_prefix_bits=incoming.state.hp_1528_bits,maximum_hp_bits=init.level.stats.old_max_hp_bits,category=0,source_label='',source_classification=4,resolved_spell=None)
   hp_boundary=incoming.state.hp_1528_bits
  else:summary_after=summary;hp_boundary=0
  result=finish_no_revival_fatal135(summary_after,FatalBoundary135(hp_boundary,0,9,None,True,0,True),history=history)
  raw=asdict(summary)
  for name in('source_id','damage984_f64_bits','taken992_f64_bits'):raw[name]=str(raw[name])
  input=dict(id=len(cases),kind=kind,left=left,hero=hero,model_state=raw,starting_hp_bits=hp_before,amount_bits=amount_bits,source_guid='0',taken_before_bits=str(f64(taken)))
  expected=dict(phase=4,hp_bits=0,paused=1,paused_time_bits=summary.now_bits,action_sequence=action,movement_sequence=result.state.movement_sequence2412,packets=prefix+[dict(opcode=p[0],capacity=p[1],payload_hex=p[2])for p in result.packets],notifications=[dict(capacity=n[0],payload_hex=n[1])for n in result.notifications],packet_capacity=result.state.packet_capacity,packet_count=result.state.packet_count,notification_capacity=result.state.notification_vector_capacity,notification_count=result.state.notification_count,vectors={k:dict(count=getattr(result.state,k+'_count'),storage=list(getattr(result.state,k+'_storage')))for k in('units','auxiliary','claims')},taken_f64_bits=str(summary_after.taken992_f64_bits),maximum_hp_bits=init.level.stats.old_max_hp_bits,history=dict(capacity=history.capacity,head=history.head,count=history.count,storage=[list(v)for v in history.storage],strings=[list(v)if v is not None else None for v in history.strings]))
  cases.append(dict(id=len(cases),group=group,input=input,expected=expected))
 add('helper-empty-true-death');add('helper-three-nonempty-stop-consumers',moving=True);add('incoming-fatal-empty',kind='incoming');add('incoming-fatal-moving-NPC-aux-claims',kind='incoming',moving=True)
 if not pilot:
  for left in(1,2,255):
   for flat in(False,True):add('left-nonzero-lazy-recap-and-three-domain-stop',left=left,flat=flat,moving=True,hero='中文"\\\n\t\r\x00😀',movement=0xffffffff)
  for hp,amount in((1,1),(1,2),(.25,.5),(10,30),(0,1)):
   for moving in(False,True):add('full1073-no-revival-fatal-scalars-history',kind='incoming',moving=moving,hp=hp,amount=amount,taken=-3.5,now=12.5)
  for value in(0,1,255,0xffffffff):add('unsigned-counters-and-summary-formatter',counters={o:value for o,_ in COUNTER_KEYS},hero='勇者',now=1.5,damage=value+.125,taken=-(value+.5))
  for text in('', 'x'*1024,'"\\\n\t\r\b\f\x00\x01\x1f','中\u2028\u2029😀'):add('summary-UTF8-and-exact-capacity',hero=text)
  for moving in(False,True):add('left0-real-empty1367-5620',left=0,moving=moving,hero='真正失败')
  for hp,amount in((1,1),(1,2),(.25,.5),(10,30),(0,1)):
   for moving in(False,True):add('left0-full1073-single-fatal-hit-recap',kind='incoming',left=0,moving=moving,hp=hp,amount=amount,now=12.5,hero='角色"\\\n😀')
 return json.loads(json.dumps(cases,ensure_ascii=False,allow_nan=False))
def rejections():
 state=state_from_raw(corpus(True)[0]['input']['model_state']);boundary=FatalBoundary135(0,0,9,None,True,0,True);rows=[]
 for label,change in(
  ('unknown-mode',dict(mode2582=None)),('remote-mode',dict(mode2582=1)),('bool-is-not-mode-u8',dict(mode2582=False)),
  ('unknown-innate',dict(innate_definition_kind=None)),('raw12-unknown-cooldown',dict(innate_definition_kind=12)),
  ('raw12-ready',dict(innate_definition_kind=12,innate_cooldown_bits=0)),('raw12-NaN-not-positive',dict(innate_definition_kind=12,innate_cooldown_bits=0x7fc00000)),
  ('unknown-modifier31',dict(modifier31_absent=None)),('modifier31-present',dict(modifier31_absent=False)),
  ('unknown-lives',dict(lives1632=None)),('remaining-life',dict(lives1632=1)),('bool-is-not-lives-u32',dict(lives1632=False)),
  ('callbacks-not-completed',dict(incoming_callbacks_complete=None)),('HP-positive',dict(hp_after_callbacks_bits=0x3f800000)),('HP-NaN',dict(hp_after_callbacks_bits=0x7fc00000))):
  try:finish_no_revival_fatal135(state,replace(boundary,**change))
  except UnknownPlayerDeath135 as error:rows.append(dict(case=label,rejected=True,reason=str(error)))
  else:raise AssertionError(label)
 try:finish_no_revival_fatal135(replace(state,left2567=0),boundary)
 except UnknownPlayerDeath135 as error:rows.append(dict(case='left0-history-unknown',rejected=True,reason=str(error)))
 else:raise AssertionError('Unknown recap silently accepted')
 # Inactive innate/left domains really do not require their opaque payloads.
 assert finish_no_revival_fatal135(state,boundary,history=object()).status=='no_revival_mode0_death_complete'
 return rows
def unknown_cell_projection():
 c=corpus(True)[1];state=state_from_raw(c['input']['model_state']);changes={};preserved=0
 for name in('units','auxiliary','claims'):
  rows=[]
  for i,value in enumerate(getattr(state,name+'_storage')):
   raw=list(bytes.fromhex(value));known=((0,4),(112,120),(316,348))if name=='units'and i==0 else((0,4),(344,348))if name=='units'else((16,24),(32,64))if name=='auxiliary'and i==0 else((60,64),)if name=='auxiliary'else((24,32),(44,76))if i==0 else((68,76),)
   rows.append(tuple(v if any(a<=j<b for a,b in known)else None for j,v in enumerate(raw)))
  changes[name+'_storage']=tuple(rows)
 partial=PlayerDeathState135(**{**asdict(state),**changes,'counters':state.counters})
 result=finish_no_revival_fatal135(partial,FatalBoundary135(0,0,9,None,True,0,True))
 for name in('units','auxiliary','claims'):
  full=c['expected']['vectors'][name]['storage']
  for before,after,physical in zip(getattr(partial,name+'_storage'),getattr(result.state,name+'_storage'),full):
   row=cells135(after,len(before));physical=bytes.fromhex(physical)
   for j,value in enumerate(row):
    if value is None:assert before[j]is None;preserved+=1
    else:assert value==physical[j]
 broken=list(changes['units_storage'][0]);broken[0]=None
 try:finish_no_revival_fatal135(replace(partial,units_storage=(tuple(broken),)+partial.units_storage[1:]),FatalBoundary135(0,0,9,None,True,0,True))
 except UnknownRecordRead135:pass
 else:raise AssertionError('Consumed unknown NPC marker accepted')
 return dict(kind='known_cell_original_projection_plus_model_unknown_preservation_not_new_original_cases',case_id=1,preserved_unknown_cells=preserved,vectors={name:[list(cells135(row,stride))for row in getattr(result.state,name+'_storage')]for name,stride in(('units',424),('auxiliary',112),('claims',88))})
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();files,edges=source_files();before={n:sha(ROOT/n)for n in files};rejected=rejections();partial=unknown_cell_projection();cases=corpus(args.phase=='pilot')
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-death135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
 for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
 save(out/'fixtures.json',cases);save(out/'inputs.json',[c['input']for c in cases]);save(out/'expected.json',[dict(id=c['id'],expected=c['expected'])for c in cases]);save(out/'rejections.json',rejected);save(out/'unknown-cell-projection.json',partial);frozen={p.name:sha(p)for p in(out/'fixtures.json',out/'inputs.json',out/'expected.json',out/'rejections.json',out/'unknown-cell-projection.json',out/'manifest.json',out/manifest['module_file'])}
 assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA and before=={n:sha(ROOT/n)for n in files}
 command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_player_death135_oracle.mjs'),str(out),str(out/'inputs.json')];save(out/'prepared.json',dict(source_sha256=before,source_import_edges=edges,expected_before_original=True,artifacts=frozen,command=command,deadline_seconds=60));started=time.monotonic()
 with(out/'stdout.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
  child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
  try:code=child.wait(timeout=60)
  except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
 def missing(group=False):
  try:(os.killpg if group else os.kill)(child.pid,0)
  except ProcessLookupError:return True
  return False
 terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-started,deadline_seconds=60,pid_missing=missing(),pgid_missing=missing(True));save(out/'owned-terminal.json',terminal)
 actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];differences=[];counts=Counter();observed_unmodeled=Counter()
 if code or len(actual)!=len(cases):save(out/'failure.json',dict(status='original_execution_failed',terminal=terminal,completed=len(actual),cases=len(cases)));print(json.dumps(dict(out=str(out),status='original_execution_failed',terminal=terminal,stderr=(out/'stderr.log').read_text()[-2000:])));raise SystemExit(1)
 for c,a in zip(cases,actual,strict=True):
  assert c['id']==a['id'];e=c['expected'];after=a['after'];raw=bytes.fromhex(after['raw_game2592_hex']);old=bytes.fromhex(a['before']['raw_game2592_hex']);r=lambda o:struct.unpack_from('<I',raw,o)[0]
  got=dict(phase=raw[2587],hp_bits=r(1440),paused=r(408),paused_time_bits=r(412),action_sequence=r(1644),movement_sequence=r(2412),taken_f64_bits=str(struct.unpack_from('<Q',raw,992)[0]))
  for key in got:
   if got[key]!=e[key]:differences.append(dict(id=c['id'],field=key,expected=e[key],actual=got[key]))
   counts['known_values']+=1
  for key in('packets','notifications','packet_capacity','packet_count','notification_capacity','notification_count','vectors'):
   if after[key]!=e[key]:differences.append(dict(id=c['id'],field=key,expected=e[key],actual=after[key]))
  if a['constructor_innate_kind']==12:raise AssertionError('Innate resurrection domain')
  assert a['before']['packet_count']==c['input']['model_state']['packet_count'] and a['before']['packet_capacity']==c['input']['model_state']['packet_capacity'] and a['before']['notifications']==[]
  if c['input']['kind']=='helper':
   wanted=bytearray(old)
   for o,v in((408,1),(412,e['paused_time_bits']),(1644,e['action_sequence']),(2412,e['movement_sequence']),(1880,e['packet_capacity']),(1888,e['packet_count']),(1892,e['notification_capacity']),(1900,e['notification_count'])):struct.pack_into('<I',wanted,o,v)
   wanted[2587]=4
   for offset,capkey in((1884,'packet_capacity'),(1896,'notification_capacity')):
    if a['before'][capkey]!=after[capkey]:wanted[offset:offset+4]=raw[offset:offset+4];counts['observed_new_heap_pointer_words']+=1
   if bytes(wanted)!=raw:differences.append(dict(id=c['id'],field='all_raw_Game2592_helper',offsets=[j for j,(x,y)in enumerate(zip(wanted,raw))if x!=y]))
   counts['all_raw_Game2592_helper_bytes']+=2592;assert after['history']==a['before']['history']
  else:
   history=after['history'];want=e['history'];assert len(history['active'])==1
   if {k:history[k]for k in('capacity','head','count')}!={k:want[k]for k in('capacity','head','count')}:differences.append(dict(id=c['id'],field='history_header'))
   row=history['active'][0];words=bytes.fromhex(row['raw_hex']);expected=want['storage'][0]
   for j,value in enumerate(expected):
    if value is not None and words[j]!=value:differences.append(dict(id=c['id'],field='history_byte',offset=j,expected=value,actual=words[j]))
   if row['strings']!=want['strings'][0]:differences.append(dict(id=c['id'],field='history_strings',expected=want['strings'][0],actual=row['strings']))
   for key,value in(('22',0),('28',int(f.to_float(e['maximum_hp_bits'])))):
    if after['keyed_fields'].get(key)!=value:differences.append(dict(id=c['id'],field='keyed_'+key,expected=value,actual=after['keyed_fields'].get(key)))
   # All raw bytes are retained; only this batch's declared outputs are modeled.
   for offset,_ in a['changed_bytes']:
    if 1112<=offset<1124:observed_unmodeled['source_registry_'+str(offset)]+=1
   counts['history_records']+=1
  assert a['stack_after']==1048576 and a['host_calls']==0
  if c['id']==partial['case_id']:
   for name,rows in partial['vectors'].items():
    for projection,physical in zip(rows,after['vectors'][name]['storage'],strict=True):
     observed=bytes.fromhex(physical)
     for j,value in enumerate(projection):
      if value is not None:assert observed[j]==value;counts['unknown_projection_known_bytes_original_compared']+=1
   counts['model_only_unknown_cells_preserved']=partial['preserved_unknown_cells']
  counts[c['input']['kind']+'_calls']+=1;counts['stop_packets221']+=sum(p['opcode']==221 for p in after['packets'][a['before']['packet_count']:]);counts['complete_defeat_notifications']+=len(after['notifications'])
 assert frozen=={name:sha(out/name)for name in frozen} and before=={name:sha(ROOT/name)for name in files}
 runtime=json.loads((out/'runtime.json').read_text());receipt=dict(status='scoped_original_differential_passed'if not differences else'differences',version='0.135.1',actual_build='90898d5e3',phase=args.phase,cases=len(cases),differences=len(differences),difference_rows=differences,groups=dict(Counter(c['group']for c in cases)),counts=dict(counts),negative_boundary_checks=len(rejected),negative_checks_kind='model_selfcheck_not_original_differential',observed_unmodeled_registry_bytes=dict(observed_unmodeled),source_sha256_before=before,source_sha256_after=before,source_import_edges=edges,source_files=len(files),expected_before_original=True,original_sha256=SOURCE_SHA,manifest_sha256=sha(out/'manifest.json'),module_sha256=manifest['module_sha256'],frozen_artifacts=frozen,artifacts={n:sha(out/n)for n in('stdout.jsonl','stderr.log','runtime.json','owned-terminal.json','prepared.json')},runtime=runtime,process=terminal,limitations=['Direct5620 complete mode0 with fullGame invariants,ordered17119/17217/16340 stop bytes/221 payloads,complete1938 defeatnotification/capacity.','Full1073 executes unchanged; only no-revival mode0,sourceGUID0,emptybuff/modifier/item sources,scalar/history/keyedHP/death outputs modeled.','Source-registry metadata and all full1073 Gamebytes are retained as observations,not falsely claimed modeled.','left0 includes genuine1367 empty and single-fatal-hit recap; multi-hit1367 component validation is separate and its old runtime counts are not added. left!=0 lazily uses{} without consuming history.','Empty/flat absent-terrain geometry domain shares previously validated stop consumers; no naturalWorld terrain or completeApp producer.','incoming_callbacks_complete is an explicit boundary condition,not permission to bypass unknown real callback producers.','1560 is actual controlled setup in this batch,not new independent constructor acceptance.','Nested5620 count follows the statically verified fatal control path; internal calls were not instrumented.','No complete880/game/native execution is claimed.'])
 save(out/'comparison.json',receipt);print(json.dumps(dict(status=receipt['status'],out=str(out.relative_to(ROOT)),comparison_sha256=sha(out/'comparison.json'),cases=len(cases),differences=len(differences),first_differences=differences[:4],counts=dict(counts),process=terminal)))
 if differences:raise SystemExit(1)
if __name__=='__main__':main()
