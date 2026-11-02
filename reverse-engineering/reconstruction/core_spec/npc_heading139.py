"""Independent13935202 atan /43076 atan2 used by actualNPC1586.

Ordered expressions derive from prior independent atan work and are rebound
against full139 bodies and four fresh tables14426512/528/544/560. No old model
or old acceptance is imported; runtime reads no original or observation.
DynamicNPC comparisons cover finite coordinate differences; nonfinite helper
branches are static specifications until separately tested.
"""
from . import binary32 as f

HI=(0x3eed6338,0x3f490fda,0x3f7b985e,0x3fc90fda)
LO=(0x31ac3769,0x33222168,0x33140fb4,0x33a22168)
INF_QUADRANTS=(0x3f490fdb,0xbf490fdb,0x4016cbe4,0xc016cbe4)
XINF_QUADRANTS=(0,0x80000000,0x40490fdb,0xc0490fdb)
ONE=0x3f800000
PI=0x40490fdb
PI2=0x3fc90fdb
PI_LO=0x33bbbd2e


def atan_bits(bits):
    """Original13935202 polynomial/range reduction, including special words."""
    if type(bits)is not int or not 0<=bits<=f.MASK:raise ValueError('Expected binary32 word')
    absolute=bits&0x7fffffff
    if absolute>1283457023:
        if f.is_nan(bits):return bits
        return 0x3fc90fda|(bits&f.SIGN)
    value=bits;index=-1
    if absolute>=1054867456:
        if absolute<1066926080:
            if absolute>=1060110336:
                value=f.div(f.add(absolute,0xbf800000),f.add(absolute,ONE));index=1
            else:
                value=f.div(f.add(f.add(absolute,absolute),0xbf800000),f.add(absolute,0x40000000));index=0
        elif absolute<1075576832:
            value=f.div(f.add(absolute,0xbfc00000),f.add(f.mul(absolute,0x3fc00000),ONE));index=2
        else:
            value=f.div(0xbf800000,absolute);index=3
    elif absolute<964689920:
        # The original subnormal multiplication is discarded; exceptions are
        # not part of WASM's observable numerical state.
        return bits
    z=f.mul(value,value);w=f.mul(z,z)
    second=f.mul(w,f.add(f.mul(w,0xbdda1247),0xbe4cca98))
    first=f.mul(z,f.add(f.mul(w,f.add(f.mul(w,0x3d7cac25),0x3e11f50d)),0x3eaaaaa9))
    product=f.mul(value,f.add(second,first))
    if index<0:return f.sub(value,product)
    result=f.sub(HI[index],f.sub(f.sub(product,LO[index]),value))
    return result^(bits&f.SIGN)


def atan2_bits(y,x):
    """Original13943076 signed-quadrant arithmetic in the exact select order."""
    if any(type(v)is not int or not 0<=v<=f.MASK for v in(y,x)):
        raise ValueError('Expected binary32 words')
    if f.is_nan(y)or f.is_nan(x):return f.add(y,x)
    if x==ONE:return atan_bits(y)
    quadrant=((x>>30)&2)|(y>>31)
    ay,ax=y&0x7fffffff,x&0x7fffffff
    if ay==0:
        if quadrant==2:return PI
        if quadrant==3:return PI|f.SIGN
        return y
    if ax==0:return PI2|(y&f.SIGN)
    if ax==f.INF:
        return INF_QUADRANTS[quadrant]if ay==f.INF else XINF_QUADRANTS[quadrant]
    if ay==f.INF or ((ax+218103808)&f.MASK)<ay:
        return PI2|(y&f.SIGN)
    angle=0 if quadrant&2 and ((ay+218103808)&f.MASK)<ax else atan_bits(f.div(y,x)&0x7fffffff)
    if quadrant==0:return angle
    if quadrant==1:return angle^f.SIGN
    if quadrant==2:return f.sub(PI,f.add(angle,PI_LO))
    return f.add(f.add(angle,PI_LO),PI|f.SIGN)
