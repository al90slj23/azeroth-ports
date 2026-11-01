"""Official 0.134.0 kind1 pickup entity RNG/counter/GUID projection.

Source SHA256: 2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52.
Reviewed complete 1417/1820 WAT in evidence/death-xp0134-chain-20261101T013638.638140Z.
1417 kind1 jumps through the kind table to its common terrain/entity path,
calls 1820 once at L789, skips both kind6-only calls at L815/840, appends its
56B pickup and returns. Kind1 is not subject to the kind0/2 count/merge gates.

1820 L8..96 increments G2400 and advances G1712/1716/1720/1724. Its angular
sampler constructs a 23-bit unit value, multiplies by f32(2*pi), and rejects
angle>=f32(2*pi). The greatest unit is 0x3f7ffffe, giving maximum angle
0x40c90fd9, strictly below upper 0x40c90fdb. Thus every uint32 output accepts
and this successful kind1 path consumes exactly one additional draw.

The 37-function direct-call closure of 1820 has no imports and no other
1712/1716/1720/1724 offset accesses. Its only indirect calls are in 49501 and
172316 panic/OOM paths that terminate with unreachable. The projection assumes
valid distinct buffers and successful allocations/normal return, as with the
controlled original fixture; panic, memory corruption and pointer aliasing are
not modeled. It does not run original code or implement other entity kinds.

The other kind1 callees rooted at38322/49502/29630/23181/65336 have a26-function
closure with no imports or RNG offsets and the same terminating panic/OOM
indirect calls. Thus unresolved placement/serialization does not add a normal
RNG branch to the successful kind1 path.
"""
from dataclasses import dataclass

from . import binary32 as f
from .rng import next_u32_words

SOURCE_SHA256 = '2e86455ac39028dd45fc224b30e2e6a46ad5746bb44ce894c54e1a051bb73d52'
FUNCTION_1417_BODY_SHA256 = '22263d2e42d74ce26922ec8dac69a3f7dc4c8d3bedbdef679dcedb201f5b7c12'
FUNCTION_1820_WAT_SHA256 = '1444b9aff17952f3da4af631047c93ec23fcfcc2b1525e1c7d430d210f9ba2bc'
FUNCTION_1820_BODY_SHA256 = '52a8b8efc03afa7ac00ef0079dbf6eabfa333a001bcffb8c55313cbf3205b473'
ENTITY_GUID_PREFIX = 0xf110000000000000
KIND1_VISUAL_ID = 9004
KIND1_DESCRIPTOR_MODEL = 2614
KIND1_SCALE_BITS = 0x3f19999a
TWO_PI_BITS = 0x40c90fdb
MAX_ANGLE_BITS = 0x40c90fd9


def _u32(value):
    if type(value) is not int or not 0 <= value <= f.MASK:
        raise ValueError('Expected an unsigned 32-bit integer')
    return value


class UnsupportedEntityKind(ValueError):
    """Other 1417/entity branches remain pending rather than consuming no RNG."""


@dataclass(frozen=True)
class Kind1EntityProjection:
    rng_state: tuple
    draws: int
    counter2400: int
    guid: int
    output_u32: int
    unit23_bits: int
    angle_bits: int
    half_angle_bits: int
    known_keyed_words: tuple
    pending: tuple
    status: str = 'pending_entity_consumers'
    stage: str = '1417_kind1_1820_rng_counter_guid'


def project_kind1_entity(state, counter2400, *, kind=1):
    """Project one successful 1417(kind1)->1820 consumer, after reward draws.

    Call only for an actual kind1 request. Supply the state after 914's
    probability/bounded draws and the counter
    after any earlier kind0 pickup append. This includes the one extra draw
    missing from death_loot134.direct_rng_state. It does not represent any
    later914 callbacks. The returned GUID is a proposed entity/pickup GUID;
    actual buffers, tree, messages, geometry and pickup mutation stay pending.

    known_keyed_words are recovered raw (u16 key,u32 value) writes in1820,
    not a complete physical keyed tree. Rotation keys12/13 require original
    f32 helpers11428/11503 of half_angle_bits and remain pending. Position
    keys15/16/17 require resolved geometry and also remain pending.
    """
    _u32(kind)
    if kind != 1:
        raise UnsupportedEntityKind('Only1417 kind1 entity RNG is recovered; other kinds pending')
    _u32(counter2400)
    state = tuple(state)
    if len(state) != 4:
        raise ValueError('RNG state must contain exactly four uint32 words')
    for word in state:
        _u32(word)
    counter = (counter2400 + 1) & f.MASK
    output, state = next_u32_words(state)
    # Original uses all 23 mantissa bits here, unlike914's high24 sampler.
    unit = f.add((output >> 9) | 0x3f800000, 0xbf800000)
    angle = f.mul(unit, TWO_PI_BITS)
    # Preserve the original strict acceptance guard. The stated maximum
    # proves the rejection arm is unreachable for every uint32 input.
    if not f.to_float(angle) < f.to_float(TWO_PI_BITS):
        raise RuntimeError('Reviewed uint32 angular sampler invariant differs')
    half_angle = f.mul(f.add(angle, 0), 0x3f000000)
    guid = (ENTITY_GUID_PREFIX | ((KIND1_VISUAL_ID & 0xffffff) << 24)
            | (counter & 0xffffff))
    known = ((0, guid & f.MASK), (1, guid >> 32), (2, 33),
             (3, KIND1_VISUAL_ID), (4, KIND1_SCALE_BITS),
             (8, KIND1_DESCRIPTOR_MODEL), (9, 0), (14, 1),
             (18, f.add(angle, 0)), (20, 35), (21, 5))
    pending = (
        '1417 region/radial placement and world-height resolution',
        '1820 keyed-tree allocation/writes including rotation12/13 and position15/16/17',
        '1820 message26970/50797, message-vector growth, count and tree cleanup',
        '1417 actual56B kind1 append, visual9004, aux vector and allocation',
        'Other entity kinds, panic/OOM and later914 effects are outside this projection',
    )
    return Kind1EntityProjection(state, 1, counter, guid, output, unit, angle,
                                 half_angle, known, pending)
