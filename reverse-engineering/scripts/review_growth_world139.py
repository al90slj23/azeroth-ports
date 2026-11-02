#!/usr/bin/env python3
"""Independent current139 fullopening/inactive-world gain/select review."""
from collections import Counter
from pathlib import Path
import copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_growth139 as G
import review_opening139 as O
from review_combat139 import parse_module,local_closure,sha,bits,fp,f32
from review_world_position139 import load_world

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/growth-world139-oracle-20261102T095434.252586Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
COMP='1b874256c8c8223179d7f8b9e340700b9d432789e2d6e024defda40f03fa9bcf'
HAND='e9fffde0e79085c89d3dbfaeffa2ce760e38dc9af7d5f6e9c5fa449b47ebcaa0'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={**G.HELPERS,**O.HELPERS,
 'scripts/review_growth139.py':'db6246b4dc0da5aa902ef87e629ce4d460c04e2e41acad4c7b63fba2a2e9d243',
 'scripts/review_opening139.py':'29de9cb7dbeb7595ce2baced0a0de9d5c5e967ce73cecd8cff5868d4feafc5c9'}
load=lambda p:json.loads(Path(p).read_text())
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]


def inactive(rows,now=0):
    dead=stationary=0
    def word(row,offset):
        part=row[offset:offset+4];assert len(part)==4 and None not in part
        return int.from_bytes(bytes(part),'little')
    for row in rows:
        marker=word(row,0);assert marker in(0,1)
        if marker:dead+=1;continue
        duration=fp(word(row,344));assert math.isfinite(duration)
        if duration>0:
            start=fp(word(row,340));assert math.isfinite(start)
            assert not f32(duration+start)>fp(now),'Moving NPC outside this fixture domain'
        stationary+=1
    return dict(NPC_count=len(rows),dead=dead,stationary_or_expired=stationary)


def grow(before,case,classes,races,kit,definitions,cooldown,damage,proof):
    state=copy.deepcopy(before);state['xp']=(state['xp']+case['amount'])&0xffffffff;events=[]
    while state['level']<=119 and state['xp']>=G.threshold(state['level']):
        old=state['level'];cost=G.threshold(old);state['xp']-=cost;state['pending']+=1;state['level']+=1;G.recalculate(state,classes,races);fields=state['player_fields'];fields['34']=state['level']
        request=G.mul(state['derived_bits']['1536'],0x3e4ccccd);oldhp=state['current_hp_bits'];state['current_hp_bits']=min(G.add(oldhp,request),state['derived_bits']['1536']);fields['22']=math.ceil(fp(state['current_hp_bits']));fields['28']=math.ceil(fp(state['derived_bits']['1536']))
        events.append(dict(kind='level_up',before=old,after=state['level'],threshold_spent=cost,heal_request_bits=request,heal_delta_bits=G.sub(state['current_hp_bits'],oldhp)))
    state['player_fields'].update({'716':state['xp'],'717':G.threshold(state['level'])})
    if state['pending']:
        cards,words,draws=G.candidates(state['rng_words'],kit,state['level']);state.update(candidates=cards,rng_words=words,phase2587=2,selection_kind2585=0,generation_counter2400=1);events.append(dict(kind='candidate_choice',count=len(cards),draws=draws,inactive_world=proof))
    gain=copy.deepcopy(state);index=next((j for j,c in enumerate(state['candidates'])if c['variant']=='new'),None);selection=None
    assert case['select_index']==index
    if index is not None:
        card=state['candidates'][index];assert state['pending']==1
        state['owned_records80_hex'].append(G.selected_record(card['ability_id'],card['tier'],definitions,cooldown,damage));G.recalculate(state,classes,races);state.update(pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=[])
        live=[None]*32;live[:8]=bytes(8);live[8:12]=struct.pack('<I',12);live[20:32]=struct.pack('<III',1020,0x3f800000,0);selection=dict(projection=state,live32_cells=[live])
    return gain,index,selection,events


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(CASE/'comparison.json')==COMP and sha(CASE/'task-handoff.json')==HAND and sha(SOURCE)==WASM
    for n,h in HELPERS.items():assert sha(ROOT/n)==h
    comp=load(CASE/'comparison.json');hand=load(CASE/'task-handoff.json');prep=load(CASE/'prepared.json');manifest=load(CASE/'manifest.json');cfg=load(CASE/'config.json');author=load(ROOT/'reports/2026-11-02-growth-world0139.json')
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==42
    for n,h in sources.items():assert sha(ROOT/n)==h==sha(CASE/'source-snapshot'/n)
    for n,h in hand['frozen_author_files'].items():assert sha(ROOT/n)==h
    for n,h in prep['frozen_v1_source_sha256'].items():assert sha(ROOT/n)==h
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==114
    for table in(comp['artifacts'],comp['frozen'],prep['frozen']):
        for n,h in table.items():assert sha(CASE/n)==h
    assert prep['expected_before_original']and not prep['original_input_contains_expected']and comp['forbidden_model_reads']==[]and prep['full_world_owners_retained']
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']==comp['resource_context_snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==comp['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    assert sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==comp['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']))
    raw=SOURCE.read_bytes();original=parse_module(raw);modified_raw=(CASE/manifest['module_file']).read_bytes();modified=parse_module(modified_raw)
    assert len(original['sections'])==len(modified['sections'])
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==modified_raw[b['start']:b['end']]
    additions=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),('research139_gw_select',0,1093),('research139_gw_stack',3,0)]
    assert modified['exports']==original['exports']+additions and len(original['imports'])==882
    assert [(v['module'],v['name'])for v in original['imports']]==[(v['module'],v['name'])for v in manifest['original_imports']]
    def data(address,size):
        result=bytearray(size)
        for at,pos,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
        return bytes(result)
    word=lambda p:u(data(p,4));text=lambda p,n:data(p,n).decode()
    abilities={}
    for i in range(114):
        p=5882740+88*i;r=data(p,88);abilities[text(u(r,12),u(r,16))]=(p,r,tuple(data(u(r,36),u(r,40))))
    cls=data(5877920,108);kit=[text(p,n)for p,n in struct.iter_unpack('<II',data(u(cls,32),8*u(cls,36)))];definitions={k:abilities[k]for k in kit};classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)}
    race=data(5874636,44);racial=text(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);scalars['heading_bits']=u(zone,116);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];tables=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888;definition=data(5830904,72)
    eligible=[j for j in range(12)if word(5830904+72*j+68)==1 and math.isfinite(fp(word(5830904+72*j+64)))];assert eligible==[9,10,11];minutes=word(u(zone,72)+336);assert minutes==1098907648
    cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20));functions={};texts={}
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx in sorted(set(map(int,manifest['functions']))|{11425,11499,50441,24602,33028,30628,25511,29912}):
            a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);value=stream.read(end-start);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(value).hexdigest());functions[str(idx)]=proof;texts[idx]=value.decode();(out/f'{idx}.wat').write_bytes(value)
            if str(idx)in manifest['functions']:assert proof['body_sha256']==manifest['functions'][str(idx)]['body_sha256']and proof['WAT_sha256']==manifest['functions'][str(idx)]['WAT_sha256']and value==(CASE/'static'/f'{idx}.wat').read_bytes()
    t=texts[26364];assert all(s in t for s in ['i32.load offset=1788','i32.load offset=1792','i32.const 432','i32.const 344','i32.const 340','i32.load offset=656','i32.load offset=660','i32.const 112','i32.load offset=2112','i32.load offset=2116','i32.const 88','i64.const 34359738368'])
    first=t.split('i32.load offset=656')[0];assert 'i32.load\n                  br_if 0 (;@7;)'in first and'f32.gt\n                  i32.eqz\n                  br_if 0 (;@7;)'in first
    assert 'call 26364'in texts[35988]and'call 26364'in texts[25613]and'call 35988'in texts[2181]and'call 25613'in texts[4603]
    assert texts[35988].index('local.tee 2\n    if')<texts[35988].index('i32.load offset=2348')and texts[25613].index('local.tee 2\n    if')<texts[25613].index('i32.load offset=2348')
    cases=load(CASE/'inputs.json');expected=load(CASE/'expected.json');actual=[json.loads(x)for x in(CASE/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==11
    counts=Counter();selected=Counter();masks=Counter();reference=[]
    def check_cells(name,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for i,(v,b)in enumerate(zip(want,seen)):
            if v is None:counts[name+'_None']+=1;counts[name+'_nonzero_None']+=bool(b)
            else:assert v==b,(name,i,v,b);counts[name+'_known']+=1
    for c,e,a in zip(cases,expected,actual,strict=True):
        assert c==e['input']and c['id']==e['id']==a['id'];op,_=O.reference(dict(id=c['id'],app_seed_u64=c['app_seed_u64']),world,nav,scalars,tables,definition,speeds,classes,races,zones,eligible,minutes);opening=op['projection']
        seed=op['constructor_seed_u64'];init,_=G.reference(dict(id=c['id'],seed_u64=seed,amount=0,select_index=None),classes,races,zones,kit,definitions,cooldown,damage);before=init['before'];before['rng_words']=opening['rng_words'];rows=copy.deepcopy(opening['units']['storage'])
        for j,row in enumerate(rows):
            if c['dead_mask']>>j&1:row[:4]=bytes([1,0,0,0])
        proof=inactive(rows);gain,index,selection,events=grow(before,c,classes,races,kit,definitions,cooldown,damage,proof);background={k:copy.deepcopy(opening[k])for k in ['units','pickups','special','windows','boundaries']};background['units']['storage']=rows
        answer=dict(before=before,gain=gain,selection=selection,selected_index=index,opening=opening,background=background,model_events=events,inactive_world_proof=proof);assert answer==e['expected'],('independent_expected',c['id']);reference.append(dict(id=c['id'],expected=answer));masks[c['dead_mask']]+=1
        assert int(a['constructor_seed_u64'])==int(seed)and a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['stack_after']==1048576
        assert a['account368_before_hex']==a['account368_after_hex']and a['profile376_before_hex']==a['profile376_after_hex']and a['selection_canaries']==['c3'*16,'d7'*16]
        account=bytearray([0xa5]*368)
        for p in[196,244,256,268]:account[p:p+4]=bytes(4)
        assert account==bytes.fromhex(a['account368_before_hex']);check_cells('selected40',op['selected40_cells'],a['selected40_hex'])
        profile=bytearray(376);source=bytes.fromhex(a['profile376_before_hex']);profile[156:160]=struct.pack('<I',4);profile[168:172]=source[168:172];profile[172:176]=struct.pack('<I',6);profile[184:192]=struct.pack('<Q',int(seed));profile[224:240]=bytes(op['selected40_cells'][:16]);profile[344]=profile[345]=1;assert profile==source
        assert a['opening']['packets']==opening['packets']and a['opening']['projection']['rng_words']==opening['rng_words'];check_cells('openingGame',op['known_Game2592'],a['opening']['raw_game2592_hex']);counts['full_opening_packets']+=76;counts['full_opening_packet_bytes']+=sum(len(h)//2 for _,h in opening['packets'])
        assert a['before']['raw_game2592_hex']==a['opening']['raw_game2592_hex']and a['before']['packets']==a['opening']['packets']
        originalbg=copy.deepcopy(a['opening']['background']);expectedbg=copy.deepcopy(originalbg)
        for j,row in enumerate(expectedbg['units']['storage']):
            if c['dead_mask']>>j&1:expectedbg['units']['storage'][j]=(b'\x01\x00\x00\x00'+bytes.fromhex(row)[4:]).hex()
        assert expectedbg==a['before']['background'];counts['before_background_explicit_mask_only_full_bytes']+=sum(len(bytes.fromhex(h))for k in ['units','pickups','special','windows','boundaries']for h in originalbg[k]['storage'])
        for stage,want in [('before',before),('gain',gain)]+([]if selection is None else[('selection',selection['projection'])]):
            capture=a[stage];got=capture['projection'];game=bytes.fromhex(capture['raw_game2592_hex']);assert len(game)==2592
            for k,value in want.items():
                if k=='player_fields':
                    for key,v in value.items():assert got[k][key]==v;counts['known_logical_fields']+=1
                else:assert got[k]==value,(c['id'],stage,k);counts['projection_fields']+=1
            assert G.tree_fields(capture,game)==got['player_fields'];counts['full_raw_tree_captures_decoded']+=1
            assert game[2587]==want['phase2587']and game[2585]==want['selection_kind2585']and game[2581]==want['flag2581']and game[2573]==want['flags2573']and u(game,2348)==20544696
            for k,p in [('level',1432),('xp',1436),('pending',2376),('current_hp_bits',1440),('generation_counter2400',2400)]:assert u(game,p)==want[k]
            assert{str(1536+4*j):u(game,1536+4*j)for j in range(23)}==want['derived_bits']and[u(game,1720+4*j)for j in range(4)]==want['rng_words'];counts['derived23_values']+=23;counts['owned80_full_bytes']+=80*len(want['owned_records80_hex'])
            assert all(u(game,p)==0 for p in [1700,1676,2032,176,600,2056,2044,648,660,2116,2092,2104])and u(game,1792)==4 and u(game,1876)==2 and u(game,2128)==69 and u(game,2408)==85 and u(game,2412)==1
            bg=capture['background'];assert bg==a['before']['background'];counts['background_full_bytes_conserved']+=sum(len(bytes.fromhex(h))for k in ['units','pickups','special','windows','boundaries']for h in bg[k]['storage'])
            for k,w in background.items():
                actualbg=bg[k];assert w['count']==actualbg['count']and w['capacity']==actualbg['capacity']and len(w['storage'])==len(actualbg['storage'])
                for row,hx in zip(w['storage'],actualbg['storage'],strict=True):check_cells('background',row,hx)
            for k,p,stride in [('units',1784,432),('auxiliary',652,112),('claims',2108,88),('pickups',1868,56),('special',1916,40),('windows',1964,8),('boundaries',2120,8)]:assert bg[k]['capacity']==u(game,p)and bg[k]['pointer']==u(game,p+4)and bg[k]['count']==u(game,p+8)and bg[k]['stride']==stride
            assert bg['auxiliary']['count']==bg['claims']['count']==0 and bg['counter2408']==85 and bg['movement_sequence2412']==1
            assert capture['packets'][:76]==opening['packets']
            if stage=='gain':counts['phase2_three_cards']+=want['phase2587']==2 and len(want['candidates'])==3
            for card,hx in zip(want['candidates'],capture['raw_candidates80_hex'],strict=True):
                row=bytes.fromhex(hx);assert u(row,76)==card['tier'];counts['candidate_metadata_rows']+=1
                if card['variant']=='new':
                    d=definitions[card['ability_id']][1];assert u(row,60)==0x80000000 and u(row,64)==u(d,12)and u(row,68)==u(d,16)
                else:assert card['variant']=='upgrade'and(u(row,60)==0x80000001 or u(row,60)<0x80000000)and u(row,72)==0
            if stage=='selection':
                assert len(capture['live32_hex'])==u(game,1712)==1
                for cells,hx in zip(selection['live32_cells'],capture['live32_hex'],strict=True):check_cells('live32',cells,hx)
                chosen=gain['candidates'][index];selected[chosen['ability_id'],chosen['tier']]+=1
        assert(a['selection']is None)==(selection is None)
    assert(counts['background_known'],counts['background_None'],counts['background_nonzero_None'])==(63920,37456,27120)
    assert(counts['live32_known'],counts['live32_None'],counts['live32_nonzero_None'])==(240,80,80)and counts['phase2_three_cards']==10 and counts['full_opening_packets']==836
    assert masks=={0:9,1:1,15:1}and counts['full_raw_tree_captures_decoded']==32
    runtime=load(CASE/'runtime.json');terminal=load(CASE/'owned-terminal.json');assert runtime==comp['runtime']and terminal==comp['process']
    assert runtime['full_calls']=={'1093':10,'1108':11,'1600':11,'2945':11,'4677':11}and runtime['fresh_instances']==11 and runtime['stack_checks']==109 and runtime['allocator_calls']==55
    assert runtime['denied_imports']==882 and runtime['actual_host_calls']==0 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None
    assert len(runtime['target_and_setup_returns'])==54 and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])
    assert len(runtime['world_source_checks'])==54 and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
    assert not any(runtime[k]for k in ['old_Game_used_as_target','readiness_flags_injected','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games'])
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<120
    readback=load(CASE/'source-admission-readback.json');assert sha(CASE/'source-admission-readback.json')==hand['source_admission_readback_sha256']
    audit=load(CASE/'expectation-read-audit.json');assert audit['forbidden']==[]and all(not Path(p).suffix.lower()in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
    for n,h in hand['frozen_author_files'].items():assert sha(ROOT/n)==h
    for n,h in prep['frozen_v1_source_sha256'].items():assert sha(ROOT/n)==h
    for n,h in HELPERS.items():assert sha(ROOT/n)==h
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    (out/'independent-reference.json').write_text(json.dumps(reference,ensure_ascii=False,indent=2)+'\n')
    result=dict(status='pass_fullopening_inactive_world_first_gain_new_selection_projection',reviewer='/root/growth139_review',author='/root/growth139_world',comparison_sha256=COMP,handoff_sha256=HAND,reviewer_script_sha256=sha(Path(__file__)),helper_sha256=HELPERS,author_files=hand['frozen_author_files'],cases=11,full1108_calls=11,full4677_calls=11,full1093_calls=10,setup2945_calls=11,setup1600_calls=11,source_files=42,production_sources=32,source_edges=114,counts=dict(counts),dead_mask_cases=dict(masks),selected_new_cards=[dict(ability_id=k[0],tier=k[1],count=v)for k,v in sorted(selected.items())],current_function_bindings=functions,nonexport_sections_identical=True,reference_sha256=sha(out/'independent-reference.json'),reviewer_original_executions=0,reviewer_author_production_checker_builder_executions=0,author_process=terminal,runtime=runtime,seconds=time.monotonic()-started,limitations=['Originaluseslegalv2post1108resource-onlycontext,new2945/1600Game/full1108;notfreshApp/Rc/externref/bootstrap.','XPamountisanexplicitaward;deadmask1/15controlledmarkerfixtures,notnaturaldeathproducer. No NPC/vectorclearing;allrawbackground/pointers/countersconserved.','26364inactivepredicateverifiedcurrentWAT;movingNPC/nonemptyaux112/claims88andnonemptyliverecalculationremainpending. Sixauthorguardselfchecksaremodelonly,notoriginalcoverage.','Independentfullopeningandgrowthreferencesrecomputed;all836openingpacketschecked,subsequentfullgrowth/UI/appearance/Aura48/physicalBTreeallocationstreamremainsobservation.','556Gamebytesperopeningknown,unwrittenbackground/livecellsremainNone;observedfullrawconservationdoesnotresolveNonevalues.','OnlydefaultHumanWarrior/Elwynn/firstnewabilityselection andzeroNPCmotion;nofullmainloop/nativeWindows/network/save/completegame.'])
    (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts))))


if __name__=='__main__':main()
