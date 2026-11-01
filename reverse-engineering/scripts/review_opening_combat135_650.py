#!/usr/bin/env python3
"""Read-only650-frame wave/supply/growth/CAS review; transport dependency is explicitly declared.
No original, production model or checker executes. Transport explicitly uses
the frozen root decoder whose one-line quoting change has separate evidence.
"""
from pathlib import Path
from collections import Counter,defaultdict
from functools import lru_cache
from datetime import datetime,timezone
import argparse,ast,copy,hashlib,importlib.util,json,struct,sys,time,zlib
from decimal import Decimal,ROUND_HALF_EVEN,localcontext
import review_event_wave135 as wave_review
sys.dont_write_bytecode=True
import review_opening_combat135 as semantic
from review_combat137 import exports
from review_battle_shout135 import F,B,sub,mul,add,word
from review_resource_spawn135 import next_rng,advance,uniform,decode169
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'evidence/opening-combat0135-oracle-20261101T200425.298468Z'
DECODER_SHA='f9ace95818b6384ad2663d293a07d036efc0aac52c8cd75fdabb3ec82065cd2c'
FAST_OLD="return json.dumps(value, ensure_ascii=False, separators=(',', ':'))"
FAST_NEW='return json.encoder.encode_basestring(value)'
STAGES=semantic.STAGES

def sha(p):return semantic.sha(p)

@lru_cache(maxsize=8192)
def packet_item(metadata,capacity,pointer,length,payload,backing,opcode,stride):
    """Memoize only complete, exact immutable item values, never an index/ptr."""
    row=bytes.fromhex(metadata);assert len(row)==stride
    assert struct.unpack_from('<3I',row)==(capacity,pointer,length)
    body=bytes.fromhex(backing);value=bytes.fromhex(payload)
    assert length<=capacity<=1048576 and len(body)==capacity and len(value)==length and body[:length]==value
    if stride==16:assert opcode==struct.unpack_from('<H',row,12)[0]
    return row,pointer+capacity

def check_queue500(raw,game,base,stride,name):
    queue=raw[name];cap,ptr,n=struct.unpack_from('<3I',game,base)
    assert(queue['capacity'],queue['pointer'],queue['count'])==(cap,ptr,n)and n<=cap<=4096
    metadata=bytes.fromhex(queue['metadata_backing_hex']);assert len(metadata)==cap*stride and len(queue['active'])==n
    for i,item in enumerate(queue['active']):
        row,end=packet_item(item['metadata_hex'],item['capacity'],item['pointer'],item['length'],item['payload_hex'],item['backing_hex'],item.get('opcode'),stride)
        assert metadata[i*stride:(i+1)*stride]==row and end<=raw['memory_bytes']

@lru_cache(maxsize=16384)
def resource_packet(opcode,payload):
    if opcode!=169:return None
    raw=bytes.fromhex(payload)
    if len(raw)<7 or raw[:6]!=bytes((1,0,0,0,0,2)):return None
    pointer=7;guid=0
    for i in range(8):
        if raw[6]>>i&1:assert pointer<len(raw);guid|=raw[pointer]<<(8*i);pointer+=1
    if guid>>48!=0xf110 or(guid>>24)&0xffffff not in(9006,9007,9008):return None
    decoded=decode169(payload);assert decoded['guid']==guid
    return dict(guid=str(guid),payload169_hex=payload)

def resource_packets(raw):
    return[value for p in raw['packets']['active']if(value:=resource_packet(p['opcode'],p['payload_hex']))is not None]

@lru_cache(maxsize=16384)
def mask_descriptor(name,row,active):
    """Compile exact known-byte intervals; every changed row has a new key."""
    assert all(x is None or type(x)is int and 0<=x<=255 for x in row)
    gaps=tuple(i for i,v in enumerate(row)if v is None);segments=[];start=0
    for offset in gaps+(len(row),):
        if start<offset:segments.append((start,offset,bytes(row[start:offset])))
        start=offset+1
    if active:
        for offset in gaps:allowed_unknown650(name,list(row),offset)
    return tuple(segments),gaps

def check_snapshot500(raw,want,counts,maximum,read_static):
    p=raw['projection'];p['resource_create_packets169']=resource_packets(raw)
    if want is not None:
        BINDER.observe(raw,want)
        p['explicit_actor_creates169']=actor_packets(raw,{int(x['guid'])for x in want['projection']['explicit_actor_creates169']})
        p['banner150_packets']=[x['payload_hex']for x in raw['packets']['active']if x['opcode']==150]
    game=bytes.fromhex(raw['raw_game2592_hex'])
    for key,offset in(('next_event2424_bits',2424),('next_supply2448_bits',2448)):
        assert p[key]==word(game,offset)
    assert p['last_event2586']==game[2586]
    assert p['next_resource2444_bits']==struct.unpack_from('<I',bytes.fromhex(raw['raw_game2592_hex']),2444)[0]
    guardians=semantic.check_snapshot(raw,None,counts,maximum,read_static)
    if want is None:return guardians
    if guardians:
        assert len(want['projection']['guardian_cooldowns'])==len(guardians)
        for guardian in guardians:
            row=want['vectors']['units']['storage'][guardian['unit_index']]
            assert row[68:72]==[None]*4 and str(int.from_bytes(bytes(row[112:120]),'little'))==guardian['guid']
    semantic.check_value(want['projection'],p,('projection',),counts)
    for name,expected in want['vectors'].items():
        actual=raw['vectors'][name]
        for field in('capacity','count'):
            if field in expected:assert expected[field]==actual[field];counts['vector_shape_fields']+=1
        for field in('storage','records'):
            if field not in expected:continue
            observed=actual['storage']if field=='storage'else actual['storage'][:actual['count']]
            assert len(expected[field])==len(observed)
            for index,(wanted,encoded)in enumerate(zip(expected[field],observed)):
                payload=bytes.fromhex(encoded);assert len(payload)==len(wanted)
                segments,gaps=mask_descriptor(name,tuple(wanted),index<actual['count'])
                for start,end,value in segments:assert payload[start:end]==value,(name,index,start,end)
                counts['strict_record_bytes']+=len(payload)-len(gaps);counts['unknown_cells']+=len(gaps)
                counts['unknown_cells_nonzero_original']+=sum(payload[i]!=0 for i in gaps)
                if name=='units'and index<actual['count']and word(payload,64)==3:counts['guardian_physical_pointer_unknown_bytes']+=sum(68<=i<72 for i in gaps)
    return guardians

def check_resource_transition(before,raw,stage,frame,clock,deadline,payloads):
    p=raw['projection'];old=before['projection'];actual=p['next_resource2444_bits'];creates=p['resource_create_packets169']
    if stage!='spawn'or F(clock)<F(deadline):assert actual==deadline and creates==payloads;return None
    assert deadline==0x42200000 and actual==add(clock,B(45))and before['kind']=='claims'
    units,previous=raw['vectors']['units'],before['vectors']['units']
    assert units['storage']==previous['storage']and units['count']==previous['count']and units['capacity']==previous['capacity']
    assert F(old['budget_bits'])<1,'First resource witness requires no ordinary RNG prefix'
    incoming=before['vectors']['pickups'];outgoing=raw['vectors']['pickups'];n=incoming['count']
    assert outgoing['count']==n+1 and outgoing['capacity']==incoming['capacity']
    assert outgoing['storage'][:n]==incoming['storage'][:n]
    for index,(a,b)in enumerate(zip(incoming['storage'],outgoing['storage'])):
        if index!=n:assert a==b
    prior=bytes.fromhex(incoming['storage'][n]);new=bytes.fromhex(outgoing['storage'][n]);words=tuple(old['rng_words'])
    assert sum(3<=word(bytes.fromhex(row),8)<=5 for row in incoming['storage'][:n])==0
    for selection_draws in range(1,100001):
        output,words=next_rng(words);product=output*3
        if product&0xc0000000!=0xc0000000:break
    else:raise AssertionError('Resource selection watchdog')
    kind,amount=3+(product>>32),words[0]
    assert word(new,0)==0 and word(new,8)==kind and word(new,12)==amount
    assert new[4:8]==prior[4:8]and struct.unpack_from('<3I',new,24)==(0,8,0)and word(new,52)==clock
    visual=9006+kind-3;counter=(old['spawn_counter']+1)&0xffffffff;guid=0xf110000000000000|(visual<<24)|(counter&0xffffff)
    assert struct.unpack_from('<Q',new,16)[0]==guid and word(new,36)==visual
    assert p['spawn_counter']==counter and p['message_sequence']==old['message_sequence']
    #This witness takes the first13516 trial (two position draws), then yaw.
    #Exact final XYZ is separately compared to pre-frozen model expectation.
    position_words=advance(words,2);yaw,final_words,yaw_draws=uniform(position_words,0x40c90fdb)
    assert yaw_draws==1 and p['rng_words']==list(final_words)
    assert len(creates)==len(payloads)+1 and creates[:len(payloads)]==payloads
    packet=creates[-1];decoded=decode169(packet['payload169_hex']);fields=decoded['fields'];xyz=struct.unpack_from('<3I',new,40)
    assert packet['guid']==str(guid)and decoded['guid']==guid and decoded['xyz']==xyz and decoded['yaw']==add(yaw,0)
    assert all(fields[k]==v for k,v in{2:33,3:visual,4:0x3f800000,8:{3:5931,4:5995,5:5991}[kind],9:0,14:1,15:xyz[0],16:xyz[1],17:xyz[2],18:add(yaw,0),20:35,21:5}.items())
    payloads.append(packet)
    return dict(frame=frame,completed_frame_number=frame+1,action_index=raw['action_index'],stage_index=raw['stage_index'],clock_bits=clock,clock_seconds=F(clock),old_deadline_bits=deadline,next_deadline_bits=actual,next_deadline_seconds=F(actual),kind=kind,amount=amount,guid=str(guid),counter_before=old['spawn_counter'],counter_after=counter,rng_before=old['rng_words'],rng_after=p['rng_words'],independent_draws=dict(kind=selection_draws,position=2,yaw=1),pickup_index=n,pickup_capacity=outgoing['capacity'],prior_arrival4_hex=prior[4:8].hex(),arrival_preserved=True,new56_hex=new.hex(),packet169_hex=packet['payload169_hex'],no_ordinary_unit_spawn_on_witness=True)


EXTRA=Counter();GROWTH=[];WITNESSES=[];COMPONENT_REVIEWS=[];WAVE={}

class IndependentAddressBindings:
    """Only original-side owner arithmetic; never import the production binder.

    Each birth reads the previous original vector header, whose binding to Game
    is separately verified. Semantic None words and active four-byte masks are
    admitted only for the same unique GUID, exact producer and offset.
    """
    def __init__(self):
        self.previous=None;self.bindings={};self.births=[];self.observations=0
        self.indices=set();self.guids=set()

    def observe(self,raw,want):
        self.indices=set();self.guids=set();v=raw['vectors']['pickups']
        rows=[bytes.fromhex(x)for x in v['storage'][:v['count']]]
        actual={struct.unpack_from('<Q',r,16)[0]:r for r in rows}
        assert len(actual)==len(rows),'Nonunique active pickup GUID'
        declarations=want['opaque_pickup_amount_origins']
        declared={int(x['guid']):x for x in declarations};assert len(declared)==len(declarations)
        for index,row in enumerate(want['projection']['pickup_words']):
            guid=row[4]|row[5]<<32
            if row[3]is not None:
                assert guid not in declared;continue
            assert row[2]==2 and guid in declared,'Unowned or non-kind2 semantic None'
            origin=declared.pop(guid)
            assert set(origin)=={'guid','owner_field_offset','byte_addend','producer'}
            assert origin['guid']==guid and origin['owner_field_offset']==1872 and origin['producer']=='947.G2448'
            encoded=actual[guid];assert word(encoded,8)==2
            value=word(encoded,12)
            if guid not in self.bindings:
                before=self.previous
                assert raw['record_kind']=='stage'and raw['kind']=='spawn'and before and before['kind']=='claims'
                assert F(raw['projection']['now_bits'])<F(before['next_resource2444_bits'])
                n=before['count'];assert n>0,'Mode0 empty owner is not restored'
                delta=176+224*(n//4)if n%4==0 else 8+56*n
                assert origin['byte_addend']==delta and value==(before['pointer']+delta)&0xffffffff
                self.bindings[guid]=value
                self.births.append(dict(guid=str(guid),frame=raw['frame'],stage_index=raw['stage_index'],owner_pointer=before['pointer'],owner_count=n,byte_addend=delta,original_amount=value,independent_model_received_original_pointer=False))
            assert self.bindings[guid]==value,'Bound original word changed'
            cells=want['vectors']['pickups']['storage'][index]
            assert cells[12:16]==[None]*4 and cells[16:24]==list(encoded[16:24])
            self.indices.add(index);self.guids.add(guid);self.observations+=1
        assert not declared,'Orphan address declaration'
        self.previous=dict(kind=raw.get('kind',raw['record_kind']),pointer=v['pointer'],count=v['count'],next_resource2444_bits=raw['projection']['next_resource2444_bits'])

    def report(self):
        return dict(births=self.births,bound_words=len(self.bindings),observations=self.observations,all_birth_formulas_and_retained_bytes_verified=True,original_values_used_as_model_inputs=False,unsupported_domains=['simultaneousG2444_resource_andG2448_supply','mode0_empty_owner'])

BINDER=IndependentAddressBindings()

def allowed_unknown650(name,row,offset):
    if name=='pickups'and 12<=offset<16:
        guid=int.from_bytes(bytes(row[16:24]),'little')
        assert row[8:12]==[2,0,0,0]and row[12:16]==[None]*4 and guid in BINDER.guids
    else:semantic.allowed_unknown(name,row,offset)

def check_value650(want,actual,path,counts):
    if want is None and len(path)>=3 and path[-3]=='pickup_words':
        assert type(actual)is int and 0<=actual<=0xffffffff
        if path[-1]==1:counts['unwritten_pickup_arrival_words']+=1;return
        assert path[-1]==3 and path[-2]in BINDER.indices
        counts['verified_opaque_pickup_amount_words']+=1;return
    assert type(want)is type(actual),(path,type(want),type(actual))
    if isinstance(want,dict):
        assert set(want)<=set(actual)
        for k,v in want.items():check_value650(v,actual[k],path+(k,),counts)
    elif isinstance(want,list):
        assert len(want)==len(actual),(path,len(want),len(actual))
        for i,(a,b)in enumerate(zip(want,actual)):check_value650(a,b,path+(i,),counts)
    else:assert want==actual,(path,want,actual);counts['projection_leaves']+=1

@lru_cache(maxsize=32768)
def actor_guid(opcode,payload):
    if opcode!=169:return None
    raw=bytes.fromhex(payload)
    if len(raw)<7 or raw[:5]!=bytes((1,0,0,0,0))or raw[5]not in(2,3):return None
    at=7;guid=0
    for bit in range(8):
        if raw[6]>>bit&1:
            assert at<len(raw);guid|=raw[at]<<(8*bit);at+=1
    return guid

def actor_packets(raw,guids):
    return[dict(guid=str(g),payload169_hex=p['payload_hex'])for p in raw['packets']['active']if(g:=actor_guid(p['opcode'],p['payload_hex']))in guids]

def fixed(word_value,digits):
    with localcontext()as context:
        context.prec=128;value=Decimal.from_float(F(word_value)).quantize(Decimal(1).scaleb(-digits),rounding=ROUND_HALF_EVEN)
        return('-'if value.is_signed()else'+')+format(abs(value),'.'+str(digits)+'f')

def growth_packet(before,after,template):
    damage=mul(sub(after['1540'],before['1540']),B(100))
    hp=sub(after['1536'],before['1536']);regen=sub(after['1576'],before['1576'])
    text=template.replace('{damage}',fixed(damage,0)).replace('{health}',fixed(hp,0)).replace('{regen}',fixed(regen,2))
    raw=text.encode();return(struct.pack('<BIQI',10,0,0,len(raw)+1)+raw+b'\0\0').hex(),text

def prepare_additional(read,source):
    paths=[('event-wave0135-independent-review-20261101T192947.072998Z/review.json','ac576e5668537ade78db54a2f45abebd1543aa8988c362ab4583f584c586f850'),('supply-kind2-135-independent-review-20261101T193915.933213Z/review.json','bb56ba2213d54912521deb390f131db1205bf9fc7ad82adb51802c6131827c98'),('level-banner135-independent-review-20261101T195147.952310Z/review.json','1b3014d52043a70f283709567f36d14b3ee14ae6b1b9621ec802165809e31f13')]
    for name,digest in paths:
        p=ROOT/'evidence'/name;assert sha(p)==digest
        r=json.loads(p.read_text());assert r['version']=='0.135.1'if 'version'in r else r['source_files']in(20,61)
        original=Path(r.get('comparison',ROOT/'evidence/full0135-oracle-20261101T190041.544885Z/event-wave135-comparison.json'))
        assert sha(original)==r['comparison_sha256']
        COMPONENT_REVIEWS.append(dict(path=str(p),sha256=digest,comparison_sha256=r['comparison_sha256'],scope='Previously independently reviewed component; not new original cases in this integration audit.'))
    run=ROOT/'evidence/full0135-oracle-20261101T190041.544885Z'
    report=json.loads((run/'event-wave135-comparison.json').read_text())
    wave_audit=json.loads((ROOT/'evidence'/paths[0][0]).read_text())
    for n in('event-input.json','event-labels.json','event-results.jsonl'):
        assert sha(run/n)==wave_audit['audited_artifact_sha256'][n]
    WAVE['case']=json.loads((run/'event-input.json').read_text())[-1]
    WAVE['label']=json.loads((run/'event-labels.json').read_text())[-1]
    WAVE['component_actual']=json.loads((run/'event-results.jsonl').read_text().splitlines()[-1])['result']
    fields=wave_review.literal(source/'reconstruction/core_spec/spawn135_data.py','NORMAL_FIELDS')
    WAVE['defs']=[dict(zip(fields,row))for row in wave_review.literal(source/'reconstruction/core_spec/spawn135_data.py','NORMALS')[0]]
    WAVE['geometry']=wave_review.literal(source/'reconstruction/core_spec/spawn_position135_data.py','ZONE_GEOMETRY')[0]
    for d in WAVE['defs']:
        raw=read(d['pointer'],72)
        assert list(struct.unpack_from('<11I',raw,24))==[d[k]for k in('entry','display','scale_bits','classification','hp_bits','attack_bits','field48_bits','field52_bits','xp','cost_bits','unlock_bits')]
        assert raw[68]==d['elite']
    WAVE['world']=wave_review.World(WAVE['case']['world'])
    WAVE['growth_template']=read(1587933,88).decode()
    assert WAVE['growth_template']=='You have gained {damage}% damage, {health} maximum health and {regen} health per second.'

def audit_additional(before,raw,want,read_static):
    old=before['projection'];p=raw['projection'];stage=raw['kind'];clock=p['now_bits']
    old150=[x['payload_hex']for x in before['packets']['active']if x['opcode']==150]
    new150=[x['payload_hex']for x in raw['packets']['active']if x['opcode']==150]
    assert new150[:len(old150)]==old150,'150 queue prefix changed'
    if p['progression']['level']!=old['progression']['level']:
        assert stage=='collect'and p['progression']['level']==old['progression']['level']+1
        payload,text=growth_packet(old['derived_bits'],p['derived_bits'],WAVE['growth_template'])
        assert new150[len(old150):]==[payload]
        EXTRA['growth_events']+=1
        GROWTH.append(dict(frame=raw['frame'],stage_index=raw['stage_index'],level=p['progression']['level'],text=text,payload150_hex=payload))
    if stage!='spawn':
        assert p['next_event2424_bits']==old['next_event2424_bits']and p['next_supply2448_bits']==old['next_supply2448_bits']and p['last_event2586']==old['last_event2586'];return
    due=F(clock)>=F(old['next_event2424_bits'])
    supply_due=F(clock)>=F(old['next_supply2448_bits'])
    if not due:
        assert p['next_event2424_bits']==old['next_event2424_bits']and p['last_event2586']==old['last_event2586']
    if not supply_due:assert p['next_supply2448_bits']==old['next_supply2448_bits']
    if due:
        assert supply_due and raw['frame']==600 and raw['stage_index']==8416
        c,label=WAVE['case'],WAVE['label'];inp=c['input']
        assert old['rng_words']==inp['rng_words']and old['spawn_counter']==inp['counter']==226
        assert old['message_sequence']==p['message_sequence']==inp['message_sequence']==587
        assert old['now_bits']==clock==inp['now_bits']and old['next_event2424_bits']==inp['next_event2424_bits']and old['last_event2586']==255
        assert old['player_xyz']==inp['player_xyz_bits']and old['velocity_xy']==inp['velocity_xy']and old['progression']['level']==inp['level1432']
        assert before['vectors']['units']['count']==c['units']['count']==16 and raw['vectors']['units']['count']==24
        # The actual947 emits one combined result: independently reconstruct
        # its wave RNG state, then continue supply draws before testing it.
        # No observed intermediate state is invented or fed to the model.
        intermediate=wave_review.advance(tuple(old['rng_words']),label['wave_draws'])
        wave_actual=dict(last_event2586=p['last_event2586'],next_event2424_bits=p['next_event2424_bits'],rng_words=list(intermediate),units=raw['vectors']['units'])
        stats=Counter();index,begin,created=wave_review.event_reference(c,label,wave_actual,WAVE['defs'],WAVE['geometry'],WAVE['world'],stats)
        assert index==0 and begin==16 and len(created)==8 and label['ordinary_draws']==0 and label['wave_draws']==19
        counter=old['spawn_counter'];new_packets=raw['new_packets']['appended']
        assert len(new_packets)==10 and [x['opcode']for x in new_packets]==[169]*8+[150,169]
        for j,row in enumerate(created):
            counter=(counter+1)&0xffffffff;d=WAVE['defs'][index];decoded=decode169(new_packets[j]['payload_hex']);guid=0xf130000000000000|(d['entry']<<24)|counter
            assert struct.unpack_from('<Q',row,112)[0]==decoded['guid']==guid and decoded['variant']==3
            assert decoded['xyz']==tuple(struct.unpack_from('<3I',row,316))and decoded['fields']==wave_review.npc_fields(guid,d,row,42,6)
            assert new_packets[j]==WAVE['component_actual']['packets'][j]
        assert new_packets[8]==WAVE['component_actual']['packets'][8]and new150[len(old150):]==[new_packets[8]['payload_hex']]
        EXTRA['wave_events']+=1;EXTRA['wave_units']+=8;EXTRA['wave_draws']+=19
        assert before['vectors']['pickups']['count']==3 and raw['vectors']['pickups']['count']==4
        count_kind2=sum(word(bytes.fromhex(x),8)==2 for x in before['vectors']['pickups']['storage'][:3]);assert count_kind2==2
        assert p['next_supply2448_bits']==add(clock,B(70))and p['next_event2424_bits']==1122841024
        supply=bytes.fromhex(raw['vectors']['pickups']['storage'][3]);guid=0xf110000000000000|(9005<<24)|((counter+1)&0xffffffff)
        assert word(supply,8)==2 and struct.unpack_from('<Q',supply,16)[0]==guid and word(supply,36)==9005 and word(supply,52)==clock
        assert before['vectors']['pickups']['storage'][:3]==raw['vectors']['pickups']['storage'][:3]
        assert p['spawn_counter']==counter+1==235
        yaw,words,draws=uniform(advance(intermediate,2),0x40c90fdb);assert draws==1 and p['rng_words']==list(words)
        decoded=decode169(new_packets[9]['payload_hex']);assert decoded['guid']==guid and decoded['xyz']==struct.unpack_from('<3I',supply,40)and decoded['yaw']==add(yaw,0)
        assert decoded['fields'][3]==9005 and decoded['fields'][8]==259 and decoded['fields'][21]==3
        EXTRA['supply_events']+=1;EXTRA['supply_draws']+=3
        WITNESSES.append(dict(frame=600,stage_index=8416,old_counter=226,new_counter=235,old_unit_count=16,new_unit_count=24,wave_style=0,wave_definition=0,wave_rng=list(intermediate),final_rng=p['rng_words'],wave_independent_checks=dict(stats),supply_GUID=str(guid),supply_original_amount=word(supply,12),new_opcodes=[x['opcode']for x in new_packets]))

def opaque_negative_checks():
    """Pure auditor guards only: not additional original cases."""
    guid=0xf110000000000001;row=[0]*14;row[2]=2;row[3]=None;row[4]=guid&0xffffffff;row[5]=guid>>32
    origin=dict(guid=guid,owner_field_offset=1872,byte_addend=176,producer='947.G2448')
    def fixture():
        payload=bytearray(56);struct.pack_into('<IIQ',payload,8,2,1176,guid)
        raw=dict(record_kind='stage',kind='spawn',frame=600,stage_index=8416,projection=dict(now_bits=B(60.1),next_resource2444_bits=B(85)),vectors=dict(pickups=dict(count=1,pointer=2000,storage=[payload.hex()])))
        cells=list(payload);cells[12:16]=[None]*4
        want=dict(opaque_pickup_amount_origins=[dict(origin)],projection=dict(pickup_words=[row.copy()]),vectors=dict(pickups=dict(storage=[cells])))
        binder=IndependentAddressBindings();binder.previous=dict(kind='claims',pointer=1000,count=3,next_resource2444_bits=B(85));return binder,raw,want
    names=[]
    changes=[('wrong_word',lambda b,r,w:r['vectors']['pickups']['storage'].__setitem__(0, r['vectors']['pickups']['storage'][0][:24]+'99040000'+r['vectors']['pickups']['storage'][0][32:])),('wrong_GUID_owner',lambda b,r,w:w['opaque_pickup_amount_origins'][0].__setitem__('guid',guid+1)),('wrong_producer',lambda b,r,w:w['opaque_pickup_amount_origins'][0].__setitem__('producer','1417')),('wrong_offset',lambda b,r,w:w['opaque_pickup_amount_origins'][0].__setitem__('owner_field_offset',1876)),('wrong_addend',lambda b,r,w:w['opaque_pickup_amount_origins'][0].__setitem__('byte_addend',8)),('wrong_stage',lambda b,r,w:r.__setitem__('kind','collect')),('empty_owner',lambda b,r,w:b.previous.__setitem__('count',0)),('simultaneous_resource',lambda b,r,w:b.previous.__setitem__('next_resource2444_bits',B(60))),('missing_declaration',lambda b,r,w:w.__setitem__('opaque_pickup_amount_origins',[])),('partial_None_mask',lambda b,r,w:w['vectors']['pickups']['storage'][0].__setitem__(12,0))]
    for name,change in changes:
        b,r,w=fixture();change(b,r,w)
        try:b.observe(r,w)
        except(AssertionError,KeyError):names.append(name)
        else:raise AssertionError('Auditor admitted corrupted '+name)
    b,r,w=fixture();b.observe(r,w);assert b.observations==1
    b.previous['kind']='spawn';r['kind']='terminal';r['vectors']['pickups']['storage'][0]=r['vectors']['pickups']['storage'][0][:24]+'99040000'+r['vectors']['pickups']['storage'][0][32:]
    try:b.observe(r,w)
    except AssertionError:names.append('bound_value_drift')
    else:raise AssertionError('Bound value drift accepted')
    return names

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('directory',nargs='?',type=Path,default=DEFAULT);parser.add_argument('--output',type=Path);args=parser.parse_args()
    began=time.monotonic();semantic.check_queue=check_queue500;semantic.check_value=check_value650
    directory=args.directory.resolve();out=args.output.resolve()if args.output else ROOT/'evidence'/datetime.now(timezone.utc).strftime('opening-combat135-650frame-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=json.loads((directory/'comparison.json').read_text());fixtures=json.loads((directory/'fixtures.json').read_text());runtime=report['runtime'];source=directory/'source-snapshot'
    assert runtime==json.loads((directory/'opening-combat135-cas-runtime.json').read_text())
    assert sha(directory/'comparison.json')=='16a86a82820ee8f737b256a458b252546336b20b6cd887d3c45e755f9ba538b1'
    assert report['status']=='matched_requested_budget'and report['differences']==0 and report['independent_frames']==650 and report['independent_selections']==5 and report['compared_stages']==9105 and report['capture_format']=='cas'
    assert report['source_sha256_before']==report['source_sha256_after']and len(report['source_sha256_before'])==104
    for name,digest in report['source_sha256_before'].items():assert sha(source/name)==digest==sha(ROOT/name),name
    production=sorted(n for n in report['source_sha256_before']if n.startswith('reconstruction/'));assert production==semantic.frozen_closure(source)and len(production)==90
    for name in production:
        for node in ast.walk(ast.parse((source/name).read_text())):
            if isinstance(node,ast.Call):
                f=node.func;fn=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                assert fn not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'),(name,fn)
    decoder_source=source/'scripts/opening_combat135_cas.py';assert sha(decoder_source)==DECODER_SHA
    decoder_path=decoder_source
    assert decoder_path.read_text().count(FAST_NEW)==1 and FAST_OLD not in decoder_path.read_text()
    spec=importlib.util.spec_from_file_location('declared_CAS_transport',decoder_path);transport=importlib.util.module_from_spec(spec);spec.loader.exec_module(transport)
    decoder=transport.CaptureCAS135(directory)
    codec_review=ROOT/'evidence/opening-cas-codec135-review-20261101T200414.243123Z/review.json';assert sha(codec_review)=='079deca782201acd886c713ce8a3eb462189f1d9ca16233d140a81a1edc42115'
    codec=json.loads(codec_review.read_text());assert codec['negative_count']==codec['rejected_count']==26 and codec['sources_before']==codec['sources_after']and codec['sources_before']['scripts/opening_combat135_cas.py']==DECODER_SHA
    inputs=json.loads((directory/'inputs.json').read_text());assert inputs==[{k:fixtures[k]for k in('id','input','actions')}]
    for file,key in(('fixtures.json','fixtures_sha256'),('inputs.json','inputs_sha256'),('stage-expectations.jsonl.gz','expectations_sha256'),('results.cas.jsonl.gz','original_results_sha256')):assert sha(directory/file)==report[key]
    assert report['model_expected_before_original']and report['original_input_contains_no_expectations']
    checker=(source/'scripts/check_opening_combat135.py').read_text();assert checker.index('row=corpus(')<checker.index('child=subprocess.Popen(')and'child.wait(timeout=min(30,remaining))'in checker and'deadline_seconds=180 if args.capture_format' in checker
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();manifest=json.loads((directory/'manifest.json').read_text());module=(directory/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==report['original_sha256']and hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    a,b=semantic.sections(original),semantic.sections(module);assert[x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]
    assert all(original[x:y]==module[u:v]for(k,x,_,y),(_,u,_,v)in zip(a,b)if k!=7)
    added=[['research_opening_combat135_'+x['role'],0,x['index']]for x in manifest['roles']]+[['research_opening_combat135_stack',3,0]]
    assert exports(module)==exports(original)+added
    read_static=semantic.static_reader(original);battle_definition=read_static(5467956,88);prepare_additional(read_static,source);del original,module
    assert word(battle_definition,0)==8 and word(battle_definition,44)==6673 and battle_definition[84]==9
    context=report['original_context'];assert sha(Path(context['snapshot_path']))==context['snapshot_sha256']=='23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
    expected_reader=semantic.JsonlReader(directory/'stage-expectations.jsonl.gz',True,1073741824);expected=iter(expected_reader);opening=next(expected);assert opening['record_kind']=='opening';opening=opening['expected']
    distance=semantic.independent_distance_sha(opening,report)
    order=[('case_start',None,None,0),('constructor',None,None,0),('opening',None,None,0)];frame=0
    for index,action in enumerate(fixtures['actions']):
        if action['kind']=='select':order.append(('stage',index,'select',frame))
        else:assert action['kind']=='controlled_tail_frame';order.append(('clock_control',index,None,frame));order.extend(('stage',index,kind,frame)for kind in STAGES);frame+=1
    order.append(('case_end',None,None,frame));assert frame==650 and len(order)==9759 and len(fixtures['actions'])<=700
    compressed=(directory/'results.cas.jsonl.gz').read_bytes();assert len(compressed)<=268435456
    inflate=zlib.decompressobj(31);index_raw=inflate.decompress(compressed,33554433);assert len(index_raw)<=33554432 and inflate.eof and not inflate.unused_data and not inflate.unconsumed_tail
    counts=Counter();maximum=defaultdict(int);records=Counter();clock=0;stage_index=0;previous=None;previous_want=None;last=None;locale=None;selections=[];guardian_owners={};guardian_captures=0;guardian_payloads=0;packet_max=0;first_guardian=None;first_battle=None;battle_tick_count=0;fourth_select=None;battle_countdowns=[];previous_packets=[];previous_notifications=[];negative=[];resource_events=[];resource_deadline=0x42200000;resource_payloads=[];clock_crossings=[]
    for line_index,line in enumerate(index_raw.splitlines(keepends=True)):
        assert time.monotonic()-began<300,'Read-only review300s budget';raw=decoder.decode_line(line);kind,action_index,stage_kind,frame_index=order[line_index]
        records[raw['record_kind']]+=1;assert raw['record_kind']==kind and raw['id']==0
        if action_index is not None:assert raw['action_index']==action_index and raw['frame']==frame_index
        if stage_kind is not None:assert raw['kind']==stage_kind
        if kind=='case_start':locale=raw['locale_prestate'];assert locale['effective_index']==0 and locale['once_flag']==3
        if kind=='clock_control':
            action=fixtures['actions'][action_index];assert raw['old_bits']==clock and raw['dt_bits']==action['dt_bits'];clock=B(F(clock)+F(action['dt_bits']))
            assert raw['new_bits']==clock and raw['original880_called']is False and raw['only_external_game_write_offset']==2352
            if F(raw['old_bits'])<40<=F(clock):clock_crossings.append(dict(frame=frame_index,old_bits=raw['old_bits'],old_seconds=F(raw['old_bits']),new_bits=clock,new_seconds=F(clock)))
        if kind in('constructor','opening','stage'):
            want=opening if kind=='opening'else None
            if kind=='stage':
                item=next(expected);assert item['record_kind']=='stage'and item['stage_index']==stage_index and item['action_index']==action_index and item['kind']==stage_kind;want=item['expected'];counts['stage_identity_leaves']+=2
            guardians=check_snapshot500(raw,want,counts,maximum,read_static);packet_max=max(packet_max,raw['packets']['count'])
            for queue,field,old in(('packets','new_packets',previous_packets),('notifications','new_notifications',previous_notifications)):
                current=[{'opcode':x['opcode'],'payload_hex':x['payload_hex']}for x in raw[queue]['active']]if queue=='packets'else[x['payload_hex']for x in raw[queue]['active']]
                prefix=len(old)<=len(current)and current[:len(old)]==old;delta=raw[field]
                assert delta['prefix_preserved']==prefix and delta['previous_count']==len(old)and delta['current_count']==len(current)and delta['appended']==(current[len(old):]if prefix else[])
                if not prefix:assert delta['full_current']==current
                if queue=='packets':previous_packets=current
                else:previous_notifications=current
            if guardians:
                guardian_captures+=1;guardian_payloads+=len(guardians)
                if first_guardian is None:first_guardian=dict(frame=frame_index,stage_index=stage_index,count=len(guardians));negative=semantic.owner_negative_checks(raw,want,read_static)
                for owner in guardians:
                    identity=(owner['ability_pointer'],owner['header_pointer']);assert guardian_owners.get(owner['guid'],identity)==identity;guardian_owners[owner['guid']]=identity
            if kind=='stage':
                resource_event=check_resource_transition(previous,raw,stage_kind,frame_index,clock,resource_deadline,resource_payloads)
                if resource_event:
                    index=resource_event['pickup_index'];old_arrival=previous_want['vectors']['pickups']['storage'][index][4:8];new_arrival=want['vectors']['pickups']['storage'][index][4:8]
                    assert old_arrival==new_arrival and all(type(v)is int for v in old_arrival),'Existing known+4 bytes may not become None'
                    resource_event['expected_known_arrival_bytes_preserved']=old_arrival;resource_events.append(resource_event);resource_deadline=resource_event['next_deadline_bits']
                audit_additional(previous,raw,want,read_static)
                assert raw['stage_index']==stage_index and raw['projection']['now_bits']==clock
                assert raw['entry_index']==(1072 if stage_kind=='select'else semantic.ENTRIES[STAGES.index(stage_kind)])
                if stage_kind=='select':
                    selected=fixtures['actions'][action_index]['index'];cards=previous['projection']['candidates'];assert previous['projection']['phase2587']==2 and raw['input_index']==selected
                    selection=dict(frame=frame_index,action_index=action_index,index=selected,card=cards[selected],phase_after=raw['projection']['phase2587']);selections.append(selection)
                    if len(selections)==4:
                        assert selection['card']['ability_id']=='battle_shout'and selected==0 and frame_index==379 and raw['projection']['phase2587']==1;fourth_select=selection
                        battle=next(bytes.fromhex(x)for x in raw['projection']['owned_records_hex']if word(bytes.fromhex(x),0)==5467956)
                        assert word(battle,8)==0x3f000000 and raw['vectors']['owned80']['count']==3
                if stage_kind=='player'and fourth_select:
                    prior=[bytes.fromhex(x)for x in previous['projection']['owned_records_hex']];current=[bytes.fromhex(x)for x in raw['projection']['owned_records_hex']]
                    bi=next(i for i,x in enumerate(prior)if word(x,0)==5467956);before,after=prior[bi],current[bi];remaining=sub(word(before,8),fixtures['actions'][action_index]['dt_bits']);battle_tick_count+=1
                    assert before[:8]+before[12:]==after[:8]+after[12:]
                    if F(remaining)>0:assert word(after,8)==remaining
                    else:
                        cooldown=mul(mul(mul(mul(word(battle_definition,52),0x3fb33333),word(before,16)),word(before,56)),raw['projection']['derived_bits']['1544'])
                        cooldown=cooldown if F(cooldown)>.25 else 0x3e800000;assert word(after,8)==cooldown
                        duration=mul(mul(mul(word(battle_definition,68),0x3fb33333),word(before,28)),word(before,68));duration=duration if F(duration)>.1 else 0x3dcccccd
                        active=[bytes.fromhex(x)for x in raw['vectors']['live32']['storage'][:raw['vectors']['live32']['count']]]
                        buff=next(x for x in active if word(x,8)==8 and word(x,20)==6673)
                        assert buff[:8]==bytes(8)and word(buff,12)==mul(word(before,76),word(battle_definition,4))and word(buff,24)==add(clock,duration)and word(buff,28)==0
                        if first_battle is None:first_battle=dict(frame=frame_index,stage_index=stage_index,player_ticks_since_selection=battle_tick_count,clock_bits=clock,remaining_cooldown_bits=word(after,8),live_record_hex=buff.hex(),damage_multiplier_bits=raw['projection']['derived_bits']['1540'])
                    battle_countdowns.append(dict(frame=frame_index,remaining_bits=word(after,8)))
                path=raw['projection']['distance_map']
                if path is not None:
                    for key,value in distance.items():assert path[key]==value
                stage_index+=1
            previous=raw;previous_want=want;last=raw
        if kind=='opening':
                banners=raw['projection']['banner150_packets'];assert any('The Defias Uprising — survive the onslaught!'.encode() in bytes.fromhex(x) for x in banners);EXTRA['initial_banner_subtitle_verified']+=1
        if kind=='case_end':
            assert raw['boundary']is None and raw['host_calls']==[]and raw['stage_count']==9105 and raw['locale_writes']==0 and raw['locale_after']==locale
            for call in raw['calls']:assert call['stack_after']==1048576
            calls=[x for x in raw['calls']if x['role']!='original_allocator'];assert len(calls)==9107 and all(x['returned']for x in calls)
        if(line_index+1)%100==0:
            progress=dict(records=line_index+1,stages=stage_index,seconds=time.monotonic()-began);(out/'progress.json').write_text(json.dumps(progress)+'\n');print(json.dumps(progress),flush=True)
    assert len(order)==9759 and len(resource_events)==1 and resource_events[0]['frame']==400 and resource_events[0]['stage_index']==5615
    assert len(clock_crossings)==1 and clock_crossings[0]['frame']==resource_events[0]['frame']
    assert decoder.record_index==9759 and stage_index==9105 and len(selections)==5 and next(expected,None)is None
    cas=decoder.finish(runtime['capture_cas']);assert cas['logical_bytes']==3952877407 and cas['logical_sha256']=='0c3b9edb71921634aed2c72cf3303050b5fe34e88f777ae49a0edfbfd49ea527'
    assert expected_reader.bytes==fixtures['expected_uncompressed_bytes']==report['expected_uncompressed_bytes']and expected_reader.file_digest.hexdigest()==report['expectations_sha256']
    assert runtime['schema_version']==5 and runtime['output_protocol']=='bounded_stage_cas_jsonl_gzip'and runtime['budgets']==runtime['capture_cas']['limits']
    limits=runtime['budgets'];assert limits['logical_record_bytes']==2097152 and limits['logical_output_bytes']==8589934592 and limits['unique_blob_bytes']==536870912 and limits['blob_bytes']==16777216 and limits['blob_files']==65536 and limits['compressed_output_bytes']==268435456 and limits['owned_deadline_seconds']==180
    assert runtime['capture_cas']['compressed_bytes']==len(compressed)and runtime['capture_cas']['compressed_sha256']==hashlib.sha256(compressed).hexdigest()and runtime['memory_page_cap']==4096 and runtime['peak_memory_bytes']<=268435456 and runtime['js_heap_cap_mib']==512 and runtime['denied_imports']==878 and runtime['host_imports_throw']is True
    assert all(maximum[x]==0 for x in semantic.EMPTY_DOMAINS)and first_battle['player_ticks_since_selection']==6
    reconciled=sum(counts[k]for k in('strict_record_bytes','projection_leaves','vector_shape_fields','stage_identity_leaves'))
    assert reconciled==report['comparison']['compared_leaves']and counts['unknown_cells']==report['comparison']['declared_unknown_cells']and counts['unwritten_pickup_arrival_words']==report['comparison']['unwritten_pickup_arrivals'] and counts['verified_opaque_pickup_amount_words']==report['comparison']['verified_opaque_pickup_amounts']
    assert BINDER.report()==report['pickup_address_proof'] and EXTRA['growth_events']==5 and EXTRA['wave_events']==EXTRA['supply_events']==1 and EXTRA['initial_banner_subtitle_verified']==1
    terminal=json.loads((directory/'process-terminal.json').read_text());owned=json.loads((directory/'owned-process.json').read_text());assert terminal['exit_code']==0 and terminal['deadline_exceeded']is False and owned['deadline_seconds']==180
    assert terminal['seconds']==report['process']['seconds']<180 and terminal['pid']==terminal['pgid']==report['process']['pid']
    assert report['process']['command']==owned['command']and sha(Path(owned['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    assert semantic.missing(terminal['pid'])and semantic.missing(terminal['pgid'],True)and(directory/'stderr.log').stat().st_size==0 and json.loads((directory/'differences.json').read_text())==[]
    for name,digest in report['source_sha256_before'].items():assert sha(source/name)==digest==sha(ROOT/name),name
    result=dict(status='passed_scoped_read_only_review',comparison=str(directory/'comparison.json'),comparison_sha256=sha(directory/'comparison.json'),source_files=104,production_files=90,current_and_frozen_sources_verified=True,reviewer_script_sha256=sha(Path(__file__)),transport=dict(source= str(decoder_path),sha256=sha(decoder_path),frozen_root_decoder_sha256=DECODER_SHA,private_fast_decoder_used=False,independent_26negative_review_sha256=sha(codec_review),each_logical_SHA_and_all_occurrences_verified=True,full_finish=cas,one_complete_gzip_member=True),
        stream_record_counts=dict(records),expected_stream=expected_reader.receipt(),comparison_counts=dict(counts),reconciled_known_leaves=reconciled,nonexport_sections_identical=True,full_declared_projection_recompared=True,omitted_payload_max_counts={x:maximum[x]for x in semantic.EMPTY_DOMAINS},observed_vector_max_counts=dict(maximum),first_guardian=first_guardian,guardian_distinct_GUIDs=sorted(guardian_owners),guardian_owner_captures=guardian_captures,guardian_payload_comparisons=guardian_payloads,guardian_corruption_checks=negative,
        selections=selections,battle_first_actual_buff=first_battle,battle_player_countdown=battle_countdowns,Battle_effect8_owner0_payload_and_CD_independently_checked=True,independent_Dijkstra=distance,final_progression=last['projection']['progression'],final_gold=last['projection']['gold'],observed_packet_max=packet_max,resource_events=resource_events,first_clock_crossing40=clock_crossings[0],resource_packet_payloads=resource_payloads,resource_entry9006_9007_9008_full169_payloads_compared=True,all150_payloads_and_declared_GUID_actor169_payloads_compared=True,all_other_packet_payload_semantics_claimed_compared=False,pickup_address_proof=BINDER.report(),independent_growth_and_wave_supply_checks=dict(EXTRA),independent_growth_events=GROWTH,independent_wave_supply_events=WITNESSES,component_review_dependencies=COMPONENT_REVIEWS,opaque_negative_checks=opaque_negative_checks(),known_byte_and_unknown_mask_descriptor_cache=mask_descriptor.cache_info()._asdict(),exact_packet_item_validation_cache=packet_item.cache_info()._asdict(),
        original_process_terminal=terminal,original_wait180s_did_not_timeout=True,original_Node_seconds=report['process']['seconds'],parent_process_seconds_including_recomparison=report['process']['total_seconds_including_verification'],actual_Node_seconds_not_inferred_from_parent_total=True,original_or_model_or_checker_executed_by_reviewer=False,new_original_cases=0,new_full880_frames=0,scope='One human warrior seed0/navFalse stationary650 controlled14-tail frames, realphase1/ownedcapacity/None; independent preparsedworld/originalsnapshot/externalclock, not full880/native/wholegame.',elapsed_seconds=time.monotonic()-began)
    (out/'static-image-reads.json').write_text(json.dumps(read_static.proofs,indent=2)+'\n');result['static_image_reads_sha256']=sha(out/'static-image-reads.json')
    assert time.monotonic()-began<300,'Complete read-only review300s budget'
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],seconds=result['elapsed_seconds'],battle_first=first_battle,resource_events=resource_events)),flush=True)
if __name__=='__main__':main()
