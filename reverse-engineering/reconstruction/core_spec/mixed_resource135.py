"""Typed resource context bridge for the ordered fixed1352862 collector.

LevelCycleState remains the only HP/derived/time/RNG owner. This context
contains only physical live/aura and orthogonal wire counter/GUID sources.
Its semantic live view is checked before and updated with every effect.
The checked view preserves physical kind12/1020 and its unconsumed union bytes;
semantic value0 does not assert that those physical words contain zeros.
"""
from dataclasses import asdict, dataclass, fields, replace

from .candidates135 import DEFINITIONS
from .derived_stats135 import StatsInput
from .level_cycle135 import LevelCycleState, StatScalars
from .opening_npc_pickups135 import OpeningVector135
from .record_cells135 import u32, u64, put_u32
from .resource_aura135 import ResourceAuraState135
from .resource_consumer135 import (LiveVector135, ResourceConsumerState135,
    consume_resource135, _semantics)


class PendingMixedResource135(NotImplementedError):
    pass


def _word(value, bits=32):
    if type(value) is not int or not 0 <= value < 1 << bits:
        raise ValueError('Explicit mixed resource owner word required')


@dataclass(frozen=True)
class MixedResourceContext135:
    live: LiveVector135
    aura: ResourceAuraState135
    player_guid: int
    action_sequence1644: int
    notification_next_id14340336: int
    locale_code: str
    aura_external_sources_absent: bool

    def __post_init__(self):
        if not isinstance(self.live, LiveVector135) or not isinstance(self.aura, ResourceAuraState135):
            raise TypeError('Explicit physical live32/aura16 owners required')
        _word(self.player_guid, 64)
        _word(self.action_sequence1644)
        _word(self.notification_next_id14340336)
        if self.locale_code != 'en':
            raise PendingMixedResource135('Only explicit fixed135 English rune locale restored')
        if self.aura_external_sources_absent is not True:
            raise PendingMixedResource135('Other aura producers require an explicit continuation')


@dataclass(frozen=True)
class MixedResourceStep135:
    level: LevelCycleState
    context: MixedResourceContext135
    spawn_counter: int
    message_sequence: int
    packets: tuple
    notifications: tuple
    events: tuple


def owned_execution_snapshot135(level):
    """Resolve actual owned pointer84 bytes; no class/name-based inference."""
    result = []
    for owned in level.choice_inputs.owned:
        definition = DEFINITIONS.get(owned.ability_id)
        if definition is None or definition.pointer != owned.record.definition_pointer:
            raise PendingMixedResource135('Owned definition84 snapshot is unresolved')
        result.append(definition.execution)
    return tuple(result)


def validate_mixed_resource135(level, context):
    if not isinstance(level, LevelCycleState) or not isinstance(context, MixedResourceContext135):
        raise TypeError('Canonical level owner and typed resource context required')
    if tuple(_semantics(context.live)) != tuple(level.sources.live_effects):
        raise PendingMixedResource135('Physical live owner and LevelCycleState semantic live view disagree')


def consume_mixed_resource135(level, spawn_counter, message_sequence, context, kind):
    validate_mixed_resource135(level, context)
    _word(spawn_counter); _word(message_sequence)
    stats = StatsInput(level=level.progression.level, **asdict(level.stats), **level.sources.keywords())
    state = ResourceConsumerState135(stats, level.derived_bits, level.player_fields,
        context.live, level.heal_gate387, level.rng_words, spawn_counter, message_sequence,
        context.action_sequence1644, context.player_guid, context.aura,
        context.aura_external_sources_absent, context.notification_next_id14340336, context.locale_code)
    consumed = consume_resource135(state, kind)
    result = consumed.state
    scalars = StatScalars(**{field.name: getattr(result.stats, field.name) for field in fields(StatScalars)})
    level = replace(level, stats=scalars, derived_bits=result.derived_bits,
        player_fields=result.player_fields, rng_words=result.rng_words,
        sources=replace(level.sources, live_effects=tuple(_semantics(result.live))))
    context = replace(context, live=result.live, aura=result.aura,
        action_sequence1644=result.action_sequence1644,
        notification_next_id14340336=result.notification_next_id14340336)
    validate_mixed_resource135(level, context)
    return MixedResourceStep135(level, context, result.counter2408,
        result.message_sequence2412, consumed.packets, consumed.notifications, consumed.events)


def project_mixed_pickup_storage135(vector, initial_records, result):
    """Apply only2862's attraction writes and reverse56B memmoves.

    The semantic records are a checked view of this caller-owned physical
    vector. Unwritten arrival, padding and opaque kind2 amount cells remain
    untouched; the helper never re-encodes an entire semantic row as zeros.
    """
    if not isinstance(vector, OpeningVector135) or vector.stride != 56:
        raise TypeError('Explicit complete physical56B pickup owner required')
    if result.status != 'core_projection' or vector.count != len(initial_records):
        raise PendingMixedResource135('Completed collection and matching entry views required')
    if len(result.pre_compaction_records) != vector.count:
        raise ValueError('Attraction producer view lost a physical record')
    rows = [list(row) for row in vector.storage]
    names = ((0, 'marker'), (8, 'kind'), (12, 'amount'), (24, 'aux_capacity'),
        (28, 'aux_pointer'), (32, 'aux_count'), (36, 'visual_id'), (40, 'x_bits'),
        (44, 'y_bits'), (48, 'height_bits'), (52, 'spawn_time_bits'))
    for index, (record, produced) in enumerate(zip(initial_records, result.pre_compaction_records)):
        row = rows[index]
        if u64(row, 16, 'Mixed pickup GUID') != record.guid:
            raise ValueError('Physical pickup GUID disagrees with semantic owner')
        for offset, name in names:
            value = getattr(record, name)
            if value is None:
                if name != 'amount' or record.kind != 2 or tuple(row[12:16]) != (None,) * 4:
                    raise ValueError('Only exact unconsumed kind2 amount word may be opaque')
                continue
            if u32(row, offset, 'Mixed pickup ' + name) != value:
                raise ValueError('Physical pickup field disagrees with semantic view: ' + name)
        if record.arrival_bits is not None and u32(row, 4, 'Mixed arrival') != record.arrival_bits:
            raise ValueError('Physical arrival disagrees with semantic owner')
        if produced.marker != record.marker:
            if record.kind != 0 or record.marker != 0 or produced.marker != 1 or produced.arrival_bits is None:
                raise PendingMixedResource135('Unexpected producer outside2862 attraction')
            put_u32(row, 0, 1)
            put_u32(row, 4, produced.arrival_bits)
        elif produced.arrival_bits != record.arrival_bits:
            raise PendingMixedResource135('Unexpected arrival write without attraction marker')
    count = vector.count
    previous = count
    for index, kind, guid in result.consumption_order:
        if not 0 <= index < count or index >= previous:
            raise ValueError('Consumption indices must be the original strict reverse selection order')
        if u32(rows[index], 8, 'Removed kind') != kind or u64(rows[index], 16, 'Removed GUID') != guid:
            raise ValueError('Ordered semantic removal disagrees with physical row')
        for destination in range(index, count - 1):
            rows[destination] = rows[destination + 1].copy()
        count -= 1
        previous = index
    if count != len(result.state.death.records) or tuple(
        u64(row, 16, 'Retained GUID') for row in rows[:count]) != tuple(
            record.guid for record in result.state.death.records):
        raise ValueError('Final semantic/physical pickup owners disagree')
    return OpeningVector135(56, tuple(tuple(row) for row in rows), count)
