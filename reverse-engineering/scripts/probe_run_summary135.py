#!/usr/bin/env python3
"""Pure-model event trace of seed0 first-rune route; never an oracle test.

The trace observes the actual accepted-death callbacks, including several in
one stage. New counter/history owners do not feed the frozen model. No source
is edited and no original program or captured running state is executed/read.
"""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'reconstruction')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from check_opening_combat135 import (load_independent_world, DEFAULT_WORLD,
        EmptyOpeningInput135, initialize_absent_companion_handoff,
        EmptyCompanionProfile135, from_opening_handoff, SpecialLocale2376_135,
        ELWYNN_ENGLISH_NAMES, EventWaveLocale135, FirstRuneRoute135, f,
        move_player135, step_frame, select)
    import core_spec.headless135 as headless
    import core_spec.ai_world135 as ai_world
    from core_spec.run_summary135 import (empty_constructor_counters135,
        accept_ordinary_death135, summary_counters135)
    from core_spec.incoming_history135 import from_raw_storage, append_incoming_history, projection
    from core_spec.incoming_source135 import resolve_incoming_source135, ordinary_english_source_names135
    from production_closure135 import production_sources135
    files = set(production_sources135(ROOT, 'core_spec.headless135',
        'core_spec.opening_handoff135', 'core_spec.run_summary135',
        'core_spec.incoming_history135', 'core_spec.incoming_source135'))
    files.update(('scripts/motion_route135.py', 'scripts/check_opening_combat135.py',
                  'scripts/probe_run_summary135.py'))
    before = {path: digest(ROOT / path) for path in sorted(files)}
    out = ROOT / 'evidence' / datetime.now(timezone.utc).strftime('run-summary135-model-events-%Y%m%dT%H%M%S.%fZ')
    out.mkdir()
    world, world_receipt, _ = load_independent_world(DEFAULT_WORLD)
    value = EmptyOpeningInput135(1, 1, 0, 0, 42)
    handoff = initialize_absent_companion_handoff(value, world,
        companion_profile=EmptyCompanionProfile135(()), title_utf8=b'Elwynn Forest',
        subtitle_utf8='The Defias Uprising — survive the onslaught!'.encode())
    state = from_opening_handoff(handoff, navigation_enabled=False,
        special_locale=SpecialLocale2376_135(ELWYNN_ENGLISH_NAMES),
        event_locale=EventWaveLocale135(0), banner_locale='en', motion_enabled=True,
        app_notification_next_id=1, resource_locale='en')
    counters = empty_constructor_counters135()
    history = from_raw_storage([], 0, 0)
    route = FirstRuneRoute135()
    dt = f.from_float(.1)
    events, incoming_events = [], []
    current = dict(frame=0, stage='entry', records=())
    names = ordinary_english_source_names135()
    old_death = headless.consume_ordinary_death
    old_cast_phase = headless._cast_phase
    old_ai_phase = headless._ai_phase
    old_world = ai_world.update_world_ordinary_units135
    old_incoming = ai_world.resolve_incoming_prefix

    def accepted_death(cast, damage, context, binding):
        nonlocal counters
        counters = accept_ordinary_death135(counters, damage)
        events.append(dict(frame=current['frame'], stage=current['stage'],
            now_bits=cast.combat.now_bits, guid=str(damage.target.target_id),
            applied=damage.applied, dead=damage.dead,
            rawU416=damage.target.elite_416, definition_pointer=binding.definition_pointer,
            counter_after=asdict(counters)))
        return old_death(cast, damage, context, binding)

    def incoming_prefix(source, amount, guid=0):
        nonlocal history
        result = old_incoming(source, amount, guid)
        event = dict(frame=current['frame'], stage=current['stage'],
            source_guid=str(guid), now_bits=source.now_bits, amount_bits=amount,
            result_stage=result.stage, result_status=result.status,
            hp_before_bits=source.hp_1528_bits, hp_after_prefix_bits=result.state.hp_1528_bits,
            damage_bits=result.amount_bits, absorbed_bits=result.absorbed_bits)
        if result.stage in ('scalar_nonfatal_projection', 'before_unresolved_death'):
            found = resolve_incoming_source135(current['records'], guid,
                resolved_definition_names=names)
            history = append_incoming_history(history, now_bits=source.now_bits,
                damage_bits=result.amount_bits, absorbed_bits=result.absorbed_bits,
                hp_after_prefix_bits=result.state.hp_1528_bits,
                maximum_hp_bits=current['maximum_hp_bits'], category=0,
                source_label=found.source_label, source_classification=found.source_classification,
                resolved_spell=None)
            event.update(history_header=dict(capacity=history.capacity, head=history.head, count=history.count),
                         source_label=found.source_label, source_classification=found.source_classification,
                         callbacks_complete=False)
        incoming_events.append(event)
        return result

    def world_ai(source, *args, **kwargs):
        current['records'] = source.records
        return old_world(source, *args, **kwargs)

    def cast_phase(source, delta, *, phase='owned'):
        current['stage'] = phase
        return old_cast_phase(source, delta, phase=phase)

    def ai_phase(source, delta):
        current.update(stage='ai',
                       maximum_hp_bits=dict(source.collection.level.derived_bits)[1536])
        return old_ai_phase(source, delta)

    # Observe each original model callback; preserve its result and exceptions.
    headless.consume_ordinary_death = accepted_death
    headless._cast_phase = cast_phase
    headless._ai_phase = ai_phase
    ai_world.resolve_incoming_prefix = incoming_prefix
    ai_world.update_world_ordinary_units135 = world_ai
    status = 'not_started'
    began = time.monotonic()
    completed = 0
    try:
        for index in range(921):
            current.update(frame=index+1, stage='full_frame',
                           maximum_hp_bits=dict(state.collection.level.derived_bits)[1536])
            for motion in route.before_frame(state, dt):
                state, moved = move_player135(state, motion['opcode'], bytes.fromhex(motion['payload24_hex']))
                assert moved == 'motion_core_projection'
            # The owning frozen implementation still executes its exact14 stages.
            new, stages, status = step_frame(state, dt)
            if status != 'ordered_frame_projection':
                break
            state = new
            completed = index + 1
            while state.collection.level.phase2587 == 2:
                cards = state.collection.level.candidates
                chosen = next((i for i, card in enumerate(cards) if card.variant == 'upgrade'), 0)
                state, status = select(state, chosen)
                if status not in ('running', 'choice_regenerated'):
                    raise RuntimeError('Selection ' + status)
    except Exception as error:
        status = type(error).__name__ + ': ' + str(error)
        failure = traceback.format_exc()
    else:
        failure = None
    finally:
        headless.consume_ordinary_death = old_death
        headless._cast_phase = old_cast_phase
        headless._ai_phase = old_ai_phase
        ai_world.resolve_incoming_prefix = old_incoming
        ai_world.update_world_ordinary_units135 = old_world
    unchanged = all(digest(ROOT / path) == expected for path, expected in before.items())
    result = dict(kind='pure_model_event_trace_not_original_differential', input=asdict(value),
        status=status, completed_frames=completed, failing_frame=current['frame'],
        seconds=time.monotonic()-began, original_calls=0, native_executions=0,
        frozen_model_was_not_fed_new_owners=True, run_summary=asdict(counters),
        seven_counters=list(summary_counters135(counters, state.collection.level, state.collection.currency)),
        accepted_death_events=events, incoming_prefix_events=incoming_events,
        history=projection(history), route_events=route.events,
        source_sha256=before, source_unchanged=unchanged, world_receipt=world_receipt,
        boundaries=['New owner is event-maintained, not part of the frozen headless state yet',
                    'Incoming history preserves prefixHP before callbacks; callbacks remain incomplete',
                    'No counter/historical value came from current record population or original output',
                    'This is independent-model tracing, not evidence of original parity'],
        failure=failure)
    (out / 'trace.json').write_text(json.dumps(result, indent=2) + '\n')
    assert unchanged
    print(json.dumps(dict(directory=str(out), trace_sha256=digest(out/'trace.json'),
        completed_frames=completed, status=status, accepted_deaths=len(events),
        incoming_prefix_calls=len(incoming_events), counters=asdict(counters), original_calls=0)))


if __name__ == '__main__':
    main()
