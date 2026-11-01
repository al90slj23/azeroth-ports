#!/usr/bin/env python3
"""Compare the independent model with actual original1573 plus original callees.

The separately built full research module changes exports only. Denied host
functions must never run; the game start is never called. Synthetic fixtures
exercise original allocation, vector growth, BTree insertion and movement packet
construction in addition to the complete numeric body. No callees are shimmed.
"""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path

from check_stats_spec import (cases,equivalent,ROOT,spec_source_hashes,
                              run_fixed_oracle,checked_result_rows)
from core_spec.derived_stats import StatsInput,recalculate,input_from_dict
from core_spec.binary32 import from_float
from wasm_index import ORIGINAL_SHA,sha


def check(full_directory,output_directory):
    full_directory=Path(full_directory).resolve();output_directory=Path(output_directory).resolve()
    manifest=json.loads((full_directory/'manifest.json').read_text())
    original=ROOT.parent/'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original)!=ORIGINAL_SHA:raise ValueError('Original identity differs')
    if manifest['only_changed_section']!=7 or manifest['wasm_implicit_start_present']:
        raise ValueError('Full research module profile differs')
    fixtures=list(cases())
    for previous in [0,0x80000000,0x7f800000,0xff800000,0x7fc00000]+[
            from_float(x) for x in (6.989999,6.99,6.990001,7,7.009999,7.01,7.010001)]:
        fixtures.append({'group':'movement-threshold','input':asdict(StatsInput(previous_speed_bits=previous))})
    groups=Counter();expected={}
    for i,c in enumerate(fixtures):
        c['id']=i;groups[c['group']]+=1;expected[i]=recalculate(input_from_dict(c['input']))
    casefile=output_directory/'full-original-fixtures.jsonl'
    casefile.write_text(''.join(json.dumps(c,separators=(',',':'))+'\n' for c in fixtures))
    resultsfile=output_directory/'full-original-results.jsonl'
    runtime=run_fixed_oracle(ROOT/'scripts/run_stats_full_oracle.mjs',
        [full_directory,original,casefile],resultsfile,output_directory/'full-original-stderr.log')
    failures=[];seen=set();movement=0;memory=instances=0
    for got in checked_result_rows(resultsfile,casefile,fixtures):
        i=got['id'];want=expected[i]
        if i in seen:raise ValueError('Duplicate result')
        seen.add(i)
        for domain in ('derived_bits','object_fields'):
            for key,value in want[domain].items():
                actual=got[domain][key]
                integer=(domain=='object_fields' and key!='1109') or (domain=='derived_bits' and key in ('1228','1244'))
                if not(value==actual if integer else equivalent(value,actual)):
                    failures.append({'id':i,'group':fixtures[i]['group'],'field':domain+'.'+key,
                                     'expected':f'{value:08x}','actual':f'{actual:08x}'})
        for field in ('current_hp_bits','speed_bits'):
            if not equivalent(want[field],got[field]):
                failures.append({'id':i,'group':fixtures[i]['group'],'field':field,
                                 'expected':f"{want[field]:08x}",'actual':f"{got[field]:08x}"})
        for field in ('speed_sequence','movement_queue_count'):
            if got[field]!=int(want['speed_changed']):
                failures.append({'id':i,'group':fixtures[i]['group'],'field':field,
                                 'expected':int(want['speed_changed']),'actual':got[field]})
        if got['host_calls']!=0 or not got['original_internal_callees']:raise ValueError('Original closure guard differs')
        movement+=got['movement_queue_count'];memory=max(memory,got['memory_bytes']);instances=max(instances,got['instance_count'])
    if seen!=set(expected):raise ValueError('Missing results')
    output={'cases':len(fixtures),'case_groups':dict(groups),'passed':len(fixtures)-len({x['id'] for x in failures}),
            'mismatch_fields':len(failures),'failures':failures[:100],
            'original_function1573_executed':True,'original_internal_callees_executed':True,
            'replacement_callees':[],'changed_original_sections':[7],'host_calls':0,
            'denied_function_imports':len(manifest['denied_function_imports']),
            'application_start_called':False,'user_saves_read':False,'network_used':False,
            'actual_original_movement_packets_queued':movement,'actual_original_BTree_insertions':len(fixtures)*3,
            'maximum_memory_bytes':memory,'memory_page_cap':512,'fresh_instances':instances,
            'runner_seconds':runtime['runner_seconds'],'subprocess_deadline_seconds':60,
            'runtime':runtime,
            'persisted_fixture_ids_unique_and_ordered':True,'result_ids_unique_and_ordered':True,
            'nan_comparison':'classification only; every non-NaN result requires exact bits',
            'fixture_sha256':sha(casefile),'results_sha256':sha(resultsfile),
            'research_module_sha256':manifest['module_sha256'],'original_wasm_sha256':ORIGINAL_SHA,
            'full_oracle_directory':str(full_directory.relative_to(ROOT)),
            'evidence_directory':str(output_directory.relative_to(ROOT)),
            'source_sha256':spec_source_hashes(),
            'scope':'Actual original1573 and original internal callees on synthetic states; no game start or host call',
            'limitations':['Synthetic records do not establish real talent/item/effect producer IDs or save compatibility.',
                           'Movement queue creation is verified; external transport delivery is not executed.',
                           'NaN payload preservation is not claimed.']}
    (output_directory/'full-original-comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    if sha(original)!=ORIGINAL_SHA:raise ValueError('Original changed during execution')
    if failures:print(json.dumps(output,indent=2));raise SystemExit(1)
    return output


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--full-directory',required=True,type=Path);p.add_argument('--output-directory',required=True,type=Path);a=p.parse_args()
    print(json.dumps(check(a.full_directory,a.output_directory),indent=2))
