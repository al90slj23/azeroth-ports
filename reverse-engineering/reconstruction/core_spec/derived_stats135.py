"""Independent 0.135.1 derived-stat projection, with armor cap retained.

The ordered arithmetic is reused from the independently implemented134 model;
the new1512 additionally stores the armor cap. Physical offsets are explicit,
not inferred from one uniform relocation. StatsInput's numeric field labels are
legacy semantic input names: pool1532 is the first shield pool, for example.
No original binary/data/index is read by this production module. Unknown real
equipment/talent/effect producers remain caller-supplied snapshots.
"""
from .derived_stats134 import (
    StatsInput, Modifier, Adjustment, TimedRecord, TimedDefinition, LiveEffect,
    input_from_dict, recalculate as _recalculate134,
)
from .binary32 import add, mul, from_u32, to_float


DERIVED_OFFSETS = {
    1360:1536, 1364:1540, 1368:1544, 1372:1548, 1376:1552, 1380:1556,
    1384:1560, 1388:1564, 1392:1568, 1396:1576, 1400:1580, 1404:1584,
    1408:1588, 1412:1592, 1416:1596, 1420:1600, 1424:1604, 1428:1608,
    1432:1612, 1436:1616, 1440:1620, 1444:1624,
}
AUXILIARY_OFFSETS = {1532:1444, 1536:1448, 1348:1348, 768:768}


def armor_cap_bits(state: StatsInput):
    """Reproduce the cap accumulator retained at new G1572.

    The original resets this accumulator to0.6 after the adjustment pass.
    Item tag27 and appended timed tag27 then increase it in that order.
    Validation/range checks are supplied by recalculate's shared full pass.
    """
    cap = 0x3f19999a
    for entry in state.item_modifiers:
        if entry.tag & 255 == 27:
            cap = add(cap, entry.value_bits)
    for record in state.timed_records:
        if to_float(record.expires_bits) <= to_float(state.now_bits):
            continue
        if record.definition_index >= len(state.timed_definitions):
            continue
        definition = state.timed_definitions[record.definition_index]
        if definition.kind == 27 and definition.modifier_tag & 255 == 27:
            cap = add(cap, mul(definition.value20_bits, from_u32(record.stack_count)))
    return cap


def recalculate(state: StatsInput):
    """Return all23 new derived words plus HP/pools/object/speed projections."""
    result = _recalculate134(state)
    result['derived_bits'] = {
        str(DERIVED_OFFSETS[int(key)]): value
        for key, value in result['derived_bits'].items()
    }
    result['derived_bits']['1572'] = armor_cap_bits(state)
    result['derived_bits'] = dict(sorted(result['derived_bits'].items(), key=lambda x: int(x[0])))
    result['auxiliary_bits'] = {
        str(AUXILIARY_OFFSETS[int(key)]): value
        for key, value in result['auxiliary_bits'].items()
    }
    return result
