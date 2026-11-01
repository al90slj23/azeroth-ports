"""Fixed135 canonical opcode199 acknowledgement scalar consumer.

The GUID is decoded but is not compared on968 default local route. The
component excludes remote2080 switching and17726 mode1 queue forwarding.
Unknown/inactive correction payload bytes are preserved, never filled.
"""
from dataclasses import dataclass
import struct

SOURCE_WASM_SHA256='c62c85f5478a12d006b3bde4e5e71db5d3fb50aed218f474c228182800dc96e2'


class UnknownPlayerCorrection135(NotImplementedError):pass


@dataclass(frozen=True)
class PlayerCorrectionAck135:
    guid:int
    sequence:int


@dataclass(frozen=True)
class PlayerCorrectionResult135:
    game_bytes:bytes|tuple
    writes:tuple
    ack:PlayerCorrectionAck135
    cleared:bool


def encode_player_correction_ack135(guid,sequence):
    if type(guid)is not int or not 0<=guid<1<<64 or type(sequence)is not int or not 0<=sequence<1<<32:
        raise ValueError('Explicit u64 GUID and u32 ACK sequence required')
    words=guid.to_bytes(8,'little');mask=sum(1<<j for j,v in enumerate(words)if v)
    return bytes((mask,))+bytes(v for v in words if v)+struct.pack('<I',sequence)


def decode_player_correction_ack135(payload):
    """Exact mask+packedGUID+u32 domain; original malformed defaults pending."""
    if type(payload)is not bytes or not payload:raise UnknownPlayerCorrection135('Canonical packedGUID+sequence input required')
    mask=payload[0];count=mask.bit_count()
    if len(payload)!=1+count+4:raise UnknownPlayerCorrection135('Canonical exact packedGUID+u32 length required')
    guid=0;at=1
    for j in range(8):
        if mask>>j&1:guid|=payload[at]<<(8*j);at+=1
    return PlayerCorrectionAck135(guid,struct.unpack_from('<I',payload,at)[0])


def consume_player_correction_ack135(game_bytes,payload):
    ack=decode_player_correction_ack135(payload)
    physical=type(game_bytes)is bytes
    if not physical and(type(game_bytes)is not tuple or any(x is not None and(type(x)is not int or not 0<=x<=255)for x in game_bytes)):
        raise ValueError('Explicit bytes or tuple[byte|None] Game input')
    if len(game_bytes)<436:raise ValueError('Game view must include G432u32')
    raw=bytearray(game_bytes)if physical else list(game_bytes)
    def word(offset):
        selected=raw[offset:offset+4]
        if any(x is None for x in selected):raise UnknownPlayerCorrection135(f'Unknown consumed Gameu32 at+{offset}')
        return int.from_bytes(bytes(selected),'little')
    cleared=word(416)==1 and ack.sequence>=word(432)
    writes=()
    if cleared:raw[416:420]=bytes(4);writes=((416,0),)
    return PlayerCorrectionResult135(bytes(raw)if physical else tuple(raw),writes,ack,cleared)
