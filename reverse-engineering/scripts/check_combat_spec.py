#!/usr/bin/env python3
"""Differential finite-domain check of combat projection and original slices."""
from dataclasses import asdict, replace
import hashlib
import json
import os
import random
import signal
import struct
import subprocess
import sys
from build_combat_oracle import ROOT, build
sys.path.insert(0,str(ROOT / 'reconstruction'))
from core_spec import binary32 as f
from core_spec.combat import (CombatState, UnitState, ItemModifier, base_hit_bits,
    critical_hit_bits, resolve_damage, cap_damage_bits, encoded_hp,
    damage_modifier_bits, damage_phase_bits)

SEED=0x933934

def corpus():
    rng=random.Random(SEED)
    cases=[]
    def add(mode, group, **kw):
        cases.append(dict(id=len(cases),mode=mode,group=group,**kw))
    bits=f.from_float
    edges=[0,0x80000000,1,0x80000001,0x007fffff,0x00800000,0x3f7fffff,
           0x3f800000,0x3f800001,0x7f7fffff,0xff7fffff,0x7f800000,
           0xff800000,0x7fc00000,0x7fa00001,0xffc12345]
    for category in range(256):
        add('base','all_categories',input=[bits(12),bits(1.7),bits(1.3),category,bits(80),bits(.15),bits(1.2)])
        add('category','all_category_cap_guards',category=category)
    normal=[bits(10),bits(1.1),bits(1.3),2,bits(50),bits(.1),bits(2)]
    for slot in (0,1,2,4,5,6):
        for value in edges:
            a=normal.copy();a[slot]=value;add('base','base_special_values',input=a)
    for _ in range(1500):
        a=[rng.getrandbits(32) for _ in range(7)];a[3]=rng.randrange(256)
        add('base','base_seeded_raw_bits',input=a)
    for _ in range(1000):
        add('base','base_seeded_game_range',input=[bits(rng.uniform(0,100)),bits(rng.uniform(0,20)),
            bits(rng.uniform(0,5)),rng.randrange(12),bits(rng.uniform(0,10000)),bits(rng.uniform(0,1)),bits(rng.uniform(0,10))])
    for value in edges:
        add('critical','crit_special_values',base=value,probability=bits(.5),multiplier=bits(2),rng=[1,2,3,4])
        add('critical','crit_probability_edges',base=bits(100),probability=value,multiplier=bits(2),rng=[1,2,3,4])
        add('cap','cap_special_values',amount=value,max_hp=bits(100))
        add('cap','cap_special_values',amount=bits(100),max_hp=value)
        add('wire','wire_special_values',hp=value)
    for _ in range(1500):
        add('critical','crit_seeded_raw_bits',base=rng.getrandbits(32),probability=rng.getrandbits(32),
            multiplier=rng.getrandbits(32),rng=[rng.getrandbits(32) for _ in range(4)])
    # Strict > threshold at U, and one binary32 step to either side, including zero state.
    for words in ([0,0,0,0],[1,2,3,4],[0xffffffff]*4):
        u=critical_hit_bits(bits(100),0,bits(2),tuple(words)).uniform_bits
        for p in (max(0,u-1),u,u+1):
            add('critical','crit_strict_threshold',base=bits(100),probability=p,multiplier=bits(2),rng=words)
    for _ in range(1200):
        add('cap','cap_seeded_raw_bits',amount=rng.getrandbits(32),max_hp=rng.getrandbits(32))
        add('wire','wire_seeded_raw_bits',hp=rng.getrandbits(32))
    for _ in range(1800):
        now=bits(10)
        # Every conditional modifier, priority and linked-unit phase is varied.
        u=UnitState(1,bits(rng.choice([0,1,29.999,30,30.001,90,100])),bits(100),
            kind_40=rng.choice([-1,3]),kind_64=rng.choice([-1,1]),elite_244=rng.choice([-1,0]),
            elite_412=rng.randrange(2),afflicted_240=rng.randrange(2),
            control_until_124_bits=bits(rng.choice([9,10,11])),
            control_until_376_bits=bits(rng.choice([9,10,11])),
            control_until_384_bits=bits(rng.choice([9,10,11])),
            additive_144_bits=bits(.2),additive_until_148_bits=bits(rng.choice([9,10,11])),
            additive_152_bits=bits(.4),additive_until_156_bits=bits(rng.choice([9,10,11])),
            additive_160_bits=bits(.7),additive_until_164_bits=bits(rng.choice([9,10,11])),
            additive_364_bits=bits(rng.choice([0,.5,2])),
            phase_until_404_bits=bits(rng.choice([9,10,11])),phase_until_408_bits=bits(rng.choice([9,10,11])),
            movement_duration_344_bits=bits(4),death_time_4_bits=bits(2),movement_time_340_bits=bits(3))
        linked=UnitState(2,bits(100),bits(100),kind_40=2,linked_id_32=rng.choice([0,1]),marker=rng.randrange(2))
        items=tuple(ItemModifier(rng.choice([18,19,20,21,28,0]),bits(rng.uniform(-.2,2))) for _ in range(rng.randrange(12)))
        s=CombatState((u,linked),items,now,bits(rng.choice([0,10])),accounted_total=rng.uniform(0,100))
        add('resolve','conditional_state_compositions',state=asdict(s),target_id=1,amount=bits(rng.uniform(-10,500)))
    for hp in edges:
        for amount in edges:
            u=UnitState(1,hp,bits(100),movement_duration_344_bits=bits(4),afflicted_240=1)
            s=CombatState((u,),now_bits=bits(10))
            add('resolve','hp_special_cross_product',state=asdict(s),target_id=1,amount=amount)
    # Independent immutability/early-return checks; these are not full933 oracle executions.
    s=CombatState((UnitState(1,bits(100),bits(100)),),now_bits=bits(5))
    assert resolve_damage(s,1,bits(10)).state.units[0].hp_bits==bits(90)
    assert s.units[0].hp_bits==bits(100)
    assert not resolve_damage(replace(s,running_2299=4),1,bits(10)).applied
    assert not resolve_damage(s,2,bits(10)).applied
    assert not resolve_damage(replace(s,units=(replace(s.units[0],marker=1),)),1,bits(10)).applied
    special=replace(s,units=(replace(s.units[0],kind_40=3),))
    for category in range(256):
        got=resolve_damage(special,1,bits(100),spell_id=133,spell_category=category)
        assert got.applied==(not(category<=11 and (3340>>category)&1))
    return cases


def state(c):
    s=c['state']
    return CombatState(units=tuple(UnitState(**u) for u in s['units']),
                       items=tuple(ItemModifier(**i) for i in s['items']),
                       **{k:v for k,v in s.items() if k not in ('units','items')})


def expected(c):
    mode=c['mode']
    if mode=='base':return {'bits':base_hit_bits(*c['input'])}
    if mode=='critical':
        r=critical_hit_bits(c['base'],c['probability'],c['multiplier'],tuple(c['rng']))
        return {'bits':r.amount_bits,'critical':r.critical,'rng':list(r.rng_state)}
    if mode=='category':return {'allowed':not(c['category']<=11 and (3340>>c['category'])&1)}
    if mode=='cap':return {'bits':cap_damage_bits(c['amount'],c['max_hp'])}
    if mode=='wire':return {'encoded':encoded_hp(c['hp'])}
    s=state(c);u=s.units[0]
    modified=f.mul(f.mul(c['amount'],damage_modifier_bits(s,u)),damage_phase_bits(s,u))
    if u.kind_40==3 and u.linked_id_32==0:modified=cap_damage_bits(modified,u.max_hp_bits)
    r=resolve_damage(s,c['target_id'],c['amount'])
    result={'modified_bits':modified,'applied':r.applied,'new_hp_bits':r.new_hp_bits,
            'accounted_total_bits':struct.pack('>d',r.state.accounted_total).hex(),
            'encoded':r.encoded_hp,'dead':r.dead,'marker':r.target.marker,
            'afflicted_240':r.target.afflicted_240,'duration_bits':r.target.movement_duration_344_bits,
            'death_time_bits':r.target.death_time_4_bits,'movement_time_bits':r.target.movement_time_340_bits}
    if r.applied:result['damage_bits']=r.damage_bits
    return result


def main():
    output,manifest=build()
    cases=corpus()
    inputs=output/'cases.jsonl'
    inputs.write_text(''.join(json.dumps(c,allow_nan=False,separators=(',',':'))+'\n' for c in cases))
    wants=[dict(id=c['id'],**expected(c)) for c in cases]
    (output/'model-results.jsonl').write_text(''.join(json.dumps(x,allow_nan=False)+'\n' for x in wants))
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    actual_file=output/'original-slice-results.jsonl'
    command=[str(runtime),'--max-old-space-size=128',str(ROOT/'scripts/run_combat_oracle.mjs'),
             str(output/manifest['module_file']),str(inputs)]
    with actual_file.open('w') as out,(output/'oracle.stderr.log').open('w') as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise SystemExit('Owned slice oracle exceeded deadline')
    if code:raise SystemExit('Slice oracle failed: '+(output/'oracle.stderr.log').read_text())
    actual=[json.loads(line) for line in actual_file.read_text().splitlines()]
    if len(actual)!=len(cases) or [x['id'] for x in actual]!=list(range(len(cases))):raise SystemExit('Coverage/order differs')
    mismatches=[];groups={};modes={};nan_pairs=0
    for c,want,got in zip(cases,wants,actual):
        groups[c['group']]=groups.get(c['group'],0)+1;modes[c['mode']]=modes.get(c['mode'],0)+1
        diff={}
        for key,w in want.items():
            g=got.get(key)
            if key.endswith('bits') or key=='bits':
                if isinstance(w,int) and isinstance(g,int) and f.is_nan(w) and f.is_nan(g):nan_pairs+=1;continue
            if w!=g:diff[key]=[w,g]
        if diff:mismatches.append(dict(id=c['id'],group=c['group'],differences=diff,input=c))
    (output/'mismatches.json').write_text(json.dumps(mismatches,indent=2,allow_nan=False)+'\n')
    files=[ROOT/'reconstruction/core_spec/combat.py',ROOT/'reconstruction/core_spec/binary32.py',
           ROOT/'reconstruction/core_spec/rng.py',ROOT/'scripts/build_combat_oracle.py',
           ROOT/'scripts/check_combat_spec.py',ROOT/'scripts/run_combat_oracle.mjs']
    summary={**manifest,'case_count':len(cases),'mismatch_count':len(mismatches),'groups':groups,'modes':modes,
        'nan_category_pairs':nan_pairs,'seed':hex(SEED),'run_directory':str(output),
        'node_version':subprocess.check_output([str(runtime),'--version'],text=True).strip(),
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()},
        'limitations':['Finite sampled states, not exhaustive proof.','NaN payload/sign are compared by category only.',
            'Custom wrappers compose slices; neither full933 nor full934 executes.',
            'Per-spell statistics, HP packet queue, healing/procs, position interpolation, death XP and loot excluded.',
            'Death RNG continuation is unknown: XP/gold/loot can advance RNG after the core marker write.',
            'Projection requires unique GUIDs and a resolved category for special targets with nonzero spell ID.']}
    (output/'differential-summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run_directory':str(output),'case_count':len(cases),'modes':modes,'mismatch_count':len(mismatches)}))
    if mismatches:raise SystemExit(1)


if __name__=='__main__':main()
