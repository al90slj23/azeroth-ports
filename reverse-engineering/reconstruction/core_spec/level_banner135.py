"""Fixed135 per-level4630 presentation150/type10, independent of rendering.

The caller supplies each real level transition and its pre/post1512 words.
No original memory, locale Once state, formatting helper or packet is read.
Only the explicitly recovered English and Simplified Chinese templates are
admitted; locale selection/initialization remains a separate producer.
"""
from dataclasses import dataclass
import struct

from . import binary32 as f


class PendingLevelBanner135(NotImplementedError):
    pass


TEMPLATES135 = {
    'en': (
        'You have gained {damage}% damage, {health} maximum health and {regen} health per second.',
        'Your damage over time spells now stack {n} times on one enemy.'),
    'zh': (
        '你获得了{damage}%伤害、{health}最大生命值和每秒{regen}生命值。',
        '你的持续伤害法术现在可以在一个敌人身上叠加{n}次。'),
}


def _word(value):
    if type(value) is not int or not 0 <= value <= f.MASK:
        raise ValueError('Exact unsigned32 banner word required')
    return value


def _format(word, precision):
    _word(word)
    if word & 0x7fffffff >= f.INF:
        raise PendingLevelBanner135('Nonfinite Rust float presentation not restored')
    # Each binary32 is represented exactly by Python binary64. Decimal fixed
    # precision uses ties-to-even, preserving the original f32 sign of zero.
    return format(f.to_float(word), '+.' + str(precision) + 'f')


def type10_payload135(text):
    if type(text) is not str or '\0' in text:
        raise ValueError('Explicit NUL-free banner text required')
    raw = text.encode('utf8', errors='strict')
    if len(raw) > 1048576:
        raise ValueError('Banner text budget')
    #28964: type:u8, zero:u32, zero:u64, UTF8 length including terminator:u32,
    # UTF8 bytes, string terminator, final packet terminator.
    return struct.pack('<BIQI', 10, 0, 0, len(raw) + 1) + raw + b'\0\0'


@dataclass(frozen=True)
class LevelBannerInput135:
    level_before: int
    level_after: int
    derived_before: tuple
    derived_after: tuple
    owned_definition84: tuple
    locale: str = 'en'


@dataclass(frozen=True)
class LevelBannerResult135:
    packets: tuple
    texts: tuple
    damage_delta_percent_bits: int | None = None
    maximum_health_delta_bits: int | None = None
    regeneration_delta_bits: int | None = None
    dot_stack_limit: int | None = None


def level_banners135(value: LevelBannerInput135):
    """Each actual single level increase emits growth before heal/next level.

    Phase, choice flags, mode, difficulty and UI preferences do not gate this
    block of4630. A multi-level4630 call must supply every intermediate1512
    transition in order; endpoint-only growth would lose messages and rounding.
    """
    if not isinstance(value, LevelBannerInput135):
        raise TypeError('Explicit per-level banner input required')
    before, after = _word(value.level_before), _word(value.level_after)
    if before == after:
        return LevelBannerResult135((), ())
    if before >= 120 or after != before + 1:
        raise PendingLevelBanner135('Single actual4630 level transition required')
    if value.locale not in TEMPLATES135:
        raise PendingLevelBanner135('Only explicit recovered en/zh locale admitted')
    if not isinstance(value.owned_definition84, tuple) or any(
        type(word) is not int or not 0 <= word <= 255 for word in value.owned_definition84):
        raise ValueError('Actual owned-definition execution bytes required')
    old, new = dict(value.derived_before), dict(value.derived_after)
    for offset in (1536, 1540, 1576, 1608):
        if offset not in old or offset not in new:
            raise ValueError('Missing per-level derived word ' + str(offset))
        _word(old[offset]); _word(new[offset])
    damage = f.mul(f.sub(new[1540], old[1540]), 0x42c80000)
    health = f.sub(new[1536], old[1536])
    regen = f.sub(new[1576], old[1576])
    growth, stacks = TEMPLATES135[value.locale]
    text = growth.replace('{damage}', _format(damage, 0)).replace(
        '{health}', _format(health, 0)).replace('{regen}', _format(regen, 2))
    texts = [text]
    limit = None
    if 6 in value.owned_definition84 and new[1608] > old[1608]:
        limit = min(new[1608], 3) + 1
        texts.append(stacks.replace('{n}', str(limit)))
    return LevelBannerResult135(tuple((150, type10_payload135(text).hex()) for text in texts),
        tuple(texts), damage, health, regen, limit)
