"""Current139 empty-account2945,6786 seed step and resolved18062 packet.

These are explicit component inputs, not an App/account/storage producer.
No original program, resource, snapshot, save or runtime output is accessed.
Unknown output padding remains unknown unless the caller supplied prior bytes.
"""
from dataclasses import dataclass
import struct

MASK64=(1<<64)-1
class UnknownOpeningProfile139(NotImplementedError):pass

@dataclass(frozen=True)
class EmptyAccountSources139:
    attributes12_count196:int
    flags16_count244:int
    identifiers4_count256:int
    bytes_count268:int

    def __post_init__(self):
        if any(type(x)is not int or x!=0 for x in(self.attributes12_count196,self.flags16_count244,self.identifiers4_count256,self.bytes_count268)):
            raise UnknownOpeningProfile139('2945 currently requires four explicitly empty account sources; absent account fields are not assumed empty')

def absent_companion_selection139(sources,prior40=None):
    """2945 writes30 bytes within required36; remaining caller bytes survive."""
    if not isinstance(sources,EmptyAccountSources139):raise TypeError('Typed account source counts required')
    prior=tuple(prior40)if prior40 is not None else(None,)*40
    if len(prior)!=40 or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in prior):raise ValueError('Exact40 output cells required')
    out=list(prior)
    for offset in(0,8,16,20,24,28):out[offset:offset+4]=(0,0,0,0)
    for offset,value in((4,255),(12,255),(32,0),(33,0),(34,0),(35,0)):out[offset]=value
    return tuple(out)

def advance_app_seed139(seed):
    """6786 reads/stores App4928, then passes the new seed to1600 viaP184."""
    if type(seed)is not int or not 0<=seed<=MASK64:raise ValueError('Explicit uint64 App seed required')
    return(seed*6364136223846793005+1442695040888963407)&MASK64

@dataclass(frozen=True)
class StartPacket139:
    opcode:int
    capacity:int
    payload:bytes

def start_banner139(title,subtitle):
    """Actual18062 successful UTF8 path, including each Vec reserve step."""
    if type(title)is not bytes or type(subtitle)is not bytes:raise TypeError('Resolved UTF8 byte strings required')
    title.decode('utf8');subtitle.decode('utf8')
    if len(title)>1048576 or len(subtitle)>1048576:raise ValueError('Bounded resolved banner input')
    data=bytearray(b'\x5a'+bytes(4));capacity=32
    def append(value):
        nonlocal capacity
        required=len(data)+len(value)
        if required>capacity:capacity=max(capacity*2,required)
        data.extend(value)
    append(struct.pack('<I',len(title)+1));append(title);append(b'\0');append(bytes(8));append(struct.pack('<I',len(subtitle)+1));append(subtitle);append(b'\0');append(b'\0')
    return StartPacket139(150,capacity,bytes(data))
