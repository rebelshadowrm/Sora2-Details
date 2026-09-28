"""Build a partial meter replay from a manually bounded HP-setter trace.

Actor/team mapping and visible outcome are supplied by the researcher. This
does not establish attack source or move identity, and must not be used as an
automatic game adapter.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path


def parse_time(value):
    return datetime.fromisoformat(value)


def build(trace_path, actor_map_path, start, end, outcome):
    records = [json.loads(line) for line in trace_path.read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("{")]
    if not any(record.get("kind") == "detached" for record in records):
        raise ValueError("Probe trace did not detach cleanly")
    mapping = json.loads(actor_map_path.read_text(encoding="utf-8"))
    if not mapping or any(actor.get("team") not in ("Party", "Enemy") for actor in mapping.values()):
        raise ValueError("Actor map needs Party/Enemy teams")
    if len({actor.get("id") for actor in mapping.values()}) != len(mapping):
        raise ValueError("Actor IDs must be unique")
    within = [record for record in records if start <= parse_time(record["at"]) <= end]
    if not any(record.get("name") == "BattleEnd" for record in within):
        raise ValueError("No battle-end callback in selected interval")
    events = []
    last_hp = {}
    for record in within:
        if record.get("kind") != "hit" or record.get("name") != "HpSet":
            continue
        pointer = record["status_ptr"].lower()
        if pointer not in mapping:
            raise ValueError(f"Unmapped HP status pointer: {pointer}")
        before, maximum, requested = (record.get(field) for field in
                                      ("hp_before", "hp_max", "requested_hp"))
        if not all(isinstance(value, int) for value in (before, maximum, requested)):
            raise ValueError(f"Unreadable HP setter at {record['at']}")
        if maximum <= 0 or not 0 <= before <= maximum:
            raise ValueError(f"Invalid HP bounds at {record['at']}")
        if pointer in last_hp and before != last_hp[pointer]:
            raise ValueError(f"HP setter continuity gap for {pointer} at {record['at']}")
        after = max(0, min(maximum, requested))
        last_hp[pointer] = after
        if after == before:
            continue
        events.append({
            "sequence": len(events) + 1,
            "observedAt": record["at"],
            "actionId": None,
            "sourceId": None,
            "targetId": mapping[pointer]["id"],
            "moveId": None,
            "moveName": None,
            "kind": "Damage" if after < before else "Healing",
            "effectiveAmount": abs(after - before),
            "hpBefore": before,
            "hpAfter": after,
            "damageClass": "Unknown",
            "resolvedAmount": None,
        })
    if not events:
        raise ValueError("No changed HP values in selected interval")
    actors = [dict(id=value["id"], name=value["name"], team=value["team"])
              for value in mapping.values()]
    return [{
        "id": "research-20260926-hp-setter",
        "label": f"Observed HP totals - {outcome} (partial)",
        "startedAt": start.isoformat(),
        "outcome": outcome,
        "isComplete": False,
        "actors": actors,
        "events": events,
        "issues": [
            "Research replay: battle interval and outcome were confirmed by the player, not detected as an outcome value.",
            "BattleStart did not fire; this interval was manually bounded. The player reported no preceding quick-battle hits.",
            "Actor teams were mapped from the player's two-enemy roster and observed party HP layout; identities remain provisional unless named by the player.",
            "HP after is derived from the observed requested value and code clamp; only Agate has an independent write watchpoint.",
            "Attacker, move, damage class and displayed amount were not observed. One HP setter call is not a proven action.",
            "Only the observed HP-setter branch is covered; other HP paths and dropped events are not ruled out.",
        ],
    }]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("actor_map", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start-at", required=True, type=parse_time)
    parser.add_argument("--end-at", required=True, type=parse_time)
    parser.add_argument("--outcome", choices=("Victory", "Escape", "Defeat"), required=True)
    args = parser.parse_args()
    if args.start_at >= args.end_at:
        parser.error("start must be before end")
    replay = build(args.trace, args.actor_map, args.start_at, args.end_at, args.outcome)
    args.output.write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(replay[0]['events'])} observed HP changes to {args.output}")


if __name__ == "__main__":
    main()
