#!/usr/bin/env python3
"""Independent read-only demo180/207 audit; no model/checker/original executes."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
from review_resource_consumer137 import source_edges,identities
from review_battle_shout135 import F,B,add,sub,mul
from review_event_wave135 import rng
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/demo-shout135-oracle-20261101T204357.749953Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
MASK=0xffffffff

def sha(p):
 with Path(p).open('rb')as s:return hashlib.file_digest(s,'sha256').hexdigest()
def u(row,o=0):
 values=row[o:o+4];assert len(values)==4 and all(type(x)is int and 0<=x<=255 for x in values);return int.from_bytes(bytes(values),'little')
def put(row,o,value):row[o:o+4]=struct.pack('<I',value)
def Q(row,o):return int.from_bytes(bytes(row[o:o+8]),'little')
def divide(a,b):return B(F(a)/F(b))
def packed(guid):
 raw=guid.to_bytes(8,'little');return bytes((sum(1<<i for i,v in enumerate(raw)if v),))+bytes(x for x in raw if x)
def aura_packet(guid,fields):
 pairs=sorted(fields);count=1+max(k for k,_ in pairs)//32;masks=[sum(1<<(k%32)for k,_ in pairs if k//32==j)for j in range(count)]
 return(struct.pack('<IB',1,0)+b'\0'+packed(guid)+bytes((count,))+struct.pack('<'+'I'*count,*masks)+struct.pack('<'+'I'*len(pairs),*(v for _,v in pairs))).hex()

def merge21455(words,strength,deadline,now):
 primary=[words[0],words[1]];backup=[words[2],words[3]]
 if F(now)>=F(primary[1]):
  primary=backup if F(now)<F(backup[1])else[0,0];backup=[0,0]
 incoming=[strength,deadline]
 if F(now)>=F(primary[1])or F(strength)>F(primary[0])or(F(strength)==F(primary[0])and F(deadline)>F(primary[1])):winner,loser=incoming,primary
 else:winner,loser=primary,incoming
 chosen=None
 for candidate in(backup,loser):
  value,expiry=candidate
  if not(F(value)>0 and F(now)<F(expiry)and F(winner[1])<F(expiry)):continue
  if chosen is None or F(value)>F(chosen[0])or(F(value)==F(chosen[0])and F(expiry)>F(chosen[1])):chosen=candidate
 return[winner[0],winner[1],*(chosen if chosen is not None else[0,0])]

def effect2244(rows,guid,strength,duration,now,spell,packets,counts):
 for row in rows:
  if Q(row,112)!=guid or u(row)==1:continue
  words=merge21455([u(row,o)for o in(128,132,136,140)],strength,add(now,duration),now)
  for o,v in zip((128,132,136,140),words):put(row,o,v)
  if F(words[0])==F(strength)and F(words[1])==F(add(now,duration)):put(row,364,duration);counts['duration364_primary_accepts']+=1
  previous=u(row,360)
  if spell and previous!=spell:
   put(row,360,spell)
   for value,adding in(([previous,False],)if previous else())+([spell,True],):
    slots=[u(row,168+4*i)for i in range(16)]
    if adding:
     if value in slots or 0 not in slots:continue
     index=slots.index(0);slots[index]=value
    else:
     if value not in slots:continue
     index=slots.index(value);slots[index]=0
    assert u(row,240)==0
    put(row,168+4*index,slots[index]);flags=sum(2<<(4*i)for i,v in enumerate(slots[(index//8)*8:(index//8+1)*8])if v)
    fields=[(79+index,slots[index]),(99+index//8,flags),(121+index//4,0)];packets.append(dict(opcode=169,payload_hex=aura_packet(guid,fields)));counts['actual_Aura169_events']+=1;counts['actual_Aura169_bytes']+=len(bytes.fromhex(packets[-1]['payload_hex']))
  counts['effect2244_target_applications']+=1;break


def strict(a,b,path,counts,poison):
 if a is None:
  assert len(path)>=3 and path[-3]=='unit_cells'and type(b)is int and b==poison;counts['unknown_physical_bytes']+=1;counts['nonzero_unknown_original_bytes']+=bool(b);return
 assert type(a)is type(b),(path,type(a),type(b))
 if isinstance(a,dict):
  assert set(a)==set(b),(path,set(a),set(b))
  for k in a:strict(a[k],b[k],path+(k,),counts,poison)
 elif isinstance(a,list):
  assert len(a)==len(b),(path,len(a),len(b))
  for i,(x,y)in enumerate(zip(a,b)):strict(x,y,path+(i,),counts,poison)
 else:assert a==b,(path,a,b);counts['known_values']+=1

def targets(rows,xy,radius,now):
 found=[]
 for index,row in enumerate(rows):
  if u(row):continue
  duration=u(row,344);position=[u(row,328),u(row,332)]
  if F(duration)>0:
   t=divide(sub(now,u(row,340)),duration);t=0 if F(t)<0 else B(1)if F(t)>1 else t
   position=[add(u(row,a),mul(sub(u(row,b),u(row,a)),t))for a,b in((316,328),(320,332))]
  dx,dy=sub(position[0],xy[0]),sub(position[1],xy[1]);distance=add(mul(dx,dx),mul(dy,dy))
  if F(distance)<=F(mul(radius,radius)):found.append((distance,index,Q(row,112)))
 found.sort(key=lambda x:F(x[0]));return[(index,guid)for _,index,guid in found]

def closure(edges):
 todo=['reconstruction/core_spec/demo_shout135.py'];seen=set()
 while todo:
  n=todo.pop()
  if n in seen:continue
  seen.add(n);todo.extend(b for a,b in edges if a==n and b.startswith('reconstruction/'))
 return sorted(seen)

def review_case(c,w,a,label,counts,sem,read):
 assert c['id']==a['id']==label['id']and len(c['ops'])==len(w)==len(a['stages'])
 if c['mode']=='merge':
  words=c['words']
  for op,want,raw in zip(c['ops'],w,a['stages']):
   assert bytes.fromhex(raw['before16_hex'])==struct.pack('<4I',*words);words=merge21455(words,op['strength_bits'],op['deadline_bits'],op['now_bits'])
   assert words==want['words']==raw['words']and bytes.fromhex(raw['after16_hex'])==struct.pack('<4I',*words)
   strict(want,dict(words=raw['words']),(),counts,0);sem['helper21455_calls']+=1;sem['helper_words_bitwise']+=4
  return
 s=c['input'];rows=[row.copy()for row in c['units424']];owned=list(struct.unpack('<20I',bytes.fromhex(c['owned_hex'])));basic=list(struct.unpack('<20I',bytes.fromhex(c['basic_hex'])));state_rng=tuple(s['rng_words']);total=0.;hp=s['current_hp_bits'];player_fields={};ledgers=[[],[],[]];packets=[];timer=c['timer1628_bits'];assert timer==0x7f800000
 definition=bytes.fromhex(c['definition']['definition_hex']);assert definition==read(c['definition']['pointer'],88)and definition[84]==2 and definition[85]==0 and u(definition)==11 and u(definition,44)==1160
 cls=c['class_byte'];class_pointer=u(read(1595888+4*((cls-2)&255),4))if((cls-2)&255)<=9 else 5462608;leech=u(read(class_pointer+80,4))
 for op,want,raw,meta in zip(c['ops'],w,a['stages'],label['operations']):
  assert op['kind']==raw['kind'];now=op['now_bits'];cast=op['kind']=='cast';success=None
  if op['kind']=='owned':
   timer=sub(timer,op['dt_bits']);remaining=sub(owned[2],op['dt_bits']);cast=not F(remaining)>0;sem['full1076_calls']+=1
  elif op['kind']=='effect':sem['full2244_calls']+=1;effect2244(rows,int(op['target_guid']),op['strength_bits'],op['duration_bits'],now,op['spell_id'],packets,sem)
  else:assert op['kind']=='cast';sem['full922_calls']+=1
  if cast:
   sem['direct_or_inner922_attempts']+=1
   for ledger in ledgers:
    if 1160 not in ledger:ledger.append(1160)
   radius=mul(mul(u(definition,60),mul(owned[6],owned[16])),s['area_multiplier_bits']);assert F(radius)<=70
   selected=targets(rows,s['player_xy'],radius,now);success=int(bool(selected))
   if op['kind']=='cast':assert[str(guid)for _,guid in selected]==[str(guid)for guid in meta['selected']],(c['id'],op,selected,meta['selected'])
   base=mul(u(definition,48),0x3fb33333);base=mul(base,owned[3]);base=mul(base,owned[13]);base=mul(base,0x3f000000);base=mul(s['damage_multiplier_bits'],add(base,mul(s['max_hp_bits'],owned[18])if F(u(definition,48))>0 else 0))
   strength=mul(0x3eb33333,owned[19]);strength=strength if F(strength)<F(0x3f666666)else 0x3f666666;duration=mul(B(6),owned[17])
   for index,guid in selected:
    value,state_rng=rng(state_rng);sample=mul(B(float(value>>8)),0x33800000);damage=mul(base,s['critical_multiplier_bits'])if F(s['critical_chance_bits'])>F(sample)else base;sem['critical_draws']+=1
    row=rows[index]
    if s['phase']==1:
     damage=damage if F(damage)>1 else B(1);old=u(row,288);put(row,288,sub(old,damage));assert F(u(row,288))>0;total+=min(max(F(old),0),F(damage));sem['accepted_nonlethal_hits']+=1
     if F(leech)>0:
      hp=add(hp,mul(damage,leech));hp=hp if F(hp)<F(s['max_hp_bits'])else s['max_hp_bits'];player_fields.update({'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(s['max_hp_bits'])))})
    else:sem['phase_guarded_damage_still_effect']+=1
    effect2244(rows,guid,strength,duration,now,1160,packets,sem)
  if op['kind']=='owned':
   if cast:
    remaining=mul(mul(mul(mul(u(definition,52),0x3fb33333),owned[4]),owned[14]),s['cooldown_multiplier_bits'])if success else 0x3e4ccccd
    if success and not F(remaining)>.25:remaining=B(.25)
   owned[2]=remaining;basic[2]=sub(basic[2],op['dt_bits'])
  owners=[dict(guid=str(Q(row,112)),marker=u(row),words128_140=[u(row,o)for o in(128,132,136,140)],spell360=u(row,360),duration364_bits=u(row,364),aura_slots168=[u(row,168+i*4)for i in range(16)],ability_count240=u(row,240))for row in rows]
  projection=dict(hp_bits=[u(row,288)for row in rows],markers=[u(row)for row in rows],rng_words=list(state_rng),accounted_total_hex=struct.pack('>d',total).hex(),attempted_spell_sets=ledgers,owned_words=owned,basic_words=basic,current_hp_bits=hp,player_fields=player_fields,timer1628_bits=timer,debuffs=owners,aura_packets=packets)
  prediction=dict(kind=op['kind'],projection=projection,unit_cells=rows)
  if op['kind']=='cast':prediction['success']=success
  assert prediction==want,(c['id'],op,'independent reconstruction differs from expected',[(k,prediction[k],want.get(k))for k in prediction if prediction[k]!=want.get(k)][:1])
  observed={k:raw[k]for k in want if k!='unit_cells'};observed['unit_cells']=[list(bytes.fromhex(x))for x in raw['raw_units424_hex']];strict(want,observed,(),counts,c['unknown_poison'])
  g=bytes.fromhex(raw['Game_after8192_hex']);assert len(g)==8192 and g[2587]==s['phase']and list(struct.unpack_from('<4I',g,1720))==projection['rng_words']and g[984:992][::-1].hex()==projection['accounted_total_hex']and u(g,1440)==hp and u(g,1628)==timer
  assert raw['projection']['aura_packets']==[p for p in raw['all_packets']if p['opcode']==169 and p['payload_hex']in{x['payload_hex']for x in packets}]
  sem['cumulative_Aura169_packets']+=len(packets);sem['cumulative_Aura169_bytes']+=sum(len(bytes.fromhex(p['payload_hex']))for p in packets);sem['all_packet_observations']+=len(raw['all_packets'])

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path);args=p.parse_args();began=time.monotonic();out=args.output.resolve()if args.output else ROOT/'evidence'/datetime.now(timezone.utc).strftime('demo-shout135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();report=json.loads((RUN/'comparison.json').read_text());assert sha(RUN/'comparison.json')=='ab48f8c30461793af8f0b93579b53bc8f9abc30671f85a8c902575a58e9dbe95'and report['comparison_complete']and report['differences']==0 and report['source_sha256_before']==report['source_sha256_after'];source=RUN/'source-snapshot';files=report['source_sha256_before'];assert len(files)==27
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 edges=source_edges(source,files);production=sorted(n for n in files if n.startswith('reconstruction/'));assert production==closure(edges)and len(production)==22
 for n in production:
  for node in ast.walk(ast.parse((source/n).read_text())):
   if isinstance(node,ast.Call):
    fn=node.func;name=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else'';assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__')
 for n,h in report['artifacts'].items():assert sha(RUN/n)==h,n
 for n,h in report['external_independent_model_fragments'].items():assert sha(Path(n))==h,n
 original=ORIGINAL.read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(original).hexdigest()==manifest['original_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'and hashlib.sha256(changed).hexdigest()==manifest['module_sha256'];a,b=sections(original),sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]and all(original[x:y]==changed[v:z]for(k,x,_,y),(_,v,_,z)in zip(a,b)if k!=7)
 assert exports(changed)==exports(original)+[['demo135_cast',0,922],['demo135_owned',0,1076],['demo135_effect',0,2244],['demo135_merge',0,21455],['demo135_stack0',3,0]]
 wanted_ids=[x['index']for x in manifest['static_functions']];ids=identities(original,wanted_ids);static=[];texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=on')
  for entry in manifest['static_functions']:
   index=entry['index'];identity=ids[index];assert identity['body_sha256']==entry['body_sha256'];lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone();assert(bs,be)==(identity['body_start'],identity['body_end'])and hi-lo<=1048576;wat.seek(lo);text=wat.read(hi-lo);assert text==(RUN/f'demo-{index}.wat').read_bytes()and hashlib.sha256(text).hexdigest()==entry['wat_sha256'];texts[index]=text.decode();static.append(dict(**identity,wat_start=lo,wat_end=hi,wat_sha256=entry['wat_sha256']))
 assert ids[21455]['signature']==['7f7d7d7d','']and ids[2244]['signature']==['7f7e7f7d7f','']and ids[922]['signature']==['7f7f','7f']and ids[1076]['signature']==['7f7d','']
 read=static_reader(original);defs=manifest['definitions'];assert read(5467868,88).hex()==defs['demo_shout']['definition_hex']and read(5473324,88).hex()==defs['fireball']['definition_hex']
 for cls,value in defs['class_leech_bits'].items():
  cls=int(cls);pointer=u(read(1595888+4*((cls-2)&255),4))if((cls-2)&255)<=9 else 5462608;assert u(read(pointer+80,4))==value
 assert texts[2244].index('call 21455')<texts[2244].index('i32.const 364')and'call 4543'in texts[2244]and'i32.const 79'in texts[4543]and'i32.const 121'in texts[4543]
 inputs=[json.loads(x)for x in(RUN/'input.jsonl').read_text().splitlines()];wanted=json.loads((RUN/'expected.json').read_text());labels=json.loads((RUN/'labels.json').read_text());actual=[json.loads(x)for x in(RUN/'results.jsonl').read_text().splitlines()];assert len(inputs)==len(wanted)==len(labels)==len(actual)==180;counts=Counter();sem=Counter()
 for c,w,actual_row,label in zip(inputs,wanted,actual,labels):
  assert time.monotonic()-began<60;review_case(c,w,actual_row,label,counts,sem,read)
 assert{k:counts[k]for k in report['comparison']}==report['comparison']and sem['helper21455_calls']==134 and sem['full2244_calls']==20 and sem['full922_calls']==32 and sem['full1076_calls']==21 and sem['helper_words_bitwise']==536
 assert sem['actual_Aura169_events']==119 and sem['actual_Aura169_bytes']==4403 and sem['cumulative_Aura169_packets']==153 and sem['cumulative_Aura169_bytes']==5661
 runtime=report['runtime'];assert runtime==json.loads((RUN/'runtime.json').read_text())and runtime['calls']=={'922':32,'1076':21,'2244':20,'21455':134,'91941':328}and runtime['cases']==runtime['completed_cases']==runtime['fresh_instances']==180 and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['maximum_memory_bytes']<=runtime['memory_cap_bytes']==33554432 and runtime['stack_all_restored']and len(runtime['stack_checks'])==535 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])and runtime['failure']is None
 assert all(runtime[k]is False for k in('application_start_called','network_used','user_saves_accessed','original_memory_snapshot_read'))
 prepared=json.loads((RUN/'prepared.json').read_text());checker=(source/'scripts/check_demo_shout135.py').read_text();assert checker.index('cases,expected,labels=corpus(')<checker.index('child=subprocess.Popen(')and prepared['expected_before_original']and prepared['source_sha256']==files and prepared['artifacts']==report['artifacts']and prepared['external_independent_model_fragments']==report['external_independent_model_fragments']
 terminal=report['process'];assert terminal==json.loads((RUN/'process-terminal.json').read_text())and terminal['exit_code']==0 and terminal['error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
 assert(RUN/'results.jsonl').stat().st_size==runtime['output_bytes']<=33554432 and max(len(x)for x in(RUN/'results.jsonl').read_bytes().splitlines(keepends=True))<=2097152 and not(RUN/'stderr.log').stat().st_size and json.loads((RUN/'differences.json').read_text())==[]
 assert sha(Path(prepared['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 (out/'static-proofs.json').write_text(json.dumps(dict(functions=static,static_memory=read.proofs,local_source_import_edges=edges,helper_scope='134 direct21455 calls; all536 words bitwise, no NaN classification relaxation in auditor',class_leech_scope='Original class+80 table identity; fixture class1 accepted-hit HP/22/28 independently replayed'),ensure_ascii=False,indent=2)+'\n')
 result=dict(status='passed_scoped_read_only_review',version='0.135.1',actual_build='90898d5e3',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),reviewer_script_sha256=sha(Path(__file__)),source_files=27,production_files=22,local_dependency_edges=len(edges),current_and_frozen_sources_verified=True,nonexport_sections_and_all_callees_unchanged=True,static_proofs_sha256=sha(out/'static-proofs.json'),cases=180,stages=207,comparison_counts=dict(counts),independent_semantic_checks=dict(sem),all21455_outputs_bitwise_including_NaN_signed0=True,full424B_physical_unknowns_preserved_as_original_input_poison=True,independent_full2244_and922_and1076_projection_rebuilt=True,all119_actual_Aura169_payloads_and153_cumulative_observations_independently_compared=True,three_spell_attempt_ledgers_owned_basic_cooldown_HP_and_class_leech_replayed=True,original_or_model_or_checker_executed_by_reviewer=False,new_original_cases=0,full880_frames=0,natural665_original_frames=0,native_Windows_execution=False,process=terminal,pending=report['pending'],scope=report['scope'],external665_fragment_scope='Copied selected-owned80/derived23/HP/RNG/now from an independent665-frame model run; manually relocated3NPCs and held class prelude, not natural665 original execution.',elapsed_seconds=time.monotonic()-began)
 result['audited_artifact_sha256']={p.name:sha(p)for p in RUN.iterdir()if p.is_file()}
 result['artifact_hash_scope']='Original comparison seals prepared inputs/module; this read-only review separately binds raw results/runtime/terminal SHA at review time, without modifying or backdating the original receipt.'
 assert result['elapsed_seconds']<60;(out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],semantic=dict(sem))),flush=True)
if __name__=='__main__':main()
