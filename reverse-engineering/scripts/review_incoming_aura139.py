#!/usr/bin/env python3
"""Independent read-only139 empty Aura/shield cleanup review; no author code."""
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
from review_initial139 import reference as constructor_reference
from review_incoming139 import append_ring, ring_initial, ring_projection

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/incoming-aura139-oracle-20261102T034802.773264Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMPARISON_SHA='7dde10f5f65b9afbde625c2b0b386981eb128998a82e034b03e9366e60d488b0'
HANDOFF_SHA='2df1bbfd7565ed5f4b3b273f0840e9cfac7f9d6529bface623850f04377547ca'
TRACE_SHA='b64e36a880abd02976a275137acd2c3e6963c2ff83898d8dfe785167a7667521'
REVIEW_HELPERS={'scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
                'scripts/review_initial139.py':'86d33e69c361eef223ad3ef271b6fb987d170f4d94847c0c068148c56ebe6fbc',
                'scripts/review_incoming139.py':'adaa5e21f2e491fe3eee18a8ec57c9d8b249481c6edc52a29408ad194dece07b'}
ZERO_KEYS=tuple(range(47,101))+tuple(range(113,125))


def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def tree_fields(tree):
    """Interpret independently the captured complete leaf/internal node bytes."""
    nodes={n['pointer']:n for n in tree['nodes']};seen=set();entries=[]
    def walk(pointer,height):
        assert pointer in nodes and pointer not in seen;seen.add(pointer)
        node=nodes[pointer];raw=bytes.fromhex(node['raw_hex']);assert node['height']==height and len(raw)==(124 if height else 76)
        count=struct.unpack_from('<H',raw,50)[0];assert count<=11
        keys=list(struct.unpack_from('<'+'H'*count,raw,52));assert keys==sorted(set(keys))
        for i,key in enumerate(keys):
            if height:walk(u32(raw,76+4*i),height-1)
            entries.append((key,u32(raw,4+4*i)))
        if height:walk(u32(raw,76+4*count),height-1)
    if tree['pointer']:walk(tree['pointer'],tree['height'])
    else:assert not nodes and tree['count']==0
    assert len(entries)==tree['count'] and len(seen)==len(nodes)
    assert [k for k,_ in entries]==sorted(set(k for k,_ in entries))
    fields={str(k):v for k,v in entries};assert fields==tree['fields']
    return fields,len(nodes)


def reference(case,classes,races,zones,english):
    inp={k:int(v) for k,v in case['constructor'].items()};assert inp==dict(class_byte=1,race_byte=1,region_index=0,seed_u64=0,object_id_u64=42,flat_height_bits=0)
    ctor,cells=constructor_reference(inp,classes,races,zones)
    derived=ctor['derived_bits'];scalar={str(k):v for k,v in [(1440,ctor['current_hp_bits']),(1652,0xc1200000),(1536,derived['1536']),(1568,derived['1568']),(1572,derived['1572'])]}
    scalar.update(case['overrides']);scalar['744']=0x5ac0ffee
    fields=dict(ctor['player_fields']);categories={};total=0.;ring=ring_initial(dict(storage=[],head=0,count=0));stages=[];detail=[]
    prior=case['previous_aura'];old_count=len(prior['storage']) if prior else 0;old_flag=prior['flag2569'] if prior else 0
    if prior:assert old_count==48 and all(bytes.fromhex(row)[:4]==b'\0'*4 for row in prior['storage'])
    live=[bytes.fromhex(row) for row in case['live32']];assert all(len(row)==32 and u32(row,8)==7 for row in live)
    last_writes=[];aura_exists=False
    for index,op in enumerate(case['ops']):
        amount,armor=fp(op['amount_bits']),fp(scalar['1568']);assert math.isfinite(amount)
        new_aura=False
        if case['kind']=='aura':
            assert not live
            reason='direct1173-empty';new_aura=True
        else:
            assert case['kind']=='incoming'
            damage=f32(amount*f32(1.-armor));absorbed=0.;hp0=fp(scalar['1440'])
            if not aura_exists:
                shield,remaining=fp(scalar['1444']),fp(scalar['1348']);source=scalar['1344'];assert shield>0.
                absorbed=min(shield,damage);aftershield=f32(shield-absorbed)
                depleted=bool(source and remaining<=absorbed);exhausted=aftershield<=0.
                spill=max(0.,f32(absorbed-remaining)) if source else absorbed
                assert min(fp(scalar['764']),spill)<=0. and (exhausted or depleted)
                assert exhausted or all(u32(row,20)==source for row in live)
                # Stable retain removes all admitted entries, leaves physical
                # backing untouched, and1173 sees the resulting count0 owner.
                live=[];new_aura=True
                scalar['1444']=bits(aftershield);scalar['764']=bits(min(aftershield,fp(scalar['764'])))
                scalar['1448']=0 if exhausted else bits(max(0.,f32(fp(scalar['1448'])-absorbed)))
                scalar['1344']=0;scalar['1348']=0
                scalar['736']=scalar['740']=0
                damage=f32(damage-absorbed)
                reason='shield_exhausted' if exhausted else 'shield_source_depleted'
            else:reason='post-cleanup-no_reserve_spill_nonfatal_prefix'
            hp=f32(hp0-damage);assert hp>0.
            scalar['1440']=bits(hp);scalar['1652']=op['now_bits'];total+=damage;categories['area']=categories.get('area',0.)+damage
            metadata={1:(english['Spell'],'Spell_Shadow_ShadowBolt'),2:(english['Boss mechanic'],'Spell_Fire_SelfDestruct')}.get(op['category'],(english['Melee'],'INV_Sword_04'))
            append_ring(ring,op['now_bits'],damage,absorbed,hp,scalar['1536'],('',*metadata),4,op['category'])
        if new_aura:
            last_writes=[] if old_count==48 and old_flag&1 else list(ZERO_KEYS)
            for key in last_writes:fields[str(key)]=0
            old_count=48;old_flag=1;aura_exists=True
        if case['kind']=='incoming':
            fields['22']=math.ceil(fp(scalar['1440']));fields['28']=math.ceil(fp(scalar['1536']))
        stage=dict(branch=reason,scalar=dict(scalar),incoming992_hex=struct.pack('>d',total).hex(),phase2587=1,history=ring_projection(ring),
                   categories={k:struct.pack('>d',v).hex() for k,v in categories.items()},keyed={k:v for k,v in sorted(fields.items(),key=lambda p:int(p[0]))},
                   aura=dict(capacity=48,count=48,flag2569=1,storage=[[0]*4+[None]*12 for _ in range(48)],written_keys=list(last_writes)),live_count=0)
        stages.append(stage);detail.append(dict(case=case['id'],stage=index,branch=reason,new_aura_producer=new_aura,current_call_key_zero_writes=last_writes if new_aura else [],new_1173_field_writes=len(last_writes) if new_aura else 0))
    return dict(constructor_cells=cells,owned80=ctor['owned_records_hex'],racial80_hex=ctor['racial_record_hex'],constructor_fields=ctor['player_fields'],stages=stages),detail


def main():
    start=time.monotonic()
    assert sha(CASE/'comparison.json')==COMPARISON_SHA and sha(CASE/'task-handoff.json')==HANDOFF_SHA and sha(CASE/'static/trace.json')==TRACE_SHA
    for name,digest in REVIEW_HELPERS.items():assert sha(ROOT/name)==digest
    receipt=json.loads((CASE/'comparison.json').read_text());handoff=json.loads((CASE/'task-handoff.json').read_text());prepared=json.loads((CASE/'prepared.json').read_text());manifest=json.loads((CASE/'manifest.json').read_text());trace=json.loads((CASE/'static/trace.json').read_text());runtime=json.loads((CASE/'runtime.json').read_text())
    assert len(handoff['files'])==7
    for name,digest in handoff['files'].items():assert sha(ROOT/name)==digest
    sources=receipt['source_sha256_before'];assert sources==receipt['source_sha256_after']==prepared['sources']==handoff['source_closure']
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(CASE/'source-snapshot'/name)
    edges=local_closure(sources);assert edges==sorted(receipt['source_import_edges'])
    assert receipt['frozen_artifacts']==prepared['artifacts'] and receipt['expected_before_original'] and prepared['expected_before_original'] and not receipt['original_input_contains_expected']
    for name,digest in (receipt['artifacts']|prepared['artifacts']).items():assert sha(CASE/name)==digest
    assert sha(SOURCE)==SOURCE_SHA;raw=SOURCE.read_bytes();original=parse_module(raw);changed=(CASE/manifest['module_file']).read_bytes();modified=parse_module(changed)
    assert len(original['sections'])==len(modified['sections'])
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    exports=[('research139_incoming1076',0,1076),('research139_locale83304',0,83304),('research139_aura1173',0,1173),('research139_initial1600',0,1600),('research139_incoming_stack',3,0)]
    assert modified['exports']==original['exports']+exports and len(original['imports'])==882
    assert original['types'][original['decl'][1173-882]]==('7f','') and original['types'][original['decl'][1076-882]]==('7f7d7e7f7f7f','')
    def read(address,size):
        answer=bytearray(size)
        for base,offset,count in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+count,address+size)
            if lo<hi:answer[lo-address:hi-address]=raw[offset+lo-base:offset+hi-base]
        return bytes(answer)
    u=lambda p:u32(read(p,4),0)
    text=lambda p,n:read(p,n).decode()
    abilities={}
    for i in range(114):
        p=5882740+88*i;abilities[text(u(p+12),u(p+16))]=p
    classptr,raceptr=5877920,5874636;starter=text(u(classptr+40),u(classptr+44));racial=text(u(raceptr+24),u(raceptr+28));rp,rc=u(raceptr+16),u(raceptr+20)
    classes={1:dict(hp_armor=[u(classptr+72),u(classptr+76)],ability_pointer=abilities[starter])}
    races={1:dict(ability_pointer=abilities[racial],modifiers=[(read(rp+8*i,1)[0],u(rp+8*i+4)) for i in range(rc)])}
    zones=[dict(xyz=[u(5871348+o) for o in [104,108,116]])]
    assert abilities[starter]==5882740 and abilities[racial]==5891892 and (u(5882740),u(5891892))==(0,8)
    english=json.loads(read(u(5401532),u(5401536)));assert len(english)==3334
    db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');bodies=[];wat={}
    with (PROFILE/'official-0.139.0-full.wat').open('rb') as stream:
        for key,record in trace['functions'].items():
            idx=int(key);loc=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());assert original['bodies'][idx]==(loc['body_start'],loc['body_end'])
            assert hashlib.sha256(raw[loc['body_start']:loc['body_end']]).hexdigest()==record['body_sha256']
            stream.seek(loc['wat_start']);value=stream.read(loc['wat_end']-loc['wat_start']);assert hashlib.sha256(value).hexdigest()==record['WAT_sha256']==sha(CASE/f'static/{idx}.wat');wat[idx]=value.decode()
            bodies.append(dict(index=idx,body_sha256=record['body_sha256'],WAT_sha256=record['WAT_sha256']))
    calls=[row['callee'] for row in db.execute('select callee from calls where caller=1173')]
    assert sorted(set(calls))==trace['direct1173_callees'] and 1542 not in calls
    for window in trace['constructor_frame88_source_windows'].values():
        value='\n'.join(wat[1600].splitlines()[window['first_line']-1:window['last_line']]);assert value==window['text'] and hashlib.sha256(value.encode()).hexdigest()==window['sha256']
    assert 'i32.const 768\n      i32.const 4\n      call 108362\n      local.tee 3' in wat[1173]
    for offset in range(0,768,16):
        snippet='i32.const 0\n        i32.store'+(f' offset={offset}' if offset else '')
        assert snippet in wat[1173]
    assert wat[1173].rfind('call 73034')<wat[1173].rfind('local.get 3\n    i32.store offset=2004')
    assert [i for i,line in enumerate(wat[1173].splitlines()) if 'call 1542' in line]==[]
    runner=(ROOT/'scripts/run_incoming_aura139_oracle.mjs').read_text();assert "call('1600',e.research139_initial1600,G,P,V)" in runner and "call('locale83304',e.research139_locale83304)" in runner and "call('1173',e.research139_aura1173,G)" in runner
    assert 'original_memory_restored:false' in runner and 'language_flags_written_by_driver:false' in runner and 'bindings[x.module][x.name]=()=>{hostCalls++;throw Error' in runner
    cases=json.loads((CASE/'fixtures.json').read_text());expected=json.loads((CASE/'expected.json').read_text());inputs=[json.loads(x) for x in (CASE/'inputs.jsonl').read_text().splitlines()];actual=[json.loads(x) for x in (CASE/'stdout.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(inputs)==len(actual)==36
    counts=Counter();details=[];roles=[];tree_heights=Counter()
    def known(cells,observed):
        assert len(cells)==len(observed)
        for value,seen in zip(cells,observed):
            if value is None:counts['unknown_cells']+=1;counts['unknown_nonzero']+=seen!=0
            else:assert value==seen;counts['known_cells']+=1
    for case,want,inp,got in zip(cases,expected,inputs,actual):
        assert case['id']==want['id']==inp['id']==got['id'] and {k:v for k,v in case.items() if k!='expected'}==inp
        answer,detail=reference(case,classes,races,zones,english);assert answer==case['expected']==want['expected'];details.extend(detail)
        ctor=got['constructor'];known(answer['constructor_cells'],bytes.fromhex(ctor['raw_game2592_hex']))
        fields,nodes=tree_fields(ctor['keyed']);assert fields==answer['constructor_fields'];counts['tree_nodes_read']+=nodes
        assert ctor['owned80']==answer['owned80'] and ctor['racial80_hex']==answer['racial80_hex'] and got['inputs_unchanged']
        raw_ctor=bytes.fromhex(ctor['raw_game2592_hex'])
        assert [u32(raw_ctor,p) for p in [968,972,976,980,2000,2004,2008,1344]]==[0,4,0,0,0,4,0,0] and u64(raw_ctor,992)==0 and raw_ctor[2569]==0
        previous=got['before'];assert previous['live']['storage']==case['live32'] and previous['live']['count']==len(case['live32'])
        if case['previous_aura']:assert previous['aura']['storage']==case['previous_aura']['storage'] and previous['aura']['flag2569']==case['previous_aura']['flag2569']
        for stage,result,op,event in zip(answer['stages'],got['stages'],case['ops'],detail):
            roles.append('1173' if case['kind']=='aura' else '1076')
            for key in ['scalar','incoming992_hex','phase2587']:assert stage[key]==result[key]
            assert result['owned80']==answer['owned80'] and result['racial80_hex']==answer['racial80_hex']
            fields,nodes=tree_fields(result['keyed']);assert fields==stage['keyed'];counts['tree_nodes_read']+=nodes;tree_heights[result['keyed']['height']]+=1
            assert {k:v for k,v in result['categories']['entries']}==stage['categories']
            assert result['live']['count']==0 and result['live']['storage']==case['live32']
            assert result['aura']['capacity']==result['aura']['count']==48 and result['aura']['flag2569']==1
            assert len(result['aura']['storage'])==48
            for cells,row in zip(stage['aura']['storage'],result['aura']['storage']):known(cells,bytes.fromhex(row))
            if event['new_aura_producer']:assert result['aura']['pointer']!=previous['aura']['pointer'];counts['fresh_aura_pointer_changes']+=1
            else:assert result['aura']==previous['aura'];counts['postcleanup_without_new_aura']+=1
            h=stage['history'];real=result['history'];assert h['header']=={k:real[k] for k in ['capacity','head','count']} and h['active']==[{k:r[k] for k in ['slot','strings']} for r in real['active']]
            assert len(h['storage'])==len(real['storage'])
            for cells,row in zip(h['storage'],real['storage']):known(cells,bytes.fromhex(row))
            for key in ['packets','notifications']:assert result[key]==previous[key]
            before=bytearray.fromhex(previous['raw_game2592_hex']);after=bytes.fromhex(result['raw_game2592_hex']);assert len(before)==len(after)==2592
            struct.pack_into('<I',before,2352,op['now_bits']);before[2569]=1
            for p in [2000,2008]:struct.pack_into('<I',before,p,48)
            skip_words={2004,2476,2480}
            if case['kind']=='incoming':
                values={968:h['header']['capacity'],976:h['header']['head'],980:h['header']['count'],1712:0,1116:0,1120:len(stage['categories'])}
                values.update({int(k):v for k,v in stage['scalar'].items()})
                for p,v in values.items():struct.pack_into('<I',before,p,v)
                struct.pack_into('<Q',before,992,int(stage['incoming992_hex'],16));skip_words|={972,1112}
            struct.pack_into('<I',before,2484,len(stage['keyed']))
            skip={p+i for p in skip_words for i in range(4)}
            for p,(wanted,seen) in enumerate(zip(before,after)):
                if p not in skip:assert wanted==seen;counts['relative_Game_known_bytes']+=1
            counts['physical_pointer_or_height_words_observed']+=len(skip_words)
            # Constructor-derived numeric attributes are invariant through the
            # cleanup. Zero Aura keys are not a substitute for calling1542.
            for key,value in constructor_reference({k:int(v) for k,v in case['constructor'].items()},classes,races,zones)[0]['derived_bits'].items():assert u32(after,int(key))==value
            assert result['stack']==1048576 and not result['source_records_after']
            counts['stages']+=1;counts['branch_'+stage['branch']]+=1;previous=result
    assert (counts['stages'],counts['known_cells'],counts['unknown_cells'],counts['relative_Game_known_bytes'],counts['physical_pointer_or_height_words_observed'])==(39,26648,102568,100372,179)
    assert (counts['fresh_aura_pointer_changes'],counts['postcleanup_without_new_aura'])==(38,1)
    assert runtime==receipt['runtime'] and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['error'] is None
    assert (runtime['fresh_instances'],runtime['real1600_setup_calls'],runtime['real_locale83304_setup_calls'])==(36,36,36)
    assert (runtime['completed_target1076_calls'],runtime['completed_target1173_calls'],runtime['stack_guards'])==(31,8,295)
    assert all(record==dict(role=role,call=i,before=1048576,after=1048576,returned=True) for i,(role,record) in enumerate(zip(roles,runtime['target_stack_returns']))) and len(runtime['target_stack_returns'])==39
    assert runtime['output_bytes']==(CASE/'stdout.jsonl').stat().st_size and runtime['peak_memory_bytes']==20709376
    assert not any(runtime[k] for k in ['old_snapshot_loaded','original_memory_restored','language_flags_written_by_driver','App_produced','world_Rc_producer_executed','network_used','user_saves_accessed'])
    for i,locale in enumerate(runtime['locale_producer_receipts']):
        assert locale['instance']==i+1 and bytes.fromhex(locale['before'])==read(14476464,40) and locale['once']==3 and locale['capacity']==locale['count']==14
    assert len(runtime['locale_producer_receipts'])==36
    terminal=json.loads((CASE/'owned-terminal.json').read_text());assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing'] and terminal['seconds']<90
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('incoming-aura139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=dict(status='pass_with_declared_empty_postretain_Aura_limits',reviewer='/root/self_buffs119_review',author='/root/motion38_review',comparison_sha256=COMPARISON_SHA,author_handoff_sha256=HANDOFF_SHA,source_sha256=SOURCE_SHA,static_trace_sha256=TRACE_SHA,
                script_sha256=sha(Path(__file__)),pure_review_helpers=REVIEW_HELPERS,author_model_checker_builder_original_executions_by_reviewer=0,native_executions_by_reviewer=0,
                cases=36,complete1076_calls_checked=31,direct1173_calls_checked=8,setup1600_checked=36,setup83304_checked=36,independent_mismatches=0,counts=dict(counts),tree_height_occurrences=dict(tree_heights),
                Aura_known_tag_bytes=48*4*39,Aura_unknown_payload_bytes=48*12*39,Aura_zero_key_set=list(ZERO_KEYS),direct1173_callees=sorted(set(calls)),direct1542_call_present=False,
                source_closure=sources,source_import_edges=edges,author_files=handoff['files'],static_functions=bodies,export_delta=exports,nonexport_sections_byte_identical=True,whole_original_retained=True,
                runtime_summary={k:v for k,v in runtime.items() if k not in ['target_stack_returns','locale_producer_receipts']},author_owned_terminal=terminal,details=details,seconds=time.monotonic()-start,
                limitations=['Only actual fresh1600 humanwarrior research profiles/borrowed flat query,explicit phase1,source0/contact0,emptyNPC/modifier/item owners,no owned/racial kind12,no positive reserve spill and nonfatal shield-only live records fully removed.',
                             '36constructor+36locale calls are setup,not72newindependent constructor/localization coverage.31full1076 and8direct1173 are39exported target calls;30internal1173 branches are control-flow inference,not independently instrumented callcounts.',
                             '1173 has no direct1542 call;constructor-derived numeric words remain invariant.66Aura zero keys are written only whenready lowbit does not admit equal-skip;keyed logical trees are re-read from retained raw nodes,physical allocator/tree shape is not predicted.',
                             'Every1173 creates a fresh768B vector before freeingold;only48tag words are knownzero and12payload bytes per slot remainNone even for prior fully knownpoisoned tag0 backing. Followup1076withoutshield reusesAura and does not call1173.',
                             'Expected Aura.written_keys on postcleanup followup carries last1173 producer metadata;it is not a claim that second1076 writes66zero keys.',
                             'Relative Game conservation compares100372nonpointer/nonheight byte occurrences to actual pre-state plus independent writes;179pointer/height word occurrences stayobserved. This is not a standalone2592B producer.',
                             'Full BTree leaf/internal bytes are retained and independently traversed for all logical fields;unused node bytes/pointers/height are observation,not physical BTree reconstruction.',
                             'Other retained live,nonemptyAura/modifier/cooldown branches,1173general behavior,28155/1466,fatal/revival/naturalApp/realWorldRc/fullgame/native remain unknown.12author-model boundaries,pilot and preparation/selfcheck failures are not added toformal36/39.',
                             'Current raw source and current actual artifacts only;no135/138orpreviouspassingactual transfer. Review helpers are frozen pure independent reference/parsing functions;no author production imported or executed.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),cases=36,calls1076=31,direct1173=8,counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
