#!/usr/bin/env python3
"""Read-only review of frozen134-case learned Battle Shout135 evidence.
Does not execute originals, production models, builders or checkers.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone
import ast,hashlib,json,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
from review_opening_combat135 import sections,static_reader,missing
from review_combat137 import exports
ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/full0135-oracle-20261101T170642.056245Z'
PROFILE=ROOT/'evidence/wasm0135-profile-20261101T031028.877964Z'
POINTER=5467956

def sha(p):
    with Path(p).open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def F(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def B(v):return struct.unpack('<I',struct.pack('<f',v))[0]
def add(a,b):return B(F(a)+F(b))
def sub(a,b):return B(F(a)-F(b))
def mul(a,b):return B(F(a)*F(b))
def word(raw,o):return struct.unpack_from('<I',raw,o)[0]
def literal(path,name):
    tree=ast.parse(path.read_text());return ast.literal_eval(next(n.value for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id==name for x in n.targets)))
def closure(source):
    base=source/'reconstruction';todo=['core_spec.battle_shout135','core_spec.headless135'];seen={}
    while todo:
        module=todo.pop()
        if module in seen:continue
        parts=module.split('.');path=base.joinpath(*parts).with_suffix('.py');package=module.rsplit('.',1)[0]
        if not path.exists():path=base.joinpath(*parts)/'__init__.py';package=module
        assert path.is_file();seen[module]=str(path.relative_to(source))
        if len(parts)>1:todo.append(parts[0])
        for n in ast.walk(ast.parse(path.read_text())):
            if isinstance(n,ast.Import):todo.extend(x.name for x in n.names if x.name.split('.')[0]in('core_spec','resource_spec'))
            elif isinstance(n,ast.ImportFrom):
                assert n.level in(0,1);prefix=package+('.'+n.module if n.module else'')if n.level else(n.module or'')
                if prefix.split('.')[0]not in('core_spec','resource_spec'):continue
                todo.append(prefix)
                for alias in n.names:
                    child=prefix+'.'+alias.name
                    if base.joinpath(*child.split('.')).with_suffix('.py').exists():todo.append(child)
    return sorted(set(seen.values()))

def target30(c,now):
    for unit in c['cast']['units']:
        if unit['marker']:continue
        duration=unit['duration_bits'];position=unit['to_xy']
        if F(duration)>0:
            t=B(F(sub(now,unit['movement_time_bits']))/F(duration));t=0 if F(t)<0 else 0x3f800000 if F(t)>1 else t
            position=[add(a,mul(sub(b,a),t))for a,b in zip(unit['from_xy'],unit['to_xy'])]
        d=[sub(a,b)for a,b in zip(position,c['cast']['player_xy'])]
        if F(add(mul(d[0],d[0]),mul(d[1],d[1])))<=900:return True
    return False

def known_equal(want,actual,counts):
    assert type(want)is type(actual),(type(want),type(actual))
    if isinstance(want,dict):
        assert set(want)==set(actual)
        for k,v in want.items():known_equal(v,actual[k],counts)
    elif isinstance(want,list):
        assert len(want)==len(actual)
        for a,b in zip(want,actual):known_equal(a,b,counts)
    else:assert want==actual,(want,actual);counts['known_leaves']+=1

def check_case(c,w,a,definition,counts,semantic):
    assert c['id']==w['id']==a['id']and len(c['ops'])==len(w['stages'])==len(a['stages'])==len(w['unspecified_live_words'])
    rows=[list(struct.unpack('<8I',bytes.fromhex(x)))for x in c['live_records']];unknown={tuple(x)for x in c['initial_unknown']}
    for index,offset in unknown:
        assert offset==16 or offset==12 and rows[index][2]==12;rows[index][offset//4]=c['unknown_poison']
    ledgers=[list(x)for x in c['attempts']];owned=[bytes.fromhex(x)for x in c['owned_hex']];basic=bytes.fromhex(c['basic_hex']);cd_multiplier=c['level']['derived_bits']['1544']
    for name in('passives','adjustments','item_modifiers','owned_skills','timed_records','definitions'):assert not c['level']['sources'][name]
    assert c['context908']in(0,1)and all(row[2]in(7,8,9,12)for row in rows)and c['level']['stats']['conditional1344_id']!=11426
    assert all(len(x)==80 for x in owned)and len(basic)==80 and word(owned[c['battle_index']],0)==POINTER
    for j,(op,want,actual)in enumerate(zip(c['ops'],w['stages'],a['stages'])):
        semantic['entry_'+op['kind']]+=1;now=op['now_bits'];cast_now=op['kind']=='cast';succeeded=False
        if op['kind']=='player'and any(F(now)>=F(row[6])for row in rows):
            kept=[];remap=set()
            for i,row in enumerate(rows):
                if F(now)<F(row[6]):
                    remap.update((len(kept),o)for k,o in unknown if k==i);kept.append(row)
            semantic['expiry_passes']+=1;semantic['expired_rows']+=len(rows)-len(kept);rows,unknown=kept,remap
        if op['kind']!='cast':
            assert len(owned)==1 and c['context908']==0
            remaining=sub(word(owned[0],8),op['dt_bits']);cast_now=not F(remaining)>0
        if cast_now:
            semantic['actual_inner_or_direct_cast_attempts']+=1
            for k in range(3):
                if k<2 or not c['busy488']and not(c['context908']&1):
                    if 6673 not in ledgers[k]:ledgers[k].append(6673)
            succeeded=target30(c,now)
            if succeeded:
                semantic['successful_buff_appends']+=1;kept=[];remap=set()
                for i,row in enumerate(rows):
                    if row[0]==row[1]==0 and row[5]==6673:semantic['owner0_same_spell_rows_replaced']+=1;continue
                    remap.update((len(kept),o)for k,o in unknown if k==i);kept.append(row)
                duration=mul(mul(mul(word(definition,68),0x3fb33333),word(owned[c['battle_index']],28)),word(owned[c['battle_index']],68))
                duration=duration if F(duration)>.1 else 0x3dcccccd
                strength=mul(word(owned[c['battle_index']],76),word(definition,4))
                remap.add((len(kept),16));kept.append([0,0,8,strength,0,6673,add(now,duration),0]);rows,unknown=kept,remap
            else:semantic['target30_failed_after_ledgers']+=1
        if op['kind']=='cast':assert actual['success']==int(succeeded)and actual['owned_hex']==[x.hex()for x in owned]
        else:
            assert actual['success']is None
            if cast_now:
                remaining=mul(mul(mul(mul(word(definition,52),0x3fb33333),word(owned[0],16)),word(owned[0],56)),cd_multiplier)if succeeded else 0x3e4ccccd
                if succeeded and not F(remaining)>.25:remaining=0x3e800000
            updated=bytearray(owned[0]);struct.pack_into('<I',updated,8,remaining);owned=[bytes(updated)];assert actual['owned_hex']==[x.hex()for x in owned]
        assert actual['basic_hex']==basic.hex()and actual['attempted_spell_sets']==ledgers
        assert actual['derived_bits']['1544']==cd_multiplier and set(actual['derived_bits'])=={str(1536+4*k)for k in range(23)}
        assert actual['rng_words']==c['cast']['rng_words']and actual['timer1628_bits']==c['timer1628_bits']
        for key,source in(('message_sequence','sequence'),('action_sequence','action_sequence'),('effect_counter','effect_counter')):assert actual[key]==c[source]
        assert {tuple(x)for x in w['unspecified_live_words'][j]}==unknown
        assert len(actual['live_records'])==len(rows)==len(want['live_records'])
        for index,(predicted,observed,expected)in enumerate(zip(rows,actual['live_records'],want['live_records'])):
            words=struct.unpack('<8I',bytes.fromhex(observed));expected_words=struct.unpack('<8I',bytes.fromhex(expected))
            for k,(p,value,ew)in enumerate(zip(predicted,words,expected_words)):
                if(index,k*4)in unknown:
                    assert k==4 or k==3 and predicted[2]==12;counts['explicit_unknown_words']+=1;counts['nonzero_unknown_words_observed']+=bool(value)
                else:assert p==value==ew,(c['id'],j,index,k,p,value,ew);counts['known_leaves']+=1;semantic['strict_live_words']+=1
        left={k:v for k,v in want.items()if k!='live_records'};right={k:v for k,v in actual.items()if k!='live_records'};known_equal(left,right,counts)
        semantic['strict_owned_bytes']+=80*len(owned);semantic['strict_basic_bytes']+=80;semantic['strict_derived_words']+=23

def main():
    began=time.monotonic();out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('battle-shout135-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=json.loads((RUN/'battle-shout135-comparison.json').read_text());assert sha(RUN/'battle-shout135-comparison.json')=='df8d400630d16afdeb917d7a0b988ff8e9ac81e42ad856edde653d3d1452a740'
    assert report['source_sha256_before']==report['source_sha256_after']and report['differences']==0 and report['source_files']==94
    frozen=RUN/'source-snapshot';drift=[]
    for name,digest in report['source_sha256_before'].items():
        assert sha(frozen/name)==digest
        if sha(ROOT/name)!=digest:drift.append(name)
    assert set(drift)<={'reconstruction/core_spec/headless135.py'},drift
    core='reconstruction/core_spec/battle_shout135.py';assert sha(ROOT/core)==report['source_sha256_before'][core]=='a6ce932dfcc3271bdd8583094f4765b5cd5e50df8a41700716abd05dfa4f661a'
    production=sorted(n for n in report['source_sha256_before']if n.startswith('reconstruction/'));assert production==closure(frozen)
    for name in production:
        for node in ast.walk(ast.parse((frozen/name).read_text())):
            if isinstance(node,ast.Call):
                f=node.func;fn=f.id if isinstance(f,ast.Name)else f.attr if isinstance(f,ast.Attribute)else''
                assert fn not in('open','read_bytes','read_text','write_bytes','write_text','Popen','eval','exec','__import__'),(name,fn)
    for name,digest in(report['frozen_artifacts']|report['artifacts']).items():assert sha(RUN/name)==digest
    for name,digest in report['world_inputs'].items():assert sha(Path(name))==digest
    original=(ROOT/'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm').read_bytes();manifest=json.loads((RUN/'manifest.json').read_text());changed=(RUN/manifest['module_file']).read_bytes()
    assert hashlib.sha256(original).hexdigest()==report['original_sha256']and hashlib.sha256(changed).hexdigest()==manifest['module_sha256']
    before,after=sections(original),sections(changed);assert[x[0]for x in before]==[x[0]for x in after]and 8 not in[x[0]for x in before]
    assert all(original[a:b]==changed[c:d]for(k,a,_,b),(_,c,_,d)in zip(before,after)if k!=7)
    assert exports(changed)==exports(original)+[['research135_cast',0,922],['research135_owned_tick',0,1076],['research135_player_tick',0,2088],['research135_battle_stack0',3,0]]
    read=static_reader(original);definition=read(POINTER,88);assert definition.hex()==literal(frozen/core,'RAW88_HEX')
    assert struct.unpack_from('<I',definition)[0]==8 and word(definition,44)==6673 and definition[84:86]==bytes((9,0))
    racial=literal(frozen/'reconstruction/core_spec/racial_cast135.py','RACIALS');assert b'battle_shout'not in racial and all(x[0]!=POINTER for x in racial.values())
    trace=json.loads((RUN/'battle-shout135-static.json').read_text())
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as c,(PROFILE/'official-0.135.1-full.wat').open('rb')as wat:
        for item in trace['functions']:
            a,b=item['body_start'],item['body_end'];assert hashlib.sha256(original[a:b]).hexdigest()==item['body_sha256']
            row=c.execute('select wat_start,wat_end from functions where idx=?',(item['index'],)).fetchone();assert row==(item['wat_start'],item['wat_end']);wat.seek(row[0]);data=wat.read(row[1]-row[0]);assert data==(RUN/f"battle-{item['index']}.wat").read_bytes()and hashlib.sha256(data).hexdigest()==item['wat_sha256']
    inputs=json.loads((RUN/'battle-input.json').read_text());expected=json.loads((RUN/'battle-expected.json').read_text());actual=[json.loads(x)for x in(RUN/'battle-results.jsonl').read_text().splitlines()];assert len(inputs)==len(expected)==len(actual)==134
    counts=Counter();semantic=Counter()
    for c,w,a in zip(inputs,expected,actual):check_case(c,w,a,definition,counts,semantic)
    assert dict(counts)==report['comparison']
    groups=Counter(x['group']for x in inputs);assert groups==report['groups']
    matrix={(x['level']['stats']['class_byte'],x['level']['stats']['race_byte'])for x in inputs if x['group']=='all-class-race-23derived-rebuild'}
    assert matrix=={(a,b)for a in(1,2,3,4,5,7,8,9,11)for b in range(1,9)}
    provenance=json.loads((RUN/'battle-selection-input.json').read_text());assert provenance['frames']==379 and len(provenance['selections'])==4 and provenance['selections'][-1]==dict(frame=379,index=0,card=dict(variant='new',tier=1,ability_id='battle_shout',owned_index=0,kinds=[],gold=0))
    assert 'independent' in provenance['input_kind']and'never original observation'in provenance['input_kind']
    selected=[x for x in inputs if x['group'].startswith('actual')and'countdown'in x['group']or x['group']=='actual379-fourth-card-direct922'];assert len(selected)==2
    for x in selected:assert x['owned_hex'][x['battle_index']]==provenance['battle_owned80_hex']
    isolated=next(x for x in inputs if x['group']=='actual-selected80-isolated1076-real-countdown');isolated_actual=actual[isolated['id']];assert len(isolated['owned_hex'])==1 and len(inputs[132]['owned_hex'])==3
    new_live_counts=[len(x['live_records'])for x in isolated_actual['stages']];assert new_live_counts[:5]==[1]*5 and new_live_counts[5:]==[2]*3
    refusal=json.loads((RUN/'battle-refusals.json').read_text());assert len(refusal)==9 and all(x['boundary']=='PendingBattleShout135'for x in refusal)
    runtime=report['runtime'];assert runtime==json.loads((RUN/'battle-shout135-runtime.json').read_text())and runtime['cases']==runtime['fresh_instances']==134
    assert runtime['full_original_calls']=={'922':129,'1076':37,'2088':5}and {k:semantic['entry_'+v]for k,v in(('922','cast'),('1076','owned'),('2088','player'))}==runtime['full_original_calls']
    assert runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['peak_memory_bytes']<=33554432 and runtime['memory_page_cap']==512
    assert all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])and runtime['stack_all_restored']
    assert runtime['original_callees_replaced']is False and runtime['original_application_start']is False and runtime['original_snapshot_loaded']is False
    terminal=report['process'];assert terminal['exit_code']==0 and terminal['seconds']<60 and terminal['launcher_error']is None and missing(terminal['pid'])and missing(terminal['pgid'],True)
    assert terminal==json.loads((RUN/'battle-process-terminal.json').read_text())and(RUN/'battle-stderr.log').stat().st_size==0 and json.loads((RUN/'battle-differences.json').read_text())==[]
    prepared=json.loads((RUN/'battle-prepared.json').read_text());assert prepared['expected_before_original']and prepared['source_sha256']==report['source_sha256_before']and prepared['artifacts']==report['frozen_artifacts']
    assert '--max-old-space-size=512'in prepared['command']and'--wasm-max-mem-pages=512'in prepared['command']and prepared['deadline_seconds']==60
    source_files={n:sha(ROOT/n)for n in('scripts/review_battle_shout135.py','scripts/review_opening_combat135.py','scripts/review_combat137.py')}
    result=dict(status='passed_scoped_read_only_review',comparison=str(RUN/'battle-shout135-comparison.json'),comparison_sha256=sha(RUN/'battle-shout135-comparison.json'),reviewer_sources=source_files,
        frozen_sources=94,production_AST_closure_files=len(production),all_frozen_SHA_verified=True,current_source_drift=drift,all_94_current_sources_claimed=False,critical_component_racial_player_owned_stats_helpers_current_unchanged=True,nonexport_sections_identical=True,private_exports_only=True,learned_not_racial_catalogue=True,definition88_static_image_verified=True,
        cases=134,external_original_calls=runtime['full_original_calls'],comparison_counts=dict(counts),independent_semantic_checks=dict(semantic),class_race_matrix_cases=len(matrix),nine_refusals_observed_not_rerun=True,source_gate_audit='Explicit absent declaration; six empty nonlive vectors; exact live ownership; supported families; no inherited context beyond bit0; icebarrier continuation pending.',
        actual379_provenance=provenance,actual379_is_independent_input_not379_original_acceptance=True,isolated1076_first_cast_on_sixth_f32_tick=True,full23_stats_compared=True,all_80B_owned_and_basic_bytes_compared=True,unknown_mask_scope='Only original input-declared type12 +12/+16 and newkind8 +16; exact stable filter/expiry remapping independently reconstructed.',
        process=terminal,host_calls=0,stack_all_restored=True,model_or_original_or_checker_executed_by_reviewer=False,new_original_cases=0,new_full880_frames=0,pending=['1202 aura/display keys and packet encoding','nonempty external/proc sources','Whole379-frame/400-frame original acceptance is separate evidence'],elapsed_seconds=time.monotonic()-began)
    (out/'static-image-reads.json').write_text(json.dumps(read.proofs,indent=2)+'\n');result['static_image_reads_sha256']=sha(out/'static-image-reads.json')
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),status=result['status'],counts=dict(counts),semantic=dict(semantic))))
if __name__=='__main__':main()
