#!/usr/bin/env python3
"""Different-author read-only current952 ordinary-domain review; no originals run."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
    if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen'):
        AUDIT['forbidden_execution_attempts']+=1;raise RuntimeError('Read-only reviewer rejects execution '+event)
    if event=='import'and str(args[0]).startswith('core_spec'):
        AUDIT['forbidden_author_import_attempts']+=1;raise RuntimeError('Author production import rejected')
sys.addaudithook(audit)
import review_cast139 as C
import review_opening139 as O
import review_npc_spawn139 as N
from review_world_position139 import Reference as Position,load_world
from review_initial139 import reference as constructor_reference
from review_combat139 import parse_module,local_closure,sha,fp,bits

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/spawn-schedule139-oracle-20261102T124327.004589Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
HAND='16cd40079b7d0c84e752eac10cd1272d252e41c5023149384beeecd2f11160ef'
COMP='92b096b89c44450fe1efcb96fc976fdb286e75f6ac5544891d5284a1564458c3'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
CORRECTION=ROOT/'evidence/spawn-schedule139-timer-label-corrigendum-20261102T125058.478630Z/notes.json'
CORRECTION_SHA='98f3777b83f838636f162f1922a6ddd13c7746195c8f4a6cf502cee2362dc6a9'
HELPERS={**O.HELPERS,'scripts/review_opening139.py':'29de9cb7dbeb7595ce2baced0a0de9d5c5e967ce73cecd8cff5868d4feafc5c9','scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b'}
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
q=lambda b,o=0:struct.unpack_from('<Q',b,o)[0]


def read(row,offset):
    cells=row[offset:offset+4];assert len(cells)==4 and None not in cells
    return u(bytes(cells))


def choose(indices,minute,words,definitions,counts):
    weights=[]
    for index in indices:
        d=definitions[index];elapsed=C.sub(minute,u(d,64));elapsed=elapsed if C.rational(elapsed)>0 else 0
        weight=C.add(C.mul(elapsed,bits(.5)),C.ONE);weight=weight if C.rational(weight)<4 else bits(4.)
        weights.append(C.div(weight,u(d,60)))
    total=0x80000000
    for value in weights:total=C.add(total,value)
    high=total if C.rational(total)>C.rational(0x3a83126f)else 0x3a83126f
    for _ in range(10001):
        value,words=C.nextword(words);sample=C.mul(C.sub((value>>9)|C.ONE,C.ONE),high);counts['choice_RNG_draws']+=1
        if C.rational(sample)<C.rational(high):break
    else:raise AssertionError('Independent choice sampler watchdog')
    for index,weight in zip(indices,weights,strict=True):
        if C.rational(sample)<C.rational(weight):return index,words
        sample=C.sub(sample,weight)
    assert indices;return indices[0],words


def birth(index,now,position,player,words,counter,prior,definitions,zone,tables,speeds,counts):
    d=definitions[index];assert d[68]==0 and u(zone,140)==0
    minute=C.div(now,bits(60.));scale=u(zone,136)
    curve=C.add(C.mul(minute,0x3dcccccd),C.ONE)
    curve=C.add(curve,C.mul(minute,C.mul(minute,0x3d1374bc)))
    curve=C.add(curve,C.mul(minute,C.mul(minute,C.mul(minute,0x3be6afcd))))
    hp=C.mul(C.mul(0x409e6666,u(d,40)),C.mul(scale,curve))
    clamp=C.div(minute,bits(20.));clamp=0 if C.rational(clamp)<0 else C.ONE if C.rational(clamp)>1 else clamp
    hp=C.mul(hp,C.add(C.mul(clamp,C.mul(clamp,u(zone,140))),C.ONE))
    curve=C.add(C.mul(minute,0x3d8f5c29),C.ONE)
    curve=C.add(curve,C.mul(minute,C.mul(minute,0x3c75c28f)))
    curve=C.add(curve,C.mul(minute,C.mul(minute,C.mul(minute,0x3951b717))))
    attack=C.mul(C.mul(bits(1.25),u(d,44)),C.mul(curve,bits(N.rounded_sqrt(fp(scale)))))
    counter=(counter+1)&0xffffffff;entry=u(d,24);guid=0xf130000000000000|((entry&0xffffff)<<24)|(counter&0xffffff)
    yaw,words,yaw_draws=N.rng_sample(words,fp(0x40c90fdb));jitter,words,jitter_draws=N.rng_sample(words,fp(0x3e99999a));counts['NPC_yaw_jitter_draws']+=yaw_draws+jitter_draws
    buf=bytearray(432)
    def put(o,v):struct.pack_into('<I',buf,o,v)
    for o in(40,64,244):put(o,0xffffffff)
    struct.pack_into('<Q',buf,112,guid);struct.pack_into('<Q',buf,236,4)
    s=u(d,32);speed=u(d,48)
    fields={280:0,284:5830904+72*index,288:hp,292:hp,296:attack,300:C.mul(u(d,52),0x3f866666),304:speed,308:C.add(C.mul(s,0x3f99999a),0x400ccccd),312:s,340:now,348:C.add(now,C.add(bits(jitter),0)),352:C.mul(speed,bits(.5)),404:C.add(bits(yaw),0)}
    for o,v in fields.items():put(o,v)
    for o in(316,328):struct.pack_into('<3I',buf,o,*position)
    cells=list(prior)
    for o,n in N.WRITES:cells[o:o+n]=buf[o:o+n]
    dy,dx=(fp(C.sub(player[i],position[i]))for i in(1,0));heading=N.heading_ref(dy,dx,tables)
    packet=N.packet169(guid,entry,u(d,28),fp(s),fp(hp),position,heading,speeds)
    return cells,words,counter,packet


def reference(case,opening,world,nav,scalars,tables,definitions,zone,speeds,counts):
    p=opening['projection'];player=p['player_xyz'];rows=copy.deepcopy(p['units']['storage']);count=p['units']['count'];words=tuple(p['rng_words']);counter=p['counter'];packets=copy.deepcopy(p['packets']);budget=bits(3.);clock=0
    timeline=[];frames={};born=[];timers={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0};previous_xyz=[0,0,0]
    for frame in range(case['frames']):
        clock=C.add(clock,case['dt_bits']);assert C.rational(clock)<40
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
        counts['full952_recomputed']+=1
        line=dict(frame=frame,count=count,capacity=len(rows),rng_words=list(words),counter2408=counter,now_bits=clock,budget2416_bits=budget,kill_cost2420_bits=0,previous_player_xyz=player,velocity_xy=[0,0],timer_fields=timers,packet_count=len(packets));timeline.append(line)
        if frame in case['checkpoints']or frame==case['frames']-1:frames[frame]=dict(timeline=copy.deepcopy(line),rows=copy.deepcopy(rows),packets=copy.deepcopy(packets))
    return timeline,frames,born


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP and sha(SOURCE)==WASM and sha(CORRECTION)==CORRECTION_SHA
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');runtime=load(BATCH/'runtime.json');cfg=load(BATCH/'config.json')
    author=hand['frozen_author_files'];assert len(author)==7
    for name,h in author.items():assert sha(ROOT/name)==h
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==46
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==135
    assert len([x for x in sources if x.startswith('reconstruction/')])==34
    for table in[comp['artifacts'],prep['frozen']]:
        for name,h in table.items():assert sha(BATCH/name)==h
    assert comp['phase']=='full'and comp['cases']==comp['completed_cases']==3 and comp['differences']==0
    assert comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
    assert sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==comp['resource_context_gate_sha256']==prep['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==comp['independent_world_receipt_sha256']==prep['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));assert not scalars['flat_present']and not scalars['primary_present']
    raw=SOURCE.read_bytes();original=parse_module(raw);private=(BATCH/m['module_file']).read_bytes();assert sha(BATCH/m['module_file'])==m['module_sha256'];modified=parse_module(private)
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
    exports=[('research139_spawn_companion',0,2945),('research139_spawn_initial',0,1600),('research139_spawn_opening',0,1108),('research139_spawn_tick952',0,952),('research139_spawn_stack',3,0)]
    assert modified['exports']==original['exports']+exports and len(original['imports'])==882
    assert[(r['module'],r['name'],r['type_index'])for r in original['imports']]==[(r['module'],r['name'],r['type_index'])for r in m['original_imports']]
    assert original['types'][original['decl'][952-882]]==('7f7d','')
    texts={};bindings={};extra={6786,33028,11425,11499,35202,35232,57285,108362,1711,1886,24602}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as s:
        for idx in sorted(set(map(int,m['functions']))|extra):
            a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();s.seek(start);wat=s.read(end-start);record=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());texts[idx]=wat.decode();bindings[str(idx)]=record
            if str(idx)in m['functions']:
                r=m['functions'][str(idx)];assert record['body_sha256']==r['body_sha256']and record['WAT_sha256']==r['WAT_sha256']and wat==(BATCH/'static'/f'{idx}.wat').read_bytes()
            (out/f'{idx}.wat').write_bytes(wat)
    scheduler=texts[952];assert all(x in scheduler for x in['f32.load offset=2416','f32.store offset=2420','f32.const 0x1.7a2p+11 (;=3025;)','call 20357','call 5719','f32.load offset=2424','f32.load offset=2440'])
    assert 'f32.const 0x1.cd5f9ap-8'in texts[97427]and'f32.const 0x1.8548aap-8'in texts[97426]and'call 97427'in texts[5719]
    assert 'i32.const 120\n        i32.add\n        i32.const 0\n        i32.const 116\n        memory.fill'in texts[5719]
    correction=load(CORRECTION)
    assert hashlib.sha256(texts[952].encode()).hexdigest()==correction['current952_WAT_sha256']
    for window in correction['windows'].values():
        first,last=window['local_WAT_lines'];value='\n'.join(scheduler.splitlines()[first-1:last])+'\n';assert hashlib.sha256(value.encode()).hexdigest()==window['sha256']
    assert 'f32.const -0x1.4p+1 (;=-2.5;)'in scheduler and'f32.const 0x1.b8p+5 (;=55;)'in scheduler and'f32.const 0x1.9p+4 (;=25;)'in scheduler
    assert 'f32.const -0x1.8p+0 (;=-1.5;)'in scheduler and'f32.const 0x1.18p+5 (;=35;)'in scheduler
    for fragment in['i64.const 0\n                  i64.store offset=1824','i64.const 1077936128\n                  i64.store offset=2504','i64.const 0\n                  i64.store offset=2456','local.get 13\n                  i32.store offset=2072','i32.const 2592\n                  memory.copy']:
        assert fragment in texts[1600]
    # Bind complete current WAT for both offsets; the author's v1 variable
    # names are deliberately not imported or used as semantic evidence.
    windows=[]
    for off in[2424,2440]:
        for number,line in enumerate(scheduler.splitlines(),1):
            if ('offset='+str(off))in line:windows.append(dict(offset=off,line=number,text='\n'.join(scheduler.splitlines()[max(0,number-5):number+8])))
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
    cases=load(BATCH/'inputs.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==3
    assert[(c['id'],c['app_seed_u64'],c['frames'],c['dt_bits'])for c in cases]==[(0,'0',600,bits(.0625)),(1,'1',320,bits(.0625)),(2,'42',160,bits(.0625))]
    counts=Counter();traces=[];allowed=set()
    for off,n in[(1720,16),(1784,12),(1880,12),(2352,4),(2408,4),(2416,24)]:allowed.update(range(off,off+n))
    def cells(label,wanted,hx):
        actual=bytes.fromhex(hx);assert len(wanted)==len(actual)
        for off,(v,b)in enumerate(zip(wanted,actual)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,off,v,b);counts[label+'_known']+=1
    def header(view):
        game=bytes.fromhex(view['raw_game2592_hex']);proj=view['projection'];bg=view['background'];assert len(game)==2592
        for k,o in[('level',1432),('xp',1436),('pending',2376),('current_hp_bits',1440),('generation_counter2400',2400)]:assert u(game,o)==proj[k]
        assert{str(1536+4*j):u(game,1536+4*j)for j in range(23)}==proj['derived_bits']and[u(game,1720+4*j)for j in range(4)]==proj['rng_words'];counts['raw23_derived_values']+=23
        assert game[2587]==proj['phase2587']==1 and game[2585]==proj['selection_kind2585']==255 and game[2581]==proj['flag2581']==0 and game[2573]==proj['flags2573']==0
        for name,cap,ptr,n,width in[('units',1784,1788,1792,432),('pickups',1868,1872,1876,56),('special',1916,1920,1924,40),('windows',1964,1968,1972,8),('boundaries',2120,2124,2128,8),('claims',2108,2112,2116,88),('auxiliary',652,656,660,112)]:
            v=bg[name];assert (v['capacity'],v['pointer'],v['count'],v['stride'])==(u(game,cap),u(game,ptr),u(game,n),width)and len(v['storage'])==v['capacity']and all(len(bytes.fromhex(s))==width for s in v['storage']);counts['raw_vector_headers']+=1
        assert u(game,1888)==len(view['packets'])<=u(game,1880)and u(game,2408)==bg['counter2408']and u(game,2412)==bg['movement_sequence2412']
        assert u(game,1712)==len(view['live32_hex'])==0 and u(game,1664)==len(proj['owned_records80_hex'])==1
        return game
    for case,a in zip(cases,actual,strict=True):
        assert a['id']==case['id']and a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['stack_after']==1048576
        opening,_=O.reference(case,world,nav,scalars,tables,definitions[0],speeds,classes,races,zones,eligible,minutes);op=opening['projection'];known=opening['known_Game2592']
        for off,value in[(1736,0),(1740,0),(2368,0),(1984,0),(2416,bits(3.)),(2420,0)]:known[off:off+4]=struct.pack('<I',value)
        assert a['opening']==a['before'];b=a['before'];game=header(b);cells('openingGame',known,b['raw_game2592_hex']);assert a['constructor_seed_u64']==opening['constructor_seed_u64']
        ctor,_=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=opening['constructor_seed_u64'],object_id_u64='0',flat_height_bits=world.height(*scalars['center_xy_bits'])),classes,races,zones)
        assert b['projection']==dict(level=1,xp=0,pending=0,phase2587=1,current_hp_bits=ctor['current_hp_bits'],derived_bits=ctor['derived_bits'],player_fields=ctor['player_fields'],rng_words=op['rng_words'],candidates=[],selection_kind2585=255,generation_counter2400=0,owned_records80_hex=ctor['owned_records_hex'],flag2581=0,flags2573=0)
        assert u(game,400)==0 and game[387]==game[2582]==game[2568]==0 and u(game,2516)==bits(1.)and u(game,2540)==1 and q(game,1336)==0
        account=bytearray([165]*368)
        for off in[196,244,256,268]:account[off:off+4]=bytes(4)
        assert a['account368_before_hex']==a['account368_after_hex']==account.hex()
        selected=bytes(opening['selected40_cells']);assert a['selected40_hex']==selected.hex()and a['selection_canaries']==['c3'*16,'d7'*16]
        profile=bytes.fromhex(a['profile376_before_hex']);wanted=bytearray(376);struct.pack_into('<I',wanted,156,4);wanted[168:172]=profile[168:172];struct.pack_into('<I',wanted,172,6);struct.pack_into('<Q',wanted,184,int(opening['constructor_seed_u64']));wanted[224:240]=selected[:16];wanted[344:346]=b'\1\1';assert u(profile,168)>0 and profile==bytes(wanted)and a['profile376_before_hex']==a['profile376_after_hex'];counts['exact_account_profile_bytes']+=368+376
        assert b['packets']==op['packets'];counts['complete_setup_packets']+=len(op['packets'])
        for name in['units','pickups','special','windows','boundaries']:
            v=b['background'][name];assert(v['capacity'],v['count'])==(op[name]['capacity'],op[name]['count'])
            for row,hx in zip(op[name]['storage'],v['storage'],strict=True):cells('opening_'+name,row,hx)
        timeline,frames,born=reference(case,opening,world,nav,scalars,tables,definitions,zone,speeds,counts);assert timeline==a['timeline'];assert [x['frame']for x in a['frames']]==list(frames)
        previous=b
        for captured in a['frames']:
            j=captured['frame'];wanted=frames[j];view=captured['view'];rawgame=header(view);assert captured['spawn']=={k:v for k,v in wanted['timeline'].items()if k!='frame'};bg=view['background'];assert(bg['units']['count'],bg['units']['capacity'])==(wanted['timeline']['count'],wanted['timeline']['capacity'])
            for i,(row,hx)in enumerate(zip(wanted['rows'],bg['units']['storage'],strict=True)):
                cells('NPC',row,hx)
                if i<len(previous['background']['units']['storage']):
                    old=bytes.fromhex(previous['background']['units']['storage'][i]);new=bytes.fromhex(hx)
                    for off,value in enumerate(row):
                        if value is None:assert old[off]==new[off];counts['NPC_None_physical_inheritance']+=1
            assert view['packets']==wanted['packets'];counts['complete_cumulative_packet_snapshots']+=len(wanted['packets'])
            assert view['projection']=={**b['projection'],'rng_words':wanted['timeline']['rng_words']}and view['live32_hex']==b['live32_hex']and view['raw_candidates80_hex']==b['raw_candidates80_hex']and view['tree_nodes']==b['tree_nodes']
            for name in['auxiliary','claims','pickups','special','windows','boundaries','movement_sequence2412']:assert bg[name]==b['background'][name];counts['background_owner_inheritance']+=1
            for off,value in[(2416,wanted['timeline']['budget2416_bits']),(2420,0),(2352,wanted['timeline']['now_bits']),*[(int(k),v)for k,v in wanted['timeline']['timer_fields'].items()]]:assert u(rawgame,off)==value
            assert list(struct.unpack_from('<3I',rawgame,2428))==op['player_xyz']and list(struct.unpack_from('<2I',rawgame,1736))==[0,0]
            old=bytes.fromhex(previous['raw_game2592_hex'])
            for off,(x,y)in enumerate(zip(old,rawgame,strict=True)):
                if off not in allowed:assert x==y,(case['id'],j,'Game',off);counts['Game_nonowned_bytes_inherited']+=1
            counts['full_capture_checkpoints']+=1;previous=view
        counts['setup2945_1600_1108_each']+=1;traces.append(dict(case=case,timeline=timeline,born=born))
    assert counts['full952_recomputed']==1080 and counts['new_NPCs']==counts['new169_packets']==47 and counts['definition1_births']==2 and counts['full_capture_checkpoints']==27
    assert counts['NPC_known']==85749 and counts['NPC_None']==69771 and counts['NPC_nonzero_None']==61295 and counts['NPC_None_physical_inheritance']==47061
    assert runtime==comp['runtime']and runtime['full_calls']=={'2945':3,'1600':3,'1108':3,'952':1080}and runtime['fresh_instances']==3
    assert runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None and runtime['memory_cap_bytes']==268435456 and runtime['peak_memory_bytes']==177078272
    returns=runtime['target_and_setup_returns'];assert len(returns)==1089 and all(r['returned']and r['before']==r['after']==1048576 for r in returns)
    assert len(runtime['world_source_checks'])==33 and all(r['ranges']==2318 and r['unchanged']for r in runtime['world_source_checks'])
    for k in['NPC_positions_written_by_driver','NPC_states_or_timers_written_by_driver','velocity_or_path_headers_written_by_driver','RNG_or_budget_written_by_driver','old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored']:assert runtime[k]is False
    assert runtime['native_executions']==runtime['full_mainloop_frames']==runtime['complete_games']==0
    terminal=load(BATCH/'owned-terminal.json');assert terminal==comp['process']==hand['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<120
    audit_source=load(BATCH/'expectation-read-audit.json');assert not audit_source['forbidden']and all(not str(p).endswith(('.wasm','.wat','.memory','.exe'))and'/originals/'not in str(p)for p in audit_source['opened'])
    for name,h in author.items():assert sha(ROOT/name)==h
    for name,h in sources.items():assert sha(ROOT/name)==h
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    assert not AUDIT
    result=dict(status='pass_current952_ordinary_stationary_before40s_only_with_timer_label_corrigendum',author_handoff_sha256=HAND,comparison_sha256=COMP,reviewer_script_sha256=sha(Path(__file__)),author_files=author,pure_helper_SHA=HELPERS,source_files=46,production_files=34,source_edges=135,sources=sources,source_import_edges=edges,current_function_bindings=bindings,only_export_section_changed=True,formal_counts=dict(fixtures=3,full952_target_entries=1080,setup2945_1600_1108_each=3,all_direct_entries=1089,reviewer_original_executions=0,reviewer_author_program_executions=0,differences=0),counts=dict(counts),timer_label_correction=dict(path=str(CORRECTION),sha256=CORRECTION_SHA,correct_roles={'2424':'60s multi-shape wave','2440':'240s ordinary elite'},v1_names_reversed=True,runtime_both_branches_not_reached=True,max_time_seconds=37.5,offset_windows=windows),owned_author_terminal=terminal,reviewer_audit=dict(AUDIT),independent_expectation_uses_author_expected=False,limits=['Full952 current complete original entry, but only default mode0 HumanWarrior Elwynn, stationary/no combat/no death,now<40s. Not all952 behavior.','Killcost+0 decay and density/far55 predicates rechecked. No nonzero decay, density-fill,55-distance recycle or timer-fired branches dynamically transferred as passing coverage.','Correct timer roles from current952:2424=60s multi-shape wave;2440=240s ordinary elite. Frozen v1 variable/report names are reversed; harmless in this<40 threshold-only domain. Do not extend using old names.','No author model/checker/builder or original execution;prior independently frozen opening/geometry/NPC/heading/Fraction helpers reused as pure algorithms under current-source binding.','All114abilities/other enemy classes are not covered:only12 declarations read,actual ordinaryspawn definitions0/1 observed.','Context is legal original resource-onlyv2snapshot/new2945/1600Game. Canonical geometry independent raw resources. Full App/WorldRc/externref producer remains unimplemented.','Full2592Game nonwrite inheritance plus known opening fields and raw vector/header/tree consistency checked. Unknown pointer/resource payload semantic meaning not invented.','NPC allocator-unwritten None remains None;physical bytes inherited where old snapshot available,not filled by observations. New allocation extra unknown cells have no invented prior.','Full47new169payloads and complete ordered packet prefixes checked at27captures;internal5719 counters are derived by WAT/reference,not directly instrumented calls.','World2318-range checks and stackreturn records are frozen runner observations/static guards,not reviewer execution. No complete game/native/network/save/Android acceptance.'],seconds=time.monotonic()-started)
    save(out/'review.json',result);save(out/'reference-traces.json',traces);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
