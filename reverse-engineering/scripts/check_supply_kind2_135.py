#!/usr/bin/env python3
"""Expected-first complete1351417-kind2/full947 G2448 controlled differential."""
from collections import Counter
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import argparse,ast,hashlib,json,os,re,signal,struct,subprocess,sys,time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    with Path(path).open('rb')as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def source_files():
    bases=(ROOT/'scripts',ROOT/'reconstruction')
    pending=[Path(__file__).resolve(),ROOT/'scripts/run_supply_kind2_135_oracle.mjs'];seen=set()
    def resolve(name):
        for base in bases:
            p=base/Path(*name.split('.'))
            for q in(p.with_suffix('.py'),p/'__init__.py'):
                if q.is_file():return q
    while pending:
        p=pending.pop();key=str(p.relative_to(ROOT))
        if key in seen:continue
        seen.add(key)
        if p.suffix=='.mjs':targets=[(p.parent/name).resolve()for name in re.findall(r"from\s+['\"](\.[^'\"]+)['\"]",p.read_text())]
        else:
            base=next(b for b in bases if p.is_relative_to(b));package=list(p.relative_to(base).with_suffix('').parts[:-1]);targets=[]
            for node in ast.walk(ast.parse(p.read_text())):
                names=[]
                if isinstance(node,ast.Import):names=[x.name for x in node.names]
                elif isinstance(node,ast.ImportFrom):
                    prefix='.'.join(package[:len(package)-node.level+1])if node.level else''
                    module='.'.join(x for x in(prefix,node.module or'')if x)
                    names=[module]+['.'.join(x for x in(module,a.name)if x)for a in node.names]
                targets.extend(q for name in names if name and(q:=resolve(name))is not None)
        for q in targets:
            pending.append(q);base=next(b for b in bases if q.is_relative_to(b));par=q.parent
            while par!=base:
                if(par/'__init__.py').is_file():pending.append(par/'__init__.py')
                par=par.parent
    return tuple(sorted(seen))


FILES=source_files()
SOURCE_BEFORE={n:sha(ROOT/n)for n in FILES}
sys.path.insert(0,str(ROOT/'reconstruction'))
from check_resource_spawn135 import private_build
from trace_supply_kind2_135 import trace_supply_kind2_135
from build_full135_oracle import SOURCE,SOURCE_SHA
from ai_world135_inputs import ASSET_WORLD,HASHES,load_asset_world135,asset_world_description135
from core_spec import binary32 as f
from core_spec.opening135 import EmptyOpeningInput135
from core_spec.opening_handoff135 import initialize_absent_companion_handoff
from core_spec.profile_companions135 import EmptyCompanionProfile135
from core_spec.opening_npc_pickups135 import OpeningVector135,npc_create_fields
from core_spec.opening_entities135 import unit_create169,BASE_SPEEDS
from core_spec.record_cells135 import cells135,u32
from core_spec.spawn_schedule135 import FrameInput
from core_spec.resource_spawn135 import ResourceSpawnInput135,step_resource_spawn135
from core_spec.spawn_frame_motion135 import step_ordinary_frame
from core_spec.spawn_heading135 import atan2_bits
from core_spec.spawn135 import definition
from core_spec.supply_kind2_135 import(Kind2PickupInput135,SupplyTickInput135,
    produce_kind2_pickup135,step_supply_kind2_135,PendingSupplyKind2135)

NODE=ROOT/'.toolchain/runtime/node_modules/node/bin/node'
NODE_SHA='2cc28a1880d0774616959f2210ee739bffa6ac695c887e8988a496a21271f6c0'


def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def physical(vector):return dict(capacity=vector.capacity,count=vector.count,storage=vector.storage)


def vector(kinds,capacity=None,*,marker2=False,partial=True):
    capacity=max(4,len(kinds))if capacity is None else capacity;rows=[]
    for i in range(capacity):
        row=list(bytes((i*31+j*17+37)&255 for j in range(56)))
        if i<len(kinds):
            for offset,data in((0,struct.pack('<I',2 if marker2 else 99 if i&1 else 0)),
                (8,struct.pack('<IIQ',kinds[i],7+i,0xf110000000000000|(9005<<24)|(1000+i))),
                (24,struct.pack('<III',0,8,0)),(40,struct.pack('<4I',f.from_float(-9396),f.from_float(-633),f.from_float(66),f.from_float(5+i)))):
                row[offset:offset+len(data)]=data
        if partial:row[4:8]=[None,row[5],None,row[7]]
        rows.append(tuple(row))
    return OpeningVector135(56,tuple(rows),len(kinds))


def corpus(full):
    world=load_asset_world135();description=asset_world_description135();handoffs={};cases=[];expected=[];labels=[]
    def handoff(seed):
        if seed not in handoffs:
            handoffs[seed]=initialize_absent_companion_handoff(EmptyOpeningInput135(1,1,0,seed,42),world,
                companion_profile=EmptyCompanionProfile135(()),title_utf8=b'Elwynn Forest',subtitle_utf8=b'')
        return handoffs[seed]
    def add(operation,group,value,*,h,frame=None):
        i=len(cases);raw=asdict(value);raw['pickups']=dict(count=value.pickups.count,storage=value.pickups.storage)
        case=dict(id=i,operation=operation,input=raw,map_id_utf8='elwynn',unknown_poison=(0xa5,0x5a)[i&1],world=description,message_sequence=1)
        if operation=='produce':
            result=produce_kind2_pickup135(value,world)
            projection=dict(pickups=physical(result.pickups),rng_words=result.rng_words,counter=result.counter,
                message_sequence=1,packets=[dict(opcode=op,payload_hex=data)for op,data in result.packets],notifications_count=0,
                opaque_word_provenance=result.opaque_word_provenance)
            meta=dict(removed_guids=result.removed_guids,final_position_bits=result.position_bits,actor_draws=result.actor_draws)
        else:
            units=h.opening.units
            peers=(tuple((*frame.player_xyz,0))for _ in range(max(1,(value.party_count2140+1-value.excluded2548))if value.party_count2140+1>=value.excluded2548 else 1))if value.mode==1 else()
            peers=tuple(peers)
            if value.mode==1:
                # Complete947 mode1 uses2232/2236, not the local-player fields,
                # for its preceding far-NPC relocation predicate. This fixture
                # supplies actual finite peer positions and proves that the
                # existing four NPCs remain within the55-unit no-relocation domain.
                for row in h.records:
                    x,y=(f.to_float(u32(row,o))for o in(328,332))
                    assert any((x-f.to_float(peer[0]))**2+(y-f.to_float(peer[1]))**2<=3025 for peer in peers)
            ordinary=step_ordinary_frame(frame,destination_slots=units.storage,world=world,
                distance_map=None,allow_unknown_storage_growth=True)
            assert ordinary.status=='ordinary_projection'
            after_ordinary=replace(value,rng_words=ordinary.rng_words,counter=ordinary.counter,velocity_xy=ordinary.velocity_xy)
            result=step_supply_kind2_135(after_ordinary,world)
            storage=list(units.storage)
            while len(storage)<len(ordinary.unit_records):storage.extend([(None,)*424]*(max(4,len(storage)*2)-len(storage)))
            for j,row in enumerate(ordinary.unit_records):storage[j]=tuple(cells135(row,424))
            packets=[]
            for request,row in zip(ordinary.requests,ordinary.unit_records[units.count:]):
                desc=definition(0,request['index']);xyz=tuple(request['position_bits'])
                heading=atan2_bits(f.sub(frame.player_xyz[1],xyz[1]),f.sub(frame.player_xyz[0],xyz[0]))
                fields=npc_create_fields(request['guid'],desc['entry'],desc['display'],desc['scale_bits'],u32(row,288),desc['elite'],42,1)
                packets.append(dict(opcode=169,payload_hex=unit_create169(request['guid'],xyz,heading,BASE_SPEEDS,fields).hex()))
            packets.extend(dict(opcode=op,payload_hex=data)for op,data in result.packets)
            other={str(o):f.from_float(f.to_float(frame.now_bits)+1000)for o in(2424,2440,2444,2456,2460)}
            projection=dict(pickups=physical(result.pickups),rng_words=result.rng_words,counter=result.counter,
                message_sequence=1,packets=packets,notifications_count=0,opaque_word_provenance=result.opaque_word_provenance,
                next_supply2448_bits=result.next_supply2448_bits,budget_bits=ordinary.budget_bits,kill_cost_bits=ordinary.kill_cost_bits,
                velocity_xy=ordinary.velocity_xy,previous_player_xyz=frame.player_xyz if frame.mode==0 else frame.previous_player_xyz,
                units=dict(capacity=len(storage),count=len(ordinary.unit_records),storage=storage),other_clocks=other)
            case.update(frame=asdict(frame),units=dict(count=units.count,storage=units.storage),initial_scalars=h.initial.initial_scalar_words,
                level=1,player_guid='42',other_clocks=other,peer_positions16=peers)
            meta=dict(status=result.status,counted_kind2=result.counted_kind2,cap=result.cap,factor_bits=result.factor_bits,
                position_draws=result.position_draws,actor_draws=result.actor_draws,final_position_bits=result.final_position_bits,
                ordinary_requests=ordinary.requests,ordinary_draws=ordinary.draws,opaque_word_provenance=result.opaque_word_provenance,
                original_clock_is_explicit60_not_natural_elapsed=True,
                existing_NPCs_preserved=True,mode1_peer_positions_explicit=peers,mode1_prelude_domain='All existing NPCs within55 of at least one explicit peer')
        cases.append(case);expected.append(dict(id=i,result=projection));labels.append(dict(id=i,group=group,**meta))
    direct=[(0,0,0,(),0,False),(0,0,0,(2,2),4,False),(0,0,0,(2,)*5,5,False)]
    if full:
        direct += [(0,0,0,(2,)*n,cap,False)for n,cap in((1,1),(4,4),(6,8),(8,8))]
        direct += [(1,party,excluded,(2,)*n,n,False)for party,excluded,n in((1,0,7),(1,0,8),(3,0,13),(1,1,5),(0,2,5))]
        direct += [(0,0,0,(3,2,4,2,5,2,2,2),8,False)]
    for j,(mode,party,excluded,kinds,capacity,marked)in enumerate(direct):
        h=handoff(j%4);xyz=h.initial.player_xyz
        if j%2:xyz=(f.add(xyz[0],f.from_float(1200)),f.add(xyz[1],f.from_float(-900)),0)
        value=Kind2PickupInput135(0,(0,1,2,0xffffffff,0xdeadbeef)[j%5],xyz,f.from_float(60),h.rng_words,
            0xffffffff if j==4 else h.counter,vector(kinds,capacity,marker2=marked),mode,party,excluded)
        add('produce','direct1417-kind2-cap-replacement'if len(kinds)>=5 else'direct1417-kind2-append',value,h=h)
    if full:
        for j,arrivals in enumerate(((7,3,9,3,1),(5,5,7,8,9))):
            h=handoff(j);vec=vector((2,)*5,5);rows=[list(row)for row in vec.storage]
            for row,arrival in zip(rows,arrivals):row[52:56]=struct.pack('<I',f.from_float(arrival))
            value=Kind2PickupInput135(0,0x89abcdef,h.initial.player_xyz,f.from_float(60),h.rng_words,h.counter,
                OpeningVector135(56,tuple(tuple(row)for row in rows),5))
            add('produce','direct1417-oldest-tie-first'if j else'direct1417-oldest-last-nonmonotonic',value,h=h)
    configs=[(0,None,60,60,.1,0,0,0),(0,(2,2,2),60,60,.1,0,0,0)]
    if full:
        configs=[]
        for seed in range(4):
            configs +=[(seed,kinds,now,deadline,dt,mode,party,excluded)for kinds,now,deadline,dt,mode,party,excluded in(
                (None,60,60,.1,0,0,0),('opening2-resource40',60,60,.1,0,0,0),((2,),60,60,.1,0,0,0),((2,2,2),60,60,.1,0,0,0),
                ((2,2,2,2),60,60,.1,0,0,0),((2,3,2,4),60,60,.1,0,0,0),((3,2,4,2,5),60,60,.1,0,0,0),
                (None,59.999996,60,.1,0,0,0),(None,60,59.5,0,0,0,0),
                ((2,)*4,60,60,.1,1,1,0),((2,)*6,60,60,.1,1,3,0),
                (None,60,60,.1,1,1,1),(None,60,60,.1,1,0,2),((2,)*3,60,60,.1,1,3,4),
                ((),60,60,.1,1,1,0))]
    for seed,kinds,now,deadline,dt,mode,party,excluded in configs:
        h=handoff(seed);initial=h.initial;scalars=dict(initial.initial_scalar_words)
        rng_words,counter=h.rng_words,h.counter
        if kinds=='opening2-resource40':
            prepared=step_resource_spawn135(ResourceSpawnInput135(0,f.from_float(40),f.from_float(40),
                initial.player_xyz,(0,0),rng_words,counter,h.opening.pickups),world)
            assert prepared.status=='resource2444_spawned'and prepared.pickups.count==3
            vec,rng_words,counter=prepared.pickups,prepared.rng_words,prepared.counter
        else:vec=h.opening.pickups if kinds is None else vector(kinds)
        frame=FrameInput(0,f.from_float(now),f.from_float(dt),scalars[2416],initial.kill_cost_bits,mode,
            1,initial.level.heal_gate387,scalars[2516],0,0,0,initial.player_xyz,
            tuple(scalars[o]for o in(2428,2432,2436)),(0,0),world.fallback_height_bits,rng_words,counter,
            tuple(tuple(row)for row in h.records),True)
        value=SupplyTickInput135(0,frame.now_bits,f.from_float(deadline),initial.player_xyz,(0,0),rng_words,counter,vec,mode,party,excluded)
        add('tick','complete947-opening2-resource40-first60'if kinds=='opening2-resource40'else'complete947-opening2-first60'if kinds is None and mode==0 else'complete947-cooperative'if mode else'complete947-kind2-cap-boundaries',value,h=h,frame=frame)
        if kinds=='opening2-resource40':
            labels[-1]['fixture_resource40_preparation']='Independent step_resource_spawn135 before oracle input; not a fresh original2444 call or natural40s history'
            labels[-1]['fixture_resource40_kind']=prepared.chosen_kind
            labels[-1]['fixture_resource40_draws']=prepared.draws
    return cases,expected,labels


def compare(expected,actual,cases):
    counts=Counter();errors=[]
    def walk(a,b,path):
        if a is None:
            assert re.fullmatch(r'case\d+\.(pickups|units)\.storage\[\d+\]\[\d+\]',path),path
            assert type(b)is int and 0<=b<=255;counts['unknown_cells']+=1
        elif isinstance(a,dict):
            if type(b)is not dict or set(a)!=set(b):errors.append(dict(path=path,reason='keys'));return
            for key in a:walk(a[key],b[key],path+'.'+key)
        elif isinstance(a,(tuple,list)):
            if not isinstance(b,(tuple,list))or len(a)!=len(b):errors.append(dict(path=path,reason='length'));return
            for j,(x,y)in enumerate(zip(a,b)):walk(x,y,path+'['+str(j)+']')
        else:
            counts['known_values']+=1
            if type(a)is not type(b)or a!=b:errors.append(dict(path=path,expected=a,actual=b))
    assert len(expected)==len(actual)==len(cases)
    for want,got,case in zip(expected,actual,cases):
        assert want['id']==got['id']==case['id'];result=got['result']
        for key in('pickups','units'):
            if key in result:result[key]['storage']=[list(bytes.fromhex(row))for row in result[key]['storage']]
        walk(want['result'],result,'case'+str(want['id']))
        provenance=want['result']['opaque_word_provenance'];assert len(got['amount_observations'])==len(provenance)
        for opaque,observed in zip(provenance,got['amount_observations']):
            assert opaque['guid']==observed['guid']and opaque['byte_delta']==observed['byte_delta']
            assert observed['actual_word']==observed['derived_word']==(observed['pre_owner_base']+opaque['byte_delta'])&f.MASK
            matching=[r for r in result['pickups']['storage'][:result['pickups']['count']]if int.from_bytes(bytes(r[16:24]),'little')==int(opaque['guid'])]
            assert len(matching)==1 and int.from_bytes(bytes(matching[0][12:16]),'little')==observed['actual_word']
            counts['opaque_amount_words_exact_owner_formula_checked']+=1
        before,after=(bytes.fromhex(got[k])for k in('game_before8192_hex','game_after8192_hex'));assert len(before)==len(after)==8192
        allowed=set(range(1720,1736))|set(range(1868,1892))|set(range(2408,2412))
        if case['operation']=='tick':allowed|=set(range(1736,1744))|set(range(1784,1796))|set(range(2416,2424))|set(range(2428,2440))|set(range(2448,2452))
        unexpected=[j for j,(a,b)in enumerate(zip(before,after))if a!=b and j not in allowed]
        if unexpected:errors.append(dict(path='case'+str(want['id'])+'.Game_nonallowed',offsets=unexpected))
        counts['unchanged_Game_bytes_outside_allowed_ranges']+=8192-len(allowed)
        counts['packets']+=len(result['packets']);counts['packet_bytes']+=sum(len(row['payload_hex'])//2 for row in result['packets'])
    return errors,counts


def refusal_checks(cases):
    world=load_asset_world135();raw=next(c['input']for c in cases if c['operation']=='tick')
    vector_value=OpeningVector135(56,tuple(tuple(row)for row in raw['pickups']['storage']),raw['pickups']['count'])
    value=SupplyTickInput135(**{**raw,'pickups':vector_value});answers=[]
    future=replace(value,now_bits=f.from_float(59),next_supply2448_bits=f.from_float(60),pickups=OpeningVector135(56,((None,)*56,),1))
    assert step_supply_kind2_135(future,None).status=='supply2448_future';answers.append('future_does_not_read_unknown_kind_or_world')
    assert step_supply_kind2_135(replace(value,pickups=vector((2,2,2))),None).status=='supply2448_cap';answers.append('cap_no_rng_or_world_read')
    try:step_supply_kind2_135(replace(value,pickups=OpeningVector135(56,())),world)
    except PendingSupplyKind2135:answers.append('mode0_empty_caller_local_amount_pending')
    else:raise AssertionError('Unrecovered empty local2 accepted')
    direct=Kind2PickupInput135(0,1,value.player_xyz_bits,value.now_bits,value.rng_words,value.counter,vector((2,)*5,5,marker2=True))
    try:produce_kind2_pickup135(direct,world)
    except PendingSupplyKind2135:answers.append('marker2_original_post_compaction_trap_pending')
    else:raise AssertionError('Original marker2 panic silently converted to return')
    return answers


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=('pilot','full'),default='pilot');args=parser.parse_args()
    assert SOURCE_BEFORE=={n:sha(ROOT/n)for n in FILES}
    world_inputs={str(ASSET_WORLD/n):sha(ASSET_WORLD/n)for n in(*HASHES,'receipt.json')}
    cases,expected,labels=corpus(args.phase=='full');refusals=refusal_checks(cases);assert len(cases)<=128
    assert SOURCE_BEFORE=={n:sha(ROOT/n)for n in FILES}and all(sha(Path(p))==h for p,h in world_inputs.items())
    out,manifest=private_build();trace_supply_kind2_135(out)
    for name,h in SOURCE_BEFORE.items():
        p=out/'source-snapshot'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());assert sha(p)==h
    for name,value in(('supply-input.json',cases),('supply-expected.json',expected),('supply-labels.json',labels),('supply-refusals.json',refusals)):save(out/name,value)
    assert(out/'supply-input.json').stat().st_size<=4194304 and(out/'supply-expected.json').stat().st_size<=4194304
    artifacts={n:sha(out/n)for n in('supply-input.json','supply-expected.json','supply-labels.json','supply-refusals.json','manifest.json',manifest['module_file'],'supply-kind2-static.json')}
    command=[str(NODE),'--expose-gc','--max-old-space-size=512','--wasm-max-mem-pages=512',str(ROOT/'scripts/run_supply_kind2_135_oracle.mjs'),str(out),str(out/'supply-input.json')]
    save(out/'supply-prepared.json',dict(source_sha256=SOURCE_BEFORE,artifacts=artifacts,world_inputs=world_inputs,cases=len(cases),expected_before_original=True,command=command,deadline_seconds=60))
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    began=time.monotonic();error=None
    def stop(sig,frame):raise KeyboardInterrupt('Owned supply stop '+str(sig))
    old=signal.signal(signal.SIGTERM,stop)
    with(out/'supply-results.jsonl').open('wb')as stdout,(out/'supply-stderr.log').open('wb')as stderr:
        child=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,TMPDIR=str(out),PYTHONDONTWRITEBYTECODE='1'))
        save(out/'supply-owned-process.json',dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=60))
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
    save(out/'supply-process-terminal.json',terminal);errors=[];counts=Counter();runtime=None
    if(out/'supply-kind2-runtime.json').exists():runtime=json.loads((out/'supply-kind2-runtime.json').read_text())
    if child.returncode==0:
        actual=[json.loads(row)for row in(out/'supply-results.jsonl').read_text().splitlines()]
        errors,counts=compare(expected,actual,cases)
        assert runtime['fresh_instances']==len(cases)and runtime['actual_host_calls']==0 and runtime['stack_all_restored']
    save(out/'supply-differences.json',errors);after={n:sha(ROOT/n)for n in FILES}
    report=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',status='compared'if child.returncode==0 else'original_failed_or_incomplete',
        cases=len(cases),comparison_complete=child.returncode==0,differences=len(errors)if child.returncode==0 else None,comparison=dict(counts),pure_model_refusals=refusals,
        groups=dict(Counter(row['group']for row in labels)),source_files=len(FILES),source_sha256_before=SOURCE_BEFORE,source_sha256_after=after,
        source_unchanged=SOURCE_BEFORE==after,frozen_artifacts=artifacts,artifacts_unchanged=all(sha(out/n)==h for n,h in artifacts.items()),world_inputs=world_inputs,
        world_unchanged=all(sha(Path(n))==h for n,h in world_inputs.items()),expected_before_original=True,process=terminal,runtime=runtime,
        full880_frames=0,natural60_second_runs=0,amount_pointer_used_as_model_input=False,
        scope='Full1417kind2 declared emptyaux domain and complete947 single explicit~60 call, ordinary consumption retained separately, other timers explicitly future',
        pending=['Mode0 empty-vector caller-local amount provenance','Removedkind2 marker2 original post-compaction panic projection','Nonempty removedkind2 auxiliary ownership/drop','Primary-present nearest-miss low-address fallback','kind2 collection/effects','Natural60s/full880/native/fullgame'])
    save(out/'supply-kind2-comparison.json',report)
    print(json.dumps(dict(directory=str(out),cases=len(cases),differences=len(errors),first_errors=errors[:8],process=terminal,receipt_sha256=sha(out/'supply-kind2-comparison.json'))))
    if child.returncode or error or errors or not terminal['pid_missing']or not terminal['pgid_missing']or not report['source_unchanged']or not report['artifacts_unchanged']or not report['world_unchanged']:raise SystemExit(1)


if __name__=='__main__':main()
