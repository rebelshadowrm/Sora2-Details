"""Offline checks for raw pointer paths, unsupported keys and bounded reads."""

import struct
import unittest
from types import SimpleNamespace

from action_stream_snapshots import (action_state_snapshot, condition_request_snapshot,
                                     condition_return_snapshot, effect_dispatch_snapshot,
                                     queue_transition_snapshot, action_setup_snapshot,
                                     animation_launch_snapshot, actor_state_dispatch_snapshot,
                                     first_actor_state_update)
from action_stream_snapshots import accepted_launch_owner, battle_mode_write_snapshot
from action_stream_snapshots import item_record_snapshot, descriptor_text_snapshot


class SnapshotChecks(unittest.TestCase):
    def test_descriptor_string_companions_keep_raw_unlocalized_and_inaccessible_slots(self):
        descriptor = bytearray(0xB0)
        struct.pack_into('<QQ', descriptor, 0x90, 0x8000, 0x9999)
        self.blocks[0x8000] = bytearray(b'AniBtlCraft07\0' + b'\0' * (256-14))
        fields = {}
        descriptor_text_snapshot(fields, 'descriptor', descriptor, self.read)
        self.assertEqual('0x8000', fields['descriptor_slot_90_ptr'])
        self.assertEqual(self.blocks[0x8000].hex(), fields['descriptor_slot_90_raw'])
        self.assertEqual('0x9999', fields['descriptor_slot_98_ptr'])
        self.assertIsNone(fields['descriptor_slot_98_raw'])
        short = {}
        descriptor_text_snapshot(short, 'descriptor', descriptor[:-1], self.read)
        self.assertEqual({}, short)

    def test_condition_common_return_keeps_null_result_and_recovers_request_frame(self):
        self.blocks[0x2000] = bytearray(0x940)
        self.blocks[0x6000] = bytearray(0x80)
        self.blocks[0x7000] = bytearray(0xB0)
        ctx = SimpleNamespace(r15=0x2000, rbp=55, r12=0x7000, rax=0, rsp=0x6000)
        result = condition_return_snapshot(ctx, self.read, self.u64, 'common')
        self.assertEqual('0x61f8', result['condition_request_frame_raw'])
        self.assertEqual(55, result['condition_insert_key_raw'])
        self.assertEqual(0, result['condition_return_eax_raw'])
        self.assertIsNone(result['condition_return_rax_ptr'])
        self.assertIn('7FDE7', result['condition_return_site'])

    def test_cure_identity_reads_require_exact_dispatch_caller_and_matching_manager(self):
        manager = bytearray(0x940)
        dispatch = bytearray(0x600)
        source = bytearray(0x600)
        stack = bytearray(0x80)
        struct.pack_into('<Q', dispatch, 0x598, 0x2000)
        struct.pack_into('<Q', source, 0, 0x9000)
        struct.pack_into('<Q', stack, 0, 0x1400DF127)
        self.blocks.update({0x2000: manager, 0x7000: dispatch, 0x8000: source,
            0x9000: bytearray(0x2A0), 0xA000: bytearray(0xB0), 0x6000: stack})
        ctx = SimpleNamespace(rcx=0x2000, rdx=1, r8=1, r9=0, rsp=0x6000,
            r13=0x7000, r14=0xA000, rsi=0x8000)
        result = condition_return_snapshot(ctx, self.read, self.u64, 'remove-entry', 0x140000000)
        self.assertEqual('0xdf127', result['condition_remove_identity_route'])
        self.assertEqual('0xa000', result['condition_remove_descriptor_ptr'])
        self.assertEqual('0x9000', result['condition_remove_source_status_ptr'])
        struct.pack_into('<Q', dispatch, 0x598, 0x9999)
        mismatch = condition_return_snapshot(ctx, self.read, self.u64, 'remove-entry', 0x140000000)
        self.assertNotIn('condition_remove_identity_route', mismatch)
        struct.pack_into('<Q', stack, 0, 0x1400813BE)
        ordinary = condition_return_snapshot(ctx, self.read, self.u64, 'remove-entry', 0x140000000)
        self.assertNotIn('condition_remove_descriptor_raw', ordinary)

    def test_condition_remove_return_recovers_original_frame_without_using_clobbered_key(self):
        self.blocks[0x2000] = bytearray(0x940)
        ctx = SimpleNamespace(rcx=0x2000, rdx=27, r8=1, r9=0, rsp=0x6000)
        request = condition_return_snapshot(ctx, self.read, self.u64, 'remove-entry')
        returned = condition_return_snapshot(SimpleNamespace(rsi=0x2000, rax=0x101, rsp=0x5F38),
            self.read, self.u64, 'remove-return')
        self.assertEqual(request['condition_remove_frame_raw'], returned['condition_remove_frame_raw'])
        self.assertEqual(27, request['condition_remove_key_raw'])
        self.assertEqual(1, returned['condition_remove_return_al_raw'])
        self.assertNotIn('condition_remove_key_raw', returned)
        self.assertNotIn('expired', returned)

    def test_general_condition_insert_return_uses_preserved_manager_and_descriptor(self):
        manager = bytearray(0x940)
        struct.pack_into('<Q', manager, 0x908, 0x3000)
        struct.pack_into('<i', manager, 0x910, 1)
        record = bytearray(0x48)
        struct.pack_into('<I', record, 0, 56)
        self.blocks.update({0x2000: manager, 0x3000: record, 0x4000: bytearray(0xB0)})
        ctx = SimpleNamespace(r15=0x2000, r12=0x4000, rbp=56, rsp=0x6000, rax=0x3000)
        result = condition_return_snapshot(ctx, self.read, self.u64, 'insert')
        self.assertEqual('0x2000', result['condition_manager_ptr'])
        self.assertEqual('0x4000', result['condition_insert_descriptor_ptr'])
        self.assertEqual(56, result['condition_insert_key_raw'])
        self.assertEqual(record.hex(), result['condition_return_rax_raw'])
        self.assertIsNone(result['condition_insert_source_status_raw'])
        self.assertNotIn('applied', result)

    def test_item_companion_read_is_bounded_and_ordinary_skills_do_not_read_past_b0(self):
        block = bytearray(0xB8)
        struct.pack_into('<I', block, 0, 0xFFFF057A)
        block[0x10] = 6
        struct.pack_into('<I', block, 0xB0, 1)
        self.blocks[0x5000] = block
        result = {}
        item_record_snapshot(result, 'descriptor', 0x5000, block[:0xB0], self.read)
        raw = bytes.fromhex(result['descriptor_item_record_raw'])
        self.assertEqual(0xB8, len(raw))
        self.assertEqual(1, struct.unpack_from('<I', raw, 0xB0)[0])
        struct.pack_into('<I', block, 0, 0xFFFF0076)
        result = {}
        item_record_snapshot(result, 'descriptor', 0x5000, block[:0xB0], self.read)
        self.assertIsNone(result['descriptor_item_record_ptr'])
        self.assertIsNone(result['descriptor_item_record_raw'])
        struct.pack_into('<I', block, 0, 0xFFFF057A)
        result = {}
        item_record_snapshot(result, 'descriptor', 0x9999, block[:0xB0], self.read)
        self.assertIsNone(result['descriptor_item_record_raw'])
    def test_mode_root_snapshot_retains_flags_and_bounds_roster_reads(self):
        owner = bytearray(0x3000)
        struct.pack_into('<Q', owner, 0x2448, 0x9000)
        struct.pack_into('<i', owner, 0x2450, 100000)
        struct.pack_into('<I', owner, 0x2CEC, 0x4008)
        self.blocks.update({0x1000: owner, 0x9000: bytearray(16 * 8)})
        snapshot = battle_mode_write_snapshot(0x1000, self.read, self.u64)
        self.assertEqual(16, len(snapshot['mode_roster_candidates']))
        self.assertTrue(snapshot['mode_roster_truncated'])
        self.assertEqual(0x4008, struct.unpack_from('<I', bytes.fromhex(snapshot['mode_root_2ce0_raw']), 12)[0])
        self.assertTrue(all(r['actor_raw'] is None for r in snapshot['mode_roster_candidates']))
        struct.pack_into('<i', owner, 0x2450, -1)
        self.assertEqual([], battle_mode_write_snapshot(0x1000, self.read, self.u64)['mode_roster_candidates'])
        self.assertIsNone(battle_mode_write_snapshot(None, self.read, self.u64)['mode_root_2ce0_raw'])

    def test_actor_dispatch_first_update_and_handler_are_read_on_the_shared_path(self):
        actor = bytearray(0x1000)
        struct.pack_into('<Q', actor, 0x88, 0x1000)
        struct.pack_into('<Q', actor, 0x120, 0x140068320)
        struct.pack_into('<Q', actor, 0xC70, 0x5000)
        self.blocks.update({0x1000: actor, 0x5000: bytearray(0xB0)})
        self.ctx.rcx = 0x1000
        self.ctx.rbx = self.ctx.rsi = 0x1088
        self.ctx.rax = 18
        self.assertTrue(first_actor_state_update(self.ctx, self.read, self.u64))
        snapshot = actor_state_dispatch_snapshot(self.ctx, self.read, self.u64)
        self.assertEqual('0x140068320', snapshot['actor_state_handler_ptr_raw'])
        self.assertEqual('0x5000', snapshot['actor_state_owner_c70_ptr'])
        struct.pack_into('<i', actor, 0x260, 12)
        self.assertFalse(first_actor_state_update(self.ctx, self.read, self.u64))
        self.ctx.rbx = 0xBAD
        self.assertIsNone(first_actor_state_update(self.ctx, self.read, self.u64))
        self.assertIsNone(actor_state_dispatch_snapshot(self.ctx, self.read, self.u64)['actor_state_first_update_candidate'])

    def test_launch_request_and_acceptance_preserve_the_same_call_frame(self):
        context = bytearray(0x1D98)
        actor = bytearray(0x1000)
        struct.pack_into('<Q', context, 0x1D88, 0x1000)
        struct.pack_into('<Q', context, 0x1D90, 0xA000)
        struct.pack_into('<Q', actor, 0x328, 0x8000)
        struct.pack_into('<Q', actor, 0xC70, 0x4500)
        linked = bytearray(0x600)
        struct.pack_into('<Q', linked, 0, 0xB000)
        stack = bytearray(0x100)
        struct.pack_into('<Q', stack, 0x78, 0x140069311)
        struct.pack_into('<Q', stack, 0x70, 0x1C70)
        self.blocks.update({0x8000: context, 0x1000: actor, 0x4500: bytearray(0xB0),
                            0xA000: linked, 0xB000: bytearray(0x2A0),
                            0x5000: bytearray(0x100), 0x5F88: stack})
        self.ctx.rcx = self.ctx.rbx = 0x8000
        self.ctx.rdi = self.ctx.r8
        request = animation_launch_snapshot(self.ctx, self.read, self.u64, 'request')
        self.ctx.rsp -= 0x78
        self.ctx.rcx = 0xBAD  # Volatile RCX is now the animation queue object.
        self.ctx.rbx = 0x26  # EBX was overwritten with a script index.
        accepted = animation_launch_snapshot(self.ctx, self.read, self.u64, 'accepted', 0x140000000)
        for field in ('launch_context_ptr', 'launch_script_ptr', 'launch_entry_stack_pointer_raw',
                      'launch_caller_raw', 'launch_actor_c70_raw', 'launch_linked_first_ptr'):
            self.assertEqual(request[field], accepted[field], field)
        self.assertTrue(request['launch_owner_link_matches'])
        self.assertEqual('0x140069311', accepted['launch_caller_raw'])
        self.assertNotIn('launch_channel_u32_raw', accepted)
        self.assertNotIn('executed', accepted)

    def test_saved_launch_owner_is_scoped_to_verified_callers(self):
        stack = bytearray(0x80)
        struct.pack_into('<Q', stack, 0x60, 0x1000)
        struct.pack_into('<Q', stack, 0x70, 0x2000)
        self.assertEqual(0x1000, accepted_launch_owner(0x686F1, stack))
        self.assertEqual(0x2000, accepted_launch_owner(0x68E8B, stack))
        self.assertEqual(0x2000, accepted_launch_owner(0x69638, stack))
        self.assertIsNone(accepted_launch_owner(0x12345, stack))
        self.assertIsNone(accepted_launch_owner(0x686F1, stack[:16]))

    def test_setup_entry_preserves_descriptor_actor_and_linked_status(self):
        actor = bytearray(0x1000)
        context = bytearray(0x1D98)
        linked = bytearray(0x600)
        struct.pack_into('<Q', actor, 0x328, 0x8000)
        struct.pack_into('<Q', actor, 0xC70, 0x4000)
        struct.pack_into('<Q', context, 0x1D90, 0xA000)
        struct.pack_into('<Q', linked, 0, 0xB000)
        self.blocks.update({0x1000: actor, 0x4000: bytearray(0xB0),
                            0x8000: context, 0xA000: linked,
                            0xB000: bytearray(0x2A0), 0x6000: bytearray(0x80)})
        struct.pack_into('<Q', self.blocks[0x6000], 0, 0x12345678)
        result = action_setup_snapshot(self.ctx, self.read, self.u64)
        self.assertEqual('0x1000', result['setup_actor_ptr'])
        self.assertEqual('0x4000', result['setup_rdx_ptr'])
        self.assertEqual('0xb000', result['setup_linked_first_ptr'])
        self.assertEqual('0x12345678', result['setup_entry_return_address_raw'])
        self.assertNotIn('executed', result)

    def setUp(self):
        self.blocks = {}
        self.reads = []
        self.ctx = SimpleNamespace(rcx=0x1000, rdx=0x4000, r8=0x5000,
                                   r9=0xFFFFFFFFDEADBEEF, rsp=0x6000,
                                   r13=0x7000, rax=0xFFFFFFFF,
                                   r14=0x5000, rsi=0x4000, rbx=0x2000, rbp=0x3000)

    def read(self, address, size):
        self.reads.append((address, size))
        for base, block in self.blocks.items():
            offset = address - base
            if 0 <= offset and offset + size <= len(block):
                return bytes(block[offset:offset + size])
        return None

    def u64(self, address):
        raw = self.read(address, 8)
        return struct.unpack("<Q", raw)[0] if raw is not None else None

    def manager(self, count, pointer=0x9000):
        block = bytearray(0x940)
        struct.pack_into("<Q", block, 0x908, pointer)
        struct.pack_into("<i", block, 0x910, count)
        self.blocks[0x1000] = block

    def test_unknown_key_and_missing_memory_are_preserved(self):
        result = effect_dispatch_snapshot(self.ctx, self.read, self.u64)
        self.assertEqual(result["dispatch_r9_u32"], 0xDEADBEEF)
        self.assertIsNone(result["dispatch_r8_raw"])
        self.assertEqual(result["dispatch_r8_ptr"], "0x5000")
        self.assertNotIn("moveName", result)

    def test_condition_vector_is_bounded(self):
        self.manager(100000)
        self.blocks[0x9000] = bytearray(16 * 0x48)
        struct.pack_into("<I", self.blocks[0x9000], 0, 0xDEADBEEF)
        result = condition_request_snapshot(self.ctx, self.read, self.u64)
        self.assertEqual(result["condition_vector_count_raw"], 100000)
        self.assertTrue(result["condition_vector_truncated"])
        self.assertEqual(len(bytes.fromhex(result["condition_vector_raw"])), 16 * 0x48)
        self.assertEqual(struct.unpack_from("<I", bytes.fromhex(result["condition_vector_raw"]))[0],
                         0xDEADBEEF)
        self.assertFalse(any(size > 0x1000 for _, size in self.reads))

    def test_invalid_vector_does_not_read_entries(self):
        for count, pointer in ((-1, 0x9000), (10, 0)):
            with self.subTest(count=count, pointer=pointer):
                self.manager(count, pointer)
                self.reads.clear()
                result = condition_request_snapshot(self.ctx, self.read, self.u64)
                self.assertTrue(result["condition_vector_invalid"])
                self.assertIsNone(result["condition_vector_raw"])
                self.assertFalse(any(address == 0x9000 for address, _ in self.reads))

    def test_return_site_uses_preserved_r13_link(self):
        self.manager(1)
        self.blocks[0x9000] = bytearray(0x48)
        self.blocks[0x7000] = bytearray(0x600)
        struct.pack_into("<Q", self.blocks[0x7000], 0x598, 0x1000)
        self.ctx.rcx = 0xBAD0  # Volatile argument no longer describes the manager.
        result = condition_return_snapshot(self.ctx, self.read, self.u64)
        self.assertEqual(result["condition_manager_ptr"], "0x1000")
        self.assertEqual(result["condition_return_eax_raw"], 0xFFFFFFFF)
        self.assertEqual(result["condition_return_rax_ptr"], "0xffffffff")
        self.assertIsNone(result["condition_return_rax_raw"])
        self.assertEqual(result["condition_vector_count_raw"], 1)

    def test_state_links_are_captured_inline(self):
        self.blocks[0x1000] = bytearray(0x100)
        self.blocks[0x2000] = bytearray(0x1000)
        self.blocks[0x5000] = bytearray(0xB0)
        struct.pack_into("<Q", self.blocks[0x1000], 0xF0, 0x2000)
        struct.pack_into("<Q", self.blocks[0x2000], 0xC70, 0x5000)
        struct.pack_into("<I", self.blocks[0x5000], 0, 0xFFFF00AA)
        result = action_state_snapshot(self.ctx, self.read, self.u64)
        self.assertEqual(result["state_actor_c70_ptr"], "0x5000")
        self.assertEqual(struct.unpack_from("<I", bytes.fromhex(result["state_actor_c70_raw"]))[0],
                         0xFFFF00AA)
        self.assertIsNone(result["state_actor_c78_raw"])

    def test_queue_sites_use_distinct_preserved_actor_registers(self):
        self.blocks[0x2000] = bytearray(0x1000)
        self.blocks[0x3000] = bytearray(0x1000)
        self.blocks[0x5000] = bytearray(0xB0)
        struct.pack_into("<Q", self.blocks[0x2000], 0xC70, 0x5000)
        struct.pack_into("<Q", self.blocks[0x3000], 0xC78, 0x5000)
        self.ctx.r9 = 0x5000
        before = queue_transition_snapshot(self.ctx, self.read, self.u64, "store")
        resumed = queue_transition_snapshot(self.ctx, self.read, self.u64, "resume")
        self.assertEqual(before["queue_actor_ptr"], "0x2000")
        self.assertEqual(before["queue_store_r9_ptr"], "0x5000")
        self.assertIsNone(before["queue_actor_c78_ptr"])
        self.assertEqual(resumed["queue_actor_ptr"], "0x3000")
        self.assertEqual(resumed["queue_actor_c78_ptr"], "0x5000")
        self.assertNotIn("executed", resumed)


if __name__ == "__main__":
    unittest.main()
