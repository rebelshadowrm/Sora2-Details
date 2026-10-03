"""Bounded raw snapshots for exact-build action/condition research.

Pointer paths describe disassembled reads, not verified game semantics. Readers
return None on inaccessible memory. No names or executed/applied states are inferred.
"""

import struct


def blob(fields, name, pointer, size, read_bytes):
    raw = read_bytes(pointer, size) if pointer else None
    fields[name + "_ptr"] = hex(pointer) if pointer else None
    fields[name + "_raw"] = raw.hex() if raw is not None else None
    return raw


def item_record_snapshot(fields, name, pointer, descriptor, read_bytes):
    # Exact-build 23E760 creates B8-byte generated item records; 69736 reads
    # original item ID at +B0 after matching the descriptor's low-word key.
    # Collect the companion bytes only for its bounded key/kind shape.
    qualifies = (descriptor is not None and len(descriptor) == 0xB0 and
        0xFFFF0578 <= struct.unpack_from('<I', descriptor)[0] <= 0xFFFF07CF and descriptor[0x10] == 6)
    blob(fields, name + '_item_record', pointer if qualifies else None, 0xB8, read_bytes)


def descriptor_text_snapshot(fields, name, descriptor, read_bytes):
    # Exact SkillParam layout has pointer/string slots at 90/98. Runtime
    # descriptors relocate them; collect raw companions without naming moves.
    if descriptor is None or len(descriptor) != 0xB0:
        return
    for offset in (0x90, 0x98):
        address = struct.unpack_from('<Q', descriptor, offset)[0]
        blob(fields, f'{name}_slot_{offset:x}', address, 0x100, read_bytes)


def battle_mode_write_snapshot(owner, read_bytes, read_u64):
    # Exact-build C2750 stores its incoming R9D at root+2CEC. C4E30
    # iterates root+2448 with signed count +2450. These are raw candidates.
    fields = {}
    blob(fields, 'mode_root_2ce0', owner + 0x2CE0 if owner else None, 0x80, read_bytes)
    count_raw = read_bytes(owner + 0x2450, 4) if owner else None
    count = struct.unpack('<i', count_raw)[0] if count_raw is not None and len(count_raw) == 4 else None
    roster = read_u64(owner + 0x2448) if owner else None
    fields.update(mode_roster_count_raw=count, mode_roster_ptr=hex(roster) if roster else None,
                  mode_roster_truncated=count is not None and count > 16,
                  mode_roster_candidates=[])
    if count is None or count < 0 or not roster:
        return fields
    for index in range(min(count, 16)):
        actor = read_u64(roster + index * 8)
        row = {'index': index}
        blob(row, 'actor', actor, 0x1000, read_bytes)
        context = read_u64(actor + 0x328) if actor else None
        linked = read_u64(context + 0x1D90) if context else None
        status = read_u64(linked) if linked else None
        blob(row, 'status', status, 0x2A0, read_bytes)
        fields['mode_roster_candidates'].append(row)
    return fields


def action_state_snapshot(ctx, read_bytes, read_u64):
    fields = {}
    blob(fields, "state_rcx", ctx.rcx, 0x100, read_bytes)
    actor = read_u64(ctx.rcx + 0xF0) if ctx.rcx else None
    blob(fields, "state_rcx_f0", actor, 0x1000, read_bytes)
    for offset in (0xC70, 0xC78, 0xC88):
        pointer = read_u64(actor + offset) if actor else None
        blob(fields, f"state_actor_{offset:x}", pointer, 0xB0, read_bytes)
    context = read_u64(actor + 0x328) if actor else None
    blob(fields, "state_actor_328", context, 0x400, read_bytes)
    linked = read_u64(context + 0x1D90) if context else None
    blob(fields, "state_context_1d90", linked, 0x600, read_bytes)
    blob(fields, "state_stack", ctx.rsp, 0x80, read_bytes)
    return fields


def effect_dispatch_snapshot(ctx, read_bytes, read_u64):
    fields = {"dispatch_r9_u32": ctx.r9 & 0xFFFFFFFF}
    for name, pointer, size in (("dispatch_rcx", ctx.rcx, 0x600),
                                ("dispatch_rdx", ctx.rdx, 0x600),
                                ("dispatch_r8", ctx.r8, 0xB0),
                                ("dispatch_stack", ctx.rsp, 0x80)):
        descriptor = blob(fields, name, pointer, size, read_bytes)
        if name == 'dispatch_r8':
            item_record_snapshot(fields, name, pointer, descriptor, read_bytes)
            descriptor_text_snapshot(fields, name, descriptor, read_bytes)
    for name, pointer in (("dispatch_rcx_first", ctx.rcx),
                           ("dispatch_rdx_first", ctx.rdx)):
        linked = read_u64(pointer) if pointer else None
        blob(fields, name, linked, 0x2A0, read_bytes)
    params = read_u64(ctx.rsp + 0x28) if ctx.rsp else None
    blob(fields, "dispatch_stack_28", params, 0x10, read_bytes)
    return fields


def queue_transition_snapshot(ctx, read_bytes, read_u64, site):
    # Both sites are mid-function. Register selection comes from exact-build
    # disassembly; raw stack bytes are not a native backtrace.
    actor = ctx.rbx if site == "store" else ctx.rbp
    fields = {"queue_observation_site": site}
    blob(fields, "queue_actor", actor, 0x1000, read_bytes)
    for offset in (0xC70, 0xC78, 0xC88):
        pointer = read_u64(actor + offset) if actor else None
        blob(fields, f"queue_actor_{offset:x}", pointer, 0xB0, read_bytes)
    if site == "store":
        # +0x68E20 is immediately BEFORE [RBX+0xC78] = R9.
        blob(fields, "queue_store_r9", ctx.r9, 0xB0, read_bytes)
    blob(fields, "queue_stack", ctx.rsp, 0x80, read_bytes)
    return fields


def action_setup_snapshot(ctx, read_bytes, read_u64):
    # Exact-build +0x68F80 is a function entry: RCX actor, RDX descriptor.
    # Its branches consume descriptor +0x20 for target setup. Execution semantics
    # and callback multiplicity still require live controls.
    fields = {}
    actor = ctx.rcx
    blob(fields, "setup_actor", actor, 0x1000, read_bytes)
    blob(fields, "setup_rdx", ctx.rdx, 0xB0, read_bytes)
    for offset in (0xC70, 0xC78, 0xC88):
        linked = read_u64(actor + offset) if actor else None
        blob(fields, f"setup_actor_{offset:x}", linked, 0xB0, read_bytes)
    context = read_u64(actor + 0x328) if actor else None
    blob(fields, "setup_actor_328", context, 0x400, read_bytes)
    linked = read_u64(context + 0x1D90) if context else None
    blob(fields, "setup_context_1d90", linked, 0x600, read_bytes)
    status = read_u64(linked) if linked else None
    blob(fields, "setup_linked_first", status, 0x2A0, read_bytes)
    blob(fields, "setup_stack", ctx.rsp, 0x80, read_bytes)
    returned = read_u64(ctx.rsp) if ctx.rsp else None
    fields["setup_entry_return_address_raw"] = hex(returned) if returned else None
    return fields


def accepted_launch_owner(caller_rva, stack_raw):
    # EBX is overwritten at +0x2153A8. Use caller nonvolatile values saved
    # in this function's frame, scoped to statically verified actor callers.
    if stack_raw is None or len(stack_raw) != 0x80:
        return None
    if caller_rva == 0x686F1:
        return struct.unpack_from('<Q', stack_raw, 0x60)[0] or None  # Caller RSI actor.
    saved = struct.unpack_from('<Q', stack_raw, 0x70)[0]
    if caller_rva in (0x68E8B, 0x69638):
        return saved or None  # Caller RBX actor.
    if caller_rva == 0x69311 and saved > 0xC70:
        return saved - 0xC70  # Caller RBX = actor + 0xC70.
    return None


def animation_launch_snapshot(ctx, read_bytes, read_u64, site, module_base=None):
    # +0x215320 saves RCX in RBX initially, but +0x2153A8 overwrites EBX.
    # RDI retains the script. Recover owners only through verified caller frames.
    # Two pushes and sub RSP,0x68 put the original return slot at RSP+0x78.
    script = ctx.r8 if site == "request" else ctx.rdi
    entry_stack = ctx.rsp if site == "request" else ctx.rsp + 0x78
    fields = {"launch_site": site, "launch_entry_stack_pointer_raw": hex(entry_stack)}
    stack_raw = blob(fields, "launch_stack", ctx.rsp, 0x80, read_bytes)
    caller = read_u64(entry_stack) if entry_stack else None
    fields["launch_caller_raw"] = hex(caller) if caller else None
    caller_rva = caller - module_base if caller and module_base else None
    recovered_actor = accepted_launch_owner(caller_rva, stack_raw) if site == 'accepted' else None
    context = ctx.rcx if site == 'request' else read_u64(recovered_actor + 0x328) if recovered_actor else None
    fields['launch_owner_recovery'] = 'entry-context' if site == 'request' else 'verified-caller-saved-registers' if recovered_actor else 'unknown-caller-or-frame'
    blob(fields, "launch_context", context, 0x400, read_bytes)
    blob(fields, "launch_script", script, 0x100, read_bytes)
    actor = read_u64(context + 0x1D88) if context else None
    actor_raw = blob(fields, "launch_actor", actor, 0x1000, read_bytes)
    back_link = (struct.unpack_from('<Q', actor_raw, 0x328)[0]
                 if actor_raw is not None and len(actor_raw) >= 0x330 else None)
    fields["launch_actor_328_ptr_raw"] = hex(back_link) if back_link else None
    fields["launch_owner_link_matches"] = back_link == context if back_link is not None else None
    for offset in (0xC70, 0xC78, 0xC88):
        linked = read_u64(actor + offset) if actor else None
        blob(fields, f"launch_actor_{offset:x}", linked, 0xB0, read_bytes)
    linked = read_u64(context + 0x1D90) if context else None
    blob(fields, "launch_context_1d90", linked, 0x600, read_bytes)
    status = read_u64(linked) if linked else None
    blob(fields, "launch_linked_first", status, 0x2A0, read_bytes)
    fields['launch_recovered_owner_matches'] = actor == recovered_actor if recovered_actor else None
    if site == "request":
        fields["launch_channel_u32_raw"] = ctx.rdx & 0xFFFFFFFF
    else:
        fields["launch_queue_pointer_raw"] = hex(ctx.rsi) if ctx.rsi else None
    return fields


def first_actor_state_update(ctx, read_bytes, read_u64):
    """False only for a verified actor callback after its first update.

    Inaccessible or unfamiliar layouts return None and remain raw observations.
    +0x7A68B has RCX owner, RBX embedded machine and RSI selected state row base.
    """
    if not ctx.rcx or ctx.rbx != ctx.rcx + 0x88 or read_u64(ctx.rbx) != ctx.rcx:
        return None
    offset = ctx.rsi - ctx.rbx
    if offset < 0 or offset % 12 or offset // 12 >= 4:
        return None
    raw = read_bytes(ctx.rsi + 0x1D8, 4)
    if raw is None or len(raw) != 4:
        return None
    phase = struct.unpack('<i', raw)[0]
    return phase == 0 if phase >= 0 else None


def actor_state_dispatch_snapshot(ctx, read_bytes, read_u64):
    fields = {'actor_state_first_update_candidate': first_actor_state_update(ctx, read_bytes, read_u64),
              'actor_state_id_rax_raw': hex(ctx.rax)}
    blob(fields, 'actor_state_machine', ctx.rbx, 0x220, read_bytes)
    blob(fields, 'actor_state_row', ctx.rsi + 0x1D0, 12, read_bytes)
    blob(fields, 'actor_state_owner', ctx.rcx, 0x1000, read_bytes)
    selected = read_u64(ctx.rbx + ctx.rax * 8 + 8) if 0 <= ctx.rax < 57 else None
    fields['actor_state_handler_ptr_raw'] = hex(selected) if selected else None
    for offset in (0xC70, 0xC78, 0xC88):
        linked = read_u64(ctx.rcx + offset) if ctx.rcx else None
        descriptor = blob(fields, f'actor_state_owner_{offset:x}', linked, 0xB0, read_bytes)
        if offset == 0xC70:
            item_record_snapshot(fields, 'actor_state_owner_c70', linked, descriptor, read_bytes)
            descriptor_text_snapshot(fields, 'actor_state_owner_c70', descriptor, read_bytes)
    context = read_u64(ctx.rcx + 0x328) if ctx.rcx else None
    blob(fields, 'actor_state_owner_328', context, 0x400, read_bytes)
    linked = read_u64(context + 0x1D90) if context else None
    blob(fields, 'actor_state_context_1d90', linked, 0x600, read_bytes)
    status = read_u64(linked) if linked else None
    blob(fields, 'actor_state_linked_first', status, 0x2A0, read_bytes)
    blob(fields, 'actor_state_stack', ctx.rsp, 0x80, read_bytes)
    return fields


def condition_vector_snapshot(manager, read_bytes):
    fields = {}
    raw = blob(fields, "condition_manager", manager, 0x940, read_bytes)
    pointer = count = None
    if raw is not None and len(raw) >= 0x914:
        pointer = struct.unpack_from("<Q", raw, 0x908)[0]
        count = struct.unpack_from("<i", raw, 0x910)[0]
    fields["condition_vector_count_raw"] = count
    fields["condition_vector_limit"] = 16
    captured = min(count, 16) if count is not None and count >= 0 and pointer else 0
    fields["condition_vector_requested_records"] = captured
    fields["condition_vector_truncated"] = count is not None and count > 16
    fields["condition_vector_invalid"] = count is not None and (count < 0 or (count > 0 and not pointer))
    blob(fields, "condition_vector", pointer, captured * 0x48, read_bytes) if captured else fields.update(
        condition_vector_ptr=hex(pointer) if pointer else None, condition_vector_raw=None)
    return fields


def condition_request_snapshot(ctx, read_bytes, read_u64):
    fields = condition_vector_snapshot(ctx.rcx, read_bytes)
    fields["condition_r9_u32"] = ctx.r9 & 0xFFFFFFFF
    fields['condition_request_frame_raw'] = hex(ctx.rsp)
    for name, pointer, size in (("condition_rdx", ctx.rdx, 0x400),
                                ("condition_r8", ctx.r8, 0xB0),
                                ("condition_stack", ctx.rsp, 0x80)):
        blob(fields, name, pointer, size, read_bytes)
    return fields


def condition_remove_snapshot(ctx, read_bytes, read_u64, site='entry', module_base=None):
    # 80730 pushes five registers then subtracts A0; 80780 is the common
    # epilogue before stack restoration. RSI retains manager on both routes.
    manager = ctx.rcx if site == 'entry' else ctx.rsi
    fields = condition_vector_snapshot(manager, read_bytes)
    fields['condition_remove_frame_raw'] = hex(ctx.rsp if site == 'entry' else ctx.rsp + 0xC8)
    if site == 'entry':
        fields['condition_remove_key_raw'] = ctx.rdx & 0xFFFFFFFF
        fields['condition_remove_r8b_raw'] = ctx.r8 & 0xFF
        fields['condition_remove_r9b_raw'] = ctx.r9 & 0xFF
        caller = read_u64(ctx.rsp)
        fields['condition_remove_caller_raw'] = hex(caller) if caller else None
        caller_rva = caller - module_base if caller and module_base else None
        if caller_rva in (0xDF127, 0xDF207) and read_u64(ctx.r13 + 0x598) == manager:
            # Exact dispatcher cure loops retain descriptor R14 and source
            # effect context RSI at removal function entry. Do not read these
            # as identities on expiry/bulk-clear callers.
            fields['condition_remove_identity_route'] = hex(caller_rva)
            fields['condition_remove_dispatch_manager_ptr'] = hex(manager)
            blob(fields, 'condition_remove_descriptor', ctx.r14, 0xB0, read_bytes)
            blob(fields, 'condition_remove_source_context', ctx.rsi, 0x600, read_bytes)
            source_status = read_u64(ctx.rsi) if ctx.rsi else None
            blob(fields, 'condition_remove_source_status', source_status, 0x2A0, read_bytes)
    else:
        fields['condition_remove_return_al_raw'] = ctx.rax & 0xFF
    target = read_u64(manager) if manager else None
    blob(fields, 'condition_remove_target_context', target, 0x400, read_bytes)
    linked = read_u64(target + 0x1D90) if target else None
    status = read_u64(linked) if linked else None
    blob(fields, 'condition_remove_target_status', status, 0x2A0, read_bytes)
    return fields


def condition_return_snapshot(ctx, read_bytes, read_u64, site='dispatch', module_base=None):
    if site in ('remove-entry', 'remove-return'):
        return condition_remove_snapshot(ctx, read_bytes, read_u64, 'entry' if site == 'remove-entry' else 'return', module_base)
    if site in ('insert', 'common'):
        # +7FD63 follows +7FD5E -> 7FE10. R15 is the manager, R12 the
        # descriptor, and original source context is saved at RSP+60.
        # This route covers attempted insertion, not refresh/removal coverage.
        fields = condition_vector_snapshot(ctx.r15, read_bytes)
        fields['condition_return_eax_raw'] = ctx.rax & 0xFFFFFFFF
        fields['condition_insert_key_raw'] = ctx.rbp & 0xFFFFFFFF
        fields['condition_return_site'] = 'native-7FD63-after-7FE10'
        if site == 'common':
            # 7FDE7 precedes restoration of eight saved registers and 1B8
            # stack bytes. It covers early null returns as well as insertion.
            fields['condition_return_site'] = 'native-7FDE7-common-7F750-return'
            fields['condition_request_frame_raw'] = hex(ctx.rsp + 0x1F8)
        blob(fields, 'condition_return_rax', ctx.rax, 0x48, read_bytes)
        blob(fields, 'condition_insert_descriptor', ctx.r12, 0xB0, read_bytes)
        source = read_u64(ctx.rsp + 0x60) if ctx.rsp else None
        target = read_u64(ctx.r15) if ctx.r15 else None
        blob(fields, 'condition_insert_source_context', source, 0x400, read_bytes)
        blob(fields, 'condition_insert_target_context', target, 0x400, read_bytes)
        for name, context in [('condition_insert_source_status', source),
                              ('condition_insert_target_status', target)]:
            linked = read_u64(context + 0x1D90) if context else None
            status = read_u64(linked) if linked else None
            blob(fields, name, status, 0x2A0, read_bytes)
        return fields
    # +0xDE962 follows the call at +0xDE95D. R13 remains the dispatch
    # context; volatile argument registers no longer describe entry arguments.
    manager = read_u64(ctx.r13 + 0x598) if ctx.r13 else None
    fields = condition_vector_snapshot(manager, read_bytes)
    fields["condition_return_eax_raw"] = ctx.rax & 0xFFFFFFFF
    # The candidate routine can return a record pointer. Preserve full RAX
    # alongside its low word rather than interpreting the low word as a code.
    blob(fields, "condition_return_rax", ctx.rax, 0x48, read_bytes)
    blob(fields, "condition_return_r13", ctx.r13, 0x600, read_bytes)
    # Nonvolatile R14/RSI still hold the dispatcher descriptor/context here.
    blob(fields, "condition_return_r14", ctx.r14, 0xB0, read_bytes)
    blob(fields, "condition_return_rsi", ctx.rsi, 0x600, read_bytes)
    return fields
