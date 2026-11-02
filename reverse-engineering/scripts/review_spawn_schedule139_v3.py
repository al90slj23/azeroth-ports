#!/usr/bin/env python3
"""Different-author current139952 first60s review; author/original never executed."""
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
from review_world_position139 import Reference as Position,load_world,hypot_ref
import review_enemy_ai139 as E
import review_death_pickups139 as D
from review_initial139 import reference as constructor_reference
from review_combat139 import parse_module,local_closure,sha,fp,bits

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/spawn-schedule139-v3-oracle-20261102T142920.787549Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
HAND='e93f42fbc613bc09d8e91bc6212d83acf779cecad1075802d8a5f1c8f80ee6d2'
COMP='87e6f65d4a19b56c8b14765467c95801642be7a1a85acef6bad2724fb8d78844'
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


def integer_draw(words,count,counts):
    assert count>0;limit=(count<<(32-count.bit_length()))-1
    for _ in range(10001):
        value,words=C.nextword(words);product=value*count;counts['wave_index_draws']+=1
        if product&0xffffffff<=limit:return product>>32,words
    raise AssertionError('Independent integer sampler bound')


def wave_reference(now,last,player,rows,count,words,counter,packets,definitions,zone,tables,speeds,world,nav,scalars,counts):
    minute=C.div(now,bits(60.));eligible=[i for i,d in enumerate(definitions)if not d[68]and C.rational(u(d,64))<=C.rational(minute)];pool=[i for i in eligible if C.rational(u(definitions[i],60))<=C.rational(0x3f99999a)]or eligible
    shapes=[i for i in range(4)if i!=last];index,words=integer_draw(words,len(shapes),counts);style=shapes[index];index,words=integer_draw(words,len(pool),counts);definition=pool[index];positions=[];charged=[];births=[]
    deadline=C.add(now,max(C.add(C.mul(minute,0xbfc00000),bits(60.)),bits(35.),key=C.rational))
    def uniform():
        nonlocal words
        high=0x40c90fdb
        for _ in range(10001):
            v,words=C.nextword(words);counts['wave_uniform_draws']+=1;sample=C.mul(C.sub((v>>9)|C.ONE,C.ONE),high)
            if C.rational(sample)<C.rational(high):return C.add(sample,0)
        raise AssertionError('Independent uniform bound')
    def probe(x,y,inline=False):
        counts['wave_geometry_probes']+=1
        distance=bits(hypot_ref(fp(C.sub(x,scalars['center_xy_bits'][0])),fp(C.sub(y,scalars['center_xy_bits'][1]))))
        if C.rational(distance)>C.rational(C.add(scalars['radius_bits'],bits(18.))):counts['wave_radius_rejects']+=1;return None
        height=world.height(x,y)
        if height is None:counts['wave_height_rejects']+=1;return None
        threshold=8 if C.rational(distance)>C.rational(scalars['radius_bits'])else 25
        if abs(C.rational(C.sub(height,player[2])))>threshold:counts['wave_elevation_rejects']+=1;return None
        cell,_=E.probe(nav,[x,y])
        if cell is not None and(cell==1 if inline else bool(cell)):counts['wave_nav_rejects']+=1;return None
        return[x,y,height]
    def radial(angle,radii,inline=False):
        sine,cosine=E.trig(angle)
        for radius in radii:
            xyz=probe(C.add(player[0],C.mul(cosine,bits(float(radius)))),C.add(player[1],C.mul(sine,bits(float(radius)))),inline)
            if xyz is not None:return xyz
        return None
    def append(xyz,charge=None):
        nonlocal count,words,counter
        if count>=50:counts['wave_cap50_rejections']+=1;return
        if count==len(rows):rows.extend([[None]*432 for _ in range(max(4,2*len(rows))-len(rows))])
        row,words,counter,packet=birth(definition,now,xyz,player,words,counter,rows[count],definitions,zone,tables,speeds,counts);rows[count]=row;packets.append(packet);guid=q(bytes(row[112:120]))
        if charge is not None:
            for off,value in[(16,1),(20,charge[0]),(24,charge[1]),(28,charge[2]),(348,now)]:row[off:off+4]=struct.pack('<I',value)
            charged.append(str(guid));counts['wave_charged_NPCs']+=1
        positions.append(xyz);births.append(dict(slot=count,definition_index=definition,guid=str(guid),origin='wave2424',position_bits=xyz));count+=1;counts['new_NPCs']+=1;counts['wave_NPCs']+=1;counts['new169_packets']+=1;counts['new169_payload_bytes']+=len(packet[1])//2;counts['definition'+str(definition)+'_births']+=1
    if style==0:
        requested=max(1,int(C.rational(C.mul(C.add(C.mul(minute,bits(2.5)),bits(12.)),bits(.6)))))
        for i in range(requested):
            xyz=radial(C.mul(C.div(bits(float(i)),bits(float(requested))),0x40c90fdb),range(26,7,-2),True)
            if xyz is not None:append(xyz)
    elif style==3:
        definition,words=choose(eligible,minute,words,definitions,counts);anchor=radial(uniform(),range(32,13,-2));requested=max(2,int(C.rational(C.mul(C.add(C.mul(minute,bits(.8)),bits(5.)),bits(.6)))))
        if anchor is not None:
            for i in range(requested):
                angle=C.mul(bits(float(i)),bits(2.4));sine,cosine=E.trig(angle);radius=C.add(C.mul(E.sqrt32(bits(float(i))),bits(1.6)),C.ONE);xyz=probe(C.add(anchor[0],C.mul(cosine,radius)),C.add(anchor[1],C.mul(sine,radius)))
                if xyz is None:counts['wave_anchor_fallbacks']+=1
                append(anchor if xyz is None else xyz)
    else:
        requested=max(1,int(C.rational(C.mul(C.add(C.add(minute,minute),bits(10.)),bits(.6)))))
        if style==1:
            #Current952 compares finite-positive field52 with later-row tie.
            definition=max(pool,key=lambda i:(C.rational(u(definitions[i],52)),i));theta=uniform();anchor=radial(C.add(theta,0x40490fdb),range(34,13,-2))
            if anchor is not None:
                sine,cosine=E.trig(theta);distance=bits(hypot_ref(fp(C.sub(anchor[0],player[0])),fp(C.sub(anchor[1],player[1]))));travel=C.add(C.add(distance,distance),bits(12.));speed=max(C.mul(C.mul(u(definitions[definition],52),0x3f866666),bits(1.4)),C.ONE,key=C.rational);duration=C.div(travel,speed);columns=(requested+1)//2;middle=C.mul(C.sub(bits(float(columns)),C.ONE),bits(.5))
                for i in range(requested):
                    rr,cc=divmod(i,columns);lateral=C.mul(C.sub(bits(float(cc)),middle),bits(2.6));x=C.sub(C.sub(anchor[0],C.mul(sine,lateral)),C.mul(C.mul(cosine,bits(float(rr))),bits(3.)));y=C.sub(C.add(anchor[1],C.mul(cosine,lateral)),C.mul(C.mul(sine,bits(float(rr))),bits(3.)));xyz=probe(x,y)
                    if xyz is not None:append(xyz,[C.add(xyz[0],C.mul(cosine,travel)),C.add(xyz[1],C.mul(sine,travel)),C.add(C.add(duration,now),bits(3.))])
        else:
            theta=uniform();start=C.sub(theta,bits(1.2))
            for i in range(requested):
                angle=C.add(start,C.div(C.mul(C.add(bits(float(i)),bits(.5)),bits(2.4)),bits(float(requested))));xyz=radial(angle,range(30,11,-2),True)
                if xyz is not None:append(xyz)
    assert positions,'Natural first-wave anchor expected in this captured domain'
    counts['wave_shape'+str(style)]+=1
    return dict(rows=rows,count=count,words=words,counter=counter,deadline=deadline,last=style,definition_index=definition,requested=requested,born=births,charged=charged)


def reference(case,opening,world,nav,scalars,tables,definitions,zone,speeds,names,messages,counts):
    p=opening['projection'];player=p['player_xyz'];rows=copy.deepcopy(p['units']['storage']);count=p['units']['count'];pickups=copy.deepcopy(p['pickups']['storage']);pickup_count=p['pickups']['count'];words=tuple(p['rng_words']);counter=p['counter'];packets=copy.deepcopy(p['packets']);budget=bits(3.);clock=0;last=255
    timeline=[];frames={};born=[];timers={'2424':bits(60.),'2440':bits(240.),'2444':bits(40.),'2448':bits(60.),'2452':20,'2456':0};previous_xyz=[0,0,0];waves=[]
    for frame in range(case['frames']):
        clock=C.add(clock,case['dt_bits']);assert C.rational(clock)<=64 and C.rational(clock)<C.rational(timers['2440'])
        for row in rows[:count]:
            assert read(row,0)==0 and read(row,244)==0xffffffff and read(row,344)==0
            distance=C.distance((read(row,328),read(row,332)),player);assert C.rational(distance)<=3025;counts['far55_predicates_not_taken']+=1
        velocity=[C.div(C.sub(player[i],previous_xyz[i]),case['dt_bits'])for i in range(2)]
        if frame==0:assert C.rational(C.distance(velocity,(0,0)))>=1600;counts['first_velocity_jump_filtered']+=1
        else:assert velocity==[0,0]
        previous_xyz=player[:];minute=C.div(clock,bits(60.));rate=C.mul(C.add(C.add(C.mul(minute,0x3ea3d70a),0x3f666666),C.mul(minute,C.mul(minute,0x3ccccccd))),0x3f19999a);budget=C.add(budget,C.mul(case['dt_bits'],rate));counts['zero_killcost_decay_predicates']+=1
        eligible=[i for i,d in enumerate(definitions)if d[68]==0 and C.rational(u(d,64))<=C.rational(minute)]
        def attempt(index,origin):
            nonlocal words,counter,count
            if count>=50:counts['budget_cap50_rejections']+=1;return False
            location=Position(dict(zone=0,player_xyz=player,velocity_xy=[0,0],low_radius_bits=bits(26.),high_radius_bits=bits(36.),bias_probability_bits=bits(.5),rng_words=words,distance_map=None),world,nav,scalars,tables);xyz=location.spawn();words=location.words
            if count==len(rows):rows.extend([[None]*432 for _ in range(max(4,2*len(rows))-len(rows))])
            row,words,counter,packet=birth(index,clock,xyz,player,words,counter,rows[count],definitions,zone,tables,speeds,counts);rows[count]=row;packets.append(packet);born.append(dict(frame=frame,slot=count,definition_index=index,guid=str(q(bytes(row[112:120]))),origin=origin,position_bits=xyz));count+=1;counts['new_NPCs']+=1;counts['budget_NPCs']+=int(origin=='budget');counts['new169_packets']+=1;counts['new169_payload_bytes']+=len(packet[1])//2;counts['definition'+str(index)+'_births']+=1;return True
        if C.rational(budget)>=1:
            for iteration in range(8):
                index,words=choose(eligible,minute,words,definitions,counts);cost=u(definitions[index],60);counts['budget_choice_attempts']+=1
                if C.rational(cost)>C.rational(budget):counts['budget_insufficient_choice_breaks']+=1;break
                if not attempt(index,'budget'):budget=min(cost,budget,key=C.rational);break
                budget=C.sub(budget,cost)
                if C.rational(budget)<1:break
            else:counts['eight_budget_loop_limit_hits']+=1
        target=int(min(36,C.rational(C.add(C.mul(minute,0x3fcccccd),bits(4.)))));alive=sum(read(row,0)==0 and read(row,284)!=0 and definitions[(read(row,284)-5830904)//72][68]==0 for row in rows[:count]);fill=min(3,max(0,target-alive));counts['density_predicates']+=1;counts['density_fill_requested']+=fill
        for _ in range(fill):
            index,words=choose(eligible,minute,words,definitions,counts)
            if not attempt(index,'density'):break
        if C.rational(clock)>=C.rational(timers['2424']):
            wave=wave_reference(clock,last,player,rows,count,words,counter,packets,definitions,zone,tables,speeds,world,nav,scalars,counts);rows=wave['rows'];count=wave['count'];words=wave['words'];counter=wave['counter'];timers['2424']=wave['deadline'];last=wave['last'];name=names[wave['definition_index']];message=messages[last]
            raw=b'\x5a'+struct.pack('<II',0,len(name)+1)+name+b'\0'+bytes(8)+struct.pack('<I',len(message)+1)+message+b'\0\0';packets.append([150,raw.hex()]);counts['wave150_packets']+=1;born.extend(dict(frame=frame,**entry)for entry in wave['born']);waves.append(dict(frame=frame,**{key:wave[key]for key in['last','definition_index','requested','charged','deadline']}))
        for row in p['windows']['storage'][:p['windows']['count']]:assert C.rational(clock)<C.rational(read(row,4)),'Window due remains outside admitted domain'
        def pickup(radius_low,radius_high,kind,amount,entry,display,actor_kind):
            nonlocal words,counter,pickup_count
            location=Position(dict(zone=0,player_xyz=player,velocity_xy=[0,0],low_radius_bits=bits(radius_low),high_radius_bits=bits(radius_high),bias_probability_bits=bits(.5),rng_words=words,distance_map=None),world,nav,scalars,tables);xyz=location.random();words=location.words;placed,clamped=D.geometry(dict(xyz=xyz),world,scalars);assert not clamped
            counter=(counter+1)&0xffffffff;guid=0xf110000000000000|((entry&0xffffff)<<24)|(counter&0xffffff);yaw,words=O.uniform(words,0.,fp(0x40c90fdb));packets.append([169,O.object_packet(guid,entry,display,C.ONE,placed,O.f32(yaw+0.),actor_kind,0)])
            if pickup_count==len(pickups):pickups.extend([[None]*56 for _ in range(max(4,2*len(pickups))-len(pickups))])
            row=pickups[pickup_count];row[0:4]=bytes(4);row[8:12]=struct.pack('<I',kind);row[12:16]=[None]*4 if amount is None else struct.pack('<I',amount);row[16:56]=struct.pack('<Q4I4I',guid,0,8,0,entry,*placed,clock);pickup_count+=1;counts['pickup169_packets']+=1;counts['pickup_kind'+str(kind)]+=1
        if C.rational(clock)>=C.rational(timers['2444']):
            timers['2444']=C.add(clock,bits(45.));assert sum(read(r,8)in(3,4,5)for r in pickups[:pickup_count])<2
            for _ in range(10001):
                output,words=C.nextword(words);product=output*3;counts['kind3range_draws']+=1
                if product&0xc0000000!=0xc0000000:break
            else:raise AssertionError('Independent kind3 RNG bound')
            kind=3+(product>>32);pickup(15.,40.,kind,words[0],9006+(kind-3),{3:5931,4:5995,5:5991}[kind],5)
        if C.rational(clock)>=C.rational(timers['2448']):
            timers['2448']=C.add(clock,bits(70.));assert pickup_count==3 and sum(read(r,8)==2 for r in pickups[:pickup_count])==2;pickup(18.,50.,2,None,9005,259,3);counts['Rune_argument2_unknown4']+=4
        counts['full952_recomputed']+=1
        line=dict(frame=frame,last_wave2586=last,count=count,capacity=len(rows),rng_words=list(words),counter2408=counter,now_bits=clock,budget2416_bits=budget,kill_cost2420_bits=0,previous_player_xyz=player,velocity_xy=[0,0],timer_fields=copy.deepcopy(timers),packet_count=len(packets));timeline.append(line)
        if frame in case['checkpoints']or frame==case['frames']-1:frames[frame]=dict(timeline=copy.deepcopy(line),rows=copy.deepcopy(rows),pickups=copy.deepcopy(pickups),pickup_count=pickup_count,packets=copy.deepcopy(packets))
    return timeline,frames,born,waves

def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP and sha(SOURCE)==WASM and sha(CORRECTION)==CORRECTION_SHA
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');runtime=load(BATCH/'runtime.json');cfg=load(BATCH/'config.json');author=hand['author_files'];assert len(author)==8
    for name,digest in author.items():assert sha(ROOT/name)==digest
    helpers={**HELPERS,**D.HELPERS,**E.HELPERS,'scripts/review_enemy_ai139.py':'73b093bdfcc59c08c010fb2c074298435b6d0f057fe15a0e5d2a8228c0fe0f42','scripts/review_death_pickups139.py':'092328f7b6e7c5323f1d3b9c74b1080b1181fdd002f7153d32756110d9dcaef3','scripts/review_spawn_schedule139.py':'b2e9997dff3d356e637945806802dde95354e7ffdc86c796275e7bfa3d2e1fe2'}
    for name,digest in helpers.items():assert sha(ROOT/name)==digest,(name,sha(ROOT/name))
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==50 and sum(name.startswith('reconstruction/')for name in sources)==38
    for name,digest in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==digest
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==161
    for table in[comp['artifacts'],comp['frozen'],prep['frozen']]:
        for name,digest in table.items():assert sha(BATCH/name)==digest
    assert comp['cases']==comp['completed_cases']==4 and comp['differences']==0 and comp['expected_before_original']and prep['expected_before_original']and not comp['original_input_contains_expected']and not prep['original_input_contains_expected']
    expectation_audit=load(BATCH/'expectation-read-audit.json');assert not expectation_audit['forbidden']and all('/originals/'not in str(p)and not str(p).endswith(('.wasm','.wat','.memory','.exe'))for p in expectation_audit['opened'])
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    assert sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')==comp['resource_context_gate_sha256']==prep['resource_context_gate_sha256']=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==comp['independent_world_receipt_sha256']==prep['independent_world_receipt_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));assert not scalars['primary_present']and not scalars['flat_present']
    raw=SOURCE.read_bytes();original=parse_module(raw);private=(BATCH/m['module_file']).read_bytes();assert sha(BATCH/m['module_file'])==m['module_sha256'];modified=parse_module(private)
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
    exports=[('research139_spawn_companion',0,2945),('research139_spawn_initial',0,1600),('research139_spawn_opening',0,1108),('research139_spawn_tick952',0,952),('research139_spawn_stack',3,0)]
    assert modified['exports']==original['exports']+exports and len(original['imports'])==882 and m['added_exports']==[list(x)for x in exports]
    assert[(r['module'],r['name'],r['type_index'])for r in original['imports']]==[(r['module'],r['name'],r['type_index'])for r in m['original_imports']]and original['types'][original['decl'][952-882]]==('7f7d','')
    texts={};bindings={};extra={6786,33028,35202,35232,57285,108362,1711,24602,46462,55846}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as s:
        for idx in sorted(set(map(int,m['functions']))|extra):
            lo,hi=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();s.seek(start);wat=s.read(end-start);record=dict(body_sha256=hashlib.sha256(raw[lo:hi]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());texts[idx]=wat.decode();bindings[str(idx)]=record
            if str(idx)in m['functions']:assert record['body_sha256']==m['functions'][str(idx)]['body_sha256']and record['WAT_sha256']==m['functions'][str(idx)]['WAT_sha256']and wat==(BATCH/'static'/f'{idx}.wat').read_bytes()
            (out/f'{idx}.wat').write_bytes(wat)
    assert len(m['functions'])==32
    scheduler=texts[952];correction=load(CORRECTION);assert hashlib.sha256(scheduler.encode()).hexdigest()==correction['current952_WAT_sha256']
    for window in correction['windows'].values():
        first,last=window['local_WAT_lines'];value='\n'.join(scheduler.splitlines()[first-1:last])+'\n';assert hashlib.sha256(value.encode()).hexdigest()==window['sha256']
    assert scheduler.index('f32.load offset=2424')<scheduler.index('f32.load offset=2444')<scheduler.index('f32.load offset=2448')
    charge='\n'.join(scheduler.splitlines()[6430:6670]);assert 'f32.const 0x1.8p+3 (;=12;)'in charge and'f32.const 0x1.666666p+0 (;=1.4;)'in charge and'f32.const 0x1.4cccccp+1 (;=2.6;)'in charge and'call 5719'in charge
    rune='\n'.join(scheduler.splitlines()[8050:8235]);assert 'f32.const 0x1.18p+6 (;=70;)'in rune and'i32.const 176'in rune and'i32.const 56'in rune and'f32.const 0x1.2p+4 (;=18;)'in rune and'f32.const 0x1.9p+5 (;=50;)'in rune and'call 1446'in rune
    assert 'f32.const 0x1.2p+4 (;=18;)'in texts[31851]and'f32.const 0x1p+3 (;=8;)'in texts[31851]and'f32.const 0x1.9p+4 (;=25;)'in texts[31851]and'call 50441'in texts[31851]
    assert 'f32.const 0x1.cd5f9ap-8'in texts[97427]and'f32.const 0x1.8548aap-8'in texts[97426]and'call 97427'in texts[5719]
    def data(address,size):
        result=bytearray(size)
        for at,pos,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
        return bytes(result)
    for address_size,claim in m['static_reads'].items():
        address,size=map(int,address_size.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==claim['sha256']and size==claim['bytes']
    word=lambda p:u(data(p,4));text=lambda p,n:data(p,n).decode();abilities={}
    for i in range(114):
        p=5882740+88*i;r=data(p,88);abilities[text(u(r,12),u(r,16))]=(p,r)
    cls=data(5877920,108);classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};race=data(5874636,44);races={1:dict(ability_pointer=abilities[text(u(race,24),u(race,28))][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);scalars['heading_bits']=u(zone,116);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];definitions=[data(5830904+72*i,72)for i in range(12)];eligible=[i for i,d in enumerate(definitions)if d[68]==1 and math.isfinite(fp(u(d,64)))];minutes=word(u(zone,72)+336)
    tables=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888;names=[data(u(d,16),u(d,20))for d in definitions];messages=[data(p,n)for p,n in[(1593856,20),(1593892,27),(1593919,25),(1593944,17)]]
    tree=ast.parse((ROOT/'reconstruction/core_spec/spawn_schedule139_data.py').read_text());literal={n.targets[0].id:ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)};assert literal==dict(ELWYNN152_HEX=zone.hex(),NORMAL_BASE=5830904,NORMALS72_HEX=tuple(x.hex()for x in definitions))
    names_tree=ast.parse((ROOT/'reconstruction/core_spec/spawn_wave139_data.py').read_text());name_literals={n.targets[0].id:ast.literal_eval(n.value)for n in names_tree.body if isinstance(n,ast.Assign)};assert tuple(names_tree.body)and name_literals['NORMAL_NAMES139']==tuple(x.decode()for x in names)
    cases=load(BATCH/'inputs.json');actual=[json.loads(line)for line in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==4 and[(c['app_seed_u64'],c['frames'],c['dt_bits'])for c in cases]==[(str(seed),1024,bits(.0625))for seed in[0,1,5,8]]
    counts=Counter();traces=[]
    def cells(label,wanted,hx):
        seen=bytes.fromhex(hx);assert len(wanted)==len(seen)
        for off,(value,byte)in enumerate(zip(wanted,seen,strict=True)):
            if value is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(byte)
            else:assert value==byte,(label,off,value,byte);counts[label+'_known']+=1
    def header(view):
        game=bytes.fromhex(view['raw_game2592_hex']);proj=view['projection'];bg=view['background'];assert len(game)==2592
        for key,off in[('level',1432),('xp',1436),('pending',2376),('current_hp_bits',1440),('generation_counter2400',2400)]:assert u(game,off)==proj[key]
        assert{str(1536+4*j):u(game,1536+4*j)for j in range(23)}==proj['derived_bits']and[u(game,1720+4*j)for j in range(4)]==proj['rng_words']and game[2587]==proj['phase2587']==1
        for name,cap,ptr,n,width in[('units',1784,1788,1792,432),('pickups',1868,1872,1876,56),('special',1916,1920,1924,40),('windows',1964,1968,1972,8),('boundaries',2120,2124,2128,8),('claims',2108,2112,2116,88),('auxiliary',652,656,660,112)]:
            v=bg[name];assert(v['capacity'],v['pointer'],v['count'],v['stride'])==(u(game,cap),u(game,ptr),u(game,n),width)and len(v['storage'])==v['capacity']and all(len(s)==2*width for s in v['storage']);counts['vector_headers']+=1
        assert u(game,1888)==len(view['packets'])<=u(game,1880)and u(game,2408)==bg['counter2408']and u(game,2412)==bg['movement_sequence2412']and u(game,1712)==len(view['live32_hex'])==0 and u(game,1664)==len(proj['owned_records80_hex'])==1
        return game
    for case,a in zip(cases,actual,strict=True):
        assert a['id']==case['id']and a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['stack_after']==1048576
        opening,_=O.reference(case,world,nav,scalars,tables,definitions[0],speeds,classes,races,zones,eligible,minutes);op=opening['projection'];known=opening['known_Game2592']
        for off,value in[(1736,0),(1740,0),(2368,0),(1984,0),(2416,bits(3.)),(2420,0)]:known[off:off+4]=struct.pack('<I',value)
        known[2586]=255;assert a['opening']==a['before'];b=a['before'];game=header(b);cells('openingGame',known,b['raw_game2592_hex']);assert a['constructor_seed_u64']==opening['constructor_seed_u64']
        ctor,_=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=opening['constructor_seed_u64'],object_id_u64='0',flat_height_bits=world.height(*scalars['center_xy_bits'])),classes,races,zones)
        assert b['projection']==dict(level=1,xp=0,pending=0,phase2587=1,current_hp_bits=ctor['current_hp_bits'],derived_bits=ctor['derived_bits'],player_fields=ctor['player_fields'],rng_words=op['rng_words'],candidates=[],selection_kind2585=255,generation_counter2400=0,owned_records80_hex=ctor['owned_records_hex'],flag2581=0,flags2573=0)
        account=bytearray([165]*368)
        for off in[196,244,256,268]:account[off:off+4]=bytes(4)
        assert a['account368_before_hex']==a['account368_after_hex']==account.hex();selected=bytes(opening['selected40_cells']);assert a['selected40_hex']==selected.hex()and a['selection_canaries']==['c3'*16,'d7'*16]
        profile=bytes.fromhex(a['profile376_before_hex']);wanted=bytearray(376);struct.pack_into('<I',wanted,156,4);wanted[168:172]=profile[168:172];struct.pack_into('<I',wanted,172,6);struct.pack_into('<Q',wanted,184,int(opening['constructor_seed_u64']));wanted[224:240]=selected[:16];wanted[344:346]=b'\1\1';assert u(profile,168)>0 and bytes(wanted)==profile and a['profile376_before_hex']==a['profile376_after_hex']
        assert b['packets']==op['packets'];counts['setup_packets']+=len(op['packets'])
        for name in['units','pickups','special','windows','boundaries']:
            v=b['background'][name];assert(v['capacity'],v['count'])==(op[name]['capacity'],op[name]['count'])
            for row,hx in zip(op[name]['storage'],v['storage'],strict=True):cells('opening_'+name,row,hx)
        timeline,frames,born,waves=reference(case,opening,world,nav,scalars,tables,definitions,zone,speeds,names,messages,counts);assert timeline==a['timeline'];assert[x['frame']for x in a['frames']]==list(frames)
        previous=b;pcap=128
        for cap in a['frames']:
            j=cap['frame'];want=frames[j];view=cap['view'];rawgame=header(view);line=want['timeline'];bg=view['background'];assert cap['spawn']=={k:v for k,v in line.items()if k!='frame'}
            assert(bg['units']['capacity'],bg['units']['count'])==(line['capacity'],line['count'])and(bg['pickups']['capacity'],bg['pickups']['count'])==(len(want['pickups']),want['pickup_count'])
            for i,(row,hx)in enumerate(zip(want['rows'],bg['units']['storage'],strict=True)):
                cells('NPC',row,hx)
                if i<len(previous['background']['units']['storage']):
                    old=bytes.fromhex(previous['background']['units']['storage'][i]);new=bytes.fromhex(hx)
                    for off,value in enumerate(row):
                        if value is None:assert old[off]==new[off];counts['NPC_None_physical_inheritance']+=1
            for i,(row,hx)in enumerate(zip(want['pickups'],bg['pickups']['storage'],strict=True)):
                cells('pickup',row,hx)
                if i<previous['background']['pickups']['capacity']:
                    old=bytes.fromhex(previous['background']['pickups']['storage'][i]);new=bytes.fromhex(hx)
                    for off,value in enumerate(row):
                        if value is None and not(i==3 and 12<=off<16 and previous['background']['pickups']['count']<4<=bg['pickups']['count']):assert old[off]==new[off];counts['pickup_None_physical_inheritance']+=1
            assert view['packets']==want['packets'];counts['cumulative_packet_snapshots']+=len(want['packets'])
            assert view['projection']=={**b['projection'],'rng_words':line['rng_words']}and view['live32_hex']==b['live32_hex']and view['raw_candidates80_hex']==b['raw_candidates80_hex']and view['tree_nodes']==b['tree_nodes']
            for name in['special','windows','boundaries','auxiliary','claims','movement_sequence2412']:assert bg[name]==b['background'][name];counts['background_owner_inheritance']+=1
            assert bg['pickups']['storage'][:2]==b['background']['pickups']['storage'][:2]
            wantgame=bytearray.fromhex(previous['raw_game2592_hex'])
            for off,value in[(1720+4*k,v)for k,v in enumerate(line['rng_words'])]+[(1736,0),(1740,0),(1784,line['capacity']),(1792,line['count']),(1868,len(want['pickups'])),(1876,want['pickup_count']),(1888,line['packet_count']),(2352,line['now_bits']),(2408,line['counter2408']),(2416,line['budget2416_bits']),(2420,0),*[(2428+4*k,v)for k,v in enumerate(op['player_xyz'])],*[(int(k),v)for k,v in line['timer_fields'].items()]]:struct.pack_into('<I',wantgame,off,value)
            while pcap<len(want['packets']):pcap=max(4,2*pcap)
            struct.pack_into('<I',wantgame,1880,pcap);wantgame[2586]=line['last_wave2586']
            oldgame=bytes.fromhex(previous['raw_game2592_hex'])
            for capoff,ptroff in[(1784,1788),(1868,1872),(1880,1884)]:
                if u(wantgame,capoff)!=u(oldgame,capoff):assert u(rawgame,ptroff)>0;wantgame[ptroff:ptroff+4]=rawgame[ptroff:ptroff+4];counts['observed_reallocation_pointer_words']+=1
            assert bytes(wantgame)==rawgame,(case['id'],j,[(i,x,y)for i,(x,y)in enumerate(zip(wantgame,rawgame))if x!=y][:8]);counts['fullGame2592_bytes']+=2592;counts['full_checkpoints']+=1;previous=view
        assert a['timeline'][-1]['count']==50 and a['timeline'][-1]['now_bits']==bits(64.)and waves[0]['frame']==959 and len(waves)==1
        traces.append(dict(case=case,born=born,waves=waves,timeline=timeline))
    assert counts['full952_recomputed']==4096 and counts['new_NPCs']==184 and counts['budget_NPCs']==166 and counts['wave_NPCs']==18 and counts['new169_packets']==184 and counts['wave150_packets']==4 and counts['pickup169_packets']==8 and counts['pickup_kind2']==4 and counts['full_checkpoints']==56
    assert[traces[i]['waves'][0]['last']for i in range(4)]==[0,1,2,3]and counts['wave_charged_NPCs']==5
    assert runtime==comp['runtime']and runtime['full_calls']=={'2945':4,'1600':4,'1108':4,'952':4096}and runtime['fresh_instances']==4 and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None
    assert len(runtime['target_and_setup_returns'])==4108 and all(r['returned']and r['before']==r['after']==1048576 for r in runtime['target_and_setup_returns'])and len(runtime['world_source_checks'])==64 and all(r['ranges']==2318 and r['unchanged']for r in runtime['world_source_checks'])
    assert runtime['stack_checks']==4128 and runtime['allocator_calls']==20 and runtime['peak_memory_bytes']==177078272<=runtime['memory_cap_bytes']==268435456
    proofs=runtime['Rune2448_argument2_proofs'];assert len(proofs)==4
    for index,proof in enumerate(proofs):
        assert proof['frame']==959 and proof['preRune_count']==3 and proof['matched']and proof['expression_argument2']==proof['actual_argument2']==proof['preRune_base']+176
        before=next(c['view']for c in actual[index]['frames']if c['frame']==958);after=next(c['view']for c in actual[index]['frames']if c['frame']==959)
        assert before['background']['pickups']['pointer']==after['background']['pickups']['pointer']==proof['preRune_base']and read(list(bytes.fromhex(after['background']['pickups']['storage'][3])),12)==proof['actual_argument2'];counts['Rune_opaque_argument2_physical_expressions']+=1
    for key in['NPC_positions_written_by_driver','NPC_states_or_timers_written_by_driver','velocity_or_path_headers_written_by_driver','RNG_or_budget_written_by_driver','old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','App_or_world_Rc_producer_executed','externref_restored']:assert runtime[key]is False
    assert runtime['full952_body_unchanged']and runtime['real_initial_budget3']and runtime['active_initial_NPCs_retained']and runtime['internal5719_calls_notinstrumented']and runtime['native_executions']==runtime['full_mainloop_frames']==runtime['complete_games']==0
    terminal=load(BATCH/'owned-terminal.json');assert terminal==comp['process']==hand['original_process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing'];assert load(BATCH/'owned-start.json')['deadline_seconds']==120
    for name,digest in author.items():assert sha(ROOT/name)==digest
    for name,digest in sources.items():assert sha(ROOT/name)==digest
    assert not AUDIT
    result=dict(accepted=True,status='current139_default_stationary_full952_through64s_first_wave_all_shapes_and_firstRune_only',author_handoff_sha256=HAND,author_comparison_sha256=COMP,reviewer_sha256=sha(Path(__file__)),author_files=author,helpers=helpers,source_files=50,production_files=38,source_edges=161,current_function_bindings=bindings,only_export_section_changed=True,formal_counts=dict(fixtures=4,target_full952=4096,setup2945_1600_1108=12,all_direct_entries=4108,reviewer_author_program_executions=0,reviewer_original_executions=0,differences=0),counts=dict(counts),original_process=terminal,independent_expected_values_from_author=False,reviewer_forbidden=dict(AUDIT),old_timer_label_corrigendum_sha256=CORRECTION_SHA,correct_timer_roles={'2424':'first60s multishape wave','2440':'240s ordinary elite'},full884_frames=0,complete_games=0,limits=['Default stationary HumanWarrior Elwynn up to64s only; no AI/combat/death or nonzero killcost and no full884 frame.', 'Ordinary budget166 + wave18 =184 real new NPCs; four40s resources + four60sRune =8 actors;192new169+4new150; no old135/139-v1/v2 runtime acceptance transferred.', 'Wave style0..3 are natural first-wave inputs, including5 genuine stampede charge records; only one wave/locale/domain, not repeated/wave multiplayer/positivevelocity.', 'NPC cap50 admission and density/far55 predicates independently evaluated; positive density-fill/far-recycle not reached.', 'Full windows/background kept; no due-window branch,180sBoss or240selite.', 'Unknown432/56B allocator gaps retained logicallyNone; firstRune+12 remainsNone, with a separate original raw pointer-expression proof preRuneBase+176; no output filling of independent logical state.', 'Whole2592Game exact overlay per56checkpoint, reallocated pointer values observed only on independently predicted capacity changes; heap addresses/layout not predicted.', 'Resource-only original v2 context and independently queried world are explicit inputs; no reconstructed fullApp/WorldRc/externref bootstrap.', 'Worldrange/stack observations verified from frozen instrumentation+flags, not fresh reviewer execution or independent raw fullresource pairs.', 'No original/author programs executed by reviewer; currentWAT/table/data plus frozen pure different-author math/opening/geometry/NPC helpers.'],seconds=time.monotonic()-started)
    save(out/'review.json',result);save(out/'reference-traces.json',traces);print(json.dumps({key:result[key]for key in['accepted','formal_counts','seconds']})+'\n'+json.dumps(dict(counts)),flush=True)


if __name__=='__main__':main()
