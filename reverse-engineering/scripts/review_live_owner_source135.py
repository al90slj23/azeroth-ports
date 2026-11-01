#!/usr/bin/env python3
"""Read-only109-case audit of explicit922 scratch source and live backing.

Imports only this reviewer's separate read-only evidence helpers. No product,
oracle, checker, builder or private WASM module is executed.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import argparse, ast, hashlib, json, sys, time, struct

sys.dont_write_bytecode=True
import review_live_owner135 as audit

ROOT=Path(__file__).resolve().parents[1]
RUN=ROOT/'evidence/live-owner135-oracle-20261101T224420.333917Z'
RECEIPT_SHA='85979898b212c591d45bc81dc3c3baf8311b861622e5687c6cefb6aa9965e695'
sha,load,save=audit.sha,audit.load,audit.save


def ref(case,counts,*,materialize=False):
    rows,count,source=audit.reference(case,counts,materialize=materialize)
    if source and(materialize or not case['scratch_source_unresolved']):
        audit.put(rows[source[0]],16,case['scratch_word16_bits'])
    return rows,count,source


def raw_bind(case,raw,runtime):
    result=raw['result'];before=bytes.fromhex(raw['raw_Game_before8192_hex']);after=bytes.fromhex(raw['raw_Game_after8192_hex'])
    assert len(before)==len(after)==8192
    R=lambda data,off:struct.unpack_from('<I',data,off)[0]
    assert(R(before,1704),R(before,1712))==(len(case['physical_live']['storage']),case['physical_live']['count'])
    assert(R(after,1704),R(after,1712),R(after,1708))==(result['physical_live']['capacity'],result['physical_live']['count'],raw['live_pointer'])
    assert result['derived_bits']=={str(o):R(after,o)for o in range(1536,1628,4)}
    assert result['current_hp_bits']==R(after,1440)and result['speed_bits']==R(after,1648)
    assert result['rng_words']==list(struct.unpack_from('<4I',after,1720))==case['level']['rng_words']
    assert result['action_sequence1644']==R(after,1644)==9 and result['message_sequence2412']==R(after,2412)==19
    assert result['basic_hex']==after[1256:1336].hex()==case['basic_hex']and result['cast_owned_hex']==case['cast_owned_hex']
    assert result['phase2587']==after[2587]and result['selection_kind2585']==after[2585]and result['generation_counter2400']==R(after,2400)
    for queue,off,stride in(('raw_packets',1880,16),('raw_notifications',1892,12)):
        q=raw[queue];assert(q['capacity'],q['count'],q['pointer'])==(R(after,off),R(after,off+8),R(after,off+4))
        md=bytes.fromhex(q['metadata_hex']);assert len(md)==q['count']*stride and len(q['active'])==q['count']
        for j,item in enumerate(q['active']):
            cap,ptr,length=struct.unpack_from('<3I',md,j*stride);assert(item['capacity'],item['pointer'],item['length'])==(cap,ptr,length)
            assert length<=cap<=1048576 and len(bytes.fromhex(item['payload_hex']))==length and ptr+length<=runtime['peak_memory_bytes']
            if queue=='raw_packets':assert item['opcode']==struct.unpack_from('<H',md,j*stride+12)[0]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    out=args.output or ROOT/'evidence'/datetime.now(timezone.utc).strftime('live-owner-source135-independent-review-%Y%m%dT%H%M%S.%fZ')
    assert out.resolve().is_relative_to((ROOT/'evidence').resolve());out.mkdir(parents=True,exist_ok=False)
    began=time.monotonic();assert sha(RUN/'comparison.json')==RECEIPT_SHA
    primary=load(RUN/'comparison.json');manifest=load(RUN/'manifest.json');prepared=load(RUN/'prepared.json');runtime=load(RUN/'runtime.json');terminal=load(RUN/'process-terminal.json')
    assert primary['cases']==primary['full_calls']==109 and primary['comparison_complete']and primary['differences']==0
    sources=primary['source_before'];assert sources==primary['source_after']==prepared['source_before']and len(sources)==51
    assert sources=={n:sha(RUN/'source-snapshot'/n)for n in sources}
    before={n:sha(ROOT/n)for n in sources};assert before==sources
    for n in sources:
        if n.startswith('reconstruction/'):
            tree=ast.parse((RUN/'source-snapshot'/n).read_text())
            assert not any(isinstance(node,(ast.Import,ast.ImportFrom))and any(alias.name.split('.')[0]in('os','sys','subprocess','socket','urllib','pathlib')for alias in node.names)for node in ast.walk(tree))
    frozen={n:sha(RUN/n)for n in primary['frozen_artifacts']};assert frozen==primary['frozen_artifacts']==prepared['artifacts']
    other={n:sha(RUN/n)for n in('comparison.json','stdout.jsonl','runtime.json','process-terminal.json','prepared.json','owned-process.json','differences.json')}
    original=audit.ORIGINAL.read_bytes();assert hashlib.sha256(original).hexdigest()==manifest['original_sha256']==primary['original_sha256']
    changed=(RUN/manifest['module_file']).read_bytes();s1=audit.sections(original);s2=audit.sections(changed)
    assert[s[0]for s in s1]==[s[0]for s in s2]and all(s[0]!=8 for s in s1)
    for x,y in zip(s1,s2):
        if x[0]!=7:assert original[x[1]:x[3]]==changed[y[1]:y[3]]
    old=audit.exports(original,next(s for s in s1 if s[0]==7));new=audit.exports(changed,next(s for s in s2 if s[0]==7))
    allowed=[['research135_live_cast922',0,922],['research135_live_select1072',0,1072],['research135_live_resume4600',0,4600],['research135_live_stack0',3,0]]
    assert new==old+allowed and manifest['added_exports']==allowed
    for item in manifest['functions']:assert hashlib.sha256(original[item['body_start']:item['body_end']]).hexdigest()==item['body_sha256']
    audit.RUN=RUN;static=audit.static_proof(manifest);del original,changed
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and audit.missing(terminal['pid'])and audit.missing(terminal['pgid'],True)
    assert runtime['cases']==runtime['fresh_instances']==runtime['full_calls']==109 and runtime['actual_host_calls']==0 and runtime['denied_imports']==878 and runtime['error']is None
    assert runtime['peak_memory_bytes']<=runtime['memory_cap_bytes']==33554432 and runtime['heap_mib']==512
    assert runtime['entry_counts']=={'922':43,'1072':33,'4600':33}and runtime['stack_all_restored']
    assert all(x['returned']and x['before']==x['after']==1048576 for x in runtime['stack_checks'])
    cases=load(RUN/'input.json');expected=load(RUN/'expected.json');labels=load(RUN/'labels.json');actual=[json.loads(line)for line in(RUN/'stdout.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(labels)==len(actual)==109
    counts=Counter();witnesses=[];poisons=Counter()
    for c,w,label,raw in zip(cases,expected,labels,actual):
        assert c['id']==w['id']==label['id']==raw['id'];mode=c['mode'];counts[mode+'_cases']+=1
        result=raw['result'];result['physical_live']['storage']=[list(bytes.fromhex(row))for row in result['physical_live']['storage']]
        audit.mechanical(w['result'],result,(),counts);raw_bind(c,raw,runtime)
        rows,count,source=ref(c,counts);concrete,concrete_count,_=ref(c,Counter(),materialize=True)
        assert len(rows)==len(concrete)==result['physical_live']['capacity']and count==concrete_count==result['physical_live']['count']
        if mode=='cast':
            q=raw['controlled_scratch'];assert q['entry_stack']==1048576 and q['frame_bytes']==240 and q['offset']==48
            assert q['address']==1048576-240+48 and q['before_call_bits']==q['declared_input_bits']==c['scratch_word16_bits']
            assert type(q['prior_bits'])is int and 0<=q['prior_bits']<=0xffffffff
            if source:
                assert q['after_call_bits']==q['before_call_bits']
                actual_word=audit.u(result['physical_live']['storage'][source[0]],16)
                assert actual_word==c['scratch_word16_bits'];poisons[str(actual_word)]+=1
                if c['scratch_source_unresolved']:counts['typed_unresolved_source_casts']+=1
                else:counts['explicit_known_source_casts']+=1
                if len(witnesses)<12:witnesses.append({'case':c['id'],'caster':c['caster'],'source_unresolved_to_model':c['scratch_source_unresolved'],'controlled_input':q['declared_input_bits'],'slot':source[0],'observed_live_plus16':actual_word})
            else:counts['target_absent_no_append']+=1
            assert result['success']==int(c['target_present'])
        else:
            assert raw['controlled_scratch']is None;counts['selection_or_resume_partial_append']+=1
        for i,(row,truth,observed)in enumerate(zip(rows,concrete,result['physical_live']['storage'])):
            assert len(row)==len(truth)==len(observed)==32
            for j,(v,t,a)in enumerate(zip(row,truth,observed)):
                if v is not None:
                    assert v==a,(c['id'],i,j,v,a);counts['independent_known_physical_bytes']+=1
                elif source==(i,16)and 16<=j<20:
                    assert c['scratch_source_unresolved']and t==a
                    counts['typed_source_unknown_bytes_companion_strict']+=1
                elif t is not None:
                    assert t==a,(c['id'],i,j,t,a);counts['inherited_initial_None_poison_bytes']+=1
                else:counts['unwritten_new_allocation_bytes']+=1
        #Both model views were independently reconstructed from the immutable
        #declared input; no original output is used to fill a missing source.
        assert w['result']['physical_live']['capacity']==len(rows)and w['result']['physical_live']['count']==count
        assert w['result']['physical_live']['storage']==rows
        assert w['materialized_physical_live']=={'capacity':len(concrete),'count':concrete_count,'storage':concrete}
    assert counts['mechanical_known_values']==primary['counts']['known_values']==17215
    assert counts['expected_unknown_bytes']==primary['counts']['explicit_unknown_bytes']==2500
    assert counts['typed_unresolved_source_casts']==4 and counts['typed_source_unknown_bytes_companion_strict']==16
    assert counts['explicit_known_source_casts']==37 and counts['target_absent_no_append']==2
    assert len(poisons)==4
    assert frozen=={n:sha(RUN/n)for n in frozen}and other=={n:sha(RUN/n)for n in other}
    assert before=={n:sha(ROOT/n)for n in before}
    assert sources=={n:sha(RUN/'source-snapshot'/n)for n in sources}
    reviewer_sources={Path(__file__).name:sha(Path(__file__)),'review_live_owner135.py':sha(Path(audit.__file__))}
    for name,h in reviewer_sources.items():
        q=out/'source-snapshot/scripts'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/'scripts'/name).read_bytes());assert sha(q)==h
    result={'status':'scoped_explicit_source_physical_projection_and_independent_read_only_review_passed',
        'version':'0.135.1','actual_build':'90898d5e3','comparison':str(RUN/'comparison.json'),'comparison_sha256':RECEIPT_SHA,
        'cases':109,'full_original_calls':109,'entry_counts':runtime['entry_counts'],'source_files':51,'production_files':43,
        'all_capture_sources_current_and_snapshots_match':True,'artifacts':{**frozen,**other},'counts':dict(counts),
        'controlled_source_words':dict(poisons),'witnesses':witnesses,'static_proof':static,'original_process':terminal,
        'runtime_identity':{k:v for k,v in runtime.items()if k!='stack_checks'},'reviewer_sources':reviewer_sources,
        'new_original_executions':0,'production_model_executions':0,'checker_executions':0,'builder_executions':0,
        'natural_caller_stack_producer_restored':False,
        'numeric_scope':'Known numeric projection mechanically re-compared; physical retain/append/source writes independently reconstructed.',
        'old105_general_source_claim_remains_contradicted':True,
        'limitations':['Controlled entry frame+48 is explicitly written as fixture input, not natural1076 caller reconstruction.','Four opaque-source model cases do not predict+16; their companion explicit-source controlled input is independently compared separately.','Physical1202 cache/messages are raw observations here, not a new full Aura model.','No headless/App/full880/Windows/fullgame acceptance.'],
        'seconds':time.monotonic()-began}
    save(out/'review.json',result)
    print(json.dumps({'directory':str(out),'status':result['status'],'counts':result['counts'],'review_sha256':sha(out/'review.json')}),flush=True)


if __name__=='__main__':main()
