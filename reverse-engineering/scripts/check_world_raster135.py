#!/usr/bin/env python3
"""Expected-first independent mesh/height-candidate/navigation producer differential."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
from trace_world_raster135 import ROOT,SOURCE,SOURCE_SHA,build
from source_closure135 import core_sources

FILES=('scripts/check_world_raster135.py','scripts/run_world_raster135_oracle.mjs','scripts/trace_world_raster135.py',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/source_closure135.py',
 'reconstruction/resource_spec/__init__.py','reconstruction/resource_spec/world_raster135.py')+core_sources(ROOT,'binary32.py','binary32_sqrt.py','ai_trig135.py')
def sha(p):
 with Path(p).open('rb')as h:return hashlib.file_digest(h,'sha256').hexdigest()
IMPORT_HASH={n:sha(ROOT/n)for n in FILES}
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
INVENTORY=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
INVENTORY_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'

def corpus(full):
    sys.path.insert(0,str(ROOT/'reconstruction'))
    from core_spec import binary32 as f
    from resource_spec.world_raster135 import(CollisionMesh135,CandidateRaster135,CandidateVector135,
       parse_classic_m2_collision,transform_mesh,height_candidates,append_height_candidates,mark_navigation)
    b=f.from_float;cases=[];expected=[]
    def add(*,vertices=None,indices=None,asset=None,pos=(0,0,0),rot=(0,0,0),scale=1,nav_width=12,ceiling=100,cap=4,length=1,ground_pattern=False,ground_base=0,origin_margin=6,label=''):
        ident=len(cases);position=tuple(b(x)for x in pos);rotation=tuple(b(x)for x in rot);origin=(b(pos[0]-origin_margin),b(pos[1]-origin_margin))
        if asset:
            data=Path(asset['file']).read_bytes();assert len(data)==asset['bytes']and hashlib.sha256(data).hexdigest()==asset['sha256']==asset['prior_index_row']['reference_sha256']
            mesh=parse_classic_m2_collision(data);asset_input=dict(path=asset['file'],bytes=len(data),sha256=asset['sha256'],chain=asset['chain'],archive=asset['archive'],prior_index_row=asset['prior_index_row'])
            parsed=dict(vertex_count=len(mesh.vertices),index_count=len(mesh.indices),vertices_hex=b''.join(struct.pack('<3I',*v)for v in mesh.vertices).hex(),indices=list(mesh.indices))
        else:
            mesh=CollisionMesh135(tuple(tuple(b(x)for x in v)for v in vertices),tuple(indices));asset_input=None;parsed=None
        transformed=transform_mesh(mesh,position,rotation,b(scale));grid=CandidateRaster135(origin,nav_width*2)
        # Every index triplet from all actualM2s participates, not only chosen triangles.
        triangles=[(j,j+1,j+2)for j in range(0,len(mesh.indices)-2,3)]
        initial=tuple((0x10203040+j,b(10.25+j))for j in range(cap));state=CandidateVector135(initial,length);candidate_stages=[]
        for tri in triangles:
            samples=height_candidates(grid,*(transformed.vertices[mesh.indices[j]]for j in tri),b(ceiling))
            state=append_height_candidates(state,samples)
            candidate_stages.append(dict(capacity=len(state.storage),length=state.length,storage=[list(x)if x is not None else None for x in state.storage]))
        nav=bytes(2+j%5 for j in range(nav_width*nav_width))+bytes.fromhex('a55ac33c112233')
        ground=tuple(0x7fc12345 if ground_pattern and j%7==0 else 0xff800000 if ground_pattern and j%11==0 else b(ground_base)for j in range(nav_width*nav_width))
        navigation=mark_navigation(nav,nav_width*nav_width,CandidateRaster135(origin,nav_width),mesh,position,rotation,b(scale),ground)
        inp=dict(asset=asset_input,vertices=[list(v)for v in mesh.vertices]if not asset else None,indices=list(mesh.indices)if not asset else None,
          position_bits=list(position),rotation_bits=list(rotation),scale_bits=b(scale),origin_xy_bits=list(origin),height_width=nav_width*2,ceiling_bits=b(ceiling),
          height_triangles=[list(t)for t in triangles],initial_candidate_words=[w for row in initial for w in row],initial_candidate_length=length,
          nav_hex=nav.hex(),nav_active_length=nav_width*nav_width,nav_width=nav_width,ground_bits=list(ground))
        cases.append(dict(id=ident,input=inp));expected.append(dict(id=ident,label=label,parsed=parsed,
          transformed_hex=b''.join(struct.pack('<3I',*v)for v in transformed.vertices).hex(),candidate_stages=candidate_stages,
          navigation_hex=navigation.hex(),nav_header_words=[len(nav),nav_width*nav_width,*origin,nav_width]))
    floor=((0,0,1),(4,0,1),(0,4,1));wall=((0,0,0),(0,4,0),(0,0,3));slope=((0,0,0),(4,0,0),(0,4,4))
    for i,(vertices,indices,rot,scale,ceiling)in enumerate([
     (floor,(0,1,2),(0,0,0),1,100),(wall,(0,1,2),(0,0,0),1,100),
     (slope,(0,1,2),(0,0,0),1,100),(floor,(2,1,0),(15,123,-10),.5,100),
     (((0,0,0),(0,0,0),(0,0,0)),(0,1,2),(0,0,0),1,100),
     (floor,(0,1,2),(0,90,0),0,100),(wall,(2,1,0),(0,0,0),1,100),
     (floor,(0,1,2),(-0.0,-0.0,-0.0),1,.5)]):
        add(vertices=vertices,indices=indices,rot=rot,scale=scale,ceiling=ceiling,cap=[0,1,3,4][i%4],length=0 if i%4==0 else 1,label=f'pilot{i}')
    assets=[x for x in json.loads(INVENTORY.read_text())['requests']if x['status']==200 and x['chain'].endswith('.m2')]
    if not full:assets=[assets[j]for j in(0,12,14)]
    for i,asset in enumerate(assets):add(asset=asset,rot=(0,i*17%360,0),scale=.125,ground_pattern=i%2==0,label='actualM2:'+asset['chain'])
    if full:
        variants=[floor,wall,slope,((0,0,0),(4,0,4.001),(0,4,0)),((0,0,0),(4,0,4.2),(0,4,0)),((.25,.25,.35),(2.25,.25,.35),(.25,2.25,.35)),((.25,.25,2.4),(2.25,.25,2.4),(.25,2.25,2.4)),((0,0,0),(4,0,0),(0,.0000003,0))]
        for i in range(64):
            add(vertices=variants[i%len(variants)],indices=(0,1,2,2,1,0)if i%3==0 else(0,1,2),
             pos=(-9396,-633,68)if i%8==0 else(i%4*.25,-i%3*.125,i%2*.35),rot=[(0,0,0),(15,123,-10),(360,-180,90),(0,45,0)][i%4],
             scale=[.125,.5,1,2][(i//4)%4],nav_width=[0,4,12,20][i%4],ceiling=[100,.35,2.4,-100][(i//8)%4],cap=[0,1,3,4,5][i%5],length=0 if i%5==0 else 1,
             ground_pattern=i%3==0,label='controlled'+str(i))
        add(vertices=((0,0,0),(0,180,0),(0,0,2)),indices=(0,1,2),nav_width=4,origin_margin=2,ground_pattern=True,label='400-step-cap')
        for i,z in enumerate([.34999997,.35,.35000003,2.3999998,2.4,2.4000003]):
            add(vertices=((0,0,z),(0,4,z),(0,0,z+.125)),indices=(0,1,2),nav_width=12,label='strict-height-edge'+str(i))
        for i in range(4):
            add(vertices=wall if i%2 else floor,indices=(0,1,2),pos=(-9396,-633,68),rot=(0,i*90,0),nav_width=280,
             ground_base=68,origin_margin=140,ground_pattern=i==3,ceiling=100,cap=5,length=2,label='actual-grid-dimensions'+str(i))
    return cases,expected

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_HASH and sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA and sha(INVENTORY)==INVENTORY_SHA
    cases,expected=corpus(args.phase=='full');assert before=={n:sha(ROOT/n)for n in FILES}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-raster0135-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    inputs=out/'inputs.json';inputs.write_text(json.dumps(cases,allow_nan=False)+'\n');exp=out/'expected.json';exp.write_text(json.dumps(expected,allow_nan=False)+'\n')
    snap=out/'source-snapshot';snap.mkdir()
    for n,h in before.items():q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    frozen={str(q.relative_to(out)):sha(q)for q in(inputs,exp,out/'manifest.json',out/manifest['module_file'])}
    output=out/'results.jsonl';stderr=out/'stderr.log';cmd=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_world_raster135_oracle.mjs'),str(out),str(inputs)]
    began=time.monotonic()
    with output.open('wb')as so,stderr.open('wb')as se:
        child=subprocess.Popen(cmd,stdout=so,stderr=se,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    after={n:sha(ROOT/n)for n in FILES};assert before==after and frozen=={str(q.relative_to(out)):sha(q)for q in(inputs,exp,out/'manifest.json',out/manifest['module_file'])}
    rows=[json.loads(line)for line in output.read_text().splitlines()];errors=[];known=unknown=nonzero_unknown=0
    if [r['id']for r in rows]!=list(range(len(cases))):errors.append(dict(reason='Incomplete actual result sequence',rows=len(rows),cases=len(cases)))
    for e,a in zip(expected,rows):
        for key in('parsed','transformed_hex','navigation_hex','nav_header_words'):
            if a[key]!=e[key]:errors.append(dict(id=e['id'],label=e['label'],field=key,expected=e[key],actual=a[key]))
        if len(a['candidate_stages'])!=len(e['candidate_stages']):errors.append(dict(id=e['id'],field='candidate stage count'));continue
        for j,(es,actual)in enumerate(zip(e['candidate_stages'],a['candidate_stages'])):
            for key in('capacity','length'):
                if es[key]!=actual[key]:errors.append(dict(id=e['id'],stage=j,field=key,expected=es[key],actual=actual[key]))
            for slot,row in enumerate(es['storage']):
                words=actual['storage_words'][2*slot:2*slot+2]
                if row is None:unknown+=2;nonzero_unknown+=sum(w!=0 for w in words)
                else:
                    known+=2
                    if list(row)!=words:errors.append(dict(id=e['id'],stage=j,field='candidate full backing',slot=slot,expected=row,actual=words))
    mismatch=out/'mismatches.json';mismatch.write_text(json.dumps(errors,indent=2)+'\n');runtime=out/'world-raster135-runtime.json'
    result=dict(version='0.135.1',build='0898d5e3',phase=args.phase,status='passed'if code==0 and not errors else'failed_preserved',
      cases=len(cases),completed_cases=len(rows),mismatch_fields=len(errors),source_before=before,source_after=after,original_sha256=SOURCE_SHA,
      expected_before_original=True,input_only_id_and_input=True,source_snapshots=True,frozen_artifacts=frozen,
      artifacts={q.name:sha(q)for q in(inputs,exp,output,stderr,mismatch,runtime)if q.exists()},
      runtime=json.loads(runtime.read_text())if runtime.exists()else None,process=dict(pid=child.pid,pgid=child.pid,exit_code=code,command=cmd,seconds=time.monotonic()-began,deadline_seconds=60),
      actualM2_cases=sum(c['input']['asset']is not None for c in cases),actual_asset_inventory_sha256=sha(INVENTORY),
      strict_candidate_backing_words=known,allocator_unknown_candidate_words=unknown,nonzero_unknown_candidate_words=nonzero_unknown,
      limits=['Only canonicalvalidM2 collision arrays;fullM2 animations/invalidfile recovery andWMO decoder unmodeled.',
       '12375 candidate/18572 transform/9328 nav in declaredfiniteboundedmesh domain;complete6730 candidatesort/merge andgroundproducer notindependently restored.',
       'Geometry/ground supplied explicitly;no originalworld/VFS/Once/cache orsnapshot written. Node32MiB878deny separate frombrowser world256MiB.'])
    (out/'world-raster135-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),status=result['status'],cases=len(cases),completed=len(rows),differences=len(errors),exit_code=code)))
    if result['status']!='passed':raise SystemExit(1)

if __name__=='__main__':main()
