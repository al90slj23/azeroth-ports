#!/usr/bin/env python3
"""Different-author current139 real922slow→925 review;0author/originalexec."""
from pathlib import Path
from collections import Counter,deque
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_enemy_ai139 as A
import review_thunder_clap139 as T
from review_combat139 import sha,parse_module,local_closure,fp,bits
C=A.C;O=A.O;G=A.G;W=A.W;P=A.P;I=A.I;D=T.D;U=T.U
word=A.word;put=A.put;lt=A.lt;le=A.le;minimum=A.minimum;maximum=A.maximum
sqrt32=A.sqrt32;distance=A.distance;trig=A.trig;probe=A.probe
breadth_first=A.breadth_first;segment=A.segment;position=A.position;packet221=A.packet221
ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/enemy-ai-status139-full-20261102T113858.277631Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMP='d8623785177e37973cb70d204248c73c6bbe0e2246113f5fafbafa08b7e48b9c'
HAND='03ebcf09283760d55eed35991a94271313bc76956ce50a636762079b69a020f5'
HELPERS={**A.HELPERS,**T.HELPERS,'scripts/review_enemy_ai139.py':'73b093bdfcc59c08c010fb2c074298435b6d0f057fe15a0e5d2a8228c0fe0f42','scripts/review_thunder_clap139.py':'775b8234a04067711ac126eb0ded2ce90a553db396f1bd26e07f5662fdbe0b23'}
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]

def tick(state,now,dt,player,world,nav,neighbors,names,english,counts):
    state=copy.deepcopy(state);assert C.sub(now,state['now'])==dt;state['now']=now;state['player']=player
    if state['path']is None or (probe(nav,player[:2])[1]!=state['path']['start_index'] and not lt(C.sub(now,state['path_clock']),0x3e4ccccd)):

        state['path'],values=breadth_first(nav,player,neighbors);state['path_values']=values;state['path_clock']=now;recomputed=True;counts['path_rebuilds']+=1;counts['BFS_values']+=len(values)
    else:
        recomputed=False
    motions=[];attacks=[];routing=[]
    for row in state['rows']:
        assert all(word(row,p)==0xffffffff for p in(40,64,244))and word(row,284)==5830904 and row[424]==0
        assert all(word(row,p)==0 for p in(0,8,16,240,360,380,388,396,416,420))
        if lt(now,word(row,408)):continue
        pos=position(row,now);timer=C.sub(word(row,352),dt);put(row,352,timer);target=word(row,112,8)
        if le(distance(pos,player),word(row,308)):
            if lt(0,word(row,344))and lt(now,C.add(word(row,340),word(row,344))):
                for k,v in enumerate(pos):put(row,316+4*k,v);put(row,328+4*k,v)
                put(row,340,now);put(row,344,0);motions.append((target,pos,pos,0))
            if le(timer,0)and le(word(row,412),now):
                put(row,352,word(row,304));weak=word(row,128)if lt(now,word(row,132))else word(row,136)if lt(now,word(row,140))else 0
                attacks.append([target,C.mul(word(row,296),C.sub(C.ONE,weak))])
            continue
        if lt(now,word(row,348)):continue
        angle=C.add(word(row,404),0x3e19999a);put(row,404,angle);sine,cosine=trig(angle)
        radius=maximum(C.mul(word(row,308),0x3f4ccccd),0x3fc00000)
        dest=(C.add(player[0],C.mul(radius,cosine)),C.add(player[1],C.mul(radius,sine)),player[2]);length=distance(pos,dest)
        if lt(0x41600000,length):
            factor=C.div(0x41600000,length);dest=(C.add(pos[0],C.mul(C.sub(dest[0],pos[0]),factor)),C.add(pos[1],C.mul(C.sub(dest[1],pos[1]),factor)),pos[2]);counts['clamped14_motions']+=1
        assert segment(nav,pos,dest,counts)==C.ONE,'Blocked-flow branch remains Pending; do not reuse old acceptance'
        routing.append([target,'direct_clear']);counts['direct_clear_routes']+=1
        speed=word(row,300)
        if lt(now,word(row,124)):speed=C.mul(speed,C.sub(C.ONE,word(row,120)))
        if lt(now,word(row,412)):speed=C.mul(speed,0x3faccccd)
        duration=C.div(distance(pos,dest),maximum(speed,0x3f000000))
        for k,v in enumerate(pos):put(row,316+4*k,v)
        for k,v in enumerate(dest):put(row,328+4*k,v)
        put(row,340,now);put(row,344,duration);put(row,348,C.add(now,minimum(maximum(duration,0x3e800000),0x3f333333)));motions.append((target,pos,dest,duration))
    packets=[]
    for target,start,end,duration in motions:
        state['sequence']=(state['sequence']+1)&0xffffffff;packets.append(packet221(world,target,start,end,duration,state['sequence'],counts))
    for target,amount in attacks:
        damage=C.mul(amount,C.sub(C.ONE,state['derived']['1568']));shown=max(1,int(C.rational(damage)))
        packets.append([330,(struct.pack('<I',2)+C.packguid(target)+C.packguid(0)+struct.pack('<I',shown)+b'\1'+struct.pack('<IfI6I',0,float(shown),shown,0,0,1,0,0,0)).hex()])
        counts['contact_attempts']+=1
        if any(word(row,8)==12 and lt(now,word(row,24)) for row in state['live']):
            counts['guard12_contact_attempts']+=1
            continue
        assert all(state['guards'][p]==0 for p in state['guards'])and C.rational(state['hp'])>C.rational(damage)
        state['hp']=C.sub(state['hp'],damage);state['last']=now;state['incoming']+=fp(damage);state['category']+=fp(damage);state['has_category']=True
        source=next(row for row in state['rows']if word(row,112,8)==target);assert word(source,284)in names and source[424]==0
        I.append_ring(state['history'],now,fp(damage),0.,fp(state['hp']),state['derived']['1536'],(names[word(source,284)],english['Melee'],'INV_Sword_04'),0,0)
        state['fields'].update({'22':math.ceil(fp(state['hp'])),'28':math.ceil(fp(state['derived']['1536']))});counts['contacts']+=1
    state['packets'].extend(packets)
    answer=dict(frame=state['frame'],records=copy.deepcopy(state['rows']),hp1440_bits=state['hp'],last_hit1652_bits=state['last'],incoming992_hex=struct.pack('>d',state['incoming']).hex(),categories={'mob melee':struct.pack('>d',state['category']).hex()}if state['has_category']else{},fields=copy.deepcopy(state['fields']),history=I.ring_projection(state['history']),path=copy.deepcopy(state['path']),path_clock2372_bits=state['path_clock'],movement_sequence2412=state['sequence'],packets=copy.deepcopy(state['packets']),attacks=attacks,motions=motions,routing=routing,path_recomputed=recomputed)
    state['frame']+=1;counts['frames']+=1;counts['movement221']+=len(motions);return state,answer


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir(exist_ok=True)
    assert sha(SOURCE)==WASM and sha(BATCH/'comparison.json')==COMP and sha(BATCH/'task-handoff.json')==HAND
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');manifest=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json')
    for n,h in HELPERS.items():assert sha(ROOT/n)==h,n
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==82 and sum(n.startswith('reconstruction/')for n in sources)==70
    for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h,n
    assert len(hand['frozen_author_files'])==6
    for n,h in hand['frozen_author_files'].items():assert sha(ROOT/n)==h,n
    for table in(comp['frozen'],comp['artifacts'],prep['frozen']):
        for n,h in table.items():assert sha(BATCH/n)==h,n
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==291
    for n in sources:
        if not n.startswith('reconstruction/'):continue
        for node in ast.walk(ast.parse((ROOT/n).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;label=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                assert label not in('open','read_bytes','read_text','write_bytes','write_text','Popen','system','eval','exec','__import__'),(n,label)
    assert comp['differences']==0 and comp['cases']==comp['completed_cases']==4 and comp['phase']=='full'and prep['expected_before_original']and not prep['original_input_contains_expected']and prep['controlled_player_position_only']and prep['all_source_owners_retained']
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==comp['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    assert sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(cfg['range_file']))==2318 and cfg['world_rc']==20544696
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==comp['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world,nav,scalars=P.load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']))
    raw=SOURCE.read_bytes();original=parse_module(raw);private_raw=(BATCH/manifest['module_file']).read_bytes();private=parse_module(private_raw)
    assert len(original['sections'])==len(private['sections'])and len(original['imports'])==882
    for a,b in zip(original['sections'],private['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
    additions=[('research139_gw_companion',0,2945),('research139_gw_initial',0,1600),('research139_gw_opening',0,1108),('research139_gw_gain',0,4677),('research139_gw_select',0,1093),('research139_gw_stack',3,0),('research139_status_cast922',0,922),('research139_status_tick925',0,925)]
    assert private['exports']==original['exports']+additions==original['exports']+[tuple(v)for v in manifest['added_exports']]
    def data(address,size):
        result=bytearray(size)
        for at,pos,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
        return bytes(result)
    text=lambda p,n:data(p,n).decode();worddata=lambda p:u(data(p,4));abilities={}
    for i in range(114):
        p=5882740+88*i;r=data(p,88);abilities[text(u(r,12),u(r,16))]=(p,r,tuple(data(u(r,36),u(r,40))))
    cls=data(5877920,108);classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};kit=[text(p,n)for p,n in struct.iter_unpack('<II',data(u(cls,32),8*u(cls,36)))];definitions={k:abilities[k]for k in kit}
    race=data(5874636,44);racial_name=text(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial_name][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);scalars['heading_bits']=u(zone,116);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];heading=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888;normal=data(5830904,72)
    eligible=[j for j in range(12)if worddata(5830904+72*j+68)==1 and math.isfinite(fp(worddata(5830904+72*j+64)))];assert eligible==[9,10,11];minutes=worddata(u(zone,72)+336);cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20))
    neighbors=list(struct.iter_unpack('<ii',data(5408444,64)));assert neighbors==[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
    english=json.loads(data(*struct.unpack('<II',data(5401532,8))));p,n,identifier=struct.unpack('<III',data(5830920,12));names={5830904:english.get('enemy.'+str(identifier),text(p,n))};assert names[5830904]=='Kobold Vermin'
    definition=data(5882916,88);assert definition.hex()==manifest['thunder88_hex']and definition[84]==2 and u(definition)==1
    functions={};texts={};extra={8740,13563,1886,1446,24602,6786,33028,30628,25511,26364,25613,8673,20123,36364,66546,52397}
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx in sorted(set(map(int,manifest['functions']))|extra):
            a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);value=stream.read(end-start);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(value).hexdigest());functions[str(idx)]=proof;texts[idx]=value.decode();(out/f'{idx}.wat').write_bytes(value)
            if str(idx)in manifest['functions']:assert all(proof[k]==manifest['functions'][str(idx)][k]for k in proof)and value==(BATCH/'static'/f'{idx}.wat').read_bytes()
    assert original['types'][original['decl'][925-882]]==('7f7d','')and original['types'][original['decl'][922-882]]==('7f7f','7f')
    assert all(t in texts[925]for t in['i32.store offset=2368','i32.const 5408444','i32.const 65535','call 30179','call 29237','call 1076','f32.load offset=2372','f32.const 0x1.99999ap-3'])
    assert all(t in texts[81682]for t in['f32.load offset=120','f32.load offset=124','f32.load offset=300'])
    assert all(t in texts[1076]for t in['i32.const 12','f32.load offset=2352','f32.store offset=1440','f32.store offset=1652'])
    area='\n'.join(texts[922].splitlines()[800:1170]);assert area.index('call 27754')<area.index('call 10490')<area.index('call 913')<area.index('call 2189')
    for key,proof in manifest['static_reads'].items():
        address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==proof['sha256']
    cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==4
    assert [v['updates'][23]['now_bits']for v in cases]==[0x40400000,0x403fffff,0x40400001,0x40400000]
    counts=Counter();reference=[];boundaries=[]
    def cells(label,want,hx):
        got=bytes.fromhex(hx);assert len(want)==len(got)
        for j,(v,w)in enumerate(zip(want,got)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(w)
            else:assert v==w,(label,j,v,w);counts[label+'_known']+=1
    def player(observed,want):
        assert observed['capture']['projection']==want['growth']and G.tree_fields(observed['capture'],bytes.fromhex(observed['capture']['raw_game2592_hex']))==want['growth']['player_fields']
        for k in['racial80_hex','scalar','source_flags','spell_sets']:assert observed[k]==want[k],k
        for k in['live','aura']:
            for field in['capacity','count']+(['flag2569']if k=='aura'else[]):assert observed[k][field]==want[k][field]
            for row,hx in zip(want[k]['storage'],observed[k]['storage'],strict=True):cells(k,row,hx)
        counts['player72_values']+=len(want['growth']['player_fields']);counts['derived23_values']+=len(want['growth']['derived_bits'])
    allowed=set()
    for start,size in((968,16),(992,8),(1112,12),(1440,4),(1652,4),(1880,12),(2368,8),(2412,4),(2476,12)):allowed.update(range(start,start+size))
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case==e['input']and case['id']==e['id']==a['id']and case['amount']==5 and case['select_index']==0 and case['app_seed_u64']=='0'
        op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,heading,normal,speeds,classes,races,zones,eligible,minutes);opening=op['projection'];assert opening==e['opening']
        init,_=G.reference(dict(id=case['id'],seed_u64=op['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,definitions,cooldown,damage);before=init['before'];before['rng_words']=opening['rng_words'];gain,index,selection,_=W.grow(before,case,classes,races,kit,definitions,cooldown,damage,W.inactive(opening['units']['storage']));assert index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'
        assert a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['constructor_seed_u64']==op['constructor_seed_u64']and a['stack_after']==1048576
        assert a['account368_before_hex']==a['account368_after_hex']and a['profile376_before_hex']==a['profile376_after_hex']and a['selection_canaries']==['c3'*16,'d7'*16]
        assert a['opening']['packets']==opening['packets'];cells('openingGame',op['known_Game2592'],a['opening']['raw_game2592_hex'])
        for k,want in[('before',before),('gain',gain),('selection',selection['projection'])]:
            for key,value in want.items():
                if key=='player_fields':assert all(a[k]['projection'][key][x]==y for x,y in value.items())
                else:assert a[k]['projection'][key]==value
            assert G.tree_fields(a[k],bytes.fromhex(a[k]['raw_game2592_hex']))==a[k]['projection']['player_fields']and a[k]['background']==a['opening']['background']
        for name in['units','pickups','windows','special','boundaries']:
            v=a['opening']['background'][name];assert(v['capacity'],v['count'])==(opening[name]['capacity'],opening[name]['count'])
            for row,hx in zip(opening[name]['storage'],v['storage'],strict=True):cells('opening_'+name,row,hx)
        ps=dict(g=copy.deepcopy(selection['projection']),live=copy.deepcopy(selection['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(T.initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]]);ps['g']['now_bits']=0;U.sync_aura(ps);initial=U.project(ps);assert initial==e['initial'];player(a['player_before'],initial)
        rows=copy.deepcopy(opening['units']['storage']);action=case['action'];anchor=rows[action['npc_index']];positions=[]
        for key,hkey in[('initial_offset_x_bits','initial_height_bits'),('retarget_offset_x_bits','retarget_height_bits')]:
            xy=[C.add(word(anchor,316),action[key]),word(anchor,320)];height=world.height(*xy);assert height==action[hkey];positions.append(xy+[height])
        assert positions==e['player_positions']and action['retarget_offset_x_bits']==0xc1000000 and action['initial_offset_x_bits']in(0,0x41000000)
        rawpre=bytearray.fromhex(a['player_before']['capture']['raw_game2592_hex'])
        for j,value in enumerate(positions[0]):put(rawpre,1416+4*j,value)
        assert rawpre.hex()==a['before_thunder']['capture']['raw_game2592_hex'];player(a['before_thunder'],initial)
        derived={int(k):v for k,v in selection['projection']['derived_bits'].items()};owned=bytes.fromhex(selection['projection']['owned_records80_hex'][1]);assert u(owned)==5882916 and u(owned,4)==1 and derived[1548]==0x3d4ccccd
        cs=dict(rows=rows,words=tuple(selection['projection']['rng_words']),counter=opening['counter'],total=0,spelltotals={},kills=0,elites=0,cost=0,sets=[[],[],[]],pickups=copy.deepcopy(opening['pickups']['storage']),pickup_count=2,sequence=1)
        answer,diag=T.cast(cs,positions[0],0,derived,definition,owned,world,scalars,speeds,normal,counts);assert answer['success']==a['cast_success']==1 and len(diag['selected_ids'])==1
        assert diag['selected_ids']==e['cast_selected_ids']and diag['known_packets']==e['cast_known_packets']and [[int(g),o,v]for g,o,v in diag['effect_writes']]==e['cast_effect_writes']
        assert all(answer[k]==v for k,v in e['cast_outgoing'].items());assert all(a['after_thunder_combat'][k]==v for k,v in e['cast_outgoing'].items())
        assert cs['kills']==0 and cs['sequence']==1 and cs['pickup_count']==2
        for row,hx,oldhx in zip(cs['rows'],a['after_thunder']['capture']['background']['units']['storage'],a['before_thunder']['capture']['background']['units']['storage'],strict=True):
            cells('castNPC',row,hx);physical=bytearray.fromhex(oldhx)
            for k,value in enumerate(row):
                if value is not None:physical[k]=value
            assert physical.hex()==hx;counts['producer_NPC_full_physical_replay_bytes']+=432
        ps['g']['rng_words']=list(cs['words']);ps['sets']=copy.deepcopy(cs['sets']);post=U.project(ps);assert post==e['post_cast_player'];player(a['after_thunder'],post)
        slowed=[str(word(row,112,8))for row in cs['rows']if word(row,120)==0x3f000000 and word(row,124)==0x40400000];assert slowed==e['slowed_guids']and len(slowed)==a['actual_slowed_count']==1
        cursor=0
        for packet in diag['known_packets']:
            at=next(k for k in range(cursor,len(a['thunder_new_packets']))if a['thunder_new_packets'][k]==packet);cursor=at+1;counts['upstream_known_packets']+=1
        state=dict(rows=copy.deepcopy(cs['rows']),now=0,frame=0,player=positions[0],path=None,path_values=None,path_clock=0,sequence=1,hp=post['growth']['current_hp_bits'],last=0xc1200000,incoming=0.,category=0.,has_category=False,derived=post['growth']['derived_bits'],guards={p:0 for p in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(post['growth']['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=[],live=copy.deepcopy(ps['live'][:ps['count']]))
        previous=a['after_thunder'];frames=[];assert len(case['updates'])==len(e['stages'])==len(a['frames'])==36
        for j,(control,wanted,diagnostic,observed)in enumerate(zip(case['updates'],e['stages'],e['diagnostics'],a['frames'],strict=True)):
            xyz=positions[int(control['retarget'])];now,dt=control['now_bits'],control['dt_bits'];assert control['retarget']==(j>=23)
            inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);put(inherited,2352,now)
            for k,value in enumerate(xyz):put(inherited,1416+4*k,value)
            assert inherited.hex()==observed['before']['capture']['raw_game2592_hex'];counts['inherited_Game2592_bytes']+=2592
            for key in['live','aura','racial80_hex','spell_sets','source_flags']:assert previous[key]==observed['before'][key]
            assert previous['capture']['background']==observed['before']['capture']['background']and previous['capture']['packets']==observed['before']['capture']['packets']
            oldrows=copy.deepcopy(state['rows']);prior=len(state['packets']);state,ai=tick(state,now,dt,xyz,world,nav,neighbors,names,english,counts);new_packets=state['packets'][prior:]
            guard=any(word(row,8)==12 and lt(now,word(row,24))for row in state['live']);proofs=[]
            #Motions are reconstructed from actual reference record writes, not authorproofs.
            for row,oldrow in zip(state['rows'],oldrows,strict=True):
                if word(row,340)==now and (word(row,344)!=word(oldrow,344)or word(row,340)!=word(oldrow,340)) and lt(0,word(row,344)):
                    active=lt(now,word(oldrow,124));speed=word(oldrow,300)
                    if active:speed=C.mul(speed,C.sub(C.ONE,word(oldrow,120)))
                    if lt(now,word(oldrow,412)):speed=C.mul(speed,0x3faccccd)
                    proofs.append([word(oldrow,112,8),word(oldrow,120),word(oldrow,124),active,speed,word(row,344)])
            assert proofs==diagnostic['motion_speed_proofs'],(case['id'],j,'independent_speedproof')
            assert ai['attacks']==diagnostic['attacks']and json.loads(json.dumps(ai['motions']))==diagnostic['motions']and ai['routing']==diagnostic['routing']and ai['path_recomputed']==diagnostic['path_recomputed']and guard==diagnostic['active_guard12']
            counts['active_guard12_frames']+=guard;counts['slow_motion_proofs']+=sum(p[3]for p in proofs);counts['unslow_motion_proofs']+=sum(not p[3]for p in proofs)
            ps['g']['current_hp_bits']=state['hp'];ps['g']['player_fields']=copy.deepcopy(state['fields']);ps['scalar']['2352']=now;ps['scalar']['1652']=state['last'];wp=U.project(ps)
            wa=dict(records432_cells=copy.deepcopy(state['rows']),history=ai['history'],path=ai['path'],path_clock2372_bits=ai['path_clock2372_bits'],incoming992_hex=ai['incoming992_hex'],last_hit1652_bits=ai['last_hit1652_bits'],categories=ai['categories'],movement_sequence2412=state['sequence'])
            assert dict(player=wp,ai=wa,new_packets=new_packets)==wanted,(case['id'],j,'independent_reference')
            player(observed['after'],wp);postcapture=observed['after']['capture'];rawgame=bytes.fromhex(postcapture['raw_game2592_hex'])
            for key in['path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories']:assert observed['ai'][key]==wa[key],(case['id'],j,key)
            assert observed['ai']['history']['header']==wa['history']['header']and observed['ai']['history']['active']==wa['history']['active']
            for row,hx,oldhx in zip(wa['records432_cells'],postcapture['background']['units']['storage'],observed['before']['capture']['background']['units']['storage'],strict=True):
                cells('NPC',row,hx);physical=bytearray.fromhex(oldhx)
                for k,value in enumerate(row):
                    if value is not None:physical[k]=value
                assert physical.hex()==hx;counts['NPC_full_physical_replay_bytes']+=432
            for row,hx in zip(wa['history']['storage'],observed['ai']['history']['storage'],strict=True):cells('history',row,hx)
            assert new_packets==observed['new_packets']and postcapture['packets']==observed['before']['capture']['packets']+new_packets;counts['AI_packets']+=len(new_packets);counts['AI_packet_bytes']+=sum(len(p[1])//2 for p in new_packets)
            for key in['live','aura','racial80_hex']:assert observed['after'][key]==a['player_before'][key]
            for key in['pickups','special','windows','boundaries','auxiliary','claims','counter2408']:assert postcapture['background'][key]==a['after_thunder']['capture']['background'][key]
            counts['background_conserved_bytes']+=sum(len(bytes.fromhex(hx))for key in['pickups','special','windows','boundaries']for hx in postcapture['background'][key]['storage'])
            pregame=bytes.fromhex(observed['before']['capture']['raw_game2592_hex']);assert all(x==y for k,(x,y)in enumerate(zip(pregame,rawgame))if k not in allowed);counts['Game_nonowned_conserved_bytes']+=2592-len(allowed)
            assert u(rawgame,1712)==1 and u(rawgame,1664)==2 and u(rawgame,1792)==u(rawgame,1784)==4 and u(rawgame,2352)==now and u(rawgame,1440)==state['hp']and u(rawgame,1652)==state['last']and u(rawgame,2348)==20544696
            if j in(23,24,25,26,27,28):boundaries.append(dict(id=case['id'],frame=j,now_bits=now,duration_bits=word(state['rows'][0],344),motion_start_bits=word(state['rows'][0],340),deadline_bits=word(state['rows'][0],348),slow_until_bits=word(state['rows'][0],124)))
            previous=observed['after'];frames.append(dict(player=wp,ai=wa,new_packets=new_packets))
        reference.append(dict(id=case['id'],initial=initial,post_cast=post,frames=frames))
    assert counts['frames']==144 and counts['full922']==4 and counts['damage_calls']==4 and counts['deaths']==0 and counts['contact_attempts']==6 and counts['guard12_contact_attempts']==1 and counts['contacts']==5 and counts['path_rebuilds']==8 and counts['BFS_values']==627200
    assert counts['AI_packets']==102 and counts['AI_packet_bytes']==4856 and counts['NPC_full_physical_replay_bytes']==248832 and counts['inherited_Game2592_bytes']==373248
    for key in['active_guard12_frames','slow_motion_proofs','unslow_motion_proofs','history_known','history_None','history_nonzero_None']:assert counts[key]==comp['counts'][key],key
    for suffix in['known','None','nonzero_None']:assert counts['NPC_'+suffix]+counts['castNPC_'+suffix]==comp['counts']['NPC_'+suffix],suffix
    assert counts['producer_NPC_full_physical_replay_bytes']==6912
    boundary_at={r['id']:r for r in boundaries if r['frame']==23};assert boundary_at[1]['duration_bits']==0x4082a89e and boundary_at[0]['duration_bits']==boundary_at[2]['duration_bits']==0x4002a89e
    below=[r for r in boundaries if r['id']==1];assert all(r['duration_bits']==0x4082a89e for r in below)and all(r['slow_until_bits']==0x40400000 for r in below)
    runtime=load(BATCH/'runtime.json');terminal=load(BATCH/'owned-terminal.json');assert runtime==comp['runtime']and terminal==comp['process']==hand['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']
    assert runtime['full_calls']=={'922':4,'925':144,'1093':4,'1108':4,'1600':4,'2945':4,'4677':4}and runtime['fresh_instances']==4 and runtime['allocator_calls']==20 and runtime['stack_checks']==188 and runtime['denied_imports']==882 and runtime['actual_host_calls']==0 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None
    assert len(runtime['target_and_setup_returns'])==168 and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])and len(runtime['world_source_checks'])==168 and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
    for k in['old_Game_used_as_target','readiness_flags_injected','NPC_state_writes_by_driver','source_headers_cleared','live_racial_CD_cleared','HP_filled_or_reset','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games']:assert not runtime[k],k
    audit=load(BATCH/'expectation-read-audit.json');assert audit['forbidden']==[]and all(Path(p).suffix.lower()not in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
    for n,h in hand['frozen_author_files'].items():assert sha(ROOT/n)==h,n
    for n,h in HELPERS.items():assert sha(ROOT/n)==h,n
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    save(out/'independent-reference.json',reference);save(out/'independent-boundaries.json',boundaries)
    result=dict(status='pass_current139_real922slow_to_full925_status_expiry_continuity',reviewer='/root/growth139_review',author='/root/collection139_finish',reviewer_authored_lower_Thunder_dependency_but_not_this_composition=True,frozen_prior_independent_review_helpers_only=True,helper_authorship_note="PriorA/Tindependentreviewhelperswerewrittenbeforethiscompositionbyitscurrentauthor;newreviewerrebindsallcurrentbodiesandrecomputesnewretarget/guard/expirycompositionwithoutauthorproductionexecution.",reviewer_script_sha256=sha(Path(__file__)),author_handoff_sha256=HAND,comparison_sha256=COMP,author_files=hand['frozen_author_files'],helper_sha256=HELPERS,counts=dict(counts),cases=4,full925=144,real922_producer_calls=4,prefix_each2945_1600_1108_4677_1093=4,current_function_bindings=functions,all_nonexport_sections_identical=True,source_files=82,production_files=70,source_edges=291,author_process=terminal,runtime=runtime,independent_reference_sha256=sha(out/'independent-reference.json'),independent_boundaries_sha256=sha(out/'independent-boundaries.json'),postcapture_author_audit_used_as_reference=False,prior_reviewer_run=dict(path='evidence/enemy-ai-status139-independent-owned-20261102T115449.197224Z',exit_code=1,reason='Onlyfinalcounttaxonomyassertion:authorNPCcountsinclude4postcastcaptures;referenceNPCcountsseparatecastNPCand144AIframes. Allperframereference/actualcomparisonscompletedbeforethisassertion;newreviewrerunrequired.'),reviewer_original_executions=0,reviewer_author_production_checker_builder_executions=0,author_files_modified=False,seconds=time.monotonic()-started,limitations=['Direct922 atcontrolledplayerposition followed bystandalone925 explicitclock/retarget;no2123/1238/full884,naturalinput,positive regeneration orcomplete game.','Allmotionroutes inthismatrixdirect_clear;blocked-flow/generalclasses,statuses/Boss/fatal/shield/proc familiesPending.','Oneactualselectedlive12 rowretained physically evenafterexpiry;itskind/expiryguard verifiedwithoutreadingunknown12..19 payload;AIdoesnotremoveit.','Fullnew925packetstream102/4856Bindependentlymatched;upstream922known306subsetonly,otherdamage/HP/UIpacketsremainobservations.','Historyresourcepointers/allocatorunwrittenbytesandAura inactivebytesremainNone;completeheap/pointer/bootstrap/externref/native/network/save/Androidgameoutsideclaim.','Authorpostcaptureboundaryauditnotused;newreferencefromcurrentWAT,exactFraction f32,canonicalworldBFS,andfrozenindependentreviewhelpers.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
