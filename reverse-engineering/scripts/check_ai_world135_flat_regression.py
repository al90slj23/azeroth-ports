#!/usr/bin/env python3
"""Pure-model shared-output regression against existing416 fullhex AI cases."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.ai135 import AiFrame135
from core_spec.ai_world135 import update_world_ordinary_units135
from core_spec.incoming135 import input_from_dict
from resource_spec.world_query135 import WorldQueries135


def main():
    base = ROOT / 'evidence/full0135-oracle-20261101T044817.224194Z/ai135-fixtures.jsonl'
    assert hashlib.sha256(base.read_bytes()).hexdigest() == '2670e389f721198bce82fd2f0dd7348987c6b0971f644bcf41076b44ecce3c0c'
    cases = [json.loads(line) for line in base.read_text().splitlines()]
    world = WorldQueries135((), None, None, None, 0, 0)
    stages = 0
    for case in cases:
        incoming = input_from_dict(case['input']['incoming']); rows = tuple(case['input']['records']); packets = 0
        for step, expected in zip(case['steps'], case['expected']['steps']):
            result = update_world_ordinary_units135(AiFrame135(rows, step['now_bits'], step['dt_bits'],
                tuple(step['player_xyz_bits']), incoming, other_incoming_sources_absent=True), world)
            rows, incoming = result.records, result.incoming; packets += len(result.attacks) + len(result.movements)
            actual = dict(records=list(rows), incoming_total_992_bits=struct.pack('>d', incoming.incoming_total_992).hex(),
                phase2579=incoming.phase_2579, queued_packets=packets, world_reference=0)
            for key in expected:
                if key not in actual:
                    actual[key] = getattr(incoming, key)
            assert actual == expected, (case['id'], stages)
            stages += 1
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('ai-world0135-flat-regression-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    report = dict(version='0.135.1', kind='pure-model shared-output default regression; no new original execution',
        baseline=str(base.relative_to(ROOT)), cases=len(cases), stages=stages, differences=0,
        original_calls=0, new_original_cases=0, source_sha256={name:hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            for name in ('scripts/check_ai_world135_flat_regression.py', 'reconstruction/core_spec/ai_world135.py')})
    (out / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(directory=str(out), cases=len(cases), stages=stages, differences=0, original_calls=0)))


if __name__ == '__main__': main()
