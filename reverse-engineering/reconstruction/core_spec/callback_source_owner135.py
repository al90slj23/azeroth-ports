"""Fixed135 callback source owners from the explicit empty research profile.

9868 constructs five vectors from P152's ranked-effect input;25765 optionally
adds equipment effects;1560 copies them toGame2024..2083. This module restores
the empty input branch and source-preserving ordinary selection branches. It
never derives physical emptiness from level.sources, a missing field or an
original observation. Nonempty profile/equipment producers remain boundaries.
"""
from dataclasses import dataclass, replace

from .candidates135 import Candidate, DEFINITIONS
from .incoming_callbacks135 import CallbackVector135


class UnknownCallbackSourceOwner135(NotImplementedError):
    pass


@dataclass(frozen=True)
class CallbackSourcesProfile135:
    ranked_effect_count160: int | None
    ranked_effect_flag164: int | None
    equipped_item_ids260: tuple


@dataclass(frozen=True)
class CallbackSourceOwner135:
    items8: CallbackVector135
    modifiers36: CallbackVector135
    ordinary_selection_events: tuple = ()

    def __post_init__(self):
        if not isinstance(self.items8, CallbackVector135) or self.items8.stride != 8:
            raise TypeError('Physical item8 source owner required')
        if not isinstance(self.modifiers36, CallbackVector135) or self.modifiers36.stride != 36:
            raise TypeError('Physical event-definition36 source owner required')
        if (self.items8.count, self.modifiers36.count) != (0, 0):
            raise UnknownCallbackSourceOwner135('Nonempty source production is not restored')
        if any(vector.storage or vector.capacity_word != 0 for vector in (self.items8, self.modifiers36)):
            raise UnknownCallbackSourceOwner135('This owner requires the actual9868 empty-header branch')

    @property
    def constructor_headers(self):
        # These4s are align4 dangling sentinels written by9868, not allocated
        # memory addresses. Callback consumers do not read them when count0.
        return ((2024, 0), (2028, 4), (2032, 0),
                (2048, 0), (2052, 4), (2056, 0))


def produce_callback_source_owner135(profile):
    """Produce count0 owners only from complete known empty profile inputs.

    P160=0 bypasses9868's ranked-effect pass and its derived40B queue;P164=0
    bypasses its flag-conditioned rewrite. All19 equipped IDs atP260..332
    zero cause1976(0) notfound and20363 tag2, so25765 adds no gear effects.
    Initial numeric cap/pointer/count0/4/0 come from9868's explicit stores.
    """
    if not isinstance(profile, CallbackSourcesProfile135):
        raise TypeError('Explicit selected-profile source inputs required')
    if profile.ranked_effect_count160 is None or profile.ranked_effect_flag164 is None:
        raise UnknownCallbackSourceOwner135('Ranked effect count/flag source is unresolved')
    if profile.ranked_effect_count160 != 0 or profile.ranked_effect_flag164 != 0:
        raise UnknownCallbackSourceOwner135('Nonempty ranked profile effects require9868 production')
    if (type(profile.equipped_item_ids260) is not tuple or len(profile.equipped_item_ids260) != 19
            or any(type(value) is not int or value != 0 for value in profile.equipped_item_ids260)):
        raise UnknownCallbackSourceOwner135('All19 explicit zero equipped IDs are required; gear effects remain unresolved')
    return CallbackSourceOwner135(CallbackVector135(8, 0, (), capacity_word=0),
                                  CallbackVector135(36, 0, (), capacity_word=0))


def empty_research_callback_sources135():
    """Named explicit blank376B research-profile domain, not natural menu.

    The research profile constructor deliberately zerosP376 before supplying
    identity/zone/class/race. This declares that same empty effects/equipment
    input domain; the absence of such fields in EmptyOpeningInput is not used
    as evidence. Real accounts with talents/gear must use their real producer.
    """
    return produce_callback_source_owner135(CallbackSourcesProfile135(0, 0, (0,) * 19))


def retain_callback_sources_after_selection135(owner, card, *, phase2587, selection_kind2585):
    """Preserve source owners through1072's ordinary kind0 card branches.

    Upgrade touches an existing owned80;new initializes/appends an owned80
    after readonly26967 and reorders owned priorities through24129;gold calls
    28796. Their common1512/4600 continuation reads these source headers.
    Equipment/trait/summon/item variants andkind1/2 are not admitted;2435 can
    rebuild the vectors and must not be silently represented by this retain.
    This records the accepted selection event; it does not itself select it.
    """
    if not isinstance(owner, CallbackSourceOwner135) or not isinstance(card, Candidate):
        raise TypeError('Existing physical source owner and actual Candidate required')
    if phase2587 != 2 or selection_kind2585 != 0:
        raise UnknownCallbackSourceOwner135('Only actual ordinary kind0 selection source preservation is restored')
    if card.variant not in ('upgrade', 'new', 'gold'):
        raise UnknownCallbackSourceOwner135('Equipment/trait/summon source mutation requires its real producer')
    if card.variant == 'new' and card.ability_id not in DEFINITIONS:
        raise UnknownCallbackSourceOwner135('Unresolved new-skill declaration')
    event = (card.variant, card.ability_id, card.owned_index, card.tier, tuple(card.kinds))
    return replace(owner, ordinary_selection_events=owner.ordinary_selection_events + (event,))
