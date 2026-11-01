#!/usr/bin/env python3
"""Fixed135 thunder_clap full922/1076 component differential;0 game start."""
from collections import Counter
from dataclasses import asdict, replace
import argparse
import hashlib
import json
import os
import random
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build, parse_source, section_list
from build_upgrade134_oracle import Reader, sha
from trace_thunder_clap135 import collect as trace_collect
from source_closure135 import core_sources
from build_cleave135_oracle import build_cleave135_stack
from check_cast135_full_spec import definition_catalogue, inputs, unit, state_from_input
from check_level_cycle135 import make_input
from check_owned_cast135 import snapshot, equivalent as old_equivalent

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.cast135 import CastDefinition, UnresolvedCast
from core_spec.cast_events135 import process_hits
from core_spec.thunder_clap135 import (ThunderClapOwnedEntry135, cast_dispatch_thunder_clap135,
    cast_thunder_clap135, tick_owned_thunder_clap135)
from core_spec.owned_cast135 import OwnedEntry135, OwnedSources135
from core_spec.death_pickup135 import apply_damage_lifesteal
from core_spec.level_cycle135 import from_dict

RUNTIME = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def thunder_definition():
    binary = SOURCE.read_bytes()
    assert hashlib.sha256(binary).hexdigest() == SOURCE_SHA
    _, _, _, _, segments = parse_source(binary)
    memory = bytearray(max(s['address'] + s['length'] for s in segments if s['address'] is not None))
    for s in segments:
        if s['address'] is not None:
            memory[s['address']:s['address'] + s['length']] = binary[s['file_offset']:s['file_offset'] + s['length']]
    p = 5467604
    raw = bytes(memory[p:p + 88])
    w = struct.unpack('<22I', raw)
    name = bytes(memory[w[3]:w[3] + w[4]])
    assert (name, w[0], raw[84], w[11]) == (b'thunder_clap', 1, 2, 6343)
    # Original unmodified global0 is the fixture's linear-memory stack pointer.
    global_section = next(s for s in section_list(binary) if s[0] == 6)
    reader = Reader(binary, global_section[2], global_section[3])
    assert reader.uint() > 0 and reader.byte() == 0x7f and reader.byte() == 1 and reader.byte() == 0x41
    assert reader.sint() == 1048576 and reader.byte() == 0x0b
    return CastDefinition(p, name, raw[84], w[0], w[11], raw[85],
        w[12], w[13], w[14], w[15], w[16]), raw.hex()


def _entry(d, record):
    return (ThunderClapOwnedEntry135 if d.ability_id == b'thunder_clap' else OwnedEntry135)(d, record)


def corpus(phase):
    cd, ch = thunder_definition()
    byid = {d.ability_id: (d,h) for d,h in definition_catalogue()}
    byid[b'thunder_clap']=(cd,ch)
    rows=[]; rng=random.Random(0x1356343)
    def add(group, *, mode='cast', units=None, records=None,
            steps=(.1,.4,6), overrides=None, timer=f.INF, now=10,
            names=(b'thunder_clap',), cast_count=1):
        rawlevel=make_input(class_byte=1,race_byte=1,level=2,phase=1,mode=1,
            heal_gate=0,hp_fraction=.3,rng_words=(1,2,3,4))
        level=from_dict(rawlevel); derived=dict(level.derived_bits)
        selected=[byid[n]for n in names]
        records=records if records is not None else [AbilityRecord(d.pointer)for d,h in selected]
        entries=tuple(_entry(d,a)for (d,h),a in zip(selected,records))
        bd,bh=byid[b'fireball']; basic=OwnedEntry135(bd,AbilityRecord(bd.pointer,remaining_cooldown_bits=f.INF))
        us=[unit(j+1,1+j*2,(j%2)*.3,hp_bits=f.from_float(1000000))for j in range(5)]if units is None else units
        for u in us:
            for off in (120,124,356):u.setdefault(f'field{off}_bits',0)
        s=inputs(us,phase=1,now_bits=f.from_float(now),max_hp_bits=derived[1536],
            current_hp_bits=level.stats.current_hp_bits,damage_multiplier_bits=derived[1540],
            critical_chance_bits=derived[1548],critical_multiplier_bits=derived[1552],
            cooldown_multiplier_bits=derived[1544],area_multiplier_bits=derived[1580],extra_targets=derived[1592])
        s.update(overrides or {})
        derived[1536]=s['max_hp_bits']; level=replace(level,derived_bits=tuple(sorted(derived.items())),
            stats=replace(level.stats,current_hp_bits=s['current_hp_bits']))
        state=state_from_input(s)
        units2=tuple(replace(u,control_until_124_bits=x['field124_bits'],modifier_until_356_bits=x['field356_bits'])for u,x in zip(state.combat.units,us))
        state=replace(state,combat=replace(state.combat,units=units2),spatial=tuple(replace(sp,unit=u)for sp,u in zip(state.spatial,units2)))
        effectwords=[[u[f'field{off}_bits']for off in (120,124,356)]for u in us]
        accepted=[];ops=[];stages=[];cast_details=[]
        def on_hit(cast,damage):
            nonlocal level
            level=replace(level,stats=replace(level.stats,now_bits=cast.combat.now_bits))
            level=apply_damage_lifesteal(level,damage.damage_bits)
            accepted.append((damage.target.target_id,damage.damage_bits));return cast
        def apply_effects(result):
            if result is None:return
            writes=getattr(result,'effect_writes',())
            for guid,off,word in writes:
                index=next(j for j,u in enumerate(us)if int(u['guid'])==guid)
                effectwords[index][(120,124,356).index(off)]=word
            cast_details.append(dict(selected=list(result.selected_ids),hits=[list(h)for h in result.hits],effect_writes=[list(w)for w in writes]))
        timer_initial=timer;current=s['now_bits']
        def capture(kind,result=None):
            snap=snapshot(state,entries,basic,level,timer);snap['effect_words']=[list(w)for w in effectwords]
            stage=dict(operation=kind,snapshot=snap)
            if result is not None:stage['success']=result.success
            stages.append(stage)
        if mode=='cast':
            for k in range(cast_count):
                current=f.add(s['now_bits'],f.from_float(k*.125))
                state=replace(state,combat=replace(state.combat,now_bits=current))
                result=cast_dispatch_thunder_clap135(state,cd,entries[0].record,after_hit=on_hit)
                state=result.state;apply_effects(result)
                ops.append(dict(kind='cast',entry_index=0,now_bits=current));capture('cast',result)
        else:
            for delta in steps:
                dt=delta['bits']if isinstance(delta,dict)else f.from_float(delta)
                current=f.add(current,dt);state=replace(state,combat=replace(state.combat,now_bits=current))
                result=tick_owned_thunder_clap135(state,entries,basic,dt,sources=OwnedSources135((),(),True),
                    class_byte=1,timer1628_bits=timer,after_hit=on_hit)
                state,entries,basic=result.state,result.entries,result.basic;timer=result.prelude.timer1628_bits
                for rr in (*result.cast_results,result.basic_result):apply_effects(rr)
                ops.append(dict(kind='owned',now_bits=current,dt_bits=dt));capture('owned')
                state,_=process_hits(state,current,after_hit=on_hit);ops.append(dict(kind='process',now_bits=current));capture('process')
        def dd(d):
            v=asdict(d);v['ability_id']=d.ability_id.decode();return v
        rows.append(dict(id=len(rows),group=group,input=s,level=rawlevel,
            definitions=[dd(d)for d,h in selected],definition_hex=[h for d,h in selected],
            owned_hex=[a.to_bytes().hex()for a in records],basic_definition=dd(bd),basic_definition_hex=bh,
            basic_hex=AbilityRecord(bd.pointer,remaining_cooldown_bits=f.INF).to_bytes().hex(),ops=ops,expected=stages,
            independent_cast_details=cast_details,accepted_hit_count=len(accepted),timer1628_bits=timer_initial))
    add('pilot-full922-damage-then-slow')
    add('pilot-empty-full922',units=[])
    add('pilot-replace-longer-slow-not-max',units=[unit(1,1,field120_bits=f.from_float(.9),field124_bits=f.from_float(200),field356_bits=f.from_float(99))],cast_count=2)
    add('pilot-full1076-learned-warrior',mode='owned',timer=0)
    if phase=='pilot':return rows
    for n in (0,1,3,8,16,24):
        add('target-count-stable-distance-marker-boundary',units=[unit(j+1,0,from_xy=[f.from_float((j%7)-3),f.from_float(j//7)],
            to_xy=[f.from_float((j%7)-3),f.from_float(j//7)],marker=int(j%5==0))for j in range(n)])
    for x in (0x411fffff,0x41200000,0x41200001,0xc1200000,f.INF,0x7fc00001):
        add('radius10-exact-boundary-nonfinite',units=[unit(1,0,from_xy=[x,0],to_xy=[x,0])])
    for k,duration in enumerate((0,0x80000000,f.from_float(-2),f.from_float(.1),f.from_float(2),f.INF,0xff800000,0x7fc00001)):
        add('additional-duration-and-unread-owned28',records=[replace(AbilityRecord(cd.pointer),
            duration_bits=(f.INF,0,0x7fc00001)[k%3],additional_duration_bits=duration)],cast_count=2)
    for k in range(20):
        us=[unit(j+1,rng.uniform(-14,14),rng.uniform(-14,14),
            from_xy=[f.from_float(rng.uniform(-12,12)),f.from_float(rng.uniform(-12,12))],
            duration_bits=f.from_float([0,3,20][j%3]),movement_time_bits=f.from_float(5),
            field120_bits=f.from_float(.8),field124_bits=f.from_float(100),field356_bits=f.from_float(40))for j in range(1+k%10)]
        a=replace(AbilityRecord(cd.pointer),damage_bits=f.from_float(rng.uniform(.1,3)),
            additional_damage_bits=f.from_float(rng.uniform(.2,2)),area_bits=f.from_float([.5,1,2][k%3]),
            additional_area_bits=f.from_float([.5,1,3][k%3]),additional_duration_bits=f.from_float(rng.uniform(.1,4)),
            life_damage_bits=f.from_float((k%3)*.01))
        add('motion-critical-area-duration-multipliers',units=us,records=[a],overrides=dict(
            critical_chance_bits=f.from_float([0,.3,1][k%3]),critical_multiplier_bits=f.from_float([.5,1,2][k%3]),
            damage_multiplier_bits=f.from_float([0,-.1,1,3][k%4]),area_multiplier_bits=f.from_float([.5,1,8][k%3])),cast_count=2)
    for ph in (0,1,2):
        add('effect-after-phase-rejected-damage',overrides=dict(phase=ph),cast_count=2)
    for off in (408,412):
        add('effect-after-elite-protected-damage',units=[unit(1,1,elite_244=0,**{f'phase_until{off}_bits':f.from_float(100)})])
    for remaining in (0,f.from_float(.5),f.INF,0x7fc00001):
        add('1076-countdown-success-retry-and-timer',mode='owned',records=[replace(AbilityRecord(cd.pointer),remaining_cooldown_bits=remaining)],timer=0,steps=(.1,.4,6))
    add('1076-empty-failure-retry-point2',mode='owned',units=[],steps=(.1,.4,.1,.1))
    add('1076-ordered-double-thunder-and-projectile',mode='owned',names=(b'thunder_clap',b'thunder_clap',b'fireball'),steps=(.1,.4,6))
    return rows


def equivalent(want,actual,path=''):
    if type(want)!=type(actual):return False
    if isinstance(want,dict):return set(want)==set(actual)and all(equivalent(v,actual[k],path+'.'+k)for k,v in want.items())
    if isinstance(want,list):return len(want)==len(actual)and all(equivalent(v,a,path+f'[{j}]')for j,(v,a)in enumerate(zip(want,actual)))
    return old_equivalent(want,actual,path)or('.effect_words['in path and type(want)is int and f.is_nan(want)and f.is_nan(actual))


def source_files():
    files={str(Path(m.__file__).resolve().relative_to(ROOT))for m in tuple(sys.modules.values())
        if getattr(m,'__file__',None)and str(Path(m.__file__).resolve()).startswith(str(ROOT)+'/')}
    files.update(core_sources(ROOT,'thunder_clap135.py','death_pickup135.py','level_cycle135.py'))
    files.update(('scripts/check_thunder_clap135.py','scripts/run_thunder_clap135_oracle.mjs',
        'scripts/trace_thunder_clap135.py','scripts/source_closure135.py','scripts/cleave135_host.mjs','scripts/full135_host.mjs'))
    return sorted(files)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot')
    parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    files=source_files();before={n:sha(ROOT/n)for n in files}
    rows=corpus(args.phase);assert files==source_files()
    try:OwnedEntry135(thunder_definition()[0],AbilityRecord(5467604))
    except UnresolvedCast:pass
    else:raise AssertionError('Old dispatcher gate changed')
    out,manifest=build_cleave135_stack()
    for name in files:
        target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes());assert sha(target)==before[name]
    trace=trace_collect(out)
    fixtures=out/'thunder-clap135-fixtures.jsonl'
    fixtures.write_text(''.join(json.dumps(c,separators=(',',':'),allow_nan=False)+'\n'for c in rows))
    expected=out/'expected.json';expected.write_text(json.dumps([c['expected']for c in rows],separators=(',',':'))+'\n')
    artifacts=[fixtures,expected,out/'manifest.json',out/manifest['module_file'],out/'static-evidence.json']
    frozen={p.name:sha(p)for p in artifacts}
    assert all(p.stat().st_size<=4194304 for p in (fixtures,expected))
    assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',
        str(ROOT/'scripts/run_thunder_clap135_oracle.mjs'),str(out),str(fixtures),'--stack-guard']
    prepared=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(rows),
        stages=sum(len(c['ops'])for c in rows),role_calls=dict(Counter(op['kind']for c in rows for op in c['ops'])),
        groups=dict(Counter(c['group']for c in rows)),command=command,artifacts=frozen,source_closure=before,
        tools=dict(node=dict(path=str(RUNTIME),sha256=RUNTIME_SHA)),functions=trace['functions'],
        independent_expected_before_original=True,quiet_denied_function_imports=878,memory_cap_bytes=33554432,
        heap_mib=512,deadline_seconds=60,per_fixture_allocation_and_io_cap_bytes=4194304)
    (out/'prepared.json').write_text(json.dumps(prepared,indent=2)+'\n')
    if args.prepare_only:
        print(json.dumps(dict(directory=str(out),prepared_sha256=sha(out/'prepared.json'),cases=len(rows),stages=prepared['stages'],target_executed=False)));return
    result=out/'thunder-clap135-results.jsonl';stderr=out/'thunder-clap135-stderr.log'
    started=time.monotonic();timed_out=False
    with result.open('w')as stream,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(child.pid,signal.SIGTERM)
            try:code=child.wait(timeout=3)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);code=child.wait()
        finally:
            try:os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            child.wait()
    try:os.killpg(child.pid,0)
    except ProcessLookupError:group_absent=True
    else:group_absent=False
    try:os.kill(child.pid,0)
    except ProcessLookupError:pid_absent=True
    else:pid_absent=False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,timed_out=timed_out,deadline_seconds=60,
        pid_absent_after=pid_absent,process_group_absent_after=group_absent,seconds=round(time.monotonic()-started,3))
    (out/'process-terminal.json').write_text(json.dumps(terminal,indent=2)+'\n')
    assert result.stat().st_size<=4194304 and stderr.stat().st_size<=4194304
    actual=[json.loads(x)for x in result.read_text().splitlines()]
    complete=code==0 and not timed_out and [a['id']for a in actual]==list(range(len(rows)))
    failures=[dict(id=c['id'],group=c['group'],expected=c['expected'],actual=a['stages'])
        for c,a in zip(rows,actual)if not equivalent(c['expected'],a['stages'])]
    mismatch=out/'thunder-clap135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in files};assert before==after
    assert sha(SOURCE)==SOURCE_SHA and sha(RUNTIME)==RUNTIME_SHA and frozen=={p.name:sha(p)for p in artifacts}
    runtime_path=out/'thunder-clap135-runtime.json';runtime=json.loads(runtime_path.read_text())if runtime_path.exists()else None
    if complete:
        assert runtime and runtime['actual_host_calls']==0 and runtime['stack_all_restored']is True
        assert len([x for x in runtime['stack_checks']if x['role']!='__wbindgen_malloc'])==prepared['stages']
    receipt=dict(prepared,complete=complete,mismatch_cases=len(failures),accepted_hits=sum(c['accepted_hit_count']for c in rows),
        source_sha256_after=after,source_unchanged=before==after,process=terminal,runtime=runtime,
        prepared_sha256=sha(out/'prepared.json'),
        final_artifacts={p.name:sha(p)for p in (*artifacts,result,stderr,mismatch,out/'process-terminal.json',*([runtime_path]if runtime_path.exists()else []))},
        status='passed_component_projection'if complete and not failures else 'failed_or_incomplete',
        limitations=['Complete original922/1076/1754 component calls, not natural Game/880 or independent full frames.',
            '2244 unchanged callee; only thunder_clap effect1 with empty effect49 override sources; procs/items empty.',
            'Nonlethal ordinary and declared protection/phase rejection targets; unresolved death continuation stops explicitly.',
            'Physical presentation/cooldown packet bytes and localization not predicted.',
            'Embedded G1256 is real racial slot supplied explicit effect0 isolated fireball fixture, never null.',
            'NaN float words compare by NaN class; other integer/float words strict; control120/124/356 projected.',
            'Private global0 checked read-only around every exposed allocator/target invocation; internal callee frames not separately instrumented.'])
    comparison=out/'comparison.json';comparison.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(comparison),cases=len(rows),stages=prepared['stages'],
        calls=prepared['role_calls'],mismatches=len(failures),complete=complete,first_ids=[c['id']for c in failures[:10]],process=terminal)))
    if not complete or failures:raise SystemExit(1)


if __name__=='__main__':main()
