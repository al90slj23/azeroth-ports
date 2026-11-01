"""0.135.1 enemy HP projection reused from independently recovered134 rules.

The semantic state types have legacy numeric labels. Physical135 offsets are
handled by the original-oracle runner, not by these production calculations.
Fresh135 cast/HP comparisons validate their declared composition; no134 count
is transferred. Procs, loot and death RNG remain explicit pending side effects.
"""
from dataclasses import dataclass,fields
from . import binary32 as f
from .combat134 import (
    UnitState as _UnitState134, CombatState, ItemModifier, AbilityReference, SpellModifier,
    AbilityLookupPanic, DamageResult, resolve_damage as _resolve_damage134, encoded_hp,
)
from .record_cells135 import UnknownRecordRead135


@dataclass(frozen=True)
class UnitState(_UnitState134):
    """135 state can retain inactive constructor-unwritten U4/Q32 as None.

    The inherited damage arithmetic does not read death time. Linked GUID is
    required only at the guarded kind2/kind3 consumers below and in8685.
    None never supplies zero to either arithmetic or physical record writers.
    """
    linked_id_32:int|None=0
    death_time_4_bits:int|None=0

    def __post_init__(self):
        for field in fields(self):
            value=getattr(self,field.name)
            if field.name=='death_time_4_bits' and value is None:continue
            if field.name.endswith('_bits'):
                if not isinstance(value,int)or not 0<=value<=f.MASK:
                    raise ValueError('Expected uint32 float bits')
        for value in(self.target_id,self.linked_id_32):
            if value is None:continue
            if not isinstance(value,int)or not 0<=value<=0xffffffffffffffff:
                raise ValueError('GUID must be uint64')
        if self.target_id is None:raise ValueError('Target GUID must be known')


def required_linked_id135(unit,consumer):
    if unit.linked_id_32 is None:
        raise UnknownRecordRead135(offset=32,width=8,consumer=consumer)
    return unit.linked_id_32


def resolve_damage(state,target_id,amount_bits,spell_id=0,spell_category=None):
    """Preserve914 arithmetic, requiring opaque Q32 only on its live branch."""
    target=next((u for u in state.units if u.target_id==target_id),None)
    if state.phase_2579==1 and target is not None:
        if target.kind_40==3:
            required_linked_id135(target,'914 kind3 target Q32')
        if target.elite_244!=-1 or target.kind_64!=-1:
            now=f.to_float(state.now_bits)
            if not f.to_float(target.phase_until_412_bits)>now and not f.to_float(target.phase_until_408_bits)>now:
                for other in state.units:
                    if other.marker==0 and other.kind_40==2:
                        required_linked_id135(other,'914 live kind2 protection scan Q32')
    return _resolve_damage134(state,target_id,amount_bits,spell_id,spell_category)
