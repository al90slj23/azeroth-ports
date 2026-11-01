#!/usr/bin/env python3
"""Identify a new static WASM snapshot and exact known-body reuse candidates.

No execution, semantic normalization or offset transfer. Nonmatches do not
prove changed rules: calls/data addresses and compiler layout can change bytes.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
KNOWN = (25242, 95640, 95641, 35684, 85387, 32475, 1573, 933, 1065)


def compare(current):
    current = current.resolve(strict=True)
    current.relative_to(Path('/Volumes/RuiRui4TB'))
    baseline = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    old, new = baseline.read_bytes(), current.read_bytes()
    if hashlib.sha256(old).hexdigest() != ORIGINAL_SHA or new[:8] != b'\0asm\1\0\0\0':
        raise ValueError('Baseline identity or new WASM header differs')
    candidates = sorted(set((a.decode(), v.decode()) for a, v in re.findall(
        rb'([a-f0-9]{8})(0\.\d{1,4}\.\d{1,4})(?![\d.])', new)))
    if len(candidates) != 1:
        raise ValueError('New embedded menu-brand identity is ambiguous')
    old_ranges, new_ranges = body_ranges(old), body_ranges(new)
    wanted = {i: hashlib.sha256(old[a:z]).hexdigest() for i in KNOWN for a, z, _ in (old_ranges[i],)}
    wanted_hashes = set(wanted.values()); matches = defaultdict(list)
    for idx, (a, z, length) in new_ranges.items():
        digest = hashlib.sha256(new[a:z]).hexdigest()
        if digest in wanted_hashes:
            matches[digest].append({'function_index': idx, 'body_start': a, 'body_end': z, 'body_bytes': length})
    result = {'fixed_baseline_version': '0.126.0', 'fixed_baseline_build': '3e72472a',
              'fixed_baseline_sha256': ORIGINAL_SHA,
              'new_version': candidates[0][1], 'new_build': candidates[0][0],
              'new_wasm_bytes': len(new), 'new_wasm_sha256': hashlib.sha256(new).hexdigest(),
              'old_defined_function_count': len(old_ranges), 'new_defined_function_count': len(new_ranges),
              'known_body_matches': [{'old_function_index': idx, 'body_sha256': digest,
                                       'old_body_range': list(old_ranges[idx]),
                                       'new_matches': matches.get(digest, [])} for idx, digest in wanted.items()],
              'source_sha256': {'scripts/compare_wasm_versions.py': sha(Path(__file__)),
                                'scripts/wasm_index.py': sha(ROOT / 'scripts/wasm_index.py')},
              'target_executed': False,
              'limitations': ['Exact function-body identity only; signatures/caller state/layout are not inferred here.',
                              'No match does not prove changed semantics: relocated calls/data addresses and compiler layout can differ.',
                              'These counts are not a percentage of recovered game behavior.',
                              'New snapshot SHA identifies the local download, not an independently published official WASM hash.']}
    if sha(baseline) != ORIGINAL_SHA or sha(current) != result['new_wasm_sha256']:
        raise ValueError('Input changed during comparison')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--current', required=True, type=Path)
    args = parser.parse_args()
    result = compare(args.current)
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('wasm-version-comparison-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    (out / 'comparison.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'evidence_directory': str(out), 'new_version': result['new_version'],
                      'new_build': result['new_build'], 'exact_matching_known_bodies':
                      sum(bool(x['new_matches']) for x in result['known_body_matches']), 'target_executed': False}))
