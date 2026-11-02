"""Current139 natural-appseed Thunder opening and controlled midpoint inputs.

Only independent canonical world queries are consumed. No original program,
memory snapshot or oracle output is read. Selection is the actual first card.
"""
from dataclasses import replace
from .opening139 import DefaultOpeningInput139, initialize_default_opening139
from .opening_profile139 import EmptyAccountSources139
from .growth139 import from_constructor139
from .growth_world139 import gain_xp_world139, select_card_world139
from .player_update139 import PlayerUpdateState139, LiveVector139
from .player_effects139 import AuraSnapshot139, sync_aura139
from .death139 import position3_139
from . import binary32 as f


class PendingThunderWorld139(NotImplementedError):
    pass


def prepare_thunder_world139(app_seed_u64, world):
    opening = initialize_default_opening139(DefaultOpeningInput139(app_seed_u64,
        EmptyAccountSources139(0,0,0,0), tuple([0xa5]*40)), world)
    growth = replace(from_constructor139(opening.constructor, phase2587=1),
        rng_words=opening.rng_words, units432_cells=tuple(tuple(r) for r in
            opening.units['answers'][-1]['records432_cells']))
    gain = gain_xp_world139(growth, 5)
    card = gain.state.candidates[0]
    if card.variant != 'new' or card.ability_id != 'thunder_clap':
        raise PendingThunderWorld139('Actual first card is not new Thunder Clap')
    selected = select_card_world139(gain.state, 0)
    if not selected.accepted:
        raise PendingThunderWorld139('Actual first-card selection rejected')
    live = selected.state.live32_cells
    state = PlayerUpdateState139(selected.state,
        LiveVector139(live+tuple((None,)*32 for _ in range(4-len(live))),len(live)),
        tuple(opening.constructor.player_xyz),((),(),()),0,
        AuraSnapshot139.empty_constructor139())
    value = sync_aura139(dict(player_state=state,growth=state.growth,live=state.live,
        spell_sets=state.spell_sets,aura=state.aura_state,
        racial80=state.growth.racial_record80,player_xyz=state.player_xyz))
    return opening,gain,selected,value['player_state']


def midpoint_player139(records, first, second, now_bits, world):
    if first == second or not 0 <= first < len(records) or not 0 <= second < len(records):
        raise ValueError('Two distinct real NPC indices required')
    a,b = position3_139(records[first],now_bits),position3_139(records[second],now_bits)
    x,y = (f.mul(f.add(a[k],b[k]),0x3f000000) for k in (0,1))
    height = world.height(x,y)
    if not height.found:
        raise PendingThunderWorld139('Midpoint needs actual canonical map height')
    return x,y,height.value_bits
