#!/usr/bin/env python3
"""Independent current139 area2 Thunder review of two frozen original batches."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_cast139 as C
import review_death139 as D
import review_growth139 as G
import review_growth_world139 as W
import review_opening139 as O
import review_player_update139 as U
from review_initial139 import record as initial_record
from review_world_position139 import load_world
from review_combat139 import sha,parse_module,local_closure,fp,bits

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
BATCHES=[('thunder-clap139-oracle-20261102T105223.121403Z','40286b855097ce0eed7f0bb41d74c18f4fd9e6d5240073b2dfc45dc5f2c5dd2a','d79779483e6b6bc9aa55c6b67fdb55518ab725cba70057dab4ce42a66677f44f',18,47,54,42,167),('thunder-clap-world139-oracle-20261102T110226.182643Z','bffbc17cd69348ef11c5f0d3479f977edfe01d9bebadc6bcb380597d214326e5','639f6a304828caa77a1d5a2aedb56b8354c479266ade3142d611769f5588a1a1',9,72,56,43,185)]
HELPERS={**W.HELPERS,**U.HELPERS,**{'scripts/'+k:v for k,v in D.HELPERS.items()},'scripts/review_death139.py':'fe7790f0adcb3e3d5010d53c44f375bec5bbee6d3fe780873a6e1613afe11e6a','scripts/review_player_update139.py':'4123e0715620c0d050bfad0c1c060b0fc5b426c36d0789c95a0c7801d52c8bde'}
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]


def position(row,now):
    duration=D.read(row,344)
    if C.rational(duration)<=0:return tuple(D.read(row,p)for p in(328,332,336))
    t=C.div(C.sub(now,D.read(row,340)),duration);t=0 if C.rational(t)<0 else C.ONE if C.rational(t)>1 else t
    return tuple(C.add(D.read(row,a),C.mul(C.sub(D.read(row,b),D.read(row,a)),t))for a,b in((316,328),(320,332),(324,336)))


def launch(targets):return(bytes(2)+struct.pack('<IHB',6343,256,len(targets))+b''.join(struct.pack('<Q',g)for g in targets)+bytes(3)).hex()


def decode_launch(hx):
    raw=bytes.fromhex(hx);assert raw[:2]==bytes(2);spell,flags,n=struct.unpack_from('<IHB',raw,2);targets=list(struct.unpack_from('<'+'Q'*n,raw,9))
    assert spell==6343 and flags==256 and raw[9+8*n:]==bytes(3)and len(raw)==12+8*n
    return targets


def cast(s,player,now,derived,definition,owned,world,scalars,speeds,npc_def,counts):
    radius=C.mul(derived[1580],C.mul(C.u(definition,60),C.mul(C.u(owned,24),C.u(owned,64))));assert C.rational(radius)<=70
    rows=s['rows'];chosen=[];square=C.mul(radius,radius)
    for i,row in enumerate(rows):
        if D.read(row,0)==0 and C.le(C.distance(position(row,now),player),square):
            distance=C.distance(position(row,now),player);at=len(chosen)
            while at and C.totalkey(chosen[at-1][1])>C.totalkey(distance):at-=1
            chosen.insert(at,(i,distance))
    ids=[D.read(rows[i],112,8)for i,_ in chosen]
    for ledger in s['sets']:
        if 6343 not in ledger:ledger.append(6343)
    value=C.mul(C.mul(C.mul(C.mul(C.u(definition,48),0x3fb33333),C.u(owned,12)),C.u(owned,52)),0x3f000000)
    life=C.mul(derived[1536],C.u(owned,72))if C.rational(C.u(definition,48))>0 else 0;base=C.mul(derived[1540],C.add(value,life))
    packets=[[306,launch(ids)]]if ids else[];hits=[];writes=[]
    for i,_ in chosen:
        row=rows[i];target=D.read(row,112,8);roll,s['words']=D.uniform24(s['words']);critical=int(C.rational(derived[1548])>C.rational(roll));amount=C.mul(base,derived[1552])if critical else base
        assert all(D.read(row,p)==0xffffffff for p in(40,64,244))and D.read(row,284)==5830904 and row[424]==0 and D.read(row,240)==0
        mult=C.ONE
        if C.rational(now)<C.rational(D.read(row,148)):mult=C.add(mult,D.read(row,144))
        term=D.read(row,152)if C.rational(now)<C.rational(D.read(row,156))else D.read(row,160)if C.rational(now)<C.rational(D.read(row,164))else 0
        mult=C.add(C.add(C.add(mult,term),D.read(row,368)),0);school=0x3dcccccd if definition[85]&254==2 and C.rational(now)<C.rational(D.read(row,372))else 0
        damage=C.mul(C.mul(amount,C.add(mult,school)),C.ONE);damage=damage if C.rational(damage)>1 else C.ONE
        old=D.read(row,288);hp=C.sub(old,damage);actual=min(max(C.rational(old),0),C.rational(damage));s['total']=C.bits64(C.f64(s['total'])+float(actual));s['spelltotals'][6343]=C.bits64(C.f64(s['spelltotals'].get(6343,0))+float(actual));D.put(row,288,hp)
        dead=C.rational(hp)<=0;rewards=[];direct=0;counts['damage_calls']+=1;counts['positive_critical_hits']+=critical
        if dead:
            assert D.read(row,344)==0,'Moving death is outside accepted scope'
            xyz=position(row,now);D.put(row,0,1);D.put(row,4,now);D.put(row,240,0);row[316:328]=struct.pack('<3I',*xyz);row[328:340]=struct.pack('<3I',*xyz);D.put(row,340,now);D.put(row,344,0)
            s['kills']=(s['kills']+1)&C.M;s['elites']=(s['elites']+(row[424]&1))&C.M;s['cost']=C.add(C.u(npc_def,60),s['cost']);counts['deaths']+=1
            random,s['words']=D.uniform24(s['words']);direct+=1;scaled=C.mul(C.rounded(Fraction(C.u(npc_def,56))),0x3fd33333);whole=int(C.rational(scaled));fraction=C.sub(scaled,C.rounded(Fraction(whole)));xp=whole+int(C.rational(fraction)>C.rational(random))
            if xp:
                packet,event=D.pickup(0,xp,xyz,world,scalars,speeds,s);D.put(s['pickups'][s['pickup_count']-1],52,now);packets.append(packet);rewards.append(['XP',xp,int(event['guid']),event['position_bits'],None])
            random,s['words']=D.uniform24(s['words']);direct+=1
            if C.rational(random)<C.rational(0x3e28f5c3):
                draws=0
                while True:
                    word,s['words']=C.nextword(s['words']);draws+=1;assert draws<10000;product=word*3
                    if product&C.M<=0xbfffffff:break
                direct+=draws;currency=(product>>32)+2;coinxyz=[C.add(xyz[0],0x3f4ccccd),C.add(xyz[1],0x3f4ccccd),xyz[2]];packet,event=D.pickup(1,currency,coinxyz,world,scalars,speeds,s);D.put(s['pickups'][s['pickup_count']-1],52,now);packets.append(packet);rewards.append(['currency',currency,int(event['guid']),event['position_bits'],None])
        #2189 runs after913 and excludes marker1, so killing hits have no slow.
        if D.read(row,0)!=1:
            assert D.read(row,376)==0
            expiry=C.add(now,C.mul(C.u(definition,8),C.u(owned,68)));strength=C.u(definition,4)
            for offset,value in[(124,expiry),(120,strength),(376,0)]:D.put(row,offset,value);writes.append([str(target),offset,value])
            assert D.read(row,356)==0,'Empty event49 inherited branch must preserve U356'
        hits.append(dict(target=str(target),amount_bits=amount,critical=critical,dead=dead,applied=True,direct_reward_draws=direct,rewards=rewards))
    result=dict(records432_cells=copy.deepcopy(rows),rng_words=list(s['words']),accounted_total_bits=str(s['total']),spell_sets=copy.deepcopy(s['sets']),owned80_hex=owned.hex(),player_xyz=list(player),phase2587=1,spell_totals64=[[k,str(v)]for k,v in sorted(s['spelltotals'].items())],kills1084=s['kills'],elites1088=s['elites'],counter2408=s['counter'],movement_sequence2412=s['sequence'],killcost2420_bits=s['cost'],player_hp1440_bits=derived[1536],maximum1536_bits=derived[1536],xp1436=0,pickup_capacity=len(s['pickups']),pickup_count=s['pickup_count'],pickups56_cells=copy.deepcopy(s['pickups']),success=int(bool(ids)))
    diagnostic=dict(selected_ids=list(map(str,ids)),base_damage_bits=base,radius_bits=radius,effect_writes=writes,hits=hits,known_packets=packets,enqueued_hits=[],enqueued_areas=[])
    counts['full922']+=1;counts['successful_casts']+=bool(ids);counts['multi_target_casts']+=len(ids)>1;counts['max_targets']=max(counts['max_targets'],len(ids));counts['slow_write_operations']+=len(writes)
    return result,diagnostic


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(SOURCE)==WASM
    for name,h in HELPERS.items():assert sha(ROOT/name)==h,name
    raw=SOURCE.read_bytes();original=parse_module(raw)
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
    zone=data(5871348,152);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];heading=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));spawn_speeds=list(speeds);spawn_speeds[1]=1088421888;normal=data(5830904,72)
    eligible=[j for j in range(12)if worddata(5830904+72*j+68)==1 and math.isfinite(fp(worddata(5830904+72*j+64)))];assert eligible==[9,10,11];minutes=worddata(u(zone,72)+336);cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20));definition=data(5882916,88);assert definition[84]==2 and u(definition)==1 and u(definition,44)==6343 and data(1601276,4)==struct.pack('<I',0x3f000000)
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));scalars['heading_bits']=u(zone,116)
    functions={};texts={};db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    extra={5719,8740,13563,1886,1446,11425,11499,50441,24602,6786,29912,33028,30628,25511,26364,25613,36518,48064,36367,20060,1466}
    batch_results=[];all_author_files={}
    for batchname,handoffsha,comparisonsha,ncases,ncasts,nsrc,nprod,nedges in BATCHES:
        batch=ROOT/'evidence'/batchname;assert sha(batch/'task-handoff.json')==handoffsha and sha(batch/'comparison.json')==comparisonsha
        hand=load(batch/'task-handoff.json');comp=load(batch/'comparison.json');prep=load(batch/'prepared.json');manifest=load(batch/'manifest.json');cfg=load(batch/'config.json');sources=comp['sources_before'];all_author_files.update(hand['frozen_author_files'])
        assert sources==comp['sources_after']==prep['sources']and len(sources)==nsrc and sum(n.startswith('reconstruction/')for n in sources)==nprod
        for name,h in sources.items():assert sha(ROOT/name)==sha(batch/'source-snapshot'/name)==h,name
        assert len(hand['frozen_author_files'])==6
        for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h,name
        for table in(comp['artifacts'],comp['frozen'],prep['frozen']):
            for name,h in table.items():assert sha(batch/name)==h,name
        assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(comp['source_import_edges'])==nedges
        for name in sources:
            if name.startswith('reconstruction/'):
                for node in ast.walk(ast.parse((ROOT/name).read_text())):
                    if isinstance(node,ast.Call):
                        fn=node.func;label=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else'';assert label not in('open','read_bytes','read_text','write_bytes','write_text','Popen','system','eval','exec','__import__'),(name,label)
        assert comp['differences']==0 and comp['cases']==comp['completed_cases']==ncases and comp['fullworld_objects_retained']and prep['full_world_owners_retained']and prep['controlled_player_placement']and prep['expected_before_original']and not prep['original_input_contains_expected']and comp['forbidden_model_reads']==[]
        assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']==comp['resource_context_snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
        assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==comp['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
        assert sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(cfg['range_file']))==2318 and cfg['world_rc']==20544696 and comp['independent_world_receipt_sha256']==sha(wp)
        private_raw=(batch/manifest['module_file']).read_bytes();private=parse_module(private_raw)
        assert len(original['sections'])==len(private['sections'])and len(original['imports'])==882
        for a,b in zip(original['sections'],private['sections']):
            assert a['kind']==b['kind']
            if a['kind']!=7:assert raw[a['start']:a['end']]==private_raw[b['start']:b['end']]
        assert private['exports']==original['exports']+[tuple(v)for v in manifest['added_exports']]and [v[2]for v in private['exports'][len(original['exports']):]if v[1]==0]==[2945,1600,1108,4677,1093,922,1775,3755]
        assert definition.hex()==manifest['thunder_clap88_hex']and data(5882740,88).hex()==manifest['cleave88_hex']and data(1601276,28).hex()==manifest['coefficient1601276_hex']
        with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
            for idx in sorted(set(map(int,manifest['functions']))|extra):
                a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);value=stream.read(end-start);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(value).hexdigest());functions[str(idx)]=proof;texts[idx]=value.decode();(out/f'{idx}.wat').write_bytes(value)
                if str(idx)in manifest['functions']:assert all(proof[k]==manifest['functions'][str(idx)][k]for k in proof)and value==(batch/'static'/f'{idx}.wat').read_bytes()
        assert original['types'][original['decl'][922-882]]==('7f7f','7f')and all(t in texts[922]for t in['f32.load offset=1601276','call 27754','call 10490','call 913','call 2189'])
        area=texts[922].splitlines()[800:1170];area='\n'.join(area);assert area.index('call 27754')<area.index('call 10490')<area.index('call 913')<area.index('call 2189')
        assert 'i32.load offset=2056'in texts[2189]and'i32.const 49'in texts[2189]and all('i32.const '+str(v)in texts[2189]for v in[120,124,356,376])and'i32.const 1\n                                    local.set 9'in texts[2189]
        cases=load(batch/'inputs.json');expected=load(batch/'expected.json');actual=[json.loads(x)for x in(batch/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==ncases
        counts=Counter();reference=[];diagnostics=[]
        def cells(label,want,hx):
            got=bytes.fromhex(hx);assert len(want)==len(got)
            for j,(v,w)in enumerate(zip(want,got)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(w)
                else:assert v==w,(batchname,label,j,v,w);counts[label+'_known']+=1
        def initial_player(observation,want):
            assert observation['capture']['projection']==want['growth']and G.tree_fields(observation['capture'],bytes.fromhex(observation['capture']['raw_game2592_hex']))==want['growth']['player_fields']
            for k in['racial80_hex','scalar','source_flags','spell_sets']:assert observation[k]==want[k]
            for k in['live','aura']:
                for field in['capacity','count']+(['flag2569']if k=='aura'else[]):assert observation[k][field]==want[k][field]
                for row,hx in zip(want[k]['storage'],observation[k]['storage'],strict=True):cells('initial_'+k,row,hx)
        for case,e,a in zip(cases,expected,actual,strict=True):
            assert case==e['input']and case['id']==e['id']==a['id']and case['amount']==5 and case['dead_mask']==case['select_index']==0
            op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,heading,normal,spawn_speeds,classes,races,zones,eligible,minutes);opening=op['projection'];initial,_=G.reference(dict(id=case['id'],seed_u64=op['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,definitions,cooldown,damage);before=initial['before'];before['rng_words']=opening['rng_words'];gain,index,selection,_=W.grow(before,case,classes,races,kit,definitions,cooldown,damage,W.inactive(opening['units']['storage']));assert index==0 and gain['candidates'][0]['ability_id']=='thunder_clap'
            if 'actual_card_tier'in e:assert gain['candidates'][0]['tier']==e['actual_card_tier']
            for stage,want in[('before',before),('gain',gain),('selection',selection['projection'])]:
                for k,v in want.items():
                    if k=='player_fields':assert all(a[stage]['projection'][k][x]==y for x,y in v.items())
                    else:assert a[stage]['projection'][k]==v
                assert G.tree_fields(a[stage],bytes.fromhex(a[stage]['raw_game2592_hex']))==a[stage]['projection']['player_fields']and a[stage]['background']==a['opening']['background'];counts['prefix_tree_captures']+=1
            assert a['opening']['packets']==opening['packets'];cells('openingGame',op['known_Game2592'],a['opening']['raw_game2592_hex']);counts['opening_packets']+=len(opening['packets'])
            for name in['units','pickups','windows','special','boundaries']:
                vector=a['opening']['background'][name];assert vector['capacity']==opening[name]['capacity']and vector['count']==opening[name]['count']
                for row,hx in zip(opening[name]['storage'],vector['storage'],strict=True):cells('opening_'+name,row,hx)
            assert a['constructor_seed_u64']==op['constructor_seed_u64']and a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['stack_after']==1048576
            assert a['account368_before_hex']==a['account368_after_hex']and a['profile376_before_hex']==a['profile376_after_hex']and a['selection_canaries']==['c3'*16,'d7'*16]
            ps=dict(g=copy.deepcopy(selection['projection']),live=copy.deepcopy(selection['live32_cells'])+[[None]*32 for _ in range(3)],count=1,aura=[],aura_count=0,aura_flag=None,racial=list(bytes.fromhex(initial_record(5891892))),scalar={str(k):v for k,v in[(2352,0),(1628,0),(1444,0),(1448,0),(1344,0),(1348,0),(764,0),(1648,0x40e00000),(1652,0xc1200000)]},sets=[[],[],[]]);ps['g']['now_bits']=0;U.sync_aura(ps);player_initial=U.project(ps);assert player_initial==e['initial'];initial_player(a['player_before'],player_initial)
            rows=copy.deepcopy(opening['units']['storage']);action=case['action']
            if 'npc_index'in action:
                row=rows[action['npc_index']];player=[C.add(D.read(row,316),action['offset_x_bits']),C.add(D.read(row,320),action['offset_y_bits']),D.read(row,324)]
            else:
                aa,bb=rows[action['first']],rows[action['second']];player=[C.mul(C.add(D.read(aa,p),D.read(bb,p)),0x3f000000)for p in(316,320)];height=world.height(*player);assert height==action['height_bits'];player.append(height)
            assert player==e['player_xyz'];pre=a['player_before'];controlled=a['controlled_before'];game=bytearray.fromhex(pre['capture']['raw_game2592_hex'])
            for j,v in enumerate(player):D.put(game,1416+4*j,v)
            assert game.hex()==controlled['capture']['raw_game2592_hex']and pre['capture']['background']==controlled['capture']['background']
            for k in['live','aura','racial80_hex','source_flags','scalar','spell_sets']:assert pre[k]==controlled[k]
            assert a['constructor_counters']==dict(accounted_total_bits='0',spell_totals64=[],kills1084=0,elites1088=0,movement_sequence2412=1,killcost2420_bits=0)
            derived={int(k):v for k,v in selection['projection']['derived_bits'].items()};assert derived[1548]==0x3d4ccccd
            owned=bytes.fromhex(selection['projection']['owned_records80_hex'][1]);assert C.u(owned)==5882916 and C.u(bytes.fromhex(selection['projection']['owned_records80_hex'][0]))==5882740
            s=dict(rows=rows,words=tuple(selection['projection']['rng_words']),counter=opening['counter'],total=0,spelltotals={},kills=0,elites=0,cost=0,sets=[[],[],[]],pickups=copy.deepcopy(opening['pickups']['storage']),pickup_count=2,sequence=1);previous=controlled;stages=[];case_d=[]
            assert len(case['casts'])==len(e['stages'])==len(e['diagnostics'])==len(a['cast_stages'])
            for j,(now,want,expected_diag,obs)in enumerate(zip(case['casts'],e['stages'],e['diagnostics'],a['cast_stages'],strict=True)):
                inherited=bytearray.fromhex(previous['capture']['raw_game2592_hex']);D.put(inherited,2352,now);assert inherited.hex()==obs['before']['capture']['raw_game2592_hex'];counts['inherited_Game2592_bytes']+=2592
                for k in['live','aura','racial80_hex','source_flags','spell_sets']:assert previous[k]==obs['before'][k]
                assert previous['capture']['background']==obs['before']['capture']['background']and previous['capture']['packets']==obs['before']['capture']['packets']
                assert obs['before_combat']['records432_hex']==obs['before']['capture']['background']['units']['storage']and obs['before_combat']['pickups56_hex']==obs['before']['capture']['background']['pickups']['storage']
                answer,diag=cast(s,player,now,derived,definition,owned,world,scalars,speeds,normal,counts);assert answer==want,(batchname,case['id'],j,'independent_state');assert diag==expected_diag,(batchname,case['id'],j,'independent_diag');stages.append(answer);case_d.append(diag)
                combat=obs['combat'];assert obs['after_cast']==obs['after']and obs['empty_consumers_Game2592_unchanged'];post=obs['after'];rawgame=bytes.fromhex(post['capture']['raw_game2592_hex']);growth=post['capture']['projection']
                for k,v in answer.items():
                    if k=='records432_cells':
                        for row,hx,oldhx in zip(v,combat['records432_hex'],obs['before_combat']['records432_hex'],strict=True):
                            cells('NPC',row,hx);physical=bytearray.fromhex(oldhx)
                            for offset,value in enumerate(row):
                                if value is not None:physical[offset]=value
                            assert physical.hex()==hx;counts['NPC_full_physical_replay_bytes']+=432
                    elif k=='pickups56_cells':
                        for index,(row,hx)in enumerate(zip(v,combat['pickups56_hex'],strict=True)):
                            cells('pickup',row,hx)
                            if index<len(obs['before_combat']['pickups56_hex']):
                                physical=bytearray.fromhex(obs['before_combat']['pickups56_hex'][index])
                                for offset,value in enumerate(row):
                                    if value is not None:physical[offset]=value
                                assert physical.hex()==hx;counts['pickup_existing_owner_physical_replay_bytes']+=56
                    else:assert combat[k]==v,(case['id'],j,k)
                assert combat['records432_hex']==post['capture']['background']['units']['storage']and combat['pickups56_hex']==post['capture']['background']['pickups']['storage']
                for key in player_initial['growth']:
                    assert growth[key]==(answer['rng_words']if key=='rng_words'else player_initial['growth'][key])
                assert G.tree_fields(post['capture'],rawgame)==growth['player_fields'];counts['player_tree_captures']+=1;counts['logical72_values']+=len(growth['player_fields']);counts['derived23_values']+=len(growth['derived_bits'])
                for key in['live','aura','racial80_hex']:assert post[key]==pre[key]
                assert post['spell_sets']==answer['spell_sets']and post['source_flags']==pre['source_flags']and post['scalar']==dict(pre['scalar'],**{'2352':now})
                assert obs['pending_before']==obs['pending_after']==dict(hits=dict(capacity=0,pointer=8,count=0,stride=112,storage=[]),areas=dict(capacity=0,pointer=8,count=0,stride=88,storage=[]))
                assert obs['source_headers']=={str(p):0 for p in[176,600,648,1984,2032,2044,2056]}and all(u(rawgame,p)==0 for p in[176,600,648,1984,2032,2044,2056,1852,1804,552,1676])
                assert u(rawgame,1664)==2 and u(rawgame,1660)==u(game,1660)and u(rawgame,1792)==u(rawgame,1784)==4 and u(rawgame,1788)==u(game,1788)
                assert struct.unpack_from('<Q',rawgame,984)[0]==int(answer['accounted_total_bits'])and u(rawgame,1084)==answer['kills1084']and u(rawgame,1088)==answer['elites1088']and u(rawgame,2408)==answer['counter2408']and u(rawgame,2412)==1 and u(rawgame,2420)==answer['killcost2420_bits']and u(rawgame,1876)==answer['pickup_count']and u(rawgame,1868)==answer['pickup_capacity']
                for key in['auxiliary','claims','special','windows','boundaries']:assert post['capture']['background'][key]==pre['capture']['background'][key]
                assert post['capture']['background']['pickups']['storage'][:2]==pre['capture']['background']['pickups']['storage'][:2];counts['two_Runes_conserved_bytes']+=112
                counts['other_background_conserved_bytes']+=sum(len(bytes.fromhex(hx))for key in['special','windows','boundaries']for hx in post['capture']['background'][key]['storage'])
                prior_packets=previous['capture']['packets'];all_packets=post['capture']['packets'];assert all_packets[:len(prior_packets)]==prior_packets and all_packets[len(prior_packets):]==obs['new_packets'];cursor=0
                for packet in diag['known_packets']:
                    at=next(k for k in range(cursor,len(obs['new_packets']))if obs['new_packets'][k]==packet);cursor=at+1;counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
                    if packet[0]==306:assert decode_launch(packet[1])==list(map(int,diag['selected_ids']));counts['mask0_launches']+=1
                counts['unmodeled_emitted_packets']+=len(obs['new_packets'])-len(diag['known_packets']);previous=post
            reference.append(dict(id=case['id'],opening=opening,initial=player_initial,player_xyz=player,stages=stages));diagnostics.append(dict(id=case['id'],steps=case_d))
        assert counts['full922']==ncasts and counts['inherited_Game2592_bytes']==2592*ncasts and counts['NPC_full_physical_replay_bytes']==1728*ncasts
        for key in['successful_casts','damage_calls','deaths','slow_write_operations','known_packets','known_packet_bytes']:assert counts[key]==comp['counts'][key],(batchname,key)
        for key in['NPC','pickup','initial_live','initial_aura']:
            for suffix in['known','None','nonzero_None']:assert counts[key+'_'+suffix]==comp['counts'][key+'_'+suffix],(batchname,key,suffix)
        if ncases==18:assert counts['max_targets']==1 and counts['positive_critical_hits']==0
        else:assert(counts['multi_target_casts'],counts['max_targets'],counts['positive_critical_hits'],counts['damage_calls'],counts['deaths'])==(51,3,14,113,19)
        runtime=load(batch/'runtime.json');terminal=load(batch/'owned-terminal.json');assert runtime==comp['runtime']and terminal==comp['process']and terminal==hand['owned_process']
        assert runtime['fresh_instances']==ncases and runtime['full_calls']=={'922':ncasts,'1093':ncases,'1108':ncases,'1600':ncases,'1775':ncasts,'2945':ncases,'3755':ncasts,'4677':ncases}and runtime['allocator_calls']==5*ncases and runtime['stack_checks']==10*ncases+3*ncasts
        assert len(runtime['target_and_setup_returns'])==5*ncases+3*ncasts and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])and len(runtime['world_source_checks'])==5*ncases+ncasts and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])
        assert runtime['denied_imports']==882 and runtime['actual_host_calls']==0 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None
        assert not any(runtime[k]for k in['old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games'])and all(runtime[k]for k in['input_dead_mask_all_zero','full922_callees_intact','internal913_2189_notinstrumented','empty1775_3755_only','controlled_player_relocation'])
        assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<120
        audit=load(batch/'expectation-read-audit.json');assert audit['forbidden']==[]and all(not Path(p).suffix.lower()in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
        for name,h in sources.items():assert sha(ROOT/name)==h
        label='base18'if ncases==18 else'world9';save(out/(label+'-reference.json'),reference);save(out/(label+'-diagnostics.json'),diagnostics)
        batch_results.append(dict(label=label,directory='evidence/'+batchname,author_handoff_sha256=handoffsha,comparison_sha256=comparisonsha,cases=ncases,full922=ncasts,empty1775=ncasts,empty3755=ncasts,prefix_each2945_1600_1108_4677_1093=ncases,source_files=nsrc,production_sources=nprod,source_edges=nedges,counts=dict(counts),reference_sha256=sha(out/(label+'-reference.json')),diagnostics_sha256=sha(out/(label+'-diagnostics.json')),author_process=terminal,runtime=runtime))
    for name,h in all_author_files.items():assert sha(ROOT/name)==h
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    assert len(all_author_files)==12 and not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    result=dict(status='pass_current139_thunder_area2_effect1_base18_and_natural_world9',reviewer='/root/collection139_finish',author='/root/growth139_review',reviewer_script_sha256=sha(Path(__file__)),author_files=all_author_files,helper_sha256=HELPERS,batches=batch_results,current_function_bindings=functions,all_nonexport_sections_identical=True,reviewer_original_executions=0,reviewer_author_model_checker_builder_executions=0,author_files_modified=False,seconds=time.monotonic()-started,limitations=['Controlled direct922 components after actualfull1108/XP5/firstnewThunder; not1238/2123/925/884 integration or completegame.','Playerpositions are explicit controls: baseNPC+offset and naturalworld rawcanonicalheight midpoint. NPCpositions are never changed or cleared.','Direct casts ignore skill cooldown scheduling by design; full inherited owned80/live1020/Aura/default event sources remain intact.','34base+113world damagecalls include23stationary ordinary deaths; lifesteal stays fullHP239 domain, positivehealing remains Pending.','Known306mask0 and169reward packets are verified ordered subsets;592damage/HP169/whole UI/heap/tree/network stream remains incomplete.','1775/3755 called only with actual inherited empty owners; neither pendinghit nor area job is enqueued by this path.','Nonempty effect49,slow376 removal,U356 conditional-source branch,otherNPC/status/school/fatalplayer/procs remain unknown.','Spell totalwideBTree values are read by frozen driver; its physical tree nodes are not separately captured. Player72 BTree nodes are independently decoded.','Originalresourceonlyhealthyv2context/newGame; independentmodel canonicalworldraw artifacts; naturalApp/worldRc/externref/native/save/fullgame remain unaccepted.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),batches=[dict(label=b['label'],counts=b['counts'])for b in batch_results],seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
