"""Independent0.139.0 damage913 numeric nonlethal projection,432B units.

This module reads no original, asset, WAT, capture or oracle output. Empty
item/spell/proc producers are explicit inputs. Physical record bytes are caller
inputs and retained exactly except the original HP write. Death/proc/statistics,
client packets and Windows execution remain separate unfinished domains.
"""
from dataclasses import dataclass,replace
import struct
from . import binary32 as f


class PendingDamage139(NotImplementedError):pass


@dataclass(frozen=True)
class EmptyDamageSources139:
    items2028:tuple
    spells2052:tuple
    proc_schedule1972:tuple
    other_procs_absent:bool
    def __post_init__(self):
        if type(self.items2028)is not tuple or type(self.spells2052)is not tuple or type(self.proc_schedule1972)is not tuple:
            raise TypeError('Explicit typed ordered source snapshots required')
        if self.items2028 or self.spells2052 or self.proc_schedule1972 or self.other_procs_absent is not True:
            raise PendingDamage139('Nonempty139 item/spell/proc producer pending')


@dataclass(frozen=True)
class DamageState139:
    units432:tuple
    now_bits:int
    phase2587:int
    accounted_total_bits:int
    rng_words:tuple
    sources:EmptyDamageSources139
    def __post_init__(self):
        if type(self.units432)is not tuple or len(self.units432)>128 or any(type(x)is not bytes or len(x)!=432 for x in self.units432):
            raise ValueError('Explicit complete known432B unit records required')
        if not isinstance(self.sources,EmptyDamageSources139):raise TypeError('Explicit empty source contract required')
        ids=[struct.unpack_from('<Q',u,112)[0]for u in self.units432]
        if len(ids)!=len(set(ids)):raise PendingDamage139('Duplicate GUID resolution is outside this projection')
        if type(self.rng_words)is not tuple or len(self.rng_words)!=4 or any(type(w)is not int or not 0<=w<=f.MASK for w in self.rng_words):
            raise ValueError('Explicit four RNG words required')
        for word,bits in ((self.now_bits,32),(self.phase2587,8),(self.accounted_total_bits,64)):
            if type(word)is not int or not 0<=word<1<<bits:raise ValueError('Unsigned binary scalar required')


@dataclass(frozen=True)
class DamageResult139:
    state:DamageState139
    applied:bool
    reason:str
    damage_bits:int
    old_hp_bits:int
    new_hp_bits:int
    accounted_bits:int
    write_set:tuple


def _u(row,o):return struct.unpack_from('<I',row,o)[0]
def _i(row,o):return struct.unpack_from('<i',row,o)[0]


def resolve_damage139(state,target_id,amount_bits,*,spell_id=0,school=0,critical=0,context=0):
    if not isinstance(state,DamageState139):raise TypeError('Explicit fixed139 damage state required')
    for x,bits in ((target_id,64),(amount_bits,32),(spell_id,32),(school,8),(critical,8),(context,8)):
        if type(x)is not int or not 0<=x<1<<bits:raise ValueError('Explicit unsigned damage input required')
    if context:raise PendingDamage139('Inherited139 proc context pending')
    index=next((i for i,row in enumerate(state.units432)if struct.unpack_from('<Q',row,112)[0]==target_id),None)
    row=state.units432[index]if index is not None else None
    hp=_u(row,288)if row is not None else 0
    def skip(reason):return DamageResult139(state,False,reason,0,hp,hp,0,())
    if state.phase2587!=1:return skip('not_running')
    if row is None:return skip('target_absent')
    if _i(row,244)!=-1:raise PendingDamage139('139 Boss header/accepted-hit continuation pending')
    if _i(row,40)==3:raise PendingDamage139('139 kind3 spell-category/cap lookup pending')
    now=f.to_float(state.now_bits)
    multiplier=0x3f800000
    if now<f.to_float(_u(row,148)):multiplier=f.add(multiplier,_u(row,144))
    term=0
    if now<f.to_float(_u(row,156)):term=_u(row,152)
    elif f.to_float(_u(row,164))>now:term=_u(row,160)
    multiplier=f.add(multiplier,term)
    multiplier=f.add(multiplier,_u(row,368))
    #Empty spell source still contributes original +0 before the school term.
    multiplier=f.add(multiplier,0)
    school_term=0x3dcccccd if school&254==2 and f.to_float(_u(row,372))>now else 0
    amount=f.mul(amount_bits,f.add(multiplier,school_term))
    phase=0x3f800000
    if _i(row,64)!=-1:
        if f.to_float(_u(row,420))>now:phase=0x3fc00000
        elif f.to_float(_u(row,416))>now:phase=0x3e800000
        elif any(_u(x,0)==0 and _i(x,40)==2 and struct.unpack_from('<Q',x,32)[0]==target_id for x in state.units432):phase=0x3e800000
    amount=f.mul(amount,phase)
    if _u(row,0)==1:return skip('target_dead')
    amount=0x3f800000 if f.is_nan(amount)else amount
    damage=amount if f.to_float(amount)>1 else 0x3f800000
    new_hp=f.sub(hp,damage)
    if f.to_float(new_hp)<=0:raise PendingDamage139('139 lethal death/XP/loot/RNG continuation pending')
    old_nonnegative=hp if f.to_float(hp)>0 else 0
    accounted=old_nonnegative if f.to_float(old_nonnegative)<f.to_float(damage)else damage
    old_total=struct.unpack('<d',struct.pack('<Q',state.accounted_total_bits))[0]
    new_total=old_total+f.to_float(accounted)
    total_bits=struct.unpack('<Q',struct.pack('<d',new_total))[0]
    updated=bytearray(row);struct.pack_into('<I',updated,288,new_hp);records=list(state.units432);records[index]=bytes(updated)
    after=replace(state,units432=tuple(records),accounted_total_bits=total_bits)
    return DamageResult139(after,True,'nonlethal_numeric_projection',damage,hp,new_hp,accounted,
        (('unit',index,288,new_hp),('game',984,total_bits)))
