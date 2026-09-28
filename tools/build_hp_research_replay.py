"""Create an explicitly partial meter replay from observed HP writes.

This is a research artifact, not a game adapter. The caller supplies the
command-battle interval and visible outcome; unknown sources and moves stay
unknown. Only changes to the watched actor's HP enter the replay.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path


def parse_time(value):
    return datetime.fromisoformat(value)


def build(trace_path, start, end, outcome, actor_name):
    records = [json.loads(line) for line in trace_path.read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("{")]
    if not any(record.get("kind") == "detached" for record in records):
        raise ValueError("Probe trace did not detach cleanly")
    within = [record for record in records if start <= parse_time(record["at"]) <= end]
    if not any(record.get("name") == "BattleCommandBegin" for record in within):
        raise ValueError("No command-battle callback in selected interval")
    if not any(record.get("name") == "BattleEnd" for record in within):
        raise ValueError("No battle-end callback in selected interval")
    events = []
    for record in within:
        if record.get("kind") != "hit" or record.get("name") != "AgateHp":
            continue
        before, after = record.get("before"), record.get("after")
        if not isinstance(before, int) or not isinstance(after, int) or before == after:
            continue
        events.append({
            "sequence": len(events) + 1,
            "observedAt": record["at"],
            "actionId": None,
            "sourceId": None,
            "targetId": "observed-agate",
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
    issues = [
        "Research replay: only Agate's HP was watched; enemy HP and other party HP were not captured.",
        "Encounter start was not observed; the interval starts at a command callback.",
        f"{outcome} was reported by the player; the probe observed an end callback, not an outcome value.",
        "Sources, moves, damage classes and displayed amounts were not observed.",
        "One HP write may combine multiple visible hits; each row is an HP change, not a proven action.",
    ]
    return [{
        "id": "research-20260926-agate-hp",
        "label": f"Agate HP only - {outcome} (partial)",
        "startedAt": start.isoformat(),
        "outcome": outcome,
        "isComplete": False,
        "actors": [{"id": "observed-agate", "name": actor_name, "team": "Party"}],
        "events": events,
        "issues": issues,
    }]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--start-at", required=True, type=parse_time)
    parser.add_argument("--end-at", required=True, type=parse_time)
    parser.add_argument("--outcome", choices=("Victory", "Escape", "Defeat"), required=True)
    parser.add_argument("--actor-name", default="Agate")
    args = parser.parse_args()
    if args.start_at >= args.end_at:
        parser.error("start must be before end")
    replay = build(args.trace, args.start_at, args.end_at, args.outcome, args.actor_name)
    args.output.write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(replay[0]['events'])} observed HP changes to {args.output}")


if __name__ == "__main__":
    main()
