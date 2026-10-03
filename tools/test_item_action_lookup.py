import struct
import unittest
from item_action_lookup import generated_records, ItemActionLookup, corroborate_original_item_id
from item_table_index import ROW_START, ROW_SIZE, STRING_START
from reconcile_action_stream import DescriptorLookup


class ItemActionChecks(unittest.TestCase):
    def setUp(self):
        self.payload = bytearray(STRING_START + 32)
        self.payload[STRING_START:STRING_START + 2] = b'M\0'
        self.rows = [{'row': i, 'itemId': key, 'name': name} for i, key, name in
                     ((0, 215, 'Photo'), (1, 999, 'Ineligible'), (2, 1, 'Tear Balm'), (3, 5, 'EP Charge I'))]
        # Photo is eligible through flags without any effects; it advances the
        # generated ordinal. An ineligible intervening row does not advance it.
        struct.pack_into('<Q', self.payload, ROW_START + 0x18, STRING_START)
        for row, code, amount in ((2, 122, 1500), (3, 124, 150)):
            offset = ROW_START + row * ROW_SIZE
            struct.pack_into('<I', self.payload, offset + 0x3C, code)
            struct.pack_into('<I', self.payload, offset + 0x40, amount)
        self.lookup = ItemActionLookup.__new__(ItemActionLookup)
        self.lookup.rows = generated_records(self.rows, self.payload, 50)

    def test_generated_key_is_eligible_ordinal_not_item_id(self):
        self.assertEqual([215, 1, 5], [r['itemId'] for r, _ in self.lookup.rows])
        self.assertEqual([0xFFFF0578, 0xFFFF0579, 0xFFFF057A],
                         [struct.unpack_from('<I', b)[0] for _, b in self.lookup.rows])
        item, raw = self.lookup.rows[-1]
        self.assertEqual('EP Charge I', self.lookup.match(raw)[0]['name'])
        self.assertEqual(124, struct.unpack_from('<I', raw, 0x30)[0])
        self.assertEqual(150, struct.unpack_from('<I', raw, 0x34)[0])
        self.assertEqual(50, struct.unpack_from('<H', raw, 0x86)[0])

    def test_pointer_relocation_is_ignored_but_parameters_are_required(self):
        raw = bytearray(self.lookup.rows[-1][1])
        raw[0x90:0x98] = b'pointer!'
        self.assertEqual(1, len(self.lookup.match(raw)))
        raw[0x34] ^= 1
        self.assertEqual([], self.lookup.match(raw))
        self.assertEqual([], self.lookup.match(raw[:4]))
        self.assertEqual([], self.lookup.match(bytes(0xB0)))

    def test_unknown_and_ambiguous_namespaces_do_not_gain_item_names(self):
        lookup = DescriptorLookup.__new__(DescriptorLookup)
        lookup.rows = []
        lookup.items = self.lookup
        raw = self.lookup.rows[-1][1]
        result = lookup.describe(raw.hex())
        self.assertEqual(5, result['itemIdCandidate'])
        self.assertEqual('GeneratedItemAction', result['lookupNamespace'])
        self.assertNotEqual(5, int(result['rawPackedId'], 16))
        lookup.rows = [({'row': 123, 'name': 'Other namespace'}, raw)]
        result = lookup.describe(raw.hex())
        self.assertEqual('ambiguous', result['lookupState'])
        self.assertIsNone(result['nameCandidate'])
        self.assertNotIn('itemIdCandidate', result)

    def test_original_item_id_corroborates_and_conflicts_remain_unlabelled(self):
        lookup = DescriptorLookup.__new__(DescriptorLookup)
        lookup.rows, lookup.items = [], self.lookup
        raw = self.lookup.rows[-1][1]
        companion = raw + struct.pack('<II', 5, 0)
        result = corroborate_original_item_id(lookup.describe(raw.hex()), companion.hex())
        self.assertEqual(5, result['originalItemIdRaw'])
        self.assertEqual('corroborated', result['nativeItemRecordState'])
        wrong = raw + struct.pack('<II', 6, 0)
        result = corroborate_original_item_id(lookup.describe(raw.hex()), wrong.hex())
        self.assertIsNone(result['nameCandidate'])
        self.assertEqual('conflicting-item-id', result['nativeItemRecordState'])
        self.assertEqual('conflicting-item-id', result['lookupState'])
        result = corroborate_original_item_id(lookup.describe(raw.hex()), companion[:-1].hex())
        self.assertIsNone(result['nameCandidate'])
        self.assertEqual('inconsistent', result['nativeItemRecordState'])


if __name__ == '__main__':
    unittest.main()
