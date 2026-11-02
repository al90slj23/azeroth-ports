"""Independent current139 scheduled-spell queue38553.

This is the complete finite-size queue/launch consumer, not its natural
producer or a complete884 frame. Opaque cells move with their physical row.
"""
from dataclasses import dataclass
import struct
from . import binary32 as f


class PendingFrameSystem139(NotImplementedError):
    pass


def _u(value,bits=32):
    if type(value)is not int or not 0<=value<1<<bits:
        raise ValueError('Explicit unsigned word required')
    return value


def _read(row,offset,size=4):
    cells=row[offset:offset+size]
    if len(cells)!=size or None in cells:
        raise PendingFrameSystem139('Scheduled consumer would read Unknown cells')
    return int.from_bytes(bytes(cells),'little')


def _packed(guid):
    raw=_u(guid,64).to_bytes(8,'little')
    return bytes([sum(1<<j for j,b in enumerate(raw)if b)])+bytes(b for b in raw if b)


@dataclass(frozen=True)
class ScheduledSpellVector139:
    storage: tuple
    count: int

    def __post_init__(self):
        _u(self.count)
        if type(self.storage)is not tuple or not 0<=self.count<=len(self.storage)<=512:
            raise ValueError('Explicit bounded complete32B backing required')
        for row in self.storage:
            if type(row)is not tuple or len(row)!=32:
                raise ValueError('Every backing slot is exactly32 cells')
            for b in row:
                if b is not None:_u(b,8)


@dataclass(frozen=True)
class ScheduledSpellResult139:
    vector: ScheduledSpellVector139
    packets: tuple
    removed_indices: tuple


def scheduled_launch139(guid,spell,xyz):
    """10490 location variant8: two packedGUIDs, mask64 and rawXYZ."""
    _u(spell)
    if type(xyz)is not tuple or len(xyz)!=3:
        raise ValueError('Exactly three original binary32 words required')
    for x in xyz:_u(x)
    guid=_packed(guid)
    payload=guid+guid+struct.pack('<I',spell)+b'\0\1\0\0\x40\0'+struct.pack('<3I',*xyz)
    return 306,32 if len(payload)<=32 else 64,payload.hex()


def tick_scheduled_spells139(vector,now_bits):
    """Stable remove when due<=now, including the original NaN predicate.

    Capacity and stale tail remain unchanged; only active count decreases.
    No phase, NPC, ownership, RNG or spell-database lookup is consulted.
    """
    if not isinstance(vector,ScheduledSpellVector139):
        raise TypeError('Actual scheduled32 owner required')
    _u(now_bits)
    rows=list(vector.storage);count=vector.count;i=0;packets=[];removed=[]
    while i<count:
        row=rows[i]
        if not f.to_float(_read(row,8))<=f.to_float(now_bits):
            i+=1
            continue
        guid=_read(row,0,8);spell=_read(row,12);xyz=tuple(_read(row,16+4*j)for j in range(3))
        # Copy the whole physical row, including unconsumed +28..31 cells.
        for j in range(i,count-1):rows[j]=rows[j+1]
        count-=1;removed.append(i);packets.append(scheduled_launch139(guid,spell,xyz))
    return ScheduledSpellResult139(ScheduledSpellVector139(tuple(rows),count),tuple(packets),tuple(removed))
