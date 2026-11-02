#!/usr/bin/env python3
"""Independent current139 player/racial/live/Aura reference and frozen review."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_growth139 as G
import review_growth_world139 as W
import review_opening139 as O
import review_cast139 as C
from review_stats139 import reference as stats_reference
from review_initial139 import record as initial_record
from review_combat139 import sha,parse_module,local_closure,fp,bits
from review_world_position139 import load_world

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/player-update139-oracle-20261102T103206.417048Z'
EFFECTS=ROOT/'evidence/player-effects139-static-final-20261102T103000Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
COMP='4c2e613cd691eb84086d08fadb082d84ab57e86497031f90fa5a5e4682b13526'
HAND='bfd020f05de5151956a88a7ec544db9ec73be9c6616b458c360ce583b3c53bfc'
EFFECT_HAND='d8079e80161629b82a6bcd9a40f444a20db60d6a6be0ef9b5c0dc3c7e48b16d9'
EFFECT_TRACE='f9eb27b44fb76bbd79bd8a4caa95d5c3448494cd8a352cdb072a1d78d469dc48'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={**W.HELPERS,
 'scripts/review_growth_world139.py':'0e82a1f20fd7c02ed7edcd73f4d9edfca1d3ab406402e1aa8e0b5ae4e34322a1',
 'scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b'}
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda raw,p=0:struct.unpack_from('<I',raw,p)[0]


def read(row,p,n=4):
    cells=row[p:p+n];assert len(cells)==n and None not in cells,('Unknown actuallyread',p,n)
    return int.from_bytes(bytes(cells),'little')


def put(row,p,value):row[p:p+4]=struct.pack('<I',value)


def sync_aura(state):
    groups=[];now=state['g']['now_bits']
    for row in state['live'][:state['count']]:
        if C.rational(read(row,24))<=C.rational(now):continue
        spell=read(row,20);assert spell in(1020,20600) and spell not in [g[0]for g in groups]
        groups.append((spell,read(row,24),1))
    storage=[[0]*4+[None]*12 for _ in range(48)]
    for i,group in enumerate(groups):storage[i]=list(struct.pack('<4I',1,*group))
    def fields(rows):
        values={str(47+i):read(row,4)if read(row,0)else 0 for i,row in enumerate(rows)}
        for group in range(6):
            flags=0
            for i in range(group*8,group*8+8):
                if read(rows[i],0):flags|=(9 if i<32 else 8)<<(4*(i%8))
            values[str(95+group)]=flags
        for group in range(12):
            stacks=0
            for i in range(group*4,group*4+4):
                if read(rows[i],0):stacks|=max(min(read(rows[i],12),255)-1,0)<<(8*(i%4))
            values[str(113+group)]=stacks
        return values
    fresh=fields(storage);ready=state['aura_count']==48 and bool(state['aura_flag']&1)
    prior=fields(state['aura'])if ready else{}
    updates={key:value for key,value in fresh.items()if not ready or prior[key]!=value}
    state['g']['player_fields'].update(updates);state.update(aura=storage,aura_count=48,aura_flag=1)
    return updates


def recalculate(state,classes,races):
    g=state['g'];live=[]
    for row in state['live'][:state['count']]:
        kind=read(row,8);assert kind in(8,12)
        live.append(dict(kind=kind,value_bits=read(row,12)if kind==8 else 0,spell_id=read(row,20),expires_bits=read(row,24)))
    s=dict(class_byte=1,race_byte=1,level=g['level'],passives=[],adjustments=[],item_modifiers=[],owned_skills=[],timed_records=[],timed_definitions=[],live_effects=live,now_bits=g['now_bits'],old_max_hp_bits=g['derived_bits']['1536'],current_hp_bits=g['current_hp_bits'],conditional268_bits=0,flag2574=0,pool1532_bits=state['scalar']['1444'],pool1536_bits=state['scalar']['1448'],conditional1344_id=state['scalar']['1344'],conditional1348_bits=state['scalar']['1348'],pool768_bits=state['scalar']['764'],previous_speed_bits=state['scalar']['1648'])
    result=stats_reference(s,{1:classes[1]['hp_armor']},{1:races[1]['modifiers']},Counter())
    g.update(derived_bits=result['derived_bits'],current_hp_bits=result['current_hp_bits']);g['player_fields'].update(result['object_fields'])
    state['scalar'].update(result['auxiliary_bits']);state['scalar']['1648']=result['speed_bits']


def project(state):
    g=copy.deepcopy(state['g']);g.pop('now_bits',None)
    return dict(growth=g,racial80_hex=bytes(state['racial']).hex(),live=dict(capacity=len(state['live']),count=state['count'],storage=copy.deepcopy(state['live'])),aura=dict(capacity=state['aura_count'],count=state['aura_count'],flag2569=state['aura_flag'],storage=copy.deepcopy(state['aura'])),scalar=copy.deepcopy(state['scalar']),source_flags={str(p):0 for p in [387,548,768,770,772,908]},spell_sets=copy.deepcopy(state['sets']))


def distance(row,player):
    assert read(row,344)==0
    dx=C.sub(read(row,328),player[0]);dy=C.sub(read(row,332),player[1]);return C.add(C.mul(dx,dx),C.mul(dy,dy))


def attempt(state,spell):
    for row in state['sets']:
        if spell not in row:row.append(spell)


def tick(state,now,dt,classes,races,definitions,perception):
    state=copy.deepcopy(state);g=state['g'];g['now_bits']=now;state['scalar']['2352']=now
    prior_count=state['count'];retained=[i for i in range(prior_count)if C.rational(now)<C.rational(read(state['live'][i],24))]
    expired=[read(state['live'][i],20)for i in range(prior_count)if i not in retained]
    if expired:
        old=copy.deepcopy(state['live'])
        for j,i in enumerate(retained):state['live'][j]=old[i]
        state['count']=len(retained);recalculate(state,classes,races);sync_aura(state)
    for row in state['live'][:state['count']]:assert read(row,28)==0
    assert g['current_hp_bits']==g['derived_bits']['1536']
    extra=C.mul(g['derived_bits']['1536'],g['derived_bits']['1620'])if C.rational(C.sub(now,state['scalar']['1652']))>=3 else 0
    regen=C.mul(dt,C.add(g['derived_bits']['1576'],extra));timer=C.sub(state['scalar']['1628'],dt)
    alive=[row for row in state['NPC']if read(row,0)==0]
    if C.rational(timer)<=0:
        assert all(C.rational(distance(row,state['player']))>36 for row in alive),'Warrior basic target not quiet'
        timer=0x3e19999a
    state['scalar']['1628']=timer
    for index,hx in enumerate(g['owned_records80_hex']):
        raw=bytearray.fromhex(hx);pointer=u(raw);name=next(k for k,v in definitions.items()if v[0]==pointer);definition=definitions[name][1]
        remaining=C.sub(u(raw,8),dt)
        if C.rational(remaining)<=0:
            spell=u(definition,44);attempt(state,spell)
            if name=='cleave':assert definition[84]==5;radius=u(definition,56)
            else:
                assert name=='thunder_clap' and definition[84]==2 and u(definition)!=6
                radius=C.mul(C.mul(C.mul(g['derived_bits']['1580'],u(definition,60)),u(raw,24)),u(raw,64));assert C.rational(radius)<=70
            assert all(C.rational(distance(row,state['player']))>C.rational(C.mul(radius,radius))for row in alive),'Learned actual nearby target not quiet'
            remaining=0x3e4ccccd
        struct.pack_into('<I',raw,8,remaining);g['owned_records80_hex'][index]=raw.hex()
    remaining=C.sub(read(state['racial'],8),dt);put(state['racial'],8,remaining);packets=[];appended_index=None;nearby=[]
    if C.rational(remaining)<=0:
        attempt(state,20600);nearby=[read(row,112,8)for row in alive if C.rational(distance(row,state['player']))<=900]
        assert nearby,'Human racial actual30 query must not be disabled'
        packets.append([306,(bytes(2)+struct.pack('<IHBQBH',20600,256,1,0,0,0)).hex()])
        duration=C.mul(C.mul(C.mul(u(perception,68),0x3fb33333),read(state['racial'],28)),read(state['racial'],68));duration=duration if C.rational(duration)>C.rational(0x3dcccccd) else 0x3dcccccd
        value=C.mul(read(state['racial'],76),u(perception,4));expires=C.add(now,duration)
        # Real append32 writes28declared bytes and an unmodeled scratch word16.
        keep=[i for i in range(state['count'])if not(read(state['live'][i],20)==20600 and read(state['live'][i],0,8)==0)]
        old=copy.deepcopy(state['live'])
        for j,i in enumerate(keep):state['live'][j]=old[i]
        state['count']=len(keep)
        if state['count']==len(state['live']):state['live'].extend([[None]*32 for _ in range(max(4,2*len(state['live']))-len(state['live']))])
        appended_index=state['count'];row=list(state['live'][appended_index]);row[:16]=struct.pack('<QII',0,8,value);row[16:20]=[None]*4;row[20:32]=struct.pack('<III',20600,expires,0);state['live'][appended_index]=row;state['count']+=1
        recalculate(state,classes,races);sync_aura(state)
        remaining=C.mul(C.mul(C.mul(C.mul(u(perception,52),0x3fb33333),read(state['racial'],16)),read(state['racial'],56)),g['derived_bits']['1544']);remaining=max(remaining,0x3e800000)
        milliseconds=max(0,min(0xffffffff,int(C.rational(C.mul(remaining,0x447a0000)))))
        packets.extend([[308,struct.pack('<QII',0,20600,milliseconds).hex()],[309,struct.pack('<IQ',20600,0).hex()]])
        put(state['racial'],8,remaining)
    diagnostic=dict(expired_spells=expired,retained_source_indices=retained,expiry_recalculate1542_called=bool(expired),expiry_sync1173_called=bool(expired),regen_request_bits=regen,known_packets=packets,perception_appended_index=appended_index,actual30radius_reference_guids=[str(x)for x in nearby])
    return state,diagnostic


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(BATCH/'comparison.json')==COMP and sha(BATCH/'task-handoff.json')==HAND and sha(SOURCE)==WASM
    assert sha(EFFECTS/'task-handoff.json')==EFFECT_HAND and sha(EFFECTS/'trace.json')==EFFECT_TRACE
    for name,h in HELPERS.items():assert sha(ROOT/name)==h,name
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');manifest=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');effects=load(EFFECTS/'trace.json')
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources'] and len(sources)==45 and sum(n.startswith('reconstruction/')for n in sources)==35
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
    assert len(hand['frozen_author_files'])==11
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for table in(comp['artifacts'],comp['frozen'],prep['frozen']):
        for name,h in table.items():assert sha(BATCH/name)==h
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges']) and len(edges)==128
    assert prep['expected_before_original']and not prep['original_input_contains_expected']and comp['forbidden_model_reads']==[]and prep['full_world_owners_retained']and prep['external_clock_components']
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']==comp['resource_context_snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==comp['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    assert sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(cfg['range_file']))==2318 and cfg['world_rc']==20544696
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==comp['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']))
    raw=SOURCE.read_bytes();original=parse_module(raw);private_raw=(BATCH/manifest['module_file']).read_bytes();private=parse_module(private_raw)
    assert len(original['sections'])==len(private['sections'])
    for a,b in zip(original['sections'],private['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
    additions=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),('research139_gw_select',0,1093),('research139_gw_stack',3,0),('research139_pu_update2123',0,2123)]
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
    race=data(5874636,44);racial_name=text(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial_name][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    perception=data(5891892,88);assert perception.hex()==manifest['perception88_hex']==effects['perception_definition88_hex']and perception[84]==9 and u(perception)==8 and u(perception,4)==0x3e19999a
    assert data(5882740,88).hex()==manifest['cleave88_hex']and data(5882916,88).hex()==manifest['thunder_clap88_hex']and cls.hex()==manifest['warrior_class108_hex']
    zone=data(5871348,152);scalars['heading_bits']=u(zone,116);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];heading=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888;normal=data(5830904,72)
    eligible=[j for j in range(12)if word(5830904+72*j+68)==1 and math.isfinite(fp(word(5830904+72*j+64)))];assert eligible==[9,10,11];minutes=word(u(zone,72)+336)
    cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20));functions={};texts={}
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    claims=manifest['functions']|effects['functions'];extra={5719,8740,13563,1886,1446,11425,11499,50441,24602,6786,29912,33028,30628,25511,26364,25613}
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx in sorted(set(map(int,claims))|extra):
            a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);value=stream.read(end-start);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(value).hexdigest());functions[str(idx)]=proof;texts[idx]=value.decode();(out/f'{idx}.wat').write_bytes(value)
            if str(idx)in manifest['functions']:assert proof['body_sha256']==manifest['functions'][str(idx)]['body_sha256']and proof['WAT_sha256']==manifest['functions'][str(idx)]['WAT_sha256']and value==(BATCH/'static'/f'{idx}.wat').read_bytes()
            if str(idx)in effects['functions']:assert proof['body_sha256']==effects['functions'][str(idx)]['body_sha256']and proof['WAT_sha256']==effects['functions'][str(idx)]['WAT_sha256']and value==(EFFECTS/f'{idx}.wat').read_bytes()
    for window in effects['source_windows']:
        sliced='\n'.join(texts[window['index']].splitlines()[window['first_line_1based']-1:window['last_line_1based']]);assert sliced==window['text']
    assert original['types'][original['decl'][2123-882]]==original['types'][original['decl'][1238-882]]==('7f7d','')
    assert texts[2123].index('call 1542')<texts[2123].index('call 1173')<texts[2123].index('call 1238')
    assert 'i32.const 768\n      i32.const 4\n      call 108362'in texts[1173]and'i32.store offset=2004'in texts[1173]and'i32.load offset=2000'in texts[1173]
    assert 'i32.const 308'in texts[42159]and'i32.const 309'in texts[1238]and'f32.const 0x1.333334p-3'in texts[1238]
    cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==5 and[ len(c['updates'])for c in cases]==[8,10,10,116,11]
    counts=Counter();reference=[];diagnostics=[]
    def cells(label,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for i,(v,b)in enumerate(zip(want,seen)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    def player(capture,want,label):
        ref=want;got=capture['capture']['projection'];game=bytes.fromhex(capture['capture']['raw_game2592_hex'])
        assert ref['growth']==got,(label,'growth');assert G.tree_fields(capture['capture'],game)==got['player_fields'];counts['full_raw_tree_captures']+=1
        for key in['racial80_hex','scalar','source_flags','spell_sets']:assert ref[key]==capture[key],(label,key)
        for key,width in [('live',32),('aura',16)]:
            assert ref[key]['capacity']==capture[key]['capacity']and ref[key]['count']==capture[key]['count']
            if key=='aura':assert ref[key]['flag2569']==capture[key]['flag2569']
            for row,hx in zip(ref[key]['storage'],capture[key]['storage'],strict=True):assert len(row)==width;cells(key,row,hx)
        for p,v in ref['scalar'].items():assert u(game,int(p))==v
        assert game[2587]==1 and game[2585]==255 and game[2581]==1 and game[2573]==0 and game[360]==game[361]==1
        for k,p in [('level',1432),('xp',1436),('pending',2376),('current_hp_bits',1440),('generation_counter2400',2400)]:assert u(game,p)==got[k]
        assert{str(1536+4*j):u(game,1536+4*j)for j in range(23)}==got['derived_bits']and[u(game,1720+4*j)for j in range(4)]==got['rng_words'];counts['derived23_values']+=23
        assert bytes.fromhex(ref['racial80_hex'])==game[1256:1336]and u(game,1664)==2 and u(game,1712)==ref['live']['count'] and u(game,1704)==4 and u(game,2000)==u(game,2008)==48 and game[2569]==1
        for i,(base,countoff)in enumerate([(664,672),(676,684),(724,732)]):assert u(game,countoff)==len(ref['spell_sets'][i])and u(game,base)>=len(ref['spell_sets'][i])
        assert all(u(game,p)==0 for p in [552,1700,1676,2032,176,600,2056,2044,648,660,2116,2092,2104])and u(game,1792)==4 and u(game,1876)==2 and u(game,2128)==69 and u(game,2408)==85 and u(game,2412)==1
        counts['owned80_full_bytes']+=sum(len(bytes.fromhex(hx))for hx in got['owned_records80_hex']);counts['racial80_full_bytes']+=80;counts['complete_logical_player_fields']+=len(got['player_fields'])
    allowed=set()
    for start,end in [(1256,1336),(1440,1452),(1344,1352),(764,768),(1536,1632),(1648,1656),(1704,1716),(1880,1892),(2000,2012),(2476,2488),(664,688),(724,736),(2352,2356)]:allowed.update(range(start,end))
    allowed.add(2569)
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case==e['input'] and case['id']==e['id']==a['id'] and case['app_seed_u64']=='0' and case['amount']==5 and case['dead_mask']==0 and case['select_index']==0
        op,_=O.reference(dict(id=case['id'],app_seed_u64='0'),world,nav,scalars,heading,normal,speeds,classes,races,zones,eligible,minutes);opening=op['projection'];seed=op['constructor_seed_u64'];initial,_=G.reference(dict(id=case['id'],seed_u64=seed,amount=0,select_index=None),classes,races,zones,kit,definitions,cooldown,damage);before=initial['before'];before['rng_words']=opening['rng_words'];proof=W.inactive(opening['units']['storage']);gain,index,selection,events=W.grow(before,case,classes,races,kit,definitions,cooldown,damage,proof)
        assert opening==e['opening']and index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'
        for k,v in before.items():
            if k=='player_fields':assert all(a['before']['projection'][k][x]==y for x,y in v.items())
            else:assert a['before']['projection'][k]==v
        for stage,want in [('gain',gain),('selection',selection['projection'])]:
            for k,v in want.items():
                if k=='player_fields':assert all(a[stage]['projection'][k][x]==y for x,y in v.items())
                else:assert a[stage]['projection'][k]==v
        assert a['constructor_seed_u64']==seed and a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['stack_after']==1048576
        assert a['account368_before_hex']==a['account368_after_hex']and a['profile376_before_hex']==a['profile376_after_hex']and a['selection_canaries']==['c3'*16,'d7'*16]
        assert a['opening']['packets']==opening['packets'];cells('openingGame',op['known_Game2592'],a['opening']['raw_game2592_hex']);counts['complete_opening_packets']+=76
        for name in['units','pickups','windows','special','boundaries']:
            vector=a['opening']['background'][name];assert vector['capacity']==opening[name]['capacity']and vector['count']==opening[name]['count']
            for row,hx in zip(opening[name]['storage'],vector['storage'],strict=True):cells('opening_'+name,row,hx)
        for stage in['opening','before','gain','selection']:
            assert a[stage]['background']==a['opening']['background']and G.tree_fields(a[stage],bytes.fromhex(a[stage]['raw_game2592_hex']))==a[stage]['projection']['player_fields'];counts['prefix_raw_tree_captures']+=1
        assert a['player_before']['capture']['background']==a['opening']['background']
        state=dict(g=copy.deepcopy(selection['projection']),live=copy.deepcopy(selection['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]],NPC=copy.deepcopy(opening['units']['storage']),player=opening['player_xyz'])
        state['g']['now_bits']=0;sync_aura(state);first=project(state);assert first==e['initial'];player(a['player_before'],first,'initial');assert a['selection']['raw_game2592_hex']==a['player_before']['capture']['raw_game2592_hex']
        previous=a['player_before'];stages=[];case_diags=[]
        assert len(case['updates'])==len(e['stages'])==len(a['player_stages'])
        for j,(control,want,observation)in enumerate(zip(case['updates'],e['stages'],a['player_stages'],strict=True)):
            expected_input=bytearray.fromhex(previous['capture']['raw_game2592_hex']);put(expected_input,2352,control['now_bits']);actual_before=observation['before'];actual_after=observation['after'];assert expected_input.hex()==actual_before['capture']['raw_game2592_hex'];counts['full_Game_inherited_bytes']+=2592
            for key in['live','aura','racial80_hex','spell_sets']:assert previous[key]==actual_before[key]
            pre_count=state['count'];pre_state=copy.deepcopy(state);state,d=tick(state,control['now_bits'],control['dt_bits'],classes,races,definitions,perception);answer=project(state);assert answer==want,('independent_frame',case['id'],j);player(actual_after,answer,(case['id'],j));stages.append(answer);case_diags.append(d)
            for key in['expired_spells','retained_source_indices','expiry_recalculate1542_called','expiry_sync1173_called','regen_request_bits','known_packets']:assert d[key]==e['diagnostics'][j][key],(case['id'],j,key)
            before_packets=actual_before['capture']['packets'];after_packets=actual_after['capture']['packets'];assert after_packets[:len(before_packets)]==before_packets and after_packets[len(before_packets):]==d['known_packets'];counts['complete2123_packets']+=len(d['known_packets']);counts['complete2123_packet_bytes']+=sum(len(hx)//2 for _,hx in d['known_packets'])
            assert actual_after['capture']['background']==a['player_before']['capture']['background'];counts['background_raw_conserved_bytes']+=sum(len(bytes.fromhex(h))for key in['units','pickups','windows','special','boundaries']for h in actual_after['capture']['background'][key]['storage'])
            # Strict physical live replay: source32 copies and stale tail come
            # from actual input; only a genuinely unknown freshscratch16 is observed.
            source=[bytearray.fromhex(hx)for hx in actual_before['live']['storage']];physical=[bytearray(row)for row in source]
            for dest,src in enumerate(d['retained_source_indices']):physical[dest]=bytearray(source[src])
            slot=d['perception_appended_index'];after_live=[bytes.fromhex(hx)for hx in actual_after['live']['storage']]
            if slot is not None:
                assert not any(read(row,20)==20600 for row in pre_state['live'][:pre_count])
                for k,v in enumerate(state['live'][slot]):
                    if v is not None:physical[slot][k]=v
                physical[slot][16:20]=after_live[slot][16:20];counts['fresh_unknown_scratch_words_observed']+=1;counts['perception_successes_reference']+=1
            assert [bytes(row)for row in physical]==after_live;counts['live_physical_replay_bytes']+=sum(len(row)for row in physical)
            before_game=bytes.fromhex(actual_before['capture']['raw_game2592_hex']);after_game=bytes.fromhex(actual_after['capture']['raw_game2592_hex'])
            assert all(v==w for k,(v,w)in enumerate(zip(before_game,after_game))if k not in allowed),(case['id'],j,'undeclared Game write');counts['Game_nonowned_conserved_bytes']+=2592-len(allowed)
            counts['full2123_returns']+=1;counts['expired_live_sources']+=len(d['expired_spells']);counts['expiry_paths']+=bool(d['expired_spells']);previous=actual_after
        reference.append(dict(id=case['id'],initial=first,stages=stages));diagnostics.append(dict(id=case['id'],steps=case_diags))
    assert counts['full2123_returns']==155 and counts['expiry_paths']==counts['expired_live_sources']==6 and counts['perception_successes_reference']==5 and counts['fresh_unknown_scratch_words_observed']==5
    assert(counts['live_known'],counts['live_None'],counts['live_nonzero_None'])==(8172,12308,11543)and(counts['aura_known'],counts['aura_None'],counts['aura_nonzero_None'])==(32880,90000,77298)
    assert counts['complete2123_packets']==15 and counts['complete2123_packet_bytes']==240 and counts['complete_opening_packets']==380
    assert counts['full_Game_inherited_bytes']==401760 and counts['live_physical_replay_bytes']==19840
    runtime=load(BATCH/'runtime.json');terminal=load(BATCH/'owned-terminal.json');assert runtime==comp['runtime']and terminal==comp['process']
    assert runtime['full_calls']=={'1093':5,'1108':5,'1600':5,'2123':155,'2945':5,'4677':5}and runtime['fresh_instances']==5 and runtime['stack_checks']==205 and runtime['allocator_calls']==25
    assert runtime['denied_imports']==882 and runtime['actual_host_calls']==0 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None
    assert len(runtime['target_and_setup_returns'])==180 and all(r['returned']and r['before']==r['after']==1048576 for r in runtime['target_and_setup_returns'])and len(runtime['world_source_checks'])==180 and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
    assert not any(runtime[k]for k in ['old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games'])and runtime['input_dead_mask_all_zero']
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<120
    audit=load(BATCH/'expectation-read-audit.json');assert audit['forbidden']==[]and all(not Path(p).suffix.lower()in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
    assert sha(BATCH/'postcapture-physical-audit.json')==hand['postcapture_audit_sha256']=='d1e7c1c63de3a9443c7f53623e41089343b648d4e451e21fe86a8d94ecea1588'
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    save(out/'independent-reference.json',reference);save(out/'independent-diagnostics.json',diagnostics)
    result=dict(status='pass_current139_full2123_quiet_center_real_perception_and_live_expiry',reviewer='/root/collection139_finish',authors=['/root/growth139_review','/root/growth139_world'],reviewer_script_sha256=sha(Path(__file__)),comparison_sha256=COMP,author_handoff_sha256=HAND,author_files=hand['frozen_author_files'],helper_sha256=HELPERS,cases=5,full2123_calls=155,full1108_calls=5,full4677_calls=5,full1093_calls=5,setup2945_calls=5,setup1600_calls=5,counts=dict(counts),source_files=45,production_sources=35,source_edges=128,current_function_bindings=functions,all_nonexport_sections_identical=True,full2123_emitted_packets_in_this_domain_matched=True,reference_sha256=sha(out/'independent-reference.json'),diagnostics_sha256=sha(out/'independent-diagnostics.json'),author_process=terminal,runtime=runtime,reviewer_original_executions=0,reviewer_author_model_checker_builder_executions=0,author_files_modified=False,supplemental_effects_trace_sha256=EFFECT_TRACE,supplemental_author_audit_bound_but_not_used_as_independent_reference=True,seconds=time.monotonic()-started,limitations=['Real2123/1238 incontrolledcenter/firstthunder_clap/fullHP/defaultsources/4stationaryaliveNPC domain only;notfull884/AI/input/motion.','PrefixXP5isanexplicitaward,notthenaturaldrop/collectionprefix;noNPC/racial/CD/sourceclearing orphase0bypass.','Human30radiuspredicate re-evaluated fromcurrentknownNPCpositions;perceptiongenuinekind8value12=.15,expiry14.5,live12expiry1. Source16scratchremainsNone.','Strictlive32physicalretain/staletail independentlyreplayed19840B;only5newunknownscratchwords observed20B,notmodelcompleted.','1173fresh768B Aura owner eachrebuild meansinactivepayloadNone;physicalheap/BTreeaddresses notpredicted. Full72logicalkeymap inthisdomain matched.','15emitted2123packets306/308/309 complete here;fullprefixgrowth/UI/otherpresentation/networkstreamnotclaimed.','Canonicalworldinputwaspreviouslyindependentlyraw-produced;originalresource-onlyhealthyv2snapshot/newGame,notnaturalApp/Rc/externref/bootstrap.','Sixexpiry/5perceptionpaths are reference-derived;internal1238/1542/1173notdirectlyinstrumented.','Positivehealing/otherlearnedskills/near-targetdamage/otherlive8or9/perceptionnotargetor30boundary/repeatedracial/mainloop/native/save/completegame remainunknown.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
