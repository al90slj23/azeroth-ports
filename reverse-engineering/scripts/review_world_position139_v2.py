#!/usr/bin/env python3
"""Read-only independent corrected139 position85 review; no author execution."""
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import ast,hashlib,json,sqlite3,struct,time
from review_combat139 import bits,fp,f32,local_closure,parse_module,sha,u32
from review_world_position139 import Reference,load_world,hypot_ref,direct_norm

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'evidence/world-position139-v2-oracle-20261102T042946.182486Z'
OLD=ROOT/'evidence/world-position139-oracle-20261102T035151.444640Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
STATIC=ROOT/'evidence/world-position139-static-20261102T033613.062984Z'
COMPARISON_SHA='0bcff452e5ad0cb93399e3e215200309bfe02d8d368afe0b0b33a3b0f1ab8b3b'
HANDOFF_SHA='37ca3314afb61927725ce9985df88792a87408fbc7de9953b99575b29a68be75'
SOURCE_SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
PURE_HELPERS={'scripts/review_world_position139.py':'d842c619169a582ab8eb540cab2829233eb633bbd79d10ab674c50e71c92ab7e',
              'scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9',
              'scripts/review_npc_spawn139.py':'aa1c8a9d5ca4fe0363f97cbdad71f13ce00ebccf238fe89b213f354627ef5074',
              'scripts/review_player_motion135.py':'8a339b74435adbc4abcf5aff7f3a25a24d5f8495653e42135f06aa94230de2b2'}


def save(p,value):p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def correction_ast():
    old=ast.parse((ROOT/'reconstruction/core_spec/world_position139.py').read_text())
    new=ast.parse((ROOT/'reconstruction/core_spec/world_position139_v2.py').read_text().replace('139V2','139'))
    functions=lambda tree:{n.name:n for n in tree.body if isinstance(n,ast.FunctionDef)}
    a,b=functions(old),functions(new)
    assert ast.dump(a['sample_spawn_position'])==ast.dump(b['sample_spawn_position'])
    aa,bb=a['sample_random_position'],b['sample_random_position']
    find=lambda n:[x for x in ast.walk(n) if isinstance(x,ast.Assign) and len(x.targets)==1 and isinstance(x.targets[0],ast.Name) and x.targets[0].id=='distance']
    ax,bx=find(aa),find(bb);assert len(ax)==len(bx)==1
    assert ast.unparse(ax[0].value)=='hypot_bits(dx, dy)' and ast.unparse(bx[0].value)=='sqrt_bits(f.add(f.mul(dx, dx), f.mul(dy, dy)))'
    bx[0].value=ax[0].value
    assert ast.dump(aa)==ast.dump(bb)
    return dict(spawn_AST_unchanged=True,random_only_expression_change='f32(dx*dx)+f32(dy*dy), then f32sqrt',independent_AST_normalization=True)


def old_hypot_first_trial(case,world,nav,scalars,tables):
    ref=Reference(case['input'],world,nav,scalars,tables);s=case['input'];cx,cy=map(fp,scalars['center_xy_bits']);limit=fp(scalars['radius_bits'])
    angle=f32(ref.uniform(0,0x40c90fdb)+0.);radius=ref.uniform(s['low_radius_bits'],s['high_radius_bits']);x,y=ref.xy(angle,radius);dx,dy=f32(x-cx),f32(y-cy)
    distance=hypot_ref(dx,dy);direct=direct_norm(dx,dy);assert distance>limit and direct>limit and distance!=direct
    y=f32(cy+f32(limit*f32(dy/distance)));x=f32(cx+f32(limit*f32(dx/distance)));z=ref.height(x,y);value,_=ref.probe(x,y)
    assert not value and z is not None and abs(f32(z-fp(s['player_xyz'][2])))<25
    return dict(position_bits=[bits(x),bits(y),bits(z)],rng_words=list(ref.words))


def main():
    start=time.monotonic();assert sha(CASE/'comparison.json')==COMPARISON_SHA and sha(CASE/'task-handoff.json')==HANDOFF_SHA and sha(SOURCE)==SOURCE_SHA
    for name,digest in PURE_HELPERS.items():assert sha(ROOT/name)==digest
    receipt=json.loads((CASE/'comparison.json').read_text());prepared=json.loads((CASE/'prepared.json').read_text());handoff=json.loads((CASE/'task-handoff.json').read_text());manifest=json.loads((CASE/'manifest.json').read_text());runtime=json.loads((CASE/'runtime.json').read_text())
    assert len(handoff['frozen_author_files'])==8
    for name,digest in handoff['frozen_author_files'].items():assert sha(ROOT/name)==digest
    sources=receipt['source_before'];assert sources==receipt['source_after']==prepared['source_before'] and len(sources)==26
    for name,digest in sources.items():assert sha(ROOT/name)==digest==sha(CASE/'source-snapshot'/name)
    edges=local_closure(sources);assert edges==sorted(receipt['source_import_edges']) and len(edges)==51
    assert len([p for p in sources if p.startswith('reconstruction/')])==14
    for name,digest in receipt['artifacts'].items():assert sha(CASE/name)==digest
    for name,digest in prepared['frozen'].items():assert sha(CASE/name)==digest
    assert sha(CASE/'source-correction-proof.json')==handoff['source_correction_sha256'] and sha(CASE/'regression-and-counterexamples.json')==handoff['readback_sha256']
    correction=correction_ast()
    assert receipt['expected_before_original'] and prepared['expected_before_original'] and not receipt['expectations_from_originalmemory'] and not prepared['original_input_contains_expected']
    assert receipt['model_diagnostics_notdirectoriginalcounters'] and receipt['healthy_v2_context'] and not receipt['old_bad5d940snapshot_loaded']
    world,nav,scalars=load_world(receipt['world_provenance']);assert not scalars['flat_present'] and not scalars['primary_present']
    raw=SOURCE.read_bytes();original=parse_module(raw);changed=(CASE/manifest['module_file']).read_bytes();modified=parse_module(changed)
    assert sha(CASE/manifest['module_file'])==sha(OLD/'world-position139-original.wasm')=='6988ceb9689c8c8389aa88cb5cd19cfca174b7b20d95512f7d8912fa334cf271'
    for a,b in zip(original['sections'],modified['sections']):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    assert len(original['sections'])==len(modified['sections']) and len(original['imports'])==882
    export_delta=[('research139_position_spawn',0,8740),('research139_position_random',0,13563),('research139_position_stack0',3,0)]
    assert modified['exports']==original['exports']+export_delta
    assert original['types'][original['decl'][8740-882]]==('7f7f7d7d7d','') and original['types'][original['decl'][13563-882]]==('7f7f7d7d','')
    def data(address,size):
        out=bytearray(size)
        for base,offset,count in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+count,address+size)
            if lo<hi:out[lo-address:hi-address]=raw[offset+lo-base:offset+hi-base]
        return out
    tables=[list(struct.unpack('<4f',data(p,16))) for p in [14426512,14426528,14426544,14426560]]
    proof=json.loads((STATIC/'proof.json').read_text());assert sha(STATIC/'proof.json')==receipt['static_proof_sha256']
    db=sqlite3.connect(f'file:{PROFILE}/index.sqlite?mode=ro',uri=True);db.row_factory=sqlite3.Row;db.execute('pragma query_only=on');static=[]
    with (PROFILE/'official-0.139.0-full.wat').open('rb')as stream:
        for key,row in proof['functions'].items():
            idx=int(key);loc=dict(db.execute('select * from functions where idx=?',(idx,)).fetchone());a,z=original['bodies'][idx];assert(a,z)==(loc['body_start'],loc['body_end']) and hashlib.sha256(raw[a:z]).hexdigest()==row['body_sha256']
            stream.seek(loc['wat_start']);text=stream.read(loc['wat_end']-loc['wat_start']);assert text==(STATIC/f'{idx}.wat').read_bytes();static.append(dict(index=idx,body_sha256=row['body_sha256'],WAT_sha256=hashlib.sha256(text).hexdigest()))
    assert 'call 50441' not in (STATIC/'13563.wat').read_text() and 'call 50441' in (STATIC/'8740.wat').read_text()
    validator=manifest['validator'];assert validator['reused_for_identical_binary'] and manifest['new_static_validator_processes']==0 and manifest['Node_fresh_compile_required'] and not manifest['old_model_acceptance_transferred']
    vp=Path(validator['source']);assert sha(vp)==validator['source_sha256'];v=json.loads(vp.read_text());assert v==validator['prior_receipt'] and v['exit_code']==0 and v['pid_missing'] and v['pgid_missing']
    runner=(ROOT/'scripts/run_world_position139_v2_oracle.mjs').read_text();assert 'WebAssembly.compile(bytes)' in runner and 'WebAssembly.instantiate(module,bindings)' in runner and 'hostCount++;throw Error' in runner
    checker=(ROOT/'scripts/check_world_position139_v2.py').read_text();assert "['case_input']['input']" in checker and "[x['input']for x" in checker
    assert 'result=sample_random_position' in checker or 'sample_random_position(state,world)' in checker
    audit=json.loads((CASE/'expectation-read-audit.json').read_text());assert audit['kind']=='Pythonopen_audit_notOSsyscallaudit' and not audit['forbidden']
    permitted={str(Path(receipt['world_provenance']['receipt']))}|{str(Path(receipt['world_provenance']['receipt']).parent/r['file'])for r in receipt['world_provenance']['world_artifacts'].values()}|{str(OLD/'inputs.json')}|{x['path']for x in receipt['clamp_input_sources']}
    assert all(x['allowed'] and x['path']in permitted for x in audit['events'])
    for source in receipt['clamp_input_sources']:assert sha(Path(source['path']))==source['sha256']
    cases=json.loads((CASE/'inputs.json').read_text());expected=json.loads((CASE/'expected.json').read_text());actual=[json.loads(x)for x in(CASE/'stdout.jsonl').read_text().splitlines()]
    oldcases=json.loads((OLD/'inputs.json').read_text());oldactual=[json.loads(x)for x in(OLD/'stdout.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(actual)==85 and cases[:80]==oldcases and actual[:80]==oldactual
    ranges=json.loads((CASE/'observed-world-ranges.json').read_text());assert len(ranges['ranges'])==2318 and sum(x['n']for x in ranges['ranges'])==5950608==ranges['bytes']
    nonrng=rngbytes=0;total=Counter();details=[];counterexamples=[];readback=json.loads((CASE/'regression-and-counterexamples.json').read_text())
    for case,want,got in zip(cases,expected,actual):
        assert case['id']==want['id']==got['id'] and case['input']==want['input'] and case['kind']==want['kind']
        ref=Reference(case['input'],world,nav,scalars,tables);xyz=ref.spawn() if case['kind']=='spawn'else ref.random();prediction=dict(position_bits=xyz,rng_words=list(ref.words))
        assert prediction==want['expected']==got['projection'];total.update(ref.count)
        if case['id']>=80:
            assert case['kind']=='random' and ref.count['random_trials']==1
            rejected=old_hypot_first_trial(case,world,nav,scalars,tables);assert rejected!=prediction and rejected['rng_words']==prediction['rng_words']
            entry=readback['counterexamples'][case['id']-80];assert entry['id']==case['id'] and entry['actual']==entry['v2_expected']==prediction and entry['old_hypot_reference']==rejected and entry['old_reference_rejected_by_original']
            counterexamples.append(dict(id=case['id'],actual=prediction,independent_old_hypot_prediction=rejected,old_rule_rejected=True))
        before=bytes.fromhex(got['raw_game_before_hex']);after=bytes.fromhex(got['raw_game_after_hex']);assert len(before)==len(after)==2592
        assert list(struct.unpack_from('<4I',before,1720))==case['input']['rng_words'] and list(struct.unpack_from('<4I',after,1720))==prediction['rng_words']
        assert list(struct.unpack_from('<3I',before,1416))==case['input']['player_xyz'] and list(struct.unpack_from('<2I',before,1736))==case['input']['velocity_xy']
        assert u32(before,2348)==20544696 and before[2587]==0
        for p,(a,b)in enumerate(zip(before,after)):
            if 1720<=p<1736:rngbytes+=1
            else:assert a==b;nonrng+=1
        assert got['world124_before_hex']==got['world124_after_hex'] and got['world_data_digest_before']==got['world_data_digest_after']==ranges['digest'] and got['world_ranges']==2318
        output=bytes.fromhex(got['output16_hex']);assert list(struct.unpack_from('<3I',output))==xyz and output[12:]==bytes([0xa5]*4)
        assert got['before16_hex']=='c3'*16 and got['after16_hex']=='d7'*16 and got['stack_after']==1048576
        path=case['input']['distance_map'];view=got['path_view']
        if path is None:assert view is None and u32(before,2368)==0
        else:
            buf=bytes.fromhex(view['before_hex']);assert u32(buf,24)==path['field24'] and u32(before,2368)==view['pointer']
            if path['fill_u16']is None:assert ref.count['path_cost_reads']==0 and view['values_pointer']is None
            else:assert view['values_count']==path['count'] and view['values_sha256']==hashlib.sha256(struct.pack('<H',path['fill_u16'])*path['count']).hexdigest()
        details.append(dict(id=case['id'],kind=case['kind'],reference_diagnostics_not_original_counters=dict(ref.count)))
    assert (nonrng,rngbytes)==(218960,1360) and len(counterexamples)==5
    assert runtime==receipt['runtime'] and (runtime['cases'],runtime['full8740_direct_calls'],runtime['full13563_direct_calls'])==(85,63,22)
    assert (runtime['snapshot_restores'],runtime['allocator_calls'],runtime['stack_checks'])==(85,107,192) and runtime['actual_host_calls']==0 and runtime['denied_imports']==882
    assert runtime['peak_memory_bytes']==111804416 and runtime['memory_cap_bytes']==268435456 and runtime['healthy_v2_input']
    terminal=json.loads((CASE/'process-terminal.json').read_text());assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing'] and terminal['seconds']<60
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-position139-v2-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    result=dict(status='pass_with_declared_healthy_snapshot_consumer_limits',reviewer='/root/self_buffs119_review',author='/root/stats138_review',comparison_sha256=COMPARISON_SHA,author_handoff_sha256=HANDOFF_SHA,script_sha256=sha(Path(__file__)),pure_reference_helpers=PURE_HELPERS,
                original_executions_by_reviewer=0,author_production_checker_builder_executions_by_reviewer=0,cases=85,full8740_direct=63,full13563_direct=22,mismatches=0,old80_inputs_and_full_actual_identical=True,new85_recomputed_not_old_pass_transfer=True,
                new5_actual_counterexamples=counterexamples,correction_AST=correction,source_closure=sources,source_import_edges=edges,author_files=handoff['frozen_author_files'],static_functions=static,nonexport_sections_byte_identical=True,
                nonRNG_Game_bytes=nonrng,RNG_Game_bytes=rngbytes,reference_counters_not_original_observations=dict(total),details=details,runtime=runtime,author_owned_process=terminal,
                world_ranges_observation=dict(count=2318,bytes=5950608,digest=ranges['digest'],as_read_ranges_sha256=sha(CASE/'observed-world-ranges.json')),seconds=time.monotonic()-start,
                limitations=['85fresh controlled original invocations onhealthyv2snapshots,not85natural constructors or independent Rc owners.OnlycurrentElwynn/no-primary/nonflat context and explicitplayer/RNG/pathMap inputs.',
                             '13563 correction is callsite f32square/f32sum/f32sqrt;8740 stilluses50441hypot.5new original cases distinguish rules;80regression results remain evidence of these inputs only,not oldv1source acceptance.',
                             'Expectation reference reads raw139canonical assets only,never snapshot memory.Independent geometry math is rebound to current139 getters through previous static/independent worldreview;no oldbehavior pass transferred.',
                             '192stackchecks are runner assertions/aggregate.2318ranges/5950608B and path-view immutability are original runner observations,not independent world production or reviewer rehash of memory.218960nonRNG and1360RNG Game byte occurrences directlychecked.',
                             'Attempts/draws/shrinks/internal13563fallback counts are modeldiagnostics;only63full8740+22direct13563 exports countasobserved entry calls.',
                             'Same original exportbinary reused onlyfor admission and prior static validator;Node compiled/instantiated fresh for85.45s preparation timeout/unjournaled initialvalidator PID and6pilot calls retained,not formal coverage or claimed clean ownedhistory.',
                             'Supplementary stimulus/correction scripts and reports are posthoc hashes,not retroactively added to26experimental source-before entries.Only input fields from counterexample files are used to recompute expected values.',
                             'Pythonopen audit is notOSsyscall audit. No naturalpathMapproducer/App/WorldRc ownership/full1108/native/fullgame acceptance;oldv1notaccepted receipts remainunchanged.'])
    save(out/'review.json',result);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),cases=85,calls8740=63,calls13563=22,counterexamples=5,seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
