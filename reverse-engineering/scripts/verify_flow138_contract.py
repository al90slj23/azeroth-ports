#!/usr/bin/env python3
"""Executable source/body/signature admission for13 fixed138 flow roles.

Reads original bytes as data only. A successful guard is not a gameplay test.
"""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,sys
sys.dont_write_bytecode=True
from map_core135_to136 import load
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.flow138_contract import ROLES as CORE,VERSION,BUILD,WASM_SHA256
from core_spec.flow138_consumers_contract import ROLES as CONSUMERS,UNIT_STRIDE


def main():
    source=ROOT/'originals/official-release-20261101T201508.341687Z/latest-wenilla_bg.wasm'
    model=load(source,WASM_SHA256,175576);guards=[]
    for role,(index,params,result,digest)in{**CORE,**CONSUMERS}.items():
        actual=model['signatures'][index];assert(actual[0].hex(),actual[1].hex())==(params,result)
        assert model['hashes'][index]==digest
        guards.append(dict(role=role,index=index,params_hex=params,results_hex=result,body_sha256=digest,body_bytes=model['ranges'][index][2]))
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('flow138-contract-guard-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    names=('scripts/verify_flow138_contract.py','scripts/map_core135_to136.py','scripts/wasm135_profile.py','scripts/wasm_index.py','reconstruction/core_spec/flow138_contract.py','reconstruction/core_spec/flow138_consumers_contract.py')
    hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()for n in names}
    for n in names:
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
    result=dict(status='source_body_signature_guard_passed_not_runtime_acceptance',version=VERSION,actual_build=BUILD,source_sha256=WASM_SHA256,roles=guards,unit_stride=UNIT_STRIDE,source_files_sha256=hashes,target_executed=False,new_original_calls=0,new_independent_model_cases=0,native_executions=0)
    p=out/'guard.json';p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(directory=str(out),guard_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),roles=len(guards),target_executed=False)))
if __name__=='__main__':main()
