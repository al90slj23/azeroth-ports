#!/usr/bin/env python3
"""Different-author read-only139 naturalNPC→two922→ordinarydeath review."""
from collections import Counter
from datetime import datetime,timezone
from fractions import Fraction
from pathlib import Path
import ast,hashlib,json,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_cast139 as C
import review_death_pickups139 as D
from review_combat139 import sha,parse_module,local_closure,fp,bits
from review_initial139 import default_stats,record,rng
from review_natural_npc139 import reference as natural_reference
from review_world_position139 import load_world,trig

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/death139-oracle-20261102T052717.430579Z'
STATIC=ROOT/'evidence/death139-static-20261102T053150.470026Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
COMPARISON='b60e7e11544120c98ed6008a23d538ed15e4743f44c6fe169d7841136faae5af'
HANDOFF='84df738e15a679ac55e435e704513027bec995f7734dba2914b23cadc45a0d4e'
STATIC_SHA='0d2df6b5199a7b3ede1d1ec9fe6dd1bd3ca1d5af4cdd404fb199bfa9985d4dfd'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={
 'review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b',
 'review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
 'review_initial139.py':'86d33e69c361eef223ad3ef271b6fb987d170f4d94847c0c068148c56ebe6fbc',
 'review_natural_npc139.py':'e14d0e0baa3f408380525a78c85ee068d5f5d4c52322e6dae20e76d8c1f4b665',
 'review_npc_spawn139.py':'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074',
 'review_world_position139.py':'d842c619169a582ab8eb540cab2829233eb633bbd79d10ab674c50e71c92ab7e',
 'review_player_motion135.py':'8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2',
 'review_death_pickups139.py':'092328f7b6e7c5323f1d3b9c74b1080b1181fdd002f7153d32756110d9dcaef3'}
READS=Counter()

def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def read(row,offset,width=4):
    part=row[offset:offset+width]
    assert len(part)==width and None not in part,('unknown_reference_read',offset,width)
    READS[offset,width]+=1
    return int.from_bytes(bytes(part),'little')
def put(row,offset,value):row[offset:offset+4]=struct.pack('<I',value)
def current_xyz(row):
    duration=read(row,344)
    if C.rational(duration)<=0:return tuple(read(row,o)for o in(328,332,336))
    t=C.div(C.sub(0,read(row,340)),duration)
    t=0 if C.rational(t)<0 else C.ONE if C.rational(t)>1 else t
    return tuple(C.add(read(row,a),C.mul(C.sub(read(row,b),read(row,a)),t))for a,b in((316,328),(320,332),(324,336)))
def stable(values,key):
    answer=[]
    for value in values:
        j=len(answer)
        while j and key(answer[j-1])>key(value):j-=1
        answer.insert(j,value)
    return answer

def select(rows,player,definition,owned,derived):
    square=C.mul(C.u(definition,56),C.u(definition,56));candidates=[]
    for i,row in enumerate(rows):
        assert all(read(row,o)==C.M for o in(40,64,244))and read(row,424,1)==0
        assert read(row,416)==read(row,420)==0
        if read(row,0)==0 and C.le(C.distance(current_xyz(row)[:2],player[:2]),square):candidates.append(i)
    candidates=stable(candidates,lambda i:C.totalkey(C.distance(current_xyz(rows[i])[:2],player[:2])))
    normal,deferred=[],[]
    for i in candidates:(deferred if C.rational(read(rows[i],380))>0 else normal).append(i)
    near,far=[],[]
    if normal:
        centre=current_xyz(rows[normal[0]])[:2]
        for i in normal:(near if C.rational(C.distance(current_xyz(rows[i])[:2],centre))<=36 else far).append(i)
    near=stable(near,lambda i:C.totalkey(read(rows[i],288)))
    limit=C.u(definition,64)
    limit=max(1,(limit+C.u(owned,20)+C.u(owned,60)+derived[1592])&C.M)if limit else 1
    return(near+far+deferred)[:limit]

def uniform24(words):
    word,words=C.nextword(words)
    return C.mul(C.rounded(Fraction(word>>8)),0x33800000),tuple(words)

def pickup(kind,amount,xyz,world,scalars,speeds,state):
    """Direct known/None rows; no opaque completion or production call."""
    placed,clamped=D.geometry(dict(xyz=xyz),world,scalars);rows=state['pickups'];count=state['pickup_count'];counter=(state['counter']+1)&C.M;words=state['words']
    assert kind in(0,1)and sum(read(r,0)==0 and read(r,8)==0 for r in rows[:count])<45
    if kind==0:
        guid=0xf130002329000000|(counter&0xffffff)
        scale,display=(0x3f666666,16587)if amount>=20 else(0x3eb33333,1825)if amount>=4 else(0x3e6147ae,1825)
        fields={0:guid&C.M,1:guid>>32,2:9,3:9001,4:scale,22:1,28:1,34:1,35:35,46:33554434,129:1036831949,130:1036831949,131:display,132:display}
        packet=b'\x01\x00\x00\x00\x00\x03'+C.packguid(guid)+b'\x03\x70'+bytes(8)+struct.pack('<4I',*placed,0)+bytes(4)+struct.pack('<6I',*speeds)+struct.pack('<I',1)+D.values_payload(fields);visual=9001
    else:
        guid=0xf110000000000000|(9004<<24)|(counter&0xffffff);draws=0
        while True:
            word,words=C.nextword(words);draws+=1;assert draws<10000
            yaw=C.mul(C.sub((word>>9)|C.ONE,C.ONE),0x40c90fdb)
            if C.rational(yaw)<C.rational(0x40c90fdb):break
        half=C.mul(yaw,0x3f000000);si,co=trig(fp(half))
        fields={0:guid&C.M,1:guid>>32,2:33,3:9004,4:0x3f19999a,8:2614,9:0,12:bits(si),13:bits(co),14:1,15:placed[0],16:placed[1],17:placed[2],18:yaw,20:35,21:5}
        packet=b'\x01\x00\x00\x00\x00\x02'+C.packguid(guid)+b'\x05\x50'+struct.pack('<4I',*placed,yaw)+struct.pack('<I',1)+D.values_payload(fields);visual=9004
    if count==len(rows):rows.extend([[None]*56 for _ in range(max(4,2*len(rows))-len(rows))])
    row=rows[count];row[0:4]=bytes(4);row[8:24]=struct.pack('<IIQ',kind,amount,guid);row[24:40]=struct.pack('<4I',0,8,0,visual);row[40:56]=struct.pack('<4I',*placed,0)
    state.update(pickup_count=count+1,counter=counter,words=tuple(words));return[169,packet.hex()],dict(kind=kind,amount=amount,guid=str(guid),position_bits=placed,clamped=clamped)

def cast_reference(state,player,derived,definition,owned,world,scalars,speeds,npc_def):
    rows=state['rows'];chosen=select(rows,player,definition,owned,derived);ids=[read(rows[i],112,8)for i in chosen];spell=C.u(definition,44)
    for values in state['sets']:
        if spell not in values:values.append(spell)
    value=C.mul(C.mul(C.mul(C.mul(C.u(definition,48),0x3fb33333),C.u(owned,12)),C.u(owned,52)),C.ONE);life=C.mul(derived[1536],C.u(owned,72))if C.rational(C.u(definition,48))>0 else 0;base=C.mul(derived[1540],C.add(value,life))
    packets=[]if not ids else[[306,C.launch(0,spell,ids)]];hits=[]
    for i in chosen:
        row=rows[i];chance,state['words']=uniform24(state['words']);critical=int(C.rational(C.add(0,derived[1548]))>C.rational(chance));amount=C.mul(base,derived[1552])if critical else base
        assert read(row,284)==5830904 and read(row,240)==0
        mult=C.ONE
        if C.rational(read(row,148))>0:mult=C.add(mult,read(row,144))
        term=read(row,152)if C.rational(read(row,156))>0 else read(row,160)if C.rational(read(row,164))>0 else 0
        mult=C.add(C.add(C.add(mult,term),read(row,368)),0);school=0x3dcccccd if definition[85]&254==2 and C.rational(read(row,372))>0 else 0
        damage=C.mul(C.mul(amount,C.add(mult,school)),C.ONE)
        if C.rational(damage)<=1:damage=C.ONE
        old=read(row,288);hp=C.sub(old,damage);actual=min(max(C.rational(old),0),C.rational(damage));state['total']=C.bits64(C.f64(state['total'])+float(actual));state['spelltotals'][spell]=C.bits64(C.f64(state['spelltotals'].get(spell,0))+float(actual));put(row,288,hp)
        event=dict(guid=str(read(row,112,8)),amount_bits=amount,damage_bits=damage,critical=critical,dead=C.rational(hp)<=0,rewards=[])
        if C.rational(hp)<=0:
            assert C.rational(read(row,344))==0,'Moving death not runtime covered'
            xyz=current_xyz(row);put(row,0,1);put(row,4,0);put(row,240,0);row[316:328]=struct.pack('<3I',*xyz);row[328:340]=struct.pack('<3I',*xyz);put(row,340,0);put(row,344,0)
            state['kills']=(state['kills']+1)&C.M;state['elites']=(state['elites']+(read(row,424,1)&1))&C.M;state['cost']=C.add(C.u(npc_def,60),state['cost'])
            random,state['words']=uniform24(state['words']);scaled=C.mul(C.rounded(Fraction(C.u(npc_def,56))),0x3fd33333);whole=int(C.rational(scaled));fraction=C.sub(scaled,C.rounded(Fraction(whole)));xp=whole+int(C.rational(fraction)>C.rational(random))
            if xp:
                packet,diagnostic=pickup(0,xp,xyz,world,scalars,speeds,state);packets.append(packet);event['rewards'].append(diagnostic)
            random,state['words']=uniform24(state['words'])
            if C.rational(random)<C.rational(0x3e28f5c3):
                draws=0
                while True:
                    word,state['words']=C.nextword(state['words']);draws+=1;assert draws<10000;product=word*3
                    if(product&C.M)<=0xbfffffff:break
                amount=(product>>32)+2;coinxyz=[C.add(xyz[0],0x3f4ccccd),C.add(xyz[1],0x3f4ccccd),xyz[2]];packet,diagnostic=pickup(1,amount,coinxyz,world,scalars,speeds,state);packets.append(packet);event['rewards'].append(diagnostic)
        hits.append(event)
    result=dict(success=int(bool(ids)),records432_cells=[list(r)for r in rows],rng_words=list(state['words']),accounted_total_bits=str(state['total']),spell_sets=[list(v)for v in state['sets']],owned80_hex=owned.hex(),launch306_packets=[]if not ids else[[306,C.launch(0,spell,ids)]],player_xyz=list(player),phase2587=1,spell_totals64=[[k,str(v)]for k,v in sorted(state['spelltotals'].items())],kills1084=state['kills'],elites1088=state['elites'],counter2408=state['counter'],movement_sequence2412=1,killcost2420_bits=state['cost'],player_hp1440_bits=derived[1536],maximum1536_bits=derived[1536],xp1436=0,pickup_capacity=len(state['pickups']),pickup_count=state['pickup_count'],pickups56_cells=[list(r)for r in state['pickups']],known_packets=packets)
    return result,hits

def main():
    started=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('death139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    assert sha(BATCH/'comparison.json')==COMPARISON and sha(BATCH/'task-handoff.json')==HANDOFF and sha(STATIC/'trace.json')==STATIC_SHA
    for name,digest in HELPERS.items():assert sha(ROOT/'scripts'/name)==digest
    comp=json.loads((BATCH/'comparison.json').read_text());handoff=json.loads((BATCH/'task-handoff.json').read_text());prep=json.loads((BATCH/'prepared.json').read_text());manifest=json.loads((BATCH/'manifest.json').read_text());trace=json.loads((STATIC/'trace.json').read_text());report=json.loads((ROOT/'reports/2026-11-02-death0139.json').read_text())
    sources=comp['source_before'];assert sources==comp['source_after']==prep['source_before']and len(sources)==36
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(BATCH/'source-snapshot'/name)
    for name,digest in handoff['frozen_author_files'].items():assert sha(ROOT/name)==digest
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])and len(edges)==93 and sum(n.startswith('reconstruction/')for n in sources)==26
    for name,digest in comp['artifacts'].items():assert sha(BATCH/name)==digest
    for name,digest in prep['frozen'].items():assert sha(BATCH/name)==digest
    assert prep['expected_before_original']and not prep['original_inputs_contain_expected']and comp['expectation_reads_forbidden']==[]
    config=json.loads((BATCH/'config.json').read_text());gate=ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json'
    assert sha(gate)=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    assert config['snapshot_sha256']=='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'and config['game_pointer']==14685248 and config['app_pointer']==14680072
    assert Path(config['snapshot_path'])==ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory'and Path(config['input_path'])==BATCH/'inputs.json'and config['input_sha256']==sha(BATCH/'inputs.json')
    raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE_SHA;original=parse_module(raw);private=(BATCH/manifest['module_file']).read_bytes();assert hashlib.sha256(private).hexdigest()==manifest['module_sha256'];modified=parse_module(private)
    assert len(original['imports'])==882 and modified['exports']==original['exports']+[('research139_spawn5719',0,5719),('research139_npc_cast922',0,922),('research139_spawn_stack0',3,0)]
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
    functions={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as wat:
        for name,proofs,directory in(('runtimeexportsurface',manifest['functions'],BATCH/'static'),('posthocstatic',trace['functions'],STATIC)):
            for key,proof in proofs.items():
                i=int(key);a,b=original['bodies'][i];assert hashlib.sha256(raw[a:b]).hexdigest()==proof['body_sha256'];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(i,)).fetchone();wat.seek(start);body=wat.read(end-start);assert body==(directory/(key+'.wat')).read_bytes()and hashlib.sha256(body).hexdigest()==proof['WAT_sha256'];functions[key]=proof;texts[i]=body.decode()
    assert len(trace['functions'])==24 and original['types'][original['decl'][913-882]]==('7f7e7d7f7f7f7f','')
    assert all(t in texts[913]for t in('i32.store offset=1084','i32.store offset=1088','f32.store offset=2420','f32.const 0x1.a66666p+0','f32.const 0x1.51eb86p-3','i32.const -1073741825'))
    assert texts[913].index('call 36367')<texts[913].index('i32.store offset=1084')<texts[913].index('f32.store offset=2420')
    assert 'i32.load offset=284'in texts[36367]and'call 20060'in texts[36367]and'i32.store offset=4'in texts[36367]
    tail=texts[913].splitlines()[12789:13071];tail='\n'.join(tail);assert tail.index('i32.load offset=2056')<tail.index('call 994')and'i32.eqz\n                        br_if 0 (;@10;)'in tail
    assert 'local.get 3\n          i32.eqz\n          br_if 2 (;@1;)'in texts[994]
    assert 'local.get 1\n                                                    f32.const 0x0p+0 (;=0;)\n                                                    f32.le\n                                                    i32.eqz'in texts[1466]
    assert 'i32.load offset=600'in texts[18421]and'f32.load offset=80'in texts[18421]
    def data(address,size):
        result=bytearray(size)
        for base,pos,count in original['data_segments']:
            if base is not None:
                lo,hi=max(base,address),min(base+count,address+size)
                if lo<hi:result[lo-address:hi-address]=raw[pos+lo-base:pos+hi-base]
        return bytes(result)
    definition=data(5882740,88);npc_def=data(5830904,72);assert definition.hex()==manifest['definition']['raw88_hex']and npc_def.hex()==manifest['ordinary72_hex']==trace['default_ordinary_definition']['raw72_hex'];assert C.u(npc_def,56)==1 and C.u(npc_def,60)==C.ONE and npc_def[68]==0
    classdata,racedata=data(5877920,108),data(5874636,44);ptr,n=struct.unpack_from('<II',racedata,16);derived,_,_,_=default_stats(struct.unpack_from('<II',classdata,72),list(struct.iter_unpack('<II',data(ptr,n*8))))
    tables=[list(struct.unpack('<4f',data(p,16)))for p in(14426512,14426528,14426544,14426560)];speeds=list(struct.unpack('<6I',data(1593032,24)));spawn_speeds=list(speeds);spawn_speeds[1]=1088421888
    world,nav,scalars=load_world(comp['world_provenance']);cx,cy=scalars['center_xy_bits'];height=world.height(cx,cy);assert type(height)is int;initial_player=[cx,cy,height];seed=1442695040888963407;constructor_words=rng(seed);owned=bytes.fromhex(record(5882740));assert C.u(owned)==5882740 and C.rational(derived[1536])==230
    actor=dict(derived_bits={str(k):v for k,v in derived.items()},owned80_hex=owned.hex(),initial_rng=constructor_words,player_xyz=initial_player,phase2587=0,source_id='0');cases=json.loads((BATCH/'inputs.json').read_text());expected=json.loads((BATCH/'expected.json').read_text());actual=[json.loads(x)for x in(BATCH/'stdout.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==14
    counts=Counter();reference=[];diagnostics=[]
    def compare_rows(rows,actualhex,kind,previous=None):
        assert len(rows)==len(actualhex)
        for j,(row,hx)in enumerate(zip(rows,actualhex,strict=True)):
            observed=bytes.fromhex(hx);assert len(row)==len(observed)==(432 if kind in('producer','NPC')else 56)
            for i,(want,got)in enumerate(zip(row,observed,strict=True)):
                if want is None:
                    counts[kind+'_None']+=1;counts[kind+'_nonzero_None']+=bool(got)
                    if previous is not None and j<len(previous):assert previous[j][i]==got;counts[kind+'_persistent_None']+=1
                else:assert want==got,('record_byte',kind,j,i,want,got);counts[kind+'_known']+=1
    npc_allowed=set(range(1720,1736))|set(range(1784,1796))|set(range(1880,1892))|set(range(2408,2412))
    for c,e,a in zip(cases,expected,actual,strict=True):
        assert c['id']==e['id']==a['id']and c==e['input'];assert c['repeats']==2 and not c['gentle_owned_multiplier']
        state=dict(id=c['id'],rng_words=constructor_words if c['rng_words']is None else c['rng_words'],counter=c['counter'],player_xyz=initial_player,velocity_xy=[0,0],initial_backing=c['initial_backing'],distance_map=None)
        born,position_diags=natural_reference(state,world,nav,scalars,tables,npc_def,spawn_speeds);assert born==e['natural_producer_expected']and actor==e['actor_before']==a['actor_before']and a['constructor_rng_before']==constructor_words and a['constructor_counter_before']==10 and int(a['App4928_after_controlled_seed0_LCG'])==seed
        assert a['preserve_constructor_rng']==(c['rng_words']is None)
        previous_game=bytes.fromhex(a['declared_game_before_hex'])
        for j,(p,got,game)in enumerate(zip(born,a['answers'],a['raw_games2592'],strict=True)):
            compare_rows(p['records432_cells'],got['records432_hex'],'producer');assert{k:v for k,v in p.items()if k!='records432_cells'}=={k:v for k,v in got.items()if k!='records432_hex'}
            pre,post=bytes.fromhex(game['before_hex']),bytes.fromhex(game['after_hex']);assert pre==previous_game and len(pre)==len(post)==2592;changed=[i for i,(v,w)in enumerate(zip(pre,post))if v!=w];assert changed==game['changed_bytes']and set(changed)<=npc_allowed;previous_game=post;counts['NPCproducer_Game_conserved_bytes']+=2592-len(npc_allowed);counts['original5719_returns_checked']+=1
        rows=[list(r)for r in born[-1]['records432_cells']];chosen=rows[0 if c['action']=='near_first'else 1];assert c['action']in('near_first','near_second');player=[read(chosen,o)for o in(316,320,324)]
        state=dict(rows=rows,words=tuple(born[-1]['rng_words']),counter=born[-1]['counter'],total=0,spelltotals={},kills=0,elites=0,cost=0,sets=[[],[],[]],pickups=[],pickup_count=0);priorNPC=[bytes.fromhex(hx)for hx in a['answers'][-1]['records432_hex']];priorPickups=[];all_packets=a['answers'][-1]['packets'];stages=[]
        for stage,(want,got,game)in enumerate(zip(e['expected'],a['cast_stages'],a['cast_raw_games'],strict=True)):
            pre,post=bytes.fromhex(game['before_hex']),bytes.fromhex(game['after_hex']);assert len(pre)==len(post)==2592
            if stage==0:
                action=set(range(1416,1428))|{2587};assert all(x==y for i,(x,y)in enumerate(zip(previous_game,pre))if i not in action);counts['firstcast_inherited_Game_bytes']+=2592-len(action)
            else:assert pre==previous_game;counts['latercast_inherited_Game_bytes']+=2592
            oldwords=tuple(state['words']);oldtotal=state['total'];p,hits=cast_reference(state,player,derived,definition,owned,world,scalars,speeds,npc_def);assert p==want,('stored_expectation',c['id'],stage)
            compare_rows(p['records432_cells'],got['records432_hex'],'NPC',priorNPC);compare_rows(p['pickups56_cells'],got['pickups56_hex'],'pickup',priorPickups);priorNPC=[bytes.fromhex(hx)for hx in got['records432_hex']];priorPickups=[bytes.fromhex(hx)for hx in got['pickups56_hex']]
            excluded=('records432_cells','records432_hex','pickups56_cells','pickups56_hex','known_packets','new_packets');assert{k:v for k,v in p.items()if k not in excluded}=={k:v for k,v in got.items()if k not in excluded}
            assert game['all_packets'][:len(all_packets)]==all_packets and got['new_packets']==game['all_packets'][len(all_packets):];all_packets=game['all_packets'];cursor=0
            for packet in p['known_packets']:
                j=next(i for i in range(cursor,len(got['new_packets']))if got['new_packets'][i]==packet);cursor=j+1;counts['ordered_known_packets']+=1;counts['known_packet_bytes']+=len(packet[1])//2;counts['packet_'+str(packet[0])]+=1
                if packet[0]==306:assert C.decode306(packet[1])['targets']==[int(h['guid'])for h in hits]
            for o in(176,600,648,1972,1984,2032,2044,2056):assert C.u(pre,o)==C.u(post,o)==0;counts['empty_source_word_occurrences']+=2
            assert pre[770]==post[770]==0 and pre[908]&1==post[908]&1==0 and C.u(pre,1664)==C.u(post,1664)==1 and pre[360]==post[360]==1
            assert C.u(pre,1440)==C.u(pre,1536)==C.u(post,1440)==C.u(post,1536)==derived[1536];assert C.q(pre,984)==oldtotal and[C.u(pre,1720+4*j)for j in range(4)]==list(oldwords)
            for key,offset in(('kills1084',1084),('elites1088',1088),('counter2408',2408),('movement_sequence2412',2412),('killcost2420_bits',2420),('player_hp1440_bits',1440),('maximum1536_bits',1536),('xp1436',1436),('pickup_capacity',1868),('pickup_count',1876)):assert C.u(post,offset)==p[key];counts['declared_post_Game_words']+=1
            assert C.q(post,984)==state['total']and[C.u(post,1720+4*j)for j in range(4)]==list(state['words'])and post[2587]==1 and C.u(pre,1788)==C.u(post,1788)and C.u(pre,1792)==C.u(post,1792)==4
            assert [C.u(post,o)for o in(672,684,732)]==[len(v)for v in state['sets']];assert C.u(post,1132)==len(state['spelltotals'])and C.u(post,1128)==0 and C.u(post,1124)>0
            previous_game=post;counts['original922_returns_checked']+=1
            for hit in hits:
                counts['selected_hits_reference_only']+=1;counts['deaths']+=hit['dead'];counts['criticals']+=hit['critical']
                for reward in hit['rewards']:counts['XP_events'if reward['kind']==0 else'coin_events']+=1
            stages.append(p);diagnostics.append(dict(id=c['id'],stage=stage,hits=hits,position_reference_only=position_diags if stage==0 else None))
        assert a['option16_hex']=='00000000'+'a5'*12 and a['option_canaries']==a['result_canaries']==['c3'*16,'d7'*16]and a['world124_before_hex']==a['world124_after_hex']and a['world_data_digest_before']==a['world_data_digest_after']and a['path_view']is None and a['stack_after']==1048576
        reference.append(dict(id=c['id'],actor_before=actor,natural_producer_expected=born,stages=stages))
    assert (counts['NPC_known'],counts['NPC_None'],counts['NPC_nonzero_None'])==(35056,13328,5892)and(counts['pickup_known'],counts['pickup_None'],counts['pickup_nonzero_None'])==(1820,2436,2343)
    assert (counts['ordered_known_packets'],counts['known_packet_bytes'],counts['packet_306'],counts['packet_169'])==(53,4190,27,26)and(counts['deaths'],counts['XP_events'],counts['coin_events'])==(18,18,8)
    runtime=json.loads((BATCH/'runtime.json').read_text());terminal=json.loads((BATCH/'process-terminal.json').read_text());assert runtime==comp['runtime']and terminal==comp['process'];assert runtime['full5719_calls']==56 and runtime['full922_calls']==28 and runtime['snapshot_restores']==14 and runtime['denied_imports']==882 and runtime['actual_host_calls']==0 and runtime['stack_checks']==runtime['allocator_calls']+84==113 and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']
    assert all(sha(ROOT/n)==v for n,v in sources.items())and all(sha(ROOT/n)==v for n,v in handoff['frozen_author_files'].items())
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    save(out/'independent-reference.json',reference);save(out/'diagnostics.json',diagnostics)
    receipt=dict(status='pass_with_declared_sameGame_default_ordinary_death_limits',reviewer='/root/motion38_review',author='/root/stats138_review',comparison_sha256=COMPARISON,author_handoff_sha256=HANDOFF,review_script_sha256=sha(__file__),formal_cases=14,new_original_calls=0,author_model_checker_builder_executions=0,independent_reference_uses_opaque_completion=False,author_files_untouched=True,source_count=36,production_count=26,source_edges=93,sources=sources,author_files=handoff['frozen_author_files'],helpers=HELPERS,current_functions=functions,posthoc_static_sha256=STATIC_SHA,healthy_v2_review_gate_sha256=sha(gate),counts=dict(counts),read_ranges=[dict(offset=o,width=w,count=n)for(o,w),n in sorted(READS.items())],reference_sha256=sha(out/'independent-reference.json'),diagnostics_sha256=sha(out/'diagnostics.json'),runtime=runtime,author_process=terminal,seconds=time.monotonic()-started,artifacts_as_read={p.name:sha(p)for p in BATCH.iterdir()if p.is_file()and p.suffix!='.wasm'},limitations=['14healthyv2phase0snapshotconsumerfixtures;notfreshApp/constructor/full1108/game,rootopening16isaseparatebatch.','Playerphase1/relocation/emptyitem,timed,adjustment/onkill/procsourcesareexplicitcontrolledinputcontracts;notfullnaturalproduceracceptance.','Current139432classification424andextra416/420areboundtoactualbodies/data.No135passedcaseistransferred.','64-bitdamage/spelltotalandlogicalsetsarechecked;physicalBTree/allocator/queueownersnotindependentlyreconstructed.','Known306andXPcoin169areonlyanorderedsubsequence;592andordinaryHP/death169remainobserved.','Movingfreeze/221andpositivehealing1466arenotdynamicallyexercised;fullHP230implieszerohealingand2056zeroisatrue913skip994.','NPC/pickupNonebytesremainunknown;manyactualnonzero.Unknownsfromearlierbackingareconserved,notcompleted.','36experimentalpre-runsourcesarestable;24functionproof/staticandpostcapturereadbackwerelaterbound,andarenotretroactivelypre-runprovenance.','Originalrunner113stackchecksareaggregateguardobservations;internal913/rewardcallsarenotdirectlyinstrumented.Modelhit/deatheventcountsarenotadditionaloriginalcalls.','36367resolveslocalizedNPCdisplayname(ptr,len);itdoesnotremoveNPCrecords.Locale592stringsarenotclaimedasindependentlymatched.'])
    save(out/'review.json',receipt);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=receipt['seconds'])),flush=True)
if __name__=='__main__':main()
