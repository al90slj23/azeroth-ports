"""Ordered binary32 exp and the two fixed-base endless powers used by spawns.

These independently implement the mathematical algorithms observed in135
26361/6449. No original runtime/body is loaded. The power API deliberately
accepts only actual spawn bases1.22/1.096; it is not a generic powf replacement.
"""
from fractions import Fraction
import math
from . import binary32 as f
from .binary32_sqrt import sqrt_bits


def hx(text):return f.from_float(float.fromhex(text))
ONE=0x3f800000


def scale2(value,n):
    if f.is_nan(value) or f.is_inf(value) or f.is_zero(value):return value
    if n>512:return (value&f.SIGN)|f.INF
    if n<-512:return value&f.SIGN
    return f._encode(f._fraction(value)*(Fraction(2)**n),value&f.SIGN)


def exp_bits(x):
    """Original26361 numerical projection, including finite under/overflow."""
    a=x&0x7fffffff;negative=bool(x&f.SIGN)
    if a>=1118743632:
        if a>f.INF:return x
        if a>1118925335:
            if not negative:return f.mul(x,hx('0x1p127'))
            if a>1120924084:return 0
    if a<=1051816472:
        if a<=956301312:return f.add(x,ONE)
        k=0;hi=x;lo=0
    else:
        if a<=1065686418:k=-1 if negative else 1
        else:
            rounded=f.add(f.mul(x,hx('0x1.715476p0')),hx('-0x1p-1' if negative else '0x1p-1'))
            k=int(f.to_float(rounded))
        ki=f.from_float(k)
        hi=f.add(x,f.mul(ki,hx('-0x1.62e4p-1')))
        lo=f.mul(ki,hx('0x1.7f7d1cp-20'))
    reduced=f.sub(hi,lo)
    square=f.mul(reduced,reduced)
    correction=f.sub(reduced,f.mul(square,f.add(hx('0x1.55551ep-3'),f.mul(square,hx('-0x1.6aa42ap-9')))))
    result=f.add(f.add(hi,f.sub(f.div(f.mul(reduced,correction),f.sub(hx('0x1p1'),correction)),lo)),ONE)
    return scale2(result,k)


def _log_split(base):
    # Both actual bases lie in[1,1.2247): bp=1, exponent0, dp_hi=dp_lo=0.
    u=f.sub(base,ONE);v=f.div(ONE,f.add(base,ONE));s=f.mul(u,v);sh=s&0xfffff000
    th=(((base>>1)&0x1ffff000)+0x20400000)&f.MASK
    tl=f.sub(base,f.sub(th,ONE))
    sl=f.mul(v,f.sub(f.sub(u,f.mul(sh,th)),f.mul(sh,tl)))
    square=f.mul(s,s)
    poly=hx('0x1.a7e284p-3')
    for coefficient in ('0x1.d864aap-3','0x1.17460ap-2','0x1.555556p-2','0x1.b6db6ep-2','0x1.333334p-1'):
        poly=f.add(f.mul(square,poly),hx(coefficient))
    r=f.add(f.mul(f.mul(square,square),poly),f.mul(sl,f.add(sh,s)))
    sh2=f.mul(sh,sh);th=f.add(f.add(hx('0x1.8p1'),sh2),r)&0xfffff000
    tl=f.sub(r,f.sub(f.sub(th,hx('0x1.8p1')),sh2))
    u=f.mul(sh,th);v=f.add(f.mul(sl,th),f.mul(tl,s));ph=f.add(u,v)&0xfffff000;pl=f.sub(v,f.sub(ph,u))
    zh=f.mul(hx('0x1.ec8p-1'),ph)
    zl=f.add(f.mul(hx('0x1.ec709ep-1'),pl),f.mul(hx('-0x1.ec478cp-14'),ph))
    t1=f.add(zh,zl)&0xfffff000
    t2=f.sub(zl,f.sub(t1,zh))
    return t1,t2


def endless_power(base,y):
    """Ordered6449 for positive spawn bases and arbitrary binary32 exponents."""
    if base not in (hx('0x1.3851ecp0'),hx('0x1.189374p0')):
        raise ValueError('Only the two actual endless spawn bases are supported')
    ay=y&0x7fffffff
    if ay==0:return ONE
    if f.is_nan(y):return f.NAN
    if ay==f.INF:return 0 if y&f.SIGN else f.INF
    if ay==ONE:return f.div(ONE,base) if y&f.SIGN else base
    if y==hx('0x1p1'):return f.mul(base,base)
    if y==hx('0x1p-1'):return sqrt_bits(base)
    if ay>1291845632:return 0 if y&f.SIGN else f.INF
    t1,t2=_log_split(base)
    yh=y&0xfffff000;ph=f.mul(yh,t1);pl=f.add(f.mul(f.sub(y,yh),t1),f.mul(y,t2));z=f.add(ph,pl)
    zv=f.to_float(z)
    if zv>128:return f.INF
    if zv==128 and f.to_float(f.add(pl,hx('0x1.715478p-25')))>f.to_float(f.sub(z,ph)):return f.INF
    if zv<-150:return 0
    if zv==-150 and f.to_float(pl)<=f.to_float(f.sub(z,ph)):return 0
    n=0
    if abs(zv)>.5:
        # Bit-exact nearest integer selection; the float at that integer is exact.
        absolute=z&0x7fffffff;k=(absolute>>23)-127
        rounded=(z+(0x00800000>>(k+1)))&f.MASK
        exponent=((rounded&0x7fffffff)>>23)-127
        integer=((rounded&0x7fffff)|0x800000)>>(23-exponent)
        n=-integer if z&f.SIGN else integer
        truncated=rounded&(~(0x7fffff>>exponent)&f.MASK)
        ph=f.sub(ph,truncated)
    t=f.add(pl,ph)&0xffff8000
    u=f.mul(t,hx('0x1.62e4p-1'))
    v=f.add(f.mul(f.sub(pl,f.sub(t,ph)),hx('0x1.62e43p-1')),f.mul(t,hx('0x1.7f7d18p-20')))
    zz=f.add(u,v);w=f.sub(v,f.sub(zz,u));square=f.mul(zz,zz)
    p=hx('0x1.637698p-25')
    for coefficient in ('-0x1.bbd41cp-20','0x1.1566aap-14','-0x1.6c16c2p-9','0x1.555556p-3'):
        p=f.add(f.mul(square,p),hx(coefficient))
    c=f.sub(zz,f.mul(square,p))
    r=f.sub(f.div(f.mul(zz,c),f.sub(c,hx('0x1p1'))),f.add(w,f.mul(zz,w)))
    result=f.sub(ONE,f.sub(r,zz))
    return scale2(result,n)
