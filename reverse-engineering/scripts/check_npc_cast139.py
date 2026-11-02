#!/usr/bin/env python3
"""Expected-first natural4NPC→controlled action→cleave on the same139Game."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,signal,subprocess,sys,time
sys.dont_write_bytecode=True
from build_npc_cast139_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from load_world_position139_inputs import load_world139_canonical
from source_closure137 import verify_local_source_closure
from production_closure135 import production_sources135
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec.npc_cast139 import NPCCombatInput139,compose_npc_cleave139
from core_spec.cast139 import CleaveDefinition139
CANONICAL=ROOT/'evidence/asset-world139-owned-20261102T031312.028310Z/model'
CANONICAL_SHA='46a89c27c6be70beb9f957dd05c6fecb8c93c83647fcb40182e255d352ff3a48'
SNAPSHOT=ROOT/'evidence/entry-world139-v2-probe-20261102T030946.739944Z/after_real_world6786.memory'
SNAPSHOT_SHA='ed3a755752ddf9907712b408f7ef042f5a9407d684d0aa6afd3f0a394bbd7ce2'
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def closure():
    names=set(production_sources135(ROOT,'core_spec.npc_cast139','resource_spec.world_query135'))|{
        'scripts/check_npc_cast139.py','scripts/build_npc_cast139_oracle.py',
        'scripts/run_npc_cast139_oracle.mjs','scripts/load_world_position139_inputs.py',
        'scripts/source_closure137.py','scripts/production_closure135.py'}
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            edge=e.args[0];assert isinstance(edge,tuple)and len(edge)==2 and edge[1]not in names
            names.add(edge[1])


def corpus(pilot):
    rows=[]
    def add(action='near_first',repeats=1,gentle=False,rng=None,counter=10,backing=False):
        raw=tuple(bytes((19*i+13*j+7)&255 for j in range(432)).hex()for i in range(4))if backing else()
        rows.append(dict(id=len(rows),action=action,repeats=repeats,
            gentle_owned_multiplier=gentle,rng_words=rng,counter=counter,initial_backing=list(raw)))
    for action in ('keep_start','near_first','near_second'):add(action)
    if not pilot:
        add(repeats=4,gentle=True);add('near_second',repeats=4,gentle=True)
        add(backing=True)
        add(repeats=4,gentle=True,rng=[1,2,3,4],counter=0xfffffffe,backing=True)
        add(repeats=4,gentle=True,rng=[0,0,0,0],counter=0)
    return rows


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');a=p.parse_args()
    files,edges=closure();before={n:sha(ROOT/n)for n in files}
    assert sha(SNAPSHOT)==SNAPSHOT_SHA and sha(NODE)==NODE_SHA
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('npc-cast139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    manifest=build(out);definition=CleaveDefinition139(manifest['definition']['pointer'],b'cleave',bytes.fromhex(manifest['definition']['raw88_hex']))
    world,world_provenance=load_world139_canonical(CANONICAL,CANONICAL_SHA)
    rows=corpus(a.phase=='pilot');expected=[];audit=[];live=True
    def hook(event,values):
        if event!='open'or not live or not isinstance(values[0],(str,bytes,os.PathLike)):return
        path=Path(os.fsdecode(values[0])).resolve();mode,flags=values[1:3]
        reading=isinstance(mode,str)and'r'in mode or mode is None and isinstance(flags,int)and flags&3==os.O_RDONLY
        if reading:
            allowed=path.suffix.lower()not in('.memory','.wasm','.exe','.wat');audit.append(dict(path=str(path),allowed=allowed))
            if not allowed:raise AssertionError('Original-input read denied during independent expectations')
    sys.addaudithook(hook)
    try:
        for row in rows:
            value=NPCCombatInput139(None if row['rng_words']is None else tuple(row['rng_words']),
                row['counter'],row['action'],row['repeats'],row['gentle_owned_multiplier'],tuple(row['initial_backing']))
            expected.append(dict(id=row['id'],**compose_npc_cleave139(value,world,definition)))
    finally:live=False
    for n,h in before.items():q=out/'source-snapshot'/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/n).read_bytes());assert sha(q)==h
    save(out/'inputs.json',rows);save(out/'expected.json',expected)
    save(out/'expectation-read-audit.json',dict(kind='Pythonopen_notOSsyscall',events=audit,forbidden=[]))
    save(out/'config.json',dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,
        game_pointer=14685248,app_pointer=14680072,input_path=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json')))
    frozen={n:sha(out/n)for n in('manifest.json',manifest['module_file'],'inputs.json','expected.json','config.json')}
    assert before=={n:sha(ROOT/n)for n in files}
    save(out/'prepared.json',dict(source_before=before,source_import_edges=edges,frozen=frozen,
        expected_before_original=True,input_contains_expected=False,world_provenance=world_provenance,
        controlled_player_action=True,full_input_or_AI_not_claimed=True))
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_npc_cast139_oracle.mjs'),str(out),str(out/'config.json')]
    started=time.monotonic()
    with(out/'stdout.jsonl').open('wb')as so,(out/'stderr.log').open('wb')as se:
        child=subprocess.Popen(command,stdout=so,stderr=se,start_new_session=True)
        save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=90))
        try:child.wait(timeout=90)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,
        pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True),seconds=time.monotonic()-started)
    save(out/'owned-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'stdout.jsonl').read_text().splitlines()];diff=[]
    known=unknown=nonzero=conserved=0
    def records(cells,raws,id,stage,previous=None):
        nonlocal known,unknown,nonzero,conserved
        assert len(cells)==len(raws)==4
        for ri,(row,hx)in enumerate(zip(cells,raws,strict=True)):
            raw=bytes.fromhex(hx);assert len(row)==len(raw)==432
            prior=None if previous is None else bytes.fromhex(previous[ri])
            for offset,v in enumerate(row):
                if v is None:
                    unknown+=1;nonzero+=raw[offset]!=0
                    if prior is not None:
                        conserved+=1
                        if prior[offset]!=raw[offset]:diff.append(dict(id=id,stage=stage,field='opaque_original_byte_changed',row=ri,offset=offset))
                else:
                    known+=1
                    if v!=raw[offset]:diff.append(dict(id=id,stage=stage,field='known_unit_byte',row=ri,offset=offset,expected=v,actual=raw[offset]))
    for e,g in zip(expected,actual,strict=False):
        assert e['id']==g['id']and len(g['answers'])==4
        if e['actor_before']!=g['actor_before']:diff.append(dict(id=e['id'],field='actor_before',expected=e['actor_before'],actual=g['actor_before']))
        for j,(ep,ac)in enumerate(zip(e['npc_answers'],g['answers'],strict=True)):
            records(ep['records432_cells'],ac['records432_hex'],e['id'],'NPC'+str(j))
            for key in(set(ep)|set(ac))-{'records432_cells','records432_hex'}:
                if ep.get(key)!=ac.get(key):diff.append(dict(id=e['id'],stage=j,field='NPC.'+key,expected=ep.get(key),actual=ac.get(key)))
        assert len(e['stages'])==len(g['cast_stages'])
        previous=g['answers'][-1]['records432_hex']
        for j,(ep,ac)in enumerate(zip(e['stages'],g['cast_stages'],strict=True)):
            records(ep['records432_cells'],ac['records432_hex'],e['id'],'cast'+str(j),previous);previous=ac['records432_hex']
            for key in(set(ep)|set(ac))-{'records432_cells','records432_hex'}:
                if ep.get(key)!=ac.get(key):diff.append(dict(id=e['id'],stage=j,field='cast.'+key,expected=ep.get(key),actual=ac.get(key)))
    if len(expected)!=len(actual):diff.append(dict(field='completed',expected=len(expected),actual=len(actual)))
    assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}
    save(out/'differences.json',diff)
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    report=dict(version='0.139.0',build='f79c5e2b4',cases=len(rows),completed=len(actual),differences=len(diff),
        full5719_calls=4*len(rows),full922_calls=sum(x['repeats']for x in rows),process=terminal,runtime=runtime,
        known_byte_occurrences=known,None_byte_occurrences=unknown,actual_nonzero_None_occurrences=nonzero,
        actual_opaque_byte_conservation_checks=conserved,source_before=before,source_after=before,
        source_import_edges=edges,expected_before_original=True,world_provenance=world_provenance,
        snapshot_sha256=SNAPSHOT_SHA,controlled_player_action=True,complete_games=0,native_executions=0,
        limitations=['Current139 same restoredGame, four real5719(None) then explicit player relocation/phase1 and real922;no complete1108/AI/input/motion.',
            'Pure model gets independently produced canonical139 world and explicit current static88B definition;no original memory supplies expectations.',
            'Inactive NPC bytes remainNone across modules;private A5/5A completions only self-check the explicit semantic-read/HP-only-write contract.',
            'Some extra fixtures change the actual owned80 damage multiplier to0.1 to check repeated nonlethal composition;they do not replace the unresolved default lethal second-hit path.',
            'RawGame,592/HP169 and physical allocations remain observations;complete306 and declared logical/numeric state are predicted.'])
    save(out/'comparison.json',report)
    print(json.dumps(dict(directory=str(out),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),completed=len(actual),differences=len(diff),process=terminal,first=diff[:3])),flush=True)
    if child.returncode or diff:raise SystemExit(1)


if __name__=='__main__':main()
