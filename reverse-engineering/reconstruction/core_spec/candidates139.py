"""Current1392181 first HumanWarrior level-up candidate metadata.

Resolved current139 class/ability bytes are literal data. This initial domain
requires the constructor cleave's unchanged upgrade counters and empty source
lists. UI strings, physical allocations and notifications are not fabricated.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .rng import uniform_range_bits, next_u32_words
from .candidates139_data import DEFINITIONS139, WARRIOR_KIT139


class PendingCandidates139(NotImplementedError):
    pass


@dataclass(frozen=True)
class Candidate139:
    variant: str
    tier: int
    ability_id: str
    owned_index: int = 0
    kinds: tuple = ()
    gold: int = 0


@dataclass(frozen=True)
class CandidateResult139:
    candidates: tuple
    rng_words: tuple
    draws: int


def _word(row, at):
    return struct.unpack_from('<I', row, at)[0]


def first_candidates139(words, owned_records80, level=2, *, luck_bits=0, cooldown_bits=0x3f800000,
                        blocked_count2092=0, banished_count2104=0, flag275=0, flag2581=0):
    """Full2181(kind0) metadata/RNG for constructor cleave plus its class kit.

    The two counts are constructor-produced physical-owner inputs. None and
    nonempty are rejected; they are not inferred from absent model fields.
    """
    if blocked_count2092 != 0 or banished_count2104 != 0:
        raise PendingCandidates139('Nonempty/unknown blocked or banished owner')
    if type(owned_records80) is not tuple or len(owned_records80) != 1:
        raise PendingCandidates139('First constructor-owned cleave domain')
    owned = owned_records80[0]
    if type(owned) is not bytes or len(owned) != 80 or _word(owned, 0) != DEFINITIONS139['cleave'][0]:
        raise PendingCandidates139('Resolved constructor cleave80 required')
    if any(_word(owned, off) != 0 for off in (20, 32, 36, 40, 44, 48)) or _word(owned, 16) != 0x3f800000:
        raise PendingCandidates139('Nonconstructor cleave upgrade saturation pending')
    if cooldown_bits != 0x3f800000 or not 1 <= level <= 120:
        raise PendingCandidates139('Default cooldown and bounded first growth level')
    words = tuple(words)
    pool = [(0x3fcccccd, 'new', name, 0) for name in WARRIOR_KIT139 if name != 'cleave']
    pool.append((0x3fa66666, 'upgrade', 'cleave', 0))
    selected = []
    draws = 0

    def sample(high):
        nonlocal words, draws
        result = uniform_range_bits(words, 0, high)
        words, draws = result.state, draws + result.draws
        return result.bits

    count = 3 if flag275 == 0 or flag2581 & 1 else 4
    while pool and len(selected) < count:
        total = 0x80000000
        for entry in pool:
            total = f.add(total, entry[0])
        pick = sample(total)
        at = len(pool) - 1
        for index, entry in enumerate(pool):
            if f.to_float(pick) < f.to_float(entry[0]):
                at = index
                break
            pick = f.sub(pick, entry[0])
        selected.append(pool.pop(at))
    step = f.mul(f.from_u32(level), 0x3c23d70a)
    step = step if f.to_float(step) < f.to_float(0x3e99999a) else 0x3e99999a
    factor = f.add(f.add(luck_bits, 0x3f800000), step)
    square = f.mul(factor, factor)
    weights = (0x42700000, f.mul(factor, 0x41c80000), f.mul(square, 0x41200000),
               f.mul(f.mul(factor, square), 0x40800000), f.mul(square, square))
    high = weights[0]
    for weight in weights[1:]:
        high = f.add(high, weight)
    result = []
    for _, variant, name, index in selected:
        pick = sample(high)
        tier = 0
        for number, weight in enumerate(weights):
            if f.to_float(pick) < f.to_float(weight):
                tier = number
                break
            pick = f.sub(pick, weight)
        kinds = []
        if variant == 'upgrade':
            kinds = [0, 1] if tier == 0 else [0, 1, 2]
            for length in range(len(kinds), 1, -1):
                zone = ((length << (32 - length.bit_length())) - 1) & f.MASK
                for _ in range(10000):
                    raw, words = next_u32_words(words)
                    draws += 1
                    product = raw * length
                    if product & f.MASK <= zone:
                        break
                else:
                    raise RuntimeError('Bounded current139 shuffle')
                at = product >> 32
                kinds[length - 1], kinds[at] = kinds[at], kinds[length - 1]
            kinds = kinds[:2 if tier == 4 else 1]
        result.append(Candidate139(variant, tier, name, index, tuple(kinds)))
    return CandidateResult139(tuple(result), tuple(words), draws)
