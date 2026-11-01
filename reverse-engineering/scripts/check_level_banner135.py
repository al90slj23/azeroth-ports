#!/usr/bin/env python3
"""Expected-first complete4630/all150 differential, natural cold locale Once."""
import argparse
import ast
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def sources():
    bases = (ROOT / 'scripts', ROOT / 'reconstruction')
    pending = [Path(__file__).resolve(), ROOT / 'scripts/run_level_banner135_oracle.mjs',
        ROOT / 'scripts/run_level_cycle135_oracle.mjs']
    seen = set()

    def resolve(name):
        for base in bases:
            p = base / Path(*name.split('.'))
            for q in (p.with_suffix('.py'), p / '__init__.py'):
                if q.is_file():
                    return q

    while pending:
        p = pending.pop()
        key = str(p.relative_to(ROOT))
        if key in seen:
            continue
        seen.add(key)
        if p.suffix == '.mjs':
            targets = [(p.parent / name).resolve() for name in re.findall(
                r"from\s+['\"](\.[^'\"]+)['\"]", p.read_text())]
        else:
            base = next(b for b in bases if p.is_relative_to(b))
            package = list(p.relative_to(base).with_suffix('').parts[:-1])
            targets = []
            for node in ast.walk(ast.parse(p.read_text())):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    prefix = '.'.join(package[:len(package) - node.level + 1]) if node.level else ''
                    module = '.'.join(x for x in (prefix, node.module or '') if x)
                    names = [module] + ['.'.join(x for x in (module, a.name) if x) for a in node.names]
                targets.extend(q for name in names if name and (q := resolve(name)) is not None)
        for q in targets:
            pending.append(q)
            base = next(b for b in bases if q.is_relative_to(b))
            parent = q.parent
            while parent != base:
                if (parent / '__init__.py').is_file():
                    pending.append(parent / '__init__.py')
                parent = parent.parent
    return tuple(sorted(seen))


FILES = sources()
BEFORE = {name: sha(ROOT / name) for name in FILES}
sys.path.insert(0, str(ROOT / 'reconstruction'))
from build_full135_oracle import (SOURCE, SOURCE_SHA, VALIDATOR_SHA, parse_source,
    section_list, export_entries, unsigned)
from check_level_cycle135 import make_input, SOURCE_FILES as FIXTURE_HELPER_READS
from trace_level_banner135 import trace_level_banner135
from core_spec import binary32 as f
from core_spec.candidates135 import DEFINITIONS
from core_spec.level_cycle135 import from_dict, gain_xp, projection
from core_spec.progression134 import xp_threshold
from core_spec.level_banner135 import LevelBannerInput135, level_banners135, PendingLevelBanner135

assert set(FIXTURE_HELPER_READS) <= set(FILES), 'Import-time fixture helper hash reads must be frozen'

NODE = ROOT / '.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA = '2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def owned_bytes(raw):
    return tuple(DEFINITIONS[row['ability_id']].execution for row in raw['choice_inputs']['owned'])


def corpus(full):
    cases = []

    def add(group, locale, raw, amounts, override=False):
        state = from_dict(raw)
        packets = []
        expected = []
        events = []
        initialized = False
        for amount in amounts:
            before = state
            result = gain_xp(state, amount)
            assert result.status == 'core_projection'
            # Presentation is inside the level loop; a temporarily ineligible
            # phase prevents candidate generation between these independent
            # one-level stats/heal replays. Original4630 is called once below.
            one = replace(before, phase2587=3)
            for event in result.level_events:
                needed = xp_threshold(one.progression.level) - one.progression.xp
                assert needed >= 0
                transition = gain_xp(one, needed)
                assert len(transition.level_events) == 1
                new = transition.state
                banner = level_banners135(LevelBannerInput135(one.progression.level,
                    new.progression.level, one.derived_bits, new.derived_bits, owned_bytes(raw), locale))
                assert dict(new.derived_bits)[1536] == event['max_hp_bits']
                packets.extend(dict(opcode=opcode, payload_hex=payload) for opcode, payload in banner.packets)
                events.append(dict(level=new.progression.level, before_derived=one.derived_bits,
                    after_derived=new.derived_bits, texts=banner.texts))
                one = new
            prior = initialized
            initialized |= bool(result.level_events)
            state = result.state
            expected.append(dict(projection=projection(state), packets150=list(packets),
                locale_once_before=3 if prior else 0, locale_once_after=3 if initialized else 0))
        index = 11 if locale == 'zh' else 0
        cases.append(dict(id=len(cases), group=group, input=raw, amounts=amounts,
            locale=locale, locale_default_index=0 if override else index,
            locale_override_enabled=1 if override else 0,
            locale_override_index=index if override else 0,
            expected=expected, independent_per_level_banner_events=events))

    for locale in ('en', 'zh'):
        add('pilot-no-level-single-and-multilevel', locale,
            make_input(mode=0, phase=3), [4, 1, 50])
        add('pilot-dotstack-threshold', locale,
            make_input(level=14, mode=0, phase=3, owned=('rend',)), [xp_threshold(14)])
    add('pilot-max120-no-banner', 'en', make_input(level=120, mode=0, phase=3), [0, 0xffffffff])
    if full:
        for locale in ('en', 'zh'):
            for cls in (1, 2, 3, 4, 5, 7, 8, 9, 11):
                for level in (1, 29, 44, 119):
                    add('class-level-derived-growth-and-dot-gates', locale,
                        make_input(class_byte=cls, race_byte=(cls % 8) + 1, level=level,
                            mode=0, phase=3, owned=('rend',) if cls & 1 else ('cleave',)),
                        [xp_threshold(level)], override=cls == 8)
        for locale in ('en', 'zh'):
            for mode, phase, flags in ((0, 3, 0), (0, 3, 255), (1, 3, 0),
                (1, 1, 1), (1, 1, 255), (1, 1, 0)):
                add('choice-flags-do-not-suppress-growth', locale,
                    make_input(mode=mode, phase=phase, flags2576=flags, gate2572=1,
                        flags2573=1, heal_gate=255), [5, 100], override=mode == 1)
        for locale in ('en', 'zh'):
            add('dot-absent-threshold-negative-control', locale,
                make_input(level=14, mode=0, phase=3, owned=('cleave',)), [xp_threshold(14)])
            add('dot-owned-without-threshold-negative-control', locale,
                make_input(level=15, mode=0, phase=3, owned=('rend',)), [xp_threshold(15)])
    return json.loads(json.dumps(cases, allow_nan=False))


def private_build(out):
    raw = SOURCE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == SOURCE_SHA
    types, imports, declarations, bodies, _ = parse_source(raw)
    assert len(imports) == 878
    assert types[declarations[4630 - len(imports)]] == (b'\x7f\x7f', b'')
    a, b = bodies[4630]
    assert hashlib.sha256(raw[a:b]).hexdigest() == '828722a8f200878b4bdcf5ac59df4d95f1021df6ca42044a6419c216a405fd21'
    sections = section_list(raw)
    assert 8 not in [row[0] for row in sections]
    section = next(row for row in sections if row[0] == 7)
    exports, start = export_entries(raw, section)
    assert ('__wbindgen_malloc', 0, 91941) in exports
    added = b''
    for name, kind, index in ((b'research135_gain_experience', 0, 4630),
        (b'research135_level_banner_stack0', 3, 0)):
        added += unsigned(len(name)) + name + bytes((kind,)) + unsigned(index)
    payload = unsigned(len(exports) + 2) + raw[start:section[3]] + added
    changed = raw[:section[1]] + b'\x07' + unsigned(len(payload)) + payload + raw[section[3]:]
    for old, new in zip(sections, section_list(changed)):
        assert old[0] == new[0]
        if old[0] != 7:
            assert raw[old[1]:old[3]] == changed[new[1]:new[3]]
    path = out / 'level-banner135-exports.wasm'
    path.write_bytes(changed)
    validator = ROOT / '.toolchain/rea-wasm-profile/wabt/wabt-1.0.42/bin/wasm-validate'
    assert sha(validator) == VALIDATOR_SHA
    command = [str(validator), '--enable-all', str(path)]
    with (out / 'validation.stdout').open('wb') as stdout, (out / 'validation.stderr').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
        save(out / 'validator-owned.json', dict(pid=child.pid, pgid=child.pid, deadline_seconds=45))
        try:
            child.wait(timeout=45)
        finally:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    assert child.returncode == 0
    save(out / 'validator-terminal.json', dict(pid=child.pid, pgid=child.pid,
        exit_code=child.returncode, pid_missing=missing(child.pid), pgid_missing=missing(child.pid, True)))
    manifest = dict(version='0.135.1', actual_build='90898d5e3', historical_build_alias='0898d5e3',
        original_wasm_sha256=SOURCE_SHA, module_file=path.name, module_sha256=sha(path),
        only_changed_section=7, original_function_bodies_unchanged=True,
        entry=dict(index=4630, body_sha256=hashlib.sha256(raw[a:b]).hexdigest(), signature='(i32,i32)->()'),
        stack_global0_export_readonly_by_host=True, denied_imports=878, target_executed_by_builder=False)
    save(out / 'manifest.json', manifest)
    return manifest


def missing(pid, group=False):
    try:
        (os.killpg if group else os.kill)(pid, 0)
    except ProcessLookupError:
        return True
    return False


def differences(a, b, path=''):
    if type(a) is not type(b):
        return [dict(path=path, reason='type', expected=a, actual=b)]
    if isinstance(a, dict):
        if a.keys() != b.keys():
            return [dict(path=path, reason='keys')]
        return [d for key in a for d in differences(a[key], b[key], path + '.' + str(key))]
    if isinstance(a, list):
        if len(a) != len(b):
            return [dict(path=path, reason='length', expected=len(a), actual=len(b))]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in differences(x, y, path + '[' + str(i) + ']')]
    return [] if a == b else [dict(path=path, expected=a, actual=b)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=('pilot', 'full'), default='pilot')
    args = parser.parse_args()
    assert BEFORE == {name: sha(ROOT / name) for name in FILES}
    cases = corpus(args.phase == 'full')
    assert 0 < len(cases) <= 128
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('level-banner0135-oracle-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    for name, value in BEFORE.items():
        p = out / 'source-snapshot' / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
        assert sha(p) == value
    inputs = [{key: value for key, value in c.items() if key not in (
        'expected', 'independent_per_level_banner_events')} for c in cases]
    for name, value in (('input.jsonl', inputs),):
        (out / name).write_text(''.join(json.dumps(c, ensure_ascii=False, allow_nan=False) + '\n' for c in value))
    save(out / 'expected.json', [c['expected'] for c in cases])
    save(out / 'labels.json', [dict(id=c['id'], group=c['group'],
        independent_per_level_banner_events=c['independent_per_level_banner_events']) for c in cases])
    trace_level_banner135(out)
    manifest = private_build(out)
    artifacts = {name: sha(out / name) for name in ('input.jsonl', 'expected.json', 'labels.json',
        'level-banner135-static.json', 'manifest.json', manifest['module_file'])}
    assert (out / 'input.jsonl').stat().st_size <= 4194304
    assert (out / 'expected.json').stat().st_size <= 4194304
    command = [str(NODE), '--expose-gc', '--max-old-space-size=512', '--wasm-max-mem-pages=512',
        str(ROOT / 'scripts/run_level_banner135_oracle.mjs'), str(out), str(out / 'input.jsonl')]
    assert sha(NODE) == NODE_SHA and BEFORE == {name: sha(ROOT / name) for name in FILES}
    save(out / 'prepared.json', dict(source_sha256=BEFORE, artifacts_sha256=artifacts,
        expected_before_original=True, cases=len(cases), node_sha256=NODE_SHA,
        validator_sha256=VALIDATOR_SHA, command=command, deadline_seconds=60))
    error = None
    started = time.monotonic()

    def stop(sig, frame):
        raise KeyboardInterrupt('Owned level banner stop ' + str(sig))

    old_handler = signal.signal(signal.SIGTERM, stop)
    with (out / 'results.jsonl').open('wb') as stdout, (out / 'stderr.log').open('wb') as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True,
            env=dict(os.environ, TMPDIR=str(out), PYTHONDONTWRITEBYTECODE='1'))
        save(out / 'owned-process.json', dict(pid=child.pid, pgid=child.pid, command=command, deadline_seconds=60))
        try:
            child.wait(timeout=60)
        except (subprocess.TimeoutExpired, KeyboardInterrupt, OSError) as exc:
            error = repr(exc)
        finally:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            signal.signal(signal.SIGTERM, old_handler)
    terminal = dict(pid=child.pid, pgid=child.pid, exit_code=child.returncode,
        pid_missing=missing(child.pid), pgid_missing=missing(child.pid, True),
        seconds=time.monotonic() - started, error=error)
    save(out / 'process-terminal.json', terminal)
    mismatches = []
    packets = 0
    packet_bytes = 0
    actual = [json.loads(line) for line in (out / 'results.jsonl').read_text().splitlines()]
    expected_ids = [(c['id'], step) for c in cases for step in range(len(c['amounts']))]
    complete = child.returncode == 0 and [(r['id'], r['step']) for r in actual] == expected_ids
    if complete:
        for row in actual:
            want = cases[row['id']]['expected'][row['step']]
            got = {key: row[key] for key in want}
            mismatches.extend(differences(want, got, 'case' + str(row['id']) + '.step' + str(row['step'])))
            packets += len(row['packets150'])
            packet_bytes += sum(len(p['payload_hex']) // 2 for p in row['packets150'])
    runtime = json.loads((out / 'level-banner135-runtime.json').read_text()) if (out / 'level-banner135-runtime.json').exists() else None
    after = {name: sha(ROOT / name) for name in FILES}
    save(out / 'differences.json', mismatches)
    receipt = dict(version='0.135.1', actual_build='90898d5e3', historical_build_alias='0898d5e3',
        status='compared' if complete else 'original_failed_or_incomplete', cases=len(cases),
        entry_calls=len(actual), comparison_complete=complete, differences=len(mismatches) if complete else None,
        source_files=len(FILES), source_sha256_before=BEFORE, source_sha256_after=after,
        source_unchanged=BEFORE == after, artifacts_sha256=artifacts,
        artifacts_unchanged=all(sha(out / name) == h for name, h in artifacts.items()),
        groups=dict(Counter(c['group'] for c in cases)),
        independent_per_level_transitions=sum(len(c['independent_per_level_banner_events']) for c in cases),
        cumulative150_packets_compared=packets, cumulative150_bytes_compared=packet_bytes,
        expected_before_original=True, process=terminal, runtime=runtime,
        full880_frames=0, native_executions=0, original_snapshot_inputs=False,
        scope='Complete4630/all opcode150 payloads plus frozen level-state projection; explicit controlled Game fixtures and en/zh selectors; natural original locale Once.',
        pending=['Other locales', 'Nonfinite Rustfloat formatting', 'Complete packet owner allocation identity and all Game writes', 'Main-loop integration/fullgame/native'])
    save(out / 'comparison.json', receipt)
    print(json.dumps(dict(directory=str(out), cases=len(cases), entry_calls=len(actual),
        differences=len(mismatches) if complete else None, first_differences=mismatches[:5],
        process=terminal, receipt_sha256=sha(out / 'comparison.json'))))
    if not complete or mismatches or error or not terminal['pid_missing'] or not terminal['pgid_missing'] or not receipt['source_unchanged'] or not receipt['artifacts_unchanged']:
        raise SystemExit(1)
    assert runtime['actual_host_calls'] == 0 and runtime['stack_all_restored']


if __name__ == '__main__':
    main()
