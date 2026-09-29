"""Time-limited launcher for fixed Sora 2 probes.

The service stays idle between requests and never holds a game handle while
idle. Requests use an ignored workspace queue; only fixed, hash-gated probe
scripts are callable. The production app starts elevated before its UI and
launches this service and its probe children with the inherited token.
Standard-user access is available only through the explicit diagnostic
launcher switch; the production path never retries after an access-denied result.
"""

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

import lifecycle_probe as probe


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("SORA2_DETAILS_DATA_DIR") or
                Path(os.environ.get("LOCALAPPDATA", str(ROOT))) / "Sora2 Details")
DEFAULT_SESSION_DIR = DATA_DIR / "probe-session"
OUTPUT_DIR = DATA_DIR / "research"
LIVE_DIR = DATA_DIR / "live"
EXPECTED_SHA256 = "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def now():
    return datetime.now(timezone.utc)


def verify_target(pid):
    path = probe.image_path(pid)
    digest = probe.file_hash(path)
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Executable hash mismatch: {digest} ({path})")
    return path


def run_fixed(request, pid, request_id):
    action = request.get("action")
    if action == "ping":
        return {"ok": True, "targetPid": pid, "serverPid": os.getpid()}
    if action == "stop":
        return {"ok": True, "stopping": True}
    target_path = verify_target(pid)
    enemy_table_pac = Path(target_path).parent / "pac" / "steam" / "table_en.pac"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUTPUT_DIR / f"probe-session-{request_id}.jsonl"
    if action == "live_capture":
        seconds = request.get("seconds", 1800)
        if type(seconds) is not int or not 60 <= seconds <= 3600:
            raise ValueError("Live capture seconds must be 60..3600")
        LIVE_DIR.mkdir(parents=True, exist_ok=True)
        output = LIVE_DIR / f"probe-session-{request_id}.jsonl"
        stop_file = LIVE_DIR / f"stop-{request_id}"
        stop_file.unlink(missing_ok=True)
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleInit=0xC2750",
                   "--rva", "BattleEnd=0xBA659",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--inspect-actor-identity", "AttackEffectCall",
                   "--inspect-actor-bytes", "AttackEffectCall",
                   "--inspect-effect-descriptor", "AttackEffectCall",
                   "--enemy-table-pac", str(enemy_table_pac),
                   "--rva", "HpSet=0xF8EB3", "--inspect-hp-set", "HpSet",
                   "--stop-file", str(stop_file),
                   "--seconds", str(seconds), "--max-hits", "100000"]
        timeout = seconds + 45
    elif action == "session_capture":
        seconds = request.get("seconds", 43200)
        if type(seconds) is not int or not 60 <= seconds <= 43200:
            raise ValueError("Session capture seconds must be 60..43200")
        LIVE_DIR.mkdir(parents=True, exist_ok=True)
        output = LIVE_DIR / f"probe-session-{request_id}.jsonl"
        stop_file = LIVE_DIR / f"stop-{request_id}"
        stop_file.unlink(missing_ok=True)
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleInit=0xC2750",
                   "--rva", "BattleEnd=0xBA659",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--inspect-actor-identity", "AttackEffectCall",
                   "--inspect-actor-bytes", "AttackEffectCall",
                   "--inspect-result-frame", "AttackEffectCall",
                   "--inspect-effect-descriptor", "AttackEffectCall",
                   "--enemy-table-pac", str(enemy_table_pac),
                   "--rva", "HpSet=0xF8EB3", "--inspect-hp-set", "HpSet",
                   "--stop-file", str(stop_file),
                   "--seconds", str(seconds), "--max-hits", "2000000"]
        timeout = seconds + 45
    elif action == "name_capture":
        seconds = request.get("seconds", 120)
        if type(seconds) is not int or not 10 <= seconds <= 300:
            raise ValueError("Capture seconds must be 10..300")
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleCommandBegin=0x1175B8",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--inspect-actor-identity", "AttackEffectCall",
                   "--rva", "HpSet=0xF8EB3", "--inspect-hp-set", "HpSet",
                   "--seconds", str(seconds), "--max-hits", "1000"]
        timeout = seconds + 30
    elif action == "boundary_capture":
        seconds = request.get("seconds", 300)
        if type(seconds) is not int or not 30 <= seconds <= 300:
            raise ValueError("Capture seconds must be 30..300")
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleInit=0xC2750",
                   "--rva", "BattleCommandBegin=0x1175B8",
                   "--rva", "BattleCheckResult=0x1181C0",
                   "--rva", "BattleEnd=0xBA659",
                   "--seconds", str(seconds), "--max-hits", "5000"]
        timeout = seconds + 30
    elif action == "turn_capture":
        seconds = request.get("seconds", 180)
        if type(seconds) is not int or not 30 <= seconds <= 300:
            raise ValueError("Capture seconds must be 30..300")
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleTurnBegin=0x1172C4",
                   "--rva", "BattleCommandBegin=0x1175B8",
                   "--rva", "BattleTurnEnd=0x1184D4",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--seconds", str(seconds), "--max-hits", "3000"]
        timeout = seconds + 30
    elif action == "action_id_capture":
        seconds = request.get("seconds", 180)
        if type(seconds) is not int or not 30 <= seconds <= 300:
            raise ValueError("Capture seconds must be 30..300")
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleCommandBegin=0x1175B8",
                   "--inspect-turn-context", "BattleCommandBegin",
                   "--rva", "BattleTurnEnd=0x1184D4",
                   "--inspect-turn-context", "BattleTurnEnd",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--rva", "HpSet=0xF8EB3", "--inspect-hp-set", "HpSet",
                   "--seconds", str(seconds), "--max-hits", "3000"]
        timeout = seconds + 30
    elif action == "result_class_capture":
        seconds = request.get("seconds", 180)
        if type(seconds) is not int or not 30 <= seconds <= 300:
            raise ValueError("Capture seconds must be 30..300")
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleInit=0xC2750",
                   "--rva", "ResultEntry=0xE2B60",
                   "--inspect-result-entry", "ResultEntry",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--rva", "HpSet=0xF8EB3", "--inspect-hp-set", "HpSet",
                   "--seconds", str(seconds), "--max-hits", "5000"]
        timeout = seconds + 30
    elif action == "critical_capture":
        seconds = request.get("seconds", 180)
        if type(seconds) is not int or not 30 <= seconds <= 300:
            raise ValueError("Capture seconds must be 30..300")
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleInit=0xC2750",
                   "--rva", "ResultEntry=0xE2B60",
                   "--inspect-result-entry", "ResultEntry",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--inspect-actor-bytes", "AttackEffectCall",
                   "--inspect-result-frame", "AttackEffectCall",
                   "--rva", "HpSet=0xF8EB3", "--inspect-hp-set", "HpSet",
                   "--seconds", str(seconds), "--max-hits", "5000"]
        timeout = seconds + 30
    elif action == "critical_long_capture":
        seconds = request.get("seconds", 1800)
        if type(seconds) is not int or not 60 <= seconds <= 3600:
            raise ValueError("Critical capture seconds must be 60..3600")
        LIVE_DIR.mkdir(parents=True, exist_ok=True)
        output = LIVE_DIR / f"probe-session-{request_id}.jsonl"
        stop_file = LIVE_DIR / f"stop-{request_id}"
        stop_file.unlink(missing_ok=True)
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleInit=0xC2750",
                   "--rva", "BattleEnd=0xBA659",
                   "--rva", "CandidateAttackCritical=0x116E0A",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--inspect-result-frame", "AttackEffectCall",
                   "--stop-file", str(stop_file),
                   "--seconds", str(seconds), "--max-hits", "100000"]
        timeout = seconds + 45
    elif action == "critical_popup_capture":
        seconds = request.get("seconds", 300)
        if type(seconds) is not int or not 60 <= seconds <= 1800:
            raise ValueError("Critical popup capture seconds must be 60..1800")
        LIVE_DIR.mkdir(parents=True, exist_ok=True)
        output = LIVE_DIR / f"probe-session-{request_id}.jsonl"
        stop_file = LIVE_DIR / f"stop-{request_id}"
        stop_file.unlink(missing_ok=True)
        command = [sys.executable, str(ROOT / "tools" / "lifecycle_probe.py"), str(pid),
                   "--expected-sha256", EXPECTED_SHA256,
                   "--rva", "BattleInit=0xC2750",
                   "--rva", "CriticalPopup=0x116EE0",
                   "--inspect-critical-popup", "CriticalPopup",
                   "--rva", "AttackEffectCall=0xE3E55",
                   "--inspect-attack-call", "AttackEffectCall",
                   "--rva", "HpSet=0xF8EB3", "--inspect-hp-set", "HpSet",
                   "--stop-file", str(stop_file),
                   "--seconds", str(seconds), "--max-hits", "30000"]
        timeout = seconds + 45
    elif action == "status_snapshot":
        statuses = request.get("statuses", [])
        contexts = request.get("contexts", [])
        if not isinstance(statuses, list) or not 1 <= len(statuses) <= 8 \
                or not isinstance(contexts, list) or len(contexts) > 4 \
                or any(type(value) is not int or not 0x10000 <= value <= 0x7FFFFFFFFFFF
                       for value in statuses + contexts):
            raise ValueError("Supply 1..8 status and 0..4 context addresses")
        command = [sys.executable, str(ROOT / "tools" / "read_status_identity.py"),
                   str(pid), *(hex(value) for value in statuses),
                   *(argument for value in contexts for argument in ("--context", hex(value)))]
        timeout = 30
    elif action == "scan_status":
        command = [sys.executable, str(ROOT / "tools" / "scan_status_instances.py"),
                   str(pid), "--id", "60050", "--id", "60051", "--id", "60052"]
        timeout = 60
    else:
        raise ValueError(f"Unsupported action: {action}")
    try:
        with output.open("w", encoding="utf-8") as file:
            completed = subprocess.run(command, stdout=file, stderr=subprocess.STDOUT,
                                       text=True, timeout=timeout, check=False)
        return {"ok": completed.returncode == 0, "exitCode": completed.returncode,
                "output": str(output)}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Probe exceeded its bounded duration",
                "output": str(output)}


def serve(args):
    session_dir = args.session_dir.resolve()
    session_dir.mkdir(parents=True, exist_ok=True)
    startup_error = session_dir / "startup-error.json"
    startup_error.unlink(missing_ok=True)
    try:
        verify_target(args.pid)
    except Exception as error:
        atomic_json(startup_error, {"targetPid": args.pid, "error": str(error)})
        raise
    requests = session_dir / "requests"
    results = session_dir / "results"
    requests.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    session_id = uuid.uuid4().hex
    expiry = now() + timedelta(minutes=args.minutes)
    ready = session_dir / "ready.json"
    atomic_json(ready, {"sessionId": session_id, "serverPid": os.getpid(),
                        "hostPid": int(os.environ.get("SORA2_DETAILS_HOST_PID", "0")),
                        "targetPid": args.pid, "expiresAt": expiry.isoformat(),
                        "actions": ["ping", "status_snapshot", "scan_status",
                                    "name_capture", "boundary_capture", "turn_capture",
                                    "action_id_capture", "result_class_capture", "critical_capture",
                                    "critical_long_capture", "critical_popup_capture",
                                    "live_capture", "session_capture", "stop"]})
    try:
        while now() < expiry:
            for path in sorted(requests.glob("*.json")):
                try:
                    request = json.loads(path.read_text(encoding="utf-8"))
                    if request.get("sessionId") != session_id:
                        continue
                    request_id = path.stem
                    if not request_id or any(character not in "0123456789abcdef" for character in request_id):
                        continue
                    processing = path.with_suffix(".processing")
                    os.replace(path, processing)
                    try:
                        result = run_fixed(request, args.pid, request_id)
                    except Exception as error:
                        result = {"ok": False, "error": str(error)}
                    atomic_json(results / f"{request_id}.json", result)
                    processing.unlink(missing_ok=True)
                    if result.get("stopping"):
                        return
                except (OSError, ValueError, json.JSONDecodeError):
                    continue
            time.sleep(0.1)
    finally:
        current = json.loads(ready.read_text(encoding="utf-8")) if ready.exists() else {}
        if current.get("sessionId") == session_id:
            atomic_json(ready, {"sessionId": session_id, "stopped": True,
                                "targetPid": args.pid, "serverPid": os.getpid(),
                                "hostPid": int(os.environ.get("SORA2_DETAILS_HOST_PID", "0"))})


def send(args):
    session_dir = args.session_dir.resolve()
    ready = json.loads((session_dir / "ready.json").read_text(encoding="utf-8"))
    if ready.get("stopped") or now() >= datetime.fromisoformat(ready["expiresAt"]):
        raise SystemExit("Probe session is stopped or expired")
    request_id = uuid.uuid4().hex
    request = {"sessionId": ready["sessionId"], "action": args.action}
    if args.action in ("name_capture", "boundary_capture", "turn_capture",
                       "action_id_capture", "result_class_capture", "critical_capture",
                       "critical_long_capture", "critical_popup_capture",
                       "live_capture", "session_capture"):
        request["seconds"] = args.seconds if args.seconds is not None else (
            300 if args.action == "boundary_capture" else
            43200 if args.action == "session_capture" else
            1800 if args.action in ("live_capture", "critical_long_capture") else
            300 if args.action == "critical_popup_capture" else
            180 if args.action in ("turn_capture", "action_id_capture",
                                   "result_class_capture", "critical_capture") else 120)
    elif args.action == "status_snapshot":
        request["statuses"] = args.status or []
        request["contexts"] = args.context or []
    atomic_json(session_dir / "requests" / f"{request_id}.json", request)
    print(f"Request {request_id} queued", flush=True)
    if args.no_wait:
        return
    deadline = time.monotonic() + args.wait_seconds
    result_path = session_dir / "results" / f"{request_id}.json"
    while time.monotonic() < deadline:
        if result_path.exists():
            result = json.loads(result_path.read_text(encoding="utf-8"))
            print(json.dumps(result, indent=2), flush=True)
            if not result.get("ok"):
                raise SystemExit(1)
            return
        time.sleep(0.1)
    raise SystemExit(f"Request {request_id} is still pending; check {result_path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-dir", type=Path, default=DEFAULT_SESSION_DIR)
    modes = parser.add_subparsers(dest="mode", required=True)
    server = modes.add_parser("serve")
    server.add_argument("--pid", type=int, required=True)
    server.add_argument("--minutes", type=int, default=30)
    client = modes.add_parser("send")
    client.add_argument("action", choices=("ping", "status_snapshot", "scan_status",
                                           "name_capture", "boundary_capture", "turn_capture",
                                           "action_id_capture", "result_class_capture", "critical_capture",
                                           "critical_long_capture", "critical_popup_capture", "live_capture",
                                           "session_capture", "stop"))
    client.add_argument("--seconds", type=int)
    client.add_argument("--status", action="append", type=lambda value: int(value, 0))
    client.add_argument("--context", action="append", type=lambda value: int(value, 0))
    client.add_argument("--no-wait", action="store_true")
    client.add_argument("--wait-seconds", type=int, default=15)
    args = parser.parse_args()
    if args.mode == "serve":
        if not 1 <= args.minutes <= 1500:
            parser.error("Session minutes must be 1..1500")
        serve(args)
    else:
        send(args)


if __name__ == "__main__":
    main()
