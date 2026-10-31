"""Independent specification of original 0.126.0 function25242.

The public domain here is upgrade kinds0..4 and tiers0..4. This computes the
upgrade value only; it does not mutate an ability or implement the whole game.
Fields remain numbered where their complete game meaning is still being traced.
"""
from dataclasses import dataclass

from . import binary32 as f

TABLES = (
    (0x3e3851ec, 0x3e800000, 0x3eae147b, 0x3eeb851f, 0x3f266666),
    (0x3d8f5c29, 0x3dcccccd, 0x3e051eb8, 0x3e2e147b, 0x3e6b851f),
    (1, 1, 1, 2, 2),
    (0x3df5c28f, 0x3e3851ec, 0x3e800000, 0x3eb33333, 0x3f000000),
    (0x3e19999a, 0x3e6147ae, 0x3e99999a, 0x3ecccccd, 0x3f19999a),
)
SPECIAL_CAP_TWO = frozenset((b'seal_fate', b'soul_fire', b'lightwell', b'faerie_fire'))


@dataclass(frozen=True)
class UpgradeState:
    counts: tuple = (0, 0, 0, 0, 0)
    field16_bits: int = 0x3f800000
    field20_u32: int = 0
    field24_bits: int = 0x3f800000
    field28_bits: int = 0x3f800000
    definition_kind: int = 0
    definition_id: bytes = b''


def upgrade_value_bits(kind, tier, state):
    """Return a raw binary32 result, preserving per-instruction rounding."""
    if kind not in range(5) or tier not in range(5) or len(state.counts) != 5:
        raise ValueError('This recovered API covers five kinds and five tiers')
    if not 0 <= state.definition_kind <= 255:
        raise ValueError('Definition kind must be an unsigned byte')
    if kind == 0:
        denominator = f.mul(f.from_u32(state.counts[0]), 0x3f000000)
        denominator = f.add(denominator, 0x3f800000)
        return f.div(TABLES[0][tier], denominator)
    if kind == 1:
        factor = f.add(state.field16_bits, 0xbe4ccccd)
        factor = f.div(factor, 0x3f4ccccd)
        return f.mul(TABLES[1][tier], f.positive_or_zero(factor))
    if kind == 2:
        cap = 12 if state.definition_kind != 11 else (2 if state.definition_id in SPECIAL_CAP_TWO else 0)
        remaining = max(0, cap - (state.field20_u32 & f.MASK))
        return f.from_u32(min(remaining, TABLES[2][tier]))
    if kind == 3:
        factor = f.sub(0x40a00000, state.field24_bits)
        factor = f.mul(factor, 0x3e800000)
        return f.mul(TABLES[3][tier], f.positive_or_zero(factor))
    factor = f.sub(0x40c00000, state.field28_bits)
    factor = f.div(factor, 0x40a00000)
    return f.mul(TABLES[4][tier], f.positive_or_zero(factor))
