"""Cross-check exact-build English metadata joins against saved live observations.

This is an offline table check, not a validation of runtime action IDs, monster
unit-key pointers, or complete command-battle capture.
"""

import argparse
from collections import Counter
from pathlib import Path

from item_table_index import read_rows as read_items
from monster_setting_index import read_rows as read_monster_settings
from name_table_index import read_rows as read_names, unique_id_lookup
from skill_table_index import read_rows as read_skills, rows_by_packed_id
from build_skill_icon_map import build_map as build_skill_icon_map
from status_name_index import read_rows as read_statuses


VERIFIED_PARTY = {
    0: ("Estelle", "chr5000p"),
    2: ("Scherazard", "chr5002p"),
    4: ("Kloe", "chr5004p"),
    5: ("Agate", "chr0005p"),
    6: ("Tita", "chr5006p"),
}
KNOWN_SKILLS = {
    0x000509CC: ("Final Break", 5),
    0x000007D5: ("Shatter Break", 0),
    0xFFFF00C8: ("Zodiac", 65535),
}


def check(pac_path):
    names = read_names(pac_path)
    unique_names = unique_id_lookup(names)
    statuses = {row["unitId"]: row for row in read_statuses(pac_path)}
    monsters = read_monster_settings(pac_path)
    skills = rows_by_packed_id(read_skills(pac_path))
    items = {row["itemId"]: row for row in read_items(pac_path)}

    for character_id, (expected_name, unit_key) in VERIFIED_PARTY.items():
        row = unique_names[character_id]
        assert (row["name"], row["statusUnitKey"]) == (expected_name, unit_key)
        assert row["faceModelKey"].endswith("_face")
        assert statuses[unit_key]["name"] == expected_name
    assert 60050 not in unique_names  # Captured enemy instance ID is not a table character ID.
    assert 65535 not in unique_names  # Costume/variant placeholder is reused.

    assert all(row["statusUnitKey"] in statuses for row in names if row["statusUnitKey"])
    assert all(row["unitId"] in statuses for row in monsters)
    monster_counts = Counter(row["unitId"] for row in monsters)
    assert monster_counts["mon5014_c02"] == 2
    assert monster_counts["mon5003"] == 22
    assert statuses["mon5014_c02"]["name"] == "Emeronecider"
    assert statuses["mon5003"]["name"] == "Lily Mover"

    for packed_id, (expected_name, owner_id) in KNOWN_SKILLS.items():
        assert len(skills[packed_id]) == 1
        row = skills[packed_id][0]
        assert (row["name"], row["ownerId"]) == (expected_name, owner_id)
    assert len(skills[0x000007D8]) == 2  # A packed ID is not always one row.
    assert len(skills) == 408
    # Same-actor live controls: physical Craft, Arts-damage Craft, and Art.
    # These are raw row values, not a validated runtime damage-class decoder.
    assert skills[0x000007D5][0]["rawParam30"] == 0xE  # Shatter Break
    assert (skills[0x000007D7][0]["name"],
            skills[0x000007D7][0]["rawParam30"]) == ("True Comet", 0xF)
    assert (skills[0xFFFF0099][0]["name"],
            skills[0xFFFF0099][0]["rawParam30"]) == ("Lightning", 0xF)

    icon_kinds = build_skill_icon_map(pac_path)["icons"]
    assert icon_kinds["0x000007D5"] == "craft"       # Shatter Break
    assert icon_kinds["0x000007D9"] == "craft"       # Two True Pummel rows agree.
    assert icon_kinds["0x000509CC"] == "scraft"      # Final Break
    assert icon_kinds["0xFFFF0099"] == "wind"        # Lightning
    assert icon_kinds["0xFFFF0087"] == "fire"        # Fire Bolt

    assert items[1]["name"] == "Tear Balm"
    assert (items[1]["effectCodeCandidate"], items[1]["effectValueCandidate"]) == (122, 1500)
    assert [items[item_id]["effectValueCandidate"] for item_id in (1, 2, 3)] == [1500, 3000, 6000]
    print("Cross-table joins passed: five live-verified party IDs, two monster keys,"
          " three skill IDs, and Tear Balm metadata.")
    print("Runtime enemy unit keys, action IDs, item IDs, and general damage-class coverage remain unverified.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path, help="Path to pac/steam/table_en.pac")
    args = parser.parse_args()
    check(args.pac)


if __name__ == "__main__":
    main()
