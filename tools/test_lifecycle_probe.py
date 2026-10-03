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
import tempfile

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
    root_slot = address + 0x108
    ct.c_uint64.from_address(root_slot).value = watched_address
    print(json.dumps({"pid": os.getpid(), "addresses": [hex(item) for item in locations],
                      "watched_address": hex(watched_address), "root_slot": hex(root_slot)}), flush=True)
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
    target = subprocess.Popen([sys.executable, "-B", __file__, "--child"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              text=True, creationflags=flags)
    try:
        assert target.stdout is not None
        ready = json.loads(target.stdout.readline())
        with open(sys.executable, "rb") as file:
            executable_hash = hashlib.file_digest(file, "sha256").hexdigest()
        bad_hash = subprocess.run([
            sys.executable, "-B", os.path.join(os.path.dirname(__file__), "lifecycle_probe.py"),
            str(ready["pid"]), "--expected-sha256", "0" * 64,
            "--address", f"Fixture0={ready['addresses'][0]}", "--seconds", "0.1"
        ], capture_output=True, text=True, timeout=5, creationflags=flags)
        if bad_hash.returncode == 0 or "hash mismatch" not in bad_hash.stderr.lower() \
                or '"kind": "attached"' in bad_hash.stdout:
            raise AssertionError("Executable hash guard did not reject before attach")
        probe = subprocess.run([
            sys.executable, "-B", os.path.join(os.path.dirname(__file__), "lifecycle_probe.py"),
            str(ready["pid"]), "--expected-sha256", executable_hash,
            *(item for index, address in enumerate(ready["addresses"])
              for item in ("--address", f"Fixture{index}={address}")),
            "--inspect-action-state", "Fixture0",
            "--inspect-actor-state-dispatch", "Fixture0",
            "--inspect-queue-store", "Fixture0",
            "--inspect-effect-dispatch", "Fixture1",
            "--inspect-queue-resume", "Fixture1",
            "--inspect-action-setup", "Fixture1",
            "--inspect-condition-request", "Fixture2",
            "--inspect-animation-request", "Fixture2",
            "--inspect-condition-return", "Fixture3",
            "--inspect-animation-accepted", "Fixture3",
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
        hits = [record for record in records if record["kind"] == "hit"]
        for name, field in (("Fixture0", "state_actor_c70_raw"),
                            ("Fixture0", "actor_state_first_update_candidate"),
                            ("Fixture1", "dispatch_r9_u32"),
                            ("Fixture1", "setup_entry_return_address_raw"),
                            ("Fixture2", "condition_vector_count_raw"),
                            ("Fixture2", "launch_entry_stack_pointer_raw"),
                            ("Fixture3", "condition_return_eax_raw")):
            if not all(field in record for record in hits if record["name"] == name):
                raise AssertionError(f"Missing raw research snapshot field: {name}/{field}")
        if not all('launch_queue_pointer_raw' in record for record in hits if record['name'] == 'Fixture3'):
            raise AssertionError('Missing accepted launch snapshot')
        for name in ("Fixture0", "Fixture1"):
            if not all("queue_actor_c78_raw" in record for record in hits if record["name"] == name):
                raise AssertionError(f"Missing queue snapshot: {name}")
        sequences = [record["observation_sequence"] for record in hits]
        if sequences != list(range(1, len(hits) + 1)):
            raise AssertionError("Raw observation order was not retained")
        clocks = [record["monotonic_ns"] for record in hits]
        if clocks != sorted(clocks):
            raise AssertionError("Monotonic observation time regressed")
        hit_threads = {record["tid"] for record in records if record["kind"] == "hit"}
        if len(hit_threads) < 2:
            raise AssertionError("Newly created worker thread was not traced")
        write_probe = subprocess.run([
            sys.executable, "-B", os.path.join(os.path.dirname(__file__), "lifecycle_probe.py"),
            str(ready["pid"]), "--expected-sha256", executable_hash,
            "--address", f"Fixture0={ready['addresses'][0]}",
            "--write-pointer-address", f"Counter={ready['root_slot']},0x0",
            "--seconds", "0.5"
        ], capture_output=True, text=True, timeout=15, creationflags=flags)
        if write_probe.returncode:
            raise AssertionError(f"Write probe failed: {write_probe.stderr}\n"
                                 + "\n".join(write_probe.stdout.splitlines()[-8:]))
        write_records = [json.loads(line) for line in write_probe.stdout.splitlines()]
        writes = [record for record in write_records if record.get("name") == "Counter"]
        if not writes or not any(isinstance(record.get("after"), int) for record in writes):
            raise AssertionError("Four-byte write breakpoint did not capture a value")
        if not all(record.get('pointer_root_at_arm') == ready['watched_address']
                   and record.get('pointer_root_now') == ready['watched_address'] for record in writes):
            raise AssertionError('Pointer-resolved write watch did not preserve root identity')
        if not any(record.get("kind") == "detached" for record in write_records):
            raise AssertionError("Write probe did not detach")
        # Exercise the actual manual-stop path, deliberately passing tiny legacy
        # limits. Neither limit may stop this mode before its sentinel appears.
        with tempfile.TemporaryDirectory(prefix="sora2-manual-stop-") as temp:
            stop_path = os.path.join(temp, 'stop')
            manual_records = []
            armed = threading.Event()
            manual = subprocess.Popen([
                sys.executable, "-B", os.path.join(os.path.dirname(__file__), "lifecycle_probe.py"),
                str(ready["pid"]), "--expected-sha256", executable_hash,
                "--address", f"Fixture0={ready['addresses'][0]}",
                "--until-stop-file", "--stop-file", stop_path,
                "--seconds", "0.01", "--max-hits", "1"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=flags)

            def collect_manual():
                for line in manual.stdout:
                    record = json.loads(line)
                    manual_records.append(record)
                    if record.get('kind') == 'armed':
                        armed.set()

            reader = threading.Thread(target=collect_manual, daemon=True)
            reader.start()
            try:
                if not armed.wait(5):
                    raise AssertionError('Manual-stop probe did not arm')
                time.sleep(0.3)
                if manual.poll() is not None:
                    raise AssertionError('Manual-stop probe ended before sentinel')
                if sum(r.get('kind') == 'hit' for r in manual_records) <= 1:
                    raise AssertionError('Manual-stop probe did not continue beyond hit limit')
            finally:
                with open(stop_path, 'w') as stop:
                    stop.write('test controls complete')
                try:
                    manual.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    manual.kill()
                    manual.wait(timeout=5)
                    raise AssertionError('Manual-stop probe failed to detach after sentinel')
                reader.join(timeout=5)
            if manual.returncode or not any(r.get('kind') == 'detached' for r in manual_records):
                raise AssertionError('Manual-stop probe failed: ' + manual.stderr.read())
            if any(r.get('kind') == 'hit_limit' for r in manual_records):
                raise AssertionError('Manual-stop mode applied a hit cutoff')
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
