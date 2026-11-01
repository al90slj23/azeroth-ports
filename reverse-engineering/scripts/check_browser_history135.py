#!/usr/bin/env python3
"""Real resource1073/history composition, expected before isolated browser."""
from collections import Counter
from dataclasses import replace
from pathlib import Path
import argparse,copy,hashlib,json,os,signal,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build,parse_source,section_list
from build_upgrade134_oracle import sha
from check_incoming_history135 import FILES as HISTORY_SOURCES,corpus as fallback_corpus,scalar_projection,compare
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.incoming135 import input_from_dict,resolve_incoming_prefix
from core_spec.incoming_history135 import from_raw_storage,append_incoming_history,projection
from resource_spec.dbc import DBC

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
FILES=tuple(dict.fromkeys((*HISTORY_SOURCES,'scripts/check_browser_history135.py','scripts/run_browser_history135.mjs',
 'scripts/browser_history135.mjs','reconstruction/resource_spec/dbc.py','reconstruction/resource_spec/__init__.py')))
IMPORT_SHA={n:sha(ROOT/n)for n in FILES}
BRIDGE_APPEND='''\n// Research-only additional exports. Official source prefix is unchanged.\nexport function resource135GetImports(){return __wbg_get_imports();}\nexport function resource135BindOnly(instance,module){\n  wasmInstance=instance;wasmModule=module;wasm=instance.exports;\n  cachedDataViewMemory0=null;cachedFloat32ArrayMemory0=null;cachedInt16ArrayMemory0=null;cachedInt32ArrayMemory0=null;cachedInt8ArrayMemory0=null;cachedUint16ArrayMemory0=null;cachedUint32ArrayMemory0=null;cachedUint8ArrayMemory0=null;cachedUint8ClampedArrayMemory0=null;\n  return wasm;\n}\n'''


def metadata():
    spell=DBC.parse((ASSET_ROOT/'dbfilesclient/spell.dbc').read_bytes())
    icon=DBC.parse((ASSET_ROOT/'dbfilesclient/spellicon.dbc').read_bytes())
    assert(spell.fields,spell.record_bytes,icon.fields,icon.record_bytes)==(173,692,2,8)
    table={}
    for sid in(5568,28783,28308):
        j=next(j for j in range(spell.rows)if spell.word(j,0)==sid);iid=spell.word(j,117)
        k=next(k for k in range(icon.rows)if icon.word(k,0)==iid)
        table[str(sid)]=dict(spell_id=sid,spell_row=j,icon_id=iid,icon_row=k,
            name=spell.string(spell.word(j,120)).decode('utf-8'),icon=icon.string(icon.word(k,1)).decode('utf-8'),
            spell_record_hex=spell.raw_record(j).hex(),icon_record_hex=icon.raw_record(k).hex())
    return table


def corpus(names,pilot):
    base=fallback_corpus(True);cases=[];b=f.from_float;sids=(5568,28783,28308)
    def add(index,group,times,amount=7.5,minimum_one=0):
        c={k:copy.deepcopy(v)for k,v in base[index].items()if k!='expected'}
        c['id']=len(cases);c['group']=group;c['input']['minimum_one_2578']=minimum_one
        c['ops']=[dict(now_bits=b(now),amount_bits=b(amount),category=1+j%2,critical=j%2,spell_id=sids[j%3])for j,now in enumerate(times)]
        raw=dict(c['input']);maximum=raw.pop('max_hp_bits');state=input_from_dict(raw);ring=from_raw_storage(c['storage'],c['head'],c['count']);expected=[]
        for op in c['ops']:
            state=replace(state,now_bits=op['now_bits']);before=state;result=resolve_incoming_prefix(state,op['amount_bits'],0)
            assert result.status=='pending'and result.stage=='scalar_nonfatal_projection';state=result.state;m=names[str(op['spell_id'])]
            ring=append_incoming_history(ring,now_bits=op['now_bits'],damage_bits=result.amount_bits,
                absorbed_bits=result.absorbed_bits,hp_after_prefix_bits=f.sub(before.hp_1528_bits,result.amount_bits),
                maximum_hp_bits=maximum,category=op['category'],source_label='',source_classification=4,
                resolved_spell=(m['name'],m['icon']))
            expected.append(dict(**projection(ring),scalar=scalar_projection(state)))
        c['expected']=expected;cases.append(c)
    add(0,'cold-actual-two-spells',[20,20.25]);add(1,'cold-wrapped-tie-growth',[20,20.25])
    if pilot:return cases
    add(2,'cold-prefix-greater-growth',[20,20.25]);add(3,'cold-prefix-smaller-growth',[20,20.25])
    add(4,'cold-expiry-wrap-and-cutoff',[20,20.25,30.25]);add(0,'exact-ten-second-and-beyond',[20,20.5,30,30.5001])
    add(6,'real-names-after-shield-break',[20,20.25,20.5]);add(0,'real-names-before-minimum-one',[20,21,22],600000,1)
    add(0,'consecutive-real-spell-metadata',[20+j/8 for j in range(16)])
    return cases


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_SHA
    assert sha(GLUE)==GLUE_SHA and sha(RUNTIME)==RUNTIME_SHA and sha(AUX)==AUX_SHA
    assert PW.is_dir()and CHROME.is_file(),'Existing local tools required; no downloads'
    assert {n:sha(ASSET_ROOT/n)for n in ASSET_HASHES}==ASSET_HASHES
    spell_wat=ROOT/'evidence/effect-geometry0135-static-20261101T081015.075418Z/4546.wat'
    wat=spell_wat.read_text();assert 'i32.const 488' in wat and 'i32.const 120' in wat
    names=metadata();cases=corpus(names,args.phase=='pilot')
    out,manifest=build(['incoming_damage']);original=SOURCE.read_bytes();types,imports,decl,bodies,_=parse_source(original)
    body_start,body_end=bodies[4546];assert hashlib.sha256(original[body_start:body_end]).hexdigest()=='073d44f43e2a1a3ebb31ad697f20516f07128a866eb8c7c40c2eb1fbcca2e00f'
    module=out/manifest['module_file'];changed=module.read_bytes();old=section_list(original);new=section_list(changed);assert len(old)==len(new)and 8 not in[x[0]for x in old]
    nonexport=[]
    for x,y in zip(old,new):
        assert x[0]==y[0]
        if x[0]!=7:assert original[x[1]:x[3]]==changed[y[1]:y[3]];nonexport.append(dict(section=x[0],sha256=hashlib.sha256(original[x[1]:x[3]]).hexdigest()))
    assert len(manifest['roles'])==1 and manifest['roles'][0]['index']==1073
    official=GLUE.read_bytes();bridge=out/'official-history-bridge135.mjs';bridge.write_bytes(official+BRIDGE_APPEND.encode())
    fixture=out/'browser-history135-fixtures.json';fixture.write_text(json.dumps(cases,separators=(',',':'))+'\n')
    inputs=out/'browser-history135-inputs.json';input_keys=('id','group','input','capacity','head','count','storage','ops')
    inputs.write_text(json.dumps([{k:c[k]for k in input_keys}for c in cases],separators=(',',':'))+'\n')
    md=out/'browser-history135-independent-metadata.json';md.write_text(json.dumps(names,indent=2)+'\n')
    config=dict(directory=str(out),wasm_path=str(module),wasm_sha256=sha(module),glue_path=str(bridge),glue_sha256=sha(bridge),official_glue_sha256=GLUE_SHA,
        official_glue_prefix_bytes=len(official),asset_root=str(ASSET_ROOT),assets=ASSET_HASHES,fixtures_path=str(inputs),fixtures_sha256=sha(inputs),
        auxiliary_module=dict(path=str(AUX),url='/snippets/benilla-app-e11f90d5572a787b/inline0.js',sha256=AUX_SHA),
        playwright_path=str(PW),chrome_path=str(CHROME),chrome_sha256=sha(CHROME),
        imports=[dict(id=i,module=m,name=n,type_index=t,allowed=i in ALLOWED_IMPORTS)for i,(m,n,t)in enumerate(imports)],
        unchanged_nonexport_sections=nonexport,original_sha256=SOURCE_SHA,base_manifest_sha256=sha(out/'manifest.json'),memory_cap_bytes=128*1024*1024,deadline_seconds=60)
    configfile=out/'browser-history135-config.json';configfile.write_text(json.dumps(config,indent=2)+'\n')
    snap=out/'source-snapshot'
    for n,h in before.items():q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    frozen={q.name:sha(q)for q in(module,bridge,fixture,inputs,md,configfile)}
    tmp=out/'browser-tmp';tmp.mkdir();env=dict(os.environ,TMPDIR=str(tmp))
    cmd=[str(RUNTIME),'--max-old-space-size=512',str(ROOT/'scripts/run_browser_history135.mjs'),str(configfile)]
    start=time.monotonic();stdout=out/'browser-history135.stdout';stderr=out/'browser-history135.stderr'
    with stdout.open('wb')as so,stderr.open('wb')as se:
        child=subprocess.Popen(cmd,stdout=so,stderr=se,env=env,start_new_session=True)
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            raise RuntimeError('Owned120s deadline; inspect terminal PID journal before retry')
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    assert frozen=={q.name:sha(q)for q in(module,bridge,fixture,inputs,md,configfile)}
    runtime_file=out/'browser-history135-runtime.json';runtime=json.loads(runtime_file.read_text())if runtime_file.exists()else None
    failures=[];counters=Counter()
    if code==0:
        assert runtime['status']=='passed';actual=runtime['result']['results'];assert len(actual)==len(cases)
        for c,a in zip(cases,actual):
            assert c['id']==a['id']and len(c['expected'])==len(a['stages'])
            for j,(w,observed)in enumerate(zip(c['expected'],a['stages'])):compare(w,observed,f'case{c["id"]}.stage{j}',failures,counters)
    mismatches=out/'browser-history135-mismatches.json';mismatches.write_text(json.dumps(failures,indent=2)+'\n')
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=counters['stages'],differences=counters['differences'],comparison=dict(counters),
        original_sha256=SOURCE_SHA,source_before=before,source_after=after,expected_before_original=True,source_snapshots=True,input_exact_keys=list(input_keys),input_contains_expected=False,
        browser_embedding_separate_from_all878_denied_Node=True,only_changed_wasm_section=7,only_added_export='research135_incoming_damage',
        official_glue_prefix_unchanged=True,metadata_columns=dict(spell_name=120,spell_icon_id=117,icon_id=0,icon_string=1),independent_metadata=names,
        metadata_instruction_evidence=dict(path=str(spell_wat.relative_to(ROOT)),wat_sha256=sha(spell_wat),body_sha256=hashlib.sha256(original[body_start:body_end]).hexdigest(),icon_column_expression='(488-20)/4=117'),
        process=dict(pid=child.pid,pgid=child.pid,command=cmd,exit_code=code,seconds=time.monotonic()-start,outer_deadline_seconds=120),
        artifacts={q.name:sha(q)for q in(module,bridge,fixture,inputs,md,configfile,stdout,stderr,mismatches,runtime_file,out/'manifest.json')if q.exists()},
        runtime=runtime,limitations=['Onlyhistory48/scalars are independent;registry/keyed/proc-sideeffects retained as raw observation,not full1073 model.',
            'SourceGUID0, no units,emptybuff/item/modifier/proc,nonfatal/minimum-one;3realSpellrecords/Englishnames and actualSpellIconfullpaths only.',
            '17audited realresourceimports allowed/861deny;128MiB browser, distinctfromNode878deny/32MiB.',
            'No start/finalize export invoked by explicitentrywhitelist/log;not exhaustive proof ofall internalindirectcalls.',
            'Pointer words semantic via fullactiveUTF8;oldpadding strict,newallocatorunwritten provenance preserved;allrawG/backing/messages retained.',
            'Not integratedinto realentry1089/full880/headlessorfullmatch.'])
    target=out/'browser-history135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),exit_code=code,status=(runtime or{}).get('status'),error=(runtime or{}).get('error'),cases=len(cases),stages=counters['stages'],differences=counters['differences'],first_failures=failures[:2])))
    if code or failures:raise SystemExit(code or 1)


if __name__=='__main__':main()
