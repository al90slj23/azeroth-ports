#!/usr/bin/env python3
"""Private2328/968 exports, source-identical function bodies, snapshot-only."""
from datetime import datetime, timezone
import hashlib
import json
import subprocess
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, SOURCE_BYTES, parse_source, section_list, export_entries, VALIDATOR_SHA
from build_upgrade134_oracle import unsigned, sha

ROLES = {
    'move_player': (2328,b'\x7f\x7f}',b'\x7f','8e456fb160c30e4c4275670d2f4c1d9a6691e4be791905364ea5ff34b008b84b'),
    'motion_dispatch': (968,b'\x7f\x7f\x7f\x7f\x7f\x7f',b'','ae8aedaaa5ca805c5a4e35009e03bbe542fa23c5294f9ab8dadfe4b7e3b7aa97'),
}


def build_motion135():
    original=SOURCE.read_bytes()
    assert len(original)==SOURCE_BYTES and hashlib.sha256(original).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,_=parse_source(original);sections=section_list(original)
    assert len(imports)==878 and 8 not in [s[0] for s in sections]
    assert original[next(s for s in sections if s[0]==6)[2]:next(s for s in sections if s[0]==6)[3]].hex()=='017f01418080c0000b'
    ex=next(s for s in sections if s[0]==7);exports,first=export_entries(original,ex)
    added=b'';roles=[]
    for role,(index,params,results,body_sha) in ROLES.items():
        assert types[decl[index-len(imports)]]==(params,results)
        a,b=bodies[index];assert hashlib.sha256(original[a:b]).hexdigest()==body_sha
        name='research_player_motion135_'+role;encoded=name.encode()
        added+=unsigned(len(encoded))+encoded+b'\0'+unsigned(index)
        roles.append(dict(role=role,index=index,export=name,parameters_hex=params.hex(),results_hex=results.hex(),body_sha256=body_sha))
    name=b'research_player_motion135_stack';added+=unsigned(len(name))+name+b'\x03\x00'
    payload=unsigned(len(exports)+len(roles)+1)+original[first:ex[3]]+added
    modified=original[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+original[ex[3]:]
    fresh=section_list(modified);assert [x[0]for x in fresh]==[x[0]for x in sections]
    unchanged=[]
    for a,b in zip(sections,fresh):
        if a[0]!=7:
            assert original[a[1]:a[3]]==modified[b[1]:b[3]]
            unchanged.append(dict(section=a[0],sha256=hashlib.sha256(original[a[1]:a[3]]).hexdigest()))
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('player-motion135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    module=out/'player-motion135-private-exports.wasm';module.write_bytes(modified)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    completed=subprocess.run([str(validator),'--enable-all',str(module)],capture_output=True,timeout=45)
    (out/'validation.stdout').write_bytes(completed.stdout);(out/'validation.stderr').write_bytes(completed.stderr)
    assert completed.returncode==0
    manifest=dict(kind='player-motion135-snapshot-consumer-not-freshGame',version='0.135.1',build='90898d5e3',
        original_wasm_sha256=SOURCE_SHA,module_file=module.name,module_sha256=sha(module),module_bytes=len(modified),
        roles=roles,original_exports=exports,only_changed_section=7,unchanged_nonexport_sections=unchanged,
        original_start_section=False,stack_export='research_player_motion135_stack',stack_initial=1048576,
        memory_page_cap=4096,denied_function_imports=878,target_executed=False)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return out,manifest


if __name__=='__main__':
    out,manifest=build_motion135();print(json.dumps(dict(directory=str(out),module_sha256=manifest['module_sha256'],original_executed=False)))
