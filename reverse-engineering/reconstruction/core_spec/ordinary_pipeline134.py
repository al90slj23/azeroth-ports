"""Executable restricted ordinary kill -> pickups -> XP slice for0.134.0.

Production code only: no WASM or original files. Components share explicit
time/state invariants. Placement is a resolved world input, not a terrain
implementation. Scope is one ordinary unmoving target, no items/modifiers,
flag68=0,mode0,empty claims; all omitted side effects remain named pending.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .combat134 import CombatState,resolve_damage
from .death_loot134 import OrdinaryDefinition,RewardSource,project_ordinary_rewards
from .pickup_entity134 import project_kind1_entity
from .pickups134 import PickupState,Placement,append_xp,append_idle_currency,step_pickups
from .progression134 import ProgressionState,apply_xp,card_choice_eligible


class UnsupportedPipelineDomain(ValueError):
    """An omitted game branch is explicit, never silently a no-op."""


@dataclass(frozen=True)
class PipelineState:
    combat: CombatState
    pickups: PickupState
    progression: ProgressionState
    rng: tuple
    definition_accumulator_bits: int=0
    stats_dirty: bool=False

    def __post_init__(self):
        if self.combat.now_bits!=self.pickups.now_bits:
            raise ValueError('Combat and pickup time must be the same shared snapshot')
        if len(self.rng)!=4 or any(type(x)is not int or not 0<=x<=f.MASK for x in self.rng):
            raise ValueError('Expected four uint32 RNG words')
        if type(self.definition_accumulator_bits)is not int or not 0<=self.definition_accumulator_bits<=f.MASK:
            raise ValueError('Expected accumulator float bits')
        if type(self.stats_dirty)is not bool:
            raise ValueError('stats_dirty must be boolean')


@dataclass(frozen=True)
class PipelineResult:
    state: PipelineState
    stage: str
    status: str='core_projection'
    xp_awards: tuple=()
    reward_requests: tuple=()
    draws: int=0
    pending: tuple=('statistics, keyed state, visual/binary messages, allocation addresses and complete event scheduling',)


def apply_ordinary_hit(state,target_id,amount_bits,definition,source,*,xp_placement,currency_placement=None):
    """Compose914 core fields, ordinary rewards and kind0/kind1 consumers.

    The independent combat projection does not simulate death callbacks that
    could change RNG. They are excluded by this controlled empty-state domain,
    and the returned pending list still does not claim full914 equivalence.
    Counter/RNG after an actual kind1 request includes1820's extra draw.
    """
    if not isinstance(state,PipelineState)or not isinstance(definition,OrdinaryDefinition)or not isinstance(source,RewardSource):
        raise TypeError('Expected explicit pipeline state and ordinary definition/source')
    if state.stats_dirty:
        raise UnsupportedPipelineDomain('Independent stat refresh is required before another hit')
    source.require_ordinary()
    if definition.flag68!=0:
        raise UnsupportedPipelineDomain('Flagged definition/kind2 reward consumer is pending')
    if len(state.combat.units)!=1 or state.combat.units[0].target_id!=target_id:
        raise UnsupportedPipelineDomain('One explicit ordinary target is required')
    target=state.combat.units[0]
    if (target.kind_40!=-1 or target.kind_64!=-1 or target.elite_244!=-1
            or target.movement_duration_344_bits!=0 or state.combat.items or state.combat.spell_modifiers):
        raise UnsupportedPipelineDomain('Other unit tags,movement,item/modifier callbacks are pending')
    if state.pickups.mode!=0 or not state.pickups.claims_empty:
        raise UnsupportedPipelineDomain('Mode/claims synchronization is pending')
    hit=resolve_damage(state.combat,target_id,amount_bits,spell_id=133)
    updated=replace(state,combat=hit.state)
    if not hit.applied or not hit.dead:
        return PipelineResult(updated,'hit_without_new_death')
    rewards=project_ordinary_rewards(definition,state.rng,source=source,
        accumulator_bits=state.definition_accumulator_bits)
    pickups=state.pickups
    if rewards.xp.amount:
        result=append_xp(pickups,rewards.xp.amount,xp_placement)
        if result.status!='core_projection':raise UnsupportedPipelineDomain(str(result.pending))
        pickups=result.state
    rng=rewards.direct_rng_state;draws=rewards.direct_draws
    if rewards.currency.chance_passed:
        if not isinstance(currency_placement,Placement):
            raise UnsupportedPipelineDomain('Resolved currency world placement is required')
        entity=project_kind1_entity(rng,pickups.spawn_counter)
        result=append_idle_currency(pickups,rewards.currency.amount,currency_placement,
                                   guid=entity.guid,counter_after=entity.counter2400)
        if result.status!='core_projection':raise UnsupportedPipelineDomain(str(result.pending))
        pickups=result.state;rng=entity.rng_state;draws+=entity.draws
    updated=replace(updated,pickups=pickups,rng=tuple(rng),
                    definition_accumulator_bits=rewards.accumulator2412_bits)
    return PipelineResult(updated,'ordinary_rewards_consumed',reward_requests=rewards.requests,draws=draws,
        pending=('Complete914 statistics/procs/death callbacks, entity tree/rotation and binary packets remain pending',
                 'Resolved XP/currency placement is an input; full terrain and region clamping are not implemented'))


def collect_at(state,now_bits,*,flags2568=0,gate2564=0,flags2565=0):
    """Advance only the explicit pickup consumer, then XP arithmetic.

    This is not a full frame scheduler. A true2159 guard returns pending_choice
    rather than inventing candidate generation or claiming an unchanged phase.
    """
    if state.stats_dirty:
        return PipelineResult(state,'needs_stat_refresh','pending_stats',
            pending=('XP multiplier/radius after1513 must be independently resolved before another pickup invocation',))
    state=replace(state,combat=replace(state.combat,now_bits=now_bits),
                  pickups=replace(state.pickups,now_bits=now_bits))
    progress=state.progression
    boundary=None;dirty=False
    def consume(award,pickups_after_removal):
        nonlocal progress,boundary,dirty
        previous_level=progress.level
        progress=apply_xp(progress,award).state
        dirty=dirty or progress.level!=previous_level
        if card_choice_eligible(progress.pending_upgrades,state.combat.phase_2579,
                                flags2568,gate2564,flags2565):
            boundary='before_choice2159'
            return False
        if progress.level!=previous_level and any(record.kind==0 and record.marker!=0
                and record.arrival_bits is not None and f.to_float(record.arrival_bits)<=f.to_float(now_bits)
                for record in pickups_after_removal.records):
            boundary='before_next_award_after_stat_rebuild'
            return False
        return True
    result=step_pickups(state.pickups,after_award=consume)
    if result.status=='pending_domain':
        return PipelineResult(state,'pickup_domain_boundary','pending_domain',pending=result.pending)
    updated=replace(state,pickups=result.state,progression=progress,stats_dirty=dirty)
    if boundary is not None:
        return PipelineResult(updated,boundary,'pending_choice'if boundary=='before_choice2159'else'pending_stats',
            xp_awards=result.xp_awards,pending=(
                'Actual2159 candidate generation/phase effects are not executed'if boundary=='before_choice2159'else
                '1513 can change XP multiplier before the next award; complete independent rebuild is pending',))
    if dirty:
        return PipelineResult(updated,'after_awards_before_stat_refresh','pending_stats',xp_awards=result.xp_awards,
            pending=('Selected XP fields are projected; cached XP multiplier/radius must not be reused after unimplemented1513',))
    return PipelineResult(updated,'pickup_XP_projection',xp_awards=result.xp_awards,
        pending=('Complete4630 attributes/healing/messages and full game tick scheduling remain pending',))


def with_resolved_pickup_stats(state,*,xp_multiplier_bits,radius_bits):
    """Explicit caller-supplied stat snapshot; not an independent1513 rebuild.

    A caller must establish these values externally before clearing dirty state.
    This method never derives them from the original or claims their acceptance.
    """
    if not state.stats_dirty:
        raise ValueError('No pending pickup stat snapshot')
    return replace(state,pickups=replace(state.pickups,xp_multiplier_bits=xp_multiplier_bits,
                                        radius_bits=radius_bits),stats_dirty=False)
