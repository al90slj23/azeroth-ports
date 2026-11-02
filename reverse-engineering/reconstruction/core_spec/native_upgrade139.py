"""Pure partial-ABI upgrade scalar specification, independent of both engines.

Only explicit consumed fields are inputs. No complete Native or WASM owned
object is invented. Arithmetic rounds to binary32 after every instruction.
"""
from fractions import Fraction

SIGN=1<<31
INF=0x7f800000
NAN=0x7fc00000


def classification(v):
    return'nan'if v&0x7fffffff>INF else'infinity'if v&0x7fffffff==INF else'zero'if v&0x7fffffff==0 else'finite'


def value(v):
    assert classification(v)not in('nan','infinity');e=v>>23&255;m=v&0x7fffff;n=m if e==0 else m|0x800000;power=-149 if e==0 else e-150
    answer=Fraction(n<<power)if power>=0 else Fraction(n,1<<-power)
    return-answer if v&SIGN else answer


def _even(n,d):
    q,r=divmod(n,d);return q+int(2*r>d or 2*r==d and q&1)


def rounded(v,negative_zero=False):
    if not v:return SIGN if negative_zero else 0
    sign=SIGN if v<0 else 0;n,d=abs(v).numerator,abs(v).denominator;e=n.bit_length()-d.bit_length()
    if e>=0:
        if n<d<<e:e-=1
    elif n<<-e<d:e-=1
    if e< -126:return sign|_even(n<<149,d)
    shift=23-e;sig=_even(n<<shift,d)if shift>=0 else _even(n,d<<-shift)
    if sig==1<<24:e+=1;sig>>=1
    if e>127:return sign|INF
    return sign|((e+127)<<23)|(sig&0x7fffff)


def add(a,b):
    ca,cb=classification(a),classification(b)
    if'nan'in(ca,cb):return NAN
    if ca==cb=='infinity':return NAN if bool(a&SIGN)!=bool(b&SIGN)else a
    if ca=='infinity':return a
    if cb=='infinity':return b
    return rounded(value(a)+value(b),a==b==SIGN)


def sub(a,b):return add(a,b^SIGN)


def mul(a,b):
    ca,cb=classification(a),classification(b);sign=(a^b)&SIGN
    if'nan'in(ca,cb)or ca=='infinity'and cb=='zero'or cb=='infinity'and ca=='zero':return NAN
    if'infinity'in(ca,cb):return sign|INF
    return rounded(value(a)*value(b),bool(sign))


def div(a,b):
    ca,cb=classification(a),classification(b);sign=(a^b)&SIGN
    if'nan'in(ca,cb)or ca==cb=='infinity'or ca==cb=='zero':return NAN
    if ca=='infinity'or cb=='zero':return sign|INF
    if cb=='infinity':return sign
    return rounded(value(a)/value(b),bool(sign))


def max_second_zero(v):
    # Native MAXSS xmm0,+0 and WASM's explicit NaN/strict-positive selects.
    if classification(v)=='nan':return 0
    if classification(v)=='infinity':return 0 if v&SIGN else v
    return v if value(v)>0 else 0


def upgrade_scalar139(kind,tier,input_word,execution,slug,tables):
    if type(kind)is not int or not 0<=kind<5 or type(tier)is not int or not 0<=tier<5:raise ValueError('Only declared five variants/tiers')
    if type(input_word)is not int or not 0<=input_word<1<<32:raise ValueError('Explicit consumed32-bit field required')
    if len(tables)!=5 or any(len(t)!=5 for t in tables):raise ValueError('Five exact original coefficient rows required')
    if kind==0:return div(tables[0][tier],add(mul(rounded(Fraction(input_word)),0x3f000000),0x3f800000))
    if kind==1:return mul(max_second_zero(div(add(input_word,0xbe4ccccd),0x3f4ccccd)),tables[1][tier])
    if kind==2:
        cap=12 if execution!=11 else 2 if slug in('seal_fate','soul_fire','lightwell','faerie_fire')else 0
        return rounded(Fraction(min(max(cap-input_word,0),tables[2][tier])))
    if kind==3:return mul(max_second_zero(mul(sub(0x40a00000,input_word),0x3e800000)),tables[3][tier])
    return mul(max_second_zero(div(sub(0x40c00000,input_word),0x40a00000)),tables[4][tier])
