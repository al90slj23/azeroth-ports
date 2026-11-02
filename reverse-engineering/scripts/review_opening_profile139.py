#!/usr/bin/env python3
"""Different-author read-only2945/18062 review; no production/target execution."""
from pathlib import Path
from collections import Counter
import hashlib, json, sqlite3, struct, sys
from review_combat139 import parse_module, local_closure, sha

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT/'evidence/opening-profile139-oracle-20261102T044006.251632Z'
SOURCE = ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE = ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
SOURCE_SHA = '71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
COMPARISON_SHA = 'd976cb2ab8d1c79389ce956d66f4313a6528c14cf21ccceb3cfb6481fd4388f9'
HANDOFF_SHA = '5029a5890ae57afb933d34b3a3ed66a0449d212f94f00660e4e22b44519e085a'
HELPER_SHA = '158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9'
load = lambda p: json.loads(p.read_text())


def reference(case):
    if case['kind'] == 'selection':
        account = bytes.fromhex(case['account_hex'])
        assert len(account) == 368 and all(struct.unpack_from('<I', account, o)[0] == 0 for o in (196,244,256,268))
        prior = bytes((case['poison'],))*40
        after = bytearray(prior)
        for start, stop in ((0,4), (8,12), (16,36)):
            after[start:stop] = bytes(stop-start)
        after[4] = after[12] = 255
        return dict(id=case['id'], kind='selection', prior40_hex=prior.hex(),
            output40_hex=after.hex(), account_unchanged=True,
            canaries=['c3'*16, 'd7'*16])
    assert case['kind'] == 'banner'
    title, subtitle = case['title'].encode('utf8'), case['subtitle'].encode('utf8')
    payload = (b'\x5a\x00\x00\x00\x00'+struct.pack('<I',len(title)+1)
        + title+b'\0'+bytes(8)+struct.pack('<I',len(subtitle)+1)+subtitle+b'\0\0')
    size, capacity = 9, 32
    for amount in (len(title), 1, 8, 4, len(subtitle), 1, 1):
        required = size+amount
        if required > capacity:
            capacity = max(2*capacity, required, 8)
        size = required
    assert size == len(payload)
    return dict(id=case['id'], kind='banner', capacity=capacity,
        length=size, opcode=150, payload_hex=payload.hex(),
        strings_unchanged=True, canaries=['c3'*16, 'd7'*16])


def main():
    out = Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(ROOT/'scripts/review_combat139.py') == HELPER_SHA
    assert sha(CASE/'comparison.json') == COMPARISON_SHA
    assert sha(CASE/'task-handoff.json') == HANDOFF_SHA
    assert sha(SOURCE) == SOURCE_SHA
    receipt, prepared, manifest, runtime = (load(CASE/n) for n in ('comparison.json','prepared.json','manifest.json','runtime.json'))
    handoff = load(CASE/'task-handoff.json')
    frozen_author = handoff['files']
    for name, digest in frozen_author.items():
        assert sha(ROOT/name) == digest, name
    assert receipt['source_sha256_before'] == receipt['source_sha256_after'] == prepared['sources']
    for name, digest in prepared['sources'].items():
        assert sha(ROOT/name) == sha(CASE/'source-snapshot'/name) == digest
    edges = local_closure(prepared['sources'])
    assert edges == sorted(prepared['source_import_edges']) == sorted(receipt['source_import_edges'])
    for name, digest in receipt['frozen_artifacts'].items():
        assert sha(CASE/name) == digest == prepared['artifacts'][name]
    for name, digest in receipt['artifacts'].items():
        assert sha(CASE/name) == digest
    assert prepared['expected_before_original'] and receipt['original_input_contains_expected'] is False
    original_bytes = SOURCE.read_bytes();original = parse_module(original_bytes)
    module_bytes = (CASE/manifest['module_file']).read_bytes();changed = parse_module(module_bytes)
    assert sha(CASE/manifest['module_file']) == manifest['module_sha256']
    assert len(original['imports']) == 882 and len(original['bodies']) == 177101
    assert len(original['sections']) == len(changed['sections'])
    for a,b in zip(original['sections'], changed['sections']):
        assert a['kind'] == b['kind']
        if a['kind'] != 7:
            assert original_bytes[a['start']:a['end']] == module_bytes[b['start']:b['end']]
    assert changed['exports'] == original['exports'] + [
        ('research139_companion2945',0,2945),('research139_start18062',0,18062),
        ('research139_opening_profile_stack0',3,0)]
    assert ('__wbindgen_malloc',0,93344) in original['exports']
    gs = next(x for x in original['sections'] if x['kind']==6)
    assert original_bytes[gs['payload']:gs['end']].hex() == '017f01418080c0000b'
    imports = [(x['module'],x['name']) for x in original['imports']]
    assert imports == [(x['module'],x['name']) for x in manifest['original_imports']]
    static = load(CASE/'static/trace.json');texts={};bindings={}
    db = sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
    with (PROFILE/'official-0.139.0-full.wat').open('rb') as stream:
        indices = set(map(int,static['functions']))|{25700,55846,68886}
        for index in sorted(indices):
            row = db.execute('select *from functions where idx=?',(index,)).fetchone()
            a,b=original['bodies'][index];assert (a,b)==(row['body_start'],row['body_end'])
            stream.seek(row['wat_start']);wat=stream.read(row['wat_end']-row['wat_start'])
            body_hash=hashlib.sha256(original_bytes[a:b]).hexdigest();wat_hash=hashlib.sha256(wat).hexdigest()
            if str(index) in static['functions']:
                claim=static['functions'][str(index)]
                assert body_hash==claim['body_sha256'] and wat_hash==claim['WAT_sha256']
                assert sha(CASE/f'static/{index}.wat')==wat_hash
            (out/f'{index}.wat').write_bytes(wat)
            texts[index]=wat.decode();bindings[str(index)]=dict(body_sha256=body_hash,WAT_sha256=wat_hash)
    assert original['types'][original['decl'][2945-882]]==('7f7f','')
    assert original['types'][original['decl'][18062-882]]==('7f7f7f7f7f','')
    assert 'i32.const 255\n            local.set 11' in texts[2945]
    assert 'i32.const 255\n              local.set 10' in texts[2945]
    for count in (196,244,256,268):assert f'i32.load offset={count}' in texts[2945]
    for offset in (0,4,8,12,16,20,24,28,32,33,34,35):
        store = 'store' if offset==0 else f'store offset={offset}'
        assert store in texts[2945] or f'store8 offset={offset}' in texts[2945]
    assert 'i32.const 0\n          i32.store offset=8' in texts[25700]
    for text in ('i32.const 90','i32.const 150','i64.const 0','memory.copy','call 55846','call 68886'):
        assert text in texts[18062]
    assert 'i32.const 1\n    i32.shl' in texts[55846] and 'i32.const 8' in texts[55846]
    assert 'i32.const 1\n    i32.shl' in texts[68886] and 'i32.const 8' in texts[68886]
    expected=load(CASE/'expected.json');cases=load(CASE/'inputs.json')
    actual=[json.loads(line) for line in (CASE/'actual.jsonl').read_text().splitlines()]
    assert len(cases)==len(expected)==len(actual)==89
    counts=Counter()
    for index,(case, want, got) in enumerate(zip(cases,expected,actual,strict=True)):
        assert case['id']==want['id']==got['id']==index
        independent=reference(case)
        if case['kind']=='banner':
            desc=bytes.fromhex(got['raw_descriptor16_hex']);assert len(desc)==16
            cap,pointer,length,opcode=struct.unpack_from('<IIIH',desc)
            assert (cap,length,opcode)==(got['capacity'],got['length'],150)
            assert 0<pointer<pointer+max(length,1)<=33554432
            counts['physical_pointer_observed_bytes']+=4
            counts['stack_unwritten_padding_observed_bytes']+=2
            got={key:value for key,value in got.items() if key!='raw_descriptor16_hex'}
            counts['complete18062']+=1;counts['payload_bytes']+=len(bytes.fromhex(got['payload_hex']))
        else:
            counts['complete2945']+=1;counts['full40_output_bytes']+=40
        assert independent==want==got,case['id']
    assert dict(counts)==dict(physical_pointer_observed_bytes=284,
        stack_unwritten_padding_observed_bytes=142,complete18062=71,
        payload_bytes=12329,complete2945=18,full40_output_bytes=720)
    assert runtime['full2945_calls']==18 and runtime['full18062_calls']==71
    assert runtime['fresh_instances']==3 and runtime['host_calls']==0
    assert runtime['denied_imports']==882 and runtime['allocator_calls']==249
    assert runtime['stack_guards']==338 and len(runtime['target_returns'])==89
    assert all(x['before']==x['after']==1048576 and x['returned'] for x in runtime['target_returns'])
    assert runtime['error'] is None and not runtime['original_snapshot_loaded']
    assert not runtime['App_produced'] and not runtime['user_saves_accessed']
    terminal=load(CASE/'owned-terminal.json');start=load(CASE/'owned-start.json')
    assert terminal['pid']==terminal['pgid']==start['pid']==start['pgid']
    assert terminal['exit_code']==0 and terminal['pid_missing'] and terminal['pgid_missing'] and terminal['seconds']<60
    assert receipt['differences']==0 and receipt['full1108_calls']==receipt['full6786_calls']==0
    assert 'i64.const 6364136223846793005' in texts[6786] and 'i64.const 1442695040888963407' in texts[6786]
    checks=load(CASE/'model-checks.json')
    for row in checks['seed_examples']:
        assert int(row['output']) == (int(row['input'])*6364136223846793005+1442695040888963407)&((1<<64)-1)
    for name, digest in frozen_author.items():assert sha(ROOT/name)==digest
    result=dict(status='pass_declared_empty_sources_and_resolved_UTF8_components',
        reviewer_source_sha256=sha(Path(__file__)),pure_parser_helper_sha256=HELPER_SHA,
        author_comparison_sha256=COMPARISON_SHA,author_handoff_sha256=HANDOFF_SHA,
        source_sha256=SOURCE_SHA,author_files=frozen_author,
        independent_cases=89,counts=dict(counts),source_files=len(prepared['sources']),
        local_edges=len(edges),current_WAT_body_bindings=bindings,
        only_export_section_changed=True,unmodified_callees_preserved=True,
        original_process=terminal,all_original_target_returns_restored=True,
        independent_reference_executions=89,reviewer_original_executions=0,
        reviewer_author_model_builder_checker_executions=0,author_files_modified=False,
        limitations=['Only four explicitly empty account source counts and resolved UTF8 strings;not a natural App/account/storage/localization producer.',
            'Thirty2945 bytes are known writes;6 internal padding and4 trailing caller bytes retain input poison.71 packet pointers and142 stack-padding bytes are observations.',
            'Full1108/6786 are static-bound only;LCG three examples are model selfchecks,not new target calls.',
            'Runner has89 detailed target stack returns and aggregate249 allocator guards;allocator states are not249 serialized guard records.',
            '18 complete statically bound opening functions are not behavioral acceptance;0 full opening/native/complete game.'])
    (out/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(out=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json'),cases=89,counts=dict(counts))))


if __name__ == '__main__':
    main()
