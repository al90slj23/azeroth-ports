#!/usr/bin/env python3
"""Read-only different-author1391 full913 numeric/whole432B review."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import hashlib,json,math,sqlite3,struct,sys,time
sys.dont_write_bytecode=True
AUDIT=Counter()
def audit(event,args):
    if event in('subprocess.Popen','os.system','os.exec','ctypes.dlopen')or event=='import'and str(args[0]).startswith('core_spec'):
        AUDIT['forbidden_author_or_original_execution']+=1;raise RuntimeError('Read-only review rejects '+event)
sys.addaudithook(audit)
import review_cast139 as C
from review_combat139 import parse_module,local_closure,sha,fp,bits

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/'evidence/combat01391-oracle-20261102T140049.784303Z'
PROFILE=ROOT/'evidence/wasm01391-profile-20261102T133454.115329Z'
HAND='711f00009f438b8f5195818e9c118ff988f94b0ec547bfb179909fc7d92e35b6'
COMP='f599a65f622fa1cbb9896db303c0411ad7bcfbd4222b8a36ed0633137b7aad3b'
WASM='8831b4a21314cefd0b9f56dcb5681ac822a9ee30770ab1acae473f9e8f2aec71'
load=lambda p:json.loads(Path(p).read_text())
save=lambda p,v:Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
u=lambda b,o=0:struct.unpack_from('<I',b,o)[0]
q=lambda b,o=0:struct.unpack_from('<Q',b,o)[0]


def round64(v):
    #All admitted total+account sums are finite nonnegative >=1. Exact
    #Fraction addition and52-bit RNE avoid copying the production hostfloat.
    assert v>0
    n,d=v.numerator,v.denominator;e=n.bit_length()-d.bit_length()
    if e>=0:
        if n<d<<e:e-=1
    elif n<<-e<d:e-=1
    assert -1022<=e<=1023
    shift=52-e;s=C.even_div(n<<shift,d)if shift>=0 else C.even_div(n,d<<-shift)
    if s==1<<53:s>>=1;e+=1
    assert e<=1023
    return((e+1023)<<52)|(s&((1<<52)-1))


def reference(case,counts):
    state=case['state'];rows=[bytearray.fromhex(x)for x in state['units432_hex']];total=int(state['accounted_total_bits']);answers=[];branches=[];now=C.rational(state['now_bits'])
    assert state['sources']==dict(items2028=[],spells2052=[],proc_schedule1972=[],other_procs_absent=True)
    assert len({q(r,112)for r in rows})==len(rows)and all(len(r)==432 for r in rows)
    for op in case['operations']:
        assert op['context']==0 and 0<=op['school']<256 and 0<=op['critical']<256
        target=int(op['target_id']);index=next((i for i,row in enumerate(rows)if q(row,112)==target),None);reason='phase_guard'if state['phase2587']!=1 else'missing_target'if index is None else None;phase=C.ONE;school=0;damage=None
        if reason is None:
            row=rows[index];assert u(row,244)==0xffffffff and u(row,40)!=3
            multiplier=C.ONE
            if now<C.rational(u(row,148)):multiplier=C.add(multiplier,u(row,144));counts['active_first_status']+=1
            if now<C.rational(u(row,156)):term=u(row,152);counts['active_second_status']+=1
            elif C.rational(u(row,164))>now:term=u(row,160);counts['fallback_third_status']+=1
            else:term=0
            multiplier=C.add(C.add(C.add(multiplier,term),u(row,368)),0)
            if op['school']&254==2 and C.rational(u(row,372))>now:school=0x3dcccccd;counts['school372_strictly_active']+=1
            if u(row,64)!=0xffffffff:
                if C.rational(u(row,420))>now:phase=0x3fc00000;counts['phase420_one_point_five']+=1
                elif C.rational(u(row,416))>now:phase=0x3e800000;counts['phase416_quarter']+=1
                elif any(u(other,0)==0 and u(other,40)==2 and q(other,32)==target for other in rows):phase=0x3e800000;counts['linked_kind2_quarter']+=1
            if u(row,0)==1:reason='marker1_guard'
            else:
                amount=op['amount_bits'];nan=amount&0x7fffffff>0x7f800000
                if nan:damage=C.ONE;counts['NaN_input_value_category_only']+=1
                else:
                    assert amount&0x7fffffff<0x7f800000
                    raw=C.mul(C.mul(amount,C.add(multiplier,school)),phase);damage=raw if C.rational(raw)>1 else C.ONE
                old=u(row,288);new=C.sub(old,damage);assert C.rational(new)>0,'Lethal branch must not be substituted'
                account=min(max(C.rational(old),Fraction(0)),C.rational(damage));old_float=struct.unpack('<d',struct.pack('<Q',total))[0];assert math.isfinite(old_float)and old_float>=0
                total=round64(Fraction.from_float(old_float)+account);struct.pack_into('<I',row,288,new);counts['nonlethal_applied']+=1
                counts['HP_fullbits_compared']+=1
        reason=reason or'nonlethal';counts[reason]+=1
        answers.append(dict(units432_hex=[r.hex()for r in rows],accounted_total_bits=str(total),rng_words=state['rng_words']))
        branches.append(dict(case=case['id'],reason=reason,target=op['target_id'],phase_bits=phase,school_bits=school,damage_bits=damage))
    return answers,branches


def main():
    started=time.monotonic();out=Path(sys.argv[1]).resolve();out.mkdir();assert sha(BATCH/'comparison.json')==COMP and sha(BATCH/'task-handoff.json')==HAND
    comp=load(BATCH/'comparison.json');hand=load(BATCH/'task-handoff.json');prep=load(BATCH/'prepared.json');m=load(BATCH/'manifest.json');runtime=load(BATCH/'runtime.json');contract=load(BATCH/'numeric-static-contract.json');role=load(BATCH/'role-binding.json')
    assert len(hand['frozen_author_files'])==5
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    sources=comp['source_before'];assert sources==comp['source_after']==prep['source_closure']and comp['source_unchanged']
    for name,h in sources.items():assert sha(ROOT/name)==sha(BATCH/'source-snapshot'/name)==h
    edges=local_closure(sources);assert edges==sorted(comp['source_import_edges'])
    for table in[comp['artifacts'],prep['artifacts']]:
        for name,h in table.items():assert sha(BATCH/name)==h
    assert sha(BATCH/'prepared.json')==hand['prepared_sha256']and comp['expected_before_original']and prep['expected_before_original']and comp['cases']==80 and comp['calls']==125 and comp['complete']and comp['mismatch_cases']==0
    helpers={'scripts/review_cast139.py':'bc0fc0e1a107a504893168d713b3ca73bce77e03a9aade0d9961c2761aa06c5b','scripts/review_combat139.py':'158d211c3ec36093e26536aaf402606fb558c059ee528134abe12294328932b9'}
    for name,h in helpers.items():assert sha(ROOT/name)==h
    native=Path(m['windows_reference']['path']);source=native.parent.parent/'latest-wenilla_bg.wasm';assert source.stat().st_size==92537579 and sha(source)==WASM==m['original_sha256']==contract['original_sha256']==prep['original_sha256']
    assert sha(PROFILE/'manifest.json')==m['profile_manifest_sha256']
    raw=source.read_bytes();original=parse_module(raw);changed=(BATCH/m['module_file']).read_bytes();modified=parse_module(changed)
    for a,b in zip(original['sections'],modified['sections'],strict=True):
        assert a['kind']==b['kind']
        if a['kind']!=7:assert raw[a['start']:a['end']]==changed[b['start']:b['end']]
    exports=[('research1391_damage913',0,913),('research1391_stack0',3,0)];assert modified['exports']==original['exports']+exports and len(original['imports'])==882
    assert original['decl'][913-882]==278 and original['types'][278]==('7f7e7d7f7f7f7f','')and('__wbindgen_malloc',0,93365)in original['exports']and original['decl'][93365-882]==6 and original['types'][6]==('7f7f','7f')
    assert[(r['module'],r['name'],r['type_index'])for r in original['imports']]==[(r['module'],r['name'],r['type_index'])for r in m['original_imports']]
    functions={};texts={}
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db,(PROFILE/'official-0.139.1-full.wat').open('rb')as s:
        for idx in[913,69552,93365]:
            a,z=original['bodies'][idx];lo,hi=db.execute('select wat_start,wat_end from functions where idx=?',(idx,)).fetchone();s.seek(lo);text=s.read(hi-lo);functions[str(idx)]=dict(body_sha256=hashlib.sha256(raw[a:z]).hexdigest(),WAT_sha256=hashlib.sha256(text).hexdigest());texts[idx]=text.decode();(out/f'{idx}.wat').write_bytes(text)
        calls=[dict(callee=r[0],wat_offset=r[1],wat_line=r[2],instruction=r[3])for r in db.execute('select callee,wat_offset,wat_line,instruction from calls where caller=913')]
    assert calls==m['direct_calls']and functions['913']['body_sha256']==m['entry']['body_sha256']==role['entry']['new']['body_sha256']and functions['913']['WAT_sha256']==m['entry']['wat_sha256']==role['entry']['new']['wat_sha256']==sha(BATCH/'913.wat')
    assert sha(BATCH/'numeric-static-contract.json')==m['numeric_static_contract_sha256']and sha(BATCH/'role-binding.json')==m['role_binding_sha256']and sha(ROOT/role['mapping'])==role['mapping_sha256']==m['role_mapping_sha256']=='bc7d702aedfb762bec50929d277f0374fdc74c5121d19dfc25b9328768117e42'
    lines=[line.strip()for line in texts[913].splitlines()]
    for window in contract['windows']:
        assert[dict(line=n,text=lines[n-1])for n in range(window['first'],window['last']+1)]==window['instructions']
    assert all(v in texts[913]for v in['i32.const 432','i64.load offset=112','i32.const 288','f64.store offset=984','call 69552','i32.load offset=1972','i32.load offset=2032','i32.load offset=2056'])
    def data(address,size):
        answer=bytearray(size)
        for base,pos,n in original['data_segments']:
            if base is None:continue
            lo,hi=max(base,address),min(base+n,address+size)
            if lo<hi:answer[lo-address:hi-address]=raw[pos+lo-base:pos+hi-base]
        return bytes(answer)
    npc=m['npc_definition'];declaration=data(npc['pointer'],72);assert declaration.hex()==npc['raw72_hex']and u(declaration,24)==600 and data(u(declaration,16),u(declaration,20))==b'Kobold Vermin'
    assert native.stat().st_size==150633472 and sha(native)==m['windows_reference']['sha256']=='1c0912276637a41a1a971886bb74626577d021af55a313128f85fdbfcc3b2f1d';exe=native.read_bytes();tail=declaration[24:69];assert len(tail)==45 and tail.hex()==m['windows_reference']['scalar_tail45_hex'];matches=[];at=0
    while True:
        at=exe.find(tail,at)
        if at<0:break
        matches.append(at);at+=1
    assert matches==m['windows_reference']['scalar_tail_file_matches']==[120684464]and m['windows_reference']['executed']is False
    cases=load(BATCH/'input.json');actual=[json.loads(x)for x in(BATCH/'stdout.jsonl').read_text().splitlines()];observations=[json.loads(x)for x in(BATCH/'raw-games.jsonl').read_text().splitlines()];assert len(cases)==len(actual)==80 and len(observations)==125
    counts=Counter();traces=[];cursor=0
    for case,a in zip(cases,actual,strict=True):
        assert case['id']==a['id'];answers,branches=reference(case,counts);assert answers==a['answers'],('reference',case['id']);traces.extend(branches)
        for index,answer in enumerate(answers):
            obs=observations[cursor];cursor+=1;assert obs['case_id']==case['id']and obs['operation']==index;game=bytes.fromhex(obs['raw_game8192_hex']);assert len(game)==8192
            assert (u(game,1784),u(game,1788),u(game,1792))==(len(case['state']['units432_hex']),obs['unit_pointer'],len(case['state']['units432_hex']))
            assert game[2587]==case['state']['phase2587']and u(game,2352)==case['state']['now_bits']and q(game,984)==int(answer['accounted_total_bits'])and[u(game,1720+4*i)for i in range(4)]==answer['rng_words']
            assert all(u(game,p)==0 for p in[2032,2056,1972]);counts['explicit_empty_source_headers']+=3
            for row in answer['units432_hex']:assert len(bytes.fromhex(row))==432;counts['full432_preservation_bytes']+=432
            counts['raw8192_observation_bytes_not_general_validation']+=8192;counts['full913_targets']+=1
    assert counts['full432_preservation_bytes']==55296 and counts['full913_targets']==125 and counts['NaN_input_value_category_only']==2
    assert runtime==comp['runtime']and runtime['full_original913_calls']==125 and runtime['fresh_instances']==80 and runtime['actual_host_calls']==0 and runtime['denied_imports']==882 and runtime['original_error']is None and runtime['stack_all_restored']
    assert len(runtime['stack_checks'])==285 and all(v['returned']and v['before']==v['after']==1048576 for v in runtime['stack_checks'])and runtime['peak_memory_bytes']<=33554432 and runtime['raw_observation_bytes']==(BATCH/'raw-games.jsonl').stat().st_size
    for name in['application_start_called','windows_exe_executed','network_used','user_saves_accessed']:assert runtime[name]is False
    terminal=load(BATCH/'process-terminal.json');assert terminal['exit_code']==0 and terminal['pid_missing']and terminal['pgid_missing']and terminal['launcher_error']is None
    assert m['validator']['exit_code']==0 and m['validator']['pgid_missing']and m['validator']['seconds']<45 and m['original_executed_by_builder']is False
    assert sha(BATCH/'raw-games.jsonl')==comp['raw_game_observations_sha256']and sha(BATCH/'stdout.jsonl')==comp['output_sha256']and sha(BATCH/'stderr.log')==comp['stderr_sha256']
    audit_source=load(BATCH/'expectation-read-audit.json');assert not audit_source['forbidden']
    for name,h in hand['frozen_author_files'].items():assert sha(ROOT/name)==h
    for name,h in sources.items():assert sha(ROOT/name)==h
    assert not AUDIT
    semantic_unique=len({json.dumps({k:v for k,v in case.items()if k!='id'},sort_keys=True)for case in cases})
    result=dict(status='pass_fresh1391_nonlethal913_Fraction_numeric_and_whole432only',version='0.139.1',build='b89633f9b',source_sha256=WASM,author_handoff_sha256=HAND,comparison_sha256=COMP,reviewer_script_sha256=sha(Path(__file__)),frozen_author5=hand['frozen_author_files'],source_files=len(sources),production_files=sum(n.startswith('reconstruction/')for n in sources),source_edges=len(edges),sources=sources,source_import_edges=edges,pure_helpers=helpers,bindings=functions,only_export_section_changed=True,allocator=dict(index=93365,type=6,signature=['7f7f','7f']),counts=dict(counts),formal_counts=dict(fresh_fixtures=80,semantic_unique_inputs=semantic_unique,complete_original913_entries=125,full432bytes=55296,Windows_application_or_instruction_emulation=0,full_game_frames=0,reviewer_author_program_executions=0,reviewer_original_executions=0,differences=0),native45B_static_only=dict(path=str(native),sha256=m['windows_reference']['sha256'],file_matches=matches,bytes=45,executed=False,full_Native_913_identity_or_ABI_proven=False),author_process=terminal,reviewer_audit=dict(AUDIT),expected_json_outputs_read=False,limits=['Fresh1391 original functions/inputs and explicit8KBsyntheticGame/initialized432BUnit fixtures only;old139 core reuse is a rule hypothesis not previous runtime acceptance.','Formal acceptance coversfull432Unit bytes,HP288/f64G984/RNG,vectorheaders/clock/phase/empty sourcecounts. Other8KBGame/stats/events/clientpackets are raw observations,not independently reconstructed.','Nonlethal/context0/emptyitems/spells/procs/normalbossheader. Lethal/death/rewards,nonempty69552,othercontexts/headers/variants remainPending.','NaN2 are inputvalue-category cases;JSNumber→WASM NaNpayload/sign not observed or claimed. Theirfiniteclamp1 outputs/HP/total remain exact.','Native45-byte declarationtail matchonly;no Native function/ABI/gameplay/emulation/Windowsexecution added.','No real constructor/App/AI/mainloop/world/playerinput/multiplayer/save/UI/fullgame acceptance. Negative modelguard8 are not original-case coverage.','RawGame8192 inputs are synthetic zeros/quietheaders,not a recovered completeGame schema;unasserted outputfields remainunknown.'],seconds=time.monotonic()-started)
    save(out/'review.json',result);save(out/'independent-branch-traces.json',traces);print(json.dumps(dict(directory=str(out),review_sha256=sha(out/'review.json'),counts=dict(counts),seconds=result['seconds'])),flush=True)


if __name__=='__main__':main()
