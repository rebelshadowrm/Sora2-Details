"""Inspect this build's English skill IDs, names, and animation labels.

The table is static metadata. No live action field has yet been proven to carry
the packed ID, and neither a move name nor animation proves damage class.
"""

import argparse
from collections import defaultdict
import hashlib
from pathlib import Path
import struct


PAYLOAD_OFFSET = 0x6300F8
PAYLOAD_SIZE = 96935
PAYLOAD_SHA256 = "ae81526bef7e1dedc601145961a0786df48fb1b2c96407d4571e1f3bae3bfe8a"
ROW_START = 0xF8
ROW_SIZE = 0xB0
ROW_COUNT = 415
STRING_START = 0x1209E
SECTION_LAYOUT = (
    ("SkillParam", 0xB0, 415),
    ("SkillPowerIcon", 0x10, 13),
    ("SkillGetParam", 0x0A, 39),
)


def cstring(data, offset):
    if offset == 0:
        return ""
    if not STRING_START <= offset < len(data):
        raise ValueError(f"Invalid skill-table string offset {offset:#x}")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"Unterminated skill-table string at {offset:#x}")
    return data[offset:end].decode("utf-8")


def read_rows(pac_path):
    with pac_path.open("rb") as file:
        file.seek(PAYLOAD_OFFSET)
        data = file.read(PAYLOAD_SIZE)
    if hashlib.sha256(data).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("English skill-table payload does not match the validated build")
    if data[:4] != b"#TBL" or struct.unpack_from("<I", data, 4)[0] != 3:
        raise ValueError("Invalid skill-table header")
    for index, (name, size, count) in enumerate(SECTION_LAYOUT):
        descriptor = 8 + index * 80
        found_name = data[descriptor:descriptor + 64].split(b"\0", 1)[0].decode("ascii")
        found_layout = struct.unpack_from("<II", data, descriptor + 72)
        if (found_name, *found_layout) != (name, size, count):
            raise ValueError(f"Unexpected {name} section layout")
    if ROW_START + sum(size * count for _, size, count in SECTION_LAYOUT) != STRING_START:
        raise ValueError("Skill section data do not reach expected string pool")
    rows = []
    for row_number in range(ROW_COUNT):
        offset = ROW_START + row_number * ROW_SIZE
        packed_id = struct.unpack_from("<I", data, offset)[0]
        animation_offset = struct.unpack_from("<Q", data, offset + 0x90)[0]
        name_offset = struct.unpack_from("<Q", data, offset + 0x98)[0]
        description_offset = struct.unpack_from("<Q", data, offset + 0xA8)[0]
        rows.append({
            "row": row_number,
            "packedId": packed_id,
            "ownerId": packed_id >> 16,
            "skillId": packed_id & 0xFFFF,
            # Raw SkillParam words. Their semantics require a live action-to-row
            # join; in particular rawParam30 is only a damage-class candidate.
            "rawParam10": struct.unpack_from("<I", data, offset + 0x10)[0],
            "rawParam20": struct.unpack_from("<I", data, offset + 0x20)[0],
            "rawParam30": struct.unpack_from("<I", data, offset + 0x30)[0],
            "name": cstring(data, name_offset),
            "animation": cstring(data, animation_offset),
            "description": cstring(data, description_offset),
        })
    return rows


def rows_by_packed_id(rows):
    by_id = defaultdict(list)
    for row in rows:
        by_id[row["packedId"]].append(row)
    return dict(by_id)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path, help="Path to pac/steam/table_en.pac")
    parser.add_argument("query", nargs="*", help="Name substring or packed ID (decimal/0x hex)")
    args = parser.parse_args()
    rows = read_rows(args.pac)
    by_id = rows_by_packed_id(rows)
    queries = args.query or ["Final Break", "Shatter Break", "Zodiac"]
    numeric_queries = set()
    name_queries = []
    for query in queries:
        if query.isdecimal():
            numeric_queries.add(int(query))
        elif query.lower().startswith("0x"):
            numeric_queries.add(int(query, 16))
        else:
            name_queries.append(query.lower())
    selected = []
    for row in rows:
        if row["packedId"] in numeric_queries or any(
                query in row["name"].lower() for query in name_queries):
            selected.append(row)
    for row in selected:
        ambiguous = " AMBIGUOUS" if len(by_id[row["packedId"]]) > 1 else ""
        print(f"row {row['row']}\t{row['packedId']:#010x}\towner {row['ownerId']}"
              f"\tskill {row['skillId']}\t{row['name']}\t{row['animation']}{ambiguous}")
    print(f"{len(rows)} rows; {len(by_id)} distinct packed IDs checked")


if __name__ == "__main__":
    main()
