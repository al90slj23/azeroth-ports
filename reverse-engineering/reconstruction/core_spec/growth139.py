"""Current1394677 numeric growth and real ordinary choice transition.

The initial source domain is HumanWarrior constructor state. The original
world stop/resume and UI strings remain explicit outside the empty-world
component; the model never changes phase/mode to evade2181.
"""
from dataclasses import dataclass, replace
import math
from . import binary32 as f
from .derived_stats139 import StatsInput, recalculate
from .initial_state139 import InitialState139
from .candidates139 import first_candidates139


class PendingGrowth139(NotImplementedError):
    pass


@dataclass(frozen=True)
class GrowthState139:
    level: int
    xp: int
    pending: int
    phase2587: int
    current_hp_bits: int
    derived_bits: dict
    player_fields: dict
    rng_words: tuple
    owned_records80: tuple
    racial_record80: bytes
    now_bits: int = 0
    selection_kind2585: int = 255
    generation_counter2400: int = 0
    flag275: int = 0
    flag2581: int = 0
    flags2576: int = 0
    gate2572: int = 0
    flags2573: int = 0
    mode2582: int = 0
    heal_gate387: int = 0
    source_counts: tuple = (0, 0, 0, 0, 0, 0, 0)
    blocked_count2092: int | None = 0
    banished_count2104: int | None = 0
    candidates: tuple = ()
    units432_cells: tuple = ()
    auxiliary112_cells: tuple = ()
    claims88_cells: tuple = ()
    live32_cells: tuple = ()


@dataclass(frozen=True)
class GrowthResult139:
    state: GrowthState139
    events: tuple
    levels_gained: int
    packets: tuple = ()
    presentation_pending: tuple = ('Level banner/heal/choice messages and UI allocation are not predicted here',)


def from_constructor139(initial, *, phase2587):
    if not isinstance(initial, InitialState139):
        raise TypeError('Actual independently constructed InitialState139 required')
    value = initial.input
    if (value.class_byte, value.race_byte, value.region_index) != (1, 1, 0):
        raise PendingGrowth139('First HumanWarrior/Elwynn constructor domain')
    if phase2587 != 1:
        raise PendingGrowth139('Explicit running component required;no phase0 bypass')
    derived = {int(k): v for k, v in initial.stats_result['derived_bits'].items()}
    return GrowthState139(1, 0, 0, phase2587, initial.stats_result['current_hp_bits'], derived,
        {int(k): v for k, v in initial.stats_result['object_fields'].items()}, initial.rng_words,
        tuple(bytes.fromhex(hx) for hx in initial.owned_records_hex), bytes.fromhex(initial.racial_record_hex))


def threshold139(level):
    if type(level) is not int or not 0 <= level <= f.MASK:
        raise ValueError('u32 level')
    n = f.from_u32(level - int(level != 0))
    value = f.add(f.add(f.mul(n, 0x40800000), 0x40a00000), f.mul(f.mul(n, 0x3eb33333), n))
    shifted = f.add(value, 0x3effffff | (value & f.SIGN))
    exponent = shifted >> 23 & 255
    if exponent <= 149:
        shifted &= f.SIGN if exponent < 127 else (-0x800000 >> (exponent - 127)) & f.MASK
    number = f.to_float(shifted)
    return 0 if not number > 0 else f.MASK if number >= 4294967295 else int(number)


def recalculate_growth139(state, level):
    if state.source_counts != (0,) * 7 or state.live32_cells:
        raise PendingGrowth139('Nonempty or unknown139 stat/live source producer')
    result = recalculate(StatsInput(class_byte=1, race_byte=1, level=level,
        old_max_hp_bits=state.derived_bits[1536], current_hp_bits=state.current_hp_bits,
        now_bits=state.now_bits, previous_speed_bits=0x40e00000,
        conditional268_bits=0, flag2574=state.mode2582,
        pool1532_bits=0, pool1536_bits=0, conditional1344_id=0, conditional1348_bits=0, pool768_bits=0))
    fields = dict(state.player_fields)
    fields.update({int(k): v for k, v in result['object_fields'].items()})
    return replace(state, level=level, current_hp_bits=result['current_hp_bits'],
                   derived_bits={int(k): v for k, v in result['derived_bits'].items()}, player_fields=fields)


def gain_xp139(state, amount):
    if not isinstance(state, GrowthState139):
        raise TypeError('GrowthState139 required')
    if type(amount) is not int or not 0 <= amount <= f.MASK:
        raise ValueError('u32 XP award')
    state = replace(state, xp=(state.xp + amount) & f.MASK)
    events = []
    while state.level <= 119 and state.xp >= threshold139(state.level):
        cost = threshold139(state.level)
        before = state.level
        state = replace(state, pending=(state.pending + 1) & f.MASK, xp=(state.xp - cost) & f.MASK)
        state = recalculate_growth139(state, before + 1)
        fields = dict(state.player_fields)
        fields[34] = state.level
        request = f.mul(state.derived_bits[1536], 0x3e4ccccd)
        if state.heal_gate387 > 4:
            request = f.mul(request, 0x3f000000)
        old_hp = state.current_hp_bits
        value = f.add(old_hp, request)
        hp = value if f.to_float(value) < f.to_float(state.derived_bits[1536]) else state.derived_bits[1536]
        fields[22] = max(0, math.ceil(f.to_float(hp)))
        fields[28] = max(0, math.ceil(f.to_float(state.derived_bits[1536])))
        state = replace(state, current_hp_bits=hp, player_fields=fields)
        events.append(dict(kind='level_up', before=before, after=state.level, threshold_spent=cost,
                           heal_request_bits=request, heal_delta_bits=f.sub(hp, old_hp)))
    fields = dict(state.player_fields)
    fields[716], fields[717] = state.xp, threshold139(state.level)
    state = replace(state, player_fields=fields)
    eligible = state.pending != 0 and state.phase2587 == 1 and not state.flags2576 & 1
    eligible = eligible and (state.gate2572 != 1 or state.flags2573 & 1)
    if eligible:
        # Full original2181 mode0 invokes35988→26364. Empty owners come
        # from1600 in this component;nonempty states must retain real owners.
        if state.units432_cells or state.auxiliary112_cells or state.claims88_cells:
            raise PendingGrowth139('Nonempty139 stop/resume owner continuation pending')
        result = first_candidates139(state.rng_words, state.owned_records80, state.level,
            luck_bits=state.derived_bits[1584], cooldown_bits=state.derived_bits[1544],
            blocked_count2092=state.blocked_count2092, banished_count2104=state.banished_count2104,
            flag275=state.flag275, flag2581=state.flag2581)
        state = replace(state, candidates=result.candidates, rng_words=result.rng_words,
            phase2587=2, selection_kind2585=0, generation_counter2400=(state.generation_counter2400 + 1) & f.MASK)
        events.append(dict(kind='candidate_choice', count=len(result.candidates), draws=result.draws))
    return GrowthResult139(state, tuple(events), sum(event['kind'] == 'level_up' for event in events))


def projection139(state):
    return dict(level=state.level, xp=state.xp, pending=state.pending, phase2587=state.phase2587,
        current_hp_bits=state.current_hp_bits, derived_bits={str(k): v for k, v in state.derived_bits.items()},
        player_fields={str(k): v for k, v in state.player_fields.items()}, rng_words=list(state.rng_words),
        candidates=[dict(variant=c.variant, tier=c.tier, ability_id=c.ability_id, owned_index=c.owned_index,
                         kinds=list(c.kinds), gold=c.gold) for c in state.candidates],
        selection_kind2585=state.selection_kind2585, generation_counter2400=state.generation_counter2400,
        owned_records80_hex=[v.hex() for v in state.owned_records80], flag2581=state.flag2581,
        flags2573=state.flags2573)
