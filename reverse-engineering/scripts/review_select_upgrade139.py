#!/usr/bin/env python3
"""Different-author current139 actual first-cleave upgrade review.

Only frozen independent reference helpers execute. Author production,
checkers, builders and original programs are never imported or executed.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_growth139 as G
import review_opening139 as O
import review_growth_world139 as W
import review_cast139 as C
from review_combat139 import sha,parse_module,local_closure,fp,bits,f32
from review_world_position139 import load_world

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/select-upgrade139-oracle-20261102T101111.568452Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
COMP='ca822cc51e9340587cb6c2d5f3bdcb51585db246ca2282682b316ca29f37781c'
HAND='8020a8bf852698f553f56052d87261559f13630d6898590e2c11d321765e5f85'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={**W.HELPERS,
 'scripts/review_growth_world139.py':'0e82a1f20fd7c02ed7edcd73f4d9edfca1d3ab406402e1aa8e0b5ae4e34322a1',
 'scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b'}
load=lambda p:json.loads(Path(p).read_text())
u=lambda raw,p=0:struct.unpack_from('<I',raw,p)[0]
save=lambda p,x:Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
TABLE_POINTERS=(5405004,5405040,5405076,5405112,5405148)


def upgrade(raw,kinds,tier,tables):
    """Exact rational→binary32 transcription of25511 and1093's orderedloop."""
    words=list(struct.unpack('<20I',raw));assert words[0]==5882740 and words[1]==1
    assert len(kinds)==(2 if tier==4 else 1) and len(set(kinds))==len(kinds)
    assert all(kind in(range(2)if tier==0 else range(3))for kind in kinds)
    trace=[]
    for kind in kinds:
        before=list(words);words[1]=(words[1]+1)&0xffffffff
        if kind==0:
            denominator=C.add(C.mul(C.rounded(Fraction(words[8])),0x3f000000),C.ONE)
            value=C.div(tables[0][tier],denominator)
            words[3]=C.mul(C.add(value,C.ONE),words[3])
        elif kind==1:
            factor=C.div(C.add(words[4],0xbe4ccccd),0x3f4ccccd)
            if C.rational(factor)<=0:factor=0
            value=C.mul(tables[1][tier],factor);words[4]=C.sub(words[4],value)
        else:
            amount=min(max(12-words[5],0),tables[2][tier]);value=C.rounded(Fraction(amount));words[5]=(words[5]+amount)&0xffffffff
        words[8+kind]=(words[8+kind]+1)&0xffffffff
        denominator=C.add(C.mul(C.rounded(Fraction(max(0,words[1]-2))),0x3e000000),C.ONE)
        tail=C.add(C.div(0x3d23d70a,denominator),C.ONE);words[3]=C.mul(tail,words[3])
        trace.append(dict(kind=kind,tier=tier,rank_before=before[1],rank_after=words[1],value_bits=value,tail_multiplier_bits=tail,words_before=before,words_after=list(words)))
    return struct.pack('<20I',*words).hex(),trace


def grow_and_select(before,case,classes,races,kit,definitions,cooldown,damage,tables,proof):
    state=copy.deepcopy(before);state['xp']=(state['xp']+case['amount'])&0xffffffff;events=[]
    while state['level']<=119 and state['xp']>=G.threshold(state['level']):
        old=state['level'];spent=G.threshold(old);state['xp']-=spent;state['pending']+=1;state['level']+=1;G.recalculate(state,classes,races)
        fields=state['player_fields'];fields['34']=state['level'];request=G.mul(state['derived_bits']['1536'],0x3e4ccccd);oldhp=state['current_hp_bits'];state['current_hp_bits']=min(G.add(oldhp,request),state['derived_bits']['1536']);fields['22']=math.ceil(fp(state['current_hp_bits']));fields['28']=math.ceil(fp(state['derived_bits']['1536']))
        events.append(dict(kind='level_up',before=old,after=state['level'],threshold_spent=spent,heal_request_bits=request,heal_delta_bits=G.sub(state['current_hp_bits'],oldhp)))
    state['player_fields'].update({'716':state['xp'],'717':G.threshold(state['level'])})
    if state['pending']:
        cards,words,draws=G.candidates(state['rng_words'],kit,state['level']);state.update(candidates=cards,rng_words=words,phase2587=2,selection_kind2585=0,generation_counter2400=1)
        events.append(dict(kind='candidate_choice',count=len(cards),draws=draws,inactive_world=proof))
    gain=copy.deepcopy(state);index=case['select_index'];assert state['pending']==1 and state['phase2587']==2 and len(state['candidates'])==3
    card=state['candidates'][index];trace=[]
    if card['variant']=='new':state['owned_records80_hex'].append(G.selected_record(card['ability_id'],card['tier'],definitions,cooldown,damage))
    else:
        assert card['variant']=='upgrade' and card['ability_id']=='cleave' and card['owned_index']==0
        state['owned_records80_hex'][0],trace=upgrade(bytes.fromhex(state['owned_records80_hex'][0]),card['kinds'],card['tier'],tables)
    G.recalculate(state,classes,races);state.update(pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=[])
    live=[None]*32;live[:8]=bytes(8);live[8:12]=struct.pack('<I',12);live[20:32]=struct.pack('<III',1020,0x3f800000,0)
    return gain,dict(projection=state,live32_cells=[live]),events,card,trace


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(BATCH/'comparison.json')==COMP and sha(BATCH/'task-handoff.json')==HAND and sha(SOURCE)==WASM
    for name,h in HELPERS.items():assert sha(ROOT/name)==h,name
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');manifest=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json')
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources'] and len(sources)==44
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for name,h in prep['frozen_v1_source_sha256'].items():assert sha(ROOT/name)==h
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges']) and len(edges)==128
    for table in(comp['artifacts'],comp['frozen'],prep['frozen']):
        for name,h in table.items():assert sha(BATCH/name)==h
    assert prep['expected_before_original']and not prep['original_input_contains_expected']and comp['forbidden_model_reads']==[]and prep['full_world_owners_retained']
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']==comp['resource_context_snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==comp['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    assert sha(Path(cfg['range_file']))==cfg['range_sha256'] and len(load(cfg['range_file']))==2318 and cfg['world_rc']==20544696
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==comp['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']))
    raw=SOURCE.read_bytes();original=parse_module(raw);private_raw=(BATCH/manifest['module_file']).read_bytes();private=parse_module(private_raw)
    assert len(original['sections'])==len(private['sections'])
    for a,b in zip(original['sections'],private['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
    additions=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),('research139_gw_select',0,1093),('research139_gw_stack',3,0)]
    assert private['exports']==original['exports']+additions and len(original['imports'])==882
    assert [(v['module'],v['name'])for v in original['imports']]==[(v['module'],v['name'])for v in manifest['original_imports']]
    def data(address,size):
        result=bytearray(size)
        for at,pos,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
        return bytes(result)
    word=lambda p:u(data(p,4));text=lambda p,n:data(p,n).decode();abilities={}
    for i in range(114):
        p=5882740+88*i;r=data(p,88);abilities[text(u(r,12),u(r,16))]=(p,r,tuple(data(u(r,36),u(r,40))))
    cls=data(5877920,108);kit=[text(p,n)for p,n in struct.iter_unpack('<II',data(u(cls,32),8*u(cls,36)))];definitions={k:abilities[k]for k in kit};classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)}
    race=data(5874636,44);racial=text(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);scalars['heading_bits']=u(zone,116);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];tables_heading=[list(struct.unpack('<4f',data(p,16)))for p in [14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888;definition=data(5830904,72)
    eligible=[j for j in range(12)if word(5830904+72*j+68)==1 and math.isfinite(fp(word(5830904+72*j+64)))];assert eligible==[9,10,11];minutes=word(u(zone,72)+336)
    cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20));tables=tuple(struct.unpack('<5I',data(p,20))for p in TABLE_POINTERS)
    assert list(TABLE_POINTERS)==manifest['upgrade_table_pointers'] and [list(t)for t in tables]==manifest['upgrade_tables139'] and definitions['cleave'][0]==5882740 and definitions['cleave'][1][84]==5
    literal={n.targets[0].id:ast.literal_eval(n.value)for n in ast.parse((ROOT/'reconstruction/core_spec/select_upgrade139.py').read_text()).body if isinstance(n,ast.Assign)}
    assert literal['UPGRADE_TABLE_POINTERS139']==TABLE_POINTERS and literal['UPGRADE_TABLES139']==tables
    functions={};texts={};db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    claims=manifest['functions']|manifest['extra_upgrade_functions']
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx in sorted(set(map(int,claims))|{11425,11499,50441,24602,33028,30628,29912}):
            a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);value=stream.read(end-start);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(value).hexdigest());functions[str(idx)]=proof;texts[idx]=value.decode();(out/f'{idx}.wat').write_bytes(value)
            if str(idx)in claims:
                assert proof['body_sha256']==claims[str(idx)]['body_sha256']and proof['WAT_sha256']==claims[str(idx)]['WAT_sha256']
                folder='upgrade-static'if idx==25511 else'static';assert value==(BATCH/folder/f'{idx}.wat').read_bytes()
    assert original['types'][original['decl'][25511-882]]==('7f7f7f','7d')
    for pointer in TABLE_POINTERS:assert f'load offset={pointer}'in texts[25511]
    assert 'f32.const 0x1p-1'in texts[25511] and'f32.const -0x1.99999ap-3'in texts[25511]and'f32.const 0x1.99999ap-1'in texts[25511]and'i32.const 12'in texts[25511]
    loop='\n'.join(texts[1093].splitlines()[816:956]);assert loop.index('i32.store offset=4')<loop.index('call 25511')<loop.index('i32.store\n') and'f32.const 0x1.47ae14p-5'in loop and'f32.const 0x1p-3'in loop
    assert all(s in texts[26364]for s in ['i32.load offset=1788','i32.load offset=1792','i32.const 432','i32.const 344','i32.const 340','i32.load offset=656','i32.load offset=660','i32.const 112','i32.load offset=2112','i32.load offset=2116','i32.const 88'])
    cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');actual=[json.loads(v)for v in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==19
    counts=Counter();variants=Counter();keys=Counter();reference=[];traces=[]
    def check_cells(label,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for i,(v,b)in enumerate(zip(want,seen)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case==e['input']and case['id']==e['id']==a['id'] and case['amount']==5 and case['dead_mask']==0
        op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,tables_heading,definition,speeds,classes,races,zones,eligible,minutes);opening=op['projection'];seed=op['constructor_seed_u64']
        initial,_=G.reference(dict(id=case['id'],seed_u64=seed,amount=0,select_index=None),classes,races,zones,kit,definitions,cooldown,damage);before=initial['before'];before['rng_words']=opening['rng_words'];rows=copy.deepcopy(opening['units']['storage']);proof=W.inactive(rows)
        gain,selection,events,chosen,trace=grow_and_select(before,case,classes,races,kit,definitions,cooldown,damage,tables,proof)
        background={k:copy.deepcopy(opening[k])for k in ['units','pickups','special','windows','boundaries']};answer=dict(before=before,gain=gain,selection=selection,selected_index=case['select_index'],selected_card=dict(variant=chosen['variant'],tier=chosen['tier'],kinds=chosen['kinds']),opening=opening,background=background,model_events=events,inactive_world_proof=proof)
        assert answer==e['expected'],('independent_expected',case['id']);reference.append(dict(id=case['id'],expected=answer));traces.append(dict(id=case['id'],card=chosen,ordered_steps=trace));variants[chosen['variant']]+=1
        if chosen['variant']=='upgrade':keys[chosen['tier'],tuple(chosen['kinds'])]+=1
        assert a['constructor_seed_u64']==seed and a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['stack_after']==1048576
        assert a['account368_before_hex']==a['account368_after_hex'] and a['profile376_before_hex']==a['profile376_after_hex'] and a['selection_canaries']==['c3'*16,'d7'*16]
        account=bytearray([0xa5]*368)
        for p in [196,244,256,268]:account[p:p+4]=bytes(4)
        assert account==bytes.fromhex(a['account368_before_hex']);check_cells('selected40',op['selected40_cells'],a['selected40_hex'])
        profile=bytearray(376);observed_profile=bytes.fromhex(a['profile376_before_hex']);profile[156:160]=struct.pack('<I',4);profile[168:172]=observed_profile[168:172];profile[172:176]=struct.pack('<I',6);profile[184:192]=struct.pack('<Q',int(seed));profile[224:240]=bytes(op['selected40_cells'][:16]);profile[344]=profile[345]=1;assert profile==observed_profile
        assert a['opening']['packets']==opening['packets'] and a['opening']['projection']['rng_words']==opening['rng_words'];check_cells('openingGame',op['known_Game2592'],a['opening']['raw_game2592_hex']);counts['full_opening_packets']+=76
        assert a['before']['raw_game2592_hex']==a['opening']['raw_game2592_hex'] and a['before']['background']==a['opening']['background']
        for stage,want in [('before',before),('gain',gain),('selection',selection['projection'])]:
            capture=a[stage];got=capture['projection'];game=bytes.fromhex(capture['raw_game2592_hex']);assert len(game)==2592
            for key,value in want.items():
                if key=='player_fields':
                    for field,v in value.items():assert got[key][field]==v;counts['known_player_fields']+=1
                else:assert got[key]==value,(case['id'],stage,key);counts['projection_fields']+=1
            assert G.tree_fields(capture,game)==got['player_fields'];counts['raw_tree_captures']+=1
            assert game[2587]==want['phase2587'] and game[2585]==want['selection_kind2585'] and game[2581]==want['flag2581'] and game[2573]==want['flags2573']
            for key,offset in [('level',1432),('xp',1436),('pending',2376),('current_hp_bits',1440),('generation_counter2400',2400)]:assert u(game,offset)==want[key]
            assert{str(1536+4*j):u(game,1536+4*j)for j in range(23)}==want['derived_bits'] and[u(game,1720+4*j)for j in range(4)]==want['rng_words'];counts['derived_values']+=23;counts['owned80_bytes']+=80*len(want['owned_records80_hex'])
            assert all(u(game,p)==0 for p in [1700,1676,2032,176,600,2056,2044,648,660,2116,2092,2104])and u(game,1792)==4 and u(game,1876)==2 and u(game,2128)==69 and u(game,2408)==85 and u(game,2412)==1
            bg=capture['background'];assert bg==a['before']['background'];counts['background_full_bytes_conserved']+=sum(len(bytes.fromhex(h))for k in ['units','pickups','special','windows','boundaries']for h in bg[k]['storage'])
            for k,v in background.items():
                seen=bg[k];assert v['count']==seen['count'] and v['capacity']==seen['capacity']
                for row,hx in zip(v['storage'],seen['storage'],strict=True):check_cells('background',row,hx)
            for k,p,stride in [('units',1784,432),('auxiliary',652,112),('claims',2108,88),('pickups',1868,56),('special',1916,40),('windows',1964,8),('boundaries',2120,8)]:assert bg[k]['capacity']==u(game,p) and bg[k]['pointer']==u(game,p+4) and bg[k]['count']==u(game,p+8) and bg[k]['stride']==stride
            assert capture['packets'][:76]==opening['packets']
            if stage=='gain':
                assert want['phase2587']==2 and len(want['candidates'])==3;counts['phase2_three_cards']+=1
                for card,hx in zip(want['candidates'],capture['raw_candidates80_hex'],strict=True):
                    row=bytes.fromhex(hx);assert u(row,76)==card['tier'];counts['candidate_rows']+=1
                    if card['variant']=='new':d=definitions[card['ability_id']][1];assert u(row,60)==0x80000000 and u(row,64)==u(d,12) and u(row,68)==u(d,16)
                    else:assert card['variant']=='upgrade' and(u(row,60)==0x80000001 or u(row,60)<0x80000000)and u(row,72)==0
            if stage=='selection':
                for row,hx in zip(selection['live32_cells'],capture['live32_hex'],strict=True):check_cells('live32',row,hx)
                assert u(game,1664)==(1 if chosen['variant']=='upgrade'else 2) and len(capture['live32_hex'])==u(game,1712)==1
    wanted={(t,(k,))for t in range(4)for k in range(2 if t==0 else 3)}|{(4,(a,b))for a in range(3)for b in range(3)if a!=b}
    assert set(keys)==wanted and len(keys)==17 and variants=={'upgrade':18,'new':1}
    assert len({json.dumps({k:v for k,v in row.items()if k!='id'},sort_keys=True)for row in cases})==18
    assert(counts['background_known'],counts['background_None'],counts['background_nonzero_None'])==(113988,66588,48177) and(counts['live32_known'],counts['live32_None'],counts['live32_nonzero_None'])==(456,152,152)
    assert counts['full_opening_packets']==1444 and counts['raw_tree_captures']==57
    runtime=load(BATCH/'runtime.json');terminal=load(BATCH/'owned-terminal.json');assert runtime==comp['runtime'] and terminal==comp['process']
    assert runtime['full_calls']=={'1093':19,'1108':19,'1600':19,'2945':19,'4677':19} and runtime['fresh_instances']==19 and runtime['stack_checks']==190 and runtime['allocator_calls']==95
    assert runtime['denied_imports']==882 and runtime['actual_host_calls']==0 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None
    assert len(runtime['target_and_setup_returns'])==95 and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])
    assert len(runtime['world_source_checks'])==95 and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
    assert not any(runtime[k]for k in ['old_Game_used_as_target','readiness_flags_injected','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games'])
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<120
    audit=load(BATCH/'expectation-read-audit.json');assert audit['forbidden']==[] and all(not Path(p).suffix.lower()in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
    search=load(BATCH/'model-input-search.json');assert search['last_seed_inclusive']==4923 and len(search['required_upgrade_keys'])==len(search['found_keys'])==17 and not search['actual_functions_executed'] and not search['original_program_reads']
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    save(out/'independent-reference.json',reference);save(out/'ordered-upgrade-traces.json',traces)
    result=dict(status='pass_current139_first_cleave_ordered_upgrade_selection',reviewer='/root/collection139_finish',author='/root/growth139_world',reviewer_script_sha256=sha(Path(__file__)),comparison_sha256=COMP,author_handoff_sha256=HAND,author_files=hand['frozen_author_files'],helper_sha256=HELPERS,cases=19,unique_inputs=18,full1108_calls=19,full4677_calls=19,full1093_calls=19,setup2945_calls=19,setup1600_calls=19,variants=dict(variants),reachable_upgrade_keys=[dict(tier=t,kinds=list(k),cases=n)for(t,k),n in sorted(keys.items())],counts=dict(counts),source_files=44,source_edges=128,current_function_bindings=functions,current_upgrade_tables=dict(zip(map(str,TABLE_POINTERS),tables)),all_nonexport_sections_identical=True,reference_sha256=sha(out/'independent-reference.json'),ordered_trace_sha256=sha(out/'ordered-upgrade-traces.json'),author_process=terminal,runtime=runtime,reviewer_original_executions=0,reviewer_author_production_checker_builder_executions=0,author_files_modified=False,seconds=time.monotonic()-started,limitations=['Explicit5XP award afteractualfull1108;not naturaldrop/collection inthismatrix.','Currentfirstconstructorcleave only;full80orderedrank/count/value/tail arithmetic checked,not repeated/saturated/otherability upgrade theorem.','17actualreachablekeys are2tier0+9tier1..3+6orderedtier4;25511table3/4staticdata bound butnot dynamicallyselected byfirstcleave.','All19actualcards derive fromfull4677/2181 andgivenseeds;model-only4923search metadata checked butsearch not reexecuted or counted asoriginal.','Legalv2post1108resource-onlycontext/newGame;independentraw-derivedcanonicalworld,notnaturalApp/Rc/externref/bootstrap.','Live32payload12..19 remainsNone;fullgrowth/UI/Aura48/physicalheap/allocator/extra keyed fields/packetstreams remainobservations.','No new original executions byreviewer;oldv1/v2receipts reused onlyasfrozenpure reference helpersreboundtocurrentbodies/data,not transferred acceptance.','ActiveNPC/aux/claims/nonemptylive statrecalculation/mainloop/nativeWindows/network/save/fullgame remainunknown.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
