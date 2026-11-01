"""Official 0.134.0 / 983346a7 kind0 candidate metadata, static finite domain.

New2159/1480/29736/27375/32652 are the evidence. This module never loads or
executes WASM. It returns selection-relevant data and RNG state, not allocated
80B UI strings, world notifications, or a claim of full choice integration.
Kinds1/2 raise PendingCandidates134 before any input state is changed. Special
summon state and derived cooldown are supplied as explicit snapshots.
"""
from dataclasses import dataclass

from . import binary32 as f
from .ability_state import AbilityRecord
from .rng import next_u32_words, uniform_range_bits
from .upgrade_values import UpgradeState, upgrade_value_bits

SOURCE_SHA256 = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
WAT_SHA256 = '6014dab110e40ae279a6450ae15dcc0d84727c31e2da71f18f2cab1f21ec8422'


class PendingCandidates134(NotImplementedError):
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
    'cleave': Definition(5463472, (0, 1, 2), 5, 0x423c0000, 0x00000000, 3, 0, 0x3fc00000, 0x00000000),
    'whirlwind': Definition(5463560, (0, 1, 3), 2, 0x42400000, 0x41000000, 0, 0, 0x40900000, 0x00000000),
    'thunder_clap': Definition(5463648, (0, 1, 3), 2, 0x41a80000, 0x41200000, 0, 1, 0x40a00000, 0x00000000),
    'mortal_strike': Definition(5463736, (0, 1, 2), 5, 0x43088000, 0x00000000, 1, 0, 0x40400000, 0x00000000),
    'execute': Definition(5463824, (0, 1), 7, 0x42ea0000, 0x00000000, 1, 0, 0x40200000, 0x00000000),
    'demo_shout': Definition(5463912, (1, 3), 2, 0x41000000, 0x41600000, 0, 11, 0x41200000, 0x00000000),
    'battle_shout': Definition(5464000, (1, 4), 9, 0x00000000, 0x00000000, 0, 8, 0x41800000, 0x41000000),
    'bloodthirst': Definition(5464088, (0, 1, 2), 5, 0x42b00000, 0x00000000, 1, 5, 0x40800000, 0x00000000),
    'rend': Definition(5464176, (0, 1, 4, 2), 6, 0x429c0000, 0x00000000, 3, 0, 0x40400000, 0x40a00000),
    'shield_slam': Definition(5464264, (0, 1, 2), 5, 0x43160000, 0x00000000, 2, 3, 0x40c00000, 0x00000000),
    'bloodrage': Definition(5464352, (0, 1, 3), 11, 0x43110000, 0x41100000, 0, 0, 0x40e4cccd, 0x00000000),
    'consecration': Definition(5464440, (0, 1, 3, 4), 3, 0x42c00000, 0x41000000, 0, 0, 0x41000000, 0x41000000),
    'exorcism': Definition(5464528, (0, 1, 2), 0, 0x43070000, 0x00000000, 1, 0, 0x40600000, 0x00000000),
    'hammer_of_wrath': Definition(5464616, (0, 1, 2), 0, 0x42850000, 0x00000000, 1, 0, 0x3fcccccd, 0x00000000),
    'holy_shock': Definition(5464704, (0, 1, 2), 1, 0x42a70000, 0x00000000, 2, 6, 0x40400000, 0x00000000),
    'holy_wrath': Definition(5464792, (0, 1, 3), 2, 0x42606666, 0x41400000, 0, 0, 0x40e00000, 0x00000000),
    'judgement': Definition(5464880, (0, 1, 2), 0, 0x43480000, 0x00000000, 1, 0, 0x40c00000, 0x00000000),
    'hammer_of_justice': Definition(5464968, (0, 1, 2), 0, 0x425c0000, 0x00000000, 2, 3, 0x40e00000, 0x00000000),
    'holy_light': Definition(5465056, (0, 1), 9, 0x00000000, 0x00000000, 0, 6, 0x41400000, 0x00000000),
    'divine_shield': Definition(5465144, (1, 4), 9, 0x00000000, 0x00000000, 0, 12, 0x42000000, 0x40800000),
    'holy_shield': Definition(5465232, (0, 1, 4), 9, 0x00000000, 0x00000000, 0, 13, 0x41600000, 0x41200000),
    'redemption': Definition(5465320, (0, 1, 3), 11, 0x42500000, 0x41000000, 0, 0, 0x3eb851ec, 0x00000000),
    'auto_shot': Definition(5465408, (0, 1, 2), 0, 0x420a0000, 0x00000000, 2, 0, 0x3f8ccccd, 0x00000000),
    'arcane_shot': Definition(5465496, (0, 1, 2), 0, 0x42890000, 0x00000000, 1, 0, 0x40200000, 0x00000000),
    'multi_shot': Definition(5465584, (0, 1, 2), 0, 0x41f00000, 0x00000000, 3, 0, 0x3fcccccd, 0x00000000),
    'serpent_sting': Definition(5465672, (0, 1, 4, 2), 6, 0x42640000, 0x00000000, 2, 0, 0x40200000, 0x40a00000),
    'volley': Definition(5465760, (0, 1, 3, 4), 3, 0x424e6666, 0x41000000, 0, 0, 0x41000000, 0x40c00000),
    'explosive_trap': Definition(5465848, (0, 1, 3), 2, 0x420b3333, 0x41100000, 0, 0, 0x40c00000, 0x00000000),
    'concussive_shot': Definition(5465936, (0, 1, 2), 0, 0x41880000, 0x00000000, 2, 1, 0x40800000, 0x00000000),
    'aimed_shot': Definition(5466024, (0, 1, 2), 0, 0x43aa0000, 0x00000000, 1, 0, 0x40900000, 0x00000000),
    'immolation_trap': Definition(5466112, (0, 1, 3, 4), 3, 0x42700000, 0x40e00000, 0, 0, 0x41100000, 0x41000000),
    'frost_trap': Definition(5466200, (0, 1, 3, 4), 3, 0x41840000, 0x41200000, 0, 2, 0x41200000, 0x40c00000),
    'hunters_mark': Definition(5466288, (0, 1, 3), 11, 0x437a0000, 0x41000000, 0, 0, 0x3fb70a3d, 0x00000000),
    'sinister_strike': Definition(5466376, (0, 1, 2), 5, 0x420c0000, 0x00000000, 2, 0, 0x3f800000, 0x00000000),
    'eviscerate': Definition(5466464, (0, 1), 7, 0x42b60000, 0x00000000, 2, 0, 0x40400000, 0x00000000),
    'blade_flurry': Definition(5466552, (0, 1, 3), 2, 0x41c00000, 0x40e00000, 0, 0, 0x40200000, 0x00000000),
    'rupture': Definition(5466640, (0, 1, 4, 2), 6, 0x42740000, 0x00000000, 2, 0, 0x40600000, 0x40800000),
    'kidney_shot': Definition(5466728, (0, 1, 2), 5, 0x41c80000, 0x00000000, 2, 3, 0x40c00000, 0x00000000),
    'gouge': Definition(5466816, (0, 1, 2), 5, 0x41cc0000, 0x00000000, 3, 3, 0x40a00000, 0x00000000),
    'ghostly_strike': Definition(5466904, (0, 1, 2), 5, 0x42380000, 0x00000000, 1, 7, 0x40800000, 0x00000000),
    'adrenaline_rush': Definition(5466992, (1, 4), 9, 0x00000000, 0x00000000, 0, 9, 0x41a00000, 0x41000000),
    'backstab': Definition(5467080, (0, 1), 7, 0x425e0000, 0x00000000, 2, 0, 0x3fe66666, 0x00000000),
    'slice_and_dice': Definition(5467168, (1, 4), 9, 0x00000000, 0x00000000, 0, 8, 0x41700000, 0x41100000),
    'seal_fate': Definition(5467256, (0, 1, 2), 11, 0x43020000, 0x00000000, 1, 0, 0x3fe51eb8, 0x00000000),
    'smite': Definition(5467344, (0, 1, 2), 0, 0x42260000, 0x00000000, 1, 0, 0x3f99999a, 0x00000000),
    'sw_pain': Definition(5467432, (0, 1, 4, 2), 6, 0x42900000, 0x00000000, 2, 0, 0x3fcccccd, 0x40c00000),
    'mind_blast': Definition(5467520, (0, 1, 2), 0, 0x42ba0000, 0x00000000, 1, 0, 0x40800000, 0x00000000),
    'holy_nova': Definition(5467608, (0, 1, 3), 2, 0x41da6666, 0x41200000, 0, 6, 0x40800000, 0x00000000),
    'pw_shield': Definition(5467696, (0, 1), 9, 0x00000000, 0x00000000, 0, 7, 0x41400000, 0x41400000),
    'renew': Definition(5467784, (0, 1), 9, 0x00000000, 0x00000000, 0, 6, 0x41200000, 0x41200000),
    'holy_fire': Definition(5467872, (0, 1, 2), 0, 0x43200000, 0x00000000, 1, 0, 0x40a00000, 0x00000000),
    'mind_flay': Definition(5467960, (0, 1, 3), 8, 0x42533333, 0x00000000, 0, 1, 0x40200000, 0x00000000),
    'psychic_scream': Definition(5468048, (1, 3), 2, 0x41280000, 0x41200000, 0, 4, 0x41400000, 0x00000000),
    'devouring_plague': Definition(5468136, (0, 1, 4, 2), 6, 0x42d50000, 0x00000000, 3, 5, 0x40c00000, 0x40c00000),
    'lightwell': Definition(5468224, (0, 1, 4, 2), 11, 0x42a00000, 0x00000000, 1, 0, 0x4164cccd, 0x40e4cccd),
    'lightning_bolt': Definition(5468312, (0, 1, 2), 0, 0x42120000, 0x00000000, 2, 0, 0x3fb33333, 0x00000000),
    'chain_lightning': Definition(5468400, (0, 1, 2), 4, 0x421e0000, 0x41400000, 5, 0, 0x4019999a, 0x00000000),
    'earth_shock': Definition(5468488, (0, 1, 2), 0, 0x42bb0000, 0x00000000, 1, 0, 0x40400000, 0x00000000),
    'flame_shock': Definition(5468576, (0, 1, 4, 2), 6, 0x42a50000, 0x00000000, 2, 0, 0x40400000, 0x40c00000),
    'frost_shock': Definition(5468664, (0, 1, 2), 0, 0x42680000, 0x00000000, 2, 1, 0x40600000, 0x00000000),
    'lightning_shield': Definition(5468752, (0,), 9, 0x00000000, 0x00000000, 0, 13, 0x41700000, 0x41700000),
    'magma_totem': Definition(5468840, (0, 1, 3, 4), 10, 0x41c00000, 0x41200000, 0, 0, 0x41400000, 0x41400000),
    'searing_totem': Definition(5468928, (0, 1, 4, 2), 10, 0x42080000, 0x00000000, 1, 0, 0x41200000, 0x41700000),
    'fire_nova': Definition(5469016, (0, 1, 3), 2, 0x42280000, 0x41400000, 0, 0, 0x40a00000, 0x00000000),
    'healing_wave': Definition(5469104, (0, 1), 9, 0x00000000, 0x00000000, 0, 6, 0x41400000, 0x00000000),
    'stormstrike': Definition(5469192, (0, 1, 2), 5, 0x43ac0000, 0x00000000, 1, 0, 0x40e00000, 0x00000000),
    'rockbiter': Definition(5469280, (0, 1, 2), 5, 0x42f00000, 0x00000000, 2, 0, 0x3fe49ba6, 0x00000000),
    'fireball': Definition(5469368, (0, 1, 2), 0, 0x424a0000, 0x00000000, 1, 0, 0x3fa66666, 0x00000000),
    'frostbolt': Definition(5469456, (0, 1, 2), 0, 0x42120000, 0x00000000, 1, 1, 0x3fc00000, 0x00000000),
    'arcane_missiles': Definition(5469544, (0, 1, 2), 1, 0x41c9999a, 0x00000000, 4, 0, 0x3fe66666, 0x00000000),
    'frost_nova': Definition(5469632, (0, 1, 3), 2, 0x4144cccd, 0x41200000, 0, 2, 0x40e00000, 0x00000000),
    'arcane_explosion': Definition(5469720, (0, 1, 3), 2, 0x41c9999a, 0x41100000, 0, 0, 0x40200000, 0x00000000),
    'blizzard': Definition(5469808, (0, 1, 3, 4), 3, 0x4273999a, 0x41100000, 0, 1, 0x41000000, 0x40e00000),
    'flamestrike': Definition(5469896, (0, 1, 3, 4), 3, 0x42546666, 0x41000000, 0, 0, 0x40e00000, 0x40c00000),
    'fire_blast': Definition(5469984, (0, 1, 2), 1, 0x42880000, 0x00000000, 1, 0, 0x40400000, 0x00000000),
    'cone_of_cold': Definition(5470072, (0, 1, 3), 8, 0x420b3333, 0x00000000, 0, 1, 0x40800000, 0x00000000),
    'blast_wave': Definition(5470160, (0, 1, 3), 2, 0x4207999a, 0x41200000, 0, 1, 0x41000000, 0x00000000),
    'pyroblast': Definition(5470248, (0, 1, 2), 0, 0x43bdc000, 0x00000000, 1, 0, 0x40e00000, 0x00000000),
    'ice_barrier': Definition(5470336, (0, 1), 9, 0x00000000, 0x00000000, 0, 7, 0x41700000, 0x41700000),
    'polymorph': Definition(5470424, (0, 3), 11, 0x42e60000, 0x40e00000, 0, 0, 0x400926e9, 0x00000000),
    'shadow_bolt': Definition(5470512, (0, 1, 2), 0, 0x42080000, 0x00000000, 1, 0, 0x3fb33333, 0x00000000),
    'corruption': Definition(5470600, (0, 1, 4, 2), 6, 0x427a0000, 0x00000000, 2, 0, 0x3fb33333, 0x40c00000),
    'immolate': Definition(5470688, (0, 1, 4, 2), 6, 0x428a0000, 0x00000000, 1, 0, 0x40200000, 0x40a00000),
    'curse_of_agony': Definition(5470776, (0, 1, 4, 2), 6, 0x42cf0000, 0x00000000, 3, 0, 0x40400000, 0x41100000),
    'rain_of_fire': Definition(5470864, (0, 1, 3, 4), 3, 0x42533333, 0x41000000, 0, 0, 0x41000000, 0x41000000),
    'hellfire': Definition(5470952, (0, 1, 3), 2, 0x41400000, 0x40e00000, 0, 0, 0x3fc00000, 0x00000000),
    'death_coil': Definition(5471040, (0, 1, 2), 0, 0x42960000, 0x00000000, 1, 5, 0x40c00000, 0x00000000),
    'searing_pain': Definition(5471128, (0, 1, 2), 1, 0x42480000, 0x00000000, 1, 0, 0x3fcccccd, 0x00000000),
    'drain_life': Definition(5471216, (0, 1, 4, 2), 6, 0x42660000, 0x00000000, 1, 5, 0x40800000, 0x40400000),
    'fear': Definition(5471304, (1, 2), 0, 0x40b00000, 0x00000000, 3, 4, 0x40c00000, 0x00000000),
    'soul_fire': Definition(5471392, (0, 1, 2), 11, 0x44160000, 0x00000000, 1, 0, 0x408947ae, 0x00000000),
    'demonic_empowerment': Definition(5471480, (1, 4), 9, 0x00000000, 0x00000000, 0, 10, 0x41800000, 0x41000000),
    'wrath': Definition(5471568, (0, 1, 2), 0, 0x42160000, 0x00000000, 2, 0, 0x3f99999a, 0x00000000),
    'moonfire': Definition(5471656, (0, 1, 4, 2), 6, 0x428f0000, 0x00000000, 3, 0, 0x3fe66666, 0x40a00000),
    'starfire': Definition(5471744, (0, 1, 2), 0, 0x43080000, 0x00000000, 1, 0, 0x40900000, 0x00000000),
    'hurricane': Definition(5471832, (0, 1, 3, 4), 3, 0x42896666, 0x41200000, 0, 1, 0x41100000, 0x41000000),
    'insect_swarm': Definition(5471920, (0, 1, 4, 2), 6, 0x428a0000, 0x00000000, 3, 11, 0x40200000, 0x40c00000),
    'entangling_roots': Definition(5472008, (0, 1, 2), 0, 0x41e40000, 0x00000000, 3, 2, 0x40a00000, 0x00000000),
    'rejuvenation': Definition(5472096, (0, 1), 9, 0x00000000, 0x00000000, 0, 6, 0x41000000, 0x41400000),
    'regrowth': Definition(5472184, (0, 1), 9, 0x00000000, 0x00000000, 0, 6, 0x41600000, 0x00000000),
    'thorns': Definition(5472272, (0,), 9, 0x00000000, 0x00000000, 0, 13, 0x41a00000, 0x41a00000),
    'swipe': Definition(5472360, (0, 1, 3), 2, 0x41ce6666, 0x40e00000, 0, 0, 0x40400000, 0x00000000),
    'shred': Definition(5472448, (0, 1), 5, 0x42d20000, 0x00000000, 1, 0, 0x40000000, 0x00000000),
    'faerie_fire': Definition(5472536, (0, 2, 3), 11, 0x43480000, 0x41000000, 1, 0, 0x3f800000, 0x00000000),
    'perception': Definition(5472624, (1, 4), 9, 0x00000000, 0x00000000, 0, 8, 0x41f00000, 0x41200000),
    'blood_fury': Definition(5472712, (1, 4), 9, 0x00000000, 0x00000000, 0, 8, 0x42200000, 0x41400000),
    'stoneform': Definition(5472800, (0, 1), 9, 0x00000000, 0x00000000, 0, 7, 0x41f00000, 0x41000000),
    'shadowmeld': Definition(5472888, (1, 4), 9, 0x00000000, 0x00000000, 0, 12, 0x42960000, 0x40400000),
    'will_of_the_forsaken': Definition(5472976, (1, 4), 9, 0x00000000, 0x00000000, 0, 12, 0x42700000, 0x40800000),
    'war_stomp': Definition(5473064, (0, 1, 3), 2, 0x41400000, 0x41000000, 0, 3, 0x41700000, 0x00000000),
    'escape_artist': Definition(5473152, (0, 1, 3), 2, 0x40c00000, 0x41000000, 0, 2, 0x41a00000, 0x00000000),
    'berserking': Definition(5473240, (1, 4), 9, 0x00000000, 0x00000000, 0, 9, 0x420c0000, 0x41200000),
    'penance': Definition(5473328, (0, 1, 2), 1, 0x424a0000, 0x00000000, 3, 0, 0x400ccccd, 0x00000000),
    'arcane_power': Definition(5473416, (1, 4), 9, 0x00000000, 0x00000000, 0, 8, 0x41f00000, 0x41400000),
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
            raise PendingCandidates134('Unknown declared upgrade kind')
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
        raise PendingCandidates134('Only kind0 is independently specified; kinds1/2 use1708')
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
            raise PendingCandidates134('Owned ID is outside the pinned114 declarations')
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
