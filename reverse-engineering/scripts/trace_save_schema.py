#!/usr/bin/env python3
"""Retain the current original account-save schema and one unlock round trip.

Reads only the identified original WASM, original JS and read-only WAT index.
It never reads a user's save, executes target code or connects to a service.
The small independent envelope model is exercised only on synthetic bytes;
its self-tests are not original-target differential verification.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
from pathlib import Path
import re
import sqlite3
import struct

from core_type_map import leb
from trace_abilities import reconstruct_memory
from trace_coop import module_data
from wasm_index import ORIGINAL_SHA, body_ranges, sha

ROOT = Path(__file__).resolve().parents[1]
WAT_SHA = '02f5c4c2951a037c35c4fe110f040ad872bd43719e27b1c0766b04d35c7d8d9c'
FUNCTIONS = (880, 889, 980, 1160, 2883, 3903, 4427, 4801, 5361,
             1436, 3640, 18163, 18819, 25062, 27429, 30934, 38110, 42687, 47320, 58403,
             47324, 51776, 65427, 86262, 93274, 95768,
             170036, 170037, 169994, 57441, 41074, 39998, 135154)
TEMPLATE_ADDRESSES = (1055777, 1056201, 1380215, 1380225, 1380235, 1380246, 1380260,
                      1380272, 1380282, 1380293, 1380304, 1380315,
                      1380325, 1380335, 1380344, 1380356, 1380369,
                      1380383, 1380396, 1380410, 1380423, 1380441,
                      1380457, 1380476, 1380504, 1380525)

# These are offsets in the recovered 368-byte account aggregate, not Rust
# source-field names. A Vec is [capacity, pointer, length], each u32.
RECORDS = (
    ('character', None, 104, 48, 'u64|string|u8|u8|u8|five-u8-csv|u32|u32|u32|u32',
     'ten untagged fields; element offsets 0,8,36,37,38,39..43,20,24,28,32'),
    ('pick', 1380476, None, None, 'pick|u8|u8|u8|string|string|five-u8-csv|u8',
     'optional selection at account+68..100; emitted only when +68 != -1'),
    ('open', 1380410, 116, 8, 'open|class-u8|zone-id',
     'element +0 class byte; +4 open-count u32; writes zone[clamp(count,1,12)-1].id'),
    ('items', 1380293, 128, 4, 'items|u32-csv', 'numeric item IDs'),
    ('equip', 1380525, 140, 232, 'equip|class-u8|slot:item-u32-csv',
     'element +152..227 is 19 u32 slots; class byte +228; zero slots omitted'),
    ('look', 1380525, 140, 232, 'look|class-u8|slot:item-u32-csv',
     'element +0..151 is 19 pairs of presence-u32 and item-u32; class +228; absent pairs omitted'),
    ('talent', 1380423, 152, 24, 'talent|u8|u8|node:rank-csv',
     'two key bytes +0,+1; allocation at +8 stores 8-byte pairs; optional flag +20'),
    ('spec', 1380441, 164, 52, 'spec|u8|u8|three-pipe-separated-node-rank-groups',
     'element key bytes +0,+1; three groups at +4,+20,+36; grammar remains partly reviewed'),
    ('seen', 1380315, 176, 16, 'seen|string:u8-csv', 'element String +0 and value byte +12'),
    ('ach', 1380335, 188, 4, 'ach|u32-csv', 'numeric achievement IDs'),
    ('achat', 1380235, 200, 24, 'achat|string=u64-csv', 'element String +0 and numeric u64 +16'),
    ('stat', 1380225, None, 8, 'stat|name=u64-csv', 'eight counters at +0..63; omitted when all zero'),
    ('beat', 1380383, 212, 8, 'beat|class-u8|zone-id-csv', 'pairs of class u8 +0 and zone index u32 +4'),
    ('coopbeat', 1380246, 224, 4, 'coopbeat|zone-id-csv', 'stored as zone indices u32; invalid indices skipped by writer'),
    ('perk', 1380325, 236, 16, 'perk|string:u8-csv', 'String +0; rank byte +12'),
    ('tabard', 1380344, 248, 4, 'tabard|u32-csv', 'numeric IDs'),
    ('races', 1380304, 260, 1, 'races|u8-csv', 'race-code bytes'),
    ('pets', 1380272, 272, 4, 'pets|u32-csv', 'numeric IDs'),
    ('hero', 1380457, 284, 8, 'hero|u8|u8|u8|five-u8-csv', 'three bytes +0,+1,+2; five bytes +3..7'),
    ('marks', 1380396, 296, 8, 'marks|class-u8|u32', 'element class +0; numeric value +4'),
    ('stars', 1380282, 308, 8, 'stars|u32:u8-csv', 'element numeric key +0; byte value +4'),
    ('pity', 1380215, 320, 8, 'pity|u32:u8-csv', 'element numeric key +0; byte value +4'),
    ('hbeat', 1380369, 332, 8, 'hbeat|class-u8|zone-id-csv', 'pairs of zone index u32 +0 and class u8 +4'),
    ('glow', 1380356, 344, 8, 'glow|class-u8|u32', 'element class +0; numeric value +4'),
    ('resets', 1380260, None, 4, 'resets|u32', 'counter at account+64; omitted when zero'),
    ('unknown_lines', None, 356, 12, 'unrecognized non-numeric record text',
     '30934 skips numeric-leading records and all 25 known tags; preserves other trimmed lines'),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def compact_template(memory, address):
    """Decode the reviewed simple literal/argument Rust format templates."""
    p = address
    output = []
    arguments = 0
    while True:
        length = memory[p]
        p += 1
        if length == 0:
            break
        if length == 0xc0:
            output.append('{' + str(arguments) + '}')
            arguments += 1
        elif length < 0x80:
            output.append(bytes(memory[p:p + length]).decode('utf-8'))
            p += length
        else:
            raise ValueError('Unreviewed compact formatting marker')
        if p - address > 200:
            raise ValueError('Unbounded compact template')
    raw = bytes(memory[address:p])
    return {'memory_address': address, 'bytes': len(raw), 'sha256': digest(raw),
            'hex': raw.hex(), 'format': ''.join(output), 'arguments': arguments}


def imports(binary):
    p = 8
    while p < len(binary):
        kind = binary[p]
        size, begin = leb(binary, p + 1)
        if kind == 2:
            break
        p = begin + size
    count, p = leb(binary, begin)
    result = []
    for index in range(count):
        names = []
        for _ in range(2):
            length, p = leb(binary, p)
            names.append(binary[p:p + length].decode())
            p += length
        if binary[p] != 0:
            raise ValueError('Unexpected import kind')
        type_index, p = leb(binary, p + 1)
        result.append({'function_index': index, 'module': names[0],
                       'name': names[1], 'type_index': type_index})
    return result


def envelope_seal(plaintext, nonce, key):
    """Independent static interpretation, with caller-supplied synthetic nonce."""
    if len(nonce) != 16:
        raise ValueError('nonce must be 16 bytes')
    cipher = bytearray(plaintext)
    for block, first in enumerate(range(0, len(cipher), 20)):
        pad = hmac.digest(key, b'ks' + nonce + struct.pack('<Q', block), 'sha1')
        for j in range(min(20, len(cipher) - first)):
            cipher[first + j] ^= pad[j]
    tag = hmac.digest(key, b'tag' + nonce + cipher, 'sha1')
    return b'RSE1:' + base64.b64encode(nonce + cipher + tag)


def envelope_open(text, key):
    """Strict synthetic model subset; does not reproduce outer Unicode trim."""
    if not text.startswith(b'RSE1:'):
        raise ValueError('missing RSE1 prefix')
    payload = base64.b64decode(text[5:], validate=True)
    if len(payload) < 36:
        raise ValueError('short envelope')
    nonce, cipher, tag = payload[:16], payload[16:-20], payload[-20:]
    expected = hmac.digest(key, b'tag' + nonce + cipher, 'sha1')
    if not hmac.compare_digest(tag, expected):
        raise ValueError('tag mismatch')
    # The original uses exactly the same XOR transform for seal and open.
    output = bytearray(cipher)
    for block, first in enumerate(range(0, len(output), 20)):
        pad = hmac.digest(key, b'ks' + nonce + struct.pack('<Q', block), 'sha1')
        for j in range(min(20, len(output) - first)):
            output[first + j] ^= pad[j]
    output.decode('utf-8')
    return bytes(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--index', type=Path, required=True)
    args = parser.parse_args()
    original = ROOT.parent / 'android/assets/latest-web-core/wenilla_bg.wasm'
    if sha(original) != ORIGINAL_SHA:
        raise SystemExit('Original core identity differs')
    binary = original.read_bytes()
    ranges = body_ranges(binary)
    memory, segments = reconstruct_memory(binary)
    source = original.parent
    manifest = json.loads((source / 'core-manifest.json').read_text())
    js = {}
    for name in ('saves.js', 'wenilla.js', 'rogue.js'):
        data = (source / name).read_bytes()
        expected = manifest['files'][name]
        if (len(data), digest(data)) != (expected['bytes'], expected['sha256']):
            raise ValueError('Original JS identity differs: ' + name)
        js[name] = data
    with sqlite3.connect(args.index.resolve(strict=True).as_uri() + '?mode=ro', uri=True) as con:
        meta = {k: json.loads(v) for k, v in con.execute('SELECT key,value FROM meta')}
        if (meta.get('original_sha256') != ORIGINAL_SHA or meta.get('wat_sha256') != WAT_SHA
                or meta.get('terminal_parentheses_supported') is not True):
            raise SystemExit('Index identity/profile differs')
        wat = Path(meta['wat_path'])
        if sha(wat) != WAT_SHA:
            raise SystemExit('Complete WAT identity differs')
        run = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('save-schema-%Y%m%dT%H%M%S.%fZ')
        run.mkdir(parents=True, exist_ok=False)
        functions = []
        lines = {}
        with wat.open('rb') as stream:
            for idx in FUNCTIONS:
                row = con.execute('SELECT wat_start,wat_end,wat_line,body_start,body_end,body_bytes '
                                  'FROM functions WHERE idx=?', (idx,)).fetchone()
                if row is None or tuple(row[3:]) != ranges[idx]:
                    raise ValueError('Indexed body differs from original')
                stream.seek(row[0])
                data = stream.read(row[1] - row[0])
                if re.findall(rb'^  \(func \(;(\d+);\)', data, re.M) != [str(idx).encode()]:
                    raise ValueError('Expected one complete function')
                (run / f'function-{idx}.wat').write_bytes(data)
                lines[idx] = [x.strip() for x in data.decode().splitlines()]
                functions.append({'function_index': idx, 'body_start': row[3], 'body_end': row[4],
                                  'body_bytes': row[5], 'body_sha256': digest(binary[row[3]:row[4]]),
                                  'wat_start': row[0], 'wat_end': row[1], 'wat_line': row[2],
                                  'wat_bytes': len(data), 'wat_sha256': digest(data),
                                  'direct_callers': [x[0] for x in con.execute(
                                      'SELECT DISTINCT caller FROM calls WHERE callee=? ORDER BY caller', (idx,))]})
        guards = []

        def require(idx, sequence, label):
            joined = '\n'.join(lines[idx])
            needle = '\n'.join(sequence)
            if needle not in joined:
                raise ValueError('Reviewed path differs: ' + label)
            guards.append({'function_index': idx, 'label': label,
                           'first_function_line': joined[:joined.index(needle)].count('\n') + 1,
                           'instructions': sequence})

        require(3903, ['local.get 0', 'call 980'], 'account to plaintext serializer')
        require(3903, ['local.tee 3', 'call 4427'], 'plaintext span to envelope writer')
        require(3903, ['local.tee 6', 'call 27429'], 'writer unseals its own output')
        require(3903, ['local.tee 7', 'local.get 4', 'local.get 3', 'call 81718', 'i32.eqz'],
                'round-trip plaintext equality gate')
        require(3903, ['local.get 4', 'local.get 3', 'call 51776'], 'unsealed fallback writer')
        require(3903, ['local.get 5', 'local.get 6', 'call 51776'], 'sealed normal writer')
        require(51776, ['i32.const 1800780', 'i32.const 16', 'local.get 0', 'local.get 1', 'call 93274'],
                'fixed rogue.characters key and value span')
        require(93274, ['local.get 4', 'local.get 5', 'call 649'], 'setItem imported call')
        require(47324, ['i32.const 1800780', 'i32.const 16', 'call 65427'], 'read same key')
        require(65427, ['local.get 2', 'local.get 3', 'call 641'], 'getItem imported call')
        require(86262, ['table.get 1', 'call 499'], 'localStorage imported access')
        require(2883, ['i32.const 288', 'i32.add', 'call 47324'], 'load account storage')
        require(2883, ['local.get 3', 'local.get 2', 'call 27429'], 'load sealed envelope')
        require(2883, ['local.get 0', 'local.get 3', 'local.get 2', 'call 889'], 'legacy plaintext accepted')
        require(980, ['i32.const 1380410', 'local.get 2', 'i32.const 32', 'i32.add', 'call 32068'],
                'open record rendering')
        require(980, ['local.get 1', 'i32.load offset=124', 'local.tee 4'], 'open vector length')
        require(980, ['local.get 1', 'i32.load offset=120', 'local.tee 3'], 'open vector elements')
        require(980, ['local.get 1', 'i32.load8_u offset=100', 'local.get 3', 'call 58403'],
                'pick final field is decimal byte100')
        require(58403, ['local.get 1', 'i32.const 255', 'i32.and', 'local.tee 4', 'i32.const 10', 'i32.lt_u'],
                'pick final byte uses unsigned8 integer formatter')
        require(4801, ['local.get 2', 'local.get 3', 'call 38110', 'local.tee 5', 'i32.const 10',
                       'i32.gt_u', 'br_if 0 (;@2;)'], 'only first eleven source zones unlock next')
        require(4801, ['local.get 5', 'i32.const 2', 'i32.add', 'i32.store offset=4'], 'new open count is zone index plus two')
        require(4801, ['local.get 8', 'i32.const 1', 'i32.add', 'i32.store offset=3820', 'end', 'call 3903'],
                'append or update progress then persist')
        require(4801, ['local.get 0', 'i32.const 3696', 'i32.add'], 'game account aggregate offset')
        require(889, ['i32.const 1852141679', 'i32.ne'], 'open tag parser')
        require(889, ['i32.const 1869377141', 'i32.xor'], 'legacy unlock tag parser')
        require(889, ['local.get 11', 'local.get 4', 'i32.load', 'local.tee 4', 'local.get 4',
                      'local.get 11', 'i32.lt_u', 'select', 'i32.store'], 'duplicate class unlocks take max')
        require(889, ['i32.load offset=236', 'i32.store offset=124'], 'load open vector count into account')
        require(889, ['i64.load offset=228 align=4', 'i64.store offset=116 align=4'],
                'load open capacity and pointer into account')
        require(2883, ['local.get 0', 'i32.const -1', 'i32.store offset=68'], 'default selection absent')
        require(2883, ['local.get 0', 'i64.const 34359738368', 'i64.store offset=104'],
                'default character vector cap0 ptr8')
        require(30934, ['i32.const 48', 'i32.sub', 'i32.const 10', 'i32.lt_u', 'br_if 0 (;@5;)'],
                'numeric-leading lines excluded from unknown preservation')
        require(30934, ['i32.const -200', 'local.set 3', 'loop  ;; label = @6'],
                'unknown preservation compares exactly25 pointer-length entries')
        require(980, ['local.get 1', 'i32.load offset=364', 'local.tee 3'], 'unknown lines emitted after modeled records')
        require(27429, ['local.tee 1', 'i32.const 36', 'i32.ge_u'], 'envelope minimum36 bytes')
        require(27429, ['local.get 1', 'local.get 2', 'call 18163'], 'outer Unicode trim precedes prefix check')
        require(18819, ['i32.const 1744644', 'i32.store offset=32'], 'ks domain pointer')
        require(18819, ['local.get 5', 'i64.extend_i32_u', 'i64.store offset=56'], 'block counter is little-endian u64')
        require(18819, ['local.get 5', 'i32.const 1', 'i32.add', 'local.set 5'], 'keystream block counter starts zero and increments')
        require(3640, ['i32.const 54', 'i32.xor', 'i32.store8'], 'HMAC inner pad')
        require(3640, ['i32.const 92', 'i32.xor', 'i32.store8'], 'HMAC outer pad')
        for constant in (1518500249, 1859775393, 1894007588, 899497514):
            if f'i32.const {constant}' not in lines[1436]:
                raise ValueError('SHA1 round constant differs')
        for idx in (57441, 41074, 39998):
            require(idx, ['local.get 0', {57441: 'i32.load8_u', 41074: 'i32.load', 39998: 'i64.load'}[idx]],
                    'numeric formatter width')

        def span(address, length):
            raw = bytes(memory[address:address + length])
            sources = []
            for seg in segments:
                lo, hi = max(address, seg['memory_start']), min(address + length, seg['memory_start'] + seg['bytes'])
                if lo < hi:
                    sources.append({'segment_index': seg['index'], 'memory_start': lo,
                                    'file_start': seg['file_start'] + lo - seg['memory_start'], 'bytes': hi - lo})
            return {'memory_address': address, 'bytes': length, 'sha256': digest(raw), 'source_spans': sources}

        known = []
        for address in range(5309252, 5309452, 8):
            pointer, length = struct.unpack_from('<II', memory, address)
            known.append({'entry_memory_address': address, 'text_memory_address': pointer,
                          'bytes': length, 'tag': bytes(memory[pointer:pointer + length]).decode()})
        expected = ['pick', 'hero', 'open', 'unlock', 'items', 'equip', 'look', 'talent', 'spec', 'seen',
                    'ach', 'achat', 'stat', 'beat', 'coopbeat', 'perk', 'tabard', 'races', 'pets',
                    'resets', 'marks', 'stars', 'pity', 'hbeat', 'glow']
        if [x['tag'] for x in known] != expected:
            raise ValueError('Known save-tag table differs')
        templates = [compact_template(memory, x) for x in TEMPLATE_ADDRESSES]
        stat_names = []
        for i in range(8):
            pointer = struct.unpack_from('<I', memory, 1584296 + i * 4)[0]
            length = struct.unpack_from('<I', memory, 1584328 + i * 4)[0]
            stat_names.append({'name': bytes(memory[pointer:pointer + length]).decode(),
                               'account_offset': i * 8, 'type': 'u64', 'memory_address': pointer})
        records = [{'tag': tag, 'template_memory_address': template, 'vec_account_offset': vector,
                    'element_bytes': stride, 'grammar': grammar, 'reviewed_interpretation': meaning}
                   for tag, template, vector, stride, grammar, meaning in RECORDS]
        default_start = next(i for i in range(len(lines[2883]) - 2)
                             if lines[2883][i:i + 3] == ['local.get 0', 'i64.const 0', 'i64.store offset=56'])
        default_bytes = bytearray(368)
        default_written = bytearray(368)
        default_stores = []
        cursor = default_start
        while cursor + 2 < len(lines[2883]) and lines[2883][cursor] == 'local.get 0':
            constant = re.fullmatch(r'i(32|64)\.const (-?\d+)', lines[2883][cursor + 1])
            operation = re.fullmatch(r'i(32|64)\.store(?: offset=(\d+))?(?: align=\d+)?', lines[2883][cursor + 2])
            if not constant or not operation or constant[1] != operation[1]:
                raise ValueError('Default aggregate constant-store profile changed')
            width, value, offset = int(constant[1]) // 8, int(constant[2]), int(operation[2] or 0)
            default_bytes[offset:offset + width] = (value % (1 << (width * 8))).to_bytes(width, 'little')
            default_written[offset:offset + width] = b'\1' * width
            default_stores.append({'function_line': cursor + 1, 'offset': offset, 'width': width, 'value': value})
            cursor += 3
        if len(default_stores) != 44 or cursor - default_start != 132:
            raise ValueError('Reviewed default aggregate store count changed')
        uninitialized = []
        for match in re.finditer(b'\0+', default_written):
            uninitialized.append({'start': match.start(), 'end_exclusive': match.end()})
        zone_ids = []
        for i in range(12):
            pointer, length = struct.unpack_from('<II', memory, 1708132 + i * 152)
            zone_ids.append(bytes(memory[pointer:pointer + length]).decode())
        key = bytes(memory[1744646:1744688])
        if bytes(memory[1744644:1744646]) != b'ks' or bytes(memory[1745016:1745019]) != b'tag':
            raise ValueError('Envelope domain bytes differ')
        fixtures = [b'', b'open|1|duskwood\n', b'hero|1|2|0|0,1,2,3,4\n',
                    b'x-future|synthetic\n' + b'a' * 257]
        self_checks = []
        for fixture in fixtures:
            encoded = envelope_seal(fixture, bytes(range(16)), key)
            if envelope_open(encoded, key) != fixture:
                raise ValueError('Independent synthetic envelope self-check failed')
            damaged = bytearray(base64.b64decode(encoded[5:]))
            damaged[-1] ^= 1
            try:
                envelope_open(b'RSE1:' + base64.b64encode(damaged), key)
            except ValueError:
                pass
            else:
                raise ValueError('Synthetic damaged tag was accepted')
            self_checks.append({'plaintext_bytes': len(fixture), 'plaintext_sha256': digest(fixture),
                                'sealed_bytes': len(encoded), 'sealed_sha256': digest(encoded),
                                'model_roundtrip': True, 'damaged_tag_rejected': True})
        imported = [x for x in imports(binary) if x['function_index'] in (499, 523, 641, 649)]
        if len(imported) != 4 or not all(expected in item['name'] for expected, item in zip(
                ('__wbg_localStorage_', '__wbg_instanceof_', '__wbg_getItem_', '__wbg_setItem_'), imported)):
            raise ValueError('Reviewed browser imports differ')
        for name, data in js.items():
            (run / name).write_bytes(data)
        result = {
            'scope': 'static current-original account-save structure, envelope and class-zone unlock persistence',
            'game_version': manifest['game_version'], 'game_build': manifest['game_build'],
            'original_sha256': ORIGINAL_SHA, 'wat_sha256': WAT_SHA,
            'evidence_directory': str(run.relative_to(ROOT)), 'target_executed': False,
            'user_saves_read': False, 'network_used': False,
            'functions': functions, 'instruction_guards': guards, 'browser_imports': imported,
            'javascript': {name: {'bytes': len(data), 'sha256': digest(data)} for name, data in js.items()},
            'account_bytes': 368, 'account_in_game_state_offset': 3696,
            'vec_word_layout': ['capacity_u32', 'pointer_u32', 'length_u32'],
            'records': records, 'stat_counters': stat_names, 'format_templates': templates,
            'zone_id_order': zone_ids,
            'default_account': {'bytes': 368, 'zero_filled_projection_hex': default_bytes.hex(),
                                'zero_filled_projection_sha256': digest(default_bytes),
                                'unwritten_inactive_or_padding_ranges': uninitialized,
                                'constant_stores': default_stores,
                                'interpretation': 'empty account; pick absent; vectors length0; counters0; unwritten inactive bytes are not claimed zero'},
            'known_tag_table': {**span(5309252, 200), 'entries': known},
            'envelope': {'prefix': 'RSE1:', 'binary_order': ['nonce_16', 'ciphertext_N', 'tag_20'],
                         'encoding': 'standard padded base64', 'key_static_span': span(1744646, 42),
                         'keystream': 'HMAC-SHA1(key, b"ks" + nonce16 + block_u64_little_endian), XOR per20 bytes',
                         'tag': 'HMAC-SHA1(key, b"tag" + nonce16 + ciphertext)',
                         'verification_order': 'Unicode trim/prefix/base64/min36/tag equality/XOR/UTF8 validation',
                         'synthetic_model_subset': 'strict ASCII prefix and base64; outer Unicode trim and all base64 tolerance not reproduced',
                         'nonce_source': '4427 takes16 bytes from95651 RNG state; RNG algorithm not reviewed here'},
            'independent_synthetic_self_checks': self_checks,
            'limitations': [
                'No original-target execution or differential save fixtures; envelope model has synthetic self-checks only.',
                '368-byte aggregate and record families are recovered, but not every parser clamp/error/duplicate rule.',
                'Character/pick/hero byte meanings and all spec/talent subgrammar variants need more consumers.',
                'Default empty vector pointers are allocator sentinels, not playable initial unlock rules.',
                'Storage failure is swallowed by browser wrappers; static calls do not prove durable writes on any device.',
                'Backup rotation, import confirmation and full migration paths are retained but not fully specified.',
            ]}
        (run / 'save-schema.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
        if sha(original) != ORIGINAL_SHA:
            raise ValueError('Original changed during extraction')
        for name, data in js.items():
            if (source / name).read_bytes() != data:
                raise ValueError('Original JS changed during extraction')
        print(json.dumps({'evidence_directory': str(run), 'functions': len(functions),
                          'instruction_guards': len(guards), 'known_tags': len(known),
                          'record_families_including_character_and_unknown': len(records),
                          'synthetic_model_checks': len(self_checks), 'target_executed': False}))


if __name__ == '__main__':
    main()
