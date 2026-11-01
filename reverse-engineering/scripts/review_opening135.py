#!/usr/bin/env python3
"""Read-only full-opening audit: frozen pure replay and independent raw checks.

Never instantiate WASM. Query-world snapshots are explicit resolved inputs;
consumer replay and captured original calls are counted separately.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,os,sqlite3,struct,sys
sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import sha
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.opening135 import EmptyOpeningInput135,initialize_empty_opening,projection
from resource_spec.world_query135 import decode_world_snapshot

BATCH=ROOT/'evidence/world-snapshot0135-oracle-20261101T103934.606037Z'
RECEIPT_SHA='91de74157f822199071a0998d02b40354de124fe9a823ff4d688da47b6520b72'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
WORLD,APP=26204808,14549000
LAYOUTS={'companions':(2108,2112,2116,88),'units':(1784,1788,1792,424),
 'pickups':(1868,1872,1876,56),'special':(1916,1920,1924,40),
 'windows':(1964,1968,1972,8),'boundaries':(2120,2124,2128,8)}
# Independent actual-write boundary inventory, not imported checker masks.
WRITES={'companions':((0,8),(16,5),(24,64)),
 'units':((0,4),(8,4),(16,4),(40,4),(64,4),(112,136),(280,139)),
 'pickups':((0,4),(8,48)),'special':((0,8),(16,20)),
 'windows':((0,8),),'boundaries':((0,8),)}


def read(p):return json.loads(p.read_text())
def digest(b):return hashlib.sha256(b).hexdigest()
def u(b,p):return struct.unpack_from('<I',b,p)[0]
def q(b,p):return struct.unpack_from('<Q',b,p)[0]
def normal(v):return json.loads(json.dumps(v))


def independent_closure():
    pending=[ROOT/'scripts/check_opening135.py'];seen=set()
    def add(name,package=None):
        if package:target=package.joinpath(*name.split('.'))
        elif name.startswith(('core_spec','resource_spec')):target=(ROOT/'reconstruction').joinpath(*name.split('.'))
        else:target=(ROOT/'scripts').joinpath(*name.split('.'))
        path=target.with_suffix('.py')
        if not path.exists():
            path=target/'__init__.py'
            if not path.exists():return
        pending.append(path)
        if 'reconstruction'in path.parts:pending.append(ROOT/'reconstruction'/path.relative_to(ROOT/'reconstruction').parts[0]/'__init__.py')
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path)
        for n in ast.walk(ast.parse(path.read_text())):
            if isinstance(n,ast.Import):
                for alias in n.names:add(alias.name)
            elif isinstance(n,ast.ImportFrom):
                if n.level:
                    assert n.level==1
                    if n.module:add(n.module,path.parent)
                    else:
                        for alias in n.names:add(alias.name,path.parent)
                else:
                    add(n.module or '')
                    if n.module in('core_spec','resource_spec'):
                        for alias in n.names:add(n.module+'.'+alias.name)
    seen.update((ROOT/'scripts/run_opening135_oracle.mjs',ROOT/'scripts/world_snapshot135_host.mjs'))
    return {str(p.relative_to(ROOT))for p in seen}


def decode_create(payload):
    at=0
    def take(n):
        nonlocal at
        out=payload[at:at+n];assert len(out)==n;at+=n;return out
    def word():return int.from_bytes(take(4),'little')
    assert word()==1 and take(1)==b'\0'
    block=take(1)[0];mask=take(1)[0];guid_bytes=bytearray(8)
    for i in range(8):
        if mask>>i&1:guid_bytes[i]=take(1)[0]
    guid=int.from_bytes(guid_bytes,'little');kind,flags=take(2)
    if kind==3:assert(block,flags,word(),word())==(3,112,0,0)
    else:assert(kind,block,flags)==(5,2,80)
    xyz=[word()for _ in range(3)];heading=word()
    if kind==3:
        assert word()==0
        speeds=[word()for _ in range(6)]
    assert word()==1
    count=take(1)[0];masks=[word()for _ in range(count)];fields={}
    for i,mask in enumerate(masks):
        for j in range(32):
            if mask>>j&1:fields[i*32+j]=word()
    assert at==len(payload)and fields[0]==guid&0xffffffff and fields[1]==guid>>32
    return dict(guid=guid,kind=kind,xyz=xyz,heading=heading,fields=fields)


def banner_reference():
    title=b'Elwynn Forest';subtitle='The Defias Uprising — survive the onslaught!'.encode()
    return b'Z'+struct.pack('<II',0,len(title)+1)+title+b'\0'+bytes(8)+struct.pack('<I',len(subtitle)+1)+subtitle+b'\0\0'


def queue_check(capture,name,game):
    co,po,no,stride=(1880,1884,1888,16)if name=='packets'else(1892,1896,1900,12)
    value=capture[name];metadata=bytes.fromhex(value['metadata_backing_hex'])
    assert [value[k]for k in('capacity','pointer','count')]==[u(game,o)for o in(co,po,no)]
    assert len(metadata)==value['capacity']*stride and value['count']==len(value['active'])<=value['capacity']
    assert 0<=value['pointer']and value['pointer']+len(metadata)<=capture['memory_bytes']
    for j,row in enumerate(value['active']):
        raw=bytes.fromhex(row['metadata_hex']);backing=bytes.fromhex(row['backing_hex']);payload=bytes.fromhex(row['payload_hex'])
        assert raw==metadata[j*stride:(j+1)*stride]
        assert [row[k]for k in('capacity','pointer','length')]==[u(raw,o)for o in(0,4,8)]
        assert len(backing)==row['capacity'] and len(payload)==row['length'] and backing[:len(payload)]==payload
        assert 0<=row['pointer']and row['pointer']+len(backing)<=capture['memory_bytes']
        if name=='packets':assert row['opcode']==struct.unpack_from('<H',raw,12)[0]
    return value['active']


def main():
    own=Path(__file__);own_sha=sha(own);receipt_path=BATCH/'opening135-comparison.json'
    assert sha(receipt_path)==RECEIPT_SHA;receipt=read(receipt_path)
    before=receipt['source_sha256_before'];assert before==receipt['source_sha256_after']and len(before)==39
    assert independent_closure()==set(before)
    for name,identity in before.items():assert sha(ROOT/name)==identity==sha(BATCH/'source-snapshot'/name)
    for name,identity in receipt['artifacts'].items():assert sha(BATCH/name)==identity
    assert receipt['differences']==0 and receipt['expected_before_original']and not receipt['expected_in_original_input']
    original=SOURCE.read_bytes();assert digest(original)==SOURCE_SHA
    manifest=read(BATCH/'manifest.json');changed=(BATCH/manifest['module_file']).read_bytes()
    assert digest(changed)==manifest['module_sha256'];old,new=section_list(original),section_list(changed)
    assert [x[0]for x in old]==[x[0]for x in new]and not any(x[0]==8 for x in old)
    for a,b in zip(old,new):
        if a[0]!=7:assert original[a[1]:a[3]]==changed[b[1]:b[3]]
    ex,_=export_entries(original,next(x for x in old if x[0]==7));nx,_=export_entries(changed,next(x for x in new if x[0]==7))
    assert {r['index']for r in manifest['roles']}=={6730,1089}
    assert nx==ex+[(r['export'],0,r['index'])for r in manifest['roles']]+[('research_snapshot135_stack',3,0)]
    g=next(x for x in old if x[0]==6);assert original[g[2]:g[3]].hex()=='017f01418080c0000b'
    types,imports,decl,bodies,_=parse_source(original);assert len(imports)==878
    for r in manifest['roles']:
        a,b=bodies[r['index']];assert digest(original[a:b])==r['body_sha256']
        assert tuple(x.hex()for x in types[decl[r['index']-878]])==(r['parameters_hex'],r['results_hex'])
    runtime=read(BATCH/'opening135-runtime.json');assert runtime==receipt['runtime']
    assert runtime['original_calls']==32 and runtime['full_original6730_calls']==runtime['full_original1089_calls']==16
    assert runtime['host_calls']==0 and runtime['denied_imports']==878 and runtime['memory_cap_bytes']==268435456
    assert runtime['max_memory_bytes']==166395904 and runtime['fresh_bootstraps']==runtime['new_mainloop_frames']==0
    for key in('once_written','world_rc_forged','appstart_called','network_used','user_saves_accessed'):assert not runtime[key]
    process=receipt['process'];assert process['exit_code']==0 and not process['timed_out']and process['seconds']<60
    assert '--wasm-max-mem-pages=4096'in process['command']
    for method in(os.kill,os.killpg):
        try:method(process['pid'],0)
        except ProcessLookupError:pass
        else:raise AssertionError('Original process/group still live')
    model_source=receipt['model_world_snapshot'];original_source=receipt['original_snapshot']
    assert model_source['sha256']=='f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
    assert original_source['sha256']=='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
    model_memory=Path(model_source['path']).read_bytes();actual_memory=Path(original_source['path']).read_bytes()
    assert digest(model_memory)==model_source['sha256']and len(model_memory)==117440512
    assert digest(actual_memory)==original_source['sha256']and len(actual_memory)==166395904
    world=decode_world_snapshot(model_memory,WORLD);original_world=decode_world_snapshot(actual_memory,WORLD)
    assert world==original_world
    parity=read(BATCH/'opening135-world-input-parity.json');ranges=[]
    for label,address,size in world.source_ranges:
        if label=='word':continue
        if label=='worldRc124':address+=8;size-=8
        a=model_memory[address:address+size];b=actual_memory[address:address+size];assert a==b
        ranges.append(dict(label=label,address=address,bytes=size,sha256=digest(a)))
    assert ranges==parity['ranges']and len(ranges)==2318 and sum(x['bytes']for x in ranges)==5950600
    assert parity['model_snapshot_sha256']==model_source['sha256']and parity['original_snapshot_sha256']==original_source['sha256']
    fixture=read(BATCH/'opening135-fixtures.json');inputs=read(BATCH/'opening135-inputs.json');config=read(BATCH/'opening135-config.json')
    actual=[json.loads(line)for line in(BATCH/'opening135-results.jsonl').read_text().splitlines()]
    from check_opening135 import corpus
    assert corpus(world,False)==fixture
    assert len(fixture)==len(inputs)==len(actual)==16
    assert config['input_sha256']==sha(BATCH/'opening135-inputs.json')and config['snapshot_sha256']==original_source['sha256']
    assert config['app_pointer']==APP and config['world_pointer']==WORLD
    checker=(BATCH/'source-snapshot/scripts/check_opening135.py').read_text();runner=(BATCH/'source-snapshot/scripts/run_opening135_oracle.mjs').read_text()
    assert checker.index('fixture.write_text(')<checker.index('child=subprocess.Popen(')
    assert 'opening135-fixtures'in checker and 'opening135-fixtures'not in runner
    host=(BATCH/'source-snapshot/scripts/world_snapshot135_host.mjs').read_text()
    assert 'new Uint8Array(memory.buffer).set(snapshot)'in host and "throw Error('Snapshot original host import denied')"in host
    counts=Counter();vector_counts=Counter();window_counts=Counter();guid_samples=[]
    for case,inp,observed in zip(fixture,inputs,actual):
        assert inp=={k:case[k]for k in('id','input')}and set(inp['input'])=={'app_lcg_seed_u64','class_byte','object_id_u64','race_byte','region_index'}
        assert observed['id']==case['id'];s=inp['input'];raw=observed['raw'];G=raw['G']
        assert raw['App']==APP and raw['world_pointer']==WORLD
        app_before=bytes.fromhex(raw['app_before_declared_hex']);declared=bytes.fromhex(raw['app_after_declared_hex'])
        assert app_before==actual_memory[APP:APP+5168]
        predicted=bytearray(app_before);struct.pack_into('<Q',predicted,4928,int(s['app_lcg_seed_u64']));predicted[3720]=s['class_byte'];predicted[3721]=s['race_byte'];struct.pack_into('<Q',predicted,3552,int(s['object_id_u64']))
        assert predicted==declared and bytes.fromhex(raw['world_before_hex'])==actual_memory[WORLD:WORLD+124]
        ctor,final=raw['constructor'],raw['final'];ctorG=bytes.fromhex(ctor['raw_game2592_hex']);finalG=bytes.fromhex(final['raw_game2592_hex'])
        assert len(ctorG)==len(finalG)==2592 and ctor['phase2587']==ctorG[2587]==0 and final['phase2587']==finalG[2587]==1
        assert u(ctorG,1428)==u(finalG,1428)==0x3fcccccd
        assert ctor['counter2408']==u(ctorG,2408)==10 and final['counter2408']==u(finalG,2408)==87
        seed=(int(s['app_lcg_seed_u64'])*6364136223846793005+1442695040888963407)&((1<<64)-1)
        app_constructed=bytearray(declared);struct.pack_into('<Q',app_constructed,4928,seed)
        assert bytes.fromhex(ctor['raw_app5168_hex'])==bytes.fromhex(final['raw_app5168_hex'])==app_constructed
        assert int(ctor['app_lcg_seed_u64'])==int(final['app_lcg_seed_u64'])==seed
        rc_before=bytearray(bytes.fromhex(raw['world_before_hex']));strong=u(rc_before,0);struct.pack_into('<I',rc_before,0,strong+1)
        assert bytes.fromhex(ctor['raw_world_rc124_hex'])==bytes.fromhex(final['raw_world_rc124_hex'])==rc_before
        for capture,game in((ctor,ctorG),(final,finalG)):
            assert capture['world_cache_pointer']==capture['game_world_pointer']==u(game,2348)==WORLD
            assert capture['world_refcount']==strong+1 and capture['stack']==1048576
            assert list(struct.unpack_from('<4I',game,1720))==capture['rng_words']
            assert list(struct.unpack_from('<3I',game,1416))==capture['player_xyz']
            assert len(bytes.fromhex(capture['raw_app5168_hex']))==5168
            for name,(co,po,no,stride)in LAYOUTS.items():
                v=capture['vectors'][name]
                assert [v[k]for k in('capacity','pointer','count')]==[u(game,o)for o in(co,po,no)]
                assert v['stride']==stride and len(v['storage'])==v['capacity']
                assert all(len(bytes.fromhex(x))==stride for x in v['storage'])
                assert 0<=v['pointer']and v['pointer']+v['capacity']*stride<=capture['memory_bytes']
                if capture is ctor:assert v['count']==v['capacity']==0
            queue_check(capture,'packets',game);queue_check(capture,'notifications',game)
        model_input=EmptyOpeningInput135(s['class_byte'],s['race_byte'],s['region_index'],int(s['app_lcg_seed_u64']),int(s['object_id_u64']))
        model=initialize_empty_opening(model_input,world,title_utf8=b'Elwynn Forest',subtitle_utf8='The Defias Uprising — survive the onslaught!'.encode())
        expected=projection(model);assert expected==case['expected']
        assert expected['player_xyz']==final['player_xyz']and expected['rng_words']==final['rng_words']
        for name,(co,po,no,stride)in LAYOUTS.items():
            exp=expected[name];v=final['vectors'][name];projected=observed['projection'][name]
            assert projected=={k:v[k]for k in('capacity','count','storage')}
            assert exp['capacity']==v['capacity']and exp['count']==v['count']
            written={j for offset,length in WRITES[name]for j in range(offset,offset+length)}
            for slot,(eb,hexrow)in enumerate(zip(exp['storage'],v['storage'])):
                ab=bytes.fromhex(hexrow)
                assert len(eb)==len(ab)==stride
                if slot<exp['count']:assert {j for j,x in enumerate(eb)if x is not None}==written
                else:assert all(x is None for x in eb)
                for known,value in zip(eb,ab):
                    if known is None:
                        kind='active_unwritten'if slot<exp['count']else'inactive_allocator'
                        counts[kind+'_bytes']+=1;counts[kind+'_nonzero_bytes']+=value!=0
                    else:assert known==value;counts['strict_backing_bytes']+=1;counts['strict_active_bytes']+=slot<exp['count']
            vector_counts[name]+=v['count']
        prefix=observed['constructor_prefix'];prefix_packets=[dict(opcode=x['opcode'],payload_hex=x['payload_hex'])for x in ctor['packets']['active']]
        assert prefix['packets']==prefix_packets
        packet_all=[dict(opcode=x['opcode'],payload_hex=x['payload_hex'])for x in final['packets']['active']]
        assert packet_all[:len(prefix_packets)]==prefix_packets
        packets=packet_all[len(prefix_packets):];assert packets==expected['packets']==observed['projection']['packets']
        assert packets[0]==dict(opcode=150,payload_hex=banner_reference().hex())and len(packets)==78
        decoded=[decode_create(bytes.fromhex(x['payload_hex']))for x in packets[1:]]
        assert all(x['opcode']==169 for x in packets[1:])
        assert [x['kind']for x in decoded]==[3]*6+[5]*71
        vectors=final['vectors'];comp=[bytes.fromhex(x)for x in vectors['companions']['storage'][:2]]
        npcs=[bytes.fromhex(x)for x in vectors['units']['storage'][:4]];pickups=[bytes.fromhex(x)for x in vectors['pickups']['storage'][:2]]
        boundary=[bytes.fromhex(x)for x in vectors['boundaries']['storage'][:69]]
        physical_guids=[q(x,24)for x in comp]+[q(x,112)for x in npcs]+[q(x,16)for x in pickups]+[q(x,0)for x in boundary]
        assert [x['guid']for x in decoded]==physical_guids and len(set(physical_guids))==77
        for p,row in zip(decoded[:2],comp):assert p['xyz']==list(struct.unpack_from('<3I',row,44))and p['heading']==u(finalG,1428)
        for p,row in zip(decoded[2:6],npcs):
            assert p['xyz']==list(struct.unpack_from('<3I',row,316))
            assert p['fields'][16]|(p['fields'][17]<<32)==int(s['object_id_u64'])
        for p,row,amount in zip(decoded[6:8],pickups,(2,1)):
            assert p['xyz']==list(struct.unpack_from('<3I',row,40))and p['fields'][3]==9005
            assert(u(row,8),u(row,12))==(2,amount)
        assert all(p['fields'][3]==9013 for p in decoded[8:])
        new_notify=[x['payload_hex']for x in final['notifications']['active'][len(ctor['notifications']['active']):]]
        assert new_notify==expected['notifications_utf8_hex']==[b'{"type":"start"}'.hex()]==observed['projection']['notifications_utf8_hex']
        for k in('phase2587','counter2408','rng_words','player_xyz'):assert observed['projection'][k]==expected[k]
        calls=[x for x in observed['calls']if x['role']!='original_allocator']
        assert [x['index']for x in calls]==[6730,1089]
        assert all(x['returned']and x['stack_before']==x['stack_after']==1048576 for x in calls)
        assert observed['snapshot']['sha256']==original_source['sha256']and observed['snapshot']['bytes']==166395904
        counts['opening_packets']+=len(packets);counts['opening_packet_bytes']+=sum(len(x['payload_hex'])//2 for x in packets)
        counts['notifications']+=len(new_notify);counts['constructor_prefix_packets']+=len(prefix_packets)
        window_counts[final['vectors']['windows']['count']]+=1
        if prefix_packets:assert case['id']==10 and [x['opcode']for x in prefix_packets]==[226]
    assert dict(counts)==receipt['comparison']
    assert counts['strict_backing_bytes']+counts['active_unwritten_bytes']+counts['inactive_allocator_bytes']==55808
    assert vector_counts=={'companions':32,'units':64,'pickups':32,'special':64,'windows':38,'boundaries':1104}
    assert window_counts=={2:10,3:6}
    assert sha(PROFILE/'index.sqlite')=='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
    con=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);static=[]
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        for idx in(1089,6730,1560,1744,5736,1417,1821,17979):
            a,b=con.execute('SELECT wat_start,wat_end FROM functions WHERE idx=?',(idx,)).fetchone();wat.seek(a);text=wat.read(b-a)
            (out/f'{idx}.wat').write_bytes(text)
            if idx==1089:
                for needle in(b'call 1744',b'call 5736',b'call 1417',b'call 1821',b'call 17979',b'1916',b'1964',b'2120'):assert needle in text
            if idx==1560:assert b'local.get 8\n          f32.load offset=116\n          local.set 33'in text and b'local.get 33\n                  f32.store offset=1516'in text
            x,y=bodies[idx];static.append(dict(index=idx,wat_sha256=digest(text),body_sha256=digest(original[x:y])))
    con.close()
    assert before=={p:sha(ROOT/p)for p in before}and sha(own)==own_sha
    own_copy=out/'review_opening135.py';own_copy.write_bytes(own.read_bytes())
    result=dict(status='passed',version='0.135.1',build='0898d5e3',receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,
        cases=16,original_calls=32,new_review_original_calls=0,source_closure_count=39,source_sha256=before,reviewer_source_sha256=own_sha,
        source_and_artifact_sha_verified=True,export_only_and_callees_preserved=True,original_sha256=SOURCE_SHA,
        snapshot_input_parity=dict(model_sha256=model_source['sha256'],original_sha256=original_source['sha256'],ranges=2318,bytes=5950600,ownership8_excluded=True,pure_query_model_equal=True,parity_receipt_sha256=sha(BATCH/'opening135-world-input-parity.json')),
        comparison=dict(counts),full_backing_bytes=55808,active_vector_record_counts=dict(vector_counts),window_count_cases=dict(window_counts),
        packets_independently_decoded=1232,banners_independently_encoded=16,raw_packet_queue_full_backing_checked=True,
        raw_app_only_lcg_seed_changed=True,raw_world_only_strong_reference_plus1=True,app_and_world_no_begin_mutations=True,
        actual_constructor_heading1428_bits=0x3fcccccd,heading_not_assumed_zero=True,
        new_inline_1089_scope=['Elwynn special64records','event windows38records,2/3counts','boundary1104GUIDs/packets','16banners150'],
        all_other_zones_or_modes_not_covered=True,nightelf_case10_constructor226_prefix_retained=True,
        complete_2592_game_sidecars_checked=True,unprojected_game_bytes_remain_unknown=True,indexed_static=static,
        process=dict(pid=process['pid'],exit_code=0,pid_and_pgid_missing=True,memory_peak=166395904,memory_cap=268435456,denied_imports=878,actual_imports=0),
        original_executed_by_reviewer=False,independent_world_producer=False,fresh_bootstraps=0,new_mainloop_frames=0,full_game_goal_complete=False)
    target=out/'review.json';target.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),sha256=sha(target),status='passed',cases=16,original_calls=32,new_original_calls=0)))


if __name__=='__main__':main()
