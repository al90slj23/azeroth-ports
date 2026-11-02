#!/usr/bin/env python3
"""Expected-first139 raw-produced world -> unchanged original query entries."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,math,os,random,signal,struct,subprocess,sys,time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'reconstruction')]
from build_world_query139_oracle import build,SOURCE,SOURCE_SHA,TRACE,TRACE_SHA
from check_asset_world139 import load_world139,REFERENCE,SNAPSHOT_SHA,WORLD_RC,REVIEW,REVIEW_SHA
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from core_spec import binary32 as f
from resource_spec.terrain135 import sample_terrain
from resource_spec.world_query135 import SearchRaster135,nearest_raster,QueryBoundsTrap135

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def corpus(world,pilot=False):
    rows=[];b=f.from_float;rng=random.Random(0x13929912)
    def point(group,x,y):rows.append(dict(id=len(rows),kind='height',group=group,x_bits=b(x),y_bits=b(y)))
    def search(group,width,values,xy=(.25,.25),count=None):
        data=[0x7fc01234]*(width*width if count is None else count)
        for i,v in values.items():data[i]=b(v)
        rows.append(dict(id=len(rows),kind='nearest',group=group,x_bits=b(xy[0]),y_bits=b(xy[1]),raster=dict(width=width,origin_xy_bits=[0,0],values_bits=data)))
    point('declared139Elwynn-centre',-9386,-623)
    point('outside-terrain',100000,100000)
    search('nearest-direct',1,{0:68})
    search('nearest-tie-first',3,{1:11,3:33,5:55,7:77},(.75,.75))
    search('nearest-no-valid',3,{})
    search('nearest-short-count-bounds-trap',3,{},(.75,.75),count=1)
    if pilot:return rows
    for tile in world.tiles:
        for chunk in tile.chunks:
            a,z=chunk.vertices[0],chunk.vertices[-1]
            # Every independently parsed chunk contributes an interior sample.
            point('all-produced-terrain-chunks',(f.to_float(a[0])+f.to_float(z[0]))*.5,(f.to_float(a[1])+f.to_float(z[1]))*.5)
    for _ in range(500):point('seeded-nine-tile-region',rng.uniform(-10200,-8450),rng.uniform(-1650,50))
    ox,oy=map(f.to_float,world.nav.origin_xy_bits);w=world.nav.width
    for _ in range(256):point('seeded-cache-interior',rng.uniform(ox,ox+w),rng.uniform(oy,oy+w))
    for x in(ox-.001,ox,ox+.001,ox+.25,ox+w-.001,ox+w,ox+w+.001):
        for y in(oy-.001,oy,oy+.001,oy+.25,oy+w-.001,oy+w,oy+w+.001):point('cache-edge-halfcell',x,y)
    for name,predicate in [('secondary-finite',lambda x:not f.is_nan(x)),('secondary-NaN',f.is_nan)]:
        indices=[i for i,x in enumerate(world.secondary.values_bits)if predicate(x)]
        for index in indices[::max(1,len(indices)//96)][:96]:
            x=f.to_float(world.secondary.origin_xy_bits[0])+(index%world.secondary.width+.5)*.5
            y=f.to_float(world.secondary.origin_xy_bits[1])+(index//world.secondary.width+.5)*.5
            point(name,x,y)
    for width in(0,1,2,3,8):
        for xy in((-.25,-.25),(.25,.25),(.75,.75),(width*.5-.25,width*.5-.25),(width*.5+.25,width*.5+.25)):
            search('nearest-edges',width,{}if not width else{0:-13,width*width-1:89},xy)
    search('nearest-positive-inf-height',1,{0:float('inf')})
    search('nearest-negative-inf-height',1,{0:-float('inf')})
    search('nearest-radius20-inclusive',41,{0:123},(10.25,10.25))
    search('nearest-radius21-excluded',43,{0:123},(10.75,10.75))
    for _ in range(32):
        chosen=rng.sample(range(64),rng.randrange(1,10));search('nearest-seeded-order',8,{i:rng.uniform(-100,300)for i in chosen},(rng.uniform(-2,6),rng.uniform(-2,6)))
    assert len(rows)<=12000
    return rows


def expected(case,world):
    if case['kind']=='height':
        values={}
        for name,value in [('terrain_height',sample_terrain(world.tiles,case['x_bits'],case['y_bits'])),('world_height',world.height(case['x_bits'],case['y_bits']))]:
            values[name]=dict(found=value.found,value_bits=value.value_bits,output16_hex=(struct.pack('<II',int(value.found),value.value_bits)+bytes([0xa5])*8).hex())
        return dict(id=case['id'],kind=case['kind'],entry_status='returned',output=values)
    r=case['raster'];grid=SearchRaster135(tuple(r['values_bits']),tuple(r['origin_xy_bits']),r['width'])
    try:value=nearest_raster(grid,case['x_bits'],case['y_bits'])
    except QueryBoundsTrap135:return dict(id=case['id'],kind=case['kind'],entry_status='bounds_trap',output16_hex='a5'*16)
    words=list(value.xyz_bits)if value.found else[0xa5a5a5a5]*3
    return dict(id=case['id'],kind=case['kind'],entry_status='returned',output=dict(found=value.found,xyz_words=words),output16_hex=struct.pack('<4I',int(value.found),*words).hex())


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('world_comparison',type=Path);p.add_argument('--pilot',action='store_true');a=p.parse_args()
    model=a.model.resolve();comparison=a.world_comparison.resolve();observation=json.loads(comparison.read_text())
    assert observation['status']=='matched'and observation['model_receipt_sha256']==sha(model/'receipt.json')and observation['world_rc']==WORLD_RC
    assert sha(REVIEW)==REVIEW_SHA and sha(TRACE)==TRACE_SHA and sha(NODE)==NODE_SHA
    world,model_receipt,_=load_world139(model)
    declared=set(('scripts/check_world_query139.py','scripts/run_world_query139_oracle.mjs','scripts/build_world_query139_oracle.py','scripts/check_asset_world139.py','scripts/trace_world139.py','scripts/production_closure135.py','scripts/source_closure137.py')+production_sources135(ROOT,'resource_spec.world_query135','resource_spec.terrain135'))
    while True:
        try:edges=verify_local_source_closure(sorted(declared));break
        except AssertionError as error:
            pair=error.args[0]
            if not isinstance(pair,tuple)or len(pair)!=2 or pair[1]in declared or not(ROOT/pair[1]).is_file():raise
            declared.add(pair[1])
    files=tuple(sorted(declared))
    before={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-query139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    for n,h in before.items():
        q=out/'source-snapshot'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    rows=corpus(world,a.pilot);answers=[expected(c,world)for c in rows];save(out/'inputs.json',rows);save(out/'expected.json',answers)
    manifest=build(out)
    ranges=comparison.parent/observation['source_ranges_file'];assert sha(ranges)==observation['source_ranges_sha256']
    cfg=dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(REFERENCE/'after_real_world6786.memory'),snapshot_sha256=SNAPSHOT_SHA,world_rc=WORLD_RC,source_ranges_file=str(ranges),source_ranges_sha256=sha(ranges));save(out/'config.json',cfg)
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','manifest.json','config.json',manifest['module_file'])}
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_world_query139_oracle.mjs'),str(out),str(out/'config.json')]
    began=time.monotonic();deadline=120;error=None
    with(out/'actual.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=deadline))
        try:child.wait(timeout=deadline)
        except subprocess.TimeoutExpired as e:error=str(e)
        finally:
            if child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),deadline_seconds=deadline,seconds=time.monotonic()-began,error=error);save(out/'process-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];differences=[]
    for i,(want,got)in enumerate(zip(answers,actual)):
        if want!=got:differences.append(dict(id=i,expected=want,actual=got))
    if len(actual)!=len(answers):differences.append(dict(expected_records=len(answers),actual_records=len(actual)))
    if child.returncode:differences.append(dict(original_exit_code=child.returncode))
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    after={n:sha(ROOT/n)for n in files};assert before==after and frozen=={n:sha(out/n)for n in frozen}
    report=dict(version='0.139.0',build='f79c5e2b4',status='matched'if not differences else'failed_preserved',cases=len(rows),complete_query_calls=runtime['full_query_calls']if runtime else None,differences=differences,source_sha256_before=before,source_sha256_after=after,source_files=len(files),source_import_edges=edges,
        model_receipt_sha256=sha(model/'receipt.json'),healthy_v2_world_observation_sha256=sha(comparison),context_review_sha256=REVIEW_SHA,static_trace_sha256=TRACE_SHA,
        expected_before_original=True,expected_sha256=sha(out/'expected.json'),input_sha256=sha(out/'inputs.json'),actual_sha256=sha(out/'actual.jsonl'),manifest_sha256=sha(out/'manifest.json'),runtime=runtime,process=terminal,
        pilot=a.pilot,old_acceptance_transferred=False,model_world_from_original_snapshot=False,original_side_uses_v2_snapshot=True,
        full_mainloop_frames=0,native_windows_execution=False,complete_games=0,
        limitations=['One independent raw139 Elwynn/no-primary world; othermaps/render/cache ownership not accepted.','Nearest cases use explicit controlled descriptors,not a primary producer in this default world.','Original query process restores corrected v2 memory only,not JS/externref/naturalApp bootstrap.','Panic diagnostic text differs by static location metadata; only bounded trap/result contract compared.'])
    save(out/'comparison.json',report);print(json.dumps(dict(directory=str(out),cases=len(rows),query_calls=report['complete_query_calls'],differences=len(differences),process=terminal)),flush=True)
    if differences or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)


if __name__=='__main__':main()
