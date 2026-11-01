"""Read-only selection of the proven4543 NPC three-field169 update shape.

All other169 shapes remain outside this declared packet projection. This is
not a generic network decoder, and does not filter by model-expected GUIDs.
"""
import struct


def npc_aura_updates169(packets):
    result = []
    for opcode, payload in packets:
        if opcode != 169:
            continue
        raw = bytes.fromhex(payload)
        # A single update-values block: count1, transport0, block-kind0.
        if len(raw) < 8 or raw[:6] != b'\1\0\0\0\0\0':
            continue
        mask, cursor, guid = raw[6], 7, 0
        for i in range(8):
            if mask >> i & 1:
                if cursor >= len(raw):
                    raise ValueError('Truncated169 packed GUID')
                guid |= raw[cursor] << (8 * i)
                cursor += 1
        if guid >> 48 != 0xf130:
            continue
        if cursor >= len(raw):
            raise ValueError('Missing169 field-mask length')
        words = raw[cursor]
        cursor += 1
        if words != 4:
            continue
        if cursor + 16 > len(raw):
            raise ValueError('Truncated169 field masks')
        masks = struct.unpack_from('<4I', raw, cursor)
        cursor += 16
        keys = [32 * j + bit for j, word in enumerate(masks)
                for bit in range(32) if word >> bit & 1]
        if len(raw) != cursor + 4 * len(keys):
            raise ValueError('169 update-values payload length differs')
        slots = [key - 79 for key in keys if 79 <= key <= 94]
        if len(slots) != 1:
            continue
        slot = slots[0]
        if set(keys) != {79 + slot, 99 + (slot >> 3), 121 + (slot >> 2)}:
            continue
        result.append(dict(guid=str(guid), slot=slot, payload169_hex=payload))
    return result
