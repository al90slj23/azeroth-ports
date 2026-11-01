#!/usr/bin/env python3
"""Expected-first complete2376 due-Elwynn-NPC differential; no App/VM start."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict,replace
from collections import Counter
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from trace_special2376_spawn135 import build_special_spawn135,ROOT,SOURCE,SOURCE_SHA
from production_closure135 import production_sources135
from check_opening_handoff135 import load_independent_world,DEFAULT_WORLD
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.opening135 import EmptyOpeningInput135
from core_spec.opening_handoff135 import initialize_absent_companion_handoff
from core_spec.profile_companions135 import EmptyCompanionProfile135
from core_spec.special2376_135 import SpecialState2376_135,UnknownSpecial2376_135
from core_spec.special2376_notify135 import SpecialLocale2376_135,ELWYNN_ENGLISH_NAMES,ELWYNN_CHINESE_NAMES
from core_spec.special2376_spawn135 import SpecialSpawnInput135,tick_special_spawn135
from core_spec.opening_npc_pickups135 import OpeningVector135
from core_spec.record_cells135 import cells135,put_u32,encode_row

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
def sha(path):
    with Path(path).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def corpus(phase):
    world,receipt,world_inputs=load_independent_world(DEFAULT_WORLD)
    world_inputs.update({str(DEFAULT_WORLD/n):sha(DEFAULT_WORLD/n)for n in ('receipt.json','inputs.json')})
    handoff=initialize_absent_companion_handoff(EmptyOpeningInput135(1,1,0,0,42),world,
        companion_profile=EmptyCompanionProfile135(()),title_utf8=b'Elwynn Forest',subtitle_utf8=b'')
    opening=handoff.opening;initial=opening.initial
    special=SpecialState2376_135(tuple(encode_row(row)for row in opening.special.storage),opening.special.count,
        f.from_float(20),initial.player_xyz[:2],0,0,0,0,0,0)
    base=SpecialSpawnInput135(special,opening.units,initial.level.rng_words,opening.counter,initial.player_xyz,
        initial.source_id,1,0x3f800000,0,0,1,0,0,0,0)
    cases=[];expected=[];labels=[]
    def add(label,value,locale=ELWYNN_ENGLISH_NAMES,poison=0xa5):
        answer=tick_special_spawn135(value,locale=SpecialLocale2376_135(locale))
        def storage(rows,size):return[''.join(f'{poison if x is None else x:02x}'for x in cells135(row,size))for row in rows]
        v=asdict(value);v['player_guid']=str(v['player_guid']);v['special']['storage']=[encode_row(cells135(row,40))for row in value.special.storage]
        cases.append(dict(id=len(cases),input=dict(state=v,original_special_storage=storage(value.special.storage,40),
            original_unit_storage=storage(value.units.storage,424),locale=dict(label='Chinese'if locale==ELWYNN_CHINESE_NAMES else'English',names=locale))))
        s=answer.special
        projection=dict(special=dict(storage=[cells135(row,40)for row in s.storage],count=s.count,
            selected392=s.selected392,target396=s.target396,navigation2564=s.navigation2564,
            announced2565=s.announced2565,announcement_time2392_bits=s.announcement_time2392_bits),
            units=dict(capacity=answer.units.capacity,count=answer.units.count,storage=[list(row)for row in answer.units.storage]),
            rng_words=list(answer.rng_words),counter=answer.counter,cooldowns=[{k:v for k,v in asdict(row).items()
                if k not in ('physical_pointer_offset','physical_pointer_known')}for row in answer.cooldowns],packets=answer.packets)
        for row in projection['cooldowns']:row['guid']=str(row['guid'])
        expected.append(dict(id=len(expected),answer=json.loads(json.dumps(projection))))
        labels.append(dict(id=len(labels),group=label,rng_draws=answer.rng_draws,spawned=len(answer.cooldowns),known_cell_count=sum(x is not None for row in answer.units.storage for x in row)))
    add('independent-absent-opening-four-due',base)
    add('real-opening-future-before20',replace(base,special=replace(special,now_bits=0x419fffff)))
    add('full-four-due-navigation-Guardian-English',replace(base,special=replace(special,navigation2564=1)))
    add('full-four-due-navigation-Guardian-Chinese',replace(base,special=replace(special,navigation2564=1)),ELWYNN_CHINESE_NAMES,0x69)
    if phase=='pilot':return cases,expected,labels,world_inputs
    for mask in range(16):
        rows=[]
        for i,raw in enumerate(special.storage):
            row=cells135(raw,40);put_u32(row,32,f.from_float(20 if mask&(1<<i) else 21));rows.append(encode_row(row))
        add('every-subset-first-expiry-record-order',replace(base,special=replace(special,storage=tuple(rows))))
    for now in (20,20.125,20.999,21):
        for nav in (0,1):add('first-expiry-clock<=21-boundary',replace(base,special=replace(special,now_bits=f.from_float(now),navigation2564=nav,announced2565=1)))
    for k in range(16):
        rng=random.Random(0x23761525+k);words=tuple(rng.getrandbits(32)for _ in range(4))
        add('RNG-angle-and-variant-rejection-counterwrap-scalars',replace(base,rng_words=words,
            counter=(0,0xfffffe,0xffffff,0xffffffff)[k%4],difficulty=(0,1,2,5)[k%4],field1092=k%3,
            zone_multiplier_bits=f.from_float((.5,1,2,4)[k%4]),mode=k%2,members=(1,2,4,0)[k%4],
            victory400=k%2,endless_flag2568=k%2,endless_start404_bits=f.from_float(-40 if k%2 else 0),
            level1432=(1,60,62,0xffffffff)[k%4]),poison=(0xa5,0x69,0xcc)[k%3])
    for cap,count in ((0,0),(1,0),(3,2),(4,4),(7,7),(8,7),(16,8)):
        rows=tuple(tuple([(31+j)%256]*424)for j in range(cap))
        add('full-record-capacity-prefix-poison-preserved-growth',replace(base,units=OpeningVector135(424,rows,count)))
    for protection in (1,2,255):add('full-byte-protection-retains-due-four',replace(base,special=replace(special,protection2576=protection)))
    for fill in (0,0x69,0xff):
        rows=[]
        for raw in special.storage:
            row=cells135(raw,40);row[36:40]=bytes([fill])*4;rows.append(encode_row(row))
        add('special-guid-produced-padding-retained',replace(base,special=replace(special,storage=tuple(rows))),poison=fill)
    return cases,expected,labels,world_inputs

def compare(want,actual,path,errors,counts):
    if want is None:
        if '.storage['not in path:raise ValueError('Unknown permitted only at physical record cells')
        assert type(actual)is int and 0<=actual<=255;counts['unknown_cells']+=1;return
    if type(want)is not type(actual):errors.append(dict(path=path,expected=want,actual=actual));return
    if isinstance(want,dict):
        if set(want)!=set(actual):errors.append(dict(path=path,expected_keys=list(want),actual_keys=list(actual)));return
        for k,v in want.items():compare(v,actual[k],path+'.'+k,errors,counts)
    elif isinstance(want,list):
        if len(want)!=len(actual):errors.append(dict(path=path,expected_len=len(want),actual_len=len(actual)))
        for j,(a,b)in enumerate(zip(want,actual)):compare(a,b,path+f'[{j}]',errors,counts)
    else:
        counts['known_leaves']+=1
        if want!=actual:errors.append(dict(path=path,expected=want,actual=actual))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    scripts=('check_special2376_spawn135.py','run_special2376_spawn135_oracle.mjs','trace_special2376_spawn135.py',
        'trace_special2376_135.py','production_closure135.py','check_opening_handoff135.py','build_full135_oracle.py','build_upgrade134_oracle.py')
    files=tuple('scripts/'+n for n in scripts)+production_sources135(ROOT,'core_spec.special2376_spawn135','core_spec.opening_handoff135','resource_spec.world_query135')
    before={n:sha(ROOT/n)for n in files};cases,expected,labels,world_inputs=corpus(args.phase)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('special2376-spawn0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    save(out/'input.json',cases);save(out/'expected.json',expected);save(out/'case-labels.json',labels)
    manifest,static=build_special_spawn135(out)
    for name in files:
        dest=out/'source-snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes());assert sha(dest)==before[name]
    frozen={n:sha(out/n)for n in ('input.json','expected.json','case-labels.json','manifest.json',manifest['module_file'],'producer-static.json')}
    assert all((out/n).stat().st_size<=4194304 for n in ('input.json','expected.json'))
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_special2376_spawn135_oracle.mjs'),str(out),str(out/'input.json')]
    save(out/'prepared.json',dict(source_sha256=before,artifacts=frozen,world_inputs=world_inputs,cases=len(cases),command=command,
        original_sha256=SOURCE_SHA,independent_expected_before_original=True,scope='Preparsed independent world→opening→explicit controlled20s special tick; not original full20s gameplay',
        budgets=dict(memory_mib=32,node_heap_mib=512,io_bytes=4194304,deadline_seconds=60,denied_imports=878)))
    if args.prepare_only:print(json.dumps(dict(directory=str(out),cases=len(cases),target_executed=False,prepared_sha256=sha(out/'prepared.json'))));return
    assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA
    assert all(sha(Path(p))==h for p,h in world_inputs.items());assert all(sha(ROOT/n)==h for n,h in before.items())
    result=out/'stdout.jsonl';stderr=out/'stderr.log';began=time.monotonic();launcher_error=None
    def interrupted(sig,frame):raise KeyboardInterrupt('Owned special spawn launcher signal '+str(sig))
    previous=signal.signal(signal.SIGTERM,interrupted)
    with result.open('wb')as stdout,stderr.open('wb')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as error:launcher_error=str(error)
        finally:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,previous)
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,launcher_error=launcher_error)
    save(out/'process-terminal.json',terminal)
    assert result.stat().st_size<=4194304 and stderr.stat().st_size<=4194304
    errors=[];counts=Counter();runtime=None
    if child.returncode==0:
        actual=[json.loads(x)for x in result.read_text().splitlines()];assert len(actual)==len(expected)
        for w,a in zip(expected,actual):
            v=a['answer']
            v['special']['storage']=[list(bytes.fromhex(row))for row in v['special']['storage']]
            v['units']['storage']=[list(bytes.fromhex(row))for row in v['units']['storage']]
            compare(w,dict(id=a['id'],answer=v),'case',errors,counts)
        runtime=json.loads((out/'special2376_spawn135-runtime.json').read_text());assert runtime['cases']==len(cases)and runtime['calls']==len(cases)and runtime['actual_host_calls']==0 and runtime['stack_all_restored']is True
    after={n:sha(ROOT/n)for n in files}
    assert before==after and all(sha(out/n)==h for n,h in frozen.items())and all(sha(Path(p))==h for p,h in world_inputs.items())
    assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA
    save(out/'differences.json',errors)
    receipt=dict(version='0.135.1',build='0898d5e3',cases=len(cases),full_original2376_calls=len(cases)if child.returncode==0 else None,
        complete=child.returncode==0 and not launcher_error,mismatch_leaves=len(errors),comparison=dict(counts),groups=dict(Counter(x['group']for x in labels)),
        model_expected_before_original=True,source_sha256_before=before,source_sha256_after=after,source_files=len(before),source_unchanged=before==after,
        frozen_artifacts=frozen,prepared_sha256=sha(out/'prepared.json'),world_inputs=world_inputs,process=terminal,runtime=runtime,
        output_sha256=sha(result),stderr_sha256=sha(stderr),differences_sha256=sha(out/'differences.json'),
        independent_full880_frames=0,original_app_start=False,scope='Elwynn first expiry only; >21 localized150 / timer owner consumer / nondefault variants remain pending')
    save(out/'comparison.json',receipt);print(json.dumps(dict(directory=str(out),cases=len(cases),mismatches=len(errors),first_errors=errors[:5],process=terminal,comparison_sha256=sha(out/'comparison.json'))))
    if errors or child.returncode or launcher_error or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)

if __name__=='__main__':main()
