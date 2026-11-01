#!/usr/bin/env python3
"""Independent transport replay over stored data; no author/original execution."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,copy,hashlib,json,mmap,sqlite3,struct,sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/transport0135-20261101T114315.811874Z'
RECEIPT_SHA='d9db73414156c5877f7e9a9eeb1da9a3c0454e6adde85d0ddce634b4e7fd133a'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'

def sha(path):
 with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def vec(value):return None if value is None else dict(capacity=len(bytes.fromhex(value)),length=len(bytes.fromhex(value)),hex=value)
def unsigned(raw,p):
 value=shift=0
 while True:
  b=raw[p];p+=1;value|=(b&127)<<shift;shift+=7
  if b<128:return value,p
def sections(raw):
 p=8;answer=[]
 while p<len(raw):
  start=p;kind=raw[p];n,p=unsigned(raw,p+1);answer.append((kind,start,p,p+n));p+=n
 assert p==len(raw);return answer
def exports(raw,section):
 n,p=unsigned(raw,section[2]);answer=[]
 for _ in range(n):
  length,p=unsigned(raw,p);name=raw[p:p+length].decode();p+=length;kind=raw[p];index,p=unsigned(raw,p+1);answer.append([name,kind,index])
 assert p==section[3];return answer

def ring_append(ring,payload,branches):
 """Reconstruct original55793 memory relocation, including stale slots."""
 slots=ring['storage'];old_capacity=len(slots);head=ring['head'];length=ring['count']
 if length==old_capacity:
  new_capacity=max(4,old_capacity*2);slots.extend([None]*(new_capacity-old_capacity))
  if length>old_capacity-head:
   back_segment=old_capacity-head;front_segment=length-back_segment
   if back_segment>front_segment and new_capacity-old_capacity>=front_segment:
    branches['copy_prefix']+=1;slots[old_capacity:old_capacity+front_segment]=slots[:front_segment]
   else:
    branches['move_tail']+=1;destination=new_capacity-back_segment
    slots[destination:destination+back_segment]=slots[head:head+back_segment];head=destination
  else:branches['contiguous_growth'if old_capacity else'empty_growth']+=1
 index=head+length
 if index>=len(slots):index-=len(slots)
 slots[index]=payload;ring.update(head=head,count=length+1)

def state_projection(state):
 ring=state['ring'];row88=state['rows88'];row12=state['rows12']
 return dict(strong=state['strong'],weak=state['weak'],borrow=state['borrow'],timer_absent=True,
  ring=dict(capacity=len(ring['storage']),head=ring['head'],count=ring['count'],slots=[vec(x)for x in ring['storage']]),
  snapshot=vec(state['snapshot']),rows88=None if row88 is None else dict(capacity=len(row88),count=len(row88),rows=[dict(required=[vec(x)for x in r['required']],optional=[vec(x)for x in r['optional']],word84=r['word84'])for r in row88]),
  rows12=None if row12 is None else dict(capacity=len(row12),count=len(row12),hex=''.join(row12)),commands=state['commands'])

def main():
 own=Path(__file__);own_sha=sha(own);rp=BATCH/'transport135-comparison.json';assert sha(rp)==RECEIPT_SHA
 receipt=load(rp);before=receipt['source_sha256_before'];assert before==receipt['source_sha256_after'] and len(before)==receipt['source_count']==10
 for name,h in before.items():
  assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
  if name.endswith('.py'):ast.parse((ROOT/name).read_text())
 for name,h in{**receipt['frozen_artifacts'],**receipt['artifacts']}.items():assert sha(BATCH/name)==h
 inputs,expected=load(BATCH/'inputs.json'),load(BATCH/'expected.json');results=[json.loads(x)for x in(BATCH/'results.jsonl').read_text().splitlines()]
 assert len(inputs)==len(expected)==len(results)==43
 counts=Counter();branches=Counter();labels={};raw_unknown=Counter();replacements=Counter()
 def command(want,actual):
  if want is None:assert actual is None;return
  assert(actual['capacity'],actual['count'])==(len(want['storage']),want['count'])
  raw=bytes.fromhex(actual['backing_hex']);assert len(raw)==len(want['storage'])*232
  for i,row in enumerate(want['storage']):
   if row is None:
    counts['unknown_command_bytes']+=232;raw_unknown['command_unknown_raw_bytes']+=232;raw_unknown['command_unknown_nonzero_bytes']+=sum(x!=0 for x in raw[i*232:i*232+232]);continue
   reference=bytes.fromhex(row)if isinstance(row,str)else bytes(row)
   assert raw[i*232:i*232+232]==reference;counts['known_command_bytes']+=232
 def known_command_projection(want):
  return dict(capacity=len(want['storage']),count=want['count'],storage=[None if row is None else list(bytes.fromhex(row))for row in want['storage']])
 for case,wanted,actual in zip(inputs,expected,results):
  assert set(case)=={'id','input'} and set(case['input'])=={'initial','operations'}
  assert case['id']==wanted['id']==actual['id'];labels[case['id']]=wanted['label'];state=copy.deepcopy(case['input']['initial'])
  assert state['borrow']==0 and 0<state['strong'] and 0<state['weak']
  for row in state['commands']['storage']:
   if row is not None:assert len(bytes.fromhex(row))==232 and bytes.fromhex(row)[:8]==b'\2'+bytes(7)
  assert len(case['input']['operations'])==len(wanted['stages'])==len(actual['stages']);previous_cell=None;transport_hex=None
  for op,old_expected,stage in zip(case['input']['operations'],wanted['stages'],actual['stages']):
   kind=op['kind'];moved=None;answer=None
   if kind=='send':ring_append(state['ring'],op['hex'],branches)
   elif kind=='snapshot':
    replacements['snapshot_old_some']+=state['snapshot']is not None;state['snapshot']=op['hex']
   elif kind=='rows88':
    replacements['rows88_old_some']+=state['rows88']is not None;state['rows88']=copy.deepcopy(op['rows'])
    for row in op['rows']:
     for text in row['required']+[x for x in row['optional']if x is not None]:bytes.fromhex(text).decode('utf8')
   elif kind=='rows12':
    replacements['rows12_old_some']+=state['rows12']is not None;state['rows12']=copy.deepcopy(op['rows']);assert all(len(bytes.fromhex(x))==12 for x in op['rows'])
   elif kind=='poll':moved=state['commands'];state['commands']=dict(storage=[],count=0)
   else:assert kind=='false';answer=0
   reference=state_projection(state);frozen=copy.deepcopy(reference);frozen['commands']=known_command_projection(state['commands'])
   expected_stage=dict(kind=kind,state=frozen,moved=None if moved is None else known_command_projection(moved),answer=answer)
   assert expected_stage==old_expected,'Independent expected reconstruction differs'
   assert stage['kind']==kind and stage['answer']==answer
   observed=stage['state']
   for key in('strong','weak','borrow','timer_absent','snapshot','rows88','rows12'):assert observed[key]==reference[key]
   for key in('capacity','head','count'):assert observed['ring'][key]==reference['ring'][key]
   ringraw=bytes.fromhex(observed['ring']['raw_backing_hex']);assert len(ringraw)==12*reference['ring']['capacity']
   assert len(reference['ring']['slots'])==len(observed['ring']['slots'])
   for i,(want,got)in enumerate(zip(reference['ring']['slots'],observed['ring']['slots'])):
    if want is None:
     counts['unknown_ring_slots']+=1;raw_unknown['ring_unknown_raw_bytes']+=12;raw_unknown['ring_unknown_nonzero_bytes']+=sum(x!=0 for x in ringraw[i*12:i*12+12]);continue
    counts['known_ring_slots']+=1;assert want==got
    cap,ptr,length=struct.unpack_from('<3I',ringraw,i*12);assert(cap,length)==(want['capacity'],want['length'])
    assert ptr>0
   command(state['commands'],observed['commands']);command(moved,stage['moved'])
   cell=bytes.fromhex(stage['raw_cell76_hex']);transport=bytes.fromhex(stage['raw_transport24_hex']);assert len(cell)==76 and len(transport)==24
   assert struct.unpack_from('<2I',cell)==(state['strong'],state['weak']) and cell[8]==0 and cell[9:12]==b'\xa5'*3
   assert struct.unpack_from('<I',transport,8)[0]==0xffffffff and transport[20:22]==b'\0\0'
   if transport_hex is None:transport_hex=stage['raw_transport24_hex']
   assert transport_hex==stage['raw_transport24_hex']
   assert(struct.unpack_from('<I',cell,12)[0],struct.unpack_from('<2I',cell,20))==(reference['ring']['capacity'],(reference['ring']['head'],reference['ring']['count']))
   assert(struct.unpack_from('<I',cell,28)[0],struct.unpack_from('<I',cell,36)[0])==(len(state['commands']['storage']),state['commands']['count'])
   if not state['commands']['storage']:assert struct.unpack_from('<I',cell,32)[0]==8
   for name,at in(('snapshot',40),('rows88',52),('rows12',64)):
    value=state[name];words=struct.unpack_from('<3I',cell,at)
    if value is None:
     assert words[0]==0xffffffff;raw_unknown['absent_option_tail_observation_bytes']+=8
     raw_unknown['nonzero_absent_option_tail_observation_bytes']+=sum(x!=0 for x in cell[at+4:at+12])
    else:
     length=len(bytes.fromhex(value))if name=='snapshot'else len(value)
     assert(words[0],words[2])==(length,length)
   if state['rows88']is not None:
    backing=bytes.fromhex(stage['raw_rows88_backing_hex']);assert len(backing)==88*len(state['rows88'])
    for j,row in enumerate(state['rows88']):
     for k,value in enumerate(row['required']+row['optional']):
      cap,ptr,length=struct.unpack_from('<3I',backing,j*88+k*12)
      if value is None:
       assert cap==0xffffffff;raw_unknown['absent88_tail_observation_bytes']+=8;raw_unknown['nonzero_absent88_tail_observation_bytes']+=sum(x!=0 for x in backing[j*88+k*12+4:j*88+k*12+12])
      else:assert cap==length==len(bytes.fromhex(value)) and ptr>0
     assert struct.unpack_from('<I',backing,j*88+84)[0]==row['word84']
   else:assert stage['raw_rows88_backing_hex']is None
   allowed={'send':set(range(12,28)),'snapshot':set(range(40,52)),'rows88':set(range(52,64)),'rows12':set(range(64,76)),'poll':set(range(28,40)),'false':set()}[kind]|{8}
   if previous_cell is not None:assert all(previous_cell[i]==cell[i]for i in range(76)if i not in allowed)
   previous_cell=cell
   assert stage['source_preserved'] and stage['deep_copy_distinct'] and stage['unrelated_cell_bytes_preserved'];counts['stages']+=1;counts[kind]+=1
 assert branches['copy_prefix']>=2 and branches['move_tail']>0
 assert labels[28]=='wrapped-short-prefix-relocation-cap4' and labels[29]=='wrapped-short-prefix-relocation-cap8'
 assert{key:counts[key]for key in receipt['comparison']}==receipt['comparison']
 assert{key:counts[key]for key in receipt['runtime']['call_counts']}==receipt['runtime']['call_counts']
 physical=BATCH/'physical-unknowns-and-ring-growth.json';assert sha(physical)=='4bfd7efb7256e183916f3f988255ea5831f1e0b3aa24bef8b059144524bc7d02'
 addendum=load(physical);assert addendum['counts']==dict(ring_unknown_raw_bytes=raw_unknown['ring_unknown_raw_bytes'],ring_unknown_nonzero_bytes=raw_unknown['ring_unknown_nonzero_bytes'],rows88_optional_inactive_bytes=raw_unknown['absent88_tail_observation_bytes'],rows88_optional_inactive_nonzero_bytes=raw_unknown['nonzero_absent88_tail_observation_bytes'],command_unknown_raw_bytes=raw_unknown['command_unknown_raw_bytes'],command_unknown_nonzero_bytes=raw_unknown['command_unknown_nonzero_bytes'])
 provenance=BATCH/'typed-input-and-growth-provenance.json';assert sha(provenance)=='ddf27de3773993876503ee0a1423b9537fffaa8bf37c14b4183de190c861e434'
 old_batches=[('113625.117033','30bdc49931c62820a59d90eb942296ac39b12fc576e265228482597709d66b0e'),('113742.916745','af7a76438801914ea93354d040a14e6bba705362b8de7a368c8752ecd709a220'),('113901.046913','92c9ee49c96a14f9388b399bf35f06394b355d3535f50476eb041f14468a5a8b'),('114041.491286','1bf66d551486ec4523f803c77c8f02486cd20cfa0730f181ea7ded2c3068f448')];history=[];old_inputs={}
 for stamp,h in old_batches:
  path=ROOT/f'evidence/transport0135-20261101T{stamp}Z';assert sha(path/'transport135-comparison.json')==h
  rec=load(path/'transport135-comparison.json');assert rec['differences']==0
  assert rec['source_sha256_before']['reconstruction/core_spec/transport135.py']==before['reconstruction/core_spec/transport135.py']
  assert sha(path/'transport135.wasm')==receipt['frozen_artifacts']['transport135.wasm']
  old_inputs[stamp]=load(path/'inputs.json');invalid_tags=invalid_utf8=0
  for c in old_inputs[stamp]:
   for row in c['input']['initial']['commands']['storage']:
    if row is not None:invalid_tags+=bytes.fromhex(row)[:8]!=b'\2'+bytes(7)
   rows=list(c['input']['initial']['rows88']or[])
   for op in c['input']['operations']:
    if op['kind']=='rows88':rows+=op['rows']
   for row in rows:
    for value in row['required']+[x for x in row['optional']if x is not None]:
     try:bytes.fromhex(value).decode('utf8')
     except UnicodeDecodeError:invalid_utf8+=1
  if stamp=='113742.916745':assert invalid_tags>0
  if stamp=='113901.046913':assert invalid_tags==0 and invalid_utf8>0
  if stamp=='114041.491286':assert invalid_tags==invalid_utf8==0
  history.append(dict(directory=str(path.relative_to(ROOT)),receipt_sha256=h,cases=rec['cases'],invalid_command_tags=invalid_tags,invalid_UTF8_payloads=invalid_utf8,counters_not_added=True))
 third=load(ROOT/'evidence/transport0135-20261101T114041.491286Z/inputs.json')
 assert len(third)==41 and len(inputs)==43
 assert[case['input']for case in third]==[case['input']for i,case in enumerate(inputs)if i not in(28,29)]
 third_expected=load(ROOT/'evidence/transport0135-20261101T114041.491286Z/expected.json')
 assert[{k:v for k,v in e.items()if k!='id'}for e in third_expected]==[{k:v for k,v in e.items()if k!='id'}for i,e in enumerate(expected)if i not in(28,29)]
 manifest=load(BATCH/'manifest.json')
 with SOURCE.open('rb')as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)as original,(BATCH/'transport135.wasm').open('rb')as f2,mmap.mmap(f2.fileno(),0,access=mmap.ACCESS_READ)as module:
  assert hashlib.sha256(original).hexdigest()==receipt['original_sha256']
  old,new=sections(original),sections(module);assert[x[0]for x in old]==[x[0]for x in new] and 8 not in[x[0]for x in old]
  for a,b in zip(old,new):
   if a[0]!=7:assert original[a[1]:a[3]]==module[b[1]:b[3]]
  oe=exports(original,next(x for x in old if x[0]==7));ne=exports(module,next(x for x in new if x[0]==7))
  assert ne==oe+[[r['name'],0,r['index']]for r in manifest['roles']]
  db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
  with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
   for row in manifest['functions']:
    i=row['idx'];record=db.execute('select *from functions where idx=?',(i,)).fetchone();assert all(row[k]==record[k]for k in record.keys())
    wat.seek(record['wat_start']);text=wat.read(record['wat_end']-record['wat_start']);assert hashlib.sha256(text).hexdigest()==row['wat_sha256']
    assert hashlib.sha256(original[record['body_start']:record['body_end']]).hexdigest()==row['body_sha256']
    if i!=4253:assert text==(BATCH/f'{i}.wat').read_bytes()
    else:assert b''.join(text.splitlines(keepends=True)[4136:4216])==(BATCH/'4253-4137-4216-transport-constructor.wat').read_bytes()
  for r in manifest['roles']:assert hashlib.sha256(original[r['body_start']:r['body_end']]).hexdigest()==r['body_sha256']
 assert receipt['runtime']['actual_host_calls']==0 and receipt['runtime']['memory_page_cap']==512 and receipt['runtime']['peak_memory_bytes']<=33554432
 assert receipt['runtime']['calls']==220 and receipt['process']['exit_code']==0
 assert not receipt['full880'] and not receipt['full_App_constructor'] and not receipt['snapshot_used']
 for name,h in before.items():assert sha(ROOT/name)==h
 assert sha(own)==own_sha
 out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('transport0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
 review=dict(status='passed_scoped_independent_read_only_review',reviewer_sha256=own_sha,receipt=str(rp.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,source_closure=10,current_and_frozen_sources_verified=True,cases_reviewed=43,complete_entry_calls_reviewed=220,new_original_calls=0,counts=dict(counts),growth_branch_counts=dict(branches),replacements=dict(replacements),unknown_raw_observations=dict(raw_unknown),prior_batches=history,prior_typed41_inputs_preserved_except_two_added_cases=True,expected_independently_reconstructed_without_author_import=True,raw_struct_and_owned_headers_verified=True,source_nonalias_and_unrelated_byte_guards_reviewed=True,section7_only_and_original_bodies_verified=True,static_functions_verified=len(manifest['functions']),original_program_executed=False,author_model_or_checker_executed=False,full_App=False,full880=False,new_mainloop_frames=0,limitations=['Quiet flags20/21=0 and timer8=-1 only; clock/logging branches are not runtime-validated.','232B commands use payload-free tag2; they are moved, not decoded or replayed as gameplay.','Pointer identities and freed-heap contents are not independently predicted; live source invariance/nonalias checks are enforced by the frozen runner and original unchanged alloc/free bodies.','Absent option/ring/command unknown backing remains unasserted and raw observations are retained.','Typed76B cell is not full4253 App/transport ownership or network synchronization acceptance.'])
 target=out/'review.json';target.write_text(json.dumps(review,indent=2)+'\n');report=ROOT/'reports/2026-11-01-transport0135-independent-review.json';report.write_text(json.dumps({**review,'review_path':str(target.relative_to(ROOT)),'review_sha256':sha(target)},indent=2)+'\n')
 report.with_suffix('.md').write_text(f'''# 本地transport六原入口独立复核

限定域独审通过：[最终43例／220次完整六入口](../{rp.relative_to(ROOT)})、10份当前／冻结源码及所有输入输出SHA一致。[独审收据](../{target.relative_to(ROOT)}) SHA `{sha(target)}`。没有导入作者模型或执行原件。

独立重算每条operation、ring容量／head／count与全slot保留、poll整232B向量移动、snapshot与88／12B行替换，expected与原件输出一致。55793增长分支实际计数为`{dict(branches)}`，最终新增两例覆盖先前缺失的copy-prefix。88B记录每个required／optional所有权头、UTF8与word84及原raw backing另核；源不变／深clone不alias与无关cell字节保护在冻结runner中逐调用执行。未把未写tail或未知slot推成零，也未宣称allocator内部状态等价。

旧pilot与三次41例full均保留。首full的任意命令tag、第二full的非UTF8行输入均不冒称最终typed域；第三full41是合法typed域但缺copy-prefix。最终43仅插入两个case，旧41个input逐项保持，生产模型／原件module未变，旧计数不相加。

这是quiet flags20/21=0／timer8=-1的typed76B cell验证。host0、32MiB、未改callee及真实allocator路径保留；clock／logging、完整App4253、880与真实联网同步未验。本次新增原件调用／主循环帧0。
''')
 print(json.dumps(dict(directory=str(out),review_sha256=sha(target),growth_branches=dict(branches),counts=dict(counts),new_original_calls=0)))

if __name__=='__main__':main()
