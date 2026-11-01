#!/usr/bin/env python3
"""Isolated real-browser embedding: genuine resource imports, no app start.

This is intentionally separate from the all878-denied Node oracle. It adds one
browser-only4546 export, preserves every WASM nonexport byte, and appends bridge
exports to unchanged officialglue. Actual network is loopback-only actualfiles.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,signal,struct,subprocess,sys,time
from build_full135_oracle import (ROOT,SOURCE,SOURCE_SHA,build,parse_source,section_list,export_entries,VALIDATOR_SHA)
from build_upgrade134_oracle import unsigned,sha
from check_effect_geometry135 import corpus,FILES as GEOMETRY_SOURCES

GLUE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'
GLUE_SHA='636bcd5acba01a31c4b40234969243e964cc8e7e7610adf0817e3494d92c9945'
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
PW=Path('/Users/al90slj23/.npm/_npx/e41f203b7505f1fb/node_modules/playwright')
CHROME=Path('/Users/al90slj23/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
ASSET_ROOT=ROOT.parent/'android/assets/latest-web-core/data'
ASSET_HASHES={'__index':'1ca98562aee4c460c4eb46d20f1bf0facdff0fb0bc1f4b73814b9cfea5c4aad8',
 'dbfilesclient/spell.dbc':'913d01c0376d88310ed4a44ea1115f30fd8be15af64ce304f4f17b6bc51cf15b',
 'dbfilesclient/spellicon.dbc':'938e8c333fe914938994fc331c04655d7eb5719bc2d1b29eaf5fad4239abdfdc'}
AUX=ROOT.parent/'android/assets/latest-web-core/snippets/benilla-app-e11f90d5572a787b/inline0.js'
AUX_SHA='a6d8b6cbe3ade99211ad4f01a4712c9996044e402975fc3d72e7f7b6d043f85b'
ALLOWED_IMPORTS=(0,521,523,643,644,645,658,659,660,735,804,827,835,845,848,851,877)
FILES=tuple(dict.fromkeys((*GEOMETRY_SOURCES,'scripts/check_browser_resources135.py','scripts/run_browser_resources135.mjs','scripts/browser_resource_case135.mjs','reconstruction/resource_spec/dbc.py','reconstruction/resource_spec/__init__.py')))
IMPORT_SHA={n:sha(ROOT/n)for n in FILES}
BRIDGE_APPEND='''\n// Research-only additional exports. Official source prefix is unchanged.\nexport function resource135GetImports(){return __wbg_get_imports();}\nexport function resource135BindOnly(instance,module){\n+  wasmInstance=instance;wasmModule=module;wasm=instance.exports;\n+  cachedDataViewMemory0=null;cachedFloat32ArrayMemory0=null;cachedInt16ArrayMemory0=null;cachedInt32ArrayMemory0=null;cachedInt8ArrayMemory0=null;cachedUint16ArrayMemory0=null;cachedUint32ArrayMemory0=null;cachedUint8ArrayMemory0=null;cachedUint8ClampedArrayMemory0=null;\n+  return wasm;\n+}\n+'''.replace('\n+','\n')


def expected_names():
    sys.path.insert(0,str(ROOT/'reconstruction'))
    from resource_spec.dbc import DBC
    d=DBC.parse((ASSET_ROOT/'dbfilesclient/spell.dbc').read_bytes())
    return {str(s):d.string(d.word(next(j for j in range(d.rows)if d.word(j,0)==s),120)).decode()for s in(5568,28783,28308)}


def main():
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_SHA and sha(GLUE)==GLUE_SHA and sha(RUNTIME)==RUNTIME_SHA
    assert PW.is_dir()and CHROME.is_file(),'Existing Playwright/Chromium required; no automatic download'
    assert{n:sha(ASSET_ROOT/n)for n in ASSET_HASHES}==ASSET_HASHES
    assert sha(AUX)==AUX_SHA
    cases=[c for c in corpus(True)if c['id']in(0,3,6)]
    out,base=build(['spawn_boss','npc_action','effect_tick']);original=SOURCE.read_bytes();types,imports,decl,bodies,segments=parse_source(original)
    assert types[decl[4546-len(imports)]]==(b'\x7f',b'\x7f');a,b=bodies[4546]
    assert hashlib.sha256(original[a:b]).hexdigest()=='073d44f43e2a1a3ebb31ad697f20516f07128a866eb8c7c40c2eb1fbcca2e00f'
    changed=(out/base['module_file']).read_bytes();sections=section_list(changed);ex=next(s for s in sections if s[0]==7);entries,first=export_entries(changed,ex)
    name=b'resource135_spell_record';payload=unsigned(len(entries)+1)+changed[first:ex[3]]+unsigned(len(name))+name+b'\x00'+unsigned(4546)
    browser_module=changed[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+changed[ex[3]:]
    new_sections=section_list(browser_module);old_sections=section_list(original);assert 8 not in[s[0]for s in old_sections]
    nonexport=[]
    for x,y in zip(old_sections,new_sections):
        assert x[0]==y[0]
        if x[0]!=7:
            assert original[x[1]:x[3]]==browser_module[y[1]:y[3]];nonexport.append(dict(section=x[0],sha256=hashlib.sha256(original[x[1]:x[3]]).hexdigest()))
    assert len(new_sections)==len(old_sections)
    module=out/'browser-resource135.wasm';module.write_bytes(browser_module)
    validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    v=subprocess.run([str(validator),'--enable-all',str(module)],capture_output=True,timeout=45);(out/'browser-validation.stderr').write_bytes(v.stderr);assert v.returncode==0
    glue_bytes=GLUE.read_bytes();bridge=out/'official-resource-bridge135.mjs';bridge.write_bytes(glue_bytes+BRIDGE_APPEND.encode());assert bridge.read_bytes()[:len(glue_bytes)]==glue_bytes
    fixture=out/'browser-resource135-fixtures.json';fixture.write_text(json.dumps(cases)+'\n')
    config=dict(directory=str(out),wasm_path=str(module),wasm_sha256=sha(module),glue_path=str(bridge),glue_sha256=sha(bridge),official_glue_sha256=GLUE_SHA,
        official_glue_prefix_bytes=len(glue_bytes),asset_root=str(ASSET_ROOT),assets=ASSET_HASHES,fixtures_path=str(fixture),fixtures_sha256=sha(fixture),
        auxiliary_module=dict(path=str(AUX),url='/snippets/benilla-app-e11f90d5572a787b/inline0.js',sha256=AUX_SHA,scope='Existing packaged dependency, no latest135 equivalence claim; begin/append imports denied and never invoked.'),
        names=expected_names(),playwright_path=str(PW),chrome_path=str(CHROME),chrome_sha256=sha(CHROME),
        imports=[dict(id=i,module=m,name=n,type_index=t,allowed=i in ALLOWED_IMPORTS)for i,(m,n,t)in enumerate(imports)],
        extra_export=dict(name=name.decode(),index=4546,body_sha256=hashlib.sha256(original[a:b]).hexdigest(),signature='(i32)->i32'),
        unchanged_nonexport_sections=nonexport,original_sha256=SOURCE_SHA,base_manifest_sha256=sha(out/'manifest.json'),memory_cap_bytes=128*1024*1024,deadline_seconds=60)
    configfile=out/'browser-resource135-config.json';configfile.write_text(json.dumps(config,indent=2)+'\n')
    snap=out/'source-snapshot';snap.mkdir()
    for n,h in before.items():
        q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    frozen={q.name:sha(q)for q in(module,bridge,fixture,configfile)}
    tmp=out/'browser-tmp';tmp.mkdir();env=dict(os.environ,TMPDIR=str(tmp))
    cmd=[str(RUNTIME),'--max-old-space-size=512',str(ROOT/'scripts/run_browser_resources135.mjs'),str(configfile)]
    start=time.monotonic();stdout=out/'browser-resource135.stdout';stderr=out/'browser-resource135.stderr'
    with stdout.open('wb')as so,stderr.open('wb')as se:
        child=subprocess.Popen(cmd,stdout=so,stderr=se,env=env,start_new_session=True)
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise RuntimeError('Owned browser-harness120s deadline; see PID journal before restarting')
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    assert frozen=={q.name:sha(q)for q in(module,bridge,fixture,configfile)}
    receipt=dict(original_sha256=SOURCE_SHA,source_before=before,source_after=after,expected_before_original=True,source_snapshots=True,
        browser_embedding_separate_from_all878_denied_Node=True,only_changed_wasm_section=7,official_glue_prefix_unchanged=True,
        process=dict(pid=child.pid,pgid=child.pid,command=cmd,exit_code=code,seconds=time.monotonic()-start,outer_deadline_seconds=120),
        artifacts={q.name:sha(q)for q in(module,bridge,fixture,configfile,stdout,stderr,out/'browser-resource135-runtime.json')if q.exists()},
        runtime=json.loads((out/'browser-resource135-runtime.json').read_text())if(out/'browser-resource135-runtime.json').exists()else None)
    (out/'browser-resource135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n')
    rt=receipt['runtime']or{};res=rt.get('result')or{}
    print(json.dumps(dict(directory=str(out),exit_code=code,status=rt.get('status'),error=rt.get('error'),cases=res.get('cases'),stages=res.get('stages'),
        mismatch_fields=len(res.get('failures',[])),max_memory_bytes=res.get('max_memory_bytes'),browser_pid=rt.get('browser_pid'))))
    if code:raise SystemExit(code)


if __name__=='__main__':main()
