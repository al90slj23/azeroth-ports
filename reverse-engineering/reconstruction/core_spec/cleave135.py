"""Independent 0.135.1 Warrior cleave, execution kind5/effect0.

Definitions and source snapshots are explicit inputs. This module reads no
original program, assets or oracle outputs. It opts into the recovered cleave
branch without changing the older execution0/2 dispatcher or owned entry gate.
Presentation packet bytes and nonempty item/talent/proc sources remain outside
this projection; accepted-hit/death consumers are required by the shared model.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .cast135 import (CastResult, UnresolvedCast, CastDeathBoundary, base_damage,
                      projectile_targets, _critical)
from .cast_events135 import apply_hit, cast_ability as cast_common
from .owned_cast135 import OwnedEntry135, tick_owned


def _require_cleave(definition):
    if (definition.ability_id != b'cleave' or definition.execution_kind != 5
            or definition.effect_tag != 0 or definition.spell_id != 845):
        raise UnresolvedCast('Only recovered execution5 cleave/effect0 is supported')


@dataclass(frozen=True)
class CleaveOwnedEntry135(OwnedEntry135):
    """Opt-in cleave entry; G1256 tests use an isolated effect0 slot fixture.

    The inherited ``basic`` API name does not describe the real racial80 slot.
    The default OwnedEntry135 remains unchanged.
    """

    def __post_init__(self):
        _require_cleave(self.definition)
        if (not self.definition.pointer
                or self.record.definition_pointer != self.definition.pointer):
            raise ValueError('Resolved nonnull cleave definition required')


def cast_cleave135(state, definition, owned, *, after_hit=None, after_death=None):
    """Select the priority prefix in range, then apply one immediate hit each.

    Cleave ignores area multipliers. Its count additions wrap as u32 before a
    minimum of one and truncation to available targets. Selection precedes all
    damage so accepted-hit/death consumers cannot retroactively change it.
    Critical RNG is consumed even when914 later rejects the chosen target.
    """
    _require_cleave(definition)
    if owned.definition_pointer != definition.pointer:
        raise ValueError('Owned definition pointer differs')
    if state.context908 != 0:
        raise UnresolvedCast('Inherited proc context requires separate recovery')
    base = base_damage(state, definition, owned)
    attempts = state.attempted_spell_ids
    if definition.spell_id not in attempts:
        attempts += (definition.spell_id,)
    state = replace(state, attempted_spell_ids=attempts)
    count = 1 if definition.count == 0 else max(1,
        (definition.count + owned.extra_targets + owned.additional_targets
         + state.extra_targets) & f.MASK)
    targets = projectile_targets(state, definition.range_bits)[:count]
    hits = []
    for index, guid in enumerate(targets):
        state, damage, critical = _critical(state, base)
        try:
            state, result = apply_hit(state, guid, damage, definition.spell_id,
                after_hit=after_hit, after_death=after_death)
        except CastDeathBoundary as boundary:
            boundary.remaining_targets = targets[index + 1:]
            raise
        hits.append((guid, damage, critical, result.new_hp_bits))
    return CastResult(state, int(bool(targets)), targets, base,
        definition.range_bits, tuple(hits), status='cleave_core_projection')


def cast_dispatch135(state, definition, owned, *, after_hit=None, after_death=None):
    """Opt-in cleave plus the existing execution0/2 accepted-hit dispatcher."""
    dispatcher = cast_cleave135 if definition.execution_kind == 5 else cast_common
    return dispatcher(state, definition, owned, after_hit=after_hit,
        after_death=after_death)


def tick_owned_cleave135(state, entries, basic, dt_bits, **kwargs):
    """Use the existing1076 scheduler with the explicit cleave dispatcher."""
    if 'cast_dispatch' in kwargs:
        raise TypeError('This wrapper owns its explicit cast dispatcher')
    return tick_owned(state, entries, basic, dt_bits,
        cast_dispatch=cast_dispatch135, **kwargs)
