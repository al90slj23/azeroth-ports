"""Independent fixed135 effective armor and incoming scalar projection.

Compatibility field labels are semantic134 names, not physical135 addresses.
The original changed effective armor to27375 and removed the former extra
kind54 multiplicative factor. Original registry/events/visual/death effects are
not silently implemented; results retain pending effects even when all declared
nonfatal scalar outputs have been independently compared with complete1073.
"""
from dataclasses import dataclass,replace
from . import binary32 as f
from .incoming134 import (IncomingState as LegacyIncomingState,UnitPosition,BuffRecord,
                         ModifierRecord,Reduction,IncomingResult,position_bits,
                         _near_count,_minnum,_maxnum,_positive,_u,classify_38322)
ZERO=0
ONE=0x3f800000

@dataclass(frozen=True)
class IncomingState135(LegacyIncomingState):
    armor_cap_1572_bits:int=0x3f19999a
    minimum_one_2578:int=0

    def __post_init__(self):
        super().__post_init__()
        _u(self.minimum_one_2578,8)


def effective_armor_bits(state):
    record=next((r for r in state.modifiers if r.tag==54 and r.byte4==1),None)
    if record is None or not _near_count(state,0x42440000):
        return state.armor_1392_bits
    bonus=f.div(f.add(f.from_u32(record.byte5),f.from_u32(record.byte5)),0x42c80000)
    if not f.to_float(bonus)>0:
        return state.armor_1392_bits
    maximum=_maxnum(state.armor_1392_bits,state.armor_cap_1572_bits)
    return _minnum(maximum,f.add(bonus,state.armor_1392_bits))


def reduce_incoming_bits(state,amount_bits):
    _u(amount_bits)
    if state.phase_2579!=1:return Reduction(amount_bits,amount_bits,'phase_guard')
    if state.protection_2568&1:return Reduction(amount_bits,amount_bits,'protection_guard')
    mode_amount=amount_bits
    if state.mode_2574==1:
        region_scale=0x3f333333 if classify_38322(state.map_id)<3 else ONE
        factor=f.mul(region_scale,f.from_u32((state.wave_2532-1)&f.MASK))
        factor=f.mul(factor,0x3d83126f)
        factor=f.mul(f.add(factor,ONE),0x3f4ccccd)
        mode_amount=f.mul(mode_amount,factor)
    now=f.to_float(state.now_bits)
    if any(b.tag==12 and f.to_float(b.expires24_bits)>now for b in state.buffs):
        return Reduction(mode_amount,mode_amount,'active_raw_buff12_guard')
    amount=f.mul(mode_amount,f.sub(ONE,effective_armor_bits(state)))
    if f.to_float(state.nearby_reduction_1444_bits)>0 and _near_count(state,0x42800000)>=5:
        amount=f.mul(amount,f.sub(ONE,state.nearby_reduction_1444_bits))
    return Reduction(amount,mode_amount,'reduced')

def resolve_incoming_prefix(state, amount_bits, source_guid=0):
    """Apply known scalar prefix and stop at unimplemented original callbacks.

    This projects known scalar writes including exhausted-shield cleanup and the
    explicit minimum-one flag. Keyed/aura/source metadata and event producers
    remain pending; fatal state is not completed by this function.
    """
    _u(source_guid, 64)
    reduced = reduce_incoming_bits(state, amount_bits)
    if reduced.reason != 'reduced':
        return IncomingResult(state, 'returned', reduced.reason, reduced.amount_bits)
    amount = reduced.amount_bits
    absorbed = ZERO
    if f.to_float(state.shield_1532_bits) > 0:
        old_shield = state.shield_1532_bits
        absorbed = _minnum(old_shield, amount)
        shield = f.sub(old_shield, absorbed)
        barrier = _positive(f.sub(state.barrier_1536_bits, absorbed))
        source = state.shield_source_1344
        remaining = state.shield_source_remaining_1348_bits
        if source:
            spill = _positive(f.sub(absorbed, remaining))
            source_depleted = f.to_float(remaining) <= f.to_float(absorbed)
            remaining = ZERO if source_depleted else f.sub(remaining, absorbed)
            new_source = 0 if source_depleted else source
        else:
            spill = absorbed
            source_depleted = False
            remaining = f.sub(remaining, absorbed)
            new_source = 0
        state = replace(state, shield_1532_bits=shield, barrier_1536_bits=barrier,
                        shield_source_1344=new_source,
                        shield_source_remaining_1348_bits=remaining)
        used_reserve = _minnum(state.reserve_768_bits, spill)
        if f.to_float(used_reserve) > 0:
            state = replace(state, reserve_768_bits=f.sub(state.reserve_768_bits, used_reserve))
            return IncomingResult(state, 'pending', 'before27959_and1453', amount, absorbed,
                                  ('27959/1453 reserve-spill callbacks before HP write',))
        state = replace(state, reserve_768_bits=_minnum(shield, state.reserve_768_bits))
        exhausted = f.to_float(shield) <= 0
        if exhausted:
            state = replace(state, barrier_1536_bits=ZERO, shield_source_1344=0,
                            shield_source_remaining_1348_bits=ZERO,
                            buffs=tuple(x for x in state.buffs if x.tag != 7))
        elif source_depleted:
            state = replace(state, buffs=tuple(x for x in state.buffs if x.spell_id != source))
        amount = f.sub(amount, absorbed)
        state = replace(state, absorbed_740_bits=f.add(absorbed, state.absorbed_740_bits),
                        maximum_shield_744_bits=_maxnum(old_shield, state.maximum_shield_744_bits))
        if exhausted or source_depleted:
            #1073 writes i64 zero across740/744 before shield-break event984.
            state=replace(state,absorbed_740_bits=ZERO,maximum_shield_744_bits=ZERO)
    state = replace(state, last_hit_1648_bits=state.now_bits,
                    hp_1528_bits=f.sub(state.hp_1528_bits, amount),
                    incoming_total_992=state.incoming_total_992 + f.to_float(amount))
    if state.minimum_one_2578:
        state=replace(state,hp_1528_bits=_maxnum(0x3f800000,state.hp_1528_bits))
    stage='before_unresolved_death' if f.to_float(state.hp_1528_bits)<=0 else 'scalar_nonfatal_projection'
    return IncomingResult(state, 'pending', stage, amount, absorbed,
                          ('source-unit registry/statistics and48B history',
                           'raw buff13 and item22 retaliation through914',
                           'event984 callbacks before final HP reread',
                           'revival/death, keyed HP output and appearance/aura callbacks'))



def input_from_dict(raw):
    values=dict(raw)
    values['map_id']=values['map_id'].encode('ascii')
    for key,constructor in (('units',UnitPosition),('buffs',BuffRecord),('modifiers',ModifierRecord)):
        values[key]=tuple(constructor(**row)for row in values[key])
    return IncomingState135(**values)
