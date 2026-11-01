#!/usr/bin/env python3
"""Independent read-only receipt/model/raw-packet review; never runs WASM."""
from pathlib import Path
from datetime import datetime, timezone
import ast, hashlib, importlib.util, json, math, struct, sys

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ORIGINAL_SHA = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
BATCHES = (
 ('player-update135', 'full0135-oracle-20261101T060633.862339Z', 'check_player_update135.py', ('player_update135.py', 'ai_lifecycle135.py')),
 ('movement-pause135', 'full0135-oracle-20261101T061549.649714Z', 'check_movement_pause135.py', ('movement_pause135.py', 'loop135.py')))


def sha(path):
    with path.open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()


def strict(a, b):
    if type(a) != type(b): return False
    if isinstance(a, dict): return a.keys() == b.keys() and all(strict(a[k], b[k]) for k in a)
    if isinstance(a, list): return len(a) == len(b) and all(strict(x, y) for x, y in zip(a, b))
    return a == b


def norm(x): return json.loads(json.dumps(x, allow_nan=False))


def uint(data, at):
    x = shift = 0
    while True:
        b = data[at]; at += 1; x |= (b & 127) << shift
        if b < 128: return x, at
        shift += 7
        assert shift < 64


def sections(data):
    assert data[:8] == b'\0asm\1\0\0\0'; at = 8; result = []
    while at < len(data):
        start = at; kind = data[at]; size, at = uint(data, at + 1)
        result.append((kind, data[start:at + size], at, at + size)); at += size
    assert at == len(data)
    return result


def bodies(raw, sec):
    _, _, start, end = next(s for s in sec if s[0] == 10)
    n, at = uint(raw, start); out = []
    for _ in range(n):
        size, at = uint(raw, at); out.append((at, at + size)); at += size
    assert at == end
    return out


def core_closure(snapshot, entries):
    base = snapshot / 'reconstruction/core_spec'; todo = ['__init__.py', *entries]; found = set()
    while todo:
        rel = todo.pop()
        if rel in found: continue
        found.add(rel); tree = ast.parse((base / rel).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.level:
                    assert node.level == 1
                    names = [node.module] if node.module else [a.name for a in node.names]
                elif node.module and node.module.startswith('core_spec'):
                    names = [node.module.removeprefix('core_spec.')] if node.module != 'core_spec' else [a.name for a in node.names]
                else: continue
                for name in names:
                    target = name.replace('.', '/') + '.py'
                    assert (base / target).is_file(), target
                    todo.append(target)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('core_spec.'):
                        todo.append(alias.name[len('core_spec.'):].replace('.', '/') + '.py')
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id != '__import__', 'Dynamic core import'
    return sorted('reconstruction/core_spec/' + n for n in found)


def load_checker(snapshot, filename, name):
    # Snapshot scripts import their own snapshotted helpers. None calls main().
    for key in list(sys.modules):
        if key.startswith('core_spec') or key in ('check_level_cycle135', 'build_full135_oracle', 'build_upgrade134_oracle'):
            del sys.modules[key]
    sys.path.insert(0, str(snapshot / 'scripts'))
    spec = importlib.util.spec_from_file_location(name, snapshot / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return module


def f32_add(a, b):
    x = struct.unpack('<f', struct.pack('<I', a))[0] + struct.unpack('<f', struct.pack('<I', b))[0]
    try: return struct.unpack('<f', struct.pack('<f', x))[0]
    except OverflowError: return math.copysign(math.inf, x)


def moving_guids(records, now):
    n = struct.unpack('<f', struct.pack('<I', now))[0]; result = []
    for row in records:
        raw = bytes.fromhex(row); assert len(raw) == 424
        marker, = struct.unpack_from('<I', raw); start, duration = struct.unpack_from('<II', raw, 340)
        d = struct.unpack('<f', struct.pack('<I', duration))[0]
        if marker == 0 and d > 0 and f32_add(duration, start) > n:
            result.append(str(struct.unpack_from('<Q', raw, 112)[0]))
    return result


def independent_movement(cases, outputs):
    packets = stages = record_bytes = high_ids = 0
    for case, observed in zip(cases, outputs):
        phase = case['initial_phase']; seq = case['sequence']; count = notifications = 0
        assert len(observed['raw_packets']) == len(case['steps'])
        for step, projected, raw_packets in zip(case['steps'], observed['projection'], observed['raw_packets']):
            change = int(case['discriminant']) != 2 and not case['mode'] & 1 and ((step['payload_byte'] != 0 and phase == 1) or (step['payload_byte'] == 0 and phase == 3))
            guids = moving_guids(case['records'], step['now_bits']) if change else []
            if change: phase = 3 if step['payload_byte'] else 1; notifications += 1
            assert len(raw_packets) == len(guids) == len(projected['events'])
            events = []
            for guid, packet in zip(guids, raw_packets):
                raw = bytes.fromhex(packet['payload_hex']); assert packet['type'] == 221 and len(raw) == packet['length']
                mask = raw[0]; at = 1; decoded = 0
                for byte in range(8):
                    if mask & (1 << byte):
                        assert raw[at] != 0, 'PackedGUID mask must select nonzero bytes'
                        decoded |= raw[at] << (8 * byte); at += 1
                assert str(decoded) == guid
                flag = raw[at + 16]; seq = (seq + 1) & 0xffffffff
                assert flag == int(step['payload_byte'] != 0)
                assert len(raw) == at + (17 if flag else 41)
                assert struct.unpack_from('<I', raw, at + 12)[0] == seq
                events.append(dict(guid=guid, sequence=seq, stop_flag=flag)); high_ids += decoded > (1 << 53)
            count += len(guids); packets += len(guids); stages += 1
            expected = dict(phase=phase, sequence=seq, records=case['records'], rng_words=[1, 2, 3, 4], events=events,
                packet_count=count, notifications=notifications, auxiliary_count=0, claims_count=0)
            assert strict(expected, projected)
            record_bytes += sum(len(bytes.fromhex(x)) for x in projected['records'])
    return dict(stages=stages, independently_decoded_packets=packets, full_record_bytes=record_bytes, packet_guid_occurrences_above_2pow53=high_ids)


def main():
    raw = ORIGINAL.read_bytes(); assert hashlib.sha256(raw).hexdigest() == ORIGINAL_SHA
    source_sections = sections(raw); all_bodies = bodies(raw, source_sections)
    rows = []
    for prefix, directory, checker, entries in BATCHES:
        batch = ROOT / 'evidence' / directory; snap = batch / 'source-snapshot'
        receipt = json.loads((batch / (prefix + '-comparison.json')).read_text())
        assert receipt['source_sha256_before'] == receipt['source_sha256_after']
        frozen = receipt['source_sha256_before']; drift = {}
        for path, digest in frozen.items():
            assert sha(snap / path) == digest
            if sha(ROOT / path) != digest: drift[path] = dict(frozen=digest, current=sha(ROOT / path))
        closure = core_closure(snap, entries); assert set(closure) <= frozen.keys()
        for name, digest in receipt['artifacts'].items(): assert sha(batch / name) == digest
        assert sha(batch / 'manifest.json') == receipt['manifest_sha256']
        module = (batch / 'research135-exports.wasm').read_bytes(); assert hashlib.sha256(module).hexdigest() == receipt['module_sha256']
        unchanged = [(k, blob) for k, blob, _, _ in source_sections if k != 7]
        assert unchanged == [(k, blob) for k, blob, _, _ in sections(module) if k != 7]
        manifest = json.loads((batch / 'manifest.json').read_text()); guards = receipt.get('body_guards', []) + manifest['roles']
        for item in guards:
            a, b = all_bodies[item['index'] - 878]
            assert (a, b) == (item['body_start'], item['body_end'])
            assert hashlib.sha256(raw[a:b]).hexdigest() == item['body_sha256']
        assert manifest['denied_function_import_count'] == 878
        assert receipt['runtime']['host_calls'] == 0 and receipt['process']['exit_code'] == 0
        assert not receipt['runtime']['network_used'] and not receipt['runtime']['application_start_called']
        before = {name: sha(snap / name) for name in frozen}
        author = load_checker(snap, checker, 'review_' + prefix.replace('-', '_'))
        cases = json.loads((batch / (prefix + '-fixtures.json')).read_text())
        regenerated = author.corpus(False)
        assert strict(cases, norm(regenerated)), 'Snapshot fixture regeneration differs'
        outputs = [json.loads(line) for line in (batch / (prefix + '-results.jsonl')).read_text().splitlines()]
        assert [o['id'] for o in outputs] == list(range(len(cases)))
        for case, output in zip(cases, outputs): assert strict(case['expected'], output['result' if prefix.startswith('player') else 'projection'])
        extra = independent_movement(cases, outputs) if prefix.startswith('movement') else dict(
            stages=sum(len(c.get('steps', [0])) for c in cases),
            player_calls=sum(len(c['steps']) for c in cases if c['kind'] == 'player'),
            corpse_calls=sum(c['kind'] == 'corpse' for c in cases),
            full_live_record_bytes=sum(sum(len(bytes.fromhex(h)) for h in stage['live_records']) for output in outputs if isinstance(output['result'], list) for stage in output['result']),
            full_corpse_record_bytes=sum(sum(len(bytes.fromhex(h)) for h in output['result']['records']) for output in outputs if isinstance(output['result'], dict)))
        assert before == {name: sha(snap / name) for name in frozen}
        rows.append(dict(batch=str(batch.relative_to(ROOT)), receipt_sha256=sha(batch / (prefix + '-comparison.json')),
            cases=len(cases), source_files=len(frozen), core_init_import_closure=closure, current_drift=drift,
            fixture_regenerated_from_snapshotted_models=True, all_stored_results_strictly_equal=True,
            no_mask_or_nan_tolerance=True, all_nonexport_sections_identical=True, body_guards_recomputed=len(guards), **extra))
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('gameplay-phase0135-independent-review-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    result = dict(version='0.135.1', build='0898d5e3', original_sha256=ORIGINAL_SHA, batches=rows,
        reviewer_script_sha256=sha(Path(__file__)), original_executed=False, author_source_modified=False,
        pending=['Player2088 isolation uses actual racial record with Inf cooldown and empty learned vector; it is not a legal opening schedule.',
            'Physical heal/aura/account outputs and unmodeled player keys remain outside helper projection.',
            'Movement packet GUID/sequence/flag and complete NPC preservation are independently proven; packet geometry/terrain and nonempty112B auxiliary/88B claims remain unresolved.',
            'Command1371 tests pause1↔3; natural choice pause1↔2 and actual headless integration need their separate same-state receipt.',
            'Current builder/host may have coordinated additional exports; each reviewed batch is bound to its own intact snapshotted sources.'])
    (out / 'review.json').write_text(json.dumps(result, indent=2) + '\n')
    reports = ROOT / 'reports'; (reports / '2026-11-01-gameplay-phase0135-independent-review.json').write_text(json.dumps(result, indent=2) + '\n')
    (reports / '2026-11-01-gameplay-phase0135-independent-review.md').write_text(
        '# Gameplay phase135 independent review\n\n'
        'Fixed0.135.1/0898d5e3. No original execution or author-source modification occurred.\n\n'
        + '\n'.join(f'- `{r["batch"]}`: {r["cases"]}cases / {r["stages"]}stages, snapshot-model regeneration and strict raw result equality passed; source/init closure and non-export bytes passed.' for r in rows)
        + '\n\nMovement:604 complete original221 packets independently decoded for GUID/sequence/stop flag; NPC records remain unchanged, sequence wraps and duplicate GUIDs preserve order. Pause/resume is not a no-op.\n\n'
        + '\n'.join('- ' + p for p in result['pending']) + '\n\nReceipt: `' + str((out / 'review.json').relative_to(ROOT)) + '`\n')
    print(json.dumps(dict(directory=str(out), batches=[dict(cases=r['cases'], stages=r['stages'], drift=list(r['current_drift'])) for r in rows])))


if __name__ == '__main__': main()
