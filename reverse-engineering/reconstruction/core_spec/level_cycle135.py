"""Independent 0.135.1 XP -> per-level stats/heal -> kind0 choice composition.

This is a gameplay-state projection, not the frame scheduler. All stat source
vectors are required explicit snapshots; producer discovery is separate. It
does not load the game, infer missing sources as empty, or execute original
code. Physical trees/queues, presentation messages and account heal logs remain
pending effects. Mode1 choice fixtures use the original world-effect guard.
StatScalars retains the StatsInput semantic labels flag2574/pool1532/pool1536;
their physical135 locations are2582/1444/1448, explicitly mapped by the runner.
"""
from dataclasses import asdict, dataclass, replace
import math

from . import binary32 as f
from .ability_state import AbilityRecord
from .candidates135 import (Effect, Owned, Summon, generate_kind0_metadata)
from .derived_stats135 import (StatsInput, Modifier, Adjustment, TimedRecord,
                              TimedDefinition, LiveEffect, recalculate)
from .progression134 import (ProgressionState, card_choice_eligible,
                            trunc_sat_u32, xp_threshold)


@dataclass(frozen=True)
class SourceDefinition:
    """Shared 36B G2052 vector; +4 and summon state are explicit source data."""
    kind: int
    value4_bits: int
    value20_bits: int
    modifier_tag: int
    summon_state41: int


@dataclass(frozen=True)
class StatSources:
    passives: tuple
    adjustments: tuple
    item_modifiers: tuple
    owned_skills: tuple
    timed_records: tuple
    definitions: tuple
    live_effects: tuple

    def __post_init__(self):
        for name in self.__dataclass_fields__:
            if not isinstance(getattr(self, name), tuple):
                raise TypeError('Every stat source must be an explicit tuple snapshot: ' + name)

    def keywords(self):
        return dict(passives=list(self.passives), adjustments=list(self.adjustments),
                    item_modifiers=list(self.item_modifiers), owned_skills=list(self.owned_skills),
                    timed_records=list(self.timed_records), live_effects=list(self.live_effects),
                    timed_definitions=[TimedDefinition(d.kind, d.value20_bits, d.modifier_tag)
                                       for d in self.definitions])


@dataclass(frozen=True)
class StatScalars:
    class_byte: int
    race_byte: int
    old_max_hp_bits: int
    current_hp_bits: int
    now_bits: int
    previous_speed_bits: int
    conditional268_bits: int
    flag2574: int
    pool1532_bits: int
    pool1536_bits: int
    conditional1344_id: int
    conditional1348_bits: int
    pool768_bits: int


@dataclass(frozen=True)
class ChoiceInputs:
    owned: tuple
    blocked_ids: tuple
    banished_keys: tuple
    flag275: int
    flag2581: int


@dataclass(frozen=True)
class LevelCycleState:
    progression: ProgressionState
    stats: StatScalars
    sources: StatSources
    derived_bits: tuple
    player_fields: tuple
    rng_words: tuple
    choice_inputs: ChoiceInputs
    candidates: tuple
    phase2587: int
    selection_kind2585: int
    generation_counter2400: int
    flags2576: int
    gate2572: int
    flags2573: int
    heal_gate387: int
    pool756_bits: int

    def __post_init__(self):
        if not isinstance(self.sources, StatSources) or not isinstance(self.stats, StatScalars):
            raise TypeError('Resolved stat sources and scalar snapshot are mandatory')
        if len(self.rng_words) != 4 or any(type(x) is not int or not 0 <= x <= f.MASK for x in self.rng_words):
            raise ValueError('Four explicit u32 RNG words are required')
        for name in ('phase2587', 'selection_kind2585', 'flags2576', 'gate2572', 'flags2573', 'heal_gate387'):
            value = getattr(self, name)
            if type(value) is not int or not 0 <= value <= 255:
                raise ValueError('Expected explicit u8 ' + name)
        if tuple(sorted(self.derived_bits)) != self.derived_bits or len(dict(self.derived_bits)) != 23:
            raise ValueError('All 23 sorted derived words must be supplied')


@dataclass(frozen=True)
class LevelCycleResult:
    state: LevelCycleState
    status: str
    levels_gained: int
    level_events: tuple
    rng_draws: int
    pending: tuple


def _max_zero(bits):
    if f.is_nan(bits) or not f.to_float(bits) > 0:
        return 0
    return bits


def _ceil_u32(bits):
    number = f.to_float(bits)
    if math.isfinite(number):
        bits = f.from_float(math.ceil(number)) if number else bits
    return trunc_sat_u32(bits)


def _min_select(a, b):
    # Same explicit select order as10847, including opposite signed zeros.
    a = b if f.is_nan(a) else a
    b = a if f.is_nan(b) else b
    return a if f.to_float(a) < f.to_float(b) else b


def gain_xp(state, amount):
    """Execute each level's recalculation/heal before testing the next threshold.

    Level-up cause27960 has first word0. Consequently10847's real arg2==0
    guard omits kind32 overheal shield and kind33 accumulated-overheal writes;
    their definitions need not be empty and their state remains unchanged.
    The G387>4 half-heal applies before that guard and is implemented here.
    """
    if not isinstance(state, LevelCycleState):
        raise TypeError('Expected LevelCycleState')
    if type(amount) is not int or not 0 <= amount <= f.MASK:
        raise ValueError('XP amount must be u32')
    level, xp, pending = (state.progression.level,
                          (state.progression.xp + amount) & f.MASK,
                          state.progression.pending_upgrades)
    stats = state.stats
    derived = dict(state.derived_bits)
    fields = dict(state.player_fields)
    events = []
    while level < 120:
        needed = xp_threshold(level)
        if xp < needed:
            break
        level += 1
        xp = (xp - needed) & f.MASK
        pending = (pending + 1) & f.MASK
        fields[34] = level
        result = recalculate(StatsInput(level=level, **asdict(stats), **state.sources.keywords()))
        derived = {int(k): v for k, v in result['derived_bits'].items()}
        auxiliary = result['auxiliary_bits']
        before_heal = result['current_hp_bits']
        request = f.mul(derived[1536], 0x3e4ccccd)
        actual_request = f.mul(request, 0x3f000000 if state.heal_gate387 > 4 else 0x3f800000)
        after_heal = _min_select(f.add(before_heal, actual_request), derived[1536])
        fields.update({int(k): v for k, v in result['object_fields'].items()})
        #10847 always rewrites logical HP fields, even with cause id0.
        fields[22] = _ceil_u32(_max_zero(after_heal))
        fields[28] = _ceil_u32(derived[1536])
        stats = replace(stats, old_max_hp_bits=derived[1536], current_hp_bits=after_heal,
                        previous_speed_bits=result['speed_bits'],
                        pool1532_bits=auxiliary['1444'], pool1536_bits=auxiliary['1448'],
                        conditional1348_bits=auxiliary['1348'], pool768_bits=auxiliary['768'])
        events.append({'level': level, 'threshold_spent': needed,
                       'max_hp_bits': derived[1536], 'before_heal_bits': before_heal,
                       'heal_request_bits': actual_request, 'after_heal_bits': after_heal,
                       'heal_delta_bits': f.sub(after_heal, before_heal),
                       'xp_multiplier_bits': derived[1564], 'radius_bits': derived[1560]})
    fields[716] = xp
    fields[717] = xp_threshold(level)
    progress = ProgressionState(level, xp, pending)
    updated = replace(state, progression=progress, stats=stats,
                      derived_bits=tuple(sorted(derived.items())), player_fields=tuple(sorted(fields.items())))
    pending_effects = ('Physical keyed-tree/queue allocation, presentation messages and heal accounting logs',
                       'Stat-source producers and complete main-loop scheduling')
    if card_choice_eligible(pending, state.phase2587, state.flags2576, state.gate2572, state.flags2573):
        if stats.flag2574 != 1:
            return LevelCycleResult(updated, 'pending_choice_world', len(events), tuple(events), 0,
                pending_effects + ('Mode0 world-side choice effects35514 or other mode behavior remain pending',))
        choices = state.choice_inputs
        generated = generate_kind0_metadata(rng_words=state.rng_words, class_byte=stats.class_byte,
            owned=choices.owned, level=level, luck_bits=derived[1584], cooldown_bits=derived[1544],
            flag275=choices.flag275, flag2573=choices.flag2581,
            blocked_ids=choices.blocked_ids, banished_keys=choices.banished_keys,
            effects=tuple(Effect(e.tag & 255, e.value_bits) for e in state.sources.item_modifiers),
            summons=tuple(Summon(d.kind, d.summon_state41) for d in state.sources.definitions), kind=0)
        updated = replace(updated, rng_words=generated.rng_words, candidates=generated.candidates,
                          phase2587=2, selection_kind2585=0,
                          generation_counter2400=(state.generation_counter2400 + 1) & f.MASK)
        return LevelCycleResult(updated, 'core_projection', len(events), tuple(events), generated.rng_draws,
                                pending_effects + ('Candidate display payload, notifications and selection postprocessing',))
    return LevelCycleResult(updated, 'core_projection', len(events), tuple(events), 0, pending_effects)


def from_dict(raw):
    """Strict interchange: all sources and scalar fields must be supplied.

    Omitting a source vector is a constructor error, not an empty fallback.
    """
    sources = dict(raw['sources'])
    for name, constructor in (('passives', Modifier), ('adjustments', Adjustment),
                               ('item_modifiers', Modifier), ('timed_records', TimedRecord),
                               ('definitions', SourceDefinition), ('live_effects', LiveEffect)):
        sources[name] = tuple(constructor(**x) for x in sources[name])
    sources['owned_skills'] = tuple(tuple(x) for x in sources['owned_skills'])
    choice = dict(raw['choice_inputs'])
    choice['owned'] = tuple(Owned(x['ability_id'], AbilityRecord.from_bytes(bytes.fromhex(x['record_hex'])))
                            for x in choice['owned'])
    for name in ('blocked_ids', 'banished_keys'):
        choice[name] = tuple(choice[name])
    return LevelCycleState(progression=ProgressionState(**raw['progression']), stats=StatScalars(**raw['stats']),
        sources=StatSources(**sources), derived_bits=tuple(sorted((int(k), v) for k, v in raw['derived_bits'].items())),
        player_fields=tuple(sorted((int(k), v) for k, v in raw['player_fields'].items())),
        rng_words=tuple(raw['rng_words']), choice_inputs=ChoiceInputs(**choice), candidates=(),
        **{k: raw[k] for k in ('phase2587', 'selection_kind2585', 'generation_counter2400',
                               'flags2576', 'gate2572', 'flags2573', 'heal_gate387', 'pool756_bits')})


def projection(state):
    """Stable relevant-state surface for original differential fixtures."""
    return {'progression': asdict(state.progression), 'derived_bits': dict(state.derived_bits),
            'current_hp_bits': state.stats.current_hp_bits,
            'auxiliary_bits': {1444: state.stats.pool1532_bits, 1448: state.stats.pool1536_bits,
                               1348: state.stats.conditional1348_bits, 768: state.stats.pool768_bits,
                               756: state.pool756_bits},
            'speed_bits': state.stats.previous_speed_bits, 'player_fields': dict(state.player_fields),
            'rng_words': list(state.rng_words), 'candidates': [asdict(x) for x in state.candidates],
            'phase2587': state.phase2587, 'selection_kind2585': state.selection_kind2585,
            'generation_counter2400': state.generation_counter2400}
