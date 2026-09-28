"""Match verified party status IDs to exact-table names; leave other IDs unresolved."""

import argparse
import json
from pathlib import Path
import struct

from name_table_index import read_rows as read_name_rows, unique_id_lookup
from status_name_index import read_rows as read_status_rows


# Four independently identified live party statuses match direct t_name IDs.
# Do not generalize to other party IDs or enemy IDs without live confirmation.
VERIFIED_PARTY_IDS = {0: "Estelle", 2: "Scherazard", 5: "Agate", 6: "Tita"}


def match(snapshot, status_rows, name_rows):
    statuses = {row["unitId"]: row for row in status_rows}
    names = unique_id_lookup(name_rows)
    result = []
    for record in snapshot:
        if record.get("kind") != "status" or not record.get("bytes_256"):
            continue
        data = bytes.fromhex(record["bytes_256"])
        status_id, level, _, hp, max_hp = struct.unpack_from("<IIIII", data)
        row = names.get(status_id) if status_id in VERIFIED_PARTY_IDS else None
        status_row = statuses.get(row["statusUnitKey"]) if row else None
        if row is not None and (row["name"] != VERIFIED_PARTY_IDS[status_id] or
                                status_row is None or status_row["name"] != row["name"]):
            raise ValueError(f"Party table join mismatch for status ID {status_id}")
        result.append({"statusPtr": record["address"], "statusId": status_id,
                       "level": level, "hp": hp, "maxHp": max_hp,
                       "unitId": row["statusUnitKey"] if row else None,
                       "name": row["name"] if row else None,
                       "provenance": "verified-party-status-id + exact-English-t_name/t_status"
                       if row else "unresolved"})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("pac", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records = [json.loads(line) for line in args.snapshot.read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("{")]
    result = match(records, read_status_rows(args.pac), read_name_rows(args.pac))
    serialized = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
        print(f"Wrote {len(result)} status matches to {args.output}")
    else:
        print(serialized, end="")


if __name__ == "__main__":
    main()
