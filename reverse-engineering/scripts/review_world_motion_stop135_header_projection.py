#!/usr/bin/env python3
"""Readonly review of112 model projections over historical56 captures."""
from pathlib import Path
from collections import Counter
import argparse,ast,hashlib,json,struct,sys,time
sys.dont_write_bytecode=True
import review_world_motion_stop135 as W  # Independent reference only,not main.
M=W.M;ROOT=M.ROOT
RUN=ROOT/'evidence/world-motion-stop135-header-projection-20261102T003531.750819Z'
SHA='94d712c421b7220a3b5764a3f27951c909ea48c931795d8d78cd48aa0d5d2ec9'
HISTORY=W.RUN;OLD_REVIEW=ROOT/'evidence/world-motion-stop135-independent-review-owned-20261102T001613.577948Z/review/review.json'
OLD_REVIEW_SHA='344b098c6b1513831a96ca28aa6c2982a5c5cc0567b73441b1a0e177be89e65d'
PENDING=['packet_capacity_and_count','packet_vector_allocation_copy_and_panic','complete_physical17119_return']
sha=M.sha;load=M.load
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();assert out.is_relative_to((ROOT/'evidence').resolve());out.mkdir();start=time.monotonic()
    reviewers={str(p.relative_to(ROOT)):sha(p)for p in(Path(__file__),Path(W.__file__),Path(M.__file__))}
    for n,h in reviewers.items():target=out/'reviewer-source'/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes());assert sha(target)==h
    assert sha(RUN/'comparison.json')==SHA and sha(OLD_REVIEW)==OLD_REVIEW_SHA
    report=load(RUN/'comparison.json');prepared=load(RUN/'prepared.json');handoff=load(RUN/'task-handoff.json');old=load(HISTORY/'comparison.json')
    assert report['status']=='historical_projection_comparison_passed'and(report['historical_cases'],report['new_original_calls'],report['model_comparison_calls'],report['differences'])==(56,0,112,0)
    files=report['source_sha256_before'];assert len(files)==13 and files==report['source_sha256_after']==prepared['source_sha256']
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h,n
    edges=M.source_edges(RUN/'source-snapshot',files);assert edges==[tuple(x)for x in report['source_import_edges']]and len(edges)==27
    for n,h in report['artifacts'].items():assert sha(RUN/n)==h
    for n,h in handoff['new_files_or_modified'].items():assert sha(ROOT/n)==h
    for n,h in report['historical_files'].items():assert sha(HISTORY/n)==h
    name='reconstruction/core_spec/world_motion_stop135.py';old_source=(HISTORY/'source-snapshot'/name).read_text();new_source=(RUN/'source-snapshot'/name).read_text()
    assert sha(HISTORY/'source-snapshot'/name)==report['historical_model_sha256']=='709afc4d28df4b170d2dfb62bfcc367a5d006e01a852bf9052233f75cc7e4bed'
    old_ast=ast.parse(old_source);new_ast=ast.parse(new_source)
    byname=lambda tree:{n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    old_nodes,new_nodes=byname(old_ast),byname(new_ast)
    dump=lambda n:ast.dump(n,include_attributes=False)
    for n in('_uint','_finite','_packed','MotionStopHeight135'):assert dump(old_nodes[n])==dump(new_nodes[n])
    nested=lambda node:{n.name:n for n in ast.walk(node)if isinstance(n,ast.FunctionDef)}
    before,after=nested(old_nodes['stop_world_motion135']),nested(new_nodes['stop_world_motion135'])
    assert dump(before['position'])==dump(after['position'])and dump(before['word'])==dump(after['word'])
    oldloops=[x for x in old_nodes['stop_world_motion135'].body if isinstance(x,ast.For)];newloops=[x for x in new_nodes['stop_world_motion135'].body if isinstance(x,ast.For)]
    assert len(oldloops)==len(newloops)==3 and all(dump(a)==dump(b)for a,b in zip(oldloops,newloops))
    assert '(self.packet_capacity is None)!=(self.packet_count is None)'in new_source and'header_known=capacity is not None'in new_source and'if header_known:'in new_source and'header_known,header_known,pending'in new_source
    assert '4096'not in ast.get_source_segment(new_source,new_nodes['WorldMotionStopInput135'])
    checker=(RUN/'source-snapshot/scripts/check_world_motion_stop135_header_projection.py').read_text();assert checker.index("save(out/'expectations.json',predictions)")<checker.index("actual=[json.loads(line)for line in(HISTORY/'stdout.jsonl')")
    assert prepared['new_expectations_before_historical_stdout_read']and not prepared['author_blinded_to_historical_results']and prepared['unknown_header_not_filled_from_actual']and prepared==report['prepared']
    fixture=load(RUN/'fixture-inputs.json');assert fixture==load(HISTORY/'inputs.json')and sha(M.SNAPSHOT)==M.SNAPSHOT_SHA
    memory=M.SNAPSHOT.read_bytes();world=M.World(memory,M.R);ranges=sorted(set(world.ranges));h=hashlib.sha256()
    for address,n in ranges:h.update(struct.pack('<2I',address,n));h.update(memory[address:address+n])
    assert ranges==[tuple(x)for x in fixture['world_ranges']]and len(ranges)==2318 and h.hexdigest()==fixture['expected_world_digest'];del memory
    predictions=load(RUN/'expectations.json');actual=[json.loads(x)for x in(HISTORY/'stdout.jsonl').read_text().splitlines()];assert len(predictions)==len(actual)==len(fixture['cases'])==56
    counts=Counter();cases=[]
    for i,p,a in zip(fixture['cases'],predictions,actual):
        assert i['id']==p['id']==a['id'];r=W.reference(i,world,Counter());n=len(i['prefix'])
        semantic=dict(sequence=r['sequence'],vectors=r['vectors'],new_packets=r['packets'][n:],stopped_guids=r['stopped_guids'],heights=r['heights'])
        known={**semantic,'packet_capacity':r['packet_capacity'],'packet_count':r['packet_count'],'packet_header_known':True,'complete':True,'pending':[]}
        unknown={**semantic,'packet_capacity':None,'packet_count':None,'packet_header_known':False,'complete':False,'pending':PENDING}
        assert p==dict(id=i['id'],known=known,unknown_header=unknown),(i['id'],'both new expectation modes')
        after=a['after'];before=a['before'];assert semantic['vectors']==after['vectors']and semantic['new_packets']==after['queue']['packets'][n:]
        raw=bytes.fromhex(after['raw_game2592_hex']);prior=bytes.fromhex(before['raw_game2592_hex']);assert M.u(raw,2412)==semantic['sequence']and(r['packet_capacity'],r['packet_count'])==(after['queue']['capacity'],after['queue']['count'])
        wanted=bytearray(prior)
        for offset,value in((2412,r['sequence']),(1880,r['packet_capacity']),(1888,r['packet_count'])):M.put(wanted,offset,value)
        if before['queue']['capacity']!=after['queue']['capacity']:wanted[1884:1888]=raw[1884:1888];counts['observed_known_reallocation_pointer_words']+=1
        assert raw==wanted and before['world']==after['world']==dict(sha256=fixture['expected_world_digest'],bytes=5950608)
        for mode in('known','unknown_header'):
            counts[mode+'_projections']+=1;counts[mode+'_backing_bytes']+=sum(len(bytes.fromhex(x))for v in semantic['vectors'].values()for x in v['storage']);counts[mode+'_new221']+=len(semantic['new_packets'])
        counts['known_Game_bytes']+=2592;counts['known_header_words']+=2;cases.append(dict(id=i['id'],new221=len(semantic['new_packets']),unknown_header_compared=False,unknown_complete=False,pending=PENDING))
    assert cases==load(RUN/'case-comparisons.json')or all({k:v for k,v in c.items()if k in('id','new221')}=={k:v for k,v in o.items()if k in('id','new221')}and o['unknown_header_comparison']is False and o['unknown_complete']is False and o['unknown_pending']==PENDING for c,o in zip(cases,load(RUN/'case-comparisons.json')))
    checks=load(RUN/'model-only-checks.json');assert len(checks)==10 and len([x for x in checks if x['case']=='reject-invalid-header'])==6
    for row in checks:
        if row['case']=='known-header-above-old-fixture-budget-model-only':assert row['after_count']==row['count']+3 and row['after_capacity']==(row['capacity']if row['capacity']>row['count']else row['capacity']*2)
    terminal=load(RUN/'owned-terminal.json');assert terminal==handoff['owned_process']and terminal['exit_code']==0 and terminal['seconds']<terminal['deadline_seconds']==60 and terminal['pid_missing']and terminal['pgid_missing']and M.missing(terminal['pid'])and M.missing(terminal['pgid'],True)
    assert sha(RUN/'owned-terminal.json')==handoff['owned_terminal_sha256']
    for n,h in files.items():assert sha(ROOT/n)==sha(RUN/'source-snapshot'/n)==h
    for n,h in reviewers.items():assert sha(ROOT/n)==h
    assert sha(RUN/'comparison.json')==SHA
    result=dict(status='historical_semantic_projection_review_passed',author_receipt_sha256=SHA,reviewer_sources=reviewers,source_count=13,production_sources=10,local_import_edges=27,sources_verified=files,historical_original_cases=56,new_original_calls=0,new_original_frames=0,author_model_projection_calls=112,reviewer_production_imports=0,reviewer_production_executions=0,counts=dict(counts),old_independent_review=dict(path=str(OLD_REVIEW.relative_to(ROOT)),sha256=OLD_REVIEW_SHA),source_change_ast=dict(position_and_height_unchanged=True,three_source_loops_unchanged=True,paired_None_enforced=True,fixture4096_limit_removed=True),model_only_checks=dict(rows=10,actual_calls=4,run_by_this_reviewer=False,original_acceptance=False),process=terminal,artifacts={n:sha(RUN/n)for n in(*report['artifacts'],'comparison.json','task-handoff.json','owned-terminal.json','owned-start.json')},seconds=time.monotonic()-start,limits=['Historical56 captures reused;author was not blind,no new originalcalls/frames.','Unknown packetmetadata staysNone/completeFalse/pending;only conditional semantic records/sequence/new221 compared,no allocation/copy/panic or physical17119 return claim.','Known metadata/fullGame comparison only,with54 allocatorpointerword observations.','Largeheaders/growthrefusal only modelinterface,not largequeue native/originalvalidation.','Prior56 nonflat/staticnearest limits retained,primary absent;no actualfatal/fullApp/880/game acceptance.'])
    save(out/'review.json',result);print(json.dumps(dict(output=str(out/'review.json'),sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])))
if __name__=='__main__':main()
