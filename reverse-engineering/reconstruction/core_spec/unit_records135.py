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
from .record_cells135 import (cells135,u32,i32,u64,optional_u32,optional_u64,
    put_u32,put_u64,known_bytes)


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
    return cells135(raw,424)


def decode_unit(raw):
    """Interpret only the already modeled135 combat fields."""
    raw=_record(raw)
    word=lambda offset:u32(raw,offset,'135 combat unit field')
    signed=lambda offset:i32(raw,offset,'135 combat unit tag')
    data={name:(optional_u32(raw,offset) if name=='death_time_4_bits' else word(offset))
        for name,offset in FLOAT_FIELDS.items()}
    data.update(target_id=u64(raw,112,'135 combat target GUID'),
        linked_id_32=optional_u64(raw,32),marker=word(0),
        kind_40=signed(40),kind_64=signed(64),elite_244=signed(244),
        elite_416=raw[416],afflicted_240=word(240))
    if set(data)!={field.name for field in fields(UnitState)}:
        raise ValueError('Combat schema changed; record adapter needs explicit migration')
    return UnitState(**data)


def decode_spatial(raw):
    unit=decode_unit(raw);raw=_record(raw)
    return SpatialUnit(unit,tuple(u32(raw,o,'135 spatial fromXY')for o in(316,320)),
        tuple(u32(raw,o,'135 spatial toXY')for o in(328,332)),u32(raw,372,'135 spatial priority'))


def patch_unit(raw,unit):
    """Preserve every unmodeled byte while synchronizing modeled combat state."""
    raw=_record(raw)
    if not isinstance(unit,UnitState):
        raise TypeError('A resolved combat UnitState is required')
    if u64(raw,112,'135 unit patch GUID')!=unit.target_id:
        raise ValueError('Unit record GUID differs')
    result=list(raw)
    for name,offset in FLOAT_FIELDS.items():
        value=getattr(unit,name)
        if value is not None:put_u32(result,offset,value)
    put_u32(result,0,unit.marker)
    if unit.linked_id_32 is not None:put_u64(result,32,unit.linked_id_32)
    for name,offset in (('kind_40',40),('kind_64',64),('elite_244',244)):
        put_u32(result,offset,getattr(unit,name)&0xffffffff)
    put_u32(result,240,unit.afflicted_240)
    result[416]=unit.elite_416
    return tuple(result)if None in result else known_bytes(result)


def patch_units(records,units):
    """Preserve order and reject accidental missing/duplicate logical units."""
    records=tuple(records);units=tuple(units)
    if len(records)!=len(units):
        raise ValueError('Record/semantic unit counts differ')
    ids=[unit.target_id for unit in units]
    if len(set(ids))!=len(ids):
        raise ValueError('Unique unit GUIDs are required')
    return tuple(patch_unit(raw,unit) for raw,unit in zip(records,units))
