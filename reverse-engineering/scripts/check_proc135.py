#!/usr/bin/env python3
"""New full984/8157 and actual nonempty914/cast state comparisons."""
import argparse,json,os,signal,struct,subprocess,sys,time
from dataclasses import asdict,replace
from collections import Counter
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA,build
from build_upgrade134_oracle import sha
FILES=('scripts/check_owned_cast135.py', 'scripts/run_owned_cast135_oracle.mjs', 'reconstruction/core_spec/__init__.py', 'reconstruction/core_spec/cast_events135.py', 'reconstruction/core_spec/owned_cast135.py', 'reconstruction/core_spec/owned_prelude135.py', 'scripts/check_death_pickup135.py', 'scripts/run_death_pickup135_oracle.mjs', 'scripts/check_level_cycle135.py', 'scripts/check_cast135_full_spec.py', 'scripts/build_full135_oracle.py', 'scripts/full135_host.mjs', 'scripts/build_upgrade134_oracle.py', 'reconstruction/core_spec/death_pickup135.py', 'reconstruction/core_spec/death_loot134.py', 'reconstruction/core_spec/pickups134.py', 'reconstruction/core_spec/pickup_entity134.py', 'reconstruction/core_spec/currency134.py', 'reconstruction/core_spec/cast135.py', 'reconstruction/core_spec/combat135.py', 'reconstruction/core_spec/combat134.py', 'reconstruction/core_spec/level_cycle135.py', 'reconstruction/core_spec/derived_stats135.py', 'reconstruction/core_spec/derived_stats134.py', 'reconstruction/core_spec/progression134.py', 'reconstruction/core_spec/progression.py', 'reconstruction/core_spec/candidates135.py', 'reconstruction/core_spec/ability_state.py', 'reconstruction/core_spec/upgrade_values.py', 'reconstruction/core_spec/binary32.py', 'reconstruction/core_spec/binary32_sqrt.py', 'reconstruction/core_spec/radius.py', 'reconstruction/core_spec/rng.py', 'reconstruction/core_spec/proc_events135.py', 'scripts/check_proc135.py', 'scripts/run_proc135_oracle.mjs')
IMPORT_SHA={n:sha(ROOT/n)for n in FILES}
from check_cast135_full_spec import state_from_input
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.level_cycle135 import from_dict
from core_spec.derived_stats135 import TimedRecord,Modifier
from core_spec.proc_events135 import ProcDefinition135,ProcState135,ProcEvent135,UnresolvedProc135,dispatch_event,zero_gate_matches,after_accepted_damage
from core_spec.cast135 import CastDefinition
from core_spec.cast_events135 import cast_ability
from core_spec.ability_state import AbilityRecord
from core_spec.combat135 import CombatState,UnitState,resolve_damage
OLD_INPUT=ROOT/'evidence/full0135-oracle-20261101T044512.860275Z/death-pickup135-fixtures.jsonl'
OLD_SHA='1e31801aa86e2e312e2deca24786f7f535560e215148b9b41c540d5ac762e0ca'
RUNTIME=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
RUNTIME_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def complete(raw):
    return ProcDefinition135((raw.kind,raw.value4_bits,0,0,0,raw.value20_bits,0,0,raw.modifier_tag))


def snapshot(proc,combat,rng):
    level=proc.level;s=level.stats
    return dict(derived_bits={str(k):v for k,v in level.derived_bits},current_hp_bits=s.current_hp_bits,
        auxiliary_bits={str(k):v for k,v in((1444,s.pool1532_bits),(1448,s.pool1536_bits),(1348,s.conditional1348_bits),(768,s.pool768_bits),(756,level.pool756_bits))},
        speed_bits=s.previous_speed_bits,player_fields={str(k):v for k,v in level.player_fields},
        timed_words=[[x.definition_index,x.stack_count,x.expires_bits]for x in level.sources.timed_records],
        definitions36=[x.hex()for x in proc.definitions],unit_hp_bits=[x.hp_bits for x in combat.units],markers=[x.marker for x in combat.units],
        accounted_total_hex=struct.pack('>d',combat.accounted_total).hex(),rng_words=list(rng))


def event(category=0,flag=0):
    raw=bytearray(36);raw[29]=category;raw[34]=flag;return ProcEvent135(raw.hex())


def corpus(pilot):
    old=[json.loads(x)for x in OLD_INPUT.read_text().splitlines()];rows=[];base=old[0]['level'];b=f.from_float
    for c in old:
        level=from_dict(c['level']);proc=ProcState135(level,tuple(complete(x)for x in level.sources.definitions),True)
        cast=state_from_input(c['cast']);definition=CastDefinition(**dict(c['definition'],ability_id=c['definition']['ability_id'].encode()));stages=[]
        def hit(state,damage):
            nonlocal proc
            proc=after_accepted_damage(proc,damage.damage_bits,context774=0,nonfatal=not damage.dead).state;return state
        for op in c['ops']:
            if op['kind']=='cast':cast=cast_ability(cast,definition,AbilityRecord.from_bytes(bytes.fromhex(c['owned_hex'])),after_hit=hit).state
            elif op['kind']!='collect':raise ValueError('Unexpected retained negative operation')
            stages.append(snapshot(proc,cast.combat,cast.rng_words))
        rows.append(dict(id=len(rows),kind='cast',group='all12-retained-pending-nonempty-definitions',old_id=c['id'],level=c['level'],
            definitions36=[x.hex()for x in proc.definitions],cast=c['cast'],definition=c['definition'],definition_hex=c['definition_hex'],owned_hex=c['owned_hex'],ops=c['ops'],expected=stages))
    def add_event(group,timed,cap,duration,events=None,count=1):
        raw=json.loads(json.dumps(base));raw['sources']['timed_records']=[dict(definition_index=x[0],stack_count=x[1],expires_bits=x[2])for x in timed]
        raw['sources']['definitions']=[dict(kind=27,value4_bits=0,value20_bits=b(.07+j*.01),modifier_tag=14,summon_state41=0)for j in range(count)]
        level=from_dict(raw);defs=tuple(ProcDefinition135((27,0,0,0,0,b(.07+j*.01),cap,duration,14))for j in range(count));proc=ProcState135(level,defs,True)
        combat=CombatState((UnitState(1,b(1e6),b(1e6)),),now_bits=b(10));ops=[];expected=[]
        for e in(events or[event()]):
            proc=dispatch_event(proc,e).state;ops.append(dict(kind='event',now_bits=b(10),event_hex=e.raw_hex));expected.append(snapshot(proc,combat,level.rng_words))
        rows.append(dict(id=len(rows),kind='event',group=group,level=raw,definitions36=[x.hex()for x in defs],ops=ops,expected=expected))
    for cap in(0,3):
        for expires in(9,10,11):add_event('pilot-first-matching-update',[(0,3,b(expires)),(0,7,b(11)),(9,8,b(11))],cap,b(.5))
    add_event('pilot-append-no-cap',[],0,b(.5),events=[event(),event()])
    if pilot:return rows
    for category in range(256):
        for flag in(0,1):
            e=event(category,flag);rows.append(dict(id=len(rows),kind='gate',group='zero-gate-all-category-bytes',level=base,
                definitions36=[complete(from_dict(base).sources.definitions[0]).hex()],ops=[dict(kind='gate',now_bits=b(10),gate_hex=bytes(16).hex(),event_hex=e.raw_hex)],expected=[dict(matches=int(zero_gate_matches(e)))]))
    for expiry in(b(9),b(10),b(11),0x7fc00001):
        for stack in(0,1,3,0xffffffff):
            for cap in(0,1,3,0xffffffff):
                for duration in(b(0),b(.1),b(3),0x7fc00001):
                    add_event('ordered-stack-expiry-cap-wrap',[(0,stack,expiry),(0,7,b(12)),(9,8,b(11))],cap,duration)
    for cap in(0,1,3,0xffffffff):
        for duration in(0,b(-1),b(.1),b(3)):
            add_event('append-before-cap-next-event',[],cap,duration,events=[event(),event()])
    for count in(0,1,2,5):
        add_event('ordered-multiple-definitions',[(0,3,b(11)),(9,8,b(11))],3,b(.5),count=count)
    for cap in(0,1,3,0xffffffff):
        for duration in(0,b(.1),b(3)):
            for present in(False,True):
                for cls in(1,8):
                    raw=json.loads(json.dumps(base));raw['stats']['class_byte']=cls
                    raw['sources']['timed_records']=[dict(definition_index=0,stack_count=3,expires_bits=b(11))]if present else[]
                    level=from_dict(raw);definition=ProcDefinition135((27,0,0,0,0,b(.07),cap,duration,14));proc=ProcState135(level,(definition,),True)
                    combat=CombatState((UnitState(1,b(1e6),b(1e6)),),now_bits=b(10));ops=[];expected=[]
                    for j,amount in enumerate((0,-1,10)):
                        now=b(10+j*.05);combat=replace(combat,now_bits=now);proc=replace(proc,level=replace(proc.level,stats=replace(proc.level.stats,now_bits=now)))
                        damage=resolve_damage(combat,1,b(amount),spell_id=1680,spell_category=0);combat=damage.state;proc=after_accepted_damage(proc,damage.damage_bits,context774=0,nonfatal=not damage.dead).state
                        ops.append(dict(kind='damage',now_bits=now,target_id='1',amount_bits=b(amount),spell_id=1680));expected.append(snapshot(proc,combat,level.rng_words))
                    rows.append(dict(id=len(rows),kind='damage',group='actual914-source-mutation-before-next-hit',level=raw,definitions36=[definition.hex()],ops=ops,expected=expected))
    return rows


def boundary_cases():
    raw=json.loads(OLD_INPUT.read_text().splitlines()[0]);level=from_dict(raw['level']);definition=complete(level.sources.definitions[0]);base=ProcState135(level,(definition,),True);rows=[]
    def reject(name,call):
        try:call()
        except(UnresolvedProc135,ValueError,TypeError)as exc:rows.append(dict(case=name,rejected=True,reason=str(exc)))
        else:raise AssertionError('Unresolved proc source silently accepted: '+name)
    reject('other-source-absence-not-declared',lambda:ProcState135(level,(definition,),False))
    reject('other984-producer-kind',lambda:ProcDefinition135((22,0,0,0,0,0,0,0,0)))
    for offset in range(1,5):
        words=list(definition.words);words[offset]=1
        reject('nonzero8157-gate-word'+str(offset),lambda words=words:ProcDefinition135(tuple(words)))
    words=list(definition.words);words[8]=3;semantic=replace(level.sources.definitions[0],modifier_tag=3)
    other=ProcState135(replace(level,sources=replace(level.sources,definitions=(semantic,))),(ProcDefinition135(tuple(words)),),True)
    reject('callback-changing-cast-scalar-domain',lambda:after_accepted_damage(other,f.from_float(1),context774=0,nonfatal=True))
    other=replace(base,level=replace(level,sources=replace(level.sources,item_modifiers=(Modifier(28,f.from_float(.1)),))))
    reject('other-item-damage-producer',lambda:after_accepted_damage(other,f.from_float(1),context774=0,nonfatal=True))
    reject('raw-zero-before914-minimum',lambda:after_accepted_damage(base,0,context774=0,nonfatal=True))
    reject('raw-negative-before914-minimum',lambda:after_accepted_damage(base,f.from_float(-1),context774=0,nonfatal=True))
    reject('unknown-context774',lambda:after_accepted_damage(base,f.from_float(1),nonfatal=True))
    for context in(1,2,255):reject('nonzero-context774-'+str(context),lambda context=context:after_accepted_damage(base,f.from_float(1),context774=context,nonfatal=True))
    reject('unknown-nonfatal',lambda:after_accepted_damage(base,f.from_float(1),context774=0))
    reject('lethal-not-supported',lambda:after_accepted_damage(base,f.from_float(1),context774=0,nonfatal=False))
    return rows


def compare(e,a,path,failures):
    if type(e)is not type(a):failures.append((path,'type'));return
    if isinstance(e,dict):
        if e.keys()!=a.keys():failures.append((path,'keys'));return
        for k in e:compare(e[k],a[k],path+[k],failures)
    elif isinstance(e,list):
        if len(e)!=len(a):failures.append((path,'length'));return
        for j,(x,y)in enumerate(zip(e,a)):compare(x,y,path+[j],failures)
    elif e!=a:
        floating=(path[-1]in('current_hp_bits','speed_bits')or'derived_bits'in path and path[-1]not in('1592','1608')or'auxiliary_bits'in path or'unit_hp_bits'in path or'timed_words'in path and path[-1]==2)
        if not(floating and type(e)is int and f.is_nan(e)and f.is_nan(a)):failures.append((path,e,a))


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',choices=('pilot','full'),default='pilot');args=p.parse_args()
    before={n:sha(ROOT/n)for n in FILES};assert before==IMPORT_SHA;old_hash=sha(OLD_INPUT);assert old_hash==OLD_SHA
    rejected=boundary_cases();cases=corpus(args.phase=='pilot');out,manifest=build(['proc_event','proc_gate','damage','cast','collect_pickups']);snap=out/'source-snapshot';snap.mkdir()
    for name,value in before.items():
        q=snap/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/name).read_bytes());assert sha(q)==value
    fixture=out/'proc135-fixtures.jsonl';fixture.write_text(''.join(json.dumps(x,allow_nan=False)+'\n'for x in cases));assert[json.loads(x)for x in fixture.read_text().splitlines()]==cases
    frozen={q.name:sha(q)for q in(fixture,out/'manifest.json',out/manifest['module_file'])};assert sha(RUNTIME)==RUNTIME_SHA
    command=[str(RUNTIME),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_proc135_oracle.mjs'),str(out),str(fixture)]
    result=out/'proc135-results.jsonl';stderr=out/'proc135-stderr.log';start=time.monotonic()
    with result.open('w')as stdout,stderr.open('w')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True)
        try:code=child.wait(timeout=60)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();raise RuntimeError('Owned proc oracle exceeded60s')
    if code:raise RuntimeError(f'Proc original failed: {out}')
    actual=[json.loads(x)for x in result.read_text().splitlines()];assert[x['id']for x in actual]==list(range(len(cases)));failures=[]
    for c,a in zip(cases,actual):compare(c['expected'],a['stages'],[c['id']],failures)
    after={n:sha(ROOT/n)for n in FILES};assert before==after and sha(SOURCE)==SOURCE_SHA and sha(OLD_INPUT)==old_hash
    assert frozen=={q.name:sha(q)for q in(fixture,out/'manifest.json',out/manifest['module_file'])}
    (out/'proc135-mismatches.json').write_text(json.dumps(failures,indent=2)+'\n')
    (out/'proc135-rejected-sources.json').write_text(json.dumps(rejected,indent=2)+'\n')
    receipt=dict(version='0.135.1',build='0898d5e3',phase=args.phase,cases=len(cases),stages=sum(len(x['ops'])for x in cases),groups=dict(Counter(x['group']for x in cases)),kinds=dict(Counter(x['kind']for x in cases)),mismatch_fields=len(failures),rejected_source_cases=len(rejected),source_sha256_before=before,source_sha256_after=after,old_input_sha256=old_hash,original_sha256=SOURCE_SHA,module_sha256=manifest['module_sha256'],artifacts={q.name:sha(q)for q in(fixture,result,stderr,out/'manifest.json',out/'proc135-mismatches.json',out/'proc135-runtime.json',out/'proc135-rejected-sources.json')},runtime=json.loads((out/'proc135-runtime.json').read_text()),process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=code,deadline_seconds=60,seconds=time.monotonic()-start),independent_expected_before_original=True,only_changed_section=7,limitations=['Exact kind27 with zero16B gate,explicit nonfatal hit andcontext774==0; all other984 producers and gate families remain explicit unknowns.','Accepted-hit callback supports modifier14 plusitem14/adjustment18 only; other cast-loop stat reload behavior unresolved.','Physical vector capacity/allocation, metadata/packet bytes and complete game remain outside this source-payload projection.'])
    (out/'proc135-comparison.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(directory=str(out),cases=len(cases),mismatch_fields=len(failures),first_failures=failures[:5])))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
