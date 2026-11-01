"""Independent0.135.1 new owned-ability initialization, helpers26967/26591.

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
SOURCE_SHA256 = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
TIER_COOLDOWN = (1032805417, 1036831949, 1040522936, 1043207291, 1047233823)
TIER_DAMAGE = (1043878380, 1048576000, 1051595899, 1055622431, 1059481190)


@dataclass(frozen=True)
class AbilityDefinition135:
    pointer: int
    ability_id: bytes
    execution_kind: int
    school: int
    effect_tag: int
    base_damage_bits: int
    kinds: tuple


@dataclass(frozen=True)
class AbilityModifier135:
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
    """Original85719: f32 bias0.49999997 with input sign, then bit truncation."""
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
        if not isinstance(modifier, AbilityModifier135):
            raise TypeError('Need AbilityModifier135 snapshot records')
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
    """Build1072's80B record, then26967, then26591 in original order.

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
class SelectionState135:
    owned: tuple = ()
    candidates: tuple = ()
    phase2587: int = 2
    selection_kind2585: int = 0


@dataclass(frozen=True)
class SelectionResult135:
    state: SelectionState135
    accepted: bool
    owned_index: int | None = None
    pending_effects: tuple = ()


def accept_new_ability_selection(state, index, definitions, *, modifiers=None):
    """1072 entry guards and append only; shared original tail stays pending."""
    if state.phase2587 != 2 or not 0 <= index < len(state.candidates) or state.selection_kind2585 == 255:
        return SelectionResult135(state, False)
    card = state.candidates[index]
    if not isinstance(card, NewAbilityCard):
        raise UnresolvedAbilityEffect('This API accepts the canonical new-ability candidate variant')
    definition = definitions[card.ability_id]
    if definition.ability_id != card.ability_id:
        raise ValueError('Definition string-ID lookup differs')
    record = initialize_ability(definition, tier=card.tier, modifiers=modifiers)
    return SelectionResult135(replace(state, owned=state.owned+(record,)), True, len(state.owned),
        ('1072 spell notification', '1072 shared talent/equipment/notification postprocessing',
         '1512 derived-stat rebuild', '4600 selection completion'))


# Frozen114x88B official0.135.1 declarations; checker re-extracts every field
# from current-source active data. They are never loaded from WASM at runtime.
DEFINITIONS = {
    b'cleave': AbilityDefinition135(5467428, b'cleave', 5, 0, 0, 1111228416, (0, 1, 2)),
    b'whirlwind': AbilityDefinition135(5467516, b'whirlwind', 2, 0, 0, 1111490560, (0, 1, 3)),
    b'thunder_clap': AbilityDefinition135(5467604, b'thunder_clap', 2, 0, 1, 1101529088, (0, 1, 3)),
    b'mortal_strike': AbilityDefinition135(5467692, b'mortal_strike', 5, 0, 0, 1124630528, (0, 1, 2)),
    b'execute': AbilityDefinition135(5467780, b'execute', 7, 0, 0, 1122631680, (0, 1)),
    b'demo_shout': AbilityDefinition135(5467868, b'demo_shout', 2, 0, 11, 1090519040, (1, 3)),
    b'battle_shout': AbilityDefinition135(5467956, b'battle_shout', 9, 0, 8, 0, (1, 4)),
    b'bloodthirst': AbilityDefinition135(5468044, b'bloodthirst', 5, 0, 5, 1118830592, (0, 1, 2)),
    b'rend': AbilityDefinition135(5468132, b'rend', 6, 0, 0, 1117519872, (0, 1, 4, 2)),
    b'shield_slam': AbilityDefinition135(5468220, b'shield_slam', 5, 0, 3, 1125515264, (0, 1, 2)),
    b'bloodrage': AbilityDefinition135(5468308, b'bloodrage', 11, 0, 0, 1125187584, (0, 1, 3)),
    b'consecration': AbilityDefinition135(5468396, b'consecration', 3, 1, 0, 1119879168, (0, 1, 3, 4)),
    b'exorcism': AbilityDefinition135(5468484, b'exorcism', 0, 1, 0, 1124532224, (0, 1, 2)),
    b'hammer_of_wrath': AbilityDefinition135(5468572, b'hammer_of_wrath', 0, 1, 0, 1116012544, (0, 1, 2)),
    b'holy_shock': AbilityDefinition135(5468660, b'holy_shock', 1, 1, 6, 1118240768, (0, 1, 2)),
    b'holy_wrath': AbilityDefinition135(5468748, b'holy_wrath', 2, 1, 0, 1113613926, (0, 1, 3)),
    b'judgement': AbilityDefinition135(5468836, b'judgement', 0, 1, 0, 1128792064, (0, 1, 2)),
    b'hammer_of_justice': AbilityDefinition135(5468924, b'hammer_of_justice', 0, 1, 3, 1113325568, (0, 1, 2)),
    b'holy_light': AbilityDefinition135(5469012, b'holy_light', 9, 1, 6, 0, (0, 1)),
    b'divine_shield': AbilityDefinition135(5469100, b'divine_shield', 9, 1, 12, 0, (1, 4)),
    b'holy_shield': AbilityDefinition135(5469188, b'holy_shield', 9, 1, 13, 0, (0, 1, 4)),
    b'redemption': AbilityDefinition135(5469276, b'redemption', 11, 1, 0, 1112539136, (0, 1, 3)),
    b'auto_shot': AbilityDefinition135(5469364, b'auto_shot', 0, 0, 0, 1107951616, (0, 1, 2)),
    b'arcane_shot': AbilityDefinition135(5469452, b'arcane_shot', 0, 6, 0, 1116274688, (0, 1, 2)),
    b'multi_shot': AbilityDefinition135(5469540, b'multi_shot', 0, 0, 0, 1106247680, (0, 1, 2)),
    b'serpent_sting': AbilityDefinition135(5469628, b'serpent_sting', 6, 3, 0, 1113849856, (0, 1, 4, 2)),
    b'volley': AbilityDefinition135(5469716, b'volley', 3, 6, 0, 1112434278, (0, 1, 3, 4)),
    b'explosive_trap': AbilityDefinition135(5469804, b'explosive_trap', 2, 2, 0, 1108030259, (0, 1, 3)),
    b'concussive_shot': AbilityDefinition135(5469892, b'concussive_shot', 0, 6, 1, 1099431936, (0, 1, 2)),
    b'aimed_shot': AbilityDefinition135(5469980, b'aimed_shot', 0, 0, 0, 1135214592, (0, 1, 2)),
    b'immolation_trap': AbilityDefinition135(5470068, b'immolation_trap', 3, 2, 0, 1114636288, (0, 1, 3, 4)),
    b'frost_trap': AbilityDefinition135(5470156, b'frost_trap', 3, 4, 2, 1099169792, (0, 1, 3, 4)),
    b'hunters_mark': AbilityDefinition135(5470244, b'hunters_mark', 11, 6, 0, 1132068864, (0, 1, 3)),
    b'sinister_strike': AbilityDefinition135(5470332, b'sinister_strike', 5, 0, 0, 1108082688, (0, 1, 2)),
    b'eviscerate': AbilityDefinition135(5470420, b'eviscerate', 7, 0, 0, 1119223808, (0, 1)),
    b'blade_flurry': AbilityDefinition135(5470508, b'blade_flurry', 2, 0, 0, 1103101952, (0, 1, 3)),
    b'rupture': AbilityDefinition135(5470596, b'rupture', 6, 0, 0, 1114898432, (0, 1, 4, 2)),
    b'kidney_shot': AbilityDefinition135(5470684, b'kidney_shot', 5, 0, 3, 1103626240, (0, 1, 2)),
    b'gouge': AbilityDefinition135(5470772, b'gouge', 5, 0, 3, 1103888384, (0, 1, 2)),
    b'ghostly_strike': AbilityDefinition135(5470860, b'ghostly_strike', 5, 0, 7, 1110966272, (0, 1, 2)),
    b'adrenaline_rush': AbilityDefinition135(5470948, b'adrenaline_rush', 9, 0, 9, 0, (1, 4)),
    b'backstab': AbilityDefinition135(5471036, b'backstab', 7, 0, 0, 1113456640, (0, 1)),
    b'slice_and_dice': AbilityDefinition135(5471124, b'slice_and_dice', 9, 0, 8, 0, (1, 4)),
    b'seal_fate': AbilityDefinition135(5471212, b'seal_fate', 11, 0, 0, 1124204544, (0, 1, 2)),
    b'smite': AbilityDefinition135(5471300, b'smite', 0, 1, 0, 1109786624, (0, 1, 2)),
    b'sw_pain': AbilityDefinition135(5471388, b'sw_pain', 6, 5, 0, 1116733440, (0, 1, 4, 2)),
    b'mind_blast': AbilityDefinition135(5471476, b'mind_blast', 0, 5, 0, 1119485952, (0, 1, 2)),
    b'holy_nova': AbilityDefinition135(5471564, b'holy_nova', 2, 1, 6, 1104832102, (0, 1, 3)),
    b'pw_shield': AbilityDefinition135(5471652, b'pw_shield', 9, 1, 7, 0, (0, 1)),
    b'renew': AbilityDefinition135(5471740, b'renew', 9, 1, 6, 0, (0, 1)),
    b'holy_fire': AbilityDefinition135(5471828, b'holy_fire', 0, 1, 0, 1126170624, (0, 1, 2)),
    b'mind_flay': AbilityDefinition135(5471916, b'mind_flay', 8, 5, 1, 1112748851, (0, 1, 3)),
    b'psychic_scream': AbilityDefinition135(5472004, b'psychic_scream', 2, 5, 4, 1093140480, (1, 3)),
    b'devouring_plague': AbilityDefinition135(5472092, b'devouring_plague', 6, 5, 5, 1121255424, (0, 1, 4, 2)),
    b'lightwell': AbilityDefinition135(5472180, b'lightwell', 11, 1, 0, 1117782016, (0, 1, 4, 2)),
    b'lightning_bolt': AbilityDefinition135(5472268, b'lightning_bolt', 0, 3, 0, 1108475904, (0, 1, 2)),
    b'chain_lightning': AbilityDefinition135(5472356, b'chain_lightning', 4, 3, 0, 1109262336, (0, 1, 2)),
    b'earth_shock': AbilityDefinition135(5472444, b'earth_shock', 0, 3, 0, 1119551488, (0, 1, 2)),
    b'flame_shock': AbilityDefinition135(5472532, b'flame_shock', 6, 2, 0, 1118109696, (0, 1, 4, 2)),
    b'frost_shock': AbilityDefinition135(5472620, b'frost_shock', 0, 4, 1, 1114112000, (0, 1, 2)),
    b'lightning_shield': AbilityDefinition135(5472708, b'lightning_shield', 9, 3, 13, 0, (0,)),
    b'magma_totem': AbilityDefinition135(5472796, b'magma_totem', 10, 2, 0, 1103101952, (0, 1, 3, 4)),
    b'searing_totem': AbilityDefinition135(5472884, b'searing_totem', 10, 2, 0, 1107820544, (0, 1, 4, 2)),
    b'fire_nova': AbilityDefinition135(5472972, b'fire_nova', 2, 2, 0, 1109917696, (0, 1, 3)),
    b'healing_wave': AbilityDefinition135(5473060, b'healing_wave', 9, 3, 6, 0, (0, 1)),
    b'stormstrike': AbilityDefinition135(5473148, b'stormstrike', 5, 3, 0, 1135345664, (0, 1, 2)),
    b'rockbiter': AbilityDefinition135(5473236, b'rockbiter', 5, 3, 0, 1124335616, (0, 1, 2)),
    b'fireball': AbilityDefinition135(5473324, b'fireball', 0, 2, 0, 1112145920, (0, 1, 2)),
    b'frostbolt': AbilityDefinition135(5473412, b'frostbolt', 0, 4, 1, 1108475904, (0, 1, 2)),
    b'arcane_missiles': AbilityDefinition135(5473500, b'arcane_missiles', 1, 6, 0, 1103731098, (0, 1, 2)),
    b'frost_nova': AbilityDefinition135(5473588, b'frost_nova', 2, 4, 2, 1095027917, (0, 1, 3)),
    b'arcane_explosion': AbilityDefinition135(5473676, b'arcane_explosion', 2, 6, 0, 1103731098, (0, 1, 3)),
    b'blizzard': AbilityDefinition135(5473764, b'blizzard', 3, 4, 1, 1114872218, (0, 1, 3, 4)),
    b'flamestrike': AbilityDefinition135(5473852, b'flamestrike', 3, 2, 0, 1112827494, (0, 1, 3, 4)),
    b'fire_blast': AbilityDefinition135(5473940, b'fire_blast', 1, 2, 0, 1116209152, (0, 1, 2)),
    b'cone_of_cold': AbilityDefinition135(5474028, b'cone_of_cold', 8, 4, 1, 1108030259, (0, 1, 3)),
    b'blast_wave': AbilityDefinition135(5474116, b'blast_wave', 2, 2, 1, 1107794330, (0, 1, 3)),
    b'pyroblast': AbilityDefinition135(5474204, b'pyroblast', 0, 2, 0, 1136508928, (0, 1, 2)),
    b'ice_barrier': AbilityDefinition135(5474292, b'ice_barrier', 9, 4, 7, 0, (0, 1)),
    b'polymorph': AbilityDefinition135(5474380, b'polymorph', 11, 6, 0, 1122369536, (0, 3)),
    b'shadow_bolt': AbilityDefinition135(5474468, b'shadow_bolt', 0, 5, 0, 1107820544, (0, 1, 2)),
    b'corruption': AbilityDefinition135(5474556, b'corruption', 6, 5, 0, 1115291648, (0, 1, 4, 2)),
    b'immolate': AbilityDefinition135(5474644, b'immolate', 6, 2, 0, 1116340224, (0, 1, 4, 2)),
    b'curse_of_agony': AbilityDefinition135(5474732, b'curse_of_agony', 6, 5, 0, 1120862208, (0, 1, 4, 2)),
    b'rain_of_fire': AbilityDefinition135(5474820, b'rain_of_fire', 3, 2, 0, 1112748851, (0, 1, 3, 4)),
    b'hellfire': AbilityDefinition135(5474908, b'hellfire', 2, 2, 0, 1094713344, (0, 1, 3)),
    b'death_coil': AbilityDefinition135(5474996, b'death_coil', 0, 5, 5, 1117126656, (0, 1, 2)),
    b'searing_pain': AbilityDefinition135(5475084, b'searing_pain', 1, 2, 0, 1112014848, (0, 1, 2)),
    b'drain_life': AbilityDefinition135(5475172, b'drain_life', 6, 5, 5, 1113980928, (0, 1, 4, 2)),
    b'fear': AbilityDefinition135(5475260, b'fear', 0, 5, 4, 1085276160, (1, 2)),
    b'soul_fire': AbilityDefinition135(5475348, b'soul_fire', 11, 2, 0, 1142292480, (0, 1, 2)),
    b'demonic_empowerment': AbilityDefinition135(5475436, b'demonic_empowerment', 9, 5, 10, 0, (1, 4)),
    b'wrath': AbilityDefinition135(5475524, b'wrath', 0, 3, 0, 1108738048, (0, 1, 2)),
    b'moonfire': AbilityDefinition135(5475612, b'moonfire', 6, 6, 0, 1116667904, (0, 1, 4, 2)),
    b'starfire': AbilityDefinition135(5475700, b'starfire', 0, 6, 0, 1124597760, (0, 1, 2)),
    b'hurricane': AbilityDefinition135(5475788, b'hurricane', 3, 3, 1, 1116300902, (0, 1, 3, 4)),
    b'insect_swarm': AbilityDefinition135(5475876, b'insect_swarm', 6, 3, 11, 1116340224, (0, 1, 4, 2)),
    b'entangling_roots': AbilityDefinition135(5475964, b'entangling_roots', 0, 3, 2, 1105461248, (0, 1, 2)),
    b'rejuvenation': AbilityDefinition135(5476052, b'rejuvenation', 9, 3, 6, 0, (0, 1)),
    b'regrowth': AbilityDefinition135(5476140, b'regrowth', 9, 3, 6, 0, (0, 1)),
    b'thorns': AbilityDefinition135(5476228, b'thorns', 9, 3, 13, 0, (0,)),
    b'swipe': AbilityDefinition135(5476316, b'swipe', 2, 0, 0, 1104045670, (0, 1, 3)),
    b'shred': AbilityDefinition135(5476404, b'shred', 5, 0, 0, 1121058816, (0, 1)),
    b'faerie_fire': AbilityDefinition135(5476492, b'faerie_fire', 11, 3, 0, 1128792064, (0, 2, 3)),
    b'perception': AbilityDefinition135(5476580, b'perception', 9, 1, 8, 0, (1, 4)),
    b'blood_fury': AbilityDefinition135(5476668, b'blood_fury', 9, 0, 8, 0, (1, 4)),
    b'stoneform': AbilityDefinition135(5476756, b'stoneform', 9, 0, 7, 0, (0, 1)),
    b'shadowmeld': AbilityDefinition135(5476844, b'shadowmeld', 9, 5, 12, 0, (1, 4)),
    b'will_of_the_forsaken': AbilityDefinition135(5476932, b'will_of_the_forsaken', 9, 5, 12, 0, (1, 4)),
    b'war_stomp': AbilityDefinition135(5477020, b'war_stomp', 2, 0, 3, 1094713344, (0, 1, 3)),
    b'escape_artist': AbilityDefinition135(5477108, b'escape_artist', 2, 6, 2, 1086324736, (0, 1, 3)),
    b'berserking': AbilityDefinition135(5477196, b'berserking', 9, 0, 9, 0, (1, 4)),
    b'penance': AbilityDefinition135(5477284, b'penance', 1, 1, 0, 1112145920, (0, 1, 2)),
    b'arcane_power': AbilityDefinition135(5477372, b'arcane_power', 9, 6, 8, 0, (1, 4)),
}
