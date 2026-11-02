#!/usr/bin/env python3
"""Fixed139 expected-first nonlethal913 numeric+full432B preservation check."""
from pathlib import Path
from datetime import datetime,timezone
from dataclasses import asdict,replace
from collections import Counter
import argparse,hashlib,json,os,random,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from build_combat139_oracle import ROOT,SOURCE,SOURCE_SHA,PROFILE,build,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.combat139 import DamageState139,EmptyDamageSources139,resolve_damage139,PendingDamage139
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node';NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'

def unit(guid=1,hp=1000000,*,definition=0,overrides=None):
    row=bytearray(432);struct.pack_into('<Q',row,112,guid)
    for offset,value in ((40,f.MASK),(64,f.MASK),(244,f.MASK),(284,definition),(288,f.from_float(hp)),(292,f.from_float(1000000)),(4,f.from_float(123))):struct.pack_into('<I',row,offset,value)
    row[429:432]=b'\xa5\x69\xcc'
    for offset,value in(overrides or{}).items():struct.pack_into('<I',row,int(offset),value)
    return bytes(row)

def corpus(manifest,phase):
    rows=[];labels=[];expected=[];pointer=manifest['npc_definition']['pointer']
    def add(group,*,records=None,amount=10,amount_bits=None,phase2587=1,now=10,school=0,critical=0,target=1,total=0.,repeat=1):
        records=records if records is not None else(unit(definition=pointer),)
        s=DamageState139(tuple(records),f.from_float(now),phase2587,struct.unpack('<Q',struct.pack('<d',total))[0],(1,2,3,4),EmptyDamageSources139((),(),(),True))
        state=dict(units432_hex=[x.hex()for x in s.units432],now_bits=s.now_bits,phase2587=s.phase2587,accounted_total_bits=str(s.accounted_total_bits),rng_words=list(s.rng_words),sources=asdict(s.sources))
        ops=[];answers=[]
        for j in range(repeat):
            op=dict(target_id=str(target),amount_bits=f.from_float(amount)if amount_bits is None else amount_bits,spell_id=0 if j%2 else 133,school=school,critical=critical,context=0)
            result=resolve_damage139(s,target,op['amount_bits'],spell_id=op['spell_id'],school=school,critical=critical);s=result.state
            ops.append(op);answers.append(dict(units432_hex=[x.hex()for x in s.units432],accounted_total_bits=str(s.accounted_total_bits),rng_words=list(s.rng_words)))
        rows.append(dict(id=len(rows),state=state,operations=ops));expected.append(dict(id=len(expected),answers=answers));labels.append(dict(id=len(labels),group=group))
    add('pilot139-real913-ordinary-nonlethal')
    add('pilot139-432stride-second-GUID',records=(unit(7,definition=pointer),unit(1,definition=pointer)),repeat=2)
    add('pilot139-new-school372-bonus',records=(unit(definition=pointer,overrides={372:f.from_float(11)}),),school=2)
    add('pilot139-phase-gate-keeps-full-record',phase2587=0)
    if phase=='pilot':return rows,expected,labels
    for amount in (0,-0.,-3,1e-35,.5,1,1.25,9.5,100,10000):add('minimum1-and-f32-f64-accounting',amount=amount,total=16777217.,repeat=3)
    for amount in (0x7fc01234,0xffc01234):add('NaN-amount-minimum1',amount_bits=amount)
    for hp in (1.25,1.5,3,1000000):add('finite-nonlethal-lowHP',records=(unit(hp=hp,definition=pointer),),amount=0)
    for marker in (1,2,255):add('marker1-reject-othermarkers-accept',records=(unit(definition=pointer,overrides={0:marker}),))
    for phasebyte in (0,2,3,255):add('nonrunning-full-byte-gate',phase2587=phasebyte)
    add('target-absent-does-not-write',target=99)
    for school in (0,1,2,3,4,128,255):
        for until in (9.999,10,10.001):add('139-school-bitmask-and-U372-strict-gate',records=(unit(definition=pointer,overrides={372:f.from_float(until)}),),school=school)
    for k in range(24):
        rng=random.Random(0x137913+k);values={144:f.from_float(rng.uniform(-.3,.7)),148:f.from_float((9,10,11)[k%3]),
            152:f.from_float(rng.uniform(-.2,.8)),156:f.from_float((9,10,11)[(k//3)%3]),
            160:f.from_float(.25),164:f.from_float((9,10,11)[(k//9)%3]),368:f.from_float(rng.uniform(-.2,.4)),
            124:f.from_float(11),388:f.from_float(11),396:f.from_float(11)}
        add('ordered-status-additives-and-empty-item-controls',records=(unit(definition=pointer,overrides=values),),amount=rng.uniform(-5,500),critical=k%2,repeat=2)
    for off in (416,420):
        for until in (9.999,10,10.001):add('139-moved-phase-gates-432record',records=(unit(definition=pointer,overrides={64:0,off:f.from_float(until)}),),school=2)
    protector=bytearray(unit(2,definition=pointer,overrides={40:2}));struct.pack_into('<Q',protector,32,1)
    add('kind2-link-quarter-phase',records=(unit(definition=pointer,overrides={64:0}),bytes(protector)))
    return rows,expected,labels

def negative_model_guards(manifest):
    """Boundaries are model checks, never added to original acceptance counts."""
    s=DamageState139((unit(definition=manifest['npc_definition']['pointer']),),f.from_float(10),1,0,(1,2,3,4),EmptyDamageSources139((),(),(),True));rows=[]
    for name,action in (
        ('nonzero_context',lambda:resolve_damage139(s,1,f.from_float(10),context=1)),
        ('lethal',lambda:resolve_damage139(s,1,f.from_float(2000000))),
        ('nonempty1972',lambda:EmptyDamageSources139((),(),(b'unknown-proc',),True)),
        ('nonempty_items',lambda:EmptyDamageSources139((b'unknown-item',),(),(),True)),
        ('nonempty_spells',lambda:EmptyDamageSources139((),(b'unknown-spell',),(),True)),
        ('duplicate_GUID',lambda:replace(s,units432=(s.units432[0],s.units432[0]))),
        ('boss_header',lambda:resolve_damage139(replace(s,units432=(unit(definition=manifest['npc_definition']['pointer'],overrides={244:0}),)),1,f.from_float(10))),
        ('kind3',lambda:resolve_damage139(replace(s,units432=(unit(definition=manifest['npc_definition']['pointer'],overrides={40:3}),)),1,f.from_float(10)))):
        try:action()
        except PendingDamage139 as error:rows.append(dict(case=name,error=str(error)))
        else:raise AssertionError('Unsupported source was silently admitted: '+name)
    return rows

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    files=('scripts/check_combat139.py','scripts/build_combat139_oracle.py','scripts/run_combat139_oracle.mjs','scripts/wasm139_profile.py',
        'scripts/wasm134_profile.py','scripts/wasm_index.py','scripts/production_closure135.py','scripts/source_closure137.py')+production_sources135(ROOT,'core_spec.combat139')
    edges=verify_local_source_closure(files)
    before={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('combat0139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir()
    manifest=build(out);rows,expected,labels=corpus(manifest,args.phase);rejections=negative_model_guards(manifest)
    for name in files:
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==before[name]
    save(out/'input.json',rows);save(out/'expected.json',expected);save(out/'labels.json',labels)
    save(out/'negative-model-guards.json',rejections)
    artifacts={n:sha(out/n)for n in('input.json','expected.json','labels.json','manifest.json',manifest['module_file'],'913.wat','role-binding.json','numeric-static-contract.json','negative-model-guards.json')}
    assert all((out/n).stat().st_size<=4194304 for n in ('input.json','expected.json'))
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_combat139_oracle.mjs'),str(out),str(out/'input.json')]
    save(out/'prepared.json',dict(original_sha256=SOURCE_SHA,source_closure=before,artifacts=artifacts,cases=len(rows),calls=sum(len(x['operations'])for x in rows),entry=manifest['entry'],command=command,
        expected_before_original=True,budgets=dict(memory_mib=32,heap_mib=512,io_bytes=4194304,deadline_seconds=60,denied_imports=882)))
    if args.prepare_only:print(json.dumps(dict(directory=str(out),cases=len(rows),calls=sum(len(x['operations'])for x in rows),target_executed=False,prepared_sha256=sha(out/'prepared.json'))));return
    assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA
    began=time.monotonic();launcher_error=None
    def interrupted(sig,frame):raise KeyboardInterrupt('Owned139 signal '+str(sig))
    previous=signal.signal(signal.SIGTERM,interrupted)
    with(out/'stdout.jsonl').open('wb')as stdout,(out/'stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command))
        try:child.wait(timeout=60)
        except(subprocess.TimeoutExpired,KeyboardInterrupt,OSError)as error:launcher_error=str(error)
        finally:
            try:os.killpg(child.pid,signal.SIGTERM)
            except ProcessLookupError:pass
            try:child.wait(timeout=2)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            signal.signal(signal.SIGTERM,previous)
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,pid_missing=missing(),pgid_missing=missing(True),seconds=time.monotonic()-began,launcher_error=launcher_error);save(out/'process-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];errors=[];runtime=None
    if child.returncode==0:
        assert len(actual)==len(expected)
        errors=[dict(id=w['id'],expected=w,actual=a)for w,a in zip(expected,actual)if w!=a]
        observations=[json.loads(x)for x in(out/'raw-games.jsonl').read_text().splitlines()]
        assert len(observations)==sum(len(c['operations'])for c in rows)
        at=0
        for case,answer in zip(rows,actual):
            for operation,value in enumerate(answer['answers']):
                seen=observations[at];at+=1;assert(seen['case_id'],seen['operation'])==(case['id'],operation)
                game=bytes.fromhex(seen['raw_game8192_hex']);assert len(game)==8192
                assert struct.unpack_from('<Q',game,984)[0]==int(value['accounted_total_bits'])
                assert list(struct.unpack_from('<4I',game,1720))==value['rng_words']
                assert struct.unpack_from('<III',game,1784)==(len(case['state']['units432_hex']),seen['unit_pointer'],len(case['state']['units432_hex']))
                assert game[2587]==case['state']['phase2587']and struct.unpack_from('<I',game,2352)[0]==case['state']['now_bits']
                assert struct.unpack_from('<I',game,1972)[0]==0
        runtime=json.loads((out/'runtime.json').read_text());assert runtime['actual_host_calls']==0 and runtime['stack_all_restored']is True and runtime['full_original913_calls']==sum(len(x['operations'])for x in rows)
    assert (out/'stdout.jsonl').stat().st_size<=4194304 and (out/'raw-games.jsonl').stat().st_size<=4194304
    after={n:sha(ROOT/n)for n in files};assert before==after and artifacts=={n:sha(out/n)for n in artifacts};assert sha(NODE)==NODE_SHA and sha(SOURCE)==SOURCE_SHA
    save(out/'differences.json',errors);receipt=dict(version='0.139.0',build='f79c5e2b4',cases=len(rows),calls=sum(len(x['operations'])for x in rows),complete=child.returncode==0 and launcher_error is None,
        mismatch_cases=len(errors),source_before=before,source_after=after,source_unchanged=True,source_import_edges=edges,negative_model_guards=len(rejections),negative_guards_are_not_original_cases=True,artifacts=artifacts,process=terminal,runtime=runtime,expected_before_original=True,
        output_sha256=sha(out/'stdout.jsonl'),raw_game_observations_sha256=sha(out/'raw-games.jsonl'),raw_game_observations_bytes=(out/'raw-games.jsonl').stat().st_size,stderr_sha256=sha(out/'stderr.log'),groups=dict(Counter(x['group']for x in labels)),
        Windows_native_executed=False,full_game_frames=0,limitations=['Only nonlethal/no-proc numeric432B projection; full original913 and its actual callees unchanged.',
        'Full8192B Game per call is raw observation; per-spell statistics/packet/visual allocations are not independently predicted.',
        'Controlled all-known432B inputs are not139 constructor outputs;7 kind64=0/U68=0 fixtures only exercise numeric phase branches without timer ownership consumption.',
        'Death/XP/loot/nonempty1972/unknown new proc producers and Windows gameplay ABI/runtime remain pending; no135/136/137/138 cases transferred. Controlled stimuli are reused but every expected and original139 call is fresh.'])
    save(out/'comparison.json',receipt);print(json.dumps(dict(directory=str(out),cases=len(rows),calls=receipt['calls'],mismatches=len(errors),first_ids=[x['id']for x in errors[:8]],process=terminal,comparison_sha256=sha(out/'comparison.json'))))
    if errors or child.returncode or launcher_error or not terminal['pid_missing']or not terminal['pgid_missing']:raise SystemExit(1)

if __name__=='__main__':main()
