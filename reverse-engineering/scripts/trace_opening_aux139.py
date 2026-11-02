#!/usr/bin/env python3
"""Whole current1391108/callee boundaries and auxiliary static declarations."""
from collections import Counter
import hashlib,json,re,sqlite3,struct
from incoming139_tools import ROOT,PROFILE,SOURCE_SHA,original,static_reader,function_proof,save,sha

INDICES=(1108,6786,2945,1795,13563,1446,1886,18062,27165,10804,51773,20752,10099,4562,83304,8611,32605,1600)
def trace(out):
    raw,identity,ranges=original();read=static_reader(raw,identity);proof,text=function_proof(raw,identity,ranges,INDICES,out)
    assert proof[1108]['body_sha256']=='dee71e4ff450ac47056dff085773678b6ec5e5bcc82b24884097c7519b44ed92'
    calls=Counter(map(int,re.findall(r'\bcall (\d+)',text[1108])))
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.execute('pragma query_only=on');assert dict(db.execute('select callee,count(*)from calls where caller=1108 group by callee'))==dict(calls)
    boundaries=[];lines=text[1108].splitlines()
    for name,lo,hi,status in(
        ('phase1_and_real_Spell_DBC4562',1,14,'explicit resource-context precondition;4562 is not locale'),
        ('protection_debug_abilities_and_bosses',15,1221,'default2576=0 skipped;nondefault unknown'),
        ('localized_start_packet150',1222,1417,'18062 resolved-string component being recovered'),
        ('selected_rank_gate',1418,1724,'default387=0 skip;nondefault unknown'),
        ('startJSON_and_10099',1725,1889,'default startJSON;remaining10099 field publication separately bound'),
        ('protection_extra_effects',1890,2515,'default2576=0 skip;nondefault unknown'),
        ('companion1795',2516,2520,'2945 absent tags255 component;nonempty slots unknown'),
        ('four_natural_NPC5719',2521,2556,'owned by separate current139 naturalNPC component'),
        ('two_random_kind2_pickups',2557,2621,'13563 position v2 dependency;1446 record/actor producer pending'),
        ('event_windows2or3',2622,2929,'independent RNG/window producer pending'),
        ('special40_declarations',2930,4320,'current72B definition table and nav/world consumers pending'),
        ('boundary_objects',4321,4879,'circle and actor1886 current139 producer pending'),
        ('optional_rank_and_active_events',4880,5584,'default2577=0 and2140=0 skips;nonempty event scripts unknown')):
        block='\n'.join(lines[lo-1:hi]);boundaries.append(dict(name=name,first_line=lo,last_line=hi,sha256=hashlib.sha256(block.encode()).hexdigest(),status=status))
    assert [i for i,line in enumerate(lines,1)if line.strip()=='call 5719']==[2532,2540,2548,2556]
    assert 'call 13563'in lines[2606]and'call 1446'in lines[2611]
    selection=[s.strip()for s in text[2945].splitlines()];rebind=next(i for i,s in enumerate(selection)if s=='local.tee 0');stores=[]
    for i,s in enumerate(selection[:rebind]):
        if s!='local.get 0':continue
        j=next(j for j in range(i+1,min(i+9,rebind))if selection[j].startswith(('i32.store','f32.store')));instruction=selection[j]
        offset=int(re.search(r'offset=(\d+)',instruction)[1])if'offset='in instruction else 0;width=1 if instruction.startswith('i32.store8')else 4;stores.append(dict(line=j+1,offset=offset,width=width,instruction=instruction))
    written={j for row in stores for j in range(row['offset'],row['offset']+row['width'])};assert len(stores)==12 and len(written)==30 and max(written)==35
    zone=read(5871348,152);w=struct.unpack('<38I',zone);identifier=read(w[2],w[3]).decode();name=read(w[4],w[5]).decode();subtitle=read(w[6],w[7]).decode();normal=read(w[16],w[17]*72);eligible=[]
    for i in range(w[17]):
        row=normal[72*i:72*(i+1)];duration=struct.unpack_from('<I',row,64)[0]
        if row[68]==1 and duration&0x7fffffff<0x7f800000:eligible.append(struct.unpack_from('<I',row,24)[0])
    boss=read(w[18],w[19]*72);assert w[17]==12 and w[19]==5;window=struct.unpack('<2I',read(1593828,8));assert window==(2,3)
    jptr,jlen=struct.unpack('<2I',read(5401532,8));english_raw=read(jptr,jlen);english=json.loads(english_raw);template=read(1593372,37).decode();title=english.get('zone.'+identifier+'.name',name);subtitle=english.get('zone.'+identifier+'.subtitle',subtitle);rendered=english.get(template,template).replace('{subtitle}',subtitle)
    assert identifier=='elwynn'and eligible==[609,610,611]and struct.unpack_from('<I',boss,336)[0]==0x41800000
    assert struct.unpack('<3I',read(1590744,12))==(9013,4831,0x3f800000)
    seed_lines=text[6786].splitlines();seed_window='\n'.join(seed_lines[294:307]);assert all(t in seed_window for t in('i64.load offset=4928','i64.const 6364136223846793005','i64.const 1442695040888963407','i64.store offset=4928'))
    result=dict(version='0.139.0',actual_build='f79c5e2b4',source_sha256=SOURCE_SHA,functions=proof,whole1108_boundaries=boundaries,direct1108_calls=dict(sorted(calls.items())),default_selected_account_sources=dict(attributes12_count=196,flags16_count=244,identifiers4_count=256,bytes_count=268),selection2945=dict(required_output_bytes=36,written_bytes=30,written_stores=stores,untouched_within36=sorted(set(range(36))-written),prefix16_copied_to_selected376_offset224=True),seed6786=dict(app_offset=4928,multiplier=6364136223846793005,increment=1442695040888963407,constructor_selectedP_offset=184,window=seed_window),zone0=dict(pointer=5871348,raw152_hex=zone.hex(),identifier=identifier,center_xy_bits=list(w[26:28]),heading_bits=w[29],radius_bits=w[30],fallback_bits=w[28],boundary_flag148=zone[148],normal72_pointer=w[16],normal_count=w[17],normal72_sha256=hashlib.sha256(normal).hexdigest(),eliteIDs=eligible,boss72_pointer=w[18],boss_count=w[19],boss72_sha256=hashlib.sha256(boss).hexdigest(),last_boss_minutes_bits=struct.unpack_from('<I',boss,336)[0],window_count_range=list(window),boundary_descriptor=[9013,4831,0x3f800000],kind2_descriptor=[9005,259,0x3f800000]),English=dict(embedded_bytes=jlen,embedded_sha256=hashlib.sha256(english_raw).hexdigest(),title=title,subtitle=rendered,source_subtitle=subtitle,template=template),source_read_proofs=read.proof,trace_sha256=sha(__file__),original_executed=False,old_acceptance_transferred=False,limitations=['This is complete1108 static/callee coverage,not complete behavior acceptance.','Position13563 v1 is not used;current v2 math must be separately admitted.','No snapshot/original output supplied these static declarations.','NaturalApp/account/profile/resource initialization remains explicit;empty2945 counts must be provided rather than guessed.'])
    save(out/'trace.json',result);return result
