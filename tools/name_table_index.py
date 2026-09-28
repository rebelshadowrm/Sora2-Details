"""Read numeric character IDs and localized names from this Sora 2 English t_name.tbl.

This is a hash-gated metadata lookup. A live status ID must be verified before
using it as a name-table key; duplicate IDs remain ambiguous.
"""

import argparse
from collections import defaultdict
import hashlib
from pathlib import Path
import struct


PAYLOAD_OFFSET = 0x35BBD0
PAYLOAD_SIZE = 255068
PAYLOAD_SHA256 = "6101d18a87112e351c2ba1009933cc77b660630a0497c33d9119a81a9916c548"
ROW_START = 0x58
ROW_SIZE = 0x68
ROW_COUNT = 0x62F
NAME_FIELD = 8
VISUAL_MODEL_FIELD = 0x10
FACE_MODEL_FIELD = 0x18
CHARACTER_MODEL_FIELD = 0x20
STATUS_KEY_FIELD = 64


def cstring(data, offset):
    if not ROW_START + ROW_SIZE * ROW_COUNT <= offset < len(data):
        raise ValueError(f"Invalid name-table string offset {offset:#x}")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"Unterminated name-table string at {offset:#x}")
    return data[offset:end].decode("utf-8")


def read_rows(pac_path):
    with pac_path.open("rb") as file:
        file.seek(PAYLOAD_OFFSET)
        data = file.read(PAYLOAD_SIZE)
    if hashlib.sha256(data).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("English name-table payload does not match the validated build")
    if data[:4] != b"#TBL" or data[8:21] != b"NameTableData":
        raise ValueError("Invalid name-table header")
    row_size, row_count = struct.unpack_from("<II", data, 0x50)
    if (row_size, row_count) != (ROW_SIZE, ROW_COUNT):
        raise ValueError("Unexpected name-table row layout")
    rows = []
    for row_number in range(ROW_COUNT):
        offset = ROW_START + row_number * ROW_SIZE
        character_id = struct.unpack_from("<Q", data, offset)[0]
        name_offset = struct.unpack_from("<Q", data, offset + NAME_FIELD)[0]
        visual_model_offset = struct.unpack_from("<Q", data, offset + VISUAL_MODEL_FIELD)[0]
        face_model_offset = struct.unpack_from("<Q", data, offset + FACE_MODEL_FIELD)[0]
        character_model_offset = struct.unpack_from("<Q", data, offset + CHARACTER_MODEL_FIELD)[0]
        status_key_offset = struct.unpack_from("<Q", data, offset + STATUS_KEY_FIELD)[0]
        rows.append({
            "row": row_number,
            "characterId": character_id,
            "name": cstring(data, name_offset) if name_offset else "",
            "visualModelKey": cstring(data, visual_model_offset) if visual_model_offset else "",
            "faceModelKey": cstring(data, face_model_offset) if face_model_offset else "",
            "characterModelKey": cstring(data, character_model_offset) if character_model_offset else "",
            "statusUnitKey": cstring(data, status_key_offset) if status_key_offset else "",
        })
    return rows


def unique_id_lookup(rows):
    by_id = defaultdict(list)
    for row in rows:
        by_id[row["characterId"]].append(row)
    return {character_id: matches[0] for character_id, matches in by_id.items()
            if len(matches) == 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path, help="Path to pac/steam/table_en.pac")
    parser.add_argument("ids", nargs="*", type=lambda value: int(value, 0),
                        help="Character IDs (decimal or 0x hex); defaults to observed party IDs")
    args = parser.parse_args()
    rows = read_rows(args.pac)
    lookup = unique_id_lookup(rows)
    for character_id in args.ids or [0, 2, 5, 6]:
        row = lookup.get(character_id)
        if row is None:
            print(f"{character_id}\tUNKNOWN OR AMBIGUOUS")
        else:
            print(f"{character_id}\t{row['name']}\t{row['statusUnitKey']}")
    print(f"{len(rows)} rows; {len(lookup)} unique-ID rows checked")


if __name__ == "__main__":
    main()
