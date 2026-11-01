#!/usr/bin/env python3
"""Expected-first actual410 WMO parser/collision differential, private2exports."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,hashlib,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from trace_wmo_geometry135 import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha

FILES=('scripts/check_wmo_geometry135.py','scripts/run_wmo_geometry135_oracle.mjs','scripts/trace_wmo_geometry135.py',
 'scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py',
 'reconstruction/resource_spec/__init__.py','reconstruction/resource_spec/wmo_geometry135.py')
IMPORTED={n:sha(ROOT/n)for n in FILES}
INVENTORY=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
INVENTORY_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
INDEX=ROOT/'evidence/resource-index-base-20261101T032320.856364Z/index.sqlite'
INDEX_SHA='a3f219f6e76e1d87e50b0790b757f999091e2b479d3b1d40ac2c101aa8680cf4'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def capacity(initial,length):
    value=initial
    while value<length:value=max(4,value*2)
    return value


def hex_vertices(vertices):return b''.join(struct.pack('<3I',*v)for v in vertices).hex()
def hex_indices(indices,stride=4):return struct.pack('<'+('I'if stride==4 else'H')*len(indices),*indices).hex()


def corpus(full):
    sys.path.insert(0,str(ROOT/'reconstruction'))
    from resource_spec.wmo_geometry135 import (parse_wmo_collision,WmoRoot135,WmoGroup135,WmoCollisionMesh135,
        append_group_collision,root_group_paths)
    raw_inventory=json.loads(INVENTORY.read_text());assert raw_inventory['index_sha256']==INDEX_SHA
    assets={r['chain']:r for r in raw_inventory['requests']if r['status']==200 and r['chain'].endswith('.wmo')}
    assert len(assets)==410
    parsed={};inputs={};roots={};groups=[];projections={}
    for chain,row in assets.items():
        p=Path(row['file']);data=p.read_bytes()
        assert len(data)==row['bytes']and hashlib.sha256(data).hexdigest()==row['sha256']==row['prior_index_row']['reference_sha256']
        value=parse_wmo_collision(data);parsed[chain]=value
        inputs[chain]=dict(path=str(p),bytes=len(data),sha256=row['sha256'],chain=chain)
        if isinstance(value,WmoRoot135):
            roots[chain]=root_group_paths(chain,value);projections[chain]=dict(kind='root',group_count=value.group_count)
        else:
            groups.append(chain);projections[chain]=dict(kind='group',vertices_hex=hex_vertices(value.vertices_bits),
                indices_u16_hex=hex_indices(value.indices_u16,2),attributes_hex=bytes(x for pair in value.triangle_attributes for x in pair).hex(),
                group_flags=value.group_flags,liquid_type=value.liquid_type)
    assert len(roots)==23 and len(groups)==387
    assert sum(map(len,roots.values()))==387 and set(x for xs in roots.values()for x in xs)==set(groups)
    cases=[];expected=[]
    def add(label,names,operations,initial=None):
        ident=len(cases);initial=initial or WmoCollisionMesh135();mesh=initial;vc,ic=len(mesh.vertices),len(mesh.indices);stages=[]
        for asset_index,exclude,required in operations:
            mesh=append_group_collision(parsed[names[asset_index]],mesh,exclude_flags=exclude,required_flags=required)
            vc,ic=capacity(vc,len(mesh.vertices)),capacity(ic,len(mesh.indices))
            stages.append(dict(vertex_capacity=vc,index_capacity=ic,vertex_count=len(mesh.vertices),index_count=len(mesh.indices),
                vertices_hex=hex_vertices(mesh.vertices),indices_u32_hex=hex_indices(mesh.indices)))
        cases.append(dict(id=ident,input=dict(assets=[inputs[n]for n in names],
            append_operations=[dict(asset_index=a,exclude_flags=e,required_flags=r)for a,e,r in operations],
            initial_mesh=dict(vertices_bits=list(initial.vertices),indices=list(initial.indices)))))
        expected.append(dict(id=ident,label=label,projections=[projections[n]for n in names],append_stages=stages))
    mixed='world\\wmo\\azeroth\\buildings\\stormwind\\stormwind_114.wmo';assert mixed in groups
    base=list(assets)if full else[next(iter(roots)),groups[0],mixed]
    for name in base:add('actual-file:'+name,[name],[]if isinstance(parsed[name],WmoRoot135)else[(0,4,0)])
    masks=[(0,0),(1,0),(4,0),(255,0),(0,1),(4,1),(0,32),(4,32),(0,64),(4,64),(4,256),(256,0)]if full else[(4,0),(255,0),(0,32)]
    for exclude,required in masks:add(f'controlled-flags:{exclude}:{required}',[mixed],[(0,exclude,required)])
    if full:
        add('same-group-append-reset-map',[mixed],[(0,4,0),(0,4,0)])
        add('two-distinct-group-append-order',[groups[0],mixed],[(0,4,0),(1,4,0)])
    # A full u32 destination index above65535 must survive4464's u16 source key.
    prefix=WmoCollisionMesh135(((0,0x80000000,0x3f800000),)*65537,(65536,0,65536))
    add('u32-destination-index-not-u16',[mixed],[(0,4,0)],prefix)
    provenance=dict(inventory_path=str(INVENTORY.relative_to(ROOT)),inventory_sha256=INVENTORY_SHA,
        old_stormlib_index_path=str(INDEX.relative_to(ROOT)),old_stormlib_index_sha256=INDEX_SHA,
        files=[assets[n]for n in base],all410_files_manifest=[assets[n]for n in assets],
        root_group_requests=roots,roots=23,groups=387,all_groups_requested=True,
        root_request_order_is_local_planning_not_original9513=True,
        latest135_all_assets_equivalence=raw_inventory['latest135_asset_equivalence'])
    return cases,expected,provenance


def gone(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def compare(cases,expected,actual):
    errors=[];strict=unknown=nonzero_unknown=0
    if len(actual)!=len(cases):errors.append(dict(field='completed case count',expected=len(cases),actual=len(actual)))
    for c,e,a in zip(cases,expected,actual):
        if c['id']!=a['id']:errors.append(dict(id=c['id'],field='case id'));continue
        if len(a['assets'])!=len(e['projections']):errors.append(dict(id=c['id'],field='parser count'));continue
        for j,(p,r)in enumerate(zip(e['projections'],a['assets'])):
            if p!=r['projection']:errors.append(dict(id=c['id'],asset=j,field='parser projection',expected=p,actual=r['projection']))
            if len(bytes.fromhex(r['raw_output160_hex']))!=160:errors.append(dict(id=c['id'],field='raw parser160 capture'))
            if r['raw_cursor_before_hex']!=r['raw_cursor_after_hex']:errors.append(dict(id=c['id'],field='parser cursor'))
            if p['kind']=='root':strict+=4;continue
            strict+=8
            for name,key,stride in [('vertices','vertices_hex',12),('indices_u16','indices_u16_hex',2),('attributes','attributes_hex',2)]:
                v=r['vectors'][name];length=len(bytes.fromhex(p[key]))//stride
                if v['length']!=length or v['capacity']!=capacity(0,length):errors.append(dict(id=c['id'],asset=j,field=name+' capacity/length',expected=[capacity(0,length),length],actual=[v['capacity'],v['length']]))
                if v['active_hex']!=p[key]or v['backing_hex'][:len(p[key])]!=p[key]:errors.append(dict(id=c['id'],asset=j,field=name+' strict active backing'))
                tail=bytes.fromhex(v['backing_hex'][len(p[key]):]);strict+=length*stride;unknown+=len(tail);nonzero_unknown+=sum(x!=0 for x in tail)
        if len(a['append_stages'])!=len(e['append_stages']):errors.append(dict(id=c['id'],field='append stage count'));continue
        for j,(p,r)in enumerate(zip(e['append_stages'],a['append_stages'])):
            for name,key,stride in [('vertices','vertices_hex',12),('indices_u32','indices_u32_hex',4)]:
                v=r[name];length=p['vertex_count'if name=='vertices'else'index_count'];cap=p['vertex_capacity'if name=='vertices'else'index_capacity']
                if v['length']!=length or v['capacity']!=cap:errors.append(dict(id=c['id'],stage=j,field=name+' capacity/length',expected=[cap,length],actual=[v['capacity'],v['length']]))
                if v['active_hex']!=p[key]or v['backing_hex'][:len(p[key])]!=p[key]:errors.append(dict(id=c['id'],stage=j,field=name+' exact append order/bytes'))
                tail=bytes.fromhex(v['backing_hex'][len(p[key]):]);strict+=length*stride;unknown+=len(tail);nonzero_unknown+=sum(x!=0 for x in tail)
        if not a['raw_inputs_unchanged']:errors.append(dict(id=c['id'],field='input mutated'))
        if a['hash_state_before_hex'][-2:]!='00'or a['hash_state_after_hex'][-2:]!='01':errors.append(dict(id=c['id'],field='original hash Once initialization',before=a['hash_state_before_hex'],after=a['hash_state_after_hex']))
    return errors,dict(strict_geometry_bytes=strict,allocator_unknown_tail_bytes=unknown,nonzero_unknown_tail_bytes=nonzero_unknown)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORTED and sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    assert sha(INVENTORY)==INVENTORY_SHA and sha(INDEX)==INDEX_SHA
    cases,expected,provenance=corpus(args.phase=='full');assert before=={n:sha(ROOT/n)for n in FILES}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('wmo-geometry0135-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,h in before.items():q=out/'source-snapshot'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    inp=out/'inputs.json';inp.write_text(json.dumps(cases,separators=(',',':'))+'\n')
    exp=out/'expected.json';exp.write_text(json.dumps(expected,separators=(',',':'))+'\n')
    prov=out/'asset-provenance.json';prov.write_text(json.dumps(provenance,indent=2)+'\n')
    frozen={p.name:sha(p)for p in(inp,exp,prov,out/'manifest.json',out/manifest['module_file'])}
    output,stderr=out/'results.jsonl',out/'stderr.log'
    cmd=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_wmo_geometry135_oracle.mjs'),str(out),str(inp)]
    start=time.monotonic()
    with output.open('wb')as so,stderr.open('wb')as se:
        child=subprocess.Popen(cmd,stdout=so,stderr=se,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=-9
    assert gone(child.pid)and gone(child.pid,True)
    after={n:sha(ROOT/n)for n in FILES};assert before==after
    assert frozen=={p.name:sha(p)for p in(inp,exp,prov,out/'manifest.json',out/manifest['module_file'])}
    assert sha(SOURCE)==SOURCE_SHA and sha(INVENTORY)==INVENTORY_SHA
    actual=[json.loads(line)for line in output.read_text().splitlines()];errors,counts=compare(cases,expected,actual)
    mismatch=out/'mismatches.json';mismatch.write_text(json.dumps(errors,indent=2)+'\n')
    runtime=out/'wmo-geometry135-runtime.json';rt=json.loads(runtime.read_text())if runtime.exists()else None
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,status='passed'if code==0 and not errors else'failed_preserved',
        cases=len(cases),completed_cases=len(actual),differences=len(errors),source_before=before,source_after=after,source_count=len(before),
        original_sha256=SOURCE_SHA,expected_before_original=True,input_only=True,frozen_artifacts=frozen,
        artifacts={p.name:sha(p)for p in(inp,exp,prov,output,stderr,mismatch,runtime)if p.exists()},runtime=rt,
        actual_unique_files=len(provenance['files']),actual_roots=sum(x['projections'][0]['kind']=='root'for x in expected if x['label'].startswith('actual-file:')),
        actual_groups=sum(x['projections'][0]['kind']=='group'for x in expected if x['label'].startswith('actual-file:')),
        process=dict(pid=child.pid,pgid=child.pid,exit_code=code,pid_confirmed_missing=True,process_group_confirmed_missing=True,command=cmd,seconds=time.monotonic()-start,deadline_seconds=60),
        comparison=counts,
        limitations=['Canonical version17 realWMO collision projections,notcomplete160B WMO record/material/BSP/doodad/renderer/error recovery.',
            '1510 realroot groupcount andgroup3geometry arrays/flags;4464 realcomplete parser/hash/dedup/filtercallee retained.',
            'Activegeometry andknownprefix bytes strict;unusedallocatorbacking captured raw andcountedunknown,notzeroassumed.',
            'Pointers andunmodeled160B metadata savedraw,notindependentlypredicted;root23pathplanning isnot9513/VFS differential.',
            'Freshoriginalhashinitialization,all878denied,32MiB;no originalworld/cache/Once/snapshot fixture.',
            'OldWindowsMPQ bytes have exactactualrequest provenance;latest135fullasset equivalence remainsunknown.',
            'No fullworld/6730/1089/main-slice/fullgame acceptance.'])
    target=out/'wmo-geometry135-comparison.json';target.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),receipt_sha256=sha(target),status=receipt['status'],cases=len(cases),completed=len(actual),differences=len(errors),exit_code=code)))
    if receipt['status']!='passed':raise SystemExit(1)


if __name__=='__main__':main()
