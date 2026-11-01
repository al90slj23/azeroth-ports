#!/usr/bin/env python3
"""Expected-first private full2376 quiet-domain differential; no shared host."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict
import argparse,hashlib,json,math,os,random,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from trace_special2376_135 import build_special2376_135,ROOT,SOURCE_SHA
from source_closure135 import core_sources
FILES=('scripts/check_special2376_135.py','scripts/run_special2376_135_oracle.mjs',
 'scripts/trace_special2376_135.py','scripts/source_closure135.py','scripts/build_full135_oracle.py',
 'scripts/build_upgrade134_oracle.py')+core_sources(ROOT,'special2376_135.py')
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.special2376_135 import SpecialState2376_135,tick_special2376_135,projection_special2376_135,UnknownSpecial2376_135


def sha(file):
    with Path(file).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(file,value):file.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def state_input(state):
    result=asdict(state);result['storage']=[row.hex()for row in state.storage];return result


def expected(state):
    value=projection_special2376_135(tick_special2376_135(state));value.pop('status')
    before=bytearray([0xa5]*2592);after=bytearray(before)
    for o,v in((392,state.selected392),(396,state.target396),(2392,state.announcement_time2392_bits),(1888,0)):
        struct.pack_into('<I',before,o,v)
    before[2565]=state.announced2565;after=bytearray(before)
    for o,key in((392,'selected392'),(396,'target396'),(2392,'announcement_time2392_bits')):struct.pack_into('<I',after,o,value[key])
    struct.pack_into('<I',after,1888,len(value['packets']));after[2565]=value['announced2565']
    value['game_changes']=[[i,v]for i,v in enumerate(after)if v!=before[i]]
    return value


def real_input():
    directory=ROOT/'evidence/game-entry0135-probe-20261101T135403.797895Z'
    receipt=json.loads((directory/'receipt.json').read_text());assert sha(directory/'receipt.json')=='1a388679c0418f2fa2746c91ca8d3f7e91428563d05c1935f73ca09425e5b49e'
    app=receipt['runtime']['result']['contexts'][0]['App']
    with(directory/'original_game.memory').open('rb')as stream:
        stream.seek(app+16);game=stream.read(2592);cap,ptr,count=struct.unpack_from('<3I',game,1916)
        stream.seek(ptr);raw=stream.read(cap*40)
    u=lambda at:struct.unpack_from('<I',game,at)[0]
    result=SpecialState2376_135(tuple(raw[i*40:(i+1)*40]for i in range(cap)),count,u(2352),
        tuple(struct.unpack_from('<2I',game,1416)),game[2576],game[2564],game[2565],u(392),u(396),u(2392))
    return result,dict(source_receipt=str(directory/'receipt.json'),source_receipt_sha256=sha(directory/'receipt.json'),
        source_snapshot_sha256=receipt['runtime']['result']['capture']['sha256'],
        extraction='Explicit read-only fixture input only; production API never reads snapshot',Game=app+16,
        full_special_backing_pointer=ptr,capacity=cap,count=count)


def corpus():
    from dataclasses import replace
    actual,provenance=real_input();cases=[];labels=[]
    def add(group,state):
        identifier=len(cases);cases.append(dict(id=identifier,input=state_input(state)));labels.append(dict(id=identifier,group=group,expected=expected(state)))
    add('actual_running_four_special_unchanged',actual)
    for now in(0,0x3e88240c,f.from_float(19.999),0x7fc01234):add('real_four_future_or_unordered_clock',replace(actual,now_bits=now))
    for flag in(1,2,128,255):add('full_byte_protection_gate_keeps_due_four',replace(actual,protection2576=flag,now_bits=f.from_float(1000)))
    for count in(0,1,4):
        add('empty_prefix_with_preserved_capacity'if count==0 else'disabled_navigation_clears_all_nonzero_announcement',replace(actual,count=count,navigation2564=0,announced2565=2))
    for flag in(0,1,2,128,255):add('disabled_navigation_clear_or_no_packet',replace(actual,navigation2564=0,announced2565=flag,selected392=0,target396=0x12345678))
    suppression_rows=[]
    for i,raw in enumerate(actual.storage):
        data=bytearray(raw);struct.pack_into('<Q',data,0,1)
        if i==0:struct.pack_into('<2I',data,16,*actual.player_xy_bits)
        suppression_rows.append(bytes(data))
    for delta in(-float('inf'),-1,0,299.999,300,float('nan')):
        add('same_target_suppression_300_strict_boundary',replace(actual,storage=tuple(suppression_rows),now_bits=f.from_float(delta),announcement_time2392_bits=0))
    def row(marker,x,y,deadline,fill=0xa5):
        data=bytearray([fill]*40);struct.pack_into('<Q',data,0,marker);struct.pack_into('<2I',data,16,f.from_float(x),f.from_float(y));struct.pack_into('<I',data,32,deadline);return bytes(data)
    deadline_sets=[(0,), (0,0x80000000),(f.from_float(10),f.from_float(-3),f.from_float(2)),
        (0x7f800000,0x7fc01234,0xffc01234,0xff800000,0x80000000,0),
        (0x7fc01234,0x7fc05678,0x7f800000),(f.from_float(20),)*7]
    for values in deadline_sets:
        data=tuple(row(0,0,0,v,17+i)for i,v in enumerate(values))+(bytes([0x5a])*40,)*2
        add('all_inactive_deadline_total_order_preserves_padding',replace(actual,storage=data,count=len(values),now_bits=0x7fc01234,navigation2564=0,announced2565=0))
    positions=[[(1,3,4),(1,0,5)],[(0,0,0),(1,4,0),(0,0,0),(1,2,0)],[(1,-3,0),(2,3,0)],
        [(0,1,0),(0,2,0),(1,9,0)],[(1,1e20,0),(1,2e20,0)],[(0,0,0),(1,0,-0.0),(1,-0.0,0)]]
    for rows in positions:
        data=tuple(row(m,x,y,f.from_float(100),31+i)for i,(m,x,y)in enumerate(rows))+(bytes([0x3c])*40,)*3
        add('nearest_active_with_holes_ties_and_infinite_norm',replace(actual,storage=data,count=len(rows),now_bits=f.from_float(1),player_xy_bits=(0,0),navigation2564=0,announced2565=1))
    rng=random.Random(0x2376135)
    for _ in range(32):
        count=rng.randrange(1,12);data=[]
        for i in range(count):
            data.append(row(rng.choice((0,1,2,0xffffffffffffffff)),rng.randrange(-100,101),rng.randrange(-100,101),f.from_float(100),rng.randrange(256)))
        add('seeded_target_selection_keeps_full_capacity',replace(actual,storage=tuple(data)+(bytes([0x69])*40,)*2,count=count,now_bits=f.from_float(1),player_xy_bits=(f.from_float(3),f.from_float(-5)),navigation2564=0,announced2565=rng.choice((0,1,2,255))))
    # An active marker does not respawn when its old deadline is already past.
    for now in(20,21,300,1000):
        data=tuple(row(1,i+1,0,f.from_float(20),61+i)for i in range(4))
        add('past_deadline_active_objects_are_not_respawned',replace(actual,storage=data,count=4,now_bits=f.from_float(now),player_xy_bits=(0,0),navigation2564=0,announced2565=0))
    pending=[]
    for group,state in(
        ('inactive_due_equal',replace(actual,now_bits=f.from_float(20))),
        ('inactive_due_after',replace(actual,now_bits=f.from_float(21))),
        ('new_target_localization',replace(actual,selected392=0)),
        ('same_target_expired_300',replace(actual,now_bits=f.from_float(301),announcement_time2392_bits=0,storage=tuple(row(1,i+1,0,f.from_float(20))for i in range(4)),player_xy_bits=(0,0))),
        ('announcement_bit0_not_whole_byte',replace(actual,announced2565=2))):
        try:tick_special2376_135(state)
        except UnknownSpecial2376_135 as error:pending.append(dict(group=group,rejected=True,reason=str(error)))
        else:raise AssertionError(group)
    return cases,labels,pending,provenance


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--directory',type=Path);args=parser.parse_args()
    before={file:sha(ROOT/file)for file in FILES}
    if args.directory:
        out=args.directory.resolve();config=json.loads((out/'config.json').read_text());assert config['source_sha256']==before
        assert not(out/'owned-process.json').exists()
    else:
        out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('special2376-0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
        cases,labels,pending,provenance=corpus()
        save(out/'input.json',cases);save(out/'expected.json',[dict(id=v['id'],answer=v['expected'])for v in labels]);save(out/'case-labels.json',[{k:v for k,v in row.items()if k!='expected'}for row in labels]);save(out/'pending-boundaries.json',pending);save(out/'fixture-source.json',provenance)
        assert (out/'input.json').stat().st_size<=4194304 and(out/'expected.json').stat().st_size<=4194304
        manifest=build_special2376_135(out)
        config=dict(source_sha256=before,input_sha256=sha(out/'input.json'),expected_sha256=sha(out/'expected.json'),manifest_sha256=sha(out/'manifest.json'),module_sha256=manifest['module_sha256'],cases=len(cases),entry2376=manifest['entry'],memory_mib=32,denied_imports=878,io_file_cap_bytes=4194304,node_heap_mib=512,timeout_seconds=60)
        save(out/'config.json',config)
        for name in FILES:
            target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    if args.prepare_only:print(json.dumps(dict(directory=str(out),prepared_only=True,cases=config['cases'],config_sha256=sha(out/'config.json'),sources=len(before))));return
    assert all(sha(ROOT/name)==value for name,value in before.items())
    for name,key in(('input.json','input_sha256'),('expected.json','expected_sha256'),('manifest.json','manifest_sha256')):assert sha(out/name)==config[key]
    node=ROOT/'.toolchain/runtime/node_modules/node/bin/node';assert sha(node)=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    frozen={str(out/name):sha(out/name)for name in('input.json','expected.json','config.json','manifest.json','special2376_135.wasm')}
    command=[str(node),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_special2376_135_oracle.mjs'),str(out),str(out/'input.json')]
    began=time.monotonic();launcher_error=None
    def interrupted(sig,frame):raise KeyboardInterrupt('Owned special2376 launcher signal '+str(sig))
    previous_sigterm=signal.signal(signal.SIGTERM,interrupted)
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,timeout_seconds=60))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as error:launcher_error=str(error)
        finally:
            if child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,previous_sigterm)
    after={name:sha(ROOT/name)for name in FILES};terminal=dict(pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True))
    inputs_unchanged=all(sha(file)==value for file,value in frozen.items())
    status='original_boundary';differences=[];runtime=None
    if child.returncode==0:
        runtime=json.loads((out/'special2376_135-runtime.json').read_text());actual=[json.loads(v)for v in(out/'stdout.jsonl').read_text().splitlines()];expected_rows=json.loads((out/'expected.json').read_text())
        assert len(actual)==len(expected_rows)==config['cases']
        for wanted,observed in zip(expected_rows,actual):
            if wanted['id']!=observed['id']or wanted['answer']!=observed['answer']:differences.append(dict(id=wanted['id'],expected=wanted['answer'],actual=observed))
            assert observed['stack_before']==observed['stack_after']
        status='matched_scoped_full2376'if not differences else'differences_preserved'
    comparison=dict(status=status,directory=str(out),source_sha256_before=before,source_sha256_after=after,source_files=len(before),source_unchanged=before==after,
        frozen_inputs_before=frozen,frozen_inputs_unchanged=inputs_unchanged,launcher_error=launcher_error,
        input_sha256=sha(out/'input.json'),expected_sha256=sha(out/'expected.json'),manifest_sha256=sha(out/'manifest.json'),cases=config['cases'],differences=differences,runtime=runtime,
        process=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,seconds=time.monotonic()-began,terminal=terminal),
        full_original_entry=2376,full_original_body_sha256=config['entry2376']['body_sha256'],original_application_start=False,shared52_roles_changed=False,
        scope='Actual four not-due specials, target selection, disabled-navigation clear548. Due inactiveNPC and localized new-target announcements explicitly pending.',
        broader_full2376_behavior_complete=False,complete_game=False)
    save(out/'comparison.json',comparison)
    print(json.dumps(dict(directory=str(out),status=status,cases=config['cases'],diff=len(differences),exit_code=child.returncode,all_owned_terminal=all(terminal.values()),comparison_sha256=sha(out/'comparison.json'))))
    assert child.returncode==0 and before==after and inputs_unchanged and launcher_error is None and not differences and all(terminal.values())


if __name__=='__main__':main()
