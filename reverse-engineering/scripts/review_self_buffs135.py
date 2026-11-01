#!/usr/bin/env python3
"""Read-only independent fixed135 0/8/1020+typed-passive13 component audit.

No production imports, model/original/checker execution, or target mutation.
Prior reviewer arithmetic primitives are reused; this reviewer independently
reconstructs the new admitted semantic branches from frozen input and raw output.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_resource_consumer135 as component
from review_resource_player135 import aura_events,minnum,positive,ceil_u32
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
from review_resource_consumer137 import source_edges,identities
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/self-buffs0135-oracle-20261101T221510.852622Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
F,B,add,sub,mul=component.F,component.B,component.add,component.sub,component.mul
u,put=component.u,component.put

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def stats1512(t,live,count,now,read):
    """1512 ordered <= expiry skip; unlike1202, a NaN expiry stays active."""
    cls,race=t['class_byte'],t['race_byte']
    cp=u(read(1595888+4*((cls-2)&255),4))if((cls-2)&255)<=9 else 5462608
    rp=u(read(1595728+4*((race-2)&255),4))if((race-2)&255)<=6 else 5459304
    hp,armor=struct.unpack('<2I',read(cp+72,8));rpv,nr=struct.unpack('<2I',read(rp+16,8));assert nr<=16
    n=sub(B(float(t['level'])),B(1))
    v={0:B(1),1:add(mul(n,0x3cf5c28f),B(1)),2:0,3:B(1),4:0x3d4ccccd,5:armor,6:add(mul(n,0x3da3d70a),0x3f4ccccd),7:B(9),8:B(1),9:B(1),10:0,11:0}
    for j in range(nr):
        tag,value=struct.unpack('<2I',read(rpv+j*8,8));assert tag in v
        v[tag]=mul(v[tag],add(value,B(1)))if tag==7 else add(v[tag],value)
    seen={}
    for row in live[:count]:
        if F(u(row,24))<=F(now):continue
        kind,spell=u(row,8),u(row,20);assert kind in(0,8,12)
        if spell in seen:
            assert kind==seen[spell]==0;continue
        seen[spell]=kind
        if kind==8:
            magnitude=u(row,12);assert math.isfinite(F(magnitude))and F(magnitude)>0
            v[1]=add(v[1],mul(B(1),magnitude))
        if spell==23451:v[3]=add(v[3],0x3f19999a)
        elif spell==23505:v[1]=add(v[1],B(.5))
    base=add(hp,mul(n,B(9)));maximum=mul(add(base,0),v[0]);armor=component.minimum(v[5],0x3f19999a);speed=component.minimum(v[3],0x400ccccd)
    result={1536:maximum,1540:add(add(component.div(mul(0,armor),B(10)),mul(0,component.maximum(sub(v[5],0x3f19999a),0))),v[1]),
        1544:component.div(B(1),add(v[2],B(1))),1548:B(1)if F(v[4])>1 else v[4],1552:add(B(2),add(v[4],B(-1)))if F(v[4])>1 else B(2),
        1556:speed,1560:v[7],1564:v[8],1568:armor,1572:0x3f19999a,1576:add(mul(0,maximum),v[6]),1580:B(1),
        1584:add(v[10],t['conditional268_bits'])if t['flag2574']else v[10],1588:v[9],1592:0,1596:0,1600:v[11],1604:0,
        1608:min(t['level']//15,3),1612:0,1616:add(component.div(maximum,component.maximum(base,B(1))),B(-1)),1620:0,1624:0}
    extra=0
    for entry in t['passives']:
        assert entry['tag']==13 and math.isfinite(F(entry['value_bits']))and F(entry['value_bits'])>=0
        extra=add(extra,entry['value_bits'])
    result[1620]=extra
    return{str(k):value for k,value in result.items()}

def rebuild_aura(live,count,now,previous,initialized,fields,sem):
    selected=[];seen=set()
    for row in live[:count]:
        if not F(u(row,24))>F(now):continue
        kind,spell=u(row,8),u(row,20)
        assert kind in(0,8,12)
        if kind==12:assert spell==1020
        if kind==8:assert math.isfinite(F(u(row,12)))and F(u(row,12))>=0
        if spell in seen:
            assert kind==0 and all(k==0 for k,s,e in selected if s==spell)
            continue
        seen.add(spell);selected.append((kind,spell,u(row,24)))
    rows=[[0]*4+[None]*12 for _ in range(48)]
    for target,(kind,spell,expiry)in zip(rows,selected[:32]):
        target[:]=list(struct.pack('<4I',1,spell,expiry,1))
        if kind==12:sem['active1020_positive_Aura_observations']+=1
    events=aura_events(previous,initialized,rows)
    fields.update((str(key),value)for _,key,value in events)
    sem['aura_rebuilds']+=1;sem['aura_key_writes']+=len(events)
    return rows,1,events


def bind_raw(raw,runtime,case):
    game=bytes.fromhex(raw['raw_game8192_hex']);assert len(game)==8192
    read=lambda o:struct.unpack_from('<I',game,o)[0]
    q=raw['known'];assert q['derived_bits']=={str(o):read(o)for o in range(1536,1628,4)}
    for key,off in(('current_hp_bits',1440),('speed_bits',1648),('counter2408',2408),('message_sequence2412',2412),('action_sequence1644',1644)):
        assert q[key]==read(off)
    assert q['auxiliary_bits']=={str(o):read(o)for o in(1444,1448,1348,768,756)}
    assert q['rng_words']==list(struct.unpack_from('<4I',game,1720))and q['player_fields']==raw['raw_keyed_fields']
    assert game[360]==case['state']['stats']['class_byte']and game[361]==case['state']['stats']['race_byte']
    assert game[2587]==1 and game[387]==case['state']['heal_gate387']
    assert game[1256:1336].hex()==case['basic_hex']and read(1628)==0x7f800000
    assert struct.unpack_from('<3I',game,1656)==(0,4,0)
    for name,off,stride in(('live',1704,32),('pickups',1868,56),('aura',2000,16)):
        cap,pointer,count=struct.unpack_from('<3I',game,off);v=q[name]
        assert(v['capacity'],v['count'])==(cap,count)and count<=cap<=4096
        assert len(v['storage'])==cap and pointer+cap*stride<=runtime['max_memory_bytes']
        assert all(len(bytes.fromhex(row))==stride for row in v['storage'])
    assert q['aura']['initialized2569']==game[2569]
    a=raw['raw_aura16'];assert(a['capacity'],a['count'])==(q['aura']['capacity'],q['aura']['count'])
    assert a['storage_hex']==''.join(q['aura']['storage'])
    for name,off,stride in(('raw_packets',1880,16),('raw_notifications',1892,12)):
        cap,pointer,count=struct.unpack_from('<3I',game,off);queue=raw[name]
        assert(queue['capacity'],queue['count'])==(cap,count)and count<=cap<=512
        assert pointer+count*stride<=runtime['max_memory_bytes']and len(queue['active'])==count
        metadata=bytes.fromhex(queue['raw_hex']);assert len(metadata)==count*stride
        for i,item in enumerate(queue['active']):
            capacity,body,length=struct.unpack_from('<3I',metadata,stride*i)
            assert length<=capacity<=1048576 and body+length<=runtime['max_memory_bytes']
            assert len(bytes.fromhex(item['payload_hex']))==length
            if name=='raw_packets':assert item['opcode']==struct.unpack_from('<H',metadata,stride*i+12)[0]
    assert q['packets_known']==raw['raw_packets']['active']
    assert q['notifications_hex']==[x['payload_hex']for x in raw['raw_notifications']['active']]
    assert q['destroy170_hex']==[x['payload_hex']for x in raw['raw_packets']['active']if x['opcode']==170]
    passive=case['state']['stats']['passives'];praw=b''.join(struct.pack('<2I',e['tag'],e['value_bits'])for e in passive)
    assert raw['passive_source']==dict(count=len(passive),storage_hex=praw.hex())
    assert read(1700)==len(passive)and read(1696)+len(praw)<=runtime['max_memory_bytes']
    return game


def review_case(case,wanted,actual,label,read,runtime,counts,sem,witnesses):
    assert case['id']==wanted['id']==actual['id']==label['id']
    state=case['state'];t=state['stats'];initial=case['level_input']
    assert state['aura_external_sources_absent']and state['locale_code']=='en'
    assert all(not t[k]for k in('adjustments','item_modifiers','owned_skills','timed_records','timed_definitions'))
    assert all(not initial['sources'][k]for k in('adjustments','item_modifiers','owned_skills','timed_records','definitions'))
    assert t['conditional1344_id']==t['conditional1348_bits']==t['conditional268_bits']==t['pool768_bits']==0
    assert t['level']==initial['progression']['level']==1 and t['flag2574']==0
    assert initial['phase2587']==1 and not initial['choice_inputs']['owned']
    for key,value in initial['stats'].items():assert t[key]==value
    assert initial['sources']['live_effects']==t['live_effects']
    assert initial['sources']['passives']==t['passives']
    live=[list(row)for row in state['live']['storage']];count=state['live']['count']
    derived={str(k):v for k,v in state['derived_bits']}
    #Typed source-grant fixtures begin before full1512; only that first call
    #is allowed to reconcile the newly declared passive source with1620.
    baseline={**t,'passives':[]}if t['passives']else t
    assert derived==initial['derived_bits']==stats1512(baseline,live,count,t['now_bits'],read)
    if t['passives']:
        assert case['operations'][0]['operation']=='recalculate'and derived['1620']==0
        assert len(t['passives'])==1 and t['passives'][0]=={'tag':13,'value_bits':B(.03)}
        sem['typed_passive13_cases']+=1
    fields={str(k):v for k,v in state['player_fields']};assert fields==initial['player_fields']
    hp=t['current_hp_bits'];speed=t['previous_speed_bits'];shield=t['pool1532_bits'];barrier=t['pool1536_bits']
    aura=[list(row)for row in state['aura']['storage']];initialized=state['aura']['initialized2569']
    if aura:
        check_fields={};check,_,_=rebuild_aura(live,count,t['now_bits'],[],0,check_fields,Counter())
        assert aura==check
    sequence=state['action_sequence1644'];next_id=state['notification_next_id14340336'];guid=state['player_guid']
    assert guid==int(case['player_guid'])==42
    wire=[];notifications=[];locale_initialized=False
    assert len(case['operations'])==len(wanted['stages'])==len(actual['stages'])==len(label['operations'])
    for index,(op,want,raw,meta)in enumerate(zip(case['operations'],wanted['stages'],actual['stages'],label['operations'])):
        now,dt,last=op['now_bits'],op['dt_bits'],op['last_hit_bits'];mode=op.get('operation','player')
        assert all(math.isfinite(F(v))for v in(now,dt,last))
        old_live=[row.copy()for row in live];old_count=count;old_aura=[row.copy()for row in aura]
        before1620=derived['1620'];events=[];dirty=False
        def recalc():
            nonlocal derived,hp,speed,sequence
            derived=stats1512(t,live,count,now,read)
            hp=minnum(hp,derived['1536'])
            fields.update({'22':ceil_u32(hp),'28':ceil_u32(derived['1536']),'1109':mul(derived['1548'],B(100))})
            new_speed=mul(derived['1556'],B(7))
            if F(sub(new_speed,speed)&0x7fffffff)>F(0x3c23d70a):
                speed=new_speed;wire.append(dict(opcode=226,payload_hex=(component.packed(guid)+struct.pack('<II',sequence,speed)).hex()))
                sequence=(sequence+1)&0xffffffff;sem['new_speed226']+=1
                if sequence==0:sem['action_wrap']+=1
            sem['stats_recalculations']+=1
        def aura_now():
            nonlocal aura,initialized
            aura,initialized,aevents=rebuild_aura(live,count,now,aura,initialized,fields,sem)
            return aevents
        if mode=='recalculate':
            assert t['passives']and index==0
            recalc();events=[['full1512_initialization']]
            assert derived['1620']==B(.03)and raw['before1620_bits']==0
            assert raw['known']['derived_bits']['1620']==derived['1620']
            sem['original1512_nonzero1620_initializations']+=1
        elif mode=='aura':
            events=aura_now();sem['direct1202']+=1
        elif mode=='effect':
            kind=op['kind'];assert kind in(3,4,5)and not t['passives']
            spell={3:23451,4:23505,5:23493}[kind]
            wire.append(dict(opcode=306,payload_hex=component.spellgo(guid,spell)))
            sem['direct10298_kind'+str(kind)]+=1
            if kind==5:
                request=mul(derived['1536'],B(.5));request=mul(request,B(.5)if state['heal_gate387']>4 else B(1))
                hp=component.minimum(add(hp,request),derived['1536'])
                fields.update({'22':ceil_u32(hp),'28':ceil_u32(derived['1536'])})
                #Event metadata intentionally excludes1453 accounting.
                assert meta['events'][0][0]=='resource_heal'
            else:
                write=0
                for j in range(count):
                    if u(live[j],20)==spell:continue
                    if j!=write:live[write]=live[j].copy()
                    write+=1
                if write==len(live):live.extend([[None]*32 for _ in range(max(4,2*len(live))-len(live))])
                for off,value in((0,0),(4,0),(8,0),(20,spell),(24,add(now,B(10 if kind==3 else 15))),(28,0)):
                    put(live[write],off,value)
                count=write+1;recalc();aura_now()
            name={3:'Speed Rune',4:'Berserker Rune',5:'Restoration Rune'}[kind];text=name+'!'
            note=dict(type='banner',id=next_id,kind='rune',text=text,name=name,boss=False)
            notifications.append(json.dumps(note,ensure_ascii=False,separators=(',',':')).encode().hex())
            chat=('AZSBANNER\tid='+str(next_id)+';kind=rune;boss=0;name='+name+';text='+text).encode()
            wire.append(dict(opcode=150,payload_hex=(struct.pack('<BIQI',6,0xffffffff,guid,len(chat)+1)+chat+b'\0\0').hex()))
            next_id=(next_id+1)&0xffffffff;locale_initialized=True;sem['rune_JSON_and150']+=1
        else:
            assert mode=='player';sem['full2088']+=1
            expired=[u(row,20)for row in live[:count]if F(now)>=F(u(row,24))];dirty=bool(expired)
            if dirty:
                write=0
                for j in range(count):
                    if F(now)<F(u(live[j],24)):
                        if j!=write:live[write]=live[j].copy()
                        write+=1
                    elif math.isnan(F(u(live[j],24))):sem['NaN_co_removed']+=1
                count=write;recalc();events=[['expire_live',expired],['recalculate1512']]+aura_now()
                sem['dirty_recalculations']+=1
            else:sem['no_dirty_stages']+=1
            barrier=minnum(shield,barrier)
            elapsed=sub(now,last);extra=mul(derived['1536'],derived['1620'])if F(elapsed)>=3 else 0
            regen=mul(B(.5)if state['heal_gate387']>4 else B(1),mul(dt,add(derived['1576'],extra)))
            old_hp=hp
            if F(hp)<F(derived['1536']):
                hp=minnum(derived['1536'],add(0,add(hp,regen)))
                fields.update({'22':ceil_u32(hp),'28':ceil_u32(derived['1536'])});events.append(['regen_keys22_28'])
            delta=positive(sub(hp,old_hp));events.append(['healaccount1453_pending',minnum(delta,regen)])
            if 'expired_spell_ids'in meta:
                assert meta['expired_spell_ids']==expired and meta['recalculated']==dirty
                assert(meta['regen_request_bits'],meta['heal_delta_bits'])==(regen,delta)
            sem['nonzero1620_regen_stages']+=derived['1620']!=0
            sem['nonzero_extra_regen_stages']+=extra!=0
            if t['passives']:
                witnesses.append(dict(case_id=case['id'],group=label['group'],stage=index,elapsed_bits=elapsed,
                    elapsed=F(elapsed),gate387=state['heal_gate387'],maximum_hp_bits=derived['1536'],
                    extra1620_bits=derived['1620'],extra_regen_bits=extra,regen_request_bits=regen,
                    hp_before_bits=old_hp,hp_after_bits=hp,clamped=hp==derived['1536']))
        if mode!='effect':assert meta['events']==events,(case['id'],index,'metadata-events')
        if 'before1620_bits'in meta:
            assert meta['before1620_bits']==before1620 and meta['after1620_bits']==derived['1620']
            assert meta['operation']==mode and meta['elapsed_bits']==sub(now,last)
        if mode in('aura','recalculate'):assert live==old_live and count==old_count
        prediction=dict(aura=dict(capacity=len(aura),count=len(aura),storage=aura,initialized2569=initialized),
            packets_known=wire,notifications_hex=notifications,notification_next_id14340336=next_id,
            live=dict(capacity=len(live),count=count,storage=live),pickups=dict(capacity=0,count=0,storage=[]),destroy170_hex=[],
            derived_bits=derived,current_hp_bits=hp,speed_bits=speed,
            auxiliary_bits={'1444':shield,'1448':barrier,'1348':0,'768':0,'756':0},player_fields=fields,
            rng_words=state['rng_words'],counter2408=85,message_sequence2412=123,action_sequence1644=sequence)
        assert prediction==want,(case['id'],index,[(k,prediction[k],want[k])for k in prediction if prediction[k]!=want[k]][:1])
        bind_raw(raw,runtime,case)
        observed=dict(raw['known'])
        for name in('live','aura','pickups'):
            observed[name]={**observed[name],'storage':[list(bytes.fromhex(row))for row in observed[name]['storage']]}
        component.strict(want,observed,(),counts)
        for wrow,arow in zip(want['live']['storage'],observed['live']['storage']):
            for wcell,acell in zip(wrow,arow):
                if wcell is None:assert acell==case['unknown_poison'];sem['live_None_poison_preserved_bytes']+=1
        assert raw['before1620_bits']==before1620
        counts['stages']+=1;counts['raw_packet_observations']+=raw['raw_packets']['count']
        #1453 naturally initializes locale in player phases, rune helpers do so
        #in effect phases;1202/1512 alone do not initialize locale.
        if mode in('player','effect'):locale_initialized=True
        locale=struct.unpack('<7I',bytes.fromhex(raw['locale_state_hex']))
        assert locale[6]==(3 if locale_initialized else 0)
def mechanical_regression(directory,cases,operations,main_sources):
    """Fresh regression recompare only; no claim of a second semantic audit."""
    run=ROOT/'evidence'/directory;report=load(run/'comparison.json')
    assert report['comparison_complete']and report['differences']==0
    assert(report['cases'],report['operations'])==(cases,operations)
    assert report['source_sha256_before']==report['source_sha256_after']
    sources=report['source_sha256_before']
    for name,digest in sources.items():
        assert sha(run/'source-snapshot'/name)==digest==sha(ROOT/name)
        if name in main_sources:assert digest==main_sources[name]
    for name,digest in(report['frozen_artifacts']|report.get('artifacts',{})).items():assert sha(run/name)==digest
    expected=load(run/'expected.json');actual=[json.loads(x)for x in(run/'stdout.jsonl').read_text().splitlines()]
    counts=Counter()
    assert len(expected)==len(actual)==cases
    for want,raw in zip(expected,actual):
        assert want['id']==raw['id']and len(want['stages'])==len(raw['stages'])
        for w,a in zip(want['stages'],raw['stages']):
            got=dict(a['known'])
            for key in('pickups','live','aura'):
                got[key]={**got[key],'storage':[list(bytes.fromhex(h))for h in got[key]['storage']]}
            component.strict(w,got,(),counts);counts['stages']+=1
    assert counts['stages']==operations and counts['known_values']==report['comparison']['known_values']
    old_none=report['comparison'].get('explicit_unknown_physical_bytes',report['comparison'].get('unknown_physical_bytes'))
    assert counts['explicit_unknown_physical_bytes']==old_none
    terminal=load(run/'process-terminal.json')
    assert terminal==report['process']and terminal['exit_code']==0 and terminal['error']is None
    assert missing(terminal['pid'])and missing(terminal['pgid'],True)
    runtime=report['runtime'];assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']
    return dict(directory=str(run),comparison_sha256=sha(run/'comparison.json'),cases=cases,operations=operations,
        source_files=len(sources),strict_comparison_counts=dict(counts),new_original_executions=0,
        scope='Fresh declared-domain regression independently reread/strict-recompared; semantic reconstruction belongs to prior component audit, not repeated here.')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir()
    began=time.monotonic();report=load(RUN/'comparison.json')
    assert sha(RUN/'comparison.json')=='d61f92779fe2e984c0b85e6042acf6ac7c985e952976d5f58d829ae57344457b'
    assert report['comparison_complete']and report['differences']==0 and(report['cases'],report['operations'])==(61,119)
    assert report['source_files']==39 and report['source_sha256_before']==report['source_sha256_after']
    sources=report['source_sha256_before'];frozen=RUN/'source-snapshot'
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(frozen/name),name
    edges=source_edges(frozen,list(sources));assert edges==report['local_source_import_edges']and len(edges)==138
    production=sorted(name for name in sources if name.startswith('reconstruction/'))
    assert len(production)==30 and not any('headless'in name for name in sources)
    for name in production:
        for node in ast.walk(ast.parse((frozen/name).read_text())):
            if isinstance(node,ast.Call):
                fun=node.func;called=fun.id if isinstance(fun,ast.Name)else fun.attr if isinstance(fun,ast.Attribute)else''
                assert called not in('open','read_bytes','read_text','write_bytes','write_text','Popen','exec','eval','__import__')
    reviewer_files=['review_self_buffs135.py','review_resource_consumer135.py','review_resource_player135.py',
        'review_opening_combat135.py','review_combat137.py','review_battle_shout135.py','review_resource_consumer137.py']
    reviewer_sources={'scripts/'+n:sha(ROOT/'scripts'/n)for n in reviewer_files}
    for name,digest in reviewer_sources.items():
        p=out/'reviewer-source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==digest
    artifacts_before={p.name:sha(p)for p in RUN.iterdir()if p.is_file()}
    prepared=load(RUN/'prepared.json');assert prepared['source_sha256']==sources
    assert prepared['expected_before_original']and prepared['deadline_seconds']==60 and prepared['artifacts']==report['frozen_artifacts']
    for name,digest in report['frozen_artifacts'].items():assert sha(RUN/name)==digest
    checker=(frozen/'scripts/check_self_buffs135.py').read_text()
    assert checker.index('rows,expected,labels=corpus(')<checker.index('child=subprocess.Popen(')
    assert 'core_spec'not in Path(__file__).read_text().split('def main():')[0].split('import review_resource_consumer135')[0]
    original=ORIGINAL.read_bytes();manifest=load(RUN/'manifest.json');module=(RUN/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==manifest['original_sha256']==report['original_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
    assert hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    a,b=sections(original),sections(module)
    assert [x[0]for x in a]==[x[0]for x in b]and 8 not in[x[0]for x in a]
    assert all(original[x:y]==module[v:z]for(k,x,_,y),(_,v,_,z)in zip(a,b)if k!=7)
    expected_exports=[['research135_self_player2088',0,2088],['research135_self_aura1202',0,1202],
        ['research135_self_effect10298',0,10298],['research135_self_stats1512',0,1512],['research135_self_stack0',3,0]]
    assert exports(module)==exports(original)+expected_exports==manifest['original_exports']+manifest['added_exports']
    identities_map=identities(original,[row['idx']for row in manifest['functions']]);texts={};static=[]
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        db.execute('pragma query_only=on')
        for entry in manifest['functions']:
            idx=entry['idx'];lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone()
            assert(bs,be)==(identities_map[idx]['body_start'],identities_map[idx]['body_end'])and hi-lo<524288
            wat.seek(lo);body=wat.read(hi-lo)
            assert body==(RUN/(str(idx)+'.wat')).read_bytes()
            assert hashlib.sha256(body).hexdigest()==entry['WAT_sha256']and entry['body_sha256']==identities_map[idx]['body_sha256']
            texts[idx]=body.decode();static.append(dict(**identities_map[idx],wat_start=lo,wat_end=hi,wat_sha256=entry['WAT_sha256']))
    assert identities_map[2088]['signature']==['7f7d','']and identities_map[10298]['signature']==['7f7f','']
    assert identities_map[1512]['signature']==identities_map[1202]['signature']==['7f','']
    assert texts[2088].index('call 1512')<texts[2088].index('call 1202')<texts[2088].index('call 1453')<texts[2088].index('call 1076')
    assert texts[10298].index('call 1512')<texts[10298].index('call 1202')<texts[10298].index('call 42920')
    assert 'f32.load offset=24\n                  local.get 47\n                  f32.le'in texts[1512]
    assert 'local.get 43\n    f32.store offset=1620'in texts[1512]
    assert 'i32.load offset=1696'in texts[1512]and'i32.load offset=1700'in texts[1512]
    assert 'f32.load offset=1620'in texts[2088]and'f32.load offset=1652'in texts[2088]
    assert 'f32.load offset=24\n        local.tee 23\n        local.get 22\n        f32.gt'in texts[1202]
    read=static_reader(original);assert read(14340336,4)==b'\1\0\0\0'
    for row in manifest['English_resource_labels']:
        visual=row['visual'];i=visual-9004;pointer=u(read(5505544+4*i,4));size=u(read(5505504+4*i,4))
        assert(pointer,size,read(pointer,size).decode())==(row['pointer'],row['bytes'],row['English'])
    assert read(manifest['default_ability_pointer'],88).hex()==manifest['default_ability88_hex']and manifest['default_ability_pointer']==5467428
    del original,module
    rows=load(RUN/'input.json');expected=load(RUN/'expected.json');actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];labels=load(RUN/'labels.json')
    assert len(rows)==len(expected)==len(actual)==len(labels)==61
    runtime=load(RUN/'self-buffs135-runtime.json');assert runtime==report['runtime']
    counts=Counter();sem=Counter();witnesses=[]
    for case,want,raw,label in zip(rows,expected,actual,labels):
        assert time.monotonic()-began<90
        review_case(case,want,raw,label,read,runtime,counts,sem,witnesses)
    assert counts['stages']==119 and counts['known_values']==48530 and counts['explicit_unknown_physical_bytes']==57632
    assert counts['raw_packet_observations']==105
    assert runtime['cases']==runtime['completed_cases']==runtime['fresh_instances']==61
    assert runtime['full_original_calls']=={'1202':10,'1512':13,'2088':91,'10298':5}
    assert sem['direct1202']==10 and sem['original1512_nonzero1620_initializations']==13 and sem['full2088']==91
    assert [sem['direct10298_kind'+str(k)]for k in(3,4,5)]==[2,2,1]
    assert sem['nonzero1620_regen_stages']==13 and sem['nonzero_extra_regen_stages']==9
    assert len(witnesses)==13 and {v['elapsed']>=3 for v in witnesses}=={True,False}
    assert runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['max_memory_bytes']<=runtime['memory_cap_bytes']==33554432
    assert runtime['error']is None and runtime['stack_all_restored']
    assert all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
    assert all(not runtime[k]for k in('application_start_called','full_game_started','network_used','user_saves_accessed','original_memory_snapshot_read','once_or_locale_state_injected'))
    terminal=load(RUN/'process-terminal.json');assert terminal==report['process']and terminal['exit_code']==0 and terminal['error']is None
    assert terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
    assert sha(Path(prepared['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    assert '--wasm-max-mem-pages=512'in prepared['command']and'--max-old-space-size=512'in prepared['command']
    assert(RUN/'stdout.jsonl').stat().st_size==runtime['output_bytes']<=4194304 and(RUN/'stderr.log').stat().st_size==0
    assert load(RUN/'differences.json')==[]
    regressions=[mechanical_regression('resource-consumer0135-oracle-20261101T221321.347269Z',130,244,sources),
        mechanical_regression('mixed-pickup0135-oracle-20261101T221410.854824Z',60,61,sources)]
    assert artifacts_before=={p.name:sha(p)for p in RUN.iterdir()if p.is_file()}
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(frozen/name)
    for name,digest in reviewer_sources.items():assert sha(ROOT/name)==digest==sha(out/'reviewer-source-snapshot'/name)
    save(out/'static-proofs.json',dict(functions=static,static_read_proofs=read.proofs,
        order='2088 dirty retain→1512→1202→regen→1453→1076;10298 buff→1512→1202→notification',
        None_policy='No magnitude read for payload-free0/12; all live physical None retains supplied poison.',
        NaN_policy='1512 ordered<= skip and1202 strict> differ; NaN co-removal is tested separately.'))
    result=dict(status='passed_scoped_read_only_review',version='0.135.1',actual_build='90898d5e3',
        comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),cases=61,stages=119,
        source_files=39,production_files=30,source_import_edges=138,source_sha256=sources,
        independent_comparison_counts=dict(counts),independent_semantic_checks=dict(sem),nonzero1620_witnesses=witnesses,
        exact_packet_opcodes=[150,226,306],raw_Game_headers_and_queues_rebound=True,
        fullbacking_known_and_None_preservation_checked=True,nonexport_sections_identical=True,
        original_terminal=terminal,stack_checks=len(runtime['stack_checks']),regressions=regressions,
        reviewer_sources=reviewer_sources,artifacts_sha256=artifacts_before,
        static_proofs_sha256=sha(out/'static-proofs.json'),elapsed_seconds=time.monotonic()-began,
        new_original_executions=0,new_original_cases=0,production_model_or_checker_executed=False,
        full880_frames=0,native_executions=0,complete_games=0,
        limitations=['Controlled manualGame/World/source fixtures; no natural profile/talent producer for passive13.',
        'Full2088 executes original1076 but learned empty/basic and preludeInfinity isolate actual owned dispatch.',
        'Only unique kind12 spell1020 plus explicit resources0 and positive unique8. Other statuses/proc/periodic/shields remain pending.',
        '1453 account/statistics/presentation remains raw observation; exact validated wire here is150/226/306.',
        'Fresh regression replay is mechanical strict recompare, not a new independent reconstruction of every mixed pickup semantic.',
        'No natural nearby resource pickup/headless750/full880/latest138flow/native/fullgame acceptance.'])
    assert result['elapsed_seconds']<90
    save(out/'review.json',result)
    print(json.dumps(dict(output=str(out),sha256=sha(out/'review.json'),status=result['status'],counts=dict(counts),semantic=dict(sem))),flush=True)

if __name__=='__main__':main()
