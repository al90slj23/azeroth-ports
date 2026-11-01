#!/usr/bin/env python3
"""Read-only independent review; never instantiate original WASM or author model.

Matrix coefficients are interpreted from the original straight-line WAT prefix.
Candidate and navigation formulas are independently recomputed with the shared,
previously validated binary32/trig primitives. This adds no original cases.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import argparse,hashlib,json,math,os,re,sqlite3,struct,sys
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as F
from core_spec.binary32_sqrt import sqrt_bits
from core_spec.ai_trig135 import sin_bits,cos_bits

DEFAULT=ROOT/'evidence/world-raster0135-20261101T100905.801350Z'
FINAL_SHA='29cebe9b405f71a86ad0e673a126fdcfb1b6e8e2f809adcfe9273b4086ad9bf9'
INDEX=ROOT/'evidence/resource-index-base-20261101T032320.856364Z/index.sqlite'
INDEX_SHA='a3f219f6e76e1d87e50b0790b757f999091e2b479d3b1d40ac2c101aa8680cf4'
ASSETS=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
ASSETS_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
ARCHIVE_DIR=ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
PROFILE_INDEX_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
ROLES={14947:('7f7f7f','','aa1609794c1d3e3275cd9ae4f2b2dc0457e9c09a7379d6770e1bc53d6b4713ad'),
 18572:('7f7f7f7f7f7d','','a82a1c8b0e230958331c9c8ef152086c33ab373a7edda7dcc2b61cce7c340983'),
 12375:('7f7f7f7f7f7d','','ad87b93e4482062ad563e9672ca279afc4cbb3000bb3be271f25f3dea815b3e5'),
 9328:('7f7f7f7f7d7f7f','','a8e943e5af2103c6fd9c7d3d7e6e1d05dceb844eee84733fdcf540822b2d6179')}


def matrix_from_wat(text,rotation,scale):
    """Evaluate the branch-free prefix to its nine matrix stores, not author code."""
    stack=[];locals_=[0]*64;locals_[:6]=[0x1000,0x2000,0,0x3000,0x4000,scale]
    memory={0x4000+4*j:x for j,x in enumerate(rotation)};global0=0x8000;stores={};executed=0
    for line in text.splitlines()[2:]:
        line=re.sub(r'\(;.*?;\)','',line).strip()
        if not line:continue
        parts=line.split();op=parts[0];arg=parts[1]if len(parts)>1 else None;executed+=1
        if op=='global.get':assert arg=='0';stack.append(global0)
        elif op=='global.set':assert arg=='0';global0=stack.pop()
        elif op=='local.get':stack.append(locals_[int(arg)])
        elif op=='local.set':locals_[int(arg)]=stack.pop()
        elif op=='local.tee':locals_[int(arg)]=stack[-1]
        elif op=='i32.const':stack.append(int(arg))
        elif op in('i32.sub','i32.add'):
            b,a=stack.pop(),stack.pop();stack.append((a-b if op.endswith('sub')else a+b)&0xffffffff)
        elif op=='f32.const':stack.append(F.from_float(float.fromhex(arg)))
        elif op in('f32.add','f32.sub','f32.mul'):
            b,a=stack.pop(),stack.pop();stack.append({'f32.add':F.add,'f32.sub':F.sub,'f32.mul':F.mul}[op](a,b))
        elif op=='f32.load':
            offset=next((int(t.split('=')[1])for t in parts[1:]if t.startswith('offset=')),0);stack.append(memory[stack.pop()+offset])
        elif op=='f32.store':
            value,address=stack.pop(),stack.pop();offset=next((int(t.split('=')[1])for t in parts[1:]if t.startswith('offset=')),0)
            memory[address+offset]=value
            if offset in range(16,49,4):stores[offset]=value
            if len(stores)==9:break
        elif op=='call':
            assert int(arg)in(11428,11503);value=stack.pop();stack.append(sin_bits(value)if int(arg)==11428 else cos_bits(value))
        else:raise AssertionError(('Unexpected matrix-prefix opcode',line))
    assert len(stores)==9
    return tuple(tuple(stores[16+12*r+4*c]for c in range(3))for r in range(3)),executed


def transformed(vertices,position,rotation,scale,wat):
    matrix,instructions=matrix_from_wat(wat,rotation,scale);out=[]
    for vertex in vertices:
        axes=[]
        for row in matrix:
            products=[F.mul(x,y)for x,y in zip(row,vertex)]
            axes.append(F.mul(F.add(F.add(products[0],products[1]),products[2]),scale))
        out.append((F.add(position[0],axes[0]),F.add(position[1],axes[1]),F.add(axes[2],position[2])))
    return tuple(out),instructions


def triangle_metrics(a,b,c):
    e=tuple(F.sub(b[j],a[j])for j in range(3));g=tuple(F.sub(c[j],a[j])for j in range(3))
    normal=(F.sub(F.mul(e[1],g[2]),F.mul(e[2],g[1])),F.sub(F.mul(e[2],g[0]),F.mul(e[0],g[2])),F.sub(F.mul(e[0],g[1]),F.mul(e[1],g[0])))
    n2=F.add(F.mul(normal[2],normal[2]),F.add(F.mul(normal[0],normal[0]),F.mul(normal[1],normal[1])))
    return e,g,normal[2],sqrt_bits(n2)


def candidate_pairs(origin,width,a,b,c,ceiling):
    e,g,nz,norm=triangle_metrics(a,b,c);v=F.to_float
    if v(norm)<v(0x358637bd)or v(F.div(nz&0x7fffffff,norm))<v(0x3f333333)or min(v(a[2]),v(b[2]),v(c[2]))>v(ceiling):return[]
    bounds=[]
    for axis in(0,1):
        values=[q[axis]for q in(a,b,c)];lo=min(values,key=v);hi=max(values,key=v)
        lo=F.sub(F.add(F.sub(lo,origin[axis]),F.sub(lo,origin[axis])),0x3f000000)
        hi=F.sub(F.add(F.sub(hi,origin[axis]),F.sub(hi,origin[axis])),0x3f000000)
        bounds.append((max(0,math.ceil(v(lo))),min(width,max(0,math.floor(v(hi))+1))))
    pairs=[]
    for y in range(*bounds[1]):
        py=F.add(origin[1],F.mul(F.add(F.from_u32(y),0x3f000000),0x3f000000));dy=F.sub(py,a[1])
        for x in range(*bounds[0]):
            px=F.add(origin[0],F.mul(F.add(F.from_u32(x),0x3f000000),0x3f000000));dx=F.sub(px,a[0])
            u=F.div(F.sub(F.mul(g[1],dx),F.mul(g[0],dy)),nz)
            w=F.div(F.sub(F.mul(e[0],dy),F.mul(e[1],dx)),nz)
            if v(u)<v(0xb8d1b717)or v(w)<v(0xb8d1b717)or v(F.add(u,w))>v(0x3f800347):continue
            height=F.add(F.mul(g[2],w),F.add(a[2],F.mul(e[2],u)))
            if v(height)<=v(ceiling):pairs.append((x+width*y,height))
    return pairs


def navigation_bytes(inp,vertices,indices):
    storage=bytearray.fromhex(inp['nav_hex']);width=inp['nav_width'];origin=inp['origin_xy_bits'];ground=inp['ground_bits'];v=F.to_float;stats=Counter()
    upper=[F.add(origin[j],F.from_u32(width))for j in(0,1)]
    for start in range(0,len(indices)-2,3):
        a,b,c=[vertices[indices[start+j]]for j in range(3)]
        if any(min(v(q[axis])for q in(a,b,c))>v(upper[axis])or max(v(q[axis])for q in(a,b,c))<v(origin[axis])for axis in(0,1)):
            stats['aabb_excluded']+=1;continue
        e,g,nz,norm=triangle_metrics(a,b,c)
        if v(norm)<v(0x358637bd)or v(F.div(nz&0x7fffffff,norm))>v(0x3f333333):continue
        edges=(e,g,tuple(F.sub(c[j],b[j])for j in range(3)))
        edge_lengths=[sqrt_bits(F.add(F.add(F.mul(x[0],x[0]),F.mul(x[1],x[1])),F.mul(x[2],x[2])))for x in edges]
        uncapped=math.ceil(v(F.div(max(edge_lengths,key=v),0x3ecccccd)));steps=max(1,min(400,uncapped))
        stats['sampled_triangles']+=1;stats['cap400_triangles']+=uncapped>400
        if uncapped>400:stats['uncapped_step_ceiling']=max(stats['uncapped_step_ceiling'],uncapped)
        fractions=[F.div(F.from_u32(j),F.from_u32(steps))for j in range(steps+1)]
        for i,u in enumerate(fractions):
            base=[F.add(a[j],F.mul(e[j],u))for j in range(3)]
            for w in fractions[:steps-i+1]:
                px=F.sub(F.add(base[0],F.mul(g[0],w)),origin[0]);py=F.sub(F.add(base[1],F.mul(g[1],w)),origin[1]);stats['sample_pairs']+=1
                if v(px)<0 or v(py)<0:continue
                x,y=int(v(px)),int(v(py))
                if x>=width or y>=width:continue
                index=x+width*y
                if F.is_nan(ground[index]):continue
                z=F.add(base[2],F.mul(g[2],w))
                if v(z)>v(F.add(ground[index],0x3eb33333))and v(z)<v(F.add(ground[index],0x4019999a)):storage[index]=1
    return bytes(storage),dict(stats)


def mesh_from_input(inp,index,inventory,archive_cache):
    if inp['asset']is None:return tuple(tuple(x)for x in inp['vertices']),tuple(inp['indices']),None
    asset=inp['asset'];record=next(x for x in inventory['requests']if x.get('chain')==asset['chain']and x['status']==200)
    for key in('archive','sha256','bytes','prior_index_row'):assert asset[key]==record[key]
    payload=Path(asset['path']).read_bytes();assert len(payload)==asset['bytes']and hashlib.sha256(payload).hexdigest()==asset['sha256']
    row=index.execute('select *from files where archive=?and normalized_name=?',(asset['archive'],asset['chain'].upper())).fetchone();assert row is not None;row=dict(row)
    assert row==asset['prior_index_row']
    archive=index.execute('select *from archives where name=?',(asset['archive'],)).fetchone();archive=dict(archive)
    if archive['name']not in archive_cache:
        path=ARCHIVE_DIR/archive['name'];assert path.stat().st_size==archive['bytes']and sha(path)==archive['sha256'];archive_cache[archive['name']]=archive
    assert row['flags']==0x80000000 and row['stored_bytes']==row['decoded_bytes']==len(payload)
    with(ARCHIVE_DIR/asset['archive']).open('rb')as stream:stream.seek(row['data_offset']);stored=stream.read(row['stored_bytes'])
    assert stored==payload and row['decoded_sha256']==row['reference_sha256']==asset['sha256']
    assert payload[:8]==b'MD20\x00\x01\0\0';ni,pi,nv,pv=struct.unpack_from('<4I',payload,236)
    assert ni%3==0 and pi+ni*2<=len(payload)and pv+nv*12<=len(payload)
    vertices=tuple(struct.iter_unpack('<3I',payload[pv:pv+nv*12]));indices=struct.unpack_from('<'+'H'*ni,payload,pi)if ni else()
    assert all(i<len(vertices)for i in indices)
    parsed=dict(vertex_count=nv,index_count=ni,vertices_hex=payload[pv:pv+nv*12].hex(),indices=list(indices))
    return vertices,tuple(indices),parsed


def main():
    p=argparse.ArgumentParser();p.add_argument('--directory',type=Path,default=DEFAULT);args=p.parse_args();batch=args.directory.resolve()
    receipt_file=batch/'world-raster135-comparison.json';assert sha(receipt_file)==FINAL_SHA
    receipt=json.loads(receipt_file.read_text());assert receipt['status']=='passed'and receipt['source_before']==receipt['source_after']and receipt['cases']==114 and receipt['mismatch_fields']==0
    reviewer=Path(__file__);own_sha=sha(reviewer);shared={n:sha(ROOT/n)for n in core_sources(ROOT,'binary32.py','binary32_sqrt.py','ai_trig135.py')}
    for name,digest in receipt['source_before'].items():assert sha(ROOT/name)==digest==sha(batch/'source-snapshot'/name)
    for name,digest in(receipt['artifacts']|receipt['frozen_artifacts']).items():assert sha(batch/name)==digest
    assert sha(SOURCE)==SOURCE_SHA and sha(INDEX)==INDEX_SHA and sha(ASSETS)==ASSETS_SHA
    manifest=json.loads((batch/'manifest.json').read_text());original=SOURCE.read_bytes();changed=(batch/manifest['module_file']).read_bytes();types,imports,decl,bodies,_=parse_source(original)
    old=section_list(original);new=section_list(changed);assert len(old)==len(new)and 8 not in[x[0]for x in old]
    for x,y in zip(old,new):
        assert x[0]==y[0]
        if x[0]!=7:assert original[x[1]:x[3]]==changed[y[1]:y[3]]
    before_exports,_=export_entries(original,next(x for x in old if x[0]==7));after_exports,_=export_entries(changed,next(x for x in new if x[0]==7))
    assert after_exports==before_exports+[(x['name'],0,x['index'])for x in manifest['roles']]
    assert len(manifest['roles'])==4 and {x['index']for x in manifest['roles']}==set(ROLES)
    for role in manifest['roles']:
        i=role['index'];params,result,digest=ROLES[i];start,end=bodies[i]
        assert types[decl[i-len(imports)]]==(bytes.fromhex(params),bytes.fromhex(result))and hashlib.sha256(original[start:end]).hexdigest()==digest==role['body_sha256']
    assert sha(PROFILE/'index.sqlite')==PROFILE_INDEX_SHA
    profile=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);profile.row_factory=sqlite3.Row
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for row in manifest['functions']:
            current=dict(profile.execute('select *from functions where idx=?',(row['index'],)).fetchone())
            assert all(row[key]==value for key,value in current.items())
            stream.seek(current['wat_start']);wat=stream.read(current['wat_end']-current['wat_start'])
            assert wat==(batch/f'{row["index"]}.wat').read_bytes()and hashlib.sha256(wat).hexdigest()==row['wat_sha256']
            assert (current['body_start'],current['body_end'])==bodies[row['index']]
    inputs=json.loads((batch/'inputs.json').read_text());expected=json.loads((batch/'expected.json').read_text());actual=[json.loads(x)for x in(batch/'results.jsonl').read_text().splitlines()]
    assert[c['id']for c in inputs]==[c['id']for c in expected]==[c['id']for c in actual]==list(range(114))
    assert all(set(c)=={'id','input'}for c in inputs)
    runner=(batch/'source-snapshot/scripts/run_world_raster135_oracle.mjs').read_text();assert "fs.readFile(file,'utf8')" in runner and 'expected.json'not in runner
    index=sqlite3.connect(INDEX.resolve().as_uri()+'?mode=ro',uri=True);index.row_factory=sqlite3.Row;inventory=json.loads(ASSETS.read_text());archive_cache={};counts=Counter();nav_stats=[];m2_rows=[]
    matrix_wat=(batch/'18572.wat').read_text()
    for c,e,a in zip(inputs,expected,actual):
        inp=c['input'];vertices,indices,parsed=mesh_from_input(inp,index,inventory,archive_cache)
        assert parsed==a['parsed']==e['parsed']
        if parsed:
            counts['actual_m2']+=1;counts['nonempty_m2']+=bool(vertices);counts['real_m2_vertices']+=len(vertices);counts['real_m2_triangles']+=len(indices)//3
            m2_rows.append(dict(chain=inp['asset']['chain'],sha256=inp['asset']['sha256'],bytes=inp['asset']['bytes'],vertices=len(vertices),triangles=len(indices)//3))
        transformed_vertices,numeric_instructions=transformed(vertices,inp['position_bits'],inp['rotation_bits'],inp['scale_bits'],matrix_wat)
        mesh_hex=b''.join(struct.pack('<3I',*v)for v in transformed_vertices).hex();assert mesh_hex==a['transformed_hex']==e['transformed_hex']
        counts['strict_transform_bytes']+=len(mesh_hex)//2;counts['matrix_wat_instructions']+=numeric_instructions;counts['transforms']+=1
        assert len(a['candidate_stages'])==len(e['candidate_stages'])==len(inp['height_triangles'])
        store=list(zip(inp['initial_candidate_words'][::2],inp['initial_candidate_words'][1::2]));length=inp['initial_candidate_length']
        for tri,es,as_ in zip(inp['height_triangles'],e['candidate_stages'],a['candidate_stages']):
            triangle=[transformed_vertices[indices[j]]for j in tri];pairs=candidate_pairs(inp['origin_xy_bits'],inp['height_width'],*triangle,inp['ceiling_bits'])
            for pair in pairs:
                if length==len(store):store.extend([None]*(max(4,2*len(store))-len(store)))
                store[length]=pair;length+=1
            assert es==dict(capacity=len(store),length=length,storage=[list(row)if row is not None else None for row in store])
            assert(as_['capacity'],as_['length'],len(as_['storage_words']))==(len(store),length,len(store)*2)
            for j,row in enumerate(store):
                words=as_['storage_words'][2*j:2*j+2]
                if row is None:
                    assert j>=length;counts['allocator_unknown_candidate_words']+=2;counts['nonzero_unknown_candidate_words']+=sum(x!=0 for x in words)
                else:assert list(row)==words;counts['strict_candidate_backing_words']+=2
            counts['candidate_stages']+=1;counts['candidate_pairs_appended']+=len(pairs)
        nav,stats=navigation_bytes(inp,transformed_vertices,indices);assert nav.hex()==a['navigation_hex']==e['navigation_hex']
        expected_header=[len(bytes.fromhex(inp['nav_hex'])),inp['nav_active_length'],*inp['origin_xy_bits'],inp['nav_width']]
        assert a['nav_header_words']==e['nav_header_words']==expected_header
        assert nav[inp['nav_active_length']:]==bytes.fromhex(inp['nav_hex'])[inp['nav_active_length']:]
        counts['strict_navigation_bytes']+=len(nav);counts['navigation_tail_bytes']+=len(nav)-inp['nav_active_length'];counts['navigation_stages']+=1
        if e['label']=='400-step-cap':
            assert stats.get('cap400_triangles')==1 and stats['uncapped_step_ceiling']>400 and stats.get('sampled_triangles')==1
            changed_cells=[j for j,(x,y)in enumerate(zip(bytes.fromhex(inp['nav_hex']),nav))if x!=y];assert changed_cells==[1,5,6,10]
            stats['changed_cells']=changed_cells
        nav_stats.append(dict(case=c['id'],label=e['label'],**stats))
    assert counts['actual_m2']==31 and counts['nonempty_m2']==23 and counts['real_m2_vertices']==670 and counts['real_m2_triangles']==1113
    assert counts['strict_candidate_backing_words']==receipt['strict_candidate_backing_words']and counts['allocator_unknown_candidate_words']==receipt['allocator_unknown_candidate_words']and counts['nonzero_unknown_candidate_words']==receipt['nonzero_unknown_candidate_words']
    rt=receipt['runtime'];assert(rt['cases'],rt['calls'],rt['stages'],rt['fresh_instances'],rt['denied_imports'],rt['actual_host_calls'])==(114,1477,1332,114,878,0)
    assert rt['max_memory_bytes']<=33554432 and receipt['process']['exit_code']==0 and '--wasm-max-mem-pages=512'in receipt['process']['command']and receipt['process']['deadline_seconds']==60
    try:os.kill(receipt['process']['pid'],0)
    except ProcessLookupError:terminal=True
    else:terminal=False
    assert terminal
    prior=ROOT/'evidence/world-raster0135-20261101T100525.599907Z';oldinputs=json.loads((prior/'inputs.json').read_text());oldexpected=json.loads((prior/'expected.json').read_text())
    assert [j for j,(x,y)in enumerate(zip(inputs,oldinputs))if x!=y]==[103]and[j for j,(x,y)in enumerate(zip(expected,oldexpected))if x!=y]==[103]
    assert sha(batch/manifest['module_file'])==sha(prior/manifest['module_file'])
    assert sha(reviewer)==own_sha and shared=={n:sha(ROOT/n)for n in shared}and sha(SOURCE)==SOURCE_SHA and sha(PROFILE/'index.sqlite')==PROFILE_INDEX_SHA
    for name,digest in receipt['source_before'].items():assert sha(ROOT/name)==digest
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-raster0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    for name,value in [('nav-recomputation.json',nav_stats),('real-m2-provenance.json',dict(index_sha256=INDEX_SHA,inventory_sha256=ASSETS_SHA,archives=archive_cache,assets=m2_rows))]:(out/name).write_text(json.dumps(value,indent=2)+'\n')
    (out/'reviewer-source.py').write_bytes(reviewer.read_bytes())
    report=dict(status='passed_scoped_independent_read_only_review',receipt=str(receipt_file.relative_to(ROOT)),receipt_sha256=FINAL_SHA,
        reviewer_sha256=own_sha,reviewer_common_numeric_sources=shared,author_sources=14,source_before_equals_after=True,original_or_browser_executed=False,
        frozen_artifact_SHA_verified=True,original_nonexport_and_exportprefix_identical=True,original_callee_bodies_preserved=True,
        expected_only_in_python_artifact=True,input_original_keyset=['id','input'],counts=dict(counts),original_cases_added=0,
        original_actual_calls=1477,original_stages1332='1218candidate+114navigation;31parse+114transform are additional explicit original entries,not included in1332',
        transform_recomputed_from_original_WAT_prefix=True,original_WAT_crosschecked_against_pinned_profile_index=PROFILE_INDEX_SHA,
        candidate_and_navigation_recomputed_without_author_model=True,
        real_m2_raw_archive_payloads_reread=True,index_sha256=INDEX_SHA,inventory_sha256=ASSETS_SHA,
        updated_cap_case103_verified=True,cap_branch_evidence='Source+independentuncapped451ish>400/AABBintersect/sampledchangedcells;notdynamicinstructioncounter',
        four_280_560_grid_origin_cases_are_declared_inputs_not_world_producer=True,old100525_scope_retained=True,
        runtime=dict(denied_imports=878,actual_host_calls=0,memory_cap_bytes=33554432,actual_max_memory_bytes=rt['max_memory_bytes'],pid=receipt['process']['pid'],exit_code=0,pid_verified_missing=True),
        evidence_files={name:sha(out/name)for name in('nav-recomputation.json','real-m2-provenance.json','reviewer-source.py')},
        limitations=['Sharedbinary32/sqrt/trigprimitivesarepreviouslyvalidateddependencies;thisreadonlyreviewdoesnotreprovealltheirinputs.',
            'WATprefixinterpreterandPythonrecomputationarenotneworiginalexecution;original1477callsremainauthorreceiptcoverage.',
            'OnlycanonicalvalidMD20collisionarrays+declaredtransforms/ground/grids;full1104,M2rendering,WMOdecoderandcomplete6730rasterproducerarenotrestored.',
            'Onlynewunwritteninactivecandidatecapacityunknown;active/oldknownrowsandnavigationtailstrict;unknownrawwordsretained,notpredictedzero.',
            'BaseMPQassetreadprovenanceisnotlatest135completeassetequivalence,completeworldconstructionorfullgamecompletion.'])
    target=out/'review.json';target.write_text(json.dumps(report,indent=2)+'\n');wrapper=dict(report,review_path=str(target.relative_to(ROOT)),review_sha256=sha(target))
    (ROOT/'reports/2026-11-01-world-raster0135-independent-review.json').write_text(json.dumps(wrapper,indent=2)+'\n')
    (ROOT/'reports/2026-11-01-world-raster0135-independent-review.md').write_text(f'''# 0.135.1 world raster独立只读复核\n\n[最终作者收据](../{str(receipt_file.relative_to(ROOT))}) 已通过限定域独审；114例/1477完整原件调用/0差异保持，不新增原件案例。[review](../{str(target.relative_to(ROOT))}) SHA `{sha(target)}`。\n\n独立解释原18572的无分支WAT矩阵前缀，重新算全部transform字节、12375候选与9328导航；没有调用作者world_raster模型。31份真实M2从固定MPQ原offset再次读回，23份非空、670顶点/1113三角形；source14、输入/预期分离、原件非export和完整callee均核对。旧候选backing与导航尾字节严格比较，新分配未写capacity作为明确未知保留。\n\n新case103确实穿过网格，独立算出uncapped步数超过400并产生导航改变1/5/6/10；这是源码、输入和输出共同支持的分支依据，未假装动态instruction counter。旧100525仅case103不同，模块及其它113例保持。4份显式280/560维度/原点输入不算真实world producer。\n\n共享binary32/sqrt/trig依赖已另验；本次只读复算不重跑原件。完整M2/模型渲染、WMO、6730候选merge/ground/cache producer、最新资产全量等价及完整游戏仍未知。\n''')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),status=report['status'],counts=dict(counts))))


if __name__=='__main__':main()
