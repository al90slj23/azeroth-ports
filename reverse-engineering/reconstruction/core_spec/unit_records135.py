"""Explicit424B record adapters for independent135 world/cast composition.

No original program is loaded. Records are caller-supplied snapshots produced
by the independent spawner or observed as differential inputs. Only modeled
combat fields are patched; unknown bytes and movement endpoints remain intact.
This adapter does not infer dead-unit placement from cleared duration fields.
"""
from dataclasses import fields
import struct

from .combat135 import UnitState
from .cast135 import SpatialUnit


FLOAT_FIELDS = {
    'hp_bits':288, 'max_hp_bits':292,
    'control_until_124_bits':124, 'control_until_380_bits':380,
    'control_until_388_bits':388, 'modifier_until_356_bits':356,
    'additive_144_bits':144, 'additive_until_148_bits':148,
    'additive_152_bits':152, 'additive_until_156_bits':156,
    'additive_160_bits':160, 'additive_until_164_bits':164,
    'additive_368_bits':368, 'phase_until_408_bits':408,
    'phase_until_412_bits':412, 'movement_duration_344_bits':344,
    'movement_time_340_bits':340, 'death_time_4_bits':4,
}


def _record(raw):
    if not isinstance(raw,bytes) or len(raw)!=424:
        raise ValueError('An explicit424B unit snapshot is required')
    return raw


def decode_unit(raw):
    """Interpret only the already modeled135 combat fields."""
    raw=_record(raw)
    word=lambda offset:struct.unpack_from('<I',raw,offset)[0]
    signed=lambda offset:struct.unpack_from('<i',raw,offset)[0]
    data={name:word(offset) for name,offset in FLOAT_FIELDS.items()}
    data.update(target_id=struct.unpack_from('<Q',raw,112)[0],
        linked_id_32=struct.unpack_from('<Q',raw,32)[0],marker=word(0),
        kind_40=signed(40),kind_64=signed(64),elite_244=signed(244),
        elite_416=raw[416],afflicted_240=word(240))
    if set(data)!={field.name for field in fields(UnitState)}:
        raise ValueError('Combat schema changed; record adapter needs explicit migration')
    return UnitState(**data)


def decode_spatial(raw):
    raw=_record(raw)
    return SpatialUnit(decode_unit(raw),struct.unpack_from('<2I',raw,316),
        struct.unpack_from('<2I',raw,328),struct.unpack_from('<I',raw,372)[0])


def patch_unit(raw,unit):
    """Preserve every unmodeled byte while synchronizing modeled combat state."""
    raw=_record(raw)
    if not isinstance(unit,UnitState):
        raise TypeError('A resolved combat UnitState is required')
    if struct.unpack_from('<Q',raw,112)[0]!=unit.target_id:
        raise ValueError('Unit record GUID differs')
    result=bytearray(raw)
    for name,offset in FLOAT_FIELDS.items():
        struct.pack_into('<I',result,offset,getattr(unit,name))
    struct.pack_into('<I',result,0,unit.marker)
    struct.pack_into('<Q',result,32,unit.linked_id_32)
    for name,offset in (('kind_40',40),('kind_64',64),('elite_244',244)):
        struct.pack_into('<I',result,offset,getattr(unit,name)&0xffffffff)
    struct.pack_into('<I',result,240,unit.afflicted_240)
    result[416]=unit.elite_416
    return bytes(result)


def patch_units(records,units):
    """Preserve order and reject accidental missing/duplicate logical units."""
    records=tuple(records);units=tuple(units)
    if len(records)!=len(units):
        raise ValueError('Record/semantic unit counts differ')
    ids=[unit.target_id for unit in units]
    if len(set(ids))!=len(ids):
        raise ValueError('Unique unit GUIDs are required')
    return tuple(patch_unit(raw,unit) for raw,unit in zip(records,units))
