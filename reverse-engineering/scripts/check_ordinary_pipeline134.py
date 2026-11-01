#!/usr/bin/env python3
"""Differential restricted ordinary hit/death/reward/pickup/XP composition.

The independent production composition predicts every compared stage and the
arrival times before any original result is read. World position is an explicit
flat-region fixture; next choice generation and other callbacks remain pending.
"""
from dataclasses import replace
import json
import os
import random
import signal
import struct
import subprocess
import sys
from build_full134_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
from check_pickups134_full_spec import compare
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.combat134 import CombatState,UnitState
from core_spec.death_loot134 import OrdinaryDefinition,RewardSource,project_ordinary_rewards
from core_spec.pickups134 import PickupState,PickupRecord,Placement,encode_record56
from core_spec.progression134 import ProgressionState
from core_spec.ordinary_pipeline134 import (PipelineState,apply_ordinary_hit,collect_at,
                                          UnsupportedPipelineDomain,with_resolved_pickup_stats)

SEED=0xa2e01417
OLD_WORD=0x4faabbcc


def boundary_contract_checks():
    """Specific out-of-corpus review regression, not original-WASM case counts."""
    b=f.from_float
    records=tuple(PickupRecord(marker=1,arrival_bits=b(10),amount=amount,guid=i+1)
                  for i,amount in enumerate((1,5)))
    pickup=PickupState(records,capacity=2,now_bits=b(10))
    state=PipelineState(CombatState((UnitState(1,b(100),b(100)),),now_bits=b(10)),
                        pickup,ProgressionState(1,0,0),(1,2,3,4))
    result=collect_at(state,b(10))
    assert result.status=='pending_choice'and result.stage=='before_choice2159'
    assert result.state.progression==ProgressionState(2,0,1)
    assert tuple(r.amount for r in result.state.pickups.records)==(1,)
    assert result.xp_awards==(5,)
    assert result.state.stats_dirty
    paused=collect_at(replace(state,combat=replace(state.combat,phase_2579=3)),b(10))
    assert paused.status=='pending_stats'and paused.stage=='before_next_award_after_stat_rebuild'
    assert paused.state.progression==ProgressionState(2,0,1)and len(paused.state.pickups.records)==1
    single=replace(state,pickups=replace(pickup,records=records[1:]),combat=replace(state.combat,phase_2579=3))
    last=collect_at(single,b(10));assert last.status=='pending_stats'and last.state.stats_dirty
    blocked=collect_at(last.state,b(11));assert blocked.stage=='needs_stat_refresh'and blocked.state==last.state
    try:
        apply_ordinary_hit(last.state,1,b(10),OrdinaryDefinition(1),RewardSource(f.MASK,0,f.MASK,5411616),xp_placement=Placement(0,0,0))
    except UnsupportedPipelineDomain:pass
    else:raise AssertionError('Dirty stats must block a subsequent hit')
    refreshed=with_resolved_pickup_stats(last.state,xp_multiplier_bits=b(1),radius_bits=b(0))
    assert not refreshed.stats_dirty
    return {'mode':'purePython boundary/lifecycle contract regression','cases':5,'original_WASM_cases':0,
            'choice_boundary_preserves_later_record':True,'stat_rebuild_boundary_preserves_later_record':True,
            'last_award_marks_dirty_and_future_calls_block':True,'explicit_external_stat_snapshot_required':True}


def invert_state(words):
    a1,b1,c1,d1=words
    t=((d1>>11)|(d1<<21))&f.MASK
    a=a1^t;y=c1^b1;b=(y^(y<<9)^(y<<18)^(y<<27))&f.MASK
    return a,b,b1^b^a,t^b


def state_for_output(output,b=1,c=2):
    return 0,b,c,((output>>7)|(output<<25))&f.MASK


def corpus():
    b=f.from_float;cases=[];rng=random.Random(SEED)
    memory_path=ROOT/'evidence/catalogue0134-20261101T003611.966001Z/initial-memory.bin'
    memory=memory_path.read_bytes();base_definition=memory[5411616:5411616+72]
    if __import__('hashlib').sha256(base_definition).hexdigest()!='0de6561a210e38e6570f676a7eb5108d8e3109a17bd188399fc2b865d668289c':
        raise ValueError('Real ordinary definition differs')
    def snapshot(s,prior):
        unit=s.combat.units[0];rows=[]
        for record in s.pickups.records:
            known=prior.get(record.guid)
            raw=encode_record56(record,uninitialized_arrival_bits=known if known is not None else 0)
            words=list(struct.unpack('<14I',raw))
            if record.arrival_bits is None and known is None:words[1]=None
            rows.append(words)
        return {'phase':s.combat.phase_2579,'level':s.progression.level,'xp':s.progression.xp,'pending':s.progression.pending_upgrades,
            'unit_hp_bits':unit.hp_bits,'unit_marker':unit.marker,'unit_duration_bits':unit.movement_duration_344_bits,
            'unit_death_time_bits':unit.death_time_4_bits,'unit_movement_time_bits':unit.movement_time_340_bits,
            'unit_afflicted':unit.afflicted_240,'accounted_total_bits':struct.pack('>d',s.combat.accounted_total).hex(),
            'now_bits':s.combat.now_bits,'capacity':s.pickups.capacity,'count':len(rows),'spawn_counter':s.pickups.spawn_counter,
            'message_sequence':s.pickups.message_sequence,'accumulator_bits':s.definition_accumulator_bits,'rng':list(s.rng),'records_words':rows}
    def add(group,seed,base=1,existing=0,level=120,xp=0,collect_phase=1,amount=20,counter=0):
        definition=bytearray(base_definition);struct.pack_into('<I',definition,56,base)
        spec=OrdinaryDefinition.from_bytes(bytes(definition));position=(b(-9396),b(-633),0)
        records=tuple(PickupRecord(amount=1,guid=0xf130002329000000+i+1000,x_bits=position[0],y_bits=position[1],spawn_time_bits=b(9))for i in range(existing))
        pickups=PickupState(records,capacity=64 if existing else 0,spawn_counter=counter,now_bits=b(10),
            player_x_bits=position[0],player_y_bits=position[1],radius_bits=0)
        state=PipelineState(CombatState(units=(UnitState(1,b(10),b(100)),),now_bits=b(10)),pickups,
                            ProgressionState(level,xp,0),tuple(seed))
        source=RewardSource(f.MASK,0,f.MASK,5411616)
        hit=apply_ordinary_hit(state,1,b(amount),spec,source,xp_placement=Placement(*position),
            currency_placement=Placement(f.add(position[0],b(.8)),f.add(position[1],b(.8)),0))
        prior={r.guid:OLD_WORD for r in records};expected={'after_death':snapshot(hit.state,prior)}
        current=replace(hit.state,combat=replace(hit.state.combat,phase_2579=collect_phase))
        attraction=collect_at(current,b(10))
        if attraction.status!='core_projection':raise ValueError('Model domain boundary before arrival')
        expected['after_attraction']=snapshot(attraction.state,prior)
        xp_records=[r for r in attraction.state.pickups.records if r.kind==0 and r.marker==1]
        arrival=max((r.arrival_bits for r in xp_records),default=f.add(b(10),b(.12)))
        before=max(b(10),arrival-1)
        stage=collect_at(attraction.state,before)
        if stage.status!='core_projection':raise ValueError('Model domain boundary before due')
        expected['before_arrival']=snapshot(stage.state,prior)
        due=collect_at(stage.state,arrival)
        if due.status!='core_projection'and not(due.status=='pending_stats'and due.stage=='after_awards_before_stat_refresh'):
            raise ValueError('Candidate/foreign callbacks outside corpus')
        expected['at_arrival']=snapshot(due.state,prior)
        reward=project_ordinary_rewards(spec,tuple(seed),source=source)
        cases.append({'id':len(cases),'group':group,'definition_hex':bytes(definition).hex(),'base_xp':base,
            'position':list(position),'now_bits':b(10),'level':level,'xp':xp,'pending':0,'collect_phase':collect_phase,
            'capacity':pickups.capacity,'spawn_counter':counter,'message_sequence':0,'accumulator_bits':0,
            'radius_bits':0,'xp_multiplier_bits':b(1),'hp_bits':b(10),'max_hp_bits':b(100),'amount_bits':b(amount),
            'rng':list(seed),'record_hex':[encode_record56(r,uninitialized_arrival_bits=OLD_WORD).hex()for r in records],
            'before_arrival_bits':before,'arrival_bits':arrival,'expected':expected,
            'terminal_model_status':due.status,'terminal_stats_dirty':due.state.stats_dirty,
            'model_draws':hit.draws,'currency_pass':hit.stage=='ordinary_rewards_consumed'and reward.currency.chance_passed,
            'bounded_draws':reward.currency.bounded.draws if hit.stage=='ordinary_rewards_consumed'and reward.currency.bounded else 0})
    seeds=[(1,2,3,4),(0,0,0,0),(2079274235,2246820484,853703006,3117308271)]
    seeds += [tuple(rng.getrandbits(32)for _ in range(4))for _ in range(80)]
    for seed in seeds:
        for base in (0,1,25,0xffffffff):add('seeded_complete_ordinary_rewards',seed,base)
    for count in (44,45):
        for seed in seeds[:3]:add('death_append_or_merge_before_collection',seed,existing=count,counter=200)
    for counter in (0xffffff,0xffffffff):
        for seed in seeds[:3]:add('death_reward_counter_guid_wrap',seed,counter=counter)
    for level in (0,1,118,119):
        for base in (1,25,0xffffffff):add('phase3_growth_after_real_death',seeds[0],base,level=level,xp=4,collect_phase=3)
    for amount in (-1,0,1,9):add('nonlethal_no_reward',seeds[0],amount=amount)
    # First XP rounding draw exactly below/equal/above the representable fraction.
    fraction=f.sub(b(1.65),b(1));high24=int(f.to_float(fraction)*2**24)
    for step in (-1,0,1):add('XP_fraction_strict_boundary',state_for_output((high24+step)<<8),1)
    # Force the second draw across the f32(.165) probability grid boundary.
    boundary=int(f.to_float(0x3e28f5c3)*2**24)
    for high in (boundary,boundary+1):add('currency_probability_grid_boundary',invert_state(state_for_output(high<<8)),base=0)
    # Force the third multiply-by3 low word to the exact accept/reject boundary.
    for low in (0xbfffffff,0xc0000000):
        output=(low*0xaaaaaaab)&f.MASK
        for attempt in range(1000):
            state2=state_for_output(output,rng.getrandbits(32),rng.getrandbits(32))
            seed=invert_state(invert_state(state2));reward=project_ordinary_rewards(OrdinaryDefinition(1),seed,source=RewardSource(f.MASK,0,f.MASK,5411616))
            if reward.currency.chance_passed:break
        else:raise ValueError('Could not construct bounded sampler boundary')
        add('bounded3_exact_low32_boundary',seed)
    return cases


def main():
    contracts=boundary_contract_checks();cases=corpus();out,manifest=build(['damage','collect_pickups'])
    casefile=out/'ordinary-pipeline134-cases.json';casefile.write_text(json.dumps(cases,indent=2,allow_nan=False)+'\n')
    node=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    if sha(node)!='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0':raise ValueError('Node identity')
    resultfile=out/'ordinary-pipeline134-original-results.jsonl'
    with resultfile.open('w')as stdout,(out/'ordinary-pipeline134-stderr.log').open('w')as stderr:
        child=subprocess.Popen([str(node),'--max-old-space-size=512','--wasm-max-mem-pages=512',
            str(ROOT/'scripts/run_ordinary_pipeline134_oracle.mjs'),str(out),str(casefile)],stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise
    if code:raise SystemExit(f'Original composed path failed: {out}')
    rows=[json.loads(x)for x in resultfile.read_text().splitlines()]
    if len(rows)!=len(cases)or [x['id']for x in rows]!=list(range(len(cases))):raise ValueError('Output coverage/order')
    mismatches=[]
    for c,a in zip(cases,rows):
        for stage,want in c['expected'].items():
            if difference:=compare(want,a[stage]):mismatches.append({'id':c['id'],'stage':stage,'group':c['group'],'difference':difference})
    mismatchfile=out/'ordinary-pipeline134-mismatches.json';mismatchfile.write_text(json.dumps(mismatches,indent=2,allow_nan=False)+'\n')
    runtimefile=out/'ordinary-pipeline134-runtime.json'
    files=('scripts/build_full134_oracle.py','scripts/full134_host.mjs','scripts/check_ordinary_pipeline134.py','scripts/run_ordinary_pipeline134_oracle.mjs',
        'scripts/check_pickups134_full_spec.py','reconstruction/core_spec/ordinary_pipeline134.py','reconstruction/core_spec/combat134.py',
        'reconstruction/core_spec/death_loot134.py','reconstruction/core_spec/pickup_entity134.py','reconstruction/core_spec/pickups134.py',
        'reconstruction/core_spec/binary32_sqrt.py','reconstruction/core_spec/binary32.py','reconstruction/core_spec/rng.py','reconstruction/core_spec/progression134.py')
    receipt={'version':'0.134.0','build':'983346a7','original_wasm_sha256':SOURCE_SHA,'module_sha256':manifest['module_sha256'],
        'actual_original_chain':[914,1417,1820,2862,4630],'case_count':len(cases),'stage_snapshots_per_case':4,'mismatch_count':len(mismatches),
        'groups':{g:sum(c['group']==g for c in cases)for g in sorted({c['group']for c in cases})},
        'currency_pass_cases':sum(c['currency_pass']for c in cases),'bounded_rejection_cases':sum(c['bounded_draws']>1 for c in cases),
        'independently_predicted_times':True,'boundary_contract_checks':contracts,'runtime':json.loads(runtimefile.read_text()),
        'source_sha256':{p:sha(ROOT/p)for p in files},'artifact_sha256':{p.name:sha(p)for p in (casefile,resultfile,mismatchfile,runtimefile)},
        'limitations':['One unmoving ordinary target,flag68=0,empty items/abilities/procs/claims,mode0,region0 resolved flat world placements.',
            'Low-level progression cases explicitly set phase3 after914 to bypass2159;no independent scheduler/candidate generation implied.',
            'Full original normal callees retained;selected core fields/56B words/four-word RNG compared,not all messages/entities/events.',
            'New pickup arrival+4 remains masked until the original/model writes it;other compared words exact.',
            'Boss/special/flagged rewards,foreign collectible callbacks,terrain,full skills and independent whole game remain incomplete.']}
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Original changed')
    (out/'ordinary-pipeline134-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run':str(out),'cases':len(cases),'mismatches':len(mismatches),'currency_pass_cases':receipt['currency_pass_cases'],
                      'bounded_rejection_cases':receipt['bounded_rejection_cases']}))
    if mismatches:raise SystemExit('Independent composed ordinary pipeline differs')


if __name__=='__main__':main()
