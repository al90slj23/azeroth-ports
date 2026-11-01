#!/usr/bin/env python3
"""Independent read-only placement review, without running author or original code."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import ast
import hashlib
import json
import math
import mmap
import os
import sqlite3
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BATCH = ROOT / 'evidence/full0135-oracle-20261101T110558.641205Z'
PLAN = ROOT / 'evidence/world-placements0135-plan-20261101T110820.988358Z/plan.json'
INVENTORY = ROOT / 'evidence/entry-world0135-probe-20261101T092959.623703Z/actual-assets-inventory.json'
INDEX = ROOT / 'evidence/resource-index-base-20261101T032320.856364Z/index.sqlite'
PROFILE = ROOT / 'evidence/wasm0135-profile-20261101T031028.877964Z'
SOURCE = ROOT / 'originals/official-acquisition-20261101T030310.926207Z/latest-wenilla_bg.wasm'
ARCHIVES = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'
RECEIPT_SHA = 'b4225466e0a41e217d00c214415d42addb57bdf9d2a3e57ad3db74b9140c197a'
PLAN_SHA = '4a017d870c130ec0daa433b330d7f04a69e53b09281e91a7390759c0f0e72643'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def word(value):
    return struct.unpack('<I', struct.pack('<f', value))[0]


def number(bits):
    result = struct.unpack('<f', struct.pack('<I', bits))[0]
    assert math.isfinite(result)
    return result


def rounded(value):
    return number(word(value))


def chunk_rows(raw):
    rows = []; cursor = 0
    while cursor < len(raw):
        assert cursor + 8 <= len(raw)
        tag, size = struct.unpack_from('<4sI', raw, cursor)
        end = cursor + 8 + size
        assert end <= len(raw)
        rows.append((tag, cursor, raw[cursor+8:end])); cursor = end
    assert cursor == len(raw)
    return rows


def canonical(value):
    value.decode('utf8')
    return bytes(92 if c == 47 else c + 32 if 65 <= c <= 90 else c for c in value)


def collision_chain(kind, name):
    if kind == 'm2':
        assert len(name) <= 259
        name = canonical(name); dot = name.rfind(b'.')
        assert name[dot:] in (b'.mdx', b'.mdl', b'.m2')
        name = name[:dot] + b'.m2'
    return canonical(name).decode()


def capacity(length):
    return 0 if length == 0 else max(4, 1 << (length - 1).bit_length())


def decode_placements(raw, source_file=None):
    rows = chunk_rows(raw)
    def only(tag):
        matches = [data for key, _, data in rows if key == tag]
        assert len(matches) == 1
        return matches[0]
    answer = {}
    for kind, name_tag, offset_tag, record_tag, stride in (
            ('m2', b'XDMM', b'DIMM', b'FDDM', 36),
            ('wmo', b'OMWM', b'DIWM', b'FDOM', 64)):
        table, offsets, records = only(name_tag), only(offset_tag), only(record_tag)
        assert len(offsets) % 4 == 0 and len(records) % stride == 0
        names = []
        for (offset,) in struct.iter_unpack('<I', offsets):
            assert offset < len(table)
            end = table.index(0, offset); name = table[offset:end]; name.decode('utf8'); names.append(name)
        parsed = []
        for i, start in enumerate(range(0, len(records), stride)):
            ni, uid = struct.unpack_from('<2I', records, start)
            if ni >= len(names):
                continue
            xyz = struct.unpack_from('<3I', records, start+8)
            rotation = struct.unpack_from('<3I', records, start+20)
            for bits in (*xyz, *rotation): number(bits)
            position = [word(number(0x46855555)-number(xyz[2])),
                        word(number(0x46855555)-number(xyz[0])), xyz[1]]
            scale = word(struct.unpack_from('<H', records, start+32)[0] / 1024) if kind == 'm2' else 0x3f800000
            sets = struct.unpack_from('<I', records, start+58)[0] if kind == 'wmo' else 0
            tail = [scale, uid] if kind == 'm2' else [uid, sets]
            parsed.append(dict(name_utf8_hex=names[ni].hex(), string_capacity=len(names[ni]),
                               scalar_words=position+list(rotation)+tail,
                               source_record_index=i, source_file=source_file,
                               scale_bits=scale, unique_id=uid, wmo_sets_word=sets))
        answer[kind] = dict(length=len(parsed), capacity=capacity(len(parsed)), records=parsed)
    return answer


def projection(decoded):
    return {kind: {**{k: value[k] for k in ('capacity', 'length')},
                   'records': [{k: row[k] for k in ('name_utf8_hex', 'string_capacity', 'scalar_words')}
                               for row in value['records']]}
            for kind, value in decoded.items()}


def controlled(base, which):
    output = bytearray(base); chunks = {tag: (offset, data) for tag, offset, data in chunk_rows(base)}
    m, w = chunks[b'FDDM'][0]+8, chunks[b'FDOM'][0]+8
    if which == 0:
        for i, (scale, uid) in enumerate(zip((0,1,1023,1024,2048,65535), (0,1,0x7fffffff,0x80000000,0xffffffff,0))):
            struct.pack_into('<H', output, m+36*i+32, scale); struct.pack_into('<I', output, m+36*i+4, uid)
        struct.pack_into('<3H', output, w+56, 0xabcd, 0x1234, 0x5678)
    elif which == 1:
        for i, xyz in enumerate(((0,0x80000000,0),(0x46855555,0xc2c80000,0x46855555),(0x46855556,0x3f800000,0x46855554))):
            for ptr, stride, rotation in ((m,36,(0,0x80000000,0x43b40000)),(w,64,(0xc3b40000,0x43340000,0x80000000))):
                struct.pack_into('<3I', output, ptr+stride*i+8, *xyz)
                struct.pack_into('<3I', output, ptr+stride*i+20, *rotation)
    elif which == 2:
        for i in (0,1,3): struct.pack_into('<I', output, m+36*i, 0xffffffff)
        struct.pack_into('<I', output, w, 0xffffffff)
    else:
        assert which == 3
        for tag in (b'DIMM', b'DIWM'):
            start, raw = chunks[tag]
            output[start+8:start+8+len(raw)] = bytes(len(raw))
    return bytes(output)


def crypt_values():
    result = [0]*1280; seed = 0x100001
    for low in range(256):
        for high in range(5):
            seed = (seed*125+3) % 0x2aaaab; upper = (seed & 65535) << 16
            seed = (seed*125+3) % 0x2aaaab; result[low+256*high] = upper | (seed & 65535)
    return result


CRYPT = crypt_values()


def name_hash(text, kind):
    a, b = 0x7fed7fed, 0xeeeeeeee
    for byte in text.upper().encode('ascii'):
        a = CRYPT[(kind << 8)+byte] ^ ((a+b) & 0xffffffff)
        b = (byte+a+b+(b << 5)+3) & 0xffffffff
    return a


def decrypt(raw, name):
    key, seed, result = name_hash(name, 3), 0xeeeeeeee, bytearray()
    for (encrypted,) in struct.iter_unpack('<I', raw):
        seed = (seed+CRYPT[0x400+(key & 255)]) & 0xffffffff
        value = encrypted ^ ((key+seed) & 0xffffffff); result += struct.pack('<I', value)
        key = (((~key << 21)+0x11111111) | (key >> 11)) & 0xffffffff
        seed = (value+seed+(seed << 5)+3) & 0xffffffff
    return bytes(result)


def unsigned(raw, start):
    value = shift = 0
    while True:
        byte = raw[start]; start += 1; value |= (byte & 127) << shift; shift += 7
        if byte < 128: return value, start


def sections(raw):
    output = []; p = 8
    while p < len(raw):
        start = p; kind = raw[p]; size, p = unsigned(raw, p+1)
        output.append((kind, start, p, p+size)); p += size
    assert p == len(raw)
    return output


def exports(raw, section):
    count, p = unsigned(raw, section[2]); answer = []
    for _ in range(count):
        n, p = unsigned(raw, p); name = raw[p:p+n].decode(); p += n
        kind = raw[p]; index, p = unsigned(raw, p+1); answer.append((name,kind,index))
    assert p == section[3]
    return answer


def sources(record, folder):
    before, after = record['source_sha256_before'], record['source_sha256_after']
    assert before == after and len(before) == record['source_count']
    for name, digest in before.items():
        assert sha(ROOT/name) == sha(folder/'source-snapshot'/name) == digest
        if name.endswith('.py'): ast.parse((ROOT/name).read_text())
    return before


def main():
    own = Path(__file__); own_sha = sha(own)
    receipt_path = BATCH/'world-placements135-comparison.json'
    assert sha(receipt_path) == RECEIPT_SHA and sha(PLAN) == PLAN_SHA
    receipt, plan = load(receipt_path), load(PLAN)
    assert (receipt['cases'],receipt['completed_cases'],receipt['original_calls'],receipt['differences']) == (13,13,13,0)
    assert receipt['status'] == 'passed' and receipt['runtime']['host_calls'] == 0
    original_sources = sources(receipt, BATCH); plan_sources = sources(plan, PLAN.parent)
    assert len(original_sources) == 14 and len(plan_sources) == 10
    for name, digest in {**receipt['frozen_artifacts'], **receipt['artifacts']}.items(): assert sha(BATCH/name) == digest
    assert sha(INVENTORY) == plan['inventory_sha256'] == 'cc31b6efd90b7bacb040b142eb72b72d7baf83c418f87258a60b3755196bc84c'
    assert sha(INDEX) == 'a3f219f6e76e1d87e50b0790b757f999091e2b479d3b1d40ac2c101aa8680cf4'
    inventory = load(INVENTORY); actual = {row['chain']: row for row in inventory['requests'] if row['status'] == 200}
    index = sqlite3.connect(INDEX.resolve().as_uri()+'?mode=ro', uri=True); index.row_factory = sqlite3.Row
    archives, raw_assets, checked_assets = {}, {}, []
    for chain, row in plan['actual_inputs'].items():
        asset = actual[chain]; assert row == {k:asset[k] for k in ('bytes','sha256','file')}
        entry = dict(index.execute('select *from files where archive=? and normalized_name=?', (asset['archive'],chain.upper())).fetchone())
        assert entry == asset['prior_index_row']
        if asset['archive'] not in archives:
            ar = dict(index.execute('select *from archives where name=?',(asset['archive'],)).fetchone()); path = ARCHIVES/ar['name']
            assert path.stat().st_size == ar['bytes'] and sha(path) == ar['sha256']
            with path.open('rb') as stream:
                header = stream.read(32); magic,hs,size,version,shift,hp,bp,hn,bn = struct.unpack('<4sIIHHIIII',header)
                assert (magic,hs,size,version) == (b'MPQ\x1a',32,ar['bytes'],0)
                assert (hn,bn,512 << shift) == (ar['hash_entries'],ar['block_entries'],ar['sector_bytes'])
                stream.seek(hp); hashes = decrypt(stream.read(hn*16),'(hash table)')
                stream.seek(bp); blocks = decrypt(stream.read(bn*16),'(block table)')
            assert hashlib.sha256(hashes).hexdigest() == ar['hash_table_sha256']
            assert hashlib.sha256(blocks).hexdigest() == ar['block_table_sha256']
            archives[ar['name']] = (hashes,blocks,ar)
        hashes, blocks, ar = archives[asset['archive']]
        offset, stored, size, flags = struct.unpack_from('<4I',blocks,entry['block_index']*16)
        assert (offset,stored,size,flags) == (entry['data_offset'],entry['stored_bytes'],entry['decoded_bytes'],entry['flags'])
        assert flags == 0x80000000 and stored == size
        ha,hb,locale,platform,reserved,block = struct.unpack_from('<IIHBBI',hashes,entry['hash_slot']*16)
        assert (ha,hb,locale,platform,reserved,block) == (name_hash(chain,1),name_hash(chain,2),entry['locale'],entry['platform'],0,entry['block_index'])
        with (ARCHIVES/ar['name']).open('rb') as stream: stream.seek(offset); raw = stream.read(size)
        assert raw == Path(row['file']).read_bytes() and len(raw) == row['bytes']
        assert hashlib.sha256(raw).hexdigest() == row['sha256'] == entry['decoded_sha256']
        raw_assets[chain] = raw; checked_assets.append(dict(chain=chain,sha256=row['sha256'],bytes=size,archive=ar['name'],offset=offset))
    assert len(raw_assets) == 420
    inputs, expected = load(BATCH/'placements135-inputs.json'), load(BATCH/'placements135-expected.json')
    results = [json.loads(line) for line in (BATCH/'placements135-results.jsonl').read_text().splitlines()]
    provenance = load(BATCH/'placements135-asset-provenance.json')
    adts = [row for row in actual.values() if row['chain'].endswith('.adt')]
    assert len(adts) == 9 and provenance['assets'] == adts
    totals = Counter(); decoded_actual = {}
    for i,(case,want,actual_case) in enumerate(zip(inputs,expected,results)):
        assert set(case) == {'id','input'} and set(case['input']) == {'asset_path','asset_bytes','asset_sha256'}
        assert case['id'] == want['id'] == actual_case['id'] == i
        raw = Path(case['input']['asset_path']).read_bytes()
        assert len(raw) == case['input']['asset_bytes'] and hashlib.sha256(raw).hexdigest() == case['input']['asset_sha256']
        if i < 9:
            assert case['input']['asset_path'] == adts[i]['file'] and raw == raw_assets[adts[i]['chain']]
            decoded_actual[adts[i]['chain']] = decode_placements(raw, canonical(adts[i]['chain'].encode()).decode())
        else: assert raw == controlled(raw_assets[adts[0]['chain']],i-9)
        independent = projection(decode_placements(raw))
        assert json.loads(json.dumps(independent)) == want['vectors']
        assert actual_case['host_calls'] == 0 and actual_case['input_unchanged'] is True
        for kind in ('m2','wmo'):
            observed = actual_case['vectors'][kind]; projected = {k:observed[k] for k in ('capacity','length','records')}
            assert projected == independent[kind]
            backing = (BATCH/f'placements135-{i}-{kind}-records44.bin').read_bytes()
            assert len(backing) == observed['raw_backing_bytes'] == observed['capacity']*44
            assert hashlib.sha256(backing).hexdigest() == observed['raw_backing_sha256']
            for j,row in enumerate(independent[kind]['records']):
                words = struct.unpack_from('<11I',backing,j*44)
                assert words[0] == words[2] == len(bytes.fromhex(row['name_utf8_hex'])) and words[1] > 0
                assert list(words[3:]) == row['scalar_words']
                totals['strict_scalar_string_bytes'] += 40+len(bytes.fromhex(row['name_utf8_hex']))
            tail = backing[observed['length']*44:]
            totals['unwritten_tail_bytes'] += len(tail); totals['nonzero_unwritten_tail_bytes'] += sum(x != 0 for x in tail)
            totals['all_'+kind] += observed['length']
    for key in ('strict_scalar_string_bytes','unwritten_tail_bytes','nonzero_unwritten_tail_bytes'): assert totals[key] == receipt[key]
    assert (totals['all_m2'],totals['all_wmo']) == (11649,76)
    wdt = raw_assets['world\\maps\\azeroth\\azeroth.wdt']; main = [r for t,_,r in chunk_rows(wdt) if t == b'NIAM']; assert len(main) == 1 and len(main[0]) == 32768
    cx,cy = [number(x) for x in plan['center_xy_bits']]; extent = number(plan['extent_bits'])
    tx,ty = [min(63,max(0,int(rounded(rounded(number(0x46855555)-x)/number(0x44055555))))) for x in (cx,cy)]
    paths = [f'World\\Maps\\Azeroth\\Azeroth_{y}_{x}.adt' for x in range(tx-1,tx+2) for y in range(ty-1,ty+2) if 0<=x<64 and 0<=y<64 and main[0][(x*64+y)*8]&1]
    assert paths == plan['adt_requests']; tiles = [(name,decoded_actual[canonical(name.encode()).decode()]) for name in paths]
    independent_selections = {}
    for phase in ('nav_m2','nav_wmo','secondary_wmo'):
        kind = 'm2' if phase == 'nav_m2' else 'wmo'; seen = set(); selected = []
        for filename,tile in tiles:
            for row in tile[kind]['records']:
                if phase.startswith('nav_'):
                    margin = rounded(extent+rounded(max(number(row['scale_bits']),1)*40)) if kind == 'm2' else rounded(extent+400)
                    if any(abs(rounded(number(row['scalar_words'][axis])-center)) >= margin for axis,center in enumerate((cx,cy))): continue
                if row['unique_id'] in seen: continue
                seen.add(row['unique_id']); name = bytes.fromhex(row['name_utf8_hex'])
                selected.append(dict(kind=kind,position_xyz_bits=row['scalar_words'][:3],rotation_degrees_bits=row['scalar_words'][3:6],scale_bits=row['scale_bits'],unique_id=row['unique_id'],wmo_sets_word=row['wmo_sets_word'],source_record_index=row['source_record_index'],name_utf8_hex=row['name_utf8_hex'],source_file_hex=filename.encode().hex(),chain=collision_chain(kind,name)))
        assert selected == plan['selections'][phase]
        independent_selections[phase] = selected
    first = lambda rows: list(dict.fromkeys(row['chain'] for row in rows))
    m2 = first(independent_selections['nav_m2']); roots = first(independent_selections['nav_wmo']+independent_selections['secondary_wmo']); all_wmo = []
    for name in roots:
        mohd = [raw for tag,_,raw in chunk_rows(raw_assets[name]) if tag == b'DHOM']; assert len(mohd) == 1
        count = struct.unpack_from('<I',mohd[0],4)[0]
        all_wmo += [name] + [name[:-4]+f'_{i:03d}.wmo' for i in range(count)]
    assert m2 == plan['first_m2_requests'] == [name for name in actual if name.endswith('.m2')]
    assert roots == plan['first_wmo_root_requests'] and all_wmo == plan['first_wmo_all_requests'] == [name for name in actual if name.endswith('.wmo')]
    assert [len(independent_selections[x]) for x in ('nav_m2','nav_wmo','secondary_wmo')] == [244,14,36]
    assert plan['new_original_calls'] == plan['new_original6730_cases'] == 0
    trace = load(BATCH/'static/placement-trace.json'); assert len(trace['functions']) == 7
    with SOURCE.open('rb') as stream, mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as original, (BATCH/'research135-exports.wasm').open('rb') as stream2, mmap.mmap(stream2.fileno(),0,access=mmap.ACCESS_READ) as module:
        assert hashlib.sha256(original).hexdigest() == receipt['original_sha256'] == 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
        old,new = sections(original),sections(module); assert [s[0] for s in old] == [s[0] for s in new] and 8 not in [s[0] for s in old]
        for a,b in zip(old,new):
            if a[0] != 7: assert original[a[1]:a[3]] == module[b[1]:b[3]]
        prior,added = exports(original,next(x for x in old if x[0] == 7)),exports(module,next(x for x in new if x[0] == 7))
        assert added == prior+[('research135_adt_parse',0,1446)]
        db = sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True); db.row_factory = sqlite3.Row
        with (PROFILE/'official-0.135.1-full.wat').open('rb') as wat:
            for row in trace['functions']:
                source = db.execute('select *from functions where idx=?',(row['index'],)).fetchone()
                assert all(source[k] == row[k] for k in source.keys())
                wat.seek(source['wat_start']); text = wat.read(source['wat_end']-source['wat_start'])
                assert text == (BATCH/'static'/f"{row['index']}.wat").read_bytes()
                assert hashlib.sha256(text).hexdigest() == row['wat_sha256']
                assert hashlib.sha256(original[source['body_start']:source['body_end']]).hexdigest() == row['body_sha256']
    assert receipt['process']['exit_code'] == 0 and receipt['runtime']['cases'] == receipt['runtime']['fresh_instances'] == 13
    assert receipt['runtime']['denied_imports'] == 878 and receipt['runtime']['memory_cap_bytes'] == 33554432
    assert receipt['runtime']['peak_memory_bytes'] <= 33554432
    assert not receipt['complete_world_producer'] and receipt['full6730_selection_new_cases'] == 0
    for rows in (original_sources,plan_sources):
        for name,digest in rows.items(): assert sha(ROOT/name) == digest
    assert sha(own) == own_sha and sha(receipt_path) == RECEIPT_SHA and sha(PLAN) == PLAN_SHA
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('world-placements0135-independent-review-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    (out/'asset-recheck.json').write_text(json.dumps(dict(archives={k:v[2] for k,v in archives.items()},files=checked_assets),indent=2)+'\n')
    review = dict(status='passed_scoped_independent_read_only_review',reviewer_sha256=own_sha,receipt=str(receipt_path.relative_to(ROOT)),receipt_sha256=RECEIPT_SHA,historical_plan=str(PLAN.relative_to(ROOT)),historical_plan_sha256=PLAN_SHA,
                  original_source_closure=14,plan_source_closure=10,current_and_frozen_sources_match=True,original_cases_reviewed=13,original_calls_reviewed=13,new_original_calls=0,new_original6730_cases=0,
                  independent_chunk_record_float32_recomputation=True,raw44B_backing_rechecked=True,counts=dict(totals),actual_MPQ_files_independently_reread=420,
                  actual_ADT_files=9,controlled_ADT_inputs_independently_reconstructed=4,adt_order_independently_recomputed=True,selection_counts={k:len(v) for k,v in independent_selections.items()},first_request_counts=dict(m2=len(m2),wmo_roots=len(roots),wmo_all=len(all_wmo)),
                  exact_input_shape_expected_separated=True,only_original_export_section_changed=True,static_functions_rechecked=7,production_model_imported_or_executed=False,original_program_executed=False,network_used=False,user_saves_accessed=False,
                  full_world_producer=False,new_mainloop_frames=0,goal_complete=False,limitations=['1446 canonical placement projection only; names/pointer ownership and terrain are not newly fully modeled.','6730 placement selection is static plus historical read-set comparison; no fresh complete6730 differential.','Other maps/modes, malformed files, untested13850 branches, VFS/ownership/render/completeworld and fullgame remain outside this review.'],evidence_files={p.name:sha(p) for p in out.iterdir()})
    target=out/'review.json';target.write_text(json.dumps(review,indent=2)+'\n')
    wrapper={**review,'review_path':str(target.relative_to(ROOT)),'review_sha256':sha(target)}
    report=ROOT/'reports/2026-11-01-world-placements0135-independent-review.json';report.write_text(json.dumps(wrapper,indent=2)+'\n')
    report.with_suffix('.md').write_text(f'''# ADT placement 与实例计划独立复核

限定域独审通过：[最终13例／13次完整1446收据](../{receipt_path.relative_to(ROOT)})、14份冻结源与[10源历史计划](../{PLAN.relative_to(ROOT)})均重新读取并核对。[独审证据](../{target.relative_to(ROOT)}) SHA `{sha(target)}`。

没有导入或运行作者 placement 模型，也未执行原件。独立重读 MPQ 头、解密索引和420份原始文件；重新解析9份真实ADT及重建4份控制输入，独立计算坐标binary32、scale、UID、sets及全部有序记录，与expected、原件结果及44B backing一致。核对11,649 M2／76 WMO记录、1,181,761B声明字节；254,100B非活跃尾部仍为未知，405B非零。

从实际WDT独立重算9ADT顺序，重算244个nav M2／14个nav WMO／36个secondary WMO及其有序唯一ID选择；31条M2、23条WMO root和410条WMO root/group首次请求与历史原件读集一致。这仍是历史读集投影复核，新增原件调用0、full6730案例0、主循环帧0；不升级为完整world／游戏验证。

核对研究模块仅增加原1446导出、其余section／原body保持；7个静态函数的SQLiteRO索引、seek片段与原WASM body哈希相符。其它地图、错误恢复、未直接验证的13850分支、VFS／所有权／渲染与完整游戏未知项继续保留。
''')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),status=review['status'],counts=dict(totals),new_original_calls=0)))


if __name__ == '__main__':
    main()
