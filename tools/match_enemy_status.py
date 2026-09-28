"""Find unique exact-table enemy names from a captured status stat signature.

This is a research fallback when a runtime unit key is unavailable. Buffs,
level scaling, or table changes may make a result unknown; no nearest match is
ever accepted. Keep status pointers as instance identity.
"""

import argparse
import json
from pathlib import Path
import struct

from status_name_index import read_rows


def table_signature(row):
    level = row["level"]
    return (level, int(row["expBase"] + level * row["expGrowth"]), row["ep"],
            int(row["defBase"] + level * row["defGrowth"]),
            int(row["adfBase"] + level * row["adfGrowth"]),
            int(row["movBase"] + level * row["movGrowth"]))


def status_signature(status_bytes):
    if len(status_bytes) < 0x44:
        raise ValueError("Status snapshot is too short")
    return tuple(struct.unpack_from("<I", status_bytes, offset)[0]
                 for offset in (0x4, 0x8, 0x18, 0x28, 0x30, 0x40))


def match_status(status_bytes, rows):
    signature = status_signature(status_bytes)
    candidates = [row for row in rows if table_signature(row) == signature]
    return signature, candidates


def extract_statuses(trace_path):
    seen = {}
    for line in trace_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.startswith("{"):
            continue
        record = json.loads(line)
        if record.get("kind") == "status" and record.get("bytes_2a0"):
            seen[record["address"]] = bytes.fromhex(record["bytes_2a0"])
        for snapshot in record.get("identity_snapshots", []):
            if snapshot.get("status_2a0"):
                seen[snapshot["status_ptr"]] = bytes.fromhex(snapshot["status_2a0"])
    return seen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("pac", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = read_rows(args.pac)
    result = []
    for pointer, data in extract_statuses(args.trace).items():
        status_id = struct.unpack_from("<I", data)[0]
        if status_id < 60000:
            continue  # Party identity has a separate, verified ID mapping.
        signature, candidates = match_status(data, rows)
        unique = candidates[0] if len(candidates) == 1 else None
        result.append({"statusPtr": pointer, "runtimeStatusId": status_id,
                       "signature": dict(zip(("level", "exp", "ep", "def", "adf", "mov"),
                                             signature)),
                       "unitId": unique["unitId"] if unique else None,
                       "name": unique["name"] if unique else None,
                       "candidateCount": len(candidates),
                       "provenance": "unique-stat-signature/exact-English-table"
                       if unique else "unresolved"})
    serialized = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Wrote {len(result)} enemy status matches to {args.output}")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
