"""WIP current2181 two-owned unupgraded cleave/firstDemo2 candidate producer.

Uses current literal pool/weights and declaration kind order; no old runtime
acceptance or observation bytes. Other owned upgrades/modifiers remain Pending.
"""
from . import binary32 as f
from .rng import uniform_range_bits,next_u32_words
from .candidates139 import Candidate139,CandidateResult139,PendingCandidates139,_word,first_candidates139
from .candidates139_data import DEFINITIONS139,WARRIOR_KIT139

def second_candidates139(words, owned_records80, level=2, *, luck_bits=0, cooldown_bits=0x3f800000,
                        blocked_count2092=0, banished_count2104=0, flag275=0, flag2581=0):
    """Full2181(kind0) metadata/RNG for constructor cleave plus its class kit.

    The two counts are constructor-produced physical-owner inputs. None and
    nonempty are rejected; they are not inferred from absent model fields.
    """
    if blocked_count2092 != 0 or banished_count2104 != 0:
        raise PendingCandidates139('Nonempty/unknown blocked or banished owner')
    if len(owned_records80)==1:
        return first_candidates139(words,owned_records80,level,luck_bits=luck_bits,cooldown_bits=cooldown_bits,blocked_count2092=blocked_count2092,banished_count2104=banished_count2104,flag275=flag275,flag2581=flag2581)
    if type(owned_records80)is not tuple or len(owned_records80)!=2:raise PendingCandidates139('Only actual two-owned cleave/Demo unupgraded family')
    pointers=tuple(_word(row,0)for row in owned_records80)
    names=('cleave','demo_shout')
    if pointers!=tuple(DEFINITIONS139[name][0]for name in names):raise PendingCandidates139('Actual ordered cleave/Demo declarations required')
    for name,owned in zip(names,owned_records80):
        if type(owned)is not bytes or len(owned)!=80 or _word(owned,4)!=1:raise PendingCandidates139('Actual rank1 owned80 required')
        if any(_word(owned,k)!=0 for k in(20,32,36,40,44,48,60))or any(_word(owned,k)!=0x3f800000 for k in(16,24,28,52,56,64,68,76))or _word(owned,72)!=0:raise PendingCandidates139('Saturation/modifier/upgraded owned sources remain Pending')
        if name=='cleave'and _word(owned,12)!=0x3f800000:raise PendingCandidates139('Constructorcleave damage counter required')
        if name=='demo_shout'and _word(owned,12)!=0x3fa00000:raise PendingCandidates139('Declared firstnew Demo quality damage only')
    if cooldown_bits!=0x3f800000 or not 1<=level<=120:raise PendingCandidates139('Default cooldown and actual bounded level')
    words=tuple(words)
    pool=[(0x3fcccccd,'new',name,0)for name in WARRIOR_KIT139 if name not in names]
    pool.extend((0x3fa66666,'upgrade',name,index)for index,name in enumerate(names))
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
            kinds=([0,1]if tier==0 else[0,1,2])if name=='cleave'else[1,3]
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
