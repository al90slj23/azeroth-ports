"""Current139 caller-owned HP changes and default Regen/Leech accounting.

1466 records a positive already-applied amount; it never writes player HP.
This module distinguishes caller numeric writes from its semantic accounting.
Physical2077 catalogs/deques/history and presentation are separate projections.
"""
from dataclasses import dataclass,replace
import math,struct
from . import binary32 as f


class PendingHealing139(NotImplementedError):
    pass


def _f64(bits):
    return struct.unpack('<d',struct.pack('<Q',bits))[0]


def _bits64(value):
    return struct.unpack('<Q',struct.pack('<d',value))[0]


def _finite(word):
    return type(word) is int and 0 <= word <= f.MASK and not f.is_nan(word) and not f.is_inf(word)


def _ceil_hp(word):
    return min(f.MASK,max(0,math.ceil(f.to_float(word))))


@dataclass(frozen=True)
class DefaultHealingSources139:
    class_byte360: int
    counts: tuple

    def __post_init__(self):
        if self.class_byte360 != 1 or self.counts != (0,)*7:
            raise PendingHealing139('Actual defaultWarrior seven empty source owners required')


@dataclass(frozen=True)
class HealingLedger139:
    event_counter960: int
    accepted_count1016: int
    reason_totals64: tuple

    def __post_init__(self):
        if any(type(v) is not int or not 0 <= v < 1<<64 for v in
               (self.event_counter960,self.accepted_count1016)):
            raise ValueError('Explicit inherited u64 accounting counters required')
        if len({k for k,v in self.reason_totals64}) != len(self.reason_totals64):
            raise ValueError('Unique semantic reason totals required')
        for reason,bits in self.reason_totals64:
            if reason not in ('regen','leech') or not math.isfinite(_f64(bits)):
                raise PendingHealing139('Other/invalid inherited heal attribution pending')


@dataclass(frozen=True)
class HealingEvent139:
    reason_id: str
    amount_bits: int
    now_bits: int
    event_id: int
    resolved_spell_id_or_zero: int
    arg3_descriptor_head: int
    arg4_descriptor_head: int
    physical_history_complete: bool = False


def account_heal139(ledger,amount_bits,now_bits,reason,sources):
    if not isinstance(ledger,HealingLedger139) or not isinstance(sources,DefaultHealingSources139):
        raise TypeError('Explicit accounting/source owners required')
    if reason not in ('regen','leech') or not _finite(amount_bits) or not _finite(now_bits):
        raise PendingHealing139('Finite default Regen/Leech attribution only')
    if f.to_float(amount_bits) <= 0:
        return ledger,()
    rows=list(ledger.reason_totals64)
    index=next((j for j,(key,_) in enumerate(rows) if key==reason),None)
    total=f.to_float(amount_bits)+(0.0 if index is None else _f64(rows[index][1]))
    value=(reason,_bits64(total))
    if index is None:rows.append(value)
    else:rows[index]=value
    event_id=(ledger.event_counter960+1)&((1<<64)-1)
    result=replace(ledger,event_counter960=event_id,
        accepted_count1016=(ledger.accepted_count1016+1)&((1<<64)-1),
        reason_totals64=tuple(rows))
    return result,(HealingEvent139(reason,amount_bits,now_bits,event_id,0,
                                  -1 if reason=='regen' else -2,
                                  0 if reason=='regen' else -1),)


@dataclass(frozen=True)
class NumericHealResult139:
    hp_bits: int
    request_bits: int
    actual_delta_bits: int
    accounted_bits: int
    key_writes: tuple
    ledger: HealingLedger139
    events: tuple


def regenerate_player139(hp_bits,maximum_bits,regen1576_bits,extra1620_bits,
                         last_hit1652_bits,now_bits,dt_bits,ledger,sources,*,heal_gate387=0):
    """2123 numeric caller prefix with no periodic28/shield sources."""
    if not all(_finite(v) for v in (hp_bits,maximum_bits,regen1576_bits,
            extra1620_bits,last_hit1652_bits,now_bits,dt_bits)):
        raise PendingHealing139('Finite actual139 regeneration inputs required')
    if heal_gate387 != 0 or f.to_float(dt_bits) < 0:
        raise PendingHealing139('Current default healing gate/nonnegative delta only')
    extra=f.mul(maximum_bits,extra1620_bits) if f.to_float(f.sub(now_bits,last_hit1652_bits))>=3 else 0
    request=f.mul(0x3f800000,f.mul(dt_bits,f.add(regen1576_bits,extra)))
    hp=hp_bits;keys=()
    if f.to_float(hp_bits)<f.to_float(maximum_bits):
        candidate=f.add(0,f.add(hp_bits,request))
        hp=maximum_bits if f.to_float(maximum_bits)<f.to_float(candidate) else candidate
        keys=((22,_ceil_hp(hp)),(28,_ceil_hp(maximum_bits)))
    delta=f.sub(hp,hp_bits);positive=delta if f.to_float(delta)>0 else 0
    amount=request if f.to_float(request)<f.to_float(positive) else positive
    ledger,events=account_heal139(ledger,amount,now_bits,'regen',sources)
    return NumericHealResult139(hp,request,delta,amount,keys,ledger,events)


def leech_player139(hp_bits,maximum_bits,damage_bits,now_bits,ledger,sources,*,heal_gate387=0):
    """913/18421 defaultWarrior1.5% caller branch; general sources reject."""
    if not all(_finite(v) for v in (hp_bits,maximum_bits,damage_bits,now_bits)):
        raise PendingHealing139('Finite actual139 leech inputs required')
    if heal_gate387 != 0 or not isinstance(sources,DefaultHealingSources139):
        raise PendingHealing139('Default Warrior source/gate required')
    request=f.mul(f.mul(damage_bits,0x3c75c28f),0x3f800000)
    candidate=f.add(hp_bits,request)
    hp=maximum_bits if f.to_float(maximum_bits)<f.to_float(candidate) else candidate
    delta=f.sub(hp,hp_bits)
    ledger,events=account_heal139(ledger,delta,now_bits,'leech',sources)
    return NumericHealResult139(hp,request,delta,delta,
        ((22,_ceil_hp(hp)),(28,_ceil_hp(maximum_bits))),ledger,events)
