#!/usr/bin/env python3
"""Expected-first current139 fullopening→inactive-world first level/selection."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_growth_world139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from check_asset_world139 import load_world139
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.opening139 import DefaultOpeningInput139,initialize_default_opening139,opening_projection139
from core_spec.opening_profile139 import EmptyAccountSources139
from core_spec.growth139 import from_constructor139,projection139,PendingGrowth139
from core_spec.growth_world139 import check_inactive_world139,gain_xp_world139,select_card_world139

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
WORLD=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model'
WORLD_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
CONTEXT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_begin1108.memory'
CONTEXT_SHA='5082076b26e04c1c9a1f27bc05e89f4d5ef0b60425f9000d0aafbbd997487da0'
RANGES=ROOT/'evidence/asset-world139-observation-check-20261102T032808.223945Z/source-ranges.json'
RANGES_SHA='ddfbd9aa7c80d54a25446f33955f474feeebaf3305d416cfffd216b7d065ae02'
GATE=ROOT/'reports/2026-11-02-entry-world0139-context-v2-independent-review.json'
GATE_SHA='e3ea36cd8eb773a142afe400f959ce63e0d45b715512fdc206acbc2c0b736cb1'
V1=ROOT/'evidence/growth139-oracle-20261102T060448.902434Z/task-handoff.json'
V1_SHA='02f36fb96bddbc71a4a093bc10325a8458dd4dd1f67bf618dcee8ebfb9fc6d59'


def closure():
    names=set(production_sources135(ROOT,'core_spec.opening139','core_spec.growth_world139','resource_spec.world_query135'))|set('scripts/'+n for n in('check_growth_world139.py','run_growth_world139_oracle.mjs','build_growth_world139_oracle.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def expected(case,world):
    opening=initialize_default_opening139(DefaultOpeningInput139(int(case['app_seed_u64']),EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    cells=[list(row)for row in opening.units['answers'][-1]['records432_cells']]
    for j,row in enumerate(cells):
        if case['dead_mask']>>j&1:row[:4]=struct.pack('<I',1)
    state=replace(from_constructor139(opening.constructor,phase2587=1),rng_words=opening.rng_words,units432_cells=tuple(tuple(row)for row in cells))
    before=projection139(state);proof=check_inactive_world139(state);gain=gain_xp_world139(state,case['amount']);index=next((i for i,c in enumerate(gain.state.candidates)if c.variant=='new'),None)
    assert(case['amount']<5)==(index is None)
    selection=None
    if index is not None:
        result=select_card_world139(gain.state,index);assert result.accepted
        selection=dict(projection=projection139(result.state),live32_cells=[list(row)for row in result.state.live32_cells]);assert result.state.units432_cells==state.units432_cells
    assert gain.state.units432_cells==state.units432_cells
    projection=opening_projection139(opening)
    background={k:projection[k]for k in('units','pickups','special','windows','boundaries')};background['units']=dict(background['units'],storage=cells)
    return dict(before=before,gain=projection139(gain.state),selection=selection,selected_index=index,
        opening=projection,background=background,model_events=list(gain.events),
        inactive_world_proof=dict(NPC_count=proof.NPC_count,dead=proof.dead_markers,stationary_or_expired=proof.stationary_or_expired))


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def source_guard_selfchecks(world):
    opening=initialize_default_opening139(DefaultOpeningInput139(0,EmptyAccountSources139(0,0,0,0),tuple([0xa5]*40)),world)
    rows=tuple(tuple(r)for r in opening.units['answers'][-1]['records432_cells'])
    state=replace(from_constructor139(opening.constructor,phase2587=1),rng_words=opening.rng_words,units432_cells=rows)
    def replaced_row(offset,value):
        row=list(rows[0]);row[offset:offset+len(value)]=value
        return replace(state,units432_cells=(tuple(row),)+rows[1:])
    cases=[('active_NPC',replaced_row(344,struct.pack('<I',0x3f800000))),
        ('unknown_live_duration',replaced_row(344,[None]*4)),
        ('nonempty_auxiliary',replace(state,auxiliary112_cells=(tuple(bytes(112)),))),
        ('nonempty_claim',replace(state,claims88_cells=(tuple(bytes(88)),)))]
    checked=[]
    for name,value in cases:
        try:check_inactive_world139(value)
        except PendingGrowth139:checked.append(dict(name=name,result='rejected_pending'))
        else:raise AssertionError(('Mustretainpendingworldguard',name))
    row=list(rows[0]);row[:4]=struct.pack('<I',1);row[340:348]=[None]*8
    proof=check_inactive_world139(replace(state,units432_cells=(tuple(row),)+rows[1:]));assert proof.dead_markers==1
    checked.append(dict(name='dead_marker_skips_unknown_start_duration',result='known_predicate_only'))
    try:gain_xp_world139(replace(state,live32_cells=(tuple(bytes(32)),)),5)
    except PendingGrowth139:checked.append(dict(name='nonempty_live_recalculation',result='rejected_pending'))
    else:raise AssertionError('Nonemptyliveguard')
    return checked


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args()
    assert sha(V1)==V1_SHA
    frozen_v1=json.loads(V1.read_text())['frozen_author_files']
    for name,h in frozen_v1.items():assert sha(ROOT/name)==h
    files,edges=closure();sources={n:sha(ROOT/n)for n in files}
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA and sha(CONTEXT)==CONTEXT_SHA and sha(GATE)==GATE_SHA and sha(RANGES)==RANGES_SHA and sha(WORLD/'receipt.json')==WORLD_SHA
    opened=[];forbidden=[];model_phase=True
    def audit(event,values):
        if model_phase and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            path=Path(os.fsdecode(values[0])).resolve();opened.append(str(path))
            if path.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(path):forbidden.append(str(path));raise RuntimeError('Original input denied during independent expectation')
    sys.addaudithook(audit)
    rows=[]
    try:
        world,wr,payloads=load_world139(WORLD)
        cases=[dict(id=0,app_seed_u64='0',amount=5,dead_mask=0,select_index=None)]
        if args.phase=='full':
            for seed,amount,mask in[(1,5,0),(2,5,0),(3,5,0),(42,5,0),(255,5,0),((1<<64)-1,5,0),(0,5,1),(0,5,15),(0,2,0),(0,6,0)]:cases.append(dict(id=len(cases),app_seed_u64=str(seed),amount=amount,dead_mask=mask,select_index=None))
        guards=source_guard_selfchecks(world)
        for case in cases:
            e=expected(case,world);case['select_index']=e['selected_index'];rows.append(dict(id=case['id'],input=case,expected=e))
    finally:model_phase=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('growth-world139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for name,h in sources.items():p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    save(out/'inputs.json',cases);save(out/'expected.json',rows);save(out/'model-source-guards.json',guards);save(out/'expectation-read-audit.json',dict(layer='Pythonopenaudit_notOSaudit',opened=opened,forbidden=forbidden))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','model-source-guards.json','config.json','manifest.json',manifest['module_file'],'expectation-read-audit.json')}
    save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False,independent_world_receipt_sha256=WORLD_SHA,resource_context_gate_sha256=GATE_SHA,frozen_v1_source_sha256=frozen_v1,full_world_owners_retained=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_growth_world139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        p=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=p.pid,pgid=p.pid,command=command,deadline_seconds=120))
        try:code=p.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();code=p.returncode
    terminal=dict(pid=p.pid,pgid=p.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(p.pid),pgid_missing=missing(p.pid,True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'actual.jsonl').read_text().splitlines()];diff=[];counts=Counter()
    def eq(case,field,want,got):
        counts['assertions']+=1
        if want!=got and len(diff)<100:diff.append(dict(id=case,field=field,expected=want,actual=got))
    def projection(case,stage,want,got):
        for key,value in want.items():
            if key=='player_fields':
                for field,v in value.items():eq(case,stage+'.player_field'+field,v,got[key].get(field));counts['known_player_fields']+=1
            else:eq(case,stage+'.'+key,value,got.get(key))
    for row,a in zip(rows,actual,strict=False):
        case=row['id'];e=row['expected'];eq(case,'id',case,a['id'])
        eq(case,'freshGame',False,a['new_Game_pointer']==a['old_snapshot_Game_not_target']);eq(case,'account',a['account368_before_hex'],a['account368_after_hex']);eq(case,'profile',a['profile376_before_hex'],a['profile376_after_hex']);eq(case,'selection-canaries',['c3'*16,'d7'*16],a['selection_canaries'])
        eq(case,'opening.packets',e['opening']['packets'],a['opening']['packets']);eq(case,'opening.RNG',e['opening']['rng_words'],a['opening']['projection']['rng_words'])
        for stage in('before','gain','selection'):
            want=e['selection']['projection']if stage=='selection'and e['selection']else e.get(stage)
            if stage=='selection'and want is None:eq(case,stage,None,a[stage]);continue
            projection(case,stage,want,a[stage]['projection'])
            for key,vector in e['background'].items():
                seen=a[stage]['background'][key];eq(case,stage+'.'+key+'.count',vector['count'],seen['count']);eq(case,stage+'.'+key+'.cap',vector['capacity'],seen['capacity'])
                for j,(cells,hx)in enumerate(zip(vector['storage'],seen['storage'],strict=True)):
                    raw=bytes.fromhex(hx)
                    for i,(v,b)in enumerate(zip(cells,raw,strict=True)):
                        if v is None:counts['background_None_bytes']+=1;counts['background_nonzero_None_bytes']+=bool(b)
                        else:eq(case,f'{stage}.{key}[{j}]+{i}',v,b);counts['background_known_bytes']+=1
            eq(case,stage+'.inactive_background_fullbytes',a['before']['background'],a[stage]['background'])
            if stage=='selection':
                for cells,hx in zip(e['selection']['live32_cells'],a['selection']['live32_hex'],strict=True):
                    for i,(v,b)in enumerate(zip(cells,bytes.fromhex(hx),strict=True)):
                        if v is None:counts['live_None_bytes']+=1;counts['live_nonzero_None_bytes']+=bool(b)
                        else:eq(case,'live32+'+str(i),v,b);counts['live_known_bytes']+=1
        counts['full_opening_packets']+=len(e['opening']['packets']);counts['selected']+=e['selection']is not None;counts['phase2']+=e['gain']['phase2587']==2
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    for n,h in sources.items():assert sha(ROOT/n)==h
    for n,h in frozen.items():assert sha(out/n)==h
    for n,h in frozen_v1.items():assert sha(ROOT/n)==h
    save(out/'differences.json',diff)
    artifacts={n:sha(out/n)for n in('inputs.json','expected.json','config.json','manifest.json','prepared.json','actual.jsonl','runtime.json','owned-start.json','owned-terminal.json','expectation-read-audit.json','stderr.log','differences.json')if(out/n).exists()}
    comp=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=len(diff),sources_before=sources,sources_after=sources,source_import_edges=edges,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,artifacts=artifacts,frozen=frozen,runtime=runtime,process=terminal,counts=dict(counts),independent_world_receipt_sha256=WORLD_SHA,resource_context_snapshot_sha256=CONTEXT_SHA,resource_context_gate_sha256=GATE_SHA,frozen_v1_unchanged=True,fullworld_objects_retained=True,limitations=['Resource-onlylegalv2post1108context/newGame;notnaturalApp/Rc/bootstrap/externref.','NewXPawardexplicitinput,notcollection;deadmask1/15explicitmarkerfixtures,notnaturaldeathproducer.','Samecurrentfull1108creates4NPC/2Rune/windows/special/boundaries andallownerbyteskept;velocity0/pathNoneexplicit.','26364stop/resumedomainonlyinactiveNPC+emptyaux/claims;active movement/nonemptyauxclaimpending.','Onlyfirstnewabilityselection;upgrade/gold/nonemptylive32recalculationpending.','UI/appearance/additionalkeyedfields/fullpackets/Aura48/physicalBTreeallocationnotprojected.','Mainloop/nativeWindows/network/save/fullgame0.'])
    save(out/'comparison.json',comp);print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=len(diff),first=diff[:6],counts=dict(counts),process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or diff:raise SystemExit(1)


if __name__=='__main__':main()
