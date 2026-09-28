"""Read unit-key -> localized name pairs from this exact English status table.

The offsets below were checked against the installed Sora 2 table and the
Sora2 StatusParam schema in KuroTools. This is metadata lookup, not proof that
a live actor carries a particular unit key.
"""

import argparse
import hashlib
from pathlib import Path
import struct


PAYLOAD_OFFSET = 0x647B9F
PAYLOAD_SIZE = 546548
PAYLOAD_SHA256 = "71c3f47d5a2393d5efac262bd4db1da2283bef55dbb85169d54a118c213a0822"
ROW_START = 168
ROW_SIZE = 424
ROW_COUNT = 503
NAME_OFFSET = 408
STAT_FIELDS = {
    "level": (224, "<I"),
    "expBase": (228, "<I"),
    "expGrowth": (232, "<f"),
    "ep": (244, "<I"),
    "defBase": (264, "<I"),
    "defGrowth": (268, "<f"),
    "adfBase": (280, "<I"),
    "adfGrowth": (284, "<f"),
    "movBase": (312, "<I"),
    "movGrowth": (316, "<f"),
}


def cstring(data, offset):
    if not 0 < offset < len(data):
        raise ValueError(f"Invalid table string offset {offset:#x}")
    end = data.find(b"\0", offset)
    if end < 0:
        raise ValueError(f"Unterminated table string at {offset:#x}")
    return data[offset:end].decode("utf-8")


def read_rows(pac_path):
    with pac_path.open("rb") as file:
        file.seek(PAYLOAD_OFFSET)
        payload = file.read(PAYLOAD_SIZE)
    if hashlib.sha256(payload).hexdigest() != PAYLOAD_SHA256:
        raise ValueError("Installed English status table does not match the validated payload")
    if payload[:4] != b"#TBL" or ROW_START + ROW_COUNT * ROW_SIZE > len(payload):
        raise ValueError("Invalid status table layout")
    rows = []
    names = set()
    for index in range(ROW_COUNT):
        row = ROW_START + index * ROW_SIZE
        unit_offset = struct.unpack_from("<I", payload, row)[0]
        name_offset = struct.unpack_from("<I", payload, row + NAME_OFFSET)[0]
        unit_id, name = cstring(payload, unit_offset), cstring(payload, name_offset)
        if unit_id in names:
            raise ValueError(f"Duplicate unit key {unit_id}")
        names.add(unit_id)
        entry = {"row": index, "unitId": unit_id, "name": name}
        entry.update({field: struct.unpack_from(format, payload, row + offset)[0]
                      for field, (offset, format) in STAT_FIELDS.items()})
        rows.append(entry)
    return rows


def read_names(pac_path):
    return {row["unitId"]: row["name"] for row in read_rows(pac_path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path, help="Path to pac/steam/table_en.pac")
    parser.add_argument("query", nargs="*", help="Unit key or name substring; defaults to current party")
    args = parser.parse_args()
    names = read_names(args.pac)
    queries = args.query or ["Estelle", "Scherazard", "Tita", "Agate"]
    for unit_id, name in names.items():
        if any(query.lower() in unit_id.lower() or query.lower() in name.lower()
               for query in queries):
            print(f"{unit_id}\t{name}")
    print(f"{len(names)} unique unit keys checked", flush=True)


if __name__ == "__main__":
    main()
