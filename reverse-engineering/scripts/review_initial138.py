#!/usr/bin/env python3
"""Second-author read-only1571 review, with independent empty-profile math.

Only reviewer code and stdlib execute. No production/checker/builder, WASM,
validator, native target, historical model result or user save executes.
"""
from pathlib import Path
from collections import Counter
import argparse,ast,hashlib,json,math,mmap,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_stats138 as H  # Audited binary/static readers only, not reference().
ROOT=H.ROOT;ORIGINAL=H.ORIGINAL;PROFILE=H.PROFILE
RUN=ROOT/'evidence/initial138-oracle-20261101T234430.736166Z'
EXPECTED='fd3b76ad14f92f33bb7611888b5e86df6f9ea21918292a824aef1a3da380a3b5'
FAILED=ROOT/'evidence/initial138-oracle-20261101T234125.951369Z'
FAILED_SHA='fe4f3eb0b8cd118597208f7efa9898bd9e966794efbe7672b8dcaed595a9158a'
STATIC=ROOT/'evidence/initial138-static-20261101T233259.012419Z'
STATIC_SHA='7fdb78a5b3eca0d887bdaf4b404f2cb0c06ed146e30be03876ebf120c6e29bf7'
MASK=(1<<32)-1;MASK64=(1<<64)-1;ONE=0x3f800000
def F(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def B(x):return struct.unpack('<I',struct.pack('<f',x))[0]
def plus(a,b):return B(F(a)+F(b))
def minus(a,b):return B(F(a)-F(b))
def times(a,b):return B(F(a)*F(b))
def divide(a,b):return B(F(a)/F(b))
def low(a,b):return a if F(a)<F(b)else b
def high(a,b):return a if F(a)>F(b)else b
def word(raw,o=0):return struct.unpack_from('<I',raw,o)[0]
def put(raw,o,value):raw[o:o+4]=struct.pack('<I',value)
def sha(p):return H.digest(p)
def load(p):return H.load(p)
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')

def stats(cls,race,classes,races):
    """Direct1512 empty-source path, independently ordered binary32 math."""
    hp,armor=classes[cls];delta=plus(B(1),B(-1))
    a=dict(health=ONE,damage=plus(times(delta,0x3cf5c28f),ONE),cooldown=0,speed=ONE,
        crit=0x3d4ccccd,armor=armor,regen=plus(times(delta,0x3da3d70a),0x3f4ccccd),radius=B(9),xp=ONE,gold=ONE,luck=0,v1600=0)
    tags={0:'health',1:'damage',2:'cooldown',3:'speed',4:'crit',5:'armor',6:'regen',8:'xp',9:'gold',10:'luck',11:'v1600'}
    for tag,value in races[race]:
        if tag==7:a['radius']=times(a['radius'],plus(value,ONE))
        else:a[tags.get(tag,'health')]=plus(a[tags.get(tag,'health')],value)
    base=plus(hp,times(delta,B(9)));maximum=times(plus(base,0),a['health']);armor=low(a['armor'],0x3f19999a)
    speed_mult=low(a['speed'],0x400ccccd);speed=times(speed_mult,B(7));changed=F(minus(speed,B(7))&0x7fffffff)>F(0x3c23d70a)
    excess=F(a['crit'])>1
    d={1536:maximum,1540:plus(plus(divide(times(0,armor),B(10)),times(0,high(minus(a['armor'],0x3f19999a),0))),a['damage']),
        1544:divide(ONE,plus(a['cooldown'],ONE)),1548:ONE if excess else a['crit'],1552:plus(B(2),plus(a['crit'],B(-1)))if excess else B(2),
        1556:speed_mult,1560:a['radius'],1564:a['xp'],1568:armor,1572:0x3f19999a,1576:plus(times(0,maximum),a['regen']),
        1580:ONE,1584:a['luck'],1588:a['gold'],1592:0,1596:0,1600:a['v1600'],1604:0,1608:0,1612:0,
        1616:plus(divide(maximum,high(base,ONE)),B(-1)),1620:0,1624:0}
    return dict(derived_bits={str(k):v for k,v in d.items()},current_hp_bits=maximum,
        auxiliary_bits={'1444':0,'1448':0,'1348':0,'764':0,'752':0},speed_bits=speed if changed else B(7),
        player_fields={'22':math.ceil(F(maximum)),'28':math.ceil(F(maximum)),'1109':times(d[1548],B(100))},changed=changed)

def seed_words(seed):
    outputs=[]
    for multiplier,increment in((7520897724310334953,-2259998930035483990),(793875393913628917,5507651024068337109),(-338549647893938671,-3398641427998916252),(6364136223846793005,-6812164046247290893)):
        mixed=(seed*multiplier+increment)&MASK64;value=((mixed>>45)^(mixed>>27))&MASK;rotation=mixed>>59
        outputs.append(((value>>rotation)|(value<<((32-rotation)&31)))&MASK)
    a,b,c,d=outputs;ab=a|b;allbutc=ab|d
    nonzero=(ab>>24)|(c&0xffffff)|(d>>24)|((ab|(allbutc>>8)|(allbutc>>16)|d)&255)
    if nonzero or c>=0x1000000:return(d,a,b,c),False
    return tuple(struct.unpack('<4I',struct.pack('<QQ',(-2152535657050944081)&MASK64,7960286522194355700))),True

def record80(pointer):
    # Recreate actual overlapping stores, rather than invoking the model's
    # word tuple. The same initializer writes both starter and racial80.
    raw=bytearray(80)
    for o,v in((32,0),(20,4575657221408423936),(12,4575657222473777152),(4,4539628424389459969),(40,0),(72,4575657221408423936),(64,4575657222473777152),(52,4575657222473777152)):
        struct.pack_into('<Q',raw,o,v)
    for o,v in((0,pointer),(28,ONE),(48,0),(60,0)):struct.pack_into('<I',raw,o,v)
    return raw.hex()

def prediction(inp,classes,races,class_data,race_data,zones):
    cls,race=inp['class_byte'],inp['race_byte'];zone=zones[inp['region_index']];s=stats(cls,race,classes,races)
    rng,fallback=seed_words(int(inp['seed_u64']));guid=int(inp['object_id_u64']);ability=class_data[cls][1];racial=race_data[race][1]
    packet=[]
    if s['changed']:
        octets=guid.to_bytes(8,'little');mask=sum((1<<i)for i,v in enumerate(octets)if v)
        packed=bytes((mask,))+bytes(v for v in octets if v)
        packet=[[226,(packed+struct.pack('<II',1,s['speed_bits'])).hex()]]
    scalar={488:0,736:0,740:0,1652:0xc1200000,2416:B(3),2424:B(60),2428:0,2432:0,2436:0,
        2440:B(240),2444:B(40),2448:B(60),2452:20,2456:0,2460:0,2464:0,2468:0,2472:0,2516:ONE}
    flags={k:0 for k in(768,2568,2572,2573,2576,2578,2581,2583)};tags={k:0 for k in(416,440,448,456,464,1744,1764)}
    p=dict(progression=dict(level=1,xp=0,pending_upgrades=0),derived_bits=s['derived_bits'],current_hp_bits=s['current_hp_bits'],auxiliary_bits=s['auxiliary_bits'],
        speed_bits=s['speed_bits'],player_fields=s['player_fields'],rng_words=list(rng),candidates=[],phase2587=0,selection_kind2585=255,generation_counter2400=0,
        owned_records_hex=[record80(ability)],racial_record_hex=record80(racial),player_xyz=[zone[1],zone[2],inp['flat_height_bits']],source_id=str(guid),
        timer1628_bits=0,spawn_counter=10,message_sequence=1,kill_cost_bits=0,action_sequence1644=1+int(s['changed']),movement_packets=packet,
        game_tag='0',member_count=1,initial_scalar_words={str(k):v for k,v in scalar.items()},initial_byte_flags={str(k):v for k,v in flags.items()},constructor_tags={str(k):v for k,v in tags.items()},
        now_bits=0,mode2582=0,owned_capacity=1,owned_count=1,source_counts=dict(passives=0,adjustments=0,item_modifiers=0,owned_skills=0,timed_records=0,definitions=0,live_effects=0,ability_modifiers=0,active84=0),
        unit_count=0,pickup_count=0,gold=0,earned=0,flags768=0,context908=0,extra_cast1596_bits=0)
    known=[None]*2592
    def copy(offset,raw):known[offset:offset+len(raw)]=raw
    def w(offset,v):copy(offset,struct.pack('<I',v))
    copy(0,bytes(8));copy(1336,struct.pack('<Q',guid));copy(1256,bytes.fromhex(p['racial_record_hex']));known[360]=cls;known[361]=race
    for i,v in enumerate(p['player_xyz']):w(1416+4*i,v)
    w(1428,zone[3])
    for domain in(s['derived_bits'],s['auxiliary_bits']):
        for k,v in domain.items():w(int(k),v)
    for domain in(scalar,tags):
        for k,v in domain.items():w(k,v)
    for k,v in flags.items():known[k]=v
    for k,v in((1432,1),(1436,0),(1440,s['current_hp_bits']),(1456,0),(1100,0),(1644,p['action_sequence1644']),
        (1648,s['speed_bits']),(1628,0),(2352,0),(2376,0),(2400,0),(2408,10),(2412,1),(2540,1)):w(k,v)
    for i,v in enumerate(rng):w(1720+4*i,v)
    # Actual empty vector sentinels, not inferred allocator addresses.
    for cap,pointer,count,sentinel in((592,596,600,4),(640,644,648,4),(1668,1672,1676,4),(1704,1708,1712,8)):
        w(cap,0);w(pointer,sentinel);w(count,0)
    for count in(1700,2032,176,2056,2044):w(count,0)
    for k,v in((1656,1),(1664,1),(1792,0),(1876,0),(1888,len(packet))):w(k,v)
    for k,v in((2582,0),(2585,255),(2587,0),(908,0)):known[k]=v
    assert sum(x is not None for x in known)==502
    return p,known,fallback

def static_data(raw,read):
    declarations={}
    for i in range(114):
        p=1677996+88*i;ptr,n=struct.unpack('<2I',read(p+12,8));name=read(ptr,n).decode('ascii');assert name not in declarations
        declarations[name]=p
    classes={};races={};class_data={};race_data={};zones=[]
    for cls in(1,2,3,4,5,7,8,9,11):
        p=word(read(1597616+4*((cls-2)&255),4))if((cls-2)&255)<=9 else 1673176
        ptr,n=struct.unpack('<2I',read(p+40,8));name=read(ptr,n).decode();hp,armor=struct.unpack('<2I',read(p+72,8))
        classes[cls]=(hp,armor);class_data[cls]=(name,declarations[name],hp)
    for race in range(1,9):
        p=word(read(1597456+4*((race-2)&255),4))if((race-2)&255)<=6 else 1669892
        ptr,n=struct.unpack('<2I',read(p+16,8));races[race]=list(struct.iter_unpack('<2I',read(ptr,n*8)))if n else[]
        ptr,n=struct.unpack('<2I',read(p+24,8));name=read(ptr,n).decode();definition=declarations[name]
        race_data[race]=(name,definition,read(definition+84,1)[0],word(read(definition,4)))
    for i in range(12):
        p=1666604+i*152;ptr,n=struct.unpack('<2I',read(p+8,8));zones.append((read(ptr,n).decode(),word(read(p+104,4)),word(read(p+108,4)),word(read(p+116,4))))
    return classes,races,class_data,race_data,zones

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();out=args.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();began=time.monotonic()
    reviewers={str(p.relative_to(ROOT)):sha(p)for p in(Path(__file__),Path(H.__file__))}
    for n,h in reviewers.items():p=out/'reviewer-source'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    report=load(RUN/'comparison.json');assert sha(RUN/'comparison.json')==EXPECTED and(report['cases'],report['actual_cases'],report['original1571_calls'],report['differences'])==(162,162,162,0)
    prepared=load(RUN/'prepared.json');manifest=load(RUN/'manifest.json');runtime=load(RUN/'runtime.json');terminal=load(RUN/'process-terminal.json');handoff=load(RUN/'state-handoff.json')
    files=report['source_sha256_before'];assert len(files)==21 and files==report['source_sha256_after']==prepared['source_sha256']
    source=RUN/'source-snapshot'
    for n,h in files.items():assert sha(ROOT/n)==sha(source/n)==h,n
    edges=H.local_edges(source,files);assert edges==report['source_import_edges']==prepared['source_import_edges']and len(edges)==35
    prod={n for n in files if n.startswith('reconstruction/')};todo=['reconstruction/core_spec/initial_state138.py','reconstruction/core_spec/flow138_contract.py'];seen=set()
    while todo:
        n=todo.pop()
        if n in seen:continue
        seen.add(n);todo.extend(b for a,b in edges if a==n)
    assert seen==prod and len(prod)==10
    for n in prod:
        for node in ast.walk(ast.parse((source/n).read_text())):
            if isinstance(node,ast.Call):
                fn=node.func;name=fn.id if isinstance(fn,ast.Name)else fn.attr if isinstance(fn,ast.Attribute)else''
                assert name not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__','import_module'),(n,name)
    assert prepared['expected_before_original']and not prepared['original_input_contains_expected']and report['source_closure_verified_before_expectations']
    checker=(source/'scripts/check_initial138.py').read_text();assert checker.index("save(expected,rows)")<checker.index('subprocess.Popen(')
    for n,h in prepared['frozen_artifacts'].items():assert sha(RUN/n)==h
    for n,h in report['artifacts'].items():assert sha(RUN/n)==h
    artifacts={n:sha(RUN/n)for n in(*report['artifacts'],'comparison.json','prepared.json','runtime.json','owned-process.json','validator-terminal.json','state-handoff.json')}
    original=ORIGINAL.read_bytes();assert len(original)==90946299 and hashlib.sha256(original).hexdigest()==H.SHA==report['original_sha256']
    module=(RUN/manifest['module_file']).read_bytes();assert hashlib.sha256(module).hexdigest()==manifest['module_sha256']==report['module_sha256']
    old,new=H.sections(original),H.sections(module);assert [x[0]for x in old]==[x[0]for x in new]and not any(x[0]==8 for x in old)
    assert all(original[a:z]==module[b:y]for(k,a,_,z),(_,b,_,y)in zip(old,new)if k!=7)
    assert H.exports(module)==H.exports(original)+[['research138_initial1571',0,1571],['research138_initial_stack0',3,0]]
    identities=H.function_ids(original,{1571,1512,29649,48118,15913,25794,10287,9440,23171,92072})
    assert identities[1571]['signature']==['7f7f7f','']and identities[1571]['body_bytes']==7069 and identities[1571]['body_sha256']==manifest['entry']['body_sha256']=='37447d2eef76c4d93a5e2d2b5c0143ff8ef591e13fded44ee84e06bcb8d9a43e'
    read=H.static_image_reader(original);classes,races,class_data,race_data,zones=static_data(original,read)
    assert class_data==H.literal(source/'reconstruction/core_spec/initial_state138_data.py','CLASS_STARTERS')
    assert race_data==H.literal(source/'reconstruction/core_spec/initial_state138_data.py','RACIAL_ABILITIES')and tuple(zones)==H.literal(source/'reconstruction/core_spec/initial_state138_data.py','ZONE_ENTRIES')
    assert sha(STATIC/'initial-data.json')==STATIC_SHA;static=load(STATIC/'initial-data.json');assert static['original_wasm_sha256']==H.SHA and not static['original_executed']and not static['old_acceptance_transferred']
    assert len(static['semantic_field_equality'])==29 and len(static['windows_reference']['patterns'])==21
    for item in static['fresh']['classes']:
        assert class_data[item['class_byte']]==(item['starter_id'],item['definition_pointer'],item['hp_bits'])
        for k,n in(('raw88',88),('definition88',88)):
            p=item['pointer']if k=='raw88'else item['definition_pointer'];data=read(p,n);assert data.hex()==item[k+'_hex']and hashlib.sha256(data).hexdigest()==item[k+'_sha256']
    for item in static['fresh']['races']:
        assert race_data[item['race_byte']]==(item['racial_id'],item['definition_pointer'],item['execution_kind'],item['effect_tag'])
        for k,n in(('raw44',44),('definition88',88)):
            p=item['pointer']if k=='raw44'else item['definition_pointer'];data=read(p,n);assert data.hex()==item[k+'_hex']and hashlib.sha256(data).hexdigest()==item[k+'_sha256']
    for item in static['fresh']['zones']:
        assert zones[item['index']]==(item['identifier'],item['x_bits'],item['y_bits'],item['field116_bits'])
        assert read(item['pointer'],152).hex()==item['raw152_hex']
    native=ROOT/'originals/official-release-20261101T201508.341687Z/windows-0.138.0/AzerothSurvivors.exe'
    assert sha(native)==static['windows_reference']['exe_sha256']=='eb5fd1c1b96e6180fcf5f3d685d90a61471af28d22e5f060c02b7b7663fbf79e'
    with native.open('rb')as stream,mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ)as exe:
        for p in static['windows_reference']['patterns']:
            data=bytes.fromhex(p['pattern_hex']);start=exe.find(data);assert [start]==p['matches']and exe.find(data,start+1)==-1
    functions={}
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
    with(PROFILE/'official-0.138.0-full.wat').open('rb')as stream:
        for idx,identity in identities.items():
            row=dict(db.execute('select *from functions where idx=?',(idx,)).fetchone());assert(row['body_start'],row['body_end'])==(identity['body_start'],identity['body_end'])
            stream.seek(row['wat_start']);data=stream.read(row['wat_end']-row['wat_start']);assert len(data)<=1048576
            (out/f'{idx}.wat').write_bytes(data);functions[idx]=dict(identity,wat_sha256=hashlib.sha256(data).hexdigest(),wat_bytes=len(data))
    assert(out/'1571.wat').read_bytes()==(RUN/'1571.wat').read_bytes()
    wat=(out/'1571.wat').read_text();stats_wat=(out/'1512.wat').read_text();query=(out/'29649.wat').read_text();speed_wat=(out/'48118.wat').read_text()
    for t in('i32.const 2944','i32.const 88','i32.const 2592','call 29649','call 1512','f32.store offset=1528'):assert t in wat
    for t in('i32.load offset=596','i32.load offset=600','f32.load offset=764','f32.store offset=764','call 48118','offset=1644','offset=1648'):assert t in stats_wat
    assert 'i32.load8_u offset=112'in query and 'f32.load offset=108'in query and 'call 15913'in speed_wat and 'i32.const 226'in speed_wat
    frozen=load(RUN/'expected.json');inputs=load(RUN/'inputs.json');actual=[json.loads(x)for x in(RUN/'stdout.jsonl').read_text().splitlines()];assert len(frozen)==len(inputs)==len(actual)==162
    counts=Counter();groups=Counter();speed_events=[];classrace=set();mask_offsets=None
    for c,inp,a in zip(frozen,inputs,actual):
        assert c['id']==inp['id']==a['id']and set(inp)=={'id','input','region_id'}and inp=={k:c[k]for k in('id','input','region_id')}
        i=inp['input'];p,mask,fallback=prediction(i,classes,races,class_data,race_data,zones);assert inp['region_id']==zones[i['region_index']][0]
        assert p==c['expected']['projection']==a['projection']and mask==c['expected']['canonical_cells']
        raw=bytes.fromhex(a['raw_game2592_hex']);assert len(raw)==2592 and a['output_before_hex']=='a5'*2592
        offsets=tuple(j for j,v in enumerate(mask)if v is not None)
        if mask_offsets is None:mask_offsets=offsets
        assert offsets==mask_offsets
        for j,v in enumerate(mask):
            if v is None:counts['unknown_bytes']+=1;counts['observed_nonzero_unknown_bytes']+=raw[j]!=0
            else:assert raw[j]==v,(c['id'],j,v,raw[j]);counts['known_bytes']+=1
        profile=bytes.fromhex(a['profile376_before_hex']);assert a['profile376_before_hex']==a['profile376_after_hex']and len(profile)==376
        expected_profile=bytearray(376);put(expected_profile,156,4);put(expected_profile,168,word(profile,168));put(expected_profile,172,len(inp['region_id'].encode('ascii')))
        struct.pack_into('<QQ',expected_profile,176,int(i['object_id_u64']),int(i['seed_u64']));expected_profile[344]=i['class_byte'];expected_profile[345]=i['race_byte'];assert profile==expected_profile
        assert 0<word(profile,168)<a['ownership']['G']+8192+376+128+4096
        query_bytes=bytearray([0x5a]*128);query_bytes[120]=1;put(query_bytes,116,i['flat_height_bits']);put(query_bytes,56,MASK);put(query_bytes,32,MASK)
        assert query_bytes.hex()==a['query128_before_hex']==a['query128_after_hex']
        own=a['ownership'];assert own['game_query']==own['borrowed_query']==word(raw,2348)and not own['Rc_owner_producer_executed']and not own['App_produced']
        assert a['stack_after']==1048576 and a['host_calls']==0
        assert word(raw,1644)==p['action_sequence1644']and word(raw,1888)==len(p['movement_packets'])
        if p['movement_packets']:
            speed_events.append(dict(id=c['id'],race=i['race_byte'],source_id=i['object_id_u64'],sequence1644=p['action_sequence1644'],speed_bits=p['speed_bits'],opcode=226,payload_hex=p['movement_packets'][0][1]))
        counts['seed_fallback_cases']+=fallback;groups[c['group']]+=1;classrace.add((i['class_byte'],i['race_byte']))
    assert counts['known_bytes']==81324 and counts['unknown_bytes']==338580 and counts['observed_nonzero_unknown_bytes']==23708 and len(mask_offsets)==502 and len(speed_events)==40
    assert counts['seed_fallback_cases']==0 and len(classrace)==72 and dict(groups)==report['groups']
    assert {k:counts[k]for k in('known_bytes','unknown_bytes','observed_nonzero_unknown_bytes')}=={k:report['physical_comparison'][k]for k in('known_bytes','unknown_bytes','observed_nonzero_unknown_bytes')}
    fail=load(FAILED/'comparison.json');assert sha(FAILED/'comparison.json')==FAILED_SHA and(fail['cases'],fail['actual_cases'],fail['differences'])==(151,151,9)
    assert fail['source_sha256_before']==fail['source_sha256_after']
    for n,h in fail['source_sha256_before'].items():assert sha(FAILED/'source-snapshot'/n)==h
    for n,h in fail['artifacts'].items():assert sha(FAILED/n)==h
    failures=load(FAILED/'differences.json');oldcases=load(FAILED/'expected.json');oldactual=[json.loads(x)for x in(FAILED/'stdout.jsonl').read_text().splitlines()]
    assert len(failures)==9 and all(x['field']=='known_Game_byte'and(x['offset'],x['expected'],x['actual'])==(1644,1,2)for x in failures)
    old_known=set();newly_known=set();old_speed_counts=0;expanded_race_inputs=[]
    for oldcase,oldgot,newcase in zip(oldcases,oldactual,frozen[:151],strict=True):
        assert(oldcase['id'],oldcase['region_id'])==(newcase['id'],newcase['region_id'])
        if oldcase['input']!=newcase['input']:
            changed={k for k in oldcase['input']if oldcase['input'][k]!=newcase['input'][k]}
            assert changed=={'race_byte'}and(oldcase['input']['race_byte'],newcase['input']['race_byte'])==(1,4)
            expanded_race_inputs.append(oldcase['id'])
        # Recompute each old input independently; final expanded fixtures may
        # deliberately choose a different race and are not a same-input rerun.
        newprojection,newcells,_=prediction(oldcase['input'],classes,races,class_data,race_data,zones)
        oldprojection=oldcase['expected']['projection']
        assert set(newprojection)-set(oldprojection)=={'action_sequence1644','movement_packets'}
        assert all(v==newprojection[k]for k,v in oldprojection.items())
        oldcells=oldcase['expected']['canonical_cells']
        for offset,(v,w)in enumerate(zip(oldcells,newcells,strict=True)):
            if v is not None:
                assert w is not None and(v==w or offset==1644 and(v,w)==(1,2));old_known.add(offset)
            elif w is not None:newly_known.add(offset)
        old_speed_counts+=word(bytes.fromhex(oldgot['raw_game2592_hex']),1888)
    assert newly_known=={1888,1889,1890,1891}and len(old_known)==498 and old_speed_counts==9 and len(expanded_race_inputs)==20
    for x in failures:
        c=oldcases[x['id']];p,mask,_=prediction(c['input'],classes,races,class_data,race_data,zones);assert c['input']['race_byte']==4 and p['action_sequence1644']==2 and word(bytes.fromhex(oldactual[x['id']]['raw_game2592_hex']),1644)==2
    assert set(n for n in fail['source_sha256_before']if fail['source_sha256_before'][n]!=files[n])=={'reconstruction/core_spec/initial_state138.py','scripts/check_initial138.py','scripts/run_initial138_oracle.mjs'}
    assert runtime==report['runtime']and terminal==report['process']and terminal['exit_code']==0 and terminal['seconds']<terminal['deadline_seconds']==60
    assert terminal['pid_missing']and terminal['pgid_missing']and H.process_missing(terminal['pid'])is True and H.process_missing(terminal['pgid'],True)is True
    for k,v in dict(cases=162,completed_cases=162,full1571_calls=162,fresh_instances=162,actual_host_calls=0,denied_imports=878,peak_memory_bytes=20643840,memory_cap_bytes=33554432,stack_guards=810,initial_stack=1048576).items():assert runtime[k]==v
    for k in('old_snapshot_loaded','App_produced','externref_forged','world_Rc_producer_executed','application_start_called','phase1_started','user_saves_accessed','network_used'):assert not runtime[k]
    validator=load(RUN/'validator-terminal.json');assert validator==manifest['validator']and validator['exit_code']==0 and validator['seconds']<validator['deadline_seconds']==45
    assert validator['pid_missing']and validator['pgid_missing']and H.process_missing(validator['pid'])is True and H.process_missing(validator['pgid'],True)is True
    assert handoff['source_frozen']and handoff['receipt_sha256']==EXPECTED and not handoff['live_handles']and handoff['model_module_sha256']==files['reconstruction/core_spec/initial_state138.py']
    assert all(sha(ROOT/n)==sha(source/n)==h for n,h in files.items())and all(sha(ROOT/n)==h for n,h in reviewers.items())and all(sha(RUN/n)==h for n,h in artifacts.items())
    save(out/'static-proofs.json',dict(functions=functions,reads=read.proofs,classes=class_data,races=race_data,zones=zones,prior_static_data_sha256=STATIC_SHA,Windows_unique8B_patterns=21,native_execution=False))
    result=dict(status='passed_scoped_read_only_initial138_independent_review',version='0.138.0',actual_build='382771e6c',comparison=str(RUN/'comparison.json'),comparison_sha256=EXPECTED,
        cases=162,fresh_original1571_calls=162,new_original_executions=0,production_model_executions=0,checker_executions=0,builder_executions=0,validator_executions=0,
        source_files=21,production_files=10,source_hashes=files,local_source_edges=edges,reviewer_source_sha256=reviewers,artifacts_sha256=artifacts,
        counts=dict(counts),groups=dict(groups),class_race_pairs=72,known_Game_byte_offsets=list(mask_offsets),known_bytes_per_Game=502,complete226_packets=speed_events,
        speed_changed_cases=40,speed_unchanged_cases=122,sequence1644_values=[1,2],PCG_fallback_dynamic_cases=0,PCG_fallback_static_only=True,
        failure151=dict(comparison_sha256=FAILED_SHA,failures=failures,retained=True,not_added_to162=True,all_old_sources_and_artifacts_rehashed=True,
            no_old_known_field_dropped=True,old_known_bytes_perGame=498,new_known_queue1888_bytes=sorted(newly_known),old_observed_queue_entries_without_payloads=old_speed_counts,
            final_expanded_race_input_ids=expanded_race_inputs,old_inputs_recomputed_independently_not_assumed_equal_final=True,
            source_changes=['initial_state138.py','check_initial138.py','run_initial138_oracle.mjs']),
        static_proofs_sha256=sha(out/'static-proofs.json'),original_process=terminal,validator_process=validator,
        full880_frames=0,native_executions=0,complete_games=0,old135_cases_transferred=0,
        limitations=['EmptyselectedProfile376 andborrowedflatquery128 are explicit componentinputs,not natural account/App/profile producers.',
            'Only502 known bytes per2592Game; unknown338580cells preserved,heap pointers and BTree/owned backing physical producers remainunknown.',
            'Logical BTree fields,full80B records and40complete226payloads captured; rawphysicaltree/packetmetadata backing is not exported for independent reread.',
            'No Rc owner/cache6760 bootstrap,opening1087/phase1,continuous138flow,network/native orcompletegame acceptance.',
            'PCG ordinary seed branch exercised162; fallback branch restored statically only.',
            'Shared low-level reviewer WASM/static readers reused; empty-profile numeric projection independently rebuilt without production or older expected results.'],seconds=time.monotonic()-began)
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),speed_packets=len(speed_events))),flush=True)

if __name__=='__main__':main()
