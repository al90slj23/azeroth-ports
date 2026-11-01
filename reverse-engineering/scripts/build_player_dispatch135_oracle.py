#!/usr/bin/env python3
"""Additional private6730/1089 exports for full968 typed partial-App fixtures."""
import hashlib
import json
from build_player_motion135_oracle import build_motion135
from build_full135_oracle import SOURCE, SOURCE_SHA, parse_source, section_list, export_entries
from build_upgrade134_oracle import unsigned, sha


def build_dispatch135():
    out,manifest=build_motion135();path=out/manifest['module_file'];changed=path.read_bytes();original=SOURCE.read_bytes()
    assert hashlib.sha256(original).hexdigest()==SOURCE_SHA
    types,imports,decl,bodies,_=parse_source(original)
    sections=section_list(changed);ex=next(s for s in sections if s[0]==7);exports,first=export_entries(changed,ex)
    additions=b'';roles=[]
    for role,index,expected in (('cached_construct',6730,'9aa867cf375c7e60bffcee15c07f77e1320f715f08a68af69bd439eedb8f61e8'),
            ('begin_run',1089,'08ba0c62e0fa4009e7faa31de75154a9c0a98a1f0349d72ec7cd1874229772cb')):
        params,results=types[decl[index-len(imports)]];assert(params,results)==(b'\x7f\x7f'if index==6730 else b'\x7f',b'')
        a,b=bodies[index];assert hashlib.sha256(original[a:b]).hexdigest()==expected
        name='research_player_dispatch135_'+role;raw=name.encode();additions+=unsigned(len(raw))+raw+b'\0'+unsigned(index)
        roles.append(dict(role=role,index=index,export=name,body_sha256=expected,parameters_hex=params.hex(),results_hex=results.hex()))
    payload=unsigned(len(exports)+len(roles))+changed[first:ex[3]]+additions
    final=changed[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+changed[ex[3]:];path.write_bytes(final)
    old_sections=section_list(original);fresh=section_list(final)
    assert [x[0]for x in old_sections]==[x[0]for x in fresh]
    assert all(a[0]==7 or original[a[1]:a[3]]==final[b[1]:b[3]]for a,b in zip(old_sections,fresh))
    manifest.update(kind='full968-default-localroute-typed-partialApp-component',module_sha256=sha(path),module_bytes=len(final),
        additional_setup_roles=roles,setup_is_independent_constructor_validation=False,
        context='Cached6730 directlywritesApp+16,then1089;partialApp tags providedfrom4253 constants;notnatural1371Appproducer')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return out,manifest


if __name__=='__main__':
    out,manifest=build_dispatch135();print(json.dumps(dict(directory=str(out),module_sha256=manifest['module_sha256'],target_executed=False)))
