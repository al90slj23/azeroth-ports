#!/usr/bin/env python3
"""Read-only audit of frozen query/position original receipts; never run WASM.

Replays frozen specification inputs and independently checks nearest selection,
snapshot layout, export-only identity, raw Game bytes and component fixtures.
The source input seed helper gap is reported separately from production closure.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import argparse, hashlib, json, math, os, sqlite3, struct, sys
sys.dont_write_bytecode = True
from build_full135_oracle import ROOT, SOURCE, SOURCE_SHA, parse_source, section_list, export_entries
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.path.insert(0, str(ROOT/'reconstruction'))
from core_spec import binary32 as F
from core_spec.world_position135 import (WorldPositionInput135, DistanceMap135,
    sample_spawn_position, sample_random_position)
from resource_spec.terrain135 import HeightRaster135, sample_terrain
from resource_spec.world_query135 import WorldQueries135, NavGrid135, decode_world_snapshot

QUERY = ROOT/'evidence/world-snapshot0135-oracle-20261101T100514.012707Z'
POSITION = ROOT/'evidence/world-snapshot0135-oracle-20261101T102145.966200Z'
RECEIPTS = {'query':'24427929f2419ed3343f05e3bbcb35ed19cc3df3bf7062bc3018abc58159a720',
    'position':'583fc27a56155963d25e90d49da031bddda1df009fbecada6200b0846f81c1eb'}
SNAPSHOT = ROOT/'evidence/entry-world0135-probe-20261101T092959.623703Z/after_real_world6730.memory'
SNAPSHOT_SHA = 'f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
PROFILE = ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WORLD, GAME, STACK = 26204808, 14554176, 1048576


def read(path): return json.loads(path.read_text())
def digest(raw): return hashlib.sha256(raw).hexdigest()
def normalized(value): return json.loads(json.dumps(value))
def words(raw): return list(struct.unpack('<'+'I'*(len(raw)//4), raw))
def process_gone(pid):
    try: os.kill(pid, 0)
    except ProcessLookupError: return True
    return False


def validate_batch(directory, name, original):
    receipt_path = directory/f'world-{name}135-comparison.json'
    assert sha(receipt_path) == RECEIPTS[name]
    r = read(receipt_path)
    assert r['original_sha256'] == SOURCE_SHA and r['snapshot_sha256'] == SNAPSHOT_SHA
    before = r.get('source_before', r.get('source_sha256_before'))
    after = r.get('source_after', r.get('source_sha256_after'))
    assert before == after
    for path, identity in before.items():
        assert sha(ROOT/path) == identity == sha(directory/'source-snapshot'/path), path
    for path, identity in r['artifacts'].items(): assert sha(directory/path) == identity, path
    assert r['process']['exit_code'] == 0 and process_gone(r['process']['pid'])
    assert '--wasm-max-mem-pages=4096' in r['process']['command']
    assert r['process']['seconds'] < r['process']['deadline_seconds'] == 60
    manifest = read(directory/'manifest.json')
    changed = (directory/manifest['module_file']).read_bytes()
    assert digest(changed) == manifest['module_sha256']
    a, b = section_list(original), section_list(changed)
    assert [x[0] for x in a] == [x[0] for x in b] and not any(x[0] == 8 for x in a)
    for x, y in zip(a, b):
        if x[0] != 7: assert original[x[1]:x[3]] == changed[y[1]:y[3]]
    global_section = next(x for x in a if x[0] == 6)
    assert original[global_section[2]:global_section[3]].hex() == '017f01418080c0000b'
    old, _ = export_entries(original, next(x for x in a if x[0] == 7))
    new, _ = export_entries(changed, next(x for x in b if x[0] == 7))
    expected_adds = [(x['export'], 0, x['index']) for x in manifest['roles']]+[('research_snapshot135_stack', 3, 0)]
    assert new == old+expected_adds
    types, imports, decls, bodies, _ = parse_source(original)
    assert len(imports) == 878
    for role in manifest['roles']:
        index = role['index']; start, end = bodies[index]
        assert digest(original[start:end]) == role['body_sha256']
        assert tuple(x.hex() for x in types[decls[index-len(imports)]]) == (role['parameters_hex'], role['results_hex'])
    assert digest(original[slice(*bodies[91941])]) == manifest['original_allocator']['body_sha256']
    assert manifest['kind'] == 'snapshot-derived-world-consumers-not-bootstrap'
    assert manifest['memory_page_cap'] == 4096 and manifest['only_changed_section'] == 7
    return r, dict(receipt=str(receipt_path.relative_to(ROOT)), receipt_sha256=sha(receipt_path),
        source_count=len(before), source_identity_verified=True, artifact_count=len(r['artifacts']),
        all_nonexport_bytes_identical=True, unique_mutable_global0=STACK,
        roles=[x['index'] for x in manifest['roles']], original_callees_preserved=True,
        process_pid=r['process']['pid'], process_exit=0, process_confirmed_missing=True)


def independent_ranges(memory):
    out=[]
    def take(label, ptr, size):
        assert ptr >= 0 and ptr+size <= len(memory)
        data=memory[ptr:ptr+size]
        out.append(dict(label=label, offset=ptr, bytes=size, sha256=digest(data)))
        return data
    w=words(take('worldRc124', WORLD, 124))
    tiles=take('tiles36', w[3], w[4]*36)
    take('tileBounds16', w[6], w[7]*16)
    assert w[2]>=w[4]==9 and w[5]>=w[7]==9
    for j in range(9):
        t=words(tiles[j*36:(j+1)*36]);assert t[0]>=t[2]==256
        chunks=take(f'tile{j}.chunks264', t[1], t[2]*264)
        for k in range(256):
            c=words(chunks[k*264:(k+1)*264]);assert c[0]>=c[2]==145
            take(f'tile{j}.chunk{k}.vertices', c[1], c[2]*12)
    assert w[14]==0xffffffff and w[23]!=0xffffffff
    assert w[25]==w[28]*w[28]==313600 and w[10]==w[13]*w[13]==78400
    take('secondaryRaster',w[24],w[25]*4);nav=take('navBytes',w[9],w[10])
    assert Counter(nav)=={0:72996,1:5404}
    assert w[29]==F.from_float(68) and memory[WORLD+120]==0
    assert F.to_float(w[11])==-9536 and F.to_float(w[12])==-773
    assert w[11:13]==w[26:28]
    return out


def nearest_reference(c):
    r=c['raster'];width=r['width'];values=r['values_bits'];ox,oy=r['origin_xy_bits']
    cx=math.floor(F.to_float(F.mul(F.sub(c['x_bits'],ox),F.from_float(2))))
    cy=math.floor(F.to_float(F.mul(F.sub(c['y_bits'],oy),F.from_float(2))))
    for radius in range(21):
        candidates=[]
        for dy in range(-radius,radius+1):
            for dx in range(-radius,radius+1):
                x,y=cx+dx,cy+dy
                if max(abs(dx),abs(dy))!=radius or not(0<=x<width and 0<=y<width):continue
                index=y*width+x
                if index>=len(values):return dict(entry_status='bounds_trap',output16_hex='a5'*16)
                if not F.is_nan(values[index]):candidates.append((dx*dx+dy*dy,dy,dx,x,y,values[index]))
        if candidates:
            _,_,_,x,y,h=min(candidates)
            xyz=[F.add(ox,F.mul(F.add(F.from_u32(x),F.from_float(.5)),F.from_float(.5))),
                 F.add(oy,F.mul(F.add(F.from_u32(y),F.from_float(.5)),F.from_float(.5))),h]
            return dict(entry_status='returned',output16_hex=struct.pack('<4I',1,*xyz).hex())
    return dict(entry_status='returned',output16_hex=struct.pack('<I',0).hex()+'a5'*12)


def check_query(directory, receipt, summary, memory, world, ranges):
    inp=read(directory/'world-query135-inputs.json');cases=inp['queries']
    assert set(inp)=={'snapshot_path','snapshot_sha256','world_rc','queries'}
    assert inp['snapshot_sha256']==SNAPSHOT_SHA and Path(inp['snapshot_path'])==SNAPSHOT and inp['world_rc']==WORLD
    expected=read(directory/'world-query135-expected.json')
    actual=[json.loads(x) for x in (directory/'world-query135-results.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(actual)==959
    assert read(directory/'world-query135-source-ranges.json')==ranges
    counts=Counter();differences=[]
    for c,e,a in zip(cases,expected,actual):
        assert c['id']==e['id']==a['id']
        counts[c['kind']]+=1
        clean={k:v for k,v in a.items() if k!='error'}
        assert clean==e
        if c['kind']=='nearest':
            assert set(c)=={'id','group','kind','x_bits','y_bits','raster'}
            reference=nearest_reference(c)
            assert all(a[k]==v for k,v in reference.items()),c['id']
            counts['nearest_bounds_traps']+=a['entry_status']=='bounds_trap'
        else:
            assert set(c)=={'id','group','kind','x_bits','y_bits'}
            for role,sample in [('terrain_height',sample_terrain(world.tiles,c['x_bits'],c['y_bits'])),
                                ('world_height',world.height(c['x_bits'],c['y_bits']))]:
                output=a['output'][role]
                assert output['found']==sample.found and output['value_bits']==sample.value_bits
                assert output['output16_hex']==struct.pack('<II',int(sample.found),sample.value_bits).hex()+'a5'*8
            t,w=a['output']['terrain_height'],a['output']['world_height']
            counts['legal_height_misses']+=not w['found']
            counts['real_secondary_lifts']+=t['found'] and w['found'] and F.to_float(w['value_bits'])>F.to_float(t['value_bits'])
    assert counts=={'height':899,'nearest':60,'nearest_bounds_traps':1,'legal_height_misses':47,'real_secondary_lifts':96}
    rt=read(directory/'world-query135-runtime.json');assert rt==receipt['runtime']
    assert rt['calls']==1858 and rt['fresh_instances']==2 and rt['bounds_traps']==1
    assert rt['actual_host_calls']==0 and rt['denied_imports']==878 and rt['memory_page_cap']==4096
    assert rt['max_memory_bytes']==len(memory) and rt['stack_after']==STACK
    assert rt['world_ranges_verified_unchanged']==ranges
    assert len(rt['verified_world_instances'])==2
    for item in rt['verified_world_instances']:assert item['ranges']==ranges
    calls=[x for x in rt['entry_calls'] if x['role']!='original_allocator']
    assert len(calls)==1858
    traps=[j for j,x in enumerate(rt['entry_calls']) if x.get('returned') is False]
    assert len(traps)==1
    j=traps[0];assert rt['entry_calls'][j]['stack_after']==1048448
    assert rt['entry_calls'][j+1]['role']=='original_allocator' and rt['entry_calls'][j+1]['stack_after']==STACK
    for x in calls:
        assert x['stack_before']==STACK
        if x.get('returned'):assert x['stack_after']==STACK
    local=read(directory/'world-query135-nav-local-replay.json')
    assert local['original_executed'] is False and len(local['cases'])==79
    assert len(receipt['source_before'])==16
    summary.update(status='passed',counts=dict(counts),original_calls=1858,
        independently_checked_nearest_cases=60,world_input_ranges=2318,
        separate_local_navigation_replay=79,local_navigation_new_original_calls=0,
        snapshot_input_adapter_not_producer=True,full_snapshot_restored_instances=2,
        expected_bounds_trap_instance_discarded=True)
    return summary


def explicit_world(desc):
    def raster(v):return None if v is None else HeightRaster135(tuple(v['values_bits']),tuple(v['origin_xy_bits']),v['width'])
    v=desc['nav'];nav=None if v is None else NavGrid135(bytes.fromhex(v['values_hex']),tuple(v['origin_xy_bits']),v['width'])
    return WorldQueries135((),raster(desc['primary']),raster(desc['secondary']),nav,desc['fallback_height_bits'],desc['flat_height_bits'])


def check_position(directory, receipt, summary, memory, world):
    fixture=read(directory/'world-position135-fixtures.json');inputs=read(directory/'world-position135-inputs.json')
    actual=[json.loads(x) for x in (directory/'world-position135-results.jsonl').read_text().splitlines()]
    assert len(fixture)==len(inputs)==len(actual)==96
    counts=Counter();all_arrays=0;mutation_bytes=0
    for c,i,a in zip(fixture,inputs,actual):
        assert i=={k:c[k] for k in ('id','group','kind','input','world')}
        assert c['id']==a['id'] and c['expected']==a['projection']
        state=dict(i['input'])
        for k in ('player_xyz','velocity_xy','rng_words'):state[k]=tuple(state[k])
        m=state['distance_map'];state['distance_map']=None if m is None else DistanceMap135(tuple(m['values_u16']),m['field24'])
        state=WorldPositionInput135(**state);geometry=world if i['world'] is None else explicit_world(i['world'])
        model=(sample_spawn_position if i['kind']=='spawn' else sample_random_position)(state,geometry)
        assert normalized(dict(position_bits=model.position_bits,rng_words=model.rng_words))==a['projection']
        assert normalized(model.__dict__)==c['diagnostic']
        counts['real' if i['world'] is None else 'controlled']+=1
        before,after=bytes.fromhex(a['raw_game_before_hex']),bytes.fromhex(a['raw_game_after_hex'])
        assert len(before)==len(after)==2592
        wb,wa=words(before),words(after)
        changes=[[j*4,v] for j,v in enumerate(wa) if v!=wb[j]]
        assert changes==a['game_changes']
        assert {x[0] for x in changes} <= {1720,1724,1728,1732}
        assert wa[430:434]==a['projection']['rng_words']
        assert wb[354:357]==i['input']['player_xyz'] and wb[430:434]==i['input']['rng_words']
        assert wb[434:436]==i['input']['velocity_xy']
        assert a['output16_hex']==struct.pack('<3I',*a['projection']['position_bits']).hex()+'a5'*4
        assert a['world_record_before_hex']==a['world_record_after_hex']
        record=bytes.fromhex(a['world_record_before_hex']);assert len(record)==124
        if i['world'] is None:assert record==memory[WORLD:WORLD+124] and wb[587]==WORLD
        else:
            d=i['world'];rw=words(record);assert rw[:2]==[1,1] and rw[4]==rw[7]==0
            assert bool(record[120])==(d['flat_height_bits'] is not None)
            assert rw[29]==(d['fallback_height_bits'] if d['flat_height_bits'] is None else d['flat_height_bits'])
            expected_record=bytearray(124)
            def put(offset,value):struct.pack_into('<I',expected_record,offset,value)
            put(0,1);put(4,1);put(12,4);put(24,4)
            for offset in (32,56,92):put(offset,0xffffffff)
            put(116,d['fallback_height_bits'] if d['flat_height_bits'] is None else d['flat_height_bits'])
            expected_record[120]=int(d['flat_height_bits'] is not None)
            ai=iter(a['arrays_unchanged'])
            if d['nav'] is not None:
                n=d['nav'];meta=next(ai)
                for o,v in ((32,meta['n']),(36,meta['p']),(40,meta['n']),(44,n['origin_xy_bits'][0]),(48,n['origin_xy_bits'][1]),(52,n['width'])):put(o,v)
            for name,tag,ptr,size,origin,width in [('primary',56,72,76,80,88),('secondary',92,96,100,104,112)]:
                n=d[name]
                if n is None:continue
                meta=next(ai)
                for o,v in ((tag,0),(ptr,meta['p']),(size,len(n['values_bits'])),(origin,n['origin_xy_bits'][0]),(origin+4,n['origin_xy_bits'][1]),(width,n['width'])):put(o,v)
            assert record==expected_record
        # Every undeclared Game setup byte must retain the true snapshot value.
        expected_before=bytearray(memory[GAME:GAME+2592])
        for offset,values in ((1416,i['input']['player_xyz']),(1736,i['input']['velocity_xy']),(1720,i['input']['rng_words'])):
            struct.pack_into('<'+'I'*len(values),expected_before,offset,*values)
        for offset in (2348,2368):struct.pack_into('<I',expected_before,offset,wb[offset//4])
        assert expected_before==before
        allocators=[x for x in a['calls'] if x['role']=='original_allocator']
        if i['world'] is not None:assert allocators[0]['size']==124 and allocators[0]['pointer']==wb[587]
        if m is None:assert wb[592]==0
        else:assert any(x['size']==32 and x['pointer']==wb[592] for x in allocators)
        payloads=[]
        if i['world'] is not None:
            d=i['world']
            if d['nav'] is not None:payloads.append(bytes.fromhex(d['nav']['values_hex']))
            for name in ('primary','secondary'):
                if d[name] is not None:payloads.append(struct.pack('<'+'I'*len(d[name]['values_bits']),*d[name]['values_bits']))
        if m is not None:payloads.append(struct.pack('<'+'H'*len(m['values_u16']),*m['values_u16']))
        assert len(payloads)==len(a['arrays_unchanged'])
        for payload,meta in zip(payloads,a['arrays_unchanged']):
            assert meta['n']==len(payload) and meta['sha256']==digest(payload)
        all_arrays+=len(payloads);mutation_bytes+=2592
        assert a['stack_after']==STACK and a['snapshot']['sha256']==SNAPSHOT_SHA
        assert a['snapshot']['bytes']==len(memory) and a['snapshot']['mutable_globals']==1
        calls=[x for x in a['calls'] if x['role']!='original_allocator']
        assert len(calls)==1 and calls[0]['index']==(8751 if i['kind']=='spawn' else 13516)
        assert calls[0]['returned'] and calls[0]['stack_before']==calls[0]['stack_after']==STACK
    assert counts=={'real':58,'controlled':38}
    # Actual full-body outputs distinguish the key controlled branches.
    lookup={}
    for c,a in zip(fixture,actual):
        if c['group']=='controlled-nav-byte':
            v=c['world']['nav'];lookup[(None if v is None else bytes.fromhex(v['values_hex'])[0],c['kind'])]=(c,a)
    for byte in (2,255):
        assert lookup[(byte,'spawn')][0]['diagnostic']['attempts']==1
        assert lookup[(byte,'random')][0]['diagnostic']['attempts']==13
        assert lookup[(byte,'spawn')][1]['projection']!=lookup[(byte,'random')][1]['projection']
    assert lookup[(1,'spawn')][0]['diagnostic']['radius_shrinks']>0
    cost_cases=[x for x in fixture if x['group']=='controlled-distance-map' and bytes.fromhex(x['world']['nav']['values_hex'])[0]==0]
    assert len(cost_cases)==6
    for c in cost_cases:
        m=c['input']['distance_map'];diagnostic=c['diagnostic']
        assert (diagnostic['attempts']==1)==(m['field24']==400 or m['values_u16'][0]==0)
    last=actual[-1]['projection']['position_bits'];previous=actual[-2]['projection']['position_bits']
    assert last[:2]==previous[:2] and last[2]==F.from_float(77) and previous[2]==F.from_float(99)
    nearest=nearest_reference(dict(raster=inputs[-1]['world']['primary'],x_bits=last[0],y_bits=last[1]))
    nearest_xyz=words(bytes.fromhex(nearest['output16_hex']))[1:]
    assert nearest_xyz[2]==last[2] and nearest_xyz[:2]!=last[:2]
    rt=read(directory/'world-position135-runtime.json');assert rt==receipt['runtime']
    assert rt['cases']==rt['original_calls']==96 and rt['game_bytes_invariance_checked']==mutation_bytes==248832
    assert rt['host_calls']==0 and rt['denied_function_imports']==878 and rt['max_memory_bytes']==len(memory)
    assert rt['memory_page_cap']==4096 and not rt['real_bootstrap_reexecuted']
    declared=receipt['source_sha256_before']
    missing=sorted(set(core_sources(ROOT,'initial_state135.py'))-set(declared))
    assert set(core_sources(ROOT,'world_position135.py')) <= set(declared)
    if not missing:
        from check_world_position135 import corpus
        assert corpus(world,False)==fixture
    correction=directory/'source-closure-correction.json'
    correction_summary=None
    if correction.is_file():
        assert sha(correction)=='4e40c6dffd44af1a86395c61089de7d23363a0197d36d0a65fa40d356e70f23e'
        fix=read(correction);old=ROOT/'evidence'/fix['old_receipt']
        assert sha(old)==fix['old_receipt_sha256'] and sha(directory/'world-position135-comparison.json')==fix['new_receipt_sha256']
        assert fix['old_sources']==21 and fix['new_sources']==len(declared)==30
        for filename,identical in fix['byte_identical_artifacts'].items():
            assert identical and (old.parent/filename).read_bytes()==(directory/filename).read_bytes()
        correction_summary=dict(path=str(correction.relative_to(ROOT)),sha256=sha(correction),
            old_receipt_sha256=sha(old),old_sources=21,new_sources=30,
            four_artifacts_independently_byte_equal=True,counts_not_added=True)
    summary.update(status='passed_with_fixture_generator_scope_gap' if missing else 'passed',
        counts=dict(counts),original_calls=96,all_raw_game_bytes_compared=mutation_bytes,
        only_mutable_game_offsets=[1720,1724,1728,1732],controlled_array_payload_hashes_rederived=all_arrays,
        controlled_array_postcall_integrity='frozen original runner rehash assertion; postcall payloads not separately dumped',
        production_import_closure_verified=True,fixture_generator_unfrozen_imports=missing,
        full_seed_fixture_regenerated_without_original=not missing,
        source_closure_correction=correction_summary,
        nearest_supplies_only_z=True,nav_predicates_distinct=True,path_field24_threshold=401,
        model_replay_is_not_new_original_cases=True,snapshot_input_not_independent_world_producer=True)
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--position-directory',type=Path,default=POSITION)
    p.add_argument('--position-receipt-sha256',default=RECEIPTS['position']);args=p.parse_args()
    args.position_directory=args.position_directory.resolve()
    RECEIPTS['position']=args.position_receipt_sha256
    original=SOURCE.read_bytes();assert digest(original)==SOURCE_SHA
    assert sha(SNAPSHOT)==SNAPSHOT_SHA;memory=SNAPSHOT.read_bytes();assert len(memory)==117440512
    source_before={str(Path(__file__).relative_to(ROOT)):sha(Path(__file__))}
    query,qr=validate_batch(QUERY,'query',original)
    position,pr=validate_batch(args.position_directory,'position',original)
    declared={**query['source_before'],**position['source_sha256_before']}
    imported_extra={x:sha(ROOT/x) for x in core_sources(ROOT,'initial_state135.py') if x not in declared}
    all_before={**source_before,**declared,**imported_extra}
    ranges=independent_ranges(memory);assert len(ranges)==2318
    world=decode_world_snapshot(memory,WORLD)
    qr=check_query(QUERY,query,qr,memory,world,ranges)
    pr=check_position(args.position_directory,position,pr,memory,world)
    # Indexed seek only; no full1.3GB WAT read and no original execution.
    index=PROFILE/'index.sqlite'
    assert sha(index)=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
    con=sqlite3.connect(f'file:{index}?mode=ro',uri=True);wat={}
    with (PROFILE/'official-0.135.1-full.wat').open('rb') as fh:
        for idx in (6730,23181,8751,13516):
            start,end=con.execute('SELECT wat_start,wat_end FROM functions WHERE idx=?',(idx,)).fetchone()
            fh.seek(start);raw=fh.read(end-start);wat[idx]=dict(start=start,end=end,sha256=digest(raw),lines=raw.count(b'\n'))
            if idx==6730:assert b'i32.const 3712' in raw
            if idx==8751:assert b'i32.const 401' in raw and b'i32.const 16' in raw and b'call 13516' in raw
            if idx==13516:assert b'i32.const 12' in raw and b'call 23181' in raw
            if idx==23181:assert b'i32.const 20' in raw and b'i32.gt_s' in raw
    con.close()
    assert all(sha(ROOT/x)==h for x,h in all_before.items())
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-consumers0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    for path,h in all_before.items():
        dst=out/'source-snapshot'/path;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/path).read_bytes());assert sha(dst)==h
    report=dict(status='passed' if pr['status']=='passed' else 'passed_with_scope_gap',version='0.135.1',build='0898d5e3',
        original_wasm_sha256=SOURCE_SHA,snapshot_sha256=SNAPSHOT_SHA,snapshot_bytes=len(memory),
        query=qr,position=pr,indexed_original_wat=wat,reviewer_source_sha256=source_before,
        reviewed_source_sha256=declared,additional_current_seed_generator_sources=imported_extra,
        original_executed=False,new_original_cases=0,source_files_modified=False,
        scope=['Read-only existing original receipts and independent frozen-spec replay.',
               'Neither snapshot adapter nor controlled component fixture is a world producer.',
               'Game full2592 bytes are independently rechecked from raw; arrays have input SHA plus frozen runner postcall rehash, not separate postcall full-memory capture.',
               'No main-slice integration, new bootstrap, complete game or global restoration claim.'])
    target=out/'review.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),status=report['status'],
        query_status=qr['status'],position_status=pr['status'],fixture_gap=pr['fixture_generator_unfrozen_imports'])))


if __name__=='__main__':main()
