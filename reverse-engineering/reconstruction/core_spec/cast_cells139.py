"""Knownness-preserving current139 normal-target cleave adapter.

The external records retain every None. Only the declared semantic read view
is materialized for the frozen bytes-based cast implementation. Two private
opaque completions self-check that no inactive byte affects results; this is
model conservation, not a second original experiment or an OS read audit.
"""
from dataclasses import dataclass, replace
from .cast139 import CleaveState139, cast_cleave139
from .record_cells135 import cells135, u32, u64, UnknownRecordRead135

# Complete semantic unit reads of the admitted normal/no-proc/nonlethal path.
# Linked Q32 and inactive enum payloads are not read under header64/40/244=-1.
READ32 = (0,40,64,144,148,152,156,160,164,244,288,316,320,328,
          332,340,344,368,372,380,416,420)


@dataclass(frozen=True)
class CleaveCellsResult139:
    empty_unit_state: CleaveState139
    records432_cells: tuple
    success: int
    selected_ids: tuple
    base_damage_bits: int
    hits: tuple
    owned80: bytes
    launch306_hex: str | None
    changed_known_offsets: tuple
    private_completion_selfcheck_count: int = 2


def cast_cleave_cells139(empty_unit_state, records432_cells, definition, owned80):
    if not isinstance(empty_unit_state, CleaveState139) or empty_unit_state.combat.units432:
        raise TypeError('An explicit typed scalar state with no duplicate unit owner is required')
    if type(records432_cells) is not tuple or len(records432_cells)>64:
        raise ValueError('Bounded explicit ordered432B cell records required')
    rows = [tuple(cells135(row,432)) for row in records432_cells]
    for row in rows:
        for offset in READ32:
            u32(row,offset,'cast139 normal semantic read')
        u64(row,112,'cast139 GUID')
        if row[424] is None:
            raise UnknownRecordRead135(424,1,'cast139 classification')
    outcomes=[]
    for opaque in (0xa5,0x5a):
        carriers=tuple(bytes(opaque if value is None else value for value in row)for row in rows)
        state=replace(empty_unit_state,combat=replace(empty_unit_state.combat,units432=carriers))
        result=cast_cleave139(state,definition,owned80)
        final=[];changed=[]
        for index,(prior,carrier,after) in enumerate(zip(rows,carriers,result.state.combat.units432,strict=True)):
            assert len(after)==432
            writes=tuple(i for i,(a,b)in enumerate(zip(carrier,after))if a!=b)
            if any(not 288<=i<292 for i in writes):
                raise NotImplementedError('Knownness adapter requires a new declared write contract')
            projected=list(prior)
            for offset in writes:
                assert prior[offset] is not None
                projected[offset]=after[offset]
            assert all(projected[i] is None for i,value in enumerate(prior)if value is None)
            final.append(tuple(projected));changed.append(writes)
        scalar=replace(result.state,combat=replace(result.state.combat,units432=()))
        outcomes.append(CleaveCellsResult139(scalar,tuple(final),result.success,
            result.selected_ids,result.base_damage_bits,result.hits,result.owned80,
            result.launch306_hex,tuple(changed)))
    if outcomes[0]!=outcomes[1]:
        raise NotImplementedError('An opaque record byte influenced the recovered cast projection')
    return outcomes[0]
