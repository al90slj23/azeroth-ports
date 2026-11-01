"""Independent0.135.1 thunder_clap execution2 /2244 effect1 projection.

No original, assets, runtime outputs or oracle data are read. Resolved empty
item/proc sources are the existing CastState contract. Nonempty effect49
overrides, presentation packets and unresolved death/proc producers are pending.
The existing dispatcher/gates are unchanged; callers opt into this component.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .cast135 import (CastResult, CastDeathBoundary, UnresolvedCast, base_damage,
                      query_targets, _critical, _updated_combat)
from .cast_events135 import apply_hit, cast_ability as cast_common
from .owned_cast135 import OwnedEntry135, tick_owned
from .radius import radius_bits


@dataclass(frozen=True)
class ThunderClapResult135(CastResult):
    """Ordered physical2244 writes: (GUID, byte offset, binary32 word)."""
    effect_writes: tuple = ()


@dataclass(frozen=True)
class ThunderClapOwnedEntry135(OwnedEntry135):
    def __post_init__(self):
        _require(self.definition)
        if self.record.definition_pointer != self.definition.pointer:
            raise ValueError('Resolved thunder_clap definition required')


def _require(definition):
    if (definition.pointer != 5467604 or definition.ability_id != b'thunder_clap'
            or definition.execution_kind != 2 or definition.effect_tag != 1
            or definition.spell_id != 6343 or definition.school != 0):
        raise UnresolvedCast('Only fixed135 thunder_clap execution2/effect1')


def _slow(state, guid, duration_bits):
    #2244 scans from the start, accepts marker!=1 and overwrites existing124,
    #rather than taking max(existing124, now+duration). U356 is unchanged in
    #the empty effect49-source branch. Effect processing follows914 even when
    #damage was rejected by phase/protection; it is not an accepted-hit event.
    for i, unit in enumerate(state.combat.units):
        if unit.target_id == guid and unit.marker != 1:
            until = f.add(state.combat.now_bits, duration_bits)
            units = list(state.combat.units)
            units[i] = replace(unit, control_until_124_bits=until)
            state = _updated_combat(state, replace(state.combat, units=tuple(units)))
            return state, ((guid, 124, until), (guid, 120, 0x3f000000))
    return state, ()


def cast_thunder_clap135(state, definition, owned, *, after_hit=None,
                        after_death=None, slow_overrides=()):
    """Full known numeric branch with ordered damage→slow for each target.

    Explicit effect49 override rows are outside this projection. The function
    rejects them before mutating state. Ordinary/death consumers follow the
    shared accepted-hit contract; an unresolved lethal hit stops before2244.
    ``owned.duration_bits`` is deliberately not used by original execution2.
    """
    _require(definition)
    if type(slow_overrides) is not tuple:
        raise TypeError('Explicit ordered effect49 source snapshot required')
    if slow_overrides:
        raise UnresolvedCast('2244 effect49 override-source lookup is pending')
    if state.context908 != 0:
        raise UnresolvedCast('Inherited proc context requires separate recovery')
    if owned.definition_pointer != definition.pointer:
        raise ValueError('Owned definition pointer differs')
    base = base_damage(state, definition, owned)
    attempts = state.attempted_spell_ids
    if definition.spell_id not in attempts:
        attempts += (definition.spell_id,)
    state = replace(state, attempted_spell_ids=attempts)
    radius = f.mul(owned.area_bits, owned.additional_area_bits)
    radius = f.mul(definition.radius_bits, radius)
    radius = radius_bits(f.mul(state.area_multiplier_bits, radius))
    targets = query_targets(state.spatial, state.player_xy, radius, state.combat.now_bits)
    duration = f.mul(0x40400000, owned.additional_duration_bits)
    hits, writes = [], []
    for index, guid in enumerate(targets):
        state, damage, critical = _critical(state, base)
        try:
            state, result = apply_hit(state, guid, damage, definition.spell_id,
                after_hit=after_hit, after_death=after_death)
        except CastDeathBoundary as boundary:
            boundary.remaining_targets = targets[index + 1:]
            #The caller must complete this target's original death continuation
            #before its2244 effect, then proceed to the remaining target list.
            boundary.pending_thunder_clap_effect = (guid, duration)
            boundary.completed_effect_writes = tuple(writes)
            raise
        state, effect = _slow(state, guid, duration)
        writes.extend(effect)
        hits.append((guid, damage, critical, result.new_hp_bits))
    return ThunderClapResult135(state, int(bool(targets)), targets, base, radius,
        tuple(hits), status='thunder_clap_numeric_effect1_projection', effect_writes=tuple(writes))


def cast_dispatch_thunder_clap135(state, definition, owned, **kwargs):
    dispatcher = cast_thunder_clap135 if definition.ability_id == b'thunder_clap' else cast_common
    return dispatcher(state, definition, owned, **kwargs)


def tick_owned_thunder_clap135(state, entries, basic, dt_bits, **kwargs):
    if 'cast_dispatch' in kwargs:
        raise TypeError('This wrapper owns its explicit cast dispatcher')
    return tick_owned(state, entries, basic, dt_bits,
        cast_dispatch=cast_dispatch_thunder_clap135, **kwargs)
