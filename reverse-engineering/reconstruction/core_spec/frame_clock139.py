"""Current139 owner clock, independently implemented from884's first prefix.

This pure module reads no original code, snapshot, runtime output or files.
The selective comparisons deliberately preserve negative zero and NaN rather
than using a host clamp/min/max helper. NaN payload bits are not contractual.
Game2352 advancement is a separately admitted phase1 arithmetic operation;
neither owner sampling nor that arithmetic implements the full App/frame884.
"""
from dataclasses import dataclass
import math,struct
from . import binary32 as f

MASK64=(1<<64)-1
def _u64(v):
    if type(v)is not int or not 0<=v<=MASK64:raise ValueError('Explicitu64 bits required')
    return v
def float64(bits):return struct.unpack('<d',struct.pack('<Q',_u64(bits)))[0]
def bits64(value):return struct.unpack('<Q',struct.pack('<d',value))[0]
def classification64(bits):
    v=float64(bits)
    return'nan'if math.isnan(v)else'infinity'if math.isinf(v)else'zero'if v==0 else'finite'
def classification32(bits):
    if f.is_nan(bits):return'nan'
    if f.is_inf(bits):return'infinity'
    return'zero'if bits&0x7fffffff==0 else'finite'

@dataclass(frozen=True)
class FrameClock139:
    tag_u64:int
    previous_timestamp_bits:int|None
    def __post_init__(self):
        _u64(self.tag_u64)
        if self.previous_timestamp_bits is not None:_u64(self.previous_timestamp_bits)

@dataclass(frozen=True)
class FrameClockResult139:
    state:FrameClock139
    dt_bits:int
    previous_timestamp_consumed:bool

def sample_frame_clock139(state,now_bits):
    if not isinstance(state,FrameClock139):raise TypeError('Typedownerclock required')
    now=float64(now_bits);dt=0
    if state.tag_u64==1:
        if state.previous_timestamp_bits is None:raise ValueError('Tag1 consumespreviousf64timestamp')
        delta=now-float64(state.previous_timestamp_bits)
        lower=0.0 if delta<0.0 else delta
        selected=0.1 if lower>0.1 else lower
        dt=f.from_float(selected)
    return FrameClockResult139(FrameClock139(1,now_bits),dt,state.tag_u64==1)

def advance_game_clock139(game_clock_bits,dt_bits,*,phase2587):
    """884 phase1 does f32(dt+G2352); other phases preserve this field.

    This is not an assertion that no other mainloop branch touches Gameclock.
    Caller must bind actual Gamevariant/phase and the canonical sampled dt.
    """
    if type(phase2587)is not int or not 0<=phase2587<=255:raise ValueError('Phasebyte required')
    for v in(game_clock_bits,dt_bits):
        if type(v)is not int or not 0<=v<=f.MASK:raise ValueError('Explicitbinary32bits required')
    return f.add(dt_bits,game_clock_bits)if phase2587==1 else game_clock_bits
