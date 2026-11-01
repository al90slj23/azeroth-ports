"""Literal135 declarations for independent dispatch; no original runtime IO.

Keeping a definition available does not claim its execution/effect is restored.
Dispatchers must still reject unsupported branches explicitly.
"""
import struct
from .cast135 import CastDefinition
from .cast_catalogue135_data import RAW_DEFINITIONS

DEFINITIONS = {}
RAW_BY_POINTER = {}
for _pointer, _name, _hex in RAW_DEFINITIONS:
    _raw = bytes.fromhex(_hex)
    _w = struct.unpack('<22I', _raw)
    DEFINITIONS[_name] = CastDefinition(_pointer, _name.encode('ascii'), _raw[84], _w[0],
        _w[11], _raw[85], _w[12], _w[13], _w[14], _w[15], _w[16])
    RAW_BY_POINTER[_pointer] = _hex
BY_POINTER = {d.pointer: d for d in DEFINITIONS.values()}


def definition(pointer):
    if pointer not in BY_POINTER:
        raise ValueError('No fixed135 declaration for this pointer')
    return BY_POINTER[pointer]
