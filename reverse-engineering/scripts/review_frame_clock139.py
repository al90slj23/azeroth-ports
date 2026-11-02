#!/usr/bin/env python3
"""Different-author read-only139884 clock-prefix micro review, never full884."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,hashlib,json,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_combat139 import sha,parse_module,local_closure

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/frame-clock139-micro-20261102T114028.262512Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMP='2a5619cfb7d98030314c218226d667fcfc0f43e7d598df9aba3e874cfc0245ec'
HAND='f4e787192b071f144915cc547cc977c9cdc975dbead9ae931f34ec8c9d38bf7f'
HELPER='158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


class Reader:
    def __init__(self,raw,pos=0,end=None):self.raw=raw;self.pos=pos;self.end=len(raw)if end is None else end
    def byte(self):assert self.pos<self.end;v=self.raw[self.pos];self.pos+=1;return v
    def take(self,n):assert 0<=n<=self.end-self.pos;v=self.raw[self.pos:self.pos+n];self.pos+=n;return v
    def uint(self):
        value=shift=0
        for _ in range(10):
            b=self.byte();value|=(b&127)<<shift
            if b<128:return value
            shift+=7
        raise AssertionError('LEB overflow')
    def sint(self):
        value=shift=0
        for _ in range(10):
            b=self.byte();value|=(b&127)<<shift;shift+=7
            if b<128:return value-(1<<shift)if b&64 else value
        raise AssertionError('Signed LEB overflow')
    def name(self):return self.take(self.uint()).decode()
    def finish(self):assert self.pos==self.end


def decode(raw):
    reader=Reader(raw);answer=[]
    simple={0x6b:'i32.sub',0x51:'i64.eq',0xa1:'f64.sub',0x63:'f64.lt',0x64:'f64.gt',0x1b:'select',0xb6:'f32.demote_f64',0x0b:'end'}
    indexed={0x23:'global.get',0x24:'global.set',0x20:'local.get',0x21:'local.set',0x22:'local.tee'}
    mem={0x29:'i64.load',0x2b:'f64.load',0x37:'i64.store',0x39:'f64.store'}
    while reader.pos<reader.end:
        begin=reader.pos;op=reader.byte()
        if op in simple:value=[simple[op]]
        elif op in indexed:value=[indexed[op],reader.uint()]
        elif op in mem:value=[mem[op],reader.uint(),reader.uint()]
        elif op==0x41:value=['i32.const',reader.sint()]
        elif op==0x42:value=['i64.const',reader.sint()]
        elif op==0x44:value=['f64.const',struct.unpack('<Q',reader.take(8))[0]]
        elif op==0x04:value=['if',reader.byte()]
        else:raise AssertionError(('Unexpected opcode',hex(op),begin))
        answer.append(dict(offset=begin,end=reader.pos,instruction=value))
    return answer


def classify(raw,exponent,mantissa):
    e=(raw>>mantissa)&((1<<exponent)-1);m=raw&((1<<mantissa)-1)
    return'nan'if e==(1<<exponent)-1 and m else'infinity'if e==(1<<exponent)-1 else'zero'if not(e or m)else'finite'


def fraction(raw,exponent,mantissa):
    assert classify(raw,exponent,mantissa)not in('nan','infinity');bias=(1<<(exponent-1))-1;e=(raw>>mantissa)&((1<<exponent)-1);m=raw&((1<<mantissa)-1)
    n=m if e==0 else(1<<mantissa)|m;power=(1-bias-mantissa)if e==0 else e-bias-mantissa
    value=Fraction(n<<power)if power>=0 else Fraction(n,1<<-power)
    return -value if raw>>(exponent+mantissa)else value


def even(n,d):
    whole,rest=divmod(n,d);return whole+int(2*rest>d or 2*rest==d and whole&1)


def rounded(value,exponent,mantissa,negative_zero=False):
    signbit=1<<(exponent+mantissa)
    if not value:return signbit if negative_zero else 0
    sign=signbit if value<0 else 0;n,d=abs(value).numerator,abs(value).denominator;bias=(1<<(exponent-1))-1;emin=1-bias;emax=bias;e=n.bit_length()-d.bit_length()
    if e>=0:
        if n<d<<e:e-=1
    elif n<<-e<d:e-=1
    if e<emin:return sign|even(n<<(mantissa-emin),d)
    shift=mantissa-e;sig=even(n<<shift,d)if shift>=0 else even(n,d<<-shift)
    if sig==1<<(mantissa+1):e+=1;sig>>=1
    if e>emax:return sign|(((1<<exponent)-1)<<mantissa)
    return sign|((e+bias)<<mantissa)|(sig&((1<<mantissa)-1))


def subtraction64(a,b):
    ca,cb=classify(a,11,52),classify(b,11,52);sign=1<<63
    if'nan'in(ca,cb):return 0x7ff8000000000000
    if ca==cb=='infinity':return 0x7ff8000000000000 if bool(a&sign)==bool(b&sign)else a
    if ca=='infinity':return a
    if cb=='infinity':return b^sign
    return rounded(fraction(a,11,52)-fraction(b,11,52),11,52,a==sign and b==0)


def independent_sample(tag,previous,now):
    dt=0;consumed=tag==1
    if consumed:
        delta=subtraction64(now,previous);kind=classify(delta,11,52)
        if kind=='nan':dt=0x7fc00000
        else:
            if kind=='infinity':chosen=0 if delta>>63 else 0x3fb999999999999a
            elif fraction(delta,11,52)<0:chosen=0
            elif fraction(delta,11,52)>fraction(0x3fb999999999999a,11,52):chosen=0x3fb999999999999a
            else:chosen=delta
            dt=rounded(fraction(chosen,11,52),8,23,chosen==1<<63)
    return dict(tag=1,timestamp=now,dt_bits=dt,timestamp_class=classify(now,11,52),dt_class=classify(dt,8,23),previous_consumed=consumed)


def corpus():
    cases=[];h=lambda v:f'{v:016x}';F=lambda v:rounded(Fraction(str(v)),11,52)
    def add(label,tag,previous,nows):cases.append(dict(id=len(cases),label=label,initial_tag_hex=h(tag),initial_previous_hex=h(previous),now_hexes=list(map(h,nows))))
    for tag in(0,2,(1<<32)+1,(1<<64)-1):add('first-tag-not-one',tag,0x7ff0000000000001,[F('.125')])
    add('negative-zero-preserved',1,0,[1<<63]);add('ordinary-continuous',0,F(99),[F(v)for v in(100,'100.05','100.1','100.2','100.19',101)])
    special=[0xfff0000000000000,0xffefffffffffffff,0xbff0000000000000,0xbfb999999999999a,0x8000000000000001,1<<63,0,1,(1023-150)<<52,(1023-149)<<52,0x3fb9999999999999,0x3fb999999999999a,0x3fb999999999999b,0x3ff0000000000000,0x7fefffffffffffff,0x7ff0000000000000,0x7ff8000000000001,0xfff80000000000a5,0x7ff0000000000001]
    for previous in special:
        for now in special:add('tag1-f64-cross-product',1,previous,[now])
    for tag in(0,2,1<<32,(1<<32)+1,1<<63,(1<<64)-1):
        for now in special:add('first-tag64-ignores-previous',tag,0xfff0000000000001,[now])
    add('nan-then-recover',0,0,[0x7ff8000000000001,F(1),F('1.125'),F('1.15')]);add('infinite-then-finite',1,0,[0x7ff0000000000000,0x7ff0000000000000,F(2),F('2.05')]);add('continuous-boundary-cancellation',1,F(2**52),[F(2**52),F(2**52+1),F(2**52-1),0,F('.1'),F('.2')])
    return cases


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM and sha(BATCH/'comparison.json')==COMP and sha(BATCH/'task-handoff.json')==HAND and sha(ROOT/'scripts/review_combat139.py')==HELPER
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');manifest=load(BATCH/'manifest.json');config=load(BATCH/'config.json')
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==13 and len(hand['frozen_author_files'])==7 and len(comp['source_import_edges'])==18
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for table in(comp['artifacts'],comp['frozen'],prep['frozen']):
        for name,h in table.items():assert sha(BATCH/name)==h
    assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and prep['expected_before_original_prefix_micro_execution']and not prep['original_input_contains_expected']
    assert all(comp[k]==0 for k in['full884_calls','original_function_entry_calls','game2352_original_execution_calls'])and comp['model_game_clock_selfchecks']==25 and comp['differences']==0
    raw=SOURCE.read_bytes();original=parse_module(raw);a,z=original['bodies'][884];assert(a,z,z-a)==(1159980,1299330,139350)and original['types'][original['decl'][884-882]]==('7f7c','')
    assert hashlib.sha256(raw[a:z]).hexdigest()==manifest['original_body_sha256']=='e6ed2847bcafc4e5f3fdf918af04c672b152fcf89eea7171531d056ba140eece'
    r=Reader(raw,a,z);groups=[(r.uint(),r.byte())for _ in range(r.uint())];assert groups==[(137,127),(11,126),(11,125),(2,124)]and r.pos-a==10;decl=raw[a:r.pos];prefix=raw[r.pos:r.pos+100]
    expected_ops=[['global.get',0],['i32.const',10704],['i32.sub'],['local.tee',3],['global.set',0],['local.get',0],['i64.load',3,0],['i64.const',1],['i64.eq'],['if',64],['f64.const',0x3fb999999999999a],['f64.const',0],['local.get',1],['local.get',0],['f64.load',3,8],['f64.sub'],['local.tee',161],['local.get',161],['f64.const',0],['f64.lt'],['select'],['local.tee',161],['local.get',161],['f64.const',0x3fb999999999999a],['f64.gt'],['select'],['f32.demote_f64'],['local.set',156],['end'],['local.get',0],['local.get',1],['f64.store',3,8],['local.get',0],['i64.const',1],['i64.store',3,0]]
    decoded=decode(prefix);assert [v['instruction']for v in decoded]==expected_ops and raw[r.pos+100:r.pos+108]==bytes.fromhex('20002802d026211a')
    assert decl==(BATCH/'original-local-declaration.bin').read_bytes()and prefix==(BATCH/'original-clock-prefix.bin').read_bytes()and hashlib.sha256(decl).hexdigest()==manifest['local_declaration_sha256']=='d02dfdc16c2dae0316b2e34589f7e5945af2a6deef130bb8f01d6e53e516fd1f'and hashlib.sha256(prefix).hexdigest()==manifest['prefix_sha256']=='d77c6c23c03df0ffd34fc3018f41bee35975f5347c4f251f635875fe55de38b8'
    tail=(BATCH/'instrumentation-tail.bin').read_bytes();assert tail==bytes.fromhex('209c010b')and[v['instruction']for v in decode(tail)]==[['local.get',156],['end']]
    flat=[127,124]+[t for n,t in groups for _ in range(n)];assert len(flat)==163 and flat[3]==127 and flat[156]==125 and flat[161]==124
    micro=(BATCH/manifest['module_file']).read_bytes();assert sha(BATCH/manifest['module_file'])==manifest['module_sha256']=='2782cb38b18b654e5bf65d5ae3c41a3437c6ccc8a1b6f4a16159e2ca2a4cbe9d';m=Reader(micro);assert m.take(8)==b'\0asm\1\0\0\0';sections=[]
    while m.pos<m.end:
        kind=m.byte();size=m.uint();payload=m.take(size);sections.append((kind,payload))
    assert[k for k,p in sections]==[1,3,5,6,7,10];sec=dict(sections)
    assert sec[1]==bytes.fromhex('0160027f7c017d')and sec[3]==bytes.fromhex('0100')and sec[5]==bytes.fromhex('01012020')
    g=Reader(sec[6]);assert g.uint()==1 and g.byte()==127 and g.byte()==1 and g.byte()==0x41 and g.sint()==1048576 and g.byte()==0x0b;g.finish()
    exports=Reader(sec[7]);assert exports.uint()==3;actual_exports=[(exports.name(),exports.byte(),exports.uint())for _ in range(3)];exports.finish();assert actual_exports==[('sample',0,0),('memory',2,0),('stack',3,0)]
    body=Reader(sec[10]);assert body.uint()==1;code=body.take(body.uint());body.finish();assert code==decl+prefix+tail and len(code)==114
    assert len([v for v in decoded if v['instruction'][0].endswith('.store')])==2 and all(v['instruction'][2]in(0,8)for v in decoded if v['instruction'][0].endswith('.store'))
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on');start,end=db.execute('select wat_start,wat_end from functions where idx=884').fetchone()
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:stream.seek(start);wat=stream.read(end-start)
    assert len(wat)==4012471 and hashlib.sha256(wat).hexdigest()==manifest['indexed_WAT_sha256']=='c3c6e002656faafe3e468dd038c13471fd3f09f6a8942ce05d592103cb576501';lines=wat.decode().splitlines(keepends=True);assert ''.join(lines[:45])==(BATCH/'884-first45.wat').read_text()
    for label,lo,hi in[('firstPhase1Clock',34962,34978),('secondPhase1Clock',47936,47955)]:assert ''.join(lines[lo-1:hi])==(BATCH/(label+'.wat')).read_text()
    assert 'i32.load8_u offset=2588'in ''.join(lines[34938:34961])and'i32.load8_u offset=2587'in ''.join(lines[47927:47935])
    save(out/'static-proof.json',dict(prefix_opcode_decode=decoded,local_groups=groups,local_declaration_hex=decl.hex(),prefix_hex=prefix.hex(),tail_hex=tail.hex(),micro_sections=[k for k,p in sections],micro_body_bytes=len(code),original884_body_sha256=manifest['original_body_sha256'],WAT_sha256=manifest['indexed_WAT_sha256'],first_clock_guard_field=2588,second_clock_guard_field=2587,both_original_clock_branch_runtime_calls=0))
    cases=corpus();observed_inputs=load(BATCH/'inputs.json');actual=[json.loads(s)for s in(BATCH/'actual.jsonl').read_text().splitlines()];assert cases==observed_inputs and len(cases)==len(actual)==484 and sum(len(c['now_hexes'])for c in cases)==500
    assert config['input_sha256']==sha(BATCH/'inputs.json')and Path(config['input_file'])==BATCH/'inputs.json'
    counts=Counter();reference=[];outside_hashes={}
    def same_bits(expected,actual,exponent,mantissa,record=True):
        if classify(expected,exponent,mantissa)=='nan':
            assert classify(actual,exponent,mantissa)=='nan'
            if record:counts['NaN'+str(exponent+mantissa+1)+'_classification_checks']+=1
        else:
            assert expected==actual,(expected,actual)
            if record:counts['strict_IEEE_bits']+=1
    for c,a in zip(cases,actual,strict=True):
        assert a['id']==c['id']and len(a['steps'])==len(c['now_hexes']);tag=int(c['initial_tag_hex'],16);previous=int(c['initial_previous_hex'],16);before=bytes.fromhex(a['before_owner_and_canaries144_hex']);low=bytes((i*13+c['id']*31+7)&255 for i in range(64));high=bytes((i*17+c['id']*29+11)&255 for i in range(64));assert before==low+struct.pack('<QQ',tag,previous)+high
        key=c['id']%256
        if key not in outside_hashes:outside_hashes[key]=dict(low_sha256=hashlib.sha256(bytes(131072-64)+low).hexdigest(),high_sha256=hashlib.sha256(high+bytes(2097152-131072-16-64)).hexdigest())
        answers=[]
        for i,(hex_now,got)in enumerate(zip(c['now_hexes'],a['steps'],strict=True)):
            assert type(hex_now)is str and len(hex_now)==16 and all(ch in'0123456789abcdef'for ch in hex_now);answer=independent_sample(tag,previous,int(hex_now,16));newtag,timestamp=struct.unpack('<QQ',bytes.fromhex(got['owner16_hex']));assert newtag==1;same_bits(answer['timestamp'],timestamp,11,52);same_bits(answer['dt_bits'],got['dt_bits'],8,23)
            assert got['low64_hex']==low.hex()and got['high64_hex']==high.hex()and got['outside_owner_unchanged']and got['stack_before']==1048576-i*10704 and got['stack_after']==1048576-(i+1)*10704
            counts['micro_prefix_steps']+=1;counts['canary_bytes']+=128;counts['owner_write_bytes']+=16;counts['negative_zero_dt']+=got['dt_bits']==0x80000000;counts['first_timestamp_not_consumed']+=not answer['previous_consumed'];counts['runtime_outside_hash_flags']+=got['outside_owner_unchanged'];counts['outside_owner_bytes_per_flag']=2097152-16
            answers.append(answer);tag=1;previous=int(hex_now,16)
        reference.append(dict(id=c['id'],steps=answers))
    assert counts['micro_prefix_steps']==500 and counts['negative_zero_dt']==2 and counts['first_timestamp_not_consumed']==120 and counts['canary_bytes']==64000 and counts['owner_write_bytes']==8000 and counts['NaN32_classification_checks']==109 and counts['NaN64_classification_checks']==76
    # The expected file is only hash-bound, not read or used as a numeric source.
    model_checks=load(BATCH/'model-only-game-clock-checks.json');assert model_checks['kind']=='arithmetic_model_selfcheck_not_original'and model_checks['original_calls']==0 and len(model_checks['cases'])==25
    wanted_model=[]
    for phase in[0,1,2,4,5]:
        for old,dt in[(0,0),(0x80000000,0x80000000),(0x40a00000,0x3dcccccd),(0x7f800000,0),(0x7fc00000,0)]:
            if phase!=1:result=old
            elif'nan'in(classify(old,8,23),classify(dt,8,23)):result=0x7fc00000
            elif classify(old,8,23)=='infinity':result=old
            else:result=rounded(fraction(dt,8,23)+fraction(old,8,23),8,23,old==dt==0x80000000)
            wanted_model.append(dict(phase=phase,clock=old,dt=dt,result=result))
    for want,got in zip(wanted_model,model_checks['cases'],strict=True):
        assert all(want[k]==got[k]for k in['phase','clock','dt']);same_bits(want['result'],got['result'],8,23,False)
    model_ast=ast.parse((ROOT/'reconstruction/core_spec/frame_clock139.py').read_text());functions={n.name:n for n in model_ast.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))};guard=functions['_u64'];guard_test=ast.unparse(guard.body[0].test);assert guard_test=='type(v) is not int or not 0 <= v <= MASK64'
    assert "state.tag_u64 == 1"in ast.unparse(functions['sample_frame_clock139'])and'previous_timestamp_bits is None'in ast.unparse(functions['sample_frame_clock139'])
    runner=(ROOT/'scripts/run_frame_clock139_oracle.mjs').read_text();assert '/^[0-9a-f]{16}$/'in runner and 'BigInt(\'0x\'+h)'in runner and "Object.keys(c).sort().join()!=='id,initial_previous_hex,initial_tag_hex,label,now_hexes'"in runner and 'c.now_hexes.length>64'in runner and 'cases.length>2048'in runner and 'input.length>1048576'in runner
    assert runner.count('e.stack.value=1048576')==1 and 'lowHash=hash(b.subarray(0,P)),highHash=hash(b.subarray(P+16))'in runner and 'lowHash===hash(b.subarray(0,P))&&highHash===hash(b.subarray(P+16))'in runner
    runtime=load(BATCH/'runtime.json');terminal=load(BATCH/'owned-terminal.json');assert runtime==comp['runtime']and terminal==comp['process']==hand['process']and runtime['micro_prefix_calls']==500 and runtime['full884_calls']==runtime['original_function_entry_calls']==runtime['imports']==runtime['host_calls']==0 and runtime['instances']==1 and runtime['memory_bytes']==2097152 and runtime['memory_cap_bytes']==4194304 and runtime['heap_cap_mib']==512 and runtime['error']is None
    assert len(runtime['returns'])==500;flat_returns=[dict(case=c['id'],before=1048576-i*10704,after=1048576-(i+1)*10704,returned=True)for c in cases for i in range(len(c['now_hexes']))];assert flat_returns==runtime['returns']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60
    start_receipt=load(BATCH/'owned-start.json');assert start_receipt['pid']==terminal['pid']and start_receipt['pgid']==terminal['pgid']and start_receipt['deadline_seconds']==60 and '--max-old-space-size=512'in start_receipt['command']and '--wasm-max-mem-pages=64'in start_receipt['command']
    audit=load(BATCH/'expectation-read-audit.json');assert audit['forbidden']==[]and all(not Path(p).suffix.lower()in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    save(out/'independent-reference.json',reference);save(out/'independent-outside-memory-expected-hashes.json',outside_hashes)
    result=dict(status='pass_current139_original100B_clock_prefix_micro_only',reviewer='/root/collection139_finish',author='/root/growth139_world',version='0.139.0',build='f79c5e2b4',reviewer_script_sha256=sha(Path(__file__)),comparison_sha256=COMP,author_handoff_sha256=HAND,author_files=hand['frozen_author_files'],helper_sha256=HELPER,cases=484,micro_prefix_steps=500,full884_calls=0,original_function_entry_calls=0,original_game2352_branch_calls=0,source_files=13,source_edges=18,counts=dict(counts),reference_sha256=sha(out/'independent-reference.json'),static_proof_sha256=sha(out/'static-proof.json'),outside_expected_hashes_sha256=sha(out/'independent-outside-memory-expected-hashes.json'),original_process=terminal,original_runtime=runtime,reviewer_original_executions=0,reviewer_author_model_checker_builder_executions=0,author_files_modified=False,model_clock_selfchecks_separately_recomputed=25,first_clock_branch_guard_field2588=True,second_clock_branch_guard_field2587=True,seconds=time.monotonic()-started,limitations=['Only original100B contiguous884 prefix transplanted with original10B localdecl and4Blocal.get156/end tail into new0-import micro-module; not full884/originalfunction entry.','Owner16 clock/tag and10704stack subtraction are validated; micro has only two owner16 stores and no calls or other memory writers.','Runtime2MiBoutside-owner SHA comparisons are saved only as500booleans, not actualhash pairs/rawoutsidebytes; reviewer recomputes expected hashes and statically verifies complete checked ranges.','NaN output timestamp/dt only classified, payload/sign/quieting not promised; negativezero/nonNaN bits checked exactly.','Fullformal inputs are independently regenerated484cases with valid16lowerhex strings. Pythonu64/API static guards andJSformat/BigInt/length checks audited; JSregex coercion means arbitrary nonstring malformed inputs are not claimed rejected.','Source88434975 uses2588 layout guard,47950 uses2587; both2352addition paths static only.25arithmetic model selfchecks are not runtime branch validation.','NoGame2352originalexecution,App/bootstrap/externref/rendering/gameplay/network/native/save/fullgame acceptance; no139fulltarget counter increment.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
