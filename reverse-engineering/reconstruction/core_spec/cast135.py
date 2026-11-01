"""Independent135 spatial query and common damage-only cast/auto-cast rules.

No game binary, WAT or evidence is read. Definitions and all auxiliary source
states are explicit input snapshots. Execution kinds0/2 with effect-tag0 are
implemented; other effects reject rather than silently becoming damage-only.
Physical packet envelopes, animation, proc producers and death continuation
remain pending. Every arithmetic operation rounds through binary32 primitives.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .ability_state import AbilityRecord
from .binary32_sqrt import sqrt_bits
from .combat135 import CombatState, UnitState, resolve_damage, required_linked_id135
from .radius import radius_bits
from .rng import next_u32_words

ONE = 0x3f800000


class UnresolvedCast(NotImplementedError):
    pass


class CastDeathBoundary(UnresolvedCast):
    """Post-core death state, before unresolved loot/proc/RNG continuation.

    Critical RNG and HP/accounting writes have already been applied. Consumers
    must supply the actual ordinary-death continuation before another hit.
    """
    def __init__(self,state,damage_result):
        super().__init__('Need explicit death continuation before the next hit')
        self.state=state
        self.damage_result=damage_result
        self.remaining_targets=()
        self.unprocessed_hits=()
        self.deferred_hits=()


@dataclass(frozen=True)
class CastDefinition:
    pointer: int
    ability_id: bytes
    execution_kind: int
    effect_tag: int
    spell_id: int
    school: int
    damage_bits: int
    cooldown_bits: int
    range_bits: int
    radius_bits: int
    count: int


@dataclass(frozen=True)
class SpatialUnit:
    unit: UnitState
    from_xy: tuple
    to_xy: tuple
    priority_until372_bits: int = 0


@dataclass(frozen=True)
class QueuedHit:
    target_id: int
    source_id: int
    due_bits: int
    spell_id: int
    damage_bits: int
    critical: int
    school: int
    context908: int


@dataclass(frozen=True)
class CastState:
    combat: CombatState
    spatial: tuple
    player_xy: tuple
    rng_words: tuple
    damage_multiplier_bits: int
    max_hp_bits: int
    critical_chance_bits: int
    critical_multiplier_bits: int
    area_multiplier_bits: int
    cooldown_multiplier_bits: int
    extra_targets: int
    source_id: int
    current_target_id: int
    context908: int
    auxiliary_effects: tuple
    queued: tuple = ()
    attempted_spell_ids: tuple = ()

    def __post_init__(self):
        if self.auxiliary_effects is None:
            raise UnresolvedCast('Explicit auxiliary producer snapshot required')
        if self.auxiliary_effects:
            raise UnresolvedCast('Auxiliary effect/proc sources are not restored')
        if self.combat.items or self.combat.spell_modifiers:
            raise UnresolvedCast('Cast-wide item/talent proc continuation is not restored')
        if len(self.spatial) != len(self.combat.units):
            raise ValueError('Spatial and combat units must be in the same order')
        if tuple(s.unit for s in self.spatial) != self.combat.units:
            raise ValueError('Spatial/combat snapshots disagree')
        if len(self.rng_words) != 4:
            raise ValueError('Four RNG words required')


@dataclass(frozen=True)
class CastResult:
    state: CastState
    success: int
    selected_ids: tuple
    base_damage_bits: int
    radius_bits: int
    hits: tuple
    status: str = 'core_projection'


def _total_key(bits):
    return (~bits & f.MASK) if bits & f.SIGN else bits | f.SIGN


def position(unit, now_bits):
    duration = unit.unit.movement_duration_344_bits
    if f.to_float(duration) <= 0:
        return unit.to_xy
    t = f.div(f.sub(now_bits, unit.unit.movement_time_340_bits), duration)
    if f.to_float(t) < 0: t = 0
    if f.to_float(t) > 1: t = ONE
    return tuple(f.add(a, f.mul(f.sub(b,a),t)) for a,b in zip(unit.from_xy,unit.to_xy))


def distance_squared(a,b):
    x,y = f.sub(a[0],b[0]),f.sub(a[1],b[1])
    return f.add(f.mul(x,x),f.mul(y,y))


def query_targets(spatial, center_xy, radius, now_bits, excluded=()):
    """Full27562 numeric query: marker, exclusions, interpolation and stable sort."""
    squared = f.mul(radius,radius)
    selected = []
    for entry in spatial:
        if entry.unit.marker or entry.unit.target_id in excluded: continue
        distance = distance_squared(position(entry,now_bits),center_xy)
        if f.to_float(distance) <= f.to_float(squared):
            selected.append((entry,distance))
    selected.sort(key=lambda x:_total_key(x[1]))
    return tuple(x[0].unit.target_id for x in selected)


def projectile_targets(state, radius):
    """8685 priorities plus the 6-unit nearby/HP preference, for unique GUIDs."""
    ids = query_targets(state.spatial,state.player_xy,radius,state.combat.now_bits)
    units = {u.unit.target_id:u for u in state.spatial}
    if len(units) != len(state.spatial):
        raise UnresolvedCast('Duplicate-GUID damage lookup needs separate recovery')
    now = f.to_float(state.combat.now_bits)
    def priority(guid):
        s=units[guid];u=s.unit
        if now < f.to_float(s.priority_until372_bits): return 3
        if u.kind_40 != -1: return 0
        if u.elite_416 not in (0,1):
            raise UnresolvedCast('Noncanonical elite416 priority byte')
        if u.elite_244 != -1:
            if f.to_float(u.phase_until_412_bits)>now: return 0
            protected = f.to_float(u.phase_until_408_bits)>now or any(
                x.marker==0 and x.kind_40==2 and required_linked_id135(x,'8685 live kind2 protection scan Q32')==guid for x in state.combat.units)
            if not protected: return 0
        return 2-u.elite_416
    ordered = sorted(ids,key=priority)
    prefix=[g for g in ordered if priority(g)<2]
    ordinary=[g for g in ordered if priority(g)==2]
    deferred=[g for g in ordered if priority(g)==3]
    if ordinary:
        anchor=position(units[ordinary[0]],state.combat.now_bits)
        near=[];far=[]
        for guid in ordinary:
            d=distance_squared(position(units[guid],state.combat.now_bits),anchor)
            (near if f.to_float(d)<=36 else far).append(guid)
        near.sort(key=lambda g:_total_key(units[g].unit.hp_bits))
        ordinary=near+far
    return tuple(prefix+ordinary+deferred)


def base_damage(state, definition, owned):
    coefficient = 0x3f000000 if definition.execution_kind in (2,3,8) else ONE
    value=f.mul(definition.damage_bits,0x3fb33333)
    value=f.mul(value,owned.damage_bits)
    value=f.mul(value,owned.additional_damage_bits)
    value=f.mul(value,coefficient)
    life=f.mul(state.max_hp_bits,owned.life_damage_bits) if f.to_float(definition.damage_bits)>0 else 0
    return f.mul(state.damage_multiplier_bits,f.add(value,life))


def _critical(state, damage):
    value,rng=next_u32_words(state.rng_words)
    unit=f.mul(f.from_u32(value>>8),0x33800000)
    critical=int(f.to_float(state.critical_chance_bits)>f.to_float(unit))
    return replace(state,rng_words=rng),f.mul(damage,state.critical_multiplier_bits) if critical else damage,critical


def _updated_combat(state, combat):
    return replace(state,combat=combat,spatial=tuple(replace(s,unit=u) for s,u in zip(state.spatial,combat.units)))


def _apply_hit(state,guid,damage,spell,after_death=None):
    if any(u.target_id==guid and u.kind_40==3 for u in state.combat.units):
        raise UnresolvedCast('Kind3 target category/cap continuation is not restored')
    result=resolve_damage(state.combat,guid,damage,spell_id=spell,spell_category=0)
    state=_updated_combat(state,result.state)
    if result.dead and result.applied:
        if after_death is None:
            raise CastDeathBoundary(state,result)
        state=after_death(state,result)
        if not isinstance(state,CastState):
            raise TypeError('Death continuation must return a resolved CastState')
    return state,result


PROJECTILE_SPEED = {75:40,116:28,133:24,403:20,686:20,1510:30,
    1978:40,2643:30,2812:20,3044:40,3606:19,5116:40,5176:20,6353:24,
    6789:24,6917:40,6996:30,7269:20,10181:28,11366:24,19434:40,24275:35,27383:20}


def cast_ability(state,definition,owned,*,after_death=None):
    if definition.execution_kind not in (0,2) or definition.effect_tag != 0:
        raise UnresolvedCast('Execution kind/effect tag requires another dispatcher branch')
    if owned.definition_pointer != definition.pointer:
        raise ValueError('Owned definition pointer differs')
    base=base_damage(state,definition,owned)
    attempts=state.attempted_spell_ids
    if definition.spell_id not in attempts: attempts=attempts+(definition.spell_id,)
    state=replace(state,attempted_spell_ids=attempts)
    hits=[]
    if definition.execution_kind==2:
        radius=f.mul(owned.area_bits,owned.additional_area_bits)
        radius=f.mul(definition.radius_bits,radius)
        radius=radius_bits(f.mul(state.area_multiplier_bits,radius))
        targets=query_targets(state.spatial,state.player_xy,radius,state.combat.now_bits)
        for index,guid in enumerate(targets):
            state,damage,critical=_critical(state,base)
            try:
                state,result=_apply_hit(state,guid,damage,definition.spell_id,after_death)
            except CastDeathBoundary as boundary:
                boundary.remaining_targets=targets[index+1:]
                raise
            hits.append((guid,damage,critical,result.new_hp_bits))
        return CastResult(state,int(bool(targets)),targets,base,radius,tuple(hits))
    radius=definition.range_bits
    candidates=projectile_targets(state,radius)
    if definition.ability_id==b'aimed_shot' and state.current_target_id in candidates:
        candidates=(state.current_target_id,)+tuple(g for g in candidates if g!=state.current_target_id)
    count=1 if definition.count==0 else max(1,(definition.count+owned.extra_targets+owned.additional_targets+state.extra_targets)&f.MASK)
    if count>4096: raise UnresolvedCast('Independent target-count allocation watchdog')
    # Cyclic repetition belongs to the separate kind1 arcane-missiles branch.
    # The kind0 path truncates to available targets, including count upgrades.
    targets=tuple(candidates[:count])
    for guid in targets:
        target=next(u for u in state.spatial if u.unit.target_id==guid)
        speed=PROJECTILE_SPEED.get(definition.spell_id)
        travel=f.div(sqrt_bits(distance_squared(state.player_xy,position(target,state.combat.now_bits))),f.from_float(speed)) if speed else 0
        state,damage,critical=_critical(state,base)
        due=f.add(travel,state.combat.now_bits)
        event=QueuedHit(guid,state.source_id,due,definition.spell_id,damage,critical,definition.school,state.context908)
        state=replace(state,queued=state.queued+(event,))
        hits.append((guid,damage,critical,due))
    return CastResult(state,int(bool(targets)),targets,base,radius,tuple(hits))


def process_hits(state,now_bits,*,after_death=None):
    old_queue=state.queued
    state=replace(state,combat=replace(state.combat,now_bits=now_bits),queued=())
    pending=[];applied=[]
    for index,hit in enumerate(old_queue):
        if not f.to_float(hit.due_bits)<=f.to_float(now_bits):
            pending.append(hit);continue
        if f.to_float(hit.damage_bits)>0:
            try:
                state,result=_apply_hit(state,hit.target_id,hit.damage_bits,hit.spell_id,after_death)
            except CastDeathBoundary as boundary:
                boundary.unprocessed_hits=old_queue[index+1:]
                boundary.deferred_hits=tuple(pending)
                raise
            applied.append((hit.target_id,result.new_hp_bits))
    if state.queued:
        raise UnresolvedCast('Death/proc-created new hit ordering needs separate recovery')
    return replace(state,queued=tuple(pending)),tuple(applied)


def auto_cast(state,definition,owned,remaining_bits,dt_bits,override_bits,*,after_death=None):
    remaining=f.sub(remaining_bits,dt_bits)
    if f.to_float(remaining)>0:
        return state,remaining,None
    result=cast_ability(state,definition,owned,after_death=after_death)
    if not result.success:
        return result.state,0x3e99999a,result
    if f.to_float(override_bits)>0:
        candidate=f.mul(override_bits,state.cooldown_multiplier_bits)
        floor=0x3e800000
    else:
        candidate=f.mul(definition.cooldown_bits,0x3fb33333)
        candidate=f.mul(owned.cooldown_bits,candidate)
        candidate=f.mul(owned.additional_cooldown_bits,candidate)
        candidate=f.mul(state.cooldown_multiplier_bits,candidate)
        floor=0x3f000000 if definition.ability_id==b'hellfire' else 0x3e800000
    remaining=candidate if f.to_float(candidate)>f.to_float(floor) else floor
    return result.state,remaining,result


def auto_cast_many(state,active_entries,dt_bits,*,after_death=None):
    """Forward active-vector order, sharing target HP and RNG between casts.

    Each entry supplies its resolved owned80B record and explicit current
    countdown/override. Expired timed-effect/producer phases remain separate.
    """
    remaining=[];results=[]
    for definition,owned,bits,override in active_entries:
        state,bits,result=auto_cast(state,definition,owned,bits,dt_bits,override,after_death=after_death)
        remaining.append(bits);results.append(result)
    return state,tuple(remaining),tuple(results)
