#!/usr/bin/env python3
"""Independent complete139 opening→real drops→first choice reference."""
from collections import Counter
from pathlib import Path
import copy,hashlib,json,math,sqlite3,struct,sys
import review_cast139 as C
import review_death139 as D
import review_collection139 as L
import review_growth139 as G
import review_opening139 as O
from review_combat139 import parse_module,local_closure,sha,bits,fp,f32
from review_initial139 import reference as constructor_reference
from review_world_position139 import load_world
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
load=lambda p:json.loads(p.read_text())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def gain(s,amount,classes,races,kit):
    g=s['growth'];g['xp']=(g['xp']+amount)&0xffffffff
    while g['level']<=119 and g['xp']>=G.threshold(g['level']):
        g['xp']-=G.threshold(g['level']);g['pending']+=1;g['level']+=1;G.recalculate(g,classes,races)
        fields=g['player_fields'];fields['34']=g['level'];request=G.mul(g['derived_bits']['1536'],0x3e4ccccd)
        hp=G.add(g['current_hp_bits'],request);g['current_hp_bits']=hp if fp(hp)<fp(g['derived_bits']['1536'])else g['derived_bits']['1536'];fields['22']=math.ceil(fp(g['current_hp_bits']));fields['28']=math.ceil(fp(g['derived_bits']['1536']))
    g['player_fields'].update({'716':g['xp'],'717':G.threshold(g['level'])})
    # Current4677's phase guard matters if several preselected pickups award
    # XP in the same2890: phase2 must not generate a second candidate set.
    if g['pending'] and g['phase2587']==1:
        cards,words,_=G.candidates(g['rng_words'],kit,g['level']);g.update(candidates=cards,rng_words=words,phase2587=2,selection_kind2585=0,generation_counter2400=g['generation_counter2400']+1)
    s.update(xp=g['xp'],words=tuple(g['rng_words']),hp=g['current_hp_bits'],derived={int(k):v for k,v in g['derived_bits'].items()},fields={int(k):v for k,v in g['player_fields'].items()})


def collection_projection(s):
    g=s['growth'];p=L.project(s)
    p.update(level1432=g['level'],xp1436=g['xp'],pending2376=g['pending'],phase2587=g['phase2587'],selection_kind2585=g['selection_kind2585'],generation2400=g['generation_counter2400'])
    return p


def collect(s,now,classes,races,kit):
    rows=s['rows'];count=s['count'];player=s['player'];packets=[];attractions=[];events=[]
    assert not s['claims'] and s['mode']==0 and s['members']==1
    for i in range(count):
        old=rows[i]
        if L.read(old,8)!=0 or L.read(old,0)!=0:continue
        dist=L.distance(old,player);age=fp(C.sub(now,L.read(old,52)))>6
        if not age and not fp(dist)<=fp(s['derived'][1560]):continue
        delay=L.div(dist,0x42000000 if age else 0x41c00000)
        if not fp(delay)>fp(0x3df5c28f):delay=0x3df5c28f
        row=list(old);L.put(row,0,1);L.put(row,4,L.add(now,delay));rows[i]=row;s['sequence']=(s['sequence']+1)&0xffffffff;guid=L.read(old,16,8)
        packet=C.packguid(guid)+struct.pack('<4I',*[L.read(old,o)for o in [40,44,48]],s['sequence'])+b'\0'+struct.pack('<3I',256,max(1,L.truncsat(L.mul(delay,bits(1000.)))),1)+struct.pack('<3I',*player)
        packets.append([221,packet.hex()]);attractions.append(dict(index=i,arrival=L.add(now,delay)))
    selected=[]
    for i,row in enumerate(rows[:count]):
        kind=L.read(row,8);marker=L.read(row,0)
        if kind==0:accept=marker!=0 and fp(L.read(row,4))<=fp(now)
        elif kind==1:
            accept=fp(L.distance(row,player))<=fp(s['derived'][1560])
            if not accept:accept=marker==1 and fp(L.read(row,4))<=fp(now)
        else:assert fp(L.distance(row,player))>3;accept=False
        if accept:selected.append(i)
    for i in reversed(selected):
        row=rows[i];kind=L.read(row,8);amount=L.read(row,12);guid=L.read(row,16,8);assert L.read(row,0)in(0,1) and L.read(row,32)==0
        for j in range(i,count-1):rows[j]=list(rows[j+1])
        count-=1;packets.append([170,struct.pack('<Q',guid).hex()]);mult=s['derived'][1564 if kind==0 else 1588];value=L.rounded86979(L.mul(bits(1.),L.mul(mult,bits(f32(float(amount))))))
        if kind==0:
            if not fp(value)>1:value=bits(1.)
            award=L.truncsat(value);gain(s,award,classes,races,kit)
        else:
            award=L.truncsat(value);s['gold']=(s['gold']+award)&0xffffffff;s['earned']=(s['earned']+award)&0xffffffff;s['fields'][1176]=(s['gold']*10000)&0xffffffff;s['growth']['player_fields'][str(1176)]=s['fields'][1176]
        events.append(dict(index=i,kind=kind,amount=amount,award=award))
    s['count']=count;p=collection_projection(s);p.update(now_bits=now,new_packets=packets,growth_projection=copy.deepcopy(s['growth']))
    return p,dict(attractions=attractions,events=events)


def cast_at_time(death,growth,player,now,definition,owned,world,scalars,speeds,npc_def):
    # Reused zero-time independent reference is valid for these current
    # constructor units only: no motion or positive-expiry modifiers. Restore
    # the now-dependent written timestamps; payload169 has no spawn clock.
    for row in death['rows']:
        assert D.read(row,344)==0 and all(D.read(row,o)==0 for o in [148,156,164])
    assert growth['current_hp_bits']==growth['derived_bits']['1536']
    oldmarkers=[D.read(row,0)for row in death['rows']];oldcount=death['pickup_count'];derived={int(k):v for k,v in growth['derived_bits'].items()}
    p,hits=D.cast_reference(death,player,derived,definition,owned,world,scalars,speeds,npc_def)
    for i,(before,row)in enumerate(zip(oldmarkers,death['rows'])):
        if not before and D.read(row,0):D.put(row,4,now);D.put(row,340,now)
    for row in death['pickups'][oldcount:death['pickup_count']]:D.put(row,52,now)
    p.update(records432_cells=[list(r)for r in death['rows']],pickups56_cells=[list(r)for r in death['pickups']],xp1436=growth['xp'],movement_sequence2412=death['sequence'])
    p.pop('launch306_packets')
    return p,hits


def reference(case,world,nav,scalars,tables,npc_def,speeds,classes,races,zones,eligible,minutes,kit,definitions,cooldown,damage):
    opening,_=O.reference(case,world,nav,scalars,tables,npc_def,[*speeds[:1],1088421888,*speeds[2:]],classes,races,zones,eligible,minutes);p=opening['projection'];seed=int(opening['constructor_seed_u64']);height=world.height(*scalars['center_xy_bits'])
    ctor,_=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=str(seed),object_id_u64='0',flat_height_bits=height),classes,races,zones)
    growth=dict(level=1,xp=0,pending=0,phase2587=1,current_hp_bits=ctor['current_hp_bits'],derived_bits=ctor['derived_bits'],player_fields=ctor['player_fields'],rng_words=p['rng_words'],candidates=[],selection_kind2585=255,generation_counter2400=0,owned_records80_hex=ctor['owned_records_hex'],flag2581=0,flags2573=0)
    death=dict(rows=copy.deepcopy(p['units']['storage']),words=tuple(p['rng_words']),counter=p['counter'],total=0,spelltotals={},kills=0,elites=0,cost=0,sets=[[],[],[]],pickups=copy.deepcopy(p['pickups']['storage']),pickup_count=2,sequence=1)
    owned=bytes.fromhex(growth['owned_records80_hex'][0]);definition=definitions['cleave'][1];rounds=[];clock=0;gold=earned=0;selection=None
    for roundno in range(4):
        target=next((i for i,row in enumerate(death['rows'])if not D.read(row,0)),None);assert target is not None
        player=[D.read(death['rows'][target],o)for o in [316,320,324]];casts=[]
        for _ in range(2):
            stage,hits=cast_at_time(death,growth,player,clock,definition,owned,world,scalars,speeds,npc_def);casts.append(stage)
        growth['rng_words']=list(death['words']);growth['current_hp_bits']=int(casts[-1]['player_hp1440_bits'])
        s=dict(rows=death['pickups'],count=death['pickup_count'],words=death['words'],hp=growth['current_hp_bits'],derived={int(k):v for k,v in growth['derived_bits'].items()},fields={int(k):v for k,v in growth['player_fields'].items()},growth=growth,player=player,claims=[],claim_count=0,sequence=death['sequence'],gold=gold,earned=earned,xp=growth['xp'],mode=0,members=1,peer=0,xpq=dict(capacity=0,entries=[]),coinq=dict(capacity=0,entries=[]))
        times=[clock,L.add(clock,bits(.5))];collects=[];diagnostics=[]
        for now in times:
            stage,trace=collect(s,now,classes,races,kit);collects.append(stage);diagnostics.append(trace)
        growth=s['growth'];death.update(pickups=s['rows'],pickup_count=s['count'],sequence=s['sequence'],words=tuple(growth['rng_words']));gold,earned=s['gold'],s['earned'];clock=times[-1]
        rounds.append(dict(target_index=target,now_bits=times[0],collect_times=times,player_xyz=player,cast_stages=casts,collection_stages=collects,diagnostics=diagnostics))
        if growth['phase2587']==2:
            index=next(i for i,c in enumerate(growth['candidates'])if c['variant']=='new');card=growth['candidates'][index];assert growth['pending']==1
            growth['owned_records80_hex'].append(G.selected_record(card['ability_id'],card['tier'],definitions,cooldown,damage));G.recalculate(growth,classes,races);growth.update(pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=[])
            live=[None]*32;live[:8]=bytes(8);live[8:12]=struct.pack('<I',12);live[20:32]=struct.pack('<III',1020,L.add(clock,bits(1.)),0)
            selection=dict(index=index,projection=copy.deepcopy(growth),live32_cells=[live]);break
    assert selection is not None
    target=next((i for i,row in enumerate(death['rows'])if not D.read(row,0)),None);follow=None
    if target is not None:
        player=[D.read(death['rows'][target],o)for o in [316,320,324]];pointers=[int.from_bytes(bytes.fromhex(h)[:4],'little')for h in growth['owned_records80_hex']];lookup={v[0]:v[1]for v in definitions.values()};executions=[lookup[v][84]for v in pointers];assert 11 not in executions
        state,hits=cast_at_time(death,growth,player,clock,definition,bytes.fromhex(growth['owned_records80_hex'][0]),world,scalars,speeds,npc_def)
        follow=dict(target_index=target,player_xyz=player,now_bits=clock,actual_owned_scan=dict(pointers=pointers,execution_bytes=executions),state=state,live32_cells_preserved=copy.deepcopy(selection['live32_cells']))
    opening.pop('diagnostic')
    return dict(opening_expected=opening,rounds=rounds,selection=selection,continuation=follow)


def main():
    batch=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]).resolve();out.mkdir();comparison_sha,handoff_sha=sys.argv[3:5]
    assert sha(batch/'comparison.json')==comparison_sha and sha(batch/'task-handoff.json')==handoff_sha and sha(SOURCE)==WASM
    comp=load(batch/'comparison.json');hand=load(batch/'task-handoff.json');prep=load(batch/'prepared.json');manifest=load(batch/'manifest.json');runtime=load(batch/'runtime.json');cfg=load(batch/'config.json')
    assert comp['phase']=='full' and comp['cases']==comp['completed']==3 and comp['differences']==0 and comp['runtime_contract_checked']and comp['process_contract_checked']
    author=hand.get('files',hand.get('frozen_author_files'));assert author
    for n,h in author.items():assert sha(ROOT/n)==h
    sources=comp['source_before'];assert sources==comp['source_after']==prep['source_before']
    for n,h in sources.items():assert sha(ROOT/n)==h==sha(batch/'source-snapshot'/n)
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])
    for table in [comp['artifacts'],prep['frozen']]:
        for n,h in table.items():assert sha(batch/n)==h
    assert comp['expected_before_original']and prep['expected_before_original']and not prep['original_inputs_contain_expected']and not comp['original_inputs_contain_expected']
    helper_names=['review_combat139.py','review_cast139.py','review_death139.py','review_collection139.py','review_growth139.py','review_opening139.py','review_initial139.py','review_natural_npc139.py','review_npc_spawn139.py','review_world_position139.py','review_player_motion135.py','review_death_pickups139.py','review_stats139.py','review_opening_actor139.py']
    helpers={n:sha(ROOT/'scripts'/n)for n in helper_names}
    for name,h in [('review_collection139.py','b034feeecf15ad1562e28a10bb8d6cbf60d7e814a23cb931d8d60c96e82247d2'),('review_growth139.py','db6246b4dc0da5aa902ef87e629ce4d460c04e2e41acad4c7b63fba2a2e9d243'),('review_opening139.py','29de9cb7dbeb7595ce2baced0a0de9d5c5e967ce73cecd8cff5868d4feafc5c9')]:assert helpers[name]==h
    assert helpers['review_death139.py']=='fe7790f0adcb3e3d5010d53c44f375bec5bbee6d3fe780873a6e1613afe11e6a'
    for name,h in D.HELPERS.items():assert sha(ROOT/'scripts'/name)==h
    for mapping in [O.HELPERS,G.HELPERS]:
        for name,h in mapping.items():assert sha(ROOT/name)==h
    for name,h in [('reports/2026-11-02-opening0139-independent-review.json','8a96229937109daa2f30624288cd820376465e6ce640cc1f2a55b66c16be5a8c'),('reports/2026-11-02-collection0139-independent-review.json','466862df681e5834f129a7fe7dc3e29b7f30a9cbf141b617521663e0703fc363'),('reports/2026-11-02-growth-world0139-independent-review.json','91d231b07dead6849dd9503e734fa08c7a1b784aeb59c7ddba9ecc7b188ef4dc')]:assert sha(ROOT/name)==h
    assert cfg['snapshot_sha256']==comp['resource_context_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0' and sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']
    assert sha(Path(cfg['range_file']))==cfg['range_sha256'] and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==prep['resource_context_gate_sha256']==comp['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    raw=SOURCE.read_bytes();original=parse_module(raw);private=(batch/manifest['module_file']).read_bytes();assert hashlib.sha256(private).hexdigest()==manifest['module_sha256'];modified=parse_module(private)
    additions=[('research139_open_actor1886',0,1886),('research139_open_pickup1446',0,1446),('research139_open_random13563',0,13563),('research139_open_initial1600',0,1600),('research139_open_companion2945',0,2945),('research139_open_begin1108',0,1108),('research139_open_stack0',3,0),('research139_chain_cast922',0,922),('research139_chain_collect2890',0,2890),('research139_chain_select1093',0,1093)]
    assert modified['exports']==original['exports']+additions and len(original['imports'])==882
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
    whole=load(batch/'whole-opening-static/trace.json');claims=manifest['functions']|manifest['extra_static_functions']|manifest['chain_functions']|whole['functions'];bindings={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for key,row in claims.items():
            idx=int(key);a,z=original['bodies'][idx];assert hashlib.sha256(raw[a:z]).hexdigest()==row['body_sha256'];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);wat=stream.read(end-start);assert hashlib.sha256(wat).hexdigest()==row['WAT_sha256'];bindings[key]=row;texts[idx]=wat.decode()
    assert all('call '+str(i)in texts[2890]for i in [4677,32070,29338]) and 'call 2181'in texts[4677] and 'call 26364'in texts[25613]
    def data(address,size):
        result=bytearray(size)
        for base,pos,n in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-base:pos+hi-base]
        return bytes(result)
    u=lambda address:C.u(data(address,4));text=lambda p,n:data(p,n).decode();abilities={}
    for i in range(114):
        p=5882740+88*i;row=data(p,88);abilities[text(C.u(row,12),C.u(row,16))]=(p,row,tuple(data(C.u(row,36),C.u(row,40))))
    cls=data(5877920,108);kit=[text(p,n)for p,n in struct.iter_unpack('<II',data(C.u(cls,32),8*C.u(cls,36)))];definitions={k:abilities[k]for k in kit};classes={1:dict(hp_armor=[C.u(cls,72),C.u(cls,76)],ability_pointer=5882740)}
    race=data(5874636,44);racial=text(C.u(race,24),C.u(race,28));races={1:dict(ability_pointer=abilities[racial][0],modifiers=list(struct.iter_unpack('<II',data(C.u(race,16),8*C.u(race,20)))))}
    zone=data(5871348,152);scalars_heading=C.u(zone,116);zones=[dict(xyz=[C.u(zone,104),C.u(zone,108),scalars_heading])];npc_def=data(5830904,72);eligible=[i for i in range(12)if u(5830904+72*i+68)==1 and math.isfinite(fp(u(5830904+72*i+64)))];minutes=u(C.u(zone,72)+336)
    speeds=list(struct.unpack('<6I',data(1593032,24)));tables=[list(struct.unpack('<4f',data(p,16)))for p in [14426512,14426528,14426544,14426560]];cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20))
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==comp['world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));scalars['heading_bits']=scalars_heading
    cases=load(batch/'inputs.json');expected=load(batch/'expected.json');actual=[json.loads(x)for x in(batch/'stdout.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==3
    counts=Counter();references=[];npc_prior=[];pickup_prior=[]
    def rows(label,wants,hxs):
        assert len(wants)==len(hxs)
        for row,hx in zip(wants,hxs,strict=True):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)
            for i,(v,b)in enumerate(zip(row,raw)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:assert v==b,(label,i,v,b);counts[label+'_known']+=1
    def growth(want,got):
        for key,value in want.items():
            if key=='player_fields':
                for k,v in value.items():assert got[key][k]==v;counts['known_growth_fields']+=1
            else:assert got[key]==value,('growth',key,value,got[key])
    def packets(want,got):
        cursor=0
        for packet in want:
            cursor=next(i+1 for i in range(cursor,len(got))if got[i]==packet);counts['known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2
    def cast(want,got,rawgame):
        rows('NPC',want['records432_cells'],got['records432_hex']);rows('pickup',want['pickups56_cells'],got['pickups56_hex'])
        for label,cells,observed,prior in [('NPC',want['records432_cells'],got['records432_hex'],npc_prior),('pickup',want['pickups56_cells'],got['pickups56_hex'],pickup_prior)]:
            for row,hx,previous in zip(cells,observed,prior,strict=True):
                after=bytes.fromhex(hx);before=bytes.fromhex(previous)
                for i,v in enumerate(row):
                    if v is None:assert before[i]==after[i];counts[label+'_persistent_None_bytes']+=1
        npc_prior[:]=got['records432_hex'];pickup_prior[:]=got['pickups56_hex']
        for k,v in want.items():
            if k in ['records432_cells','pickups56_cells','known_packets']:continue
            assert got[k]==v,('cast',k,v,got[k])
        packets(want['known_packets'],got['new_packets']);pre=bytes.fromhex(rawgame['before_hex']);post=bytes.fromhex(rawgame['after_hex'])
        for o in [176,600,648,1984,2032,2044,2056]:assert C.u(pre,o)==C.u(post,o)==0
        assert pre[770]==post[770]==0 and pre[908]==post[908]==0
        counts['full922']+=1
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case['id']==e['id']==a['id']and case==e['input'];answer=reference(case,world,nav,scalars,tables,npc_def,speeds,classes,races,zones,eligible,minutes,kit,definitions,cooldown,damage);references.append(answer);claim=e['expected']
        initial_counters=dict(accounted_total_bits='0',spell_totals64=[],kills1084=0,elites1088=0,movement_sequence2412=1,killcost2420_bits=0,gold1456=0,earned1100=0)
        assert case['initial_counters']==a['initial_counters_observed']==initial_counters
        assert answer['opening_expected']==claim['opening_expected'];op=answer['opening_expected'];p=op['projection'];g=a['after']
        for k in ['selected40','constructor','afterGame']:
            key={'selected40':'selected40_cells','constructor':'constructor_cells','afterGame':'known_Game2592'}[k];rawgame=a['selected40_hex']if k=='selected40'else(a['constructor']if k=='constructor'else g)['raw_Game2592_hex'];rows(k,[op[key]],[rawgame])
        for k in ['units','pickups','companions','windows','special','boundaries']:
            assert p[k]['capacity']==g[k]['capacity']and p[k]['count']==g[k]['count'];rows('opening_'+k,p[k]['storage'],g[k]['storage'])
        for k in ['phase2587','counter','rng_words','player_xyz']:assert p[k]==g[k]
        relative=bytearray.fromhex(a['before']['raw_Game2592_hex']);after=bytes.fromhex(g['raw_Game2592_hex'])
        for i,v in enumerate(op['known_Game2592']):
            if v is not None:relative[i]=v
        for k,o in [('units',1788),('pickups',1872),('special',1920),('windows',1968),('boundaries',2124),('packets',1884),('notifications',1896)]:
            assert g[k]['capacity']!=a['before'][k]['capacity'];relative[o:o+4]=after[o:o+4];counts['opening_new_pointer_words_observed']+=1
        assert relative==after;counts['opening_relative_Game_bytes']+=2592
        assert p['packets']==[[v['opcode'],v['payload_hex']]for v in g['packets']['active']]and p['notifications']==[v['payload_hex']for v in g['notifications']['active']];counts['complete_opening_packets']+=len(p['packets'])
        assert op['constructor_seed_u64']==a['constructor_seed_u64']and a['new_game_pointer']!=a['old_snapshot_Game_pointer_not_target']==14685248
        assert a['account_unchanged']and a['profile_unchanged']and a['selection_canaries']==['c3'*16,'d7'*16]
        expected_controls=[dict(target_index=r['target_index'],now_bits=r['now_bits'],collect_times=r['collect_times'])for r in answer['rounds']];assert expected_controls==case['rounds']and case['select_index']==answer['selection']['index']and case['followup_index']==(None if answer['continuation']is None else answer['continuation']['target_index'])
        previous=g['raw_Game2592_hex'];npc_prior[:]=g['units']['storage'];pickup_prior[:]=g['pickups']['storage'];assert len(answer['rounds'])==len(claim['rounds'])==len(a['rounds'])
        for wanted,stored,observed in zip(answer['rounds'],claim['rounds'],a['rounds'],strict=True):
            for k in ['target_index','now_bits','collect_times','player_xyz','cast_stages','collection_stages']:assert wanted[k]==stored[k],('storedreference',case['id'],k)
            assert observed['before_control_hex']==previous;action=bytearray.fromhex(previous);L.put(action,2352,wanted['now_bits'])
            for i,v in enumerate(wanted['player_xyz']):L.put(action,1416+4*i,v)
            assert action.hex()==observed['action_before']['raw_Game2592_hex'];previous=action.hex()
            for w,got,rawgame in zip(wanted['cast_stages'],observed['cast_stages'],observed['cast_raw_games'],strict=True):
                assert rawgame['before_hex']==previous;cast(w,got,rawgame);previous=rawgame['after_hex'];counts['inherited_cast_Game_bytes']+=2592
            for w,got,trace in zip(wanted['collection_stages'],observed['collection_stages'],wanted['diagnostics'],strict=True):
                action=bytearray.fromhex(previous);L.put(action,2352,w['now_bits']);assert got['raw_game_before_hex']==action.hex();counts['inherited_collect_Game_bytes']+=2592
                rows('collect_pickup',w['pickups56_cells'],got['pickups56_hex'])
                for key,value in w.items():
                    if key in ['pickups56_cells','new_packets','growth_projection']:continue
                    if key=='known_player_fields':
                        fields=dict(got['player_fields'])
                        for k,v in value.items():assert fields[int(k)]==v;counts['known_player_fields']+=1
                    else:assert got[key]==value,('collect',key,value,got[key])
                growth(w['growth_projection'],got['growth']['projection']);packets(w['new_packets'],got['new_packets']);assert got['units_before_hex']==got['units_after_hex']==''.join(npc_prior);counts['NPC_bytes_conserved_during_collect']+=len(bytes.fromhex(got['units_before_hex']))
                assert got['before_pickups56_hex']==pickup_prior
                relative=[bytearray.fromhex(h)for h in got['before_pickups56_hex']];n=C.u(bytes.fromhex(got['raw_game_before_hex']),1876)
                for event in trace['attractions']:L.put(relative[event['index']],0,1);L.put(relative[event['index']],4,event['arrival'])
                for event in trace['events']:
                    for j in range(event['index'],n-1):relative[j]=bytearray(relative[j+1])
                    n-=1;counts['XP_awards'if event['kind']==0 else'coin_awards']+=1
                assert [r.hex()for r in relative]==got['pickups56_hex'];pickup_prior[:]=got['pickups56_hex'];counts['relative_pickup_bytes_including_None']+=56*len(relative);previous=got['raw_game_after_hex'];counts['full2890']+=1
        assert answer['selection']==claim['selection'];s=a['selection'];assert s['before_game_hex']==previous;growth(answer['selection']['projection'],s['projection']);rows('selected_live',answer['selection']['live32_cells'],s['live32_hex']);previous=s['after_game_hex']
        assert s['units_before_hex']==s['units_after_hex']==''.join(npc_prior) and s['hit_source_words_before']==s['hit_source_words_after']==[0]*7 and s['owned_header_after'][2]==2
        pointers=[int.from_bytes(bytes.fromhex(h)[:4],'little')for h in answer['selection']['projection']['owned_records80_hex']];lookup={v[0]:v[1]for v in definitions.values()};execution=[lookup[v][84]for v in pointers];assert s['postselection_hit_sources']==dict(pointers=pointers,execution_bytes=execution,event_definitions_count=0,initial_mode770=0)
        assert answer['continuation']==claim['continuation'];follow=answer['continuation'];observed=a['continuation']
        if follow is None:assert observed is None
        else:
            assert observed['before_control_hex']==previous;action=bytearray.fromhex(previous)
            for i,v in enumerate(follow['player_xyz']):L.put(action,1416+4*i,v)
            assert observed['before_game_hex']==action.hex() and C.u(action,1660)==s['owned_header_after'][1];cast(follow['state'],observed['state'],dict(before_hex=observed['before_game_hex'],after_hex=observed['after_game_hex']))
            assert observed['actual_owned_scan']==follow['actual_owned_scan']and observed['live32_before_hex']==observed['live32_after_hex'];rows('follow_live',follow['live32_cells_preserved'],observed['live32_after_hex']);counts['direct_cleave_after_selected_owned2']+=1
        for k in ['companions','windows','special','boundaries']:assert a['terminal_view'][k]==g[k]
        assert a['terminal_view']['pickups']['storage'][:2]==g['pickups']['storage'][:2]and a['background_unchanged'];counts['full1108']+=1;counts['full1093']+=1
    calls=runtime['full_calls'];assert calls=={'2945':3,'1600':3,'1108':3,'922':counts['full922'],'2890':counts['full2890'],'1093':3}and runtime['host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None and runtime==comp['runtime']
    assert all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])and len(runtime['target_and_setup_returns'])==sum(calls.values())and runtime['stack_guards']==runtime['allocator_calls']+sum(calls.values())
    assert all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks']);terminal=load(batch/'process-terminal.json');assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal==comp['process']
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    for n,h in author.items():assert sha(ROOT/n)==h
    for n,h in helpers.items():assert sha(ROOT/'scripts'/n)==h
    save(out/'independent-reference.json',references);result=dict(status='pass_current139_controlled_fullopening_real_death_XP_firstchoice_and_direct_continuation',comparison_sha256=comparison_sha,author_handoff_sha256=handoff_sha,reviewer_source_sha256=sha(Path(__file__)),author_files=author,helpers=helpers,cases=3,counts=dict(counts),source_files=len(sources),source_edges=len(edges),current_body_WAT_bindings=bindings,all_nonexport_sections_byte_identical=True,author_process=terminal,reviewer_original_executions=0,reviewer_author_production_checker_builder_executions=0,limits=['Resource-onlylegalv2snapshot,new2945/1600Game;independentraw-derivedworld;notnaturalApp/Rc/externref/bootstrap.','Full1108preservesallbackground;relocation/direct922/2890scheduleandclockarecontrolled,notAI/input/owned1238/main884frames.','Initialaccounting/kills/gold/sequenceareexplicitcheckedinputs,notfullGameproducerreconstruction.','ActualXPawardsderivefromrealdeaths,noXPinserted;firstnewcardonly,upgrades/goldandlaterlevelsnotacceptedhere.','Known306/XPcoin169/221/170onlyorderedsubsequenceafteropening;592/HP169/growthUIstreamstillunknown.','PostselectcleavereacquiresactualGame1660ownedvectorandprovesallcurrentownedexec!=11;live12kept,notfullowned2/newskill/expiry/autoscheduleracceptance.','Game/BTree/allocatoraddressesandunknownpaddingremainobservations;relativeunknown56BconservationdoesnotfillmodelNone.','NoWindowsnative/fullgame/save/networkacceptance.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts))))


if __name__=='__main__':main()
