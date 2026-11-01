"""Fixed135 learned Battle Shout6673 effect8 self-buff numeric consumer.

This reuses the independently implemented execution9 self-buff mechanism, with
its own exact88B learned definition and strict source boundary. It does not add
Battle Shout to the racial catalogue or read original code/results/resources.
Physical1202 aura/display keys, proc callbacks and packet encoding stay pending.
"""
from dataclasses import dataclass
import struct

from .racial_cast135 import RacialDefinition135, RacialCastResult135, cast_self_buff
from .player_update135 import prepare_player_update

POINTER = 5467956
RAW88_HEX = ('08000000cdcccc3e000000000f4f53000c000000426053000c0000004e6053001b000000'
             '6960530002000000111a0000000000000000804100000000000000000000000000000041'
             '00000000000000000000000009000000')


class PendingBattleShout135(NotImplementedError):
    pass


@dataclass(frozen=True)
class BattleShoutDefinition135(RacialDefinition135):
    """Protocol-compatible self-buff declaration; not a racial ability."""
    pointer: int = POINTER
    ability_id: bytes = b'battle_shout'
    raw88_hex: str = RAW88_HEX

    def words(self):
        if self.pointer != POINTER or self.ability_id != b'battle_shout' or self.raw88_hex != RAW88_HEX:
            raise ValueError('Exact fixed135 Battle Shout88B declaration required')
        raw = bytes.fromhex(self.raw88_hex)
        if len(raw) != 88 or raw[84:86] != bytes((9, 0)):
            raise ValueError('Battle Shout execution9/school0 identity differs')
        return struct.unpack('<22I', raw)


@dataclass(frozen=True)
class BattleShoutCastResult135(RacialCastResult135):
    pass


def _sources(level, live_records, explicit):
    if explicit is not True:
        raise PendingBattleShout135('Explicit absent external Battle Shout/proc sources required')
    if any(getattr(level.sources, name) for name in
           ('passives', 'adjustments', 'item_modifiers', 'owned_skills', 'timed_records', 'definitions')):
        raise PendingBattleShout135('Nonempty external stat/item/talent/proc sources require continuation')
    if type(live_records) is not tuple or len(live_records) != len(level.sources.live_effects):
        raise ValueError('Complete raw32 and semantic live source ownership required')
    if any(effect.kind not in (7, 8, 9, 12) for effect in level.sources.live_effects):
        raise PendingBattleShout135('Unrestored live source family retained')
    if level.stats.conditional1344_id == 11426:
        raise PendingBattleShout135('Icebarrier source/aura cleanup remains separate')


def cast_battle_shout135(cast, level, definition, owned, *, live_records,
        unspecified_live_words=(), busy488=0, attempted_spell_sets=None,
        explicit_other_sources_absent=False):
    """922 effect8: attempt sets, target30, reset owner0, append,1512,1202.

    Direct922 preserves the entire owned80B record, including its countdown.
    1076 owns countdown/infinity/floor/reset and should use its existing ordered
    scheduler with this dispatcher. Success here covers the declared numeric
    projection; the returned pending list does not claim aura/wire completion.
    """
    _sources(level, live_records, explicit_other_sources_absent)
    if not isinstance(definition, BattleShoutDefinition135):
        raise TypeError('Explicit learned BattleShoutDefinition135 required')
    if cast.context908 & ~1:
        raise PendingBattleShout135('Inherited proc-cast context beyond the known ledger bit remains pending')
    result = cast_self_buff(cast, level, definition, owned, live_records=live_records,
        unspecified_live_words=unspecified_live_words, busy488=busy488,
        attempted_spell_sets=attempted_spell_sets)
    return BattleShoutCastResult135(**{**vars(result), 'pending': (
        '1202 physical aura/object keys and message packet bytes remain pending',
        '1076 owns the learned80 countdown/cooldown; the basic1256 record is separately owned')})


def expire_battle_shout135(level, live_records, unspecified_live_words, now_bits,
        dt_bits, last_hit_bits, *, explicit_other_sources_absent=False):
    """Use recovered2088 expiry/stat/regen prefix; caller still owns1076.

    Kept separate from cast: expiration does not invent an automatic recast or
    clear an owned countdown. Only the supported empty periodic source domain
    can run; arbitrary active periodic producers remain explicit boundaries.
    """
    _sources(level, live_records, explicit_other_sources_absent)
    return prepare_player_update(level, live_records, unspecified_live_words,
        now_bits, dt_bits, last_hit_bits, explicit_other_sources_absent=True,
        periodic_input=())
