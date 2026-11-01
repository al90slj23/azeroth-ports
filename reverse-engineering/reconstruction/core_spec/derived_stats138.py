"""Independent fixed138 stats projection with explicit physical result names.

The ordered numeric implementation is shared with the135 specification; its
acceptance on138 is established only by separately recorded fresh138 calls.
StatsInput.pool768_bits remains a semantic legacy input label. The actual138
reserve is Game764, and the physical auxiliary result is named accordingly.
"""
from .derived_stats135 import (
    StatsInput,Modifier,Adjustment,TimedRecord,TimedDefinition,LiveEffect,
    input_from_dict,recalculate as _calculate,
)


def recalculate(state:StatsInput):
    result=_calculate(state)
    result['auxiliary_bits']={('764'if key=='768'else key):value
        for key,value in result['auxiliary_bits'].items()}
    return result
