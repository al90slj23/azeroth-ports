#!/usr/bin/env python3
"""Independent expected-before-original full921 ordinary movement/attack test."""
from dataclasses import asdict,replace
from collections import Counter
import argparse,json,os,signal,struct,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha

SOURCE_FILES=tuple('scripts/'+x for x in('check_ai135_spec.py','run_ai135_oracle.mjs','build_full135_oracle.py',
 'full135_host.mjs','build_upgrade134_oracle.py'))+tuple('reconstruction/core_spec/'+x+'.py'for x in(
 'ai135','ai135_data','incoming135','incoming134','spawn135','spawn135_data','spawn_math135',
 'spawn_geometry135','binary32','binary32_sqrt','enemy_scaling','progression134','rng'))
IMPORT_SHA={x:sha(ROOT/x)for x in SOURCE_FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ai135 import AiFrame135,update_ordinary_units,MELEE_DEFINITIONS
from core_spec.incoming135 import IncomingState135,ModifierRecord,BuffRecord
from core_spec.spawn135 import SpawnInput,spawn_normal,NORMALS
FIELDS=('armor_1392_bits','armor_cap_1572_bits','nearby_reduction_1444_bits','hp_1528_bits',
 'shield_1532_bits','barrier_1536_bits','shield_source_1344','shield_source_remaining_1348_bits',
 'reserve_768_bits','absorbed_740_bits','maximum_shield_744_bits','last_hit_1648_bits')
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def record(zone=0,index=0,position=(0,0,0),counter=0,**fields):
    s=SpawnInput(zone,index,f.from_float(10),f.from_float(1),0,0,1,0,0,0,(),(1,2,3,4),counter,
                 tuple(f.from_float(x)for x in position),0,bytes(424).hex())
    raw=bytearray.fromhex(spawn_normal(s).record_hex)
    struct.pack_into('<I',raw,396,0)
    for offset,value in fields.items():struct.pack_into('<I',raw,int(offset),f.from_float(value))
    return raw.hex()


def incoming(**changes):
    return IncomingState135(**dict(dict(now_bits=f.from_float(10),hp_1528_bits=f.from_float(10000)),**changes))


def corpus(pilot):
    rows=[]
    def add(group,records,s=None,steps=None):
        s=s or incoming();steps=steps or [dict(now_bits=f.from_float(10),dt_bits=f.from_float(1/60),player_xyz_bits=[0,0,0])]
        raw=asdict(s);raw['map_id']=s.map_id.decode();expected=[];current=tuple(records);queued=0
        for step in steps:
            frame=AiFrame135(current,step['now_bits'],step['dt_bits'],tuple(step['player_xyz_bits']),s,
                             incoming_item_effects=(),other_incoming_sources_absent=True)
            result=update_ordinary_units(frame);current=result.records;s=result.incoming
            queued+=len(result.attacks)+len(result.movements)
            output=dict(records=list(current),**{name:getattr(s,name)for name in FIELDS})
            output.update(incoming_total_992_bits=struct.pack('>d',s.incoming_total_992).hex(),phase2579=s.phase_2579,
                          queued_packets=queued,world_reference=0)
            expected.append(output)
        rows.append(dict(id=len(rows),group=group,input=dict(records=list(records),incoming=raw,
                         incoming_item_effects=[],other_incoming_sources_absent=True),max_hp_bits=f.from_float(10000),
                         steps=steps,expected=dict(id=len(rows),steps=expected)))
    for distance in(0,3,5,10,20,50):
        for timer in(0,.8):add('pilot-contact-or-chase',[record(position=(distance,0,0),**{'348':0,'352':timer})])
    if pilot:return rows
    for zone,definitions in enumerate(NORMALS):
        for index,d in enumerate(definitions):
            if d[1]not in MELEE_DEFINITIONS:continue
            for distance in(1,10):add('all124-melee-definitions',[record(zone,index,(distance,0,0),**{'348':0,'352':0})])
    for distance in(3.2999997,3.3,3.3000002,3.31,10,50):
        for timer in(-1,0,.016666665,.01666666753590107,.02):
            add('timer-and-range-boundaries',[record(position=(distance,0,0),**{'348':0,'352':timer})])
    for angle in(-6,-3,-1,0,.3,1,3,5,6):
        for position in((10,0,0),(0,-10,2),(-3,9,-2)):
            add('trig-and-xyz-movement',[record(position=position,**{'348':0,'396':angle})])
    for speed in(.1,.5,1,5,50):
        for slow in(0,.2,.9):
            for expiry in(9,10,11):
                add('movement-speed-slow-select',[record(position=(20,10,0),**{'348':0,'300':speed,'120':slow,'124':expiry})])
    for weakness in(0,.2,1):
        for expiry in(9,10,11):
            add('attack-weakness-priority',[record(**{'352':0,'128':weakness,'132':expiry,'136':.4,'140':11})])
    for expiry in(9,10,11):
        add('attack-haste-lock404',[record(**{'352':0,'404':expiry})])
        add('movement-haste404',[record(position=(20,0,0),**{'348':0,'404':expiry})])
        add('skip-unit400',[record(position=(20,0,0),**{'348':0,'400':expiry})])
    for active_time in(9,9.5,10,11):
        for duration in(.5,1,2):
            # Equal start/end is legitimate and still verifies ordered progress
            # and stopping an in-flight interpolation once within melee range.
            add('stop-in-flight',[record(position=(2,1,0),**{'340':active_time,'344':duration,'352':0})])
    for count in(0,1,2,5,8,16):
        recs=[record(position=(j%2,j%3,0),counter=j,**{'352':0})for j in range(count)]
        for armor in(0,.3):
            s=incoming(armor_1392_bits=f.from_float(armor),nearby_reduction_1444_bits=f.from_float(.2),
                       modifiers=(ModifierRecord(54,1,7),))
            add('queued-multi-unit-armor',recs,s)
    for shield in(0,1,5,50):
        add('contact-shield-cleanup',[record(**{'352':0})],incoming(shield_1532_bits=f.from_float(shield),barrier_1536_bits=f.from_float(shield)))
    for phase in(0,1,2):add('incoming-phase',[record(**{'352':0})],incoming(phase_2579=phase))
    for mode in(0,1):add('party-mode',[record(**{'352':0})],incoming(mode_2574=mode,wave_2532=2))
    # Persistent original memory, no record reset between200 frames: chase,
    # interpolate, stop, attack, reset cooldown, attack again.
    for distance in(0,10,30):
        steps=[dict(now_bits=f.from_float(10+j*.05),dt_bits=f.from_float(.05),player_xyz_bits=[0,0,0])for j in range(200)]
        add('continuous-ten-second-chase-attack',[record(position=(distance,0,0),**{'348':0,'352':0})],steps=steps)
    return rows


def rejected_sources():
    cases=[];base=AiFrame135((record(),),f.from_float(10),f.from_float(.05),(0,0,0),incoming(),
                            incoming_item_effects=(),other_incoming_sources_absent=True)
    for name,frame in(
        ('absence-not-declared',replace(base,other_incoming_sources_absent=False)),
        ('raw-active-buff13',replace(base,incoming=incoming(buffs=(BuffRecord(13,value12_bits=f.from_float(1),expires24_bits=f.from_float(20)),)))),
        ('other-buff14',replace(base,incoming=incoming(buffs=(BuffRecord(14),)))),
        ('item22-8B-vector',replace(base,incoming_item_effects=((22,f.from_float(.5)),))),
        ('other-item8B-vector',replace(base,incoming_item_effects=((1,f.from_float(.5)),))),
        ('modifier22-984',replace(base,incoming=incoming(modifiers=(ModifierRecord(22,1,1),)))),
        ('modifier13-984',replace(base,incoming=incoming(modifiers=(ModifierRecord(13,1,1),)))),
        ('unverified54-variant',replace(base,incoming=incoming(modifiers=(ModifierRecord(54,2,1),)))),
    ):
        try:update_ordinary_units(frame)
        except ValueError as exc:cases.append(dict(case=name,rejected=True,reason=str(exc)))
        else:raise AssertionError('Unmodeled producer silently accepted: '+name)
    return cases


def compare(e,a,path,failures):
    if type(e)is not type(a):failures.append(dict(field=path,expected=e,actual=a));return
    if isinstance(e,dict):
        assert e.keys()==a.keys()
        for key in e:compare(e[key],a[key],path+'.'+key,failures)
    elif isinstance(e,list):
        assert len(e)==len(a)
        for i,(x,y)in enumerate(zip(e,a)):compare(x,y,path+f'[{i}]',failures)
    elif e!=a:failures.append(dict(field=path,expected=e,actual=a))


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={x:sha(ROOT/x)for x in SOURCE_FILES};assert before==IMPORT_SHA
    guard_cases=rejected_sources();cases=corpus(args.phase=='pilot');out,manifest=build(['update_units'])
    snapshot=out/'source-snapshot';snapshot.mkdir()
    for name,digest in before.items():
        dest=snapshot/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes());assert sha(dest)==digest
    fixture=out/'ai135-fixtures.jsonl';fixture.write_text(''.join(json.dumps(c,allow_nan=False)+'\n'for c in cases))
    assert [json.loads(x)for x in fixture.read_text().splitlines()]==json.loads(json.dumps(cases))
    frozen={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])};assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_ai135_oracle.mjs'),str(out),str(fixture)]
    result=out/'ai135-results.jsonl';stderr=out/'ai135-stderr.log';start=time.monotonic()
    with result.open('w')as stream,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stream,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned AI oracle exceeded60s')
    if code:raise RuntimeError(f'Original AI failed: {out}')
    actual=[json.loads(x)for x in result.read_text().splitlines()];assert [x['id']for x in actual]==list(range(len(cases)))
    failures=[]
    for c,a in zip(cases,actual):compare(c['expected'],a,str(c['id']),failures)
    after={x:sha(ROOT/x)for x in SOURCE_FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    assert frozen=={p.name:sha(p)for p in(fixture,out/'manifest.json',out/manifest['module_file'])}
    (out/'ai135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
    (out/'ai135-rejected-sources.json').write_text(json.dumps(guard_cases,indent=2)+'\n')
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),steps=sum(len(c['steps'])for c in cases),
        groups=dict(Counter(c['group']for c in cases)),mismatch_fields=len(failures),rejected_source_cases=len(guard_cases),source_sha256_before=before,source_sha256_after=after,
        original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],manifest_sha256=sha(out/'manifest.json'),
        artifacts={p.name:sha(p)for p in(fixture,result,stderr,out/'ai135-mismatches.json',out/'ai135-runtime.json',out/'ai135-rejected-sources.json')},
        runtime=json.loads((out/'ai135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,
        seconds=time.monotonic()-start,deadline_seconds=60),independent_expected_before_original=True,only_changed_section=7,
        limitations=['124 ordinary normal melee definitions, flat terrain, finite small trig angles[-2pi,2pi].',
        'No alternate AI40/64/244, ranged/boss behavior, fear/stun/status producer queues, terrain or remote peer ownership.',
        'Buffs only7/12,36B modifiers only54 variant1,8B item effects empty,explicit absence of other incoming sources required; unknown984/914 producers rejected.',
        'Exact complete424B entity updates and scalar incoming HP/shields/totals; logical packets counted but encoded packet bytes and registry/aura/history remain pending.',
        'Nonfatal/guarded incoming only; reserve callbacks, death/revival and proc producers remain unresolved.'])
    (out/'ai135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),cases=len(cases),steps=receipt['steps'],mismatch_fields=len(failures),failures=failures[:3])))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
