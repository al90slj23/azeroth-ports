#!/usr/bin/env python3
"""Different-author read-only review of stored 139 incoming1076 prefix results."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math
import sqlite3
import struct
import time

from review_combat139 import bits, fp, f32, local_closure, parse_module, sha, u32, u64

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'evidence/incoming139-oracle-20261102T033003.208321Z'
SOURCE = ROOT / 'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE = ROOT / 'evidence/wasm0139-profile-20261102T012426.951871Z'
SOURCE_SHA = '71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMPARISON_SHA = '7bc59682f0b82976f113e4a93b794d3ae9aca11a861ab012bb247dc7789f2533'
HANDOFF_SHA = '1e438e6075058f3f61d076519056c110c70ca315b485e93d26a9482ad5714e29'
TRACE_SHA = 'b0a34e658ea445e5399fd877324b3cbd2d70300d3a00df34a28787efd9100bb7'
HELPER_SHA = '158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9'
SCALARS = {736:'absorbed736_bits',740:'maximum_shield740_bits',764:'reserve764_bits',1344:'shield_source1344',
           1348:'shield_remaining1348_bits',1440:'hp1440_bits',1444:'shield1444_bits',1448:'barrier1448_bits',1652:'last_hit1652_bits'}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def ring_initial(case):
    rows = [list(bytes.fromhex(s)) for s in case['storage']]
    assert all(len(row) == 48 and all(u32(bytes(row), p + 4) == 0 for p in [0,8,16]) for row in rows)
    return dict(head=case['head'], count=case['count'], rows=rows,
                strings=[['','',''] for _ in rows], origin=[['fixture']*48 for _ in rows])


def append_ring(ring, now, damage, absorbed, hp, maximum, metadata, classification, category):
    # Reproduce physical deque relocation, including the old inactive bytes.
    cap, head, count = len(ring['rows']), ring['head'], ring['count']
    cutoff = f32(fp(now) - 10.)
    while count and (count >= 400 or fp(u32(bytes(ring['rows'][head][24:28]),0)) < cutoff):
        count -= 1; head = (head + 1) % cap
    if count == cap:
        newcap = max(4, 2*cap)
        ring['rows'].extend([[None]*48 for _ in range(newcap-cap)])
        ring['origin'].extend([['allocator_unwritten']*48 for _ in range(newcap-cap)])
        ring['strings'].extend([None for _ in range(newcap-cap)])
        if head + count > cap:
            tail, front = cap-head, count-(cap-head)
            if tail > front and newcap-cap >= front:
                src, dst, length = 0, cap, front
            else:
                src, dst, length = head, newcap-tail, tail
                head = dst
            for key in ['rows','origin','strings']:
                ring[key][dst:dst+length] = [None if x is None else list(x) for x in ring[key][src:src+length]]
        cap = newcap
    slot = (head+count) % cap
    row, origin = ring['rows'][slot], ring['origin'][slot]
    for offset, string in zip([0,8,16], metadata):
        row[offset:offset+4] = [None]*4; origin[offset:offset+4] = ['resource_pointer']*4
        row[offset+4:offset+8] = struct.pack('<I',len(string.encode()))
        origin[offset+4:offset+8] = ['semantic']*4
    row[24:44] = struct.pack('<5I', now, bits(damage), bits(absorbed), bits(hp), maximum)
    row[44:46] = [classification,int(category==2)]
    origin[24:46] = ['semantic']*22
    ring['strings'][slot] = list(metadata)
    ring['head'], ring['count'] = head, count+1


def ring_projection(ring):
    capacity, head, count = len(ring['rows']), ring['head'], ring['count']
    return dict(header=dict(capacity=capacity, head=head, count=count), storage=[list(r) for r in ring['rows']],
                provenance=[list(r) for r in ring['origin']], active=[dict(slot=(head+i)%capacity,strings=ring['strings'][(head+i)%capacity]) for i in range(count)])


def reference(case, english):
    state = dict(case['input']); records = [bytes.fromhex(s) for s in case['source_records']]
    ring = ring_initial(case['history']); categories = {}; keyed = {}; stages = []; details = []
    assert state['mode2582']==0 and state['items8']==[] and all(math.isfinite(fp(v)) for k,v in state.items() if k.endswith('_bits'))
    for op in case['ops']:
        state['now_bits'] = op['now_bits']; now = fp(op['now_bits']); amount = fp(op['amount_bits'])
        assert op['spell_id']==0 and math.isfinite(amount)
        branch = 'phase_guard' if state['phase2587']!=1 else 'protection_guard' if state['protection2576']&1 else 'active_raw12_guard' if any(b['kind']==12 and fp(b['expires_bits'])>now for b in state['live32']) else None
        armor = fp(state['armor1568_bits']); nearby = None; damage = None
        if branch is None:
            modifier = next((m for m in state['modifiers36'] if m['tag']==54 and m['byte4']==1),None)
            if modifier is not None and any(b['spell_id']==324 and fp(b['expires_bits'])>now for b in state['live32']):
                bonus = f32(f32(float(modifier['byte5'])*3.)/100.)
                if bonus>0.: armor = min(max(armor,fp(state['armor_cap1572_bits'])),f32(armor+bonus))
            damage = f32(amount*f32(1.-armor))
            if fp(state['nearby1624_bits'])>0.:
                nearby = 0
                for row in records:
                    if u32(row,0)!=0: continue
                    duration = fp(u32(row,344))
                    if duration>0.:
                        ratio = f32(f32(now-fp(u32(row,340)))/duration); ratio=min(1.,max(0.,ratio))
                        xy=[f32(fp(u32(row,a))+f32(f32(fp(u32(row,b))-fp(u32(row,a)))*ratio)) for a,b in [(316,328),(320,332)]]
                    else: xy=[fp(u32(row,a)) for a in [328,332]]
                    dx,dy=[f32(v-fp(p)) for v,p in zip(xy,state['player_xy'])]
                    nearby += f32(f32(dx*dx)+f32(dy*dy)) <= 64.
                if nearby>=5: damage=f32(damage*f32(1.-fp(state['nearby1624_bits'])))
            absorbed=0.
            if fp(state['shield1444_bits'])>0.:
                shield=fp(state['shield1444_bits']); absorbed=min(shield,damage)
                remaining=fp(state['shield_remaining1348_bits']); source=state['shield_source1344']
                spill=max(f32(absorbed-remaining),0.) if source else absorbed
                depleted=bool(source and remaining<=absorbed)
                assert min(fp(state['reserve764_bits']),spill)<=0. and not depleted
                aftershield=f32(shield-absorbed); assert aftershield>0.
                state['shield1444_bits']=bits(aftershield)
                state['barrier1448_bits']=bits(max(f32(fp(state['barrier1448_bits'])-absorbed),0.))
                state['shield_remaining1348_bits']=bits(f32(remaining-absorbed))
                state['reserve764_bits']=bits(min(aftershield,fp(state['reserve764_bits'])))
                state['absorbed736_bits']=bits(f32(absorbed+fp(state['absorbed736_bits'])))
                state['maximum_shield740_bits']=bits(max(shield,fp(state['maximum_shield740_bits'])))
                damage=f32(damage-absorbed)
            hp_before_clamp=f32(fp(state['hp1440_bits'])-damage)
            state['hp1440_bits']=bits(hp_before_clamp); state['last_hit1652_bits']=op['now_bits']; state['incoming992']+=damage
            match=next((row for row in records if u64(row,112)==int(op['source_guid'])),None)
            key='area' if match is None else ('boss melee' if op['contact_flag'] else 'boss spell') if u32(match,244)!=0xffffffff else 'elite' if match[424] else 'mob melee' if op['contact_flag'] else 'mob spell'
            categories[key]=categories.get(key,0.)+damage
            source, classification = '',4
            if match is not None:
                assert u32(match,244)==u32(match,40)==0xffffffff
                pointer=u32(match,284); assert pointer in [0,5830904]
                source, classification=(english['enemy.600'] if pointer else ''),match[424]
            fallback={1:(english['Spell'],'Spell_Shadow_ShadowBolt'),2:(english['Boss mechanic'],'Spell_Fire_SelfDestruct')}.get(op['category'],(english['Melee'],'INV_Sword_04'))
            append_ring(ring,op['now_bits'],damage,absorbed,hp_before_clamp,state['maximum1536_bits'],(source,*fallback),classification,op['category'])
            if int(op['source_guid']) and op['contact_flag']:
                raw13=-0.
                for b in state['live32']:
                    if b['kind']==13 and fp(b['expires_bits'])>now:raw13=f32(raw13+fp(b['value_bits']))
                assert raw13<=0. and not state['modifiers36'] and not state['items8']
            if state['minimum_one2578']:state['hp1440_bits']=bits(max(1.,hp_before_clamp))
            assert fp(state['hp1440_bits'])>0.
            keyed={str(key):max(0,min(0xffffffff,math.ceil(fp(state[name])))) for key,name in [(22,'hp1440_bits'),(28,'maximum1536_bits')]}
            branch='no_reserve_spill_nonfatal_prefix'
        scalar={str(offset):state[name] for offset,name in SCALARS.items()}; scalar['744']=0x5ac0ffee
        stages.append(dict(branch=branch,history=ring_projection(ring),scalar=scalar,incoming992_hex=struct.pack('>d',state['incoming992']).hex(),phase2587=state['phase2587'],categories={k:struct.pack('>d',v).hex() for k,v in sorted(categories.items())},keyed=dict(keyed),packets=[],notifications=[]))
        details.append(dict(case=case['id'],branch=branch,effective_armor_bits=bits(armor),nearby_count=nearby,damage_bits=None if damage is None else bits(damage)))
    return stages, details


def main():
    start=time.monotonic()
    assert sha(CASE/'comparison.json')==COMPARISON_SHA and sha(CASE/'task-handoff.json')==HANDOFF_SHA
    assert sha(CASE/'static/trace.json')==TRACE_SHA and sha(SOURCE)==SOURCE_SHA and sha(ROOT/'scripts/review_combat139.py')==HELPER_SHA
    receipt=json.loads((CASE/'comparison.json').read_text()); handoff=json.loads((CASE/'task-handoff.json').read_text())
    prepared=json.loads((CASE/'prepared.json').read_text()); manifest=json.loads((CASE/'manifest.json').read_text()); trace=json.loads((CASE/'static/trace.json').read_text()); runtime=json.loads((CASE/'runtime.json').read_text())
    assert len(handoff['files'])==9
    for name,digest in handoff['files'].items():assert sha(ROOT/name)==digest
    sources=receipt['source_sha256_before']; assert sources==receipt['source_sha256_after']==prepared['source_sha256']==handoff['source_closure']
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(CASE/'source-snapshot'/name)
    edges=local_closure(sources); assert edges==sorted(receipt['source_import_edges']) and len(sources)==15 and len(edges)==23
    for name,digest in receipt['artifacts'].items():assert sha(CASE/name)==digest
    assert receipt['frozen_artifacts']==prepared['artifacts']
    for name,digest in prepared['artifacts'].items():assert sha(CASE/name)==digest
    raw=SOURCE.read_bytes(); original=parse_module(raw); changed=(CASE/manifest['module_file']).read_bytes(); modified=parse_module(changed)
    assert len(original['sections'])==len(modified['sections'])
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    assert modified['exports']==original['exports']+[tuple(x) for x in manifest['added_exports']]
    assert manifest['added_exports']==[['research139_incoming1076',0,1076],['research139_locale83304',0,83304],['research139_incoming_stack',3,0]]
    assert ('__wbindgen_malloc',0,93344) in original['exports'] and manifest['allocator_index']==93344
    assert original['types'][original['decl'][1076-882]]==('7f7d7e7f7f7f','') and original['decl'][1076-882]==284
    assert len(original['imports'])==882
    assert [dict(module=x['module'],name=x['name'],type_index=x['type_index']) for x in original['imports']]==manifest['original_imports']
    def read(address,count):
        out=bytearray(count)
        for base,offset,size in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+size,address+count)
            if lo<hi:out[lo-address:hi-address]=raw[offset+lo-base:offset+hi-base]
        return bytes(out)
    english_header=read(5401532,28); assert (u32(english_header,0),u32(english_header,4))==(1767182,233725)
    english_raw=read(u32(english_header,0),u32(english_header,4)); assert hashlib.sha256(english_raw).hexdigest()==trace['English']['sha256']
    english=json.loads(english_raw); assert len(english)==3334
    for key in ['Melee','Spell','Boss mechanic','enemy.600']:assert english[key]==trace['English']['selected'][key]
    definitions=[]
    for index in range(114):
        row=read(5882740+88*index,88); label=read(u32(row,12),u32(row,16)).decode()
        if label=='lightning_shield':definitions.append((index,5882740+88*index,u32(row,44),row.hex()))
    assert definitions==[(60,5888020,324,trace['lightning_shield']['raw88_hex'])]
    for key,value in trace['read_proofs'].items():
        address,count=map(int,key.split(':')); assert hashlib.sha256(read(address,count)).hexdigest()==value['sha256']
    db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on'); static_functions=[]
    with (PROFILE/'official-0.139.0-full.wat').open('rb') as stream:
        for key,record in trace['functions'].items():
            idx=int(key);loc=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());assert original['bodies'][idx]==(loc['body_start'],loc['body_end'])
            assert hashlib.sha256(raw[loc['body_start']:loc['body_end']]).hexdigest()==record['body_sha256']
            stream.seek(loc['wat_start']);text=stream.read(loc['wat_end']-loc['wat_start']);assert hashlib.sha256(text).hexdigest()==record['WAT_sha256']==sha(CASE/f'static/{idx}.wat')
            static_functions.append(dict(index=idx,body_sha256=record['body_sha256'],WAT_sha256=record['WAT_sha256']))
    lines=[line.strip() for line in (CASE/'static/1076.wat').read_text().splitlines()]
    for key,window in trace['windows'].items():
        window_text='\n'.join(lines[window['first_line']-1:window['last_line']]); assert window_text==window['text'] and hashlib.sha256(window_text.encode()).hexdigest()==window['sha256']
    assert lines[243:247]==['f32.const 0x1.8p+1 (;=3;)','f32.mul','f32.const 0x1.9p+6 (;=100;)','f32.div']
    assert 'f32.store offset=736' in lines and 'f32.store offset=740' in lines and 'i64.store offset=736' in lines
    assert 'i32.store8 offset=44' in lines and 'i32.store8 offset=45' in lines and 'i32.store8 offset=46' not in lines
    calls=Counter(row['callee'] for row in db.execute('select callee from calls where caller=1076')); assert [dict(callee=k,sites=v) for k,v in sorted(calls.items())]==trace['direct_callees']
    runner=(ROOT/'scripts/run_incoming139_oracle.mjs').read_text(); assert "call('locale83304',e.research139_locale83304)" in runner and 'language_flags_written_by_driver:false' in runner
    assert "bindings[x.module][x.name]=()=>{hostCalls++;throw Error('Denied '+x.name)" in runner and "call('1076',e.research139_incoming1076" in runner
    assert 'original_memory_restored:false' in runner and 'b().fill(0,p,p+n)' in runner and 'i%32===0' in runner
    cases=json.loads((CASE/'fixtures.json').read_text()); expected=json.loads((CASE/'expected.json').read_text()); actual=[json.loads(x) for x in (CASE/'stdout.jsonl').read_text().splitlines()]; inputs=[json.loads(x) for x in (CASE/'inputs.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(actual)==len(inputs)==99
    counts=Counter(); details=[]
    for case,want,got,inp in zip(cases,expected,actual,inputs):
        assert case['id']==want['id']==got['id']==inp['id'] and {k:v for k,v in case.items() if k!='expected'}==inp
        stages,detail=reference(case,english); assert stages==case['expected']==want['stages']; details.extend(detail)
        assert len(stages)==len(got['stages'])==len(case['ops'])
        previous=got['before']
        before_game=bytes.fromhex(previous['raw_game2592_hex']);assert len(before_game)==2592
        assert previous['scalar']=={str(offset):case['input'][name] for offset,name in SCALARS.items()}|{'744':0x5ac0ffee}
        assert previous['source_records_after']==case['source_records'] and previous['history']['storage']==case['history']['storage']
        assert (previous['history']['head'],previous['history']['count'])==(case['history']['head'],case['history']['count'])
        assert not previous['categories']['entries'] and not previous['keyed']['fields']
        assert u32(before_game,2352)==case['input']['now_bits'] and u32(before_game,1712)==len(case['input']['live32']) and u32(before_game,2056)==len(case['input']['modifiers36'])
        assert u32(before_game,1792)==len(case['source_records']) and u32(before_game,2032)==0
        for stage,result,op in zip(stages,got['stages'],case['ops']):
            for key in ['scalar','incoming992_hex','phase2587']:assert stage[key]==result[key]
            assert case['source_records']==result['source_records_after']
            assert list(stage['categories'].items())==[tuple(x) for x in result['categories']['entries']]
            assert stage['keyed']==result['keyed']['fields']
            assert not result['packets']['active'] and not result['notifications']['active']
            assert result['stack']==1048576
            h=stage['history']; observed=result['history']; assert h['header']=={k:observed[k] for k in ['capacity','head','count']}
            assert h['active']==[{k:r[k] for k in ['slot','strings']} for r in observed['active']]
            assert len(h['storage'])==len(observed['storage'])
            for row,origin,physical in zip(h['storage'],h['provenance'],observed['storage']):
                physical=bytes.fromhex(physical);assert len(physical)==48
                for value,why,seen in zip(row,origin,physical):
                    if value is None:
                        assert why in ['resource_pointer','allocator_unwritten'];counts[why]+=1;counts[why+'_nonzero']+=seen!=0
                    else:assert value==seen;counts['known_history']+=1
            for active in observed['active']:
                row=bytes.fromhex(observed['storage'][active['slot']]);assert row.hex()==active['raw48_hex']
                for offset,string in zip([0,8,16],active['strings']):assert u32(row,offset+4)==len(string.encode()) and u32(row,offset)+len(string.encode())<=runtime['peak_memory_bytes']
            before=bytearray.fromhex(previous['raw_game2592_hex']);struct.pack_into('<I',before,2352,op['now_bits']);after=bytes.fromhex(result['raw_game2592_hex']);assert len(before)==len(after)==2592
            if stage['branch'].endswith('guard'):assert before==after;counts['guard_bytes']+=2592
            for offset,value in stage['scalar'].items():assert u32(after,int(offset))==value
            assert u64(after,992)==int(stage['incoming992_hex'],16)
            assert [u32(after,p) for p in [968,972,976,980]]==[observed[p] for p in ['capacity','pointer','head','count']]
            counts['branch_'+stage['branch']]+=1;counts['stages']+=1;previous=result
    assert (counts['stages'],counts['known_history'],counts['resource_pointer'],counts['allocator_unwritten'],counts['guard_bytes'])==(164,104566,26088,48962,20736)
    assert runtime==receipt['runtime'] and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error'] is None
    assert runtime['completed_target1076_calls']==164 and runtime['real_locale83304_setup_calls']==runtime['fresh_instances']==4
    assert len(runtime['target_stack_returns'])==164 and runtime['stack_guards']==663
    assert all(r==dict(call=i,before=1048576,after=1048576,returned=True) for i,r in enumerate(runtime['target_stack_returns']))
    assert not any(runtime[k] for k in ['old_snapshot_loaded','original_memory_restored','language_flags_written_by_driver','network_used','user_saves_accessed'])
    assert runtime['peak_memory_bytes']==20840448 and runtime['memory_cap_bytes']==134217728 and runtime['heap_cap_mib']==512
    assert runtime['output_bytes']==(CASE/'stdout.jsonl').stat().st_size
    locales=runtime['locale_producer_receipts'];assert len(locales)==4
    for i,locale in enumerate(locales):
        assert locale['instance']==i+1 and bytes.fromhex(locale['before'])==read(14476464,40)
        after=bytes.fromhex(locale['after']);assert after[24]==locale['once']==3
        assert [u32(after,o) for o in [0,4,8,12,16,20]]==[locale[k] for k in ['tag','value','fallback','capacity','pointer','count']]
        assert locale['tag']==locale['fallback']==0 and locale['capacity']==locale['count']==14 and locale['pointer']>0
    terminal=json.loads((CASE/'owned-terminal.json').read_text());assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing']
    assert prepared['expected_before_original'] and receipt['expected_before_original'] and not receipt['original_input_contains_expected']
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('incoming139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=dict(status='pass_with_declared_nonfatal_numeric_history_prefix_limits',reviewer='/root/self_buffs119_review',author='/root/motion38_review',comparison_sha256=COMPARISON_SHA,author_handoff_sha256=HANDOFF_SHA,
                source_sha256=SOURCE_SHA,static_trace_sha256=TRACE_SHA,script_sha256=sha(Path(__file__)),pure_review_helper_sha256=HELPER_SHA,
                author_model_checker_builder_original_executions_by_reviewer=0,native_executions_by_reviewer=0,independently_recomputed_cases=99,independently_checked_full1076_calls=164,real83304_setups_checked=4,mismatches=0,
                source_closure=sources,source_import_edges=edges,production_source_count=5,author_files=handoff['files'],counts=dict(counts),static_functions=static_functions,direct_call_sites=sum(calls.values()),unique_direct_callees=len(calls),
                whole_original_retained=True,nonexport_sections_byte_identical=True,export_delta=modified['exports'][len(original['exports']):],locale_runtime=locales,lightning_shield_definition=trace['lightning_shield'],
                runtime={k:v for k,v in runtime.items() if k not in ['target_stack_returns','locale_producer_receipts']},author_owned_terminal=terminal,details=details,seconds=time.monotonic()-start,
                caveats=['99 controlled fixtures/164 complete1076 calls on4fresh instances, not99fresh Game constructors. Synthetic zero Game/NPC432/history/source fixtures, no natural constructor/App/world producer.',
                         'Mode0,nonfatal or minimum-one,spellID0,no-positive-reserve-spill,unexhausted/undepleted shield and known no-active-callback domain only.1173/28155/1466/fatal/revival callbacks remain excluded.',
                         'Current139 tag54 first active byte4 modifier matches lightning_shield spell324 with strict expiry; rankbyte5*3/100. No old135nearcount*2 rule or passing test is reused.',
                         'History resource pointers are unknown addresses with separately checked strings; allocator-unwritten bytes remainNone, existing padding and copied inactive slots remain known when sourced.',
                         'Full2592B Game is captured; full byte equality is checked only for8guards. Numeric fields/history/source records and logical categories/keyed22/28 are verified, BTree physical nodes and full Game are not independently reconstructed.',
                         '164 target stack records are individually stored;663totalguards include allocations and4locale calls, with non-target successes represented by runner assertions/aggregate.',
                         '83304 initializes real current embedded English tables/Once on each instance with882denied imports and0host calls. This is explicit setup, not natural menu locale choice or general multilingual reconstruction.',
                         '13 author model-boundary rejections/pilots/two failed studies are not added to99/164. Prior evidence and first failures remain untouched;0neworiginal by reviewer.',
                         'Extra output hashes bind bytes as read;prepared pins inputs/expected/module before original. No native, full gameplay, or full1076 arbitrary behavior acceptance.'])
    save(out/'review.json',result)
    print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),cases=99,calls=164,mismatches=0,counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':
    main()
