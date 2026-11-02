#!/usr/bin/env python3
"""Compare frozen independent139 world with the corrected v2 original capture.

This is a historical original observation comparison, not a new original call.
The independent producer never receives these bytes. Full chunk/render/cache
ownership is not predicted by the canonical query-field comparison.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,struct,sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from resource_spec.terrain135 import TerrainChunk135,TerrainTile135,HeightRaster135
from resource_spec.world_query135 import WorldQueries135,NavGrid135

REFERENCE=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z'
REFERENCE_SHA='36372f365f9831045a0dab80f1948f445ceda653992a145a03bc051255813eb8'
SNAPSHOT_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
WORLD_RC=20544696
REVIEW=ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json'
REVIEW_SHA='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
TRACE=ROOT/'evidence/world139-static-20261102T032207.619660Z/trace.json'
TRACE_SHA='7a66273b70a4a5c215092a0981a1652d67786576087510933f05adc810b11d16'


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def load_world139(directory):
    directory=Path(directory).resolve();receipt=json.loads((directory/'receipt.json').read_text())
    assert receipt['kind']=='independent139_raw_assets_to_canonical_world'and receipt['actual_build']=='f79c5e2b4'
    assert receipt['original_program_executed']is False and receipt['original_memory_read']is False and receipt['preparsed_world_input_read']is False
    assert receipt['source_sha256_before']==receipt['source_sha256_after']
    payloads={}
    for name,row in receipt['world_artifacts'].items():
        p=(directory/row['file']).resolve();assert p.is_relative_to(directory)and sha(p)==row['sha256']and p.stat().st_size==row['bytes'];payloads[name]=p.read_bytes()
    raw=payloads['terrain'];cursor=0
    def take(fmt):
        nonlocal cursor
        v=struct.unpack_from(fmt,raw,cursor);cursor+=struct.calcsize(fmt);return v
    count,=take('<I');assert 0<count<=512;tiles=[]
    for _ in range(count):
        *bounds,n=take('<5I');assert 0<n<=1024;chunks=[]
        for _ in range(n):
            holes,k=take('<HI');assert k==145;chunks.append(TerrainChunk135(tuple(take('<3I')for _ in range(k)),holes))
        tiles.append(TerrainTile135(tuple(chunks),tuple(bounds)))
    assert cursor==len(raw)
    n=receipt['world_artifacts']['navigation'];s=receipt['world_artifacts']['secondary']
    assert len(payloads['navigation'])==n['width']**2 and len(payloads['secondary'])==s['width']**2*4
    secondary=HeightRaster135(tuple(x[0]for x in struct.iter_unpack('<I',payloads['secondary'])),tuple(s['origin_xy_bits']),s['width'])
    world=WorldQueries135(tuple(tiles),None,secondary,NavGrid135(payloads['navigation'],tuple(n['origin_xy_bits']),n['width']),receipt['query_scalars']['fallback_height_bits'],None)
    return world,receipt,payloads


def compare_world139(directory,out):
    directory=Path(directory).resolve();out=Path(out).resolve()
    assert out.is_relative_to(Path('/Volumes/RuiRui4TB'));out.mkdir(parents=True,exist_ok=False)
    assert sha(REFERENCE/'receipt.json')==REFERENCE_SHA and sha(REVIEW)==REVIEW_SHA and sha(TRACE)==TRACE_SHA
    review=json.loads(REVIEW.read_text())
    # Exact frozen reviewer verdict is part of admission, not an old or
    # provisional byte-only audit. The corresponding artifact is immutable.
    assert 'pass'in str(review['status']).lower()and'not_accepted'not in str(review['status']).lower()
    world,model,payloads=load_world139(directory);frozen=sha(directory/'receipt.json')
    snapshot=REFERENCE/'after_real_world6786.memory';assert sha(snapshot)==SNAPSHOT_SHA
    memory=snapshot.read_bytes();assert len(memory)==111804416
    ranges=[]
    def read(p,n,label):
        assert type(p)is int and type(n)is int and 0<=p<=p+n<=len(memory)
        value=memory[p:p+n];ranges.append(dict(label=label,offset=p,bytes=n,sha256=hashlib.sha256(value).hexdigest()));return value
    words=struct.unpack('<31I',read(WORLD_RC,124,'worldRc124'))
    tilecap,tileptr,tilecount,bcap,bptr,bcount=words[2:8]
    assert 0<tilecount<=tilecap<=512 and tilecount==bcount<=bcap
    descriptors=read(tileptr,tilecount*36,'tiles36');bounds=read(bptr,bcount*16,'bounds16')
    terrain=bytearray(struct.pack('<I',tilecount))
    for i in range(tilecount):
        cap,pointer,count=struct.unpack_from('<3I',descriptors,i*36);assert 0<count<=cap<=1024
        terrain.extend(bounds[i*16:(i+1)*16]);terrain.extend(struct.pack('<I',count))
        chunks=read(pointer,count*264,f'tile{i}.chunks264')
        for j in range(count):
            vc,vp,vn=struct.unpack_from('<3I',chunks,j*264);assert vn==145 and vn<=vc<=65536
            terrain.extend(struct.pack('<HI',struct.unpack_from('<H',chunks,j*264+260)[0],vn));terrain.extend(read(vp,vn*12,f'tile{i}.chunk{j}.vertices'))
    actual={'terrain':bytes(terrain)};checks={};errors=[]
    assert words[14]==0xffffffff and words[23]!=0xffffffff and words[30]&255==0
    assert words[29]==model['query_scalars']['fallback_height_bits']
    for name,ci,pi,ni,oi,wi,stride in [('navigation',8,9,10,11,13,1),('secondary',23,24,25,26,28,4)]:
        assert 0<words[ni]<=words[ci]and words[ni]==words[wi]**2 and words[wi]<=4096
        actual[name]=read(words[pi],words[ni]*stride,name)
        want=model['world_artifacts'][name]
        assert words[wi]==want['width']and list(words[oi:oi+2])==want['origin_xy_bits']
    for name,data in actual.items():
        wanted=payloads[name];different=sum(x!=y for x,y in zip(data,wanted))+abs(len(data)-len(wanted))
        checks[name]=dict(independent_bytes=len(wanted),original_bytes=len(data),different_bytes=different,independent_sha256=hashlib.sha256(wanted).hexdigest(),original_sha256=hashlib.sha256(data).hexdigest())
        (out/('original-'+name+'.bin')).write_bytes(data)
        if different:errors.append(name)
    (out/'source-ranges.json').write_text(json.dumps(ranges,indent=2)+'\n')
    assert sha(directory/'receipt.json')==frozen and sha(snapshot)==SNAPSHOT_SHA
    result=dict(version='0.139.0',build='f79c5e2b4',kind='independent_raw_world_compared_with_healthy_historical_original_query_fields',status='matched'if not errors else'failed_preserved',
        model_directory=str(directory),model_receipt_sha256=frozen,reference_receipt_sha256=REFERENCE_SHA,reference_review_sha256=REVIEW_SHA,static_contract_sha256=TRACE_SHA,snapshot_sha256=SNAPSHOT_SHA,
        world_rc=WORLD_RC,checks=checks,differences=errors,source_range_count=len(ranges),source_ranges_file='source-ranges.json',source_ranges_sha256=sha(out/'source-ranges.json'),
        original_executions=0,new_original_cases=0,old_invalid_context_used=False,
        limitations=['One corrected139Elwynn context observation;not a new original execution.','Canonical consumed query fields only;not complete264Bchunks/render/physicalRc/cache ownership.','Fresh139query calls are a separate next validation layer.'])
    (out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n')
    if errors:raise AssertionError(errors)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    out=a.output or ROOT/'evidence'/datetime.now(timezone.utc).strftime('asset-world139-observation-check-%Y%m%dT%H%M%S.%fZ')
    result=compare_world139(a.model,out);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),differences=result['differences'],new_original_cases=0)),flush=True)


if __name__=='__main__':main()
