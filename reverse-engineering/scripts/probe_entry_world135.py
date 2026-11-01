#!/usr/bin/env python3
"""Bounded observational true6730 world producer +1089 entry; no app start.

Only append original WASM exports. A fresh browser's real empty Storage produces
the account; an explicit previously scoped empty selected-profile is an input,
not a claim that menu/profile assembly is recovered. No world/cache/Once writes.
The asset worker returns exact real MPQ bytes and rejects unknown precedence.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, signal, sqlite3, struct, subprocess, sys, time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries,VALIDATOR_SHA
from build_upgrade134_oracle import unsigned,sha
from trace_coop import module_data

GLUE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'
GLUE_SHA='636bcd5acba01a31c4b40234969243e964cc8e7e7610adf0817e3494d92c9945'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
PW=Path('/Users/al90slj23/.npm/_npx/e41f203b7505f1fb/node_modules/playwright')
CHROME=Path('/Users/al90slj23/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell')
DATA=ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'
INDEX=ROOT/'evidence/resource-index-base-20261101T032320.856364Z/index.sqlite'
INDEX_SHA='a3f219f6e76e1d87e50b0790b757f999091e2b479d3b1d40ac2c101aa8680cf4'
NAME_INDEX=ROOT.parent/'android/assets/latest-web-core/data/__index'
NAME_INDEX_SHA='1ca98562aee4c460c4eb46d20f1bf0facdff0fb0bc1f4b73814b9cfea5c4aad8'
AUX=ROOT.parent/'android/assets/latest-web-core/snippets/benilla-app-e11f90d5572a787b/inline0.js'
AUX_SHA='a6d8b6cbe3ade99211ad4f01a4712c9996044e402975fc3d72e7f7b6d043f85b'
ROLES={
 'entry135_load_account':(2902,'7f','','7b997071062b9d2540ee660f2664615e17f3c2fe6f1d923e84dcf2cbaaa2d3fb'),
 'entry135_apply_unlocks':(6959,'7f7f7e7e','','dba509c6dec130407ee8d5e6533f612791def96c137a3f727d74cb275591d65c'),
 'entry135_construct_world_game':(6730,'7f7f','','9aa867cf375c7e60bffcee15c07f77e1320f715f08a68af69bd439eedb8f61e8'),
 'entry135_begin_run':(1089,'7f','','08ba0c62e0fa4009e7faa31de75154a9c0a98a1f0349d72ec7cd1874229772cb')}
ALLOWED=(0,337,338,343,499,521,523,641,643,644,645,658,659,660,735,773,774,804,827,835,845,848,851,877)
FILES=('scripts/probe_entry_world135.py','scripts/run_entry_world135.mjs','scripts/browser_entry_world135.mjs',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py',
 'scripts/trace_coop.py','scripts/wasm_index.py',
 'reconstruction/resource_spec/__init__.py','reconstruction/resource_spec/mpq.py')
APPEND='''\n// Research bridge only; official prefix and all import functions are unchanged.\nexport function entry135GetImports(){return __wbg_get_imports();}\nexport function entry135BindOnly(instance,module){\n wasmInstance=instance;wasmModule=module;wasm=instance.exports;\n cachedDataViewMemory0=null;cachedFloat32ArrayMemory0=null;cachedInt16ArrayMemory0=null;cachedInt32ArrayMemory0=null;cachedInt8ArrayMemory0=null;cachedUint16ArrayMemory0=null;cachedUint32ArrayMemory0=null;cachedUint8ArrayMemory0=null;cachedUint8ClampedArrayMemory0=null;return wasm;\n}\n'''

def save(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def worker(config):
    sys.path.insert(0,str(ROOT/'reconstruction'));from resource_spec.mpq import Archive
    assert sha(INDEX)==INDEX_SHA
    con=sqlite3.connect(INDEX.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    archives={};byname={}
    for row in con.execute('select * from files'):
        byname.setdefault(row['normalized_name'],[]).append(dict(row))
    for row in config['archives']:
        p=DATA/row['name'];assert p.stat().st_size==row['bytes']
        a=Archive(p);assert hashlib.sha256(a.hash_table_bytes).hexdigest()==row['hash_table_sha256']
        assert hashlib.sha256(a.block_table_bytes).hexdigest()==row['block_table_sha256'];archives[row['name']]=a
    out=Path(config['directory']);assets=out/'actual-assets';assets.mkdir(exist_ok=True)
    inventory=[];cache={};total=0
    print(json.dumps({'worker_ready':True}),flush=True)
    for line in sys.stdin:
        try:
            request=json.loads(line);path=request['path'];parts=path.split('/')
            assert parts and all(p not in ('','..','.')and'\\'not in p for p in parts)
            chain='\\'.join(parts);key=chain.upper()
            if key in cache:print(json.dumps(cache[key]),flush=True);continue
            rows=byname.get(key,[])
            if not rows:result={'status':404,'path':path,'chain':chain,'reason':'No actual MPQ index match; no alias or default supplied'}
            else:
                if len({r['decoded_sha256']for r in rows})!=1:raise ValueError('Unresolved different-byte archive precedence')
                row=rows[0];archive=archives[row['archive']];entry=archive.lookup(row['name'])
                assert entry.block==row['block_index'] and entry.slot==row['hash_slot']
                block=archive.blocks[entry.block];assert block.offset==row['data_offset']and block.size==row['decoded_bytes']
                if len(inventory)>=config['asset_file_budget'] or total+block.size>config['asset_decoded_byte_budget']:raise ValueError('Declared asset request/decoded-byte budget reached')
                data=archive.read(row['name']);digest=hashlib.sha256(data).hexdigest()
                assert digest==row['decoded_sha256']==row['reference_sha256']
                target=assets/(digest+'.bin');target.write_bytes(data);total+=len(data)
                result={'status':200,'path':path,'chain':chain,'file':str(target),'bytes':len(data),'sha256':digest,
                 'index_sha256':INDEX_SHA,'archive':row['archive'],'block_index':entry.block,'hash_slot':entry.slot,
                 'block':block.__dict__,'hash_entry':entry.__dict__,'prior_index_row':row,
                 'same_byte_owners':[r['archive']for r in rows],'archive_precedence_inferred':False}
        except Exception as e:result={'status':500,'path':request.get('path')if isinstance(request,dict)else None,'error':repr(e)}
        inventory.append(result);cache[chain.upper()]=result
        save(out/'actual-assets-inventory.json',{'index_sha256':INDEX_SHA,'requests':inventory,'decoded_bytes':total,'aliasing':False,'latest135_asset_equivalence':False})
        print(json.dumps(result),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--asset-worker',type=Path);args=p.parse_args()
    if args.asset_worker:return worker(json.loads(args.asset_worker.read_text()))
    before={n:sha(ROOT/n)for n in FILES};assert sha(SOURCE)==SOURCE_SHA and sha(GLUE)==GLUE_SHA and sha(NODE)==NODE_SHA
    assert PW.is_dir()and CHROME.is_file();assert sha(NAME_INDEX)==NAME_INDEX_SHA and sha(AUX)==AUX_SHA and sha(INDEX)==INDEX_SHA
    con=sqlite3.connect(INDEX.resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    archives=[dict(row)for row in con.execute('select * from archives order by name')]
    for row in archives:assert sha(DATA/row['name'])==row['sha256']
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('entry-world0135-probe-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    original=SOURCE.read_bytes();types,imports,decl,bodies,segments=parse_source(original);sections=section_list(original)
    assert len(imports)==878 and 8 not in[s[0]for s in sections]
    ex=next(s for s in sections if s[0]==7);exports,first=export_entries(original,ex);added=b'';roles=[]
    for name,(fn,params,results,h)in ROLES.items():
        assert types[decl[fn-len(imports)]]==(bytes.fromhex(params),bytes.fromhex(results));a,b=bodies[fn];assert hashlib.sha256(original[a:b]).hexdigest()==h
        n=name.encode();added+=unsigned(len(n))+n+b'\0'+unsigned(fn);roles.append({'name':name,'index':fn,'parameters_hex':params,'results_hex':results,'body_start':a,'body_end':b,'body_sha256':h})
    payload=unsigned(len(exports)+len(roles))+original[first:ex[3]]+added
    changed=original[:ex[1]]+b'\x07'+unsigned(len(payload))+payload+original[ex[3]:];ns=section_list(changed);unchanged=[]
    assert len(ns)==len(sections)
    for a,b in zip(sections,ns):
        assert a[0]==b[0]
        if a[0]!=7:assert original[a[1]:a[3]]==changed[b[1]:b[3]];unchanged.append({'section':a[0],'sha256':hashlib.sha256(original[a[1]:a[3]]).hexdigest()})
    assert export_entries(changed,next(s for s in ns if s[0]==7))[0]==exports+[(r['name'],0,r['index'])for r in roles]
    module=out/'entry-world135.wasm';module.write_bytes(changed);validator=ROOT/'.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate';assert sha(validator)==VALIDATOR_SHA
    check=subprocess.run([str(validator),'--enable-all',str(module)],capture_output=True,timeout=45);(out/'validation.stderr').write_bytes(check.stderr);assert check.returncode==0
    bridge=out/'entry-world135-bridge.mjs';prefix=GLUE.read_bytes();bridge.write_bytes(prefix+APPEND.encode())
    data_segments,element_base,elements=module_data(original);addr=1495776
    seg=next(s for s in data_segments if s['address']<=addr and addr+36<=s['address']+s['size'])
    off=seg['file_start']+addr-seg['address'];vt=original[off:off+36];words=struct.unpack('<9I',vt)
    assert words[:3]==(1721,24,8) and words[8]==1727 and elements[words[8]-element_base]==176109
    a,b=bodies[176109];assert hashlib.sha256(original[a:b]).hexdigest()=='ffa2edca2d3a0ef88bfcea9e5cf488eb6a4d98e7f1b4011ce4fa3de388c0b4ea'
    initial=ROOT/'evidence/full0135-oracle-20261101T055136.418672Z/initial135-comparison.json'
    assert sha(initial)=='f19963db365d60021f4d547a464622bbc5eebb69ba42e9f4ff55237de1457649'
    config={'directory':str(out),'wasm_path':str(module),'wasm_sha256':sha(module),'glue_path':str(bridge),'glue_sha256':sha(bridge),
      'official_glue_sha256':GLUE_SHA,'official_glue_prefix_bytes':len(prefix),'original_sha256':SOURCE_SHA,'roles':roles,'unchanged_nonexport_sections':unchanged,
      'imports':[{'id':i,'module':m,'name':n,'type_index':t,'allowed':i in ALLOWED}for i,(m,n,t)in enumerate(imports)],
      'playwright_path':str(PW),'chrome_path':str(CHROME),'chrome_sha256':sha(CHROME),'node_path':str(NODE),'python_path':sys.executable,
      'asset_worker_script':str(Path(__file__).resolve()),'archives':archives,'asset_index_path':str(INDEX),'asset_index_sha256':INDEX_SHA,
      'name_index_path':str(NAME_INDEX),'name_index_sha256':NAME_INDEX_SHA,'aux_path':str(AUX),'aux_sha256':AUX_SHA,
      'memory_page_cap':4096,'memory_cap_bytes':256*1024*1024,'deadline_seconds':90,'asset_file_budget':1024,'asset_decoded_byte_budget':256*1024*1024,
      'capture_chunk_bytes':1024*1024,
      'prior_failed_development_batch':{'path':'evidence/entry-world0135-probe-20261101T092647.702804Z',
       'reason':'Node512MiB heap OOM in giant CDP capture message;256-file research cap returned156budget500s after256 realfiles/41097386B. All three prior processes missing before retry.',
       'changes':'Only split memory transfer into1MiB chunks, explicit server-error stop before1089, and measured file-count budget256->1024. WASM256MiB/profile/original bodies unchanged.'},
      'selected_profile_input':{'region_id':'elwynn','class_byte':1,'race_byte':1,'object_id_u64':'0','app_lcg_seed_u64':'0','live_bytes':372,'allocation_bytes':376,
       'basis':'Explicit empty376 selected-profile input previously verified with complete1560; App+3376 same live layout. This is not the complete menu/profile producer.',
       'initial1560_receipt':str(initial.relative_to(ROOT)),'initial1560_receipt_sha256':sha(initial)},
      'app_input':{'allocation_bytes':5168,'initial_poison':165,'account_offset':4160,'account_bytes':368,'selected_profile_offset':3376,'cache5116':0,
       'transport_vtable':1495776,'transport_vtable36_hex':vt.hex(),'transport_method32_table_slot':1727,'transport_method32_original_function':176109,
       'transport_method32_body_sha256':hashlib.sha256(original[a:b]).hexdigest(),'app4776':0,'flags5163_u32':4278255360},
      'unknowns':['Selected-profile/menu and initial App entropy are explicit research inputs.','World/RC/VFS/Once produced only by original6730/2902; never injected.',
       'Full current asset equivalence and MPQ precedence for differing duplicates are unknown.','No independent complete-world or entry model; this batch is observation only.'],
      'source_before':before}
    cfg=out/'entry-world135-config.json';save(cfg,config);snap=out/'source-snapshot';snap.mkdir()
    for n,h in before.items():q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    frozen={str(q.relative_to(out)):sha(q)for q in(module,bridge,cfg)};tmp=out/'browser-tmp';tmp.mkdir()
    command=[str(NODE),'--max-old-space-size=512',str(ROOT/'scripts/run_entry_world135.mjs'),str(cfg)]
    started=time.monotonic();stdout=out/'entry-world135.stdout';stderr=out/'entry-world135.stderr'
    with stdout.open('wb')as so,stderr.open('wb')as se:
        child=subprocess.Popen(command,stdout=so,stderr=se,env=dict(os.environ,TMPDIR=str(tmp)),start_new_session=True)
        save(out/'owned-process.json',{'pid':child.pid,'pgid':child.pid,'command':command,'outer_deadline_seconds':120})
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            code=child.returncode
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA
    assert frozen=={str(q.relative_to(out)):sha(q)for q in(module,bridge,cfg)}
    runtime=out/'entry-world135-runtime.json';receipt={'version':'0.135.1','build':'0898d5e3','kind':'observational_true_world_and_entry_probe_not_independent_model',
      'original_sha256':SOURCE_SHA,'source_before':before,'source_after':after,'source_snapshots':True,'input_frozen_before_original':True,
      'process':{'pid':child.pid,'pgid':child.pid,'command':command,'exit_code':code,'seconds':time.monotonic()-started,'outer_deadline_seconds':120},
      'artifacts':{q.name:sha(q)for q in(module,bridge,cfg,stdout,stderr,runtime)if q.exists()},
      'runtime':json.loads(runtime.read_text())if runtime.exists()else None,'new_independent_model_cases':0,'appstart_forbidden':True,'user_profile_used':False}
    save(out/'entry-world135-probe-receipt.json',receipt)
    print(json.dumps({'directory':str(out),'exit_code':code,'status':(receipt['runtime']or{}).get('status'),'error':(receipt['runtime']or{}).get('error')}))

if __name__=='__main__':main()
