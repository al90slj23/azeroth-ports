#!/usr/bin/env python3
"""Generate separate zh-CN resource variants; never modify original core or WASM.

The integration must select these paths only for Simplified Chinese. These are
resource variants, not an instruction to force the game's language preference.
"""
from pathlib import Path
import hashlib
import json
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'assets/latest-web-core'
OUT = ROOT / 'android-overrides/zh-CN'
TRANSLATIONS = Path(__file__).with_name('strings.zh-CN.json')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def formats(text):
    return re.findall(r'%(?:\d+\$)?[-+#0 ]*\d*(?:\.\d+)?[cdiouxXeEfgGqs]', text.replace('%%', ''))


def embedded_dictionary(wasm, anchor):
    at = wasm.find(anchor)
    if at < 0:
        raise ValueError('Missing original localization dictionary anchor')
    start = wasm.rfind(b'{\n', 0, at)
    value, _ = json.JSONDecoder().raw_decode(wasm[start:start+900000].decode('utf8', 'ignore'))
    if len(value) != 3219:
        raise ValueError('Original dictionary changed; inspect before generating')
    return value


def localized_dbc(source, field_count, name_field, names):
    magic, rows, fields, row_bytes, string_bytes = struct.unpack_from('<4s4I', source)
    if magic != b'WDBC' or fields != field_count or row_bytes != fields*4:
        raise ValueError('Unexpected DBC schema')
    end = 20 + rows*row_bytes
    if len(source) != end + string_bytes:
        raise ValueError('Incomplete DBC')
    records = bytearray(source[20:end])
    strings = bytearray(source[end:])
    known = {}
    translated = []
    for row in range(rows):
        position = row*row_bytes + name_field*4
        offset, = struct.unpack_from('<I', records, position)
        terminator = strings.find(b'\0', offset)
        if offset >= string_bytes or terminator < offset:
            raise ValueError('Invalid original name offset')
        old = strings[offset:terminator].decode('utf8')
        new = names.get(old)
        if not new or new == old:
            continue
        if new not in known:
            known[new] = len(strings)
            strings.extend(new.encode('utf8') + b'\0')
        struct.pack_into('<I', records, position, known[new])
        record_id, = struct.unpack_from('<I', records, row*row_bytes)
        translated.append({'id': record_id, 'from': old, 'to': new})
    result = struct.pack('<4s4I', magic, rows, fields, row_bytes, len(strings)) + records + strings
    # Assert the patch changes no record ID, flags, positions, or file-path fields.
    original_records = source[20:end]
    for row in range(rows):
        for field in range(fields):
            if field == name_field:
                continue
            at = row*row_bytes + field*4
            assert records[at:at+4] == original_records[at:at+4]
    return result, translated


def main():
    translations = json.loads(TRANSLATIONS.read_text())
    wasm = (SOURCE/'wenilla_bg.wasm').read_bytes()
    en = embedded_dictionary(wasm, b'"zone.elwynn.name": "Elwynn Forest"')
    cn = embedded_dictionary(wasm, '"zone.elwynn.name": "艾尔文森林"'.encode())
    names = {value: cn[key] for key, value in en.items()
             if isinstance(value, str) and isinstance(cn.get(key), str) and cn[key] != value}
    names.update(translations['place_names'])
    manifest = {'locale': 'zh-CN', 'selection_required': True,
                'original_wasm_sha256': sha(wasm), 'original_wasm_modified': False,
                'scope': 'XP/loot/exploration system templates and a bounded set of area/map display names',
                'not_full_translation': True, 'files': {}}
    original = (SOURCE/'data/interface/framexml/globalstrings.lua').read_bytes()
    text = original.decode('utf8')
    appendix = ['\n-- Android Simplified Chinese system-message resource variant.']
    for token, value in translations['globals'].items():
        match = re.search(r'^' + re.escape(token) + r'\s*=\s*("(?:[^"\\]|\\.)*")\s*;', text, re.M)
        if not match:
            raise ValueError('Missing original Lua global: ' + token)
        previous = json.loads(match[1])
        if formats(previous) != formats(value):
            raise ValueError('Format arguments changed: ' + token)
        appendix.append(token + ' = ' + json.dumps(value, ensure_ascii=False) + ';')
    target_name = 'data/interface/framexml/globalstrings.lua'
    patched = original + ('\n'.join(appendix) + '\n').encode('utf8')
    target = OUT/target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(patched)
    manifest['files'][target_name] = {'original_sha256': sha(original), 'sha256': sha(patched),
                                      'translated_globals': len(translations['globals']),
                                      'format_arguments_preserved': True}
    for filename, fields, name_field in [('areatable.dbc',25,11), ('map.dbc',42,4)]:
        name = 'data/dbfilesclient/' + filename
        data = (SOURCE/name).read_bytes()
        patched, changes = localized_dbc(data, fields, name_field, names)
        target = OUT/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(patched)
        manifest['files'][name] = {'original_sha256': sha(data), 'sha256': sha(patched),
                                   'display_name_field': name_field, 'changed_rows': len(changes),
                                   'other_record_fields_unchanged': True, 'translations': changes}
    (OUT/'localization-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'translated_globals':len(translations['globals']),
                      'area_rows':manifest['files']['data/dbfilesclient/areatable.dbc']['changed_rows'],
                      'map_rows':manifest['files']['data/dbfilesclient/map.dbc']['changed_rows']},ensure_ascii=False))


if __name__ == '__main__':
    main()
