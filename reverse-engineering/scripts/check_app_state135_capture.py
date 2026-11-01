#!/usr/bin/env python3
"""Read-only typed App projection against one prior real original cast.

This does not initialize an original module, restore a snapshot or invoke880.
Only33 explicitly declared input bytes are read for model construction; history,
empty-map headers, next three seed pairs and other known writes are predicted.
"""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,struct,sys
sys.dont_write_bytecode=True
from source_closure135 import core_sources

ROOT=Path(__file__).resolve().parents[1]
RECEIPT='evidence/full-app0135-probe-20261101T120144.289175Z/receipt.json'
RECEIPT_SHA='fd5dba35d0aeacffe822ce070fd5bc218da8352a5b725e48c166df289b91c726'
ORIGINAL_SHA='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
FILES=tuple(sorted(('scripts/check_app_state135_capture.py','scripts/source_closure135.py',
    *core_sources(ROOT,'app_state135.py','app_history135.py'))))
INPUT_RANGES=((4008,16,'first_map_seed_pair'),(4768,4,'transport24_pointer'),
    (4928,8,'lcg_entropy_seed'),(5056,4,'server_string_pointer'),(5161,1,'startup_branch_flag'))


def sha_bytes(raw):return hashlib.sha256(raw).hexdigest()
def sha(path):return sha_bytes(path.read_bytes())
def write_json(path,value):path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    before={p:sha(ROOT/p)for p in FILES}
    original_receipt=ROOT/RECEIPT;receipt_raw=original_receipt.read_bytes()
    assert sha_bytes(receipt_raw)==RECEIPT_SHA
    receipt=json.loads(receipt_raw);runtime=receipt['runtime'];result=runtime['result']
    assert receipt['version']=='0.135.1'and receipt['build']=='0898d5e3'
    assert receipt['original_sha256']==ORIGINAL_SHA
    assert receipt['source_sha256_before']==receipt['source_sha256_after']
    assert receipt['process']['exit_code']==0 and receipt['process']['terminal']['all_owned_terminal']
    assert result['original_function_bodies_changed']is False
    assert result['wasm_memory_written_by_research']is False
    assert result['user_profile_used']is False
    assert len(result['contexts'])==1
    context=result['contexts'][0];actual=bytes.fromhex(context['app5168_hex_at_cast'])
    assert len(actual)==5168 and context['source']=='actual_original_cast867_env12_plus8_AppRc'
    seed0,seed1=struct.unpack_from('<2Q',actual,4008)
    scalar=dict(lcg_seed_u64=struct.unpack_from('<Q',actual,4928)[0],
        transport_pointer=struct.unpack_from('<I',actual,4768)[0],
        server_string_pointer=struct.unpack_from('<I',actual,5056)[0],
        startup_flag5161=actual[5161])
    inputs=dict(kind='declared_opaque_scalar_inputs_from_prior_cast_not_predictions',
        source_receipt=RECEIPT,source_sha256=RECEIPT_SHA,first_map_seed_pair_u64=[str(seed0),str(seed1)],
        **scalar,ranges=[dict(offset=o,length=n,label=label)for o,n,label in INPUT_RANGES],
        directly_observed_input_bytes=sum(n for _,n,_ in INPUT_RANGES),
        whole_maps_copied=False,history_copied=False,live_copy_regions_supplied=False)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('app-state0135-capture-check-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    write_json(out/'inputs.json',inputs)
    sys.path.insert(0,str(ROOT/'reconstruction'))
    from core_spec.app_state135 import AppConstructorInputs135,project_app_constructor135,app_pointer_from_tick_closure135
    from core_spec.app_history135 import empty_history135,RandomState135,app_hash_maps135
    history=empty_history135();maps=app_hash_maps135(RandomState135(seed0,seed1))
    value=AppConstructorInputs135(history240=history,hash_maps128=maps.bytes128,**scalar)
    expected=project_app_constructor135(value)
    assert expected.known_byte_count==730 and not expected.legal_full_app
    # Persist the pure model's complete byte/None projection before comparison.
    write_json(out/'independent-expected.json',list(expected.storage))
    (out/'independent-history240.bin').write_bytes(history)
    (out/'independent-maps128.bin').write_bytes(maps.bytes128)
    supplied={o+j for o,n,_ in INPUT_RANGES for j in range(n)}
    known={i for i,v in enumerate(expected.storage)if v is not None}
    assert supplied<=known and len(supplied)==33
    predicted=known-supplied;assert len(predicted)==697
    (out/'observed-app5168.bin').write_bytes(actual)
    masks=dict(known_offsets=sorted(known),direct_input_offsets=sorted(supplied),
        independently_predicted_offsets=sorted(predicted),unknown_ranges=expected.unknown_ranges)
    write_json(out/'masks.json',masks)
    diffs=[dict(offset=i,expected=expected.storage[i],observed=actual[i],direct_input=i in supplied)
        for i in sorted(known)if expected.storage[i]!=actual[i]]
    regions=[]
    for row in expected.knowledge:
        if row.kind in('inactive','unrestored','unrestored-live-copy'):continue
        offsets=range(row.offset,row.offset+row.length)
        regions.append(dict(offset=row.offset,length=row.length,label=row.label,kind=row.kind,evidence=row.evidence,
            direct_input_bytes=sum(i in supplied for i in offsets),
            independently_predicted_bytes=sum(i in predicted for i in offsets),
            expected_sha256=sha_bytes(expected.require_known(row.offset,row.length)),
            observed_sha256=sha_bytes(actual[row.offset:row.offset+row.length]),
            equal=expected.require_known(row.offset,row.length)==actual[row.offset:row.offset+row.length]))
    env=bytes.fromhex(context['closure_env12_hex']);assert len(env)==12
    timers=[t for t in result['timers']if t['env']==context['env']]
    assert len(timers)==1 and timers[0]['vtable']==5305816 and timers[0]['interval_ms']==25
    decoded=app_pointer_from_tick_closure135(context['env'],timers[0]['vtable'],
        lambda p:struct.unpack_from('<I',env,p-context['env'])[0])
    assert decoded==context['App']==context['Rc']+16
    header=context['header'];assert header['memory_bytes']==27787264
    assert header['App']==decoded and header['Rc']==context['Rc']
    after={p:sha(ROOT/p)for p in FILES};assert before==after
    assert sha(original_receipt)==RECEIPT_SHA
    for p,h in before.items():
        dst=out/'source-snapshot'/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/p).read_bytes());assert sha(dst)==h
    artifacts={p:dict(bytes=(out/p).stat().st_size,sha256=sha(out/p))for p in(
        'inputs.json','independent-expected.json','independent-history240.bin','independent-maps128.bin',
        'observed-app5168.bin','masks.json')}
    report=dict(version='0.135.1',build='0898d5e3',kind='typed_constructor_projection_against_prior_controlled_original_cast',
        status='passed_known_projection'if not diffs else'failed_known_projection',
        source_receipt=RECEIPT,source_receipt_sha256=RECEIPT_SHA,original_sha256=ORIGINAL_SHA,
        source_sha256_before=before,source_sha256_after=after,source_count=len(before),artifacts=artifacts,
        known_bytes_compared=730,declared_input_bytes=33,independently_predicted_bytes_compared=697,
        unknown_or_inactive_bytes_uncompared=4438,differences=diffs,regions=regions,
        input_first_map_seed_pair_u64=[str(seed0),str(seed1)],maps_next_three_seed_pairs_independently_generated=True,
        history240_independently_generated=True,input_maps128_wholecopy=False,
        predicted_known_bytes_sha256=sha_bytes(bytes(expected.storage[i]for i in sorted(known))),
        observed_known_bytes_sha256=sha_bytes(bytes(actual[i]for i in sorted(known))),
        observed_predicted697_sha256=sha_bytes(bytes(actual[i]for i in sorted(predicted))),
        expected_predicted697_sha256=sha_bytes(bytes(expected.storage[i]for i in sorted(predicted))),
        pointer_projection=dict(env=context['env'],Rc=context['Rc'],App=context['App'],vtable=5305816,interval_ms=25,
            source=context['source'],cast_header=header,strong_count_predicted=False),
        prior_run_scope=dict(initialization_returned=result['initializationReturned'],
            confirmed_complete880_returns=result['confirmed_complete880_returns'],
            original_finalizer_entered=result['original_finalizer_entered'],original_appstart_called=result['original_appstart_called'],
            runtime_error_count=len(runtime['errors']),renderer_panicked=any('panicked at third_party' in x.get('text','')for x in runtime['logs']),
            healthy_renderer_or_boot_proved=False,gameplay_proved=False),
        expected_saved_before_comparison=True,new_original_calls=0,new_original_cases=0,
        new_independent_mainloop_frames=0,new_controlled_observation_runs=0,prior_controlled_observations_reused=1,
        original_module_instantiated_by_this_checker=False,appstart_called_by_this_checker=False,
        snapshot_memory_restored=False,table_or_globals_restored=False,original_memory_written=False,
        network_used=False,user_saves_accessed=False,full_legal_app_produced=False,complete_game=False,
        limitations=[
            'Only697 bytes are independently predicted from declared33-byte inputs; those33 input-byte comparisons are not predictive validation.',
            'Unknown4438 bytes remain None and are not compared; no copied live blocks are supplied.',
            'ActualApp is a prior original natural-constructor observation, not an independent legalApp producer or a fresh original differential run.',
            'Original run returned8 idle880 calls but had a separate WebGPU rendererpanic; no healthyboot/render/gameplay claim.',
            'Original fullmemory/table/global/externref state and typed ownership are not reconstructed or restored.'])
    write_json(out/'comparison.json',report)
    print(json.dumps(dict(directory=str(out),sha256=sha(out/'comparison.json'),status=report['status'],
        source_count=len(before),known_bytes=730,direct_input_bytes=33,independently_predicted_bytes=697,
        differences=len(diffs),new_original_calls=0)))
    if diffs:raise SystemExit(1)


if __name__=='__main__':main()
