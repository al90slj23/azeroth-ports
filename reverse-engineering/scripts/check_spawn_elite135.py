#!/usr/bin/env python3
"""Actual full947 due elite production with ordered RNG and original5736."""
import argparse,json,os,signal,subprocess,time
from collections import Counter
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
from check_spawn_boss135 import SOURCE_FILES as BOSS_SOURCES,compare,RUNTIME,RUNTIME_SHA
from core_spec import binary32 as f
from core_spec.spawn_elite135 import step_elite_frame
from core_spec.spawn_schedule135 import FrameInput
from core_spec.spawn_position135_data import ZONE_GEOMETRY
from core_spec.spawn135_data import ZONES
SOURCE_FILES=(*BOSS_SOURCES,'reconstruction/core_spec/spawn_elite135.py','scripts/check_spawn_elite135.py','scripts/run_spawn_elite135_oracle.mjs')
IMPORT_HASHES={n:sha(ROOT/n)for n in SOURCE_FILES}


def corpus(pilot=False):
    cases=[];b=f.from_float
    def add(zone=0,now=180,difficulty=0,group='all-zone-due',**kw):
        raw=dict(zone=zone,now_bits=b(now),dt_bits=0,budget_bits=b(4),kill_cost_bits=0,mode=0,members=1,difficulty=difficulty,
            zone_multiplier_bits=b(1),victory_field400=0,endless_flag=0,endless_start_bits=0,player_xyz=(*ZONE_GEOMETRY[zone][:2],0),
            previous_player_xyz=(*ZONE_GEOMETRY[zone][:2],0),velocity_xy=(b(3),b(4)),flat_height_bits=0,rng_words=(1,2,3,4),counter=0,
            unit_records=(),other_event_timers_future=True)
        deadline=kw.pop('next_elite_bits',b(now));raw.update(kw);result=step_elite_frame(FrameInput(**raw),deadline)
        expected=dict(count=len(result.unit_records),counter=result.counter,rng_words=result.rng_words,record_hex=result.unit_records,timers_bits=[],
            budget_bits=result.ordinary.budget_bits,kill_cost_bits=result.ordinary.kill_cost_bits,velocity_xy=result.ordinary.velocity_xy,next_elite_bits=result.next_elite_bits)
        cases.append(dict(id=len(cases),kind='tick',group=group,input=raw,zone_id=ZONES[zone][0],next_boss_index=5,next_endless_bits=f.INF,
            next_elite_bits=deadline,expected=expected,requests=result.requests,model_candidates=result.candidates,model_draws=result.draws))
    for z in((0,7,11)if pilot else range(12)):
        for now in(0,180,600,1200):
            for difficulty in(0,1,5):add(z,now,difficulty)
    if not pilot:
        for difficulty in range(256):add(difficulty=difficulty,group='all-difficulty-elite-pair')
        for z in range(12):
            for d in(-.001,0,.001):add(z,420,next_elite_bits=b(420+d),group='deadline-neighbors')
            for now in(300,600,719.999,720,720.001,900):add(z,now,1,group='interval-floor')
            add(z,180,1,group='late-frame-one-elite-only',next_elite_bits=0,dt_bits=b(.016),budget_bits=b(20))
        for mode in(0,1,2,255):
            for members in(0,1,2,4,255):add(4,600,5,group='mode-members',mode=mode,members=members)
        for seed in((0,0,0,0),(123456789,362436069,521288629,88675123),(0xffffffff,0x80000000,0x12345678,0xabcdef01)):
            for now in(0,300,600):add(11,now,5,group='shared-seeded-rng',rng_words=seed)
    return json.loads(json.dumps(cases,allow_nan=False))


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in SOURCE_FILES};assert before==IMPORT_HASHES and sha(SOURCE)==SOURCE_SHA
    cases=corpus(args.phase=='pilot');out,manifest=build(['spawn_tick','spawn_boss']);snapshot=out/'source-snapshot';snapshot.mkdir()
    for n,h in before.items():
        p=snapshot/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    fixture=out/'spawn-elite135-fixtures.json';fixture.write_text(json.dumps(cases,allow_nan=False)+'\n');assert json.loads(fixture.read_text())==cases
    results=out/'spawn-elite135-results.jsonl';stderr=out/'spawn-elite135-stderr.log';assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_spawn_elite135_oracle.mjs'),str(out),str(fixture)]
    started=time.monotonic()
    with results.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned elite deadline')
    if code:raise RuntimeError(f'Original failed: {out}')
    rows=[json.loads(x)for x in results.read_text().splitlines()];failures,words=compare(cases,rows)
    (out/'spawn-elite135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in SOURCE_FILES};assert after==before and sha(SOURCE)==SOURCE_SHA
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),groups=dict(Counter(c['group']for c in cases)),
        successful_elites=sum(len(c['requests'])for c in cases),mismatch_fields=len(failures),compared_words=words,pending_not_counted=0,
        source_sha256_before=before,source_sha256_after=after,original_wasm_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],
        only_changed_section=7,original_functions=[947],original_callees_unchanged=True,expected_before_original=True,
        artifacts={p.name:sha(p)for p in(fixture,results,stderr,out/'spawn-elite135-mismatches.json',out/'spawn-elite135-runtime.json')},
        runtime=json.loads((out/'spawn-elite135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-started),
        limitations=['Flat/absent-grid/pathfinding placement and empty peer objects with resolved owner0.',
         'All other event and Boss clocks are future; UI messages and object-registry side effects remain outside this projection.'])
    (out/'spawn-elite135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),successful_elites=receipt['successful_elites'],mismatch_fields=len(failures),first_failures=failures[:12]),indent=2))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
