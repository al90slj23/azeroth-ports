#!/usr/bin/env python3
"""Original139 world+opening context over explicit research App/profile input.

Observational capture, not an independent whole entry model or natural App.
Fresh official139 assets/glue only. Original account2917 and selection2945
produce empty account/absent companion tags. No old memory/cache/Once injected.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,signal,sqlite3,struct,subprocess,time
from build_combat139_oracle import ROOT,SOURCE,SOURCE_SHA,PROFILE,Reader,binary_identity,sha,save,unsigned,export_entries,tool_identity
from source_closure137 import verify_local_source_closure
from trace_coop import module_data
STATIC=ROOT/'evidence/opening139-context-static-20261102T022955.014560Z/proof.json'
STATIC_SHA='689fce19563120ee4a1e7b8c0779591460794f4569dc2b0dee830e63146297f8'
ASSETS=ROOT/'originals/entry-assets139-20261102T022818.157124Z'
MAP_SHA='3a794c2e35873852cc8f6661fb93ec9edae9a06626277ff123f1612495927ec2'
ASSET_RECEIPT_SHA='7aec47c1ce5b6d58f2374878e2f6877e95de4784aed7837a21a2075ecf97ea92'
GLUE=SOURCE.parent/'official-wenilla.js';GLUE_SHA='d08ade052f40bcca1da93b559e9e10397ec240ba4975a467d6089ff5407bf3bd'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
PW=Path('/Users/al90slj23/.npm/_npx/e41f203b7505f1fb/node_modules/playwright')
CHROME=Path('/Users/al90slj23/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell')
ROLES={'load_account':2917,'companion_selection':2945,'construct_world_game':6786,'begin_run':1108}
APPEND='''\n// Research bridge only; official source prefix/import functions are unchanged.
export function entry139GetImports(){return __wbg_get_imports();}
export function entry139BindOnly(instance,module){
wasmInstance=instance;wasmModule=module;wasm=instance.exports;
cachedDataViewMemory0=null;cachedFloat32ArrayMemory0=null;cachedInt16ArrayMemory0=null;cachedInt32ArrayMemory0=null;cachedInt8ArrayMemory0=null;cachedUint16ArrayMemory0=null;cachedUint32ArrayMemory0=null;cachedUint8ArrayMemory0=null;cachedUint8ClampedArrayMemory0=null;return wasm;
}
'''

def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False

def closure():
    files={'scripts/probe_entry_world139_v2.py','scripts/run_entry_world139_v2.mjs','scripts/browser_entry_world139_v2.mjs','scripts/trace_opening139_context.py','scripts/source_closure137.py'}
    while True:
        try:edges=verify_local_source_closure(sorted(files));return sorted(files),edges
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in files;files.add(pair[1])

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files}
    assert sha(SOURCE)==SOURCE_SHA and sha(GLUE)==GLUE_SHA and sha(NODE)==NODE_SHA and PW.is_dir()and CHROME.is_file()
    assert sha(STATIC)==STATIC_SHA and sha(ASSETS/'resource-map.json')==MAP_SHA and sha(ASSETS/'receipt.json')==ASSET_RECEIPT_SHA
    static=json.loads(STATIC.read_text());assert static['source_wasm_sha256']==SOURCE_SHA and static['script_sha256']==sha(ROOT/'scripts/trace_opening139_context.py')
    selection_lines=(STATIC.parent/'2945.wat').read_text().splitlines();assert selection_lines[1158].strip()=='local.get 0'and selection_lines[1197].strip()=='i32.store8 offset=34'and selection_lines[1203].strip()=='local.tee 0'
    assert any(l.strip()=='i32.store8 offset=35'for l in selection_lines[1158:1198])
    assets=json.loads((ASSETS/'resource-map.json').read_text());assert len(assets)==454
    for row in assets.values():assert sha(Path(row['file']))==row['sha256']and Path(row['file']).stat().st_size==row['bytes']
    raw=SOURCE.read_bytes();identity,ranges=binary_identity(raw);sections=identity['sections'];assert not identity['implicit_start_section']
    sec=next(s for s in sections if s['kind']==6);assert raw[sec['payload_start']:sec['end']].hex()=='017f01418080c0000b'
    segments,base,elements=module_data(raw);vp=1410440;s=next(s for s in segments if s['address']<=vp and vp+36<=s['address']+s['size']);pos=s['file_start']+vp-s['address'];vt=raw[pos:pos+36];words=struct.unpack('<9I',vt);assert words==(284,24,8,285,286,287,288,289,290)and elements[words[8]-base]==177894
    a,b,_=ranges[177894];assert raw[a:b].hex()=='0041000b'
    ex=next(s for s in sections if s['kind']==7);prior,start=export_entries(raw,ex);extra=b'';added=[];roles=[]
    for role,index in ROLES.items():
        row=static['selected_functions'][str(index)];a,b,_=ranges[index];assert hashlib.sha256(raw[a:b]).hexdigest()==row['body_sha256']
        name='entry139_'+role;n=name.encode();extra+=unsigned(len(n))+n+b'\0'+unsigned(index);added.append((name,0,index));roles.append(dict(name=name,index=index,body_sha256=row['body_sha256'],signature=row['signature']))
    name='entry139_stack0';n=name.encode();extra+=unsigned(len(n))+n+b'\3\0';added.append((name,3,0))
    payload=unsigned(len(prior)+len(added))+raw[start:ex['end']]+extra;changed=raw[:ex['start']]+b'\7'+unsigned(len(payload))+payload+raw[ex['end']:];after,_=binary_identity(changed)
    for a,b in zip(sections,after['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    assert export_entries(changed,next(s for s in after['sections']if s['kind']==7))[0]==prior+added
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('entry-world139-v2-probe-%Y%m%dT%H%M%S.%fZ');out.mkdir();module=out/'entry-world139.wasm';module.write_bytes(changed);bridge=out/'entry-world139-bridge.mjs';bridge.write_bytes(GLUE.read_bytes()+APPEND.encode())
    validator=Path(tool_identity()['tools']['wasm-validate']['path']);began=time.monotonic()
    with(out/'validation.stdout').open('wb')as so,(out/'validation.stderr').open('wb')as se:
        p=subprocess.Popen([str(validator),'--enable-all',str(module)],stdout=so,stderr=se,start_new_session=True)
        try:p.wait(timeout=45)
        finally:
            if p.poll()is None:os.killpg(p.pid,signal.SIGKILL);p.wait()
    vterm=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-began,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'validator-terminal.json',vterm);assert p.returncode==0 and vterm['pid_missing']and vterm['pgid_missing']
    # Old allow-list contributes semantic import names only, never old bodies,
    # resource bytes, state or acceptance. Every139 import/type is recorded.
    old=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/entry-world135-config.json';oldc=json.loads(old.read_text());allowed={x['name']for x in oldc['imports']if x['allowed']}
    imports=[dict(id=i,**x,allowed=x['name']in allowed)for i,x in enumerate(identity['imports'])];assert len(imports)==882 and len([x for x in imports if x['allowed']])==len(allowed)==24
    cfg=dict(directory=str(out),wasm_path=str(module),wasm_sha256=sha(module),glue_path=str(bridge),glue_sha256=sha(bridge),official_glue_sha256=GLUE_SHA,official_glue_prefix_bytes=GLUE.stat().st_size,
        roles=roles,imports=imports,original_sha256=SOURCE_SHA,only_changed_section=7,resource_map_path=str(ASSETS/'resource-map.json'),resource_map_sha256=MAP_SHA,
        asset_acquisition_receipt_sha256=ASSET_RECEIPT_SHA,aux_path=str(ASSETS/'files/snippets/benilla-app-e11f90d5572a787b/inline0.js'),aux_sha256='a6d8b6cbe3ade99211ad4f01a4712c9996044e402975fc3d72e7f7b6d043f85b',
        playwright_path=str(PW),chrome_path=str(CHROME),chrome_sha256=sha(CHROME),memory_page_cap=4096,memory_cap_bytes=268435456,capture_chunk_bytes=1048576,
        selected_profile_input=dict(region_id='elwynn',class_byte=1,race_byte=1,object_id_u64='0',app_lcg_seed_u64='0',scope='Explicit research empty376 profile; original2917/2945 supply absentcompanion selection. Naturalmenu/profileproducer notclaimed'),
        app_input=dict(allocation_bytes=5168,initial_poison=165,transport_vtable=vp,transport_vtable36_hex=vt.hex(),transport_method32_original_function=177894,flags5163_u32=4278255360,scope='Explicit research App fields requiredby6786; no naturalApp constructor executed'),
        selection_output_contract=dict(function2945_return_minimum_bytes=36,explicit_return_bytes=40,allocation_bytes=72,before_canary_bytes=16,after_canary_bytes=16,profile_copied_prefix_bytes=16),
        source_before=before,source_import_edges=edges,static_proof_sha256=STATIC_SHA,old_snapshot_loaded=False,old_resource_bytes_reused=False,independent_model_cases=0)
    config=out/'config.json';save(config,cfg)
    for name,h in before.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    frozen={p.name:sha(p)for p in(module,bridge,config)};save(out/'prepared.json',dict(frozen=frozen,source_before=before,source_import_edges=edges,original_executed=False,prepare_only=args.prepare_only,observational_only=True))
    if args.prepare_only:print(json.dumps(dict(directory=str(out),prepared=True,original_executed=False)));return
    tmp=out/'browser-tmp';tmp.mkdir();command=[str(NODE),'--max-old-space-size=512',str(ROOT/'scripts/run_entry_world139_v2.mjs'),str(config)];began=time.monotonic()
    with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
        p=subprocess.Popen(command,stdout=so,stderr=se,env=dict(os.environ,TMPDIR=str(tmp)),start_new_session=True);save(out/'owned-process.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=120))
        try:p.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=p.returncode,seconds=time.monotonic()-began,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True),deadline_seconds=120);save(out/'process-terminal.json',terminal)
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert before=={n:sha(ROOT/n)for n in files}and frozen=={p.name:sha(p)for p in(module,bridge,config)}
    receipt=dict(version='0.139.0',build='f79c5e2b4',kind='original_world_andopening_observation_over_explicit_research_inputs_not_independent_model',source_wasm_sha256=SOURCE_SHA,
        supersedes_limited_context=dict(receipt='evidence/entry-world139-probe-20261102T023815.931445Z/receipt.json',sha256='5d940f9d00f0428327791132f5b9f60df7787348d6fd5a1d50ad840aea1a2964',reason='Old2945return allocation16B was smallerthanactual36B; oldbytes retainedwithknownfixturedefect'),
        source_before=before,source_after=before,process=terminal,runtime=runtime,source_import_edges=edges,validator=vterm,
        artifacts={p.name:sha(p)for p in(out/'prepared.json',config,module,bridge,out/'stdout.jsonl',out/'stderr.log',out/'process-terminal.json',out/'runtime.json')if p.exists()},
        old_snapshot_loaded=False,old_resource_bytes_reused=False,native_executions=0,complete_games=0,natural_App_produced=False,selected_profile_producer_complete=False,independent_model_cases=0)
    save(out/'receipt.json',receipt);print(json.dumps(dict(directory=str(out),receipt_sha256=sha(out/'receipt.json'),process=terminal,status=(runtime or{}).get('status'),error=(runtime or{}).get('error'))),flush=True)
    if p.returncode or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)
if __name__=='__main__':main()
