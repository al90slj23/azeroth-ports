"""Fixed135 run counters maintained by accepted death events.

This owns the orthogonal run counters omitted by headless135. It reads no
records to infer past deaths. Level and earned gold remain owned by the
existing progression/currency producers. Boss, guardian and chest continuations
remain explicit boundaries; this is the ordinary-death counter slice of914.
"""
from dataclasses import dataclass, replace

from .combat135 import DamageResult
from .currency134 import CurrencyState
from .level_cycle135 import LevelCycleState


class UnknownRunSummary135(NotImplementedError):
    pass


def _word(value):
    if type(value) is not int or not 0 <= value < 1 << 32:
        raise ValueError('Explicit unsigned32 counter required')
    return value


@dataclass(frozen=True)
class RunSummaryCounters135:
    kills1084: int
    elites1088: int
    guardians1092: int
    bosses1096: int
    chests1104: int

    def __post_init__(self):
        for value in (self.kills1084, self.elites1088, self.guardians1092,
                      self.bosses1096, self.chests1104):
            _word(value)


def empty_constructor_counters135():
    """1560 scratch zero/copy writes, before any accepted death or chest.

    G is scratch+88. G1084..1104 come from scratch1172..1195, whose
    unaligned copied bytes originate at scratch2807..2830. The constructor
    explicitly writes zero across2795..2838 before those copies. This does
    not assert that a running state with unobserved events still has zeroes.
    """
    return RunSummaryCounters135(0, 0, 0, 0, 0)


def accept_ordinary_death135(state, damage):
    """Consume914's exact accepted lethal-hit event once, at its callback.

    resolve_damage rejects marker1 targets before creating an accepted result;
    apply_hit invokes after_death once for each applied+dead result. This
    adapter must be called at that event, including successive same-phase
    deaths. A result with a special/summoned/guardian source is not admitted.
    """
    if not isinstance(state, RunSummaryCounters135) or not isinstance(damage, DamageResult):
        raise TypeError('Counter owner and actual DamageResult required')
    if not damage.applied or not damage.dead:
        return state
    target = damage.target
    if target is None or target.marker != 1:
        raise ValueError('Accepted death must carry the just-written marker1 target')
    if (target.kind_40, target.kind_64, target.elite_244) != (-1, -1, -1):
        raise UnknownRunSummary135('Full nonordinary914 counter continuation is unresolved')
    rank = target.elite_416
    if type(rank) is not int or not 0 <= rank < 256:
        raise UnknownRunSummary135('914 rawU416 elite classification byte is unresolved')
    return replace(state, kills1084=(state.kills1084 + 1) & 0xffffffff,
                   elites1088=(state.elites1088 + (rank & 1)) & 0xffffffff)


def summary_counters135(state, level, currency):
    """Assemble1938's seven counters from their independent current owners.

    The five event counters come from this owner. Current level and lifetime
    collected run gold come from the existing canonical producers; available
    gold, current unit population and current pickup records are not tallies.
    """
    if not isinstance(state, RunSummaryCounters135):
        raise TypeError('Explicit event-maintained run counters required')
    if not isinstance(level, LevelCycleState) or not isinstance(currency, CurrencyState):
        raise TypeError('Canonical progression/currency owners required')
    return ((1432, _word(level.progression.level)),
            (1084, state.kills1084), (1088, state.elites1088),
            (1092, state.guardians1092), (1096, state.bosses1096),
            (1100, currency.earned), (1104, state.chests1104))
