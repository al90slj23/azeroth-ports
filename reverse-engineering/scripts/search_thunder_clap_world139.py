#!/usr/bin/env python3
"""Bounded pure-model appseed search; no original execution or RNG edits."""
from datetime import datetime,timezone
import json,sys,time
sys.dont_write_bytecode=True
from check_player_update139 import ROOT,load_world139,WORLD,WORLD_SHA
from incoming139_tools import sha,save
from production_closure135 import production_sources135
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.thunder_clap_world139 import (prepare_thunder_world139,
    PendingThunderWorld139,midpoint_player139)
from core_spec.thunder_clap139 import targets_thunder_clap139
from core_spec.rng import next_u32_words
from core_spec import binary32 as f


def main():
    names=production_sources135(ROOT,'core_spec.thunder_clap_world139','core_spec.thunder_clap139')
    sources={n:sha(ROOT/n)for n in names}
    assert sha(WORLD/'receipt.json')==WORLD_SHA
    world,*_=load_world139(WORLD);found=[];start=time.monotonic()
    for seed in range(128):
        try:opening,gain,selected,state=prepare_thunder_world139(seed,world)
        except PendingThunderWorld139:continue
        output,_=next_u32_words(state.growth.rng_words)
        sample=f.mul(f.from_u32(output>>8),0x33800000)
        pairs=[]
        for a in range(4):
            for b in range(a+1,4):
                xyz=midpoint_player139(state.growth.units432_cells,a,b,0,world)
                targets=targets_thunder_clap139(state.growth.units432_cells,xyz,0,0x41200000)
                if len(targets)>1:pairs.append(dict(first=a,second=b,player_xyz=list(xyz),target_ids=[str(v)for v in targets]))
        found.append(dict(app_seed_u64=str(seed),first_new='thunder_clap',tier=gain.state.candidates[0].tier,
            actual_owned80_hex=[r.hex()for r in state.growth.owned_records80],rng_before_first_cast=list(state.growth.rng_words),next_u32=output,next_roll_bits=sample,
            critical_chance_bits=state.growth.derived_bits[1548],radius_bits=0x41200000,
            next_roll_positive_critical=f.to_float(sample)<f.to_float(state.growth.derived_bits[1548]),multi_target_midpoints=pairs))
    assert sources=={n:sha(ROOT/n)for n in names}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('thunder-clap-world139-search-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    report=dict(kind='bounded_independent_model_input_search_not_original_differential',script_sha256=sha(__file__),source_hashes=sources,world_receipt_sha256=WORLD_SHA,appseed_start=0,appseed_stop_exclusive=128,inputs_checked=128,first_new_Thunder_inputs=len(found),results=found,seconds=time.monotonic()-start,source_before_after_match=True,original_executions=0,RNG_writes=0,derived_or_card_edits=0,NPC_position_edits=0,selection='actual first candidate index0 only',note='Search selects future original input seeds/layouts; no original capture was consulted.')
    save(out/'receipt.json',report);print(json.dumps(dict(directory=str(out),receipt_sha256=sha(out/'receipt.json'),inputs_checked=128,found=len(found),positive_critical_seeds=[r['app_seed_u64']for r in found if r['next_roll_positive_critical']],multi_target_seeds=[r['app_seed_u64']for r in found if r['multi_target_midpoints']],original_executions=0)))


if __name__=='__main__':main()
