"""Bounded read-only snapshot of known live status instances for name research."""

import argparse
import ctypes as ct
import json
import struct

import lifecycle_probe as probe


EXPECTED_SHA256 = "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"
PROCESS_VM_READ = 0x10
PROCESS_QUERY_INFORMATION = 0x400


def read(handle, address, size):
    buffer = ct.create_string_buffer(size)
    count = ct.c_size_t()
    if not probe.kernel32.ReadProcessMemory(handle, ct.c_void_p(address), buffer,
                                             size, ct.byref(count)) or count.value != size:
        return None
    return buffer.raw


def preview(data):
    if not data:
        return None
    part = data.split(b"\0", 1)[0]
    if not 3 <= len(part) <= 63:
        return None
    try:
        value = part.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return value if all(character.isprintable() for character in value) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("status", nargs="+", type=lambda value: int(value, 0))
    parser.add_argument("--extra-status", action="append", type=lambda value: int(value, 0),
                        default=[], help="Additional live status address, such as a battle enemy")
    parser.add_argument("--context", action="append", type=lambda value: int(value, 0),
                        default=[], help="Attack context address to inspect near its actor links")
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
        for address in args.status + args.extra_status:
            data = read(handle, address, 0x2A0)
            fields = {"kind": "status", "address": hex(address),
                      "bytes_256": data[:256].hex() if data else None,
                      "bytes_2a0": data.hex() if data else None,
                      "hp": struct.unpack_from("<ii", data, 12) if data else None,
                      "strings": []}
            if data:
                for offset in range(0, 0x2A0, 8):
                    pointer = struct.unpack_from("<Q", data, offset)[0]
                    if 0x10000 <= pointer <= 0x7FFFFFFFFFFF:
                        value = preview(read(handle, pointer, 64))
                        if value:
                            fields["strings"].append({"offset": hex(offset),
                                                       "pointer": hex(pointer), "value": value})
            print(json.dumps(fields), flush=True)
        for address in args.context:
            data = read(handle, address, 0x600)
            fields = {"kind": "context", "address": hex(address),
                      "bytes_600": data.hex() if data else None,
                      "bytes_0_256": data[:256].hex() if data else None,
                      "bytes_580_600": data[0x580:0x600].hex() if data else None,
                      "links": []}
            if data:
                for offset in (0, 8, 0x590, 0x598, 0x5A8, 0x5B0):
                    pointer = struct.unpack_from("<Q", data, offset)[0]
                    linked = read(handle, pointer, 256) if pointer else None
                    item = {"offset": hex(offset), "pointer": hex(pointer),
                            "bytes_256": linked.hex() if linked else None,
                            "text": preview(linked)}
                    if offset == 0x590 and pointer:
                        distant = read(handle, pointer + 0x1D80, 256)
                        actor_pointer = (struct.unpack_from("<Q", distant, 8)[0]
                                         if distant else None)
                        actor = read(handle, actor_pointer, 512) if actor_pointer else None
                        item.update(bytes_1d80_1e80=distant.hex() if distant else None,
                                    actor_pointer=hex(actor_pointer) if actor_pointer else None,
                                    actor_bytes_512=actor.hex() if actor else None)
                    fields["links"].append(item)
            print(json.dumps(fields), flush=True)
    finally:
        probe.kernel32.CloseHandle(handle)


if __name__ == "__main__":
    main()
