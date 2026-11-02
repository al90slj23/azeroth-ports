#!/usr/bin/env python3
"""Expected-first full49961 with actual1108/925 and explicit terminal trigger."""
from dataclasses import replace
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_terminal139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_player_update139 import (load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,
    RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA)
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.terminal139 import TerminalInput139,transition_terminal,COUNTER_KEYS
from core_spec.opening139 import DefaultOpeningInput139,initialize_default_opening139,opening_known_game139
from core_spec.opening_profile139 import EmptyAccountSources139
from core_spec.growth139 import from_constructor139
from core_spec.enemy_ai139 import EnemyAIState139,update_enemy_ai139
from core_spec.incoming139 import IncomingState139
from core_spec.incoming_history139 import IncomingHistory139


def closure():
    names=set(production_sources135(ROOT,'core_spec.terminal139','core_spec.opening139','core_spec.enemy_ai139'))
    names.update('scripts/'+n for n in('check_terminal139.py','run_terminal139_oracle.mjs','build_terminal139_oracle.py',
        'check_player_update139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def fixture_rows(kind,xyz):
    stride,guid_off,ao,bo,so,do=(112,16,32,44,56,60)if kind=='auxiliary'else(88,24,44,56,68,72)
    row=bytearray([0xa5]*stride);struct.pack_into('<Q',row,guid_off,0x1000200030004 if kind=='auxiliary'else 0x8000000000000042)
    struct.pack_into('<3I',row,ao,*xyz);struct.pack_into('<3I',row,bo,f.add(xyz[0],0x3f800000),f.add(xyz[1],0x40000000),f.add(xyz[2],0x40400000))
    struct.pack_into('<II',row,so,0x3f800000,0x40000000)
    return(tuple(row),tuple([0x5a]*stride))


def projection(s):
    return dict(phase2587=s.phase2587,action1644=s.action_sequence1644,movement2412=s.movement_sequence2412,
        packet_capacity=s.packet_capacity,packet_count=s.packet_count,notification_capacity=s.notification_vector_capacity,
        notification_count=s.notification_count,rng_preserved=True,
        vectors=dict(units=dict(count=s.units_count,storage=[list(r)for r in s.units_storage]),
            auxiliary=dict(count=s.auxiliary_count,storage=[list(r)for r in s.auxiliary_storage]),
            claims=dict(count=s.claims_count,storage=[list(r)for r in s.claims_storage])))


def scalar_delta(old,new):
    delta=[]
    for offset,a,b in((1644,old.action_sequence1644,new.action_sequence1644),(2412,old.movement_sequence2412,new.movement_sequence2412),
        (1880,old.packet_capacity,new.packet_capacity),(1888,old.packet_count,new.packet_count),
        (1892,old.notification_vector_capacity,new.notification_vector_capacity),(1900,old.notification_count,new.notification_count)):
        aa,bb=struct.pack('<I',a),struct.pack('<I',b)
        delta.extend([offset+j,bb[j]]for j in range(4)if aa[j]!=bb[j])
    if old.phase2587!=new.phase2587:delta.append([2587,new.phase2587])
    if old.packet_capacity!=new.packet_capacity:delta.append([1884,'heap_pointer'])
    if old.notification_vector_capacity!=new.notification_vector_capacity:delta.append([1896,'heap_pointer'])
    return sorted(delta)


def corpus(world,phase):
    layouts=[('real4NPC_moving_stops',0,1,1,0,'',False)]
    if phase=='full':layouts.extend([
        ('controlled_auxiliary_claims_UTF8',0,1,1,0,'中文"\\\n\t\r\x00😀',True),
        ('field400_guard',0,0,1,0,'',False),('endless_guard',11,1,1,1,'',False),
        ('phase_guard',69,1,2,0,'',False)])
    rows=[]
    for group,seed,field400,phase_byte,endless,hero,fixture in layouts:
        opening=initialize_default_opening139(DefaultOpeningInput139(seed,EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
        g=from_constructor139(opening.constructor,phase2587=1)
        records=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells'])
        incoming=IncomingState139(1,0,0,0x3f800000,g.current_hp_bits,g.derived_bits[1536],g.derived_bits[1568],g.derived_bits[1572],
            items8=(),last_hit1652_bits=0xc1200000)
        ai=update_enemy_ai139(EnemyAIState139(records,0x3f800000,0x3dcccccd,opening.constructor.player_xyz,
            incoming,IncomingHistory139(0,0,0,(),(),()),tuple(g.player_fields.items()),1),world,
            english_names={5830904:'Kobold Vermin'})
        assert not ai.attacks
        game=opening_known_game139(opening)
        def word(o):
            part=game[o:o+4]
            if o in(1084,1088,1092,1096,1104):return 0  # current1600 temp1172..1196 copies zeroScratch2807..2831
            assert None not in part
            return int.from_bytes(bytes(part),'little')
        pc=len(opening.packets)+len(ai.packets);cap=opening.packet_capacity
        for count in range(len(opening.packets),pc):
            if count==cap:cap=max(4,cap*2)
        aux=fixture_rows('auxiliary',opening.constructor.player_xyz)if fixture else()
        claims=fixture_rows('claims',opening.constructor.player_xyz)if fixture else()
        s=TerminalInput139(field400,phase_byte,endless,0x3fa00000,word(1644),ai.state.movement_sequence2412,0,
            ai.state.records432,len(records),aux,int(fixture),claims,int(fixture),cap,pc,4,1,
            tuple((o,word(o))for o,_ in COUNTER_KEYS),0,0,1,1,0,hero,0,0,'english_fallback')
        initial=projection(s);stages=[]
        for _ in range(2):
            old=s;r=transition_terminal(s,world);s=r.state
            stages.append(dict(state=projection(s),packets=[list(v)for v in r.packets],
                notifications=[list(v)for v in r.notifications],stopped_guids=[str(v)for v in r.stopped_guids],
                changed_Game_bytes=scalar_delta(old,s)))
        case=dict(id=len(rows),app_seed_u64=str(seed),field400=field400,phase2587=phase_byte,endless2568=endless,
            now_bits=0x3fa00000,hero=hero,fixture_vectors=dict(auxiliary=[bytes(r).hex()for r in aux],claims=[bytes(r).hex()for r in claims]),repeat=2)
        rows.append(dict(id=case['id'],group=group,input=case,initial=initial,stages=stages))
    return json.loads(json.dumps(rows,ensure_ascii=False))

def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA and sha(CONTEXT)==CONTEXT_SHA and sha(GATE)==GATE_SHA and sha(RANGES)==RANGES_SHA and sha(WORLD/'receipt.json')==WORLD_SHA
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original input denied during expectation')
    sys.addaudithook(audit)
    try:world,*_=load_world139(WORLD);rows=corpus(world,args.phase)
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('terminal139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden));save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json',m['module_file'],'expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,full_world_owners_retained=True,controlled_player_placement=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_terminal139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(s)for s in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();diff=[]
    def eq(cid,label,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(diff)<80:diff.append(dict(id=cid,field=label,expected=want,actual=got))
    def cells(cid,label,want,got,width):
        eq(cid,label+'.capacity',len(want),len(got))
        for j,(row,hx)in enumerate(zip(want,got,strict=False)):
            raw=bytes.fromhex(hx);assert len(raw)==len(row)==width
            for k,(v,b)in enumerate(zip(row,raw,strict=True)):
                if v is None:counts['None']+=1;counts['nonzero_None']+=bool(b)
                else:eq(cid,f'{label}[{j}]+{k}',v,b);counts['known']+=1
    for row,a in zip(rows,actual,strict=False):
        cid=row['id'];eq(cid,'id',cid,a['id']);previous=a['before']
        for j,(want,got)in enumerate(zip(row['stages'],a['stages'],strict=True)):
            for key,value in want['state'].items():
                if key=='vectors':
                    for name,width in(('units',432),('auxiliary',112),('claims',88)):
                        eq(cid,name+'.count',value[name]['count'],got['vectors'][name]['count'])
                        cells(cid,name,value[name]['storage'],got['vectors'][name]['storage'],width)
                        for index,(model,old,new)in enumerate(zip(value[name]['storage'],previous['vectors'][name]['storage'],got['vectors'][name]['storage'],strict=True)):
                            old,new=bytes.fromhex(old),bytes.fromhex(new)
                            for k,v in enumerate(model):
                                if v is None:eq(cid,f'{name}physical_None_conserved[{index}]+{k}',old[k],new[k]);counts['physical_None_conserved']+=1
                elif key=='rng_preserved':eq(cid,'rng_unmodified',previous['rng_words'],got['rng_words'])
                else:eq(cid,key,value,got[key])
            eq(cid,'complete_packets'+str(j),want['packets'],got['new_packets']);eq(cid,'complete_notifications'+str(j),want['notifications'],got['new_notifications'])
            eq(cid,'all_Game2592_changed_bytes'+str(j),want['changed_Game_bytes'],got['changed_Game_bytes'])
            for key in('pickups','special','windows','boundaries'):
                eq(cid,'background_'+key,previous['background'][key],got['background'][key])
            eq(cid,'no_spawn_counter_change',previous['background']['counter2408'],got['background']['counter2408'])
            counts['full49961']+=1;counts['stops']+=len(want['stopped_guids']);counts['complete_packets']+=len(want['packets'])
            counts['complete_packet_bytes']+=sum(len(p[2])//2 for p in want['packets']);counts['complete_notifications']+=len(want['notifications'])
            counts['complete_notification_bytes']+=sum(len(n[1])//2 for n in want['notifications']);counts['Game2592_bytes_compared']+=2592
            previous=got
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',diff)
    artifacts={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/n).exists()}
    report=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],
        sources_before=sources,sources_after=sources,source_import_edges=edges,expected_before_original=True,
        original_input_contains_expected=False,forbidden_model_reads=forbidden,artifacts=artifacts,frozen=frozen,
        runtime=runtime,process=terminal,counts=dict(counts),limits=[
        'Actualfull1108->actualfull925 atnow1/dt.1->controlledfield400/now1.25->full49961 twice; no naturalBoss victory producer.',
        'Real4NPC/2Rune/windows/special/69bounds retained; onlyexplicitauxiliary112/companion88 fixtures added in separate case.',
        'Canonical nonflat terrain queried by rebound29912/23333 semantics; processed positions finite. Miss/nearestprimary path remains static-only unless exercised.',
        'DefaultWarrior/Human/Elwynn Englishfallback labels; heroUTF8 legalownedString capacity/ptr/len; no locale-generalization.',
        'Complete new232/221 andvictoryJSON bytes/capacity,packet/notification headers,all2592Gamechangedbytes and432BNoneconservation compared; not wholeheap.',
        'Earlier135 purealgorithms adapted and rebound; noold runtime acceptance transferred. Otherrecap/source/labels remainPending.',
        '0 fullmain884frames,0 naturalvictories,0 completegames; noinstall/save/Android changes.'])
    save(out/'comparison.json',report)
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),
        differences=counts['differences'],first=diff[:4],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
