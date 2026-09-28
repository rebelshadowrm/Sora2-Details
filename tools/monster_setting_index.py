"""Read monster-setting unit keys from this build's English t_mon_mp0000.tbl.

These are static setting rows. Repeated keys are expected; row number is not a
live actor instance ID or evidence that the setting was active in a battle.
"""

import argparse
import hashlib
from pathlib import Path
import struct

from status_name_index import read_names


PAYLOAD_OFFSET = 0x286FEB
PAYLOAD_SIZE = 62457
PAYLOAD_SHA256 = "0d00dbadefbb5004d56613e277b86825f7efaa109ea8768c8d7679a9a59cdf1e"
ROW_START = 0x58
ROW_SIZE = 0xB0
ROW_COUNT = 252
STRING_START = ROW_START + ROW_SIZE * ROW_COUNT


def read_rows(pac_path):
    with pac_path.open("rb") as file:
        file.seek(PAYLOAD_OFFSET)
        data = file.read(PAYLOAD_SIZE)
    if hashlib.sha256(data).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("English monster-setting payload does not match the validated build")
    if data[:4] != b"#TBL" or data[8:27] != b"MonsterSettingParam":
        raise ValueError("Invalid monster-setting header")
    if struct.unpack_from("<II", data, 0x50) != (ROW_SIZE, ROW_COUNT):
        raise ValueError("Unexpected monster-setting row layout")
    rows = []
    for row_number in range(ROW_COUNT):
        key_offset = struct.unpack_from("<Q", data, ROW_START + row_number * ROW_SIZE)[0]
        if not STRING_START <= key_offset < len(data):
            raise ValueError(f"Invalid monster-setting key offset {key_offset:#x}")
        end = data.find(b"\0", key_offset)
        if end < 0:
            raise ValueError(f"Unterminated monster-setting key at {key_offset:#x}")
        rows.append({"row": row_number, "unitId": data[key_offset:end].decode("utf-8")})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path, help="Path to pac/steam/table_en.pac")
    parser.add_argument("query", nargs="*", help="Unit-key or display-name substring")
    args = parser.parse_args()
    rows = read_rows(args.pac)
    names = read_names(args.pac)
    queries = args.query or ["Emeronecider", "Lily Mover"]
    for row in rows:
        name = names.get(row["unitId"])
        if any(query.lower() in row["unitId"].lower() or
               query.lower() in (name or "").lower() for query in queries):
            print(f"row {row['row']}\t{row['unitId']}\t{name or 'UNKNOWN'}")
    print(f"{len(rows)} rows; {len(set(row['unitId'] for row in rows))} distinct unit keys")


if __name__ == "__main__":
    main()
