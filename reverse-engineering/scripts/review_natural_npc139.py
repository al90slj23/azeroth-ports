#!/usr/bin/env python3
"""Independent read-only139 None8740→5719 interleaved four-NPC review."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sqlite3,struct,time
from review_combat139 import fp,local_closure,parse_module,sha,u32,u64
from review_initial139 import rng as constructor_rng
from review_npc_spawn139 import reference as npc_reference
from review_world_position139 import Reference,load_world

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/natural-npc139-oracle-20261102T044325.586298Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
NPC_STATIC=ROOT/'evidence/npc-spawn139-static-20261102T031838.749854Z'
POS_STATIC=ROOT/'evidence/world-position139-static-20261102T033613.062984Z'
COMPARISON_SHA='bc6f71760ce62c824a176c8ccc2351782412b725a6f5bc0cfca5d0823dac9d1d'
HANDOFF_SHA='75d62f2497f7a2a14c0c6eb9654d2b5dd1190a1ac4210e357b4d3f86b73272dc'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HELPERS={'scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
         'scripts/review_initial139.py':'86d33e69c361eef223ad3ef271b6fb987d170f4d94847c0c068148c56ebe6fbc',
         'scripts/review_npc_spawn139.py':'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074',
         'scripts/review_world_position139.py':'d842c619169a582ab8eb540cab2829233eb633bbd79d10ab674c50e71c92ab7e',
         'scripts/review_player_motion135.py':'8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2'}


def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def reference(case,world,nav,scalars,tables,definition,speeds):
    words=case['rng_words'];counter=case['counter'];storage=[list(bytes.fromhex(s))for s in case['initial_backing']] if case['initial_backing']else[[None]*432 for _ in range(4)]
    answers=[];packets=[];details=[]
    for index in range(4):
        state=dict(zone=0,player_xyz=case['player_xyz'],velocity_xy=case['velocity_xy'],low_radius_bits=0x41d00000,high_radius_bits=0x42100000,bias_probability_bits=0x3f000000,rng_words=words,distance_map=case['distance_map'])
        loc=Reference(state,world,nav,scalars,tables);xyz=loc.spawn()
        # The independently transcribed single-NPC rule consumes yaw/jitter
        # immediately after this particular8740, before the next spawn query.
        backing=[bytes(storage[index]).hex()]*4 if None not in storage[index] else []
        one=dict(id=4*case['id']+index,rng_words=list(loc.words),counter=counter,positions=[xyz],player_xy=case['player_xyz'][:2],initial_backing=backing)
        result,_,draws=npc_reference(one,definition,fp(1062333317),tables,speeds);born=result[0]
        storage[index]=born['records432_cells'][0];words=born['rng_words'];counter=born['counter'];packets.extend(born['packets'])
        answers.append(dict(success=born['success'],guid=born['guid'],counter=counter,rng_words=list(words),position_bits=xyz,capacity=4,count=index+1,
                            records432_cells=[list(row)for row in storage],packets=list(packets),HP288_bits=born['HP288_bits'],attack296_bits=born['attack296_bits']))
        details.append(dict(case=case['id'],stage=index,position_reference_diagnostics=dict(loc.count),NPC_reference_draws=draws,original_internal_counters_observed=False))
    return answers,details


def main():
    start=time.monotonic();assert sha(CASE/'comparison.json')==COMPARISON_SHA and sha(CASE/'task-handoff.json')==HANDOFF_SHA and sha(SOURCE)==SOURCE_SHA
    for name,digest in HELPERS.items():assert sha(ROOT/name)==digest
    receipt=json.loads((CASE/'comparison.json').read_text());prepared=json.loads((CASE/'prepared.json').read_text());manifest=json.loads((CASE/'manifest.json').read_text());handoff=json.loads((CASE/'task-handoff.json').read_text());runtime=json.loads((CASE/'runtime.json').read_text());inputproof=json.loads((CASE/'static-input-proof.json').read_text())
    assert len(handoff['frozen_author_files'])==7
    for name,digest in handoff['frozen_author_files'].items():assert sha(ROOT/name)==digest
    assert sha(CASE/'static-input-proof.json')==handoff['static_input_proof_sha256']
    sources=receipt['source_before'];assert sources==receipt['source_after']==prepared['source_before'] and len(sources)==31
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(CASE/'source-snapshot'/name)
    edges=local_closure(sources);assert edges==sorted(receipt['source_import_edges']) and len(edges)==71 and len([n for n in sources if n.startswith('reconstruction/')])==20
    for name,digest in receipt['artifacts'].items():assert sha(CASE/name)==digest
    for name,digest in prepared['frozen'].items():assert sha(CASE/name)==digest
    assert receipt['expected_before_original'] and prepared['expected_before_original'] and not prepared['original_inputs_contain_expected'] and not receipt['expectation_python_reads_forbidden']
    world,nav,scalars=load_world(receipt['world_provenance']);assert not scalars['primary_present'] and not scalars['flat_present']
    raw=SOURCE.read_bytes();original=parse_module(raw);changed=(CASE/manifest['module_file']).read_bytes();modified=parse_module(changed)
    assert len(original['sections'])==len(modified['sections'])
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    assert modified['exports']==original['exports']+[('research139_spawn5719',0,5719),('research139_spawn_stack0',3,0)] and len(original['imports'])==882
    assert original['types'][original['decl'][5719-882]]==('7f7f7f7f','') and original['decl'][5719-882]==2
    def data(address,size):
        out=bytearray(size)
        for base,offset,count in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+count,address+size)
            if lo<hi:out[lo-address:hi-address]=raw[offset+lo-base:offset+hi-base]
        return bytes(out)
    definition=data(5830904,72);zone=data(5871348,152)
    assert len(definition)==72 and u32(definition,24)==600 and u32(definition,68)==0
    assert [u32(zone,p)for p in[64,68,136,140]]==[5830904,12,1062333317,0]
    tables=[list(struct.unpack('<4f',data(p,16)))for p in[14426512,14426528,14426544,14426560]];speeds=list(struct.unpack('<6I',data(1593032,24)));speeds[1]=1088421888
    db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');wat={};functions=[]
    with (PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for idx in [5719,8740,13563,6786,1600,1108]:
            row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());a,z=original['bodies'][idx];assert (a,z)==(row['body_start'],row['body_end']);stream.seek(row['wat_start']);text=stream.read(row['wat_end']-row['wat_start']);wat[idx]=text.decode();functions.append(dict(index=idx,body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(text).hexdigest()))
    assert functions[0]['body_sha256']==manifest['body_sha256']==inputproof['NPC5719_body_sha256'] and functions[0]['WAT_sha256']==inputproof['NPC5719_wat_sha256']
    assert functions[3]['WAT_sha256']==inputproof['seed6786_wat_sha256']==sha(Path(prepared['seed_proof_source']))==prepared['seed_proof_sha256']
    assert functions[5]['WAT_sha256']==inputproof['opening1108_wat_sha256']
    for key,idx in [('None_argument_path',5719),('opening_four_None_calls',1108),('LCG',6786),('selectedP_seed184_scratch3128',6786)]:
        p=inputproof[key];text='\n'.join(wat[idx].splitlines()[p['first_line_1based']-1:p['last_line_1based']]);assert text==p['text']
    assert inputproof['opening_four_None_calls']['text'].count('call 5719')==4
    assert 'i32.const 2944\n          i32.add\n          local.tee 3' in wat[6786] and 'local.get 3\n          local.get 2\n          call 1600' in wat[6786]
    seed=(0*6364136223846793005+1442695040888963407)&((1<<64)-1);derived_rng=constructor_rng(seed)
    assert str(seed)==inputproof['controlledAppseed0_LCG_u64']
    cases=json.loads((CASE/'inputs.json').read_text());expected=json.loads((CASE/'expected.json').read_text());actual=[json.loads(x)for x in(CASE/'stdout.jsonl').read_text().splitlines()];assert len(cases)==len(expected)==len(actual)==22
    counts=Counter();details=[];modes=Counter();producer_packets=prefix_packets=0
    allowed=set(range(1720,1736))|set(range(1784,1796))|set(range(1880,1892))|set(range(2408,2412))
    for case,want,got in zip(cases,expected,actual):
        assert case['id']==want['id']==got['id'] and case==want['input']
        assert case['player_xyz'][:2]==scalars['center_xy_bits']
        if case['preserve_constructor_rng']:assert case['id']==0 and case['rng_words']==derived_rng and case['counter']==10
        assert got['constructor_rng_before']==derived_rng and got['constructor_counter_before']==10 and int(got['App4928_after_controlled_seed0_LCG'])==seed
        assert got['preserve_constructor_rng']==case['preserve_constructor_rng']
        if case['id']==0:assert world.height(*case['player_xyz'][:2])==case['player_xyz'][2]
        modes['caller4'if case['initial_backing']else'reserve0to4']+=1
        answer,trace=reference(case,world,nav,scalars,tables,definition,speeds);assert answer==want['expected'];details.extend(trace)
        assert len(got['answers'])==len(got['raw_games2592'])==4
        declared=bytes.fromhex(got['declared_game_before_hex']);assert len(declared)==2592 and list(struct.unpack_from('<4I',declared,1720))==case['rng_words'] and u32(declared,2408)==case['counter']
        assert list(struct.unpack_from('<3I',declared,1416))==case['player_xyz'] and list(struct.unpack_from('<2I',declared,1736))==case['velocity_xy']
        assert u32(declared,2348)==20544696 and u64(declared,1336)==0 and u32(declared,1792)==u32(declared,1888)==0
        assert declared[2587]==0
        assert (u32(declared,2516),u32(declared,2540),u32(declared,1432),u32(declared,2352),u32(declared,400))==(0x3f800000,1,1,0,0) and all(declared[p]==0 for p in [2582,387,2568])
        previous=declared
        for stage,(a,w,observation)in enumerate(zip(answer,got['answers'],got['raw_games2592'])):
            assert {k:v for k,v in a.items()if k!='records432_cells'}=={k:v for k,v in w.items()if k!='records432_hex'}
            assert len(w['records432_hex'])==4
            for cells,row in zip(a['records432_cells'],w['records432_hex']):
                observed=bytes.fromhex(row);assert len(cells)==len(observed)==432
                for wanted,seen in zip(cells,observed):
                    if wanted is None:counts['unknown']+=1;counts['unknown_nonzero']+=seen!=0
                    else:assert wanted==seen;counts['known']+=1
            before=bytes.fromhex(observation['before_hex']);after=bytes.fromhex(observation['after_hex']);assert before==previous and len(after)==2592
            assert list(struct.unpack_from('<4I',after,1720))==a['rng_words'] and u32(after,2408)==a['counter'] and u32(after,1784)==4 and u32(after,1792)==u32(after,1888)==stage+1
            changed=[p for p,(x,y)in enumerate(zip(before,after))if x!=y];assert changed==observation['changed_bytes'] and set(changed)<=allowed
            for p,(x,y)in enumerate(zip(before,after)):
                if p not in allowed:assert x==y;counts['Game_conserved_nonowned_bytes']+=1
            counts['Game_RNG_bytes']+=16;counts['Game_counter_bytes']+=4
            prefix_packets+=len(w['packets']);producer_packets+=1;previous=after
        assert got['option16_hex']=='00000000'+'a5'*12 and got['option_canaries']==['c3'*16,'d7'*16] and got['result_canaries']==['c3'*16,'d7'*16] and got['stack_after']==1048576
        assert got['world124_before_hex']==got['world124_after_hex'] and got['world_data_digest_before']==got['world_data_digest_after']
        header=bytes.fromhex(got['world124_before_hex']);assert u32(header,56)==0xffffffff and header[120]==0 and u32(header,116)==scalars['fallback_height_bits']
        path=case['distance_map'];view=got['path_view']
        if path is None:assert view is None and u32(declared,2368)==0
        else:
            assert u32(declared,2368)==view['p'] and u32(bytes.fromhex(view['view32_hex']),24)==path['field24']
            if path['fill_u16']is None:assert view['ptr']is None and all(not z['position_reference_diagnostics'].get('path_cost_reads')for z in trace)
            else:assert view['n']==path['count'] and view['array_sha256']==hashlib.sha256(struct.pack('<H',path['fill_u16'])*path['count']).hexdigest()
    assert (counts['known'],counts['unknown'],counts['unknown_nonzero'])==(101598,50466,24297) and modes=={'caller4':9,'reserve0to4':13}
    assert (producer_packets,prefix_packets)==(88,220) and counts['Game_conserved_nonowned_bytes']==224224
    assert runtime==receipt['runtime'] and (runtime['cases'],runtime['full5719_calls'],runtime['snapshot_restores'])==(22,88,22)
    assert runtime['original_none_position_argument'] and runtime['internal8740_calls_notdirectlyinstrumented'] and runtime['actual_host_calls']==0 and runtime['denied_imports']==882
    assert (runtime['allocator_calls'],runtime['stack_checks'],runtime['peak_memory_bytes'],runtime['memory_cap_bytes'])==(58,146,111804416,268435456)
    for filename in ['process-terminal.json','validator-terminal.json']:
        terminal=json.loads((CASE/filename).read_text());assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing'] and terminal['seconds']<60
    audit=json.loads((CASE/'expectation-read-audit.json').read_text());assert audit['kind']=='Pythonopen_audit_notOSsyscallaudit' and not audit['forbidden']
    assert all(e['allowed'] and str(Path(receipt['world_provenance']['receipt']).parent)in e['path'] for e in audit['events'])
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('natural-npc139-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=dict(status='pass_with_declared_healthy_snapshot_four_None_consumer_limits',reviewer='/root/self_buffs119_review',author='/root/stats138_review',comparison_sha256=COMPARISON_SHA,author_handoff_sha256=HANDOFF_SHA,script_sha256=sha(Path(__file__)),pure_reference_helpers=HELPERS,
                cases=22,full5719_calls_checked=88,mismatches=0,original_executions_by_reviewer=0,author_model_checker_builder_executions_by_reviewer=0,allocation_modes=dict(modes),counts=dict(counts),new169_messages=88,cumulative169_prefix_observations=220,
                source_closure=sources,source_import_edges=edges,author_files=handoff['frozen_author_files'],static_functions=functions,nonexport_sections_byte_identical=True,whole_original_retained=True,
                static_input_proof_sha256=sha(CASE/'static-input-proof.json'),controlled_seed_lineage=dict(App_seed_before=0,LCG_after=str(seed),constructor_PCG_words=derived_rng,firstcase_not_overwritten=True,other21_controlled_overrides=True),
                runtime=runtime,author_owned_process=receipt['process'],details=details,seconds=time.monotonic()-start,
                limitations=['22restored healthyv2snapshot fixtures,88full5719 withNone position. No fresh1600/6786/1108 runs in this batch;firstcase preserves supplied snapshotconstructorRNG/counter,independently predicted from explicitly controlled Appseed0 LCG→1600PCG only.',
                             'Everyposition8740 occurs before thatNPCyaw/jitter;all88finalRNGstates/XYZ/full169/recordmasks rechecked. Internal8740 calls,attempt/draw/shrink counts inferred by WAT/reference,not directly instrumented original counters.',
                             'DefaultElwynn definition0,time0/mode0/member1/level1/playerGUID0/centerXY only,explicit velocities/Z/pathMap and21RNG/counter overrides. This is a naturalNone callsite component,not natural fullApp/profile/world ownership or complete1108.',
                             '9caller432backing cases and13actual reserve0to4 cases. Allfour slots are compared with101598known+50466None;24297nonzero unknown observations never fill unknown cells.',
                             '224224Game nonowned byte occurrences are conserved;fourRNGwords andcounter are predicted,vector/packetheader pointer and capacity allocations remain observed with declared count/domain checks. Other constructorGame fields are not independently reconstructed here.',
                             'Full169payloads independently predicted:220cumulative prefix observations are88new producer messages. No other packets/entity callbacks/UI/fullgame/native acceptance.',
                             'WorldRc124/range digest and pathimmutability are frozenrunner observations/guards,not reviewer snapshot parsing or independent Rc production.146stack checks are runner assertions/aggregate,not serialized per call.',
                             'Expectation reads raw139canonical only;no reference snapshotmemory read. Current fixedWAT/validated pure reference functions reused as algorithms,not oldbehavior passingcases. Trace script/static-input proof is posthoc bound,not retroactively partof31experimental pre-run sources.',
                             'Pythonopen audit is not OSsyscall audit. Source opening1108 fourNone window is static evidence only;its preceding1795 and other opening logic were not executed/reconstructed by this batch.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),cases=22,calls=88,known=counts['known'],unknown=counts['unknown'],seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
