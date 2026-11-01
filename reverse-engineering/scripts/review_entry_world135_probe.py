#!/usr/bin/env python3
"""Read-only provenance/state review of true-world observation; never run WASM."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import argparse, hashlib, json, mmap, os, sqlite3, struct, sys

from review_gameplay_phase135 import ROOT, ORIGINAL, ORIGINAL_SHA, sha, sections, bodies, uint
from review_headless135 import exports, signatures

DEFAULT = 'entry-world0135-probe-20261101T092959.623703Z'
RECEIPT_SHA = '530f079d322365691ce897120ac0014be0da416eb048861b4d42ab988160556c'
ALLOWED = {0,337,338,343,499,521,523,641,643,644,645,658,659,660,735,773,774,804,827,835,845,848,851,877}
ROLES = {'entry135_load_account': (2902, '7f', ''),
         'entry135_apply_unlocks': (6959, '7f7f7e7e', ''),
         'entry135_construct_world_game': (6730, '7f7f', ''),
         'entry135_begin_run': (1089, '7f', '')}


def u(raw, offset): return struct.unpack_from('<I', raw, offset)[0]
def q(raw, offset): return struct.unpack_from('<Q', raw, offset)[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', default=DEFAULT)
    args = parser.parse_args()
    batch = ROOT/'evidence'/args.batch
    receipt = batch/'entry-world135-probe-receipt.json'
    assert args.batch == DEFAULT and sha(receipt) == RECEIPT_SHA
    d = json.loads(receipt.read_text())
    assert d['source_before'] == d['source_after'] and len(d['source_before']) == 9
    for name, digest in d['source_before'].items():
        assert sha(ROOT/name) == digest == sha(batch/'source-snapshot'/name), name
    for name, digest in d['artifacts'].items(): assert sha(batch/name) == digest, name
    assert d['process']['exit_code'] == 0 and d['process']['seconds'] < 120
    assert d['new_independent_model_cases'] == 0 and not d['user_profile_used']
    config = json.loads((batch/'entry-world135-config.json').read_text())
    rt = json.loads((batch/'entry-world135-runtime.json').read_text())
    assert rt == d['runtime'] and rt['status'] == 'original_entry_returned' and rt['error'] is None
    result = rt['result']
    assert result['status'] == rt['status'] and result['error'] is None
    assert not rt['blocked'] and not rt['browserErrors']
    assert not rt['external_network_permitted'] and not rt['user_profile_used']
    assert result['page_cap_negative_checked'] and result['max_memory_bytes'] == 166395904
    assert config['memory_page_cap'] == 4096 and config['memory_cap_bytes'] == rt['memory_cap_bytes'] == 256*1024*1024
    assert config['capture_chunk_bytes'] == 1048576
    assert not result['all_storage_keys'] and not result['session_keys'] and not result['indexeddb_databases']
    assert not result['selected_profile_producer_complete'] and result['independent_model_cases'] == 0
    assert not result['appstart_exports_called'] and not result['finalizer_called']

    assert sha(ORIGINAL) == ORIGINAL_SHA == d['original_sha256']
    original = ORIGINAL.read_bytes()
    module = Path(config['wasm_path']).read_bytes()
    assert hashlib.sha256(module).hexdigest() == config['wasm_sha256']
    a, b = sections(original), sections(module)
    assert len(a) == len(b) and 8 not in [x[0] for x in a]
    for x, y in zip(a, b):
        assert x[0] == y[0]
        if x[0] != 7: assert x[1] == y[1], x[0]
    old_exports = exports(original, next(x for x in a if x[0] == 7))
    new_exports = exports(module, next(x for x in b if x[0] == 7))
    assert new_exports == old_exports + [(name, 0, values[0]) for name, values in ROLES.items()]
    sig = signatures(original, a)
    code = bodies(original, a)
    assert len(config['roles']) == len(ROLES)
    for role in config['roles']:
        index, params, returns = ROLES[role['name']]
        assert role['index'] == index and sig(index) == (params, returns)
        begin, end = code[index-878]
        assert role['body_start'] == begin and role['body_end'] == end
        assert hashlib.sha256(original[begin:end]).hexdigest() == role['body_sha256']
    glue = Path(config['glue_path']).read_bytes()
    official = ROOT/'originals/official-acquisition-20261101T030310.926207Z/official-wenilla.js'
    prefix = official.read_bytes()
    assert sha(official) == config['official_glue_sha256'] == rt['source_glue_sha256']
    assert glue[:len(prefix)] == prefix and hashlib.sha256(glue).hexdigest() == config['glue_sha256']
    tail = glue[len(prefix):].decode()
    assert '__wbg_get_imports()' in tail and 'wasm=instance.exports' in tail
    assert not any(x in tail for x in ('finalize', '__wbindgen_start', 'initSync('))

    imports = {x['id']: x for x in config['imports']}
    assert len(imports) == 878 and {i for i, x in imports.items() if x['allowed']} == ALLOWED
    assert rt['other_denied_imports'] == 854 and 649 not in ALLOWED
    for row in result['imports']:
        meta = imports[row['id']]
        assert row['allowed'] and meta['allowed'] and row['name'] == meta['name'] and 'error' not in row
    assert len(result['imports']) == 3396 and len({x['id'] for x in result['imports']}) == 16
    storage = [x for x in result['imports'] if x['id'] == 641]
    assert len(storage) == 1 and storage[0]['storage_key'] == 'rogue.characters' and not storage[0]['storage_has_key']
    calls = result['entries']
    assert len(calls) == 10 and sum(x['name'] == '__wbindgen_malloc' for x in calls) == 6
    assert [x['name'] for x in calls if x['name'] != '__wbindgen_malloc'] == list(ROLES)
    assert all(x['sequence'] == i and x['returned'] and 'error' not in x for i, x in enumerate(calls))
    for pid in (d['process']['pid'], rt['browser_pid'], rt['worker_pid']):
        try: os.kill(pid, 0)
        except ProcessLookupError: pass
        else: raise AssertionError(('Owned process is still present', pid))
    lifecycle = rt['lifecycle']
    assert any(x['event'] == 'browser_final' and x['exit_code'] == 0 for x in lifecycle)
    assert any(x['event'] == 'asset_worker_final' and x['signal_code'] == 'SIGTERM' for x in lifecycle)
    assert any(x['event'] == 'http_server_closed' for x in lifecycle)
    launch = next(x for x in lifecycle if x['event'] == 'browser_started')
    assert any(x.startswith('--user-data-dir='+str(batch/'browser-tmp')) for x in launch['spawnargs'])
    origin = next(x['origin'] for x in lifecycle if x['event'] == 'http_listening')
    assert all(x['url'].startswith(origin+'/') and x['status'] == 200 for x in rt['requests'])
    assert all(x['bytes'] <= config['capture_chunk_bytes'] for x in rt['requests'] if x['method'] == 'POST')

    inventory = json.loads((batch/'actual-assets-inventory.json').read_text())
    index = Path(config['asset_index_path'])
    assert sha(index) == config['asset_index_sha256'] == inventory['index_sha256']
    assert len(inventory['requests']) == 453 and inventory['decoded_bytes'] == 83632785
    assert not inventory['aliasing'] and not inventory['latest135_asset_equivalence']
    con = sqlite3.connect(index.resolve().as_uri()+'?mode=ro', uri=True)
    con.row_factory = sqlite3.Row
    sys.path.insert(0, str(ROOT/'reconstruction'))
    from resource_spec.mpq import Archive
    archives = {}
    for row in config['archives']:
        path = ROOT/'originals/official-acquisition-20261031T235700.049192Z/windows-rar-extracted/AzerothSurvivors/Data'/row['name']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
        archive = Archive(path)
        assert hashlib.sha256(archive.hash_table_bytes).hexdigest() == row['hash_table_sha256']
        assert hashlib.sha256(archive.block_table_bytes).hexdigest() == row['block_table_sha256']
        archives[row['name']] = archive
    assets = {}
    for asset in inventory['requests']:
        assert asset['status'] == 200 and not asset['archive_precedence_inferred']
        row = asset['prior_index_row']
        indexed = dict(con.execute('select * from files where archive=? and hash_slot=?', (asset['archive'], asset['hash_slot'])).fetchone())
        assert row == indexed
        assert asset['sha256'] == row['decoded_sha256'] == row['reference_sha256']
        assert asset['bytes'] == row['decoded_bytes']
        owners = [dict(x) for x in con.execute('select * from files where normalized_name=?', (row['normalized_name'],))]
        assert {x['decoded_sha256'] for x in owners} == {asset['sha256']}
        actual = archives[asset['archive']].read(row['name'])
        assert hashlib.sha256(actual).hexdigest() == asset['sha256'] and len(actual) == asset['bytes']
        assert sha(Path(asset['file'])) == asset['sha256'] and Path(asset['file']).read_bytes() == actual
        assets[asset['path']] = asset
    data_gets = [x for x in rt['requests'] if x['method'] == 'GET' and x['path'].startswith('/data/')]
    assert len(data_gets) == 561
    from urllib.parse import unquote
    for row in data_gets:
        if row['path'] == '/data/__index':
            assert row['sha256'] == config['name_index_sha256'] == sha(Path(config['name_index_path']))
        else:
            asset = assets[unquote(row['path'][6:])]
            assert row['sha256'] == asset['sha256'] and row['bytes'] == asset['bytes']

    snaps = result['snapshots']
    assert [x['label'] for x in snaps] == ['declared_input_before_account', 'after_real_account2902', 'after_real_unlocks6959', 'after_real_world6730', 'after_real_begin1089']
    assert snaps[0]['world_cache5116'] == 0 and not snaps[0]['storage_keys']
    assert len(rt['captures']) == 4
    outputs = []
    for snap, capture in zip(snaps[1:], rt['captures']):
        assert snap['memory_artifact'] == capture and capture['complete']
        path = batch/capture['file']
        assert sha(path) == capture['sha256'] and path.stat().st_size == capture['bytes'] == snap['memory_bytes']
        with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as memory:
            App, G = snap['App'], snap['G']
            assert memory[App:App+5168].hex() == snap['app5168_hex']
            assert memory[G:G+2592].hex() == snap['game2592_hex']
            if snap['label'] in ('after_real_world6730', 'after_real_begin1089'):
                world = u(memory, App+5116)
                assert world == snap['world_rc_pointer'] == u(memory, G+2348) == 26204808
                assert memory[world:world+124].hex() == snap['world_rc124_hex']
                assert u(memory, world) == 2 and u(memory, world+4) == 1 and memory[world+120] == 0
                assert u(memory, world+32) == u(memory, world+40) == 78400
                assert u(memory, world+92) == u(memory, world+100) == 313600
                assert (u(memory, world+52), u(memory, world+112)) == (280, 560)
                npc_count, pickup_count = u(memory, G+1792), u(memory, G+1876)
                assert (npc_count, pickup_count, memory[G+2587]) == ((0, 0, 0) if snap['label'].endswith('6730') else (4, 2, 1))
                assert (npc_count, pickup_count, memory[G+2587]) == (snap['npc_count'], snap['pickup_count'], snap['phase2587'])
                units = [memory[u(memory, G+1788)+j*424:u(memory, G+1788)+(j+1)*424].hex() for j in range(npc_count)]
                pickups = [memory[u(memory, G+1872)+j*56:u(memory, G+1872)+(j+1)*56].hex() for j in range(pickup_count)]
                assert all(u(bytes.fromhex(x), 284) == 5415572 and u(bytes.fromhex(x), 0) == 0 for x in units)
                if pickups:
                    assert [(u(bytes.fromhex(x),8),u(bytes.fromhex(x),12),u(bytes.fromhex(x),36)) for x in pickups] == [(2,2,9005),(2,1,9005)]
                outputs.append(dict(stage=snap['label'], world_rc=world, phase=memory[G+2587], npc_count=npc_count,
                    pickup_count=pickup_count, units424_hex=units, pickups56_hex=pickups,
                    world124_hex=snap['world_rc124_hex'], counter2408=u(memory,G+2408),
                    rng_words=list(struct.unpack_from('<4I',memory,G+1720))))
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('entry-world0135-independent-review-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    for name in ('review_entry_world135_probe.py','review_gameplay_phase135.py','review_headless135.py'):
        (out/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    review = dict(status='passed_scoped_original_world_entry_observation_review', receipt=str(receipt.relative_to(ROOT)),
        receipt_sha256=sha(receipt), reviewer_sha256=sha(Path(__file__)), author_sources_unchanged=True,
        original_executed_by_reviewer=False, browser_executed_by_reviewer=False, only_wasm_export_section_changed=True,
        official_glue_prefix_unchanged=True, exact_original_exports_added=list(ROLES),
        native_storage_read_empty=True, storage_writes_observed=0, import_calls=3396, import_kinds=16,
        resource_imports_allowed=len(ALLOWED), resource_imports_denied=878-len(ALLOWED),
        data_gets=len(data_gets), unique_mpq_files=len(assets), mpq_decoded_bytes=inventory['decoded_bytes'],
        independently_reread_all_mpq_files=True, original_asset_precedence_inferred=False,
        all_resource_responses200=True, asset_extensions=dict(Counter(Path(x['path']).suffix for x in assets.values())),
        full_memory_captures=[dict(x,sha256_rechecked=True) for x in rt['captures']], world_and_entry_outputs=outputs,
        same_original_world_preserved=True, no_flat_world_injected=True, actual_phase0_then1=True,
        memory_cap_bytes=config['memory_cap_bytes'], peak_memory_bytes=result['max_memory_bytes'], owned_processes_absent=True,
        new_independent_gameplay_cases=0, selected_profile_and_entropy_remain_research_inputs=True,
        limitations=['Original observation and provenance, not an independent world/entry model or full-game acceptance.',
            'Explicit empty selected-profile and App inputs; menu assembly and all profile behavior are not recovered.',
            'MPQ bytes verified against historical StormLib reference; latest135 complete-asset equivalence remains unproved.',
            'No renderer, normal main-loop continuation, all-skill behavior, saves or multiplayer acceptance.',
            'No implicit WASM start and explicit entry allowlist checked; no claim to an exhaustive dynamic indirect-call trace.'])
    (out/'review.json').write_text(json.dumps(review,indent=2)+'\n')
    assert d['source_after'] == {n:sha(ROOT/n) for n in d['source_after']}
    print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),data_gets=len(data_gets),mpq_files=len(assets),outputs=[(x['phase'],x['npc_count'],x['pickup_count']) for x in outputs],new_independent_gameplay_cases=0)))


if __name__ == '__main__': main()
