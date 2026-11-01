"""Fixed135 guardian921 idle/return consumer over explicit physical owners.

This is a per-unit slice, not a replacement for921's global distance-map,
cross-unit queue drain, incoming callbacks or910. It reads no original program,
memory, resources or IO. Nonempty skill timers remain independently owned;
their unknown U68 allocator address is never read or replaced with zero.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .ai135 import position, _distance, _speed
from .ai_world135 import _geometry
from .record_cells135 import cells135, u32, u64, put_u32, encode_row
from .special2376_spawn135 import SpecialCooldowns135
from .special2376_spawn135_data import special_ability_records135, special_header135


class PendingGuardianAi135(NotImplementedError):
    """The next actual guardian consumer is outside the admitted slice."""


@dataclass(frozen=True)
class GuardianContext135:
    now_bits: int
    dt_bits: int
    player_xyz_bits: tuple
    special_storage40: tuple
    special_count: int
    world: object
    mode: int = 0
    local_peer: int = 0
    phase2587: int = 1
    other_sources_absent: bool = False


@dataclass(frozen=True)
class GuardianUnitResult135:
    record: object
    cooldowns: SpecialCooldowns135
    status: str
    movements: tuple = ()
    movement_geometry: tuple = ()
    attacks: tuple = ()
    planned_actions: tuple = ()
    pending: tuple = ()


def _finite(word):
    if type(word) is not int or not 0 <= word <= f.MASK or word & 0x7fffffff >= f.INF:
        raise ValueError('Explicit finite guardian binary32 word required')
    return word


def _validate(record, owner, context, unit_index):
    if not isinstance(context, GuardianContext135) or not isinstance(owner, SpecialCooldowns135):
        raise TypeError('Explicit guardian context and producer-owned cooldowns required')
    if context.other_sources_absent is not True:
        raise PendingGuardianAi135('Explicit absent auxiliary/status/party sources required')
    if context.mode != 0 or context.phase2587 != 1:
        raise PendingGuardianAi135('Only local running guardian921 domain is restored')
    if type(context.local_peer) is not int or not 0 <= context.local_peer <= f.MASK:
        raise ValueError('Explicit local peer word required')
    if type(context.player_xyz_bits) is not tuple or len(context.player_xyz_bits) != 3:
        raise ValueError('Explicit player XYZ words required')
    for word in (context.now_bits, context.dt_bits, *context.player_xyz_bits):
        _finite(word)
    if not 0 <= f.to_float(context.dt_bits) <= .1000000015:
        raise ValueError('Clamped nonnegative guardian frame delta required')
    if (type(context.special_storage40) is not tuple or type(context.special_count) is not int
            or not 0 <= context.special_count <= len(context.special_storage40) <= 512):
        raise ValueError('Explicit special40 owner and active count required')
    for row in context.special_storage40:
        cells135(row, 40)
    if context.world is None or not all(callable(getattr(context.world, name, None))
            for name in ('height', 'nearest_primary', 'nav_probe')):
        raise TypeError('Explicit independently produced world query provider required')
    raw = cells135(record, 424)
    word = lambda offset: u32(raw, offset, 'guardian_ai135 owned field')
    if u64(raw, 112, 'guardian_ai135 GUID owner') != owner.guid:
        raise ValueError('Guardian cooldown owner GUID differs')
    if word(0) != 0:
        raise PendingGuardianAi135('Guardian death/resource cleanup is a separate consumer')
    if any(word(offset) != f.MASK for offset in (40, 244)):
        raise PendingGuardianAi135('Only actual special64 family with absent40/244 restored')
    if (owner.capacity != 3 or len(owner.timers_bits) != 3 or word(64) != 3 or word(72) != 3
            or owner.physical_pointer_offset != 68 or owner.physical_pointer_known):
        raise PendingGuardianAi135('Exact three-timer independent guardian owner required')
    if raw[68:72] != [None] * 4:
        raise ValueError('Independent guardian allocator word must stay explicitly unknown')
    if any(word(offset) != owner.ability_pointer for offset in (76, 84)) or any(word(offset) != 3 for offset in (80, 88)):
        raise PendingGuardianAi135('Nondefault guardian skill variant requires continuation')
    if word(96) != owner.header_pointer:
        raise ValueError('Guardian header identity differs from its timer owner')
    if (owner.ability_records44_hex != special_ability_records135(owner.ability_pointer)
            or owner.header28_hex != special_header135(owner.header_pointer)):
        raise ValueError('Guardian declaration bytes differ from fixed producer')
    for timer in owner.timers_bits:
        _finite(timer)
    if any(word(offset) for offset in (8, 16, 232, 240, 360, 372, 380, 388)):
        raise PendingGuardianAi135('Guardian status/resource source requires an earlier921 continuation')
    if word(280) != context.local_peer:
        raise PendingGuardianAi135('Guardian remote-owner routing remains unresolved')
    for offset in (124, 288, 292, 300, 304, 308, 316, 320, 324, 328, 332, 336,
                   340, 344, 348, 352, 400, 404):
        _finite(word(offset))
    if unit_index is not None and (type(unit_index) is not int or not 0 <= unit_index < 512):
        raise ValueError('Explicit relocated guardian unit index required')
    return raw, replace(owner, unit_index=owner.unit_index if unit_index is None else unit_index)


def _home(raw, context, xyz):
    index = u32(raw, 92, 'guardian_ai135 home index')
    if index >= context.special_count:
        return xyz  # Original921 selects its current-position scratch fallback.
    row = context.special_storage40[index]
    result = tuple(u32(row, offset, 'guardian_ai135 special home XYZ') for offset in (16, 20, 24))
    for word in result:
        _finite(word)
    return result


def step_guardian_unit135(record, cooldown_owner, context, *, world=None, unit_index=None):
    """Complete admitted idle/return branch; engage/leash/action910 stay pending.

    The caller owns921's preceding global distance-map update and final merged
    event drain. Returned movements are in ordinary AiResult135 logical form;
    movement_geometry contains the separately queried packet XYZ projection.
    Exceptions return no replacement state, so an unsupported frame cannot be
    counted complete merely because a prefix was calculated.
    """
    if world is not None:
        context = replace(context, world=world)
    raw, owner = _validate(record, cooldown_owner, context, unit_index)
    word = lambda offset: u32(raw, offset, 'guardian_ai135 idle field')
    now, now_value = context.now_bits, f.to_float(context.now_bits)
    if f.to_float(word(400)) > now_value:
        return GuardianUnitResult135(encode_row(raw), owner, 'guardian_locked_complete')
    xyz = position(raw, now)
    distance = _distance(xyz, context.player_xyz_bits)
    # The shared melee branch precedes the special64 state dispatch. Keep a
    # contact branch explicit rather than bypassing its actual incoming work.
    if f.to_float(distance) <= f.to_float(word(308)):
        raise PendingGuardianAi135('Guardian shared melee/contact requires ordered incoming continuation')
    if raw[108] != 0:
        raise PendingGuardianAi135('Guardian engaged/leash/skill consumers remain pending')
    if word(288) != word(292) or not f.to_float(word(292)) > 0:
        raise PendingGuardianAi135('Damaged guardian aggro transition requires continuation')
    home = _home(raw, context, xyz)
    home_distance = _distance(xyz, home)
    if f.to_float(home_distance) <= 3 and f.to_float(distance) <= 20:
        raise PendingGuardianAi135('Nearby player activates guardian; engage/skill branch remains pending')
    put_u32(raw, 352, f.sub(word(352), context.dt_bits))
    if f.to_float(word(344)) > 0 and now_value < f.to_float(f.add(word(340), word(344))):
        return GuardianUnitResult135(encode_row(raw), owner, 'guardian_idle_inflight_complete')
    if f.to_float(home_distance) <= 2:
        return GuardianUnitResult135(encode_row(raw), owner, 'guardian_idle_complete')
    speed = _speed(raw, now)
    duration = f.div(home_distance, speed if f.to_float(speed) > .5 else 0x3f000000)
    for offset, point in ((316, xyz), (328, home)):
        for index, value in enumerate(point):
            put_u32(raw, offset + index * 4, value)
    put_u32(raw, 340, now)
    put_u32(raw, 344, duration)
    movement = (owner.guid, xyz, home, duration)
    return GuardianUnitResult135(encode_row(raw), owner, 'guardian_idle_return_complete',
        movements=(movement,), movement_geometry=(_geometry(context.world, *movement),))


def guardian_cleanup_admitted135(record, cooldown_owner, context):
    """Permit preservation of this exact live domain, never corpse deletion.

    A caller may exempt such living rows from ordinary-family corpse guards.
    This predicate does not run cleanup or dispose an owned timer allocation.
    """
    try:
        result = step_guardian_unit135(record, cooldown_owner, context)
    except (PendingGuardianAi135, ValueError, TypeError):
        return False
    return result.status in ('guardian_idle_complete', 'guardian_idle_inflight_complete',
                            'guardian_idle_return_complete', 'guardian_locked_complete')
