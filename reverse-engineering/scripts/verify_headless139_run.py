#!/usr/bin/env python3
"""Validate the independent raw-resource executable against frozen observations.

No game/model/author checker is imported or executed. This is comparison with
historical original observations plus raw-world composition checks; it adds
zero original executions and is not a new full-game differential experiment.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'evidence/natural-spawn139-oracle-20261102T151856.594632Z'
WORLD = ROOT / 'evidence/asset-world139-owned-20261102T031312.028310Z/model/receipt.json'

def sha(p):
    with Path(p).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    run = args.run.resolve()
    out = args.output.resolve()
    assert run.is_relative_to(Path('/Volumes/RuiRui4TB')) and out.is_relative_to(Path('/Volumes/RuiRui4TB'))
    out.mkdir(parents=True,exist_ok=False)
    receipt = json.loads((run/'receipt.json').read_text())
    original = json.loads((ORIGINAL/'comparison.json').read_text())
    assert sha(ORIGINAL/'comparison.json') == '5cab88ba3b2090e794c41ff23753ecd5aaf1fabb394765ea604cb949e29f3ec9'
    assert sha(WORLD) == '46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
    world = json.loads(WORLD.read_text())
    prepared = json.loads((ORIGINAL/'prepared.json').read_text())
    assert sha(ORIGINAL/'actual.jsonl') == original['artifacts']['actual.jsonl']
    actual = [json.loads(line) for line in (ORIGINAL/'actual.jsonl').read_text().splitlines()]
    inputs = json.loads((ORIGINAL/'inputs.json').read_text())
    assert sha(ORIGINAL/'inputs.json') == prepared['frozen']['inputs.json']
    assert len(inputs)==len(actual)==3 and [int(row['app_seed_u64']) for row in inputs]==[0,50,111]
    assert receipt['kind']=='independent_raw_assets_world_natural_combat139_headless_run'
    assert receipt['version']=='0.139.0' and receipt['actual_build']=='f79c5e2b4'
    assert receipt['source_sha256_before']==receipt['source_sha256_after']
    assert receipt['original_program_executed'] is receipt['original_memory_read'] is receipt['pre_parsed_world_read'] is False
    assert receipt['original_calls']==receipt['complete_games']==receipt['full_main884_frames']==0
    assert receipt['loaded_assets']==451 and receipt['raw_asset_bytes']==67281330
    sources=receipt['source_sha256_before']
    for name,expected in sources.items():
        assert sha(run/'source-snapshot'/name)==expected,name
        assert sha(ROOT/'reconstruction'/name)==expected,name
    for name,value in receipt['world_artifacts'].items():
        assert (value['bytes'],value['sha256'])==(world['world_artifacts'][name]['bytes'],world['world_artifacts'][name]['sha256'])
    audit=json.loads((run/'read-audit.json').read_text())
    assert not audit['forbidden'] and all(row['admitted']for row in audit['opened'])
    assert sha(run/'states.jsonl')==receipt['states_sha256']
    assert (run/'states.jsonl').stat().st_size<=268435456
    rows=[json.loads(line)for line in(run/'states.jsonl').read_text().splitlines()]
    counts=Counter();differences=[]
    def eq(label,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(differences)<50:differences.append(dict(field=label,expected=want,actual=got))
    def cells(label,known,hexes,width):
        eq(label+'.count',len(known),len(hexes))
        for j,(row,hx)in enumerate(zip(known,hexes,strict=True)):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)==width
            for k,(value,observed)in enumerate(zip(row,raw,strict=True)):
                if value is None:counts['unknown_bytes_observed_only']+=1
                else:eq(f'{label}[{j}]+{k}',value,observed);counts['known_bytes_compared']+=1
    by_seed={int(i['app_seed_u64']):a for i,a in zip(inputs,actual,strict=True)}
    stage_counts=Counter()
    for row in rows:
        seed,step,stage=row['seed'],row['step'],row['stage'];s=row['state'];a=by_seed[seed]
        tag=f'{seed}:{step}:{stage}';stage_counts[stage]+=1
        if stage=='opening':
            p=a['initial'];combat=a['stages'][0]['before_combat'];heal=a['initial_healing'];gold=earned=0
        else:
            observed=a['stages'][step]
            if stage=='components'and observed['before_choice']is not None:
                view=observed['before_choice'];p=view['player'];combat=view['combat'];heal=view['healing'];gold=view['gold1456'];earned=view['earned1100']
            else:
                p=observed['after'];combat=observed['combat'];heal=observed['healing'];gold=observed['gold1456'];earned=observed['earned1100']
        eq(tag+'.growth',s['growth'],p['capture']['projection'])
        eq(tag+'.playerXYZ',s['player_xyz'],combat['player_xyz'])
        for k,width in [('live',32),('aura',16)]:
            eq(tag+'.'+k+'.count',s[k]['count'],p[k]['count'])
            cells(tag+'.'+k,s[k]['storage'],p[k]['storage'],width)
        background=p['capture']['background']
        eq(tag+'.NPCcount',s['physical_NPC_count'],background['units']['count'])
        cells(tag+'.NPCphysical',s['physical_NPC_storage'],background['units']['storage'],432)
        eq(tag+'.pickupcount',s['pickups_count'],background['pickups']['count'])
        cells(tag+'.pickups',s['pickups_storage'],background['pickups']['storage'],56)
        for k in ['accounted_total_bits','killcost2420_bits','counter2408','movement_sequence2412','kills1084']:
            eq(tag+'.'+k,s[k],combat[k])
        eq(tag+'.gold1456',s['gold1456'],gold);eq(tag+'.earned1100',s['earned1100'],earned)
        for k in ['event_counter960','accepted_count1016','reason_totals64']:
            eq(tag+'.ledger.'+k,s['ledger'][k],heal[k])
    assert stage_counts=={'opening':3,'components':306,'choice':2}
    terminal=json.loads((run.parent/'owned-terminal.json').read_text())
    assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing']
    result=dict(kind='independent_raw139_entry_historical_original_projection_comparison',passed=not differences,
        run_receipt_sha256=sha(run/'receipt.json'),verifier_sha256=sha(Path(__file__)),source_files=len(sources),
        original_comparison_sha256=sha(ORIGINAL/'comparison.json'),original_actual_sha256=sha(ORIGINAL/'actual.jsonl'),world_receipt_sha256=sha(WORLD),
        counts=dict(counts),records=dict(stage_counts),run_process=terminal,world_full_artifacts_matched=3,
        raw_assets_loaded=451,raw_asset_bytes=67281330,Python_open_audit_forbidden=0,
        source_unchanged=True,differences=differences,original_executions_by_verifier=0,model_executions_by_verifier=0,
        new_original_acceptance_cases=0,full_main884_frames=0,complete_games=0,
        scope='FreshCLIraw451→world→opening/natural306+2choices;allreportedgrowth/player/knownphysicalbytes/ledgerprojectionscomparedagainstfrozenhistoricaloriginal. Samepurealgorithmsarecomposed;thisisnotdifferent-authorindependentmathorneworiginalexecution. Unknownbytesobservedonly,packetstreamnotcomparedhere.')
    (out/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(directory=str(out),sha256=sha(out/'comparison.json'),counts=dict(counts),records=dict(stage_counts),passed=not differences,new_original_acceptance_cases=0)),flush=True)
    assert not differences

if __name__=='__main__':main()
