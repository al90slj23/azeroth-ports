#!/usr/bin/env python3
"""Independent13926364/35988/25613 reference, awaiting author freeze.

No author production/checker or original executes. Only current original WAT,
independent Fraction arithmetic and canonical-world query helpers are used.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
    if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith('core_spec'):
        AUDIT['forbidden_author_or_original_execution']+=1;raise RuntimeError('Read-only reviewer refuses '+event)
sys.addaudithook(audit)
import review_cast139 as C
import review_opening139 as O
import review_enemy_ai139 as E
from review_initial139 import reference as constructor_reference
from review_world_position139 import load_world
from review_combat139 import parse_module,local_closure,sha,fp,bits

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'evidence/world-pause139-static-20261102T140707.021418Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
NAN=0x7fc00000
INF=0x7f800000
SIGN=0x80000000


def nan(b):return b&0x7fffffff>INF
def infinite(b):return b&0x7fffffff==INF
def zero(b):return b&0x7fffffff==0
def finite(b):return b&0x7fffffff<INF
def lt(a,b):return not(nan(a)or nan(b))and fp(a)<fp(b)
def le(a,b):return not(nan(a)or nan(b))and fp(a)<=fp(b)


def rounded32(v,negative_zero=False):
    if not v:return SIGN if negative_zero else 0
    sign=SIGN if v<0 else 0;n,d=abs(v).numerator,abs(v).denominator;e=n.bit_length()-d.bit_length()
    if e>=0:
        if n<d<<e:e-=1
    elif n<<-e<d:e-=1
    if e< -126:return sign|C.even_div(n<<149,d)
    shift=23-e;s=C.even_div(n<<shift,d)if shift>=0 else C.even_div(n,d<<-shift)
    if s==1<<24:s>>=1;e+=1
    if e>127:return sign|INF
    return sign|((e+127)<<23)|(s&0x7fffff)


def add(a,b):
    if nan(a)or nan(b):return NAN
    if infinite(a)and infinite(b):return NAN if(a^b)&SIGN else a
    if infinite(a):return a
    if infinite(b):return b
    return rounded32(C.rational(a)+C.rational(b),a==b==SIGN)
def sub(a,b):return add(a,b^SIGN)
def mul(a,b):
    sign=(a^b)&SIGN
    if nan(a)or nan(b)or infinite(a)and zero(b)or infinite(b)and zero(a):return NAN
    if infinite(a)or infinite(b):return sign|INF
    return rounded32(C.rational(a)*C.rational(b),bool(sign))
def div(a,b):
    sign=(a^b)&SIGN
    if nan(a)or nan(b)or infinite(a)and infinite(b)or zero(a)and zero(b):return NAN
    if infinite(a)or zero(b):return sign|INF
    if infinite(b):return sign
    return rounded32(C.rational(a)/C.rational(b),bool(sign))


def read(row,off,width=4):
    part=row[off:off+width]
    if len(part)!=width or None in part:raise NotImplementedError('Actually consumed unknown source cell')
    return int.from_bytes(bytes(part),'little')


def vector_rows(vector,stride):
    rows=[tuple(bytes.fromhex(row))if isinstance(row,str)else tuple(row)for row in vector['storage']]
    assert 0<=vector['count']<=len(rows)<=512 and all(len(row)==stride for row in rows)
    return rows[:vector['count']]


def reserve(capacity,length,additional,element_size):
    needed=length+additional
    if needed<=capacity:return capacity
    minimum=8 if element_size==1 else 4 if element_size<1025 else 1
    return max(2*capacity,needed,minimum)


def family_capacity(count):
    #Filtered iterator's first produced40B element allocates4slots. Each
    #family is materialized separately before appended to the output vector.
    capacity=0
    for length in range(count):capacity=reserve(capacity,length,1,40)
    return capacity


def gather_reference(vectors,now_bits):
    records=[];events=[];capacity=0;family_counts={}
    for name,stride,src,dst,start,duration,guid in[('units',432,316,328,340,344,112),('auxiliary',112,32,44,56,60,16),('claims',88,44,56,68,72,24)]:
        family=[]
        for index,row in enumerate(vector_rows(vectors[name],stride)):
            if name=='units'and read(row,0)!=0:continue
            life=read(row,duration)
            if not lt(0,life):continue
            began=read(row,start);end=add(life,began)
            eligible=(not le(end,now_bits))if name=='claims'else lt(now_bits,end)
            if not eligible:continue
            ratio=div(sub(now_bits,began),life)
            if lt(ratio,0):ratio=0
            if lt(C.ONE,ratio):ratio=C.ONE
            origin=[read(row,src+4*j)for j in range(3)];destination=[read(row,dst+4*j)for j in range(3)]
            xyz=[add(a,mul(sub(b,a),ratio))for a,b in zip(origin,destination,strict=True)];remaining=sub(end,now_bits);identifier=read(row,guid,8)
            payload=struct.pack('<Q7I',identifier,*xyz,*destination,remaining)
            cells=list(payload)+[None]*4;assert len(cells)==40
            family.append(cells);events.append(dict(family=name,index=index,guid=str(identifier),current_xyz_bits=xyz,destination_xyz_bits=destination,remaining_bits=remaining,ratio_bits=ratio))
        family_counts[name]=len(family)
        if name=='units':capacity=family_capacity(len(family))
        else:capacity=reserve(capacity,len(records),len(family),40)
        records.extend(family)
    return dict(capacity=capacity,count=len(records),storage=records+[[None]*40 for _ in range(capacity-len(records))],events=events,family_counts=family_counts)


def project(world,xyz,*,primary_present=False):
    if any(not finite(b)for b in xyz[:2]):raise NotImplementedError('Nonfinite XY terrain query source not restored')
    height=world.height(*xyz[:2])
    if height is not None:return[*xyz[:2],height]
    if primary_present:raise NotImplementedError('Nearestprimary projection not dynamically admitted')
    return list(xyz)


def truncsat(word):
    if nan(word)or le(word,0):return 0
    if infinite(word)or fp(word)>=0xffffffff:return 0xffffffff
    return int(C.rational(word))


def emit_reference(vectors,now_bits,sequence,packet_capacity,packet_count,world,*,resume,primary_present=False):
    gathered=gather_reference(vectors,now_bits);packets=[];observations=[]
    for event in gathered['events']:
        sequence=(sequence+1)&0xffffffff;start=project(world,event['current_xyz_bits'],primary_present=primary_present);identifier=int(event['guid']);prefix=C.packguid(identifier)+struct.pack('<4I',*start,sequence)
        if resume:
            end=project(world,event['destination_xyz_bits'],primary_present=primary_present);milliseconds=max(1,truncsat(mul(event['remaining_bits'],0x447a0000)))
            raw=prefix+b'\0'+struct.pack('<3I3I',256,milliseconds,1,*end);payload_capacity=64
        else:raw=prefix+b'\1';payload_capacity=32;milliseconds=None
        packets.append([221,payload_capacity,raw.hex()]);packet_capacity=reserve(packet_capacity,packet_count,1,16);packet_count+=1
        observations.append(dict(guid=event['guid'],sequence=sequence,projected_current=start,milliseconds=milliseconds))
    return dict(sequence=sequence,packet_capacity=packet_capacity,packet_count=packet_count,packets=packets,gathered=gathered,observations=observations)


def bind_static(out):
    """Read-only primary binding; no author model/checker/expected imports."""
    out=Path(out);out.mkdir();assert sha(SOURCE)==WASM;raw=SOURCE.read_bytes();original=parse_module(raw)
    claims=json.loads((STATIC/'proofs.json').read_text())|json.loads((STATIC/'extra-proofs.json').read_text());ids=set(map(int,claims))|{15962,46462,68886,57285};bindings={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as s:
        for idx in sorted(ids):
            a,z=original['bodies'][idx];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();s.seek(lo);wat=s.read(hi-lo);record=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());bindings[str(idx)]=record;texts[idx]=wat.decode()
            if str(idx)in claims:assert record['body_sha256']==claims[str(idx)]['body_sha256']and record['WAT_sha256']==claims[str(idx)]['WAT_sha256']and wat==(STATIC/f'{idx}.wat').read_bytes()
            (out/f'{idx}.wat').write_bytes(wat)
    assert original['types'][original['decl'][26364-882]]==('7f7f','')and original['types'][original['decl'][35988-882]]==original['types'][original['decl'][25613-882]]==('7f','')
    result=dict(version='0.139.0',source_sha256=WASM,reviewer_source_sha256=sha(Path(__file__)),bindings=bindings,independent_math='Fraction/RNEf32;NaNpayloadnotpromised',record40=dict(GUID=0,currentXYZ=8,destinationXYZ=20,remaining=32,unknownTail=[36,40]),family_order=['units','auxiliary','claims'],NPC_predicate='marker0 && duration>0 && f32(start+duration)>now',aux_predicate='duration>0 && f32(start+duration)>now',comp_predicate='duration>0 && !(f32(start+duration)<=now)',capacity_rule='firstfamilyfilteredVec cap4/double; outputmerge reserve max(2cap,length+incoming,4)',source_records_written=False,stop='projectcurrent;seq++;221packedGUID+XYZ+seq+kind1;payloadcap32',resume='projectcurrent+destination;seq++;221kind0/256/max(1,truncsat(f32(remaining*1000)))/count1;payloadcap64',author_models_read=False,author_expected_read=False,author_or_original_executions=0,scope='IndependentWIP/staticpreparationonly,notruntimeacceptance')
    (out/'static-preparation.json').write_text(json.dumps(result,indent=2)+'\n');return result


BATCH=ROOT/'evidence/world-pause139-20261102T142612.009278Z'
HAND='248cb1aa1ad635c797f650e17f9933973fae64dce3d11211c8ec524da295bc71'
COMP='4626b50b8ede4872868da3b18603878fe57e53a53805f3a8cc4aabc62f1a0428'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]

def independent_fixture(family,xyz,count,start,duration):
    stride,guid,source,dest,clock,life=(112,16,32,44,56,60)if family=='auxiliary'else(88,24,44,56,68,72)
    rows=[]
    for index in range(count):
        row=bytearray([0x5a]*stride);identifier=(0x0102030405060708 if index==0 else 0x1000000000000000+index)+(0x10000 if family=='companions'else 0)
        origin=[add(v,rounded32(Fraction(index,8))if axis<2 else 0)for axis,v in enumerate(xyz)]
        end=[add(v,rounded32(Fraction(axis+1)))for axis,v in enumerate(origin)]
        struct.pack_into('<Q',row,guid,identifier);struct.pack_into('<3I',row,source,*origin);struct.pack_into('<3I',row,dest,*end);struct.pack_into('<II',row,clock,bits(start),bits(duration));rows.append(row.hex())
    if count:rows.append(bytes([0xa5]*stride).hex())
    return dict(count=count,storage=rows)


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP
    hand=load(BATCH/'task-handoff.json');comp=load(BATCH/'comparison.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');cfg=load(BATCH/'config.json');runtime=load(BATCH/'runtime.json')
    assert len(hand['frozen_author_files'])==6
    for name,digest in hand['frozen_author_files'].items():assert sha(ROOT/name)==digest
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']and len(sources)==75 and sum(n.startswith('reconstruction/')for n in sources)==63
    for name,digest in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==digest
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==250
    for table in[comp['artifacts'],comp['frozen'],prep['frozen']]:
        for name,digest in table.items():assert sha(BATCH/name)==digest
    assert comp['differences']==0 and comp['cases']==comp['completed_cases']==8 and comp['expectation_before_original']and prep['expected_before_original']and not prep['original_input_contains_expected']
    expectation_audit=load(BATCH/'expectation-read-audit.json');assert not expectation_audit['forbidden']and not any('/originals/'in s or Path(s).suffix in('.wasm','.wat','.memory','.exe')for s in expectation_audit['opened'])
    helpers={**O.HELPERS,**E.HELPERS,'scripts/review_opening139.py':'29de9cb7dbeb7595ce2baced0a0de9d5c5e967ce73cecd8cff5868d4feafc5c9','scripts/review_enemy_ai139.py':'73b093bdfcc59c08c010fb2c074298435b6d0f057fe15a0e5d2a8228c0fe0f42','scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b'}
    for name,digest in helpers.items():assert sha(ROOT/name)==digest,(name,sha(ROOT/name))
    assert sha(Path(cfg['snapshot_file']))==cfg['snapshot_sha256']=='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'and sha(Path(cfg['range_file']))==cfg['range_sha256']and len(load(Path(cfg['range_file'])))==2318 and cfg['world_rc']==20544696
    assert prep['resource_gate_sha256']==sha(ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json')=='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
    wp=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json';wr=load(wp);assert sha(wp)==prep['independent_world_sha256']=='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48';world,nav,scalars=load_world(dict(receipt=str(wp),receipt_sha256=sha(wp),world_artifacts=wr['world_artifacts']));assert not scalars['primary_present']and not scalars['flat_present']
    static=bind_static(out/'prewritten-reference-binding');raw=SOURCE.read_bytes();original=parse_module(raw);private=(BATCH/m['module_file']).read_bytes();modified=parse_module(private)
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==private[b['start']:b['end']]
    exports=[('research139_pause_account',0,2945),('research139_pause_ctor',0,1600),('research139_pause_opening',0,1108),('research139_pause_AI',0,925),('research139_pause_gather',0,26364),('research139_pause_stop',0,35988),('research139_pause_resume',0,25613),('research139_pause_free',0,73034),('research139_pause_stack',3,0)]
    assert modified['exports']==original['exports']+exports and m['added_exports']==[list(v)for v in exports]and len(original['imports'])==882 and m['original_imports']==[{k:r[k]for k in('module','name','type_index')}for r in original['imports']]
    bindings={};texts={};extra={30179,29237,50441,81682,11425,11499,35202,35232,1711,108362,6786}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.0-full.wat').open('rb')as s:
        for idx in sorted(set(map(int,m['functions']))|extra):
            a,z=original['bodies'][idx];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();s.seek(lo);wat=s.read(hi-lo);record=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(wat).hexdigest());bindings[str(idx)]=record;texts[idx]=wat.decode()
            if str(idx)in m['functions']:assert record['body_sha256']==m['functions'][str(idx)]['body_sha256']and record['WAT_sha256']==m['functions'][str(idx)]['WAT_sha256']and wat==(BATCH/'static'/f'{idx}.wat').read_bytes()
            (out/f'{idx}.wat').write_bytes(wat)
    assert len(m['functions'])==18 and all('call 26364'in texts[n]and'i32.store offset=2412'in texts[n]for n in[35988,25613])
    assert 'call 46692'in texts[35988]and'call 27650'in texts[25613]and'i32.const 1'in texts[27650]and'i32.le_u'in texts[27650]
    def data(address,size):
        result=bytearray(size)
        for base,pos,n in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-base:pos+hi-base]
        return bytes(result)
    word=lambda p:u(data(p,4));string=lambda p,n:data(p,n).decode();abilities={}
    for index in range(114):
        p=5882740+88*index;r=data(p,88);abilities[string(u(r,12),u(r,16))]=(p,r)
    cls=data(5877920,108);race=data(5874636,44);zone=data(5871348,152);classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=5882740)};races={1:dict(ability_pointer=abilities[string(u(race,24),u(race,28))][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    scalars['heading_bits']=u(zone,116);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];normal=data(5830904,72);eligible=[i for i in range(12)if word(5830904+72*i+68)==1 and math.isfinite(fp(word(5830904+72*i+64)))];minutes=word(u(zone,72)+336)
    tables=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888;neighbors=list(struct.iter_unpack('<ii',data(5408444,64)));english=json.loads(data(*struct.unpack('<II',data(5401532,8))));names={5830904:'Kobold Vermin'}
    cases=load(BATCH/'inputs.json');actual=[json.loads(line)for line in(BATCH/'actual.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==8
    layouts=[(0,0,0,1,2),(0,1,1,1,2),(11,0,0,1,2),(69,0,0,1,2),(0,5,9,1,2),(11,5,0,100,2),(69,0,9,100,2),(0,3,3,-2,1)]
    counts=Counter();traces=[]
    def cells(label,want,hx):
        seen=bytes.fromhex(hx);assert len(want)==len(seen)
        for index,(v,b)in enumerate(zip(want,seen,strict=True)):
            if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
            else:assert v==b,(label,index,v,b);counts[label+'_known']+=1
    owner_keys=dict(units=(1784,432),auxiliary=(652,112),companions=(2108,88),pickups=(1868,56),special=(1916,40),windows=(1964,8),boundaries=(2120,8))
    def capture_headers(cap):
        game=bytes.fromhex(cap['raw_game2592_hex']);assert len(game)==2592 and cap['sequence']==u(game,2412)and cap['packet_capacity']==u(game,1880)and cap['packet_count']==u(game,1888)==len(cap['packets'])
        assert len(cap['rng_words'])==4 and cap['rng_words']==[u(game,1720+4*j)for j in range(4)]
        for key,(off,stride)in owner_keys.items():
            vector=cap['owners'][key];assert vector['stride']==stride and vector['capacity']==u(game,off)==len(vector['storage'])and vector['pointer']==u(game,off+4)and vector['count']==u(game,off+8)<=vector['capacity']
            assert all(len(hx)==stride*2 for hx in vector['storage'])
        return game
    for index,(case,a,layout)in enumerate(zip(cases,actual,layouts,strict=True)):
        seed,na,nc,start,duration=layout;assert case['id']==a['id']==index and case['seed']==seed
        c=dict(id=index,app_seed_u64=str(seed));opening,_=O.reference(c,world,nav,scalars,tables,normal,speeds,classes,races,zones,eligible,minutes);op=opening['projection'];ctor,_=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=opening['constructor_seed_u64'],object_id_u64='0',flat_height_bits=world.height(*scalars['center_xy_bits'])),classes,races,zones)
        og=capture_headers(a['opening']);assert [[p[0],p[2]]for p in a['opening']['packets']]==op['packets']and a['opening']['packet_capacity']==128 and a['opening']['rng_words']==op['rng_words'];cells('openingGame',opening['known_Game2592'],a['opening']['raw_game2592_hex'])
        for key in['units','pickups','special','windows','boundaries']:
            vector=op[key];got=a['opening']['owners'][key];assert vector['capacity']==got['capacity']and vector['count']==got['count']
            for row,hx in zip(vector['storage'],got['storage'],strict=True):cells('opening_'+key,row,hx)
        initial=dict(rows=copy.deepcopy(op['units']['storage']),now=C.sub(bits(1.),0x3dcccccd),frame=0,player=op['player_xyz'],path=None,path_values=None,path_clock=0,sequence=1,hp=ctor['current_hp_bits'],last=0xc1200000,incoming=0.,category=0.,has_category=False,derived=ctor['derived_bits'],guards={k:0 for k in[736,740,764,1344,1348,1444,1448,1624]},fields=copy.deepcopy(ctor['player_fields']),history=dict(head=0,count=0,rows=[],strings=[],origin=[]),packets=copy.deepcopy(op['packets']))
        ai,answer=E.tick(initial,0x3dcccccd,world,nav,neighbors,names,english,counts);assert ai['now']==bits(1.)and not answer['attacks']and len(answer['records'])==4
        mg=capture_headers(a['moving']);assert [[p[0],p[2]]for p in a['moving']['packets']]==answer['packets']and a['moving']['sequence']==answer['movement_sequence2412']and a['moving']['rng_words']==op['rng_words']and a['moving']['packet_capacity']==128
        for row,hx in zip(answer['records'],a['moving']['owners']['units']['storage'],strict=True):cells('movingNPC',row,hx)
        for key in['auxiliary','companions','pickups','special','windows','boundaries']:assert a['opening']['owners'][key]==a['moving']['owners'][key]
        expected_fixtures={family:independent_fixture(family,op['player_xyz'],number,start,duration)for family,number in[('auxiliary',na),('companions',nc)]};assert case['fixtures']==expected_fixtures
        before=a['before'];bg=capture_headers(before);wanted=bytearray(mg)
        for key,(off,stride)in owner_keys.items():
            if key in expected_fixtures:
                fixture=expected_fixtures[key];got=before['owners'][key];assert got['capacity']==len(fixture['storage'])and got['count']==fixture['count']and got['storage']==fixture['storage']
                if fixture['storage']:assert got['pointer']>0;struct.pack_into('<3I',wanted,off,len(fixture['storage']),got['pointer'],fixture['count'])
                else:assert got==a['moving']['owners'][key]
            else:assert before['owners'][key]==a['moving']['owners'][key]
        assert bytes(wanted)==bg and before['packets']==a['moving']['packets']and before['rng_words']==op['rng_words']
        assert a['profile_before']==a['profile_after']and a['account_before']==a['account_after']and a['stack_after']==1048576
        #Derive declared clocks from independent motion fields; no author expectedvalues.
        row=answer['records'][0];end=add(read(row,340),read(row,344));times=[bits(100.25 if start==100 else .5 if index==3 else 1.25)]
        if index==0:times=[bits(.5),bits(1.25),bits(100.)]
        if index==2:times=[end-1,end,end+1]
        updates=[dict(action=action,now_bits=t,phase=2 if action=='pause'else 1)for t in times for action in['gather','pause','resume']]
        if index==1:updates.extend([dict(action=action,now_bits=bits(1.25),phase=2 if action=='pause'else 1)for _ in range(3)for action in['pause','resume']])
        assert case['updates']==updates and len(a['stages'])==len(updates)
        vectors=dict(units=dict(count=4,storage=answer['records']),auxiliary=expected_fixtures['auxiliary'],claims=expected_fixtures['companions']);sequence=answer['movement_sequence2412'];packet_capacity=128;packet_count=len(answer['packets']);previous=before;record=[]
        for step,(control,got)in enumerate(zip(updates,a['stages'],strict=True)):
            result=gather_reference(vectors,control['now_bits']);action=control['action'];packets=[]
            if action!='gather':
                emitted=emit_reference(vectors,control['now_bits'],sequence,packet_capacity,packet_count,world,resume=action=='resume');sequence=emitted['sequence'];packet_capacity=emitted['packet_capacity'];packet_count=emitted['packet_count'];packets=emitted['packets'];counts['height_queries']+=len(result['events'])*(2 if action=='resume'else 1)
            assert got['action']==action and got['sequence']==sequence and got['packet_capacity']==packet_capacity and got['packet_count']==packet_count and got['new_packets']==packets and got['packets']==previous['packets']+packets
            if action=='gather':
                observed=got['gathered'];assert observed['capacity']==result['capacity']and observed['count']==result['count']and(len(observed['storage'])==result['capacity']);assert observed['pointer']>0
                for row,hx in zip(result['storage'],observed['storage'],strict=True):cells('gather40',row,hx)
                if not result['capacity']:assert observed['pointer']==8
            else:assert got['gathered']is None
            input_game=bytes.fromhex(got['input_game2592_hex']);want=bytearray.fromhex(previous['raw_game2592_hex']);struct.pack_into('<I',want,2352,control['now_bits']);want[2587]=control['phase'];assert bytes(want)==input_game
            output=capture_headers(got);wanted=bytearray(input_game)
            for off,value in[(2412,sequence),(1880,packet_capacity),(1888,packet_count)]:struct.pack_into('<I',wanted,off,value)
            if packet_capacity!=previous['packet_capacity']:
                assert u(output,1884)>0;wanted[1884:1888]=output[1884:1888];counts['observed_packet_reallocation_pointer_words']+=1
            assert bytes(wanted)==output and got['owners']==previous['owners']and got['rng_words']==previous['rng_words']
            counts['target_'+action]+=1;counts['whole_Game_bytes']+=2592;counts['source_actor_background_bytes_conserved']+=sum(v['capacity']*v['stride']for v in got['owners'].values());counts['ordered221_packets']+=len(packets);counts['packet_payload_bytes']+=sum(len(p[2])//2 for p in packets);counts['family_'+action+'_NPC']+=result['family_counts']['units'];counts['family_'+action+'_aux']+=result['family_counts']['auxiliary'];counts['family_'+action+'_comp']+=result['family_counts']['claims'];counts['gather_capacity_'+str(result['capacity'])]+=int(action=='gather')
            record.append(dict(step=step,action=action,capacity=result['capacity'],count=result['count'],family_counts=result['family_counts'],sequence=sequence));previous=got
        traces.append(dict(id=index,seed=seed,stages=record))
    assert counts['target_gather']==12 and counts['target_pause']==counts['target_resume']==15 and counts['ordered221_packets']==158 and counts['packet_payload_bytes']==5490 and counts['whole_Game_bytes']==108864 and counts['source_actor_background_bytes_conserved']==148368
    wanted_calls={'2945':8,'1600':8,'1108':8,'925':8,'26364':12,'35988':15,'25613':15,'73034':11};assert runtime['calls']==wanted_calls and runtime['fresh_instances']==8 and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error']is None and runtime['stack_checks']==145
    assert len(runtime['returns'])==85 and all(r['before']==r['after']==1048576 and r['returned']for r in runtime['returns'])and len(runtime['world_checks'])==58 and all(w['ranges']==2318 and w['unchanged']for w in runtime['world_checks'])
    assert runtime['peak_memory_bytes']==177078272<=runtime['memory_cap_bytes']==268435456 and runtime['output_bytes']==(BATCH/'actual.jsonl').stat().st_size and runtime['old_Game_used_as_target']is False and runtime['NPC_or_player_positions_or_HP_patched']is False and runtime['phase_clock_controls_explicit']and runtime['controlled_auxiliary_companion_owners']
    terminal=load(BATCH/'owned-terminal.json');assert terminal==comp['process']and terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing'];command=load(BATCH/'owned-start.json');assert command['pid']==terminal['pid']and command['pgid']==terminal['pgid']and command['deadline_seconds']==60
    for name,digest in hand['frozen_author_files'].items():assert sha(ROOT/name)==digest
    for name,digest in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==digest
    assert not AUDIT
    result=dict(accepted=True,author_handoff_sha256=HAND,author_comparison_sha256=COMP,reviewer_sha256=sha(Path(__file__)),author_files=hand['frozen_author_files'],source_sha256=WASM,author_sources=len(sources),production_sources=63,source_edges=len(edges),current_body_bindings=bindings,prewritten_reference_bindings=static['bindings'],helper_source_sha256=helpers,fixtures=8,target_entries=42,target_functions={'26364':12,'35988':15,'25613':15},setup_entries_excluded=32,cleanup_entries_excluded=11,counts=dict(counts),traces=traces,original_process=terminal,source_flags_verified=True,only_export_section_changed=True,author_models_or_checker_executed=0,original_executions=0,author_expected_values_read=False,audit_forbidden=dict(AUDIT),seconds=time.monotonic()-started,full884_frames=0,complete_games=0,limits=['Current139 admission only; no 1391 migration claim.', 'Setup2945/1600/1108/925 independently recomputed as setup, not new targets; cleanup73034 separately excluded.', 'Motion NPCs are true fresh full925 outputs; auxiliary/companion records and spare bytes are explicit controlled owner inputs.', 'No actor movement writes: whole2592Game differs only seq/packet header and explicit caller clock/phase; allcapacity actor/background storage raw inherited byte-for-byte.', 'Gather40 trailing4 and all allocated spare records Unknown; independent source None cells are not reconstructed from output.', 'Finite processed motion/no-primary canonical-world only; NaN companion predicate is static recovery, not runtime coverage; nearestprimary fallback remains Pending.', 'Packet reallocation pointer values observed when capacity changes; heap layout/allocation addresses not independently predicted.', 'Resource range conservation is checked runner instrumentation and runtime flags, not independent retained raw before/after resource pairs.', 'Phase patches do not establish original2181/1093 scheduling or full884 execution; no full game or Windows app execution.'])
    save(out/'review.json',result);print(json.dumps({k:result[k]for k in['accepted','fixtures','target_entries','setup_entries_excluded','cleanup_entries_excluded','original_executions','seconds']})+'\n'+json.dumps(dict(counts)),flush=True)


if __name__=='__main__':main()
