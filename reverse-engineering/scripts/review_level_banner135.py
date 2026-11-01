#!/usr/bin/env python3
"""Read-only93-case level-banner evidence review; no model/oracle/checker runs."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
from decimal import Decimal,ROUND_HALF_EVEN,localcontext
import ast,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
from review_battle_shout135 import F,B,add,sub,mul
from review_resource_consumer137 import source_edges,identities
from review_resource_spawn135 import advance
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/level-banner0135-oracle-20261101T194550.118916Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
MASK=0xffffffff
def sha(p):
 with Path(p).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def u(b,o=0):return struct.unpack_from('<I',b,o)[0]
def div(a,b):return B(F(a)/F(b))
def low(a,b):return a if F(a)<F(b)else b
def high(a,b):return a if F(a)>F(b)else b
def round85719(w):
 r=add(w,(w&0x80000000)|0x3effffff);e=(r>>23)&255
 if e<=149:r&=0x80000000 if e<127 else((-8388608)>>((e-127)&31))&MASK
 return max(0,min(MASK,int(F(r))))
def threshold(level):
 n=B(float(level-bool(level)));return round85719(add(add(mul(n,B(4)),B(5)),mul(mul(n,0x3eb33333),n)))
def fixed(word,precision):
 assert math.isfinite(F(word))
 with localcontext()as context:
  context.prec=128;v=Decimal.from_float(F(word));v=v.quantize(Decimal(1).scaleb(-precision),rounding=ROUND_HALF_EVEN)
  return('-'if v.is_signed()else'+')+format(abs(v),'.'+str(precision)+'f')
def packet(text):
 encoded=text.encode('utf8');assert b'\0'not in encoded;return dict(opcode=150,payload_hex=(struct.pack('<BIQI',10,0,0,len(encoded)+1)+encoded+b'\0\0').hex())
def decode_packet(p):
 assert p['opcode']==150;raw=bytes.fromhex(p['payload_hex']);assert raw[:13]==b'\x0a'+bytes(12)and len(raw)==u(raw,13)+18 and raw[-2:]==b'\0\0';return raw[17:-2].decode('utf8')
def equal(want,got,counts):
 assert want is not None and type(want)is type(got),(type(want),type(got))
 if isinstance(want,dict):
  assert set(want)==set(got)
  for k in want:equal(want[k],got[k],counts)
 elif isinstance(want,list):
  assert len(want)==len(got)
  for a,b in zip(want,got):equal(a,b,counts)
 else:assert want==got,(want,got);counts['strict_known_values']+=1

def empty_stats(level,stats,read):
 """Independent finite empty-source1512 slice, static class/race records."""
 cls,race=stats['class_byte'],stats['race_byte'];cp=u(read(1595888+4*((cls-2)&255),4))if((cls-2)&255)<=9 else 5462608;rp=u(read(1595728+4*((race-2)&255),4))if((race-2)&255)<=6 else 5459304
 hp,armor=struct.unpack('<2I',read(cp+72,8));rpv,rn=struct.unpack('<2I',read(rp+16,8));assert rn<=16
 values={0:0x3f800000,1:add(mul(sub(B(float(level)),B(1)),0x3cf5c28f),B(1)),2:0,3:B(1),4:0x3d4ccccd,5:armor,6:add(mul(sub(B(float(level)),B(1)),0x3da3d70a),0x3f4ccccd),7:B(9),8:B(1),9:B(1),10:0,11:0}
 for i in range(rn):
  tag,v=struct.unpack('<2I',read(rpv+i*8,8));assert tag in values
  if tag==7:values[7]=mul(values[7],add(v,B(1)))
  else:values[tag]=add(values[tag],v)
 n=sub(B(float(level)),B(1));base=add(hp,mul(n,B(9)));maximum=mul(add(base,0),values[0]);armor=low(values[5],0x3f19999a);speed=low(values[3],0x400ccccd);critical=low(values[4],B(1))
 derived={1536:maximum,1540:add(add(div(mul(0,armor),B(10)),mul(0,high(sub(values[5],0x3f19999a),0))),values[1]),1544:div(B(1),add(values[2],B(1))),1548:critical,1552:add(B(2),add(values[4],B(-1)))if F(values[4])>1 else B(2),1556:speed,1560:values[7],1564:values[8],1568:armor,1572:0x3f19999a,1576:add(mul(0,maximum),values[6]),1580:B(1),1584:add(values[10],stats['conditional268_bits'])if stats['flag2574']else values[10],1588:values[9],1592:0,1596:0,1600:values[11],1604:0,1608:min(level//15,3),1612:0,1616:add(div(maximum,high(base,B(1))),B(-1)),1620:0,1624:0}
 current=low(add(sub(maximum,stats['old_max_hp_bits']),stats['current_hp_bits'])if F(sub(maximum,stats['old_max_hp_bits']))>0 else stats['current_hp_bits'],maximum)
 pool=high(low(stats['pool1536_bits'],stats['pool1532_bits']),0);excess=high(sub(pool,maximum),0);aux={1444:stats['pool1532_bits'],1448:sub(pool,excess),1348:stats['conditional1348_bits'],768:stats['pool768_bits']}
 if F(excess)>0:
  aux[1444]=high(sub(aux[1444],excess),0)
  if stats['conditional1344_id']==11426:aux[1348]=low(aux[1348],aux[1448])
  aux[768]=low(aux[768],aux[1444])
 new_speed=mul(speed,B(7));new_speed=new_speed if F(sub(new_speed,stats['previous_speed_bits'])&0x7fffffff)>F(0x3c23d70a)else stats['previous_speed_bits']
 return{str(k):v for k,v in derived.items()},current,aux,new_speed

def raw_binding(row):
 g=bytes.fromhex(row['Game_after8192_hex']);assert len(g)==8192;p=row['projection'];assert p['progression']==dict(level=u(g,1432),xp=u(g,1436),pending_upgrades=u(g,2376))
 assert p['derived_bits']=={str(o):u(g,o)for o in range(1536,1628,4)}and p['current_hp_bits']==u(g,1440)and p['speed_bits']==u(g,1648)and p['auxiliary_bits']=={str(o):u(g,o)for o in(1444,1448,1348,768,756)}and p['rng_words']==list(struct.unpack_from('<4I',g,1720))
 assert p['phase2587']==g[2587]and p['selection_kind2585']==g[2585]and p['generation_counter2400']==u(g,2400)
 assert u(g,1888)==len(row['all_packet_opcodes'])and row['all_packet_opcodes'].count(150)==len(row['packets150'])and u(g,1880)>=u(g,1888)

def review_case(c,w,observed,label,templates,read,counts,sem):
 s=c['input'];assert c['id']==label['id']and len(c['amounts'])==len(w)==len(observed);assert all(not v for v in s['sources'].values())and not s['player_fields']and not s['choice_inputs']['blocked_ids']and not s['choice_inputs']['banished_keys']
 owned=[]
 for record in s['choice_inputs']['owned']:
  raw=bytes.fromhex(record['record_hex']);assert len(raw)==80;owned.append(read(u(raw)+84,1)[0])
 locale=c['locale'];assert locale in('en','zh');index=c['locale_override_index']if c['locale_override_enabled']else c['locale_default_index'];assert index=={'en':0,'zh':11}[locale]
 stats=dict(s['stats']);derived=dict(s['derived_bits']);progress=dict(s['progression']);fields={};phase=s['phase2587'];kind=s['selection_kind2585'];generation=s['generation_counter2400'];rng=s['rng_words'];events=iter(label['independent_per_level_banner_events']);packets=[];initialized=False;speed=stats['previous_speed_bits'];hp=stats['current_hp_bits'];aux={1444:stats['pool1532_bits'],1448:stats['pool1536_bits'],1348:stats['conditional1348_bits'],768:stats['pool768_bits'],756:s['pool756_bits']}
 assert empty_stats(progress['level'],stats,read)[0]==derived,'Initial empty-source23-word fixture does not match original static records'
 for step,(amount,want,row)in enumerate(zip(c['amounts'],w,observed)):
  assert(row['id'],row['step'])==(c['id'],step);raw_binding(row);before=bytes.fromhex(row['Game_before8192_hex']);assert len(before)==8192
  assert dict(level=u(before,1432),xp=u(before,1436),pending_upgrades=u(before,2376))==progress and {str(o):u(before,o)for o in range(1536,1628,4)}==derived and u(before,1440)==hp and u(before,1648)==speed
  assert row['locale_once_before']==(3 if initialized else 0);oldlevel=progress['level'];progress['xp']=(progress['xp']+amount)&MASK;prior=len(packets)
  while progress['level']<120 and progress['xp']>=threshold(progress['level']):
   spent=threshold(progress['level']);progress['xp']=(progress['xp']-spent)&MASK;progress['level']+=1;progress['pending_upgrades']=(progress['pending_upgrades']+1)&MASK;event=next(events);assert event['level']==progress['level']
   old=dict(derived);derived,hp,update,speed=empty_stats(progress['level'],stats,read);assert dict(event['before_derived'])=={int(k):v for k,v in old.items()}and dict(event['after_derived'])=={int(k):v for k,v in derived.items()}
   damage=mul(sub(derived['1540'],old['1540']),B(100));health=sub(derived['1536'],old['1536']);regen=sub(derived['1576'],old['1576']);template,stacktemplate=templates[locale]
   text=template.replace('{damage}',fixed(damage,0)).replace('{health}',fixed(health,0)).replace('{regen}',fixed(regen,2));texts=[text];sem['growth_events']+=1;sem['distinct_growth_texts'].add(text)
   if 6 in owned and derived['1608']>old['1608']:texts.append(stacktemplate.replace('{n}',str(min(derived['1608'],3)+1)));sem['DOT_events']+=1;sem['DOT_transition_levels'].add(progress['level'])
   assert texts==event['texts'];packets.extend(packet(t)for t in texts)
   request=mul(derived['1536'],0x3e4ccccd);request=mul(request,0x3f000000 if s['heal_gate387']>4 else B(1));hp=low(add(hp,request),derived['1536']);aux.update(update)
   stats.update(old_max_hp_bits=derived['1536'],current_hp_bits=hp,previous_speed_bits=speed,pool1532_bits=aux[1444],pool1536_bits=aux[1448],conditional1348_bits=aux[1348],pool768_bits=aux[768]);fields.update({'34':progress['level'],'22':max(0,math.ceil(F(hp))),'28':max(0,math.ceil(F(derived['1536']))),'1109':mul(derived['1548'],B(100))});initialized=True
  gained=progress['level']-oldlevel;fields.update({'716':progress['xp'],'717':threshold(progress['level'])});sem['multilevel_calls']+=gained>1;sem['no_level_calls']+=gained==0
  eligible=progress['pending_upgrades']!=0 and phase==1 and not(s['flags2576']&1)and(s['gate2572']!=1 or bool(s['flags2573']&1))
  if eligible:
   assert s['stats']['flag2574']==1;phase=2;kind=0;generation=(generation+1)&MASK;target=want['projection']['rng_words'];matches=[n for n in range(1,513)if list(advance(tuple(rng),n))==target];assert len(matches)==1;rng=target;sem['eligible_choice_calls']+=1;sem['choice_rng_draws_sequence_verified']+=matches[0]
  else:assert want['projection']['rng_words']==rng
  prediction=dict(progression=dict(progress),derived_bits=derived,current_hp_bits=hp,auxiliary_bits={str(k):v for k,v in aux.items()},speed_bits=speed,player_fields=dict(fields),rng_words=rng,phase2587=phase,selection_kind2585=kind,generation_counter2400=generation)
  assert{key:want['projection'][key]for key in prediction}==prediction,(c['id'],step,'Independent finite numeric replay differs')
  assert want['packets150']==packets and want['locale_once_before']==row['locale_once_before']and want['locale_once_after']==row['locale_once_after']==(3 if initialized else 0)
  equal(want,{key:row[key]for key in want},counts)
  assert all(decode_packet(p)==decode_packet(q)for p,q in zip(packets,row['packets150']))
  counts['entry_calls']+=1;counts['cumulative150_packets']+=len(packets);counts['cumulative150_bytes']+=sum(len(bytes.fromhex(p['payload_hex']))for p in packets);sem['new_packets']+=len(packets)-prior
  if s['flags2576']and gained:sem['nonzero_choice_flags_still_growth_calls']+=1
  if oldlevel==120:assert gained==0 and len(packets)==prior;sem['max120_calls']+=1
 assert next(events,None)is None;sem['locale_initialized_cases'if initialized else'locale_uninitialized_cases']+=1;sem['locale_'+locale+'_cases']+=1

def main():
 began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('level-banner135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir();report=json.loads((RUN/'comparison.json').read_text());assert sha(RUN/'comparison.json')=='4cd02d8adf74d4129e58040b3a81bd2dac1b96e2eed8ff4bb5c1e67a6561a4e3'and report['comparison_complete']and report['differences']==0 and report['source_sha256_before']==report['source_sha256_after'];source=RUN/'source-snapshot';files=report['source_sha256_before'];assert len(files)==20
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 assert files['reconstruction/core_spec/level_banner135.py']=='5df523046bf3c9926f4161130256195006cd40dc838bd709a51057c2fea7a701';edges=source_edges(source,files)
 helper=ast.parse((source/'scripts/check_level_cycle135.py').read_text());readset=ast.literal_eval(next(n.value for n in helper.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SOURCE_FILES'for t in n.targets)));assert set(readset)<=set(files)
 reachable={'scripts/check_level_banner135.py','scripts/run_level_banner135_oracle.mjs'}|set(readset)
 while True:
  expanded=reachable|{b for a,b in edges if a in reachable}
  if expanded==reachable:break
  reachable=expanded
 assert reachable==set(files);production=[n for n in files if n.startswith('reconstruction/')];assert len(production)==12
 for n in production:
  for node in ast.walk(ast.parse((source/n).read_text())):
   if isinstance(node,ast.Call):
    fn=node.func;name=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else'';assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__')
 for n,h in report['artifacts_sha256'].items():assert sha(RUN/n)==h
 raw=ORIGINAL.read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());changed=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(raw).hexdigest()==manifest['original_wasm_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'and hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
 a,b=sections(raw),sections(changed);assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]and all(raw[x:y]==changed[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7);assert exports(changed)==exports(raw)+[['research135_gain_experience',0,4630],['research135_level_banner_stack0',3,0]]
 trace=json.loads((RUN/'level-banner135-static.json').read_text());ids=identities(raw,tuple(r['idx']for r in trace['functions']));assert ids[4630]['signature']==['7f7f','']and ids[4630]['body_sha256']==manifest['entry']['body_sha256'];static=[];texts={}
 with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
  db.execute('pragma query_only=ON')
  for entry in trace['functions']:
   index=entry['idx'];identity=ids[index];lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(index,)).fetchone();assert(bs,be)==(identity['body_start'],identity['body_end'])and hi-lo<=524288;wat.seek(lo);text=wat.read(hi-lo);assert text==(RUN/f'level-banner-{index}.wat').read_bytes()and hashlib.sha256(text).hexdigest()==entry['wat_sha256']and identity['body_sha256']==entry['body_sha256'];texts[index]=text.decode();static.append(dict(**identity,wat_start=lo,wat_end=hi,wat_sha256=entry['wat_sha256']))
 read=static_reader(raw);assert read(1588021,6).hex()=='c12000207000'and read(1588033,8).hex()=='c520002070020000'and read(14384320,28)==bytes(28);growth=read(1587933,88).decode();stacks=read(1588041,62).decode();templates={}
 for index,code in((0,'en'),(11,'zh')):
  row=read(5212184+28*index,28);values=struct.unpack('<7I',row);assert read(values[0],values[1]).decode()==code;dictionary=json.loads(read(values[4],values[5]));templates[code]=(dictionary.get(growth,growth),dictionary.get(stacks,stacks));entry=next(x for x in trace['declared_languages']if x['index']==index);assert list(templates[code])==[entry['growth'],entry['stacks']]and hashlib.sha256(read(values[4],values[5])).hexdigest()==entry['dictionary_sha256']
 assert texts[4630].index('call 1512')<texts[4630].index('call 28964')<texts[4630].index('call 10847')<texts[4630].index('i32.load8_u offset=2587')<texts[4630].index('call 2159')and 'i32.load8_u offset=84'in texts[4630]and'i32.load offset=1608'in texts[4630]
 assert 'call 82070'in texts[19964]and'i32.const 14384344'in texts[19964]and'i32.const 14384328'in texts[19964]
 inputs=[json.loads(x)for x in(RUN/'input.jsonl').read_text().splitlines()];wanted=json.loads((RUN/'expected.json').read_text());labels=json.loads((RUN/'labels.json').read_text());actual=[json.loads(x)for x in(RUN/'results.jsonl').read_text().splitlines()];assert len(inputs)==len(wanted)==len(labels)==93 and len(actual)==110 and[(r['id'],r['step'])for r in actual]==[(c['id'],i)for c in inputs for i in range(len(c['amounts']))]
 counts=Counter();sem=Counter();sem['distinct_growth_texts']=set();sem['DOT_transition_levels']=set()
 for c,w,label in zip(inputs,wanted,labels):
  assert time.monotonic()-began<60;review_case(c,w,[a for a in actual if a['id']==c['id']],label,templates,read,counts,sem)
 assert counts['cumulative150_packets']==report['cumulative150_packets_compared']==186 and counts['cumulative150_bytes']==report['cumulative150_bytes_compared']==16528 and sem['growth_events']==report['independent_per_level_transitions']==146 and sem['DOT_events']==26 and sem['new_packets']==172 and sem['DOT_transition_levels']=={15,30,45}
 checker=(source/'scripts/check_level_banner135.py').read_text();runner=(source/'scripts/run_level_banner135_oracle.mjs').read_text();core=(source/'reconstruction/core_spec/level_banner135.py').read_text();main_source=checker.split('def main():')[1];assert main_source.index('cases = corpus(')<main_source.index('child = subprocess.Popen(')and'start_new_session=True'in main_source and'child.wait(timeout=60)'in main_source and'finally:'in main_source
 assert 'u32(14384328,c.locale_default_index)'in runner and'u32(14384320,c.locale_override_enabled)'in runner and'u32(14384324,c.locale_override_index)'in runner and 'u32(14384344'not in runner and'u8(14384344'not in runner and'Once must be fresh original0'in runner
 assert 'Nonfinite Rust float presentation not restored'in core and'Only explicit recovered en/zh locale admitted'in core and'Single actual4630 level transition required'in core
 runtime=report['runtime'];assert runtime==json.loads((RUN/'level-banner135-runtime.json').read_text())and runtime['case_count']==runtime['fresh_instances']==93 and runtime['entry_calls']==110 and runtime['original_entry']==4630 and runtime['actual_host_calls']==0 and runtime['denied_function_imports']==878 and runtime['memory_page_cap']==512 and runtime['maximum_memory_bytes']<=33554432 and runtime['stack_all_restored']and len(runtime['stack_checks'])==281 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
 assert all(runtime[k]is False for k in('locale_Once_injected','application_start_called','full_game_started','network_used','user_saves_accessed'))and runtime['failure']is None
 prepared=json.loads((RUN/'prepared.json').read_text());owned=json.loads((RUN/'owned-process.json').read_text());terminal=json.loads((RUN/'process-terminal.json').read_text());assert prepared['source_sha256']==files and prepared['artifacts_sha256']==report['artifacts_sha256']and prepared['expected_before_original']and prepared['command']==owned['command']and prepared['deadline_seconds']==owned['deadline_seconds']==60 and '--max-old-space-size=512'in prepared['command']and'--wasm-max-mem-pages=512'in prepared['command']
 assert sha(Path(prepared['command'][0]))==prepared['node_sha256']=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'and terminal==report['process']and terminal['exit_code']==0 and terminal['error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
 assert (RUN/'results.jsonl').stat().st_size==runtime['output_bytes']<=16777216 and max(len(x)for x in(RUN/'results.jsonl').read_bytes().splitlines(keepends=True))<=2097152 and not(RUN/'stderr.log').stat().st_size and json.loads((RUN/'differences.json').read_text())==[]
 correction=json.loads((RUN/'source-closure-correction.json').read_text());old=ROOT/correction['old_comparison'];assert sha(old)==correction['old_sha256']and correction['final_sha256']==sha(RUN/'comparison.json')
 for n in correction['byte_identical']:assert sha(old.parent/n)==sha(RUN/n)
 assert set(correction['added_source_files'])=={'scripts/full135_host.mjs','scripts/run_level_cycle135_oracle.mjs'}and correction['old_receipt_modified']is False and correction['cases_not_added']is True
 proofs=dict(functions=static,static_memory_intervals=read.proofs,ordering='4630 old derived capture ->1512 ->growth28964 ->optionalDOT28964 ->heal10847 ->nextlevel loop; terminalchoice2159 after loop',source_import_edges=edges,import_time_hash_readset=list(readset));(out/'static-proofs.json').write_text(json.dumps(proofs,ensure_ascii=False,indent=2)+'\n')
 for n,h in files.items():assert sha(source/n)==h==sha(ROOT/n),n
 sem={k:sorted(v)if isinstance(v,set)else v for k,v in sem.items()};result=dict(status='passed_scoped_read_only_review',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),reviewer_script_sha256=sha(Path(__file__)),source_files=20,production_files=12,local_source_edges=len(edges),import_time_hash_readset_frozen=True,nonexecuted_old_JS_hash_inputs=correction['added_source_files'],source_current_and_frozen_SHA_verified_at_both_boundaries=True,all_original_nonexport_sections_and_callees_unchanged=True,static_proofs_sha256=sha(out/'static-proofs.json'),cases=93,entry_calls=110,comparison_counts=dict(counts),independent_semantic_checks=sem,independent_empty_source_numeric_replay='All23 derived words from original static class/race data, XP wrap/thresholds/120cap, HP/heal/aux/speed and known keyed state recomputed. Candidates remain strict frozen expected/original metadata; eligible choice RNG sequence additionally checked.',independent_decimal_formatting='Exact finite binary32 -> Decimal ties-to-even signed fixed0/0/2; checked actual146 transitions, not all Rust formatting edge cases.',no_None_or_wildcard_in_projected_expected=True,full_Game8192_and_non150_opcode_scope='Captured observations; all Game writes, non150payloads, allocation and packet owner identities are not declared predicted.',locale='Explicit en0/zh11 original static dictionaries and selector inputs, cold original Once0 ->3 on first growth; no Once/dictionary/snapshot injection.',historical18source_batch_superseded_not_added=correction,process=terminal,actual_host_calls=0,stack_checks=281,original_snapshot_inputs=False,model_original_checker_executed_by_reviewer=False,new_original_cases=0,full880_frames=0,native_executions=0,all_artifact_sha256={p.name:sha(p)for p in RUN.iterdir()if p.is_file()},pending=report['pending'],elapsed_seconds=time.monotonic()-began)
 assert result['elapsed_seconds']<60
 (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],counts=dict(counts),semantic=sem)),flush=True)
if __name__=='__main__':main()
