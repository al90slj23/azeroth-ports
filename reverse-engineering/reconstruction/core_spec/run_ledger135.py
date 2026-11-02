"""Same-run history, event counters and selected-profile hero ownership.

This module performs no original/runtime/file IO. The research constructor
names its explicit empty selected376 input; missing profile fields elsewhere
never imply an empty hero. Incoming history is committed before callbacks,
including a lethal prefix whose final continuation remains unresolved.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .incoming135 import resolve_incoming_prefix
from .incoming_history135 import (
    IncomingHistory135, from_raw_storage, append_incoming_history,
    projection as history_projection135,
)
from .incoming_source135 import (
    resolve_incoming_source135, ordinary_english_source_names135,
)
from .profile_hero135 import ProfileHero135, empty_research_selected_profile_hero135
from .callback_source_owner135 import (
    CallbackSourceOwner135, empty_research_callback_sources135,
    retain_callback_sources_after_selection135,
)
from .run_summary135 import (
    RunSummaryCounters135, empty_constructor_counters135,
    accept_ordinary_death135, summary_counters135,
)


class UnknownRunLedger135(NotImplementedError):
    pass


@dataclass(frozen=True)
class RunLedger135:
    counters: RunSummaryCounters135
    history: IncomingHistory135
    hero: ProfileHero135
    localization_profile: str
    callback_sources: CallbackSourceOwner135
    lives1632: int
    left2567: int
    auxiliary_motion: object|None = None

    def __post_init__(self):
        if not isinstance(self.counters, RunSummaryCounters135):
            raise TypeError('Explicit event-maintained run counters required')
        if not isinstance(self.history, IncomingHistory135):
            raise TypeError('Explicit complete incoming48 owner required')
        if not isinstance(self.hero, ProfileHero135):
            raise TypeError('Explicit selected-profile hero producer required')
        if self.localization_profile != 'english_fallback':
            raise UnknownRunLedger135('Other source-name/summary localization producers remain unresolved')
        if not isinstance(self.callback_sources,CallbackSourceOwner135):
            raise TypeError('Constructor/selection-maintained callback source owner required')
        if type(self.lives1632)is not int or not 0<=self.lives1632<1<<32:
            raise ValueError('Explicit lives1632 word required')
        if type(self.left2567)is not int or not 0<=self.left2567<256:
            raise ValueError('Explicit left2567 byte required')


@dataclass(frozen=True)
class RecordedIncoming135:
    ledger: RunLedger135
    prefix: object


def empty_research_run_ledger135(*,auxiliary_motion=None):
    """1560 empty376 contract, not a default for arbitrary running states.

    scratch1056 i64=17179869184 and scratch1064 i64=0, copied from
    scratch+88, produce G968cap0/G972ptr4/G976head0/G980count0. The
    semantic history owner never dereferences or invents the ptr4 sentinel.
    The explicit selected376 name input is length0, cloned to cap0/ptr1/len0.
    1560 scratch1720=0 and scratch2655 byte0 produce lives1632/left2567.
    Callback vectors come from9868/25765's explicit empty profile branch.
    """
    return RunLedger135(empty_constructor_counters135(), from_raw_storage((), 0, 0),
        empty_research_selected_profile_hero135(), 'english_fallback',
        empty_research_callback_sources135(),0,0,auxiliary_motion)


def record_ordinary_death135(ledger, damage):
    if not isinstance(ledger, RunLedger135):
        raise TypeError('Canonical run ledger required')
    return replace(ledger, counters=accept_ordinary_death135(ledger.counters, damage))


def record_ordinary_selection135(ledger, card, *, phase2587, selection_kind2585):
    """Retain sources/lives only through1072's restored ordinary branches.

    The other tag16 trait branch can add lives and is not admitted here. A
    new equipment/talent/summon producer cannot silently retain these owners.
    """
    sources=retain_callback_sources_after_selection135(ledger.callback_sources,card,
        phase2587=phase2587,selection_kind2585=selection_kind2585)
    return replace(ledger,callback_sources=sources)


def record_incoming_prefix135(ledger, incoming, amount_bits, source_guid, *,
        source_records, maximum_hp_bits, category=0):
    """1073 scalar prefix→source resolution→48B append, before callbacks.

    This does not claim the item/raw13/984 continuations are complete. The
    caller must prove or execute them before using the prefix's final HP.
    A minimum-one clamp is later than history: record the unclamped HP here.
    Returned entry guards neither resolve a source nor append history.
    """
    if not isinstance(ledger, RunLedger135):
        raise TypeError('Canonical run ledger required')
    result = resolve_incoming_prefix(incoming, amount_bits, source_guid)
    if result.status == 'returned':
        return RecordedIncoming135(ledger, result)
    if result.stage not in ('scalar_nonfatal_projection', 'before_unresolved_death'):
        raise UnknownRunLedger135('Incoming continuation before history is unresolved: ' + result.stage)
    source = resolve_incoming_source135(source_records, source_guid,
        resolved_definition_names=ordinary_english_source_names135())
    history = append_incoming_history(ledger.history, now_bits=incoming.now_bits,
        damage_bits=result.amount_bits, absorbed_bits=result.absorbed_bits,
        hp_after_prefix_bits=f.sub(incoming.hp_1528_bits, result.amount_bits),
        maximum_hp_bits=maximum_hp_bits, category=category,
        source_label=source.source_label, source_classification=source.source_classification)
    return RecordedIncoming135(replace(ledger, history=history), result)


def run_ledger_projection135(ledger, level, currency):
    """Known history cells and semantic strings; pointers remain unknown."""
    history = history_projection135(ledger.history)
    return dict(counters=dict(summary_counters135(ledger.counters, level, currency)),
        hero=ledger.hero.text, incoming_history={k: history[k] for k in ('header', 'storage', 'active')},
        lives1632=ledger.lives1632,left2567=ledger.left2567)
