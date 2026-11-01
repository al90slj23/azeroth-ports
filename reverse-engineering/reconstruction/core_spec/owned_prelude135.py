"""Independent135 class-kind1 melee prelude at the start of learned80 tick1076.

Known-empty G2028/2032 item modifier source is a caller-enforced scope. This is
separate from the embedded basic AbilityRecord at G1256 and runs before owned
skills. Production code reads no original, index, assets, saves or network.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .binary32_sqrt import sqrt_bits
from .cast135 import CastState, projectile_targets
from .cast_events135 import apply_hit
from .progression134 import trunc_sat_u32
from .rng import next_u32_words

# class -> (kind, damage+4, interval+8, radius+12), exact initial data words.
CLASS_PRELUDE = {
    1:(1,1104936960,1070386381,1086324736),
    2:(1,1104674816,1072064102,1086324736),
    3:(0,0,0,0),
    4:(1,1096810496,1067030938,1086324736),
    5:(0,0,0,0),
    7:(0,0,0,0),
    8:(0,0,0,0),
    9:(0,0,0,0),
    11:(0,0,0,0),
}


@dataclass(frozen=True)
class PreludeResult135:
    state: CastState
    timer1628_bits: int
    class_kind: int
    target_id: int | None = None
    damage_bits: int | None = None
    critical: int | None = None
    encoded_damage: int | None = None
    packet_count: int = 0
    applied_damage_bits: int | None = None
    pending: tuple = ('Physical13814 attack packet and914 presentation/accounting remain pending',)


def tick_class_prelude(state, class_byte, timer1628_bits, dt_bits, *,
                       after_hit=None, after_death=None):
    """1076's actual melee prelude for empty item modifier sources.

    Kind0 leaves the timer unchanged. Kind1 decrements it once and at most one
    immediate attack is attempted. The 8685 priority query is exactly the
    independent projectile_targets helper, not a nearest-distance shortcut.
    Damage/critical RNG precede914, then callbacks thread hit/death effects.
    The caller must reject nonempty item modifier sources or first restore
    tag16's ordered sum, which changes this prelude's damage multiplier.
    """
    if not isinstance(state, CastState):
        raise TypeError('Resolved CastState required')
    if type(class_byte) is not int or not 0 <= class_byte <= 255:
        raise ValueError('Explicit class byte required')
    for word in (timer1628_bits, dt_bits):
        if type(word) is not int or not 0 <= word <= f.MASK:
            raise ValueError('Explicit timer/dt binary32 words required')
    kind, base, interval, radius = CLASS_PRELUDE.get(class_byte, CLASS_PRELUDE[1])
    if kind != 1:
        return PreludeResult135(state, timer1628_bits, kind)
    timer = f.sub(timer1628_bits, dt_bits)
    if not f.to_float(timer) <= 0:
        return PreludeResult135(state, timer, kind)
    targets = projectile_targets(state, radius)
    if not targets:
        return PreludeResult135(state, 0x3e19999a, kind)
    # 1076 computes class+4 *1.5 *(item16_sum+1) *1540 before critical.
    damage = f.mul(f.mul(f.mul(base, 0x3fc00000), 0x3f800000), state.damage_multiplier_bits)
    word, rng = next_u32_words(state.rng_words)
    sample = f.mul(f.from_u32(word >> 8), 0x33800000)
    critical = int(f.to_float(state.critical_chance_bits) > f.to_float(sample))
    if critical:
        damage = f.mul(state.critical_multiplier_bits, damage)
    state = replace(state, rng_words=tuple(rng))
    encoded = trunc_sat_u32(damage)
    state, result = apply_hit(state, targets[0], damage, 0,
        after_hit=after_hit, after_death=after_death)
    timer = f.mul(f.mul(interval, 0x3f99999a), sqrt_bits(state.cooldown_multiplier_bits))
    return PreludeResult135(state, timer, kind, targets[0], damage, critical,
                            encoded, 1, result.damage_bits if result.applied else None)
