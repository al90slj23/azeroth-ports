#!/usr/bin/env python3
"""Compare independent new80B records with complete official0.135.1 1073.

Run --phase pilot first. Every expected byte is computed by ability_state135;
the original helper calls and complete1072 tail remain unchanged in the oracle.
"""
import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import signal
import struct
import subprocess
import sys
import time

from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, build
from build_upgrade134_oracle import sha
from trace_new_ability135 import static_snapshot

SOURCE_FILES = ('scripts/check_new_ability135_full_spec.py', 'scripts/run_new_ability135_full_oracle.mjs',
    'scripts/trace_new_ability135.py', 'scripts/build_full135_oracle.py', 'scripts/build_upgrade134_oracle.py',
    'scripts/full135_host.mjs', 'scripts/extract_catalogue135.py', 'reconstruction/core_spec/ability_state135.py',
    'reconstruction/core_spec/ability_state.py', 'reconstruction/core_spec/upgrade_values.py',
    'reconstruction/core_spec/binary32.py','scripts/extract_catalogue134.py')


def source_hashes():
    return {p:sha(ROOT/p) for p in SOURCE_FILES}


IMPORT_SOURCE_HASHES = source_hashes()
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.ability_state135 import (AbilityModifier135 as Modifier, DEFINITIONS, TIER_DAMAGE,
    TIER_COOLDOWN, initialize_ability, modifier_additional_bytes, tier_adjustment_kind,
    SelectionState135, accept_new_ability_selection)
from core_spec.ability_state import AbilityRecord, NewAbilityCard, UnresolvedAbilityEffect
from core_spec import binary32 as f

RUNTIME = ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
RUNTIME_VERSION = 'v22.23.4'
RUNTIME_FLAGS = ('--max-old-space-size=512','--wasm-max-mem-pages=512')


def pilot_cases():
    for name in (b'cleave',b'battle_shout',b'holy_light',b'holy_shield',b'bloodrage',b'arcane_power'):
        for tier in (0,1,4):
            yield {'group':'pilot-actual-definition-branches','ability_id':name,'tier':tier}
    yield {'group':'pilot-explicit-modifiers','ability_id':b'cleave','tier':4,
        'modifiers':tuple(Modifier(k,f.from_float(v)) for k,v in enumerate((.1,.2,2.5,.3,.4,.5,.6)))}
    yield {'group':'pilot-filter-ID-list','ability_id':b'holy_light','tier':2,
        'modifiers':(Modifier(0,f.from_float(.5),2,ability_ids=(b'no',b'holy_light')),)}
    yield {'group':'pilot-preexisting-owned-preserved','ability_id':b'cleave','tier':3,
        'owned':(AbilityRecord(DEFINITIONS[b'fireball'].pointer),)}


def full_cases():
    for name in DEFINITIONS:
        for tier in range(5):
            yield {'group':'all114-tier0..4-empty-modifiers','ability_id':name,'tier':tier}
    # The fifth nonzero entry is original behavior, beyond current candidate tiers.
    for name in DEFINITIONS:
        yield {'group':'all114-original-tier5-table-entry','ability_id':name,'tier':5}
    values = [0,0x80000000,1,0x80000001,0x3efffffe,0x3effffff,0x3f000000,0x3f000001,
        f.from_float(.1),f.from_float(-.1),f.from_float(.6),f.from_float(1),f.from_float(1.5),
        f.from_float(2.5),f.from_float(-2.5),f.from_float(16777216),f.from_float(4294967040),
        f.from_float(4294967296),0x7f7fffff,0xff7fffff,0x7f800000,0xff800000,0x7fc00001]
    for kind in tuple(range(9))+(255,):
        for value in values:
            for tier in (0,2,4):
                yield {'group':'modifier-every-kind-binary32-and-u32-edges','ability_id':b'cleave',
                    'tier':tier,'modifiers':(Modifier(kind,value),)}
    for name in (b'cleave',b'holy_light',b'holy_shield',b'faerie_fire',b'arcane_power'):
        d=DEFINITIONS[name]
        filters=[Modifier(0,f.from_float(.25),tag) for tag in (0,5,6,7,8,255)]
        filters += [Modifier(0,f.from_float(.25),1,ability_id=identifier) for identifier in (name,b'no',b'',name+b'_')]
        filters += [Modifier(0,f.from_float(.25),2,ability_ids=identifiers) for identifiers in ((),(name,),(b'no',name),(name,b'no'),(b'no',b''),(name,name))]
        filters += [Modifier(0,f.from_float(.25),3,value) for value in (d.school,(d.school+1)&255)]
        filters += [Modifier(0,f.from_float(.25),4,value) for value in (d.execution_kind,(d.execution_kind+1)&255)]
        for modifier in filters:
            for tier in (0,4):
                yield {'group':'modifier-all-filter-dispatch-match-and-miss','ability_id':name,
                    'tier':tier,'modifiers':(modifier,)}
    # This vector tests all7 output words on all114 definitions together.
    for name in DEFINITIONS:
        modifiers=tuple(Modifier(k,f.from_float(v),1,ability_id=name)
            for k,v in enumerate((.123,.234,2.5,.345,.456,.567,.678)))
        for tier in (0,4):
            yield {'group':'all114-all-seven-additional-words','ability_id':name,'tier':tier,'modifiers':modifiers}
    # Targets accumulate before rounding; binary32 order differs under cancellation.
    triples=((16777216,1,-16777216),(16777216,-16777216,1),(.25,.25,0),(.5,.5,.5),
        (-.5,.5,.5),(4294967040,256,-256),(1e20,-1e20,3),(1e20,3,-1e20))
    for kind in range(7):
        for values_ in triples:
            for tier in range(5):
                yield {'group':'ordered-f32-sums-before-round-clamp','ability_id':b'cleave','tier':tier,
                    'modifiers':tuple(Modifier(kind,f.from_float(x)) for x in values_)}
    # Synthetic definition fields exercise the complete original classification,
    # including branches absent from the114 actual declarations.
    overrides=[]
    overrides += [{'execution_kind':9,'effect_tag':tag} for tag in tuple(range(17))+(255,0xffffffff)]
    overrides += [{'execution_kind':11,'kinds':kinds} for kinds in ((),(1,),(0,),(1,0),(1,2,3,4))]
    overrides += [{'execution_kind':execution,'base_damage_bits':value}
        for execution in (0,8,10,12,255) for value in (0,0x80000000,0xbf800000,1,0x7f800000,0x7fc00001)]
    for override in overrides:
        for tier in range(5):
            yield {'group':'synthetic-definition-tier-classification','ability_id':b'cleave',
                'tier':tier,'definition_override':override}
    rng=random.Random(0x013426967)
    numeric=[f.from_float(x)for x in (-100,-2,-.6,-.1,0,.01,.1,.2,.6,1,2,100,16777216)]
    for _ in range(400):
        name=rng.choice(tuple(DEFINITIONS));definition=DEFINITIONS[name];modifiers=[]
        for _ in range(rng.randrange(1,24)):
            tag=rng.randrange(9)
            modifiers.append(Modifier(rng.randrange(9),rng.choice(numeric),tag,
                rng.choice((definition.school,definition.execution_kind,255)),
                rng.choice((name,b'no')),(b'no',name)if rng.randrange(2)else(b'no',)))
        yield {'group':'seeded-mixed-ordered-explicit-modifiers','ability_id':name,'tier':rng.randrange(5),
            'modifiers':tuple(modifiers)}
    for phase in (0,1,3,255):
        yield {'group':'phase-entry-guard','ability_id':b'cleave','tier':4,'phase':phase}
    for kind in (0,1,2,255):
        for index in (0,1,-1):
            if kind in (1,2) and index==0:
                continue  # Successful nondefault queue completion remains pending.
            yield {'group':'kind-index-entry-guards','ability_id':b'holy_light','tier':2,
                'selection_kind':kind,'choice_index':index}
    for count in (1,2,3):
        owned=tuple(replace(AbilityRecord(DEFINITIONS[b'fireball'].pointer),level=5+i,
            damage_bits=f.from_float(2+i),counts=(i,0,0,0,0)) for i in range(count))
        for tier in range(5):
            yield {'group':'append-preserves-existing-owned-records','ability_id':b'cleave','tier':tier,'owned':owned}


def encode_modifier(m):
    return {'kind':m.kind,'value_bits':m.value_bits,'filter_tag':m.filter_tag,'filter_value':m.filter_value,
        'ability_id_hex':m.ability_id.hex(),'ability_ids_hex':[v.hex()for v in m.ability_ids]}


def materialize(phase,static):
    actual={d['ability_id']:d for d in static['definitions']};cases=[]
    for i,c in enumerate(pilot_cases()if phase=='pilot'else full_cases()):
        name=c['ability_id'];definition=DEFINITIONS[name];override=c.get('definition_override')
        if override:definition=replace(definition,**override)
        modifiers=c.get('modifiers',());owned=c.get('owned',())
        state=SelectionState135(owned,(NewAbilityCard(name,c['tier']),),c.get('phase',2),c.get('selection_kind',0))
        selected=accept_new_ability_selection(state,c.get('choice_index',0),{name:definition},modifiers=modifiers)
        # The independent API deliberately does not claim this shared tail; the
        # empty synthetic queue domain's fields are separately compared here.
        expected={'id':i,'owned_records_hex':[r.to_bytes().hex()for r in selected.state.owned],
            'owned_count1664':len(selected.state.owned),'phase2587':1 if selected.accepted else state.phase2587,
            'selection_kind2585':255 if selected.accepted else state.selection_kind2585,
            'pending2376':0 if selected.accepted else 1,'candidate_count1912':0 if selected.accepted else 1,
            'host_calls':0}
        cases.append({'id':i,'group':c['group'],'ability_id':name.decode(),'definition_pointer':definition.pointer,
            'definition_raw88_hex':actual[name.decode()]['raw88_hex'],'definition_override':override,
            'tier':c['tier'],'modifiers':[encode_modifier(m)for m in modifiers],
            'owned_hex':[r.to_bytes().hex()for r in owned],'phase':state.phase2587,
            'selection_kind':state.selection_kind2585,'choice_index':c.get('choice_index',0),'expected':expected})
    # Definition override kind lists start as tuples in the independent model;
    # normalize the interchange representation before freezing JSON readback.
    return json.loads(json.dumps(cases,allow_nan=False))


def compare(expected,actual):
    failures=[]
    for key,value in expected.items():
        if key=='owned_records_hex':continue
        if actual.get(key)!=value:failures.append({'field':key,'expected':value,'actual':actual.get(key)})
    records=actual.get('owned_records_hex',[])
    if len(records)!=len(expected['owned_records_hex']):
        failures.append({'field':'owned_records_hex.length','expected':len(expected['owned_records_hex']),'actual':len(records)})
    int_words={0,1,5,8,9,10,11,12,15}
    for i,(wanted,got)in enumerate(zip(expected['owned_records_hex'],records)):
        raw=bytes.fromhex(got)
        if len(raw)!=80:raise ValueError('Original returned a truncated owned record')
        for word,(a,b)in enumerate(zip(struct.unpack('<20I',bytes.fromhex(wanted)),struct.unpack('<20I',raw))):
            if a!=b and not(word not in int_words and f.is_nan(a)and f.is_nan(b)):
                failures.append({'field':f'owned[{i}]+{word*4}','expected':f'{a:08x}','actual':f'{b:08x}'})
    return failures


def run_oracle(module_directory,out,casefile):
    if sha(RUNTIME)!=RUNTIME_SHA:raise ValueError('Pinned Node identity differs')
    version=subprocess.check_output([str(RUNTIME),'--version'],text=True,timeout=10).strip()
    if version!=RUNTIME_VERSION:raise ValueError('Pinned Node version differs')
    command=[str(RUNTIME),*RUNTIME_FLAGS,str(ROOT/'scripts/run_new_ability135_full_oracle.mjs'),
        str(module_directory),str(casefile),str(out)]
    resultfile=out/'results.jsonl';stderr=out/'stderr.log';start=time.monotonic();timed_out=False
    with resultfile.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        pid=child.pid;pgid=os.getpgid(pid)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:
            timed_out=True;os.killpg(pgid,signal.SIGKILL);code=child.wait()
    receipt={'command':command,'pid':pid,'pgid':pgid,'owned_process_group':pid==pgid,
        'runtime_version':version,'runtime_sha256':RUNTIME_SHA,'runtime_flags':list(RUNTIME_FLAGS),
        'deadline_seconds':60,'timed_out':timed_out,'exit_code':code,'elapsed_seconds':round(time.monotonic()-start,3),
        'stderr_bytes':stderr.stat().st_size,'stderr_sha256':sha(stderr),'result_sha256':sha(resultfile)}
    (out/'process.json').write_text(json.dumps(receipt,indent=2)+'\n')
    if sha(RUNTIME)!=RUNTIME_SHA:raise ValueError('Pinned Node changed during run')
    if code or timed_out:raise RuntimeError(f'Original1072 oracle failed; evidence retained at {out}')
    return resultfile,receipt


def check(phase,full_directory=None):
    sources=source_hashes()
    if sources!=IMPORT_SOURCE_HASHES:raise ValueError('Imported source changed')
    static=static_snapshot()
    raw=static['definitions']
    if len(raw)!=len(DEFINITIONS)or len(raw)!=114:raise ValueError('Current definition count differs')
    for d in raw:
        got=DEFINITIONS[d['ability_id'].encode()]
        for key in ('pointer','execution_kind','school','effect_tag','base_damage_bits','kinds'):
            if getattr(got,key)!=(tuple(d[key])if key=='kinds'else d[key]):raise ValueError('Frozen definition differs: '+key)
    if tuple(static['tables']['damage_bits'])!=TIER_DAMAGE or tuple(static['tables']['cooldown_bits'])!=TIER_COOLDOWN:
        raise ValueError('Original current tier tables differ')
    # Unknown modifier-producer state is an error, even at tier0.
    for fn in (initialize_ability,modifier_additional_bytes):
        try:fn(DEFINITIONS[b'cleave'])
        except UnresolvedAbilityEffect:pass
        else:raise ValueError('Unknown modifier producer was silently treated as empty')
    if full_directory is None:full_directory,_=build(['select_ability'])
    full_directory=Path(full_directory).resolve()
    module_manifest=full_directory/'manifest.json';manifest=json.loads(module_manifest.read_text())
    module=full_directory/manifest['module_file'];module_hash=sha(module);manifest_hash=sha(module_manifest)
    if module_hash!=manifest['module_sha256']or manifest['original_wasm_sha256']!=SOURCE_SHA:
        raise ValueError('Current full module differs')
    out=full_directory/datetime.now(timezone.utc).strftime(f'new-ability135-{phase}-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True,exist_ok=False)
    for name,wanted in sources.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
        if sha(p)!=wanted:raise ValueError('Source snapshot differs')
    (out/'sources-before.json').write_text(json.dumps(sources,indent=2)+'\n')
    cases=materialize(phase,static);casefile=out/'fixtures.jsonl'
    casefile.write_text(''.join(json.dumps(c,separators=(',',':'),allow_nan=False)+'\n'for c in cases))
    case_hash=sha(casefile)
    resultfile,process=run_oracle(full_directory,out,casefile)
    result_hash=sha(resultfile)
    persisted=[json.loads(x)for x in casefile.read_text().splitlines()]
    rows=[json.loads(x)for x in resultfile.read_text().splitlines()]
    ids=list(range(len(cases)))
    if persisted!=cases or [c['id']for c in persisted]!=ids or [c['id']for c in rows]!=ids:
        raise ValueError('Persisted fixture/result IDs, order, uniqueness or count differ')
    failures=[]
    for c,got in zip(cases,rows):
        failures.extend(dict(id=c['id'],group=c['group'],**f)for f in compare(c['expected'],got))
    mismatch=out/'mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
    after=source_hashes();(out/'sources-after.json').write_text(json.dumps(after,indent=2)+'\n')
    if after!=sources or sha(SOURCE)!=SOURCE_SHA or sha(module)!=module_hash or sha(module_manifest)!=manifest_hash:
        raise ValueError('Frozen source/module/manifest changed during run')
    if sha(casefile)!=case_hash or sha(resultfile)!=result_hash:raise ValueError('Fixtures/results changed during comparison')
    runtime=json.loads((out/'runtime.json').read_text())
    report={'version':'0.135.1','build':'0898d5e3','phase':phase,'status':'passed'if not failures else'failed',
        'cases':len(cases),'case_groups':dict(Counter(c['group']for c in cases)),
        'mismatch_fields':len(failures),'mismatch_cases':len({f['id']for f in failures}),
        'original_wasm_sha256':SOURCE_SHA,'original_function':1072,'complete_original_function_executed':True,
        'original_helpers_executed':[26967,26591,85719],'replacement_callees':[],
        'only_changed_original_section':7,'comparison_fields':['every owned80B word','owned count1664',
            'phase2587','selection kind2585','pending2376','candidate count1912','host call count'],
        'nan_comparison':'NaN classification only; all non-NaN floating words and all u32 words require exact bits',
        'modifier_context':'Explicit synthetic snapshot; unknown/default producer state raises. Real producers remain pending.',
        'original_runtime':runtime,'process':process,'source_sha256':sources,'source_freeze_before_after':True,
        'source_snapshot_directory':str(out/'source-snapshot'),'fixture_ids_unique_contiguous_and_ordered':True,
        'result_ids_unique_contiguous_and_ordered':True,'fixture_sha256':case_hash,'results_sha256':result_hash,
        'mismatches_sha256':sha(mismatch),'research_module_sha256':module_hash,'research_manifest_sha256':manifest_hash,
        'static_evidence_directory':static['evidence_directory'],'static_guards':static['guards'],
        'runtime_evidence_directory':str(out),'full_module_directory':str(full_directory),
        'tier_adjustment_actual_definition_counts':dict(Counter(tier_adjustment_kind(d)for d in DEFINITIONS.values())),
        'limitations':['Synthetic warrior/human level1, explicit ability-modifier snapshots and empty equipment/loot.',
            'Original1072 tail executes; independent model exposes shared postprocessing,1512 and4600 as pending effects.',
            'No real talent/equipment modifier producers, save compatibility, whole-core or playable-game claim.',
            'Current candidate tiers0..4 covered; tier5 is extra original helper-domain evidence.',
            'Other pending queues,next-choice generation and other candidate variants are outside this checker.'],
        'application_start_called':False,'network_used':False,'app_or_save_writes':False}
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'phase':phase,'cases':len(cases),'mismatch_fields':len(failures),
        'evidence_directory':str(out),'full_module_directory':str(full_directory),'failures':failures[:10]},indent=2))
    if failures:raise SystemExit(1)
    if phase=='full':
        (ROOT/'reports/2026-11-01-new-ability0135-spec.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=('pilot','full'),default='pilot')
    parser.add_argument('--full-directory',type=Path)
    args=parser.parse_args();check(args.phase,args.full_directory)
