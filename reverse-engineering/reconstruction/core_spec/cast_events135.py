"""Independent135 common casts with ordered accepted-hit event delivery.

Spatial queries, arithmetic and target priorities reuse the earlier independent
cast model. This module adds the missing per-accepted-hit consumer before death
continuation. A target GUID is never used to coalesce distinct hits. Sources
remain explicit: effect-tag0, execution0/2 and empty item/proc vectors only.
No original program or original output is read by this production module.
"""
from dataclasses import replace

from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .combat135 import resolve_damage
from .cast135 import (CastState, CastResult, CastDeathBoundary, QueuedHit,
    UnresolvedCast, PROJECTILE_SPEED, base_damage, query_targets,
    projectile_targets, position, distance_squared, _critical, _updated_combat)
from .radius import radius_bits


def apply_hit(state, guid, damage, spell, *, after_hit=None, after_death=None):
    """914 core, then each accepted-hit consumer, then ordinary death consumer.

    The hit consumer receives DamageResult.damage_bits, which includes914's
    minimum-damage rule. It runs for accepted nonlethal AND lethal hits. Its
    owner must thread player HP/source state; CastState owns only cast/unit/RNG
    state. A callback cannot stand in for unresolved original proc production.
    """
    if any(u.target_id == guid and u.kind_40 == 3 for u in state.combat.units):
        raise UnresolvedCast('Kind3 target category/cap continuation is unresolved')
    result = resolve_damage(state.combat, guid, damage, spell_id=spell, spell_category=0)
    state = _updated_combat(state, result.state)
    if result.applied:
        if after_hit is None:
            raise UnresolvedCast('Each accepted hit requires an explicit player/proc consumer')
        state = after_hit(state, result)
        if not isinstance(state, CastState):
            raise TypeError('Accepted-hit consumer must return a resolved CastState')
    if result.applied and result.dead:
        if after_death is None:
            raise CastDeathBoundary(state, result)
        state = after_death(state, result)
        if not isinstance(state, CastState):
            raise TypeError('Death consumer must return a resolved CastState')
    return state, result


def cast_ability(state, definition, owned, *, after_hit=None, after_death=None):
    if definition.execution_kind not in (0, 2) or definition.effect_tag != 0:
        raise UnresolvedCast('Unrestored execution/effect dispatcher branch')
    if owned.definition_pointer != definition.pointer:
        raise ValueError('Owned definition pointer differs')
    base = base_damage(state, definition, owned)
    attempts = state.attempted_spell_ids
    if definition.spell_id not in attempts:
        attempts += (definition.spell_id,)
    state = replace(state, attempted_spell_ids=attempts)
    hits = []
    if definition.execution_kind == 2:
        radius = f.mul(owned.area_bits, owned.additional_area_bits)
        radius = f.mul(definition.radius_bits, radius)
        radius = radius_bits(f.mul(state.area_multiplier_bits, radius))
        targets = query_targets(state.spatial, state.player_xy, radius, state.combat.now_bits)
        for index, guid in enumerate(targets):
            state, damage, critical = _critical(state, base)
            try:
                state, result = apply_hit(state, guid, damage, definition.spell_id,
                    after_hit=after_hit, after_death=after_death)
            except CastDeathBoundary as boundary:
                boundary.remaining_targets = targets[index + 1:]
                raise
            hits.append((guid, damage, critical, result.new_hp_bits))
        return CastResult(state, int(bool(targets)), targets, base, radius, tuple(hits))
    radius = definition.range_bits
    candidates = projectile_targets(state, radius)
    if definition.ability_id == b'aimed_shot' and state.current_target_id in candidates:
        candidates = (state.current_target_id,) + tuple(g for g in candidates if g != state.current_target_id)
    count = 1 if definition.count == 0 else max(1,
        (definition.count + owned.extra_targets + owned.additional_targets + state.extra_targets) & f.MASK)
    if count > 4096:
        raise UnresolvedCast('Independent target-count allocation watchdog')
    targets = tuple(candidates[:count])
    for guid in targets:
        target = next(u for u in state.spatial if u.unit.target_id == guid)
        speed = PROJECTILE_SPEED.get(definition.spell_id)
        travel = f.div(sqrt_bits(distance_squared(state.player_xy, position(target,
            state.combat.now_bits))), f.from_float(speed)) if speed else 0
        state, damage, critical = _critical(state, base)
        due = f.add(travel, state.combat.now_bits)
        state = replace(state, queued=state.queued + (QueuedHit(guid, state.source_id, due,
            definition.spell_id, damage, critical, definition.school, state.context908),))
        hits.append((guid, damage, critical, due))
    return CastResult(state, int(bool(targets)), targets, base, radius, tuple(hits))


def process_hits(state, now_bits, *, after_hit=None, after_death=None):
    """Preserve queue order, including repeated GUIDs and deferred earlier hits."""
    old_queue = state.queued
    state = replace(state, combat=replace(state.combat, now_bits=now_bits), queued=())
    pending, applied = [], []
    for index, hit in enumerate(old_queue):
        if not f.to_float(hit.due_bits) <= f.to_float(now_bits):
            pending.append(hit)
            continue
        if f.to_float(hit.damage_bits) > 0:
            try:
                state, result = apply_hit(state, hit.target_id, hit.damage_bits, hit.spell_id,
                    after_hit=after_hit, after_death=after_death)
            except CastDeathBoundary as boundary:
                boundary.unprocessed_hits = old_queue[index + 1:]
                boundary.deferred_hits = tuple(pending)
                raise
            applied.append((hit.target_id, result.new_hp_bits))
    if state.queued:
        raise UnresolvedCast('Death/proc-created hit insertion remains unresolved')
    return replace(state, queued=tuple(pending)), tuple(applied)
