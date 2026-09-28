"""Build a partial meter replay from one manually bounded attack/HP probe.

This projects paired damage results only. Standalone HP writes and unsupported
action/status outcomes are counted as gaps; they are never silently decoded.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path


def build(trace_path, actor_map_path, encounter_id, outcome, move_at, move_name):
    records = [json.loads(line) for line in trace_path.read_text(encoding="utf-8-sig").splitlines()
               if line.startswith("{")]
    if not any(record.get("kind") == "detached" for record in records):
        raise ValueError("Probe did not detach cleanly")
    executable = next((record for record in records if record.get("kind") == "executable"), None)
    if not executable or executable.get("sha256") != (
            "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"):
        raise ValueError("Unexpected executable fingerprint")
    mapping = json.loads(actor_map_path.read_text(encoding="utf-8"))
    if len({actor["id"] for actor in mapping.values()}) != len(mapping):
        raise ValueError("Actor IDs must be unique")

    pending = {}
    events = []
    other_hp = []
    for record in records:
        name = record.get("name")
        tid = record.get("tid")
        if name == "AttackEffectCall":
            if tid in pending:
                raise ValueError(f"Overlapping attack calls on thread {tid}")
            pending[tid] = record
        elif name == "HpSet":
            attack = pending.get(tid)
            if attack is None:
                other_hp.append(record)
                continue
            if attack.get("target_status_ptr") != record.get("status_ptr"):
                raise ValueError(f"Attack/HP target mismatch at {record['at']}")
            del pending[tid]
            source = attack.get("source_status_ptr")
            target = attack.get("target_status_ptr")
            if source not in mapping or target not in mapping:
                raise ValueError(f"Unmapped actor at {record['at']}")
            before, maximum, requested = (record.get(key) for key in
                                          ("hp_before", "hp_max", "requested_hp"))
            amount = attack.get("candidate_resolved_amount")
            if not all(isinstance(value, int) for value in (before, maximum, requested, amount)):
                raise ValueError(f"Unreadable result at {record['at']}")
            if not 0 <= before <= maximum or maximum <= 0 or amount < 0:
                raise ValueError(f"Invalid HP bounds or amount at {record['at']}")
            if requested >= 0 and amount != before - requested:
                raise ValueError(f"Nonlethal amount and HP request disagree at {record['at']}")
            after = max(0, min(maximum, requested))
            if after > before:
                raise ValueError(f"Attack increased HP at {record['at']}")
            known = move_at is not None and datetime.fromisoformat(attack["at"]) == move_at
            events.append({
                "sequence": len(events) + 1,
                "observedAt": attack["at"],
                "actionId": None,
                "sourceId": mapping[source]["id"],
                "targetId": mapping[target]["id"],
                "moveId": None,
                "moveName": move_name if known else None,
                "kind": "Damage",
                "effectiveAmount": before - after,
                "hpBefore": before,
                "hpAfter": after,
                "damageClass": "Unknown",
                "resolvedAmount": amount,
            })
    if pending or not events:
        raise ValueError("Unpaired attack calls or no results")
    if move_at is not None and not any(event["moveName"] for event in events):
        raise ValueError("Known move timestamp not found")

    # A replay is a damage projection of the raw trace, never a completeness claim.
    issues = [
        "Research replay: entry and victory were player-confirmed, not captured by this probe.",
        "Only the paired attack/HP path is projected; action IDs, support effects, and damage classes are unknown.",
        f"{len(other_hp)} HP writes had no attack-call partner and are omitted from this damage projection; inspect the raw trace.",
        "Move label is player-reported; other moves and Burst/follow-up relationships are not identified by runtime IDs.",
        "Resolved amounts are candidate attack-call values; lethal HP requests use a -1 sentinel and effective damage is clamped.",
    ]
    return [{
        "id": encounter_id,
        "label": f"Attack/HP research - {outcome} (partial)",
        "startedAt": events[0]["observedAt"],
        "outcome": outcome,
        "isComplete": False,
        "actors": [dict(id=actor["id"], name=actor["name"], team=actor["team"])
                   for actor in mapping.values()],
        "events": events,
        "issues": issues,
    }], len(other_hp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("actor_map", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--encounter-id", required=True)
    parser.add_argument("--outcome", choices=("Victory", "Escape", "Defeat"), required=True)
    parser.add_argument("--known-move-at", type=datetime.fromisoformat)
    parser.add_argument("--known-move")
    args = parser.parse_args()
    if bool(args.known_move_at) != bool(args.known_move):
        parser.error("Supply both known-move options or neither")
    replay, other_hp = build(args.trace, args.actor_map, args.encounter_id,
                             args.outcome, args.known_move_at, args.known_move)
    args.output.write_text(json.dumps(replay, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(replay[0]['events'])} paired damage results; "
          f"{other_hp} other HP writes remain outside the projection")


if __name__ == "__main__":
    main()
