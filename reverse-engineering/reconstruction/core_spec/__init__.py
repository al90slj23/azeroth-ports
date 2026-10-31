"""Independent, executable specifications of recovered game rules.

This package does not load the original game. Only explicitly recovered
subsystems are implemented; it is not yet a playable replacement core.
"""

from .upgrade_values import UpgradeState, upgrade_value_bits

__all__ = ['UpgradeState', 'upgrade_value_bits']
