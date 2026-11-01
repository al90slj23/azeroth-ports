#!/usr/bin/env python3
"""Actual full2785 Bosses and successful due947 Boss scheduling differential."""
import argparse
from collections import Counter
from dataclasses import asdict
import json,os,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
from check_spawn_motion135 import SOURCE_FILES as MOTION_SOURCES,RUNTIME,RUNTIME_SHA
from extract_spawn_boss135 import extract
SOURCE_FILES=tuple(dict.fromkeys((*MOTION_SOURCES,'scripts/check_spawn_boss135.py','scripts/run_spawn_boss135_oracle.mjs',
 'scripts/extract_spawn_boss135.py','reconstruction/core_spec/spawn_boss135.py','reconstruction/core_spec/spawn_boss135_data.py',
 'reconstruction/core_spec/spawn_boss_schedule135.py')))
IMPORT_HASHES={n:sha(ROOT/n)for n in SOURCE_FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.spawn_boss135 import BossInput,spawn_boss
from core_spec.spawn_boss135_data import BOSSES,POINTS
from core_spec.spawn_boss_schedule135 import step_boss_frame
from core_spec.spawn_schedule135 import FrameInput
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.spawn135_data import ZONES
FLOAT_FIELDS=set(range(288,356,4))|{380,384,396}


def corpus(pilot=False):
    cases=[];pending=[];b=f.from_float;seed=(1,2,3,4)
    def boss(z=0,index=0,group='all-definitions',**kw):
        raw=dict(zone=z,definition_index=index,now_bits=b(180),zone_multiplier_bits=b(1),difficulty=0,mode=0,members=1,
            victory_field400=0,endless_flag=0,endless_start_bits=0,rng_words=seed,counter=0,
            player_xyz=(*ZONE_GEOMETRY[z][:2],0),velocity_xy=(0,0),flat_height_bits=0,scalar_bits=b(1),resolved_owner=0,
            initial_slot_hex=bytes(424).hex());raw.update(kw)
        result=spawn_boss(BossInput(**raw))
        if result.status!='boss_projection':pending.append(dict(group=group,input=raw,status=result.status));return
        cases.append(dict(id=len(cases),kind='boss',group=group,zone_id=ZONES[z][0],input=raw,definition_pointer=BOSSES[z][index][0],
            expected=dict(count=1,counter=result.counter,rng_words=result.rng_words,record_hex=[result.record_hex],timers_bits=[result.timers_bits]),
            requests=[dict(index=index,position_route=result.position_route)],model_draws=result.draws))
    def tick(z=0,index=0,group='due-schedule',delta=0,**kw):
        due=f.mul(BOSSES[z][min(index,4)][5],b(60))
        raw=dict(zone=z,now_bits=f.add(due,b(delta)),dt_bits=0,budget_bits=b(4),kill_cost_bits=0,mode=0,members=1,difficulty=0,
            zone_multiplier_bits=b(1),victory_field400=0,endless_flag=0,endless_start_bits=0,player_xyz=(*ZONE_GEOMETRY[z][:2],0),
            previous_player_xyz=(*ZONE_GEOMETRY[z][:2],0),velocity_xy=(b(3),b(4)),flat_height_bits=0,rng_words=seed,counter=0,
            unit_records=(),other_event_timers_future=True)
        deadline=kw.pop('next_endless_bits',b(10000));raw.update(kw)
        result=step_boss_frame(FrameInput(**raw),index,deadline)
        expected=dict(count=len(result.unit_records),counter=result.counter,rng_words=result.rng_words,record_hex=result.unit_records,
            timers_bits=result.boss_timers,budget_bits=result.ordinary.budget_bits,kill_cost_bits=result.ordinary.kill_cost_bits,
            velocity_xy=result.ordinary.velocity_xy,next_boss_index=result.next_boss_index,next_endless_bits=result.next_endless_bits)
        cases.append(dict(id=len(cases),kind='tick',group=group,zone_id=ZONES[z][0],input=raw,next_boss_index=index,next_endless_bits=deadline,
            expected=expected,requests=result.requests,model_draws=result.draws))
    for z in((0,7,11)if pilot else range(12)):
        for index in range(5):
            boss(z,index);tick(z,index)
            tick(z,index,'difficulty5-due',difficulty=5)
    if pilot:return json.loads(json.dumps(cases)),pending
    for z in range(12):
        for index in range(5):
            for delta in(-.001,.001):tick(z,index,'deadline-neighbors',delta)
            boss(z,index,'difficulty-group-endless',difficulty=5,mode=1,members=4,now_bits=b(1500),victory_field400=1,endless_flag=1,endless_start_bits=b(600),
                rng_words=(0xffffffff,0x80000000,0x12345678,0xabcdef01),velocity_xy=(b(-3),b(4)),zone_multiplier_bits=b(1.7),scalar_bits=b(.6))
        for flag in(0,1,2,255):
            for due in(-.001,0,.001):tick(z,5,'endless-deadline',endless_flag=flag,now_bits=b(1800),next_endless_bits=b(1800+due),difficulty=5)
        tick(z,0,'late-frame-one-boss-only',now_bits=b(1800),budget_bits=b(20),dt_bits=b(.016))
    for difficulty in range(256):boss(0,2,'all-difficulty-bytes',difficulty=difficulty)
    for mode in(0,1,2,7,255):
        for members in(0,1,2,4,255,0xffffffff):boss(4,1,'group-byte-members',mode=mode,members=members)
    for flag in(0,1,2,255):
        for victory in(0,1,2):
            for start in(0,180,300):boss(11,4,'endless-bit-guards',endless_flag=flag,victory_field400=victory,endless_start_bits=b(start))
    for z in(7,11):
        for i,point in enumerate(POINTS[z]):
            for seed2 in((1,2,3,4),(123456789,362436069,521288629,88675123)):
                boss(z,1,'static-point-filter',player_xyz=(*point,0),rng_words=seed2)
    for fill in(0x55,0xa5,0xff):
        for z in(0,7,11):boss(z,4,'preserve-unwritten-bytes',initial_slot_hex=bytes([fill]*424).hex(),counter=0xffffffff)
    for scalar in(0,-1,.6,2):boss(0,0,'scalar-placement',scalar_bits=b(scalar),velocity_xy=(b(3),b(4)))
    return json.loads(json.dumps(cases)),json.loads(json.dumps(pending))


def compare(cases,rows):
    assert [r['id']for r in rows]==list(range(len(cases)))
    failures=[];words=0
    for c,r in zip(cases,rows):
        for key,want in c['expected'].items():
            got=r['result'][key]
            if key=='record_hex':
                if len(want)!=len(got):failures.append((c['id'],'record_count',len(want),len(got)));continue
                for j,(a,b)in enumerate(zip(want,got)):
                    for o,(x,y)in enumerate(zip(struct.unpack('<106I',bytes.fromhex(a)),struct.unpack('<106I',bytes.fromhex(b)))):
                        words+=1
                        if x!=y and not(o*4 in FLOAT_FIELDS and f.is_nan(x)and f.is_nan(y)):failures.append((c['id'],f'unit{j}+{o*4}',x,y))
            else:
                words+=1
                if want!=got:failures.append((c['id'],key,want,got))
    return failures,words


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in SOURCE_FILES};assert before==IMPORT_HASHES and sha(SOURCE)==SOURCE_SHA
    assert extract()==(BOSSES,POINTS),'Static declarations differ from fixed original'
    cases,pending=corpus(args.phase=='pilot');out,manifest=build(['spawn_boss','spawn_tick']);snapshot=out/'source-snapshot';snapshot.mkdir()
    for n,value in before.items():
        p=snapshot/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==value
    fixture=out/'spawn-boss135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
    (out/'spawn-boss135-pending.json').write_text(json.dumps(pending,indent=2)+'\n')
    results=out/'spawn-boss135-results.jsonl';stderr=out/'spawn-boss135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_spawn_boss135_oracle.mjs'),str(out),str(fixture)]
    started=time.monotonic()
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned Boss deadline')
    if code:raise RuntimeError(f'Original failed: {out}')
    rows=[json.loads(x)for x in results.read_text().splitlines()];failures,words=compare(cases,rows)
    (out/'spawn-boss135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in SOURCE_FILES};assert after==before and sha(SOURCE)==SOURCE_SHA
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),kinds=dict(Counter(c['kind']for c in cases)),
        groups=dict(Counter(c['group']for c in cases)),successful_bosses=sum(len(c['requests'])for c in cases),mismatch_fields=len(failures),
        compared_words=words,pending_not_counted=len(pending),source_sha256_before=before,source_sha256_after=after,
        original_wasm_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],only_changed_section=7,original_functions=[2785,947],
        original_callees_unchanged=True,expected_before_original=True,allocator_pointer_mask={'unit_offset248':'zero handle; entire ability timer payload read back separately'},
        artifacts={p.name:sha(p)for p in(fixture,results,stderr,out/'spawn-boss135-pending.json',out/'spawn-boss135-mismatches.json',out/'spawn-boss135-runtime.json')},
        runtime=json.loads((out/'spawn-boss135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),
        limitations=['Flat terrain, absent obstacle grid/pathfinding, resolved owner0 and empty peer objects only.',
         'Object-registry allocations, UI/announcement queues, entry-specific spell-object side effects and other elite/event timers are not independently reconstructed.',
         'Farthest-static-point fallback retained statically but unreachable in these finite fixed-map point fixtures.'])
    (out/'spawn-boss135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),pending=len(pending),mismatch_fields=len(failures),first_failures=failures[:12]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
