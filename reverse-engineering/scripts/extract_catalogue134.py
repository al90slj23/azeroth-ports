#!/usr/bin/env python3
"""Extract official 0.134.0 declaration tables and compare the pinned old image.

No WASM is instantiated. New bounds come from complete, indexed new functions;
initial memory is zero-filled to the declared size and all active data applied.
Historical field names are descriptive labels, not proof of every execution.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import struct
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/latest-wenilla_bg.wasm'
SOURCE_SHA = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
PROFILE = ROOT / 'evidence/wasm0134-profile-20261101T001728.222975Z'
WAT = PROFILE / 'official-0.134.0-full.wat'
WAT_SHA = '6014dab110e40ae279a6450ae15dcc0d84727c31e2da71f18f2cab1f21ec8422'
DB = PROFILE / 'index.sqlite'
DB_SHA = 'f131b4454ac1a8754f5b0417e4192efbaada6478df737e09490154c71fd340f9'
OLD_SOURCE = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
OLD_SHA = '067059375d884186338e6f86364b658f1daf6bdb779908d6d0c116f2068b147c'
OLD_REPORT = ROOT / 'reports/2026-11-01-abilities.json'
OLD_REPORT_SHA = '17a8f37e7a00efdeb7a4fbcee6b1d598ceb18d71573f23a931c2160a3ef122e2'
FUNCTIONS = (1011, 1073, 1480)
FLOAT_FIELDS = {4: 'effect_parameter_4_f32', 8: 'effect_parameter_8_f32',
                48: 'base_damage_f32', 52: 'base_cooldown_f32', 56: 'base_range_f32',
                60: 'base_radius_f32', 68: 'base_duration_f32', 76: 'projectile_speed_candidate_f32'}
INT_FIELDS = {0: 'effect_tag_u32', 44: 'spell_id_u32', 64: 'base_count_u32',
              72: 'word72_u32', 80: 'word80_u32'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def strict_json(text):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'Duplicate JSON key')
            out[key] = value
        return out
    def invalid(value):
        raise ValueError('Non-JSON constant: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=invalid)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    require(strict_json(path.read_text()) == value, 'JSON artifact readback differs')


class Reader:
    def __init__(self, data, start=0, end=None):
        self.data, self.pos, self.end = data, start, len(data) if end is None else end
        require(0 <= start <= self.end <= len(data), 'Reader bounds differ')

    def raw(self, size):
        begin = self.pos
        self.pos += size
        require(size >= 0 and self.pos <= self.end, 'Read exceeds section')
        return self.data[begin:self.pos]

    def byte(self):
        return self.raw(1)[0]

    def leb(self, signed=False):
        value = 0
        for shift in range(0, 35, 7):
            byte = self.byte()
            value |= (byte & 127) << shift
            if byte < 128:
                if signed and byte & 64:
                    value -= 1 << (shift + 7)
                require((-(1 << 31) <= value < (1 << 31)) if signed else value <= 0xffffffff,
                        'LEB exceeds32 bits')
                return value
        raise ValueError('Invalid32-bit LEB')

    def finished(self):
        require(self.pos == self.end, 'Section boundary differs')


def parse_binary(binary):
    require(binary[:8] == b'\0asm\1\0\0\0', 'Wrong WASM header')
    reader, sections = Reader(binary, 8), {}
    while reader.pos < reader.end:
        kind, size = reader.byte(), reader.leb()
        start = reader.pos
        reader.raw(size)
        if kind:
            require(kind not in sections, 'Duplicate non-custom section')
            sections[kind] = (start, reader.pos)
    def part(kind):
        return Reader(binary, *sections[kind])
    imp = part(2)
    import_count = imp.leb()
    for _ in range(import_count):
        for _ in range(2):
            imp.raw(imp.leb())
        require(imp.byte() == 0, 'Expected function imports only')
        imp.leb()
    imp.finished()
    fun = part(3)
    defined = fun.leb()
    for _ in range(defined):
        fun.leb()
    fun.finished()
    code, bodies = part(10), {}
    require(code.leb() == defined, 'Function/code counts differ')
    for index in range(import_count, import_count + defined):
        size = code.leb()
        begin = code.pos
        code.raw(size)
        bodies[index] = (begin, code.pos)
    code.finished()
    mem = part(5)
    require(mem.leb() == 1, 'Expected one memory')
    limits = mem.leb()
    require(limits in (0, 1), 'Unsupported memory limits')
    pages = mem.leb()
    maximum = mem.leb() if limits else None
    mem.finished()
    dat, segments = part(11), []
    for index in range(dat.leb()):
        flags = dat.leb()
        require(flags in (0, 2), 'Exact image requires active data segments')
        require(flags == 0 or dat.leb() == 0, 'Nonzero memory index')
        require(dat.byte() == 0x41, 'Data address is not i32.const')
        address = dat.leb(signed=True) & 0xffffffff
        require(dat.byte() == 0x0b, 'Data expression differs')
        size = dat.leb()
        # The payload starts after its length LEB, not before it.
        begin = dat.pos
        dat.raw(size)
        require(address + size <= pages * 65536, 'Active data exceeds declared memory')
        segments.append({'index': index, 'memory_start': address, 'bytes': size,
                         'file_start': begin, 'file_end': dat.pos})
    dat.finished()
    return {'function_imports': import_count, 'defined_functions': defined,
            'memory_initial_pages': pages, 'memory_maximum_pages': maximum,
            'bodies': bodies, 'segments': segments}


def reconstruct(binary, profile):
    memory = bytearray(profile['memory_initial_pages'] * 65536)
    for segment in profile['segments']:
        start = segment['memory_start']
        memory[start:start + segment['bytes']] = binary[segment['file_start']:segment['file_end']]
    return memory


def extract(memory, segments, ability_table, class_table):
    def span(address, length):
        require(0 <= address <= address + length <= len(memory), 'Span outside declared memory')
        return bytes(memory[address:address + length])
    def string(address):
        pointer, length = struct.unpack_from('<II', memory, address)
        require(length <= 4096, 'Unexpected static string length')
        return span(pointer, length).decode('utf8')
    def spans(address, length):
        found, intervals = [], []
        for segment in segments:
            lo = max(address, segment['memory_start'])
            hi = min(address + length, segment['memory_start'] + segment['bytes'])
            if lo < hi:
                intervals.append((lo, hi))
                found.append({'segment_index': segment['index'], 'memory_start': lo,
                              'memory_end_exclusive': hi,
                              'original_file_start': segment['file_start'] + lo - segment['memory_start'],
                              'original_file_end_exclusive': segment['file_start'] + hi - segment['memory_start']})
        intervals.sort()
        require(all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:])), 'Table has overlapping active data')
        return {'active_segment_spans': found,
                'implicit_zero_bytes': length - sum(hi - lo for lo, hi in intervals)}
    abilities = []
    for index in range(ability_table['count']):
        address = ability_table['memory_start'] + index * ability_table['stride']
        raw = span(address, ability_table['stride'])
        identifier = string(address + 12)
        require(re.fullmatch('[a-z][a-z0-9_]*', identifier), 'Invalid ability identifier')
        ptr, count = struct.unpack_from('<II', memory, address + 36)
        kinds = list(span(ptr, count))
        require(0 < count <= 5 and len(set(kinds)) == count and all(k <= 4 for k in kinds), 'Invalid declared upgrade list')
        record = {'index': index, 'memory_address': address, 'record_bytes': len(raw),
                  'record_sha256': digest(raw), 'record_raw_hex': raw.hex(),
                  'raw_words_u32': list(struct.unpack('<22I', raw)),
                  'identifier': identifier, 'display_name': string(address + 20), 'icon_key': string(address + 28),
                  'declared_upgrade_kinds': kinds, 'upgrade_kind_bytes_address': ptr,
                  'execution_kind_u8': raw[84], 'school_code_u8': raw[85],
                  'reserved_86_87_hex': raw[86:88].hex(), 'f32_field_bits_u32': {}}
        for offset, label in FLOAT_FIELDS.items():
            value, bits = struct.unpack_from('<f', raw, offset)[0], struct.unpack_from('<I', raw, offset)[0]
            record[label] = value if math.isfinite(value) else ('NaN' if math.isnan(value) else ('+Infinity' if value > 0 else '-Infinity'))
            record['f32_field_bits_u32'][label] = bits
        for offset, label in INT_FIELDS.items():
            record[label] = struct.unpack_from('<I', raw, offset)[0]
        abilities.append(record)
    by_id = {a['identifier']: a for a in abilities}
    require(len(by_id) == len(abilities), 'Duplicate ability identifier')
    classes = []
    for index in range(class_table['count']):
        address = class_table['memory_start'] + index * class_table['stride']
        raw = span(address, class_table['stride'])
        ptr, count = struct.unpack_from('<II', memory, address + 32)
        require(0 < count < 256, 'Invalid class kit size')
        kit = [string(ptr + i * 8) for i in range(count)]
        require(len(set(kit)) == len(kit) and all(x in by_id for x in kit), 'Class kit fails ability resolution')
        start = string(address + 40)
        require(start in kit, 'Starting ability not in class kit')
        classes.append({'index': index, 'memory_address': address, 'record_bytes': len(raw),
                        'record_sha256': digest(raw), 'record_raw_hex': raw.hex(),
                        'raw_words_u32': list(struct.unpack('<22I', raw)),
                        'identifier': string(address + 16), 'display_name': string(address + 24),
                        'ability_ids': kit, 'kit_slice_address': ptr, 'kit_slice_count': count,
                        'kit_slice_raw_hex': span(ptr, count * 8).hex(),
                        'starting_ability_id': start, 'color': string(address + 48),
                        'icon_key': string(address + 56), 'description_text': string(address + 64),
                        'header_words_0_to_12': list(struct.unpack_from('<4I', raw)),
                        'uninterpreted_tail_words_72_to_84': list(struct.unpack_from('<4I', raw, 72))})
    require(len({x['identifier'] for x in classes}) == len(classes), 'Duplicate class identifier')
    kit_ids = {x for c in classes for x in c['ability_ids']}
    for table in (ability_table, class_table):
        length = table['count'] * table['stride']
        table.update({'bytes': length, 'reconstructed_initial_memory_sha256': digest(span(table['memory_start'], length)),
                      **spans(table['memory_start'], length)})
    return {'abilities': abilities, 'classes': classes, 'ability_table': ability_table, 'class_table': class_table,
            'class_kit_entries': sum(len(c['ability_ids']) for c in classes), 'unique_class_kit_ids': len(kit_ids),
            'outside_class_kits': sorted(set(by_id) - kit_ids)}


def compare(old, new):
    def difference(key, fields):
        old_by, new_by = ({r['identifier']: r for r in cat[key]} for cat in (old, new))
        changed = []
        for identifier in sorted(old_by.keys() & new_by.keys()):
            a, b = old_by[identifier], new_by[identifier]
            fields_changed = {k: {'old': a[k], 'new': b[k]} for k in fields if a[k] != b[k]}
            if key == 'abilities':
                for offset, label in FLOAT_FIELDS.items():
                    old_bits, new_bits = a['f32_field_bits_u32'][label], b['f32_field_bits_u32'][label]
                    if old_bits != new_bits:
                        fields_changed[label] = {'offset': offset, 'old': a[label], 'new': b[label],
                                                 'old_bits_u32': old_bits, 'new_bits_u32': new_bits,
                                                 'old_bits_hex': f'0x{old_bits:08x}', 'new_bits_hex': f'0x{new_bits:08x}'}
            if fields_changed:
                changed.append({'identifier': identifier, 'fields': fields_changed})
        return {'added_ids': sorted(new_by.keys() - old_by.keys()), 'removed_ids': sorted(old_by.keys() - new_by.keys()),
                'common_ids': len(old_by.keys() & new_by.keys()), 'changed_common_records': changed,
                'added_records': [new_by[x] for x in sorted(new_by.keys() - old_by.keys())],
                'removed_records': [old_by[x] for x in sorted(old_by.keys() - new_by.keys())]}
    ability_fields = ['display_name', 'icon_key', 'declared_upgrade_kinds',
                      *INT_FIELDS.values(), 'execution_kind_u8', 'school_code_u8', 'reserved_86_87_hex']
    class_fields = ['display_name', 'ability_ids', 'starting_ability_id', 'color', 'icon_key', 'description_text',
                    'header_words_0_to_12', 'uninterpreted_tail_words_72_to_84']
    delta = {'baseline_version': '0.126.0', 'current_version': '0.134.0',
             'abilities': difference('abilities', ability_fields), 'classes': difference('classes', class_fields)}
    kits = []
    old_by = {x['identifier']: x for x in old['classes']}
    for record in new['classes']:
        before = old_by.get(record['identifier'])
        if before and before['ability_ids'] != record['ability_ids']:
            kits.append({'class_id': record['identifier'], 'old_kit': before['ability_ids'], 'new_kit': record['ability_ids'],
                         'added_ids': sorted(set(record['ability_ids']) - set(before['ability_ids'])),
                         'removed_ids': sorted(set(before['ability_ids']) - set(record['ability_ids']))})
    delta['class_kit_changes'] = kits
    delta['outside_class_kits'] = {'old': old['outside_class_kits'], 'new': new['outside_class_kits'],
                                  'added_ids': sorted(set(new['outside_class_kits']) - set(old['outside_class_kits'])),
                                  'removed_ids': sorted(set(old['outside_class_kits']) - set(new['outside_class_kits']))}
    return delta


def main():
    started = time.monotonic()
    script_sha = sha(Path(__file__))
    identities = {SOURCE: SOURCE_SHA, WAT: WAT_SHA, DB: DB_SHA, OLD_SOURCE: OLD_SHA, OLD_REPORT: OLD_REPORT_SHA}
    require(all(sha(p) == expected for p, expected in identities.items()), 'Pinned source/profile/baseline identity differs')
    binary = SOURCE.read_bytes()
    require(len(binary) == 90953762 and digest(binary) == SOURCE_SHA, 'New source readback differs')
    profile = parse_binary(binary)
    require((profile['function_imports'], profile['defined_functions'], len(profile['segments']), profile['memory_initial_pages'])
            == (878, 175316, 28470, 222), 'New source profile differs')
    run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('catalogue0134-%Y%m%dT%H%M%S.%fZ')
    run.mkdir(parents=True, exist_ok=False)
    con = sqlite3.connect(DB.resolve().as_uri() + '?mode=ro', uri=True)
    functions, normalized, guards = [], {}, []
    try:
        meta = {k: strict_json(v) for k, v in con.execute('SELECT key,value FROM meta')}
        require(meta['original_sha256'] == SOURCE_SHA and meta['wat_sha256'] == WAT_SHA
                and meta['target_version'] == '0.134.0' and meta['terminal_parentheses_supported'] is True,
                'Indexed source identity differs')
        with WAT.open('rb') as stream:
            for index in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes FROM functions WHERE idx=?', (index,)).fetchone()
                require(row is not None and profile['bodies'][index] == tuple(row[3:5])
                        and row[5] == row[4] - row[3], 'Indexed body differs from independently parsed source')
                stream.seek(row[0])
                wat = stream.read(row[1] - row[0])
                require(re.findall(rb'^  \(func \(;(\d+);\)', wat, re.M) == [str(index).encode()], 'Not one complete function')
                body = binary[row[3]:row[4]]
                (run / f'function-{index}.wat').write_bytes(wat)
                (run / f'function-{index}.body.bin').write_bytes(body)
                normalized[index] = '\n'.join(line.strip() for line in wat.decode().splitlines())
                functions.append({'function_index': index, 'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(wat), 'wat_sha256': digest(wat), 'body_start': row[3],
                                  'body_end': row[4], 'body_bytes': len(body), 'body_sha256': digest(body)})
    finally:
        con.close()
    def guard(index, pattern, label):
        matches = list(re.finditer(pattern, normalized[index]))
        require(len(matches) == 1, 'Reviewed complete-function guard differs: ' + label)
        match = matches[0]
        line = normalized[index][:match.start()].count('\n') + 1
        absolute = next(x['wat_line'] for x in functions if x['function_index'] == index) + line - 1
        guards.append({'function_index': index, 'label': label, 'function_line': line,
                       'complete_wat_line': absolute, 'instructions': match[0].splitlines()})
        return match
    loop = guard(1480, r'local.get 9\ni32.const (\d+)\ni32.add\nlocal.tee 9\ni32.const (\d+)\ni32.ne', 'new ability-table cursor stride and terminating byte count')
    stride, size = map(int, loop.groups())
    base = int(guard(1480, r'local.get 9\ni32.const (\d+)\ni32.add\nlocal.tee 6\ni32.store offset=304', 'new ability definition pointer base')[1])
    require(size % stride == 0 and stride == 88, 'Current supported record layout differs from observed stride')
    guard(1073, rf'local.get 1\ni32.const {stride}\ni32.add\nlocal.tee 1\ni32.const {size}\ni32.ne', 'independent new selected-card lookup confirms ability bounds')
    guard(1073, rf'local.get 1\ni32.const {base}\ni32.add\nlocal.tee 4\ni32.store offset=200', 'selected-card lookup confirms definition base')
    guard(1480, r'local.get 6\ni32.load offset=36\nlocal.tee 8\ni32.store offset=208\nlocal.get 4\nlocal.get 8\nlocal.get 6\ni32.load offset=40\ni32.add', 'definition upgrade-byte-list begin/end consumed in new code')
    class_start = guard(1011, r'i32.const (\d+)\nlocal.set 2\nglobal.get 0\ni32.const 16\ni32.sub\nlocal.tee 5\nglobal.set 0\nblock  ;; label = @10', 'new class-table iterator begins at static base')
    class_base = int(class_start[1])
    class_loop = guard(1011, r'br_if 1 \(;@13;\)\nlocal.get 2\ni32.const (\d+)\ni32.add\nlocal.tee 2\ni32.const (\d+)\ni32.ne\nbr_if 0 \(;@14;\)', 'new class-table first iterator increments to end pointer')
    class_stride, class_end = map(int, class_loop.groups())
    require(class_stride == 88 and (class_end - class_base) % class_stride == 0, 'Observed class record layout differs')
    ability_table = {'memory_start': base, 'stride': stride, 'count': size // stride,
                     'bounds_derived_from_new_functions': [1480, 1073]}
    class_table = {'memory_start': class_base, 'stride': class_stride, 'count': (class_end - class_base) // class_stride,
                   'memory_end_exclusive': class_end, 'bounds_derived_from_new_functions': [1011]}
    memory = reconstruct(binary, profile)
    current = extract(memory, profile['segments'], ability_table, class_table)
    (run / 'initial-memory.bin').write_bytes(memory)
    save(run / 'data-segments.json', profile['segments'])
    baseline_report = strict_json(OLD_REPORT.read_text())
    require(baseline_report['version'] == '0.126.0' and baseline_report['original_wasm_sha256'] == OLD_SHA
            and len(baseline_report['abilities']) == 113 and len(baseline_report['classes']) == 9, 'Baseline evidence profile differs')
    old_binary = OLD_SOURCE.read_bytes()
    require(digest(old_binary) == OLD_SHA, 'Baseline source readback differs')
    old_profile = parse_binary(old_binary)
    old_memory = reconstruct(old_binary, old_profile)
    old = extract(old_memory, old_profile['segments'],
                  {k: baseline_report['ability_table'][k] for k in ('memory_start', 'stride', 'count')},
                  {k: baseline_report['class_table'][k] for k in ('memory_start', 'stride', 'count')})
    for key in ('abilities', 'classes'):
        require([r['record_sha256'] for r in old[key]] == [r['record_sha256'] for r in baseline_report[key]],
                'Historical declaration record bytes differ from pinned prior report')
    delta = compare(old, current)
    save(run / 'catalogues.json', current)
    save(run / 'delta-from-0126.json', delta)
    for path in run.iterdir():
        if path.suffix == '.json':
            strict_json(path.read_text())
    require((run / 'initial-memory.bin').read_bytes() == memory, 'Memory artifact readback differs')
    for function in functions:
        index = function['function_index']
        require(sha(run / f'function-{index}.wat') == function['wat_sha256']
                and sha(run / f'function-{index}.body.bin') == function['body_sha256'], 'Function artifact readback differs')
    require(all(sha(p) == expected for p, expected in identities.items()) and sha(Path(__file__)) == script_sha,
            'Source/profile/baseline/script changed during extraction')
    artifacts = {p.name: {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in sorted(run.iterdir()) if p.is_file()}
    report = {'date': '2026-11-01', 'version': '0.134.0', 'build': '983346a7',
              'method': 'Pinned new full-function instruction bounds plus independently parsed zero-initialized active-data image; exact declaration extraction, no target execution.',
              'original_wasm_sha256': SOURCE_SHA, 'complete_wat_sha256': WAT_SHA, 'index_sha256': DB_SHA,
              'script_sha256': script_sha, 'complete_functions': functions, 'instruction_guards': guards,
              'memory_initial_pages': profile['memory_initial_pages'], 'memory_bytes': len(memory),
              'memory_image_sha256': digest(memory), 'active_data_segments': len(profile['segments']),
              **current, 'delta_from_0126': delta,
              'baseline': {'version': '0.126.0', 'build': '3e72472a', 'original_wasm_sha256': OLD_SHA,
                           'report_path': str(OLD_REPORT), 'report_sha256': OLD_REPORT_SHA,
                           'ability_count': len(old['abilities']), 'class_count': len(old['classes']),
                           'all_old_record_hashes_reconfirmed_against_old_original': True,
                           'purpose': 'Historical declaration comparison only; new bounds and records never use old table constants.'},
              'field_interpretation': {'raw_layout': 'All88B retained as raw_hex/22u32; declaration lists and strings followed through pointers in reconstructed memory.',
                                       'numeric_labels': 'Historical descriptive field names retained for comparison. Their offsets/bit patterns are exact; all latest gameplay consumers are not semantically recovered.',
                                       'execution_kind_u8': 'Raw record byte84; no claim that every variant behavior is recovered.',
                                       'school_code_u8': 'Raw record byte85; school names intentionally not inferred from strings.',
                                       'effect_tag_u32': 'Raw word at0; union parameters at4/8 remain exact raw bits plus float interpretation.',
                                       'class_description_text': 'Pointer/length at64/68, included here in addition to the historical report fields.'},
              'run_directory': str(run), 'artifacts': artifacts, 'source_and_artifact_readback_verified': True,
              'target_executed': False, 'network_used': False, 'user_saves_accessed': False,
              'installed_game_modified': False, 'elapsed_seconds': round(time.monotonic() - started, 3),
              'limitations': ['These are initial static declarations, not observed runtime mutations or a proof of all114 ability behaviors.',
                              'A class kit is a declaration list, not proof of unlock eligibility, talent/proc ordering or every gameplay path.',
                              'rockbiter is outside the nine declared class kits; this does not prove it is unreachable or inactive.',
                              'Numeric labels are historical descriptive names; school/execution/effect values are retained raw without guessing enum names.',
                              'No game/module instantiation, networking, saves, binary patch, commit or push is performed.']}
    save(run / 'manifest.json', report)
    final = {**report, 'local_manifest_sha256': sha(run / 'manifest.json')}
    save(ROOT / 'reports/2026-11-01-catalogue0134.json', final)
    lines = ['# Official 0.134.0 ability and class declarations', '',
             'The new official 0.134.0 / 983346a7 image declares **114 abilities and9 classes**. '
             'Complete new functions1480/1073 prove ability base5463472, stride88 and10032-byte bound; '
             'function1011 proves class base5458652, stride88 and end5459444. '
             'Counts are derived from these new instructions.', '',
             '| Table | Base | Stride | Records |', '| --- | ---: | ---: | ---: |',
             f"| Abilities | {base} | {stride} | {ability_table['count']} |",
             f"| Classes | {class_base} | {class_stride} | {class_table['count']} |", '',
             f"The initial image contains{len(memory):,} bytes ({profile['memory_initial_pages']} pages), zero-filled before applying "
             f"all{len(profile['segments']):,} active data segments. All114 complete88B ability records and nine class records, "
             'string references, upgrade-byte lists and class kits are retained in the JSON and ignored raw evidence.', '',
             'Compared with the pinned0.126.0 declaration image (113 abilities/9 classes):', '',
             '- Added IDs: `stormstrike`, `rockbiter`.', '- Removed ID: `call_of_flame`.',
             '- Shaman kit: `call_of_flame` replaced by `stormstrike`; the nine class IDs are unchanged.',
             '- `stoneform`: raw float field+4 changes from bits`0x3e99999a` (0.30000001192092896) '
             'to`0x3ee66666` (0.44999998807907104); field+52 changes from45 (`0x42340000`) to30 (`0x41f00000`).',
             '- Other common ability declaration numeric bits, upgrade lists, raw execution-kind84 and school85 fields are unchanged.', '',
             f"The class kits have{current['class_kit_entries']} entries/{current['unique_class_kit_ids']} distinct IDs; "
             f"{len(current['outside_class_kits'])} declarations lie outside them, including`rockbiter`. "
             'This is a directory fact, not a reachability result.', '',
             '| Class | Kit size | Starting ability |', '| --- | ---: | --- |']
    lines.extend(f"| {r['identifier']} | {len(r['ability_ids'])} | {r['starting_ability_id']} |" for r in current['classes'])
    lines.extend(['', '| Added declaration | Index | Upgrade kinds | Effect tag | Execution byte84 | School byte85 |',
                  '| --- | ---: | --- | ---: | ---: | ---: |'])
    lines.extend(f"| {r['identifier']} | {r['index']} | {r['declared_upgrade_kinds']} | {r['effect_tag_u32']} | {r['execution_kind_u8']} | {r['school_code_u8']} |"
                 for r in delta['abilities']['added_records'])
    lines.extend(['', 'The adjacent JSON includes every current record and the complete ID/field/kit delta, preserving raw effect words, '
                  'execution/school bytes and exact float bits. Class descriptions at64/68 are also retained. '
                  'The old records were re-read from the pinned old original and all prior record hashes confirmed; '
                  'the old image is used only as the comparison baseline.', '',
                  'This is static declaration recovery. It does not claim all114 execution/effect implementations, runtime unlock behavior, '
                  'complete talent/proc semantics or whole-core compatibility. Historical scalar labels aid comparison; '
                  'raw bytes remain the primary evidence. No target was executed, and no network, save or installed-game write was used.', '',
                  f"Official source SHA256: `{SOURCE_SHA}`. Full WAT: `{WAT_SHA}`.",
                  f"Ignored evidence: `{run.relative_to(ROOT)}`; manifest SHA256`{final['local_manifest_sha256']}`.",
                  'Reproduce: `python3 reverse-engineering/scripts/extract_catalogue134.py`. All source/profile/baseline identities '
                  'were checked before and after extraction; raw artifacts and strict JSON were read back.'])
    text = '\n'.join(lines) + '\n'
    target = ROOT / 'reports/2026-11-01-catalogue0134.md'
    target.write_text(text)
    require(target.read_text() == text, 'Markdown readback differs')
    print(json.dumps({'run_directory': str(run), 'version': '0.134.0', 'abilities': len(current['abilities']),
                      'classes': len(current['classes']), 'added_ability_ids': delta['abilities']['added_ids'],
                      'removed_ability_ids': delta['abilities']['removed_ids'], 'target_executed': False,
                      'network_used': False, 'elapsed_seconds': report['elapsed_seconds']}, allow_nan=False))


if __name__ == '__main__':
    main()
