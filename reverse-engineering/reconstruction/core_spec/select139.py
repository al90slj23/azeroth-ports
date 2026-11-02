"""Current1391093 first new-ability selection and4603 control projection."""
from dataclasses import dataclass, replace
import struct
from . import binary32 as f
from .candidates139_data import DEFINITIONS139, TIER_COOLDOWN139, TIER_DAMAGE139
from .growth139 import GrowthState139, PendingGrowth139, recalculate_growth139


@dataclass(frozen=True)
class SelectResult139:
    state: GrowthState139
    accepted: bool
    new_owned_index: int | None
    pending: tuple


def initialize_selected139(name, tier):
    if name not in DEFINITIONS139 or not 0 <= tier <= 4:
        raise PendingGrowth139('Current declared warrior new ability/tier required')
    pointer, raw, kinds = DEFINITIONS139[name]
    definition = bytes.fromhex(raw)
    words = [pointer, 1, 0x3f000000, 0x3f800000, 0x3f800000, 0, 0x3f800000, 0x3f800000,
             0, 0, 0, 0, 0, 0x3f800000, 0x3f800000, 0, 0x3f800000, 0x3f800000, 0, 0x3f800000]
    if tier:
        effect = struct.unpack_from('<I', definition)[0]
        execution = definition[84]
        if execution == 9:
            damage = effect <= 13 and bool((1 << effect) & 8384)
        elif execution == 11:
            damage = 0 in kinds
        else:
            damage = f.to_float(struct.unpack_from('<I', definition, 48)[0]) > 0
        if damage:
            words[3] = f.mul(words[3], f.add(TIER_DAMAGE139[tier - 1], 0x3f800000))
        else:
            words[4] = f.mul(words[4], f.sub(0x3f800000, TIER_COOLDOWN139[tier - 1]))
    return struct.pack('<20I', *words)


def select_card139(state, index):
    if not isinstance(state, GrowthState139):
        raise TypeError('GrowthState139 required')
    if state.phase2587 != 2 or not 0 <= index < len(state.candidates) or state.selection_kind2585 == 255:
        return SelectResult139(state, False, None, ())
    if state.selection_kind2585 != 0:
        raise PendingGrowth139('Nonordinary selection source pending')
    card = state.candidates[index]
    if card.variant != 'new':
        raise PendingGrowth139('Existing-ability upgrade/gold selection pending')
    if state.source_counts != (0,) * 7:
        raise PendingGrowth139('Nonempty ability modifier/stat sources pending')
    if state.units432_cells or state.auxiliary112_cells or state.claims88_cells:
        raise PendingGrowth139('Nonempty world resume source pending')
    if state.pending != 1 or state.live32_cells:
        raise PendingGrowth139('Only first completed level-choice continuation admitted')
    owned = state.owned_records80 + (initialize_selected139(card.ability_id, card.tier),)
    state = recalculate_growth139(replace(state, owned_records80=owned), state.level)
    live = [None] * 32
    live[:8] = bytes(8)
    live[8:12] = struct.pack('<I', 12)
    live[20:32] = struct.pack('<III', 1020, f.add(state.now_bits, 0x3f800000), 0)
    state = replace(state, pending=0, phase2587=1, selection_kind2585=255, flag2581=1,
                    flags2573=0, candidates=(), live32_cells=(tuple(live),))
    return SelectResult139(state, True, len(owned) - 1,
        ('1093 appearance/equipment keyed fields and notifications are not fully projected',
         '4603 live32 payload12..19 remainsNone;Aura48/BTree allocation and packets are observations',
         'Other ability choices and nonempty world stop/resume remain separate domains'))
