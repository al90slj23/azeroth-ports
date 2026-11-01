"""Independent135 ordinary-death and mixed pickup/XP consumers.

The cast state owns RNG until the death callback returns. LevelCycleState owns
HP/time/RNG during collection. DeathContext135 has no duplicate clock, HP or
RNG. Old arithmetic/56B codecs are reused as pure algorithms, not as evidence
that135 was tested. Placements and all source vectors are explicit inputs.
No original runtime, asset, index, save or network is read by production code.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .cast135 import CastState
from .candidates135 import Effect, Summon, generate_kind0_metadata
from .combat135 import DamageResult
from .currency134 import CurrencyState, apply_currency, mode_multiplier_bits
from .death_loot134 import OrdinaryDefinition, RewardSource, project_ordinary_rewards
from .level_cycle135 import LevelCycleState, gain_xp
from .pickup_entity134 import project_kind1_entity
from .pickups134 import (PickupRecord, PickupState, Placement, append_xp,
                         append_idle_currency, MessageProjection)
from .progression134 import round_85718_bits, trunc_sat_u32


def _u(value, width=32):
    if type(value) is not int or not 0 <= value < 1 << width:
        raise ValueError('Explicit unsigned integer required')
    return value


class PendingDeathPickup135(NotImplementedError):
    """The caller must resolve an unimplemented source before continuing."""


@dataclass(frozen=True)
class DeathContext135:
    records: tuple
    capacity: int
    spawn_counter: int
    message_sequence: int
    kill_cost_bits: int

    def __post_init__(self):
        if type(self.records) is not tuple or any(not isinstance(x, PickupRecord) for x in self.records):
            raise TypeError('Explicit ordered pickup records required')
        for value in (self.capacity, self.spawn_counter, self.message_sequence, self.kill_cost_bits):
            _u(value)
        if len(self.records) > self.capacity:
            raise ValueError('Pickup record count exceeds capacity')


@dataclass(frozen=True)
class OrdinaryDeathBinding135:
    definition: OrdinaryDefinition
    definition_pointer: int
    xp_placement: Placement
    currency_placement: Placement
    death_xyz: tuple | None = None
    movement_message: bool = False

    def __post_init__(self):
        if not isinstance(self.definition, OrdinaryDefinition):
            raise TypeError('Resolved72B ordinary definition fields required')
        _u(self.definition_pointer)
        if not self.definition_pointer:
            raise ValueError('Ordinary definition pointer cannot be null')
        if not isinstance(self.xp_placement, Placement) or not isinstance(self.currency_placement, Placement):
            raise TypeError('Resolved original XP/currency placements required')
        if self.death_xyz is not None:
            if type(self.death_xyz) is not tuple or len(self.death_xyz) != 3:
                raise TypeError('Explicit pre-hit interpolated death XYZ required')
            for bits in self.death_xyz:
                _u(bits)
        if type(self.movement_message) is not bool:
            raise TypeError('Explicit pre-hit active movement condition required')


@dataclass(frozen=True)
class DeathResult135:
    cast: CastState
    context: DeathContext135
    reward_requests: tuple
    draws: int
    pending: tuple
    death_xyz: tuple | None


def consume_ordinary_death(cast, damage, context, binding):
    """Continue after914's already-applied ordinary death core, in draw order.

    Explicit placements must be computed from the pre-hit spatial snapshot.
    The post-core UnitState has already cleared its movement duration; this
    function must not reinterpret that as an unmoving death position.
    """
    if not isinstance(cast, CastState) or not isinstance(damage, DamageResult):
        raise TypeError('Post-core cast and DamageResult required')
    if not isinstance(context, DeathContext135) or not isinstance(binding, OrdinaryDeathBinding135):
        raise TypeError('Explicit death context/binding required')
    if not damage.applied or not damage.dead or damage.target is None:
        raise ValueError('Only a newly accepted lethal hit reaches this consumer')
    target = damage.target
    if target.kind_40 != -1 or target.kind_64 != -1 or target.elite_244 != -1:
        raise PendingDeathPickup135('Nonordinary unit tags/death sources remain unresolved')
    if binding.definition.flag68:
        raise PendingDeathPickup135('Flagged definition/kind2 entity consumer remains unresolved')
    source = RewardSource(f.MASK, 0, f.MASK, binding.definition_pointer)
    reward = project_ordinary_rewards(binding.definition, cast.rng_words, source=source,
                                      accumulator_bits=context.kill_cost_bits)
    pickup = PickupState(context.records, context.capacity, context.spawn_counter,
                         context.message_sequence, cast.combat.now_bits)
    if reward.xp.amount:
        appended = append_xp(pickup, reward.xp.amount, binding.xp_placement)
        if appended.status != 'core_projection':
            raise PendingDeathPickup135(str(appended.pending))
        pickup = appended.state
    rng = reward.direct_rng_state
    draws = reward.direct_draws
    if reward.currency.chance_passed:
        entity = project_kind1_entity(rng, pickup.spawn_counter)
        appended = append_idle_currency(pickup, reward.currency.amount, binding.currency_placement,
                                       guid=entity.guid, counter_after=entity.counter2400)
        if appended.status != 'core_projection':
            raise PendingDeathPickup135(str(appended.pending))
        pickup = appended.state
        rng = entity.rng_state
        draws += entity.draws
    result = DeathContext135(pickup.records, pickup.capacity, pickup.spawn_counter,
                             (pickup.message_sequence + int(binding.movement_message)) & f.MASK,
                             reward.accumulator2412_bits)
    spatial = cast.spatial
    if binding.death_xyz is not None:
        spatial = tuple(replace(s, from_xy=binding.death_xyz[:2], to_xy=binding.death_xyz[:2])
                        if s.unit.target_id == target.target_id else s for s in spatial)
    return DeathResult135(replace(cast, rng_words=tuple(rng), spatial=spatial), result, reward.requests, draws,
        ('Resolved placement excludes terrain/navigation production',
         'Physical visual entities/messages/keyed fields, item/proc and other death events remain pending')
        + (() if binding.death_xyz is not None else ('Pre-hit death XYZ not supplied; endpoint freeze unresolved',)),
        binding.death_xyz)


class OrdinaryDeathConsumer135:
    """Small stateful adapter for cast135's per-hit continuation callback.

    Pure logic is consume_ordinary_death. The root controller may instead call
    it directly while threading its own context. Bindings use uint64 GUIDs.
    """
    def __init__(self, context, bindings):
        self.context = context
        self.bindings = dict(bindings)
        self.events = []

    def __call__(self, cast, damage):
        if damage.target is None or damage.target.target_id not in self.bindings:
            raise PendingDeathPickup135('No explicit ordinary death binding for this GUID')
        result = consume_ordinary_death(cast, damage, self.context,
                                       self.bindings[damage.target.target_id])
        self.context = result.context
        self.events.append(result)
        return result.cast


@dataclass(frozen=True)
class CollectionState135:
    level: LevelCycleState
    death: DeathContext135
    currency: CurrencyState
    player_xyz: tuple
    xp_queue: tuple
    xp_queue_capacity: int
    claims_empty: bool

    def __post_init__(self):
        if not isinstance(self.level, LevelCycleState) or not isinstance(self.death, DeathContext135):
            raise TypeError('Resolved level and death state required')
        if not isinstance(self.currency, CurrencyState):
            raise TypeError('Resolved currency state required')
        if self.currency.mode != self.level.stats.flag2574:
            raise ValueError('Mode snapshots disagree')
        if type(self.player_xyz) is not tuple or len(self.player_xyz) != 3:
            raise ValueError('Explicit player xyz required')
        for value in self.player_xyz:
            _u(value)
        if type(self.claims_empty) is not bool:
            raise TypeError('Claim producer state must be explicitly resolved')
        _u(self.xp_queue_capacity)
        if type(self.xp_queue) is not tuple or len(self.xp_queue) > self.xp_queue_capacity:
            raise ValueError('Explicit XP forwarding queue/capacity required')
        for row in self.xp_queue:
            if type(row) is not tuple or len(row) != 2:
                raise ValueError('XP queue rows must be peer/base pairs')
            for value in row:
                _u(value)


@dataclass(frozen=True)
class CollectionResult135:
    state: CollectionState135
    status: str
    xp_awards: tuple = ()
    coin_awards: tuple = ()
    removed_guids: tuple = ()
    messages: tuple = ()
    pending: tuple = ()
    #2862 writes attraction markers/arrival words before31731 compaction.
    #Physical owners need this ordered producer state, including removed rows.
    pre_compaction_records: tuple = ()
    growth_events: tuple = ()


# Actual18353 class-table+80, selected by the class byte before additive sources.
_CLASS_LEECH = {1:0x3c75c28f,2:0x3bc49ba6,3:0x3ba3d70a,4:0x3cf5c28f,
                5:0x3c656042,7:0,8:0x3ba3d70a,9:0x3c23d70a,11:0}


def damage_lifesteal_coefficient(level):
    """Full18353 coefficient from explicit ordered sources, without runtime IO."""
    if not isinstance(level, LevelCycleState):
        raise TypeError('Resolved level source vectors required')
    timed, item, adjustment = f.SIGN, f.SIGN, f.SIGN
    for record in level.sources.timed_records:
        if not f.to_float(record.expires_bits) > f.to_float(level.stats.now_bits):
            continue
        if record.definition_index >= len(level.sources.definitions):
            continue
        definition = level.sources.definitions[record.definition_index]
        if definition.kind == 27 and definition.modifier_tag & 255 == 14:
            timed = f.add(timed, f.mul(definition.value20_bits, f.from_u32(record.stack_count)))
    for source in level.sources.item_modifiers:
        if source.tag & 255 == 14:
            item = f.add(item, source.value_bits)
    for source in level.sources.adjustments:
        if source.tag & 255 == 18:
            adjustment = f.add(adjustment, source.value_bits)
    base = _CLASS_LEECH.get(level.stats.class_byte & 255, _CLASS_LEECH[1])
    return f.add(f.add(f.add(timed, base), item), adjustment)


def apply_damage_lifesteal(level, applied_damage_bits):
    """914's per-accepted-hit HP and keys22/28, before its death continuation.

    The damage word is914's final minimum1 damage, not clamped target HP loss.
    Heal accounting1453 and physical messages are retained as unknown outputs.
    The owner calls this for every accepted hit, including nonlethal hits.
    """
    _u(applied_damage_bits)
    coefficient = damage_lifesteal_coefficient(level)
    if not f.to_float(coefficient) > 0:
        return level
    request = f.mul(f.mul(applied_damage_bits, coefficient),
                    0x3f000000 if level.heal_gate387 > 4 else 0x3f800000)
    total = f.add(level.stats.current_hp_bits, request)
    maximum = dict(level.derived_bits)[1536]
    # Exact two orderedselect NaN-aware minimum used in914.
    first = maximum if f.is_nan(total) else total
    second = first if f.is_nan(maximum) else maximum
    after = first if f.to_float(second) > f.to_float(first) else second
    fields = dict(level.player_fields)
    import math
    def ceil_u(bits):
        value = f.to_float(bits)
        return trunc_sat_u32(f.from_float(math.ceil(value))) if math.isfinite(value) else trunc_sat_u32(bits)
    positive = 0 if f.is_nan(after) or not f.to_float(after) > 0 else after
    fields[22], fields[28] = ceil_u(positive), ceil_u(maximum)
    return replace(level, stats=replace(level.stats,current_hp_bits=after),
                   player_fields=tuple(sorted(fields.items())))


def _distance(record, xyz):
    dx, dy = f.sub(record.x_bits, xyz[0]), f.sub(record.y_bits, xyz[1])
    return sqrt_bits(f.add(f.mul(dx, dx), f.mul(dy, dy)))


def _max_min_delay(bits):
    bits = 0x3df5c28f if f.is_nan(bits) else bits
    return bits if f.to_float(bits) > f.to_float(0x3df5c28f) else 0x3df5c28f


def collect_pickups(state, now_bits):
    """Complete proven kind0/1 part of2862, with immediate XP side effects.

    Radius/player/time and eligibility are entry snapshots. After reverse
    ordered removal, each award reads the latest1564 or1588 multiplier. A
    level-up may alter later awards, while it cannot change this invocation's
    already selected indices. Arrival is ignored for a nearby kind1 coin.
    """
    if not isinstance(state, CollectionState135):
        raise TypeError('Resolved collection state required')
    _u(now_bits)
    if not state.claims_empty:
        return CollectionResult135(state, 'pending_claims', pending=('Claim GUID producer is unresolved',))
    records = list(state.death.records)
    if any(r.marker not in (0, 1) for r in records):
        raise ValueError('Canonical live markers0/1 required; sentinel2 is not a live record')
    if any(r.aux_capacity or r.aux_count for r in records):
        return CollectionResult135(state, 'pending_auxiliary_entities', pending=('Pickup auxiliary GUID destruction is unresolved',))
    level = replace(state.level, stats=replace(state.level.stats, now_bits=now_bits))
    radius = dict(level.derived_bits)[1560]
    now = f.to_float(now_bits)
    # Do not partially consume a branch whose side effects are not modeled.
    if any(r.kind >= 2 and f.to_float(_distance(r, state.player_xyz)) <= 3 for r in records):
        return CollectionResult135(state, 'pending_other_kind', pending=('Nearby kind>=2 consumer is unresolved',))
    messages = []
    sequence = state.death.message_sequence
    for index, record in enumerate(records):
        if record.kind or record.marker:
            continue
        distance = _distance(record, state.player_xyz)
        age = f.to_float(f.sub(now_bits, record.spawn_time_bits)) > 6
        if not age and not f.to_float(distance) <= f.to_float(radius):
            continue
        delay = _max_min_delay(f.div(distance, 0x42000000 if age else 0x41c00000))
        records[index] = replace(record, marker=1, arrival_bits=f.add(now_bits, delay))
        sequence = (sequence + 1) & f.MASK
        messages.append(MessageProjection('xp_attract', record.guid, sequence,
            (record.x_bits, record.y_bits, record.height_bits), state.player_xyz,
            delay, trunc_sat_u32(f.mul(delay, 0x447a0000))))
    pre_compaction_records=tuple(records)
    eligible = []
    for index, record in enumerate(records):
        if record.kind == 0:
            if record.marker and record.arrival_bits is None:
                raise ValueError('Marked XP requires an actual stored arrival word')
            collect = bool(record.marker and f.to_float(record.arrival_bits) <= now)
        elif record.kind == 1:
            collect = f.to_float(_distance(record, state.player_xyz)) <= f.to_float(radius)
            collect = collect or (record.marker == 1 and record.arrival_bits is not None
                                  and f.to_float(record.arrival_bits) <= now)
        else:
            collect = False
        if collect:
            eligible.append(index)
    currency = state.currency
    xp_queue, capacity = state.xp_queue, state.xp_queue_capacity
    xp_awards, coin_awards, removed = [], [], []
    growth_events = []
    for index in reversed(eligible):
        record = records.pop(index)
        removed.append(record.guid)
        messages.append(MessageProjection('pickup_despawn', record.guid))
        derived = dict(level.derived_bits)
        if record.kind == 0:
            if currency.mode:
                if len(xp_queue) == capacity:
                    capacity = max(4, capacity * 2)
                    if capacity > f.MASK:
                        raise PendingDeathPickup135('XP queue capacity overflow remains unresolved')
                xp_queue += ((currency.local_peer, record.amount),)
            factor = mode_multiplier_bits(currency.mode, currency.member_count,
                                          region_index=currency.region_index)
            scaled = f.mul(factor, f.mul(derived[1564], f.from_u32(record.amount)))
            rounded = round_85718_bits(scaled)
            if f.is_nan(rounded) or not f.to_float(rounded) > 1:
                rounded = 0x3f800000
            award = trunc_sat_u32(rounded)
            result = gain_xp(level, award)
            growth_events.extend(result.growth_events)
            level = result.state
            if result.status == 'pending_choice_world':
                # Actual2159 uses mode only after metadata/RNG generation:
                # mode0 additionally stops movement through35514. Preserve
                # that unresolved world effect instead of changing the mode.
                d, ci = dict(level.derived_bits), level.choice_inputs
                generated = generate_kind0_metadata(rng_words=level.rng_words,
                    class_byte=level.stats.class_byte, owned=ci.owned,
                    level=level.progression.level, luck_bits=d[1584], cooldown_bits=d[1544],
                    flag275=ci.flag275, flag2573=ci.flag2581,
                    blocked_ids=ci.blocked_ids, banished_keys=ci.banished_keys,
                    effects=tuple(Effect(x.tag & 255, x.value_bits) for x in level.sources.item_modifiers),
                    summons=tuple(Summon(x.kind, x.summon_state41) for x in level.sources.definitions), kind=0)
                level = replace(level, rng_words=generated.rng_words, candidates=generated.candidates,
                    phase2587=2, selection_kind2585=0,
                    generation_counter2400=(level.generation_counter2400 + 1) & f.MASK)
            elif result.status != 'core_projection':
                raise PendingDeathPickup135(str(result.pending))
            xp_awards.append(award)
        else:
            currency = replace(currency, multiplier_bits=derived[1588], player_fields=level.player_fields)
            result = apply_currency(currency, record.amount)
            if result.status != 'core_projection':
                raise PendingDeathPickup135(str(result.pending))
            currency = result.state
            level = replace(level, player_fields=currency.player_fields)
            coin_awards.append(result.award)
    currency = replace(currency, player_fields=level.player_fields,
                       multiplier_bits=dict(level.derived_bits)[1588])
    death = replace(state.death, records=tuple(records), message_sequence=sequence)
    updated = replace(state, level=level, death=death, currency=currency,
                      xp_queue=xp_queue, xp_queue_capacity=capacity)
    return CollectionResult135(updated, 'core_projection', tuple(xp_awards), tuple(coin_awards),
        tuple(removed), tuple(messages), ('Physical queues/visual entities/wire bytes and full frame scheduling remain unresolved',
        'Mode0 next-choice35514 movement-stop effects are pending; numeric metadata/control is projected'),
        pre_compaction_records=pre_compaction_records,growth_events=tuple(growth_events))
