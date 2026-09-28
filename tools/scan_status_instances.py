"""Bounded read-only scan for current command-battle enemy status instances."""

import argparse
import ctypes as ct
import json
import struct

import hp_memory_probe as memory
import lifecycle_probe as probe


EXPECTED_SHA256 = "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"
PROCESS_VM_READ = 0x10
PROCESS_QUERY_INFORMATION = 0x400
RANGE_START = 0x16C20000000
RANGE_END = 0x16C30000000
MAX_READ = 1024 * 1024


def scan(handle, ids):
    targets = {struct.pack("<I", value): value for value in ids}
    found = {}
    for base, size in memory.regions(handle):
        left, right = max(base, RANGE_START), min(base + size, RANGE_END)
        if left >= right:
            continue
        address = left
        while address < right:
            data = memory.read(handle, address, min(MAX_READ + 0x2A0, right - address))
            for needle, status_id in targets.items():
                at = data.find(needle)
                while at >= 0:
                    absolute = address + at
                    if absolute not in found and absolute % 8 == 0:
                        status = memory.read(handle, absolute, 0x2A0)
                        if len(status) == 0x2A0:
                            _, level, exp, hp, maximum = struct.unpack_from("<IIIII", status)
                            ep = struct.unpack_from("<I", status, 0x18)[0]
                            defense = struct.unpack_from("<I", status, 0x28)[0]
                            adf = struct.unpack_from("<I", status, 0x30)[0]
                            mov = struct.unpack_from("<I", status, 0x40)[0]
                            if 1 <= level <= 200 and 0 <= hp <= maximum and maximum > 0 \
                                    and 0 <= exp <= 100000 and 0 <= ep <= 100000 \
                                    and 0 <= defense <= 100000 and 0 <= adf <= 100000 \
                                    and 0 <= mov <= 100:
                                found[absolute] = {"kind": "status", "address": hex(absolute),
                                                   "statusId": status_id, "level": level,
                                                   "exp": exp, "hp": hp, "maxHp": maximum,
                                                   "ep": ep, "def": defense, "adf": adf,
                                                   "mov": mov, "bytes_2a0": status.hex()}
                    at = data.find(needle, at + 1)
            address += MAX_READ
    return [found[address] for address in sorted(found)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("--id", action="append", type=int, required=True)
    args = parser.parse_args()
    path = probe.image_path(args.pid)
    digest = probe.file_hash(path)
    if digest != EXPECTED_SHA256:
        raise SystemExit(f"Executable hash mismatch: {digest}")
    handle = probe.kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
                                         False, args.pid)
    if not handle:
        raise OSError(ct.get_last_error(), "OpenProcess")
    try:
        print(json.dumps({"kind": "executable", "sha256": digest, "path": path}), flush=True)
        for record in scan(handle, set(args.id)):
            print(json.dumps(record), flush=True)
    finally:
        probe.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
