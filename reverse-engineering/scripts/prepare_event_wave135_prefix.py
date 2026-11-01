#!/usr/bin/env python3
"""Independent model-only600-frame replay and next-frame pre-G2424 prefix.

Explicitly repeats the existing controlled14-entry composition's prefix once;
this is an input producer, not original601-frame validation. No file/snapshot
is read by this helper. Caller supplies the already independent world.
"""
from dataclasses import replace
from core_spec import headless135 as H
from core_spec.opening135 import EmptyOpeningInput135
from core_spec.opening_handoff135 import initialize_absent_companion_handoff
from core_spec.profile_companions135 import EmptyCompanionProfile135
from core_spec.special2376_notify135 import SpecialLocale2376_135,ELWYNN_ENGLISH_NAMES


def prepare_default_event_prefix135(world):
 handoff=initialize_absent_companion_handoff(EmptyOpeningInput135(1,1,0,0,42),world,companion_profile=EmptyCompanionProfile135(()),title_utf8=b'Elwynn Forest',subtitle_utf8=b'')
 state=H.from_opening_handoff(handoff,navigation_enabled=False,special_locale=SpecialLocale2376_135(ELWYNN_ENGLISH_NAMES));selections=[];dt=H.f.from_float(.1)
 for frame in range(600):
  state,_,status=H.step_frame(state,dt)
  if status!='ordered_frame_projection':raise RuntimeError('Independent600 prefix stopped: '+status)
  while state.collection.level.phase2587==2:
   cards=state.collection.level.candidates;index=next((i for i,c in enumerate(cards)if c.variant=='upgrade'),0);selections.append(dict(frame=frame,index=index,card=cards[index].ability_id));state,status=H.select(state,index)
   if status not in('running','choice_regenerated'):raise RuntimeError(status)
 prior=state;level=state.collection.level;now=H.f.add(level.stats.now_bits,dt);words=dict(state.initial_scalars)
 if not H.f.to_float(level.stats.now_bits)<60<=H.f.to_float(now):raise ValueError('Expected first contiguous f32 crossing60')
 if H.f.to_float(now)>=H.f.to_float(words[2440]):raise RuntimeError('Earlier G2440 event is outside prefix')
 state=replace(state,collection=replace(state.collection,level=replace(level,stats=replace(level.stats,now_bits=now))),frames=state.frames+1)
 prepared=H.prepare_player_update(state.collection.level,state.live_records,state.unspecified_live_words,now,dt,state.incoming.last_hit_1648_bits,explicit_other_sources_absent=True,periodic_input=())
 state=replace(state,collection=replace(state.collection,level=prepared.level),live_records=prepared.live_records,unspecified_live_words=prepared.unspecified_live_words)
 state=H._cast_phase(state,dt);state=H._tail_phase(state,'extra',dt);state=H._tail_phase(state,'owned_effects',dt);state=H._cast_phase(state,dt,phase='hits');state=H._cast_phase(state,dt,phase='area');state=H._effects_phase(state,dt);state=H._tail_phase(state,'deadline',dt);state=H._tail_phase(state,'secondary',dt);state=H._ai_phase(state,dt)
 result=H.collect_pickups(state.collection,now)
 if result.status!='core_projection':raise RuntimeError(result.status)
 if state.collection.level.stats.flag2574==0 and state.collection.level.phase2587==1 and result.state.level.phase2587==2:
  motion=H.moving_sequence_delta(state.records,now,auxiliary_motions=(),claims=());result=replace(result,state=replace(result.state,death=replace(result.state.death,message_sequence=(result.state.death.message_sequence+motion.count)&H.f.MASK)))
 state=H._sync_pickup_owner(replace(state,collection=result.state),pre_compaction_records=result.pre_compaction_records);state=H._tail_phase(state,'claims',dt)
 if state.tail.gate2579:raise RuntimeError('Unsupported alternate2579 gate')
 level=state.collection.level;frame=H.FrameInput(state.zone,now,dt,state.budget_bits,state.collection.death.kill_cost_bits,level.stats.flag2574,state.collection.currency.member_count,level.heal_gate387,words[2516],0,0,0,state.collection.player_xyz,state.previous_player_xyz,state.velocity_xy,state.flat_height_bits,level.rng_words,state.collection.death.spawn_counter,state.records,True)
 ordinary=H.step_ordinary_frame(frame,destination_slots=state.unit_storage,world=state.world,distance_map=state.distance_map,allow_unknown_storage_growth=state.allow_unknown_storage_growth)
 if ordinary.status!='ordinary_projection':raise RuntimeError(ordinary.status)
 return prior,state,frame,ordinary,selections
