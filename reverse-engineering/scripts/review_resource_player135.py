#!/usr/bin/env python3
"""Independent read-only full2088 resource prefix review; no target/model runs."""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_resource_consumer135 as component
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
from review_resource_consumer137 import source_edges,identities

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/resource-player0135-oracle-20261101T214934.226082Z'
ORIGINAL=ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
F,B,add,sub,mul=component.F,component.B,component.add,component.sub,component.mul
u,put=component.u,component.put

def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def load(path):return json.loads(Path(path).read_text())
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def minnum(a,b):
    if math.isnan(F(a)):return b
    if math.isnan(F(b)):return a
    return a if F(a)<F(b)else b
def positive(value):return value if F(value)>0 else 0
def ceil_u32(value):return min(0xffffffff,max(0,math.ceil(F(value))))

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
        kind,spell=u(row,8),u(row,20);assert kind in(0,8)
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
    return{str(k):value for k,value in result.items()}

def aura_events(previous,initialized,current):
    def spell(row):return u(row,4)if u(row)else 0
    def flags(rows,group):return sum((9 if i<32 else 8)<<(4*(i%8))for i in range(group*8,group*8+8)if u(rows[i])==1)
    def stacks(rows,group):return sum((min(u(rows[i],12),255)-1)<<(8*(i%4))for i in range(group*4,group*4+4)if u(rows[i])==1 and u(rows[i],12)>0)
    valid=len(previous)==48 and bool(initialized&1);events=[]
    for i,row in enumerate(current):
        value=spell(row)
        if not valid or value!=spell(previous[i]):events.append(['aura_field_write',47+i,value])
    for group in range(6):
        value=flags(current,group)
        if not valid or value!=flags(previous,group):events.append(['aura_field_write',95+group,value])
    for group in range(12):
        value=stacks(current,group)
        if not valid or value!=stacks(previous,group):events.append(['aura_field_write',113+group,value])
    return events

def closure(edges):
    todo=['reconstruction/core_spec/resource_player_update135.py'];seen=set()
    while todo:
        name=todo.pop()
        if name in seen:continue
        seen.add(name);todo.extend(b for a,b in edges if a==name and b.startswith('reconstruction/'))
    return sorted(seen)

def raw_binding(raw,runtime,case):
    game=bytes.fromhex(raw['raw_game8192_hex']);assert len(game)==8192
    read=lambda offset:struct.unpack_from('<I',game,offset)[0]
    q=raw['known']
    assert q['derived_bits']=={str(o):read(o)for o in range(1536,1628,4)}
    for key,offset in(('current_hp_bits',1440),('speed_bits',1648),('counter2408',2408),('message_sequence2412',2412),('action_sequence1644',1644)):
        assert q[key]==read(offset)
    assert q['auxiliary_bits']=={str(o):read(o)for o in(1444,1448,1348,768,756)}
    assert q['rng_words']==list(struct.unpack_from('<4I',game,1720))and q['player_fields']==raw['raw_keyed_fields']
    assert game[360]==case['state']['stats']['class_byte']and game[361]==case['state']['stats']['race_byte']
    assert game[2587]==1 and game[387]==case['state']['heal_gate387']
    assert game[1256:1336].hex()==case['basic_hex']and read(1628)==0x7f800000
    assert struct.unpack_from('<3I',game,1656)==(0,4,0)
    for name,offset,stride in(('live',1704,32),('pickups',1868,56),('aura',2000,16)):
        cap,pointer,count=struct.unpack_from('<3I',game,offset);v=q[name]
        assert(v['capacity'],v['count'])==(cap,count)and count<=cap<=4096
        assert len(v['storage'])==cap and pointer+cap*stride<=runtime['max_memory_bytes']
        assert all(len(bytes.fromhex(row))==stride for row in v['storage'])
    assert q['aura']['initialized2569']==game[2569]
    a=raw['raw_aura16'];assert(a['capacity'],a['count'])==(q['aura']['capacity'],q['aura']['count'])
    assert a['storage_hex']==''.join(q['aura']['storage'])
    for name,offset,stride in(('raw_packets',1880,16),('raw_notifications',1892,12)):
        cap,pointer,count=struct.unpack_from('<3I',game,offset);queue=raw[name]
        assert(queue['capacity'],queue['count'])==(cap,count)and count<=cap<=512 and pointer+count*stride<=runtime['max_memory_bytes']
        metadata=bytes.fromhex(queue['raw_hex']);assert len(metadata)==count*stride and len(queue['active'])==count
        for i,item in enumerate(queue['active']):
            capacity,body,length=struct.unpack_from('<3I',metadata,stride*i)
            assert length<=capacity<=1048576 and body+length<=runtime['max_memory_bytes']and len(bytes.fromhex(item['payload_hex']))==length
            if name=='raw_packets':assert item['opcode']==struct.unpack_from('<H',metadata,stride*i+12)[0]
    assert q['packets_known']==[x for x in raw['raw_packets']['active']if x['opcode']==226]
    assert q['notifications_hex']==[x['payload_hex']for x in raw['raw_notifications']['active']]
    assert q['destroy170_hex']==[x['payload_hex']for x in raw['raw_packets']['active']if x['opcode']==170]
    return game

def review_case(case,wanted,actual,label,read,runtime,counts,sem,witnesses):
    assert case['id']==wanted['id']==actual['id']==label['id']
    state=case['state'];t=state['stats'];initial=case['level_input']
    assert t['level']==initial['progression']['level']==1 and t['flag2574']==0
    assert state['aura_external_sources_absent']and state['locale_code']=='en'
    assert all(not t[k]for k in('passives','adjustments','item_modifiers','owned_skills','timed_records','timed_definitions'))
    assert all(not initial['sources'][k]for k in('passives','adjustments','item_modifiers','owned_skills','timed_records','definitions'))
    assert t['conditional1344_id']==t['conditional1348_bits']==t['conditional268_bits']==t['pool768_bits']==0
    assert initial['phase2587']==1 and not initial['choice_inputs']['owned']
    for key,value in initial['stats'].items():assert t[key]==value
    assert initial['sources']['live_effects']==t['live_effects']
    live=[list(row)for row in state['live']['storage']];count=state['live']['count']
    derived={str(k):v for k,v in state['derived_bits']}
    assert derived==initial['derived_bits']==stats1512(t,live,count,t['now_bits'],read)
    fields={str(k):v for k,v in state['player_fields']};assert fields==initial['player_fields']
    hp=t['current_hp_bits'];speed=t['previous_speed_bits'];shield=t['pool1532_bits'];barrier=t['pool1536_bits']
    aura=[list(row)for row in state['aura']['storage']];initialized=state['aura']['initialized2569']
    sequence=state['action_sequence1644'];wire=[];previous_raw_aura=None
    assert len(case['operations'])==len(wanted['stages'])==len(actual['stages'])==len(label['operations'])
    for index,(op,want,raw,meta)in enumerate(zip(case['operations'],wanted['stages'],actual['stages'],label['operations'])):
        now,dt,last=op['now_bits'],op['dt_bits'],op['last_hit_bits']
        assert all(math.isfinite(F(v))for v in(now,dt,last))
        old_live=[row.copy()for row in live];old_count=count
        expired=[u(row,20)for row in live[:count]if F(now)>=F(u(row,24))]
        events=[];recalculated=bool(expired)
        if expired:
            write=0
            for i in range(count):
                if F(now)<F(u(live[i],24)):
                    if write!=i:live[write]=live[i].copy()
                    write+=1
                elif math.isnan(F(u(live[i],24))):sem['NaN_rows_removed_only_by_dirty_retain']+=1
            count=write
            derived=stats1512(t,live,count,now,read)
            hp=minnum(hp,derived['1536']);fields.update({'22':ceil_u32(hp),'28':ceil_u32(derived['1536']),'1109':mul(derived['1548'],B(100))})
            new_speed=mul(derived['1556'],B(7))
            if F(sub(new_speed,speed)&0x7fffffff)>F(0x3c23d70a):
                speed=new_speed;wire.append(dict(opcode=226,payload_hex=(component.packed(state['player_guid'])+struct.pack('<II',sequence,speed)).hex()))
                sequence=(sequence+1)&0xffffffff;sem['new_speed226']+=1
                if sequence==0:sem['action_sequence_wraps']+=1
            old_aura,old_initialized=aura,initialized
            aura,initialized=component.reference_aura(live,count,now,aura,initialized,fields,sem)
            events.extend([['expire_live',expired],['recalculate1512']])
            events.extend(aura_events(old_aura,old_initialized,aura))
            sem['dirty_recalculations']+=1;sem['expired_spell_observations']+=len(expired)
            if live!=old_live:sem['stable_full32_compaction_stages']+=1
        else:
            assert live==old_live and count==old_count
            sem['no_dirty_stages']+=1
            if any(math.isnan(F(u(row,24)))for row in live[:count]):sem['NaN_no_dirty_retained_stages']+=1
        barrier=minnum(shield,barrier)
        half=B(.5)if state['heal_gate387']>4 else B(1)
        elapsed=sub(now,last);extra=mul(derived['1536'],derived['1620'])if F(elapsed)>=3 else 0
        regen=mul(half,mul(dt,add(derived['1576'],extra)))
        old_hp=hp
        if F(hp)<F(derived['1536']):
            hp=minnum(derived['1536'],add(0,add(hp,regen)))
            fields.update({'22':ceil_u32(hp),'28':ceil_u32(derived['1536'])});events.append(['regen_keys22_28']);sem['regen_hp_key_writes']+=1
        delta=positive(sub(hp,old_hp));request=minnum(delta,regen)
        events.append(['healaccount1453_pending',request])
        assert meta['expired_spell_ids']==expired and meta['recalculated']==recalculated
        assert(meta['regen_request_bits'],meta['heal_delta_bits'])==(regen,delta)
        assert meta['events']==events
        sem['negative_dt_stages']+=F(dt)<0;sem['zero_dt_stages']+=F(dt)==0
        sem['half_heal_gate_stages']+=state['heal_gate387']>4
        sem['three_second_elapsed_ge_stages']+=F(elapsed)>=3
        sem['nonzero_extra_regen_stages']+=extra!=0
        prediction=dict(aura=dict(capacity=len(aura),count=len(aura),storage=aura,initialized2569=initialized),
            packets_known=wire,notifications_hex=[],notification_next_id14340336=1,
            live=dict(capacity=len(live),count=count,storage=live),pickups=dict(capacity=0,count=0,storage=[]),destroy170_hex=[],
            derived_bits=derived,current_hp_bits=hp,speed_bits=speed,
            auxiliary_bits={'1444':shield,'1448':barrier,'1348':0,'768':0,'756':0},player_fields=fields,
            rng_words=state['rng_words'],counter2408=85,message_sequence2412=123,action_sequence1644=sequence)
        assert prediction==want,(case['id'],index,[(key,prediction[key],want[key])for key in prediction if prediction[key]!=want[key]][:1])
        raw_binding(raw,runtime,case)
        observed=dict(raw['known'])
        for name in('live','aura','pickups'):observed[name]={**observed[name],'storage':[list(bytes.fromhex(row))for row in observed[name]['storage']]}
        component.strict(want,observed,(),counts)
        for wanted_row,actual_row in zip(want['live']['storage'],observed['live']['storage']):
            for known,byte in zip(wanted_row,actual_row):
                if known is None:assert byte==case['unknown_poison'];sem['live_None_poison_preservation_bytes']+=1
        if not recalculated and previous_raw_aura is not None:
            assert raw['known']['aura']==previous_raw_aura;sem['no_dirty_full_raw_Aura_backing_preservations']+=1
        if not recalculated and index==0:
            assert observed['aura']['storage']==[[case['unknown_poison']if v is None else v for v in row]for row in state['aura']['storage']]
            sem['initial_no_dirty_Aura_input_bytes_preserved']+=1
        previous_raw_aura=raw['known']['aura']
        counts['stages']+=1;counts['raw_packet_observations']+=raw['raw_packets']['count']
        sem['all_raw_non226_packet_observations']+=sum(p['opcode']!=226 for p in raw['raw_packets']['active'])
        locale=struct.unpack('<7I',bytes.fromhex(raw['locale_state_hex']));assert locale[6]==3
        if label['group']in('NaN-alone-no-dirty','NaN-co-remove','NaN-kind8-co-remove','pool-min-no-dirty','226-action-wrap','last-hit-three-second'):
            witnesses.append(dict(case_id=case['id'],group=label['group'],stage=index,now_bits=now,dt_bits=dt,last_hit_bits=last,
                expired=expired,retained=count,recalculated=recalculated,regen_request_bits=regen,heal_delta_bits=delta,
                current_hp_bits=hp,speed_bits=speed,action_sequence1644=sequence,extra1620_bits=derived['1620'],barrier1448_bits=barrier))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    out=args.output.resolve();out.mkdir();began=time.monotonic();report=load(RUN/'comparison.json')
    reviewer_files=['scripts/review_resource_player135.py','scripts/review_resource_consumer135.py','scripts/review_opening_combat135.py','scripts/review_combat137.py','scripts/review_battle_shout135.py','scripts/review_resource_consumer137.py']
    reviewer_sources={name:sha(ROOT/name)for name in reviewer_files}
    for name,digest in reviewer_sources.items():
        target=out/'reviewer-source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes());assert sha(target)==digest
    assert sha(RUN/'comparison.json')=='82719c31ea3de180d1a4b0c036d1a6764bd1518f3a1cdea17e3a627b6d85024d'
    assert report['comparison_complete']and report['differences']==0 and(report['cases'],report['operations'])==(38,56)
    assert report['source_sha256_before']==report['source_sha256_after']and report['source_files']==37
    sources=report['source_sha256_before'];frozen=RUN/'source-snapshot'
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(frozen/name),name
    edges=source_edges(frozen,list(sources));assert edges==report['local_source_import_edges']and len(edges)==124
    production=sorted(name for name in sources if name.startswith('reconstruction/'));assert production==closure(edges)and len(production)==30
    for name in production:
        for node in ast.walk(ast.parse((frozen/name).read_text())):
            if isinstance(node,ast.Call):
                fun=node.func;called=fun.id if isinstance(fun,ast.Name)else fun.attr if isinstance(fun,ast.Attribute)else''
                assert called not in('open','read_bytes','read_text','write_bytes','write_text','Popen','exec','eval','__import__')
    prepared=load(RUN/'prepared.json');assert prepared['source_sha256']==sources and prepared['expected_before_original']and prepared['deadline_seconds']==60
    assert prepared['artifacts']==report['frozen_artifacts']
    for name,digest in prepared['artifacts'].items():assert sha(RUN/name)==digest,name
    checker=(frozen/'scripts/check_resource_player135.py').read_text();assert checker.index('rows,expected,labels=corpus(')<checker.index('child=subprocess.Popen(')
    original=ORIGINAL.read_bytes();manifest=load(RUN/'manifest.json');module=(RUN/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==manifest['original_sha256']==report['original_sha256']=='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
    assert hashlib.sha256(module).hexdigest()==manifest['module_sha256']
    before,after=sections(original),sections(module);assert[x[0]for x in before]==[x[0]for x in after]and 8 not in[x[0]for x in before]
    assert all(original[a:b]==module[c:d]for(k,a,_,b),(_,c,_,d)in zip(before,after)if k!=7)
    assert exports(module)==exports(original)+[['research135_resource_player2088',0,2088],['research135_resource_player_stack0',3,0]]
    functions=identities(original,[row['idx']for row in manifest['functions']]);static=[];texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        db.execute('pragma query_only=on')
        for item in manifest['functions']:
            idx=item['idx'];lo,hi,bs,be=db.execute('select wat_start,wat_end,body_start,body_end from functions where idx=?',(idx,)).fetchone()
            assert(bs,be)==(functions[idx]['body_start'],functions[idx]['body_end'])and functions[idx]['body_sha256']==item['body_sha256']and hi-lo<524288
            stream.seek(lo);raw=stream.read(hi-lo);assert raw==(RUN/(str(idx)+'.wat')).read_bytes()and hashlib.sha256(raw).hexdigest()==item['WAT_sha256']
            texts[idx]=raw.decode();static.append(dict(**functions[idx],wat_start=lo,wat_end=hi,wat_sha256=item['WAT_sha256']))
    assert functions[2088]['signature']==['7f7d','']
    assert texts[2088].index('call 1512')<texts[2088].index('call 1202')<texts[2088].index('call 1453')<texts[2088].index('call 1076')
    assert 'f32.load offset=24\n                  local.get 47\n                  f32.le'in texts[1512]
    assert 'f32.load offset=1576'in texts[2088]and'f32.load offset=1620'in texts[2088]and'f32.load offset=1652'in texts[2088]
    read=static_reader(original);assert read(manifest['default_ability_pointer'],88).hex()==manifest['default_ability88_hex']and manifest['default_ability_pointer']==5467428
    assert read(14340336,4)==b'\1\0\0\0'
    del original,module
    rows=load(RUN/'input.json');expected=load(RUN/'expected.json');actual=[json.loads(line)for line in(RUN/'stdout.jsonl').read_text().splitlines()];labels=load(RUN/'labels.json')
    assert len(rows)==len(expected)==len(actual)==len(labels)==38
    runtime=load(RUN/'resource-player135-runtime.json');assert runtime==report['runtime']
    counts=Counter();sem=Counter();witnesses=[]
    for case,want,raw,label in zip(rows,expected,actual,labels):
        review_case(case,want,raw,label,read,runtime,counts,sem,witnesses)
    assert counts['stages']==56 and counts['known_values']==23309 and counts['explicit_unknown_physical_bytes']==30416 and counts['raw_packet_observations']==47
    assert counts['known_values']==report['comparison']['known_values']and counts['explicit_unknown_physical_bytes']==report['comparison']['unknown_physical_bytes']
    assert runtime['cases']==runtime['completed_cases']==runtime['fresh_instances']==38 and runtime['full_original_calls']=={'2088':56}
    assert runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['max_memory_bytes']<=runtime['memory_cap_bytes']==33554432 and runtime['error']is None
    assert len(runtime['stack_checks'])==221 and all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
    assert runtime['stack_all_restored']and all(not runtime[key]for key in('application_start_called','full_game_started','network_used','user_saves_accessed','original_memory_snapshot_read','once_or_locale_state_injected'))
    assert len(runtime['locales'])==38 and all(x['first_call_bootstrap_untouched']and bytes.fromhex(x['before_hex'])==bytes(28)and struct.unpack_from('<I',bytes.fromhex(x['after_hex']),24)[0]==3 for x in runtime['locales'])
    terminal=load(RUN/'process-terminal.json');assert terminal==report['process']and terminal['exit_code']==0 and terminal['error']is None and terminal['seconds']<60 and missing(terminal['pid'])and missing(terminal['pgid'],True)
    assert sha(Path(prepared['command'][0]))=='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
    assert '--wasm-max-mem-pages=512'in prepared['command']and'--max-old-space-size=512'in prepared['command']
    assert(RUN/'stdout.jsonl').stat().st_size==runtime['output_bytes']<=4194304 and max(map(len,(RUN/'stdout.jsonl').read_bytes().splitlines(keepends=True)))<=2097152
    assert(RUN/'stderr.log').stat().st_size==0 and load(RUN/'differences.json')==[]and len(load(RUN/'refusals.json'))==7
    production_text=(frozen/'reconstruction/core_spec/resource_player_update135.py').read_text()
    assert production_text.index('if kind==0:')<production_text.index('elif kind==8:')<production_text.index("magnitude=u32(row,12")
    assert production_text.index("events.extend((('expire_live',expired),('recalculate1512',),*aura.events))")<production_text.index("events.append(('healaccount1453_pending'")
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(frozen/name),name
    save(out/'static-proofs.json',dict(functions=static,original_static_reads=read.proofs,local_source_import_edges=edges,
        kind0_magnitude='No auditor magnitude read for kind0; typed source uses separate kind8 branch, and all live None bytes retain A5/5A poison.',
        execution_order='Unchanged2088:1512→1202 then pool clamp/regen→1453→1076; actual owned/basic/prelude effects isolated by empty learned/infinity controls.'))
    for name,digest in reviewer_sources.items():assert sha(ROOT/name)==digest==sha(out/'reviewer-source-snapshot'/name)
    result=dict(status='passed_scoped_read_only_review',version='0.135.1',actual_build='90898d5e3',comparison=str(RUN/'comparison.json'),comparison_sha256=sha(RUN/'comparison.json'),
        cases=38,stages=56,source_files=37,production_files=30,local_source_import_edges=124,current_and_frozen_sources_verified=True,source_sha256=sources,
        comparison_counts=dict(counts),independent_semantic_checks=dict(sem),witnesses=witnesses,
        nonexport_sections_identical=True,full_original2088_and_callees_preserved=True,known_full32_and48Aura_recompared=True,
        all_live_None_bytes_preserved_as_input_poison=True,kind0_magnitude_not_read=True,all23_derived_stats_and_keyed_fields_independently_recomputed=True,
        raw_Game_header_and_queue_metadata_rebound=True,exact226_payloads_and_action_wrap_independently_checked=True,
        unmodeled_non226_packets_observed_only=True,locale_once_initialized_naturally=True,original_terminal=terminal,stack_checks=221,
        new_original_executions=0,new_original_cases=0,original_model_or_checker_executed_by_reviewer=False,
        static_proofs_sha256=sha(out/'static-proofs.json'),reviewer_sources=reviewer_sources,
        artifact_sha256={p.name:sha(p)for p in RUN.iterdir()if p.is_file()},pure_model_refusals_observed_not_rerun=7,
        full880_frames=0,complete_games=0,native_executions=0,
        limitations=['Manual Game8192/World128 and BTree/source owners; no full original constructor or historical memory snapshot.',
        'Complete original2088 invokes1076, but learned is empty and actual cleave80/basic and class-prelude timers stayInfinity; independent prefix does not execute1076.',
        'Kind0 resource23451/23505 and finite positive unique kind8 only; other live/periodic/shield/proc/aura families pending.',
        'All tested derived1620 values are0; last-hit3s numerical nonzero extra-regeneration path is not validated.',
        '1453 account/presentation/statistics and all non226 wire semantics are raw observations, not independent predictions.',
        'Fresh component cases are not natural resource pickup in750 or complete gameplay.'],elapsed_seconds=time.monotonic()-began)
    assert result['elapsed_seconds']<60
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],counts=dict(counts),semantics=dict(sem))),flush=True)

if __name__=='__main__':main()
