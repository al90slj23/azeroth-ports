#!/usr/bin/env python3
"""Compare independent0.134.0 core damage fields with complete original914.

Original instructions/callees are retained, only section7 exports change. The
fixed source's original allocator owns synthetic fixtures; no app start is run.
This checks a selected projection, not full proc/death/loot implementation.
"""
import itertools
import json
import os
from pathlib import Path
import signal
import struct
import subprocess
import sys
from dataclasses import replace

from build_full134_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.combat134 import (CombatState,UnitState,ItemModifier,SpellModifier,
                                AbilityReference,AbilityLookupPanic,resolve_damage)
from core_spec.rng import next_u32_words

CATALOGUE=ROOT/'evidence/catalogue0134-20261101T003611.966001Z'


def declarations():
    public=json.loads((ROOT/'reports/2026-11-01-catalogue0134.json').read_text())
    memory=(CATALOGUE/'initial-memory.bin').read_bytes()
    if public['original_wasm_sha256']!=SOURCE_SHA or public['memory_image_sha256']!=sha(CATALOGUE/'initial-memory.bin'):
        raise ValueError('Current declaration source identity differs')
    result=[]
    for i in range(114):
        p=5463472+88*i
        identifier,length=struct.unpack_from('<II',memory,p+12)
        spell=struct.unpack_from('<I',memory,p+44)[0]
        result.append(AbilityReference(memory[identifier:identifier+length],spell))
    if len({x.id_bytes for x in result})!=114:
        raise ValueError('Current114 ability IDs differ')
    return tuple(result),memory[5411616:5411616+72].hex()


def fixtures(enemy_hex):
    b=f.from_float;cases=[]
    def add(group='baseline',hp=100,maximum=100,amount=10,**kw):
        cases.append({'id':len(cases),'group':group,'hp_bits':b(hp),'max_hp_bits':b(maximum),
                      'amount_bits':b(amount),'now_bits':b(10),'rng':[1,2,3,4],
                      'enemy_definition_hex':enemy_hex,**kw})
    for amount in (0,-0.,-10,1e-30,1,1.25,10,99,99.99999,100,100.00001,150,1e30,float('inf'),float('nan')):
        add(amount=amount)
    for hp in (0,-1,1,1.25,29.999,30,30.001,float('nan'),float('inf')):
        add(hp=hp)
    for offset in (124,380,388):
        add('item18',items=[[18,b(.2)],[18,b(.3)]],unit_overrides={str(offset):b(11)})
    add('item19',items=[[19,b(.2)]],unit_overrides={'416':1})
    add('item20',hp=29,items=[[20,b(.7)]])
    add('item21',items=[[21,b(.5)]],unit_overrides={'240':1})
    add('item28',items=[[28,b(.4)]],state_overrides={'1532':b(10)})
    add('additives',unit_overrides={'144':b(.2),'148':b(11),'152':b(.4),'156':b(11),
                                  '160':b(.7),'164':b(11),'368':b(.5)})
    for offset in (408,412):
        add('phase',unit_overrides={'64':0,str(offset):b(11)})
    add('not_running',phase=3,spell_modifiers=[[50,'missing-ability',b(.2),0]],unit_overrides={'356':b(11)})
    add('target_absent',target_id=2,spell_modifiers=[[50,'missing-ability',b(.2),0]],unit_overrides={'356':b(11)})
    add('target_dead',unit_overrides={'0':1})
    for spell,gate,value in itertools.product((0,133,845),(0,9.999999,10,10.000001,float('inf'),float('nan')),
                                              (-1,0,.1,.5,float('nan'))):
        add('tag50',spell_id=spell,unit_overrides={'356':b(gate)},spell_modifiers=[[50,'fireball',b(value),b(77)]])
    for threshold,hp,value in itertools.product((0,.25,.3,1,float('nan'),float('inf'),-float('inf')),
                                               (0,29.999,30,99,100,101,float('nan'),float('inf')),
                                               (-1,0,.2,1e20,float('nan'))):
        add('tag51',hp=hp,spell_modifiers=[[51,'fireball',b(threshold),b(value)]])
    for values in itertools.permutations((1e20,-1e20,.25)):
        for tag in (50,51):
            mods=[[tag,'fireball',b(x) if tag==50 else b(1),b(x) if tag==51 else 0] for x in values]
            add('ordered_sum',hp=50,unit_overrides={'356':b(11)},spell_modifiers=mods)
    for tag in (0,11,12,49,52,255,0xffffffff):
        add('ignored_tag',unit_overrides={'356':b(11)},spell_modifiers=[[tag,'missing-ability',b(.5),b(.9)]])
    for tag in (50,51):
        add('failed_gate_does_not_lookup',spell_modifiers=[[tag,'missing-ability',b(0),b(.9)]])
        add('spell0_does_not_lookup',spell_id=0,unit_overrides={'356':b(11)},
            spell_modifiers=[[tag,'missing-ability',b(1),b(.9)]])
    for hp,phase,extra in itertools.product((29,30,99),(408,412),(0,.25,.5,1)):
        add('M_plus_T_then_P',hp=hp,items=[[18,b(.2)],[20,b(.7)],[28,b(.4)]],
            state_overrides={'1532':b(10)},unit_overrides={'124':b(11),'356':b(11),'64':0,str(phase):b(11),'368':b(.125)},
            spell_modifiers=[[50,'cleave',b(10),0],[50,'fireball',b(extra),0],[51,'fireball',b(.5),b(.3)]])
    return cases


def model(c,abilities):
    mapping={124:'control_until_124_bits',380:'control_until_380_bits',388:'control_until_388_bits',
        356:'modifier_until_356_bits',416:'elite_416',240:'afflicted_240',144:'additive_144_bits',
        148:'additive_until_148_bits',152:'additive_152_bits',156:'additive_until_156_bits',
        160:'additive_160_bits',164:'additive_until_164_bits',368:'additive_368_bits',64:'kind_64',
        408:'phase_until_408_bits',412:'phase_until_412_bits',0:'marker'}
    unit=UnitState(1,c['hp_bits'],c['max_hp_bits'])
    unit=replace(unit,**{mapping[int(k)]:v for k,v in c.get('unit_overrides',{}).items()})
    state=CombatState(units=(unit,),items=tuple(ItemModifier(*x) for x in c.get('items',[])),
        spell_modifiers=tuple(SpellModifier(tag,identifier.encode(),x,y) for tag,identifier,x,y in c.get('spell_modifiers',[])),
        abilities=abilities,now_bits=c['now_bits'],shield_bits=c.get('state_overrides',{}).get('1532',0),phase_2579=c.get('phase',1))
    try:
        result=resolve_damage(state,c.get('target_id',1),c['amount_bits'],spell_id=c.get('spell_id',133))
        after=result.state.units[0];total=result.state.accounted_total;completed=True
    except AbilityLookupPanic:
        after=unit;total=0.;completed=False
    return {'completed':completed,'hp_bits':after.hp_bits,'marker':after.marker,
        'duration_bits':after.movement_duration_344_bits,'afflicted_240':after.afflicted_240,
        'death_time_bits':after.death_time_4_bits,'movement_time_bits':after.movement_time_340_bits,
        'accounted_total_bits':struct.pack('>d',total).hex()}


def main():
    abilities,enemy_hex=declarations()
    cases=fixtures(enemy_hex)
    for c in cases:c['expected']=model(c,abilities)
    out,manifest=build(['damage'])
    casefile=out/'combat134-cases.json';casefile.write_text(json.dumps(cases,allow_nan=False,indent=2)+'\n')
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    if sha(runtime)!='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0':
        raise ValueError('Pinned Node identity differs')
    command=[str(runtime),'--max-old-space-size=512','--wasm-max-mem-pages=512',
             str(ROOT/'scripts/run_combat134_full_oracle.mjs'),str(out),str(casefile)]
    results=out/'combat134-original-results.jsonl'
    with results.open('w')as stdout,(out/'combat134-stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise SystemExit('Owned full914 comparison exceeded60s')
    if code:raise SystemExit(f'Full new914 run failed; inspect {out}')
    rows=[json.loads(line) for line in results.read_text().splitlines()]
    if len(rows)!=len(cases) or [x['id']for x in rows]!=list(range(len(cases))):
        raise ValueError('Original output IDs/order differ')
    mismatches=[];draws={}
    for c,actual in zip(cases,rows):
        difference={k:[v,actual[k]] for k,v in c['expected'].items() if v!=actual[k]
                    and not(k=='hp_bits'and f.is_nan(v)and f.is_nan(actual[k]))}
        if difference:mismatches.append({'id':c['id'],'group':c['group'],'difference':difference})
        current=tuple(c['rng']);found=None
        for n in range(101):
            if current==tuple(actual['rng']):found=n;break
            _,current=next_u32_words(current)
        draws[str(c['id'])]=found
    mismatchfile=out/'combat134-mismatches.json';mismatchfile.write_text(json.dumps(mismatches,indent=2,allow_nan=False)+'\n')
    runtime_receipt=json.loads((out/'combat134-runtime.json').read_text())
    files=('scripts/build_full134_oracle.py','scripts/full134_host.mjs','scripts/check_combat134_full_spec.py',
           'scripts/run_combat134_full_oracle.mjs','reconstruction/core_spec/combat134.py',
           'reconstruction/core_spec/binary32.py','reconstruction/core_spec/rng.py')
    receipt={'version':'0.134.0','build':'983346a7','original_wasm_sha256':SOURCE_SHA,
        'module_sha256':manifest['module_sha256'],'original_function':914,'original_full_function_executed':True,
        'case_count':len(cases),'mismatch_count':len(mismatches),'completed':sum(x['completed']for x in rows),
        'groups':{g:sum(c['group']==g for c in cases) for g in sorted({c['group'] for c in cases})},
        'fields_compared':list(cases[0]['expected']),'runtime':runtime_receipt,'rng_draw_count_observations':draws,
        'only_changed_source_section':7,'dependency_shims':[],
        'source_sha256':{p:sha(ROOT/p)for p in files},
        'artifact_sha256':{p.name:sha(p)for p in (casefile,results,mismatchfile,out/'combat134-runtime.json')},
        'declaration_memory_sha256':sha(CATALOGUE/'initial-memory.bin'),'enemy_definition_address':5411616,
        'enemy_definition_hex':enemy_hex,'enemy_definition_sha256':__import__('hashlib').sha256(bytes.fromhex(enemy_hex)).hexdigest(),
        'limitations':['Ordinary unique target, spell0/133/845, empty abilities/procs/talent producers and controlled item/rawtag50/51 records.',
            'Full original death/callees execute if reached, but independent model compares only core HP/death/accounted fields.',
            'Per-spell statistics, packets, loot, XP and death RNG continuation are not independently implemented.',
            'Gated missing ability ID panic, linked targets and special kind3 not exercised by this corpus.',
            'NaN HP payloads compare by category; all other compared values exact bits.',
            'No application start, game UI, network or user save APIs called.']}
    if sha(SOURCE)!=SOURCE_SHA:raise ValueError('Original changed during run')
    (out/'combat134-comparison.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'run':str(out),'version':'0.134.0','complete_original914':True,
                      'cases':len(cases),'mismatches':len(mismatches),'completed':receipt['completed']}))
    if mismatches:raise SystemExit('Independent current damage projection differs')


if __name__=='__main__':main()
