#!/usr/bin/env python3
"""Review frozen asset/world/opening outputs without executing producer or original."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import ast
import hashlib
import json
import mmap
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'evidence/asset-world0135-independent-20261101T111736.050879Z'
COMPARISON = ROOT / 'evidence/asset-world0135-historical-comparison-20261101T112022.317639Z/comparison.json'
REFERENCE = ROOT / 'evidence/entry-world0135-probe-20261101T092959.623703Z'
OLDER = ROOT / 'evidence/world-snapshot0135-oracle-20261101T103934.606037Z'
ARCHIVES = ROOT / 'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'
EXPECTED_SCRIPTS = {
    'scripts/run_asset_world135.py': 'aa782f1b9c1833d2348507d5aa50d4a4071a1b7c1b1030b6960a7c418ceae304',
    'scripts/check_asset_world135.py': '0cf2cc93b38e048515565ea4d12e0aa42806dd8fd052dbc41cd2935b1f96e596'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def source_closure():
    """Independently follow every static reconstruction import, including packages."""
    base = ROOT / 'reconstruction'; pending = [ROOT/'scripts/run_asset_world135.py']; visited = set()
    while pending:
        path = pending.pop()
        if path in visited: continue
        visited.add(path); tree = ast.parse(path.read_text())
        package = list(path.relative_to(base).parts[:-1]) if path.is_relative_to(base) else []
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import): names = [x.name.split('.') for x in node.names]
            elif isinstance(node, ast.ImportFrom):
                prefix = package[:len(package)-node.level+1] if node.level else []
                parts = prefix + (node.module.split('.') if node.module else [])
                names = [parts] + [parts + [x.name] for x in node.names]
            for parts in names:
                if not parts or parts[0] not in ('core_spec','resource_spec'): continue
                for count in range(1,len(parts)+1):
                    folder = base.joinpath(*parts[:count]); file = folder.with_suffix('.py')
                    if file.is_file(): pending.append(file)
                    elif (folder/'__init__.py').is_file(): pending.append(folder/'__init__.py')
    return {str(path.relative_to(ROOT)) for path in visited}


class Capture:
    def __init__(self, path, digest):
        assert sha(path) == digest
        self.file = path.open('rb'); self.raw = mmap.mmap(self.file.fileno(),0,access=mmap.ACCESS_READ)
    def take(self, pointer, size):
        assert 0 <= pointer <= len(self.raw) and 0 <= size <= len(self.raw)-pointer
        return self.raw[pointer:pointer+size]
    def words(self, pointer, count):
        return struct.unpack('<'+'I'*count,self.take(pointer,count*4))
    def u(self, pointer): return self.words(pointer,1)[0]
    def close(self): self.raw.close(); self.file.close()


def original_terrain(capture, rc):
    tile_capacity,tile_pointer,tile_count,bounds_capacity,bounds_pointer,bounds_count = rc[2:8]
    assert 0 < tile_count <= tile_capacity <= 512 and tile_count == bounds_count <= bounds_capacity
    encoded = bytearray(struct.pack('<I',tile_count)); chunks = vertices = 0
    for i in range(tile_count):
        chunk_capacity,chunk_pointer,chunk_count = capture.words(tile_pointer+36*i,3)
        assert 0 < chunk_count <= chunk_capacity <= 1024
        encoded += capture.take(bounds_pointer+16*i,16)+struct.pack('<I',chunk_count)
        for j in range(chunk_count):
            chunk = chunk_pointer+264*j; capacity,pointer,count = capture.words(chunk,3)
            assert 0 < count <= capacity <= 65536
            holes = struct.unpack('<H',capture.take(chunk+260,2))[0]
            encoded += struct.pack('<HI',holes,count)+capture.take(pointer,count*12)
            chunks += 1; vertices += count
    return bytes(encoded),dict(tiles=tile_count,chunks=chunks,vertices=vertices)


def opening(capture, expected):
    game = 14554176
    state = dict(phase2587=capture.raw[game+2587],counter2408=capture.u(game+2408),
                 rng_words=list(capture.words(game+1720,4)),player_xyz=list(capture.words(game+1416,3)))
    assert all(expected[key] == value for key,value in state.items())
    counts = Counter(); vectors = {}
    for name,start,stride in (('companions',2108,88),('units',1784,424),('pickups',1868,56),
                              ('special',1916,40),('windows',1964,8),('boundaries',2120,8)):
        capacity,pointer,count = capture.words(game+start,3); value = expected[name]
        assert 0 <= count <= capacity <= 4096
        assert (capacity,count) == (value['capacity'],value['count'])
        assert len(value['storage']) == capacity
        for slot,row in enumerate(value['storage']):
            assert len(row) == stride; raw = capture.take(pointer+stride*slot,stride)
            for offset,byte in enumerate(row):
                if byte is None:
                    domain = 'active_unknown' if slot < count else 'inactive_unknown'
                    counts[domain] += 1; counts[domain+'_nonzero'] += raw[offset] != 0
                else:
                    assert type(byte) is int and 0 <= byte <= 255 and byte == raw[offset]
                    counts['known_record_bytes'] += 1
        vectors[name] = dict(capacity=capacity,count=count,stride=stride)
    def messages(start,stride,packet):
        capacity,pointer,count = capture.words(game+start,3); assert 0 <= count <= capacity <= 4096
        values = []
        for i in range(count):
            item = pointer+i*stride; cap,ptr,length = capture.words(item,3)
            assert 0 <= length <= cap <= 1048576
            raw = capture.take(ptr,length)
            values.append(dict(opcode=struct.unpack('<H',capture.take(item+12,2))[0],payload_hex=raw.hex()) if packet else raw.hex())
        return values
    packets,notifications = messages(1880,16,True),messages(1892,12,False)
    assert packets == expected['packets'] and notifications == expected['notifications_utf8_hex']
    return dict(state=state,vectors=vectors,record_bytes=dict(counts),packet_count=len(packets),
                packet_bytes=sum(len(row['payload_hex'])//2 for row in packets),notification_count=len(notifications))


def main():
    own = Path(__file__); own_sha = sha(own)
    for name,digest in EXPECTED_SCRIPTS.items(): assert sha(ROOT/name) == digest
    assert sha(BUILD/'receipt.json') == '4042ee79112521f67bca6d39447d9072a9b9b2f1c6f78d3b8fdab21a9d36f7c5'
    assert sha(COMPARISON) == '462e77e056e33c72609d55abac4fa2f4b4f2686706016a638dae6bd619d1f845'
    receipt,comparison = load(BUILD/'receipt.json'),load(COMPARISON)
    assert receipt['original_program_executed'] is receipt['original_memory_read'] is False
    assert receipt['new_original_differential_cases'] == receipt['mainloop_frames'] == 0
    assert comparison['status'] == 'passed' and comparison['differences'] == 0
    assert comparison['new_original_calls'] == comparison['new_original_cases'] == comparison['fresh_original_bootstraps'] == comparison['new_mainloop_frames'] == 0
    assert comparison['historical_original_cases'] == 1 and comparison['comparison_script_sha256'] == EXPECTED_SCRIPTS['scripts/check_asset_world135.py']
    before = receipt['source_sha256_before']; assert before == receipt['source_sha256_after'] == load(BUILD/'source-before.json')
    assert len(before) == 37 and source_closure() == set(before)
    for name,digest in before.items(): assert sha(ROOT/name) == sha(BUILD/'source-snapshot'/name) == digest
    # Read only frozen producer outputs first; historical captures follow below.
    frozen = comparison['independent_output_sha256']
    assert frozen == load(COMPARISON.parent/'independent-output-before.json')
    for name,digest in frozen.items(): assert sha(BUILD/name) == digest
    inputs = load(BUILD/'inputs.json'); assert inputs == receipt['inputs'] and sha(BUILD/'inputs.json') == receipt['inputs_sha256']
    assert inputs['opening'] == dict(class_byte=1,race_byte=1,region_index=0,app_lcg_seed_u64=0,object_id_u64=0)
    assert inputs['world'] == dict(map_id=0,center_xy_bits=[3323121664,3290316800],radius_bits=1123024896,fallback_height_bits=1116209152)
    manifest = Path(inputs['asset_manifest']); assert sha(manifest) == inputs['asset_manifest_sha256'] == receipt['asset_manifest_sha256']
    assets = {row['chain']:row for row in load(manifest)['requests'] if row['status'] == 200}
    names = receipt['asset_names']; assert len(names) == len(set(names)) == receipt['asset_files'] == 451
    assert set(receipt['asset_requests']) == set(names)
    asset_bytes = 0; asset_rows = []
    for name in names:
        row = assets[name]; path = Path(row['file']).resolve()
        assert path.is_relative_to(Path('/Volumes/RuiRui4TB')) and path.suffix == '.bin'
        raw = path.read_bytes(); assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
        # Independent raw archive reads additionally rule out capture contents masquerading as assets.
        block = row['block']; assert block['flags'] == 0x80000000 and block['compressed_size'] == block['size'] == len(raw)
        with (ARCHIVES/row['archive']).open('rb') as stream: stream.seek(block['offset']); archive_raw = stream.read(block['size'])
        assert archive_raw == raw
        asset_bytes += len(raw); asset_rows.append(dict(chain=name,bytes=len(raw),sha256=row['sha256'],archive=row['archive'],offset=block['offset']))
    assert asset_bytes == receipt['decoded_asset_bytes'] == 67281330
    extension_counts = Counter(Path(name.replace('\\','/')).suffix for name in names)
    assert extension_counts == {'.wdt':1,'.adt':9,'.m2':31,'.wmo':410}
    projection = load(BUILD/'opening.json'); assert sha(BUILD/'opening.json') == receipt['opening']['sha256']
    assert sha(OLDER/'opening135-fixtures.json') == '60f195fbebf29bc68c12b632b26b074c1e2ec28b194f8654dbc875752407d257'
    prior = load(OLDER/'opening135-fixtures.json')[0]
    assert prior['input'] == dict(class_byte=1,race_byte=1,region_index=0,app_lcg_seed_u64='0',object_id_u64='0')
    assert projection == prior['expected'], 'Independent asset world must preserve entire previously reviewed opening projection and unknown mask'
    world = Capture(REFERENCE/'after_real_world6730.memory',comparison['world_snapshot_sha256'])
    assert comparison['world_snapshot_sha256'] == 'f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
    rc = world.words(26204808,31); terrain,terrain_counts = original_terrain(world,rc)
    terrain_output = (BUILD/'terrain-query.bin').read_bytes(); assert terrain_output == terrain
    assert terrain_counts == dict(tiles=9,chunks=2304,vertices=334080)
    world_checks = dict(terrain=dict(bytes=len(terrain),sha256=hashlib.sha256(terrain).hexdigest(),**terrain_counts))
    for name,cap_i,ptr_i,count_i,origin_i,width_i,stride in (
            ('navigation',8,9,10,11,13,1),('secondary',23,24,25,26,28,4)):
        art = receipt['world_artifacts'][name]; raw = (BUILD/art['file']).read_bytes()
        assert 0 < rc[count_i] <= rc[cap_i] and rc[count_i] == rc[width_i]**2
        assert list(rc[origin_i:origin_i+2]) == art['origin_xy_bits'] and rc[width_i] == art['width']
        assert raw == world.take(rc[ptr_i],rc[count_i]*stride)
        assert len(raw) == art['bytes'] and hashlib.sha256(raw).hexdigest() == art['sha256']
        world_checks[name] = dict(bytes=len(raw),sha256=art['sha256'],origin_xy_bits=list(rc[origin_i:origin_i+2]),width=rc[width_i])
    assert len(terrain) == receipt['world_artifacts']['terrain']['bytes'] == 4022968
    assert hashlib.sha256(terrain).hexdigest() == receipt['world_artifacts']['terrain']['sha256']
    assert receipt['query_scalars'] == dict(primary_present=rc[14]!=0xffffffff,flat_height_bits=None if world.raw[26204808+120] == 0 else rc[29],fallback_height_bits=rc[29])
    world.close()
    original = Capture(REFERENCE/'after_real_begin1089.memory',comparison['opening_snapshot_sha256'])
    assert comparison['opening_snapshot_sha256'] == '23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
    opening_checks = opening(original,projection); original.close()
    assert (opening_checks['record_bytes']['known_record_bytes'],opening_checks['packet_count'],opening_checks['packet_bytes'],opening_checks['notification_count']) == (2118,78,8410,1)
    for key in ('terrain','navigation','secondary'):
        assert comparison['world_comparison'][key]['different_bytes'] == 0
        assert comparison['world_comparison'][key]['independent_sha256'] == comparison['world_comparison'][key]['original_sha256'] == world_checks[key]['sha256']
    for name,digest in frozen.items(): assert sha(BUILD/name) == digest
    for name,digest in before.items(): assert sha(ROOT/name) == digest
    for name,digest in EXPECTED_SCRIPTS.items(): assert sha(ROOT/name) == digest
    assert sha(own) == own_sha
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('asset-world0135-independent-review-%Y%m%dT%H%M%S.%fZ'); out.mkdir()
    (out/'asset-payload-recheck.json').write_text(json.dumps(asset_rows,indent=2)+'\n')
    review = dict(status='passed_scoped_independent_read_only_review',reviewer_sha256=own_sha,producer_scripts=EXPECTED_SCRIPTS,independent_directory=str(BUILD.relative_to(ROOT)),independent_receipt_sha256=sha(BUILD/'receipt.json'),comparison=str(COMPARISON.relative_to(ROOT)),comparison_sha256=sha(COMPARISON),
                  static_source_closure_matches_frozen_imports=37,all_current_and_frozen_sources_verified=True,exact_explicit_inputs_verified=True,all451_asset_payloads_sha_and_raw_MPQ_reads_verified=True,decoded_asset_bytes=asset_bytes,asset_extensions=dict(extension_counts),
                  captures_read_only_after_independent_output_freeze=True,world_comparison=world_checks,opening_comparison=opening_checks,whole_opening_matches_prior_frozen_fixture=True,unknown_record_mask_not_weakened=True,
                  author_producer_or_checker_executed=False,original_program_executed=False,historical_original_cases_reviewed=1,new_original_calls=0,new_original_cases=0,new_mainloop_frames=0,world_ownership_or_full_App_validated=False,whole_game_complete=False,
                  limitations=['One historical empty-profile Elwynn/class1/race1/seed0/GUID0 case, not a fresh original differential.','Only canonical terrain/query geometry, nav/secondary values and opening written/logical records/messages are compared; heap pointers/allocator/ownership remain unmodeled.','Rendering, complete App4253/main880, other maps/modes, profiles/saves/UI/multiplayer/fullgame remain incomplete.'],evidence_files={p.name:sha(p) for p in out.iterdir()})
    target=out/'review.json';target.write_text(json.dumps(review,indent=2)+'\n')
    report=ROOT/'reports/2026-11-01-asset-world0135-independent-review.json';report.write_text(json.dumps({**review,'review_path':str(target.relative_to(ROOT)),'review_sha256':sha(target)},indent=2)+'\n')
    report.with_suffix('.md').write_text(f'''# 真实资源到 world 查询与默认开局的独立复核

限定单例复核通过：[纯模型输出收据](../{BUILD.relative_to(ROOT)}/receipt.json)和[历史原件比较](../{COMPARISON.relative_to(ROOT)})的冻结产物、37份静态导入闭包／当前源码／source-snapshot一致。[独审证据](../{target.relative_to(ROOT)}) SHA `{sha(target)}`。

没有运行作者CLI、checker或原件。独立校验显式class／race／seed／GUID／地图输入，重读451份asset文件及相应MPQ原payload（67,281,330B），确认输入为真实WDT／ADT／M2／WMO资源。原件内存仅用于比较已冻结输出。

独立解码历史原件指针与结构，重编码4,022,968B地形查询几何（9 tiles／2,304 chunks／334,080 vertices），并逐字核对78,400B导航及1,254,400B secondary高度。独立解析开局6个向量与2种消息队列，核对2,118B已还原记录、78包／8,410B、1通知、RNG／counter87／位置／phase。新开局投影与已独审旧批case0整体一致，None未知字节mask没有缩减。

本轮是独立asset生产结果对1个历史原件样本的验收，新增原件调用／案例／bootstrap／主循环帧均为0。几何规范不冒充原heap/Rc布局；完整4253 App／880主循环、所有权、其它地图模式、渲染／存档／UI／联机和完整游戏仍未完成。
''')
    print(json.dumps(dict(directory=str(out),review_sha256=sha(target),status=review['status'],world=world_checks,opening=opening_checks,new_original_calls=0)))


if __name__ == '__main__':
    main()
