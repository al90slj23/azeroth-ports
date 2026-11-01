#!/usr/bin/env python3
"""Execute unchanged full original933/internal callees against combat projection.

Only explicit research exports differ. All878 original host imports throw;
no implicit WASM start exists, and no application start export is invoked.
Each fixture uses a fresh instance and original allocator-owned synthetic state.
"""
from dataclasses import replace
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
from pathlib import Path
from build_full_function_oracle import ROOT, build
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.combat import CombatState, UnitState, ItemModifier, resolve_damage
from core_spec.rng import next_u32_words


def fixtures():
    b=f.from_float
    cases=[]
    def add(hp=100,amount=10,**kw):
        cases.append(dict(id=len(cases),hp_bits=b(hp),max_hp_bits=b(100),amount_bits=b(amount),
                          now_bits=b(10),rng=[1,2,3,4],**kw))
    for amount in (0,-0.,-10,1e-30,1,1.25,10,99,99.99999,100,100.00001,150,1e30,float('inf'),float('nan')):
        add(amount=amount)
    for hp in (0,-1,1,1.25,29.999,30,30.001,float('nan'),float('inf')):
        add(hp=hp)
    add(amount=10,items=[[18,b(.2)],[18,b(.3)]],unit_overrides={'124':b(11)})
    add(amount=10,items=[[19,b(.2)]],unit_overrides={'412':1})
    add(hp=29,amount=10,items=[[20,b(.7)]])
    add(amount=10,items=[[21,b(.5)]],unit_overrides={'240':1})
    add(amount=10,items=[[28,b(.4)]],state_overrides={'1348':b(10)})
    add(amount=10,unit_overrides={'144':b(.2),'148':b(11),'152':b(.4),'156':b(11),
                                 '160':b(.7),'164':b(11),'364':b(.5)})
    add(amount=10,unit_overrides={'64':0,'408':b(11)})
    add(amount=10,unit_overrides={'64':0,'404':b(11)})
    return cases


def model(c):
    mapping={124:'control_until_124_bits',412:'elite_412',240:'afflicted_240',144:'additive_144_bits',
       148:'additive_until_148_bits',152:'additive_152_bits',156:'additive_until_156_bits',
       160:'additive_160_bits',164:'additive_until_164_bits',364:'additive_364_bits',64:'kind_64',
       404:'phase_until_404_bits',408:'phase_until_408_bits'}
    unit=UnitState(1,c['hp_bits'],c['max_hp_bits'])
    unit=replace(unit,**{mapping[int(k)]:v for k,v in c.get('unit_overrides',{}).items()})
    state=CombatState((unit,),tuple(ItemModifier(tag,b) for tag,b in c.get('items',[])),
                      c['now_bits'],c.get('state_overrides',{}).get('1348',0))
    r=resolve_damage(state,1,c['amount_bits'],spell_id=133,spell_category=0)
    return {'hp_bits':r.new_hp_bits,'marker':r.target.marker,'duration_bits':r.target.movement_duration_344_bits,
            'afflicted_240':r.target.afflicted_240,'death_time_bits':r.target.death_time_4_bits,
            'movement_time_bits':r.target.movement_time_340_bits,
            'accounted_total_bits':struct.pack('>d',r.state.accounted_total).hex()}


def main():
    directory,manifest=build([933,106495])
    cases=fixtures();casefile=directory/'combat-full-cases.json'
    casefile.write_text(json.dumps(cases,allow_nan=False,indent=2)+'\n')
    resultfile=directory/'combat-full-results.json'
    runtime=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
    command=[str(runtime),'--max-old-space-size=512',str(ROOT/'scripts/run_combat_full_oracle.mjs'),
      str(directory),str(ROOT.parent/'android/assets/latest-web-core/wenilla_bg.wasm'),str(casefile),str(resultfile)]
    with (directory/'combat-full.stdout.log').open('w') as out,(directory/'combat-full.stderr.log').open('w') as err:
        child=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=45)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGKILL);child.wait();raise SystemExit('Owned full933 fixture run exceeded deadline')
    if code:raise SystemExit('Full933 run failed: '+(directory/'combat-full.stderr.log').read_text())
    actual=json.loads(resultfile.read_text())
    if actual['actual_host_calls'] or actual['case_count']!=len(cases):raise SystemExit('Host call/coverage mismatch')
    mismatches=[];draws={}
    for c,got in zip(cases,actual['outputs']):
        if got['id']!=c['id'] or not got['completed']:
            mismatches.append({'id':c['id'],'error':got});continue
        want=model(c)
        diff={k:[v,got[k]] for k,v in want.items() if v!=got[k] and not(k=='hp_bits' and f.is_nan(v) and f.is_nan(got[k]))}
        if diff:mismatches.append({'id':c['id'],'input':c,'difference':diff})
        current=tuple(c['rng']);found=None
        for n in range(101):
            if current==tuple(got['rng']):found=n;break
            _,current=next_u32_words(current)
        draws[str(c['id'])]=found
    (directory/'combat-full-mismatches.json').write_text(json.dumps(mismatches,indent=2)+'\n')
    report={'original_wasm_sha256':manifest['original_wasm_sha256'],'research_module_sha256':manifest['module_sha256'],
      'run_directory':str(directory),'case_count':len(cases),'completed':actual['completed'],
      'mismatch_count':len(mismatches),'actual_host_calls':actual['actual_host_calls'],
      'original_full_933_executed':True,'original_internal_callees_unchanged':True,
      'only_changed_section':7,'no_implicit_or_application_start_executed':True,
      'stub_callees':[],'host_import_policy':'all878 imports throw; zero host calls observed',
      'fresh_instance_per_fixture':True,'synthetic_state_original_allocator_owned':True,
      'rng_draw_count_by_case':draws,
      'scope':'Ordinary unique target, spell133/school2, no abilities/procs/talents; controlled item/debuff/phase cases included.',
      'limitations':['Finite synthetic corpus, not original gameplay tick.',
         'Other target kinds, proc/death/loot branches and subsequent event consumers not covered.',
         'RNG draw-count observations apply to exact fixtures; independent combat projection still excludes death RNG.',
         'NaN payload compared by category.','No network/UI/save APIs or application start invoked.'],
      'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [ROOT/'scripts/run_combat_full_oracle.mjs',ROOT/'scripts/check_combat_full_spec.py',ROOT/'reconstruction/core_spec/combat.py']}}
    (directory/'combat-full-summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'run_directory':str(directory),'case_count':len(cases),'completed':actual['completed'],
                      'mismatch_count':len(mismatches),'rng_draw_count_by_case':draws}))
    if mismatches:raise SystemExit(1)


if __name__=='__main__':main()
