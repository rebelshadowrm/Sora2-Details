"""Build a manually bounded, partial replay from paired attack and HP records.

The probe verifies source/target pointers and effective HP loss for this path.
Battle boundaries, names, move labels and coverage still need external evidence.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path


def parse_time(value):
    return datetime.fromisoformat(value)


def build(trace_path, actor_map_path, start, end, outcome, known_move_at=None, known_move=None):
    records = [json.loads(line) for line in trace_path.read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("{")]
    if not any(record.get("kind") == "detached" for record in records):
        raise ValueError("Probe trace did not detach cleanly")
    mapping = json.loads(actor_map_path.read_text(encoding="utf-8"))
    if len({actor["id"] for actor in mapping.values()}) != len(mapping):
        raise ValueError("Actor IDs must be unique")
    within = [record for record in records if start <= parse_time(record["at"]) <= end]
    if not any(record.get("name") == "BattleEnd" for record in within):
        raise ValueError("No battle-end callback in selected interval")
    pending = {}
    events = []
    matched_known_move = False
    for record in within:
        name = record.get("name")
        if name == "AttackEffectCall":
            tid = record["tid"]
            if tid in pending:
                raise ValueError(f"Unpaired attack call on thread {tid}")
            pending[tid] = record
        elif name == "HpSet":
            tid = record["tid"]
            if tid not in pending:
                raise ValueError(f"HP setter without paired attack call at {record['at']}")
            attack = pending.pop(tid)
            source, target = (attack.get("source_status_ptr"), attack.get("target_status_ptr"))
            if source not in mapping or target not in mapping or target != record["status_ptr"]:
                raise ValueError(f"Source/target pointer mismatch at {record['at']}")
            before, maximum, requested = (record.get(key) for key in
                                          ("hp_before", "hp_max", "requested_hp"))
            if not all(isinstance(value, int) for value in (before, maximum, requested)):
                raise ValueError(f"Unreadable HP setter at {record['at']}")
            if not 0 <= before <= maximum or maximum <= 0:
                raise ValueError(f"Invalid HP bounds at {record['at']}")
            after = max(0, min(maximum, requested))
            resolved = attack["candidate_resolved_amount"]
            if requested >= 0 and resolved != before - requested:
                raise ValueError(f"Attack amount and HP request disagree at {record['at']}")
            is_known_move = known_move_at is not None and parse_time(attack["at"]) == known_move_at
            if is_known_move:
                matched_known_move = True
            events.append({
                "sequence": len(events) + 1,
                "observedAt": record["at"],
                "actionId": None,
                "sourceId": mapping[source]["id"],
                "targetId": mapping[target]["id"],
                "moveId": None,
                "moveName": known_move if is_known_move else None,
                "kind": "Damage",
                "effectiveAmount": before - after,
                "hpBefore": before,
                "hpAfter": after,
                "damageClass": "Unknown",
                "resolvedAmount": resolved if is_known_move else None,
            })
    if pending:
        raise ValueError("Attack call(s) without HP setter")
    if not events or (known_move_at is not None and not matched_known_move):
        raise ValueError("No paired effects or known move time not found")
    actors = [dict(id=actor["id"], name=actor["name"], team=actor["team"])
              for actor in mapping.values()]
    return [{
        "id": "research-20260926-attributed-attack",
        "label": f"Attributed attack path - {outcome} (partial)",
        "startedAt": start.isoformat(),
        "outcome": outcome,
        "isComplete": False,
        "actors": actors,
        "events": events,
        "issues": [
            "Research replay: the command interval and victory were player-confirmed, not automatically bounded.",
            "The source/target pointers and HP changes were paired only for one attack-result path; other effect paths are not covered.",
            "Actor names/teams come from the player's roster and prior HP mapping; enemy names remain unknown.",
            "Only the timed normal Attack has a player-reported move label; other moves and all damage classes are unknown.",
            "Effective HP loss excludes overkill and repeated hits on an already-zero-HP target.",
            "Earlier Escape/re-entry and any field effects are excluded from this selected interval.",
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
    parser.add_argument("--known-move-at", type=parse_time)
    parser.add_argument("--known-move")
    args = parser.parse_args()
    if args.start_at >= args.end_at or bool(args.known_move_at) != bool(args.known_move):
        parser.error("invalid interval or known-move arguments")
    replay = build(args.trace, args.actor_map, args.start_at, args.end_at,
                   args.outcome, args.known_move_at, args.known_move)
    args.output.write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(replay[0]['events'])} paired attack results to {args.output}")


if __name__ == "__main__":
    main()
