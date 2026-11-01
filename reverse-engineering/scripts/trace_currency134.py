#!/usr/bin/env python3
"""Freeze kind1 2862 -> 28795 statically; no original target is executed."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import struct
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
READER = ROOT / 'scripts/extract_catalogue134.py'
READER_SHA = '4e465095731c6abc9775ce8445fdd6b96c11982300ec33be1c1b4bda0b8b709a'
MANIFEST_SHA = '952e2cd4c1fdb0bbf62cf44d6cf4f265ae15120a1572facaad23b43ff4fc51b9'
PRIOR = ROOT / 'evidence/full0134-oracle-20261101T020143.890376Z'
PRIOR_FILES = {
    'ordinary-pipeline134-cases.json': '201f3c66130c1560c17f403e44fcc1c63667d22e8d690e04db4f77dd58ba7243',
    'ordinary-pipeline134-original-results.jsonl': '538d6472910c37cab98081c407819d238ba0c4be62e006961fd5c1325b326731',
    'ordinary-pipeline134-comparison.json': '5a0b99e7e4b772125ae6480f0827847b604404bb20474f36cbd4a58e38df016b'}


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


if sha(READER) != READER_SHA:
    raise ValueError('Pinned static reader differs')
from extract_catalogue134 import (SOURCE, SOURCE_SHA, PROFILE, WAT, WAT_SHA, DB, DB_SHA,
                                  parse_binary, require, digest, save, strict_json)


def model_checks():
    """Hand-derived arithmetic/lifecycle contracts; not original differential."""
    sys.path.insert(0, str(ROOT / 'reconstruction'))
    from core_spec import binary32 as f
    from core_spec.currency134 import CurrencyState, apply_currency, currency_award, mode_multiplier_bits
    count = 0
    for amount, scale, expected in ((0,1,0),(1,1,1),(4,1,4),(15,1,15),
                                   (1,.5,1),(3,.5,2),(5,.5,3),(4,1.2,5),
                                   (4,-1,0),(4,0,0),(0xffffffff,1,0xffffffff)):
        assert currency_award(amount, f.from_float(scale))['amount'] == expected
        count += 1
    for scale, expected in ((f.NAN,0),(f.INF,0xffffffff),(f.SIGN|f.INF,0),
                             (1,0),(0x7f7fffff,0xffffffff)):
        assert currency_award(4, scale)['amount'] == expected
        count += 1
    assert currency_award(0, f.INF)['amount'] == 0
    assert mode_multiplier_bits(0, 0) == mode_multiplier_bits(2, 0) == 0x3f800000
    assert mode_multiplier_bits(1, 1, region_index=0) == 0x3f800000
    assert mode_multiplier_bits(1, 1, region_index=3) == 0x3f800000
    assert mode_multiplier_bits(1, 0, region_index=0) != mode_multiplier_bits(1, 1, region_index=0)
    for mode in (0, 2, 255):
        assert currency_award(4, f.from_float(1), mode, 0)['amount'] == 4
        count += 1
    original = CurrencyState(gold=0xfffffffe, earned=0xfffffffd, player_fields=((1,8),(1176,9)))
    result = apply_currency(original, 4)
    assert (result.state.gold, result.state.earned) == (2,1)
    assert result.key_update == (1176,20000) and not result.missing_key_insert
    assert result.state.player_fields == ((1,8),(1176,20000))
    assert result.state.queue == () and original.gold == 0xfffffffe
    count += 1
    original = CurrencyState(mode=2, local_peer=42)
    result = apply_currency(original, 0)
    assert result.state.queue == ((42,0),) and result.state.queue_capacity == 4
    assert result.key_update == (1176,0) and result.missing_key_insert and result.pending
    count += 1
    result = apply_currency(CurrencyState(gold=0xffffffff), 0)
    assert result.key_update == (1176,0xffffd8f0)
    count += 1
    original = CurrencyState(mode=1)
    result = apply_currency(original, 4)
    assert result.status == 'pending_domain' and result.state is original
    count += 1
    return {'kind':'purePython hand-derived contracts', 'cases':count,
            'original_WASM_cases':0, 'original_target_executed':False,
            'limits':'No original28795/2862 differential was run by this extractor'}


def main():
    started = time.monotonic()
    pins = {SOURCE:SOURCE_SHA, WAT:WAT_SHA, DB:DB_SHA, READER:READER_SHA,
            PROFILE/'manifest.json':MANIFEST_SHA,
            **{PRIOR/name:hash_ for name,hash_ in PRIOR_FILES.items()}}
    require(all(sha(path)==hash_ for path,hash_ in pins.items()), 'Pinned input identity differs')
    identity = strict_json((PROFILE/'manifest.json').read_text())
    require(identity['target_version']=='0.134.0' and identity['embedded_build']=='983346a7',
            'Wrong original version/build')
    binary = SOURCE.read_bytes()
    profile = parse_binary(binary)
    require(digest(binary)==SOURCE_SHA and profile['function_imports']==878,
            'Original parse identity differs')
    out = ROOT/'evidence'/datetime.now(timezone.utc).strftime('currency0134-chain-%Y%m%dT%H%M%S.%fZ')
    out.mkdir(parents=True, exist_ok=False)
    c = sqlite3.connect(DB.resolve().as_uri()+'?mode=ro', uri=True)
    functions, lines, edges, guards = {}, {}, [], []
    closure, frontier = set(), [28795]
    try:
        meta = {k:strict_json(v) for k,v in c.execute('SELECT key,value FROM meta')}
        require(meta['original_sha256']==SOURCE_SHA and meta['wat_sha256']==WAT_SHA,
                'Index metadata identity differs')
        while frontier:
            i = frontier.pop()
            if i in closure:
                continue
            closure.add(i)
            frontier += [x[0] for x in c.execute('SELECT DISTINCT callee FROM calls WHERE caller=?',(i,))
                         if x[0] not in closure]
        require(len(closure)==25 and min(closure)>=878, '28795 direct callee closure differs')
        roles = {28795:'currency numeric award, mode queue and player-key update',
                 2862:'actual collection guard and dispatch',31731:'ordered removal and despawn messages',
                 65326:'8B queue reserve',3735:'u16 to u32 keyed-tree insertion',
                 38322:'region string to index',85718:'binary32 round helper',
                 20660:'available gold spend example',20570:'available gold spend example',
                 65323:'16B message vector reserve'}
        with WAT.open('rb') as stream:
            for i in sorted(closure|set(roles)):
                r = c.execute('SELECT * FROM functions WHERE idx=?',(i,)).fetchone()
                require(r is not None and (r[4],r[5])==profile['bodies'][i], 'Function body range differs')
                stream.seek(r[1]); raw = stream.read(r[2]-r[1]); body = binary[r[4]:r[5]]
                require(re.findall(rb'^  \(func \(;(\d+);\)',raw,re.M)==[str(i).encode()],
                        'Incomplete function extraction')
                (out/f'function-{i}.wat').write_bytes(raw)
                (out/f'function-{i}.body.bin').write_bytes(body)
                lines[i] = [x.strip() for x in raw.decode().splitlines()]
                functions[i] = {'index':i,'role':roles.get(i,'28795 complete direct callee closure'),
                    'signature_wat':raw.splitlines()[0].decode(),'wat_start':r[1],'wat_end':r[2],
                    'wat_line':r[3],'wat_bytes':len(raw),'wat_sha256':digest(raw),
                    'body_start':r[4],'body_end':r[5],'body_bytes':len(body),'body_sha256':digest(body),
                    'in28795_direct_closure':i in closure}
                for callee, offset, lineno, instruction in c.execute(
                    'SELECT callee,wat_offset,wat_line,instruction FROM calls WHERE caller=? ORDER BY wat_line',(i,)):
                    edges.append({'caller':i,'callee':callee,'wat_offset':offset,'wat_line':lineno,'instruction':instruction})
        def g(i, label, sequence):
            seq = sequence.split('|')
            at = [n for n in range(len(lines[i])-len(seq)+1) if lines[i][n:n+len(seq)]==seq]
            require(at, 'Reviewed guard differs: '+label)
            guards.append({'function_index':i,'label':label,'function_lines':[n+1 for n in at],
                           'full_wat_lines':[functions[i]['wat_line']+n for n in at],'instructions':seq})
        g(28795,'mode0 skips currency queue','local.get 0|i32.load8_u offset=2574|i32.eqz|br_if 0 (;@1;)')
        g(28795,'queue stores peer and unmodified base','local.get 0|i32.load offset=2152|local.get 2|i32.const 3|i32.shl|i32.add|local.tee 5|local.get 1|i32.store offset=4|local.get 5|local.get 3|i32.store')
        g(28795,'only exact mode1 has member divisor','local.get 0|i32.load8_u offset=2574|i32.const 1|i32.ne|br_if 0 (;@1;)')
        g(28795,'member count wrap before f32','local.get 0|i32.load offset=2532|i32.const 1|i32.sub|f32.convert_i32_u|f32.mul|f32.const 0x1.3f7ceep-2 (;=0.312;)|f32.mul')
        g(28795,'no minimum1 or NaN1 after round','local.get 0|local.get 11|local.get 0|f32.load offset=1408|local.get 1|f32.convert_i32_u|f32.mul|f32.mul|call 85718|i32.trunc_sat_f32_u|local.tee 1')
        g(28795,'gold1544 wrap addition','local.get 0|i32.load offset=1544|i32.add|local.tee 2|i32.store offset=1544')
        g(28795,'local collected tally1100 wrap addition','local.get 0|local.get 1|local.get 0|i32.load offset=1100|i32.add|i32.store offset=1100')
        g(28795,'keyed copper value wraps','local.get 2|i32.const 10000|i32.mul|local.set 8')
        g(28795,'missing key1176 calls3735','local.get 4|i32.const 1176|i32.store offset=28')
        g(28795,'tree root address for insertion','local.get 4|local.get 0|i32.const 2468|i32.add|i32.store offset=12|local.get 4|i32.const 12|i32.add|local.get 8|call 3735')
        g(2862,'K1 real radius can collect even marker0','f32.sqrt|local.get 25|f32.le|br_if 0 (;@4;)|local.get 1|i32.load|i32.const 1|i32.ne|br_if 1 (;@3;)')
        g(2862,'save amount then remove before dispatch','local.get 4|i32.load offset=12|local.set 4|local.get 0|local.get 1|call 31731|local.get 3|i32.const 1|i32.sub|br_table 3 (;@15;) 1 (;@17;) 4 (;@14;) 4 (;@14;) 4 (;@14;) 5 (;@13;) 2 (;@16;)')
        g(2862,'kind1 dispatcher28795','local.get 0|local.get 4|call 28795|br 10 (;@4;)')
        g(31731,'preserve order shift56','local.get 2|local.get 2|i32.const 56|i32.add|local.get 6|memory.copy')
        g(31731,'despawn opcode170 and8B GUID','local.tee 1|i32.const 170|i32.store16 offset=12|local.get 1|i32.const 8|i32.store offset=8')
        g(20660,'available gold is checked then spent','local.get 0|i32.load offset=1544|local.tee 10|local.get 0|i32.load offset=2444|local.tee 8|i32.ge_u|if  ;; label = @4|local.get 0|local.get 10|local.get 8|i32.sub|local.tee 3|i32.store offset=1544')
    finally:
        c.close()
    windows = []
    for i,lo,hi,label in ((2862,785,910,'collection gates'),(2862,1015,1170,'reverse remove and kind dispatch'),
                          (28795,1,len(lines[28795]),'entire currency consumer'),
                          (31731,1,len(lines[31731]),'entire ordered removal and messages'),
                          (20660,8,51,'gold spending proves local balance')):
        raw = ('\n'.join(lines[i][lo-1:hi])+'\n').encode()
        name=f'guard-{i}-{lo}-{hi}.wat.txt';(out/name).write_bytes(raw)
        windows.append({'function_index':i,'label':label,'function_lines':[lo,hi],
                        'full_wat_lines':[functions[i]['wat_line']+lo-1,functions[i]['wat_line']+hi-1],
                        'path':name,'bytes':len(raw),'sha256':digest(raw)})
    # This is an already recorded original914 output, not a newly run oracle.
    original_rows = (PRIOR/'ordinary-pipeline134-original-results.jsonl').read_text().splitlines()
    case = strict_json((PRIOR/'ordinary-pipeline134-cases.json').read_text())[0]
    observed = strict_json(original_rows[0])
    require(case['id']==observed['id']==0, 'Prior case identity differs')
    words = observed['after_death']['records_words'][0]
    require(words[0]==0 and words[2]==1 and words[3]==4 and words[9]==9004,
            'Prior actual kind1 record differs')
    record = struct.pack('<14I', *words)
    (out/'prior-original-case0-kind1-record.bin').write_bytes(record)
    provenance = {'path':str(PRIOR.relative_to(ROOT)), 'artifacts':PRIOR_FILES,
        'case_id':0,'group':case['group'],'stage':'after_death','record_index':0,
        'original_chain':[914,1417,1820], 'rng_input':case['rng'],
        'definition_hex':case['definition_hex'], 'source': 'prior recorded original result, read only',
        'record_words':words,'record_hex':record.hex(),'record_sha256':digest(record),
        'arrival_word_policy':'raw observed uninitialized append+4 word retained; radius guard ignores it',
        'not_new_runtime_evidence':True}
    fixture = {'status':'recipe_only_not_executed', 'entry_function':2862,'allocate_G_bytes':8192,
        'record_source':provenance,'record_stride':56,
        'G_initial_u32':{'1384':0x41100000,'1388':0x3f800000,'1408':0x3f800000,
            '1504':case['position'][0],'1508':case['position'][1],'1512':case['position'][2],
            '1520':120,'1524':0,'1544':0,'1100':0,'1860':1,'1868':1,'1872':4,'1880':0,
            '2108':0,'2148':0,'2156':0,'2344':case['now_bits'],'2468':0,'2472':0,
            '2520':0,'2532':1},'G_initial_u8':{'2574':0,'2579':1},
        'G_pointer_fields':{'1864':'one allocated record copied byte-for-byte',
            '1876':'allocated message vector with1872 capacity>=4',
            '2152':'empty currency queue dangling/aligned4; mode0 does not read'},
        'containers':'Zero-initialize fresh G; explicitly set all cap/pointer/count triples valid. No claims, aux records, items, modifiers or owned callbacks.',
        'expected_projection':{'pickup_count':0,'G1544':4,'G1100':4,'player_key1176':40000,
            'currency_queue_count':0,'rng_unchanged':True,
            'message':'31731 opcode170,8B GUID payload; later player-field flush outside entry'},
        'required_synthetic_boundaries':['radius0 retains the same marker0 record',
            'radius9 collects marker0 with raw stale arrival',
            'radius0 marker1 at arrival<=now collects; future or NaN arrival does not',
            'radius0 marker2 is outside supported normal-marker domain',
            'mode0/1/2/255, member0/1/2, region<3 and>=3, scale0/1/1.2/NaN/±Inf',
            'amount0/1/maxu32, gold/earned wrapping, key1176 multiplication wrapping',
            'empty and nonempty currency queue, missing/existing key1176, ordered mixed XP/K1 dispatch'],
        'do_not_claim':'This extractor runs no target, so no28795/2862 collection differential is established'}
    save(out/'controlled-collection-fixture.json',fixture)
    checks=model_checks()
    indirect_sites = []
    for i in sorted(closure):
        for n, line in enumerate(lines[i]):
            if 'call_indirect' in line:
                indirect_sites.append({'function_index':i,'function_line':n+1,
                    'full_wat_line':functions[i]['wat_line']+n,'instruction':line,
                    'continuous_context':lines[i][max(0,n-8):min(len(lines[i]),n+5)],
                    'status':'unresolved dynamic error/panic callback; never treated as no-op'})
    require(len(indirect_sites)==4 and {x['function_index'] for x in indirect_sites}=={172316,49501},
            'Error/panic indirect boundary differs')
    direct_offsets=sorted(set(int(x) for x in re.findall(r'offset=(\d+)', '\n'.join(lines[28795]))))
    result={'date':'2026-11-01','version':'0.134.0','build':'983346a7',
        'status':'static_currency_consumer_recovered_independent_projection_no_new_original_execution',
        'original_wasm_sha256':SOURCE_SHA,'profile_manifest_sha256':MANIFEST_SHA,
        'full_wat_sha256':WAT_SHA,'sqlite_sha256':DB_SHA,
        'run_directory':str(out.relative_to(ROOT)),'target_executed':False,'new_original_runtime_cases':0,
        'functions':list(functions.values()),'complete28795_direct_closure':sorted(closure),
        'closure_function_count':len(closure),'closure_imports':[],
        'closure_call_indirect_instructions':len(indirect_sites),'indirect_call_sites':indirect_sites,
        'direct_edges':edges,'continuous_guards':guards,'windows':windows,
        'G28795_direct_memory_offsets':direct_offsets,
        'layout':{'currency_multiplier_f32':1408,'available_run_gold_u32':1544,
            'local_collected_tally_u32':1100,'mode_u8':2574,'local_peer_u32':2520,
            'member_count_u32':2532,'region_id_ptr_len':[184,188],
            'currency_queue_capacity_pointer_count':[2148,2152,2156],'queue_stride':8,
            'player_key_tree_root_depth':[2468,2472],'currency_player_key_u16':1176},
        'semantics':{'gate':'distance<=radius OR(marker==1 AND arrival<=entryNow); no phase entry guard',
            'order':'2862 captures kind/amount,31731 ordered delete/despawn,then28795; eligible indices consumed descending',
            'mode0':'multiplier1,no currency queue append',
            'mode_nonzero':'append(peer=G2520,unmodified base amount) to8B G2148/2152/2156 queue',
            'mode1':'1/(1+f32(f32((regionIndex<3?.7:1)*f32.u32(wrap(G2532-1)))*f32(.312)))',
            'mode_other_nonzero':'queue still appended,mode multiplier remains1',
            'award':'trunc_sat_u32(round85718(f32(modeMultiplier*f32(G1408*f32.u32(baseAmount)))))',
            'no_XP_minimum':'zero legal; NaN/negative→0; +overflow→0xffffffff',
            'writes':['G1544=wrap(G1544+award)','G1100=wrap(G1100+award)',
                      'logical player-key1176=wrap(G1544*10000),existing overwrite or3735 insert'],
            'caps':'No explicit gold maximum clamp in complete28795; trunc_sat applies award only; additions and*10000 wrap',
            'messages':'31731 queues opcode170 with8B pickup GUID,then each aux GUID;28795 has no message constructor/flush call',
            'RNG':'28795 arithmetic/queue/key normal path has no RNG; spawning1820 RNG belongs to earlier creation. Direct closure has no imports but four unresolved indirect error/panic callbacks remain pending; do not infer complete error-path behavior',
            'account':'No account write or persistence call in28795;G1100→persistent account stat transfer remains unknown'},
        'controlled_fixture':fixture,'model_checks':checks,
        'unknown':['G1100 to persistent account gold statistics transfer and its exact new-version guard',
            'Later keyed player-state serialization/flush and network queue consumer acceptance',
            'Full logical-to-physical keyed B-tree and allocation identity; retained original callee evidence is complete',
            'Four dynamic error/panic callbacks in172316/49501: original table/callees must be preserved; no no-op substitution',
            'Mixed XP/K1 full2862 scheduling and later unknown foreign-kind callbacks stay pending',
            'No account persistence, browser bridge, disk save or recipient delivery demonstrated'],
        'independent_reconstruction_complete':False,
        'source_sha256':{'scripts/trace_currency134.py':sha(Path(__file__)),
            'reconstruction/core_spec/currency134.py':sha(ROOT/'reconstruction/core_spec/currency134.py'),
            'reconstruction/core_spec/binary32.py':sha(ROOT/'reconstruction/core_spec/binary32.py'),
            'reconstruction/core_spec/progression134.py':sha(ROOT/'reconstruction/core_spec/progression134.py')},
        'pinned_inputs_stable_after':all(sha(path)==hash_ for path,hash_ in pins.items()),
        'elapsed_seconds':round(time.monotonic()-started,3)}
    require(result['pinned_inputs_stable_after'],'Input changed during extraction')
    save(out/'manifest.json',result)
    result['evidence_manifest_sha256']=sha(out/'manifest.json')
    save(ROOT/'reports/2026-11-01-currency0134-chain.json',result)
    print(json.dumps({'evidence':str(out),'manifest_sha256':result['evidence_manifest_sha256'],
                      'retained_functions':len(functions),'currency_closure_functions':len(closure),
                      'guards':len(guards),'model_checks':checks,'target_executed':False}))


if __name__=='__main__':
    main()
