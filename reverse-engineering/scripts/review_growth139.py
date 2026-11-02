#!/usr/bin/env python3
"""Read-only different-author139 first gain/choice/select reference.

No author production, checker, builder or original function is executed.
Independent reference helpers are frozen and rebound to current139 bodies.
"""
from collections import Counter
from pathlib import Path
import ast,copy,hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_combat139 import parse_module,local_closure,sha,bits,fp,f32
from review_initial139 import reference as constructor_reference
from review_stats139 import reference as stats_reference

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/growth139-oracle-20261102T060448.902434Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
COMP='bd70df451612fce78bd0e8074a9c975acaf790e037caecc02c9fd8052bab8169'
HAND='02f36fb96bddbc71a4a093bc10325a8458dd4dd1f67bf618dcee8ebfb9fc6d59'
WASM='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={'scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
 'scripts/review_initial139.py':'86d33e69c361eef223ad3ef271b6fb987d170f4d94847c0c068148c56ebe6fbc',
 'scripts/review_stats139.py':'175667eded3461b118ddc2b7e47ee29517434b0bee7dfe77d4e388a9cc327473'}
load=lambda p:json.loads(Path(p).read_text())
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
q=lambda b,o=0:struct.unpack_from('<Q',b,o)[0]
add=lambda a,b:bits(f32(fp(a)+fp(b)))
sub=lambda a,b:bits(f32(fp(a)-fp(b)))
mul=lambda a,b:bits(f32(fp(a)*fp(b)))


class Sampler:
    def __init__(self,words):self.words=tuple(words);self.draws=0
    def word(self):
        a,b,c,d=self.words;rol=lambda x,n:((x<<n)|(x>>(32-n)))&0xffffffff
        self.words=(a^b^d,a^b^c,(a^c^(b<<9))&0xffffffff,rol(b^d,11));self.draws+=1
        return(rol((a+d)&0xffffffff,7)+a)&0xffffffff
    def uniform(self,high):
        for _ in range(10000):
            value=mul(sub((self.word()>>9)|0x3f800000,0x3f800000),high)
            if fp(value)<fp(high):return value
        raise AssertionError('Independent bounded draw watchdog')
    def shuffle(self,items):
        for n in range(len(items),1,-1):
            zone=((n<<(32-n.bit_length()))-1)&0xffffffff
            for _ in range(10000):
                product=self.word()*n
                if product&0xffffffff<=zone:break
            else:raise AssertionError('Independent shuffle watchdog')
            j=product>>32;items[n-1],items[j]=items[j],items[n-1]


def candidates(words,kit,level):
    random=Sampler(words);pool=[(0x3fcccccd,name,False)for name in kit if name!='cleave']+[(0x3fa66666,'cleave',True)]
    selected=[]
    for _ in range(3):
        total=0x80000000
        for weight,_,_ in pool:total=add(total,weight)
        remainder=random.uniform(total);index=len(pool)-1
        for j,(weight,_,_)in enumerate(pool):
            if fp(remainder)<fp(weight):index=j;break
            remainder=sub(remainder,weight)
        selected.append(pool.pop(index))
    factor=add(0x3f800000,min(mul(bits(float(level)),0x3c23d70a),0x3e99999a));square=mul(factor,factor)
    weights=[0x42700000,mul(factor,0x41c80000),mul(square,0x41200000),mul(mul(factor,square),0x40800000),mul(square,square)]
    total=weights[0]
    for weight in weights[1:]:total=add(total,weight)
    result=[]
    for _,name,upgrade in selected:
        remainder=random.uniform(total);tier=0
        for j,weight in enumerate(weights):
            if fp(remainder)<fp(weight):tier=j;break
            remainder=sub(remainder,weight)
        kinds=[]
        if upgrade:
            kinds=[0,1]if tier==0 else[0,1,2];random.shuffle(kinds);kinds=kinds[:2 if tier==4 else 1]
        result.append(dict(variant='upgrade'if upgrade else'new',tier=tier,ability_id=name,owned_index=0,kinds=kinds,gold=0))
    return result,list(random.words),random.draws


def threshold(level):
    n=bits(float(max(0,level-1)));value=add(add(mul(n,0x40800000),0x40a00000),mul(mul(n,0x3eb33333),n))
    shifted=add(value,0x3effffff|(value&0x80000000));e=(shifted>>23)&255
    if e<=149:shifted&=0x80000000 if e<127 else((-0x800000>>(e-127))&0xffffffff)
    return max(0,min(0xffffffff,int(fp(shifted))))


def recalculate(state,classes,races):
    s=dict(class_byte=1,race_byte=1,level=state['level'],passives=[],adjustments=[],item_modifiers=[],owned_skills=[],timed_records=[],timed_definitions=[],live_effects=[],now_bits=0,old_max_hp_bits=state['derived_bits']['1536'],current_hp_bits=state['current_hp_bits'],conditional268_bits=0,flag2574=0,pool1532_bits=0,pool1536_bits=0,conditional1344_id=0,conditional1348_bits=0,pool768_bits=0,previous_speed_bits=0x40e00000)
    answer=stats_reference(s,{1:classes[1]['hp_armor']},{1:races[1]['modifiers']},Counter());state['derived_bits']=answer['derived_bits'];state['current_hp_bits']=answer['current_hp_bits'];state['player_fields'].update(answer['object_fields'])


def selected_record(name,tier,definitions,cooldown,damage):
    pointer,definition,kinds=definitions[name];words=[0]*20
    for i in(1,3,4,6,7,13,14,16,17,19):words[i]=0x3f800000
    words[:3]=[pointer,1,0x3f000000]
    if tier:
        execution=definition[84];effect=u(definition)
        offensive=bool(0 in kinds)if execution==11 else bool(effect<=13 and (1<<effect)&8384)if execution==9 else fp(u(definition,48))>0
        offset=3 if offensive else 4;factor=add(damage[tier-1],0x3f800000)if offensive else sub(0x3f800000,cooldown[tier-1]);words[offset]=mul(words[offset],factor)
    return struct.pack('<20I',*words).hex()


def reference(case,classes,races,zones,kit,definitions,cooldown,damage):
    initial,known=constructor_reference(dict(class_byte=1,race_byte=1,region_index=0,seed_u64=case['seed_u64'],object_id_u64='0',flat_height_bits=1116212265),classes,races,zones)
    before=dict(level=1,xp=0,pending=0,phase2587=1,current_hp_bits=initial['current_hp_bits'],derived_bits=initial['derived_bits'],player_fields=initial['player_fields'],rng_words=initial['rng_words'],candidates=[],selection_kind2585=255,generation_counter2400=0,owned_records80_hex=initial['owned_records_hex'],flag2581=0,flags2573=0)
    state=copy.deepcopy(before);state['xp']=case['amount'];events=[]
    while state['level']<=119 and state['xp']>=threshold(state['level']):
        old=state['level'];spent=threshold(old);state['xp']-=spent;state['pending']+=1;state['level']+=1;recalculate(state,classes,races)
        fields=state['player_fields'];fields['34']=state['level'];request=mul(state['derived_bits']['1536'],0x3e4ccccd);oldhp=state['current_hp_bits'];state['current_hp_bits']=min(add(oldhp,request),state['derived_bits']['1536']);fields['22']=math.ceil(fp(state['current_hp_bits']));fields['28']=math.ceil(fp(state['derived_bits']['1536']))
        events.append(dict(kind='level_up',before=old,after=state['level'],threshold_spent=spent,heal_request_bits=request,heal_delta_bits=sub(state['current_hp_bits'],oldhp)))
    state['player_fields'].update({'716':state['xp'],'717':threshold(state['level'])})
    if state['pending']:
        cards,words,draws=candidates(state['rng_words'],kit,state['level']);state.update(candidates=cards,rng_words=words,phase2587=2,selection_kind2585=0,generation_counter2400=1);events.append(dict(kind='candidate_choice',count=len(cards),draws=draws))
    gain=copy.deepcopy(state);selection=None
    if case['select_index']is not None:
        card=state['candidates'][case['select_index']];assert card['variant']=='new' and state['pending']==1
        state['owned_records80_hex'].append(selected_record(card['ability_id'],card['tier'],definitions,cooldown,damage));recalculate(state,classes,races);state.update(pending=0,phase2587=1,selection_kind2585=255,flag2581=1,flags2573=0,candidates=[])
        live=[None]*32;live[:8]=bytes(8);live[8:12]=struct.pack('<I',12);live[20:32]=struct.pack('<III',1020,0x3f800000,0)
        selection=dict(projection=state,live32_cells=[live])
    known[2587]=1
    return dict(id=case['id'],before=before,gain=gain,selection=selection,model_events=events),known


def tree_fields(capture,raw):
    nodes={v['p']:v for v in capture['tree_nodes']};seen=set();entries=[]
    def walk(pointer,height):
        assert pointer in nodes and pointer not in seen;seen.add(pointer);node=nodes[pointer];assert node['h']==height;row=bytes.fromhex(node['hex']);n=struct.unpack_from('<H',row,50)[0];assert n<=11 and len(row)==(124 if height else 76)
        for j in range(n):
            if height:walk(u(row,76+4*j),height-1)
            entries.append((struct.unpack_from('<H',row,52+2*j)[0],u(row,4+4*j)))
        if height:walk(u(row,76+4*n),height-1)
    if u(raw,2476):walk(u(raw,2476),u(raw,2480))
    assert len(entries)==u(raw,2484) and len(seen)==len(nodes) and [k for k,_ in entries]==sorted(k for k,_ in entries)
    return{str(k):v for k,v in entries}


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(CASE/'comparison.json')==COMP and sha(CASE/'task-handoff.json')==HAND and sha(SOURCE)==WASM
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    comp=load(CASE/'comparison.json');hand=load(CASE/'task-handoff.json');prep=load(CASE/'prepared.json');manifest=load(CASE/'manifest.json');author=load(ROOT/'reports/2026-11-02-growth0139.json')
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    sources=comp['source_before'];assert sources==comp['source_after']==prep['source_before']and len(sources)==21
    for name,h in sources.items():assert sha(ROOT/name)==h==sha(CASE/'source-snapshot'/name)
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])and len(edges)==40
    for table in(comp['artifacts'],prep['frozen']):
        for name,h in table.items():assert sha(CASE/name)==h
    assert prep['expected_before_original']and prep['explicit_phase1']and prep['real_phase2_path']and not prep['original_inputs_contain_expected']and not prep['snapshot_input']and prep['forbidden_model_reads']==comp['model_forbidden_reads']==[]
    raw=SOURCE.read_bytes();original=parse_module(raw);modified_raw=(CASE/manifest['module_file']).read_bytes();modified=parse_module(modified_raw)
    assert len(original['sections'])==len(modified['sections'])
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==modified_raw[b['start']:b['end']]
    assert modified['exports']==original['exports']+[('research139_growth_ctor',0,1600),('research139_growth_locale',0,83304),('research139_growth_gain',0,4677),('research139_growth_select',0,1093),('research139_growth_stack',3,0)]and len(original['imports'])==882
    assert [(v['module'],v['name'])for v in original['imports']]==[(v['module'],v['name'])for v in manifest['original_imports']]
    def data(address,size):
        result=bytearray(size)
        for at,pos,n in original['data_segments']:
            if at is None:continue
            lo,hi=max(at,address),min(at+n,address+size)
            if lo<hi:result[lo-address:hi-address]=raw[pos+lo-at:pos+hi-at]
        return bytes(result)
    word=lambda address:u(data(address,4));readtext=lambda p,n:data(p,n).decode()
    abilities={}
    for i in range(114):
        pointer=5882740+88*i;row=data(pointer,88);name=readtext(u(row,12),u(row,16));abilities[name]=(pointer,row,tuple(data(u(row,36),u(row,40))))
    cls=data(5877920,108);kit=[readtext(p,n)for p,n in struct.iter_unpack('<II',data(u(cls,32),8*u(cls,36)))];definitions={k:abilities[k]for k in kit}
    classes={1:dict(hp_armor=[u(cls,72),u(cls,76)],ability_pointer=abilities['cleave'][0])};race=data(5874636,44);racial=readtext(u(race,24),u(race,28));races={1:dict(ability_pointer=abilities[racial][0],modifiers=list(struct.iter_unpack('<II',data(u(race,16),8*u(race,20)))))}
    zone=data(5871348,152);zones=[dict(xyz=[u(zone,104),u(zone,108),u(zone,116)])];cooldown=struct.unpack('<5I',data(5912332,20));damage=struct.unpack('<5I',data(5912384,20))
    literal={node.targets[0].id:ast.literal_eval(node.value)for node in ast.parse((ROOT/'reconstruction/core_spec/candidates139_data.py').read_text()).body if isinstance(node,ast.Assign)}
    assert literal['WARRIOR_KIT139']==tuple(kit)and literal['TIER_COOLDOWN139']==cooldown and literal['TIER_DAMAGE139']==damage
    assert literal['DEFINITIONS139']=={k:(p,row.hex(),kinds)for k,(p,row,kinds)in definitions.items()}
    functions={};texts={};db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    with(PROFILE/'official-0.139.0-full.wat').open('rb')as wat:
        for idx in sorted(set(map(int,manifest['functions']))|{33028,29912,30628,25511,1677,1038}):
            a,z=original['bodies'][idx];start,end=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();wat.seek(start);value=wat.read(end-start);proof=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(value).hexdigest());texts[idx]=value.decode();functions[str(idx)]=proof
            if str(idx)in manifest['functions']:assert proof['body_sha256']==manifest['functions'][str(idx)]['body_sha256']and proof['WAT_sha256']==manifest['functions'][str(idx)]['WAT_sha256']and value==(CASE/'static'/f'{idx}.wat').read_bytes()
            (out/f'{idx}.wat').write_bytes(value)
    assert 'i64.const 5362837094'in texts[2181] and(5362837094&0xffffffff)==0x3fa66666
    for token in ['f32.const 0x1.99999ap+0','f32.const 0x1.47ae14p-7','f32.const 0x1.333334p-2','f32.const 0x1.ep+5','f32.const 0x1.9p+4','f32.const 0x1.4p+3','f32.const 0x1p+2','call 33028','call 35988','i32.store8 offset=2587']:assert token in texts[2181]
    assert 'i32.const 0\n      i32.const 1\n      call 2181'in texts[4677]and'call 1542'in texts[4677]and'call 1542'in texts[1093]and'call 4603'in texts[1093]
    for token in ['f32.load offset=5912384','f32.load offset=5912332','i32.const 8384']:assert token in texts[28657]
    assert 'f32.const 0x1.fffffep-2'in texts[86979]and'f32.copysign'in texts[86979]and'i32.const 1020'in texts[4603]and'call 25613'in texts[4603]
    cases=load(CASE/'inputs.json');expected=load(CASE/'expected.json');actual=[json.loads(v)for v in(CASE/'stdout.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==24
    counts=Counter();chosen=Counter();tiers=Counter();independent=[]
    for case,e,a in zip(cases,expected,actual,strict=True):
        assert case['id']==e['id']==a['id'];answer,known=reference(case,classes,races,zones,kit,definitions,cooldown,damage);assert answer==e,('independent_expected',case['id']);independent.append(answer)
        assert a['profile376_before_hex']==a['profile376_after_hex']and a['view128_before_hex']==a['view128_after_hex']and a['stack_after']==1048576
        profile=bytearray(376);profile[156:160]=struct.pack('<I',4);observed=bytes.fromhex(a['profile376_before_hex']);profile[168:172]=observed[168:172];profile[172:176]=struct.pack('<I',6);profile[184:192]=struct.pack('<Q',int(case['seed_u64']));profile[344]=profile[345]=1;assert bytes(profile)==observed
        view=bytearray([0x5a]*128);view[120]=1
        for offset,value in [(116,1116212265),(56,0xffffffff),(32,0xffffffff)]:view[offset:offset+4]=struct.pack('<I',value)
        assert view==bytes.fromhex(a['view128_before_hex'])and not a['owned_source']['App_produced']and not a['owned_source']['Rc_forged']
        for stage,want in [('before',answer['before']),('gain',answer['gain'])]+([]if answer['selection']is None else[('selection',answer['selection']['projection'])]):
            capture=a[stage];got=capture['projection'];game=bytes.fromhex(capture['raw_game2592_hex']);assert len(game)==2592 and game[360:362]==bytes([1,1])and game[2582]==0 and u(game,2348)==a['owned_source']['borrowed_query']
            for key,value in want.items():
                if key=='player_fields':
                    for field,v in value.items():assert got[key][field]==v;counts['known_logical_fields']+=1
                else:assert value==got[key],(case['id'],stage,key,value,got[key]);counts['projection_fields']+=1
            assert tree_fields(capture,game)==got['player_fields'];counts['full_raw_tree_captures_decoded']+=1
            for key,offset in [('level',1432),('xp',1436),('pending',2376),('current_hp_bits',1440),('generation_counter2400',2400)]:assert u(game,offset)==want[key];counts['raw_Game_declared_words']+=1
            for key,offset in [('phase2587',2587),('selection_kind2585',2585),('flag2581',2581),('flags2573',2573)]:assert game[offset]==want[key]
            assert [u(game,1720+4*j)for j in range(4)]==want['rng_words']and{str(1536+4*j):u(game,1536+4*j)for j in range(23)}==want['derived_bits']
            assert u(game,1664)==len(want['owned_records80_hex'])and u(game,1912)==len(want['candidates']);counts['owned80_full_bytes']+=80*len(want['owned_records80_hex']);counts['derived23_values']+=23
            assert all(u(game,p)==0 for p in [1700,1676,2032,176,600,2056,2044,648,1792,660,2116,2092,2104]);counts['empty_source_count_observations']+=13
            if stage=='before':
                for i,v in enumerate(known):
                    if v is None:counts['constructor_None_observed']+=1
                    else:assert game[i]==v;counts['constructor_known_bytes']+=1
                assert game[275]==game[2581]==0 and u(game,1712)==0
            for card,rawcard in zip(want['candidates'],capture['raw_candidates80_hex'],strict=True):
                row=bytes.fromhex(rawcard);assert len(row)==80 and u(row,76)==card['tier'];counts['candidate_metadata_rows']+=1;tiers[card['tier']]+=1
                if card['variant']=='new':
                    d=definitions[card['ability_id']][1];assert u(row,60)==0x80000000 and u(row,64)==u(d,12)and u(row,68)==u(d,16)and readtext(u(row,64),u(row,68))==card['ability_id']
                else:assert card['variant']=='upgrade'and(u(row,60)==0x80000001 or u(row,60)<0x80000000)and u(row,72)==0
            if stage=='gain':counts['phase2_three_cards']+=want['phase2587']==2 and len(want['candidates'])==3
            if stage=='selection':
                card=answer['gain']['candidates'][case['select_index']];chosen[card['ability_id'],card['tier']]+=1;assert len(capture['live32_hex'])==u(game,1712)==1
                for row,hx in zip(answer['selection']['live32_cells'],capture['live32_hex'],strict=True):
                    for wantbyte,byte in zip(row,bytes.fromhex(hx),strict=True):
                        if wantbyte is None:counts['live32_None']+=1;counts['live32_nonzero_None']+=bool(byte)
                        else:assert wantbyte==byte;counts['live32_known']+=1
        assert(a['selection']is None)==(answer['selection']is None)
    assert(counts['live32_known'],counts['live32_None'],counts['live32_nonzero_None'])==(432,144,16)and counts['phase2_three_cards']==19
    assert counts['full_raw_tree_captures_decoded']==66 and counts['constructor_known_bytes']==24*502
    assert {tier for(_,tier)in chosen}==set(range(5))and sum(chosen.values())==18
    runtime=load(CASE/'runtime.json');terminal=load(CASE/'process-terminal.json');assert runtime==comp['runtime']and terminal==comp['process']
    assert(runtime['fresh_instances'],runtime['full1600_calls'],runtime['real83304_calls'],runtime['full4677_calls'],runtime['full1093_calls'])==(24,24,24,24,18)
    assert(runtime['snapshot_restores'],runtime['actual_host_calls'],runtime['denied_imports'],runtime['allocations'],runtime['stack_checks'],runtime['peak_memory_bytes'])==(0,0,882,96,186,20709376)and runtime['error']is None
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['seconds']<60
    readback=load(CASE/'source-admission-readback.json');assert sha(CASE/'source-admission-readback.json')==hand['source_admission_readback_sha256']and readback['actual_sha256']==sha(CASE/'stdout.jsonl')and readback['original_executions']==0
    for h in author['history']:assert sha(ROOT/h['comparison'])==h['sha256']and not h['counted_in_final']
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for name,h in HELPERS.items():assert sha(ROOT/name)==h
    assert not any(n.startswith(('core_spec','resource_spec'))for n in sys.modules)
    (out/'independent-reference.json').write_text(json.dumps(independent,ensure_ascii=False,indent=2)+'\n')
    result=dict(status='pass_fresh139_first_gain_candidates_and_new_selection_projection',reviewer='/root/growth139_review',author='/root/self_buffs119_review',comparison_sha256=COMP,handoff_sha256=HAND,reviewer_script_sha256=sha(Path(__file__)),helper_sha256=HELPERS,author_files=hand['frozen_author_files'],cases=24,unique_inputs_excluding_id=len({json.dumps({k:v for k,v in c.items()if k!='id'},sort_keys=True)for c in cases}),full4677_calls=24,full1093_calls=18,setup1600_calls=24,setup83304_calls=24,source_files=21,production_sources=12,source_edges=40,counts=dict(counts),selected_new_cards=[dict(ability_id=k[0],tier=k[1],count=v)for k,v in sorted(chosen.items())],current_function_bindings=functions,nonexport_sections_identical=True,reference_sha256=sha(out/'independent-reference.json'),reviewer_original_executions=0,reviewer_author_production_checker_builder_executions=0,author_process=terminal,runtime=runtime,prior_studies_not_added=author['history'],seconds=time.monotonic()-started,limitations=['OnlyfreshHumanWarriorlevel1/xp0/awards0..13/newcardselection;24fixturescontain21distinctinputcombinations.No u32wrap/multilevel/upgradeacceptance theorem.','ExplicitP376/borrowedflatV128/phase1;real83304/2181phase2/full1093,notnaturalApp/Rc/ownership or nonemptyworld.','All23derived/declaredlogicalfieldsubset/orderedcardmetadata/fullowned80/RNG/live32knownprojectionchecked;otherUI/cardstrings/layout/Aura/packetstreamsremainobservations.','Constructor502knownbytes only;sourceheader zeros independently observed inrawcapture,not completeinitializer production proof.','Rawtree nodes decoded withvalueoffset4;actualfullkeyedmap checkedas-capture,only22/28/1109/34/716/717independentlyspecified.','144livepaddingNone remainunknown;16actualnonzerobytesnotcompleted.OtherphysicalGame/pointers/backing notpredicted.','CurrentfunctionWAT/datarebound;no oldacceptance transferred. CompleteApp/mainloop/native/game/network/save notaccepted.'])
    (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(out=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),cases=24)))


if __name__=='__main__':main()
