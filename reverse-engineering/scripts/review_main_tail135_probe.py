#!/usr/bin/env python3
"""Read-only observational tail receipt consistency; no new model/original run."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import hashlib,json,struct
from review_headless135 import ROOT,ORIGINAL,ORIGINAL_SHA,sha,strict,sections,bodies,signatures,exports,ROLE_BINDINGS,compare,lossless
from review_gameplay_phase135 import core_closure
from extract_catalogue134 import parse_binary

BATCH=ROOT/'evidence/full0135-oracle-20261101T080624.993012Z'
BASE=ROOT/'evidence/full0135-oracle-20261101T072329.149731Z'
ORDER=('player','extra','owned_effects','hits','area','effects','deadline','secondary','ai','collect','claims','spawn','special','terminal')
IDLE=('extra','owned_effects','deadline','secondary','claims','special','terminal')

def w(raw,o):return struct.unpack_from('<I',raw,o)[0]

def main():
    path=BATCH/'main-tail135-probe-receipt.json';receipt=json.loads(path.read_text());frozen=receipt['source_sha256_before'];snap=BATCH/'source-snapshot'
    assert frozen==receipt['source_sha256_after']
    for n,h in frozen.items():assert sha(snap/n)==h
    for n,h in receipt['artifacts'].items():assert sha(BATCH/n)==h
    closure=core_closure(snap,('headless135.py',));assert set(closure)<=frozen.keys()
    assert sha(BASE/'headless135-comparison.json')==receipt['baseline_receipt_sha256']
    assert sha(BASE/'headless135-fixtures.jsonl')==sha(BATCH/'prior-independent-expected.jsonl')
    source=ORIGINAL.read_bytes();assert hashlib.sha256(source).hexdigest()==ORIGINAL_SHA
    sec=sections(source);code=bodies(source,sec);signature=signatures(source,sec);changed=(BATCH/'research135-exports.wasm').read_bytes();cs=sections(changed)
    assert[(k,v)for k,v,_,_ in sec if k!=7]==[(k,v)for k,v,_,_ in cs if k!=7]
    manifest=json.loads((BATCH/'manifest.json').read_text());assert len(manifest['roles'])==16 and manifest['denied_function_import_count']==878
    for role in manifest['roles']:
        i,p,r=ROLE_BINDINGS[role['role']];assert(i,p,r)==(role['index'],role['parameters_hex'],role['results_hex'])and signature(i)==(p,r)
        a,b=code[i-878];assert hashlib.sha256(source[a:b]).hexdigest()==role['body_sha256']
    old=exports(source,next(s for s in sec if s[0]==7));new=exports(changed,next(s for s in cs if s[0]==7));assert new[:len(old)]==old
    assert new[len(old):]==[(r['export'],0,r['index'])for r in manifest['roles']]
    profile=parse_binary(source);memory=bytearray(max(s['memory_start']+s['file_end']-s['file_start']for s in profile['segments']))
    for s in profile['segments']:memory[s['memory_start']:s['memory_start']+s['file_end']-s['file_start']]=source[s['file_start']:s['file_end']]
    del source,changed,sec,cs,profile,code
    totals=Counter();comparison=Counter();cases=[]
    with(BATCH/'main-tail135-probe-results.jsonl').open()as results,(BASE/'headless135-fixtures.jsonl').open()as old:
        for ident in range(8):
            observed=json.loads(next(results));prior=json.loads(next(old));assert observed['id']==prior['id']==ident
            lookup={};frame=offset=0
            for action in prior['actions']:
                if action['kind']=='frame':
                    frame+=1
                    for kind in('player','hits','area','effects','ai','collect','spawn'):
                        expected=prior['expected'][offset];assert expected['kind']==kind;lookup[frame,kind]=expected['projection'];offset+=1
                else:expected=prior['expected'][offset];assert expected['kind']=='select';lookup[frame,'select']=expected['projection'];offset+=1
            assert offset==len(prior['expected'])
            raw=bytearray.fromhex(observed['controlled_initial_raw_g2592_hex']);assert len(raw)==2592
            local=Counter();failures=[];per_frame={};new_types=Counter()
            for stage in observed['stages']:
                kind=stage['kind'];frame=stage['frame'];local['snapshots']+=1
                lossless(raw,stage['game_delta_words'],local,'raw_game')
                domains=stage['main_domains'];projection=stage['projection'];assert raw[2587]==projection['phase2587']and w(raw,2352)==projection['now_bits']
                execution11=any(memory[w(bytes.fromhex(r),0)+84]==11 for r in projection['owned_records_hex'])
                assert execution11==domains['owned_execution11'];local['owned_execution11_snapshot_observations']+=execution11
                for base in(644,1832,1856,2108,1916):assert w(raw,base)==w(raw,base+8)==0
                if kind!='select':per_frame.setdefault(frame,[]).append(kind)
                expected=lookup.get((frame,kind))
                if expected is not None:compare(expected,projection,f'case{ident}.frame{frame}.{kind}',comparison);local['legacy_model_stages_compared']+=1
                for name in('packets','notifications'):
                    for message in stage['new_messages'][name]:
                        data=bytes.fromhex(message['payload_hex']);assert len(data)==message['length'] if 'length'in message else True
                    local[name+'_'+kind]+=len(stage['new_messages'][name])
                if kind in IDLE:
                    assert not stage['game_delta_words']and not stage['new_messages']['packets']and not stage['new_messages']['notifications']
                    local['idle_tail_snapshot_observations']+=1
                if 'opcode'in stage['new_messages']:new_types.update(stage['new_messages']['opcode'])
            assert all(tuple(kinds)==ORDER for kinds in per_frame.values())
            assert raw.hex()==observed['final_raw_g2592_hex']and observed['failure']is None and not observed['denied_host_attempts']and not observed['skipped']
            for selected in observed['selections']:
                cards=selected['cards'];index=next((j for j,c in enumerate(cards)if c['variant']=='upgrade'),0)
                assert selected['index']==index and selected['chosen']==cards[index]
            prior_receipt_case=receipt['cases'][ident];assert prior_receipt_case['frames']==observed['frames']and prior_receipt_case['selections']==observed['selections']
            cases.append(dict(id=ident,frames=observed['frames'],snapshots=local['snapshots'],selections=len(observed['selections']),outcome=observed['outcome'],final_phase2587=raw[2587],**{k:v for k,v in local.items()if k!='snapshots'}));totals.update(local)
        assert not results.read().strip()and not old.read().strip()
    assert sum(c['frames']for c in cases)==3038 and totals['snapshots']==42550 and totals['legacy_model_stages_compared']==11309
    assert comparison.get('differences',0)==0 and receipt['prior_model_differences']==0
    assert receipt['runtime']['original_entry_calls']==42558 and receipt['runtime']['denied_host_attempts']==0
    assert receipt['runtime']['observational_probe_only']and not receipt['complete880_called']and not receipt['original_effect_or_resource_vectors_overwritten']
    for n,h in frozen.items():assert sha(snap/n)==h
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('main-tail0135-probe-independent-review-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    deps=(Path(__file__),ROOT/'scripts/review_headless135.py',ROOT/'scripts/review_gameplay_phase135.py',ROOT/'scripts/extract_catalogue134.py')
    for p in deps:q=out/'reviewer-source'/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(p.read_bytes())
    result=dict(version='0.135.1',build='0898d5e3',kind='observational receipt consistency only;not independent new gameplay',
        receipt=str(path.relative_to(ROOT)),receipt_sha256=sha(path),sources=len(frozen),core_package_init_closure=closure,
        cases=cases,totals=dict(totals),legacy_comparison=dict(comparison),original_module_nonexport_bytes_identical=True,role_bindings_verified=16,
        new_independent_model_frames=0,original_executed_by_reviewer=False,author_sources_modified=False,
        reviewer_source_sha256={str(p.relative_to(ROOT)):sha(p)for p in deps},
        limits=['42550rawGworddelta snapshots are internally reconstructible through final2592B state;this is observational byteconsistency,not an independent algorithm for those newframes.',
            'Only11309 legacy projections have preexisting independent expectations;3038observedframes do not replace1614 independently rebuiltframes.',
            'Execution11canbeobserved beyond modelstop while idle-tail writes remain0;this is not a restored975active logic specification.',
            'Packet/notification bodies and full backing semantics beyond prior independent boundary are observations only.',
            'Controlledphase1+128zero unit/area slots,omitted880front/party/transport/resourceentry remain boundaries.'])
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n')
    wrapper=dict(result,evidence_directory=str(out.relative_to(ROOT)),review_sha256=sha(out/'review.json'))
    (ROOT/'reports/2026-11-01-main-tail0135-probe-independent-review.json').write_text(json.dumps(wrapper,indent=2)+'\n')
    (ROOT/'reports/2026-11-01-main-tail0135-probe-independent-review.md').write_text('# 主尾段原件观察器独立一致性复核\n\n3038个观察帧/42550快照、18次选择的来源与记录一致性通过。67源快照、16原入口及非export字节通过；固定first-upgrade-else-first策略保留。完整G2592由逐word delta重建到终态；原有11309个legacy投影严格对照，无新增独立算法覆盖。\n\n两次phase_boundary和六个frame_budget均保留。975 execution11可出现在独立模型停点之后；即使新增tail阶段无写入，也不能据此宣布活跃逻辑已恢复。消息、额外原件帧及完整880仍是观察，不能追加独立1614帧验收数量。未重跑原件或修改作者源。\n\n证据：`'+str((out/'review.json').relative_to(ROOT))+'`。\n')
    print(json.dumps(dict(directory=str(out),sha256=sha(out/'review.json'),totals=dict(totals))))

if __name__=='__main__':main()
