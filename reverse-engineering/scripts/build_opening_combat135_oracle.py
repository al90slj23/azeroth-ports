#!/usr/bin/env python3
"""Private fixed135 full opening plus old14-stage tail export-only admission.

No shared builder/model is changed. --pilot performs one original observation
case with an explicit external clock scheduler, never a model comparison or880.
"""
from datetime import datetime,timezone
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode=True
from build_full135_oracle import (ROOT,SOURCE,SOURCE_SHA,SOURCE_BYTES,parse_source,
    section_list,export_entries,ROLES as CORE_ROLES,APPROVED_BODY_SHA,VALIDATOR_SHA)
from build_world_snapshot135_oracle import ROLES as WORLD_ROLES,GLOBAL_BYTES
from build_upgrade134_oracle import unsigned,sha

STAGES=(('player','player_tick'),('extra','auto_cast'),('owned_effects','owned_effect_tick'),
    ('hits','process_hits'),('area','area_tick'),('effects','effect_tick'),
    ('deadline','deadline_tick'),('secondary','secondary_hits'),('ai','update_units'),
    ('collect','collect_pickups'),('claims','claim_tick'),('spawn','spawn_tick'),
    ('special','special_tick'),('terminal','terminal_tick'))
STACK_EXPORT='research_opening_combat135_stack'
SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_begin1089.memory'
SNAPSHOT_SHA='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def build_opening_combat135(directory=None):
    out=Path(directory).resolve()if directory else ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-combat0135-oracle-%Y%m%dT%H%M%S.%fZ')
    if not out.is_relative_to(Path('/Volumes/RuiRui4TB')):raise ValueError('4T evidence required')
    out.mkdir(parents=True,exist_ok=directory is not None)
    raw=SOURCE.read_bytes();assert len(raw)==SOURCE_BYTES and hashlib.sha256(raw).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,_=parse_source(raw);sections=section_list(raw)
    assert 8 not in[s[0]for s in sections]
    global_section=next(s for s in sections if s[0]==6)
    assert raw[global_section[2]:global_section[3]].hex()==GLOBAL_BYTES
    export=next(s for s in sections if s[0]==7);original_exports,first=export_entries(raw,export)
    assert ('__wbindgen_malloc',0,91941)in original_exports
    roles={'cached_construct':WORLD_ROLES['cached_construct'],'begin_run':WORLD_ROLES['begin_run']}
    for _,role in STAGES:roles[role]=(*CORE_ROLES[role],APPROVED_BODY_SHA[role])
    roles['select_ability']=(*CORE_ROLES['select_ability'],APPROVED_BODY_SHA['select_ability'])
    additions=b'';details=[]
    for role,(index,params,results,expected)in sorted(roles.items()):
        assert types[decl[index-len(imports)]]==(params,results)
        begin,end=bodies[index];assert hashlib.sha256(raw[begin:end]).hexdigest()==expected
        name='research_opening_combat135_'+role;encoded=name.encode()
        additions+=unsigned(len(encoded))+encoded+b'\x00'+unsigned(index)
        details.append(dict(role=role,index=index,export=name,parameters_hex=params.hex(),results_hex=results.hex(),
            body_sha256=expected,body_start=begin,body_end=end))
    encoded=STACK_EXPORT.encode();additions+=unsigned(len(encoded))+encoded+b'\x03\x00'
    payload=unsigned(len(original_exports)+len(details)+1)+raw[first:export[3]]+additions
    changed=raw[:export[1]]+b'\x07'+unsigned(len(payload))+payload+raw[export[3]:]
    fresh=section_list(changed);assert[s[0]for s in fresh]==[s[0]for s in sections]
    unchanged=[]
    for before,after in zip(sections,fresh):
        if before[0]!=7:
            assert raw[before[1]:before[3]]==changed[after[1]:after[3]]
            unchanged.append(dict(section=before[0],sha256=hashlib.sha256(raw[before[1]:before[3]]).hexdigest()))
    exports,_=export_entries(changed,next(s for s in fresh if s[0]==7))
    assert exports[:len(original_exports)]==original_exports and len(exports)==len(original_exports)+len(details)+1
    module=out/'opening-combat135-exports.wasm';module.write_bytes(changed)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    done=subprocess.run([str(validator),'--enable-all',str(module)],capture_output=True,timeout=45)
    (out/'validation.stdout').write_bytes(done.stdout);(out/'validation.stderr').write_bytes(done.stderr);assert done.returncode==0
    manifest=dict(kind='fixed135-real-opening-plus-controlled14-tail-not-full880',schema_version=2,version='0.135.1',
        historical_build_alias='0898d5e3',actual_consumed_web_build='90898d5e3',
        original_wasm_sha256=SOURCE_SHA,module_file=module.name,module_sha256=sha(module),module_bytes=len(changed),
        original_exports=original_exports,roles=details,only_changed_section=7,unchanged_nonexport_sections=unchanged,
        source_implicit_start=False,memory_page_cap=4096,denied_function_imports=878,
        stack_export=dict(name=STACK_EXPORT,index=0,initial_value=1048576,global_section_hex=GLOBAL_BYTES),
        stages=[dict(kind=kind,role=role,index=CORE_ROLES[role][0],parameters_hex=CORE_ROLES[role][1].hex(),
            results_hex=CORE_ROLES[role][2].hex())for kind,role in STAGES],
        owned_tick1076='Called inside full2088; not a second standalone stage. Extra stage is916.',
        selection=dict(role='select_ability',index=CORE_ROLES['select_ability'][0],
            parameters_hex=CORE_ROLES['select_ability'][1].hex(),results_hex=CORE_ROLES['select_ability'][2].hex(),
            action=dict(kind='select',index='explicit uint32 choice index'),clock_advanced=False),
        budgets=dict(cases=1,actions_per_case=200,output_bytes=268435456),
        original_allocator=dict(index=91941,export='__wbindgen_malloc'),validator_sha256=VALIDATOR_SHA,
        target_executed_by_builder=False,full880_called=False,shared_builders_changed=False)
    save(out/'manifest.json',manifest);assert sha(SOURCE)==SOURCE_SHA
    return out,manifest


# Convenient private API for the root's expected-first driver.
build=build_opening_combat135


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    except PermissionError:return None
    return False


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pilot',action='store_true');args=parser.parse_args()
    out,manifest=build_opening_combat135()
    sources={str(path.relative_to(ROOT)):sha(path)for path in(Path(__file__).resolve(),
        ROOT/'scripts/run_opening_combat135_oracle.mjs',ROOT/'scripts/build_full135_oracle.py',
        ROOT/'scripts/build_world_snapshot135_oracle.py',ROOT/'scripts/build_upgrade134_oracle.py')}
    for name in sources:
        target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    if not args.pilot:print(json.dumps(dict(directory=str(out),module_sha256=manifest['module_sha256'],prepared_only=True)));return
    assert sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    bits=struct.unpack('<I',struct.pack('<f',.025))[0]
    save(out/'inputs.json',[dict(id=0,input=dict(class_byte=1,race_byte=1,region_index=0,
        app_lcg_seed_u64='0',object_id_u64='0',companion_tags=[255,255]),
        actions=[dict(kind='controlled_tail_frame',dt_bits=bits)])])
    save(out/'config.json',dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,
        app_pointer=14549000,world_pointer=26204808,input_path=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),
        clock_scheduler='explicit_external_f32_add_G2352_not_original880',
        locale=dict(kind='preserve_initialized_snapshot',expected_language_index=0)))
    frozen={name:sha(out/name)for name in('inputs.json','config.json','manifest.json',manifest['module_file'])}
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',
        str(ROOT/'scripts/run_opening_combat135_oracle.mjs'),str(out),str(out/'config.json')]
    began=time.monotonic();launcher_error=None
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,
            env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,timeout_seconds=60,
            pilot_original_observation_only=True,independent_expected_generated=False))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as error:launcher_error=str(error)
        finally:
            if child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=2)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    terminal=dict(pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True))
    runtime=json.loads((out/'opening-combat135-runtime.json').read_text())if(out/'opening-combat135-runtime.json').exists()else None
    after={name:sha(ROOT/name)for name in sources}
    receipt=dict(kind='original_observation_pilot_not_model_validation',source_sha256_before=sources,
        source_sha256_after=after,source_unchanged=sources==after,frozen_inputs=frozen,
        inputs_unchanged=all(sha(out/name)==digest for name,digest in frozen.items()),runtime=runtime,
        process=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,terminal=terminal,
            seconds=time.monotonic()-began,launcher_error=launcher_error),
        outputs={name:sha(out/name)for name in('stdout.jsonl','stderr.log')},
        new_independent_model_cases=0,new_full880_frames=0,whole_game_complete=False)
    save(out/'pilot-receipt.json',receipt)
    print(json.dumps(dict(directory=str(out),exit_code=child.returncode,terminal=terminal,
        runtime=runtime,pilot_receipt_sha256=sha(out/'pilot-receipt.json'))))
    assert sources==after and receipt['inputs_unchanged'] and launcher_error is None
    if child.returncode:raise SystemExit(child.returncode)


if __name__=='__main__':main()
