"""Read-only integrity and coverage inventory; does not attach to the game."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path


def read_trace(path):
    records, invalid = [], 0
    for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        try:
            row = json.loads(line)
            if isinstance(row, dict): records.append(row)
            else: invalid += 1
        except json.JSONDecodeError:
            if line.strip(): invalid += 1
    kinds = Counter(row.get("kind", "unknown") for row in records)
    hits = Counter(row.get("name", "unknown") for row in records if row.get("kind") == "hit")
    module = next((row for row in records if row.get("kind") == "module"), {})
    return {
        "path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "executableHashes": sorted({row["sha256"] for row in records if row.get("kind") == "executable" and row.get("sha256")}),
        "armed": any(row.get("kind") == "armed" for row in records),
        "finished": any(row.get("kind") in ("detached", "detached_after_error", "target_exited") for row in records),
        "armedAt": [row.get("at") for row in records if row.get("kind") == "armed"],
        "hooks": module.get("breakpoints", {}), "recordKinds": dict(kinds),
        "hitKinds": dict(hits), "nonJsonLines": invalid,
        "resourceProperties": dict(Counter(str(row.get("property_code")) for row in records if row.get("name") == "ResourceSetEntry")),
    }


def audit(data_dir, trace_dirs):
    traces = {}
    for directory in trace_dirs:
        if not directory.exists(): continue
        for path in directory.rglob("probe-session-*.jsonl"):
            traces.setdefault(path.name, []).append(read_trace(path))
    encounters, errors, warnings = [], [], []
    for path in sorted((data_dir / "encounters").glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8-sig"))
            expected = hashlib.sha256(row["id"].encode()).hexdigest().upper() + ".json"
            if path.name.upper() != expected.upper(): errors.append(f"{path.name}: identity/filename mismatch")
            actors = row.get("actors") or []
            events = row.get("events") or []
            ids = [actor["id"] for actor in actors]
            if len(set(ids)) != len(ids): errors.append(f"{path.name}: duplicate actor identities")
            seq = [event["sequence"] for event in events]
            if seq != list(range(1, len(seq) + 1)): errors.append(f"{path.name}: noncontiguous event sequence")
            unknown_refs = sum(event.get("targetId") not in ids or
                event.get("sourceId") is not None and event["sourceId"] not in ids for event in events)
            if unknown_refs: errors.append(f"{path.name}: {unknown_refs} unknown actor references")
            invalid_hp = sum(event.get("effectiveAmount") != (
                event["hpBefore"] - event["hpAfter"] if event["kind"] in ("Damage", "HpLoss") else event["hpAfter"] - event["hpBefore"])
                for event in events if event["kind"] in ("Damage", "Healing", "HpLoss") and
                isinstance(event.get("hpBefore"), int) and isinstance(event.get("hpAfter"), int))
            if invalid_hp: errors.append(f"{path.name}: {invalid_hp} inconsistent HP calculations")
            cross_trace = sum(str(event.get("moveNameProvenance", "")).startswith("cross-trace-") for event in events)
            if cross_trace: errors.append(f"{path.name}: {cross_trace} labels rely on unverified cross-trace memory")
            raw = [issue.removeprefix("Raw trace: ") for issue in row.get("issues", []) if issue.startswith("Raw trace: ")]
            missing = [name for name in raw if name not in traces]
            if missing: warnings.append(f"{path.name}: missing raw traces: {', '.join(missing)}")
            if row.get("isComplete") and row.get("issues"):
                errors.append(f"{path.name}: claims complete despite coverage issues")
            encounters.append({
                "path": str(path), "id": row["id"], "startedAt": row.get("startedAt"),
                "outcome": row.get("outcome"), "complete": row.get("isComplete"),
                "schema": row.get("schemaVersion", 1), "events": len(events),
                "eventKinds": dict(Counter(event["kind"] for event in events)),
                "namedHeals": sum(event["kind"] == "Healing" and event.get("moveId") is not None and
                    event.get("sourceId") is not None for event in events),
                "calculatedResourceRows": sum(event.get("resourceCandidateProvenance") is not None for event in events),
                "rawTraces": raw, "issues": row.get("issues", []),
            })
        except (ValueError, KeyError, TypeError) as error:
            errors.append(f"{path.name}: unreadable encounter: {error}")
    return {"at": datetime.now(timezone.utc).isoformat(), "dataDirectory": str(data_dir),
        "encounterCount": len(encounters), "eventCount": sum(row["events"] for row in encounters),
        "traceCount": sum(len(paths) for paths in traces.values()), "errors": errors, "warnings": warnings,
        "encounters": encounters, "traces": traces,
        "scope": "Structural integrity and available coverage only; does not establish unobserved events or live game completeness."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("LOCALAPPDATA", ".")) / "Sora2 Details")
    parser.add_argument("--trace-dir", type=Path, action="append", default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.data_dir, [args.data_dir / "live", args.data_dir / "research", *args.trace_dir])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{result['encounterCount']} encounters / {result['eventCount']} events / {result['traceCount']} traces")
    print(f"{len(result['errors'])} integrity errors, {len(result['warnings'])} evidence warnings. Report: {args.output}")
    for issue in result["errors"]: print(issue)
    raise SystemExit(1 if result["errors"] else 0)


if __name__ == "__main__":
    main()
