#!/usr/bin/env python3
"""Expected-first0/8/1020 coexistence through real1512/1202/10298/2088."""
from pathlib import Path
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
from itertools import permutations
import argparse,json,os,re,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_self_buffs135_oracle import ROOT,SOURCE,SOURCE_SHA,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
import check_resource_player135 as legacy
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.ability_state import AbilityRecord
from core_spec.derived_stats135 import StatsInput,Modifier,recalculate
from core_spec.resource_consumer135 import LiveVector135,_semantics
from core_spec.resource_aura135 import rebuild_resource_aura135
from core_spec.mixed_resource135 import consume_mixed_resource135,validate_mixed_resource135
from core_spec.resource_player_update135 import prepare_resource_player_update135
from core_spec.opening_entities135 import packed_guid
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def recalc_level(level,context):
    stats=StatsInput(level=level.progression.level,**asdict(level.stats),**level.sources.keywords());result=recalculate(stats);d={int(k):v for k,v in result['derived_bits'].items()};a=result['auxiliary_bits'];fields=dict(level.player_fields);fields.update({int(k):v for k,v in result['object_fields'].items()});packets=()
    if result['speed_changed']:
        packets=((226,(packed_guid(context.player_guid)+struct.pack('<II',context.action_sequence1644,result['speed_bits'])).hex()),)
        context=replace(context,action_sequence1644=(context.action_sequence1644+1)&f.MASK)
    level=replace(level,stats=replace(level.stats,old_max_hp_bits=d[1536],current_hp_bits=result['current_hp_bits'],previous_speed_bits=result['speed_bits'],pool1532_bits=a['1444'],pool1536_bits=a['1448'],conditional1348_bits=a['1348'],pool768_bits=a['768']),derived_bits=tuple(sorted(d.items())),player_fields=tuple(sorted(fields.items())))
    return level,context,packets


def corpus(full):
    rows,expected,labels=legacy.corpus(full)
    b=f.from_float;speed=(0,23451,b(10),0);berserk=(0,23505,b(15),0);battle=(8,6673,b(20),b(.2));protection=(12,1020,b(1),0)
    def add(group,definitions,operations,*,passive13=None,hp=.2,gate=0):
        live=legacy.live_vector(definitions)
        data=[list(row)for row in live.storage]
        for row,definition in zip(data,definitions):
            if definition[0]==12:row[:8]=[0]*8
        live=LiveVector135(tuple(tuple(row)for row in data),live.count)
        raw,level,context,state=legacy.initial(live,hp=hp,gate=gate)
        if passive13 is not None:
            # Explicit source-grant input before full1512 initialization. The
            # first original call must compute nonzero1620 from this8B source;
            # subsequent2088 starts with source/derived self-consistent.
            level=replace(level,sources=replace(level.sources,passives=(Modifier(13,b(passive13)),)))
            state['stats']['passives']=[dict(tag=13,value_bits=b(passive13))]
            raw['sources']['passives']=[dict(tag=13,value_bits=b(passive13))]
        packets=();notifications=();answers=[];metadata=[];ops=[]
        for operation,now,dt,last,kind in operations:
            nowbits=b(now);level=replace(level,stats=replace(level.stats,now_bits=nowbits));op=dict(operation=operation,now_bits=nowbits,dt_bits=b(dt),last_hit_bits=b(last),kind=kind);before1620=dict(level.derived_bits)[1620]
            if operation=='aura':
                aura=rebuild_resource_aura135(context.live.storage,context.live.count,nowbits,context.aura,level.player_fields);context=replace(context,aura=aura.aura);level=replace(level,player_fields=aura.player_fields);event=aura.events
            elif operation=='effect':
                result=consume_mixed_resource135(level,85,123,context,kind);level,context=result.level,result.context;packets+=result.packets;notifications+=result.notifications;event=result.events
            elif operation=='recalculate':
                level,context,extra=recalc_level(level,context);packets+=extra;event=(('full1512_initialization',),)
            else:
                assert operation=='player';result=prepare_resource_player_update135(level,context,nowbits,op['dt_bits'],op['last_hit_bits'],periodic_input=(),explicit_other_sources_absent=True);level,context=result.level,result.context;packets+=result.packets;event=result.events
            validate_mixed_resource135(level,context);answer=legacy.known(level,context,packets);answer['notifications_hex']=notifications
            answers.append(answer);ops.append(op);metadata.append(dict(operation=operation,before1620_bits=before1620,after1620_bits=dict(level.derived_bits)[1620],elapsed_bits=f.sub(nowbits,op['last_hit_bits']),events=event))
        i=len(rows);basic=replace(AbilityRecord(5467428),remaining_cooldown_bits=0x7f800000)
        rows.append(dict(id=i,state=state,level_input=raw,operations=ops,player_guid='42',unknown_poison=(0xa5,0x5a)[i&1],basic_hex=basic.to_bytes().hex(),pool756_bits=0));expected.append(dict(id=i,stages=answers));labels.append(dict(id=i,group=group,passive13_source='Explicit controlled8B tag13 input followed by originalfull1512; not natural talent/profile producer'if passive13 is not None else None,operations=metadata))
    aura_ops=[('aura',.999,0,0,0),('aura',1,0,0,0),('aura',10,0,0,0)]
    add('new1020-positive-Aura-order',(speed,protection,battle),aura_ops)
    add('new1020-prefix-strict1second',(speed,protection,battle,berserk),[('player',t,.1,0,0)for t in(.999,1,1.001,10,15,20)])
    add('new1020-consume-resource-then-expire',(protection,battle),[('effect',.2,0,0,3),('effect',.3,0,0,4),('effect',.4,0,0,5),('player',1,.1,0,0),('player',15.3,.1,0,0)])
    add('typedpassive13-full1512-before2088',(speed,protection,battle),[('recalculate',0,0,0,0),('player',1,1,-2,0)],passive13=.03)
    if not full:return rows,expected,labels
    for order in ((battle,protection,speed),(protection,speed,battle)):
        add('new1020-Aura-permuted',order,aura_ops)
        add('new1020-prefix-permuted',order+(berserk,),[('player',t,.1,0,0)for t in(.999,1,10,15,20)])
    add('new1020-consume-reverse-resource-order',(protection,),[('effect',.2,0,0,4),('effect',.3,0,0,3),('player',1,.1,0,0),('player',15.2,.1,0,0)])
    add('new1020-NaN-co-remove',((12,1020,0x7fc01234,0),speed),[('player',10,.1,0,0)])
    add('new1020-NaN-alone',((12,1020,0x7fc01234,0),),[('aura',1,0,0,0),('player',1,.1,0,0)])
    for since in(2.999,3,3.001):
        for gate in(0,5):
            for hp in(.2,.9999):
                add('typedpassive13-elapsed-gate-HPclamp',(speed,protection,battle),[('recalculate',0,0,0,0),('player',1,1,1-since,0)],passive13=.03,hp=hp,gate=gate)
    return rows,expected,labels


def refusal_checks():
    checks=legacy.refusal_checks();b=f.from_float
    for label,live in [('otherkind12',((12,7744,b(1),0),)),('duplicate1020',((12,1020,b(1),0),(12,1020,b(2),0)))]:
        try:legacy.initial(legacy.live_vector(live))
        except NotImplementedError as error:checks.append(dict(name=label,error=str(error)))
        else:raise AssertionError('Unknown protection source accepted')
    return checks

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    scripts=('check_self_buffs135.py','build_self_buffs135_oracle.py','run_self_buffs135_oracle.mjs','check_resource_player135.py','build_resource_player135_oracle.py','build_full135_oracle.py','build_upgrade134_oracle.py','production_closure135.py','source_closure137.py')
    files=tuple('scripts/'+n for n in scripts)+production_sources135(ROOT,'core_spec.resource_player_update135')
    edges=verify_local_source_closure(files);before={n:sha(ROOT/n)for n in files};rows,expected,labels=corpus(args.phase=='full');refusals=refusal_checks()
    out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('self-buffs0135-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest=build(out)
    for n,h in before.items():
        p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    for n,v in(('input.json',rows),('expected.json',expected),('labels.json',labels),('refusals.json',refusals)):save(out/n,v)
    assert all((out/n).stat().st_size<=4194304 for n in('input.json','expected.json'))
    artifacts={n:sha(out/n)for n in('input.json','expected.json','labels.json','refusals.json','manifest.json',manifest['module_file'])}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_self_buffs135_oracle.mjs'),str(out),str(out/'input.json')]
    save(out/'prepared.json',dict(source_sha256=before,local_source_import_edges=edges,artifacts=artifacts,expected_before_original=True,command=command,deadline_seconds=60))
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA;began=time.monotonic();error=None
    def stop(sig,frame):raise KeyboardInterrupt('Owned resource player stop '+str(sig))
    old=signal.signal(signal.SIGTERM,stop)
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=60))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as exc:error=repr(exc)
        finally:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,old)
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,error=error)
    save(out/'process-terminal.json',terminal);errors=[];counts=Counter();runtime=None
    if child.returncode==0:
        actual=[json.loads(l)for l in(out/'stdout.jsonl').read_text().splitlines()];errors,counts=legacy.compare(expected,actual,rows)
    if(out/'self-buffs135-runtime.json').exists():runtime=json.loads((out/'self-buffs135-runtime.json').read_text())
    after={n:sha(ROOT/n)for n in files};save(out/'differences.json',errors)
    receipt=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',original_sha256=SOURCE_SHA,cases=len(rows),operations=sum(len(r['operations'])for r in rows),full_original_roles=runtime['full_original_calls']if runtime else None,comparison_complete=child.returncode==0,differences=len(errors)if child.returncode==0 else None,comparison=dict(counts),pure_model_refusals=refusals,groups=dict(Counter(row['group']for row in labels)),source_files=len(files),local_source_import_edges=edges,source_sha256_before=before,source_sha256_after=after,source_unchanged=before==after,frozen_artifacts=artifacts,artifacts_unchanged=all(sha(out/n)==h for n,h in artifacts.items()),expected_before_original=True,process=terminal,runtime=runtime,scope='Complete1512/1202/10298/2088; original0/8 corpus regenerated fresh and new0/8/1020 coexistence,fullbacking,None,48Aura,resourcewire/JSON/regen; controlledtypedpassive13 initialization distinct from natural grant producer',observations_not_predictions=['1453 account/presentation/statistics payload','FullGame8192 and allocator/BTree/queue addresses'],full880_frames=0,complete_games=0,native_executions=0,pending=['1076 actual owned/basic/racial scheduling','Otherkind12 and live/periodic/shield/proc/aura source families','Natural talent/profile grant producer of passive13; this batch only typed input consumer','Full1453 healaccount logging','CompleteGame/mainloop/native'])
    save(out/'comparison.json',receipt);print(json.dumps(dict(directory=str(out),cases=len(rows),operations=receipt['operations'],differences=receipt['differences'],first_errors=errors[:6],process=terminal,receipt_sha256=sha(out/'comparison.json'))))
    if child.returncode or errors or error or not terminal['pid_missing']or not terminal['pgid_missing']or not receipt['source_unchanged']or not receipt['artifacts_unchanged']:raise SystemExit(1)
    assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']
if __name__=='__main__':main()
