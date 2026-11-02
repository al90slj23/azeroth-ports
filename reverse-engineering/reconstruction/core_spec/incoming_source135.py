"""Fixed135 ordinary-NPC source resolution for incoming history.

This is the second GUID lookup in1073, not the earlier damage-statistics
registry lookup. Names must be explicitly resolved for the selected locale;
the convenience catalogue supplies only proven static English fallbacks.
"""
from dataclasses import dataclass

from .record_cells135 import cells135, u32, u64
from .spawn135_data import NORMALS, NORMAL_FIELDS


class UnknownIncomingSource135(NotImplementedError):
    pass


@dataclass(frozen=True)
class IncomingSource135:
    source_label: str
    source_classification: int
    unit_index: int | None
    definition_pointer: int | None


def ordinary_english_source_names135():
    """Static fallback data only; no translation-map producer is implied."""
    names = {}
    for zone in NORMALS:
        for row in zone:
            definition = dict(zip(NORMAL_FIELDS, row))
            pointer, name = definition['pointer'], definition['name']
            if pointer in names and names[pointer] != name:
                raise ValueError('Conflicting ordinary-NPC fallback names')
            names[pointer] = name
    return names


def resolve_incoming_source135(records, source_guid, *, resolved_definition_names):
    """1073 GUID scan→ordinary U284 name→raw U416 classification.

    The first matching vector entry wins, including a dead entry. Unmatched
    GUIDs do not consume names or inactive fields. Custom actors and summons
    stop at their real branch, rather than being treated as ordinary NPCs.
    """
    if type(source_guid) is not int or not 0 <= source_guid < 1 << 64:
        raise ValueError('Explicit u64 source GUID required')
    if not isinstance(resolved_definition_names, dict):
        raise TypeError('Explicit locale-resolved definition names required')
    for index, record in enumerate(records):
        row = cells135(record, 424)
        if u64(row, 112, '1073 history source GUID') != source_guid:
            continue
        if u32(row, 244, '1073 custom source branch') != 0xffffffff:
            raise UnknownIncomingSource135('Custom source labels require their own producer')
        if u32(row, 40, '1073 summoned source branch') != 0xffffffff:
            raise UnknownIncomingSource135('Summoned source labels require their own producer')
        pointer = u32(row, 284, '1073 ordinary source definition')
        if pointer:
            if pointer not in resolved_definition_names:
                raise UnknownIncomingSource135('Source definition name is unresolved')
            label = resolved_definition_names[pointer]
            if type(label) is not str:
                raise TypeError('Resolved UTF8 source label required')
            label.encode('utf-8')
        else:
            label = ''
        rank = row[416]
        if rank is None:
            raise UnknownIncomingSource135('Raw source classification U416 is unresolved')
        return IncomingSource135(label, rank, index, pointer)
    return IncomingSource135('', 4, None, None)
