#!/usr/bin/env python3
"""Different-author current139 full925 reference; never runs author/original."""
from pathlib import Path
from collections import Counter,deque
from fractions import Fraction
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_cast139 as C
import review_opening139 as O
import review_growth139 as G
import review_growth_world139 as W
import review_world_position139 as P
import review_incoming139 as I
from review_combat139 import sha,parse_module,local_closure,fp,bits

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/enemy-ai139-oracle-20261102T105256.293681Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMP='dac8878e298546011ec6ddf35738f078ae8dbafd0f00689c4de4c5a7fef186bc'
HAND='e2144c801b6cef68283a76ead068b4312c2ad0823be4ba5cd8e86f7c53fca720'
SUPPLEMENT='14b44b5670174fc69fa8c4c8b969170528ba77405f368871a27927aa027dfec5'
HELPERS={**W.HELPERS,
 'scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b',
 'scripts/review_incoming139.py':'adaa5e21f2e491fe3eee18a8ec57c9d8b249481c6edc52a29408ad194dece07b'}
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,p=0:struct.unpack_from('<I',b,p)[0]


def word(row,p,n=4):
    cells=row[p:p+n];assert len(cells)==n and None not in cells,('Consumed unknown',p,n)
    return int.from_bytes(bytes(cells),'little')


def put(row,p,value):row[p:p+4]=struct.pack('<I',value)
def lt(a,b):return C.rational(a)<C.rational(b)
def le(a,b):return C.rational(a)<=C.rational(b)
def minimum(a,b):return a if lt(a,b)else b
def maximum(a,b):return b if lt(a,b)else a


def sqrt32(value):
    assert C.rational(value)>=0
    if not C.rational(value):return value
    hint=bits(math.sqrt(fp(value)));v=C.rational(value)
    # Correct the hardware-f64 hint against exact squared f32 midpoints.
    while v<((C.rational(hint-1)+C.rational(hint))/2)**2:hint-=1
    while v>((C.rational(hint)+C.rational(hint+1))/2)**2:hint+=1
    for other in(hint-1,hint+1):
        if v==((C.rational(other)+C.rational(hint))/2)**2 and hint&1:hint=other
    return hint


def distance(a,b):return sqrt32(C.distance(a,b))


def trig(angle):
    absolute=angle&0x7fffffff;x=fp(angle)
    if absolute<=0x40c90fdb:
        sine,cosine=P.trig(x);return bits(sine),bits(cosine)
    if absolute<1088565718:
        y=abs(x)-P.TAU;return bits(P.sin_kernel(y))^(angle&0x80000000),bits(P.cos_kernel(y))
    assert absolute<=1305022426,'Large Payne-Hanek reduction remains outside reference'
    H=float.fromhex;n=((x*H('0x1.45f306dc9c883p-1'))+H('0x1.8p52'))+H('-0x1.8p52')
    y=(x+n*H('-0x1.921fb5p0'))+n*H('-0x1.110b4611a6263p-26');s,c=bits(P.sin_kernel(y)),bits(P.cos_kernel(y))
    return((s,c),(c,s^0x80000000),(s^0x80000000,c^0x80000000),(c^0x80000000,s))[int(n)&3]


def probe(nav,xy):
    p=[C.sub(a,b)for a,b in zip(xy,nav['origin_xy_bits'])]
    if any(lt(x,0)for x in p):return None,None
    x,y=(int(C.rational(v))for v in p);width=nav['width']
    if x>=width or y>=width:return None,None
    index=x+y*width;return nav['bytes'][index],index


def breadth_first(nav,player,neighbors):
    _,seed=probe(nav,player[:2]);assert seed is not None
    width=nav['width'];values=[65535]*len(nav['bytes']);values[seed]=0;pending=deque([seed]);visited=1
    while pending:
        index=pending.popleft();y,x=divmod(index,width)
        for dx,dy in neighbors:
            xx,yy=x+dx,y+dy
            if not(0<=xx<width and 0<=yy<width):continue
            target=xx+yy*width
            if nav['bytes'][target]or values[target]!=65535:continue
            if dx and dy and(nav['bytes'][xx+y*width]or nav['bytes'][x+yy*width]):continue
            values[target]=values[index]+1;visited+=1;pending.append(target)
    raw=struct.pack('<'+'H'*len(values),*values)
    return dict(capacity=len(values),count=len(values),start_index=seed,field24=visited,u16le_sha256=hashlib.sha256(raw).hexdigest()),values


def segment(nav,start,end,counts):
    length=distance(start,end)
    if lt(length,0x3a83126f):return C.ONE
    n=math.ceil(C.rational(C.div(length,0x3e99999a)));assert 0<n<1000
    prior,_=probe(nav,start);prior=0 if prior is None else prior;last=0
    for j in range(1,n+1):
        ratio=C.div(C.rounded(Fraction(j)),C.rounded(Fraction(n)))
        xy=[C.add(a,C.mul(C.sub(b,a),ratio))for a,b in zip(start[:2],end[:2])]
        cell,_=probe(nav,xy);cell=0 if cell is None else cell;counts['segment_nav_probes']+=1
        if (prior|~cell)&1==0:return last
        if j>=n:return C.ONE
        prior&=cell;last=ratio
    raise AssertionError('Segment loop did not return')


def position(row,now):
    duration=word(row,344)
    if le(duration,0):return tuple(word(row,p)for p in(328,332,336))
    ratio=minimum(C.ONE,maximum(0,C.div(C.sub(now,word(row,340)),duration)))
    return tuple(C.add(word(row,a),C.mul(C.sub(word(row,b),word(row,a)),ratio))for a,b in((316,328),(320,332),(324,336)))


def packet221(world,target,start,end,duration,sequence,counts):
    prefix=C.packguid(target)+struct.pack('<4I',*start,sequence)
    if le(duration,0):
        counts['stop_kind3_packets']+=1
        return[221,(prefix+b'\3'+struct.pack('<Q6I',0,256,1,1,*start)).hex()]
    def project(xyz):
        height=world.height(*xyz[:2]);counts['packet_height_queries']+=1
        return(*xyz[:2],xyz[2]if height is None else height)
    milliseconds=max(1,min(0xffffffff,int(C.rational(C.mul(duration,0x447a0000)))))
    return[221,(C.packguid(target)+struct.pack('<4I',*project(start),sequence)+bytes(1)+struct.pack('<3I',256,milliseconds,1)+struct.pack('<3I',*project(end))).hex()]


def tick(state,dt,world,nav,neighbors,names,english,counts):
    state=copy.deepcopy(state);now=C.add(state['now'],dt);state['now']=now;player=state['player']
    if state['path']is None:
        state['path'],values=breadth_first(nav,player,neighbors);state['path_values']=values;state['path_clock']=now;recomputed=True;counts['path_rebuilds']+=1;counts['BFS_values']+=len(values)
    else:
        assert probe(nav,player[:2])[1]==state['path']['start_index'];recomputed=False
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
        assert all(state['guards'][p]==0 for p in state['guards'])and C.rational(state['hp'])>C.rational(damage)
        state['hp']=C.sub(state['hp'],damage);state['last']=now;state['incoming']+=fp(damage);state['category']+=fp(damage);state['has_category']=True
        source=next(row for row in state['rows']if word(row,112,8)==target);assert word(source,284)in names and source[424]==0
        I.append_ring(state['history'],now,fp(damage),0.,fp(state['hp']),state['derived']['1536'],(names[word(source,284)],english['Melee'],'INV_Sword_04'),0,0)
        state['fields'].update({'22':math.ceil(fp(state['hp'])),'28':math.ceil(fp(state['derived']['1536']))});counts['contacts']+=1
    state['packets'].extend(packets)
    answer=dict(frame=state['frame'],records=copy.deepcopy(state['rows']),hp1440_bits=state['hp'],last_hit1652_bits=state['last'],incoming992_hex=struct.pack('>d',state['incoming']).hex(),categories={'mob melee':struct.pack('>d',state['category']).hex()}if state['has_category']else{},fields=copy.deepcopy(state['fields']),history=I.ring_projection(state['history']),path=copy.deepcopy(state['path']),path_clock2372_bits=state['path_clock'],movement_sequence2412=state['sequence'],packets=copy.deepcopy(state['packets']),attacks=attacks,routing=routing,path_recomputed=recomputed)
    state['frame']+=1;counts['frames']+=1;counts['movement221']+=len(motions);return state,answer


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(SOURCE)==WASM and sha(BATCH/'comparison.json')==COMP and sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'postcapture-static-supplement.json')==SUPPLEMENT
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');manifest=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');trace=load(BATCH/'static/trace.json')
    for name,h in HELPERS.items():assert sha(ROOT/name)==h,name
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==72 and sum(n.startswith('reconstruction/')for n in sources)==59
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h,name
    assert len(hand['frozen_author_files'])==7
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for table in(comp['frozen'],comp['artifacts'],prep['frozen']):
        for name,h in table.items():assert sha(BATCH/name)==h,name
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==237
    for name in sources:
        if not name.startswith('reconstruction/'):continue
        for node in ast.walk(ast.parse((ROOT/name).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;label=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                assert label not in('open','read_bytes','read_text','write_bytes','write_text','Popen','system','eval','exec','__import__'),(name,label)
    assert comp['differences']==0 and comp['phase']=='full'and comp['cases']==comp['completed_cases']==3 and prep['expected_before_original']and not prep['original_input_contains_expected']and prep['all_background_owners_retained']
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
    additions=[('research139_ai_companion',0,2945),('research139_ai_initial',0,1600),('research139_ai_opening',0,1108),('research139_ai_tick',0,925),('research139_ai_stack',3,0)]
    assert private['exports']==original['exports']+additions and [(v['module'],v['name'])for v in original['imports']]==[(v['module'],v['name'])for v in manifest['original_imports']]
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
    neighbors=list(struct.iter_unpack('<ii',data(5408444,64)));assert neighbors==[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]and neighbors==list(map(tuple,trace['neighbors']))
    english=json.loads(data(*struct.unpack('<II',data(5401532,8))));p,n,identifier=struct.unpack('<III',data(5830920,12));names={5830904:english.get('enemy.'+str(identifier),text(p,n))};assert names=={int(k):v for k,v in trace['english_names'].items()}and names[5830904]=='Kobold Vermin'
    functions={};texts={};claims=manifest['functions']|manifest['setup_functions'];extra={8740,13563,1886,1446,24602,6786,33028,30628,25511,26364,25613}
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx in sorted(set(map(int,claims))|extra):
            a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();stream.seek(start);value=stream.read(end-start);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(value).hexdigest());functions[str(idx)]=proof;texts[idx]=value.decode();(out/f'{idx}.wat').write_bytes(value)
            if str(idx)in claims:assert all(proof[k]==claims[str(idx)][k]for k in proof)and value==(BATCH/'static'/f'{idx}.wat').read_bytes()
    for key,proof in trace['data_proof'].items():
        address,size=map(int,key.split(':'));assert hashlib.sha256(data(address,size)).hexdigest()==proof['sha256']
    assert original['types'][original['decl'][925-882]]==('7f7d','')and original['types'][original['decl'][1076-882]]==('7f7d7e7f7f7f','')
    assert 'i32.store offset=2368'in texts[925]and'i32.store16'in texts[925]and'i32.const 5408444'in texts[925]and'i32.const 65535'in texts[925]and'call 30179'in texts[925]and'call 29237'in texts[925]and'call 1076'in texts[925]
    assert all(s in texts[1076]for s in['f32.store offset=1440','f32.store offset=1652','i32.const 48','i32.store offset=28'])
    cases=load(BATCH/'inputs.json');expected=load(BATCH/'expected.json');actual=[json.loads(x)for x in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==3 and [(c['app_seed_u64'],c['dt_bits'],c['frames'])for c in cases]==[('0',0x3f000000,32),('1',0x3e800000,48),('42',0x3f800000,12)]
    counts=Counter();reference=[]
    def cells(label,want,hx):
        got=bytes.fromhex(hx);assert len(want)==len(got)
        for j,(v,w)in enumerate(zip(want,got)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(w)
            else:assert v==w,(label,j,v,w);counts[label+'_known']+=1
    allowed=set()
    for start,size in((968,16),(992,8),(1112,12),(1440,4),(1652,4),(1880,12),(2352,4),(2368,8),(2412,4),(2476,12)):allowed.update(range(start,start+size))
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case['id']==e['id']==a['id'];op,_=O.reference(dict(id=case['id'],app_seed_u64=case['app_seed_u64']),world,nav,scalars,heading,normal,speeds,classes,races,zones,eligible,minutes);opening=op['projection'];assert opening==e['expected']['opening']
        initial,_=G.reference(dict(id=case['id'],seed_u64=op['constructor_seed_u64'],amount=0,select_index=None),classes,races,zones,kit,definitions,cooldown,damage);growth=initial['before'];growth['rng_words']=opening['rng_words']
        assert a['new_Game_pointer']!=a['old_snapshot_Game_not_target']==14685248 and a['constructor_seed_u64']==op['constructor_seed_u64']and a['stack_after']==1048576
        assert a['account368_before_hex']==a['account368_after_hex']and a['profile376_before_hex']==a['profile376_after_hex']and a['selection_canaries']==['c3'*16,'d7'*16]and a['before']==a['opening']
        assert a['opening']['packets']==opening['packets'];cells('openingGame',op['known_Game2592'],a['opening']['raw_game2592_hex']);counts['opening_packets']+=len(opening['packets'])
        for k,v in growth.items():
            if k=='player_fields':assert all(a['before']['projection'][k][x]==y for x,y in v.items())
            else:assert a['before']['projection'][k]==v
        for name in['units','pickups','windows','special','boundaries']:
            vector=a['opening']['background'][name];assert vector['capacity']==opening[name]['capacity']and vector['count']==opening[name]['count']
            for row,hx in zip(opening[name]['storage'],vector['storage'],strict=True):cells('opening_'+name,row,hx)
        game=bytes.fromhex(a['before']['raw_game2592_hex']);assert u(game,2368)==u(game,1712)==u(game,2056)==u(game,552)==u(game,1676)==0 and game[2582]==game[2576]==game[2578]==0 and game[2587]==1
        state=dict(rows=copy.deepcopy(opening['units']['storage']),now=0,frame=0,player=opening['player_xyz'],path=None,path_values=None,path_clock=0,sequence=u(game,2412),hp=growth['current_hp_bits'],last=0xc1200000,incoming=0.,category=0.,has_category=False,derived=growth['derived_bits'],guards={p:u(game,p)for p in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(growth['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=copy.deepcopy(opening['packets']))
        assert u(game,968)==u(game,980)==u(game,992)==u(game,996)==u(game,1112)==u(game,1120)==0 and u(game,1652)==state['last']and state['sequence']==1
        previous=a['before'];frames=[];assert len(a['frames'])==len(e['expected']['frames'])==case['frames']
        for j,(wanted,observed)in enumerate(zip(e['expected']['frames'],a['frames'],strict=True)):
            state,answer=tick(state,case['dt_bits'],world,nav,neighbors,names,english,counts);assert answer==wanted,('independent_reference',case['id'],j);frames.append(answer)
            v=observed['view'];ai=observed['ai'];g=v['projection'];rawgame=bytes.fromhex(v['raw_game2592_hex']);assert observed['frame']==j
            assert answer['hp1440_bits']==g['current_hp_bits']and answer['fields']==g['player_fields']and G.tree_fields(v,rawgame)==g['player_fields'];counts['full_tree_captures']+=1
            for key in['path','path_clock2372_bits','incoming992_hex','last_hit1652_bits','categories']:assert answer[key]==ai[key],(case['id'],j,key)
            assert answer['movement_sequence2412']==v['background']['movement_sequence2412']==u(rawgame,2412)and answer['packets']==v['packets']
            assert answer['history']['header']==ai['history']['header']and answer['history']['active']==ai['history']['active']
            for row,hx in zip(answer['records'],v['background']['units']['storage'],strict=True):cells('NPC',row,hx)
            for row,hx in zip(answer['history']['storage'],ai['history']['storage'],strict=True):cells('history',row,hx)
            for key in['pickups','special','windows','boundaries','auxiliary','claims','counter2408']:assert v['background'][key]==a['before']['background'][key]
            counts['background_other_conserved_bytes']+=sum(len(bytes.fromhex(hx))for key in['pickups','special','windows','boundaries']for hx in v['background'][key]['storage'])
            for key in growth:
                if key not in('current_hp_bits','player_fields'):assert g[key]==a['before']['projection'][key]
            assert v['live32_hex']==[]and u(rawgame,1712)==0 and u(rawgame,1792)==u(rawgame,1784)==4 and u(rawgame,1788)==u(game,1788)and u(rawgame,2352)==state['now']and u(rawgame,1440)==state['hp']and u(rawgame,1652)==state['last']
            assert struct.unpack_from('<Q',rawgame,992)[0]==int(answer['incoming992_hex'],16)and [u(rawgame,p)for p in(968,976,980)]==list(answer['history']['header'].values())
            assert bool(u(rawgame,2368))and u(rawgame,2372)==state['path_clock']and u(rawgame,2348)==20544696 and all(u(rawgame,p)==0 for p in state['guards'])
            oldgame=bytes.fromhex(previous['raw_game2592_hex']);assert all(x==y for k,(x,y)in enumerate(zip(oldgame,rawgame))if k not in allowed);counts['Game_nonowned_conserved_bytes']+=2592-len(allowed)
            for oldhx,newhx,row in zip(previous['background']['units']['storage'],v['background']['units']['storage'],answer['records'],strict=True):
                physical=bytearray.fromhex(oldhx)
                for k,x in enumerate(row):
                    if x is not None:physical[k]=x
                assert physical.hex()==newhx;counts['NPC_full_physical_replay_bytes']+=432
            previous=v
        reference.append(dict(id=case['id'],opening=opening,frames=frames))
    assert counts['frames']==92 and counts['contacts']==52 and counts['movement221']==83 and counts['path_rebuilds']==3 and counts['BFS_values']==235200 and counts['NPC_full_physical_replay_bytes']==158976
    assert(counts['NPC_known'],counts['NPC_None'],counts['NPC_nonzero_None'])==(111504,47472,43700)and(counts['history_known'],counts['history_None'],counts['history_nonzero_None'])==(18972,15396,12770)
    runtime=load(BATCH/'runtime.json');terminal=load(BATCH/'owned-terminal.json');assert runtime==comp['runtime']and terminal==comp['process']and terminal==hand['original_process_terminal']
    assert runtime['fresh_instances']==3 and runtime['full_calls']=={'2945':3,'1600':3,'1108':3,'925':92}and runtime['allocator_calls']==15 and runtime['stack_checks']==116 and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['peak_memory_bytes']==177078272 and runtime['error']is None
    assert len(runtime['world_source_checks'])==98 and all(v['unchanged']and v['ranges']==2318 for v in runtime['world_source_checks'])and len(runtime['target_and_setup_returns'])==101 and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['target_and_setup_returns'])
    assert not any(runtime[k]for k in['old_Game_used_as_target','readiness_flags_injected','explicit_dead_marker_fixtures','NPC_positions_written_by_driver','App_or_world_Rc_producer_executed','externref_restored','native_executions','full_mainloop_frames','complete_games'])and runtime['full925_body_unchanged']and runtime['full1076_internal_calls_notinstrumented']
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<120
    audit=load(BATCH/'expectation-read-audit.json');assert audit['forbidden']==[]and all(not Path(p).suffix.lower()in('.wasm','.wat','.memory','.exe')and'/originals/'not in p for p in audit['opened'])
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    save(out/'independent-reference.json',reference)
    result=dict(status='pass_current139_full925_natural_fourNPC_movement_nonfatal_contact_path_history',reviewer='/root/collection139_finish',author='/root/growth139_world',version='0.139.0',build='f79c5e2b4',reviewer_script_sha256=sha(Path(__file__)),author_handoff_sha256=HAND,comparison_sha256=COMP,author_files=hand['frozen_author_files'],helper_sha256=HELPERS,counts=dict(counts),cases=3,full925_calls=92,full1108_calls=3,setup2945_calls=3,setup1600_calls=3,source_files=72,production_sources=59,source_edges=237,current_function_bindings=functions,all_nonexport_sections_identical=True,source_labels=names,reference_sha256=sha(out/'independent-reference.json'),author_process=terminal,runtime=runtime,reviewer_original_executions=0,reviewer_author_model_checker_builder_executions=0,author_files_modified=False,seconds=time.monotonic()-started,limitations=['Only current139 full925 standalone schedule: no2123/1466/884 integration, movement input, spawning-after-opening, native or complete game.','Initial four actual NPC positions/full1108 and background retained; explicit velocity0/pathNone constructor setup, path genuinely built by first925 and retained.','Three full78400 nonuniform BFS maps matched; every reached motion direct_clear independently ray sampled. Blocked-flow139 remains Pending; no old135 runtime acceptance reused.','Nonfatal default ordinary melee, no status/guardian/boss/ranged/pet/item/modifier/shield callbacks; no positive regen scheduled and actual HP declines.','All432B physical NPC storage replayed from actual previous owners, known updates independently calculated; unconsumed None preserved and never zero-filled.','History known semantics/padding/resource strings and physical deque layout matched; heap/resource pointers and allocator-unwritten bytes remain None.','Full captured925 packet stream matched inthisscope; complete UI/network/save/bootstrap/externref/fullgame not claimed.','Driver does not capture a separate pre925 view per frame; unchanged Game domains compared across outputs and sole2352 clock writes statically bound to frozen driver.','Canonical world comes from earlier independently raw-produced resource artifacts; healthyv2 snapshot resource context is not natural App/worldRc bootstrapping.'])
    save(out/'review.json',result);print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
