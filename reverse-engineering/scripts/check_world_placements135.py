#!/usr/bin/env python3
"""Expected-first canonical ADT placement projection, complete original1446."""
from pathlib import Path
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from source_closure135 import core_sources
from trace_world_placements135 import trace

FILES=('scripts/check_world_placements135.py','scripts/run_world_placements135_oracle.mjs','scripts/trace_world_placements135.py',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py','scripts/full135_host.mjs','scripts/source_closure135.py',
 'reconstruction/resource_spec/__init__.py','reconstruction/resource_spec/world_placements135.py',
 'reconstruction/resource_spec/entry_resources135.py','reconstruction/resource_spec/dbc.py')+core_sources(ROOT,'binary32.py')
INVENTORY=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
INVENTORY_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def sha(path):
    with Path(path).open('rb')as h:return hashlib.file_digest(h,'sha256').hexdigest()

IMPORTED={p:sha(ROOT/p)for p in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from resource_spec.world_placements135 import parse_adt_placements
from resource_spec.entry_resources135 import chunks

def capacity(length):
    if length==0:return 0
    value=4
    while value<length:value*=2
    return value

def project(data):
    value=parse_adt_placements(data)
    return {kind:dict(length=len(getattr(value,kind)),capacity=capacity(len(getattr(value,kind))),
        records=[dict(name_utf8_hex=r.name_utf8.hex(),string_capacity=len(r.name_utf8),scalar_words=r.scalar_words)for r in getattr(value,kind)])
        for kind in('m2','wmo')}

def modified(data,which):
    result=bytearray(data);by={c.tag:c for c in chunks(data)}
    a=by[b'FDDM'].offset+8;b=by[b'FDOM'].offset+8
    if which==0:
        for i,s in enumerate((0,1,1023,1024,2048,65535)):
            struct.pack_into('<H',result,a+i*36+32,s)
            struct.pack_into('<I',result,a+i*36+4,(0,1,0x7fffffff,0x80000000,0xffffffff,0)[i])
        struct.pack_into('<3H',result,b+56,0xabcd,0x1234,0x5678)
    elif which==1:
        for i,words in enumerate(((0,0x80000000,0),(0x46855555,0xc2c80000,0x46855555),(0x46855556,0x3f800000,0x46855554))):
            struct.pack_into('<3I',result,a+i*36+8,*words)
            struct.pack_into('<3I',result,a+i*36+20,0,0x80000000,0x43b40000)
            struct.pack_into('<3I',result,b+i*64+8,*words)
            struct.pack_into('<3I',result,b+i*64+20,0xc3b40000,0x43340000,0x80000000)
    elif which==2:
        for i in(0,1,3):struct.pack_into('<I',result,a+i*36,0xffffffff)
        struct.pack_into('<I',result,b,0xffffffff)
    elif which==3:
        # Repoint every name offset to the first valid string while preserving
        # the actual vector size, duplicate UID order, and complete ADT bytes.
        for tag in(b'DIMM',b'DIWM'):
            c=by[tag]
            for i in range(len(c.payload)//4):struct.pack_into('<I',result,c.offset+8+4*i,0)
    return bytes(result)

def gone(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORTED and sha(INVENTORY)==INVENTORY_SHA and sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    inventory=json.loads(INVENTORY.read_text());assets=[r for r in inventory['requests']if r['status']==200 and r['chain'].endswith('.adt')]
    assert len(assets)==9
    out,manifest=build(['adt_parse']);snap=out/'source-snapshot';snap.mkdir()
    for n,h in before.items():q=snap/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    trace_dir=out/'static';trace_dir.mkdir();trace(trace_dir)
    cases=[];expected=[];asset_manifest=[]
    for row in assets if args.phase=='full'else assets[:1]:
        data=Path(row['file']).read_bytes();assert sha(row['file'])==row['sha256']and len(data)==row['bytes']
        ident=len(cases);cases.append(dict(id=ident,input=dict(asset_path=row['file'],asset_bytes=len(data),asset_sha256=row['sha256'])))
        expected.append(dict(id=ident,label='actual:'+row['chain'],vectors=project(data)))
        asset_manifest.append(row)
    if args.phase=='full':
        folder=out/'controlled-assets';folder.mkdir();base=Path(assets[0]['file']).read_bytes()
        for which in range(4):
            data=modified(base,which);target=folder/f'{which}.adt';target.write_bytes(data);ident=len(cases)
            cases.append(dict(id=ident,input=dict(asset_path=str(target),asset_bytes=len(data),asset_sha256=sha(target))))
            expected.append(dict(id=ident,label='controlled:'+str(which),vectors=project(data)))
    inp=out/'placements135-inputs.json';inp.write_text(json.dumps(cases,separators=(',',':'))+'\n')
    exp=out/'placements135-expected.json';exp.write_text(json.dumps(expected,separators=(',',':'))+'\n')
    provenance=out/'placements135-asset-provenance.json';provenance.write_text(json.dumps(dict(inventory=str(INVENTORY.relative_to(ROOT)),inventory_sha256=INVENTORY_SHA,assets=asset_manifest),indent=2)+'\n')
    frozen_paths=[inp,exp,provenance,out/'manifest.json',out/manifest['module_file'],*out.glob('controlled-assets/*')]
    frozen={str(p.relative_to(out)):sha(p)for p in frozen_paths}
    cmd=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_world_placements135_oracle.mjs'),str(out),str(inp)]
    output=out/'placements135-results.jsonl';stderr=out/'placements135-stderr.log';start=time.monotonic()
    with output.open('wb')as stream,stderr.open('wb')as err:
        child=subprocess.Popen(cmd,stdout=stream,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    assert gone(child.pid)and gone(child.pid,True)
    after={n:sha(ROOT/n)for n in FILES};assert before==after and frozen=={str(p.relative_to(out)):sha(p)for p in frozen_paths}
    results=[json.loads(line)for line in output.read_text().splitlines()];errors=[];known=unknown=nonzero_unknown=0
    if len(results)!=len(cases):errors.append(dict(field='case count',expected=len(cases),actual=len(results)))
    for c,e,r in zip(cases,expected,results):
        if c['id']!=r['id']:errors.append(dict(field='id'));continue
        for kind in('m2','wmo'):
            wanted=json.loads(json.dumps(e['vectors'][kind]));actual={k:r['vectors'][kind][k]for k in('length','capacity','records')}
            if wanted!=actual:
                if len(wanted['records'])!=len(actual['records']):errors.append(dict(id=c['id'],kind=kind,field='record count',expected=len(wanted['records']),actual=len(actual['records'])))
                for i,(x,y)in enumerate(zip(wanted['records'],actual['records'])):
                    if x!=y:errors.append(dict(id=c['id'],kind=kind,index=i,expected=x,actual=y))
                if(wanted['length'],wanted['capacity'])!=(actual['length'],actual['capacity']):errors.append(dict(id=c['id'],kind=kind,field='vector descriptor',expected=[wanted['length'],wanted['capacity']],actual=[actual['length'],actual['capacity']]))
            raw=(out/f"placements135-{c['id']}-{kind}-records44.bin").read_bytes();tail=raw[actual['length']*44:]
            known+=sum(40+len(bytes.fromhex(x['name_utf8_hex']))for x in wanted['records']);unknown+=len(tail);nonzero_unknown+=sum(x!=0 for x in tail)
    mismatches=out/'placements135-mismatches.json';mismatches.write_text(json.dumps(errors,indent=2)+'\n')
    runtime=out/'placements135-runtime.json'
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,status='passed'if code==0 and not errors else'failed_preserved',
        cases=len(cases),completed_cases=len(results),original_calls=len(results),differences=len(errors),original_sha256=SOURCE_SHA,
        source_sha256_before=before,source_sha256_after=after,source_count=len(before),expected_before_original=True,input_contains_expected=False,
        input_shape='id/input(asset_path,asset_bytes,asset_sha256)',frozen_artifacts=frozen,process=dict(command=cmd,pid=child.pid,exit_code=code,seconds=time.monotonic()-start,
        deadline_seconds=60,pid_and_pgid_missing=True),runtime=json.loads(runtime.read_text())if runtime.exists()else None,
        strict_scalar_string_bytes=known,unwritten_tail_bytes=unknown,nonzero_unwritten_tail_bytes=nonzero_unknown,
        artifacts={p.name:sha(p)for p in(output,stderr,mismatches,runtime)if p.exists()},
        complete_world_producer=False,full6730_selection_new_cases=0,installed_apps_or_saves_modified=False)
    path=out/'world-placements135-comparison.json';path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),status=receipt['status'],cases=len(cases),differences=len(errors),receipt_sha256=sha(path))))
    if code!=0 or errors:sys.exit(1)

if __name__=='__main__':main()
