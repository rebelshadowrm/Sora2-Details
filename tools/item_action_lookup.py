"""Exact-build generated item action descriptors; research metadata only.

Native 23E760 emits B8-byte records: a B0 skill-shaped descriptor followed by
the original item ID at B0. Its low-word key is 578 + eligible-row ordinal,
NOT an item ID. See docs/ITEM-IDENTITY-LIVE-RESULT-20261002.md.
"""
import struct
from item_table_index import (read_rows, cstring, PAYLOAD_OFFSET, PAYLOAD_SIZE,
                              ROW_START, ROW_SIZE, PAYLOAD_SHA256)
from skill_table_index import (read_rows as read_skills, PAYLOAD_OFFSET as SKILL_OFFSET,
                               ROW_START as SKILL_START, ROW_SIZE as SKILL_SIZE)

# Exact native 258400 switch (A..b). B/M are the 0xC0000 eligibility bits.
FLAG_BITS = dict(zip('ABCEFGILMNOPQRSTXbDH',
    (21, 18, 16, 13, 12, 23, 17, 27, 19, 26, 22, 25, 29, 15, 14, 20, 30, 31, 24, 28)))
COMPARE_RANGES = ((0, 8), (0x10, 0x18), (0x20, 0x90))


def generated_records(rows, payload, default_word):
    result = []
    for row in rows:
        source = payload[ROW_START + row['row'] * ROW_SIZE:ROW_START + (row['row'] + 1) * ROW_SIZE]
        if len(source) != ROW_SIZE:
            raise ValueError('Incomplete item row')
        flags = 0
        for char in cstring(payload, struct.unpack_from('<Q', source, 0x18)[0]):
            if char in FLAG_BITS:
                flags |= 1 << FLAG_BITS[char]
        if not (flags & 0xC0000 or any(struct.unpack_from('<H', source, 0x3C + n * 0x10)[0] for n in range(5))):
            continue
        key = 0x578 + len(result)
        if key > 0x7CF:
            raise ValueError('Generated item key exceeds native supported range')
        descriptor = bytearray(0xB0)
        struct.pack_into('<I', descriptor, 0, 0xFFFF0000 | key)
        struct.pack_into('<I', descriptor, 8, flags)
        descriptor[0x10] = 6
        descriptor[0x11] = source[0x2E]
        struct.pack_into('<I', descriptor, 0x18, 3)
        descriptor[0x20:0x22] = source[0x30:0x32]
        descriptor[0x24:0x2C] = source[0x34:0x3C]
        descriptor[0x30:0x80] = source[0x3C:0x8C]
        descriptor[0x80:0x84] = source[0x8C:0x90]
        struct.pack_into('<H', descriptor, 0x86, default_word)
        descriptor[0x8E:0x90] = source[0x2C:0x2E]
        # Relocated name/animation/description pointers at 90/98/A8 are omitted.
        result.append((row, bytes(descriptor)))
    return result


class ItemActionLookup:
    def __init__(self, pac):
        rows = read_rows(pac)  # Exact localized payload hash and unique IDs.
        skills = read_skills(pac)
        default = next((row for row in skills if row['skillId'] == 0x40), None)
        if default is None:
            raise ValueError('Missing native default item skill row')
        with pac.open('rb') as stream:
            stream.seek(PAYLOAD_OFFSET)
            payload = stream.read(PAYLOAD_SIZE)
            stream.seek(SKILL_OFFSET + SKILL_START + default['row'] * SKILL_SIZE + 0x86)
            default_word = struct.unpack('<H', stream.read(2))[0]
        self.rows = generated_records(rows, payload, default_word)

    def match(self, data):
        return [row for row, candidate in self.rows if len(data) == 0xB0 and
                all(data[a:b] == candidate[a:b] for a, b in COMPARE_RANGES)]


def corroborate_original_item_id(result, companion):
    if companion is None:
        return result
    try:
        data = bytes.fromhex(companion)
        descriptor = bytes.fromhex(result['inlineRaw'])
    except (ValueError, TypeError):
        data = descriptor = b''
    if len(data) != 0xB8 or len(descriptor) != 0xB0 or data[:0xB0] != descriptor:
        result.update(nativeItemRecordState='inconsistent', lookupState='inconsistent-item-record', nameCandidate=None)
        return result
    key = struct.unpack_from('<I', data)[0]
    if not (0xFFFF0578 <= key <= 0xFFFF07CF and data[0x10] == 6):
        result.update(nativeItemRecordState='outside-generated-item-shape', lookupState='unknown', nameCandidate=None)
        return result
    original = struct.unpack_from('<I', data, 0xB0)[0]
    result.update(originalItemIdRaw=original,
        originalItemIdProvenance='inline-generated-record-plus-B0/native-69736')
    if result.get('lookupNamespace') == 'GeneratedItemAction':
        matches = original == result.get('itemIdCandidate')
        result['nativeItemRecordState'] = 'corroborated' if matches else 'conflicting-item-id'
        if not matches:
            result['nameCandidate'] = None
            result['lookupState'] = 'conflicting-item-id'
    else:
        result['nativeItemRecordState'] = 'original-id-observed; descriptor-unresolved'
    return result
