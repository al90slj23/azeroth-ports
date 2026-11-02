#!/usr/bin/env python3
"""Different-author static/input-only reference for complete13938553 receipts."""
from pathlib import Path
from collections import Counter
import hashlib,json,sqlite3,struct,sys
sys.dont_write_bytecode=True
from review_combat139 import parse_module,local_closure

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/frame-deadline139-20261102T132356.853100Z'
SOURCE=ROOT/'originals/official-release-20261102T011227.335145Z/latest-wenilla_bg.wasm'
PROFILE=ROOT/'evidence/wasm0139-profile-20261102T012426.951871Z'
SHA='71a44d44a91245aa0a4db4171b5893e4343ba84c3699f7fa87dafc2856973299'
HAND='26229438e06e9676259d2df06b7fbd43f3778287845d97e4f72e3ada066be001'
COMP='c4495b084ac7b1d43ea26a781f63c06e0a6174f71475f4fe670dce6d64da45d8'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def packed(raw):
    assert len(raw)==8
    return bytes([sum(bool(v)<<i for i,v in enumerate(raw))])+bytes(v for v in raw if v)


def packet(row):
    #Current38553:10490(source,spell,emptytargets,pointVariant1,mask0).
    data=packed(row[:8])*2+row[12:16]+b'\0\1\0\0\x40\0'+row[16:28]
    return dict(opcode=306,capacity=32 if len(data)<=32 else 64,payload_hex=data.hex())


def finite_or_ieee(word):return struct.unpack('<f',word)[0]
def word(raw,o):return int.from_bytes(raw[o:o+4],'little')
def put(raw,o,n):raw[o:o+4]=int(n).to_bytes(4,'little')


def main():
    out=Path(sys.argv[1]).resolve();out.mkdir()
    assert sha(BATCH/'task-handoff.json')==HAND and sha(BATCH/'comparison.json')==COMP and sha(SOURCE)==SHA
    assert sha(ROOT/'scripts/review_combat139.py')=='158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9'
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');manifest=load(BATCH/'manifest.json')
    sources=comp['sources_before'];assert sources==comp['sources_after']==prep['sources']
    for n,h in sources.items():assert sha(ROOT/n)==sha(BATCH/'source-snapshot'/n)==h
    for n,h in hand['frozen_author_files'].items():assert sha(ROOT/n)==h
    for table in(comp['artifacts'],comp['frozen'],prep['frozen']):
        for n,h in table.items():assert sha(BATCH/n)==h
    assert local_closure(sources)==sorted(comp['source_import_edges'])==sorted(prep['source_import_edges'])
    assert prep['expected_before_original_execution']and not prep['original_input_contains_expected']and not prep['natural_queue_producer']
    assert load(BATCH/'expectation-read-audit.json')['forbidden']==[]
    config=load(BATCH/'config.json');assert config['input_sha256']==sha(BATCH/'inputs.json')and Path(config['input_file'])==BATCH/'inputs.json'
    original=SOURCE.read_bytes();modified=(BATCH/manifest['module_file']).read_bytes()
    a,b=parse_module(original),parse_module(modified)
    assert len(a['imports'])==len(b['imports'])==882 and a['imports']==b['imports']
    assert [{k:x[k]for k in('module','name','type_index')}for x in a['imports']]==manifest['original_imports']
    assert len(a['sections'])==len(b['sections'])
    for x,y in zip(a['sections'],b['sections'],strict=True):
        assert x['kind']==y['kind']
        if x['kind']!=7:assert original[x['start']:x['end']]==modified[y['start']:y['end']]
    assert b['exports']==a['exports']+[tuple(v)for v in manifest['added_exports']]
    assert manifest['only_export_section_changed']and manifest['original_executions']==0
    db=sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True);db.execute('pragma query_only=on')
    proof={};texts={}
    for index in sorted(set(map(int,manifest['functions']))|{46462}):
        lo,hi=a['bodies'][index];body=original[lo:hi];signature=a['types'][a['decl'][index-882]]
        wlo,whi=db.execute('select wat_start,wat_end from functions where idx=?',(index,)).fetchone()
        with(PROFILE/'official-0.139.0-full.wat').open('rb')as stream:stream.seek(wlo);wat=stream.read(whi-wlo)
        texts[index]=wat.decode();proof[index]=dict(body_sha256=hashlib.sha256(body).hexdigest(),signature=signature,WAT_sha256=hashlib.sha256(wat).hexdigest())
        if str(index)in manifest['functions']:
            q=manifest['functions'][str(index)]
            assert(lo,hi,len(body),proof[index]['body_sha256'],tuple(q['signature']))==(q['body_start'],q['body_end'],q['body_bytes'],q['body_sha256'],signature)
            assert proof[index]['WAT_sha256']==q['WAT_sha256']==sha(BATCH/'static'/f'{index}.wat')
    db.close()
    assert 'f32.le'in texts[38553]and 'offset=2587'not in texts[38553]and 'memory.copy'in texts[38553]
    assert 'i32.const 1\n            i32.store offset=16'in texts[38553]and 'i32.const 0\n            i32.store offset=36'in texts[38553]
    assert 'i32.const 64'in texts[10490]and'call 46462'in texts[10490]and'call 15962'in texts[10490]
    assert 'i32.const 32'in texts[10490]and'i32.const 306'in texts[10490]
    assert 'i32.const 4'in texts[66546]and('call 55846'in texts[46462]or'call 68886'in texts[46462])
    save(out/'current-source-proof.json',dict(functions=proof,point46462_current_WAT=texts[46462],module_nonexport_sections_identical=True,original_execution=False))
    cases=load(BATCH/'inputs.json');actual=[json.loads(s)for s in(BATCH/'actual.jsonl').read_text().splitlines()]
    assert len(cases)==len(actual)==58
    counts=Counter();reference=[]
    for c,got in zip(cases,actual,strict=True):
        assert c['id']==got['id'];rows=[bytes.fromhex(h)for h in c['storage32_hex']];count=c['count'];cap=len(rows)
        before=got['before'];assert before['count']==count and before['capacity']==cap and before['storage']==c['storage32_hex']and before['packets']==[]and before['packet_count']==before['packet_capacity']==0
        assert all(len(r)==32 for r in rows)and 0<=count<=cap
        profile=bytearray(376);actual_profile=bytes.fromhex(got['profile_before_hex']);assert len(actual_profile)==376
        put(profile,156,4);put(profile,168,word(actual_profile,168));put(profile,172,6);profile[184:192]=(1).to_bytes(8,'little');profile[344]=profile[345]=1
        assert actual_profile==bytes(profile)==bytes.fromhex(got['profile_after_hex'])
        query=bytearray([0x5a]*128);put(query,32,0xffffffff);put(query,56,0xffffffff);put(query,116,0);query[120]=1
        assert got['query_before_hex']==got['query_after_hex']==query.hex()and got['stack_after']==1048576
        assert len(got['stages'])==len(c['updates']);packets=[];pcap=0;previous=bytes.fromhex(before['raw_game2592_hex']);answers=[]
        assert previous[2587]==c['phase']and word(previous,1832)==cap and word(previous,1840)==count
        for now,z in zip(c['updates'],got['stages'],strict=True):
            inherited=bytearray(previous);put(inherited,2352,now);assert inherited.hex()==z['input_game2592_hex']and z['now_bits']==now
            i=0;removed=0
            while i<count:
                deadline=finite_or_ieee(rows[i][8:12]);clock=finite_or_ieee(now.to_bytes(4,'little'))
                if not deadline<=clock:
                    if deadline!=deadline or clock!=clock:counts['NaN_nonexpiry_rows']+=1
                    i+=1;continue
                if rows[i][8:12]==now.to_bytes(4,'little'):counts['exact_inclusive_expiry_rows']+=1
                row=rows[i];rows[i:count-1]=rows[i+1:count];count-=1;removed+=1
                if len(packets)==pcap:pcap=max(4,2*pcap)
                message=packet(row);packets.append(message);counts['packets']+=1;counts['packet_bytes']+=len(bytes.fromhex(message['payload_hex']));counts['payload_capacity'+str(message['capacity'])]+=1
            assert z['count']==count and z['capacity']==cap and z['storage']==[r.hex()for r in rows]
            assert z['packet_capacity']==pcap and z['packet_count']==len(packets)and z['packets']==packets
            predicted=bytearray(inherited);put(predicted,1840,count);put(predicted,1880,pcap);put(predicted,1888,len(packets))
            if word(inherited,1880)!=pcap:
                pointer=z['packet_pointer'];assert pointer%4==0 and 0<pointer<=33554432-16*pcap
                put(predicted,1884,pointer);counts['allocator_pointer_observations_not_predictions']+=1
            else:assert word(predicted,1884)==z['packet_pointer']
            assert predicted.hex()==z['raw_game2592_hex']
            counts['full38553']+=1;counts['removed']+=removed;counts['queue_bytes']+=32*cap;counts['Game_bytes']+=2592
            answers.append(dict(count=count,capacity=cap,storage=[r.hex()for r in rows],packet_capacity=pcap,packet_count=len(packets),packets=list(packets)))
            previous=bytes.fromhex(z['raw_game2592_hex'])
        reference.append(dict(id=c['id'],stages=answers))
    runtime=load(BATCH/'runtime.json');terminal=load(BATCH/'owned-terminal.json')
    assert counts['full38553']==124 and counts['packets']==counts['removed']==187 and counts['packet_bytes']==5582 and counts['queue_bytes']==15456
    assert runtime['fresh_instances']==runtime['setup1600_calls']==58 and runtime['full38553_calls']==124 and runtime['actual_host_calls']==0 and runtime['denied_imports']==882
    assert all(v['returned']and v['before']==v['after']==1048576 for v in runtime['returns'])
    assert sum(v['role']=='38553'for v in runtime['returns'])==124 and sum(v['role']=='1600'for v in runtime['returns'])==58
    assert runtime['error']is None and runtime['snapshot_restores']==0 and not runtime['App_bootstrap']and runtime['full_mainloop_frames']==runtime['complete_games']==0
    assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']
    assert sources=={n:sha(ROOT/n)for n in sources}and hand['frozen_author_files']=={n:sha(ROOT/n)for n in hand['frozen_author_files']}
    save(out/'independent-reference.json',reference)
    result=dict(status='accepted_bounded_current139_fixture_consumer',counts=dict(counts),source_files=len(sources),source_edges=len(comp['source_import_edges']),author_files_unchanged=hand['frozen_author_files'],functions=proof,
        author_process=terminal,author_original_executions_by_reviewer=0,author_production_checker_builder_executions=0,
        expected_file_used_as_reference=False,helper_execution='Frozen independent review_combat139 parser/ASTclosure only',
        limitations=['Scheduled32 queue is controlled fixture, naturalproducer0. Actual1600 emptyprofile/world-query fixture is not App/resourcebootstrap.',
        'Allocatorpointer is observation only, not independentlypredicted. All otherGame2592 bytes andwhole32B capacity/staleTail compare exactly.',
        'Phaseignored by currentconsumer; inclusiveIEEE comparisons/NaN nonexpiry andpackedGUID/XYZ bitpayload verified. No mainloop/nativeWindows/completegame acceptance.',
        'Pilot11 excluded; 124 formal currentconsumer entries and58 setups classified separately.'])
    save(out/'review.json',result);print(json.dumps(dict(status=result['status'],counts=dict(counts))),flush=True)


if __name__=='__main__':main()
