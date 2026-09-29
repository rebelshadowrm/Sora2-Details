"""Synthetic attach/hit/detach check; does not touch the game process."""

import ctypes as ct
import hashlib
import json
import os
import struct
import subprocess
import sys
import threading
import time

from lifecycle_probe import enemy_lookup_gap, enemy_signature_index


def child():
    kernel32 = ct.WinDLL("kernel32", use_last_error=True)
    kernel32.VirtualAlloc.argtypes = [ct.c_void_p, ct.c_size_t, ct.c_uint32, ct.c_uint32]
    kernel32.VirtualAlloc.restype = ct.c_void_p
    address = kernel32.VirtualAlloc(None, 4096, 0x1000 | 0x2000, 0x40)
    if not address:
        raise OSError(ct.get_last_error(), "VirtualAlloc")
    locations = [address + 16 * index for index in range(4)]
    for location in locations:
        ct.memmove(location, b"\xC3", 1)  # x64 ret in this disposable test process.
    callbacks = [ct.CFUNCTYPE(None)(location) for location in locations]
    watched_address = address + 0x100
    watched_value = ct.c_int32.from_address(watched_address)
    print(json.dumps({"pid": os.getpid(), "addresses": [hex(item) for item in locations],
                      "watched_address": hex(watched_address)}), flush=True)
    start_worker_at = time.monotonic() + 0.5
    worker_started = False

    def worker():
        for _ in range(50):
            callbacks[3]()
            time.sleep(0.01)

    while True:
        if not worker_started and time.monotonic() >= start_worker_at:
            threading.Thread(target=worker, daemon=True).start()
            worker_started = True
        for callback in callbacks:
            callback()
        watched_value.value += 1
        time.sleep(0.01)


def parent():
    row = {"unitId": "mon-test", "level": 54, "expBase": 301, "expGrowth": 0.0,
           "ep": 1000, "defBase": 361, "defGrowth": 0.0,
           "adfBase": 321, "adfGrowth": 0.0, "movBase": 6, "movGrowth": 0.0}
    status = bytearray(0x2A0)
    for offset, value in zip((0, 0x4, 0x8, 0x18, 0x28, 0x30, 0x40),
                             (60050, 54, 301, 1000, 361, 321, 6)):
        struct.pack_into("<I", status, offset, value)
    assert enemy_lookup_gap(status, enemy_signature_index([row])) == (None, ["mon-test"])
    assert enemy_lookup_gap(status, enemy_signature_index([row, dict(row, unitId="mon-other")])) == (
        "enemy-unit-key-ambiguous", ["mon-test", "mon-other"])
    assert enemy_lookup_gap(status, {}) == ("enemy-unit-key-missing", [])
    struct.pack_into("<I", status, 0, 5)
    assert enemy_lookup_gap(status, {}) == (None, [])
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    target = subprocess.Popen([sys.executable, __file__, "--child"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, creationflags=flags)
    try:
        assert target.stdout is not None
        ready = json.loads(target.stdout.readline())
        with open(sys.executable, "rb") as file:
            executable_hash = hashlib.file_digest(file, "sha256").hexdigest()
        bad_hash = subprocess.run([
            sys.executable, os.path.join(os.path.dirname(__file__), "lifecycle_probe.py"),
            str(ready["pid"]), "--expected-sha256", "0" * 64,
            "--address", f"Fixture0={ready['addresses'][0]}", "--seconds", "0.1"
        ], capture_output=True, text=True, timeout=5, creationflags=flags)
        if bad_hash.returncode == 0 or "hash mismatch" not in bad_hash.stderr.lower() \
                or '"kind": "attached"' in bad_hash.stdout:
            raise AssertionError("Executable hash guard did not reject before attach")
        probe = subprocess.run([
            sys.executable, os.path.join(os.path.dirname(__file__), "lifecycle_probe.py"),
            str(ready["pid"]), "--expected-sha256", executable_hash,
            *(item for index, address in enumerate(ready["addresses"])
              for item in ("--address", f"Fixture{index}={address}")),
            "--seconds", "1.5"
        ], capture_output=True, text=True, timeout=15, creationflags=flags)
        if probe.returncode:
            raise AssertionError(f"Probe failed (code {probe.returncode}):\n"
                                 + "\n".join(probe.stdout.splitlines()[-8:])
                                 + f"\n{probe.stderr}\ntarget={target.poll()} "
                                 + (target.stderr.read() if target.poll() is not None else ""))
        records = [json.loads(line) for line in probe.stdout.splitlines()]
        kinds = [record["kind"] for record in records]
        for required in ("attached", "armed", "hit", "disarmed", "detached"):
            if required not in kinds:
                raise AssertionError(f"Missing {required}:\n"
                                     + "\n".join(probe.stdout.splitlines()[-6:])
                                     + f"\ntarget={target.poll()} "
                                     + (target.stderr.read() if target.poll() is not None else ""))
        hit_names = {record["name"] for record in records if record["kind"] == "hit"}
        if hit_names != {f"Fixture{index}" for index in range(4)}:
            raise AssertionError(f"Not all hardware slots fired: {hit_names}\n"
                                 + "\n".join(probe.stdout.splitlines()[:20]))
        hit_threads = {record["tid"] for record in records if record["kind"] == "hit"}
        if len(hit_threads) < 2:
            raise AssertionError("Newly created worker thread was not traced")
        write_probe = subprocess.run([
            sys.executable, os.path.join(os.path.dirname(__file__), "lifecycle_probe.py"),
            str(ready["pid"]), "--expected-sha256", executable_hash,
            "--address", f"Fixture0={ready['addresses'][0]}",
            "--write-address", f"Counter={ready['watched_address']}",
            "--seconds", "0.5"
        ], capture_output=True, text=True, timeout=15, creationflags=flags)
        if write_probe.returncode:
            raise AssertionError(f"Write probe failed: {write_probe.stderr}\n"
                                 + "\n".join(write_probe.stdout.splitlines()[-8:]))
        write_records = [json.loads(line) for line in write_probe.stdout.splitlines()]
        writes = [record for record in write_records if record.get("name") == "Counter"]
        if not writes or not any(isinstance(record.get("after"), int) for record in writes):
            raise AssertionError("Four-byte write breakpoint did not capture a value")
        if not any(record.get("kind") == "detached" for record in write_records):
            raise AssertionError("Write probe did not detach")
        time.sleep(0.2)
        if target.poll() is not None:
            raise AssertionError(f"Synthetic target exited after debugger detached: "
                                 f"code={target.returncode}, stderr={target.stderr.read() if target.stderr else ''}, "
                                 f"last probe lines={probe.stdout.splitlines()[-5:]}")
        print("Synthetic lifecycle probe attach/hit/detach check passed.")
    finally:
        target.terminate()
        target.wait(timeout=5)


if __name__ == "__main__":
    if sys.argv[1:] == ["--child"]:
        child()
    else:
        parent()
