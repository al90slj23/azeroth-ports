#!/usr/bin/env python3
"""Separate256MiB snapshot oracle admission; shared32MiB builder is unchanged."""
from datetime import datetime,timezone
import hashlib,json,subprocess
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,SOURCE_BYTES,parse_source,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import unsigned,sha

ROLES={
 'world_height':(29631,b'\x7f\x7f}}',b'','26ad625360e80687c9aa00161d60e8cb2cfde429209ef361bb0c325b93441650'),
 'terrain_height':(18670,b'\x7f\x7f}}',b'','e69b2fbf238393d43be83153dbbfa5ff310497d104691c829438e18be91cd0e5'),
 'nearest_height':(23181,b'\x7f\x7f}}',b'','a46874e377eac8590d923753e6a5e26289b8388144a0241b6b29cc1f77640666'),
 'spawn_position':(8751,b'\x7f\x7f}}}',b'','94147d4d71b3186ec42fa1b9012884441fb874563c5995527d04d35ab926e4d8'),
 'random_position':(13516,b'\x7f\x7f}}',b'','58ff93447950538f3b0f4df4bbed8a1cef1fda89a7b6cbc182340d0926299c5e'),
 'cached_construct':(6730,b'\x7f\x7f',b'','9aa867cf375c7e60bffcee15c07f77e1320f715f08a68af69bd439eedb8f61e8'),
 'begin_run':(1089,b'\x7f',b'','08ba0c62e0fa4009e7faa31de75154a9c0a98a1f0349d72ec7cd1874229772cb'),
 'companions':(1744,b'\x7f',b'','c7c16dcf45b62c60bf6ba39c8e9e97fe7ca09845d9ad0de467e4362b80a93af7'),
 'world_actor':(1821,b'\x7f\x7f\x7f\x7f\x7f',b'\x7e','fbb21ae4ebb683d34bf3e62eb96f50571b16fb7d8053e980c6fd45cfcb3575db'),
}
STACK_EXPORT='research_snapshot135_stack'
GLOBAL_BYTES='017f01418080c0000b' # exactly one mutable i32, initial1048576


def build_snapshot135(roles):
    roles=sorted(set(roles))
    if not roles or any(x not in ROLES for x in roles):raise ValueError('Explicit snapshot query roles required')
    original=SOURCE.read_bytes();assert len(original)==SOURCE_BYTES and hashlib.sha256(original).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,_=parse_source(original);sections=section_list(original)
    assert 8 not in[x[0]for x in sections]
    global_section=next(s for s in sections if s[0]==6)
    assert original[global_section[2]:global_section[3]].hex()==GLOBAL_BYTES
    ex=next(s for s in sections if s[0]==7);exports,first=export_entries(original,ex)
    assert [x for x in exports if x[0]=='__wbindgen_malloc']==[('__wbindgen_malloc',0,91941)]
    added=b'';details=[]
    for role in roles:
        index,params,results,expected=ROLES[role];assert types[decl[index-len(imports)]]==(params,results)
        start,end=bodies[index];assert hashlib.sha256(original[start:end]).hexdigest()==expected
        name='research_snapshot135_'+role;raw=name.encode();added+=unsigned(len(raw))+raw+b'\x00'+unsigned(index)
        details.append(dict(role=role,index=index,export=name,parameters_hex=params.hex(),results_hex=results.hex(),body_sha256=expected,body_start=start,body_end=end))
    name=STACK_EXPORT.encode();added+=unsigned(len(name))+name+b'\x03\x00'
    payload=unsigned(len(exports)+len(details)+1)+original[first:ex[3]]+added
    changed=original[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+original[ex[3]:]
    new_sections=section_list(changed);assert [x[0]for x in new_sections]==[x[0]for x in sections]
    unchanged=[]
    for a,b in zip(sections,new_sections):
        if a[0]!=7:
            assert original[a[1]:a[3]]==changed[b[1]:b[3]]
            unchanged.append(dict(section=a[0],sha256=hashlib.sha256(original[a[1]:a[3]]).hexdigest()))
    new_exports,_=export_entries(changed,next(s for s in new_sections if s[0]==7))
    assert new_exports[:len(exports)]==exports and len(new_exports)==len(exports)+len(details)+1
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-snapshot0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    module=out/'world-snapshot135-exports.wasm';module.write_bytes(changed)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    done=subprocess.run([str(validator),'--enable-all',str(module)],capture_output=True,timeout=45)
    (out/'validation.stdout').write_bytes(done.stdout);(out/'validation.stderr').write_bytes(done.stderr);assert done.returncode==0
    manifest=dict(version='0.135.1',build='0898d5e3',kind='snapshot-derived-world-consumers-not-bootstrap',original_wasm_sha256=SOURCE_SHA,
        module_file=module.name,module_sha256=sha(module),module_bytes=len(changed),original_exports=exports,
        only_changed_section=7,source_implicit_start=False,roles=details,unchanged_nonexport_sections=unchanged,
        stack_export=dict(name=STACK_EXPORT,index=0,initial_value=1048576,global_section_hex=GLOBAL_BYTES),
        original_allocator=dict(name='__wbindgen_malloc',index=91941,body_sha256='38e2f7621626125da4fae75d4f333479a60c541666792b343880178971598246'),
        memory_page_cap=4096,denied_function_imports=878,validator_sha256=VALIDATOR_SHA,target_executed=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');assert sha(SOURCE)==SOURCE_SHA
    return out,manifest
