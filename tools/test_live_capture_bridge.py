"""Offline command-battle scope and pairing check; does not attach to the game."""

import json
from pathlib import Path
import struct
import tempfile

from live_capture_bridge import (LiveBridge, consume, damage_class_for_flags,
                                 source_context_flags, lookup_live_move,
                                 observed_effect_descriptor, target_status_7c)


def main():
    control_trace = (Path(__file__).resolve().parents[1] / "samples" / "research" /
                     "probe-session-03143c21c411410485de04e85427abae.jsonl")
    controls = {row["candidate_resolved_amount"]: row
                for row in (json.loads(line) for line in control_trace.open(encoding="utf-8"))
                if row.get("name") == "AttackEffectCall" and row.get("source_actor_id") == 5}
    assert [source_context_flags(controls[amount]) for amount in (11058, 11624, 15156)] == [3, 1, 3]
    assert [target_status_7c(controls[amount]) for amount in (11058, 11624, 15156)] == [0, 0, 3]
    assert source_context_flags(dict(controls[11058], source_context_256="")) is None
    assert target_status_7c(dict(controls[11058], target_status_256="")) is None
    assert damage_class_for_flags(0x42000) == "Physical"
    assert damage_class_for_flags(0x52000) == "Unknown"
    assert damage_class_for_flags(0x52002) == "Unknown"
    assert damage_class_for_flags(0x62220) == "Unknown"
    at = "2026-09-27T10:00:00.000-05:00"
    enemy_row = {"name": "Synthetic Enemy", "unitId": "mon-synthetic",
                 "level": 54, "expBase": 301,
                 "expGrowth": 0.0, "ep": 1000, "defBase": 361,
                 "defGrowth": 0.0, "adfBase": 321, "adfGrowth": 0.0,
                 "movBase": 6, "movGrowth": 0.0}
    status = bytearray(0x2A0)
    for offset, value in zip((0, 0x4, 0x8, 0x18, 0x28, 0x30, 0x40),
                             (60050, 54, 301, 1000, 361, 321, 6)):
        struct.pack_into("<I", status, offset, value)
    records = [
        {"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
         "source_status_ptr": "0x11", "target_status_ptr": "0x22",
         "source_actor_id": 5, "target_actor_id": 60050,
         "candidate_resolved_amount": 99},  # Field combat: excluded.
        {"at": at, "kind": "hit", "name": "BattleInit", "tid": 1},
        {"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
         "source_status_ptr": "0x11", "target_status_ptr": "0x22",
         "source_actor_id": 5, "target_actor_id": 60050,
         "candidate_resolved_amount": 10,
         "candidate_result_flags": 0x42000,
         "identity_snapshots": [{"role": "target", "status_ptr": "0x22",
                                 "status_2a0": status.hex()}]},
        {"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
         "status_ptr": "0x22", "status_actor_id": 60050,
         "hp_before": 20, "hp_max": 20, "requested_hp": 10},
        {"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
         "status_ptr": "0x11", "status_actor_id": 5,
         "hp_before": 50, "hp_max": 60, "requested_hp": 60},
        {"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
         "status_ptr": "0x11", "status_actor_id": 5,
         "hp_before": 60, "hp_max": 60, "requested_hp": 55},
        {"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
         "status_ptr": "0x11", "status_actor_id": 5,
         "hp_before": 55, "hp_max": 60, "requested_hp": 55},
        {"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
         "source_status_ptr": "0x22", "target_status_ptr": "0x11",
         "source_actor_id": 60050, "target_actor_id": 5,
         "candidate_resolved_amount": 56},
        {"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
         "status_ptr": "0x11", "status_actor_id": 5,
         "hp_before": 55, "hp_max": 60, "requested_hp": -1},
        {"at": at, "kind": "hit", "name": "BattleEnd", "tid": 1},
        {"at": at, "kind": "hit", "name": "BattleEnd", "tid": 1},
        {"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
         "source_status_ptr": "0x11", "target_status_ptr": "0x22",
         "source_actor_id": 5, "target_actor_id": 60050,
         "candidate_resolved_amount": 99},  # Field combat: excluded.
        {"at": at, "kind": "hit", "name": "BattleInit", "tid": 1},
        {"at": at, "kind": "detached"},
    ]
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        trace = root / "synthetic.jsonl"
        trace.write_text("".join(json.dumps(record) + "\n" for record in records),
                         encoding="utf-8")
        bridge = consume(trace, root / "encounters", table_rows=[enemy_row])
        encounters = [json.loads(path.read_text(encoding="utf-8"))
                      for path in (root / "encounters").glob("*.json")]
        assert bridge.changed >= 6
        assert len(encounters) == 2
        first = next(encounter for encounter in encounters if encounter["outcome"] == "Unknown")
        assert [event["kind"] for event in first["events"]] == [
            "Damage", "Healing", "HpLoss", "Unknown", "Damage", "Knockout"]
        assert [event["effectiveAmount"] for event in first["events"]] == [10, 10, 5, None, 55, None], first["events"]
        assert first["events"][0]["rawResultFlags"] == 0x42000
        assert first["events"][0]["isCritical"] is None
        assert first["events"][0]["damageClass"] == "Physical"
        assert {actor["name"] for actor in first["actors"]} == {"Agate", "Synthetic Enemy"}
        assert next(actor for actor in first["actors"] if actor["team"] == "Enemy")["nameProvenance"] == "unique-stat-signature/exact-English-t_status"
        assert not first["isComplete"] and first["issues"]
        second = next(encounter for encounter in encounters if encounter["outcome"] == "Interrupted")
        assert second["events"] == []
        # Rebuilding a saved raw session updates the same encounters.
        consume(trace, root / "encounters", table_rows=[enemy_row])
        assert len(list((root / "encounters").glob("*.json"))) == 2
        ambiguous = LiveBridge(root / "ambiguous", "synthetic.jsonl",
                               table_rows=[enemy_row, dict(enemy_row, name="Another Enemy")])
        ambiguous.start({"at": at})
        ambiguous.observe_identity(records[2])
        ambiguous.actor("0x22", 60050)
        assert ambiguous.current["actors"][0]["name"] == "? Enemy 1 (ID 60050)"
        assert ambiguous.current["actors"][0]["nameProvenance"] == "unresolved"
        assert ambiguous.current["actors"][0]["nameLookupStatus"] == "ambiguous"
        assert ambiguous.current["actors"][0]["nameLookupSignature"] == {
            "level": 54, "exp": 301, "ep": 1000, "def": 361, "adf": 321, "mov": 6}
        assert ambiguous.current["actors"][0]["nameLookupCandidates"] == [
            {"unitId": "mon-synthetic", "name": "Synthetic Enemy"},
            {"unitId": "mon-synthetic", "name": "Another Enemy"}]
        assert any("ambiguous" in issue for issue in ambiguous.current["issues"])
        hit_status = LiveBridge(root / "hit_status", "synthetic.jsonl", table_rows=[enemy_row])
        hit_status.handle({"at": at, "kind": "hit", "name": "BattleInit"})
        hit_status.handle({"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
                           "source_status_ptr": "0x22", "source_actor_id": 60050,
                           "source_status_256": status[:256].hex(),
                           "target_status_ptr": "0x11", "target_actor_id": 5,
                           "candidate_resolved_amount": 10})
        hit_status.actor("0x22", 60050)
        assert hit_status.current["actors"][0]["name"] == "Synthetic Enemy"
        assert hit_status.current["actors"][0]["nameLookupStatus"] == "matched"
        assert hit_status.current["actors"][0]["nameLookupCandidateCount"] == 1
        no_match = LiveBridge(root / "no_match", "synthetic.jsonl", table_rows=[enemy_row])
        no_match.handle({"at": at, "kind": "hit", "name": "BattleInit"})
        other_status = bytearray(status)
        struct.pack_into("<I", other_status, 0x4, 55)
        no_match.handle({"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
                         "source_status_ptr": "0x22", "source_actor_id": 60050,
                         "source_status_256": other_status[:256].hex(),
                         "target_status_ptr": "0x11", "target_actor_id": 5,
                         "candidate_resolved_amount": 10})
        no_match.actor("0x22", 60050)
        assert no_match.current["actors"][0]["name"] == "? Enemy 1 (ID 60050)"
        assert no_match.current["actors"][0]["nameLookupStatus"] == "missing"
        assert no_match.current["actors"][0]["nameLookupCandidates"] == []
        interleaved = LiveBridge(root / "interleaved", "interleaved.jsonl")
        interleaved.start({"at": at})
        interleaved.handle({"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
                            "source_status_ptr": "0x11", "source_actor_id": 5,
                            "target_status_ptr": "0x22", "target_actor_id": 60050,
                            "candidate_resolved_amount": 10})
        interleaved.handle({"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
                            "status_ptr": "0x11", "status_actor_id": 5,
                            "hp_before": 20, "hp_max": 30, "requested_hp": 25})
        assert 1 in interleaved.pending
        interleaved.handle({"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
                            "status_ptr": "0x22", "status_actor_id": 60050,
                            "hp_before": 20, "hp_max": 20, "requested_hp": 10})
        assert [event["kind"] for event in interleaved.current["events"]] == ["Healing", "Damage"]
        assert interleaved.current["events"][0]["sourceId"] is None
        assert interleaved.current["events"][1]["sourceId"] == "status-11"
        assert not interleaved.pending
        swapped = LiveBridge(root / "swapped", "synthetic.jsonl", name_rows=[
            {"characterId": 4, "name": "Kloe", "statusUnitKey": "chr5004p"}])
        swapped.start({"at": at})
        swapped.actor("0x44", 4)
        assert swapped.current["actors"][0]["name"] == "Kloe"
        assert swapped.current["actors"][0]["nameProvenance"] == "live-status-ID/exact-English-t_name"
        assert swapped.current["actors"][0]["lookupUnitId"] == "chr5004p"
        assert swapped.current["actors"][0]["runtimeStatusId"] == 4
        skill_rows = [
            {"packedId": 0x7D5, "ownerId": 0, "name": "Shatter Break",
             "rawParam10": 2, "rawParam20": 0x126, "rawParam30": 0xE},
            {"packedId": 0x7D7, "ownerId": 0, "name": "True Comet",
             "rawParam10": 2, "rawParam20": 0x1124, "rawParam30": 0xF},
            {"packedId": 0x3E, "ownerId": 0, "name": "Normal Attack",
             "rawParam10": 1, "rawParam20": 0x109, "rawParam30": 0xC},
        ]
        move_bridge = LiveBridge(root / "moves", "moves.jsonl", skill_rows=skill_rows)
        move_bridge.start({"at": at})
        for index, (row, expected_class) in enumerate(zip(
                skill_rows, ("Physical", "Arts", "Physical"))):
            descriptor = bytearray(0x100)
            for offset, value in ((0, row["packedId"]), (0x10, row["rawParam10"]),
                                  (0x20, row["rawParam20"]), (0x30, row["rawParam30"])):
                struct.pack_into("<I", descriptor, offset, value)
            attack = {"at": at, "kind": "hit", "name": "AttackEffectCall", "tid": 1,
                      "source_status_ptr": "0x11", "target_status_ptr": "0x22",
                      "source_actor_id": 0, "target_actor_id": 60050,
                      "candidate_resolved_amount": 10,
                      "candidate_result_flags": 0x62220 if index == 2 else 0x52000,
                      "effect_descriptor_100": descriptor.hex()}
            move_bridge.handle(attack)
            move_bridge.handle({"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
                                "status_ptr": "0x22", "status_actor_id": 60050,
                                "hp_before": 30 - index * 10, "hp_max": 30,
                                "requested_hp": 20 - index * 10})
            effect = move_bridge.current["events"][-1]
            assert (effect["moveId"], effect["moveName"], effect["damageClass"]) == (
                f"0x{row['packedId']:08X}", row["name"], expected_class)
            assert effect["moveNameProvenance"] == "live-effect-descriptor/exact-English-t_skill"
            assert effect["damageClassProvenance"]
            assert effect["rawEffectId"] == effect["moveId"]
            assert effect["rawEffectCode"] == row["rawParam30"]
            if index == 0:
                descriptor[0x30] = 0xF  # Same ID but wrong parameter: reject.
                assert lookup_live_move(dict(attack, effect_descriptor_100=descriptor.hex()),
                                        move_bridge.skill_lookup) is None
        # Source-owner mismatch must not apply a party member's move to another actor.
        assert lookup_live_move(dict(attack, source_actor_id=5),
                                move_bridge.skill_lookup) is None
        unknown_descriptor = bytearray(0x100)
        struct.pack_into("<I", unknown_descriptor, 0, 0xEA7E03E8)
        struct.pack_into("<I", unknown_descriptor, 0x30, 0xC)
        unknown_bridge = LiveBridge(root / "unknown_skill", "unknown.jsonl",
                                    skill_rows=skill_rows)
        unknown_bridge.start({"at": at})
        unknown_bridge.handle(dict(attack, source_actor_id=60030, target_actor_id=2,
                                   source_status_ptr="0x33", target_status_ptr="0x44",
                                   candidate_result_flags=0x42000,
                                   effect_descriptor_100=unknown_descriptor.hex()))
        unknown_bridge.handle({"at": at, "kind": "hit", "name": "HpSet", "tid": 1,
                               "status_ptr": "0x44", "status_actor_id": 2,
                               "hp_before": 20, "hp_max": 20, "requested_hp": 10})
        unknown_effect = unknown_bridge.current["events"][0]
        assert unknown_effect["moveId"] is None and unknown_effect["moveName"] is None
        assert unknown_effect["rawEffectId"] == "0xEA7E03E8"
        assert unknown_effect["rawEffectCode"] == 0xC
        class FakeEnemyAI:
            def skill_names(self, unit_key):
                assert unit_key == "mon-synthetic"
                return {1000: ["Snow Breath"]}

        enemy_bridge = LiveBridge(root / "enemy_move", "enemy.jsonl",
                                  table_rows=[enemy_row], enemy_ai_index=FakeEnemyAI())
        enemy_bridge.start({"at": at})
        enemy_attack = dict(attack, source_actor_id=60050, target_actor_id=2,
                            source_status_ptr="0x22", target_status_ptr="0x44",
                            source_status_256=status[:256].hex(),
                            effect_descriptor_100=unknown_descriptor.hex())
        struct.pack_into("<I", unknown_descriptor, 0, (60050 << 16) | 1000)
        enemy_attack["effect_descriptor_100"] = unknown_descriptor.hex()
        enemy_bridge.observe_identity(enemy_attack)
        enemy_move = enemy_bridge.lookup_enemy_move(
            enemy_attack, observed_effect_descriptor(enemy_attack))
        assert enemy_move["name"] == "? Snow Breath"
        assert enemy_move["rawParam30"] == 0xC
        assert "provisional" in enemy_move["provenance"]
        enemy_attack["source_actor_id"] = 60051
        assert enemy_bridge.lookup_enemy_move(
            enemy_attack, observed_effect_descriptor(enemy_attack)) is None
        reset_marker = root / "retry.reset.json"
        retry_bridge = LiveBridge(root / "retry_encounters", "retry.jsonl",
                                  reset_path=reset_marker)
        retry_bridge.handle({"at": "2026-09-28T10:00:00.000-05:00",
                             "kind": "hit", "name": "BattleInit"})
        original_id = retry_bridge.current["id"]
        retry_bridge.handle({"at": "2026-09-28T10:00:10.000-05:00",
                             "kind": "hit", "name": "BattleEnd"})
        retry_bridge.handle({"at": "2026-09-28T10:00:20.000-05:00",
                             "kind": "hit", "name": "AttackEffectCall", "tid": 1})
        assert retry_bridge.current is None and not reset_marker.exists()
        for actor_id in range(4):
            retry_bridge.handle({"at": f"2026-09-28T10:00:20.00{actor_id}-05:00",
                                 "kind": "hit", "name": "HpSet", "status_actor_id": actor_id,
                                 "status_ptr": f"0x{actor_id + 1:x}", "hp_before": 50,
                                 "hp_max": 100, "requested_hp": 0})
            assert reset_marker.exists() == (actor_id == 3)
        assert retry_bridge.current is None
        assert json.loads(reset_marker.read_text(encoding="utf-8"))["reason"] == (
            "party_status_reset_outside_battle")
        retry_bridge.handle({"at": "2026-09-28T10:00:30.000-05:00",
                             "kind": "hit", "name": "BattleInit"})
        assert retry_bridge.current["id"] != original_id
        assert len(list((root / "retry_encounters").glob("*.json"))) == 2
        wipe_bridge = LiveBridge(root / "wipe_encounters", "walter-retry.jsonl")
        wipe_bridge.handle({"at": "2026-09-28T16:00:00.000-05:00",
                            "kind": "hit", "name": "BattleInit"})
        first_attempt_id = wipe_bridge.current["id"]
        for actor_id in range(4):
            wipe_bridge.handle({"at": f"2026-09-28T16:00:10.00{actor_id}-05:00",
                                "kind": "hit", "name": "HpSet", "tid": 1,
                                "status_actor_id": actor_id,
                                "status_ptr": f"0x{actor_id + 1:x}",
                                "hp_before": 50, "hp_max": 100,
                                "requested_hp": -1})
        assert wipe_bridge.pending_wipe is not None
        # Retry restores status directly; the next setter reads a member full.
        wipe_bridge.handle({"at": "2026-09-28T16:01:22.000-05:00",
                            "kind": "hit", "name": "HpSet", "tid": 1,
                            "status_actor_id": 3, "status_ptr": "0x4",
                            "hp_before": 100, "hp_max": 100, "requested_hp": 120})
        assert wipe_bridge.current["id"] != first_attempt_id
        assert wipe_bridge.encounter_index == 2
        attempts = [json.loads(path.read_text(encoding="utf-8"))
                    for path in (root / "wipe_encounters").glob("*.json")]
        assert sorted(attempt["outcome"] for attempt in attempts) == ["Defeat", "InProgress"]
        assert any("Retry entry inferred" in issue for issue in wipe_bridge.current["issues"])
        staggered_bridge = LiveBridge(root / "staggered_retry", "staggered.jsonl")
        staggered_bridge.handle({"at": "2026-09-28T16:00:00.000-05:00",
                                 "kind": "hit", "name": "BattleInit"})
        staggered_id = staggered_bridge.current["id"]
        for actor_id in range(4):
            staggered_bridge.handle({"at": f"2026-09-28T16:0{actor_id + 1}:00.000-05:00",
                                     "kind": "hit", "name": "HpSet", "tid": 1,
                                     "status_actor_id": actor_id,
                                     "status_ptr": f"0x{actor_id + 1:x}",
                                     "hp_before": 50, "hp_max": 100,
                                     "requested_hp": -1})
        assert staggered_bridge.pending_wipe is not None
        staggered_bridge.handle({"at": "2026-09-28T16:06:00.000-05:00",
                                 "kind": "hit", "name": "HpSet", "tid": 1,
                                 "status_actor_id": 0, "status_ptr": "0x1",
                                 "hp_before": 100, "hp_max": 100,
                                 "requested_hp": 90})
        assert staggered_bridge.current["id"] != staggered_id
        assert staggered_bridge.current["outcome"] == "InProgress"
        revive_bridge = LiveBridge(root / "revive_encounters", "revive.jsonl")
        revive_bridge.handle({"at": "2026-09-28T16:00:00.000-05:00",
                              "kind": "hit", "name": "BattleInit"})
        revived_fight_id = revive_bridge.current["id"]
        for actor_id in range(4):
            revive_bridge.handle({"at": f"2026-09-28T16:00:10.00{actor_id}-05:00",
                                  "kind": "hit", "name": "HpSet", "tid": 1,
                                  "status_actor_id": actor_id,
                                  "status_ptr": f"0x{actor_id + 1:x}",
                                  "hp_before": 50, "hp_max": 100,
                                  "requested_hp": -1})
        revive_bridge.handle({"at": "2026-09-28T16:00:11.000-05:00",
                              "kind": "hit", "name": "HpSet", "tid": 1,
                              "status_actor_id": 0, "status_ptr": "0x1",
                              "hp_before": 0, "hp_max": 100, "requested_hp": 50})
        assert revive_bridge.pending_wipe is None
        revive_bridge.handle({"at": "2026-09-28T16:01:22.000-05:00",
                              "kind": "hit", "name": "HpSet", "tid": 1,
                              "status_actor_id": 3, "status_ptr": "0x4",
                              "hp_before": 100, "hp_max": 100, "requested_hp": 120})
        assert revive_bridge.current["id"] == revived_fight_id
    print("Synthetic live bridge scope, pairing, knockout, and persistence checks passed.")


if __name__ == "__main__":
    main()
