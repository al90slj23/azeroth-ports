#!/usr/bin/env python3
"""Bind current139 main884 clock and battle ordering, without execution.

This is a static integration contract. It does not turn a component schedule
into a natural App frame or establish the still-unknown entry conditions.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import sqlite3

from incoming139_tools import ROOT, PROFILE, SOURCE_SHA, original, function_proof, save, sha

ROLES = {
    2123:'player',924:'extra_player_actions',983:'owned_effects',1775:'hit_events',
    3755:'area_events',920:'effects',38553:'deadline',2621:'secondary',
    925:'enemy_AI',2890:'collection',2584:'claims',952:'spawn',2372:'special',
    49961:'terminal',1173:'Aura',13956:'after_Aura',4677:'gain_XP',
    973:'network',1108:'opening',1600:'constructor',6786:'cached_world',
    1542:'recalculate',1093:'select',5648:'fatal',2346:'motion'
}
ORDER = [2123,924,983,1775,3755,920,38553,2621,925,2890,2584,952,2372,49961]


def trace(out):
    out.mkdir(parents=True,exist_ok=False)
    source=out/'source';source.mkdir()
    raw,identity,ranges=original()
    proof,texts=function_proof(raw,identity,ranges,{884},source)
    text=texts[884];lines=text.splitlines()
    assert proof[884]['signature']==('7f7c','')
    with sqlite3.connect((PROFILE/'index.sqlite').resolve().as_uri()+'?mode=ro',uri=True)as db:
        db.row_factory=sqlite3.Row;db.execute('pragma query_only=on')
        row=dict(db.execute('select * from functions where idx=884').fetchone())
        calls=[dict(v)for v in db.execute('select callee,wat_offset,wat_line from calls where caller=884 order by wat_offset')]
    wanted=[v['callee']for v in calls]
    candidates=[j for j in range(len(wanted)-len(ORDER)+1)if wanted[j:j+len(ORDER)]==ORDER]
    assert len(candidates)==1, candidates
    sequence=calls[candidates[0]:candidates[0]+len(ORDER)]
    normalized=[' '.join(s.split())for s in lines]
    frames=[];stack=[];at_line={}
    for n,s in enumerate(normalized):
        if re.match(r'^(block|loop|if)(?:\s|$)',s):
            f=dict(kind=s.split()[0],start_local_line=n+1,source_open=s,else_local_line=None,end_local_line=None)
            frames.append(f);stack.append(f)
        elif re.match(r'^else(?:\s|$)',s):
            assert stack and stack[-1]['kind']=='if'
            stack[-1]['else_local_line']=n+1
        elif re.match(r'^end(?:\s|$|\))',s):
            assert stack
            stack.pop()['end_local_line']=n+1
        at_line[n+row['wat_line']]=tuple(stack)
    assert not stack
    common=at_line[sequence[0]['wat_line']]
    for call in sequence:
        assert all(f in at_line[call['wat_line']]for f in common)
    prefix_end=next(j for j in range(10,len(normalized)-1)if normalized[j:j+2]==['i64.store','local.get 0'])
    # The first plain i64.store must be the final timestamp-header tag=1 write.
    assert normalized[prefix_end-2:prefix_end+1]==['local.get 0','i64.const 1','i64.store']
    clock_lines=normalized[:prefix_end+1]
    assert 'local.set 156'in clock_lines and 'f32.demote_f64'in clock_lines
    assert 'f64.store offset=8'in clock_lines and clock_lines.count('select')==2
    start=sequence[0]['wat_line']-row['wat_line']
    finish=sequence[-1]['wat_line']-row['wat_line']
    windows={
        'timestamp_header_prefix':(0,prefix_end+1),
        'core_stage_sequence':(start-2,finish+1)
    }
    # Find the phase1 clock-advance block that lexically encloses this sequence.
    enclosing=[]
    for scope in common:
        a=scope['start_local_line']-1;b=scope['end_local_line']
        near=normalized[a:min(a+18,b)]
        if 'f32.store offset=2352'in near:
            enclosing.append(scope)
    assert len(enclosing)==1
    phase=enclosing[0];pa=phase['start_local_line']-1
    assert normalized[pa+1:pa+7]==['local.get 4','i32.const 255','i32.and','i32.const 1','i32.ne','br_if 0 (;@13;)']
    windows['phase1_clock_gate']=(pa-12,pa+15)
    owner=[j for j in range(len(normalized)-4)if normalized[j:j+4]==['local.get 0','i32.const 16','i32.add','local.set 6']]
    preceding=[j for j in owner if j<pa]
    assert preceding
    last_owner=preceding[-1]
    windows['nearby_stage_owner_base_plus16_assignment']=(last_owner,last_owner+10)
    spawn=next(j for j in range(start,finish)if normalized[j]=='i32.load8_u offset=2579')
    windows['spawn_and_special_guard']=(spawn-1,spawn+12)
    assert normalized[spawn:spawn+3]==['i32.load8_u offset=2579','i32.eqz','if ;; label = @14']
    after=[v for v in calls[candidates[0]+len(ORDER):]if v['callee']in(4677,2181,1173,13956)][:4]
    assert [v['callee']for v in after[:3]]==[4677,2181,1173]
    end_Aura=after[2]['wat_line']-row['wat_line']
    windows['terminal_credit_XP_and_Aura']=(finish+1,end_Aura+3)
    pieces=[]
    for name,(a,b)in windows.items():
        data='\n'.join(lines[a:b])+'\n';p=source/(name+'.wat');p.write_text(data)
        pieces.append(dict(name=name,file=str(p.relative_to(out)),first_WAT_line=row['wat_line']+a,last_WAT_line=row['wat_line']+b-1,sha256=sha(p),text=data))
    selected=[dict(v,role=ROLES[v['callee']])for v in calls if v['callee']in ROLES]
    result=dict(kind='static_current139_main884_integration_contract',version='0.139.0',build='f79c5e2b4',original_wasm_sha256=SOURCE_SHA,trace_source_sha256=sha(__file__),main_function=proof[884],main_owner_expression='Stages receive local6; nearby param0+16 assignments are captured, but full control-flow dominance and param0/App ownership remain unresolved',owner_assignment_WAT_lines=[row['wat_line']+j for j in owner],core_sequence=[dict(v,role=ROLES[v['callee']])for v in sequence],same_sequence_matches=len(candidates),phase_gate='(local4 &255)==1; local4 comes from phase2587 in the surrounding branch; full preceding control flow is not reconstructed',clock='tag@0==1: f64 delta now-previous@8, compare/select clamp0..0.1, demote f32; otherwise dt default+0; always timestamp@8 andtag1. Active phase block adds f32(dt,Game2352).',optional_stages='spawn952 andspecial2372 run only when Game2579==0',tail='terminal49961 → possible2388credit/4677/2181 →1173→13956, with source guards; no full owner or branch semantics claimed',windows=pieces,selected_role_call_sites=selected,selected_role_call_count=len(selected),all_direct_call_sites=len(calls),all_structured_control_frames=len(frames),prestage_calls=[v for v in calls if row['wat_start']+sum(len(x.encode())+1 for x in lines[:pa])<=v['wat_offset']<sequence[0]['wat_offset']],original_executions=0,wasm_instantiations=0,model_runtime_cases=0,full_mainloop_frames=0,complete_games=0,limits=['Static integration order only; no App/bootstrap/externref/network/input/UI/render or complete884 execution.','Several core paths occur earlier in other branches; this unique contiguous14-stage slice does not establish their global reachability or equivalence.','Repeated lexical owner assignments do not prove dominance; App/Game owner construction remains unknown.','Prestage demo/movement/pool guards, callback owners andpoststage queues are retained as source windows/call sites, not independently implemented.','No prior135/138runtime acceptance transferred; installers/saves/Android/public registry untouched.'])
    save(out/'trace.json',result)
    return result


if __name__=='__main__':
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('mainloop139-schedule-static-%Y%m%dT%H%M%S.%fZ')
    r=trace(out)
    print(json.dumps(dict(directory=str(out),trace_sha256=sha(out/'trace.json'),selected_roles=r['selected_role_call_count'],stages=len(r['core_sequence']),original_executions=0)))
