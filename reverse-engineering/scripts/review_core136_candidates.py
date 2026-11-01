#!/usr/bin/env python3
"""Review enumerated integer/reference differences in static core candidates.

This does not broaden the original mapping's normalization or turn diagnostic
candidates into runtime acceptance. Every remaining changed integer is emitted;
table references are decoded from the actual original element sections.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import re
import sqlite3
import time

from map_core135_to136 import load, normalize, sha, OLD, NEW, OLD_SHA, NEW_SHA, ROOT, OLD_PROFILE
from wasm135_profile import Reader


def elements(raw):
    top=Reader(raw,8);sections={}
    while top.pos<top.end:
        kind,size=top.byte(),top.uint();sections[kind]=(top.pos,top.pos+size);top.raw(size)
    value=Reader(raw,*sections[9]);assert value.uint()==1 and value.uint()==0 and value.byte()==0x41
    offset=value.sint();assert value.byte()==0x0b
    result={offset+i:value.uint()for i in range(value.uint())};value.finish();return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mapping_directory',type=Path);args=p.parse_args()
    started=time.monotonic();deadline=started+120
    directory=args.mapping_directory.resolve();mapping=json.loads((directory/'mapping.json').read_text())
    assert mapping['old_sha256']==OLD_SHA and mapping['new_sha256']==NEW_SHA
    old=load(OLD,OLD_SHA,175317);new=load(NEW,NEW_SHA,175319)
    old_elements,new_elements=elements(old['raw']),elements(new['raw'])
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('core0136-candidate-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    new_profile=Path(mapping['new_profile'])
    old_con=sqlite3.connect((OLD_PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    new_con=sqlite3.connect((new_profile/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    old_wat=Path(json.loads((OLD_PROFILE/'manifest.json').read_text())['wat_path'])
    new_wat=Path(json.loads((new_profile/'manifest.json').read_text())['wat_path'])
    old_file,new_file=old_wat.open('rb'),new_wat.open('rb')
    def source(index,con,stream):
        begin,end=con.execute('select wat_start,wat_end from functions where idx=?',(index,)).fetchone()
        stream.seek(begin);return stream.read(end-begin).decode()
    table_proofs={};rows=[];call_graph=defaultdict(set)
    for entry in mapping['entries']:
        assert time.monotonic()<deadline
        i=entry['old_index'];j=(entry['selected_candidates'] or [entry['diagnostic_top3'][0]['new_index']])[0]
        a=(directory/f'135-{i}.wat').read_text();b=(directory/f'136-{j}.wat').read_text()
        aa=normalize(a,old,True).splitlines();bb=normalize(b,new,True).splitlines()
        assert len(aa)==len(bb)
        changes=Counter();proofs=[]
        for line,(x,y)in enumerate(zip(aa,bb),1):
            if x==y:continue
            mx=re.fullmatch(r'(i32|i64)\.const (-?\d+)(\)*)',x)
            my=re.fullmatch(r'(i32|i64)\.const (-?\d+)(\)*)',y)
            assert mx and my and mx[1]==my[1] and mx[3]==my[3],(i,j,line,x,y)
            op=mx[1];u,v=int(mx[2]),int(my[2]);changes[(op,u,v)]+=1
            if op=='i32':
                assert v-u==3712 and u>=old['static_bounds'][1] and v>=new['static_bounds'][1]
            else:
                assert u&0xffffffff==v&0xffffffff==0
                old_slot,new_slot=u>>32,v>>32
                old_fn,new_fn=old_elements[old_slot],new_elements[new_slot]
                assert old['signatures'][old_fn]==new['signatures'][new_fn]
                key=(old_slot,new_slot)
                if key not in table_proofs:
                    osrc=source(old_fn,old_con,old_file);nsrc=source(new_fn,new_con,new_file)
                    table_proofs[key]=dict(old_slot=old_slot,new_slot=new_slot,old_function=old_fn,new_function=new_fn,
                        old_body_sha256=old['hashes'][old_fn],new_body_sha256=new['hashes'][new_fn],
                        exact_referenced_body_equal=old['hashes'][old_fn]==new['hashes'][new_fn],
                        referenced_calls_static_normalized_equal=normalize(osrc,old,True)==normalize(nsrc,new,True),
                        same_signature=True,referenced_behavior_acceptance=False)
                proofs.append(dict(normalized_line=line,old_slot=old_slot,new_slot=new_slot))
        ac=re.findall(r'^\s*(?:call|return_call) (\d+)\)*\s*$',a,re.M)
        bc=re.findall(r'^\s*(?:call|return_call) (\d+)\)*\s*$',b,re.M)
        assert len(ac)==len(bc)
        calls=Counter(zip(map(int,ac),map(int,bc)))
        for old_fn,new_fn in calls:
            if old_fn in old['signatures'] and new_fn in new['signatures']:
                assert old['signatures'][old_fn]==new['signatures'][new_fn]
            call_graph[old_fn].add(new_fn)
        rows.append(dict(role=entry['role'],old_index=i,reviewed_new_candidate=j,
            original_mapping_method=entry['match_method'],original_selected_candidates=entry['selected_candidates'],
            instruction_lines=len(aa),unchanged_after_initial_normalization_lines=sum(x==y for x,y in zip(aa,bb)),
            remaining_integer_immediate_changes=[dict(operation=op,old=u,new=v,count=count,
                classification='data-tail-external address displacement candidate'if op=='i32'else'actual element-table slot reference')
                for (op,u,v),count in changes.items()],
            remaining_noninteger_or_opcode_changes=0,table_reference_proofs=proofs,
            direct_call_pairs=[dict(old_callee=x,new_callee=y,count=count)for (x,y),count in calls.items()],
            actual_opcode_branch_local_float_field_offset_changes_after_initial_normalization=0,
            static_correspondence_only=True,new_acceptance=False))
    old_con.close();new_con.close();old_file.close();new_file.close()
    report=dict(kind='reviewed_static_candidate_reference_differences_not_acceptance',
        mapping_sha256=sha(directory/'mapping.json'),mapping_directory=str(directory),
        old_sha256=OLD_SHA,new_sha256=NEW_SHA,entries=rows,element_table_proofs=list(table_proofs.values()),
        ambiguous_callee_correspondences=[dict(old_callee=k,new_callees=sorted(v))for k,v in call_graph.items()if len(v)>1],
        observed_nonactive_data_address_displacement=3712,
        displacement_is_not_proof_of_BSS_ownership=True,normalized_masks_unchanged=True,
        target_executed=False,new_original_calls=0,new_acceptance_transferred=False,
        script_sha256=sha(Path(__file__)),elapsed_seconds=time.monotonic()-started,
        limitations=[
            'No integer literal was erased from the prior mapping to obtain this review; each residual difference is enumerated.',
            'Top similarity candidates remain provisional, including the originally retained diagnostic alternatives.',
            'Data-tail-external addresses share +3712 displacement; their allocation/ownership is not proven by this numerical fact.',
            'Decoded element slots and matching referenced signatures are static facts; referenced behavior still needs distinct136 review/tests.',
            'Static candidate correspondence never transfers135 behavior acceptance or changes a fixed135 fixture/builder.'])
    target=out/'review.json';target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),entries=len(rows),
        element_table_pairs=len(table_proofs),ambiguous_callee_pairs=len(report['ambiguous_callee_correspondences']),
        target_executed=False)))


if __name__=='__main__':main()
