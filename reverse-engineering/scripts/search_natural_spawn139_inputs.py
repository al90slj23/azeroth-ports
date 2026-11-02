#!/usr/bin/env python3
"""Bounded model-only Appseed search; never loads or executes the original."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys,time
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reconstruction'))
from check_player_update139 import load_world139,WORLD
from core_spec import binary32 as f
from core_spec.natural_spawn139 import prepare_natural_spawn139,advance_natural_spawn139
from core_spec.world_pause139 import update_world_pause139


def main():
    world,*_=load_world139(WORLD);rows=[];start=time.monotonic()
    for seed in range(64):
        state=prepare_natural_spawn139(seed,world);entry=dict(app_seed=seed)
        for index in range(120):
            try:
                now=f.add(state.run.actor.player.growth.now_bits,0x3dcccccd)
                result=advance_natural_spawn139(state,now,0x3dcccccd,world,
                    pause_world=update_world_pause139);state=result.state
            except Exception as e:
                entry.update(step=index,status='Pending',error_type=type(e).__name__,error=str(e));break
            g=state.run.actor.player.growth
            if g.phase2587==2:
                entry.update(step=index,status='actual_model_first_phase2',now_bits=now,
                    cards=[dict(variant=c.variant,ability_id=c.ability_id,tier=c.tier,kinds=c.kinds)for c in g.candidates],
                    living_NPC=sum(int.from_bytes(bytes(r[:4]),'little')==0 for r in state.run.units.active),
                    default0_supported=g.candidates[0].variant=='new'and g.candidates[0].ability_id=='thunder_clap');break
        else:entry.update(status='no_first_phase2_within120')
        rows.append(entry)
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('natural-spawn139-model-input-search-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    record=dict(kind='model_only_input_selection_not_original_differential',app_seed_bounds=[0,63],
        max_steps_per_seed=120,dt_bits=0x3dcccccd,seconds=time.monotonic()-start,rows=rows,
        original_calls=0,card_RNG_HP_position_CD_timer_edits=False,
        source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    raw=(json.dumps(record,indent=2)+'\n').encode();(out/'receipt.json').write_bytes(raw)
    print(json.dumps(dict(directory=str(out),sha256=hashlib.sha256(raw).hexdigest(),seconds=record['seconds'],
        tried=len(rows),supported=[r for r in rows if r.get('default0_supported')],Pending=[r for r in rows if r['status']=='Pending'])))


if __name__=='__main__':main()
