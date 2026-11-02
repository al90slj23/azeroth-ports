#!/usr/bin/env python3
"""Expected-first first2372 notice→allfour due20Guardians→active continuation."""
from pathlib import Path
from dataclasses import replace,asdict
from collections import Counter
from datetime import datetime,timezone
import argparse,ast,json,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_special_world139_oracle import ROOT,SOURCE,SOURCE_SHA,sha,save,build
from check_player_update139 import load_world139,WORLD,WORLD_SHA,CONTEXT,CONTEXT_SHA,RANGES,RANGES_SHA,GATE,GATE_SHA,NODE,NODE_SHA
from check_natural_run139 import stage_projection
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.natural_run139 import prepare_natural_run139,_incoming,_adopt_player
from core_spec.enemy_ai_dead139 import PhysicalNPCVector139
from core_spec.special_world139 import from_opening_special139,update_special_world139
from core_spec.special_world139_data import SPECIAL_DECLARATIONS139,ZONE136_BITS,FIRST_MILESTONE139


def closure():
    names=set(production_sources135(ROOT,'core_spec.special_world139','core_spec.natural_run139'))
    names.update('scripts/'+n for n in('check_special_world139.py','build_special_world139_oracle.py','trace_special_world139.py','run_special_world139_oracle.mjs','check_natural_run139.py','check_player_update139.py','check_asset_world139.py','production_closure135.py','source_closure137.py'))
    while True:
        try:return sorted(names),verify_local_source_closure(sorted(names))
        except AssertionError as e:
            pair=e.args[0];assert isinstance(pair,tuple)and len(pair)==2 and pair[1]not in names;names.add(pair[1])


def special_projection(s):
    return dict(special40_storage=[list(r)for r in s.special40_storage],special_count=s.special_count,selected392=s.selected392,target396=s.target396,announced2565=s.announced2565,stamp2392_bits=s.stamp2392_bits,navigation2564=s.navigation2564,protection2576=s.protection2576,timers=[dict(unit_slot=t.unit_slot,guid=str(t.guid),capacity=t.capacity,count=len(t.timers_bits),timers_bits=list(t.timers_bits),header_pointer=t.header_pointer,ability_pointer=t.ability_pointer)for t in s.timer_owners])


def corpus(world,phase):
    rows=[]
    for seed in([0]if phase=='pilot'else[0,1,5]):
        opening,run=prepare_natural_run139(seed,world);s=from_opening_special139(opening);inputs=[];stages=[]
        for now,follow in[(.1,None),(19.9,None),(20.,None),(20.1,None),(30.1,1)]:
            xyz=run.actor.player.player_xyz
            if follow is not None:xyz=tuple(int.from_bytes(bytes(s.special40_storage[follow][16+4*j:20+4*j]),'little')for j in range(3))
            s=replace(s,now_bits=f.from_float(now),player_xyz=xyz)
            p=replace(run.actor.player,growth=replace(run.actor.player.growth,now_bits=s.now_bits),player_xyz=xyz)
            actor=_adopt_player(run.actor,p,run.units);run=replace(run,actor=actor,incoming=_incoming(run.incoming,p,run.units))
            before=stage_projection(run);before_special=special_projection(s);result=update_special_world139(s);s=result.state
            units=PhysicalNPCVector139(s.units432_storage,s.units_count)
            p=replace(p,growth=replace(p.growth,units432_cells=units.active,rng_words=s.rng_words))
            actor=_adopt_player(actor,p,units);actor=replace(actor,damage=replace(actor.damage,counter2408=s.counter2408))
            run=replace(run,actor=actor,units=units,incoming=_incoming(run.incoming,p,units))
            inputs.append(dict(now_bits=s.now_bits,player_xyz=xyz,follow_special_index=follow))
            stages.append(dict(before=before,before_special=before_special,after=stage_projection(run),special=special_projection(s),packets=result.packets,creates=result.creates,rng_draws=result.rng_draws))
        rows.append(dict(id=len(rows),input=dict(id=len(rows),app_seed_u64=str(seed),steps=inputs),stages=stages))
    return json.loads(json.dumps(rows))


def missing(pid,group=False):
    try:(os.killpg if group else os.kill)(pid,0)
    except ProcessLookupError:return True
    return False


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--phase',choices=('pilot','full'),default='pilot');args=ap.parse_args();files,edges=closure();sources={n:sha(ROOT/n)for n in files};opened=[];forbidden=[];active=True
    def audit(event,values):
        if active and event=='open'and isinstance(values[0],(str,bytes,os.PathLike)):
            p=Path(os.fsdecode(values[0])).resolve();opened.append(str(p))
            if p.suffix.lower()in('.wasm','.wat','.memory','.exe')or'/originals/'in str(p):forbidden.append(str(p));raise RuntimeError('Original reads denied in model')
    sys.addaudithook(audit)
    try:world,*_=load_world139(WORLD);rows=corpus(world,args.phase)
    finally:active=False
    assert not forbidden and sources=={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('special-world139-'+args.phase+'-%Y%m%dT%H%M%S.%fZ');out.mkdir();m=build(out)
    assert json.loads(json.dumps(SPECIAL_DECLARATIONS139))==json.loads(json.dumps(m['special_trace']['declarations']))and ZONE136_BITS==m['special_trace']['zone136_bits']and list(FIRST_MILESTONE139)==m['special_trace']['first_milestone']
    for p,h in((SOURCE,SOURCE_SHA),(NODE,NODE_SHA),(CONTEXT,CONTEXT_SHA),(RANGES,RANGES_SHA),(GATE,GATE_SHA),(WORLD/'receipt.json',WORLD_SHA)):assert sha(p)==h
    for n,h in sources.items():p=out/'source-snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes());assert sha(p)==h
    save(out/'inputs.json',[r['input']for r in rows]);save(out/'expected.json',rows);save(out/'expectation-read-audit.json',dict(opened=opened,forbidden=forbidden))
    save(out/'config.json',dict(input_file=str(out/'inputs.json'),input_sha256=sha(out/'inputs.json'),snapshot_file=str(CONTEXT),snapshot_sha256=CONTEXT_SHA,range_file=str(RANGES),range_sha256=RANGES_SHA,world_rc=20544696))
    frozen={n:sha(out/n)for n in('inputs.json','expected.json','manifest.json',m['module_file'],'config.json','expectation-read-audit.json')};save(out/'prepared.json',dict(sources=sources,source_import_edges=edges,frozen=frozen,expected_before_original=True,original_input_contains_expected=False))
    argv=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts/run_special_world139_oracle.mjs'),str(out),str(out/'config.json')];start=time.monotonic()
    with(out/'actual.jsonl').open('w')as so,(out/'stderr.log').open('w')as se:
        child=subprocess.Popen(argv,stdout=so,stderr=se,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=argv,deadline_seconds=120))
        try:code=child.wait(timeout=120)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(child.pid),pgid_missing=missing(child.pid,True));save(out/'owned-terminal.json',terminal);actual=[json.loads(x)for x in(out/'actual.jsonl').read_text().splitlines()];counts=Counter();differences=[]
    def eq(cid,label,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(differences)<100:differences.append(dict(id=cid,field=label,expected=want,actual=got))
    def cells(cid,label,want,got):
        eq(cid,label+'.capacity',len(want),len(got))
        for row,hx in zip(want,got):
            raw=bytes.fromhex(hx);eq(cid,label+'.width',len(row),len(raw))
            for o,(v,b)in enumerate(zip(row,raw)):
                if v is None:counts[label+'_None']+=1;counts[label+'_nonzero_None']+=bool(b)
                else:eq(cid,label+'+'+str(o),v,b);counts[label+'_known']+=1
    allowed=set(range(392,400))|set(range(1720,1736))|set(range(1784,1796))|set(range(1880,1892))|set(range(2392,2396))|set(range(2408,2412))|{2565}
    for E,A in zip(rows,actual):
        cid=E['id'];eq(cid,'id',cid,A['id']);eq(cid,'stagecount',len(E['stages']),len(A['stages']));initial=A['initial'];previous=initial
        for i,(W,O)in enumerate(zip(E['stages'],A['stages'])):
            control=E['input']['steps'][i];raw=bytearray.fromhex(previous['capture']['raw_game2592_hex']);struct.pack_into('<I',raw,2352,control['now_bits']);struct.pack_into('<3I',raw,1416,*control['player_xyz']);eq(cid,f'{i}.only_clock_and_player',raw.hex(),O['before']['capture']['raw_game2592_hex'])
            eq(cid,f'{i}.growth',W['after']['player']['growth'],O['after']['capture']['projection'])
            for key in('scalar','racial80_hex','source_flags','spell_sets','live','aura'):eq(cid,f'{i}.preserved_player.'+key,O['before'][key],O['after'][key])
            for key in('selected392','target396','announced2565','stamp2392_bits','navigation2564','protection2576'):
                want=W['special'][key]
                if want is None:eq(cid,f'{i}.unknown_target396_preserved',O['before_special'][key],O['special'][key])
                else:eq(cid,f'{i}.special.'+key,want,O['special'][key])
            cells(cid,'special40',W['special']['special40_storage'],O['after']['capture']['background']['special']['storage']);eq(cid,f'{i}.special_count',W['special']['special_count'],O['after']['capture']['background']['special']['count'])
            for slot,(model,oldhx,newhx)in enumerate(zip(W['special']['special40_storage'],O['before']['capture']['background']['special']['storage'],O['after']['capture']['background']['special']['storage'])):
                beforebytes=bytes.fromhex(oldhx);afterbytes=bytes.fromhex(newhx)
                for at,value in enumerate(model):
                    if value is None:eq(cid,f'{i}.unwritten_special{slot}+{at}',beforebytes[at],afterbytes[at]);counts['special_unknown_copy_bytes']+=1
            eq(cid,f'{i}.units_count',W['after']['physical_NPC_count'],O['after']['capture']['background']['units']['count']);cells(cid,'units432',W['after']['physical_NPC_storage'],O['after']['capture']['background']['units']['storage'])
            for key in('counter2408','movement_sequence2412'):eq(cid,f'{i}.'+key,W['after']['combat'][key],O['combat'][key])
            eq(cid,f'{i}.timer_owners',W['special']['timers'],O['special']['timers'])
            eq(cid,f'{i}.complete_packets',[[op,hx]for op,cap,hx in W['packets']],O['new_packets'])
            eq(cid,f'{i}.notice_payload_capacities',[cap for op,cap,hx in W['packets']if op==548],[v['capacity']for v in O['packet_details']if v['opcode']==548])
            old=O['before']['capture']['background']['units'];new=O['after']['capture']['background']['units'];
            for j in range(old['count']):eq(cid,f'{i}.existing_unit'+str(j),old['storage'][j],new['storage'][j]);counts['existing_NPC_bytes_conserved']+=432
            for key in('auxiliary','claims','pickups','windows','boundaries'):eq(cid,f'{i}.background.'+key,O['before']['capture']['background'][key],O['after']['capture']['background'][key])
            for at,(before,after)in enumerate(zip(bytes.fromhex(O['before']['capture']['raw_game2592_hex']),bytes.fromhex(O['after']['capture']['raw_game2592_hex']))):
                if at not in allowed:eq(cid,f'{i}.unowned_Game'+str(at),before,after);counts['Game_unowned_bytes_conserved']+=1
            counts['full2372']+=1;counts['Guardian_creates']+=len(W['creates']);counts['known_packets']+=len(W['packets']);counts['known_packet_bytes']+=sum(len(hx)//2 for op,cap,hx in W['packets']);counts['RNG_draws']+=W['rng_draws'];previous=O['after']
    runtime=json.loads((out/'runtime.json').read_text())if(out/'runtime.json').exists()else None
    assert sources=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen};save(out/'differences.json',differences)
    comparison=dict(version='0.139.0',build='f79c5e2b4',phase=args.phase,cases=len(rows),completed_cases=len(actual),differences=counts['differences'],counts=dict(counts),sources_before=sources,sources_after=sources,source_import_edges=edges,frozen=frozen,runtime=runtime,process=terminal,expected_before_original=True,original_input_contains_expected=False,forbidden_model_reads=forbidden,fullmain_frames=0,complete_games=0,limits=['Controlledclock sequence to30.1 and oneplayerfollow;notnatural30seconds/mainframe.','Complete2372 firstdue20/4Guardian source only;noGuardianAI/skills/death,nondefaultscaling,respawn150beyond21.','Timerheap pointerNonewithlogical3timerowner;staticheader/abilitypointersbound,physicalallocationpointernotpredicted.'])
    save(out/'comparison.json',comparison);print(json.dumps(dict(directory=str(out),sha256=sha(out/'comparison.json'),differences=counts['differences'],counts=dict(counts),first=differences[:3],process=terminal)),flush=True)
    if code or len(actual)!=len(rows)or counts['differences']:raise SystemExit(1)


if __name__=='__main__':main()
