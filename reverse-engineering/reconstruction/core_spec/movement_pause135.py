"""Independent26200 NPC movement-snapshot sequence projection.

35514 pause and25472 resume each consume the same ordered collector. Auxiliary
112B motions and88B claims remain explicit unknown sources, never assumed empty.
This pure consumer does not mutate NPC records, phase, RNG, or packet bytes.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f
from .record_cells135 import cells135,u32,u64


class UnresolvedMovementPause135(NotImplementedError):pass


@dataclass(frozen=True)
class MovementSequence135:
    count:int
    guids:tuple


def moving_sequence_delta(records,now_bits,*,auxiliary_motions=None,claims=None):
    """One35514/25472 invocation: ordered NPC GUIDs and wrapping-seq delta.

    Every complete424B record is retained by the caller. Only marker==0,
    duration344>0 and f32(duration344+start340)>now2352 emit a snapshot. There
    is no GUID deduplication, ownership filter, family check, or record update.
    """
    if type(now_bits)is not int or not 0<=now_bits<=f.MASK:
        raise ValueError('Explicit rawbinary32 clock required')
    if type(records)is not tuple:raise TypeError('Ordered complete424B record tuple required')
    for name,source in(('auxiliary_motions',auxiliary_motions),('claims',claims)):
        if type(source)is not tuple or source:
            raise UnresolvedMovementPause135('Explicit empty '+name+' source snapshot required')
    guids=[]
    for value in records:
        raw=cells135(value,424)
        if len(raw)!=424:raise ValueError('Complete424B NPC source required')
        marker=u32(raw,0,'26200 marker');start=u32(raw,340,'26200 movement start');duration=u32(raw,344,'26200 movement duration')
        if marker==0 and f.to_float(duration)>0 and f.to_float(f.add(duration,start))>f.to_float(now_bits):
            guids.append(u64(raw,112,'26200 moving GUID'))
    return MovementSequence135(len(guids),tuple(guids))
