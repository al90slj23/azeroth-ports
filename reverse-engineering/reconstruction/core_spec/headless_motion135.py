"""Explicit motion-only scalar owner for the fixed135 headless controller.

This does not restore original Game bytes. Only constructor-proven motion
flags and later motion writes are retained. Current player position, clock,
identity and action sequence are bound from the canonical controller at each
call boundary. Unrestored queue/allocation words stay unknown.
"""
from dataclasses import dataclass

from .record_cells135 import cells135, put_u32, put_u64, u32
from .initial_state135_data import ZONE_ENTRIES


#1560 local3 is a temporary frame; Game starts at local3+88. The actual
#zero stores are frame504/528/536/544/552/1832/1852 and frame2584(i64).
ZERO_WORDS135=(416,440,448,456,464,1744,1764,2496,2500)
MOTION_WORDS135=(416,420,424,428,432,436,440,444,448,452,456,460,464,
    1428,1744,1748,1752,1756,1760,1764,1768,1772,1776,1780,2496,2500)


@dataclass(frozen=True)
class HeadlessMotionOwner135:
    cells: tuple

    def __post_init__(self):
        cells135(self.cells,2592)
        allowed={j for o in MOTION_WORDS135 for j in range(o,o+4)}
        if any(v is not None for j,v in enumerate(self.cells)if j not in allowed):
            raise ValueError('Motion owner cannot retain another canonical scalar source')

    @classmethod
    def from_empty_constructor(cls,zone):
        if type(zone)is not int or not 0<=zone<len(ZONE_ENTRIES):
            raise ValueError('Explicit fixed135 region required')
        raw=[None]*2592
        for offset in ZERO_WORDS135:put_u32(raw,offset,0)
        put_u32(raw,1428,ZONE_ENTRIES[zone][3])
        return cls(tuple(raw))

    def bind(self,*,player_xyz,now_bits,source_id,action_sequence1644,
            player_action_tag416,phase2587,local_peer2528,flags2583):
        if u32(self.cells,416,'Motion pending correction')!=player_action_tag416:
            raise ValueError('Motion/action416 ownership disagrees with controller')
        raw=list(self.cells)
        for offset,value in ((2352,now_bits),(1644,action_sequence1644),(2528,local_peer2528)):
            put_u32(raw,offset,value)
        for j,value in enumerate(player_xyz):put_u32(raw,1416+4*j,value)
        put_u64(raw,1336,source_id)
        for offset,value in ((2587,phase2587),(2583,flags2583)):
            if type(value)is not int or not 0<=value<=255:raise ValueError('Explicit motion control byte')
            raw[offset]=value
        return tuple(raw)

    def adopt(self,result_cells):
        result=cells135(result_cells,2592);raw=[None]*2592
        for offset in MOTION_WORDS135:raw[offset:offset+4]=result[offset:offset+4]
        return HeadlessMotionOwner135(tuple(raw))
