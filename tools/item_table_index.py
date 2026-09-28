"""Read exact-English item IDs, names, and candidate effect values for this build.

The numeric value at row+0x40 matches Tear Balm's observed 1,500 heal, but its
meaning varies by item/effect type and is not a general resolved-heal amount.
"""

import argparse
import hashlib
from pathlib import Path
import struct


PAYLOAD_OFFSET = 0x1A7CD4
PAYLOAD_SIZE = 472790
PAYLOAD_SHA256 = "16a8703a01e02ec9782d2d36dbdf1f3b150ba96982cf141c6a49f301a351abea"
ROW_START = 0x148
ROW_SIZE = 0x100
ROW_COUNT = 1382
STRING_START = 0x56A9C
SECTION_LAYOUT = (
    ("ItemTableData", 0x100, 1382),
    ("ItemKindParam2", 0x10, 30),
    ("ItemTabType", 0x0C, 17),
    ("ItemShopTabType", 0x08, 21),
)


def cstring(data, offset):
    if offset == 0:
        return ""
    if not STRING_START <= offset < len(data):
        raise ValueError(f"Invalid item-table string offset {offset:#x}")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"Unterminated item-table string at {offset:#x}")
    return data[offset:end].decode("utf-8")


def read_rows(pac_path):
    with pac_path.open("rb") as file:
        file.seek(PAYLOAD_OFFSET)
        data = file.read(PAYLOAD_SIZE)
    if hashlib.sha256(data).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("English item-table payload does not match the validated build")
    if data[:4] != b"#TBL" or struct.unpack_from("<I", data, 4)[0] != 4:
        raise ValueError("Invalid item-table header")
    for index, (name, size, count) in enumerate(SECTION_LAYOUT):
        descriptor = 8 + index * 80
        found_name = data[descriptor:descriptor + 64].split(b"\0", 1)[0].decode("ascii")
        found_layout = struct.unpack_from("<II", data, descriptor + 72)
        if (found_name, *found_layout) != (name, size, count):
            raise ValueError(f"Unexpected {name} section layout")
    if ROW_START + sum(size * count for _, size, count in SECTION_LAYOUT) != STRING_START:
        raise ValueError("Item section data do not reach expected string pool")
    rows = []
    seen_ids = set()
    for row_number in range(ROW_COUNT):
        offset = ROW_START + row_number * ROW_SIZE
        item_id = struct.unpack_from("<I", data, offset)[0]
        if item_id in seen_ids:
            raise ValueError(f"Duplicate item ID {item_id}")
        seen_ids.add(item_id)
        rows.append({
            "row": row_number,
            "itemId": item_id,
            "effectCodeCandidate": struct.unpack_from("<I", data, offset + 0x3C)[0],
            "effectValueCandidate": struct.unpack_from("<I", data, offset + 0x40)[0],
            "animation": cstring(data, struct.unpack_from("<Q", data, offset + 0xD8)[0]),
            "name": cstring(data, struct.unpack_from("<Q", data, offset + 0xE0)[0]),
            "description": cstring(data, struct.unpack_from("<Q", data, offset + 0xE8)[0]),
        })
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path, help="Path to pac/steam/table_en.pac")
    parser.add_argument("query", nargs="*", help="Item ID or name substring")
    args = parser.parse_args()
    rows = read_rows(args.pac)
    queries = args.query or ["Tear Balm", "Teara Balm", "Tearal Balm"]
    for row in rows:
        if any(query.lower() in row["name"].lower() or query == str(row["itemId"])
               for query in queries):
            print(f"row {row['row']}\tid {row['itemId']}\t{row['name']}"
                  f"\teffect code {row['effectCodeCandidate']}"
                  f"\tvalue {row['effectValueCandidate']}")
    print(f"{len(rows)} unique item IDs checked")


if __name__ == "__main__":
    main()
