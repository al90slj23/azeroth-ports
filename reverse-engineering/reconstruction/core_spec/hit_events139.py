"""Current139 constructor-only sources and exact empty994/913-tail routing.

This is a static recovery, with no new original runtime acceptance. A source
owner is produced from the selected profile bytes actually consumed by
1600 -> 25911 -> 9819/20442. Unknown bytes are kept unknown. Nonempty36-byte
event definitions, execution11 procs and other constructors remain pending.

The tail plan covers only the conditional two994 region of913; it does not
replace death, XP, on-hit schedules, spell-set handling or any other913 work.
"""
from dataclasses import dataclass
from .hit_events139_data import DECLARATIONS139, RACIAL_POINTERS139

MASK = (1 << 32) - 1


class PendingHitEvents139(RuntimeError):
    pass


def _cells(value, size, label):
    if isinstance(value, bytes):
        result = tuple(value)
    elif type(value) is tuple:
        result = value
    else:
        raise TypeError(label + ' requires bytes or canonical byte/None tuple')
    if len(result) != size or any(x is not None and (type(x) is not int or not 0 <= x < 256) for x in result):
        raise ValueError(label + ' has invalid canonical cells')
    return result


def _uint(cells, offset, size, label):
    row = cells[offset:offset + size]
    if any(x is None for x in row):
        raise PendingHitEvents139('Unknown consumed ' + label)
    return int.from_bytes(bytes(row), 'little')


@dataclass(frozen=True)
class EventDefinitions139:
    capacity_word: int | None
    pointer_word: int | None
    count: int | None
    records36: tuple | None

    def __post_init__(self):
        for name in ('capacity_word', 'pointer_word', 'count'):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or not 0 <= value <= MASK):
                raise ValueError(name + ' is an explicit u32 or None')
        if self.records36 is not None:
            if type(self.records36) is not tuple:
                raise TypeError('Ordered physical36 records required')
            for row in self.records36:
                _cells(row, 36, 'event36')
            if self.count is not None and len(self.records36) != self.count:
                raise ValueError('Count and event36 backing disagree')


def produce_empty_profile_event_definitions139(selected_profile376):
    """Known empty owner, not a semantic empty tuple supplied as a boolean.

    P160 is the count of the P152 talent8 vector consumed by9819. The 19
    equipment IDs are read by20442 atP260. All zero IDs resolve to absent
    in2004, so20442 returns tag2 and25911 skips the equipment-source arm.
    Rank bytes, inactive headers and the rest ofP376 need not be known.
    9819's third vector is cap0/ptr4/count0;25911 and1600 copy it unchanged
    to Game2048/2052/2056. This is valid only at the constructor boundary.
    """
    cells = _cells(selected_profile376, 376, 'selected profile376')
    if _uint(cells, 160, 4, 'profile talent count160') != 0:
        raise PendingHitEvents139('Nonempty talent-derived sources pending')
    for at in range(260, 336, 4):
        if _uint(cells, at, 4, 'equipment ID' + str(at)) != 0:
            raise PendingHitEvents139('Equipment-derived event sources pending')
    return EventDefinitions139(0, 4, 0, ())


@dataclass(frozen=True)
class OwnedExecutionScan139:
    definition_pointers: tuple
    execution_bytes84: tuple
    execution11_arm_skipped: bool


def prove_owned_execution11_absent139(owned_records80, declarations):
    """Exact913 owned80 scan: record.pointer -> definition.byte84 ==11.

    This proves only that particular arm is skipped. The inline racial80
    is a separate Game1256 record, not another element ofGame1660/1664.
    No owned multiplier/padding/cooldown is read by this guard.
    """
    if type(owned_records80) is not tuple or type(declarations) is not tuple:
        raise TypeError('Ordered owned records and resolved declarations required')
    resolved = {}
    for pointer, definition88 in declarations:
        if type(pointer) is not int or not 0 <= pointer <= MASK or pointer in resolved:
            raise ValueError('Unique u32 definition pointer required')
        resolved[pointer] = _cells(definition88, 88, 'ability88')
    pointers, codes = [], []
    for record in owned_records80:
        pointer = _uint(_cells(record, 80, 'owned80'), 0, 4, 'owned definition pointer')
        if pointer not in resolved:
            raise PendingHitEvents139('Unresolved owned definition')
        execution = _uint(resolved[pointer], 84, 1, 'definition execution84')
        if execution == 11:
            raise PendingHitEvents139('Nonempty execution11 owned proc arm pending')
        pointers.append(pointer)
        codes.append(execution)
    return OwnedExecutionScan139(tuple(pointers), tuple(codes), True)


@dataclass(frozen=True)
class ConstructorHitSources139:
    event_definitions36: EventDefinitions139
    owned_execution_scan: OwnedExecutionScan139
    racial_pointer: int
    racial_execution84: int
    initial_mode770: int


def produce_default_cleave_hit_sources139(selected_profile376, owned_records80, racial80):
    """Empty-profile warrior plus one of the eight current constructor racials.

    Full declarations are literal139 data, independently bound by the static
    trace. Only class/race, record pointers, talent count and equipment IDs
    are consumed. This does not prove that later selection/equipment writes
    preserve the owner; a caller must retain the actual state producer chain.
    """
    cells = _cells(selected_profile376, 376, 'selected profile376')
    if _uint(cells, 344, 1, 'class344') != 1:
        raise PendingHitEvents139('Only constructor warrior cleave admitted')
    race = _uint(cells, 345, 1, 'race345')
    if not 1 <= race <= len(RACIAL_POINTERS139):
        raise PendingHitEvents139('Unresolved current racial declaration')
    if type(owned_records80) is not tuple or len(owned_records80) != 1:
        raise PendingHitEvents139('Only one constructor-owned cleave admitted')
    if _uint(_cells(owned_records80[0], 80, 'owned80'), 0, 4, 'owned pointer') != 5882740:
        raise PendingHitEvents139('Non-default owned ability pending')
    pointer = _uint(_cells(racial80, 80, 'racial80'), 0, 4, 'racial pointer')
    if pointer != RACIAL_POINTERS139[race - 1]:
        raise PendingHitEvents139('Racial record does not match selected race')
    declarations = tuple((p, bytes.fromhex(row[1])) for p, row in DECLARATIONS139.items())
    scan = prove_owned_execution11_absent139(owned_records80, declarations)
    racial_execution = bytes.fromhex(DECLARATIONS139[pointer][1])[84]
    return ConstructorHitSources139(produce_empty_profile_event_definitions139(cells), scan,
                                    pointer, racial_execution, 0)


@dataclass(frozen=True)
class EmptyDispatch139:
    event_records_consumed: int = 0
    game_writes: tuple = ()
    RNG_draws: int = 0
    helper_calls: tuple = ()
    heap_allocations: int = 0


def dispatch_hit_event139(sources, event35=None, death44_context=None):
    """994's real outer empty branch, without reading an inactive event.

    The original subtracts/restores176 fromSP and loadsG2056. With count0 it
    never readsG2052, event bytes, owned/racial records, RNG or keyed fields.
    Nonempty source dispatch has effects and is intentionally not a no-op.
    """
    if not isinstance(sources, EventDefinitions139) or sources.count is None:
        raise PendingHitEvents139('Unknown physical event-definition owner')
    if sources.count != 0:
        raise PendingHitEvents139('Nonempty994 dispatch pending')
    return EmptyDispatch139()


@dataclass(frozen=True)
class DamageTailEventPlan139:
    reason: str
    calls994: tuple
    release_death44: bool
    release_bytes: int | None
    event_region_game_writes: tuple


def plan_damage_tail_events139(mode770, sources, death44_count):
    """913@12790..13071 only; exact early skip, not full913 completion.

    mode3 short-circuits before reading the source count. A known empty
    count also makes the result independent of an unknown mode byte. The
    death-list release is returned as a plan, never carried out here. Counts
    zero and u32(-1) skip free; other u32 counts use wrapped count*44.
    """
    if mode770 is not None and (type(mode770) is not int or not 0 <= mode770 < 256):
        raise ValueError('mode770 is u8 or None')
    if type(death44_count) is not int or not 0 <= death44_count <= MASK:
        raise ValueError('Actual local18 death44 count or sentinel required')
    if mode770 == 3:
        reason = 'mode770=3:913 skips both994 calls before reading2056'
    elif isinstance(sources, EventDefinitions139) and sources.count == 0:
        reason = 'count2056=0:913 skips both994 calls'
    else:
        raise PendingHitEvents139('Nonempty/unknown913 tail event route pending')
    release = ((death44_count - 1) & MASK) <= MASK - 2
    return DamageTailEventPlan139(reason, (), release,
                                  ((death44_count * 44) & MASK) if release else None, ())
