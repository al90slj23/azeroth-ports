"""Independent kind0 selection -> stats -> XP sweep -> next choice/run projection.

Every source is an explicit snapshot. This composes already independent135
models and known invariant arithmetic; it never loads or executes the original.
Physical queue allocation, visual notification and real source producers remain
separate effects. Priority kind1/2 regeneration is returned as pending metadata.
"""
from dataclasses import asdict, dataclass, replace

from . import binary32 as f
from .ability_state import UpgradeCard
from .ability_state135 import DEFINITIONS as INIT_DEFS, initialize_ability
from .ability_upgrade135 import apply_upgrade_card
from .candidates135 import Owned,Effect,Summon,generate_kind0_metadata
from .currency134 import CurrencyState,apply_currency,mode_multiplier_bits
from .derived_stats135 import StatsInput,recalculate,LiveEffect
from .level_cycle135 import LevelCycleState,gain_xp,projection as level_projection
from .pickups134 import PickupRecord,decode_record56,encode_record56
from .binary32_sqrt import sqrt_bits
from .progression134 import ProgressionState,round_85718_bits,trunc_sat_u32
from .pickup_record_cells135 import encode_pickup_cells135


@dataclass(frozen=True)
class SelectionCycleState:
    level: LevelCycleState
    pending_kind1: int
    pending_kind2: int
    pickups: tuple
    player_x_bits: int
    player_y_bits: int
    currency: CurrencyState
    game_tag: int
    xp_queue: tuple
    xp_queue_capacity: int

    def __post_init__(self):
        if not isinstance(self.level,LevelCycleState) or not isinstance(self.currency,CurrencyState):
            raise TypeError('Explicit resolved level and currency snapshots required')
        for value in (self.pending_kind1,self.pending_kind2,self.player_x_bits,self.player_y_bits):
            if type(value)is not int or not 0<=value<=f.MASK:raise ValueError('u32 snapshot required')
        if type(self.game_tag)is not int or not 0<=self.game_tag<1<<64:raise ValueError('u64 game tag required')
        if type(self.pickups)is not tuple or any(not isinstance(p,PickupRecord) for p in self.pickups):
            raise TypeError('Resolved ordered pickup records required')
        #4600's sweep reads kind/marker/XY/amount, never an old arrival word.
        #Keep an unconsumed +4 opaque instead of assigning a dummy value.
        if any(p.marker not in(0,1)for p in self.pickups):
            raise ValueError('Canonical live pickup markers0/1 required; original31732 rejects sentinel2')
        if self.currency.mode!=self.level.stats.flag2574:raise ValueError('Mode snapshots differ')
        if type(self.xp_queue)is not tuple or len(self.xp_queue)>self.xp_queue_capacity:raise ValueError('Explicit XP forward queue required')


@dataclass(frozen=True)
class SelectionCycleResult:
    state: SelectionCycleState
    accepted: bool
    status: str
    swept_base_xp: int=0
    awarded_xp: int=0
    next_kind: int|None=None
    pending: tuple=()
    growth_events: tuple=()


def _stat_rebuild(level):
    stats=level.stats
    result=recalculate(StatsInput(level=level.progression.level,**asdict(stats),**level.sources.keywords()))
    aux=result['auxiliary_bits'];fields=dict(level.player_fields);fields.update((int(k),v)for k,v in result['object_fields'].items())
    return replace(level,derived_bits=tuple(sorted((int(k),v)for k,v in result['derived_bits'].items())),
        player_fields=tuple(sorted(fields.items())),stats=replace(stats,
            old_max_hp_bits=result['derived_bits']['1536'],current_hp_bits=result['current_hp_bits'],
            previous_speed_bits=result['speed_bits'],pool1532_bits=aux['1444'],pool1536_bits=aux['1448'],
            conditional1348_bits=aux['1348'],pool768_bits=aux['768']))


def select_card(state,index,*,additional_modifiers):
    """Apply canonical kind0 card then original4600's proven control/numeric order."""
    if not isinstance(state,SelectionCycleState):raise TypeError('Resolved SelectionCycleState required')
    level=state.level
    if level.phase2587!=2 or not 0<=index<len(level.candidates) or level.selection_kind2585==255:
        return SelectionCycleResult(state,False,'entry_rejected')
    if level.selection_kind2585!=0:
        return SelectionCycleResult(state,False,'pending_nonordinary_entry',pending=('kind1/2 entry producers and card variants',))
    if additional_modifiers is None:raise ValueError('Additional modifier producer must be explicitly resolved')
    if any(p.aux_count or p.aux_capacity for p in state.pickups):
        return SelectionCycleResult(state,False,'pending_pickup_claims',pending=('Resolve original pickup claim/aux destruction before composing',))
    card=level.candidates[index];owned=list(level.choice_inputs.owned);currency=state.currency
    if card.variant=='new':
        definition=INIT_DEFS[card.ability_id.encode()]
        owned.append(Owned(card.ability_id,initialize_ability(definition,tier=card.tier,modifiers=additional_modifiers)))
    elif card.variant=='upgrade':
        if card.owned_index<len(owned):
            item=owned[card.owned_index];definition=INIT_DEFS[item.ability_id.encode()]
            owned[card.owned_index]=Owned(item.ability_id,apply_upgrade_card(item.record,
                UpgradeCard(card.owned_index,card.kinds,card.tier),definition))
    elif card.variant=='gold':
        currency=replace(currency,multiplier_bits=dict(level.derived_bits)[1588],player_fields=level.player_fields)
        result=apply_currency(currency,card.gold)
        if result.status!='core_projection':return SelectionCycleResult(state,False,'pending_currency',pending=result.pending)
        currency=result.state;level=replace(level,player_fields=currency.player_fields)
    else:return SelectionCycleResult(state,False,'pending_candidate_variant')
    level=replace(level,choice_inputs=replace(level.choice_inputs,owned=tuple(owned)))
    level=_stat_rebuild(level)
    # Finish-kind0 decrements pending, sets flag2581 before sweeping/priority.
    pending=max(level.progression.pending_upgrades-1,0)
    level=replace(level,progression=replace(level.progression,pending_upgrades=pending),candidates=(),
                  choice_inputs=replace(level.choice_inputs,flag2581=1))
    base=0;remaining=[];radius=dict(level.derived_bits)[1560]
    for record in state.pickups:
        dx=f.sub(record.x_bits,state.player_x_bits);dy=f.sub(record.y_bits,state.player_y_bits)
        distance=sqrt_bits(f.add(f.mul(dx,dx),f.mul(dy,dy)))
        if record.kind==0 and (record.marker!=0 or f.to_float(distance)<=f.to_float(radius)):
            base=(base+record.amount)&f.MASK
        else:remaining.append(record)
    award=0;xp_queue=state.xp_queue;xp_capacity=state.xp_queue_capacity;growth_events=()
    if base:
        if currency.mode:
            if len(xp_queue)==xp_capacity:xp_capacity=max(4,2*xp_capacity)
            xp_queue+=((currency.local_peer,base),)
        factor=mode_multiplier_bits(currency.mode,currency.member_count,region_index=currency.region_index)
        scaled=f.mul(factor,f.mul(dict(level.derived_bits)[1564],f.from_u32(base)))
        rounded=round_85718_bits(scaled)
        if f.is_nan(rounded)or not f.to_float(rounded)>1:rounded=0x3f800000
        award=trunc_sat_u32(rounded)
        # Phase2 prevents the XP consumer's own final choice generation.
        gained=gain_xp(level,award);level=gained.state;growth_events=gained.growth_events
    next_kind=1 if state.pending_kind1 else 2 if state.pending_kind2 else None
    if next_kind is None and level.progression.pending_upgrades and (level.gate2572!=1 or level.flags2573&1):next_kind=0
    pending_effects=('Physical message/queue/tree allocation and source producers remain unresolved',
        '1072 equipment/appearance keyed-field producer and1202 aura display fields remain unresolved; original observations are not model expectations')
    if next_kind==0:
        d=dict(level.derived_bits);ci=level.choice_inputs
        generated=generate_kind0_metadata(rng_words=level.rng_words,class_byte=level.stats.class_byte,
            owned=ci.owned,level=level.progression.level,luck_bits=d[1584],cooldown_bits=d[1544],
            flag275=ci.flag275,flag2573=ci.flag2581,blocked_ids=ci.blocked_ids,banished_keys=ci.banished_keys,
            effects=tuple(Effect(e.tag&255,e.value_bits)for e in level.sources.item_modifiers),
            summons=tuple(Summon(e.kind,e.summon_state41)for e in level.sources.definitions),kind=0)
        level=replace(level,candidates=generated.candidates,rng_words=generated.rng_words,
                      selection_kind2585=0,generation_counter2400=(level.generation_counter2400+1)&f.MASK)
        status='choice_regenerated'
    elif next_kind is not None:
        status='pending_priority_choice_metadata'
        pending_effects+=('kind1/2 metadata generation and its RNG remain pending',)
    else:
        live=tuple(e for e in level.sources.live_effects if e.spell_id!=1020)
        # Kind12 has no numeric union payload: original4600 does not write+12.
        # Zero is a semantic canonical value, not an asserted raw heap word.
        live+=(LiveEffect(12,0,1020,f.add(level.stats.now_bits,0x3f800000)),)
        level=replace(level,phase2587=1,selection_kind2585=255,flags2573=0,
                      sources=replace(level.sources,live_effects=live))
        status='running'
        if level.stats.flag2574==0:pending_effects+=('Original25472 movement resume intent',)
    updated=replace(state,level=level,pickups=tuple(remaining),currency=currency,
                    game_tag=0 if next_kind is None else state.game_tag,
                    xp_queue=xp_queue,xp_queue_capacity=xp_capacity)
    return SelectionCycleResult(updated,True,status,base,award,next_kind,pending_effects,growth_events=growth_events)


def projection(state):
    result=level_projection(state.level)
    result.update(owned_records_hex=[e.record.to_bytes().hex()for e in state.level.choice_inputs.owned],
        pending_kind1=state.pending_kind1,pending_kind2=state.pending_kind2,
        remaining_pickups_hex=[encode_pickup_cells135(p)for p in state.pickups],game_tag=state.game_tag,
        flag2581=state.level.choice_inputs.flag2581,flags2573=state.level.flags2573,
        live_effects=[asdict(e)for e in state.level.sources.live_effects],
        gold=state.currency.gold,earned=state.currency.earned,
        currency_queue=[list(e)for e in state.currency.queue],currency_queue_capacity=state.currency.queue_capacity,
        xp_queue=[list(e)for e in state.xp_queue],xp_queue_capacity=state.xp_queue_capacity)
    return result
