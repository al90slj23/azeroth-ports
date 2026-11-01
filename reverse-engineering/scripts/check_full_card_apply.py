#!/usr/bin/env python3
"""Bounded full-original1065 probes; no application start or host imports called."""
import json
import subprocess
import sys

from build_full_function_oracle import ROOT, build

sys.path.insert(0, str(ROOT / 'reconstruction'))
from core_spec.ability_state import AbilityDefinition, AbilityRecord, UpgradeCard, apply_upgrade_card


def main():
    output, manifest = build([1065, 1573, 106495, 71577])
    definition = AbilityDefinition(1719492, b'cleave', 5)
    base = AbilityRecord(1719492)
    cases = []
    for variant, phase, kinds, tier, owned_index in (
        ('upgrade', 2, (0, 1), 2, 0),
        ('upgrade', 1, (0, 1), 2, 0),
        ('upgrade', 2, (), 999, 0),
        ('upgrade', 2, (0,), 2, 1),
        ('new', 2, (), 0, 0)):
        changed = phase == 2
        expected_record = (apply_upgrade_card(base, UpgradeCard(0, kinds, tier), definition)
                           if variant == 'upgrade' and changed and owned_index == 0 else base)
        case = {'id': len(cases), 'variant': variant, 'phase': phase,
                'input_hex': base.to_bytes().hex(), 'kinds': list(kinds),
                'tier': tier, 'owned_index': owned_index}
        case['expected'] = {'id': case['id'], 'record_hex': expected_record.to_bytes().hex(),
                            'owned_count': 1, 'phase2299': 1,
                            'selection_kind2297': 255 if changed else 0,
                            'pending2088': 0 if changed else 1,
                            'candidate_count1720': 0 if changed else 1}
        cases.append(case)
    fixtures = output / 'full-card-fixtures.json'
    fixtures.write_text(json.dumps(cases, indent=2) + '\n')
    runtime = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
    command = [str(runtime), '--max-old-space-size=768',
               str(ROOT / 'scripts/probe_full_card_apply.mjs'), str(output),
               str(ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'), str(fixtures)]
    subprocess.run(command, check=True, timeout=60)


if __name__ == '__main__':
    main()
