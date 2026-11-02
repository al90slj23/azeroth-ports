#!/usr/bin/env python3
"""Expected-first fresh1600→1173/full1076 shield cleanup, current139 only."""
from collections import Counter
from dataclasses import replace
from datetime import datetime,timezone
import argparse,json,math,os,signal,struct,subprocess,sys,time
sys.dont_write_bytecode=True
from incoming139_tools import ROOT,SOURCE,SOURCE_SHA,sha,save
from source_closure137 import verify_local_source_closure
from production_closure135 import production_sources135
from build_incoming_aura139_oracle import build
from check_incoming139 import SCALARS,NODE,NODE_SHA
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.incoming139 import IncomingState139,Buff139,resolve_prefix139
from core_spec.incoming_history139 import from_raw_storage,append_incoming_history,projection
from core_spec.incoming_aura139 import AuraInputs139,empty_aura139,resolve_cleanup_incoming139
from core_spec.initial_state139 import ConstructorInput139,initialize_empty_profile139,projection139,canonical_game_cells139
from core_spec.initial_state139_data import ZONE_ENTRIES

def closure():
    names=set(production_sources135(ROOT,'core_spec.incoming_aura139','core_spec.initial_state139','core_spec.incoming_history139'))|set('scripts/'+n for n in('check_incoming_aura139.py','run_incoming_aura139_oracle.mjs','trace_incoming_aura139.py','build_incoming_aura139_oracle.py','production_closure135.py','source_closure137.py'))
    while True:
        try:edges=verify_local_source_closure(sorted(names));return sorted(names),edges
        except AssertionError as error:
            pair=error.args[0]
            if not isinstance(pair,tuple)or len(pair)!=2 or pair[1]in names:raise
            names.add(pair[1])

def live_record(spell=324,kind=7,expiry=100,value=5):
    raw=bytearray([0x5a]*32)
    for o,v in((8,kind),(12,f.from_float(value)),(20,spell),(24,f.from_float(expiry))):struct.pack_into('<I',raw,o,v)
    return raw.hex()

def corpus(pilot):
    rows=[];b=f.from_float
    def add(group,kind='incoming',*,shield=5,remaining=100,source=324,amount=10,live=None,previous=None,ops=None,**overrides):
        fields={'1444':b(shield),'1448':b(shield),'1344':source,'1348':b(remaining),'764':0,'736':b(3),'740':b(7)}
        fields.update({str(k):v for k,v in overrides.items()})
        rows.append(dict(id=len(rows),group=group,kind=kind,constructor=dict(class_byte=1,race_byte=1,region_index=0,seed_u64='0',object_id_u64='42',flat_height_bits=0),region_id=ZONE_ENTRIES[0][0],now_bits=b(20),overrides=fields,live32=live if live is not None else[]if kind=='aura'else[live_record()],previous_aura=previous,ops=ops or[dict(now_bits=b(20),amount_bits=b(amount),category=0)]))
    add('direct1173-empty-current-constructor',kind='aura',shield=0,source=0)
    add('full1076-shield-exhaustion-kind7',shield=5,amount=10)
    add('full1076-shield-source-depletion',shield=100,remaining=5,amount=10)
    if pilot:return rows
    add('direct1173-repeat-empty',kind='aura',shield=0,source=0,ops=[dict(now_bits=b(20+j),amount_bits=0,category=0)for j in range(3)])
    for flag in(0,1,2,3):
        storage=[(b'\0'*4+bytes([0x30+j%40])*12).hex()for j in range(48)]
        add('direct1173-prior-tag0-ready-policy',kind='aura',shield=0,source=0,previous=dict(flag2569=flag,storage=storage))
    for shield in(1,5,10,20):
        for amount in(30,100):
            for source in(0,324):add('exhaustion-matrix',shield=shield,amount=amount,source=source)
    for remaining in(0,1,5,7):add('source-depletion-matrix',shield=100,remaining=remaining,amount=10)
    add('exhaustion-removes-all-kind7',shield=5,amount=10,live=[live_record(324),live_record(123),live_record(999)])
    add('source-depletion-removes-all-matching-spell',shield=100,remaining=5,amount=10,live=[live_record(324),live_record(324),live_record(324)])
    add('exhaustion-no-live-record-still1173',shield=5,amount=10,live=[])
    add('depletion-no-live-record-still1173',shield=100,remaining=5,amount=10,live=[])
    for category in(1,2,255):add('cleanup-real-English-history-fallback',shield=5,amount=10,ops=[dict(now_bits=b(20),amount_bits=b(10),category=category)])
    add('same-Game-post-cleanup-followup',shield=5,amount=10,ops=[dict(now_bits=b(20),amount_bits=b(10),category=0),dict(now_bits=b(21),amount_bits=b(5),category=1)])
    return rows

def expected(c,trace):
    ctorvalue=ConstructorInput139(**{k:int(v)for k,v in c['constructor'].items()});ctor=initialize_empty_profile139(ctorvalue);p=projection139(ctor);derived=p['derived_bits'];o=c['overrides'];live=tuple(Buff139(*[struct.unpack_from('<I',bytes.fromhex(row),x)[0]for x in(8,12,20,24)])for row in c['live32'])
    state=IncomingState139(1,0,0,c['now_bits'],p['current_hp_bits'],derived['1536'],derived['1568'],derived['1572'],nearby1624_bits=derived['1624'],shield1444_bits=o['1444'],barrier1448_bits=o['1448'],shield_source1344=o['1344'],shield_remaining1348_bits=o['1348'],reserve764_bits=o['764'],absorbed736_bits=o['736'],maximum_shield740_bits=o['740'],last_hit1652_bits=dict(ctor.initial_scalar_words)[1652],incoming992=0.0,player_xy=tuple(ctor.player_xyz[:2]),live32=live,items8=())
    previous=c['previous_aura'];fields=tuple(sorted((int(k),v)for k,v in p['player_fields'].items()));owner=AuraInputs139((trace['default_humanwarrior_definition_kinds']['5882740'],),trace['default_humanwarrior_definition_kinds']['5891892'],(),(),len(previous['storage'])if previous else 0,previous['flag2569']if previous else 0,tuple(tuple(bytes.fromhex(row))for row in previous['storage'])if previous else(),fields)
    ring=from_raw_storage([],0,0);stages=[];aura=None
    for op in c['ops']:
        state=replace(state,now_bits=op['now_bits']);old=state
        if c['kind']=='aura':aura=empty_aura139(owner);branch='direct1173-empty'
        else:
            if aura is None:
                result=resolve_cleanup_incoming139(state,op['amount_bits'],owner);prefix=result.prefix;aura=result.aura;branch=result.reason
            else:prefix=resolve_prefix139(state,op['amount_bits']);branch='post-cleanup-'+prefix.branch
            state=prefix.state;ring=append_incoming_history(ring,now_bits=op['now_bits'],damage_bits=prefix.damage_bits,absorbed_bits=prefix.absorbed_bits,hp_after_prefix_bits=f.sub(old.hp1440_bits,prefix.damage_bits),maximum_hp_bits=state.maximum1536_bits,category=op['category'])
            fields=dict(aura.player_fields);fields[22]=max(0,math.ceil(f.to_float(state.hp1440_bits)));fields[28]=max(0,math.ceil(f.to_float(state.maximum1536_bits)));aura=replace(aura,player_fields=tuple(sorted(fields.items())))
        owner=replace(owner,previous_count=48,previous_flag2569=1,previous_storage=aura.storage,player_fields=aura.player_fields)
        scalar={str(offset):getattr(state,name)for offset,name in SCALARS.items()};scalar.update({'744':0x5ac0ffee,'1536':state.maximum1536_bits,'1568':state.armor1568_bits,'1572':state.armor_cap1572_bits})
        stages.append(dict(branch=branch,scalar=scalar,incoming992_hex=struct.pack('>d',state.incoming992).hex(),phase2587=1,history=projection(ring),categories={k:struct.pack('>d',v).hex()for k,v in state.category1112},keyed={str(k):v for k,v in aura.player_fields},aura=dict(capacity=48,count=48,flag2569=1,storage=[list(row)for row in aura.storage],written_keys=list(aura.written_keys)),live_count=0 if c['kind']=='incoming'else len(c['live32'])))
    return dict(constructor_cells=list(canonical_game_cells139(ctor)),owned80=p['owned_records_hex'],racial80_hex=p['racial_record_hex'],constructor_fields=p['player_fields'],stages=stages)

def compare(c,a,counts,diffs):
    def eq(path,w,g):
        counts['assertions']+=1
        if w!=g:
            counts['differences']+=1
            if len(diffs)<80:diffs.append(dict(id=c['id'],group=c['group'],field=path,expected=w,actual=g))
    def known(path,w,g):
        if w is None:counts['unknown_cells_observed']+=1
        else:eq(path,w,g);counts['known_cells']+=1
    e=c['expected'];ctor=bytes.fromhex(a['constructor']['raw_game2592_hex'])
    for j,w in enumerate(e['constructor_cells']):known('constructor+'+str(j),w,ctor[j])
    eq('constructor-keyed',e['constructor_fields'],a['constructor']['keyed']['fields']);eq('borrowed-inputs',True,a['inputs_unchanged']);previous=a['before']
    for i,(w,g,op)in enumerate(zip(e['stages'],a['stages'],c['ops'],strict=True)):
        label='stage'+str(i)
        for k in('scalar','incoming992_hex','phase2587'):eq(label+'.'+k,w[k],g[k])
        eq(label+'.owned80',e['owned80'],g['owned80']);eq(label+'.racial80',e['racial80_hex'],g['racial80_hex']);eq(label+'.keyed',w['keyed'],g['keyed']['fields']);eq(label+'.keyed-count',len(w['keyed']),g['keyed']['count']);eq(label+'.categories',w['categories'],dict(g['categories']['entries']))
        for k in('capacity','count','flag2569'):eq(label+'.aura.'+k,w['aura'][k],g['aura'][k])
        for j,(row,physical)in enumerate(zip(w['aura']['storage'],g['aura']['storage'],strict=True)):
            for k,(value,actual)in enumerate(zip(row,bytes.fromhex(physical),strict=True)):known(f'{label}.Aura[{j}]+{k}',value,actual)
        eq(label+'.live-count',w['live_count'],g['live']['count']);eq(label+'.all-live-backing',c['live32'],g['live']['storage'])
        h=w['history'];actual=g['history'];eq(label+'.history-header',h['header'],{k:actual[k]for k in('capacity','head','count')});eq(label+'.history-active',h['active'],[{k:r[k]for k in('slot','strings')}for r in actual['active']])
        for j,(row,physical)in enumerate(zip(h['storage'],actual['storage'],strict=True)):
            for k,(value,actual_byte)in enumerate(zip(row,bytes.fromhex(physical),strict=True)):known(f'{label}.history[{j}]+{k}',value,actual_byte)
        for k in('packets','notifications'):eq(label+'.'+k,previous[k],g[k])
        wanted=bytearray.fromhex(previous['raw_game2592_hex']);after=bytes.fromhex(g['raw_game2592_hex']);struct.pack_into('<I',wanted,2352,op['now_bits']);wanted[2569]=1
        for offset,value in((2000,48),(2008,48)):struct.pack_into('<I',wanted,offset,value)
        unknown_words={2004,2476,2480}
        if c['kind']=='incoming':
            for offset,value in((968,h['header']['capacity']),(976,h['header']['head']),(980,h['header']['count']),(1712,0),(1116,0),(1120,len(w['categories']))):struct.pack_into('<I',wanted,offset,value)
            struct.pack_into('<Q',wanted,992,int(w['incoming992_hex'],16))
            for offset,value in w['scalar'].items():struct.pack_into('<I',wanted,int(offset),value)
            unknown_words|={972,1112}
        struct.pack_into('<I',wanted,2484,len(w['keyed']))
        for offset in unknown_words:wanted[offset:offset+4]=after[offset:offset+4];counts['physical_pointer_or_treeheight_words_observed']+=1
        eq(label+'.relative-Game2592-knownbytes',wanted.hex(),after.hex());counts['relative_Game_known_bytes']+=2592-4*len(unknown_words);counts['stages']+=1;counts['branch_'+w['branch']]+=1;previous=g

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args();files,edges=closure();before={n:sha(ROOT/n)for n in files};out=ROOT/'evidence'/datetime.now(timezone.utc).strftime('incoming-aura139-oracle-%Y%m%dT%H%M%S.%fZ');out.mkdir();manifest,trace=build(out)
    for name,digest in before.items():q=out/'source-snapshot'/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/name).read_bytes());assert sha(q)==digest
    rows=corpus(args.phase=='pilot')
    for c in rows:c['expected']=expected(c,trace)
    save(out/'fixtures.json',rows);(out/'inputs.jsonl').write_text(''.join(json.dumps({k:v for k,v in c.items()if k!='expected'},separators=(',',':'))+'\n'for c in rows));save(out/'expected.json',[dict(id=c['id'],expected=c['expected'])for c in rows]);frozen={n:sha(out/n)for n in('fixtures.json','inputs.jsonl','expected.json','manifest.json',manifest['module_file'])}
    assert sha(NODE)==NODE_SHA and before=={n:sha(ROOT/n)for n in files}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=2048',str(ROOT/'scripts/run_incoming_aura139_oracle.mjs'),str(out),str(out/'inputs.jsonl')];save(out/'prepared.json',dict(expected_before_original=True,sources=before,source_import_edges=edges,artifacts=frozen,command=command,deadline_seconds=90));start=time.monotonic()
    with(out/'stdout.jsonl').open('w')as stdout,(out/'stderr.log').open('w')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True);save(out/'owned-start.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=90))
        try:code=child.wait(timeout=90)
        except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait();code=child.returncode
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid=child.pid,pgid=child.pid,exit_code=code,seconds=time.monotonic()-start,pid_missing=missing(),pgid_missing=missing(True),deadline_seconds=90);save(out/'owned-terminal.json',terminal)
    actual=[json.loads(x)for x in(out/'stdout.jsonl').read_text().splitlines()];runtime=json.load(open(out/'runtime.json'));counts=Counter();diffs=[]
    if code or len(actual)!=len(rows):save(out/'failure.json',dict(process=terminal,completed=len(actual),expected=len(rows)));print(json.dumps(dict(out=str(out.relative_to(ROOT)),status='failed_preserved',process=terminal,stderr=(out/'stderr.log').read_text()[-2000:])));raise SystemExit(1)
    for c,a in zip(rows,actual,strict=True):assert c['id']==a['id'];compare(c,a,counts,diffs)
    assert before=={n:sha(ROOT/n)for n in files}and frozen=={n:sha(out/n)for n in frozen}and sha(SOURCE)==SOURCE_SHA and runtime['actual_host_calls']==0
    save(out/'differences.json',diffs);receipt=dict(status='scoped_original_differential_passed'if not diffs else'differences_preserved',version='0.139.0',actual_build='f79c5e2b4',cases=len(rows),phase=args.phase,differences=counts['differences'],counts=dict(counts),groups=dict(Counter(c['group']for c in rows)),source_sha256_before=before,source_sha256_after=before,source_import_edges=edges,original_sha256=SOURCE_SHA,expected_before_original=True,original_input_contains_expected=False,frozen_artifacts=frozen,artifacts={n:sha(out/n)for n in('stdout.jsonl','stderr.log','runtime.json','prepared.json','owned-terminal.json','differences.json','static/trace.json')},runtime=runtime,process=terminal,scope='Fresh controlled1600 consistent humanwarrior→actual83304→direct1173 empty-source or complete1076 shield exhaustion/source-depletion;66 keyed outputs,48 Aura known/None cells,HP/history/counters and relative Game conservation.',limitations=['Actual1600 and83304 are setup, not new independent constructor/localization acceptance counts.','Phase1 is explicit consumer input; noApp/externref/natural cachedworld or opening1108.','Only shield-only live records entirely removed,empty mod36,no owned/racial kind12,no reserve spill and nonfatal source0/contact0 are accepted.','Nonempty Aura/modifier/retained live/cooldown branches remain future work; physical BTree allocation/pointers/treeheight are observations with full nodes retained.','No full880/native/complete game runs or transferred135/138 cases.'])
    save(out/'comparison.json',receipt);print(json.dumps(dict(out=str(out.relative_to(ROOT)),comparison_sha256=sha(out/'comparison.json'),cases=len(rows),calls1076=runtime['completed_target1076_calls'],calls1173=runtime['completed_target1173_calls'],differences=counts['differences'],first_differences=diffs[:5],process=terminal)))
    if diffs:raise SystemExit(1)
if __name__=='__main__':main()
