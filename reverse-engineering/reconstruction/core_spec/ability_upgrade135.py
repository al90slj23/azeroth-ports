"""Independent135 ordered upgrade loop, reusing version-invariant arithmetic.

The full135 selector1072 still applies each kind in order through numeric25368.
Real135 declaration pointers/execution kinds must be supplied. This function
does not claim talent/equipment postprocessing, stats or completion side effects.
"""
from .ability_state import AbilityRecord, UpgradeCard, apply_upgrade_card as _apply


def apply_upgrade_card(record, card, definition):
    return _apply(record, card, definition)
