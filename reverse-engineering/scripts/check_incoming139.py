#!/usr/bin/env python3
"""Expected-first current139 full1076 within an explicit nonfatal input domain."""
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,ast,json,math,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from production_closure135 import production_sources135
from source_closure137 import verify_local_source_closure
from build_incoming139_oracle import build
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.incoming139 import IncomingState139,Buff139,Modifier139,resolve_prefix139,resolve_source139
from core_spec.incoming_history139 import from_raw_storage,append_incoming_history,projection
NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'
SCALARS={1440:'hp1440_bits',1444:'shield1444_bits',1448:'barrier1448_bits',1344:'shield_source1344',1348:'shield_remaining1348_bits',764:'reserve764_bits',736:'absorbed736_bits',740:'maximum_shield740_bits',1652:'last_hit1652_bits'}

def source_files():
    files=set(production_sources135(ROOT,'core_spec.incoming139','core_spec.incoming_history139'))
    pending=['scripts/check_incoming139.py','scripts/run_incoming139_oracle.mjs','scripts/production_closure135.py','scripts/source_closure137.py','scripts/build_incoming139_oracle.py']
    while pending:
        name=pending.pop()
        if name in files:continue
        files.add(name)
        if not name.endswith('.py'):continue
        for node in ast.walk(ast.parse((ROOT/name).read_text())):
            names=[x.name for x in node.names]if isinstance(node,ast.Import)else[node.module or'']if isinstance(node,ast.ImportFrom)and not node.level else[]
            for module in names:
                path=ROOT/'scripts'/Path(*module.split('.')).with_suffix('.py')
                if path.is_file():pending.append(str(path.relative_to(ROOT)))
    result=tuple(sorted(files));return result,verify_local_source_closure(result)

def history_row(stamp,poison=0x5a):
    raw=bytearray([poison]*48)
    for o in(0,8,16):struct.pack_into('<II',raw,o,1,0)
    struct.pack_into('<I',raw,24,stamp)
    return raw.hex()

def npc(guid=101,rank=0,marker=0,x=0,y=0,start=None,duration=0,definition=5830904):
    raw=bytearray([0xa5]*432)
    for o,v in((0,marker),(40,f.MASK),(64,f.MASK),(244,f.MASK),(280,0),(284,definition),(416,0),(420,0)):
        struct.pack_into('<I',raw,o,v)
    struct.pack_into('<Q',raw,112,guid)
    sx,sy=x,y if start is None else start[1]
    if start is not None:sx,sy=start
    for o,v in((316,sx),(320,sy),(328,x),(332,y),(340,10),(344,duration)):
        struct.pack_into('<I',raw,o,f.from_float(v))
    raw[424]=rank;raw[425]=raw[426]=0
    return raw.hex()

def corpus(pilot=False):
    rows=[];b=f.from_float
    def op(amount=10,now=20,guid=0,contact=0,category=0):return dict(amount_bits=b(amount),now_bits=b(now),source_guid=str(guid),contact_flag=contact,category=category,spell_id=0)
    def add(group,*,records=(),history=None,ops=None,**changes):
        state=IncomingState139(1,0,0,b(20),b(1000000),b(1000000),b(.2),b(.6),barrier1448_bits=0,shield_source1344=0,shield_remaining1348_bits=0,reserve764_bits=0,absorbed736_bits=b(3),maximum_shield740_bits=b(4),last_hit1652_bits=b(-7),incoming992=1.25,items8=(),lightning_shield_spell_id=324)
        data=asdict(replace(state,**changes));data.pop('records432');data.pop('category1112')
        rows.append(dict(id=len(rows),group=group,input=data,source_records=list(records),history=history or dict(head=0,count=0,storage=[]),ops=ops or[op()]))
    add('baseline-real-English')
    for phase in(0,2,4,255):add('phase-guard',phase2587=phase)
    for flag in(1,3,255):add('protection-guard',protection2576=flag)
    add('protection-bit2-permits',protection2576=2)
    for expiry in(19,20,21):add('raw12-strict-expiry',live32=(Buff139(12,b(0),0,b(expiry)),))
    for shield,remaining,source in((100,100,0),(100,100,324),(100,9,324)):
        add('shield736740-source-reserve0',shield1444_bits=b(shield),barrier1448_bits=b(6),shield_source1344=source,shield_remaining1348_bits=b(remaining))
    for category in(0,1,2,3,255):add('real-English-fallback',ops=[op(category=category)])
    add('normal-source432',records=[npc()],ops=[op(guid=101,contact=1)])
    add('history-wrap-growth',history=dict(head=2,count=4,storage=[history_row(b(20),30+i)for i in range(4)]))
    if pilot:return rows
    for armor in(-.5,0,.2,.6,1,1.5):
        for amount in(0,7.5,25):add('finite-armor-domain',armor1568_bits=b(armor),ops=[op(amount=amount)])
    for rank in(0,1,2,4,7,255):
        for contact in(0,1):add('classification424-not416',records=[npc(rank=rank)],ops=[op(guid=101,contact=contact)])
    add('first-GUID-wins',records=[npc(rank=1),npc(rank=4)],ops=[op(guid=101,contact=1)])
    add('dead-source-still-resolves',records=[npc(marker=1)],ops=[op(guid=101,contact=1)])
    add('unmatched-GUID',records=[npc()],ops=[op(guid=202,contact=1)])
    add('high-GUID',records=[npc(guid=0xf130112233445566)],ops=[op(guid=0xf130112233445566,contact=1)])
    add('zero-GUID-match',records=[npc(guid=0)],ops=[op(guid=0)])
    add('null-definition-preserves-rank',records=[npc(rank=7,definition=0)],ops=[op(guid=101)])
    for rank in(0,1,10,255):
        for expiry in(20,21):
            add('modifier54-current-lightning-rank3pct',modifiers36=(Modifier139(54,1,rank),),live32=(Buff139(99,b(0),324,b(expiry)),))
    add('modifier54-first-wins',modifiers36=(Modifier139(54,1,1),Modifier139(54,1,255)),live32=(Buff139(99,0,324,b(21)),))
    add('modifier54-inactive-byte4',modifiers36=(Modifier139(54,0,255),),live32=(Buff139(99,0,324,b(21)),))
    for count in(0,1,4,5,6,8):add('nearby-five-threshold',nearby1624_bits=b(.25),records=[npc(guid=101+j,x=8 if j==0 else 0)for j in range(count)])
    add('nearby-dead-skip',nearby1624_bits=b(.25),records=[npc(guid=101+j,marker=int(j==0))for j in range(5)])
    add('nearby-outside8',nearby1624_bits=b(.25),records=[npc(guid=101+j,x=8.001 if j==0 else 0)for j in range(5)])
    add('nearby-interpolation',nearby1624_bits=b(.25),records=[npc(guid=101+j,x=16,start=(0,0),duration=20)for j in range(5)])
    for cap in(1,2,3,4,8):
        for head in range(cap):add('physical-ring-growth',history=dict(head=head,count=cap,storage=[history_row(b(20),30+j)for j in range(cap)]))
    add('strict-10s-prune',history=dict(head=6,count=4,storage=[history_row(b(20),j+10)for j in range(8)]),ops=[op(now=30),op(now=30.001)])
    add('count400-prune',history=dict(head=500,count=400,storage=[history_row(b(20),10+j%200)for j in range(512)]))
    add('repeated-same-state-category-history',records=[npc(rank=1)],ops=[op(amount=1,now=20+j/8,guid=101 if j%2 else 0,contact=j%2,category=j%3)for j in range(64)])
    add('minimum-one-history-preclamp',hp1440_bits=b(1),minimum_one2578=1,ops=[op(amount=10),op(amount=10,now=21)])
    return json.loads(json.dumps(rows,allow_nan=False))

def expected(case,trace):
    value=dict(case['input']);value['live32']=tuple(Buff139(**v)for v in value['live32']);value['modifiers36']=tuple(Modifier139(**v)for v in value['modifiers36']);value['items8']=tuple(value['items8']);value['records432']=tuple(tuple(bytes.fromhex(x))for x in case['source_records']);value['player_xy']=tuple(value['player_xy'])
    state=IncomingState139(**value);ring=from_raw_storage(case['history']['storage'],case['history']['head'],case['history']['count']);stages=[];keyed={}
    names={int(p):name for p,name in trace['ordinary_english_names'].items()}
    assert state.lightning_shield_spell_id==trace['lightning_shield']['spell_id']
    for op in case['ops']:
        state=replace(state,now_bits=op['now_bits']);before=state;result=resolve_prefix139(state,op['amount_bits'],source_guid=int(op['source_guid']),contact_flag=op['contact_flag']);state=result.state
        if result.history_required:
            source=resolve_source139(state.records432,int(op['source_guid']),english_names=names)
            ring=append_incoming_history(ring,now_bits=op['now_bits'],damage_bits=result.damage_bits,absorbed_bits=result.absorbed_bits,hp_after_prefix_bits=f.sub(before.hp1440_bits,result.damage_bits),maximum_hp_bits=state.maximum1536_bits,category=op['category'],source_label=source.name,source_classification=source.classification)
            keyed={'22':min(f.MASK,max(0,math.ceil(f.to_float(state.hp1440_bits)))),'28':min(f.MASK,max(0,math.ceil(f.to_float(state.maximum1536_bits))))}
        stages.append(dict(branch=result.branch,history=projection(ring),scalar={str(o):getattr(state,name)for o,name in SCALARS.items()}|{'744':0x5ac0ffee},incoming992_hex=struct.pack('>d',state.incoming992).hex(),phase2587=state.phase2587,categories={k:struct.pack('>d',v).hex()for k,v in state.category1112},keyed=dict(keyed),packets=[],notifications=[]))
    return stages

def compare(case,actual,counts,differences):
    def equal(path,want,got):
        counts['assertions']+=1
        if want!=got:
            counts['differences']+=1
            if len(differences)<80:differences.append(dict(id=case['id'],group=case['group'],field=path,expected=want,actual=got))
    previous=actual['before']
    for i,(want,got,op)in enumerate(zip(case['expected'],actual['stages'],case['ops'],strict=True)):
        path=f'stage{i}'
        for name in('scalar','incoming992_hex','phase2587'):equal(path+'.'+name,want[name],got[name])
        equal(path+'.source432',case['source_records'],got['source_records_after'])
        equal(path+'.category-ordered',list(want['categories'].items()),[tuple(x)for x in got['categories']['entries']])
        equal(path+'.keyed',want['keyed'],got['keyed']['fields'])
        for name in('packets','notifications'):equal(path+'.'+name,want[name],got[name]['active'])
        h=got['history'];w=want['history'];equal(path+'.history-header',w['header'],{k:h[k]for k in('capacity','head','count')});equal(path+'.history-active',w['active'],[{k:r[k]for k in('slot','strings')}for r in h['active']]);equal(path+'.history-cap',len(w['storage']),len(h['storage']))
        for j,(row,origin,physical)in enumerate(zip(w['storage'],w['provenance'],h['storage'],strict=True)):
            raw=bytes.fromhex(physical)
            for k,(value,provenance)in enumerate(zip(row,origin,strict=True)):
                if value is None:
                    assert provenance in('resource_pointer','allocator_unwritten');counts[provenance+'_observed_bytes']+=1
                else:equal(f'{path}.history[{j}]+{k}',value,raw[k]);counts['known_history_bytes']+=1
        before=bytearray.fromhex(previous['raw_game2592_hex']);struct.pack_into('<I',before,2352,op['now_bits']);after=bytes.fromhex(got['raw_game2592_hex'])
        if want['branch'].endswith('guard'):equal(path+'.all2592-guard-bytes',bytes(before).hex(),after.hex());counts['guard_bytes']+=2592
        else:
            changed=[k for k,(a,b)in enumerate(zip(before,after))if a!=b];counts['observed_changed_Game_bytes']+=len(changed)
        counts['stages']+=1;counts['branch_'+want['branch']]+=1;previous=got

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();files,edges=source_files();before={n:sha(ROOT/n)for n in files}
    out=ROOT/'evidence'/('incoming139-oracle-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ'));out.mkdir();manifest,trace=build(out)
    for name,digest in before.items():
        target=out/'source-snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes());assert sha(target)==digest
    cases=corpus(args.phase=='pilot')
    for c in cases:c['expected']=expected(c,trace)
    save(out/'fixtures.json',cases)
    (out/'inputs.jsonl').write_text(''.join(json.dumps({k:v for k,v in c.items()if k!='expected'},separators=(',',':'))+'\n'for c in cases))
    save(out/'expected.json',[dict(id=c['id'],stages=c['expected'])for c in cases]);frozen={name:sha(out/name)for name in('fixtures.json','inputs.jsonl','expected.json','manifest.json',manifest['module_file'])}
    assert before=={n:sha(ROOT/n)for n in files}and sha(NODE)==NODE_SHA
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=2048',str(ROOT/'scripts/run_incoming139_oracle.mjs'),str(out),str(out/'inputs.jsonl')]
    save(out/'prepared.json',dict(source_sha256=before,source_import_edges=edges,expected_before_original=True,artifacts=frozen,command=command,deadline_seconds=90));started=time.monotonic()
    with(out/'stdout.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,deadline_seconds=90,command=command))
        try:code=child.wait(timeout=90)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-started,deadline_seconds=90,pid_missing=missing(),pgid_missing=missing(True));save(out/'owned-terminal.json',terminal)
    actual=[json.loads(line)for line in(out/'stdout.jsonl').read_text().splitlines()];counts=Counter();differences=[]
    if code or len(actual)!=len(cases):
        save(out/'failure.json',dict(status='original_execution_failed',terminal=terminal,completed=len(actual),cases=len(cases)));print(json.dumps(dict(out=str(out),status='original_execution_failed',terminal=terminal,stderr=(out/'stderr.log').read_text()[-2000:])));raise SystemExit(1)
    for case,got in zip(cases,actual,strict=True):assert case['id']==got['id'];compare(case,got,counts,differences)
    runtime=json.loads((out/'runtime.json').read_text());assert runtime['completed_target1076_calls']==sum(len(c['ops'])for c in cases)and runtime['actual_host_calls']==0 and runtime['real_locale83304_setup_calls']==(len(cases)+31)//32
    assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}and sha(SOURCE)==SOURCE_SHA
    save(out/'differences.json',differences)
    result=dict(status='scoped_original_differential_passed'if not differences else'differences_preserved',version='0.139.0',actual_build='f79c5e2b4',phase=args.phase,cases=len(cases),full1076_calls=runtime['completed_target1076_calls'],setup83304_calls=runtime['real_locale83304_setup_calls'],differences=counts['differences'],counts=dict(counts),groups=dict(Counter(c['group']for c in cases)),source_sha256_before=before,source_sha256_after=before,source_import_edges=edges,production_sources=[n for n in files if n.startswith('reconstruction/')],expected_before_original=True,original_input_contains_expected=False,original_sha256=SOURCE_SHA,frozen_artifacts=frozen,artifacts={n:sha(out/n)for n in('stdout.jsonl','stderr.log','runtime.json','owned-terminal.json','prepared.json','differences.json','static/trace.json')},runtime=runtime,process=terminal,scope='Complete unchanged1076 controlled invocation; independent scalar/shield/source-category/history48/keyed-HP projection with actual fresh83304 English producer.',limitations=['Explicit synthetic zero Game and432B NPC consumer fixtures; not natural constructor/NPC/world/App producers.','Only mode0 nonfatal/minimum-one,spellID0,no-positive-reserve-spill and known no-active-callback inputs are accepted.','Unknown history resource-pointer and allocator-unwritten cells remain None; full physical backing captured, only known cells claimed.','Full Game2592 captured; all bytes independently checked for guards, remaining full-body bytes retained as observations.','Category/keyed logical values verified; physical BTree pointer/allocation/layout not independently reconstructed.','No old135/138 acceptance or discovery pilot counts are transferred.','0 complete game/native/full880/latest headless composition claimed.'])
    save(out/'comparison.json',result);print(json.dumps(dict(out=str(out.relative_to(ROOT)),comparison_sha256=sha(out/'comparison.json'),status=result['status'],cases=len(cases),full1076_calls=result['full1076_calls'],differences=counts['differences'],first_differences=differences[:5],process=terminal)))
    if differences:raise SystemExit(1)
if __name__=='__main__':main()
