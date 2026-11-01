#!/usr/bin/env python3
"""Run the independent numeric research composition without game binaries."""
import argparse
import json

from core_spec import binary32 as f
from core_spec.initial_state135 import ConstructorInput135, initialize_empty_profile
from core_spec.headless135 import (from_initial, resolve_controlled_entry, step_frame,
                                  select, PendingHeadless135)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed', type=int, default=1)
    p.add_argument('--frames', type=int, default=250)
    p.add_argument('--class-id', type=int, default=8)
    p.add_argument('--race-id', type=int, default=1)
    p.add_argument('--zone', type=int, default=0)
    p.add_argument('--research-resolved-entry', action='store_true',
        help='Explicitly supply phase1 research input; does not implement1089/resource boot.')
    args = p.parse_args()
    if not 1 <= args.frames <= 2000: p.error('frames must be1..2000')
    initial = initialize_empty_profile(ConstructorInput135(args.class_id, args.race_id,
        args.zone, args.seed, 42, 0))
    state = from_initial(initial, flat_height_bits=0, zeroed_unit_storage_resolved=True,
        zeroed_area_storage_resolved=True)
    events, boundary = [], 'pending_real_phase_entry'
    if args.research_resolved_entry:
        state = resolve_controlled_entry(state, phase1_entry_explicitly_resolved=True)
        boundary = 'frame_budget'
        for frame in range(args.frames):
            try:
                state, _, status = step_frame(state, f.from_float(.1))
            except (PendingHeadless135, NotImplementedError, ValueError) as exc:
                boundary = 'unresolved_model_branch'
                events.append(dict(frame=frame, reason=str(exc))); break
            if status != 'ordered_frame_projection': boundary = status; break
            if state.collection.level.phase2587 == 2:
                cards = state.collection.level.candidates
                index = next((i for i, card in enumerate(cards) if card.variant == 'upgrade'), 0)
                card = cards[index]
                events.append(dict(frame=frame, time=f.to_float(state.collection.level.stats.now_bits),
                    level=state.collection.level.progression.level, chosen_index=index,
                    variant=card.variant, ability=card.ability_id, kinds=list(card.kinds)))
                state, status = select(state, index)
    print(json.dumps(dict(version='0.135.1', build='0898d5e3',
        implementation='independent Python arithmetic; no original runtime loaded',
        scope='flat-world ordered-entry research composition; complete game is not reconstructed',
        controlled_phase1=args.research_resolved_entry, boundary=boundary, frames=state.frames,
        simulation_seconds=f.to_float(state.collection.level.stats.now_bits),
        level=state.collection.level.progression.level, xp=state.collection.level.progression.xp,
        hp=f.to_float(state.collection.level.stats.current_hp_bits), selections=state.selections,
        gold=state.collection.currency.gold,
        learned=[entry.ability_id for entry in state.collection.level.choice_inputs.owned],
        events=events), ensure_ascii=False, indent=2))


if __name__ == '__main__': main()
