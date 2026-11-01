"""0.135.1 enemy HP projection reused from independently recovered134 rules.

The semantic state types have legacy numeric labels. Physical135 offsets are
handled by the original-oracle runner, not by these production calculations.
Fresh135 cast/HP comparisons validate their declared composition; no134 count
is transferred. Procs, loot and death RNG remain explicit pending side effects.
"""
from .combat134 import (
    UnitState, CombatState, ItemModifier, AbilityReference, SpellModifier,
    AbilityLookupPanic, DamageResult, resolve_damage, encoded_hp,
)
