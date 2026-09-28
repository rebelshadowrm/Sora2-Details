"""Build icon-category metadata from this exact English t_skill table.

These categories select game UI symbols. They do not classify damage or prove
that a Craft and an Art have different result mechanics.
"""

import argparse
import json
from pathlib import Path

from skill_table_index import PAYLOAD_SHA256, read_rows, rows_by_packed_id


ICON_KINDS = {
    0x1: "attack",
    0x2: "craft",
    0x3: "scraft",
    0x6: "item",
    0x9: "craft",  # Alternate/continuation rows retain their Craft icon.
    0xB: "attack",
    0xD: "craft",
    0x104: "earth",
    0x204: "water",
    0x304: "fire",
    0x404: "wind",
    0x504: "time",
    0x604: "space",
    0x704: "mirage",
}


def build_map(pac_path):
    icons = {}
    for packed_id, rows in rows_by_packed_id(read_rows(pac_path)).items():
        candidates = {ICON_KINDS.get(row["rawParam10"]) for row in rows}
        if len(candidates) == 1 and None not in candidates:
            icons[f"0x{packed_id:08X}"] = candidates.pop()
    return {"tablePayloadSha256": PAYLOAD_SHA256, "icons": dict(sorted(icons.items()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("table_pac", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    document = build_map(args.table_pac)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(document['icons'])} unambiguous icon categories to {args.output}")


if __name__ == "__main__":
    main()
