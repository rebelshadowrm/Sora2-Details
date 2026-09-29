"""Short-lived x64 hardware execution-breakpoint probe for battle lifecycle research.

Attaching a debugger briefly stops the target. This records candidate function hits;
it does not identify battle outcomes or prove that a name is a correct boundary.
The game executable SHA-256 is checked before attachment. No game files or code
bytes are modified. Run only for a controlled test, not routine play.
"""

import argparse
import ctypes as ct
from ctypes import wintypes as wt
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import struct
import sys
import time

from match_enemy_status import status_signature, table_signature
from status_name_index import read_rows as read_enemy_rows


if sys.platform != "win32" or ct.sizeof(ct.c_void_p) != 8:
    raise SystemExit("This probe requires 64-bit Windows Python.")

kernel32 = ct.WinDLL("kernel32", use_last_error=True)
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_DEBUG_EVENT = 1
CREATE_THREAD_DEBUG_EVENT = 2
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_THREAD_DEBUG_EVENT = 4
EXIT_PROCESS_DEBUG_EVENT = 5
LOAD_DLL_DEBUG_EVENT = 6
STATUS_BREAKPOINT = 0x80000003
STATUS_SINGLE_STEP = 0x80000004
ERROR_SEM_TIMEOUT = 121
CONTEXT_AMD64 = 0x00100000
CONTEXT_CONTROL = CONTEXT_AMD64 | 0x1
CONTEXT_INTEGER = CONTEXT_AMD64 | 0x2
CONTEXT_DEBUG_REGISTERS = CONTEXT_AMD64 | 0x10


class EventData(ct.Union):
    _fields_ = [("bytes", ct.c_ubyte * 160), ("alignment", ct.c_uint64 * 20)]


class DebugEvent(ct.Structure):
    _fields_ = [("code", wt.DWORD), ("pid", wt.DWORD), ("tid", wt.DWORD), ("data", EventData)]


class ContextPrefix(ct.Structure):
    _fields_ = [
        *((f"home_{index}", ct.c_uint64) for index in range(6)),
        ("flags", wt.DWORD), ("mxcsr", wt.DWORD),
        *((f"seg_{name}", wt.WORD) for name in ("cs", "ds", "es", "fs", "gs", "ss")),
        ("eflags", wt.DWORD),
        *((name, ct.c_uint64) for name in (
            "dr0", "dr1", "dr2", "dr3", "dr6", "dr7", "rax", "rcx", "rdx", "rbx",
            "rsp", "rbp", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13",
            "r14", "r15", "rip")),
    ]


assert ct.sizeof(DebugEvent) == 176 and DebugEvent.data.offset == 16
assert ContextPrefix.dr0.offset == 72 and ContextPrefix.rip.offset == 248

kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
kernel32.OpenProcess.restype = wt.HANDLE
kernel32.CloseHandle.argtypes = [wt.HANDLE]
kernel32.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, ct.POINTER(wt.DWORD)]
kernel32.QueryFullProcessImageNameW.restype = wt.BOOL
kernel32.DebugSetProcessKillOnExit.argtypes = [wt.BOOL]
kernel32.DebugSetProcessKillOnExit.restype = wt.BOOL
kernel32.DebugActiveProcess.argtypes = [wt.DWORD]
kernel32.DebugActiveProcess.restype = wt.BOOL
kernel32.DebugActiveProcessStop.argtypes = [wt.DWORD]
kernel32.DebugActiveProcessStop.restype = wt.BOOL
kernel32.WaitForDebugEvent.argtypes = [ct.POINTER(DebugEvent), wt.DWORD]
kernel32.WaitForDebugEvent.restype = wt.BOOL
kernel32.ContinueDebugEvent.argtypes = [wt.DWORD, wt.DWORD, wt.DWORD]
kernel32.ContinueDebugEvent.restype = wt.BOOL
kernel32.GetThreadContext.argtypes = [wt.HANDLE, ct.c_void_p]
kernel32.GetThreadContext.restype = wt.BOOL
kernel32.SetThreadContext.argtypes = [wt.HANDLE, ct.c_void_p]
kernel32.SetThreadContext.restype = wt.BOOL
kernel32.DebugBreakProcess.argtypes = [wt.HANDLE]
kernel32.DebugBreakProcess.restype = wt.BOOL
kernel32.ReadProcessMemory.argtypes = [wt.HANDLE, ct.c_void_p, ct.c_void_p,
                                       ct.c_size_t, ct.POINTER(ct.c_size_t)]
kernel32.ReadProcessMemory.restype = wt.BOOL


def checked(result, operation):
    if not result:
        raise OSError(ct.get_last_error(), operation)
    return result


def image_path(pid):
    handle = checked(kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid), "OpenProcess")
    try:
        size = wt.DWORD(32768)
        buffer = ct.create_unicode_buffer(size.value)
        checked(kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ct.byref(size)),
                "QueryFullProcessImageNameW")
        return buffer.value
    finally:
        kernel32.CloseHandle(handle)


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        while chunk := file.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest().upper()


def context(handle, flags=CONTEXT_DEBUG_REGISTERS | CONTEXT_CONTROL | CONTEXT_INTEGER):
    # Win64 CONTEXT needs 16-byte alignment and room for its vector registers.
    storage = ct.create_string_buffer(1248)
    address = (ct.addressof(storage) + 15) & ~15
    prefix = ct.cast(address, ct.POINTER(ContextPrefix)).contents
    prefix.flags = flags
    checked(kernel32.GetThreadContext(handle, ct.c_void_p(address)), "GetThreadContext")
    return storage, address, prefix


def set_context(handle, address, prefix, control=False):
    prefix.flags = CONTEXT_DEBUG_REGISTERS | (CONTEXT_CONTROL if control else 0)
    checked(kernel32.SetThreadContext(handle, ct.c_void_p(address)), "SetThreadContext")


def event_pointer(event, offset):
    return ct.c_uint64.from_address(ct.addressof(event) + DebugEvent.data.offset + offset).value


def exception_code(event):
    return ct.c_uint32.from_address(ct.addressof(event) + DebugEvent.data.offset).value


def emit(kind, **fields):
    print(json.dumps({"at": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                      "kind": kind, **fields}), flush=True)


def parse_named_address(value):
    name, separator, number = value.partition("=")
    if not separator or not name or not number:
        raise argparse.ArgumentTypeError("use NAME=0xADDRESS or NAME=0xRVA")
    try:
        address = int(number, 0)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error
    if address < 0:
        raise argparse.ArgumentTypeError("addresses must be positive")
    return name, address


def enemy_signature_index(rows):
    index = {}
    for row in rows:
        index.setdefault(table_signature(row), []).append(row["unitId"])
    return index


def enemy_lookup_gap(status_bytes, signatures):
    """Decide whether an exact, hash-gated table lookup needs more live evidence."""
    if status_bytes is None or len(status_bytes) < 0x44:
        return None, []
    runtime_id = struct.unpack_from("<I", status_bytes)[0]
    if runtime_id < 60000:
        return None, []
    candidates = signatures.get(status_signature(status_bytes), [])
    if len(candidates) == 1:
        return None, candidates
    return ("enemy-unit-key-ambiguous" if candidates else "enemy-unit-key-missing"), candidates


def trace(pid, specs, seconds, use_rvas, max_hits, write_specs=(),
          hp_set_names=(), effect_entry_names=(), attack_call_names=(),
          actor_bytes_names=(), actor_identity_names=(),
          result_frame_names=(), effect_descriptor_names=(), turn_context_names=(),
          result_entry_names=(), critical_popup_names=(),
          stop_file=None, enemy_signatures=None):
    threads = {}
    originals = {}
    module_base = None
    debug_process_handle = None
    read_process_handle = None
    addresses = None
    attached = False
    installed = False
    initial_break_seen = False
    stop_break_requested = False
    stop_break_seen = False
    drain_until = None
    exited = False
    hit_count = 0
    prior_values = {}
    identity_seen = set()
    heal_diagnostics = 0
    heal_diagnostic_limit = 16  # Per battle; each read is bounded to 256 bytes.
    descriptor_diagnostics = 0
    descriptor_diagnostic_limit = 8
    enemy_diagnostics = set()
    enemy_diagnostic_limit = 8
    enemy_signatures = enemy_signatures or {}

    def read_bytes(address, count):
        if read_process_handle is None:
            return None
        buffer = ct.create_string_buffer(count)
        size = ct.c_size_t()
        if not kernel32.ReadProcessMemory(read_process_handle, ct.c_void_p(address),
                                          buffer, count, ct.byref(size)) or size.value != count:
            return None
        return buffer.raw

    def read_i32(address):
        data = read_bytes(address, 4)
        return struct.unpack("<i", data)[0] if data is not None else None

    def read_u64(address):
        data = read_bytes(address, 8)
        return struct.unpack("<Q", data)[0] if data is not None else None

    def install(tid, handle):
        nonlocal installed
        storage, address, ctx = context(handle)
        original = (ctx.dr0, ctx.dr1, ctx.dr2, ctx.dr3, ctx.dr6, ctx.dr7)
        if ctx.dr7 & 0xFF:
            raise RuntimeError(f"Thread {tid} already uses hardware debug slots.")
        # Four x86 debug slots; each uses its local enable bit for execution.
        for slot, (_, watched) in enumerate(addresses):
            setattr(ctx, f"dr{slot}", watched)
            ctx.dr7 &= ~(0xF << (16 + 4 * slot))
            if slot >= len(specs):
                # DR7 R/W=01 (write), LEN=11 (four bytes).
                ctx.dr7 |= 0xD << (16 + 4 * slot)
            ctx.dr7 |= 1 << (2 * slot)
        ctx.dr6 = 0
        set_context(handle, address, ctx)
        originals[tid] = original
        installed = True

    def clear_all():
        failures = []
        for tid, original in list(originals.items()):
            handle = threads.get(tid)
            if handle is None:
                continue
            try:
                storage, address, ctx = context(handle)
                ctx.dr0, ctx.dr1, ctx.dr2, ctx.dr3, ctx.dr6, ctx.dr7 = original
                set_context(handle, address, ctx)
            except OSError as error:
                failures.append(f"thread {tid}: {error}")
        if failures:
            emit("restore_error", details=failures)
        return not failures

    # Open the least-privilege memory handle before attaching so a denied read
    # request cannot leave the game paused in an initial debug event.
    read_process_handle = checked(
        kernel32.OpenProcess(PROCESS_VM_READ, False, pid),
        "OpenProcess(PROCESS_VM_READ)")
    try:
        checked(kernel32.DebugActiveProcess(pid), "DebugActiveProcess")
    except Exception:
        kernel32.CloseHandle(read_process_handle)
        read_process_handle = None
        raise
    attached = True
    try:
        checked(kernel32.DebugSetProcessKillOnExit(False), "DebugSetProcessKillOnExit")
    except OSError:
        kernel32.DebugActiveProcessStop(pid)
        attached = False
        kernel32.CloseHandle(read_process_handle)
        read_process_handle = None
        raise
    emit("attached", pid=pid)
    deadline = time.monotonic() + seconds
    try:
        while not exited:
            if drain_until is not None and time.monotonic() >= drain_until:
                break
            if stop_file is not None and stop_file.exists():
                deadline = time.monotonic()
            if time.monotonic() >= deadline and not stop_break_requested:
                if debug_process_handle and installed:
                    checked(kernel32.DebugBreakProcess(debug_process_handle), "DebugBreakProcess")
                    stop_break_requested = True
                else:
                    break
            event = DebugEvent()
            if not kernel32.WaitForDebugEvent(ct.byref(event), 100):
                error = ct.get_last_error()
                if error == ERROR_SEM_TIMEOUT:
                    continue
                raise OSError(error, "WaitForDebugEvent")
            status = DBG_CONTINUE
            if event.code == CREATE_PROCESS_DEBUG_EVENT:
                # DebugActiveProcess supplies a debugger process handle with both
                # PROCESS_VM_READ and PROCESS_VM_WRITE. Keep it for debugger control;
                # memory inspection uses the earlier PROCESS_VM_READ-only handle.
                debug_process_handle = event_pointer(event, 8)
                threads[event.tid] = event_pointer(event, 16)
                module_base = event_pointer(event, 24)
                addresses = ([(name, module_base + value if use_rvas else value)
                              for name, value in specs] + list(write_specs))
                if any(address == 0 for _, address in addresses):
                    raise ValueError("Zero breakpoint address")
                if any(address % 4 for _, address in write_specs):
                    raise ValueError("Four-byte write breakpoint addresses must be aligned")
                prior_values = {name: read_i32(address) for name, address in write_specs}
                emit("module", base=hex(module_base), breakpoints={name: hex(value) for name, value in addresses})
                if write_specs:
                    emit("write_baseline", values=prior_values)
                image_file = event_pointer(event, 0)
                if image_file:
                    kernel32.CloseHandle(image_file)
            elif event.code == CREATE_THREAD_DEBUG_EVENT:
                handle = event_pointer(event, 0)
                threads[event.tid] = handle
                if initial_break_seen and drain_until is None:
                    install(event.tid, handle)
            elif event.code == EXIT_THREAD_DEBUG_EVENT:
                thread_handle = threads.pop(event.tid, None)
                if thread_handle:
                    kernel32.CloseHandle(thread_handle)
                originals.pop(event.tid, None)
            elif event.code == EXIT_PROCESS_DEBUG_EVENT:
                exited = True
                emit("target_exited")
            elif event.code == LOAD_DLL_DEBUG_EVENT:
                image_file = event_pointer(event, 0)
                if image_file:
                    kernel32.CloseHandle(image_file)
            elif event.code == EXCEPTION_DEBUG_EVENT:
                code = exception_code(event)
                if code == STATUS_BREAKPOINT and not initial_break_seen:
                    initial_break_seen = True
                    for tid, handle in list(threads.items()):
                        install(tid, handle)
                    emit("armed", threads=len(threads))
                elif code == STATUS_BREAKPOINT and stop_break_requested:
                    if not clear_all():
                        raise RuntimeError("Unable to restore every thread debug register")
                    stop_break_seen = True
                    drain_until = time.monotonic() + 0.3
                    emit("disarmed")
                elif code == STATUS_SINGLE_STEP and event.tid in threads:
                    handle = threads[event.tid]
                    storage, address, ctx = context(handle)
                    slots = [slot for slot in range(len(addresses)) if ctx.dr6 & (1 << slot)]
                    if not slots:
                        if drain_until is not None and event.tid in originals:
                            # An execution-breakpoint exception may already be queued
                            # when DR6 is restored. Drain it before detaching.
                            emit("drained_single_step", tid=event.tid, rip=hex(ctx.rip))
                        else:
                            status = DBG_EXCEPTION_NOT_HANDLED
                    else:
                        if drain_until is None:
                            for slot in slots:
                                hit_count += 1
                                name, watched = addresses[slot]
                                fields = dict(name=name, tid=event.tid, rip=hex(ctx.rip),
                                              rva=hex(ctx.rip - module_base),
                                              rcx=hex(ctx.rcx), rdx=hex(ctx.rdx),
                                              r8=hex(ctx.r8), r9=hex(ctx.r9),
                                              rsi=hex(ctx.rsi), r12=hex(ctx.r12),
                                              r14=hex(ctx.r14), rdi=hex(ctx.rdi))
                                if name == "BattleInit":
                                    heal_diagnostics = 0
                                    descriptor_diagnostics = 0
                                    enemy_diagnostics.clear()
                                    identity_seen.clear()
                                if name in hp_set_names:
                                    # Preserve bounded frame evidence for later heal-path
                                    # research. This hook is inside the setter, so neither
                                    # stack address is yet a verified action/source link.
                                    hp_stack = read_bytes(ctx.rsp, 64)
                                    frame_return = read_u64(ctx.rbp + 8)
                                    fields.update(status_ptr=hex(ctx.rsi),
                                                  status_actor_id=read_i32(ctx.rsi),
                                                  hp_before=read_i32(ctx.rsi + 0xC),
                                                  hp_max=read_i32(ctx.rsi + 0x10),
                                                  requested_hp=ct.c_int32(ctx.r14 & 0xFFFFFFFF).value,
                                                  hp_rsp=hex(ctx.rsp),
                                                  hp_rbp=hex(ctx.rbp),
                                                  hp_stack_64=(hp_stack.hex()
                                                               if hp_stack is not None else None),
                                                  hp_frame_return_candidate=(hex(frame_return)
                                                                             if frame_return is not None else None))
                                    if (isinstance(fields["hp_before"], int)
                                            and isinstance(fields["hp_max"], int)
                                            and fields["hp_before"] < min(fields["hp_max"],
                                                                          fields["requested_hp"])
                                            and heal_diagnostics < heal_diagnostic_limit):
                                        # A positive HP write cannot pair with the verified
                                        # damaging result path. Read while this setter is paused;
                                        # bridge-side lookup runs after the memory can change.
                                        deep_stack = read_bytes(ctx.rsp, 256)
                                        deep_frame = read_bytes(ctx.rbp - 0x80, 256)
                                        fields["diagnostic_snapshot"] = {
                                            "trigger": "hp-write-without-attack-result",
                                            "stack_256": (deep_stack.hex() if deep_stack is not None else None),
                                            "frame_base": hex(ctx.rbp - 0x80),
                                            "frame_256": (deep_frame.hex() if deep_frame is not None else None),
                                            "ordinal": heal_diagnostics + 1,
                                            "limit_per_battle": heal_diagnostic_limit}
                                        heal_diagnostics += 1
                                if name in critical_popup_names:
                                    # Command-battle caller at RVA 0x116EE0 passes a
                                    # stack popup object in RDX. Its +0x78 enum is
                                    # assigned 9 immediately before this call.
                                    fields.update(popup_type=read_i32(ctx.rdx + 0x78),
                                                  popup_flags=read_i32(ctx.rdx + 0x70),
                                                  source_battle_object=hex(ctx.rsi),
                                                  target_battle_object=hex(ctx.rdi))
                                if name in turn_context_names:
                                    turn_bytes = read_bytes(ctx.r9, 0x400)
                                    fields.update(turn_object=hex(ctx.r9),
                                                  turn_object_400=(turn_bytes.hex()
                                                                   if turn_bytes is not None else None))
                                    if name == "BattleCommandBegin":
                                        actor_bytes = read_bytes(ctx.rcx, 0x400)
                                        active_command = read_u64(ctx.rdi + 0x2C30)
                                        active_bytes = (read_bytes(active_command, 0x400)
                                                        if active_command else None)
                                        fields.update(candidate_actor_object=hex(ctx.rcx),
                                                      actor_object_400=(actor_bytes.hex()
                                                                        if actor_bytes is not None else None),
                                                      active_command_ptr=(hex(active_command)
                                                                          if active_command is not None else None),
                                                      active_command_400=(active_bytes.hex()
                                                                          if active_bytes is not None else None))
                                if name in effect_entry_names:
                                    words = read_bytes(ctx.rcx, 128)
                                    target = read_u64(ctx.rcx)
                                    link_590 = read_u64(ctx.rcx + 0x590)
                                    link_5a8 = read_u64(ctx.rcx + 0x5A8)
                                    return_address = read_u64(ctx.rsp)
                                    fields.update(effect_context=hex(ctx.rcx),
                                                  signed_delta=ct.c_int32(ctx.rdx & 0xFFFFFFFF).value,
                                                  target_status_ptr=hex(target) if target is not None else None,
                                                  link_590=hex(link_590) if link_590 is not None else None,
                                                  link_5a8=hex(link_5a8) if link_5a8 is not None else None,
                                                  return_address=hex(return_address)
                                                  if return_address is not None else None,
                                                  context_words=[hex(word) for word in struct.unpack("<16Q", words)]
                                                  if words is not None else None)
                                if name in result_entry_names:
                                    target_status = read_u64(ctx.rcx)
                                    candidate_source_status = read_u64(ctx.rdx)
                                    candidate_source = read_bytes(ctx.rdx, 0x100)
                                    auxiliary = read_bytes(ctx.r8, 0x100)
                                    fields.update(result_arg_flags=ctx.r9 & 0xFFFFFFFF,
                                                  candidate_source_context=hex(ctx.rdx),
                                                  candidate_source_context_100=(candidate_source.hex()
                                                                                if candidate_source is not None else None),
                                                  auxiliary_context=hex(ctx.r8),
                                                  auxiliary_context_100=(auxiliary.hex()
                                                                         if auxiliary is not None else None),
                                                  target_status_ptr=(hex(target_status)
                                                                     if target_status else None),
                                                  target_actor_id=(read_i32(target_status)
                                                                   if target_status else None),
                                                  candidate_source_status_ptr=(hex(candidate_source_status)
                                                                               if candidate_source_status else None),
                                                  candidate_source_actor_id=(read_i32(candidate_source_status)
                                                                             if candidate_source_status else None))
                                if name in attack_call_names:
                                    source_status = read_u64(ctx.r12)
                                    target_status = read_u64(ctx.rsi)
                                    fields.update(source_context=hex(ctx.r12),
                                                  source_status_ptr=hex(source_status)
                                                  if source_status is not None else None,
                                                  source_actor_id=(read_i32(source_status)
                                                                   if source_status else None),
                                                  target_context=hex(ctx.rsi),
                                                  target_status_ptr=hex(target_status)
                                                  if target_status is not None else None,
                                                  target_actor_id=(read_i32(target_status)
                                                                   if target_status else None),
                                                  candidate_resolved_amount=ct.c_int32(ctx.rdi & 0xFFFFFFFF).value,
                                                  candidate_result_flags=read_i32(ctx.rbp - 0x58))
                                    if name in result_frame_names:
                                        frame_base = ctx.rbp - 0x100
                                        frame = read_bytes(frame_base, 0x200)
                                        fields.update(result_frame_base=hex(frame_base),
                                                      result_frame_200=(frame.hex()
                                                                        if frame is not None else None))
                                    if name in effect_descriptor_names:
                                        # This exact result function saved its entry R8 at
                                        # [rsp+0x70], where rsp == rbp-0x100. At RVA
                                        # 0xE343B it reads [saved R8+8] into the result
                                        # flags. Keep the object raw until its layout and
                                        # relationship to a selected move are verified.
                                        descriptor = read_u64(ctx.rbp - 0x90)
                                        raw = read_bytes(descriptor, 0x100) if descriptor else None
                                        fields.update(effect_descriptor_ptr=(hex(descriptor)
                                                                             if descriptor else None),
                                                      effect_descriptor_100=(raw.hex()
                                                                             if raw is not None else None))
                                        if raw is None and descriptor_diagnostics < descriptor_diagnostic_limit:
                                            frame = read_bytes(ctx.rbp - 0x100, 0x200)
                                            fields["diagnostic_snapshot"] = {
                                                "trigger": "effect-descriptor-missing",
                                                "result_frame_base": hex(ctx.rbp - 0x100),
                                                "result_frame_200": (frame.hex() if frame is not None else None),
                                                "ordinal": descriptor_diagnostics + 1,
                                                "limit_per_battle": descriptor_diagnostic_limit}
                                            descriptor_diagnostics += 1
                                    if name in actor_bytes_names:
                                        for prefix, context_ptr, status_ptr in (
                                                ("source", ctx.r12, source_status),
                                                ("target", ctx.rsi, target_status)):
                                            context_data = read_bytes(context_ptr, 256)
                                            status_data = read_bytes(status_ptr, 256) if status_ptr else None
                                            fields[f"{prefix}_context_256"] = (
                                                context_data.hex() if context_data is not None else None)
                                            fields[f"{prefix}_status_256"] = (
                                                status_data.hex() if status_data is not None else None)
                                    if name in actor_identity_names:
                                        snapshots = []
                                        for role, context_ptr, status_ptr in (
                                                ("source", ctx.r12, source_status),
                                                ("target", ctx.rsi, target_status)):
                                            if not status_ptr or status_ptr in identity_seen:
                                                continue
                                            context_data = read_bytes(context_ptr, 0x600)
                                            status_data = read_bytes(status_ptr, 0x2A0)
                                            if context_data is not None and status_data is not None:
                                                identity_seen.add(status_ptr)
                                            links = []
                                            if context_data is not None:
                                                for offset in (8, 0x590, 0x598, 0x5A8, 0x5B0):
                                                    pointer = struct.unpack_from("<Q", context_data, offset)[0]
                                                    linked = read_bytes(pointer, 256) if pointer else None
                                                    item = {"offset": hex(offset),
                                                            "pointer": hex(pointer),
                                                            "bytes_256": linked.hex() if linked else None}
                                                    if offset == 0x590 and pointer:
                                                        distant = read_bytes(pointer + 0x1D80, 256)
                                                        actor_pointer = (struct.unpack_from("<Q", distant, 8)[0]
                                                                         if distant is not None else None)
                                                        actor = (read_bytes(actor_pointer, 512)
                                                                 if actor_pointer else None)
                                                        item.update(bytes_1d80_1e80=(distant.hex()
                                                                   if distant is not None else None),
                                                                    actor_pointer=(hex(actor_pointer)
                                                                   if actor_pointer else None),
                                                                    actor_bytes_512=(actor.hex()
                                                                   if actor is not None else None))
                                                    links.append(item)
                                            snapshots.append({"role": role,
                                                              "context_ptr": hex(context_ptr),
                                                              "status_ptr": hex(status_ptr),
                                                              "context_600": (context_data.hex()
                                                              if context_data is not None else None),
                                                              "status_2a0": (status_data.hex()
                                                              if status_data is not None else None),
                                                              "links": links})
                                            if (enemy_signatures and status_ptr not in enemy_diagnostics
                                                    and len(enemy_diagnostics) < enemy_diagnostic_limit):
                                                gap, candidates = enemy_lookup_gap(status_data, enemy_signatures)
                                                if gap:
                                                    # The first-seen snapshot has 0x600 context
                                                    # and short links. Preserve a wider bounded
                                                    # graph now, while these pointers are live.
                                                    link_590 = read_u64(context_ptr + 0x590)
                                                    link_bytes = (read_bytes(link_590 + 0x1C00, 0x400)
                                                                  if link_590 else None)
                                                    actor_ptr = (read_u64(link_590 + 0x1D88)
                                                                 if link_590 else None)
                                                    actor_bytes = (read_bytes(actor_ptr, 0x400)
                                                                   if actor_ptr else None)
                                                    wide_context = read_bytes(context_ptr, 0x1000)
                                                    snapshots[-1]["diagnostic_snapshot"] = {
                                                        "trigger": gap,
                                                        "candidate_unit_ids": candidates,
                                                        "context_1000": (wide_context.hex()
                                                                         if wide_context is not None else None),
                                                        "link_590": hex(link_590) if link_590 else None,
                                                        "link_590_offset_1c00_400": (link_bytes.hex()
                                                                                       if link_bytes is not None else None),
                                                        "actor_ptr": hex(actor_ptr) if actor_ptr else None,
                                                        "actor_400": (actor_bytes.hex()
                                                                      if actor_bytes is not None else None),
                                                        "ordinal": len(enemy_diagnostics) + 1,
                                                        "limit_per_battle": enemy_diagnostic_limit}
                                                    enemy_diagnostics.add(status_ptr)
                                        if snapshots:
                                            fields["identity_snapshots"] = snapshots
                                if slot >= len(specs):
                                    value = read_i32(watched)
                                    stack = read_bytes(ctx.rsp, 64)
                                    fields.update(address=hex(watched), before=prior_values[name],
                                                  after=value, rsp=hex(ctx.rsp),
                                                  rax=hex(ctx.rax), rsi=hex(ctx.rsi),
                                                  r14=hex(ctx.r14),
                                                  stack_words=[hex(word) for word in struct.unpack("<8Q", stack)]
                                                  if stack is not None else None)
                                    prior_values[name] = value
                                emit("hit", **fields)
                            if hit_count >= max_hits:
                                emit("hit_limit", count=hit_count)
                                deadline = time.monotonic()
                        # RF resumes past an execution breakpoint for one instruction.
                        # It avoids a queued trap-flag step when detaching.
                        ctx.eflags |= 0x10000
                        ctx.dr6 = 0
                        set_context(handle, address, ctx, control=True)
                else:
                    status = DBG_EXCEPTION_NOT_HANDLED
            checked(kernel32.ContinueDebugEvent(event.pid, event.tid, status), "ContinueDebugEvent")
        if attached and not exited:
            if installed and not stop_break_seen:
                # Fallback if the timed stop breakpoint could not be delivered.
                if not clear_all():
                    raise RuntimeError("Unable to restore every thread debug register")
            checked(kernel32.DebugActiveProcessStop(pid), "DebugActiveProcessStop")
            attached = False
            emit("detached")
    finally:
        if attached and not exited:
            restored = False
            try:
                restored = clear_all()
            except Exception as error:
                emit("restore_error", detail=str(error))
            try:
                if kernel32.DebugActiveProcessStop(pid):
                    attached = False
                    emit("detached_after_error" if restored else "detach_cleanup_error",
                         detail=None if restored else "One or more thread debug registers could not be restored")
                else:
                    emit("detach_error", detail=f"DebugActiveProcessStop failed: {ct.get_last_error()}")
            except Exception as error:
                emit("detach_error", detail=str(error))
        elif exited:
            # Windows removes the debugger association when the target exits.
            attached = False
        for thread_handle in threads.values():
            if thread_handle:
                kernel32.CloseHandle(thread_handle)
        threads.clear()
        if debug_process_handle:
            kernel32.CloseHandle(debug_process_handle)
            debug_process_handle = None
        if read_process_handle:
            kernel32.CloseHandle(read_process_handle)
            read_process_handle = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--expected-sha256", required=True,
                        help="Refuse to attach if the running executable does not match")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--rva", action="append", type=parse_named_address,
                       help="Candidate function RVA as NAME=0xRVA (repeat, max four)")
    group.add_argument("--address", action="append", type=parse_named_address,
                       help="Absolute test address as NAME=0xADDRESS (repeat, max four)")
    parser.add_argument("--seconds", type=float, default=90)
    parser.add_argument("--max-hits", type=int, default=2000)
    parser.add_argument("--stop-file", type=Path,
                        help="Detach cleanly when this sentinel file appears")
    parser.add_argument("--write-address", action="append", type=parse_named_address,
                        help="Four-byte aligned address to watch for writes (repeat)")
    parser.add_argument("--inspect-hp-set", action="append", default=[], metavar="NAME",
                        help="At this named execution breakpoint, read status HP at RSI+0xC/+0x10")
    parser.add_argument("--inspect-effect-entry", action="append", default=[], metavar="NAME",
                        help="At this named execution breakpoint, read effect context and target pointer")
    parser.add_argument("--inspect-result-entry", action="append", default=[], metavar="NAME",
                        help="At a candidate result function entry, snapshot raw descriptor and actor IDs")
    parser.add_argument("--inspect-attack-call", action="append", default=[], metavar="NAME",
                        help="At this named execution breakpoint, read candidate source/target and amount")
    parser.add_argument("--inspect-actor-bytes", action="append", default=[], metavar="NAME",
                        help="At an attack-call breakpoint, include bounded source/target context and status bytes")
    parser.add_argument("--inspect-result-frame", action="append", default=[], metavar="NAME",
                        help="At an attack-call breakpoint, include bounded result stack-frame bytes")
    parser.add_argument("--inspect-effect-descriptor", action="append", default=[], metavar="NAME",
                        help="At an attack-call breakpoint, include the saved entry-R8 object's raw bytes")
    parser.add_argument("--inspect-actor-identity", action="append", default=[], metavar="NAME",
                        help="At first attack for each status pointer, collect context/status and actor links")
    parser.add_argument("--inspect-turn-context", action="append", default=[], metavar="NAME",
                        help="At a turn callback, read bounded raw context bytes for move-ID research")
    parser.add_argument("--inspect-critical-popup", action="append", default=[], metavar="NAME",
                        help="At the command-battle Critical popup call, read its enum and flags")
    parser.add_argument("--enemy-table-pac", type=Path,
                        help="Hash-check exact English enemy table before attach for conditional raw snapshots")
    args = parser.parse_args()
    specs = args.rva or args.address
    specs = specs or []
    write_specs = args.write_address or []
    if not 0 < len(specs) + len(write_specs) <= 4 or args.seconds <= 0 or args.max_hits <= 0:
        parser.error("one to four breakpoints, a positive duration and hit limit are required")
    if len({name for name, _ in specs + write_specs}) != len(specs) + len(write_specs):
        parser.error("breakpoint names must be unique")
    execution_names = {candidate for candidate, _ in specs}
    if any(name not in execution_names for name in
           args.inspect_hp_set + args.inspect_effect_entry + args.inspect_result_entry
           + args.inspect_attack_call
           + args.inspect_turn_context + args.inspect_critical_popup):
        parser.error("inspection options must name an execution breakpoint")
    if any(name not in args.inspect_attack_call for name in
           args.inspect_actor_bytes + args.inspect_actor_identity + args.inspect_result_frame
           + args.inspect_effect_descriptor):
        parser.error("actor inspection requires the same name in --inspect-attack-call")
    path = image_path(args.pid)
    actual_hash = file_hash(path)
    if actual_hash != args.expected_sha256.upper():
        raise SystemExit(f"Executable hash mismatch: {actual_hash} ({path})")
    enemy_signatures = (enemy_signature_index(read_enemy_rows(args.enemy_table_pac))
                        if args.enemy_table_pac else None)
    emit("executable", path=path, sha256=actual_hash)
    trace(args.pid, specs, args.seconds, use_rvas=bool(args.rva), max_hits=args.max_hits,
          write_specs=write_specs, hp_set_names=set(args.inspect_hp_set),
          effect_entry_names=set(args.inspect_effect_entry),
          attack_call_names=set(args.inspect_attack_call),
          actor_bytes_names=set(args.inspect_actor_bytes),
          actor_identity_names=set(args.inspect_actor_identity),
          result_frame_names=set(args.inspect_result_frame),
          effect_descriptor_names=set(args.inspect_effect_descriptor),
          turn_context_names=set(args.inspect_turn_context),
          result_entry_names=set(args.inspect_result_entry),
          critical_popup_names=set(args.inspect_critical_popup),
          stop_file=args.stop_file, enemy_signatures=enemy_signatures)


if __name__ == "__main__":
    main()
