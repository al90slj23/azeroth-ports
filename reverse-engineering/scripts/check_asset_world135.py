#!/usr/bin/env python3
"""Compare a frozen independent asset build with one historical original world.

No original code executes. Original captures are comparison data, read only
after the independent output and its source hashes have been frozen on disk.
This does not add a new original case or validate a full application lifecycle.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / 'evidence/entry-world0135-probe-20261101T092959.623703Z'
WORLD_SHA = 'f651042520491d22e9910b1c01b34eaf90c73e004a4cd60ce310428186d9291a'
OPENING_SHA = '23af074eaebd5c1ac915ee8f8a35430b94c4276c822bc15aaf505e9c29911aaf'
WORLD_RC, GAME = 26204808, 14554176


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


class Memory:
    def __init__(self, path, digest):
        assert sha(path) == digest, 'Historical original capture identity differs'
        self.raw = path.read_bytes()
    def take(self, start, count):
        if start < 0 or count < 0 or start + count > len(self.raw):
            raise ValueError('Original range outside captured memory')
        return self.raw[start:start+count]
    def u(self, offset): return struct.unpack('<I', self.take(offset, 4))[0]


def compare_world(memory, output, artifacts):
    errors = []
    rc = struct.unpack('<31I', memory.take(WORLD_RC, 124))
    checks = {}
    tilecap,tileptr,tilecount,boundcap,boundptr,boundcount = rc[2:8]
    assert 0 < tilecount <= tilecap <= 512 and tilecount == boundcount <= boundcap
    terrain = bytearray(struct.pack('<I',tilecount))
    for i in range(tilecount):
        tile = struct.unpack('<9I', memory.take(tileptr+i*36,36))
        cap,pointer,count=tile[:3]
        assert 0 < count <= cap <= 1024
        terrain.extend(memory.take(boundptr+i*16,16))
        terrain.extend(struct.pack('<I',count))
        for j in range(count):
            raw=memory.take(pointer+j*264,264)
            vcap,vptr,vcount=struct.unpack_from('<3I',raw)
            assert 0 < vcount <= vcap <= 65536
            terrain.extend(struct.pack('<HI',struct.unpack_from('<H',raw,260)[0],vcount))
            terrain.extend(memory.take(vptr,vcount*12))
    expected=(output/artifacts['terrain']['file']).read_bytes()
    different=sum(a!=b for a,b in zip(expected,terrain))
    checks['terrain']={'independent_bytes':len(expected),'original_bytes':len(terrain),
        'different_bytes':different,'independent_sha256':hashlib.sha256(expected).hexdigest(),
        'original_sha256':hashlib.sha256(terrain).hexdigest()}
    if different or len(expected)!=len(terrain):errors.append({'field':'terrain',**checks['terrain']})
    for name, indices, filename in [('navigation', (8, 9, 10, 11, 13), 'navigation.bin'),
                                    ('secondary', (23, 24, 25, 26, 28), 'secondary-height.u32le')]:
        ci, pi, ni, oi, wi = indices
        size = 1 if name == 'navigation' else 4
        assert rc[ni] <= rc[ci] and rc[ni] == rc[wi]**2
        expected = (output / filename).read_bytes()
        actual = memory.take(rc[pi], rc[ni]*size)
        positions = [i for i, (a,b) in enumerate(zip(expected,actual)) if a != b]
        art = artifacts[name]
        shape_ok = len(expected) == len(actual) and list(art['origin_xy_bits']) == list(rc[oi:oi+2]) and art['width'] == rc[wi]
        checks[name] = {'bytes': len(expected), 'shape_equal': shape_ok,
                       'independent_sha256': hashlib.sha256(expected).hexdigest(),
                       'original_sha256': hashlib.sha256(actual).hexdigest(),
                       'different_bytes': len(positions), 'first_different_offsets': positions[:64]}
        if positions or not shape_ok:
            errors.append({'field': name, **checks[name]})
            if name == 'secondary':
                words = sorted(set(i//4 for i in positions))
                checks[name]['different_words'] = len(words)
                checks[name]['first_word_differences'] = [
                    {'index': i, 'xy': [i%rc[wi], i//rc[wi]],
                     'independent': struct.unpack_from('<I',expected,i*4)[0],
                     'original': struct.unpack_from('<I',actual,i*4)[0]}
                    for i in words[:64] if i*4+4<=min(len(expected),len(actual))]
    return errors, checks


def compare_opening(memory, expected):
    errors, known, unknown = [], 0, 0
    actual = {'phase2587': memory.raw[GAME+2587],
              'counter2408': memory.u(GAME+2408),
              'rng_words': [memory.u(GAME+1720+i*4) for i in range(4)],
              'player_xyz': [memory.u(GAME+1416+i*4) for i in range(3)]}
    for key,value in actual.items():
        if expected[key] != value:
            errors.append({'field': key, 'independent': expected[key], 'original': value})
    layouts = {'companions': (2108,2112,2116,88), 'units': (1784,1788,1792,424),
               'pickups': (1868,1872,1876,56), 'special': (1916,1920,1924,40),
               'windows': (1964,1968,1972,8), 'boundaries': (2120,2124,2128,8)}
    for name,(co,po,no,stride) in layouts.items():
        cap,pointer,count = (memory.u(GAME+i) for i in (co,po,no))
        if not 0 <= count <= cap <= 4096: raise ValueError('Original vector shape')
        want = expected[name]
        if (want['capacity'],want['count']) != (cap,count):
            errors.append({'field': name+'.shape', 'independent': [want['capacity'],want['count']], 'original': [cap,count]})
        for i,row in enumerate(want['storage']):
            if len(row) != stride or i >= cap: raise ValueError('Compared vector shape differs')
            raw = memory.take(pointer+i*stride,stride)
            for j,byte in enumerate(row):
                if byte is None: unknown += 1; continue
                known += 1
                if byte != raw[j]:
                    errors.append({'field': name, 'slot': i, 'byte': j, 'independent': byte, 'original': raw[j]})
    def queue(co,po,no,stride,packets):
        cap,pointer,count = (memory.u(GAME+i) for i in (co,po,no))
        if not 0 <= count <= cap <= 4096: raise ValueError('Original queue shape')
        result = []
        for i in range(count):
            q=pointer+i*stride; length=memory.u(q+8);capacity=memory.u(q)
            if not 0 <= length <= capacity <= 1048576: raise ValueError('Original payload shape')
            payload=memory.take(memory.u(q+4),length).hex()
            result.append({'opcode':struct.unpack('<H',memory.take(q+12,2))[0], 'payload_hex':payload} if packets else payload)
        return result
    packets = queue(1880,1884,1888,16,True)
    notifications = queue(1892,1896,1900,12,False)
    if expected['packets'] != packets:
        errors.append({'field':'opening_packets','independent_count':len(expected['packets']),
                       'original_count':len(packets),'first_different_indices':[
                           i for i,(a,b) in enumerate(zip(expected['packets'],packets)) if a != b][:64]})
    if expected['notifications_utf8_hex'] != notifications:
        errors.append({'field':'opening_notifications','independent':expected['notifications_utf8_hex'],'original':notifications})
    return errors, {'known_record_bytes':known, 'unwritten_or_inactive_record_bytes':unknown,
                    'packet_count':len(packets),'packet_bytes':sum(len(x['payload_hex'])//2 for x in packets),
                    'notification_count':len(notifications), **actual}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('independent_directory',type=Path)
    args=parser.parse_args();directory=args.independent_directory.resolve()
    independent=json.loads((directory/'receipt.json').read_text())
    assert independent['kind']=='independent_asset_to_world_to_default_opening'
    assert independent['original_program_executed'] is False and independent['original_memory_read'] is False
    assert independent['source_sha256_before']==independent['source_sha256_after']
    assert sha(directory/'inputs.json')==independent['inputs_sha256']
    assert json.loads((directory/'inputs.json').read_text())==independent['inputs']
    assert independent['inputs']['opening']=={'class_byte':1,'race_byte':1,'region_index':0,
        'app_lcg_seed_u64':0,'object_id_u64':0}, 'Historical capture has one explicit opening input'
    for path,digest in independent['source_sha256_before'].items():
        assert sha(ROOT/path)==digest
        assert sha(directory/'source-snapshot'/path)==digest
    artifacts=independent['world_artifacts']
    frozen={'receipt.json':sha(directory/'receipt.json'),'opening.json':sha(directory/'opening.json'),
            'inputs.json':sha(directory/'inputs.json')}
    for name in ('terrain','navigation','secondary'):
        entry=artifacts[name];assert sha(directory/entry['file'])==entry['sha256'];frozen[entry['file']]=entry['sha256']
    assert frozen['opening.json']==independent['opening']['sha256']
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('asset-world0135-historical-comparison-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    (out/'independent-output-before.json').write_text(json.dumps(frozen,indent=2)+'\n')
    world_path=REFERENCE/'after_real_world6730.memory'
    opening_path=REFERENCE/'after_real_begin1089.memory'
    world=Memory(world_path,WORLD_SHA)
    errors,world_checks=compare_world(world,directory,artifacts)
    scalars={'primary_present':world.u(WORLD_RC+56)!=0xffffffff,
             'flat_height_bits':None if world.raw[WORLD_RC+120]==0 else world.u(WORLD_RC+116),
             'fallback_height_bits':world.u(WORLD_RC+116)}
    if independent['query_scalars']!=scalars:
        errors.append({'field':'query_scalars','independent':independent['query_scalars'],'original':scalars})
    del world
    opening=Memory(opening_path,OPENING_SHA)
    opening_errors,opening_checks=compare_opening(opening,json.loads((directory/'opening.json').read_text()))
    errors+=opening_errors
    assert all(sha(directory/p)==digest for p,digest in frozen.items())
    assert sha(world_path)==WORLD_SHA and sha(opening_path)==OPENING_SHA
    result={'version':'0.135.1','build':'0898d5e3',
        'kind':'independent_asset_build_vs_one_historical_original_world_and_opening',
        'status':'passed' if not errors else 'failed_preserved',
        'independent_directory':str(directory),'independent_output_sha256':frozen,
        'comparison_script_sha256':sha(Path(__file__)),
        'world_snapshot_sha256':WORLD_SHA,'opening_snapshot_sha256':OPENING_SHA,
        'world_comparison':world_checks,'opening_comparison':opening_checks,
        'differences':len(errors),'first_differences':errors[:128],
        'historical_original_cases':1,'new_original_calls':0,'new_original_cases':0,
        'fresh_original_bootstraps':0,'new_mainloop_frames':0,
        'scope':'Default empty-profile Elwynn/class1/race1/Appseed0/GUID0;nav andsecondary exact bits,opening known records/messages;not a fresh original differential or complete world/App ownership/game.',
        'independent_expected_frozen_before_original_capture_read':True,
        'installed_apps_or_saves_modified':False,'whole_game_complete':False}
    (out/'comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'directory':str(out),'status':result['status'],'differences':len(errors),
                      'world_comparison':world_checks,'opening_comparison':opening_checks},ensure_ascii=False))
    raise SystemExit(0 if not errors else 1)


if __name__=='__main__':
    main()
