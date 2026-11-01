#!/usr/bin/env python3
"""Read-only independent WMO review; no author model or original executes.

Re-read stored MPQ payloads and independently decode archive tables, canonical
WMO chunks and first-use collision indexing. All comparisons use raw words.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,os,sqlite3,struct,sys
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import sha
sys.dont_write_bytecode=True

BATCH=ROOT/'evidence/wmo-geometry0135-20261101T103753.433490Z'
RECEIPT_SHA='331886a6b0a720966b17c8a5338ed4257b8900f910d1a64f2cf7919ac1c1bd18'
INDEX=ROOT/'evidence/resource-index-base-20261101T032320.856364Z/index.sqlite'
INDEX_SHA='a3f219f6e76e1d87e50b0790b757f999091e2b479d3b1d40ac2c101aa8680cf4'
INVENTORY=ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
INVENTORY_SHA='cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
ARCHIVES=ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
PROFILE_INDEX_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
ROLES={1510:('7f7f','','2f1b0db5ff4235ab674e720d57ba8a520107b959bf1708cf140aab5492fe8cb0'),
       4464:('7f7f7f7f7f7f','','ba1477e3eddfc9b96a6d67be12a4af02e4d283ed787bb717e160b299bad8d5d1')}


def crypt_table():
    values=[0]*1280;seed=0x100001
    for low in range(256):
        for high in range(5):
            seed=(seed*125+3)%0x2aaaab;upper=(seed&65535)<<16
            seed=(seed*125+3)%0x2aaaab;values[low+high*256]=upper|(seed&65535)
    return values


CRYPT=crypt_table();MASK=0xffffffff


def name_hash(text,kind):
    first=0x7fed7fed;second=0xeeeeeeee
    for byte in text.upper().encode('ascii'):
        first=CRYPT[(kind<<8)+byte]^((first+second)&MASK)
        second=(byte+first+second+(second<<5)+3)&MASK
    return first


def decrypt_table(raw,name):
    key=name_hash(name,3);seed=0xeeeeeeee;out=bytearray()
    for(word,)in struct.iter_unpack('<I',raw):
        seed=(seed+CRYPT[0x400+(key&255)])&MASK;plain=word^((key+seed)&MASK)
        out+=struct.pack('<I',plain)
        key=(((~key<<21)+0x11111111)|(key>>11))&MASK
        seed=(plain+seed+(seed<<5)+3)&MASK
    return bytes(out)


def archive_tables(record):
    path=ARCHIVES/record['name'];assert path.stat().st_size==record['bytes']and sha(path)==record['sha256']
    with path.open('rb')as f:
        header=f.read(32);magic,size,length,version,shift,hp,bp,hn,bn=struct.unpack('<4sIIHHIIII',header)
        assert(magic,size,length,version)==(b'MPQ\x1a',32,record['bytes'],0)
        assert(hn,bn,512<<shift)==(record['hash_entries'],record['block_entries'],record['sector_bytes'])
        f.seek(hp);hr=f.read(hn*16);f.seek(bp);br=f.read(bn*16)
    hashes=decrypt_table(hr,'(hash table)');blocks=decrypt_table(br,'(block table)')
    assert hashlib.sha256(hashes).hexdigest()==record['hash_table_sha256']
    assert hashlib.sha256(blocks).hexdigest()==record['block_table_sha256']
    return hashes,blocks,dict(record,header32_hex=header.hex(),raw_hash_table_sha256=hashlib.sha256(hr).hexdigest(),raw_block_table_sha256=hashlib.sha256(br).hexdigest())


def chunks(raw,start=0):
    rows=[];cursor=start
    while cursor<len(raw):
        assert cursor+8<=len(raw)
        tag=raw[cursor:cursor+4];length=int.from_bytes(raw[cursor+4:cursor+8],'little');end=cursor+8+length
        assert end<=len(raw);rows.append((tag,raw[cursor+8:end]));cursor=end
    assert cursor==len(raw);return rows


def parse_geometry(raw):
    top=chunks(raw);assert [v for k,v in top if k==b'REVM']==[b'\x11\0\0\0']
    selected=[(k,v)for k,v in top if k in(b'DHOM',b'PGOM')];assert len(selected)==1
    tag,data=selected[0]
    if tag==b'DHOM':
        assert len(data)==64;return dict(kind='root',group_count=int.from_bytes(data[4:8],'little'))
    assert len(data)>=68;inside=chunks(data,68)
    def only(tag):
        values=[v for k,v in inside if k==tag];assert len(values)==1;return values[0]
    vertices,indices,attributes=only(b'TVOM'),only(b'IVOM'),only(b'YPOM')
    assert len(vertices)%12==len(indices)%6==len(attributes)%2==0 and len(indices)==len(attributes)*3
    vertex_count=len(vertices)//12;assert vertex_count<=65536
    assert all(value<vertex_count for(value,)in struct.iter_unpack('<H',indices))
    return dict(kind='group',vertices_hex=vertices.hex(),indices_u16_hex=indices.hex(),attributes_hex=attributes.hex(),
                group_flags=int.from_bytes(data[8:12],'little'),liquid_type=int.from_bytes(data[52:56],'little'))


def append_collision(projection,vertex_bytes,index_bytes,exclude,required):
    source=bytes.fromhex(projection['vertices_hex']);indices=bytes.fromhex(projection['indices_u16_hex']);attributes=bytes.fromhex(projection['attributes_hex'])
    destination=bytearray(vertex_bytes);out=bytearray(index_bytes);seen={}
    for triangle,(a,b,c)in enumerate(struct.iter_unpack('<3H',indices)):
        flag=attributes[triangle*2]
        if flag&exclude or(flag&required)!=(required&255):continue
        for original_index in(a,b,c):
            if original_index not in seen:
                seen[original_index]=len(destination)//12;destination+=source[original_index*12:original_index*12+12]
            out+=struct.pack('<I',seen[original_index])
    return bytes(destination),bytes(out)


def grown_capacity(capacity,length):
    while capacity<length:capacity=max(4,capacity*2)
    return capacity


def verify_vector(vector,raw,stride,capacity,counts):
    backing=bytes.fromhex(vector['backing_hex']);length=len(raw)//stride
    assert len(raw)%stride==0 and vector['length']==length and vector['capacity']==capacity
    assert vector['active_hex']==raw.hex()and len(backing)==capacity*stride and backing[:len(raw)]==raw
    tail=backing[len(raw):];counts['strict_geometry_bytes']+=len(raw);counts['allocator_unknown_tail_bytes']+=len(tail)
    counts['nonzero_unknown_tail_bytes']+=sum(x!=0 for x in tail)


def source_closure():
    pending=[ROOT/'scripts/check_wmo_geometry135.py'];seen=set()
    def add(name,relative=None):
        base=relative if relative else(ROOT/'reconstruction'if name.startswith('resource_spec')else ROOT/'scripts')
        p=base.joinpath(*name.split('.')).with_suffix('.py')
        if p.is_file():
            pending.append(p)
            if 'reconstruction' in p.parts:pending.append(ROOT/'reconstruction/resource_spec/__init__.py')
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):
                for alias in node.names:add(alias.name)
            elif isinstance(node,ast.ImportFrom):
                assert node.level in(0,1)
                if node.module:add(node.module,path.parent if node.level else None)
    seen.add(ROOT/'scripts/run_wmo_geometry135_oracle.mjs')
    return{str(p.relative_to(ROOT))for p in seen}


def main():
    own=Path(__file__);own_sha=sha(own);receipt_path=BATCH/'wmo-geometry135-comparison.json';assert sha(receipt_path)==RECEIPT_SHA
    receipt=json.loads(receipt_path.read_text());before=receipt['source_before'];assert before==receipt['source_after']and source_closure()==set(before)and len(before)==7
    for name,digest in before.items():assert sha(ROOT/name)==digest==sha(BATCH/'source-snapshot'/name)
    for table in('artifacts','frozen_artifacts'):
        for name,digest in receipt[table].items():assert sha(BATCH/name)==digest
    assert receipt['expected_before_original']is True and receipt['input_only']is True and receipt['differences']==0
    assert sha(SOURCE)==SOURCE_SHA and sha(INDEX)==INDEX_SHA and sha(INVENTORY)==INVENTORY_SHA and sha(PROFILE/'index.sqlite')==PROFILE_INDEX_SHA
    original=SOURCE.read_bytes();types,imports,decl,bodies,_=parse_source(original);manifest=json.loads((BATCH/'manifest.json').read_text())
    changed=(BATCH/manifest['module_file']).read_bytes();old,new=section_list(original),section_list(changed)
    assert len(imports)==878 and[x[0]for x in old]==[x[0]for x in new]and 8 not in[x[0]for x in old]
    for x,y in zip(old,new):
        if x[0]!=7:assert original[x[1]:x[3]]==changed[y[1]:y[3]]
    old_exports,_=export_entries(original,next(x for x in old if x[0]==7));new_exports,_=export_entries(changed,next(x for x in new if x[0]==7))
    assert new_exports==old_exports+[(r['name'],0,r['index'])for r in manifest['roles']]
    assert{r['index']for r in manifest['roles']}==set(ROLES)
    for r in manifest['roles']:
        i=r['index'];params,result,digest=ROLES[i];start,end=bodies[i]
        assert types[decl[i-len(imports)]]==(bytes.fromhex(params),bytes.fromhex(result))
        assert hashlib.sha256(original[start:end]).hexdigest()==digest==r['body_sha256']
    g=next(x for x in old if x[0]==6);assert original[g[2]:g[3]].hex()=='017f01418080c0000b'
    profile=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);profile.row_factory=sqlite3.Row;wat_rows=[];texts={}
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for f in manifest['functions']:
            row=dict(profile.execute('select *from functions where idx=?',(f['idx'],)).fetchone());assert(row['body_start'],row['body_end'])==bodies[f['idx']]
            stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);assert text==(BATCH/f"{f['idx']}.wat").read_bytes()
            assert text.startswith(f"  (func (;{f['idx']};)".encode())and hashlib.sha256(text).hexdigest()==f['wat_sha256']
            assert hashlib.sha256(original[slice(*bodies[f['idx']])]).hexdigest()==f['body_sha256'];texts[f['idx']]=text.decode()
            wat_rows.append(dict(index=f['idx'],wat_sha256=f['wat_sha256'],body_sha256=f['body_sha256'],profile_row=row))
    assert set(texts)=={1510,4464,9513,60913,60916,81334,65313,65321,65323,39629,44774}
    assert 'call 1510'in texts[4464]and 'i32.load8_u'in texts[4464]and 'i32.const 255'in texts[4464]
    instructions=[' '.join(line.split())for line in texts[4464].splitlines()]
    assert '\n'.join(('local.get 0','local.get 3','i32.and','local.get 3','i32.const 255','i32.and','i32.ne','br_if 0 (;@4;)'))in'\n'.join(instructions)
    assert 'i32.load16_u'in instructions and 'i32.store'in instructions and 'i32.const 2'in instructions
    assert all('call 81334'in texts[i]and 'i32.store8'in texts[i]for i in(60913,60916))
    assert 'call 106891'in texts[81334]and 'call 71889'in texts[81334]
    inventory=json.loads(INVENTORY.read_text());actual_files={x['chain']:x for x in inventory['requests']if x['status']==200 and x['chain'].endswith('.wmo')};assert len(actual_files)==410
    provenance=json.loads((BATCH/'asset-provenance.json').read_text());assert provenance['all410_files_manifest']==list(actual_files.values())
    assert provenance['root_request_order_is_local_planning_not_original9513']is True
    index=sqlite3.connect(INDEX.resolve().as_uri()+'?mode=ro',uri=True);index.row_factory=sqlite3.Row
    archives={};parsed={};asset_rows=[];counts=Counter();root_requests={}
    for chain,asset in actual_files.items():
        row=dict(index.execute('select *from files where archive=?and normalized_name=?',(asset['archive'],chain.upper())).fetchone());assert row==asset['prior_index_row']
        if asset['archive']not in archives:
            record=dict(index.execute('select *from archives where name=?',(asset['archive'],)).fetchone());archives[asset['archive']]=archive_tables(record)
        hashes,blocks,_=archives[asset['archive']]
        offset,stored,size,flags=struct.unpack_from('<4I',blocks,row['block_index']*16)
        assert(offset,stored,size,flags)==(row['data_offset'],row['stored_bytes'],row['decoded_bytes'],row['flags'])and flags==0x80000000 and stored==size
        ha,hb,locale,platform,reserved,block=struct.unpack_from('<IIHBBI',hashes,row['hash_slot']*16)
        assert(ha,hb)==(name_hash(chain,1),name_hash(chain,2))and(locale,platform,reserved,block)==(row['locale'],row['platform'],0,row['block_index'])
        assert asset['hash_entry']==dict(slot=row['hash_slot'],name_a=ha,name_b=hb,locale=locale,platform=platform,reserved=reserved,block=block)
        with(ARCHIVES/asset['archive']).open('rb')as stream:stream.seek(offset);raw=stream.read(stored)
        assert raw==Path(asset['file']).read_bytes()and len(raw)==asset['bytes']and hashlib.sha256(raw).hexdigest()==asset['sha256']==row['decoded_sha256']==row['reference_sha256']
        assert raw[:16].hex()==row['first16_hex'];p=parse_geometry(raw);parsed[chain]=p
        if p['kind']=='root':
            counts['actual_roots']+=1;root_requests[chain]=[chain[:-4]+'_'+str(i).zfill(3)+'.wmo'for i in range(p['group_count'])]
        else:
            counts['actual_groups']+=1;counts['source_vertices']+=len(p['vertices_hex'])//24;counts['source_u16_indices']+=len(p['indices_u16_hex'])//4
            v,i=append_collision(p,b'',b'',4,0);counts['default_filtered_vertices']+=len(v)//12;counts['default_filtered_u32_indices']+=len(i)//4
        asset_rows.append(dict(chain=chain,bytes=len(raw),sha256=asset['sha256'],archive=asset['archive'],block_index=row['block_index'],hash_slot=row['hash_slot'],offset=offset,kind=p['kind']))
    assert root_requests==provenance['root_group_requests']and sum(map(len,root_requests.values()))==387
    assert set(x for rows in root_requests.values()for x in rows)=={n for n,p in parsed.items()if p['kind']=='group'}
    cases=json.loads((BATCH/'inputs.json').read_text());expected=json.loads((BATCH/'expected.json').read_text());assert len(cases)==len(expected)==425
    runner=(BATCH/'source-snapshot/scripts/run_wmo_geometry135_oracle.mjs').read_text();checker=(BATCH/'source-snapshot/scripts/check_wmo_geometry135.py').read_text()
    assert 'expected.json'not in runner and 'snapshot'not in runner.replace('snapshot_input_used:false','')and 'bytes().set(data,p)'in runner
    assert 'for(const imp of imports)'in runner and "throw Error('All original hosts denied')"in runner
    assert checker.index('exp.write_text(')<checker.index('child=subprocess.Popen(')
    assert receipt['process']['command'][-1]==str(BATCH/'inputs.json')
    summaries=[]
    with(BATCH/'results.jsonl').open()as stream:
        for c,e,line in zip(cases,expected,stream):
            a=json.loads(line);assert c['id']==e['id']==a['id']and set(c)=={'id','input'}and set(c['input'])=={'assets','append_operations','initial_mesh'}
            s=c['input'];assert len(a['assets'])==len(s['assets'])==len(e['projections'])
            for item,observation,pre in zip(s['assets'],a['assets'],e['projections']):
                assert set(item)=={'path','bytes','sha256','chain'};asset=actual_files[item['chain']]
                assert(item['path'],item['bytes'],item['sha256'])==(asset['file'],asset['bytes'],asset['sha256'])
                projection=parsed[item['chain']];assert observation['projection']==pre==projection and observation['chain']==item['chain']
                raw=bytes.fromhex(observation['raw_output160_hex']);cursor=bytes.fromhex(observation['raw_cursor_before_hex'])
                assert len(raw)==160 and len(cursor)==16 and observation['raw_cursor_before_hex']==observation['raw_cursor_after_hex']
                assert int.from_bytes(cursor[4:8],'little')==asset['bytes'];counts['raw160_bytes_retained']+=160;counts['parse_entries']+=1
                if projection['kind']=='root':
                    assert int.from_bytes(raw[:4],'little')==0xffffffff and int.from_bytes(raw[40:44],'little')==projection['group_count'];counts['strict_geometry_bytes']+=4
                    assert observation['vectors']is None
                else:
                    assert raw[:4]!=b'\xfe\xff\xff\xff'and raw[:4]!=b'\xff'*4
                    assert struct.unpack_from('<2I',raw,152)==(projection['group_flags'],projection['liquid_type']);counts['strict_geometry_bytes']+=8
                    for name,key,stride,base in(('vertices','vertices_hex',12,0),('indices_u16','indices_u16_hex',2,48),('attributes','attributes_hex',2,72)):
                        payload=bytes.fromhex(projection[key]);v=observation['vectors'][name];verify_vector(v,payload,stride,grown_capacity(0,len(payload)//stride),counts)
                        assert struct.unpack_from('<3I',raw,base)==(v['capacity'],v['pointer'],v['length'])
            mesh=s['initial_mesh'];assert set(mesh)=={'vertices_bits','indices'}
            vertices=b''.join(struct.pack('<3I',*v)for v in mesh['vertices_bits']);indices=b''.join(struct.pack('<I',x)for x in mesh['indices']);vc,ic=len(vertices)//12,len(indices)//4
            assert len(s['append_operations'])==len(e['append_stages'])==len(a['append_stages'])
            for op,pre,observation in zip(s['append_operations'],e['append_stages'],a['append_stages']):
                assert set(op)=={'asset_index','exclude_flags','required_flags'};p=parsed[s['assets'][op['asset_index']]['chain']]
                vertices,indices=append_collision(p,vertices,indices,op['exclude_flags'],op['required_flags']);vc=grown_capacity(vc,len(vertices)//12);ic=grown_capacity(ic,len(indices)//4)
                independent=dict(vertex_capacity=vc,index_capacity=ic,vertex_count=len(vertices)//12,index_count=len(indices)//4,vertices_hex=vertices.hex(),indices_u32_hex=indices.hex());assert pre==independent
                for name,payload,stride,cap,header in(('vertices',vertices,12,vc,'raw_vertex_vec12_hex'),('indices_u32',indices,4,ic,'raw_index_vec12_hex')):
                    v=observation[name];verify_vector(v,payload,stride,cap,counts);assert struct.unpack('<3I',bytes.fromhex(observation[header]))==(v['capacity'],v['pointer'],v['length'])
                counts['append_entries']+=1
            assert a['raw_inputs_unchanged']is True and a['hash_state_before_hex']=='00'*17 and len(bytes.fromhex(a['hash_state_after_hex']))==17 and a['hash_state_after_hex'][-2:]=='01'
            assert a['memory_bytes']<=33554432 and a['memory_initial_bytes']<=a['memory_bytes'];counts['cases']+=1
            summaries.append(dict(id=c['id'],label=e['label'],parses=len(a['assets']),appends=len(a['append_stages']),final_vertices=len(vertices)//12,final_indices=len(indices)//4))
        assert not stream.read().strip()
    assert cases[-1]['input']['initial_mesh']['vertices_bits']==[[0,0x80000000,0x3f800000]]*65537
    wide=a['append_stages'][0]
    wi=bytes.fromhex(wide['indices_u32']['active_hex']);assert struct.unpack_from('<3I',wi)==(65536,0,65536)and max(x for(x,)in struct.iter_unpack('<I',wi[12:]))>65535
    assert(counts['cases'],counts['parse_entries'],counts['append_entries'])==(425,426,404)
    assert(counts['source_vertices'],counts['source_u16_indices'],counts['default_filtered_vertices'],counts['default_filtered_u32_indices'])==(987600,3168786,459261,1051449)
    for key,value in receipt['comparison'].items():assert counts[key]==value
    rt=receipt['runtime'];assert(rt['calls'],rt['denied_imports'],rt['actual_host_calls'],rt['fresh_instances'],rt['memory_page_cap'],rt['max_memory_bytes'])==(830,878,0,425,512,19202048)
    assert rt['snapshot_input_used']is False and rt['world_or_once_injected']is False and rt['hash_initialization_original']is True
    process=receipt['process'];assert process['exit_code']==0 and process['deadline_seconds']==60 and process['pid']==process['pgid']==20841
    assert '--wasm-max-mem-pages=512'in process['command']and '--max-old-space-size=512'in process['command']
    assert sha(Path(process['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    for kill in(os.kill,os.killpg):
        try:kill(process['pid'],0)
        except ProcessLookupError:pass
        else:raise AssertionError('Original process/group unexpectedly exists')
    assert sha(own)==own_sha and sha(SOURCE)==SOURCE_SHA and sha(INDEX)==INDEX_SHA and sha(INVENTORY)==INVENTORY_SHA
    for name,digest in before.items():assert sha(ROOT/name)==digest
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('wmo-geometry0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    (out/'reviewer-source.py').write_bytes(own.read_bytes())
    (out/'asset-source-recheck.json').write_text(json.dumps(dict(archives={k:v[2]for k,v in archives.items()},files=asset_rows),indent=2)+'\n')
    (out/'case-recomputation.json').write_text(json.dumps(summaries,indent=2)+'\n')
    (out/'original-wat-identities.json').write_text(json.dumps(wat_rows,indent=2)+'\n')
    review=dict(status='passed_scoped_independent_read_only_review',receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,
        reviewer_sha256=own_sha,source_closure_exact=7,current_and_frozen_sources_verified=True,
        cases=425,original_explicit_calls=830,new_original_cases=0,original_or_browser_executed_by_reviewer=False,author_model_executed_by_reviewer=False,
        counts=dict(counts),mpq_header_tables_payloads_independently_verified=True,asset_inventory_sha256=INVENTORY_SHA,resource_index_sha256=INDEX_SHA,
        original_WAT_SQLite_profile_sha256=PROFILE_INDEX_SHA,section7_only_original_bodies_signatures_preserved=True,expected_separate_from_original_inputs=True,
        raw160_predicted_scope='Root tag/count(+0,+40);group three Vec headers+active arrays and+152/+156 flags/type internally crosschecked. Pointer values/other160B bytes retained observations,not independently predicted.',
        collision_recomputed='Raw XYZ words;MOPY first-byte mask filtering;first-use source-index ordering and group-local map reset;fullu32 destination indices;prefix65537 retained.',
        original_hash_initialization='425fresh states0->1;original60913/60916->81334 retained;runner has no state/snapshot injection. Seed values observed,not independently predicted.',
        runtime=dict(pid=20841,pgid=20841,exit_code=0,pid_and_group_missing=True,denied_imports=878,actual_host_calls=0,memory_cap_bytes=33554432,actual_max_memory_bytes=19202048),
        evidence_files={p.name:sha(p)for p in out.iterdir()},
        limitations=['CanonicalactualREVM17 collisionprojections only;not full160B WMO parser/material/BSP/doodad/render/error handling.',
            'Rootgroup path/count planning is local pure computation,not9513/VFS/original aggregate loader differential.',
            'Original830calls remainauthorreceiptcoverage;this review adds0 originalcases.',
            'OldWindowsMPQ sourceproof isnot latest135completeassetequivalence,independentworldproduction,6730/1089/fullgame acceptance.',
            'Allocator unusedtails,physicaladdresses andunmodeled160B fields remainraw observations,notzero expectations.'])
    target=out/'review.json';target.write_text(json.dumps(review,indent=2)+'\n');wrapper=dict(review,review_path=str(target.relative_to(ROOT)),review_sha256=sha(target))
    (ROOT/'reports/2026-11-01-wmo-geometry0135-independent-review.json').write_text(json.dumps(wrapper,indent=2)+'\n')
    (ROOT/'reports/2026-11-01-wmo-geometry0135-independent-review.md').write_text(f'''# 0.135.1 WMO碰撞投影独立只读复核

[作者最终收据](../{receipt_path.relative_to(ROOT)})通过限定域独审：425组、830次显式原1510/4464入口，新增原件案例0。[review](../{target.relative_to(ROOT)}) SHA `{sha(target)}`。没有执行原件、浏览器或作者WMO模型。

从固定patch.MPQ重新读全部410文件；独立解密并核hash/block表、MPQ32B头、实际文件名hash、SQLite行与原始offset/payload SHA。23root、387group，987,600原顶点/3,168,786个u16索引；独立按flags过滤与首次出现次序重算459,261顶点/1,051,449个u32索引，所有受控追加亦逐字匹配。65,537顶点前缀与大于65,535的目的索引完整保留。

30,932,188B已知几何严格比较；14,196,304B未写allocator尾段单列未知，其中832,181B非零。完整160B原输出保留；独立范围是root标签/组数、group三组几何Vec与+152/+156字段，指针和其它字段仅作原始观察，未声称完整160B解析对象已恢复。

7源闭包、只读SQLite定点11函数WAT、函数签名/body、section7仅增两导出、expected分离、原hash真实0→1及878导入全拒绝/实际0均核对。峰值19,202,048B、32MiB上限；PID/PGID20841退出0且均缺失，无snapshot/Once注入。

root路径规划未算作9513/VFS差分。旧Windows MPQ身份不等于最新135全部资产等价；完整WMO、world/6730/1089与完整一局仍需后续验证。
''')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),status=review['status'],counts=dict(counts))))


if __name__=='__main__':main()
