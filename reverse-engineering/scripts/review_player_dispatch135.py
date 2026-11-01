#!/usr/bin/env python3
"""Independent read-only full968 local-route review; never executes production.

The prior independent2328 arithmetic reader is reused explicitly, not presented
as a second restoration of that helper. Setup observations remain inputs.
"""
from pathlib import Path
from collections import Counter
import argparse,hashlib,json,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
import review_player_motion135 as M
ROOT=M.ROOT
RUN=ROOT/'evidence/player-motion135-oracle-20261101T231626.255308Z'
EXPECTED='0513dc6d834df50dd845f032a417d6922accde21c575141a0e3c45516316349d'
PRIOR=ROOT/'reports/2026-11-02-player-motion0135-independent-review.json'
PRIOR_SHA='4ff4eb4a63b6ed8a626321d1336c082aab7caeeb1162469c46c4e2230af8b0ff'

def static_proofs(original,out):
    db=sqlite3.connect((M.PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');functions={};texts={}
    with(M.PROFILE/'official-0.135.1-full.wat').open('rb')as stream:
        for idx in(968,17726,6730,1089):
            row=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone())
            n=row['wat_end']-row['wat_start'];assert n<=6*1024*1024
            stream.seek(row['wat_start']);data=stream.read(n);body=original[row['body_start']:row['body_end']]
            assert data.splitlines()[0].startswith(f'  (func (;{idx};)'.encode())
            texts[idx]=data.decode().splitlines();functions[idx]=dict(body_start=row['body_start'],body_end=row['body_end'],body_sha256=M.digest(body),wat_bytes=n,wat_sha256=M.digest(data))
    windows={}
    for name,idx,a,b,tokens in(
        ('canonical_motion_opcodes',968,545,584,('i32.const 181','i32.const 23','i32.const 218','i32.const 1048579','br_if 32')),
        ('flags_and_timestamp_LE',968,13752,13895,('i32.load8_u','i32.const 8','i32.const 16','i32.const 24','i32.store offset=476','i32.store offset=136')),
        ('XY_LE',968,13896,14050,('i32.const 9','i32.const 13','i32.load8_u offset=3','local.set 19','local.set 12')),
        ('Z_facing_LE',968,14051,14198,('i32.const 17','i32.const 21','i32.store offset=248','i32.store offset=252','i32.store offset=256','i32.store offset=192')),
        ('reject_nonfinite_before_owner_writes',968,14199,14222,('i32.const 2147483647','i32.const 2139095039','i32.gt_u','br_if 104')),
        ('route0_inline_owner',968,14223,14308,('local.get 1','i32.const 1','i32.load offset=2724','i64.load offset=2608','i64.load offset=16','i32.const 16','local.set 20','local.get 10','i32.eqz')),
        ('local_player2328_consumer',968,14952,14991,('i32.store offset=2496','i32.store offset=440','f32.convert_i32_u','f32.const 0x1.f4p+9','f32.div','f32.store offset=444','call 2328','i32.const 0','call 17726')),
        ('route0_skips_network_send',968,15000,15039,('local.get 1','i32.const 1','i32.ne','br_if 1','i64.const 3','br_if 105')),
        ('mode0_full17726_noop',17726,8,13,('i32.load8_u offset=2582','i32.const 1','i32.ne','br_if 0'))):
        text='\n'.join(x.strip()for x in texts[idx][a-1:b]);assert all(t in text for t in tokens),(name,tokens)
        windows[name]=dict(function=idx,first_line=a,last_line=b,text=text,sha256=M.digest(text.encode()))
    assert windows['reject_nonfinite_before_owner_writes']['text'].count('i32.gt_u')==4
    return dict(functions=functions,windows=windows,full_module_WAT_scanned=False)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);a=parser.parse_args()
    out=a.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();start=time.monotonic()
    own=Path(__file__);dependencies={str(p.relative_to(ROOT)):M.sha(p)for p in(own,Path(M.__file__))}
    for name,h in dependencies.items():
        p=out/'reviewer-source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert M.sha(p)==h
    assert M.sha(PRIOR)==PRIOR_SHA;prior=M.load(PRIOR)
    assert prior['reviewer_sha256']==dependencies['scripts/review_player_motion135.py']
    report=M.load(RUN/'dispatch-comparison.json');assert M.sha(RUN/'dispatch-comparison.json')==EXPECTED
    assert report['cases']==report['actual_cases']==33 and report['differences']==0 and not report['difference_rows']
    sources=report['source_sha256_before'];assert len(sources)==21 and sources==report['source_sha256_after']
    for name,h in sources.items():assert M.sha(ROOT/name)==M.sha(RUN/'source-snapshot'/name)==h,name
    edges=M.source_edges(RUN/'source-snapshot',sources);assert len(edges)==45 and edges==[tuple(x)for x in report['complete_static_local_import_edges']]
    assert report['closure_verified_before_expectations']and report['target_expected_before_original']and not report['input_contains_expected']
    assert report['setup_observation_used_as_explicit_prestate']and not report['independent_constructor_validation']
    for name,h in report['artifacts'].items():assert M.sha(RUN/name)==h
    artifacts={name:M.sha(RUN/name)for name in(*report['artifacts'],'dispatch-comparison.json','setup-runtime.json','cases-runtime.json','setup-results.jsonl','setup-stderr.log')}
    original=M.ORIGINAL.read_bytes();assert M.digest(original)==M.ORIGINAL_SHA and len(original)==90959080
    manifest=M.load(RUN/'manifest.json');module=(RUN/manifest['module_file']).read_bytes();assert M.digest(module)==manifest['module_sha256']and len(module)==manifest['module_bytes']
    before,after=M.sections(original),M.sections(module);assert [x[0]for x in before]==[x[0]for x in after]and not any(x[0]==8 for x in before)
    for x,y in zip(before,after):
        if x[0]!=7:assert original[x[1]:x[3]]==module[y[1]:y[3]]
    old=M.exports(original,next(x for x in before if x[0]==7));new=M.exports(module,next(x for x in after if x[0]==7))
    assert new==old+[( 'research_player_motion135_move_player',0,2328),('research_player_motion135_motion_dispatch',0,968),('research_player_motion135_stack',3,0),('research_player_dispatch135_cached_construct',0,6730),('research_player_dispatch135_begin_run',0,1089)]
    proofs=static_proofs(original,out)
    for role in manifest['roles']+manifest['additional_setup_roles']:
        idx=role['index']
        if idx in proofs['functions']:assert proofs['functions'][idx]['body_sha256']==role['body_sha256']
    snapshot=M.SNAPSHOT.read_bytes();assert len(snapshot)==166395904 and M.digest(snapshot)==M.SNAPSHOT_SHA
    world=M.World(snapshot,M.R);assert len(world.ranges)==2318
    context=M.load(RUN/'setup-context.json');assert M.sha(RUN/'setup-context.json')==report['setup_context_sha256']
    App,G,R=context['App'],context['G'],context['world_pointer'];assert(App,G,R)==(14549000,14549016,26204808)
    assert context['full_setup_functions']==[6730,1089]and context['setup_target968_calls']==context['original_host_calls']==0
    assert context['stack']==1048576 and not context['completeApp_producer']and not context['worldRc_forged']and not context['externref_forged']
    assert context['declared_app_tags']==dict(inline_game_pre6730='2',network2608='2')
    app=bytes.fromhex(context['app5168_hex']);game=bytes.fromhex(context['game2592_hex']);assert len(app)==5168 and len(game)==2592 and app[16:2608]==game
    assert context['app_original5168_hex']==snapshot[App:App+5168].hex()
    assert int.from_bytes(app[2608:2616],'little')==2 and game[2582]==0 and game[2587]==1 and M.u(game,2348)==R
    raw_world=bytes.fromhex(context['world124_hex']);assert len(raw_world)==124
    assert context['old_world_refcount']==M.u(world.header)==2 and context['world_refcount']==M.u(raw_world)==3
    assert raw_world[4:]==world.header[4:]
    fixture=M.load(RUN/'fixtures.json');inputs=M.load(RUN/'inputs.json');actual=[json.loads(x)for x in(RUN/'cases-results.jsonl').read_text().splitlines()]
    assert len(fixture)==len(inputs)==len(actual)==33
    config=M.load(RUN/'cases-config.json');setup_config=M.load(RUN/'setup-config.json')
    common=dict(snapshot_path=str(M.SNAPSHOT),snapshot_sha256=M.SNAPSHOT_SHA,app_pointer=App,world_pointer=R,world_ranges=[list(x)for x in world.ranges])
    assert setup_config==common and config==dict(common,input_path=str(RUN/'inputs.json'),input_sha256=M.sha(RUN/'inputs.json'),context_sha256=M.sha(RUN/'setup-context.json'))
    zone=M.static_reader(original)(5456016,152);counts=Counter();groups=Counter();opcode_counts=Counter();packets_by_opcode=Counter();branches=Counter();unmodified_app=Counter();scalar_writes=Counter()
    allowed=set(range(181,199))|set(range(200,204))|{218,219,238}
    for c,inp,got in zip(fixture,inputs,actual):
        assert c['id']==inp['id']==got['id']and inp==c['input']and set(inp)=={'id','opcode','payload24_hex','patch_words'}
        raw=bytearray(game)
        for o,v in inp['patch_words']:M.put(raw,o,v)
        before_app=bytearray(app);before_app[16:2608]=raw
        assert raw.hex()==got['game_before_hex']==c['expected']['game_before_hex']
        assert before_app.hex()==got['app_before_hex']==c['expected']['app_before_hex']
        payload=bytes.fromhex(inp['payload24_hex']);assert len(payload)==24 and inp['opcode']in allowed
        flags,ms,x,y,z,facing=struct.unpack('<6I',payload);finite=all((v&0x7fffffff)<=0x7f7fffff for v in(x,y,z,facing))
        writes=[];packets=[]
        if finite:
            counts['finite_inputs']+=1
            clock=M.div(M.B(float(ms)),M.B(1000));seed=bytearray(raw)
            for o,v in((2496,flags),(440,1),(444,clock)):M.put(seed,o,v);writes.append((o,v))
            cells,ret,packets,motion_writes,branch=M.reference(seed,(x,y,z),facing,world,zone,counts)
            writes+=motion_writes;M.put(cells,440,0);writes.append((440,0));result=bytes(cells)
            branches[branch]+=1;assert M.u(result,2496)==flags and M.u(result,444)==clock and M.u(result,440)==0
        else:
            counts['nonfinite_before_mutation_rejections']+=1;result=bytes(raw)
            bad=[j for j,v in enumerate((x,y,z,facing))if(v&0x7fffffff)>0x7f7fffff];assert len(bad)==1
            counts['nonfinite_field_'+str(bad[0])]+=1
        expected_app=bytearray(before_app);expected_app[16:2608]=result
        assert result.hex()==got['game_after_hex']==c['expected']['game_after_hex']
        assert expected_app.hex()==got['app_after_hex']==c['expected']['app_after_hex']
        assert packets==got['packets']==c['expected']['packets']
        assert [list(x)for x in writes]==c['diagnostic']['scalar_writes']and c['diagnostic']['rejected_nonfinite']==(not finite)
        after_app=bytes.fromhex(got['app_after_hex']);assert before_app[:16]==after_app[:16]and before_app[2608:]==after_app[2608:]
        counts['strict_game_bytes']+=2592;counts['strict_app_bytes']+=5168;unmodified_app['outside_inline_Game_bytes']+=5168-2592
        assigned={j for o,v in writes for j in range(o,o+4)};assert all(raw[j]==result[j]for j in range(2592)if j not in assigned)
        counts['unassigned_Game_bytes_unchanged']+=2592-len(assigned)
        qb,qa=got['queue_before'],got['queue_after'];assert tuple(qb[k]for k in('capacity','pointer','count'))==struct.unpack_from('<3I',raw,1880)
        assert tuple(qa[k]for k in('capacity','pointer','count'))==struct.unpack_from('<3I',result,1880)
        assert qb['capacity']==qa['capacity']and qb['pointer']==qa['pointer']and qa['count']==qb['count']+len(packets)
        assert got['world_before_hex']==got['world_after_hex']==context['world124_hex']
        assert(got['stack_after'],got['host_calls'],got['full_target_function'],got['same_inline_G'])==(1048576,0,968,G)
        assert got['route']==[0,0]and got['setup_functions']==[6730,1089]and got['partialApp_fixture']
        groups[c['group']]+=1;opcode_counts[inp['opcode']]+=1;packets_by_opcode.update(p[0]for p in packets);scalar_writes.update(o for o,v in writes)
    assert dict(groups)==report['groups']and counts['finite_inputs']==21 and counts['nonfinite_before_mutation_rejections']==12
    assert len(opcode_counts)==12 and sum(packets_by_opcode.values())==7
    process={}
    for phase,key in(('setup','setup_process'),('cases','target_process')):
        p=M.load(RUN/(phase+'-terminal.json'));assert p==report[key]
        assert p['exit_code']==0 and p['pid_missing']and p['pgid_missing']and p['seconds']<p['deadline_seconds']==60
        assert M.missing(p['pid'])is True and M.missing(p['pgid'],True)is True;process[phase]=p
    for phase,key,n,target in(('setup','setup_runtime',1,0),('cases','runtime',33,33)):
        rt=M.load(RUN/(phase+'-runtime.json'));assert rt==report[key]
        assert(rt['cases'],rt['full6730_calls'],rt['full1089_calls'],rt['full968_calls'])==(n,n,n,target)
        assert(rt['host_calls'],rt['denied_imports'],rt['max_memory_bytes'],rt['memory_page_cap'])==(0,878,166395904,4096)
        assert not any(rt[k]for k in('original_bodies_modified','worldRc_forged','externref_forged','completeApp_producer','natural1371Game_install','network_used','user_saves_accessed','app_entry_called'))
        assert(rt['mode2582'],rt['owner_route'],rt['peer'],rt['default_network_tag2608'])==(0,0,0,2)
    assert all(M.sha(ROOT/n)==h for n,h in sources.items())and all(M.sha(ROOT/n)==h for n,h in dependencies.items())
    assert all(M.sha(RUN/n)==h for n,h in artifacts.items())
    M.save(out/'static-proofs.json',proofs)
    value=dict(status='passed_scoped_read_only_full968_localroute_review',version='0.135.1',actual_build='90898d5e3',comparison=str(RUN/'dispatch-comparison.json'),comparison_sha256=EXPECTED,
        source_sha256=sources,source_files=21,production_files=sum(n.startswith('reconstruction/')for n in sources),source_import_edges=edges,artifacts_sha256=artifacts,
        cases=33,target968_original_calls=33,target2328_finite_calls=21,target2328_nonfinite_skips=12,setup6730_calls_separate=34,setup1089_calls_separate=34,setup_observation_cases_not_target_cases=1,
        callee_call_count_evidence_layer='2328/17726 finite21 calls inferred from actual canonical inputs and original968 static branch; not separately instrumented counter',
        counts=dict(counts),groups=dict(groups),opcode_counts=dict(opcode_counts),new_packet_opcodes=dict(packets_by_opcode),motion_branches=dict(branches),unmodified_App=dict(unmodified_app),scalar_write_counts=dict(scalar_writes),
        setup_input_provenance=dict(context_sha256=M.sha(RUN/'setup-context.json'),kind=context['kind'],App=App,G=G,world_pointer=R,network_tag=2,Game_pre6730_tag=2,independent_constructor_validation=False,natural_App1371=False),
        static_proofs_sha256=M.sha(out/'static-proofs.json'),prior_motion_review_sha256=PRIOR_SHA,prior_2328_independent_reader_reused_not_second_restoration=True,
        reviewer_source_sha256=dependencies,original_processes=process,new_original_executions=0,production_model_executions=0,builder_executions=0,checker_executions=0,
        full880_frames=0,complete_games=0,native_executions=0,seconds=time.monotonic()-start,
        limitations=['Typedpartial App setup observation is explicit pre968 input, not independent6730/1089 validation or natural4253/1371 App installation.',
            'Canonical exact24,ownerroute0,peer0,mode0,phase1,12 distinct movement opcodes of25 only.',
            'Full17726 executes its mode0 early return; no nonempty transport/register/broadcast/peer sync acceptance.',
            'Setup world geometry and existingqueueprefix postbytes are not exported; their target invariance is a frozen originalrunner hash/prefix assertion, not independent fullpostmemory reread.',
            'No malformed/truncatedpayload,unknownopcode,199ACK,phase0 begin,UI/joystick inputproducer,network route or complete game.'])
    M.save(out/'review.json',value);print(json.dumps(dict(directory=str(out),review_sha256=M.sha(out/'review.json'),counts=value['counts'],packets=value['new_packet_opcodes'])),flush=True)

if __name__=='__main__':main()
