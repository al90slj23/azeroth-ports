#!/usr/bin/env python3
"""Expected-first independent opening/world -> original same-G14-tail check.

The original side restores a declared historical linear-memory context, then
runs complete6730/1089 and unchanged component callees. Time is advanced by an
explicit external scheduler. This is not a full880 or fresh App/VM bootstrap.
"""
from pathlib import Path
from dataclasses import asdict
from functools import lru_cache
import argparse,gzip,hashlib,json,os,re,resource,signal,struct,subprocess,sys,time

sys.dont_write_bytecode=True
from build_full135_oracle import ROOT,SOURCE,SOURCE_SHA
from build_upgrade134_oracle import sha
from build_opening_combat135_oracle import build_opening_combat135,SNAPSHOT,SNAPSHOT_SHA,NODE,NODE_SHA
from production_closure135 import production_sources135
from check_opening_handoff135 import load_independent_world,DEFAULT_WORLD
sys.path.insert(0,str(ROOT/'reconstruction'))
from core_spec import binary32 as f
from core_spec.headless135 import from_opening_handoff,step_frame,select,move_player135,PendingHeadless135
from core_spec.opening135 import EmptyOpeningInput135
from core_spec.opening_handoff135 import initialize_absent_companion_handoff
from core_spec.profile_companions135 import EmptyCompanionProfile135
from core_spec.record_cells135 import cells135,UnknownRecordRead135
from core_spec.special2376_notify135 import SpecialLocale2376_135,ELWYNN_ENGLISH_NAMES
from core_spec.initial_state135_data import ZONE_ENTRIES
from core_spec.pickup_record_cells135 import pickup_words135
from core_spec.event_wave135 import EventWaveLocale135
from opening_pickup_provenance135 import PickupAddressVerifier135
from opening_npc_aura135 import npc_aura_updates169
from opening_live_auxiliary135 import LiveAuxiliaryVerifier135
from motion_route135 import FirstRuneRoute135


@lru_cache(maxsize=16)
def map_sha(values):return hashlib.sha256(b''.join(struct.pack('<H',x)for x in values)).hexdigest()


def create_guid169(payload):
    raw=bytes.fromhex(payload)
    if len(raw)<7 or raw[:5]!=b'\x01\x00\x00\x00\x00'or raw[5]not in(2,3):return None
    mask=raw[6];offset=7;guid=0
    for i in range(8):
        if mask>>i&1:
            if offset>=len(raw):raise ValueError('Truncated create GUID')
            guid|=raw[offset]<<(8*i);offset+=1
    return guid


def explicit_create_packets169(packets,known_guids=None):
    result=[]
    for opcode,payload in packets:
        if opcode!=169:continue
        guid=create_guid169(payload)
        if guid is not None and(known_guids is None or guid in known_guids):
            result.append(dict(guid=str(guid),payload169_hex=payload))
    return result


def resource_create_packets169(packets):
    """Retain every single-create actor packet with a resource-entry GUID.

    Other wire messages remain outside this composition's semantic coverage;
    resource packets compare exact payload, count and queue order.
    """
    result=[]
    for opcode,payload in packets:
        if opcode!=169:continue
        guid=create_guid169(payload)
        if guid is None:continue
        if guid>>48==0xf110 and (guid>>24)&0xffffff in(9006,9007,9008):
            result.append(dict(guid=str(guid),payload169_hex=payload))
    return result


def rune_notifications135(payloads):
    result=[]
    for payload in payloads:
        raw=bytes.fromhex(payload)
        try:value=json.loads(raw)
        except (ValueError,UnicodeDecodeError):continue
        if isinstance(value,dict)and value.get('type')=='banner'and value.get('kind')=='rune':
            result.append(payload)
    return result


def wanted(state):
    level=state.collection.level;tail=state.tail;path=state.distance_map
    if (state.effect_records120 or state.delayed_records56 or state.queued_hits
            or tail.active84_count or level.sources.timed_records or state.pending_banner_events):
        raise PendingHeadless135('Nonempty unmodeled payload vector is outside this comparison domain')
    def backing(rows,size):return[cells135(row,size)for row in rows]
    live=backing(state.live_records,32)
    for i,offset in state.unspecified_live_words:live[i][offset:offset+4]=[None]*4
    vectors={
        'units':dict(capacity=len(state.unit_storage),count=len(state.records),storage=backing(state.unit_storage,424)),
        'areas':dict(capacity=len(state.area_storage),count=len(state.areas),storage=backing(state.area_storage,88)),
        'pickups':dict(capacity=state.collection.death.capacity,count=len(state.collection.death.records),storage=backing(state.pickup_storage56,56)),
        'special':dict(capacity=len(tail.special40_storage),count=tail.special40_count,storage=backing(tail.special40_storage,40)),
        'companions':dict(capacity=len(tail.claims88_storage),count=tail.claims88_count,storage=backing(tail.claims88_storage,88)),
        'windows':dict(capacity=len(state.window_storage8),count=state.window_count,storage=backing(state.window_storage8,8)),
        'boundaries':dict(capacity=len(state.boundary_storage8),count=state.boundary_count,storage=backing(state.boundary_storage8,8)),
        'live32':dict(count=len(live),records=live),
        'effects120':dict(count=len(state.effect_records120)),
        'delayed56':dict(count=len(state.delayed_records56)),
        'hits112':dict(count=len(state.queued_hits)),
        'active84':dict(count=tail.active84_count),
        'timed12':dict(count=len(level.sources.timed_records)),
    }
    if state.player_sources is not None:
        owner=state.player_sources
        vectors['live32']=dict(capacity=owner.live.capacity,count=owner.live.count,
            storage=backing(owner.live.storage,32))
        vectors['aura48']=dict(capacity=owner.aura.capacity,count=owner.aura.count,
            storage=backing(owner.aura.storage,16))
    values=dict(level.derived_bits);progress=asdict(level.progression)
    projection=dict(phase2587=level.phase2587,now_bits=level.stats.now_bits,rng_words=list(level.rng_words),
        spawn_counter=state.collection.death.spawn_counter,message_sequence=state.collection.death.message_sequence,
        kill_cost_bits=state.collection.death.kill_cost_bits,source_id=str(state.source_id),map_id_utf8=ZONE_ENTRIES[state.zone][0],
        player_xyz=list(state.collection.player_xyz),velocity_xy=list(state.velocity_xy),previous_player_xyz=list(state.previous_player_xyz),
        progression={k:progress[k]for k in('level','xp','pending_upgrades')},current_hp_bits=level.stats.current_hp_bits,
        derived_bits={str(k):v for k,v in values.items()},player_fields={str(k):v for k,v in level.player_fields if k in(22,28,34,716,717,1109,1176)},
        racial_record_hex=state.racial.to_bytes().hex(),owned_records_hex=[x.record.to_bytes().hex()for x in level.choice_inputs.owned],
        pickup_words=[list(pickup_words135(p))for p in state.collection.death.records],timer1628_bits=state.melee_timer_bits,
        budget_bits=state.budget_bits,gold=state.collection.currency.gold,earned=state.collection.currency.earned,
        outgoing_total_hex=struct.pack('>d',state.outgoing_total).hex(),incoming_total_hex=struct.pack('>d',state.incoming.incoming_total_992).hex(),
        last_hit_bits=state.incoming.last_hit_1648_bits,absorbed740_bits=state.incoming.absorbed_740_bits,maximum_shield744_bits=state.incoming.maximum_shield_744_bits,
        candidates=[asdict(c)for c in level.candidates],selection_kind2585=level.selection_kind2585,generation_counter2400=level.generation_counter2400,
        field1092=state.special_field1092,mode2582=state.special_mode2582,
        next_resource2444_bits=state.next_resource2444_bits,
        next_event2424_bits=state.next_event2424_bits,last_event2586=state.last_event2586,
        next_supply2448_bits=state.next_supply2448_bits,
        resource_create_packets169=resource_create_packets169(state.produced_packets),
        explicit_actor_creates169=explicit_create_packets169(state.produced_packets),
        banner150_packets=[payload for opcode,payload in state.produced_packets if opcode==150],
        npc_aura_updates169=npc_aura_updates169(state.produced_packets),
        guardian_cooldowns=[dict(unit_index=x.unit_index,guid=str(x.guid),capacity=x.capacity,timers_bits=list(x.timers_bits),
            ability_pointer=x.ability_pointer,header_pointer=x.header_pointer,ability_records44_hex=list(x.ability_records44_hex),
            header28_hex=x.header28_hex)for x in state.guardian_cooldowns],
        special=dict(selected392=tail.special_selected392,target396=tail.special_target396,navigation2564=tail.special_navigation2564,
            announced2565=tail.special_announced2565,announcement_time2392_bits=tail.special_clock2392_bits),
        effect=dict(clock2364_bits=state.effect_clock2364_bits,effect_counter2356=state.effect_counter2356,
            action_sequence1644=state.action_sequence1644,player_action_tag416=state.player_action_tag416),
        tail_flags=dict(field400=tail.field400,protection2576=level.flags2576,flag2568=tail.flag2568,gate2579=tail.gate2579),
        distance_map=None if path is None else dict(count=len(path.values_u16),start_index=path.start_index,field24=path.field24,values_sha256=map_sha(path.values_u16)),
        distance_map_updated_at_bits=state.distance_map_updated_at_bits)
    if state.player_sources is not None:
        projection['player_fields']={str(k):v for k,v in level.player_fields}
        projection.update(aura_initialized2569=state.player_sources.aura.initialized2569,
            notification_next_id14340336=state.player_sources.notification_next_id14340336,
            player_speed226_packets=[payload for opcode,payload in state.produced_packets if opcode==226],
            rune_notifications=rune_notifications135(state.rune_notifications))
    if state.player_motion_owner is not None:
        from core_spec.headless_motion135 import MOTION_WORDS135
        from core_spec.record_cells135 import u32
        projection['motion_scalar_words']={str(o):u32(state.player_motion_owner.cells,o,'motion known word')
            for o in MOTION_WORDS135 if None not in state.player_motion_owner.cells[o:o+4]}
    result=dict(projection=projection,vectors=vectors,
        opaque_pickup_amount_origins=[asdict(origin)for origin in state.opaque_pickup_amount_origins])
    if state.player_sources is not None:
        result['unresolved_live_auxiliary_origins']=[dict(slot=i,source=list(origin))
            for i,origin in enumerate(state.player_sources.live_auxiliary_origins)if origin is not None]
    return result


def original_view(raw,expected):
    def subset(want,value):
        if isinstance(want,dict):return{k:subset(v,value[k])for k,v in want.items()}
        return value
    raw_projection=dict(raw['projection'])
    raw_projection['resource_create_packets169']=resource_create_packets169((p['opcode'],p['payload_hex'])for p in raw['packets']['active'])
    guids={int(item['guid'])for item in expected['projection']['explicit_actor_creates169']}
    raw_projection['explicit_actor_creates169']=explicit_create_packets169(
        ((p['opcode'],p['payload_hex'])for p in raw['packets']['active']),guids)
    raw_projection['banner150_packets']=[p['payload_hex']for p in raw['packets']['active']if p['opcode']==150]
    raw_projection['npc_aura_updates169']=npc_aura_updates169(
        (p['opcode'],p['payload_hex'])for p in raw['packets']['active'])
    if 'player_speed226_packets'in expected['projection']:
        raw_projection['player_speed226_packets']=[p['payload_hex']for p in raw['packets']['active']if p['opcode']==226]
        raw_projection['rune_notifications']=rune_notifications135(p['payload_hex']for p in raw['notifications']['active'])
    projection=subset(expected['projection'],raw_projection);vectors={}
    for name,want in expected['vectors'].items():
        value=raw['vectors'][name];v={}
        for key in want:
            if key=='storage':v[key]=[list(bytes.fromhex(row))for row in value['storage']]
            elif key=='records':v[key]=[list(bytes.fromhex(row))for row in value['storage'][:value['count']]]
            else:v[key]=value[key]
        vectors[name]=v
    return dict(projection=projection,vectors=vectors)


def compare(want,actual,path,errors,counts,*,opaque_pickup_indices=()):
    if want is None and re.search(r'\.vectors\.[^.]+\.(storage|records)\[\d+\]\[\d+\]$',path):
        assert type(actual)is int and 0<=actual<=255;counts['declared_unknown_cells']+=1;return
    if want is None and re.search(r'\.projection\.pickup_words\[\d+\]\[1\]$',path):
        assert type(actual)is int and 0<=actual<=f.MASK;counts['unwritten_pickup_arrivals']+=1;return
    if want is None:
        match=re.search(r'\.projection\.pickup_words\[(\d+)\]\[3\]$',path)
        if match and int(match.group(1))in opaque_pickup_indices:
            assert type(actual)is int and 0<=actual<=f.MASK
            counts['verified_opaque_pickup_amounts']+=1;return
    if type(want)is not type(actual):
        if len(errors)<80:errors.append(dict(field=path,expected=want,actual=actual))
        counts['differences']+=1;return
    if isinstance(want,dict):
        if set(want)!=set(actual):
            errors.append(dict(field=path,expected_keys=list(want),actual_keys=list(actual)));counts['differences']+=1;return
        for k,v in want.items():compare(v,actual[k],path+'.'+str(k),errors,counts,opaque_pickup_indices=opaque_pickup_indices)
    elif isinstance(want,list):
        if len(want)!=len(actual):
            if len(errors)<80:errors.append(dict(field=path,expected_length=len(want),actual_length=len(actual)))
            counts['differences']+=1
        for i,(a,b)in enumerate(zip(want,actual)):compare(a,b,path+f'[{i}]',errors,counts,opaque_pickup_indices=opaque_pickup_indices)
    else:
        counts['compared_leaves']+=1
        if want!=actual:
            counts['differences']+=1
            if len(errors)<80:errors.append(dict(field=path,expected=want,actual=actual))


def corpus(world,seed,frames,dt,expected_path,*,physical_player_sources=False,motion_route=False):
    value=EmptyOpeningInput135(1,1,0,seed,42)
    handoff=initialize_absent_companion_handoff(value,world,companion_profile=EmptyCompanionProfile135(()),
        title_utf8=b'Elwynn Forest',subtitle_utf8='The Defias Uprising — survive the onslaught!'.encode('utf8'))
    state=from_opening_handoff(handoff,navigation_enabled=False,special_locale=SpecialLocale2376_135(ELWYNN_ENGLISH_NAMES),
        event_locale=EventWaveLocale135(0),banner_locale='en',
        motion_enabled=motion_route,
        **(dict(app_notification_next_id=1,resource_locale='en')if physical_player_sources else{}))
    route=FirstRuneRoute135()if motion_route else None
    actions=[];boundary='frame_budget';stage_count=0;expected_bytes=0
    with gzip.open(expected_path,'wb',compresslevel=1)as stream:
        def emit(value):
            nonlocal expected_bytes
            raw=(json.dumps(value,separators=(',',':'))+'\n').encode()
            expected_bytes+=len(raw)
            if len(raw)>2*1024*1024 or expected_bytes>1024*1024*1024:
                raise ValueError('Bounded independent expectation stream exceeded')
            stream.write(raw)
        emit(dict(record_kind='opening',expected=wanted(state)))
        for _ in range(frames):
            if route is not None:
                for motion in route.before_frame(state,dt):
                    if len(actions)>=800:raise ValueError('Controlled motion/action budget exceeded')
                    state,status=move_player135(state,motion['opcode'],bytes.fromhex(motion['payload24_hex']))
                    if status!='motion_core_projection':raise ValueError('Controlled motion unexpectedly rejected')
                    action_index=len(actions);actions.append(motion)
                    emit(dict(record_kind='stage',stage_index=stage_count,action_index=action_index,
                        kind='motion',expected=wanted(state)))
                    stage_count+=1
            try:new,stages,status=step_frame(state,dt)
            except (NotImplementedError,UnknownRecordRead135)as error:
                boundary=type(error).__name__+': '+str(error);break
            if status!='ordered_frame_projection':boundary=status;break
            if len(actions)>=800:raise ValueError('Controlled action budget exceeded')
            action_index=len(actions);actions.append(dict(kind='controlled_tail_frame',dt_bits=dt));state=new
            for kind,snapshot in stages:
                emit(dict(record_kind='stage',stage_index=stage_count,action_index=action_index,kind=kind,expected=wanted(snapshot)))
                stage_count+=1
            choices=0
            while state.collection.level.phase2587==2:
                if choices>=64 or len(actions)>=800:raise ValueError('Controlled selection/action budget exceeded')
                cards=state.collection.level.candidates;index=next((i for i,c in enumerate(cards)if c.variant=='upgrade'),0)
                selected,status=select(state,index)
                if status not in('running','choice_regenerated'):
                    boundary='selection_status: '+status;break
                state=selected;choices+=1
                action_index=len(actions);actions.append(dict(kind='select',index=index))
                emit(dict(record_kind='stage',stage_index=stage_count,action_index=action_index,kind='select',expected=wanted(state)))
                stage_count+=1
            if boundary!='frame_budget':break
    raw=asdict(value);raw['app_lcg_seed_u64']=str(value.app_lcg_seed_u64);raw['object_id_u64']=str(value.object_id_u64);raw['companion_tags']=[255,255]
    return json.loads(json.dumps(dict(id=0,input=raw,actions=actions,stage_count=stage_count,boundary=boundary,
        independent_frames=state.frames,independent_selections=state.selections,final_level=state.collection.level.progression.level,
        expected_uncompressed_bytes=expected_bytes,
        **(dict(physical_player_sources=True,explicit_App_notification_counter=1)if physical_player_sources else{}),
        **(dict(motion_route='first_spawned_rune',motion_route_events=route.events,
            motion_actions=sum(a['kind']=='motion'for a in actions))if route is not None else{}))))


def main():
    from collections import Counter
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=('pilot','full'),default='pilot')
    parser.add_argument('--seed',type=int,default=0);parser.add_argument('--frames',type=int)
    parser.add_argument('--physical-player-sources',action='store_true')
    parser.add_argument('--motion-route',choices=('first-rune',))
    parser.add_argument('--capture-format',choices=('gzip','cas'),default='gzip');args=parser.parse_args()
    frames=args.frames if args.frames is not None else(1 if args.phase=='pilot'else 200)
    if not 1<=frames<=750:raise ValueError('Bounded controlled frame corpus required')
    cas_files=('scripts/run_opening_combat135_cas_oracle.mjs','scripts/opening_combat135_cas.mjs','scripts/opening_combat135_cas.py')if args.capture_format=='cas'else()
    files=tuple(dict.fromkeys(('scripts/check_opening_combat135.py','scripts/production_closure135.py',
        'scripts/check_opening_handoff135.py','scripts/build_opening_combat135_oracle.py','scripts/run_opening_combat135_oracle.mjs',
        'scripts/build_world_snapshot135_oracle.py','scripts/build_full135_oracle.py','scripts/build_upgrade134_oracle.py',
        'scripts/trace_coop.py','scripts/wasm_index.py','scripts/opening_pickup_provenance135.py','scripts/opening_npc_aura135.py',
        'scripts/opening_live_auxiliary135.py','scripts/motion_route135.py')+cas_files+production_sources135(ROOT,'core_spec.headless135','core_spec.opening_handoff135')))
    before={p:sha(ROOT/p)for p in files};world,world_receipt,world_inputs=load_independent_world(DEFAULT_WORLD)
    world_inputs.update({str(path):sha(path)for path in(DEFAULT_WORLD/'receipt.json',DEFAULT_WORLD/'inputs.json')})
    out,manifest=build_opening_combat135();source=out/'source-snapshot'
    for p,h in before.items():
        target=source/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/p).read_bytes());assert sha(target)==h
    expectations=out/'stage-expectations.jsonl.gz'
    row=corpus(world,args.seed,frames,f.from_float(.025 if args.phase=='pilot'else.1),expectations,
        physical_player_sources=args.physical_player_sources,motion_route=args.motion_route is not None)
    fixtures=out/'fixtures.json';fixtures.write_text(json.dumps(row,separators=(',',':'))+'\n')
    inputs=out/'inputs.json';inputs.write_text(json.dumps([{k:row[k]for k in('id','input','actions')}],separators=(',',':'))+'\n')
    config=dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,app_pointer=14549000,world_pointer=26204808,
        input_path=str(inputs),input_sha256=sha(inputs),clock_scheduler='explicit_external_f32_add_G2352_not_original880',
        locale=dict(kind='preserve_initialized_snapshot',expected_language_index=0))
    if args.motion_route is not None:
        if not args.physical_player_sources:raise ValueError('Motion route requires canonical physical player sources')
        config['app_game_domain']='typed_partial_inline_fixture_not_naturalApp'
    cfg=out/'config.json';cfg.write_text(json.dumps(config,indent=2)+'\n')
    frozen_paths=(fixtures,expectations,inputs,cfg,out/'manifest.json',out/manifest['module_file'])
    frozen={p.name:sha(p)for p in frozen_paths}
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA
    runner='run_opening_combat135_cas_oracle.mjs'if args.capture_format=='cas'else'run_opening_combat135_oracle.mjs'
    results=out/('results.cas.jsonl.gz'if args.capture_format=='cas'else'results.jsonl.gz');stderr=out/'stderr.log'
    command=[str(NODE),'--max-old-space-size=512','--wasm-max-mem-pages=4096',str(ROOT/'scripts'/runner),str(out),str(cfg)]
    began=time.monotonic();deadline_seconds=180 if args.capture_format=='cas'else 60
    child_usage_before=resource.getrusage(resource.RUSAGE_CHILDREN)
    deadline_exceeded=False
    with results.open('wb')as stdout,stderr.open('wb')as err:
        child=subprocess.Popen(command,stdout=stdout,stderr=err,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
        (out/'owned-process.json').write_text(json.dumps(dict(pid=child.pid,pgid=child.pid,command=command,deadline_seconds=deadline_seconds),indent=2)+'\n')
        try:
            while child.poll()is None:
                remaining=deadline_seconds-(time.monotonic()-began)
                if remaining<=0:deadline_exceeded=True;break
                try:child.wait(timeout=min(30,remaining))
                except subprocess.TimeoutExpired:continue
        finally:
            if child.poll()is None:
                os.killpg(child.pid,signal.SIGTERM)
                try:child.wait(timeout=3)
                except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
            child_seconds=time.monotonic()-began
            child_usage_after=resource.getrusage(resource.RUSAGE_CHILDREN)
            (out/'process-terminal.json').write_text(json.dumps(dict(pid=child.pid,pgid=child.pid,exit_code=child.returncode,
                deadline_exceeded=deadline_exceeded,deadline_seconds=deadline_seconds,seconds=child_seconds,
                child_cpu_user_seconds=child_usage_after.ru_utime-child_usage_before.ru_utime,
                child_cpu_system_seconds=child_usage_after.ru_stime-child_usage_before.ru_stime),indent=2)+'\n')
    def missing(group=False):
        try:(os.killpg if group else os.kill)(child.pid,0)
        except ProcessLookupError:return True
        return False
    terminal=dict(pid_missing=missing(),pgid_missing=missing(True));errors=[];counts=Counter();observed_stages=0
    raw_digest=hashlib.sha256();raw_bytes=0;max_line=0;cas_decoder=None;pickup_address_verifier=PickupAddressVerifier135()
    live_auxiliary_verifier=LiveAuxiliaryVerifier135()
    if child.returncode==0:
        record_counts=Counter()
        assert results.stat().st_size<=256*1024*1024
        if args.capture_format=='cas':
            from opening_combat135_cas import CaptureCAS135
            cas_decoder=CaptureCAS135(out)
        with gzip.open(results,'rb')as stream,gzip.open(expectations,'rt')as expected_stream:
            while line:=stream.readline(2*1024*1024+1):
                if len(line)>2*1024*1024 or not line.endswith(b'\n'):raise ValueError('Original record budget/truncation')
                raw_bytes+=len(line);max_line=max(max_line,len(line));raw_digest.update(line)
                if raw_bytes>1024*1024*1024:raise ValueError('Original uncompressed stream budget exceeded')
                raw=cas_decoder.decode_line(line)if cas_decoder is not None else json.loads(line)
                kind=raw['record_kind'];record_counts[kind]+=1
                assert raw['id']==0
                if kind in('opening','stage'):
                    wanted_stage=json.loads(next(expected_stream));assert wanted_stage['record_kind']==kind
                    if kind=='stage':
                        i=observed_stages;assert raw['stage_index']==i==wanted_stage['stage_index'] and i<row['stage_count']
                        for key in('action_index','kind'):compare(wanted_stage[key],raw[key],f'stage[{i}].{key}',errors,counts)
                        observed_stages+=1
                    path='opening'if kind=='opening'else f'stage[{observed_stages-1}]'
                    expected=wanted_stage['expected'];opaque_indices=pickup_address_verifier.observe(raw,expected)
                    live_auxiliary_verifier.observe(raw,expected)
                    comparable={key:value for key,value in expected.items()if key not in(
                        'opaque_pickup_amount_origins','unresolved_live_auxiliary_origins')}
                    compare(comparable,original_view(raw,expected),path,errors,counts,opaque_pickup_indices=opaque_indices)
                elif kind=='case_end':
                    assert raw['boundary']is None and raw['host_calls']==[]
                    assert raw['stage_count']==row['stage_count']
            assert next(expected_stream,None)is None
        assert all(record_counts[k]==1 for k in('case_start','constructor','opening','case_end'))
        assert record_counts['clock_control']==row['independent_frames']
        assert observed_stages==row['stage_count']
    else:errors.append(dict(field='original_exit',exit_code=child.returncode));counts['differences']+=1
    (out/'differences.json').write_text(json.dumps(errors,indent=2)+'\n')
    after={p:sha(ROOT/p)for p in files};assert before==after and frozen=={p.name:sha(p)for p in frozen_paths}
    assert all(sha(Path(p))==h for p,h in world_inputs.items())
    assert sha(SOURCE)==SOURCE_SHA and sha(NODE)==NODE_SHA and sha(SNAPSHOT)==SNAPSHOT_SHA
    runtime_path=out/('opening-combat135-cas-runtime.json'if args.capture_format=='cas'else'opening-combat135-runtime.json')
    runtime=json.loads(runtime_path.read_text())if runtime_path.exists()else None;cas_verification=None
    if child.returncode==0:
        assert runtime is not None,'Missing original runtime receipt'
        assert runtime['boundaries']==0 and runtime['cases']==1
        assert runtime['completed_stages']==row['stage_count']
        assert runtime['completed_controlled_tail_frames']==row['independent_frames']
        assert runtime['original_wasm_sha256']==SOURCE_SHA
        assert runtime['input_sha256']==sha(inputs)
        assert runtime['module_sha256']==manifest['module_sha256']
        assert runtime['denied_imports']==878 and runtime['host_imports_throw']is True
        if cas_decoder is not None:
            assert runtime['schema_version']==5 and runtime['output_protocol']=='bounded_stage_cas_jsonl_gzip'
            cas_verification=cas_decoder.finish(runtime['capture_cas'])
        else:assert runtime['schema_version']==4 and runtime['output_protocol']=='bounded_stage_jsonl_gzip'
        assert runtime['compressed_output_bytes']==results.stat().st_size and runtime['output_sha256']==sha(results)
        assert runtime['uncompressed_output_bytes']==raw_bytes and runtime['uncompressed_sha256']==raw_digest.hexdigest()
    report=dict(version='0.135.1',actual_build='90898d5e3',historical_build_alias='0898d5e3',kind='independent_opening_plus_controlled14_tail_declared_projection_differential',
        original_sha256=SOURCE_SHA,cases=1,independent_frames=row['independent_frames'],independent_selections=row['independent_selections'],
        requested_frames=frames,completed_requested_budget=row['independent_frames']==frames and row['boundary']=='frame_budget',
        status=('matched_requested_budget'if row['independent_frames']==frames and row['boundary']=='frame_budget'else'matched_prefix_with_pending')if counts['differences']==0 else'failed_preserved',
        compared_stages=observed_stages,final_level=row['final_level'],boundary=row['boundary'],differences=counts['differences'],comparison=dict(counts),
        source_files=len(files),source_sha256_before=before,source_sha256_after=after,
        inputs_sha256=sha(inputs),expectations_sha256=sha(expectations),fixtures_sha256=sha(fixtures),original_results_sha256=sha(results),runtime=runtime,
        capture_format=args.capture_format,capture_cas_verification=cas_verification,
        pickup_address_proof=pickup_address_verifier.report(),
        live_auxiliary_source_observations=live_auxiliary_verifier.report(),
        original_uncompressed_bytes=raw_bytes,maximum_original_record_bytes=max_line,expected_uncompressed_bytes=row['expected_uncompressed_bytes'],
        process=dict(command=command,pid=child.pid,pgid=child.pid,exit_code=child.returncode,seconds=child_seconds,
            total_seconds_including_verification=time.monotonic()-began,deadline_seconds=deadline_seconds,**terminal),
        model_expected_before_original=True,original_input_contains_no_expectations=True,
        physical_player_sources=args.physical_player_sources,
        motion_route=args.motion_route,
        world_input=dict(kind='independently_produced_preparsed_world_query_artifacts',receipt=str(DEFAULT_WORLD/'receipt.json'),receipt_sha256=sha(DEFAULT_WORLD/'receipt.json'),artifacts=world_inputs),
        original_context=dict(snapshot_path=str(SNAPSHOT),snapshot_sha256=SNAPSHOT_SHA,externref_VM_restoration=False,fresh_bootstraps=0),
        full880_frames=0,native_Windows_execution=False,playable_replacement=False,
        limitations=['Controlled external f32 time scheduler and14 component entries,not880 front/party/transport.',
            'World is independently produced canonical query input; this check does not rerun451-asset parser.',
            'Independent state retains None only from producer/consumer write sets; original buffers remain concrete.',
            'Original full raw captures retained. Only declared state projection/known record cells compared; unrelated allocator bytes/keyed fields/runtime packet producers remain unknown.',
            'Navigation preferenceFalse corresponds to declared snapshot App5165=0; actual menu defaults are another input domain.',
            'Original initialized locale is preserved, not reconstructed; model receives explicit static English names.'])
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'directory':str(out),'differences':counts['differences'],'frames':row['independent_frames'],'selections':row['independent_selections'],
        'compared_stages':row['stage_count'],'boundary':row['boundary'],'source_files':len(files),'exit_code':child.returncode,'terminal':terminal}))
    if counts['differences']or not all(terminal.values()):raise SystemExit(1)


if __name__=='__main__':main()
