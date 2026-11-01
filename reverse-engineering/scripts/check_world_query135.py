#!/usr/bin/env python3
"""Independent true-world query consumers from pinned original snapshot input."""
from collections import Counter
from dataclasses import asdict
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
from build_world_snapshot135_oracle import build_snapshot135
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.dont_write_bytecode=True
FILES=('scripts/check_world_query135.py','scripts/run_world_query135_oracle.mjs','scripts/trace_world_query135.py',
    'scripts/build_world_snapshot135_oracle.py','scripts/world_snapshot135_host.mjs','scripts/build_full135_oracle.py',
    'scripts/build_upgrade134_oracle.py','scripts/source_closure135.py','reconstruction/resource_spec/__init__.py',
    'reconstruction/resource_spec/world_query135.py','reconstruction/resource_spec/terrain135.py',
    'reconstruction/resource_spec/entry_resources135.py','reconstruction/resource_spec/dbc.py')+core_sources(ROOT,'binary32.py')
IMPORTED={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from resource_spec.terrain135 import sample_terrain
from resource_spec.world_query135 import (decode_world_snapshot,nearest_raster,SearchRaster135,
    QueryBoundsTrap135,NavGrid135,probe_nav)

SNAPSHOT=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_world6730.memory'
SNAPSHOT_SHA='f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
WORLD_RC=26204808
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node';RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
POISON='a5'*16


def expected(c,world):
    if c['kind']=='height':
        output={}
        for role,value in [('terrain_height',sample_terrain(world.tiles,c['x_bits'],c['y_bits'])),('world_height',world.height(c['x_bits'],c['y_bits']))]:
            output[role]=dict(found=value.found,value_bits=value.value_bits,
                output16_hex=(struct.pack('<II',int(value.found),value.value_bits)+bytes([0xa5])*8).hex())
        return dict(id=c['id'],kind='height',entry_status='returned',output=output)
    raster=SearchRaster135(tuple(c['raster']['values_bits']),tuple(c['raster']['origin_xy_bits']),c['raster']['width'])
    try:value=nearest_raster(raster,c['x_bits'],c['y_bits'])
    except QueryBoundsTrap135:return dict(id=c['id'],kind='nearest',entry_status='bounds_trap',output16_hex=POISON)
    words=list(value.xyz_bits)if value.found else[0xa5a5a5a5]*3
    return dict(id=c['id'],kind='nearest',entry_status='returned',output16_hex=struct.pack('<4I',int(value.found),*words).hex(),
                output=dict(found=value.found,xyz_words=words))


def corpus(world,pilot):
    rows=[];b=f.from_float
    def point(group,x,y):rows.append(dict(id=len(rows),kind='height',group=group,x_bits=b(x),y_bits=b(y)))
    def nearest(group,width,finite,coords=(.25,.25),origin=(0,0),count=None):
        values=[0x7fc01234]*(width*width if count is None else count)
        for index,value in finite.items():values[index]=b(value)
        rows.append(dict(id=len(rows),kind='nearest',group=group,x_bits=b(coords[0]),y_bits=b(coords[1]),
            raster=dict(values_bits=values,origin_xy_bits=[b(x)for x in origin],width=width)))
    point('real-opening-center',-9386,-623)
    point('outside-all-terrain',100000,100000)
    nearest('nearest-current-cell',1,{0:68})
    nearest('nearest-tie-preserves-first',3,{1:11,3:33,5:55,7:77},(.75,.75))
    nearest('nearest-no-valid-keeps-payload',3,{})
    nearest('nearest-short-count-trap',3,{},(.75,.75),count=1)
    if pilot:return rows
    rng=random.Random(0x2318129631)
    for _ in range(400):point('real-nine-tile-geography',rng.uniform(-10200,-8450),rng.uniform(-1650,50))
    for x in(-9536.001,-9536,-9535.999,-9535.75,-9256.001,-9256,-9255.999):
        for y in(-773.001,-773,-772.999,-772.75,-493.001,-493,-492.999):point('cache-boundary-half-cell',x,y)
    secondary=world.secondary;assert secondary is not None
    finite=[i for i,value in enumerate(secondary.values_bits)if not f.is_nan(value)]
    nan=[i for i,value in enumerate(secondary.values_bits)if f.is_nan(value)]
    for group,indices in [('real-model-raster-nonNaN',finite),('real-model-raster-NaN',nan)]:
        for index in indices[::max(1,len(indices)//96)][:96]:
            x=f.to_float(secondary.origin_xy_bits[0])+(index%secondary.width+.5)*.5
            y=f.to_float(secondary.origin_xy_bits[1])+(index//secondary.width+.5)*.5
            point(group,x,y)
    for _ in range(256):point('real-local-nonflat-world',rng.uniform(-9536,-9256),rng.uniform(-773,-493))
    for width in(1,2,3,8):
        for x,y in((-.25,-.25),(.25,.25),(.75,.75),(width*.5-.25,width*.5-.25),(width*.5+.25,width*.5+.25)):
            nearest('nearest-edges-and-outside',width,{0:-13,width*width-1:89},(x,y))
    nearest('nearest-positive-infinity-valid',1,{0:float('inf')})
    nearest('nearest-negative-infinity-valid',1,{0:-float('inf')})
    nearest('nearest-radius20-inclusive',41,{0:123},(10.25,10.25))
    nearest('nearest-radius21-excluded',43,{0:123},(10.75,10.75))
    for k in range(32):
        width=8;chosen=rng.sample(range(64),rng.randrange(1,10));values={j:rng.uniform(-100,300)for j in chosen}
        nearest('nearest-seeded-score-and-order',width,values,(rng.uniform(-2,6),rng.uniform(-2,6)))
    return rows


def nav_contract_replay(world):
    """Local/static inline contract replay, explicitly not original execution."""
    assert world.nav is not None;nav=world.nav;b=f.from_float;rows=[]
    for index in range(0,len(nav.values),max(1,len(nav.values)//64)):
        x=f.add(nav.origin_xy_bits[0],b(index%nav.width+.25));y=f.add(nav.origin_xy_bits[1],b(index//nav.width+.25))
        result=probe_nav(nav,x,y);assert result.in_bounds and result.index==index and result.value==nav.values[index]
        rows.append(dict(group='snapshot-byte-grid-local-replay',x_bits=x,y_bits=y,actual=asdict(result)))
    for grid,name in((None,'missing'),(NavGrid135(b'\x00\x01\x02\xff',(0,0),2),'controlled-raw-bytes')):
        for x,y in((0,0),(.25,.25),(1.25,0),(0,1.25),(1.25,1.25),(-.01,0),(2,0)):
            rows.append(dict(group=name,x_bits=b(x),y_bits=b(y),actual=asdict(probe_nav(grid,b(x),b(y)))))
    try:probe_nav(NavGrid135(b'\x01',(0,0),2),b(1),b(1))
    except QueryBoundsTrap135:rows.append(dict(group='short-nav-vector',rejected=True))
    else:raise AssertionError('Short navigation count must trap')
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORTED and sha(SNAPSHOT)==SNAPSHOT_SHA and sha(RUNTIME)==RUNTIME_SHA
    memory=SNAPSHOT.read_bytes();world=decode_world_snapshot(memory,WORLD_RC);queries=corpus(world,args.phase=='pilot')
    wants=[expected(c,world)for c in queries];nav_replay=nav_contract_replay(world)
    out,manifest=build_snapshot135(['world_height','terrain_height','nearest_height']);snap=out/'source-snapshot'
    for n,h in before.items():q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    inputs=out/'world-query135-inputs.json';inputs.write_text(json.dumps(dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,world_rc=WORLD_RC,queries=queries),separators=(',',':'))+'\n')
    fixture=out/'world-query135-expected.json';fixture.write_text(json.dumps(wants,separators=(',',':'))+'\n')
    source_ranges=[]
    for label,offset,size in world.source_ranges:
        if label=='word':continue
        source_ranges.append(dict(label=label,offset=offset,bytes=size,sha256=hashlib.sha256(memory[offset:offset+size]).hexdigest()))
    ranges=out/'world-query135-source-ranges.json';ranges.write_text(json.dumps(source_ranges,indent=2)+'\n')
    local=out/'world-query135-nav-local-replay.json';local.write_text(json.dumps(dict(original_executed=False,cases=nav_replay),indent=2)+'\n')
    freeze={q.name:sha(q)for q in(inputs,fixture,ranges,local,out/'manifest.json',out/manifest['module_file'])}
    cmd=[str(RUNTIME),'--max-old-space-size=768','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_world_query135_oracle.mjs'),str(out),str(inputs)]
    result=out/'world-query135-results.jsonl';stderr=out/'world-query135-stderr.log';start=time.monotonic()
    with result.open('w')as so,stderr.open('w')as se:
        child=subprocess.Popen(cmd,stdout=so,stderr=se,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError(f'Owned60s deadline:{out}')
    if code:raise RuntimeError(f'Original world query exit{code}:{out}')
    actual=[json.loads(x)for x in result.read_text().splitlines()];assert len(actual)==len(wants)
    failures=[]
    for w,a in zip(wants,actual):
        compare={k:v for k,v in a.items()if k!='error'}
        if w!=compare:failures.append(dict(case=w['id'],expected=w,actual=compare))
    mismatch=out/'world-query135-mismatches.json';mismatch.write_text(json.dumps(failures,indent=2)+'\n')
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA
    assert freeze=={q.name:sha(q)for q in(inputs,fixture,ranges,local,out/'manifest.json',out/manifest['module_file'])}
    runtime=out/'world-query135-runtime.json';rt=json.loads(runtime.read_text());receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(queries),
        original_calls=rt['calls'],differences=len(failures),groups=dict(Counter(c['group']for c in queries)),kinds=dict(Counter(c['kind']for c in queries)),
        source_before=before,source_after=after,original_sha256=SOURCE_SHA,snapshot_path=str(SNAPSHOT.relative_to(ROOT)),snapshot_sha256=SNAPSHOT_SHA,snapshot_bytes=len(memory),world_rc=WORLD_RC,
        independent_expected_before_original=True,input_contains_expected=False,input_exact_keys=['snapshot_path','snapshot_sha256','world_rc','queries'],
        world_input=dict(tiles=len(world.tiles),chunks=sum(len(t.chunks)for t in world.tiles),terrain_vertices=sum(len(c.vertices)for t in world.tiles for c in t.chunks),
            primary_present=world.primary is not None,secondary_width=world.secondary.width,nav_width=world.nav.width,
            nav_bytes=dict(Counter(world.nav.values)),fallback_height_bits=world.fallback_height_bits,flat=world.flat_height_bits is not None),
        nav_model_local_replay_cases=len(nav_replay),nav_model_new_original_calls=0,
        artifacts={q.name:sha(q)for q in(inputs,fixture,ranges,local,result,stderr,mismatch,runtime,out/'manifest.json',out/manifest['module_file'])},runtime=rt,
        process=dict(pid=child.pid,pgid=child.pid,command=cmd,exit_code=code,seconds=time.monotonic()-start,deadline_seconds=60),
        limitations=['Snapshot-derived trueworld consumer input,not an independent world producer or freshbootstrap.',
            'Complete29631/18670 and23181 run unchanged; actualnavigation predicate isinline8751/13516 and only locallyreplayed here,positionconsumer differentialseparate.',
            'Actualsnapshot primaryabsent;nearest23181 is controlledexplicitraster,not falselyrelabelled trueworldprimarycoverage.',
            'Canonical145 snapshot terrainadapter only; othermodel/objectvectors,ownership/lifetime and allresourceproducer semantics areunknown.',
            'All878imports denied,actual0;separate256MiBrestoredmemoryhost,notshared32MiBNodehost;externrefs/JSstate notrestored,nocalls required inthisdomain.',
            'Fullsnapshotincludesallocatorstate;oneglobal0initial1048576andoriginal6730onlynormalreturnrestorestaticproof plusactualquerystackreadback;notexhaustiveallgameglobalrestorationproof.',
            'No complete8751/13516bodyormain880/headless/fullgame completion claimed.'])
    target=out/'world-query135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),cases=len(queries),original_calls=rt['calls'],differences=len(failures),first_failures=failures[:2])))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
