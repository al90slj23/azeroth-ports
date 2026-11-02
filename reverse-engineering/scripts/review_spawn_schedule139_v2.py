#!/usr/bin/env python3
"""Different-author current952 before60s review incl real40skinds3/4/5."""
from pathlib import Path
from collections import Counter
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_spawn_schedule139 as S
import review_death_pickups139 as D
C,O,N,Position=S.C,S.O,S.N,S.Position
from review_combat139 import parse_module,local_closure,sha,fp,bits
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
HAND_BATCH=ROOT/'evidence/spawn-schedule139-v2-kind5-oracle-20261102T134231.621630Z'
HAND='3addfbcefc16415241548ab0fab9dea47b87b632b0afb5d585c9a1346b0d5418'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=S.u
q=S.q
read=S.read
choose=S.choose
birth=S.birth
constructor_reference=S.constructor_reference
load_world=S.load_world


def reference(case,opening,world,nav,scalars,tables,definitions,zone,speeds,counts):
    p=opening['projection'];player=p['player_xyz'];rows=copy.deepcopy(p['units']['storage']);count=p['units']['count'];pickups=copy.deepcopy(p['pickups']['storage']);pickup_count=p['pickups']['count'];words=tuple(p['rng_words']);counter=p['counter'];packets=copy.deepcopy(p['packets']);budget=bits(3.);clock=0
    timeline=[];frames={};born=[];timers={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0};previous_xyz=[0,0,0]
    for frame in range(case['frames']):
        clock=C.add(clock,case['dt_bits']);assert C.rational(clock)<60
        # 952 never moves these actors: branch predicates are independently
        # evaluated rather than treating absence of recycling as execution.
        for row in rows[:count]:
            assert read(row,0)==0 and read(row,244)==0xffffffff and read(row,344)==0
            distance=C.distance((read(row,328),read(row,332)),player);assert C.rational(distance)<=3025;counts['far55_predicates_not_taken']+=1
        velocity=[C.div(C.sub(player[i],previous_xyz[i]),case['dt_bits'])for i in range(2)]
        if frame==0:assert C.rational(C.distance(velocity,(0,0)))>=1600;counts['first_velocity_jump_filtered']+=1
        else:assert velocity==[0,0]
        previous_xyz=player[:]
        minute=C.div(clock,bits(60.));rate=C.add(C.add(C.mul(minute,0x3ea3d70a),0x3f666666),C.mul(minute,C.mul(minute,0x3ccccccd)))
        rate=C.mul(rate,0x3f19999a);budget=C.add(budget,C.mul(case['dt_bits'],rate))
        # Actual killcost0 × exp(dt/-12) stays +0. No approximate host exp is
        # substituted into nonzero decay, which is outside this frozen domain.
        counts['zero_killcost_decay_predicates']+=1
        eligible=[i for i,d in enumerate(definitions)if d[68]==0 and C.rational(u(d,64))<=C.rational(minute)]
        def attempt(index,origin):
            nonlocal words,counter,count
            assert count<50
            state=dict(zone=0,player_xyz=player,velocity_xy=[0,0],low_radius_bits=bits(26.),high_radius_bits=bits(36.),bias_probability_bits=bits(.5),rng_words=words,distance_map=None)
            location=Position(state,world,nav,scalars,tables);xyz=location.spawn();words=location.words
            if count==len(rows):rows.extend([[None]*432 for _ in range(max(4,2*len(rows))-len(rows))])
            row,words,counter,packet=birth(index,clock,xyz,player,words,counter,rows[count],definitions,zone,tables,speeds,counts);rows[count]=row;packets.append(packet)
            born.append(dict(frame=frame,slot=count,definition_index=index,guid=str(q(bytes(row[112:120]))),origin=origin,position_bits=xyz,position_reference_diagnostics=dict(location.count)));count+=1
            counts['new_NPCs']+=1;counts['new169_packets']+=1;counts['new169_payload_bytes']+=len(bytes.fromhex(packet[1]));counts['definition'+str(index)+'_births']+=1
        if C.rational(budget)>=1:
            for iteration in range(8):
                index,words=choose(eligible,minute,words,definitions,counts);cost=u(definitions[index],60);counts['budget_choice_attempts']+=1
                if C.rational(cost)>C.rational(budget):counts['budget_insufficient_choice_breaks']+=1;break
                attempt(index,'budget');budget=C.sub(budget,cost)
                if C.rational(budget)<1:break
            else:counts['eight_budget_loop_limit_hits']+=1
        target=C.add(C.mul(minute,0x3fcccccd),bits(4.));target=int(min(36,C.rational(target)))
        alive=sum(read(row,0)==0 and read(row,284)!=0 and definitions[(read(row,284)-5830904)//72][68]==0 for row in rows[:count]);fill=min(3,max(0,target-alive));counts['density_predicates']+=1;counts['density_fill_requested']+=fill
        for _ in range(fill):index,words=choose(eligible,minute,words,definitions,counts);attempt(index,'density')
        if C.rational(clock)>=C.rational(timers['2444']):
            timers['2444']=C.add(clock,bits(45.))
            resource_count=sum(read(row,8)in(3,4,5)for row in pickups[:pickup_count])
            assert resource_count<2
            for _ in range(10001):
                output,words=C.nextword(words);product=output*3;counts['kind3range_draws']+=1
                if product&0xc0000000!=0xc0000000:break
            else:raise AssertionError('Independent3range watchdog')
            kind=3+(product>>32);assert kind in(3,4,5)
            raw_amount=words[0]
            request=dict(zone=0,player_xyz=player,velocity_xy=[0,0],low_radius_bits=bits(15.),high_radius_bits=bits(40.),bias_probability_bits=bits(.5),rng_words=words,distance_map=None)
            location=Position(request,world,nav,scalars,tables);xyz=location.random();words=location.words
            placed,clamped=D.geometry(dict(xyz=xyz),world,scalars);assert not clamped
            counter=(counter+1)&0xffffffff;entry=9006+(kind-3);display={3:5931,4:5995,5:5991}[kind]
            guid=0xf110000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
            yaw,words=O.uniform(words,0.,fp(0x40c90fdb));yaw=O.f32(yaw+0.)
            packets.append([169,O.object_packet(guid,entry,display,C.ONE,placed,yaw,5,0)])
            if pickup_count==len(pickups):pickups.extend([[None]*56 for _ in range(max(4,2*len(pickups))-len(pickups))])
            row=pickups[pickup_count];row[0:4]=bytes(4);row[8:56]=struct.pack('<IIQ4I4I',kind,raw_amount,guid,0,8,0,entry,*placed,clock);pickup_count+=1
            counts['kind'+str(kind)+'_resource_births']+=1;counts['resource169_packets']+=1
        counts['full952_recomputed']+=1
        line=dict(frame=frame,count=count,capacity=len(rows),rng_words=list(words),counter2408=counter,now_bits=clock,budget2416_bits=budget,kill_cost2420_bits=0,previous_player_xyz=player,velocity_xy=[0,0],timer_fields=copy.deepcopy(timers),packet_count=len(packets));timeline.append(line)
        if frame in case['checkpoints']or frame==case['frames']-1:frames[frame]=dict(timeline=copy.deepcopy(line),rows=copy.deepcopy(rows),pickups=copy.deepcopy(pickups),pickup_count=pickup_count,packets=copy.deepcopy(packets))
    return timeline,frames,born


def main():
    out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(HAND_BATCH/'task-handoff.json')==HAND and sha(SOURCE)==WASM
    hand=load(HAND_BATCH/'task-handoff.json');author=hand['frozen_author_files'];assert len(author)==7
    helpers={**S.HELPERS,'scripts/review_spawn_schedule139.py':'b2e9997dff3d356e637945806802dde95354e7ffdc86c796275e7bfa3d2e1fe2','scripts/review_death_pickups139.py':'092328f7b6e7c5323f1d3b9c74b1080b1181fdd002f7153d32756110d9dcaef3'}
    for n,h in helpers.items():assert sha(ROOT/n)==h
    for n,h in author.items():assert sha(ROOT/n)==h
    raw=SOURCE.read_bytes();original=parse_module(raw);m=load(ROOT/hand['formal_batches'][0]['path']/'manifest.json')
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp)
    assert sha(wp)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']))
    assert not scalars['flat_present']and not scalars['primary_present']
    texts={};bindings={};extra={6786,33028,11425,11499,35202,35232,57285,108362,1711,1886,24602}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx in sorted(set(map(int,m['functions']))|extra):
            lo,hi=original['bodies'][idx];wlo,whi=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(wlo);wat=stream.read(whi-wlo)
            bindings[str(idx)]=dict(body_sha256=hashlib.sha256(raw[lo:hi]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());texts[idx]=wat.decode()
            if str(idx)in m['functions']:
                q=m['functions'][str(idx)];assert q['body_sha256']==bindings[str(idx)]['body_sha256']and q['WAT_sha256']==bindings[str(idx)]['WAT_sha256']
    assert texts[952].index('f32.load offset=2444')<texts[952].index('f32.load offset=2448')
    region=texts[952][texts[952].index('f32.load offset=2444'):texts[952].index('f32.load offset=2448')]
    for fragment in('i64.const 3','i64.const 3221225472','i64.const 32','i32.const 3','i32.const 4','i32.const 5','f32.const 0x1.68p+5 (;=45;)','call 13563','call 1446'):assert fragment in region
    assert 'f32.const 0x1.ep+3 (;=15;)'in region and'f32.const 0x1.4p+5 (;=40;)'in region
    def data(address,size):
        result=bytearray(size)
        for at,pos,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
        return bytes(result)
    word=lambda p:u(data(p,4));text=lambda p,n:data(p,n).decode();abilities={}
    for i in range(114):
        p=5882740+88*i;r=data(p,88);abilities[text(u(r,12),u(r,16))]=(p,r)
    cls=data(5877920,108);classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};race=data(5874636,44);racial=text(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);scalars['heading_bits']=u(zone,116);assert[u(zone,o)for o in[64,68,104,108,136,140]]==[5830904,12,*scalars['center_xy_bits'],1062333317,0]
    zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];definitions=[data(5830904+72*i,72)for i in range(12)];eligible=[i for i,d in enumerate(definitions)if d[68]==1 and math.isfinite(fp(u(d,64)))];assert eligible==[9,10,11];minutes=word(u(zone,72)+336)
    tables=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888
    tree=ast.parse((ROOT/'reconstruction/core_spec/spawn_schedule139_data.py').read_text());literal={n.targets[0].id:ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)}
    assert literal==dict(ELWYNN152_HEX=zone.hex(),NORMAL_BASE=5830904,NORMALS72_HEX=tuple(x.hex()for x in definitions))
    counts=Counter();traces=[];batch_records=[];all_sources=None
    allowed=set()
    for offset,size in((1720,16),(1784,12),(1868,24),(2352,4),(2408,4),(2416,24),(2444,4)):allowed.update(range(offset,offset+size))
    def cells(label,wanted,hx):
        actual=bytes.fromhex(hx);assert len(wanted)==len(actual)
        for offset,(value,byte)in enumerate(zip(wanted,actual,strict=True)):
            if value is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(byte)
            else:assert value==byte,(label,offset,value,byte);counts[label+'_known']+=1
    def header(view):
        game=bytes.fromhex(view['raw_game2592_hex']);proj=view['projection'];bg=view['background'];assert len(game)==2592
        for key,offset in(('level',1432),('xp',1436),('pending',2376),('current_hp_bits',1440),('generation_counter2400',2400)):assert u(game,offset)==proj[key]
        assert{str(1536+4*j):u(game,1536+4*j)for j in range(23)}==proj['derived_bits']
        assert[u(game,1720+4*j)for j in range(4)]==proj['rng_words']and game[2587]==proj['phase2587']==1
        for name,cap,ptr,n,width in(('units',1784,1788,1792,432),('pickups',1868,1872,1876,56),('special',1916,1920,1924,40),('windows',1964,1968,1972,8),('boundaries',2120,2124,2128,8),('claims',2108,2112,2116,88),('auxiliary',652,656,660,112)):
            vector=bg[name];assert(vector['capacity'],vector['pointer'],vector['count'],vector['stride'])==(u(game,cap),u(game,ptr),u(game,n),width)
            assert len(vector['storage'])==vector['capacity']and all(len(bytes.fromhex(s))==width for s in vector['storage'])
        assert u(game,1888)==len(view['packets'])<=u(game,1880)and u(game,2408)==bg['counter2408']and u(game,2412)==bg['movement_sequence2412']
        assert u(game,1712)==len(view['live32_hex'])==0 and u(game,1664)==len(proj['owned_records80_hex'])==1
        return game
    for batch_info in hand['formal_batches']:
        batch=ROOT/batch_info['path'];comp=load(batch/'comparison.json');prep=load(batch/'prepared.json');manifest=load(batch/'manifest.json');runtime=load(batch/'runtime.json');cfg=load(batch/'config.json')
        assert sha(batch/'comparison.json')==batch_info['comparison_sha256']and sha(batch/'manifest.json')==batch_info['manifest_sha256']and sha(batch/'prepared.json')==batch_info['prepared_sha256']
        sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==46
        for name,h in sources.items():assert sha(ROOT/name)==sha(batch/'source-snapshot'/name)==h
        assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(comp['source_import_edges'])==136
        assert sum(name.startswith('reconstruction/')for name in sources)==34
        if all_sources is None:all_sources=sources
        else:
            assert all(all_sources[n]==h for n,h in sources.items()if n in all_sources)
            all_sources.update(sources)
        for table in(comp['artifacts'],prep['frozen']):
            for name,h in table.items():assert sha(batch/name)==h
        assert comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']
        assert not load(batch/'expectation-read-audit.json')['forbidden']
        assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
        assert sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
        assert comp['resource_context_gate_sha256']==prep['resource_context_gate_sha256']==sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')
        assert comp['independent_world_receipt_sha256']==prep['independent_world_receipt_sha256']==sha(wp)
        private=(batch/manifest['module_file']).read_bytes();assert sha(batch/manifest['module_file'])==manifest['module_sha256'];modified=parse_module(private)
        assert len(original['sections'])==len(modified['sections'])
        for a,b in zip(original['sections'],modified['sections'],strict=True):
            assert a['kind']==b['kind']
            if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
        assert modified['exports']==original['exports']+[tuple(v)for v in manifest['added_exports']]
        assert len(original['imports'])==882 and [(x['module'],x['name'],x['type_index'])for x in original['imports']]==[(x['module'],x['name'],x['type_index'])for x in manifest['original_imports']]
        assert manifest['functions']==m['functions']and manifest['only_export_section_changed']and manifest['original_executions']==0
        for index,record in manifest['functions'].items():assert sha(batch/'static'/f'{index}.wat')==record['WAT_sha256']
        cases=load(batch/'inputs.json');actual=[json.loads(line)for line in(batch/'actual.jsonl').read_text().splitlines()]
        assert len(cases)==len(actual)==comp['cases']==comp['completed_cases']
        for case,a in zip(cases,actual,strict=True):
            assert a['id']==case['id']and a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['stack_after']==1048576
            opening,_=O.reference(case,world,nav,scalars,tables,definitions[0],speeds,classes,races,zones,eligible,minutes);op=opening['projection'];known=opening['known_Game2592']
            for offset,value in((1736,0),(1740,0),(2368,0),(1984,0),(2416,bits(3.)),(2420,0)):known[offset:offset+4]=struct.pack('<I',value)
            assert a['opening']==a['before'];before=a['before'];game=header(before);cells('opening_Game',known,before['raw_game2592_hex'])
            assert a['constructor_seed_u64']==opening['constructor_seed_u64']and before['packets']==op['packets']
            account=bytearray([165]*368)
            for offset in(196,244,256,268):account[offset:offset+4]=bytes(4)
            assert a['account368_before_hex']==a['account368_after_hex']==account.hex()
            selected=bytes(opening['selected40_cells']);assert a['selected40_hex']==selected.hex()and a['selection_canaries']==['c3'*16,'d7'*16]
            profile=bytes.fromhex(a['profile376_before_hex']);wanted=bytearray(376);struct.pack_into('<I',wanted,156,4);wanted[168:172]=profile[168:172];struct.pack_into('<I',wanted,172,6);struct.pack_into('<Q',wanted,184,int(opening['constructor_seed_u64']));wanted[224:240]=selected[:16];wanted[344:346]=b'\1\1'
            assert profile==bytes(wanted)and a['profile376_before_hex']==a['profile376_after_hex']
            for name in('units','pickups','special','windows','boundaries'):
                v=before['background'][name];assert(v['capacity'],v['count'])==(op[name]['capacity'],op[name]['count'])
                for row,hx in zip(op[name]['storage'],v['storage'],strict=True):cells('opening_'+name,row,hx)
            timeline,frames,born=reference(case,opening,world,nav,scalars,tables,definitions,zone,speeds,counts)
            if timeline!=a['timeline']:
                finding=next((dict(index=index,independent=want,actual=got)for index,(want,got)in enumerate(zip(timeline,a['timeline'],strict=True))if want!=got),None)
                save(out/'timeline-finding.json',finding)
            assert timeline==a['timeline'],('timeline',batch.name,case['id'])
            assert [capture['frame']for capture in a['frames']]==list(frames)
            previous=before
            for capture in a['frames']:
                index=capture['frame'];wanted=frames[index];view=capture['view'];game=header(view);bg=view['background']
                assert capture['spawn']=={k:v for k,v in wanted['timeline'].items()if k!='frame'}
                assert(bg['units']['count'],bg['units']['capacity'])==(wanted['timeline']['count'],wanted['timeline']['capacity'])
                assert bg['pickups']['count']==wanted['pickup_count']and bg['pickups']['capacity']==len(wanted['pickups'])
                for name,model in(('units',wanted['rows']),('pickups',wanted['pickups'])):
                    for slot,(row,hx)in enumerate(zip(model,bg[name]['storage'],strict=True)):
                        cells(name,row,hx)
                        if slot<len(previous['background'][name]['storage']):
                            old,new=bytes.fromhex(previous['background'][name]['storage'][slot]),bytes.fromhex(hx)
                            for offset,value in enumerate(row):
                                if value is None:assert old[offset]==new[offset];counts[name+'_None_physical_inheritance']+=1
                assert view['packets']==wanted['packets'];counts['complete_ordered_packet_snapshots']+=len(wanted['packets'])
                assert view['projection']=={**before['projection'],'rng_words':wanted['timeline']['rng_words']}
                for key in('live32_hex','raw_candidates80_hex','tree_nodes'):assert view[key]==before[key]
                for name in('auxiliary','claims','windows','special','boundaries'):
                    assert bg[name]==before['background'][name];counts['background_owners_conserved']+=1
                assert u(game,2412)==before['background']['movement_sequence2412'];counts['background_owners_conserved']+=1
                for offset,value in[(2416,wanted['timeline']['budget2416_bits']),(2420,0),(2352,wanted['timeline']['now_bits']),*[(int(k),v)for k,v in wanted['timeline']['timer_fields'].items()]]:assert u(game,offset)==value
                assert list(struct.unpack_from('<3I',game,2428))==op['player_xyz']and list(struct.unpack_from('<2I',game,1736))==[0,0]
                old=bytes.fromhex(previous['raw_game2592_hex'])
                for offset,(x,y)in enumerate(zip(old,game,strict=True)):
                    if offset not in allowed:assert x==y,(batch.name,case['id'],index,'Game',offset);counts['Game_nonowned_bytes_inherited']+=1
                counts['checkpoints']+=1;previous=view
            counts['fresh_instances']+=1;traces.append(dict(batch=batch.name,case=case,timeline=timeline,born=born))
        assert runtime==comp['runtime']and runtime['full_calls']==batch_info['full_calls']and runtime['fresh_instances']==len(cases)
        assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None
        assert all(x['returned']and x['before']==x['after']==1048576 for x in runtime['target_and_setup_returns'])
        assert all(x['ranges']==2318 and x['unchanged']for x in runtime['world_source_checks'])
        for key in('NPC_positions_written_by_driver','NPC_states_or_timers_written_by_driver','velocity_or_path_headers_written_by_driver','RNG_or_budget_written_by_driver','old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored'):assert runtime[key]is False
        assert runtime['native_executions']==runtime['full_mainloop_frames']==runtime['complete_games']==0
        terminal=load(batch/'owned-terminal.json');assert terminal==comp['process']==batch_info['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']
        batch_records.append(dict(path=str(batch.relative_to(ROOT)),comparison_sha256=sha(batch/'comparison.json'),process=terminal))
    assert counts['full952_recomputed']==3119 and counts['fresh_instances']==4 and counts['new_NPCs']==132 and counts['resource169_packets']==4
    assert all(counts['kind'+str(kind)+'_resource_births']for kind in(3,4,5))and counts['checkpoints']==37
    for name,h in author.items():assert sha(ROOT/name)==h
    for name,h in all_sources.items():assert sha(ROOT/name)==h
    for name,h in helpers.items():assert sha(ROOT/name)==h
    assert not S.AUDIT
    result=dict(status='accepted_current139_stationary_before60s_with_real40_resources',counts=dict(counts),author_handoff_sha256=HAND,author_files=author,
        sources=all_sources,unique_source_files=len(all_sources),per_batch_source_files=46,production_files=34,per_batch_source_edges=136,current_bindings=bindings,helper_SHA=helpers,batches=batch_records,
        author_or_original_executions_by_reviewer=0,expected_file_used_as_reference=False,reviewer_audit=dict(S.AUDIT),
        limits=['4 genuineopening instances,3119 full952 target entries and12 setup classified separately;natural40s kind3/4/5 matched. No60s wave/Rune or240s elite/Boss coverage.',
        'Stationary/no combat/no death/zero killcost/default owners;far55 recycle,densitypositive/spawncap50/resourcecount2 not silently accepted.',
        'Correct2424=60wave/2440=240elite timer roles. Only2444 triggers here, setsnow+45;naturalresourcecapture stilldoesnotimplement theircollection.',
        'Previous independentlywritten ordinary/opening/geometry/NPC/Fraction/packet algorithms reused withcurrentwholeWAT/body/data binding;noauthor production imports.',
        'Resource-onlyv2 context,new2945/1600/full1108;fullApp/Rc/externref/bootstrap/full884/nativeWindows/network/save/completegame remainPending.'])
    save(out/'review.json',result);save(out/'reference-traces.json',traces)
    print(json.dumps(dict(status=result['status'],counts={k:counts[k]for k in('full952_recomputed','fresh_instances','new_NPCs','resource169_packets','kind3_resource_births','kind4_resource_births','kind5_resource_births','kind3range_draws','checkpoints')})),flush=True)


if __name__=='__main__':main()
