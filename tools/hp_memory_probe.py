"""Read-only Windows probe for candidate current/max HP fields in a running process.

This locates candidates, not an attributed damage hook. Recheck candidate addresses
after a controlled HP change before treating one as a character's HP field.
"""

import argparse
import ctypes as ct
from datetime import datetime
import struct
import sys
import time
from ctypes import wintypes as wt


PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01
READABLE = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}
CHUNK = 1024 * 1024


class MemoryInfo(ct.Structure):
    _fields_ = [
        ("base", ct.c_void_p),
        ("allocation_base", ct.c_void_p),
        ("allocation_protect", wt.DWORD),
        ("partition_id", wt.WORD),
        ("region_size", ct.c_size_t),
        ("state", wt.DWORD),
        ("protect", wt.DWORD),
        ("type", wt.DWORD),
    ]


kernel32 = ct.WinDLL("kernel32", use_last_error=True) if sys.platform == "win32" else None
if kernel32:
    kernel32.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    kernel32.OpenProcess.restype = wt.HANDLE
    kernel32.VirtualQueryEx.argtypes = [wt.HANDLE, ct.c_void_p, ct.POINTER(MemoryInfo), ct.c_size_t]
    kernel32.VirtualQueryEx.restype = ct.c_size_t
    kernel32.ReadProcessMemory.argtypes = [wt.HANDLE, ct.c_void_p, ct.c_void_p, ct.c_size_t, ct.POINTER(ct.c_size_t)]
    kernel32.ReadProcessMemory.restype = wt.BOOL
    kernel32.CloseHandle.argtypes = [wt.HANDLE]


def read(handle, address, size):
    buffer = ct.create_string_buffer(size)
    count = ct.c_size_t()
    if not kernel32.ReadProcessMemory(handle, ct.c_void_p(address), buffer, size, ct.byref(count)):
        return b""
    return buffer.raw[: count.value]


def regions(handle):
    address = 0
    limit = 0x7FFFFFFFFFFF
    while address < limit:
        info = MemoryInfo()
        if not kernel32.VirtualQueryEx(handle, ct.c_void_p(address), ct.byref(info), ct.sizeof(info)):
            break
        base = info.base or 0
        next_address = base + info.region_size
        if next_address <= address:
            break
        if info.state == MEM_COMMIT and info.protect & (PAGE_GUARD | PAGE_NOACCESS) == 0 \
                and info.protect & 0xFF in READABLE:
            yield base, info.region_size
        address = next_address


def scan(handle, hp, max_hp, limit):
    needle = struct.pack("<i", hp)
    maximum = struct.pack("<i", max_hp)
    found = 0
    for base, size in regions(handle):
        offset = 0
        while offset < size:
            data = read(handle, base + offset, min(CHUNK + 64, size - offset))
            if data:
                position = data.find(needle)
                while position >= 0:
                    address = base + offset + position
                    if position < CHUNK and address % 4 == 0:
                        for delta in range(-64, 65, 4):
                            adjacent = position + delta
                            if delta and 0 <= adjacent <= len(data) - 4 and data[adjacent:adjacent + 4] == maximum:
                                print(f"current=0x{address:X} max=0x{address + delta:X} delta={delta:+d}")
                                found += 1
                                if found >= limit:
                                    print(f"Stopped at {limit} candidate pairs; use another HP state to narrow them.")
                                    return
                    position = data.find(needle, position + 1)
            offset += CHUNK
    print(f"Found {found} candidate pair(s).")


def watch(handle, address, seconds, interval):
    """Log raw HP changes without claiming attacker, move, or battle context."""
    previous = None
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        data = read(handle, address, 8)
        value = struct.unpack("<ii", data) if len(data) == 8 else None
        if value != previous:
            print(f"{datetime.now().astimezone().isoformat(timespec='milliseconds')} "
                  f"current={value[0] if value else 'unreadable'} "
                  f"max={value[1] if value else 'unreadable'}", flush=True)
            previous = value
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int, help="Running sora_2nd.exe process ID")
    parser.add_argument("current_hp", type=int, help="Displayed current HP")
    parser.add_argument("max_hp", type=int, help="Displayed maximum HP")
    parser.add_argument("--limit", type=int, default=100, help="Maximum candidate pairs to print")
    parser.add_argument("--read", nargs="+", type=lambda value: int(value, 0),
                        help="Read these candidate 32-bit addresses instead of scanning memory")
    parser.add_argument("--watch", type=lambda value: int(value, 0),
                        help="Watch current/max HP at this address for raw changes")
    parser.add_argument("--seconds", type=float, default=60, help="Watch duration in seconds")
    parser.add_argument("--interval", type=float, default=0.05, help="Watch poll interval in seconds")
    args = parser.parse_args()
    if kernel32 is None:
        parser.error("This probe requires Windows.")
    if not (0 <= args.current_hp <= args.max_hp and args.max_hp > 0 and args.limit > 0
            and args.seconds > 0 and args.interval > 0):
        parser.error("HP must be between zero and max HP; limit must be positive.")
    access = PROCESS_VM_READ
    if args.watch is None and not args.read:
        # Only the full scan enumerates regions with VirtualQueryEx.
        access |= PROCESS_QUERY_INFORMATION
    handle = kernel32.OpenProcess(access, False, args.pid)
    if not handle:
        raise OSError(ct.get_last_error(), "OpenProcess failed")
    try:
        if args.watch is not None:
            watch(handle, args.watch, args.seconds, args.interval)
        elif args.read:
            for address in args.read:
                data = read(handle, address, 4)
                value = struct.unpack("<i", data)[0] if len(data) == 4 else "unreadable"
                print(f"0x{address:X}: {value}")
        else:
            scan(handle, args.current_hp, args.max_hp, args.limit)
    finally:
        kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
