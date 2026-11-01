"""Independent official 0.134.0 kind 1 award arithmetic (complete 28795).

Original SHA256: 2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52.
This module does not load or call the original. It projects logical queue and
keyed-state writes, not heap addresses, tree allocation, wire serialization or
account persistence. The caller retains the 2862 gate / reverse removal order.
All floating arguments and intermediates are IEEE754 binary32 words.
"""
from dataclasses import dataclass, replace

from . import binary32 as f
from .progression134 import round_85718_bits, trunc_sat_u32

ONE = 0x3f800000
REGION_FACTOR = 0x3f333333          # f32 .7
MEMBER_FACTOR = 0x3e9fbe77          # f32 .312, WAT 0x1.3f7ceep-2
GOLD_PLAYER_KEY = 1176


def _uint(value, width=32):
    if type(value) is not int or not 0 <= value < 1 << width:
        raise ValueError('Expected uint' + str(width))
    return value


def mode_multiplier_bits(mode, member_count=1, *, region_index=None):
    """Exact 28795 mode branch; region lookup is supplied, never guessed.

    Modes other than 1 retain multiplier 1. Mode 1 requires the actual 38322
    index. Member count 0 wraps to 0xffffffff before conversion to binary32.
    """
    _uint(mode, 8)
    _uint(member_count)
    if mode != 1:
        return ONE
    if region_index is None:
        raise ValueError('Mode 1 requires the resolved original 38322 region index')
    _uint(region_index)
    coefficient = REGION_FACTOR if region_index < 3 else ONE
    members = f.from_u32((member_count - 1) & f.MASK)
    denominator = f.add(f.mul(f.mul(coefficient, members), MEMBER_FACTOR), ONE)
    return f.div(ONE, denominator)


def currency_award(amount, multiplier_bits, mode=0, member_count=1, *, region_index=None):
    """Return the award and intermediate bits of 28795, including zero.

    There is no XP-style minimum 1 or NaN replacement. Positive overflow
    saturates to 0xffffffff; NaN, negative values and negative infinity to 0.
    The later two integer additions and copper multiplication wrap normally.
    """
    _uint(amount)
    _uint(multiplier_bits)
    mode_bits = mode_multiplier_bits(mode, member_count, region_index=region_index)
    scaled_bits = f.mul(mode_bits, f.mul(multiplier_bits, f.from_u32(amount)))
    rounded_bits = round_85718_bits(scaled_bits)
    return {'amount': trunc_sat_u32(rounded_bits), 'mode_multiplier_bits': mode_bits,
            'scaled_bits': scaled_bits, 'rounded_bits': rounded_bits}


@dataclass(frozen=True)
class CurrencyState:
    """Logical 28795 fields; account progress is deliberately a separate owner.

    gold = G1544 available current-run currency; earned = G1100 collected tally.
    queue entries are (peer_u32, unmodified_base_amount_u32), each exactly 8B.
    player_fields is the logical G2468/2472 u16->u32 tree, sorted by key.
    """
    gold: int = 0
    earned: int = 0
    multiplier_bits: int = ONE             # G1408
    mode: int = 0                         # G2574
    local_peer: int = 0                   # G2520
    member_count: int = 1                 # G2532
    region_index: int | None = None       # explicitly resolved 38322 result
    queue: tuple = ()
    queue_capacity: int = 0               # G2148, only used in nonzero mode
    player_fields: tuple = ()

    def __post_init__(self):
        for value in (self.gold, self.earned, self.multiplier_bits,
                      self.local_peer, self.member_count, self.queue_capacity):
            _uint(value)
        _uint(self.mode, 8)
        if self.region_index is not None:
            _uint(self.region_index)
        queue = tuple(tuple(row) for row in self.queue)
        for row in queue:
            if len(row) != 2:
                raise ValueError('Currency queue entry must be peer and base amount')
            for word in row:
                _uint(word)
        if len(queue) > self.queue_capacity:
            raise ValueError('Currency queue count exceeds capacity')
        player_fields = tuple(tuple(row) for row in self.player_fields)
        if any(len(row) != 2 for row in player_fields):
            raise ValueError('Player field must be u16 key and u32 value')
        for key, value in player_fields:
            _uint(key, 16)
            _uint(value)
        if tuple(sorted(player_fields)) != player_fields or len(dict(player_fields)) != len(player_fields):
            raise ValueError('Player fields must have unique sorted u16 keys')
        object.__setattr__(self, 'queue', queue)
        object.__setattr__(self, 'player_fields', player_fields)


@dataclass(frozen=True)
class CurrencyResult:
    state: CurrencyState
    status: str
    award: int | None = None
    mode_multiplier_bits: int | None = None
    scaled_bits: int | None = None
    rounded_bits: int | None = None
    queue_append: tuple | None = None
    key_update: tuple | None = None
    missing_key_insert: bool = False
    pending: tuple = ()


def apply_currency(state, amount):
    """Project complete 28795 arithmetic/logical writes in the original order.

    Missing mode-1 region returns pending_domain with the original input.
    Successful projections expose physical allocation/wire obligations as
    pending side effects; none are called or silently simulated as a no-op.
    No account fields or RNG state are read or written by 28795.
    """
    if not isinstance(state, CurrencyState):
        raise TypeError('Expected CurrencyState')
    _uint(amount)
    if state.mode == 1 and state.region_index is None:
        return CurrencyResult(state, 'pending_domain', pending=(
            '28795 mode1 requires the resolved 38322 region index before queue mutation',))
    numeric = currency_award(amount, state.multiplier_bits, state.mode,
                             state.member_count, region_index=state.region_index)
    append = (state.local_peer, amount) if state.mode else None
    queue = state.queue + ((append,) if append is not None else ())
    # 65326 is the original shared 8B reserve: max(4, 2*old_capacity).
    capacity = state.queue_capacity
    pending = []
    if append is not None:
        if len(state.queue) == capacity:
            capacity = max(4, capacity * 2)
            if capacity > f.MASK:
                return CurrencyResult(state, 'pending_domain', pending=(
                    '65326 queue capacity overflow/allocation trap boundary is pending',))
            pending.append('65326/56191 physical 8B queue allocation or reallocation')
        pending.append('currency queue consumption / transport remains outside28795')
    gold = (state.gold + numeric['amount']) & f.MASK
    earned = (state.earned + numeric['amount']) & f.MASK
    key_update = (GOLD_PLAYER_KEY, (gold * 10000) & f.MASK)
    player_fields = dict(state.player_fields)
    missing = GOLD_PLAYER_KEY not in player_fields
    player_fields[GOLD_PLAYER_KEY] = key_update[1]
    if missing:
        pending.append('3735 physical keyed-tree insertion/allocation')
    if missing or (append is not None and len(state.queue) == state.queue_capacity):
        pending.append('allocation/invariant-failure indirect panic handlers172316/49501 remain pending')
    pending.append('later keyed-player-state wire update / flush is outside28795')
    result = replace(state, gold=gold, earned=earned, queue=queue,
                     queue_capacity=capacity, player_fields=tuple(sorted(player_fields.items())))
    return CurrencyResult(result, 'core_projection', numeric['amount'],
        numeric['mode_multiplier_bits'], numeric['scaled_bits'], numeric['rounded_bits'],
        append, key_update, missing, tuple(pending))
