"""Offline command-battle scope and pairing check; does not attach to the game."""

import json
from pathlib import Path
import struct
import tempfile
import threading
import time

from live_capture_bridge import (LiveBridge, consume, damage_class_for_flags,
                                 source_context_flags, lookup_live_move,
                                 lookup_live_move_with_reason,
                                 lookup_resource_skill_with_reason,
                                 observed_effect_descriptor, read_r14_context_snapshots,
                                 target_status_7c)


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
        # Two starts, a verified end, and the interrupted next encounter each
        # produce a durable snapshot; intra-second writes may coalesce.
        assert bridge.changed >= 4
        assert len(encounters) == 2
        first = next(encounter for encounter in encounters if encounter["outcome"] == "Unknown")
        actions = [event for event in first["events"] if event["kind"] == "ActionObserved"]
        outcomes = [event for event in first["events"] if event["kind"] != "ActionObserved"]
        assert len(actions) == 2
        assert all(event["eventStage"] == "attack-effect-call" for event in actions)
        assert [event["kind"] for event in outcomes] == [
            "Damage", "Healing", "HpLoss", "Unknown", "Damage", "Knockout"]
        assert [event["effectiveAmount"] for event in outcomes] == [10, 10, 5, None, 55, None], outcomes
        assert outcomes[0]["rawResultFlags"] == 0x42000
        assert outcomes[0]["isCritical"] is None
        assert outcomes[0]["damageClass"] == "Physical"
        assert outcomes[0]["moveLookupReason"] == "effect-descriptor-missing"
        assert outcomes[1]["moveLookupReason"] == "hp-write-without-attack-result"
        assert outcomes[-1]["moveLookupReason"] == "effect-descriptor-missing"
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
        tear_id = 0xFFFF0076
        tear_params = (0x10, 0x20, 0x30)
        tear_row_bytes = bytearray(0xB0)
        struct.pack_into("<I", tear_row_bytes, 0, tear_id)
        for offset, value in zip(tear_params, (1, 2, 3)):
            struct.pack_into("<I", tear_row_bytes, offset, value)
        tear_row = {"packedId": tear_id, "ownerId": 119, "skillId": 118,
                    "name": "Tear", "rawParam10": 1, "rawParam20": 2,
                    "rawParam30": 3}
        healing = LiveBridge(root / "numeric_heal", "numeric_heal.jsonl",
                             skill_rows=[tear_row])
        module_base = 0x7FF700000000
        healing.handle({"kind": "executable",
                        "sha256": "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"})
        healing.handle({"kind": "module", "base": hex(module_base),
                        "breakpoints": {"NumericEffectCall": hex(module_base + 0xE1A67),
                                        "ResourceSetEntry": hex(module_base + 0xF8DB0)}})
        healing.handle({"at": at, "kind": "hit", "name": "BattleCommandBegin", "tid": 77})
        numeric_at = "2026-09-28T16:00:01.000-05:00"
        healing.handle({"at": numeric_at, "kind": "hit", "name": "NumericEffectCall",
                        "tid": 77, "source_status_ptr": "0x11", "source_actor_id": 119,
                        "target_status_ptr": "0x22", "target_actor_id": 5,
                        "skill_row_packed_id_candidate": tear_id,
                        "skill_row_0xb0_candidate": tear_row_bytes.hex(),
                        "result_entry_amount": 1200})
        healing.handle({"at": numeric_at, "kind": "hit", "name": "ResourceSetEntry",
                        "tid": 77, "status_ptr": "0x22", "status_actor_id": 5,
                        "property_code": 7, "value_before": 1000,
                        "maximum_before": 2000, "requested_value": 2200,
                        "caller_return_rva": "0xe4db1"})
        numeric_actions = [event for event in healing.current["events"]
                           if event["kind"] == "ActionObserved"]
        numeric_heals = [event for event in healing.current["events"]
                         if event["kind"] == "Healing"]
        assert len(numeric_actions) == 1 and numeric_actions[0]["moveName"] == "Tear"
        assert numeric_actions[0]["moveNameProvenance"] == (
            "live-NumericEffectCall-R14/exact-English-t_skill")
        assert numeric_actions[0]["candidateAmount"] == 1200
        assert len(numeric_heals) == 1
        assert numeric_heals[0]["sourceId"] == "status-11"
        assert next(actor for actor in healing.current["actors"]
                    if actor["id"] == "status-11")["runtimeStatusId"] == 119
        assert numeric_heals[0]["effectiveAmount"] == 1000
        assert numeric_heals[0]["candidateAmount"] == 1200
        assert numeric_heals[0]["actionId"] == numeric_actions[0]["actionId"]
        assert numeric_heals[0]["moveName"] == "Tear"
        for caller, amount in (("0xe4a67", 1200), ("0xe4db1", 900)):
            contrast = LiveBridge(root / f"heal_contrast_{caller}_{amount}", "contrast.jsonl", skill_rows=[tear_row])
            contrast.executable_sha256 = healing.executable_sha256
            contrast.module_base = healing.module_base
            contrast.module_breakpoints = healing.module_breakpoints
            contrast.start({"at": at})
            contrast.handle({"at": numeric_at, "kind": "hit", "name": "NumericEffectCall",
                "tid": 77, "source_status_ptr": "0x11", "source_actor_id": 119,
                "target_status_ptr": "0x22", "target_actor_id": 5,
                "skill_row_0xb0_candidate": tear_row_bytes.hex(), "result_entry_amount": amount})
            contrast.handle({"at": numeric_at, "kind": "hit", "name": "ResourceSetEntry",
                "tid": 77, "status_ptr": "0x22", "status_actor_id": 5,
                "property_code": 7, "value_before": 1000, "maximum_before": 3000,
                "requested_value": 2200, "caller_return_rva": caller})
            heal = next(event for event in contrast.current["events"] if event["kind"] == "Healing")
            assert heal["sourceId"] is None and heal["actionId"] is None
            assert heal["moveName"] == "Unattributed HP write"
        snapshot_path = root / "numeric_context_snapshot.jsonl"
        snapshot_path.write_text(
            json.dumps({"kind": "executable",
                        "sha256": "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"}) +
            "\n" + json.dumps({"kind": "context", "address": "0x99",
                               "bytes_600": (tear_row_bytes + bytearray(0x600 - 0xB0)).hex()}) +
            "\n" + json.dumps({"kind": "context", "address": "0x77",
                               "bytes_600": (bytearray(0x600)).hex()}) + "\n",
            encoding="utf-8")
        heat_up_id = 0xFFFF2721
        heat_up_bytes = bytearray(0x600)
        struct.pack_into("<I", heat_up_bytes, 0, heat_up_id)
        for offset, value in zip(tear_params, (4, 5, 6)):
            struct.pack_into("<I", heat_up_bytes, offset, value)
        snapshot_lines = snapshot_path.read_text(encoding="utf-8").splitlines()
        snapshot_lines[-1] = json.dumps({"kind": "context", "address": "0x77",
                                         "bytes_600": heat_up_bytes.hex()})
        snapshot_path.write_text("\n".join(snapshot_lines) + "\n", encoding="utf-8")
        snapshot_rows = read_r14_context_snapshots([snapshot_path])
        cross_trace = LiveBridge(root / "numeric_cross_trace", "numeric_cross_trace.jsonl",
                                 skill_rows=[tear_row], r14_context_snapshots=snapshot_rows)
        cross_trace.handle({"kind": "executable",
                            "sha256": "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"})
        cross_trace.handle({"kind": "module", "base": hex(module_base),
                            "breakpoints": {"NumericEffectCall": hex(module_base + 0xE1A67)}})
        cross_trace.start({"at": at})
        cross_trace.handle({"at": numeric_at, "kind": "hit", "name": "NumericEffectCall",
                            "tid": 77, "r14": "0x99",
                            "source_status_ptr": "0x11", "source_actor_id": 119,
                            "target_status_ptr": "0x22", "target_actor_id": 5,
                            "skill_row_packed_id_candidate": tear_id})
        cross_event = cross_trace.current["events"][0]
        assert cross_event["moveName"] is None
        assert cross_event["moveNameProvenance"] is None
        assert cross_event["moveLookupReason"] == "numeric-effect-skill-row-bytes-missing"
        assert cross_event["rawEffectId"] == "0xFFFF0076"  # Observed inline key survives.
        assert cross_event["rawEffectCode"] is None  # Never invent bytes from another trace.
        heat_up_row = {"packedId": heat_up_id, "ownerId": 65535, "skillId": 10017,
                       "name": "Heat Up II", "rawParam10": 4, "rawParam20": 5,
                       "rawParam30": 6}
        cp_bridge = LiveBridge(root / "cp_cross_trace", "cp_cross_trace.jsonl",
                               skill_rows=[heat_up_row],
                               r14_context_snapshots=snapshot_rows)
        cp_bridge.handle({"kind": "executable",
                          "sha256": "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"})
        cp_bridge.handle({"kind": "module", "base": hex(module_base),
                          "breakpoints": {"ResourceSetEntry": hex(module_base + 0xF8DB0)}})
        cp_bridge.start({"at": at})
        cp_bridge.handle({"at": numeric_at, "kind": "hit", "name": "ResourceSetEntry",
                          "tid": 77, "r14": "0x77", "status_ptr": "0x22",
                          "status_actor_id": 5, "property_code": 12,
                          "value_before": 200, "maximum_before": 200,
                          "requested_value": 40,
                          "caller_return": hex(module_base + 0xE1FAD)})
        cp_event = cp_bridge.current["events"][0]
        assert cp_event["kind"] == "ResourceChange"
        assert cp_event["moveName"] is None
        assert cp_event["moveNameProvenance"] is None
        assert cp_event["rawEffectId"] is None
        assert cp_event["moveLookupReason"] == "resource-skill-row-bytes-missing"
        assert cp_event["resourceCandidateDelta"] == 0
        assert cp_event["requestedResourceValue"] == 40
        assert cp_event["sourceId"] is None
        cp_bridge.handle({"at": numeric_at, "kind": "hit", "name": "ResourceSetEntry",
            "tid": 77, "status_ptr": "0x22", "status_actor_id": 5, "property_code": 12,
            "value_before": 100, "maximum_before": 200, "requested_value": 40,
            "caller_return_rva": "0xe1fad", "skill_row_0xb0_candidate": heat_up_bytes[:0xB0].hex()})
        assert cp_bridge.current["events"][-1]["moveName"] == "Heat Up II"
        assert cp_bridge.current["events"][-1]["resourceCandidateDelta"] == 40
        resource_trace = root / "resource_recovery.jsonl"
        resource_dir = root / "resource_recovery_encounters"
        resource_records = [
            {"kind": "executable",
             "sha256": "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF"},
            {"kind": "module", "base": hex(module_base),
             "breakpoints": {"ResourceSetEntry": hex(module_base + 0xF8DB0)}},
            {"at": at, "kind": "hit", "name": "ResourceSetEntry",
             "tid": 77, "r14": "0x77", "status_ptr": "0x22",
             "status_actor_id": 5, "property_code": 12,
             "value_before": 200, "maximum_before": 200, "requested_value": 40,
             "caller_return": hex(module_base + 0xE1FAD)},
            {"at": numeric_at, "kind": "detached"},
        ]
        resource_trace.write_text("".join(json.dumps(record) + "\n"
                                          for record in resource_records),
                                  encoding="utf-8")
        consume(resource_trace, resource_dir, skill_rows=[heat_up_row],
                r14_context_snapshots=snapshot_rows, recover_first_resource=True)
        recovered_resource = json.loads(next(resource_dir.glob("*.json")).read_text(
            encoding="utf-8"))
        assert recovered_resource["outcome"] == "Unknown"
        assert recovered_resource["events"][0]["moveName"] is None
        assert any("first resource-setter callback" in issue
                   for issue in recovered_resource["issues"])
        _, wrong_caller_reason = lookup_resource_skill_with_reason(
            {"property_code": 12, "caller_return": hex(module_base + 0xE45A7),
             "r14": "0x77"}, cp_bridge.skill_lookup, snapshot_rows,
            module_base, path_verified=True)
        assert wrong_caller_reason == "resource-skill-caller-unverified"
        unverified_numeric = LiveBridge(root / "numeric_unverified", "numeric.jsonl",
                                        skill_rows=[tear_row])
        unverified_numeric.start({"at": at})
        unverified_numeric.handle({"at": numeric_at, "kind": "hit",
                                   "name": "NumericEffectCall", "tid": 77,
                                   "source_status_ptr": "0x11", "source_actor_id": 119,
                                   "target_status_ptr": "0x22", "target_actor_id": 5,
                                   "skill_row_packed_id_candidate": tear_id,
                                   "skill_row_0xb0_candidate": tear_row_bytes.hex()})
        assert unverified_numeric.current["events"][0]["moveName"] is None
        assert unverified_numeric.current["events"][0]["rawEffectId"] == "0xFFFF0076"
        assert unverified_numeric.current["events"][0]["moveLookupReason"] == (
            "numeric-effect-callsite-unverified")
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
        interleaved_events = interleaved.current["events"]
        assert [event["kind"] for event in interleaved_events] == [
            "ActionObserved", "Healing", "Damage"]
        assert interleaved_events[1]["sourceId"] is None
        assert interleaved_events[1]["moveLookupReason"] == "hp-write-without-attack-result"
        assert interleaved_events[2]["sourceId"] == "status-11"
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
            assert effect["moveLookupReason"] is None
            if index == 0:
                descriptor[0x30] = 0xF  # Same ID but wrong parameter: reject.
                assert lookup_live_move_with_reason(
                    dict(attack, effect_descriptor_100=descriptor.hex()),
                    move_bridge.skill_lookup) == (None, "skill-parameters-mismatch")
        # Source-owner mismatch must not apply a party member's move to another actor.
        assert lookup_live_move(dict(attack, source_actor_id=5),
                                move_bridge.skill_lookup) is None
        assert lookup_live_move_with_reason(dict(attack, source_actor_id=5),
                                            move_bridge.skill_lookup)[1] == "skill-owner-mismatch"
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
        assert unknown_effect["moveLookupReason"] == "enemy-ai-index-unavailable"
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
        assert enemy_bridge.lookup_enemy_move_with_reason(
            enemy_attack, observed_effect_descriptor(enemy_attack))[1] is None
        missing_ai_attack = dict(enemy_attack)
        missing_ai_descriptor = bytearray.fromhex(enemy_attack["effect_descriptor_100"])
        struct.pack_into("<I", missing_ai_descriptor, 0, (60050 << 16) | 1001)
        missing_ai_attack["effect_descriptor_100"] = missing_ai_descriptor.hex()
        assert enemy_bridge.lookup_enemy_move_with_reason(
            missing_ai_attack, observed_effect_descriptor(missing_ai_attack))[1] == (
                "enemy-ai-skill-id-absent")
        ambiguous_enemy = LiveBridge(root / "ambiguous_enemy_move", "ambiguous.jsonl",
                                     enemy_ai_index=FakeEnemyAI())
        ambiguous_enemy.enemy_lookup["0x22"] = {"status": "ambiguous"}
        assert ambiguous_enemy.lookup_enemy_move_with_reason(
            enemy_attack, observed_effect_descriptor(enemy_attack))[1] == (
                "enemy-unit-key-ambiguous")
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
                                 "hp_before": 35, "hp_max": 100,
                                 "requested_hp": 20})
        assert staggered_bridge.current["id"] != staggered_id
        assert staggered_bridge.current["outcome"] == "InProgress"
        assert staggered_bridge.current["events"][0]["hpBefore"] == 35
        assert staggered_bridge.current["events"][0]["effectiveAmount"] == 15
        attack_retry = LiveBridge(root / "attack_retry", "attack-retry.jsonl")
        attack_retry.handle({"at": "2026-09-28T16:00:00.000-05:00",
                             "kind": "hit", "name": "BattleInit"})
        old_attempt_id = attack_retry.current["id"]
        for actor_id in range(4):
            attack_retry.handle({"at": f"2026-09-28T16:00:10.00{actor_id}-05:00",
                                 "kind": "hit", "name": "HpSet", "tid": 1,
                                 "status_actor_id": actor_id,
                                 "status_ptr": f"0x{actor_id + 1:x}",
                                 "hp_before": 50, "hp_max": 100,
                                 "requested_hp": -1})
        attack_retry.handle({"at": "2026-09-28T16:01:00.000-05:00",
                             "kind": "hit", "name": "AttackEffectCall", "tid": 1,
                             "source_actor_id": 60050, "source_status_ptr": "0x22",
                             "target_actor_id": 60051, "target_status_ptr": "0x33",
                             "candidate_resolved_amount": 10})
        assert attack_retry.current["id"] == old_attempt_id
        attack_retry.handle({"at": "2026-09-28T16:01:01.000-05:00",
                             "kind": "hit", "name": "AttackEffectCall", "tid": 1,
                             "source_actor_id": 1, "source_status_ptr": "0x2",
                             "target_actor_id": 60050, "target_status_ptr": "0x22",
                             "candidate_resolved_amount": 10})
        assert attack_retry.current["id"] != old_attempt_id
        attack_retry.handle({"at": "2026-09-28T16:01:01.001-05:00",
                             "kind": "hit", "name": "HpSet", "tid": 1,
                             "status_actor_id": 60050, "status_ptr": "0x22",
                             "hp_before": 50, "hp_max": 50,
                             "requested_hp": 40})
        attack_retry_outcomes = [event for event in attack_retry.current["events"]
                                 if event["kind"] != "ActionObserved"]
        assert [(event["kind"], event["effectiveAmount"]) for event in
                attack_retry_outcomes] == [("Damage", 10)]
        assert attack_retry.current["events"][0]["sourceId"] == "status-2"
        old_attempt = next(json.loads(path.read_text(encoding="utf-8"))
                           for path in (root / "attack_retry").glob("*.json")
                           if json.loads(path.read_text(encoding="utf-8"))["id"] == old_attempt_id)
        assert old_attempt["outcome"] == "Defeat"
        assert all(event["observedAt"] < "2026-09-28T16:01:01" for event in
                   old_attempt["events"])
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
        # Join an already-open command battle at its next command callback;
        # callbacks outside that boundary remain excluded.
        midbattle_trace = root / "midbattle.jsonl"
        midbattle_dir = root / "midbattle_encounters"
        midbattle_records = [
            {"at": "2026-09-28T16:10:00.000-05:00", "kind": "hit",
             "name": "AttackEffectCall", "tid": 1,
             "source_status_ptr": "0x11", "target_status_ptr": "0x22",
             "source_actor_id": 5, "target_actor_id": 60050,
             "candidate_resolved_amount": 99},
            {"at": "2026-09-28T16:10:01.000-05:00", "kind": "hit",
             "name": "BattleCommandBegin", "tid": 1},
            {"at": "2026-09-28T16:10:02.000-05:00", "kind": "hit",
             "name": "AttackEffectCall", "tid": 1,
             "source_status_ptr": "0x11", "target_status_ptr": "0x22",
             "source_actor_id": 5, "target_actor_id": 60050,
             "candidate_resolved_amount": 10},
            {"at": "2026-09-28T16:10:02.001-05:00", "kind": "hit",
             "name": "HpSet", "tid": 1, "status_ptr": "0x22",
             "status_actor_id": 60050, "hp_before": 20, "hp_max": 20,
             "requested_hp": 10},
            {"at": "2026-09-28T16:10:03.000-05:00", "kind": "hit",
             "name": "BattleEnd", "tid": 1},
            {"at": "2026-09-28T16:10:03.010-05:00", "kind": "hit",
             "name": "BattleEnd", "tid": 1},
            {"at": "2026-09-28T16:10:04.000-05:00", "kind": "hit",
             "name": "AttackEffectCall", "tid": 1,
             "source_status_ptr": "0x11", "target_status_ptr": "0x22",
             "source_actor_id": 5, "target_actor_id": 60050,
             "candidate_resolved_amount": 99},
            {"at": "2026-09-28T16:10:05.000-05:00", "kind": "detached"},
        ]
        midbattle_trace.write_text("".join(json.dumps(record) + "\n"
                                         for record in midbattle_records),
                                   encoding="utf-8")
        consume(midbattle_trace, midbattle_dir)
        midbattle_rows = [json.loads(path.read_text(encoding="utf-8"))
                          for path in midbattle_dir.glob("*.json")]
        assert len(midbattle_rows) == 1
        assert midbattle_rows[0]["outcome"] == "Unknown"
        assert midbattle_rows[0]["issues"][0].startswith("Live partial capture:")
        assert any("first observed command callback" in issue
                   for issue in midbattle_rows[0]["issues"])
        midbattle_outcomes = [event for event in midbattle_rows[0]["events"]
                              if event["kind"] != "ActionObserved"]
        assert [event["effectiveAmount"] for event in midbattle_outcomes] == [10]

        # Older user-confirmed traces can be explicitly recovered when they
        # contain neither battle-entry nor command callbacks.
        recovery_trace = root / "recovered.jsonl"
        recovery_dir = root / "recovered_encounters"
        recovery_records = [midbattle_records[index] for index in (2, 3, 4, 5)]
        recovery_records.append({"at": "2026-09-28T16:10:05.000-05:00",
                                 "kind": "detached"})
        recovery_trace.write_text("".join(json.dumps(record) + "\n"
                                         for record in recovery_records),
                                  encoding="utf-8")
        consume(recovery_trace, recovery_dir, recover_first_attack=True,
                player_confirmed_outcome="Victory")
        recovered_rows = [json.loads(path.read_text(encoding="utf-8"))
                          for path in recovery_dir.glob("*.json")]
        assert len(recovered_rows) == 1
        assert any("first observed attack-effect callback" in issue
                   for issue in recovered_rows[0]["issues"])
        assert recovered_rows[0]["outcome"] == "Victory"
        assert any("Victory outcome supplied by the player" in issue
                   for issue in recovered_rows[0]["issues"])
        recovered_outcomes = [event for event in recovered_rows[0]["events"]
                              if event["kind"] != "ActionObserved"]
        assert [event["effectiveAmount"] for event in recovered_outcomes] == [10]
        boundaryless = LiveBridge(root / "boundaryless", "boundaryless.jsonl")
        boundaryless.handle({"kind": "module", "base": hex(module_base),
                             "breakpoints": {"NumericEffectCall": hex(module_base + 0xE1A67)}})
        boundaryless.start({"at": at})
        boundaryless.interrupt("Probe detached.")
        assert boundaryless.current is None
        boundaryless_file = next((root / "boundaryless").glob("*.json"))
        boundaryless_row = json.loads(boundaryless_file.read_text(encoding="utf-8"))
        assert boundaryless_row["outcome"] == "Unknown"
        assert any("did not watch BattleEnd" in issue
                   for issue in boundaryless_row["issues"])
        # A lone event must become durable without waiting for another action.
        # A live JSONL append may be split; only parse completed lines.
        idle_trace = root / "idle.jsonl"
        idle_dir = root / "idle_encounters"
        idle_trace.write_text(json.dumps({"kind": "hit", "name": "BattleCommandBegin", "at": at}) + "\n")
        follower_errors = []
        def follow_idle():
            try:
                consume(idle_trace, idle_dir, follow=True, max_wait_seconds=5)
            except Exception as error:
                follower_errors.append(error)
        follower = threading.Thread(target=follow_idle)
        follower.start()
        row = json.dumps({"at": at, "kind": "hit", "name": "ResourceSetEntry", "tid": 1,
            "status_ptr": "0x11", "status_actor_id": 5, "property_code": 12,
            "value_before": 100, "maximum_before": 200, "requested_value": 40}) + "\n"
        with idle_trace.open("a") as output:
            output.write(row[:len(row)//2]); output.flush()
            time.sleep(0.15)
            output.write(row[len(row)//2:]); output.flush()
        deadline = time.monotonic() + 3
        seen = False
        while time.monotonic() < deadline:
            files = list(idle_dir.glob("*.json"))
            if files and len(json.loads(files[0].read_text())["events"]) == 1:
                seen = True; break
            time.sleep(0.025)
        with idle_trace.open("a") as output:
            output.write(json.dumps({"at": at, "kind": "detached"}) + "\n")
        follower.join(timeout=2)
        assert seen, "single resource event was not flushed during idle"
        assert not follower.is_alive() and not follower_errors, follower_errors
    print("Synthetic live bridge scope, pairing, knockout, and persistence checks passed.")


if __name__ == "__main__":
    main()
