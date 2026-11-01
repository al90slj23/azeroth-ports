#!/usr/bin/env python3
"""Read-only1744/1821 review; no author model or original code is executed."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import ast,hashlib,json,math,os,sqlite3,struct,sys
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,parse_source,section_list,export_entries
from build_upgrade134_oracle import sha
from source_closure135 import core_sources
sys.dont_write_bytecode=True;sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as F
from core_spec.ai_trig135 import sin_bits,cos_bits
from resource_spec.world_query135 import decode_world_snapshot

BATCH=ROOT/'evidence/world-snapshot0135-oracle-20261101T101743.010880Z'
RECEIPT_SHA='132de5b5e8fd59a6f74ecb3b34859f8677b291122f5fa1aacb9c2fbd41cd2499'
SNAPSHOT_SHA='f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
PROFILE_INDEX_SHA='b1032d016b6ef43da115eb373a10f03ee2ddfae428cee7d988057d2caac773a0'
BASE_SPEEDS=(1075838976,1088421888,1083179008,1083645041,1075838976,1078530011)
MASK=0xffffffff


def rotl(value,count):return((value<<count)|(value>>(32-count)))&MASK


def actor_angle(words):
    draws=0
    while True:
        a,b,c,d=words;output=(rotl((a+d)&MASK,7)+a)&MASK
        words=(a^(d^b),b^(c^a),(c^a)^((b<<9)&MASK),rotl(d^b,11));draws+=1
        unit=F.add((output>>9)|0x3f800000,0xbf800000);angle=F.mul(unit,0x40c90fdb)
        if F.to_float(angle)<F.to_float(0x40c90fdb):return F.add(angle,0),words,draws
        assert draws<100000


def encoded_fields(fields):
    keys=sorted(fields);count=keys[-1]//32+1 if keys else 0;out=bytearray([count]);masks=[0]*count
    for key in keys:masks[key//32]|=1<<(key%32)
    for mask in masks:out+=mask.to_bytes(4,'little')
    for key in keys:out+=fields[key].to_bytes(4,'little')
    return bytes(out)


def make_packet(guid,xyz,heading,fields,*,speeds=None):
    raw=guid.to_bytes(8,'little');active=[j for j,x in enumerate(raw)if x]
    packed=bytes([sum(1<<j for j in active)])+bytes(raw[j]for j in active)
    unit=speeds is not None
    out=bytearray((1).to_bytes(4,'little')+b'\0'+bytes([3 if unit else 2])+packed+bytes([3,112]if unit else[5,80]))
    if unit:out+=bytes(8)
    for x in(*xyz,heading):out+=x.to_bytes(4,'little')
    if unit:
        out+=bytes(4)
        for x in speeds:out+=x.to_bytes(4,'little')
    out+=(1).to_bytes(4,'little');out+=encoded_fields(fields)
    return bytes(out)


def decode_packet(payload):
    """Independent exact parser, including zero-valued keys and trailing bytes."""
    p=0
    def take(n):
        nonlocal p
        value=payload[p:p+n];assert len(value)==n;p+=n;return value
    def u():return int.from_bytes(take(4),'little')
    assert u()==1 and take(1)==b'\0';block=take(1)[0];mask=take(1)[0];raw=bytearray(8)
    for j in range(8):
        if mask&(1<<j):raw[j]=take(1)[0]
    guid=int.from_bytes(raw,'little');kind,flags=take(2);speeds=None
    if kind==3:assert(block,flags,u(),u())==(3,112,0,0)
    else:assert(kind,block,flags)==(5,2,80)
    xyz=tuple(u()for _ in range(3));heading=u()
    if kind==3:assert u()==0;speeds=tuple(u()for _ in range(6))
    assert u()==1;n=take(1)[0];masks=[u()for _ in range(n)];fields={}
    for j,word in enumerate(masks):
        for bit in range(32):
            if word>>bit&1:fields[j*32+bit]=u()
    assert p==len(payload)and fields[0]==guid&MASK and fields[1]==guid>>32
    return dict(guid=guid,kind=kind,xyz=xyz,heading=heading,speeds=speeds,fields=fields)


def guid_fields(guid,values):return{0:guid&MASK,1:guid>>32,**values}


def height(world,x,y):
    result=world.height(x,y)
    if result.found:return result.value_bits
    nearest=world.nearest_primary(x,y)
    return nearest.xyz_bits[2]if nearest.found else world.fallback_height_bits


def write_companion(rows,count,writes):
    if count==len(rows):rows.extend([(None,)*88]*(max(4,len(rows)*2)-len(rows)))
    row=list(rows[count])
    for offset,payload in writes:row[offset:offset+len(payload)]=payload
    rows[count]=tuple(row);return count+1


def independent_local_closure():
    """Walk Python source imports and executed package entries without importing author."""
    pending=[ROOT/'scripts/check_opening_entities135.py'];seen=set()
    def include_module(name,package=None):
        if package:
            target=package.joinpath(*name.split('.'))
        elif name.startswith(('core_spec','resource_spec')):
            target=(ROOT/'reconstruction').joinpath(*name.split('.'))
        else:target=(ROOT/'scripts').joinpath(*name.split('.'))
        path=target.with_suffix('.py')
        if not path.exists():
            path=target/'__init__.py'
            if not path.exists():return
        pending.append(path)
        if 'reconstruction' in path.parts:
            package_init=(ROOT/'reconstruction'/path.relative_to(ROOT/'reconstruction').parts[0]/'__init__.py')
            pending.append(package_init)
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.Import):
                for alias in node.names:include_module(alias.name)
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    assert node.level==1
                    if node.module:include_module(node.module,path.parent)
                    else:
                        for alias in node.names:include_module(alias.name,path.parent)
                else:
                    include_module(node.module or '')
                    if node.module in('core_spec','resource_spec'):
                        for alias in node.names:include_module(node.module+'.'+alias.name)
    seen.update((ROOT/'scripts/run_opening_entities135_oracle.mjs',ROOT/'scripts/world_snapshot135_host.mjs'))
    return{str(path.relative_to(ROOT))for path in seen}


def main():
    path=BATCH/'opening-entities135-comparison.json';assert sha(path)==RECEIPT_SHA
    receipt=json.loads(path.read_text());before=receipt['source_sha256_before'];assert before==receipt['source_sha256_after']and len(before)==23
    assert independent_local_closure()==set(before)
    assert receipt['expected_before_original']is True and receipt['input_contains_expected']is False and receipt['differences']==0
    own=Path(__file__);own_sha=sha(own)
    for name,digest in before.items():assert sha(ROOT/name)==digest==sha(BATCH/'source-snapshot'/name)
    for name,digest in receipt['artifacts'].items():assert sha(BATCH/name)==digest
    assert sha(SOURCE)==SOURCE_SHA and sha(PROFILE/'index.sqlite')==PROFILE_INDEX_SHA
    snapshot=Path(receipt['snapshot_path']);assert sha(snapshot)==SNAPSHOT_SHA and snapshot.stat().st_size==117440512
    memory=snapshot.read_bytes();world=decode_world_snapshot(memory,26204808)
    original=SOURCE.read_bytes();manifest=json.loads((BATCH/'manifest.json').read_text());changed=(BATCH/manifest['module_file']).read_bytes();types,imports,decl,bodies,_=parse_source(original)
    old,new=section_list(original),section_list(changed);assert len(old)==len(new)and 8 not in[x[0]for x in old]
    for x,y in zip(old,new):
        assert x[0]==y[0]
        if x[0]!=7:assert original[x[1]:x[3]]==changed[y[1]:y[3]]
    oldex,_=export_entries(original,next(x for x in old if x[0]==7));newex,_=export_entries(changed,next(x for x in new if x[0]==7))
    assert newex==oldex+[(x['export'],0,x['index'])for x in manifest['roles']]+[('research_snapshot135_stack',3,0)]
    assert{r['index']for r in manifest['roles']}=={1744,1821}
    expected_bodies={1744:('7f','','c7c16dcf45b62c60bf6ba39c8e9e97fe7ca09845d9ad0de467e4362b80a93af7'),1821:('7f7f7f7f7f','7e','fbb21ae4ebb683d34bf3e62eb96f50571b16fb7d8053e980c6fd45cfcb3575db')}
    for role in manifest['roles']:
        i=role['index'];params,result,digest=expected_bodies[i];start,end=bodies[i]
        assert types[decl[i-len(imports)]]==(bytes.fromhex(params),bytes.fromhex(result))and hashlib.sha256(original[start:end]).hexdigest()==digest==role['body_sha256']
    global_section=next(x for x in old if x[0]==6);assert original[global_section[2]:global_section[3]].hex()=='017f01418080c0000b'
    config=json.loads((BATCH/'opening-entities135-config.json').read_text());assert set(config)=={'snapshot','snapshot_sha256','G','inputs'}and config['snapshot_sha256']==SNAPSHOT_SHA
    cases=json.loads((BATCH/'opening-entities135-inputs.json').read_text());fixtures=json.loads((BATCH/'opening-entities135-fixtures.json').read_text());actual=[json.loads(x)for x in(BATCH/'opening-entities135-results.jsonl').read_text().splitlines()]
    assert len(cases)==len(fixtures)==len(actual)==27
    assert all(set(c)=={'id','kind','input','ops'}for c in cases)
    assert cases==[{k:value for k,value in c.items()if k!='expected'}for c in fixtures]
    assert config['inputs']==str(BATCH/'opening-entities135-inputs.json')and config['snapshot']==str(snapshot)and config['G']==14554176
    runner=(BATCH/'source-snapshot/scripts/run_opening_entities135_oracle.mjs').read_text();assert 'expected.json'not in runner and 'opening-entities135-fixtures'not in runner
    checker=(BATCH/'source-snapshot/scripts/check_opening_entities135.py').read_text()
    assert checker.index("fixture.write_text(")<checker.index('child=subprocess.Popen(')
    assert "const cases=JSON.parse(await fs.readFile(config.inputs,'utf8'))"in runner
    host=(BATCH/'source-snapshot/scripts/world_snapshot135_host.mjs').read_text()
    assert "for(const m of imports){bindings[m.module]??={};bindings[m.module][m.name]=()=>{hostCalls.push"in host
    assert "throw Error('Snapshot original host import denied')"in host and 'new Uint8Array(memory.buffer).set(snapshot)'in host
    assert len(imports)==878
    profile=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);profile.row_factory=sqlite3.Row;static=[]
    with(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        for i in(1744,1821,10823,26970,50798):
            row=dict(profile.execute('select *from functions where idx=?',(i,)).fetchone());assert(row['body_start'],row['body_end'])==bodies[i]
            wat.seek(row['wat_start']);text=wat.read(row['wat_end']-row['wat_start']);assert text.startswith(f'  (func (;{i};)'.encode())
            static.append(dict(index=i,wat_sha256=hashlib.sha256(text).hexdigest(),body_sha256=hashlib.sha256(original[row['body_start']:row['body_end']]).hexdigest(),text=text))
    assert b'i32.load8_u offset=273'in static[0]['text']and b'f32.load offset=1556'in static[0]['text']
    counts=Counter();case_summaries=[]
    for c,fixture,observed in zip(cases,fixtures,actual):
        assert c['id']==fixture['id']==observed['id'];s=c['input'];counter=s['counter'];words=tuple(s['rng_words']);packets=[];returns=[];rows=[tuple(bytes.fromhex(row))for row in s.get('prior_storage',[])];count=s.get('prior_count',0);initial_count=count
        mapping={p['token']:p for p in observed['pointer_map']}
        for m in observed['pointer_map']:
            prototype=s['prototypes'][m['slot']];assert m['token']==prototype['token']
            raw=bytes.fromhex(m['prototype44_hex']);assert len(raw)==44
            if m['pointer']:assert struct.unpack_from('<3I',raw,32)==(prototype['display'],prototype['scale_bits'],prototype['entry'])
            else:assert raw==memory[:44]and struct.unpack_from('<3I',raw,32)==(0,0,0)
        assert observed['snapshot']['sha256']==SNAPSHOT_SHA and observed['snapshot']['restored_memory_bytes']==117440512 and observed['snapshot']['stack_after']==1048576
        assert len(c['ops'])==len(observed['stages'])==len(fixture['expected'])
        for op,a,e in zip(c['ops'],observed['stages'],fixture['expected']):
            new_creates=[]
            if c['kind']=='companions':
                if not s['protection2576']:
                    stat=op['stat1556_bits'];stat=stat if not F.is_nan(stat)and F.to_float(stat)>1 else 0x3f800000
                    run=F.mul(stat,F.mul(F.add(F.mul(F.from_u32(op['rank273']),0x3e4ccccd),0x3f800000),0x41600000))
                    speeds=list(BASE_SPEEDS);speeds[1]=run;effective=0
                    for proto,tag in zip(s['prototypes'],op['tags']):
                        if tag==255:continue
                        relative=F.mul(F.add(F.mul(F.from_u32(effective),0x3eb33333),0x3f933333),0x40490fdb);effective+=1
                        angle=F.add(relative,op['heading']);co,si=cos_bits(angle),sin_bits(angle)
                        x=F.add(op['player_xyz'][0],F.add(co,co));y=F.add(op['player_xyz'][1],F.add(si,si));xyz=(x,y,height(world,x,y))
                        counter=(counter+1)&MASK;guid=0xf130000000000000|((proto['entry']&0xffffff)<<24)|(counter&0xffffff)
                        fields=guid_fields(guid,{2:9,3:proto['entry'],4:proto['scale_bits'],22:1,28:1,34:1,35:35,46:33554434,129:1050253722,130:1056964608,131:proto['display'],132:proto['display'],145:0x3f800000})
                        packet=make_packet(guid,xyz,op['heading'],fields,speeds=tuple(speeds));packets.append(dict(opcode=169,payload_hex=packet.hex()));new_creates.append(packet)
                        now=op['now_bits'];count=write_companion(rows,count,((0,struct.pack('<2I',0,F.add(now,0x3f800000))),(16,struct.pack('<I',proto['token'])),(20,bytes([tag])),
                            (24,struct.pack('<Q',guid)),(32,struct.pack('<3I',0,4,0)),(44,struct.pack('<3I',*xyz)),(56,struct.pack('<3I',*xyz)),(68,struct.pack('<5I',now,0,now,relative,now))))
                assert(a['companion_count'],a['companion_capacity'])==(count,len(rows))and len(a['companion_storage'])==len(rows)
                assert e['companion_count']==count and e['companion_capacity']==len(rows)
                for j,(row,raw_hex,physical_hex)in enumerate(zip(rows,a['companion_storage'],a['companion_raw_storage'])):
                    normal=bytes.fromhex(raw_hex);physical=bytes.fromhex(physical_hex);assert len(normal)==len(physical)==88
                    expected_physical=bytearray(normal)
                    if initial_count<=j<count:
                        token=int.from_bytes(normal[16:20],'little');m=mapping[token];expected_physical[16:20]=m['pointer'].to_bytes(4,'little')
                    assert bytes(expected_physical)==physical
                    assert list(row)==e['companion_storage'][j]
                    for offset,(w,value)in enumerate(zip(row,normal)):
                        if w is None:
                            assert j>=count or offset in(8,9,10,11,12,13,14,15,21,22,23);counts['unknown_unwritten_bytes']+=1;counts['unknown_nonzero_bytes']+=bool(value)
                        else:assert w==value;counts['strict_record_bytes']+=1
                    counts['raw_record_backing_bytes']+=88
            else:
                assert c['kind']=='world_actor';angle,words,draws=actor_angle(words);counts['actor_rng_draws']+=draws
                counter=(counter+1)&MASK;guid=0xf110000000000000|((op['entry']&0xffffff)<<24)|(counter&0xffffff);half=F.mul(angle,0x3f000000)
                fields=guid_fields(guid,{2:33,3:op['entry'],4:op['scale_bits'],8:op['display'],9:op['flags9'],12:sin_bits(half),13:cos_bits(half),14:1,
                    15:op['xyz'][0],16:op['xyz'][1],17:op['xyz'][2],18:angle,20:35,21:op['kind21']})
                packet=make_packet(guid,tuple(op['xyz']),angle,fields);packets.append(dict(opcode=169,payload_hex=packet.hex()));returns.append(str(guid));new_creates.append(packet)
                assert a['return_guids']==e['return_guids']==returns and len(a['signed_i64_returns'])==len(returns)
                for signed,expected_guid in zip(a['signed_i64_returns'],returns):
                    value=int(signed);assert -(1<<63)<=value<1<<63 and value&((1<<64)-1)==int(expected_guid)
                    counts['signed_return_observations']+=1;counts['negative_signed_return_observations']+=value<0
            for packet in new_creates:
                decoded=decode_packet(packet);assert make_packet(decoded['guid'],decoded['xyz'],decoded['heading'],decoded['fields'],speeds=decoded['speeds'])==packet
            assert(a['counter'],a['rng_words'],a['packets'])==(counter,list(words),packets)
            assert e['counter']==counter and e['rng_words']==list(words)and e['packets']==packets
            game=bytes.fromhex(a['raw_game2592_hex']);metadata=bytes.fromhex(a['message_metadata_backing_hex']);assert len(game)==2592 and a['actual_stack']==1048576
            assert struct.unpack_from('<I',game,2408)[0]==counter and tuple(struct.unpack_from('<4I',game,1720))==words
            capacity,pointer,length=struct.unpack_from('<3I',game,1880);assert len(metadata)==capacity*16 and length==len(packets)
            for j,payload in enumerate(packets):assert struct.unpack_from('<I',metadata,j*16+8)[0]==len(bytes.fromhex(payload['payload_hex']))and struct.unpack_from('<H',metadata,j*16+12)[0]==169
            if c['kind']=='companions':assert(struct.unpack_from('<I',game,2108)[0],struct.unpack_from('<I',game,2116)[0])==(len(rows),count)
            counts['stages']+=1;counts['packet_cumulative_observation_bytes']+=sum(len(bytes.fromhex(p['payload_hex']))for p in packets);counts['raw_game2592_bytes']+=len(game)
        counts['final_packet_observations']+=len(packets);counts['final_packet_bytes']+=sum(len(bytes.fromhex(p['payload_hex']))for p in packets)
        counts['final_signed_return_observations']+=len(returns)
        case_summaries.append(dict(case=c['id'],kind=c['kind'],calls=len(c['ops']),final_packets=len(packets),final_counter=counter,final_rng=list(words)))
        role_calls=[call for call in observed['original_calls']if call['role']in('companions','world_actor')]
        assert len(role_calls)==len(c['ops'])and all(call['returned']for call in role_calls)
        counts['actual_role_call_records']+=len(role_calls)
        for call in observed['original_calls']:
            if call.get('returned'):assert call['stack_before']==call['stack_after']==1048576
    assert counts['stages']==116 and counts['strict_record_bytes']==8415 and counts['unknown_unwritten_bytes']==4785 and counts['unknown_nonzero_bytes']==3780
    assert counts['final_packet_observations']==135 and counts['final_packet_bytes']==15990 and counts['packet_cumulative_observation_bytes']==262209
    rt=receipt['runtime'];assert(rt['cases'],rt['stages'],rt['original1744_1821_calls'],rt['full_snapshot_restores'],rt['denied_imports'],rt['host_calls'])==(27,116,116,27,878,0)
    assert rt['max_memory_bytes']==117440512 and rt['memory_cap_bytes']==268435456 and receipt['process']['exit_code']==0 and receipt['process']['deadline_seconds']==60
    assert '--wasm-max-mem-pages=4096'in receipt['process']['command']
    assert counts['actual_role_call_records']==116 and counts['final_signed_return_observations']==91
    try:os.kill(receipt['process']['pid'],0)
    except ProcessLookupError:terminal=True
    else:terminal=False
    assert receipt['process']['pgid']==receipt['process']['pid']
    try:os.killpg(receipt['process']['pgid'],0)
    except ProcessLookupError:group_terminal=True
    else:group_terminal=False
    assert terminal and group_terminal and sha(own)==own_sha and sha(SOURCE)==SOURCE_SHA and sha(snapshot)==SNAPSHOT_SHA
    for name,digest in before.items():assert sha(ROOT/name)==digest
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-entities0135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    (out/'reviewer-source.py').write_bytes(own.read_bytes());(out/'case-recomputation.json').write_text(json.dumps(case_summaries,indent=2)+'\n')
    for row in static:(out/f'{row["index"]}.wat').write_bytes(row.pop('text'))
    report=dict(status='passed_scoped_independent_read_only_review',receipt=str(path.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,
        reviewer_sha256=own_sha,author_sources=23,current_and_snapshot_sources_verified=True,independent_static_import_closure_exact=True,original_module_nonexport_and_exports_preserved=True,
        original_body_and_signature_verified=True,full_snapshot_sha256=SNAPSHOT_SHA,full_snapshot_bytes=117440512,
        expected_never_passed_to_original=True,original_input_keys=['id','kind','input','ops'],counts=dict(counts),cases=27,actual_original_calls=116,
        original_or_browser_executed_by_reviewer=False,new_original_cases=0,author_source_modified=False,
        independently_recomputed=['1744effective-slot-compaction/counter/GUID/geometry/speed/fields/full88B-knownwrites/growth/padding','1821raw-RNG-transition/angle/GUID/keyedfields/signed-i64-normalization','full169binaryencoder-and-decoder/value-masks-including-zero-keys'],
        numeric_and_world_dependencies='Previouslyvalidatedbinary32/trigandworld_query/terrainheightaretrustedshareddependencies;thisreadonlyreviewdoesnotreproveallthoseconsumers.',
        pointer_normalization='Onlynewcompaniondefinitionpointer+16..19 mappedbacktoinputtoken;actualraw88B/prototype44/map retainedandcrosschecked;oldpointerbytesstrict.',
        raw_game_and_message_metadata='All116 rawG2592 and metadata payloadlinks/count/size/opcode crosschecked;unknownkeyedallocationsnotindependentlymodeled.',
        windows8_special40_boundary_and_banner_not_added_to116call_coverage=True,historical_replay_not_new_differential=True,
        runtime=dict(pid=receipt['process']['pid'],pgid=receipt['process']['pgid'],exit_code=0,pid_verified_missing=True,pgid_verified_missing=True,memory_cap_bytes=268435456,max_memory_bytes=117440512,denied_imports=878,host_calls=0,normal_return_stack1048576=True),
        static_functions=static,evidence_files={q.name:sha(q)for q in out.iterdir()},
        limitations=['Only complete1744/1821 scopedcomponents;inline1089windows/special/boundaries/bannerand4NPC/kind2composeareseparate.',
            'Snapshot-derivedworld/declaredprofileinputs;notindependentworldproducerorfreshbootstrap/fullgame.',
            'PhysicalBTree/messageallocatoraddressesandotherrawGsideeffectsremainobservations,notwholeGameequivalence.',
            'Sharednumericandworldquerydependenciesarevalidatedseparately;readonlyrecomputationisnotneworiginalexecution.'])
    target=out/'review.json';target.write_text(json.dumps(report,indent=2)+'\n');wrapper=dict(report,review_path=str(target.relative_to(ROOT)),review_sha256=sha(target))
    (ROOT/'reports/2026-11-01-opening-entities0135-independent-review.json').write_text(json.dumps(wrapper,indent=2)+'\n')
    (ROOT/'reports/2026-11-01-opening-entities0135-independent-review.md').write_text(f'''# 0.135.1 opening entities独立只读复核\n\n[最终27组/116调用收据](../{str(path.relative_to(ROOT))})通过限定域独审；[review](../{str(target.relative_to(ROOT))}) SHA `{sha(target)}`。没有执行原件、浏览器或作者opening_entities模型，新增原件案例0。\n\n独立重算1744的有效slot次序、counter/GUID、位置/速度、88B所有已写字节及旧padding；1821采用独立原始四字RNG位运算，验证GUID24位截取、counter回绕和有符号i64→u64适配，raw signed返回保留。完整169编码/解码、所有value mask和值（含零key）均重新构造。\n\n严格记录8,415B，未写4,785B单独观察其中3,780非零；定义指针仅在新记录+16..19按显式映射规范化，完整raw88/prototype44/映射已核对。27组最终包共135个/15,990B，与116阶段累计重复观察262,209B分列，不混作新增包。\n\n原件只增export7，完整函数body/签名、23源闭包、117,440,512B真实snapshot、输入/expected分离、878导入全拒绝/实际0、256MiB上限和正常返回栈1048576均核对。Node52920退出0且PID缺失。\n\n共享binary32/trig和world_query高度依赖另有验证；本复算不重新证明其全部输入。窗口8B、special40、边界几何及banner仍不倒记到116调用；历史快照重放不计新差分。完整1089、worldproducer、880与独立一局仍未由本报告证明。\n''')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),status=report['status'],counts=dict(counts))))


if __name__=='__main__':main()
