#!/usr/bin/env python3
"""Reproducible independent static/read-only review of fixed135 world cache.

No original execution, snapshot restore, or production-model execution occurs.
The exact reviewed source is guarded; bounded indexed WAT, static zone bytes
and raw387 WMO-group budgets are reread and retained.  This review does not
substitute for a complete real-asset -> original-world differential.
"""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,sqlite3,struct,sys
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parents[1]
MODEL=ROOT/'reconstruction/resource_spec/world_cache135.py'
MODEL_SHA='34bdcd7116dcf25ec300d5ac028ca97122dba8b2be64e91324e03a37cf89a762'
SOURCE=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
SOURCE_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
INDEX_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
WAT_SHA='15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'
INVENTORY=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
INVENTORY_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
INDICES=(6730,15374,9328,12375,18572,18670,84193)
WINDOWS={
 'zone_extent_primary_flag':(473,505,('f32.load offset=120','f32.const 0x1.4p+4','i32.load8_u offset=148')),
 'nav_width':(6230,6253,('f32.add','f32.ceil','i32.trunc_sat_f32_u')),
 'origin':(6365,6382,('f32.sub','local.set 66','local.set 63')),
 'no_primary_ground':(6616,6689,('f32.const 0x1p-1','call 18670','f32.const nan')),
 'center_seed':(8249,8305,('i32.trunc_sat_f32_u','i32.load8_u','i32.store')),
 'perimeter_iterator':(8330,8785,('call 15374','i32.load8_u')),
 'four_neighbour_bfs':(9014,9373,('i32.div_u','i32.const 1','i32.sub','i32.add','i32.load8_u')),
 'final_raw_nav_or':(9374,9403,('i32.load8_u','i32.const 1','i32.xor','i32.or','i32.store8')),
 'secondary_width_and_geometry':(9720,10000,('f32.ceil','call 9513','call 18572','call 12375','0x1.fffffep+127')),
 'secondary_filter_and_max':(10204,10295,('call 18670','0x1.99999ap-4','0x1.8p+1','f32.gt','f32.le','f32.lt')),
 'secondary_absent_if_no_update':(10312,10327,('local.get 23','i32.const -1','call 71889')),
}


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def production_sources():
    """Independently collect both package entries and static local imports."""
    base=ROOT/'reconstruction';pending=[MODEL,base/'resource_spec/__init__.py',base/'core_spec/__init__.py'];seen=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        assert path.is_file(),path;seen.add(path)
        package=path.parent
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom):
                if node.level:
                    assert node.level==1
                    names=[node.module]if node.module else[a.name for a in node.names]
                    pending.extend(package/(n.replace('.','/')+'.py')for n in names)
                elif node.module in('core_spec','resource_spec'):
                    pending.append(base/node.module/'__init__.py')
                    pending.extend(base/node.module/(a.name+'.py')for a in node.names if(base/node.module/(a.name+'.py')).is_file())
                elif node.module and node.module.split('.')[0]in('core_spec','resource_spec'):
                    pending.append(base/(node.module.replace('.','/')+'.py'))
            elif isinstance(node,ast.Import):
                pending.extend(base/(a.name.replace('.','/')+'.py')for a in node.names if a.name.split('.')[0]in('core_spec','resource_spec')and'.'in a.name)
    return tuple(sorted(seen))


def uint(raw,pos):
    value=shift=0
    while True:
        byte=raw[pos];pos+=1;value|=(byte&127)<<shift
        if byte<128:return value,pos
        shift+=7;assert shift<=35


def sint32(raw,pos):
    value=shift=0
    while True:
        byte=raw[pos];pos+=1;value|=(byte&127)<<shift;shift+=7
        if byte<128:break
        assert shift<=35
    if byte&64:value-=1<<shift
    return value&0xffffffff,pos


def static_zone(raw):
    """Independent data-section decode, including original implicit-zero gaps."""
    assert raw[:8]==b'\0asm\1\0\0\0';at=8;sections={}
    while at<len(raw):
        kind=raw[at];size,start=uint(raw,at+1);end=start+size;assert end<=len(raw)
        if kind:assert kind not in sections;sections[kind]=(start,end)
        at=end
    at,end=sections[11];count,at=uint(raw,at);zone=bytearray(152);coverage=bytearray(152);parts=[];address=5456016
    for index in range(count):
        flags,at=uint(raw,at);assert flags in(0,1,2);memory=None;offset=None
        if flags!=1:
            memory=0
            if flags==2:memory,at=uint(raw,at)
            assert raw[at]==0x41;offset,at=sint32(raw,at+1);assert raw[at]==0x0b;at+=1
        size,start=uint(raw,at);at=start+size;assert at<=end
        if memory!=0:continue
        lo=max(address,offset);hi=min(address+152,offset+size)
        if lo<hi:
            payload=raw[start+lo-offset:start+hi-offset];zone[lo-address:hi-address]=payload;coverage[lo-address:hi-address]=bytes([1])*(hi-lo)
            parts.append(dict(index=index,segment_address=offset,segment_length=size,segment_file_offset=start,
                copied_zone_offsets=[lo-address,hi-address],copied_file_offsets=[start+lo-offset,start+hi-offset],copied_sha256=hashlib.sha256(payload).hexdigest()))
    assert at==end
    assert hashlib.sha256(zone).hexdigest()=='aa7ace8cbc885786ee0752885198aa690e9482b91c77cdec6ebf0dee90828da7'
    assert struct.unpack_from('<7I',zone,96)==(0,12,3323121664,3290316800,1116209152,1070386381,1123024896)
    assert zone[148]==0 and struct.unpack_from('<I',zone,48)[0]==4
    return dict(address=address,bytes152_hex=zone.hex(),sha256=hashlib.sha256(zone).hexdigest(),active_segments=parts,
        initial_zero_gap_offsets=[i for i,c in enumerate(coverage)if not c],map_id=0,center_xy_bits=[3323121664,3290316800],
        fallback_z_bits=1116209152,heading_bits=1070386381,radius_bits=1123024896,primary_enabled_byte148=0,
        raw_polygon_length48=4,selected_primary_polygon_length=0,implicit_zero_is_module_initialization_not_runtime_guess=True)


def chunk_rows(raw,start=0):
    result=[];at=start
    while at<len(raw):
        assert at+8<=len(raw);tag,size=struct.unpack_from('<4sI',raw,at);end=at+8+size;assert end<=len(raw)
        result.append((tag,raw[at+8:end]));at=end
    return result


def group_budgets():
    """Raw MOPY/u16-source-index review; never use production geometry parser."""
    inventory=json.loads(INVENTORY.read_text());groups=[];roots=[];total_vertices=total_indices=0
    for row in inventory['requests']:
        if row['status']!=200 or not row['chain'].endswith('.wmo'):continue
        path=Path(row['file']);assert path.stat().st_size==row['bytes']and sha(path)==row['sha256'];raw=path.read_bytes()
        top=chunk_rows(raw);assert next(p for t,p in top if t==b'REVM')==struct.pack('<I',17)
        kind,payload=next((t,p)for t,p in top if t in(b'DHOM',b'PGOM'))
        if kind==b'DHOM':roots.append(dict(chain=row['chain'],group_count=struct.unpack_from('<I',payload,4)[0],sha256=row['sha256']));continue
        assert len(payload)>=68;sub=dict(chunk_rows(payload,68));v=sub[b'TVOM'];i=sub[b'IVOM'];a=sub[b'YPOM']
        assert len(v)%12==len(i)%6==len(a)%2==0 and len(i)//6==len(a)//2
        nv=len(v)//12;indices=struct.unpack('<'+'H'*(len(i)//2),i);seen=set();kept=0
        for triangle in range(len(a)//2):
            if a[triangle*2]&4:continue
            for index in indices[triangle*3:triangle*3+3]:assert index<nv;seen.add(index);kept+=1
        assert len(seen)<=65536 and kept<=196608
        groups.append(dict(chain=row['chain'],input_bytes=row['bytes'],input_sha256=row['sha256'],
            source_vertices=nv,source_triangles=len(a)//2,filtered_vertices=len(seen),filtered_indices=kept,
            frozen_mesh_budget_passed=True))
        total_vertices+=len(seen);total_indices+=kept
    assert len(roots)==23 and len(groups)==387
    max_vertices=max(groups,key=lambda r:r['filtered_vertices']);max_indices=max(groups,key=lambda r:r['filtered_indices'])
    assert max_vertices['filtered_vertices']==15452 and max_indices['filtered_indices']==30603
    assert(total_vertices,total_indices)==(459261,1051449)
    return dict(actual_unique_wmo_files=410,roots=roots,groups=groups,group_count=387,
        total_filtered_vertices=total_vertices,total_filtered_indices=total_indices,max_vertices=max_vertices,max_indices=max_indices,
        per_group_frozen_vertex_budget=65536,per_group_frozen_index_budget=196608,
        filter='MOPY triangle first-byte &4 rejects; independent group-local unique u16 source indices',
        original_calls=0,production_geometry_parser_called=False)


def main():
    assert sha(MODEL)==MODEL_SHA and sha(SOURCE)==SOURCE_SHA
    assert sha(PROFILE/'index.sqlite')==INDEX_SHA and sha(PROFILE/'official-0.135.1-full.wat')==WAT_SHA
    assert sha(INVENTORY)==INVENTORY_SHA
    sources=(*production_sources(),Path(__file__));before={str(p.relative_to(ROOT)):sha(p)for p in sources}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-cache0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    raw=SOURCE.read_bytes();zone=static_zone(raw);(out/'zone0-initial152.bin').write_bytes(bytes.fromhex(zone['bytes152_hex']))
    sql='SELECT idx,wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?'
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);con.row_factory=sqlite3.Row
    functions=[];texts={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for index in INDICES:
            row=dict(con.execute(sql,(index,)).fetchone());stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start'])
            assert text.startswith(f'  (func (;{index};)'.encode())and len(text)==row['wat_end']-row['wat_start']
            assert row['body_end']-row['body_start']==row['body_bytes'];path=out/f'{index}.wat';path.write_bytes(text);texts[index]=text
            functions.append(dict(query=sql,query_parameters=[index],**row,wat_sha256=hashlib.sha256(text).hexdigest(),
                body_sha256=hashlib.sha256(raw[row['body_start']:row['body_end']]).hexdigest()))
    con.close();windows=[];lines=texts[6730].splitlines(keepends=True)
    for name,(start,end,tokens)in WINDOWS.items():
        text=b''.join(lines[start-1:end]);assert all(token.encode()in text for token in tokens),(name,tokens)
        path=out/f'6730-{start}-{end}-{name}.wat';path.write_bytes(text)
        windows.append(dict(name=name,function=6730,line_start=start,line_end=end,file=path.name,
            sha256=hashlib.sha256(text).hexdigest(),required_tokens=list(tokens),all_tokens_observed=True))
    budget=group_budgets();budget_path=out/'actual387-group-budgets.json';budget_path.write_text(json.dumps(budget,indent=2)+'\n')
    after={str(p.relative_to(ROOT)):sha(p)for p in sources};assert before==after and sha(INVENTORY)==INVENTORY_SHA
    for name,h in before.items():
        path=out/'source-snapshot'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((ROOT/name).read_bytes());assert sha(path)==h
    result=dict(status='passed_scoped_static_read_only_review',version='0.135.1',build='0898d5e3',kind='independent_static_review_not_new_original_differential',
        production_source_sha256=MODEL_SHA,source_count=len(before),source_sha256_before=before,source_sha256_after=after,
        original_sha256=SOURCE_SHA,sqlite_sha256=INDEX_SHA,full_wat_sha256=WAT_SHA,functions=functions,windows=windows,
        zone=zone,actual_group_budget=dict(path=budget_path.name,sha256=sha(budget_path),group_count=387,max_vertices=15452,max_indices=30603),
        reviewed_rules=[
            dict(rule='extent / width / origin',model_lines=[56,64],basis='6730 zone120+20 roundedf32; diameter ceil; secondaryceil doublef32diameter; centre-extent'),
            dict(rule='no-primary ground',model_lines=[67,76],basis='6730 no-primary calls18670 per row-major one-unit cellcentre, canonicalNaN onmiss'),
            dict(rule='connectivity',model_lines=[79,101],basis='6730 plus15374 enumerate freecentre and allfourperimeter cells, floodonlyfree four-neighbours, thenoldbyte|(visited^1)'),
            dict(rule='secondary max',model_lines=[104,132],basis='6730 calls18670 at half-unit cellcentre; lowerstrict+.1 andupperinclusive+3, boundsafterfilters, replaceNaN/loweronly, absentifnoupdate'),
            dict(rule='instance phases',model_lines=[186,209],basis='Declared nav_m2 thennav_wmo thensecondary_wmo; independentlyrestored placement sourceorder retained'),
        ],group_split_equivalence=dict(
            premise='Original4464 deduplicates source indices independently for each group and appends groups in rootindex order.',
            vertex_transform='18572 computes fixedmatrix fromsamepose then eachvertex independently. Transform(concatenation)=concatenation(transform(group)).',
            navigation='9328 pertriangle AABB/normal/edge-length400cap andsamplepositions dependonlythattriangle andsameground; effectsare nav[index]=1. No cross-trianglefloatreduction.',
            secondary='12375 emits orderedcandidatepairs pertriangle; grouping preserves triangleorder and scalaroperations. Final6730 maxmerge retainsfirstequal.',
            supporting_functions=[18572,9328,12375],actual_all387_groups_fit_frozen_mesh_budget=True,
            arithmetic_statement_is_static_reasoning_not_new_original_differential=True),
        historical_world_comparison=dict(status='pending_in_root_owned_run',reviewed=False,new_original_calls=0,
            note='A later separately hashed read-only wrapper must inspect terminal asset-world comparison receipt; this static review cannot mark it passed.'),
        original_executed=False,production_executed=False,snapshot_read=False,new_original_calls=0,new_original_cases=0,
        limitations=['Successful finite canonical nonflat/no-primary path only. Primary-present/polygon/flat world paths are outside review.',
            'Fullarrayworld comparison, othermaps/modes, VFS/cache/Rc ownership andprofile/menu/rendering not established by static checks.',
            'This reviewer binds evidence windows and exact current source; it is not a formal equivalence proof or completeworld differential.'],
        files_sha256={str(p.relative_to(out)):sha(p)for p in out.iterdir()if p.is_file()})
    target=out/'review.json';target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),source_count=len(before),functions=len(functions),windows=len(windows),original_calls=0)))


if __name__=='__main__':main()
