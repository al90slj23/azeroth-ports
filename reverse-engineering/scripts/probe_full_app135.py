#!/usr/bin/env python3
"""Separate whole-original-app observation; no caller-built App or memory edits."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,hashlib,json,os,plistlib,signal,subprocess,sys,time
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha

FILES=('scripts/probe_full_app135.py','scripts/run_full_app135.mjs','scripts/browser_full_app135.mjs',
       'scripts/probe_entry_world135.py','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py',
       'scripts/trace_coop.py','scripts/wasm_index.py','reconstruction/resource_spec/__init__.py','reconstruction/resource_spec/mpq.py')
APPEND='''
// Dedicated observer bridge: original prefix/functions remain byte-for-byte.
export function fullApp135Exports(){return wasm;}
export async function fullApp135Start(module,observe,wrapArguments,afterCall){
 const real=__wbg_get_imports(),surface=WebAssembly.Module.imports(module),bindings={};
 if(surface.length!==878||surface.some(x=>x.kind!=='function'))throw Error('Fixed original import surface');
 for(let id=0;id<surface.length;id++){const item=surface[id],fn=real[item.module]?.[item.name];if(typeof fn!=='function')throw Error('Official binding missing');bindings[item.module]??={};
  bindings[item.module][item.name]=function(...originalArgs){observe('before',id,item.name,originalArgs);const args=wrapArguments(id,originalArgs);const value=Reflect.apply(fn,this,args);observe('after',id,item.name,originalArgs,value);afterCall(id,args,value);return value;};
 }
 const instance=await WebAssembly.instantiate(module,bindings);
 observe('original_finalizer_entry',-1,'__wbg_finalize_init',[]);
 return __wbg_finalize_init(instance,module);
}
'''

def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False

def verify_owned_terminal(child,runtime):
    pids={child.pid};groups={child.pid};observed=[]
    for row in (runtime or {}).get('events',[]):
        if row.get('label') in ('browser_started','worker_started'):
            pid,group=row['pid'],row.get('pgid');pids.add(pid)
            if group==pid or group==child.pid:groups.add(group)
            elif group is not None:observed.append({'unexpected_group_not_signaled':group,'pid':pid})
    assert os.getpgrp()not in groups and all(p>1 for p in groups)
    for group in groups:
        if not missing(group,True):
            os.killpg(group,signal.SIGTERM);time.sleep(.25)
            if not missing(group,True):os.killpg(group,signal.SIGKILL)
            observed.append({'owned_group_signaled':group})
    until=time.monotonic()+3
    while time.monotonic()<until and(any(not missing(p)for p in pids)or any(not missing(g,True)for g in groups)):time.sleep(.05)
    return {'owned_pids':{str(p):missing(p)for p in pids},'owned_pgids':{str(p):missing(p,True)for p in groups},'events':observed,
            'all_owned_terminal':all(missing(p)for p in pids)and all(missing(g,True)for g in groups)and not any('unexpected_group_not_signaled'in x for x in observed)}

def prepare(before,browser_profile):
    prior=json.loads((ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/entry-world135-config.json').read_text())
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('full-app0135-probe-%Y%m%dT%H%M%S.%fZ');out.mkdir();(out/'tmp').mkdir()
    glue=ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js';assert sha(glue)==prior['official_glue_sha256']
    bridge=out/'bridge.mjs';bridge.write_bytes(glue.read_bytes()+APPEND.encode())
    if browser_profile=='metal':
        chrome=Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        version=plistlib.loads(Path('/Applications/Google Chrome.app/Contents/Info.plist').read_bytes())['CFBundleShortVersionString']
        browser_args=['--use-angle=metal','--enable-unsafe-webgpu']
        expected_architecture='metal-3'
    else:
        chrome=Path('/Users/al90slj23/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell').resolve()
        version='chromium-headless-shell1248';browser_args=['--enable-unsafe-webgpu'];expected_architecture='swiftshader'
    assert chrome.is_file()
    node=ROOT/'.toolchain/runtime/node_modules/node/bin/node';assert sha(node)=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    package=Path(prior['playwright_path'])/'package.json';package_metadata=json.loads(package.read_text())
    aux=ROOT/'originals/official-full-app-support-20261101T114415.104930Z/inline0.js';assert sha(aux)==prior['aux_sha256']
    font=ROOT/'originals/official-full-app-font-20261101T122429.151414Z/azs_sc.ttf';assert sha(font)=='5499291b696324c10c3e7f2d3d89a5c490897319a629141ea5b40c85e62e6224'
    assert font.stat().st_size<=32*1024*1024
    config={k:prior[k]for k in ('archives','name_index_path','name_index_sha256','playwright_path','asset_index_path','asset_index_sha256')}
    config.update(directory=str(out),original_path=str(SOURCE),original_sha256=SOURCE_SHA,glue_path=str(bridge),glue_sha256=sha(bridge),glue_prefix_bytes=glue.stat().st_size,official_glue_sha256=sha(glue),aux_path=str(aux),aux_sha256=sha(aux),
        python_path=sys.executable,asset_worker_script=str(ROOT/'scripts/probe_entry_world135.py'),chrome_path=str(chrome),chrome_sha256=sha(chrome),
        node_path=str(node),node_sha256=sha(node),playwright_version=package_metadata['version'],playwright_package_sha256=sha(package),
        browser_profile=browser_profile,browser_version=version,browser_extra_args=browser_args,expected_adapter_architecture=expected_architecture,
        font_path=str(font),font_sha256=sha(font),font_bytes=font.stat().st_size,font_origin_url='https://wow.aethus.pl/data/fonts/azs_sc.ttf',
        memory_page_cap=8192,memory_cap_bytes=512*1024*1024,asset_file_budget=1024,asset_decoded_byte_budget=256*1024*1024,capture_chunk_bytes=1024*1024,
        frame_budget=8,observation_seconds=45,source_sha256=before,
        scope='Separate whole original startup host: real878 official browser bindings,loopback resources/capture only. Actual browser GPU backend recorded,not performance validation. Eligible complete idle880 calls observed through original4253 cast867/vtable5305816/env+8 Rc+16 App/setInterval25ms. No research memory writes,syntheticApp/world/profile/cache/Once or external network. Renderer errors remain explicit boundaries,not a successful fullgame boot.')
    cfg=out/'config.json';cfg.write_text(json.dumps(config,indent=2)+'\n');snap=out/'source-snapshot'
    for p in FILES:q=snap/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/p).read_bytes())
    return out,cfg,config

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare-only',action='store_true');parser.add_argument('--directory',type=Path);parser.add_argument('--browser-profile',choices=('swiftshader','metal'),default='metal');args=parser.parse_args()
    before={p:sha(ROOT/p) for p in FILES};assert sha(SOURCE)==SOURCE_SHA
    if args.directory:
        out=args.directory.resolve();assert out.parent==ROOT/'evidence' and out.name.startswith('full-app0135-probe-')
        cfg=out/'config.json';config=json.loads(cfg.read_text());assert config['source_sha256']==before and config['directory']==str(out)
        assert not(out/'owned-process.json').exists(),'A prepared experiment can run only once'
    else:out,cfg,config=prepare(before,args.browser_profile)
    if args.prepare_only:
        print(json.dumps({'directory':str(out),'prepared_only':True,'source_files':len(before),'config_sha256':sha(cfg),'original_executed':False}));return
    bridge=Path(config['glue_path']);assert sha(bridge)==config['glue_sha256'];frozen={str(p):sha(p)for p in(cfg,bridge)}
    assert sha(Path(config['node_path']))==config['node_sha256'] and sha(Path(config['chrome_path']))==config['chrome_sha256']
    assert sha(Path(config['playwright_path'])/'package.json')==config['playwright_package_sha256']
    command=[str(ROOT/'.toolchain/runtime/node_modules/node/bin/node'),'--max-old-space-size=512',str(ROOT/'scripts/run_full_app135.mjs'),str(cfg)]
    began=time.monotonic()
    with (out/'stdout.log').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out/'tmp')))
        (out/'owned-process.json').write_text(json.dumps({'pid':child.pid,'pgid':child.pid,'command':command,'outer_deadline_seconds':120},indent=2)+'\n')
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            code=child.returncode
    after={p:sha(ROOT/p)for p in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and all(sha(Path(p))==digest for p,digest in frozen.items())
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    terminal=verify_owned_terminal(child,runtime)
    status=(runtime or {}).get('status')if terminal['all_owned_terminal']else'cleanup_boundary'
    receipt={'version':'0.135.1','build':'0898d5e3','kind':'controlled_whole_original_app_initialization_observation_not_independent_model',
        'status':status,
        'original_sha256':SOURCE_SHA,'source_sha256_before':before,'source_sha256_after':after,'config_sha256':sha(cfg),'bridge_sha256':sha(bridge),
        'process':{'pid':child.pid,'pgid':child.pid,'exit_code':code,'seconds':time.monotonic()-began,'terminal':terminal},'runtime':runtime,
        'new_independent_cases':0,'new_independent_mainloop_frames':0,'user_profile_used':False,'installed_apps_or_saves_modified':False,'complete_game':False}
    (out/'receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'directory':str(out),'exit_code':code,'status':status,'error':runtime.get('error')if runtime else None,'all_owned_terminal':terminal['all_owned_terminal']}))

if __name__=='__main__':main()
