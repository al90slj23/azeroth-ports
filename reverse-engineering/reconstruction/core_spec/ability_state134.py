"""Independent0.134.0 new owned-ability initialization, helpers26967/26591.

No WASM or evidence file is read by this model. Caller-owned modifier snapshots
are explicit: None means unresolved producer state and raises, while () means
the caller established that the 20B modifier vector is empty. Reconstructing
the talent/equipment producers of that vector is outside this numeric module.
"""
from dataclasses import dataclass, replace
import struct

from . import binary32 as f
from .ability_state import AbilityRecord, NewAbilityCard, UnresolvedAbilityEffect

ONE = 0x3f800000
COOLDOWN_FLOOR = 0x3ecccccd
SOURCE_SHA256 = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
TIER_COOLDOWN = (0x3d8f5c29, 0x3dcccccd, 0x3e051eb8, 0x3e2e147b, 0x3e6b851f)
TIER_DAMAGE = (0x3e3851ec, 0x3e800000, 0x3eae147b, 0x3eeb851f, 0x3f266666)


@dataclass(frozen=True)
class AbilityDefinition134:
    pointer: int
    ability_id: bytes
    execution_kind: int
    school: int
    effect_tag: int
    base_damage_bits: int
    kinds: tuple


@dataclass(frozen=True)
class AbilityModifier134:
    """One explicit20B26967 input, with pointed-to strings copied as bytes.

    filter_tag1 matches ability_id,2 matches any ability_ids,3 matches school,
    4 matches execution_kind,5/6 skip; all other byte tags apply unconditionally.
    Numeric kind1=cooldown reduction,2=targets,3=area,4=duration,5=life-damage,
    6=field76; other byte kinds add damage. Input vector order is significant.
    These meanings describe helper dispatch, not real producer/tag availability.
    """
    kind: int
    value_bits: int
    filter_tag: int = 0
    filter_value: int = 0
    ability_id: bytes = b''
    ability_ids: tuple = ()


def _matches(modifier, definition):
    tag = modifier.filter_tag & 255
    if tag == 1:
        return modifier.ability_id == definition.ability_id
    if tag == 2:
        return definition.ability_id in modifier.ability_ids
    if tag == 3:
        return modifier.filter_value & 255 == definition.school
    if tag == 4:
        return modifier.filter_value & 255 == definition.execution_kind
    return tag not in (5, 6)


def round_targets_bits(bits):
    """Original85718: f32 bias0.49999997 with input sign, then bit truncation."""
    value = f.add(bits, 0x3effffff | (bits & f.SIGN))
    exponent = (value >> 23) & 255
    if exponent <= 149:
        mask = f.SIGN if exponent < 127 else (-0x800000 >> (exponent - 127)) & f.MASK
        value &= mask
    return value


def _trunc_sat_u32(bits):
    value = f.to_float(bits)
    if not value > 0:
        return 0
    return f.MASK if value >= 4294967295 else int(value)


def modifier_additional_bytes(definition, *, modifiers=None):
    """Return26967's seven raw words for record+52..79.

    Each add rounds to binary32. Targets round only after the ordered sum;
    cooldown is max(0.4,1-sum) with NaN mapped to0.4 by the original selects.
    """
    if modifiers is None:
        raise UnresolvedAbilityEffect('Need explicit0.13420B modifier snapshot; producer state is unresolved')
    damage = area = duration = field76 = ONE
    cooldown_reduction = targets = life_damage = 0
    for modifier in modifiers:
        if not isinstance(modifier, AbilityModifier134):
            raise TypeError('Need AbilityModifier134 snapshot records')
        if not _matches(modifier, definition):
            continue
        kind = modifier.kind & 255
        value = modifier.value_bits & f.MASK
        if kind == 1:
            cooldown_reduction = f.add(cooldown_reduction, value)
        elif kind == 2:
            targets = f.add(targets, value)
        elif kind == 3:
            area = f.add(area, value)
        elif kind == 4:
            duration = f.add(duration, value)
        elif kind == 5:
            life_damage = f.add(life_damage, value)
        elif kind == 6:
            field76 = f.add(field76, value)
        else:
            damage = f.add(damage, value)
    cooldown = f.sub(ONE, cooldown_reduction)
    if not f.to_float(cooldown) > f.to_float(COOLDOWN_FLOOR):
        cooldown = COOLDOWN_FLOOR
    return struct.pack('<7I', damage, cooldown, _trunc_sat_u32(round_targets_bits(targets)),
                       area, duration, life_damage, field76)


def tier_adjustment_kind(definition):
    """26591's damage/cooldown classification, independently read in0.134."""
    if definition.execution_kind == 9:
        return 'damage' if definition.effect_tag <= 13 and (1 << definition.effect_tag) & 8384 else 'cooldown'
    if definition.execution_kind == 11:
        return 'damage' if 0 in definition.kinds else 'cooldown'
    return 'damage' if f.to_float(definition.base_damage_bits) > 0 else 'cooldown'


def initialize_ability(definition, *, tier=0, modifiers=None):
    """Build1073's80B record, then26967, then26591 in original order.

    Current candidates produce tiers0..4. Original26591 also has a fifth
    nonzero table entry (tier5), retained here; other tiers raise. No level or
    kind counter is increased by the new-ability rarity adjustment.
    """
    additional = modifier_additional_bytes(definition, modifiers=modifiers)
    record = AbilityRecord.from_bytes(AbilityRecord(definition.pointer).to_bytes()[:52] + additional)
    if tier == 0:
        return record
    if tier not in range(1, 6):
        raise ValueError('Original26591 traps outside tiers0..5')
    if tier_adjustment_kind(definition) == 'damage':
        return replace(record, damage_bits=f.mul(record.damage_bits, f.add(TIER_DAMAGE[tier-1], ONE)))
    return replace(record, cooldown_bits=f.mul(record.cooldown_bits, f.sub(ONE, TIER_COOLDOWN[tier-1])))


@dataclass(frozen=True)
class SelectionState134:
    owned: tuple = ()
    candidates: tuple = ()
    phase2579: int = 2
    selection_kind2577: int = 0


@dataclass(frozen=True)
class SelectionResult134:
    state: SelectionState134
    accepted: bool
    owned_index: int | None = None
    pending_effects: tuple = ()


def accept_new_ability_selection(state, index, definitions, *, modifiers=None):
    """1073 entry guards and append only; shared original tail stays pending."""
    if state.phase2579 != 2 or not 0 <= index < len(state.candidates) or state.selection_kind2577 == 255:
        return SelectionResult134(state, False)
    card = state.candidates[index]
    if not isinstance(card, NewAbilityCard):
        raise UnresolvedAbilityEffect('This API accepts the canonical new-ability candidate variant')
    definition = definitions[card.ability_id]
    if definition.ability_id != card.ability_id:
        raise ValueError('Definition string-ID lookup differs')
    record = initialize_ability(definition, tier=card.tier, modifiers=modifiers)
    return SelectionResult134(replace(state, owned=state.owned+(record,)), True, len(state.owned),
        ('1073 spell notification', '1073 shared talent/equipment/notification postprocessing',
         '1513 derived-stat rebuild', '4600 selection completion'))


# Frozen114x88B official0.134.0 declarations; checker re-extracts every field
# from current-source active data. They are never loaded from WASM at runtime.
DEFINITIONS = {
    b'cleave': AbilityDefinition134(5463472, b'cleave', 5, 0, 0, 0x423c0000, (0, 1, 2)),
    b'whirlwind': AbilityDefinition134(5463560, b'whirlwind', 2, 0, 0, 0x42400000, (0, 1, 3)),
    b'thunder_clap': AbilityDefinition134(5463648, b'thunder_clap', 2, 0, 1, 0x41a80000, (0, 1, 3)),
    b'mortal_strike': AbilityDefinition134(5463736, b'mortal_strike', 5, 0, 0, 0x43088000, (0, 1, 2)),
    b'execute': AbilityDefinition134(5463824, b'execute', 7, 0, 0, 0x42ea0000, (0, 1)),
    b'demo_shout': AbilityDefinition134(5463912, b'demo_shout', 2, 0, 11, 0x41000000, (1, 3)),
    b'battle_shout': AbilityDefinition134(5464000, b'battle_shout', 9, 0, 8, 0x00000000, (1, 4)),
    b'bloodthirst': AbilityDefinition134(5464088, b'bloodthirst', 5, 0, 5, 0x42b00000, (0, 1, 2)),
    b'rend': AbilityDefinition134(5464176, b'rend', 6, 0, 0, 0x429c0000, (0, 1, 4, 2)),
    b'shield_slam': AbilityDefinition134(5464264, b'shield_slam', 5, 0, 3, 0x43160000, (0, 1, 2)),
    b'bloodrage': AbilityDefinition134(5464352, b'bloodrage', 11, 0, 0, 0x43110000, (0, 1, 3)),
    b'consecration': AbilityDefinition134(5464440, b'consecration', 3, 1, 0, 0x42c00000, (0, 1, 3, 4)),
    b'exorcism': AbilityDefinition134(5464528, b'exorcism', 0, 1, 0, 0x43070000, (0, 1, 2)),
    b'hammer_of_wrath': AbilityDefinition134(5464616, b'hammer_of_wrath', 0, 1, 0, 0x42850000, (0, 1, 2)),
    b'holy_shock': AbilityDefinition134(5464704, b'holy_shock', 1, 1, 6, 0x42a70000, (0, 1, 2)),
    b'holy_wrath': AbilityDefinition134(5464792, b'holy_wrath', 2, 1, 0, 0x42606666, (0, 1, 3)),
    b'judgement': AbilityDefinition134(5464880, b'judgement', 0, 1, 0, 0x43480000, (0, 1, 2)),
    b'hammer_of_justice': AbilityDefinition134(5464968, b'hammer_of_justice', 0, 1, 3, 0x425c0000, (0, 1, 2)),
    b'holy_light': AbilityDefinition134(5465056, b'holy_light', 9, 1, 6, 0x00000000, (0, 1)),
    b'divine_shield': AbilityDefinition134(5465144, b'divine_shield', 9, 1, 12, 0x00000000, (1, 4)),
    b'holy_shield': AbilityDefinition134(5465232, b'holy_shield', 9, 1, 13, 0x00000000, (0, 1, 4)),
    b'redemption': AbilityDefinition134(5465320, b'redemption', 11, 1, 0, 0x42500000, (0, 1, 3)),
    b'auto_shot': AbilityDefinition134(5465408, b'auto_shot', 0, 0, 0, 0x420a0000, (0, 1, 2)),
    b'arcane_shot': AbilityDefinition134(5465496, b'arcane_shot', 0, 6, 0, 0x42890000, (0, 1, 2)),
    b'multi_shot': AbilityDefinition134(5465584, b'multi_shot', 0, 0, 0, 0x41f00000, (0, 1, 2)),
    b'serpent_sting': AbilityDefinition134(5465672, b'serpent_sting', 6, 3, 0, 0x42640000, (0, 1, 4, 2)),
    b'volley': AbilityDefinition134(5465760, b'volley', 3, 6, 0, 0x424e6666, (0, 1, 3, 4)),
    b'explosive_trap': AbilityDefinition134(5465848, b'explosive_trap', 2, 2, 0, 0x420b3333, (0, 1, 3)),
    b'concussive_shot': AbilityDefinition134(5465936, b'concussive_shot', 0, 6, 1, 0x41880000, (0, 1, 2)),
    b'aimed_shot': AbilityDefinition134(5466024, b'aimed_shot', 0, 0, 0, 0x43aa0000, (0, 1, 2)),
    b'immolation_trap': AbilityDefinition134(5466112, b'immolation_trap', 3, 2, 0, 0x42700000, (0, 1, 3, 4)),
    b'frost_trap': AbilityDefinition134(5466200, b'frost_trap', 3, 4, 2, 0x41840000, (0, 1, 3, 4)),
    b'hunters_mark': AbilityDefinition134(5466288, b'hunters_mark', 11, 6, 0, 0x437a0000, (0, 1, 3)),
    b'sinister_strike': AbilityDefinition134(5466376, b'sinister_strike', 5, 0, 0, 0x420c0000, (0, 1, 2)),
    b'eviscerate': AbilityDefinition134(5466464, b'eviscerate', 7, 0, 0, 0x42b60000, (0, 1)),
    b'blade_flurry': AbilityDefinition134(5466552, b'blade_flurry', 2, 0, 0, 0x41c00000, (0, 1, 3)),
    b'rupture': AbilityDefinition134(5466640, b'rupture', 6, 0, 0, 0x42740000, (0, 1, 4, 2)),
    b'kidney_shot': AbilityDefinition134(5466728, b'kidney_shot', 5, 0, 3, 0x41c80000, (0, 1, 2)),
    b'gouge': AbilityDefinition134(5466816, b'gouge', 5, 0, 3, 0x41cc0000, (0, 1, 2)),
    b'ghostly_strike': AbilityDefinition134(5466904, b'ghostly_strike', 5, 0, 7, 0x42380000, (0, 1, 2)),
    b'adrenaline_rush': AbilityDefinition134(5466992, b'adrenaline_rush', 9, 0, 9, 0x00000000, (1, 4)),
    b'backstab': AbilityDefinition134(5467080, b'backstab', 7, 0, 0, 0x425e0000, (0, 1)),
    b'slice_and_dice': AbilityDefinition134(5467168, b'slice_and_dice', 9, 0, 8, 0x00000000, (1, 4)),
    b'seal_fate': AbilityDefinition134(5467256, b'seal_fate', 11, 0, 0, 0x43020000, (0, 1, 2)),
    b'smite': AbilityDefinition134(5467344, b'smite', 0, 1, 0, 0x42260000, (0, 1, 2)),
    b'sw_pain': AbilityDefinition134(5467432, b'sw_pain', 6, 5, 0, 0x42900000, (0, 1, 4, 2)),
    b'mind_blast': AbilityDefinition134(5467520, b'mind_blast', 0, 5, 0, 0x42ba0000, (0, 1, 2)),
    b'holy_nova': AbilityDefinition134(5467608, b'holy_nova', 2, 1, 6, 0x41da6666, (0, 1, 3)),
    b'pw_shield': AbilityDefinition134(5467696, b'pw_shield', 9, 1, 7, 0x00000000, (0, 1)),
    b'renew': AbilityDefinition134(5467784, b'renew', 9, 1, 6, 0x00000000, (0, 1)),
    b'holy_fire': AbilityDefinition134(5467872, b'holy_fire', 0, 1, 0, 0x43200000, (0, 1, 2)),
    b'mind_flay': AbilityDefinition134(5467960, b'mind_flay', 8, 5, 1, 0x42533333, (0, 1, 3)),
    b'psychic_scream': AbilityDefinition134(5468048, b'psychic_scream', 2, 5, 4, 0x41280000, (1, 3)),
    b'devouring_plague': AbilityDefinition134(5468136, b'devouring_plague', 6, 5, 5, 0x42d50000, (0, 1, 4, 2)),
    b'lightwell': AbilityDefinition134(5468224, b'lightwell', 11, 1, 0, 0x42a00000, (0, 1, 4, 2)),
    b'lightning_bolt': AbilityDefinition134(5468312, b'lightning_bolt', 0, 3, 0, 0x42120000, (0, 1, 2)),
    b'chain_lightning': AbilityDefinition134(5468400, b'chain_lightning', 4, 3, 0, 0x421e0000, (0, 1, 2)),
    b'earth_shock': AbilityDefinition134(5468488, b'earth_shock', 0, 3, 0, 0x42bb0000, (0, 1, 2)),
    b'flame_shock': AbilityDefinition134(5468576, b'flame_shock', 6, 2, 0, 0x42a50000, (0, 1, 4, 2)),
    b'frost_shock': AbilityDefinition134(5468664, b'frost_shock', 0, 4, 1, 0x42680000, (0, 1, 2)),
    b'lightning_shield': AbilityDefinition134(5468752, b'lightning_shield', 9, 3, 13, 0x00000000, (0,)),
    b'magma_totem': AbilityDefinition134(5468840, b'magma_totem', 10, 2, 0, 0x41c00000, (0, 1, 3, 4)),
    b'searing_totem': AbilityDefinition134(5468928, b'searing_totem', 10, 2, 0, 0x42080000, (0, 1, 4, 2)),
    b'fire_nova': AbilityDefinition134(5469016, b'fire_nova', 2, 2, 0, 0x42280000, (0, 1, 3)),
    b'healing_wave': AbilityDefinition134(5469104, b'healing_wave', 9, 3, 6, 0x00000000, (0, 1)),
    b'stormstrike': AbilityDefinition134(5469192, b'stormstrike', 5, 3, 0, 0x43ac0000, (0, 1, 2)),
    b'rockbiter': AbilityDefinition134(5469280, b'rockbiter', 5, 3, 0, 0x42f00000, (0, 1, 2)),
    b'fireball': AbilityDefinition134(5469368, b'fireball', 0, 2, 0, 0x424a0000, (0, 1, 2)),
    b'frostbolt': AbilityDefinition134(5469456, b'frostbolt', 0, 4, 1, 0x42120000, (0, 1, 2)),
    b'arcane_missiles': AbilityDefinition134(5469544, b'arcane_missiles', 1, 6, 0, 0x41c9999a, (0, 1, 2)),
    b'frost_nova': AbilityDefinition134(5469632, b'frost_nova', 2, 4, 2, 0x4144cccd, (0, 1, 3)),
    b'arcane_explosion': AbilityDefinition134(5469720, b'arcane_explosion', 2, 6, 0, 0x41c9999a, (0, 1, 3)),
    b'blizzard': AbilityDefinition134(5469808, b'blizzard', 3, 4, 1, 0x4273999a, (0, 1, 3, 4)),
    b'flamestrike': AbilityDefinition134(5469896, b'flamestrike', 3, 2, 0, 0x42546666, (0, 1, 3, 4)),
    b'fire_blast': AbilityDefinition134(5469984, b'fire_blast', 1, 2, 0, 0x42880000, (0, 1, 2)),
    b'cone_of_cold': AbilityDefinition134(5470072, b'cone_of_cold', 8, 4, 1, 0x420b3333, (0, 1, 3)),
    b'blast_wave': AbilityDefinition134(5470160, b'blast_wave', 2, 2, 1, 0x4207999a, (0, 1, 3)),
    b'pyroblast': AbilityDefinition134(5470248, b'pyroblast', 0, 2, 0, 0x43bdc000, (0, 1, 2)),
    b'ice_barrier': AbilityDefinition134(5470336, b'ice_barrier', 9, 4, 7, 0x00000000, (0, 1)),
    b'polymorph': AbilityDefinition134(5470424, b'polymorph', 11, 6, 0, 0x42e60000, (0, 3)),
    b'shadow_bolt': AbilityDefinition134(5470512, b'shadow_bolt', 0, 5, 0, 0x42080000, (0, 1, 2)),
    b'corruption': AbilityDefinition134(5470600, b'corruption', 6, 5, 0, 0x427a0000, (0, 1, 4, 2)),
    b'immolate': AbilityDefinition134(5470688, b'immolate', 6, 2, 0, 0x428a0000, (0, 1, 4, 2)),
    b'curse_of_agony': AbilityDefinition134(5470776, b'curse_of_agony', 6, 5, 0, 0x42cf0000, (0, 1, 4, 2)),
    b'rain_of_fire': AbilityDefinition134(5470864, b'rain_of_fire', 3, 2, 0, 0x42533333, (0, 1, 3, 4)),
    b'hellfire': AbilityDefinition134(5470952, b'hellfire', 2, 2, 0, 0x41400000, (0, 1, 3)),
    b'death_coil': AbilityDefinition134(5471040, b'death_coil', 0, 5, 5, 0x42960000, (0, 1, 2)),
    b'searing_pain': AbilityDefinition134(5471128, b'searing_pain', 1, 2, 0, 0x42480000, (0, 1, 2)),
    b'drain_life': AbilityDefinition134(5471216, b'drain_life', 6, 5, 5, 0x42660000, (0, 1, 4, 2)),
    b'fear': AbilityDefinition134(5471304, b'fear', 0, 5, 4, 0x40b00000, (1, 2)),
    b'soul_fire': AbilityDefinition134(5471392, b'soul_fire', 11, 2, 0, 0x44160000, (0, 1, 2)),
    b'demonic_empowerment': AbilityDefinition134(5471480, b'demonic_empowerment', 9, 5, 10, 0x00000000, (1, 4)),
    b'wrath': AbilityDefinition134(5471568, b'wrath', 0, 3, 0, 0x42160000, (0, 1, 2)),
    b'moonfire': AbilityDefinition134(5471656, b'moonfire', 6, 6, 0, 0x428f0000, (0, 1, 4, 2)),
    b'starfire': AbilityDefinition134(5471744, b'starfire', 0, 6, 0, 0x43080000, (0, 1, 2)),
    b'hurricane': AbilityDefinition134(5471832, b'hurricane', 3, 3, 1, 0x42896666, (0, 1, 3, 4)),
    b'insect_swarm': AbilityDefinition134(5471920, b'insect_swarm', 6, 3, 11, 0x428a0000, (0, 1, 4, 2)),
    b'entangling_roots': AbilityDefinition134(5472008, b'entangling_roots', 0, 3, 2, 0x41e40000, (0, 1, 2)),
    b'rejuvenation': AbilityDefinition134(5472096, b'rejuvenation', 9, 3, 6, 0x00000000, (0, 1)),
    b'regrowth': AbilityDefinition134(5472184, b'regrowth', 9, 3, 6, 0x00000000, (0, 1)),
    b'thorns': AbilityDefinition134(5472272, b'thorns', 9, 3, 13, 0x00000000, (0,)),
    b'swipe': AbilityDefinition134(5472360, b'swipe', 2, 0, 0, 0x41ce6666, (0, 1, 3)),
    b'shred': AbilityDefinition134(5472448, b'shred', 5, 0, 0, 0x42d20000, (0, 1)),
    b'faerie_fire': AbilityDefinition134(5472536, b'faerie_fire', 11, 3, 0, 0x43480000, (0, 2, 3)),
    b'perception': AbilityDefinition134(5472624, b'perception', 9, 1, 8, 0x00000000, (1, 4)),
    b'blood_fury': AbilityDefinition134(5472712, b'blood_fury', 9, 0, 8, 0x00000000, (1, 4)),
    b'stoneform': AbilityDefinition134(5472800, b'stoneform', 9, 0, 7, 0x00000000, (0, 1)),
    b'shadowmeld': AbilityDefinition134(5472888, b'shadowmeld', 9, 5, 12, 0x00000000, (1, 4)),
    b'will_of_the_forsaken': AbilityDefinition134(5472976, b'will_of_the_forsaken', 9, 5, 12, 0x00000000, (1, 4)),
    b'war_stomp': AbilityDefinition134(5473064, b'war_stomp', 2, 0, 3, 0x41400000, (0, 1, 3)),
    b'escape_artist': AbilityDefinition134(5473152, b'escape_artist', 2, 6, 2, 0x40c00000, (0, 1, 3)),
    b'berserking': AbilityDefinition134(5473240, b'berserking', 9, 0, 9, 0x00000000, (1, 4)),
    b'penance': AbilityDefinition134(5473328, b'penance', 1, 1, 0, 0x424a0000, (0, 1, 2)),
    b'arcane_power': AbilityDefinition134(5473416, b'arcane_power', 9, 6, 8, 0x00000000, (1, 4)),
}
