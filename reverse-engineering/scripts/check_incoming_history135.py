#!/usr/bin/env python3
"""Expected-first incoming48 history, complete original1073 controlled domain."""
from collections import Counter
from dataclasses import asdict, replace
import argparse, hashlib, json, os, signal, struct, subprocess, sys, time
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.dont_write_bytecode = True
FILES = tuple(dict.fromkeys(('scripts/check_incoming_history135.py',
    'scripts/run_incoming_history135_oracle.mjs', 'scripts/source_closure135.py',
    'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py',
    'scripts/full135_host.mjs') + core_sources(ROOT, 'incoming_history135.py')
    + core_sources(ROOT, 'incoming135.py')))
IMPORTED = {p: sha(ROOT/p) for p in FILES}
sys.path.insert(0, str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.incoming135 import IncomingState135, input_from_dict, resolve_incoming_prefix
from core_spec.incoming_history135 import from_raw_storage, append_incoming_history, projection
RUNTIME = ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
SCALARS = ('armor_1392_bits','armor_cap_1572_bits','nearby_reduction_1444_bits',
    'hp_1528_bits','shield_1532_bits','barrier_1536_bits','shield_source_1344',
    'shield_source_remaining_1348_bits','reserve_768_bits','absorbed_740_bits',
    'maximum_shield_744_bits','last_hit_1648_bits')
INPUT_KEYS = ('id','group','input','capacity','head','count','storage','ops')


def scalar_projection(state):
    value = {key: getattr(state,key) for key in SCALARS}
    value.update(incoming_total_992_bits=struct.pack('<d',state.incoming_total_992)[::-1].hex(),
                 phase_2579=state.phase_2579)
    return value


def expected(c):
    raw = dict(c['input']); maximum = raw.pop('max_hp_bits')
    state = input_from_dict(raw)
    ring = from_raw_storage(c['storage'],c['head'],c['count'])
    stages = []
    for op in c['ops']:
        state = replace(state,now_bits=op['now_bits'])
        before = state
        result = resolve_incoming_prefix(state,op['amount_bits'],0)
        assert result.status in ('returned','pending')
        assert result.stage not in ('before27959_and1453','before_unresolved_death')
        state = result.state
        if result.status == 'pending':
            # History is written before the final minimum-one reread/clamp.
            hp_at_append = f.sub(before.hp_1528_bits,result.amount_bits)
            ring = append_incoming_history(ring,now_bits=op['now_bits'],
                damage_bits=result.amount_bits,absorbed_bits=result.absorbed_bits,
                hp_after_prefix_bits=hp_at_append,maximum_hp_bits=maximum,
                category=op['category'],source_label='',source_classification=4)
        stages.append(dict(**projection(ring),scalar=scalar_projection(state)))
    return stages


def row(stamp_bits,poison):
    raw = bytearray([poison & 255] * 48)
    for o in (0,8,16): struct.pack_into('<II',raw,o,1,0)
    struct.pack_into('<I',raw,24,stamp_bits)
    return raw.hex()


def corpus(pilot=False):
    rows=[]; b=f.from_float
    def add(group,capacity=0,head=0,count=0,timestamps=None,ops=None,**overrides):
        state=IncomingState135(hp_1528_bits=b(1000000),map_id=b'sw',
            shield_source_remaining_1348_bits=b(1000),**overrides)
        raw=asdict(state);raw['map_id']='sw';raw['max_hp_bits']=b(1000000)
        storage=[row(b(20),((j*31+17)%251)+1) for j in range(capacity)]
        if timestamps is not None:
            assert len(timestamps)==count
            for j,stamp in enumerate(timestamps):
                slot=(head+j)%capacity;storage[slot]=row(stamp,((slot*31+17)%251)+1)
        c=dict(id=len(rows),group=group,input=raw,capacity=capacity,head=head,count=count,
            storage=storage,ops=ops or[dict(now_bits=b(20),amount_bits=b(7.5),category=0,critical=0)])
        c['expected']=expected(c);rows.append(c)
    add('empty-real-append')
    add('grow-strict-tie',4,2,4)
    add('grow-prefix-greater',4,1,4)
    add('grow-prefix-smaller',4,3,4)
    add('strict-ten-second-cutoff',8,7,4,[b(9.999),b(10),b(10.001),b(20)])
    add('metadata-three-fallbacks',ops=[dict(now_bits=b(20+j),amount_bits=b(3),category=j,critical=j%2)for j in range(3)])
    add('shield-break-history',shield_1532_bits=b(5),barrier_1536_bits=b(5))
    if pilot:return rows
    for cap in (1,2,3,4,5,7,8,16,32,64,128,256,399):
        for head in sorted({0,1 if cap>1 else 0,cap//2,cap-1}):
            add('full-ring-grow-layout',cap,head,cap)
    for cap in (4,8,32,512):
        for count in sorted({0,1,min(3,cap),min(399,cap),min(400,cap)}):
            for head in sorted({0,cap-1}):add('idle-slots-wrap-preservation',cap,head,count)
    for count in (400,401,511,512):
        for head in (0,256,511):add('four-hundred-pruning',512,head,count)
    for stamp in (b(9),b(9.999999),b(10),b(10.000001),b(11),0x7fc01234,0x7f800000,0xff800000):
        for head in (0,7):add('cutoff-nan-infinity',8,head,8,[stamp]*8)
    add('mixed-expired-unordered-stops-at-oldest',8,6,8,[b(9),b(10),b(0),b(20),b(20),b(20),b(20),b(20)])
    add('consecutive-hit-limit',ops=[dict(now_bits=b(20),amount_bits=b(7.5),category=j%3,critical=j%2)for j in range(421)])
    add('consecutive-hit-expiry',ops=[dict(now_bits=b(j/8),amount_bits=b(.5),category=j%3,critical=j%2)for j in range(240)])
    add('repeated-existing-wrapped-growth',4,2,4,ops=[dict(now_bits=b(20),amount_bits=b(1),category=0,critical=0)for _ in range(48)])
    for category in (0,1,2,3,255):
        for critical in (0,1):
            add('fallback-category-and-critical',
                ops=[dict(now_bits=b(20),amount_bits=b(1),category=category,critical=critical)])
    for phase in (0,2,3,4,5,255):add('phase-guard-no-append',8,7,5,phase_2579=phase)
    for protection in (1,3,255):add('protection-guard-no-append',8,7,5,protection_2568=protection)
    for shield in (0,1,5,10,100):
        for amount in (0,1,5,7.5,10):
            add('shield-scalar-records',shield_1532_bits=b(shield),barrier_1536_bits=b(shield),
                ops=[dict(now_bits=b(20+j/4),amount_bits=b(amount),category=j%3,critical=0)for j in range(3)])
    add('minimum-one-history-before-clamp',minimum_one_2578=1,
        ops=[dict(now_bits=b(20+j),amount_bits=b(600000),category=0,critical=0)for j in range(3)])
    return json.loads(json.dumps(rows,allow_nan=False))


def compare(want,actual,path,failures,counters):
    def issue(field,w,a):
        counters['differences']+=1
        if len(failures)<60:failures.append(dict(field=field,expected=w,actual=a))
    for key in ('header','scalar'):
        if want[key]!=actual[key]:issue(path+'.'+key,want[key],actual[key])
    active=[dict(slot=x['slot'],strings=x['strings']) for x in actual['active']]
    if want['active']!=active:issue(path+'.active',want['active'],active)
    if len(want['storage'])!=len(actual['storage']):issue(path+'.backing-size',len(want['storage']),len(actual['storage']));return
    active_slots={x['slot']for x in want['active']}
    for j,(expected_row,origin,rowhex)in enumerate(zip(want['storage'],want['provenance'],actual['storage'])):
        row=bytes.fromhex(rowhex);assert len(row)==48
        for o,(w,why,a)in enumerate(zip(expected_row,origin,row)):
            if w is None:
                if why=='resource_pointer':assert o in (0,1,2,3,8,9,10,11,16,17,18,19)
                elif why=='allocator_unwritten':assert j not in active_slots or o in (46,47)
                else:raise AssertionError(why)
                counters[why+'_observations']+=1
                if a:counters[why+'_nonzero_observations']+=1
            else:
                counters['strict_backing_bytes']+=1
                if w!=a:issue(f'{path}.storage[{j}]+{o}',w,a)
                if o in (46,47):counters['strict_unwritten_padding_bytes']+=1
    counters['active_rows']+=len(active)
    counters['stages']+=1


def negatives():
    failures=[]
    for name,fn in (
        ('unknown-active-timestamp',lambda:append_incoming_history(
            __import__('core_spec.incoming_history135',fromlist=['IncomingHistory135']).IncomingHistory135(1,0,1,((None,)*48,),((None,None,None),),(('allocator_unwritten',)*48,)),
            now_bits=0,damage_bits=0,absorbed_bits=0,hp_after_prefix_bits=0,maximum_hp_bits=0)),
        ('missing-backing',lambda:from_raw_storage(('00',),0,1)),
        ('unresolved-fixture-strings',lambda:from_raw_storage((('0100000001000000'+'00'*40),),0,1))):
        try:fn()
        except (ValueError,TypeError,struct.error):failures.append(dict(name=name,rejected=True))
        else:raise AssertionError(name)
    return failures


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORTED
    cases=corpus(args.phase=='pilot');rejections=negatives()
    out,manifest=build(['incoming_damage']);snap=out/'source-snapshot'
    for n,h in before.items():
        q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    fixture=out/'incoming-history135-fixtures.json';fixture.write_text(json.dumps(cases,separators=(',',':'))+'\n')
    inputs=out/'incoming-history135-inputs.json';inputs.write_text(json.dumps([{k:c[k]for k in INPUT_KEYS}for c in cases],separators=(',',':'))+'\n')
    assert sha(RUNTIME)==RUNTIME_SHA
    frozen={q.name:sha(q)for q in(fixture,inputs,out/'manifest.json',out/manifest['module_file'])}
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_incoming_history135_oracle.mjs'),str(out),str(inputs)]
    results=out/'incoming-history135-results.jsonl';stderr=out/'incoming-history135-stderr.log';start=time.monotonic()
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError(f'Owned60s deadline:{out}')
    if code:raise RuntimeError(f'Original exit{code}:{out}')
    failures=[];counters=Counter()
    with results.open()as stream:
        for c in cases:
            a=json.loads(next(stream));assert a['id']==c['id'];assert len(a['stages'])==len(c['expected'])
            for j,(w,observed)in enumerate(zip(c['expected'],a['stages'])):compare(w,observed,f'case{c["id"]}.stage{j}',failures,counters)
        assert not stream.read().strip()
    mismatch=out/'incoming-history135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
    rejected=out/'incoming-history135-rejections.json';rejected.write_text(json.dumps(rejections,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    assert frozen=={q.name:sha(q)for q in(fixture,inputs,out/'manifest.json',out/manifest['module_file'])}
    runtime=out/'incoming-history135-runtime.json'
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=counters['stages'],
        differences=counters['differences'],comparison=dict(counters),groups=dict(Counter(c['group']for c in cases)),
        source_sha256_before=before,source_sha256_after=after,original_sha256=SOURCE_SHA,
        independent_expected_before_original=True,original_input_keys=list(INPUT_KEYS),original_input_contains_expected=False,
        artifacts={q.name:sha(q)for q in(fixture,inputs,results,stderr,mismatch,rejected,runtime,out/'manifest.json',out/manifest['module_file'])},
        runtime=json.loads(runtime.read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),
        limitations=['Complete1073 is executed, but only incoming scalar projection and48B history ring are independently modeled.',
            'SourceGUID0 and no source units;source metadata classification4/emptylabel,English fallback/spellID0 only;real4546 resource metadata excluded.',
            'No active modifiers,rawbuff,item,proc,source-shield,reserve spill or fatal continuation;guarded and minimum-one nonfatal states only.',
            'Resource pointer words compared semantically via everyactive decodedstring;actual pointer words kept in raw48 sidecars.',
            'Existing46..47 padding preserved and strict;newallocatorunwritten bytes retained as explicit unknown,notpredictedzero.',
            'FullrawG2592,allhistorybacking,packet/notificationpayloadandmetadata retained;registry,keyedcontainersandproc-tail notindependentlymodeled.',
            'This is not realentry1089/full880/headless integration or complete gameplay.'])
    target=out/'incoming-history135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),cases=len(cases),stages=receipt['stages'],differences=counters['differences'],first_failures=failures[:3]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
