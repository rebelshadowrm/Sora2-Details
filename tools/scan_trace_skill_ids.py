"""Research-only scan for exact static skill IDs in saved live snapshots.

An ID appearing in actor memory is only a candidate; it is not an executed
action until its field and timing are independently verified.
"""

import argparse
import json
from pathlib import Path
import struct

from skill_table_index import read_rows


def snapshots(trace):
    for line in trace.read_text(encoding="utf-8-sig").splitlines():
        if not line.startswith("{"):
            continue
        record = json.loads(line)
        if record.get("name") == "AttackEffectCall":
            for field in ("effect_descriptor_100", "result_frame_200",
                          "source_context_256", "target_context_256"):
                if record.get(field):
                    yield record["at"], "attack", field, bytes.fromhex(record[field])
        for snapshot in record.get("identity_snapshots", []):
            for field in ("context_600", "status_2a0"):
                if snapshot.get(field):
                    yield record["at"], snapshot["role"], field, bytes.fromhex(snapshot[field])
            for link in snapshot.get("links", []):
                if link.get("bytes_256"):
                    yield record["at"], snapshot["role"], f"link@{link['offset']}", bytes.fromhex(link["bytes_256"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("pac", type=Path)
    parser.add_argument("names", nargs="+", help="Exact skill display names")
    args = parser.parse_args()
    wanted = {row["packedId"]: row["name"] for row in read_rows(args.pac)
              if row["name"] in args.names}
    if not wanted:
        raise SystemExit("No exact skill names matched")
    found = 0
    for at, role, field, data in snapshots(args.trace):
        for offset in range(len(data) - 3):
            value = struct.unpack_from("<I", data, offset)[0]
            if value in wanted:
                print(f"{at} {role} {field}+0x{offset:x} "
                      f"{value:#010x} {wanted[value]}")
                found += 1
    print(f"{found} exact 32-bit occurrences in saved snapshots; none alone proves an executed move")


if __name__ == "__main__":
    main()
