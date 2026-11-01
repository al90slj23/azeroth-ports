"""Scoped independent2922 empty-account -> two absent companion selections.

2922 first clones the account's16B flag vector (account+240/+244). With count0
both companion entitlement booleans remain0, so the branch at its lines590..600
sets both selection tags255 and exits before definition lookup. Its output
tags+4/+12 pass via880 toApp+3604/+3612;6730 toselected376+228/+236;
1560's profile copy toGame+244/+252;1744 skips those tag255 variants.
No original runtime/memory/account/save is read by this model. Nonempty flags,
entitlements, selected definitions and the rest of2922 remain separate work.
"""
from dataclasses import dataclass

from .opening_entities135 import CompanionSlot135


@dataclass(frozen=True)
class EmptyCompanionProfile135:
    account_flags: tuple

    def __post_init__(self):
        if self.account_flags != () or type(self.account_flags) is not tuple:
            raise NotImplementedError('Only explicitly empty account16B flags are resolved')


@dataclass(frozen=True)
class AbsentCompanionSlot135(CompanionSlot135):
    """Known absent tag; unused payload is not fabricated as zero bytes."""
    pointer: int | None = None
    tag: int = 255
    entry40: int | None = None
    display32: int | None = None
    scale36_bits: int | None = None

    def __post_init__(self):
        if self.tag != 255 or any(value is not None for value in
                (self.pointer, self.entry40, self.display32, self.scale36_bits)):
            raise ValueError('Absent companion variant has only its known255 discriminant')


def produce_companion_slots(profile):
    if not isinstance(profile, EmptyCompanionProfile135):
        raise TypeError('Explicit empty account companion profile required')
    return (AbsentCompanionSlot135(), AbsentCompanionSlot135())
