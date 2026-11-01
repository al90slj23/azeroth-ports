"""Official 0.135.1 / 0898d5e3 kind0 candidate metadata, static finite domain.

New2159/1480/29737/27376/32653 are the evidence. This module never loads or
executes WASM. It returns selection-relevant data and RNG state, not allocated
80B UI strings, world notifications, or a claim of full choice integration.
Kinds1/2 raise PendingCandidates135 before any input state is changed. Special
summon state and derived cooldown are supplied as explicit snapshots.
"""
from dataclasses import dataclass

from . import binary32 as f
from .ability_state import AbilityRecord
from .rng import next_u32_words, uniform_range_bits
from .upgrade_values import UpgradeState, upgrade_value_bits

SOURCE_SHA256 = 'c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'
WAT_SHA256 = '15bccec81235752573d903d098911612d8add22cc51956d03afb8fb17382a7f2'


class PendingCandidates135(NotImplementedError):
    """This snapshot reaches a candidate rule outside the frozen finite domain."""


@dataclass(frozen=True)
class Definition:
    pointer: int
    kinds: tuple
    execution: int
    damage_bits: int
    radius_bits: int
    count: int
    effect_tag: int
    cooldown_bits: int
    duration_bits: int


# Frozen new-version declaration data. Numbers are raw u32 words, not host floats.
DEFINITIONS = {
    'cleave': Definition(5467428, (0, 1, 2), 5, 1111228416, 0, 3, 0, 1069547520, 0),
    'whirlwind': Definition(5467516, (0, 1, 3), 2, 1111490560, 1090519040, 0, 0, 1083179008, 0),
    'thunder_clap': Definition(5467604, (0, 1, 3), 2, 1101529088, 1092616192, 0, 1, 1084227584, 0),
    'mortal_strike': Definition(5467692, (0, 1, 2), 5, 1124630528, 0, 1, 0, 1077936128, 0),
    'execute': Definition(5467780, (0, 1), 7, 1122631680, 0, 1, 0, 1075838976, 0),
    'demo_shout': Definition(5467868, (1, 3), 2, 1090519040, 1096810496, 0, 11, 1092616192, 0),
    'battle_shout': Definition(5467956, (1, 4), 9, 0, 0, 0, 8, 1098907648, 1090519040),
    'bloodthirst': Definition(5468044, (0, 1, 2), 5, 1118830592, 0, 1, 5, 1082130432, 0),
    'rend': Definition(5468132, (0, 1, 4, 2), 6, 1117519872, 0, 3, 0, 1077936128, 1084227584),
    'shield_slam': Definition(5468220, (0, 1, 2), 5, 1125515264, 0, 2, 3, 1086324736, 0),
    'bloodrage': Definition(5468308, (0, 1, 3), 11, 1125187584, 1091567616, 0, 0, 1088736461, 0),
    'consecration': Definition(5468396, (0, 1, 3, 4), 3, 1119879168, 1090519040, 0, 0, 1090519040, 1090519040),
    'exorcism': Definition(5468484, (0, 1, 2), 0, 1124532224, 0, 1, 0, 1080033280, 0),
    'hammer_of_wrath': Definition(5468572, (0, 1, 2), 0, 1116012544, 0, 1, 0, 1070386381, 0),
    'holy_shock': Definition(5468660, (0, 1, 2), 1, 1118240768, 0, 2, 6, 1077936128, 0),
    'holy_wrath': Definition(5468748, (0, 1, 3), 2, 1113613926, 1094713344, 0, 0, 1088421888, 0),
    'judgement': Definition(5468836, (0, 1, 2), 0, 1128792064, 0, 1, 0, 1086324736, 0),
    'hammer_of_justice': Definition(5468924, (0, 1, 2), 0, 1113325568, 0, 2, 3, 1088421888, 0),
    'holy_light': Definition(5469012, (0, 1), 9, 0, 0, 0, 6, 1094713344, 0),
    'divine_shield': Definition(5469100, (1, 4), 9, 0, 0, 0, 12, 1107296256, 1082130432),
    'holy_shield': Definition(5469188, (0, 1, 4), 9, 0, 0, 0, 13, 1096810496, 1092616192),
    'redemption': Definition(5469276, (0, 1, 3), 11, 1112539136, 1090519040, 0, 0, 1052266988, 0),
    'auto_shot': Definition(5469364, (0, 1, 2), 0, 1107951616, 0, 2, 0, 1066192077, 0),
    'arcane_shot': Definition(5469452, (0, 1, 2), 0, 1116274688, 0, 1, 0, 1075838976, 0),
    'multi_shot': Definition(5469540, (0, 1, 2), 0, 1106247680, 0, 3, 0, 1070386381, 0),
    'serpent_sting': Definition(5469628, (0, 1, 4, 2), 6, 1113849856, 0, 2, 0, 1075838976, 1084227584),
    'volley': Definition(5469716, (0, 1, 3, 4), 3, 1112434278, 1090519040, 0, 0, 1090519040, 1086324736),
    'explosive_trap': Definition(5469804, (0, 1, 3), 2, 1108030259, 1091567616, 0, 0, 1086324736, 0),
    'concussive_shot': Definition(5469892, (0, 1, 2), 0, 1099431936, 0, 2, 1, 1082130432, 0),
    'aimed_shot': Definition(5469980, (0, 1, 2), 0, 1135214592, 0, 1, 0, 1083179008, 0),
    'immolation_trap': Definition(5470068, (0, 1, 3, 4), 3, 1114636288, 1088421888, 0, 0, 1091567616, 1090519040),
    'frost_trap': Definition(5470156, (0, 1, 3, 4), 3, 1099169792, 1092616192, 0, 2, 1092616192, 1086324736),
    'hunters_mark': Definition(5470244, (0, 1, 3), 11, 1132068864, 1090519040, 0, 0, 1068960317, 0),
    'sinister_strike': Definition(5470332, (0, 1, 2), 5, 1108082688, 0, 2, 0, 1065353216, 0),
    'eviscerate': Definition(5470420, (0, 1), 7, 1119223808, 0, 2, 0, 1077936128, 0),
    'blade_flurry': Definition(5470508, (0, 1, 3), 2, 1103101952, 1088421888, 0, 0, 1075838976, 0),
    'rupture': Definition(5470596, (0, 1, 4, 2), 6, 1114898432, 0, 2, 0, 1080033280, 1082130432),
    'kidney_shot': Definition(5470684, (0, 1, 2), 5, 1103626240, 0, 2, 3, 1086324736, 0),
    'gouge': Definition(5470772, (0, 1, 2), 5, 1103888384, 0, 3, 3, 1084227584, 0),
    'ghostly_strike': Definition(5470860, (0, 1, 2), 5, 1110966272, 0, 1, 7, 1082130432, 0),
    'adrenaline_rush': Definition(5470948, (1, 4), 9, 0, 0, 0, 9, 1101004800, 1090519040),
    'backstab': Definition(5471036, (0, 1), 7, 1113456640, 0, 2, 0, 1072064102, 0),
    'slice_and_dice': Definition(5471124, (1, 4), 9, 0, 0, 0, 8, 1097859072, 1091567616),
    'seal_fate': Definition(5471212, (0, 1, 2), 11, 1124204544, 0, 1, 0, 1071980216, 0),
    'smite': Definition(5471300, (0, 1, 2), 0, 1109786624, 0, 1, 0, 1067030938, 0),
    'sw_pain': Definition(5471388, (0, 1, 4, 2), 6, 1116733440, 0, 2, 0, 1070386381, 1086324736),
    'mind_blast': Definition(5471476, (0, 1, 2), 0, 1119485952, 0, 1, 0, 1082130432, 0),
    'holy_nova': Definition(5471564, (0, 1, 3), 2, 1104832102, 1092616192, 0, 6, 1082130432, 0),
    'pw_shield': Definition(5471652, (0, 1), 9, 0, 0, 0, 7, 1094713344, 1094713344),
    'renew': Definition(5471740, (0, 1), 9, 0, 0, 0, 6, 1092616192, 1092616192),
    'holy_fire': Definition(5471828, (0, 1, 2), 0, 1126170624, 0, 1, 0, 1084227584, 0),
    'mind_flay': Definition(5471916, (0, 1, 3), 8, 1112748851, 0, 0, 1, 1075838976, 0),
    'psychic_scream': Definition(5472004, (1, 3), 2, 1093140480, 1092616192, 0, 4, 1094713344, 0),
    'devouring_plague': Definition(5472092, (0, 1, 4, 2), 6, 1121255424, 0, 3, 5, 1086324736, 1086324736),
    'lightwell': Definition(5472180, (0, 1, 4, 2), 11, 1117782016, 0, 1, 0, 1097125069, 1088736461),
    'lightning_bolt': Definition(5472268, (0, 1, 2), 0, 1108475904, 0, 2, 0, 1068708659, 0),
    'chain_lightning': Definition(5472356, (0, 1, 2), 4, 1109262336, 1094713344, 5, 0, 1075419546, 0),
    'earth_shock': Definition(5472444, (0, 1, 2), 0, 1119551488, 0, 1, 0, 1077936128, 0),
    'flame_shock': Definition(5472532, (0, 1, 4, 2), 6, 1118109696, 0, 2, 0, 1077936128, 1086324736),
    'frost_shock': Definition(5472620, (0, 1, 2), 0, 1114112000, 0, 2, 1, 1080033280, 0),
    'lightning_shield': Definition(5472708, (0,), 9, 0, 0, 0, 13, 1097859072, 1097859072),
    'magma_totem': Definition(5472796, (0, 1, 3, 4), 10, 1103101952, 1092616192, 0, 0, 1094713344, 1094713344),
    'searing_totem': Definition(5472884, (0, 1, 4, 2), 10, 1107820544, 0, 1, 0, 1092616192, 1097859072),
    'fire_nova': Definition(5472972, (0, 1, 3), 2, 1109917696, 1094713344, 0, 0, 1084227584, 0),
    'healing_wave': Definition(5473060, (0, 1), 9, 0, 0, 0, 6, 1094713344, 0),
    'stormstrike': Definition(5473148, (0, 1, 2), 5, 1135345664, 0, 1, 0, 1086474533, 0),
    'rockbiter': Definition(5473236, (0, 1, 2), 5, 1124335616, 0, 2, 0, 1068349148, 0),
    'fireball': Definition(5473324, (0, 1, 2), 0, 1112145920, 0, 1, 0, 1067869798, 0),
    'frostbolt': Definition(5473412, (0, 1, 2), 0, 1108475904, 0, 1, 1, 1069547520, 0),
    'arcane_missiles': Definition(5473500, (0, 1, 2), 1, 1103731098, 0, 4, 0, 1072064102, 0),
    'frost_nova': Definition(5473588, (0, 1, 3), 2, 1095027917, 1092616192, 0, 2, 1088421888, 0),
    'arcane_explosion': Definition(5473676, (0, 1, 3), 2, 1103731098, 1091567616, 0, 0, 1075838976, 0),
    'blizzard': Definition(5473764, (0, 1, 3, 4), 3, 1114872218, 1091567616, 0, 1, 1090519040, 1088421888),
    'flamestrike': Definition(5473852, (0, 1, 3, 4), 3, 1112827494, 1090519040, 0, 0, 1088421888, 1086324736),
    'fire_blast': Definition(5473940, (0, 1, 2), 1, 1116209152, 0, 1, 0, 1077936128, 0),
    'cone_of_cold': Definition(5474028, (0, 1, 3), 8, 1108030259, 0, 0, 1, 1082130432, 0),
    'blast_wave': Definition(5474116, (0, 1, 3), 2, 1107794330, 1092616192, 0, 1, 1090519040, 0),
    'pyroblast': Definition(5474204, (0, 1, 2), 0, 1136508928, 0, 1, 0, 1088421888, 0),
    'ice_barrier': Definition(5474292, (0, 1), 9, 0, 0, 0, 7, 1097859072, 1097859072),
    'polymorph': Definition(5474380, (0, 3), 11, 1122369536, 1088421888, 0, 0, 1074341609, 0),
    'shadow_bolt': Definition(5474468, (0, 1, 2), 0, 1107820544, 0, 1, 0, 1068708659, 0),
    'corruption': Definition(5474556, (0, 1, 4, 2), 6, 1115291648, 0, 2, 0, 1068708659, 1086324736),
    'immolate': Definition(5474644, (0, 1, 4, 2), 6, 1116340224, 0, 1, 0, 1075838976, 1084227584),
    'curse_of_agony': Definition(5474732, (0, 1, 4, 2), 6, 1120862208, 0, 3, 0, 1077936128, 1091567616),
    'rain_of_fire': Definition(5474820, (0, 1, 3, 4), 3, 1112748851, 1090519040, 0, 0, 1090519040, 1090519040),
    'hellfire': Definition(5474908, (0, 1, 3), 2, 1094713344, 1088421888, 0, 0, 1069547520, 0),
    'death_coil': Definition(5474996, (0, 1, 2), 0, 1117126656, 0, 1, 5, 1086324736, 0),
    'searing_pain': Definition(5475084, (0, 1, 2), 1, 1112014848, 0, 1, 0, 1070386381, 0),
    'drain_life': Definition(5475172, (0, 1, 4, 2), 6, 1113980928, 0, 1, 5, 1082130432, 1077936128),
    'fear': Definition(5475260, (1, 2), 0, 1085276160, 0, 3, 4, 1086324736, 0),
    'soul_fire': Definition(5475348, (0, 1, 2), 11, 1142292480, 0, 1, 0, 1082738606, 0),
    'demonic_empowerment': Definition(5475436, (1, 4), 9, 0, 0, 0, 10, 1098907648, 1090519040),
    'wrath': Definition(5475524, (0, 1, 2), 0, 1108738048, 0, 2, 0, 1067030938, 0),
    'moonfire': Definition(5475612, (0, 1, 4, 2), 6, 1116667904, 0, 3, 0, 1072064102, 1084227584),
    'starfire': Definition(5475700, (0, 1, 2), 0, 1124597760, 0, 1, 0, 1083179008, 0),
    'hurricane': Definition(5475788, (0, 1, 3, 4), 3, 1116300902, 1092616192, 0, 1, 1091567616, 1090519040),
    'insect_swarm': Definition(5475876, (0, 1, 4, 2), 6, 1116340224, 0, 3, 11, 1075838976, 1086324736),
    'entangling_roots': Definition(5475964, (0, 1, 2), 0, 1105461248, 0, 3, 2, 1084227584, 0),
    'rejuvenation': Definition(5476052, (0, 1), 9, 0, 0, 0, 6, 1090519040, 1094713344),
    'regrowth': Definition(5476140, (0, 1), 9, 0, 0, 0, 6, 1096810496, 0),
    'thorns': Definition(5476228, (0,), 9, 0, 0, 0, 13, 1101004800, 1101004800),
    'swipe': Definition(5476316, (0, 1, 3), 2, 1104045670, 1088421888, 0, 0, 1077936128, 0),
    'shred': Definition(5476404, (0, 1), 5, 1121058816, 0, 1, 0, 1073741824, 0),
    'faerie_fire': Definition(5476492, (0, 2, 3), 11, 1128792064, 1090519040, 1, 0, 1065353216, 0),
    'perception': Definition(5476580, (1, 4), 9, 0, 0, 0, 8, 1106247680, 1092616192),
    'blood_fury': Definition(5476668, (1, 4), 9, 0, 0, 0, 8, 1109393408, 1094713344),
    'stoneform': Definition(5476756, (0, 1), 9, 0, 0, 0, 7, 1106247680, 1090519040),
    'shadowmeld': Definition(5476844, (1, 4), 9, 0, 0, 0, 12, 1117126656, 1077936128),
    'will_of_the_forsaken': Definition(5476932, (1, 4), 9, 0, 0, 0, 12, 1114636288, 1082130432),
    'war_stomp': Definition(5477020, (0, 1, 3), 2, 1094713344, 1090519040, 0, 3, 1097859072, 0),
    'escape_artist': Definition(5477108, (0, 1, 3), 2, 1086324736, 1090519040, 0, 2, 1101004800, 0),
    'berserking': Definition(5477196, (1, 4), 9, 0, 0, 0, 9, 1108082688, 1092616192),
    'penance': Definition(5477284, (0, 1, 2), 1, 1112145920, 0, 3, 0, 1074580685, 0),
    'arcane_power': Definition(5477372, (1, 4), 9, 0, 0, 0, 8, 1106247680, 1094713344),
}

CLASS_KITS = {
    'warrior': ('cleave', 'whirlwind', 'thunder_clap', 'mortal_strike', 'execute', 'demo_shout', 'battle_shout', 'bloodthirst', 'rend', 'shield_slam', 'bloodrage'),
    'paladin': ('consecration', 'exorcism', 'hammer_of_wrath', 'holy_shock', 'holy_wrath', 'judgement', 'hammer_of_justice', 'holy_light', 'divine_shield', 'holy_shield', 'redemption'),
    'hunter': ('auto_shot', 'arcane_shot', 'multi_shot', 'serpent_sting', 'volley', 'explosive_trap', 'concussive_shot', 'aimed_shot', 'immolation_trap', 'frost_trap', 'hunters_mark'),
    'rogue': ('sinister_strike', 'eviscerate', 'blade_flurry', 'rupture', 'kidney_shot', 'gouge', 'ghostly_strike', 'adrenaline_rush', 'backstab', 'slice_and_dice', 'seal_fate'),
    'priest': ('smite', 'sw_pain', 'mind_blast', 'holy_nova', 'pw_shield', 'renew', 'holy_fire', 'mind_flay', 'psychic_scream', 'devouring_plague', 'lightwell'),
    'shaman': ('lightning_bolt', 'chain_lightning', 'earth_shock', 'flame_shock', 'frost_shock', 'lightning_shield', 'magma_totem', 'searing_totem', 'fire_nova', 'healing_wave', 'stormstrike'),
    'mage': ('fireball', 'frostbolt', 'arcane_missiles', 'frost_nova', 'arcane_explosion', 'blizzard', 'flamestrike', 'fire_blast', 'cone_of_cold', 'blast_wave', 'pyroblast', 'ice_barrier', 'polymorph'),
    'warlock': ('shadow_bolt', 'corruption', 'immolate', 'curse_of_agony', 'rain_of_fire', 'hellfire', 'death_coil', 'searing_pain', 'drain_life', 'fear', 'soul_fire', 'demonic_empowerment'),
    'druid': ('wrath', 'moonfire', 'starfire', 'hurricane', 'insect_swarm', 'entangling_roots', 'rejuvenation', 'regrowth', 'thorns', 'swipe', 'faerie_fire', 'shred'),
}

CLASS_BYTE = {2: 'paladin', 3: 'hunter', 4: 'rogue', 5: 'priest',
              7: 'shaman', 8: 'mage', 9: 'warlock', 11: 'druid'}


@dataclass(frozen=True)
class Owned:
    ability_id: str
    record: AbilityRecord


@dataclass(frozen=True)
class Candidate:
    variant: str
    tier: int = 0
    ability_id: str = ''
    owned_index: int = 0
    kinds: tuple = ()
    gold: int = 0


@dataclass(frozen=True)
class CandidateResult:
    candidates: tuple
    rng_words: tuple
    rng_draws: int
    pool: tuple
    kind: int = 0
    ui_payload_pending: bool = True


@dataclass(frozen=True)
class Effect:
    kind: int
    value_bits: int


@dataclass(frozen=True)
class Summon:
    tag: int
    state41: int = 0


def demonic_empowerment_available(effects, summons):
    """New2159's special predicate, using only fields actually read there.

    Effects are G+2020/2024 8B records (kind byte0/value f32+4). Summons are
    G+2044/2048 36B records; tag42 reads u8+41 from the object at record+4.
    """
    total = 0x80000000
    for effect in effects:
        if effect.kind == 32:
            total = f.add(total, effect.value_bits)
    empowered = f.to_float(total) > 0
    for summon in summons:
        if summon.tag in (46, 47) or (summon.tag == 45 and not empowered):
            return True
        if summon.tag == 42 and summon.state41 > (4 if empowered else 0):
            return True
    return False


def eligible_kinds(owned, tier, cooldown_bits=0x3f800000):
    """Collect29736/27375, preserving the definition's byte-list order.

    cooldown_bits is G.f32[1368], the effective stats.f32+8 used by interval
    saturation. All114 pinned definitions have execution bytes in0..11.
    """
    definition = DEFINITIONS[owned.ability_id]
    execution = definition.execution
    record = owned.record
    state = UpgradeState(record.counts, record.cooldown_bits, record.extra_targets,
                         record.area_bits, record.duration_bits, execution,
                         owned.ability_id.encode('ascii'))
    result = []
    tag = definition.effect_tag
    interval_tag = tag in (8, 9, 10, 13)

    def duration():
        return f.mul(f.mul(f.mul(definition.duration_bits, 0x3fb33333),
                           record.duration_bits), record.additional_duration_bits)

    def interval():
        return f.mul(f.mul(f.mul(f.mul(definition.cooldown_bits, 0x3fb33333),
                                 record.cooldown_bits), record.additional_cooldown_bits),
                     cooldown_bits)

    def floor_interval():
        if owned.ability_id == 'hellfire':
            return 0x3f000000
        if owned.ability_id == 'divine_shield':
            value = duration()
            value = value if f.to_float(value) < 6 else 0x40c00000
            return f.sub(0x41200000, value)
        return 0x3e800000

    def effective_interval():
        value, floor = interval(), floor_interval()
        return value if f.to_float(value) > f.to_float(floor) else floor

    for kind in definition.kinds:
        if execution == 11:
            structural = kind != 2 or definition.count != 0
        elif execution == 9:
            if kind == 0:
                structural = bool((8384 >> ((tag & 0xffff) & 31)) & 1)
            elif kind == 1:
                structural = not interval_tag or not (
                    f.to_float(definition.duration_bits) >= f.to_float(definition.cooldown_bits))
            elif kind == 4:
                structural = (f.to_float(definition.duration_bits) > 0 and (tag & 14) != 6 and
                              (not interval_tag or not (
                                  f.to_float(definition.duration_bits) >= f.to_float(definition.cooldown_bits))))
            else:
                structural = False
        elif kind == 0:
            structural = f.to_float(definition.damage_bits) > 0
        elif kind == 1:
            structural = True
        elif kind == 2:
            structural = definition.count != 0 and (
                execution in (0, 1, 4, 5, 6, 7) or
                (execution not in (2, 3, 8, 9) and f.to_float(definition.radius_bits) <= 0))
            structural = structural and tier != 0
        elif kind == 3:
            structural = execution in (2, 3, 4, 8) or (
                execution == 10 and f.to_float(definition.radius_bits) > 0)
        elif kind == 4:
            structural = execution in (3, 6, 10)
        else:
            raise PendingCandidates135('Unknown declared upgrade kind')
        if not structural:
            continue
        if kind in (1, 4) and execution == 9 and interval_tag:
            value = duration()
            if owned.ability_id == 'divine_shield':
                value = value if f.to_float(value) < 6 else 0x40c00000
            if f.to_float(value) >= f.to_float(effective_interval()):
                continue
        if kind == 1 and execution == 11:
            if owned.ability_id == 'faerie_fire':
                continue
            if owned.ability_id == 'redemption':
                numerator = f.mul(f.mul(definition.cooldown_bits, 0x3dcccccd), 0x3fb33333)
                value = interval()
                value = value if f.to_float(value) > 0.25 else 0x3e800000
                ratio = f.div(numerator, value)
                factor = ratio if f.to_float(ratio) < f.to_float(0x3e4ccccd) else 0x3e4ccccd
                if not f.to_float(f.mul(record.field76_bits, factor)) < f.to_float(0x3e4ac083):
                    continue
            else:
                floor = {'bloodrage': 0x41000000, 'seal_fate': 0x40000000,
                         'soul_fire': 0x40400000, 'lightwell': 0x40c00000,
                         'polymorph': 0x40400000, 'hunters_mark': 0x40000000}.get(owned.ability_id, 0)
                if not f.to_float(effective_interval()) > f.to_float(f.mul(floor, 0x3f8147ae)):
                    continue
        if kind == 2 and tier == 0:
            continue
        if structural and f.to_float(upgrade_value_bits(kind, tier, state)) >= f.to_float(0x3ba3d70a):
            result.append(kind)
    return tuple(result)


def tier_weights(level, luck_bits):
    """Ordered f32 weights [60,25*x,10*x^2,4*x^3,x^4] in new2159."""
    step = f.mul(f.from_u32(level), 0x3c23d70a)
    step = step if f.to_float(step) < f.to_float(0x3e99999a) else 0x3e99999a
    factor = f.add(f.add(luck_bits, 0x3f800000), step)
    square = f.mul(factor, factor)
    fourth = f.mul(square, square)
    third4 = f.mul(f.mul(factor, square), 0x40800000)
    return (0x42700000, f.mul(factor, 0x41c80000),
            f.mul(square, 0x41200000), third4, fourth)


def generate_kind0_metadata(*, rng_words, class_byte=1, owned=(), level=1,
                            luck_bits=0, cooldown_bits=0x3f800000, flag275=0, flag2573=0,
                            blocked_ids=(), banished_keys=(), effects=(),
                            summons=(), kind=0,
                            max_draws=100000):
    """Reproduce kind0 selection data and random consumption in a finite domain.

    blocked_ids is G+2080/2084 (8B borrowed IDs). banished_keys is G+2092/2096
    (12B strings): plain ability ID excludes new cards, 'rank:'+ID excludes an
    existing upgrade. flag275=0 selects3 cards; when nonzero, bit0 of flag2573
    selects3 instead of4. G+1944 choice history has no effect on the
    new/existing/gold variants generated here. max_draws is a model watchdog.

    Allocated UI presentation bytes, 35513 world effects and 1203/6310 text
    notifications remain pending and are deliberately absent from this result.
    """
    if kind != 0:
        raise PendingCandidates135('Only kind0 is independently specified; kinds1/2 use1708')
    words = tuple(rng_words)
    if len(words) != 4 or any(type(x) is not int or not 0 <= x <= f.MASK for x in words):
        raise ValueError('rng_words must contain four u32 words')
    if type(level) is not int or not 0 <= level <= f.MASK:
        raise ValueError('level must be u32')
    for byte in (class_byte, flag275, flag2573):
        if type(byte) is not int or not 0 <= byte <= 255:
            raise ValueError('State flag/class must be u8')
    if any(type(bits) is not int or not 0 <= bits <= f.MASK for bits in (luck_bits, cooldown_bits)):
        raise ValueError('luck_bits/cooldown_bits must be raw f32 u32 bits')
    effects, summons = tuple(effects), tuple(summons)
    for effect in effects:
        if not (type(effect.kind) is int and 0 <= effect.kind <= 255 and
                type(effect.value_bits) is int and 0 <= effect.value_bits <= f.MASK):
            raise ValueError('Effects require u8 kind and raw f32 value bits')
    for summon in summons:
        if not (type(summon.tag) is int and 0 <= summon.tag <= f.MASK and
                type(summon.state41) is int and 0 <= summon.state41 <= 255):
            raise ValueError('Summons require u32 tag and u8 object state41')
    owned = tuple(owned)
    blocked_ids, banished_keys = frozenset(blocked_ids), frozenset(banished_keys)
    for item in owned:
        if item.ability_id not in DEFINITIONS:
            raise PendingCandidates135('Owned ID is outside the pinned114 declarations')
        if item.record.definition_pointer != DEFINITIONS[item.ability_id].pointer:
            raise ValueError('Owned record pointer differs from pinned definition')
    pool = []
    if len(owned) < 6:
        owned_ids = {item.ability_id for item in owned}
        new_weight = 0x3fcccccd if len(owned) < 3 else 0x3f666666
        for ability_id in CLASS_KITS[CLASS_BYTE.get(class_byte, 'warrior')]:
            if ability_id in owned_ids:
                continue
            # New2159 checks the special predicate before explicit blocked lists.
            if ability_id == 'demonic_empowerment' and not demonic_empowerment_available(effects, summons):
                continue
            if ability_id not in blocked_ids and ability_id not in banished_keys:
                pool.append((new_weight, 'new', ability_id, 0))
    for index, item in enumerate(owned):
        if eligible_kinds(item, 4, cooldown_bits) and 'rank:' + item.ability_id not in banished_keys:
            pool.append((0x3fa66666, 'upgrade', item.ability_id, index))
    frozen_pool = tuple(pool)
    if not pool:
        return CandidateResult((Candidate('gold', gold=25),), words, 0, frozen_pool)
    draws = 0

    def sample(high):
        nonlocal words, draws
        result = uniform_range_bits(words, 0, high, max_draws=max_draws)
        words = result.state
        draws += result.draws
        return result.bits

    count = 3 if not flag275 or (flag2573 & 1) else 4
    selected = []
    while pool and len(selected) < count:
        total = 0x80000000
        for entry in pool:
            total = f.add(total, entry[0])
        if not f.to_float(total) >= f.to_float(0x00800000):
            total = 0x00800000
        pick = sample(total)
        index = len(pool) - 1
        for i, entry in enumerate(pool):
            if f.to_float(pick) < f.to_float(entry[0]):
                index = i
                break
            pick = f.sub(pick, entry[0])
        selected.append(pool.pop(index))

    def shuffled(kinds):
        nonlocal words, draws
        result = list(kinds)
        for length in range(len(result), 1, -1):
            zone = ((length << (32 - length.bit_length())) - 1) & f.MASK
            for _ in range(max_draws):
                raw, words = next_u32_words(words)
                draws += 1
                product = raw * length
                if (product & f.MASK) <= zone:
                    break
            else:
                raise RuntimeError('Independent shuffle watchdog exceeded')
            index = product >> 32
            result[length - 1], result[index] = result[index], result[length - 1]
        return result

    weights = tier_weights(level, luck_bits)
    high = weights[0]
    for weight in weights[1:]:
        high = f.add(high, weight)
    candidates = []
    for _, variant, ability_id, index in selected:
        random = sample(high)
        tier = 0
        for n, weight in enumerate(weights):
            if f.to_float(random) < f.to_float(weight):
                tier = n
                break
            random = f.sub(random, weight)
        if variant == 'new':
            candidates.append(Candidate('new', tier, ability_id))
            continue
        item = owned[index]
        while tier < 4 and not eligible_kinds(item, tier, cooldown_bits):
            tier += 1
        kinds = shuffled(eligible_kinds(item, tier, cooldown_bits))
        kinds = tuple(kinds[:2 if tier == 4 else 1])
        candidates.append(Candidate('upgrade', tier, ability_id, index, kinds))
    return CandidateResult(tuple(candidates), words, draws, frozen_pool)
