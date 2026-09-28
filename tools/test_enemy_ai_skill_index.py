"""Offline exact-archive checks for the per-monster AI skill lookup."""

import argparse
from pathlib import Path

from enemy_ai_skill_index import EnemyAiSkillIndex


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pac", type=Path)
    args = parser.parse_args()
    index = EnemyAiSkillIndex(args.pac)
    assert index.skill_names("mon5031")[1000] == ["Fate Saber"]
    assert index.skill_names("mon5031")[1001] == ["Wonder Blaze"]
    assert index.skill_names("mon5023")[1000] == ["Force of Nature"]
    assert index.skill_names("mon5036")[1000] == ["Snow Breath"]
    assert index.skill_names("mon5014_c02")[1000] == ["Wild Horn"]
    assert index.skill_names("../../mon5031") == {}
    print("Exact English enemy AI archive and ID/name controls passed.")


if __name__ == "__main__":
    main()
