#!/usr/bin/env python3
"""Independent static/reference review; never import or execute production."""
import ast
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,math,re,sqlite3,struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRACE=ROOT/'evidence/incoming-callbacks135-static-20261102T003044.215536Z/trace.json'
TRACE_SHA='54853c37c7a3285384c921f1b289ab6151bb105efa62c68ad6b18051cfbc55a7'
OBSERVER=ROOT/'evidence/incoming-callback-sources135-model-observer-20261102T002438.264636Z/sources.json'
OBSERVER_SHA='880fc4c769ee4da33a2261ea632bf021c873b32188d8dcbee70b92f31f77f59c'
MODULE='reconstruction/core_spec/incoming_callbacks135.py'
MODULE_SHA='4045cd21c510175bfe87313687045ee66de8b2dffc3dd3a498580b3955ef4fc9'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb')as stream:
  for block in iter(lambda:stream.read(1048576),b''):h.update(block)
 return h.hexdigest()
def bits(value):
 try:return struct.unpack('<I',struct.pack('<f',value))[0]
 except OverflowError:return 0xff800000 if value<0 else 0x7f800000
def number(word):return struct.unpack('<f',struct.pack('<I',word))[0]
def plus(a,b):
 value=number(a)+number(b)
 return 0x7fc00000 if math.isnan(value)else bits(value)
class Refused(Exception):pass
def word(row,offset):
 cells=row[offset:offset+4]
 if any(x is None for x in cells):raise Refused('unknown consumed word'+str(offset))
 return int.from_bytes(bytes(cells),'little')
def live(kind,value=0,expiry=20):
 raw=[None]*32;raw[8:12]=struct.pack('<I',kind);raw[24:28]=struct.pack('<I',bits(expiry))
 if value is not None:raw[12:16]=struct.pack('<I',bits(value))
 return raw
def item(kind,value):
 raw=[None]*8;raw[0]=kind
 if value is not None:raw[4:8]=struct.pack('<I',bits(value))
 return raw
def modifier(kind):return list(struct.pack('<I',kind)+bytes(32))
def raw13(rows,now):
 total=0x80000000
 for row in rows:
  if number(now)<number(word(row,24)) and word(row,8)==13:total=plus(total,word(row,12))
 return total

def reference(value):
 """Direct1073/984 semantic reference; no production imports/functions."""
 if any(value.get(k)is None for k in('live','items','modifiers')):raise Refused('unknown physical source')
 if value.get('phase',1)!=1:raise Refused('phase domain')
 live_rows,items,mods=(value[k]for k in('live','items','modifiers'))
 total=raw13(live_rows,value['now'])
 common=dict(hp_before_minimum_one1440_bits=value['hp'],raw13_sum_bits=total,
  skipped_914_calls=['raw13','item22'],input_counts=[len(live_rows),len(items),len(mods)])
 if value.get('guid',123)==0 or value.get('contact',1)==0:
  return dict(**common,item22_sum_bits=None,returned_984_calls=0,modifier_noevent_tags=[],branch='source_or_contact_gate_skips_entire_callback_block')
 if number(total)>0:raise Refused('raw13 may call914')
 reflected=0x80000000
 for row in items:
  if row[0]is None:raise Refused('unknown item kind')
  if row[0]==22:reflected=plus(reflected,word(row,4))
 if number(value.get('base',bits(2)))>0 and number(reflected)>0:raise Refused('item22 may call914')
 tags=[]
 for row in mods:
  tag=word(row,0)
  if tag!=54:raise Refused('unrestored984 tag')
  if any(x is None for x in row):raise Refused('unknown copied36 payload')
  tags.append(tag)
 return dict(**common,item22_sum_bits=reflected,returned_984_calls=2,modifier_noevent_tags=tags,branch='source_contact_active_no914_and_two_inert984')

def fixtures():
 base=dict(now=bits(10),hp=bits(-1),guid=123,contact=1,phase=1,base=bits(2),live=[],items=[],modifiers=[])
 rows=[]
 def add(label,**values):rows.append((label,dict(base,**values)))
 add('explicit_empty_sources_contact_nonzero')
 add('zero_GUID_skips_item_and_984',guid=0,items=[item(22,3)],modifiers=[modifier(0)])
 add('flag0_skips_item_and_984',contact=0,items=[item(22,3)],modifiers=[modifier(0)])
 add('kind8_opaque_value_and_auxiliary_unused',live=[live(8,None)])
 add('expired13_payload_unknown_unused',live=[live(13,None,9)])
 add('raw13_ordered_cancellation',live=[live(13,2),live(13,-2)])
 add('item22_zero_base_amount',base=0,items=[item(22,2)])
 add('item7_unknown_value_unused',items=[item(7,None)])
 add('full36_tag54_noevent',modifiers=[modifier(54)])
 add('raw13_active_positive',live=[live(13,1)])
 add('raw13_active_unknown_value',live=[live(13,None)])
 add('item22_positive',items=[item(22,1)])
 add('unknown_item_kind',items=[[None]*8])
 add('unknown_modifier_kind',modifiers=[[None]*36])
 add('unrestored984_kind',modifiers=[modifier(0)])
 damaged=modifier(54);damaged[4]=None
 add('copied54_payload_unknown',modifiers=[damaged])
 add('unknown_physical_nonlive_owner',items=None)
 add('phase2',phase=2)
 return rows

def closure():
 """Independent AST walk, including package initializer, never import."""
 pending=['core_spec.incoming_callbacks135'];seen=set();edges=set()
 while pending:
  module=pending.pop()
  if module in seen:continue
  seen.add(module);path=ROOT/'reconstruction'/Path(*module.split('.')).with_suffix('.py')
  if not path.exists():path=ROOT/'reconstruction'/Path(*module.split('.'))/'__init__.py'
  for node in ast.walk(ast.parse(path.read_text())):
   if not isinstance(node,ast.ImportFrom)or node.level!=1:continue
   package=module.rsplit('.',1)[0]
   candidates=[package+'.'+node.module]if node.module else[package+'.'+v.name for v in node.names]
   for other in candidates:
    p=ROOT/'reconstruction'/Path(*other.split('.')).with_suffix('.py')
    if p.exists():edges.add((str(path.relative_to(ROOT)),str(p.relative_to(ROOT))));pending.append(other)
 files=['reconstruction/core_spec/__init__.py']
 for module in sorted(seen):files.append('reconstruction/'+str(Path(*module.split('.')).with_suffix('.py')))
 return files,sorted(edges)

def main():
 assert sha(TRACE)==TRACE_SHA and sha(OBSERVER)==OBSERVER_SHA and sha(ROOT/MODULE)==MODULE_SHA
 assert sha(ORIGINAL)==ORIGINAL_SHA
 files,edges=closure();before={name:sha(ROOT/name)for name in files}
 author=json.loads(TRACE.read_text());assert author['original_calls']==0 and author['new_original_cases']==0
 assert author['source_before']==author['source_after']
 for name in files:
  if name in author['source_before']:assert before[name]==author['source_before'][name]
 tree=ast.parse((ROOT/MODULE).read_text())
 assert {node.module for node in ast.walk(tree)if isinstance(node,ast.ImportFrom)}=={'dataclasses',None,'record_cells135'}
 assert not any(isinstance(n,ast.Import)for n in ast.walk(tree))
 now=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ');out=ROOT/'evidence'/('incoming-callbacks135-independent-review-'+now);out.mkdir()
 functions={};texts={}
 db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row
 with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat,ORIGINAL.open('rb')as original:
  for index in(1073,984,921):
   row=dict(db.execute('select * from functions where idx=?',(index,)).fetchone());wat.seek(row['wat_start']);data=wat.read(row['wat_end']-row['wat_start']);original.seek(row['body_start']);body=original.read(row['body_end']-row['body_start']);texts[index]=data.decode().splitlines()
   assert hashlib.sha256(body).hexdigest()==author['functions'][str(index)]['body_sha256'] and hashlib.sha256(data).hexdigest()==author['functions'][str(index)]['wat_sha256']
   (out/f'{index}.wat').write_bytes(data)
   functions[str(index)]=dict(body_sha256=hashlib.sha256(body).hexdigest(),wat_sha256=hashlib.sha256(data).hexdigest(),lines=len(texts[index]))
 #Resolve984's actual structured jump, independently of author's label lookup.
 lines=texts[984];stack=[];frames={};first=None;target_start=None
 for index,line in enumerate(lines):
  s=line.strip()
  if s.startswith(('block','loop','if '))or s=='if':stack.append(index)
  if s.startswith('br_table')and first is None:
   first=index;targets=re.findall(r'(\d+)\s+\(;@(\d+);\)',s);selector=(54-12)-1;depth,label=map(int,targets[selector]);assert(selector,depth,label)==(41,31,6);target_start=stack[-depth-1]
  if s=='end':
   start=stack.pop();frames[start]=index
 end=frames[target_start]
 assert 'label = @6'in lines[target_start]
 flag_writes=[i for i,line in enumerate(lines)if line.strip()in('local.set 41','local.tee 41')]
 assert flag_writes and all(first<i<end for i in flag_writes)
 after='\n'.join(lines[end+1:])
 assert all(term in after for term in('local.get 29','local.get 38','call 71889','i32.store offset=476','i32.store offset=472','local.get 41','call 1512'))
 hp_stores=[i+1 for i,line in enumerate(lines)if 'store offset=1440'in line]
 assert not any(i>end for i in hp_stores)
 #Full1073 callback area: exactlytwo984; HP reread occurs after its @2 exit.
 callback='\n'.join(texts[1073][3442:3891]);assert callback.count('call 984')==2 and callback.count('call 914')==2
 first984=callback.index('call 984')
 assert callback.index('i32.const 1024')<first984<callback.index('i32.const 5\n',first984)<callback.rindex('call 984')<callback.index('f32.load offset=1440')
 assert texts[921][7490].strip()=='call 1073'
 checked=[]
 stored=author['model_checks'];declared=fixtures();assert[label for label,_ in declared]==[row['case']for row in stored]
 for(label,value),row in zip(declared,stored):
  try:got=reference(value)
  except Refused as error:
   assert row['accepted']is False;checked.append(dict(case=label,accepted=False,independent_reason=str(error)))
  else:
   assert row['accepted']is True and got==row['proof'];checked.append(dict(case=label,accepted=True,proof=got))
 observed=json.loads(OBSERVER.read_text());assert observed['original_calls']==0 and observed['source_unchanged']
 reductions=Counter();kinds=Counter();opaque=0
 for frame in observed['observations']:
  src=frame['shape']['player_sources'];rows=src['live_storage'][:src['live_count']]
  result=raw13(rows,frame['stats']['now_bits']);reductions[str(result)]+=1
  for row in rows:kinds[str(word(row,8))]+=1;opaque+=sum(v is None for v in row)
  assert frame['unowned']['original_G2056_36B_vector']is None and frame['unowned']['original_G2028_8B_item_vector']is None
 assert dict(reductions)==author['observer']['raw13_reductions'] and dict(kinds)==author['observer']['active_live_kinds'] and opaque==author['observer']['unknown_cells']['active_None_cells']
 after_sources={name:sha(ROOT/name)for name in files};assert before==after_sources and sha(ROOT/MODULE)==MODULE_SHA
 review=dict(status='passed_narrow_static_HP_inertness_predicate_only',independent_reviewer='/root/self_buffs119_review',author='/root/motion38_review',module_sha256=MODULE_SHA,author_trace_sha256=TRACE_SHA,source_sha256_before=before,source_sha256_after=after_sources,production_import_edges=[list(x)for x in edges],original_calls=0,production_executions=0,author_checker_executions=0,original_functions=functions,tag54_controlflow=dict(selector=41,target_depth=31,target_label=6,target_start_line=target_start+1,target_end_line=end+1,local41_writes_bypassed=[i+1 for i in flag_writes],hp_stores_after_target=[]),stored_selfchecks_independently_recomputed=checked,observer_input_reductions=dict(reductions),observer_live_kinds=dict(kinds),observer_opaque_cells=opaque,
  observations=['Raw13 expirystrict now<expiry,kind32==13,orderedf32 addition fromnegativezero','GUID0 orcontact0 skipsitem22 andboth984 afterraw13reduction','Positive active13 rejected;positive item22 andpositive original/modescaled prearmoramount rejected','Itemkind usesbyte0;only22 consumesvalue4;unknown selectedbytes reject','984count0 exitsbeforeptr/cap access;allknown36B tag54 mapsselector41 tocommonexit','tag54 bypassesalllocal41 assignments;temporary472/476restore;no1512 orHPmutation','HPbits returnedunchangedbefore2578 clamp;no claimprefixorrevival/death/keyedoutput implemented'],
  limits=['Static/reference review,notnewfull1073 originaldifferential','Stored18 author checks aremodelselfchecks;independent recomputation doesnotturnthem intooriginalcases','Observer was authoredbythisreviewer;readasdeclaredmodelinput only,notsecondindependentoriginalcapture','Sourceowner135 authoredbythisreviewer isnot imported,executed,validatedorcountedinthisreview','Requirescomplete posthistorysources afterallprefix-sideeffects;preAIobserveralonecannotproveposthistoryidentity','Tag54clone/free physicalallocation effects andfailure arenotpredicted;currentcount0domain performsnoallocation','Conservative unknown/copy-payload rejections areallowednarrowing,notproofallvalidcallbackdomains covered','Canonicalized NaN payloads arelogicalinertness values,notoriginalpayloadbitdifferential'])
 for name,digest in before.items():
  path=out/'source-snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes());assert sha(path)==digest
 path=out/'review.json';path.write_text(json.dumps(review,indent=2)+'\n')
 print(json.dumps(dict(directory=str(out),review_sha256=sha(path),selfchecks=len(checked),accepted=sum(x['accepted']for x in checked),observer_frames=len(observed['observations']),original_calls=0,production_executions=0)))

if __name__=='__main__':main()
