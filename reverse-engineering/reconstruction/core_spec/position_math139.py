"""Independent13911425/11499 bounded trig and50441 hypot algorithms.

Expressions derive from prior independent numeric work, rebound to current139
bodies and constants. Runtime imports no old geometry model/original. Actual
8740/13563 angles are within[-2pi,2pi]; largerange reduction staysunknown.
"""
from . import binary32 as f
from .binary32_sqrt import sqrt_bits

H=float.fromhex
PI2=H('0x1.921fb54442d18p0');PI=H('0x1.921fb54442d18p1');PI3=H('0x1.2d97c7f3321d2p2');TAU=H('0x1.921fb54442d18p2')


def _sin_kernel(x):
    z=x*x;v=z*x
    a=(v*(z*z))*(z*H('0x1.6cd878c3b46a7p-19')+H('-0x1.a00f9e2cae774p-13'))
    b=v*(z*H('0x1.11110896efbb2p-7')+H('-0x1.5555554cbac77p-3'))+x
    return f.from_float(a+b)


def _cos_kernel(x):
    z=x*x;w=z*z
    a=(z*H('-0x1.ffffffd0c5e81p-2')+1)+w*H('0x1.55553e1053a42p-5')
    return f.from_float(a+(z*w)*(z*H('0x1.99342e0ee5069p-16')+H('-0x1.6c087e80f1e27p-10')))


def sin_bits(bits):
    a=bits&0x7fffffff
    if a>0x40c90fdb:raise ValueError('Large-angle reduction remains unresolved')
    x=abs(f.to_float(bits))
    if a<1061752795:r=_sin_kernel(x)
    elif a<1075235812:r=_cos_kernel(x-PI2)
    elif a<1081824210:r=_sin_kernel(x-PI)^f.SIGN
    elif a<1085271520:r=_cos_kernel(x-PI3)^f.SIGN
    else:r=_sin_kernel(x-TAU)
    return r^(bits&f.SIGN)


def cos_bits(bits):
    a=bits&0x7fffffff
    if a>0x40c90fdb:raise ValueError('Large-angle reduction remains unresolved')
    x=abs(f.to_float(bits))
    if a<=1061752794:return _cos_kernel(x)
    if a<=1075235811:return _sin_kernel(PI2-x)
    if a<=1081824209:return _cos_kernel(x-PI)^f.SIGN
    if a<=1085271519:return _sin_kernel(x-PI3)
    return _cos_kernel(x-TAU)


def hypot_bits(a,b):
    small,large=sorted((a&0x7fffffff,b&0x7fffffff))
    if small==f.INF:return f.INF
    if large>0x7f7fffff or small==0 or large-small>=209715200:return f.add(large,small)
    factor=0x3f800000
    if large>1568669695:
        small=f.mul(small,f.from_float(2.0**-90));large=f.mul(large,f.from_float(2.0**-90));factor=f.from_float(2.0**90)
    elif small<562036736:
        small=f.mul(small,f.from_float(2.0**90));large=f.mul(large,f.from_float(2.0**90));factor=f.from_float(2.0**-90)
    x,y=f.to_float(small),f.to_float(large)
    return f.mul(factor,sqrt_bits(f.from_float(x*x+y*y)))
