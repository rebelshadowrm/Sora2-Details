"""Project bounded Sora 2 probe observations into partial live encounters.

The probe JSONL remains the raw record. This bridge writes one atomic encounter
snapshot per battle for the existing WPF history watcher. Unknown data stays
unknown; this is deliberately not a complete action log.
"""

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import struct
import time
import uuid

from match_enemy_status import match_status
from enemy_ai_skill_index import EnemyAiSkillIndex
from name_table_index import read_rows as read_name_rows, unique_id_lookup
from skill_table_index import read_rows as read_skill_rows, rows_by_packed_id
from status_name_index import read_rows


PARTY_NAMES = {0: "Estelle", 2: "Scherazard", 5: "Agate", 6: "Tita"}
PARTIAL_ISSUE = "Live partial capture: some move names, misses, support actions, status changes, and effect paths are not captured."
CLASS_PROVENANCE = "exact-result-flag/player-controlled-live-comparison"
TABLE_CLASS_PROVENANCE = "live-effect-descriptor/effect-code/player-controlled-comparison"


def damage_class_for_flags(flags):
    # 0x42000 has matched controlled ordinary physical Attacks. 0x52000
    # occurs on both confirmed Arts and a player-confirmed non-Art Estelle
    # action; it cannot classify damage without the missing move context.
    return {0x42000: "Physical"}.get(flags, "Unknown")


def damage_class_for_attack(move, flags):
    # Raw SkillParam 0xC occurs on verified ordinary Attacks, 0xE on the
    # player-confirmed physical Shatter Break, and 0xF on Arts-damage True
    # Comet and Lightning. Keep the provenance visible; other codes remain
    # unknown until independently compared.
    if move and move["rawParam30"] in (0xC, 0xE, 0xF):
        return ("Arts" if move["rawParam30"] == 0xF else "Physical",
                TABLE_CLASS_PROVENANCE)
    damage_class = damage_class_for_flags(flags)
    return (damage_class,
            CLASS_PROVENANCE if damage_class != "Unknown" else None)


def source_context_flags(attack):
    raw = attack.get("source_context_256")
    if not isinstance(raw, str):
        return None
    try:
        context = bytes.fromhex(raw)
    except ValueError:
        return None
    return struct.unpack_from("<I", context, 0x30)[0] if len(context) >= 0x34 else None


def target_status_7c(attack):
    raw = attack.get("target_status_256")
    if not isinstance(raw, str):
        return None
    try:
        status = bytes.fromhex(raw)
    except ValueError:
        return None
    return struct.unpack_from("<I", status, 0x7C)[0] if len(status) >= 0x80 else None


def observed_effect_descriptor(attack):
    """Retain the raw effect key even when no English SkillParam row matches."""
    raw = attack.get("effect_descriptor_100")
    if not raw:
        return None
    try:
        descriptor = bytes.fromhex(raw)
    except ValueError:
        return None
    if len(descriptor) < 0x34:
        return None
    return {"bytes": descriptor,
            "id": f"0x{struct.unpack_from('<I', descriptor, 0)[0]:08X}",
            "rawParam30": struct.unpack_from("<I", descriptor, 0x30)[0]}


def lookup_live_move_with_reason(attack, skill_rows_by_id):
    """Join a captured effect descriptor to one exact English SkillParam row.

    The descriptor's first word and three unchanged raw parameters matched two
    independently reported Estelle Crafts. An absent or nonmatching descriptor
    must not be turned into a guessed move name.
    """
    if not attack.get("effect_descriptor_100"):
        return None, "effect-descriptor-missing"
    observed = observed_effect_descriptor(attack)
    if observed is None:
        return None, "effect-descriptor-invalid"
    if not skill_rows_by_id:
        return None, "skill-table-unavailable"
    descriptor = observed["bytes"]
    packed_id = struct.unpack_from("<I", descriptor, 0)[0]
    candidates = skill_rows_by_id.get(packed_id, ())
    if not candidates:
        return None, "skill-id-absent"
    matches = [row for row in candidates
               if all(struct.unpack_from("<I", descriptor, offset)[0] == row[f"rawParam{offset:02x}"]
                      for offset in (0x10, 0x20, 0x30))]
    move_name_provenance = "live-effect-descriptor/exact-English-t_skill"
    if not matches:
        # The 2026-09-30 exact-build trace carries Counter's unique packed ID
        # and matching Param10/Param20, while the live Param30 is 0xC and the
        # static Counter row stores zero. The unique ID still resolves the
        # name; the returned table Param30 remains zero, so it cannot classify
        # this hit's damage.
        counter = candidates[0] if len(candidates) == 1 else None
        if (packed_id == 0xFFFF0042 and counter is not None
                and counter["name"] == "Counter"
                and counter["animation"] == "AniBtlCounterAttack"
                and struct.unpack_from("<I", descriptor, 0x10)[0] == counter["rawParam10"]
                and struct.unpack_from("<I", descriptor, 0x20)[0] == counter["rawParam20"]
                and counter["rawParam30"] == 0
                and struct.unpack_from("<I", descriptor, 0x30)[0] == 0xC):
            matches = [counter]
            move_name_provenance = (
                "live-effect-ID/exact-English-t_skill/Counter-rawParam30-variant")
        else:
            return None, "skill-parameters-mismatch"
    source_id = attack.get("source_actor_id")
    if isinstance(source_id, int) and 0 <= source_id < 1000:
        matches = [row for row in matches if row["ownerId"] in (source_id, 65535)]
        if not matches:
            return None, "skill-owner-mismatch"
    if len(matches) != 1:
        return None, "skill-row-ambiguous"
    if not matches[0]["name"]:
        return None, "skill-name-missing"
    row = matches[0]
    return ({"id": f"0x{packed_id:08X}", "name": row["name"],
             "rawParam30": row["rawParam30"],
             "provenance": move_name_provenance}, None)


def lookup_live_move(attack, skill_rows_by_id):
    return lookup_live_move_with_reason(attack, skill_rows_by_id)[0]


class LiveBridge:
    def __init__(self, store_dir, raw_trace_name, table_rows=None, name_rows=None,
                 skill_rows=None, enemy_ai_index=None, reset_path=None):
        self.store_dir = Path(store_dir)
        self.raw_trace_name = raw_trace_name
        self.encounter_index = 0
        self.current = None
        self.pending = {}
        self.changed = 0
        self.table_rows = table_rows or []
        self.enemy_names = {}
        self.enemy_lookup = {}
        self.party_lookup = unique_id_lookup(name_rows) if name_rows is not None else {}
        self.skill_lookup = rows_by_packed_id(skill_rows) if skill_rows is not None else {}
        self.enemy_ai_index = enemy_ai_index
        self.reset_path = Path(reset_path) if reset_path is not None else None
        self.reset_window_at = None
        self.reset_actors = set()
        self.last_reset_at = None
        self.last_end_at = None
        self.knocked_out_party = set()
        self.pending_wipe = None
        self.observed_party_hp = {}

    def lookup_enemy_move_with_reason(self, attack, raw_effect):
        """Use a uniquely matched enemy unit key to select its own AI script."""
        if raw_effect is None:
            return None, ("effect-descriptor-missing" if not attack.get("effect_descriptor_100")
                          else "effect-descriptor-invalid")
        if self.enemy_ai_index is None:
            return None, "enemy-ai-index-unavailable"
        source_id = attack.get("source_actor_id")
        source_ptr = attack.get("source_status_ptr")
        if not isinstance(source_id, int) or source_id < 60000:
            return None, "enemy-source-id-missing"
        if not source_ptr:
            return None, "enemy-source-pointer-missing"
        packed_id = int(raw_effect["id"], 16)
        if packed_id >> 16 != source_id:
            return None, "effect-owner-mismatch"
        matched_enemy = self.enemy_names.get(source_ptr)
        if not matched_enemy:
            status = self.enemy_lookup.get(source_ptr, {}).get("status", "unobserved")
            return None, f"enemy-unit-key-{status}"
        if matched_enemy["numericId"] != source_id:
            return None, "enemy-status-id-mismatch"
        names = self.enemy_ai_index.skill_names(matched_enemy["unitId"]).get(packed_id & 0xFFFF, [])
        if not names:
            return None, "enemy-ai-skill-id-absent"
        if len(names) != 1:
            return None, "enemy-ai-skill-id-ambiguous"
        return ({"id": raw_effect["id"], "name": f"? {names[0]}",
                 "rawParam30": raw_effect["rawParam30"],
                 "provenance": "live-effect-ID/provisional-stat-signature/exact-English-enemy-AI"}, None)

    def lookup_enemy_move(self, attack, raw_effect):
        return self.lookup_enemy_move_with_reason(attack, raw_effect)[0]

    @staticmethod
    def actor_key(pointer):
        if not pointer or pointer == "0x0":
            return None
        return "status-" + pointer.lower().removeprefix("0x")

    def actor(self, pointer, numeric_id):
        key = self.actor_key(pointer)
        if key is None or self.current is None:
            return None
        actors = self.current["actors"]
        if any(actor["id"] == key for actor in actors):
            return key
        if isinstance(numeric_id, int) and 0 <= numeric_id < 1000:
            row = self.party_lookup.get(numeric_id)
            if row and row["name"] and row["statusUnitKey"]:
                name, provenance, unit_id = (row["name"],
                                             "live-status-ID/exact-English-t_name",
                                             row["statusUnitKey"])
            elif numeric_id in PARTY_NAMES:
                name, provenance, unit_id = (PARTY_NAMES[numeric_id],
                                             "live-verified-status-ID", None)
            else:
                name, provenance, unit_id = f"Party ID {numeric_id}", "unresolved", None
                self.issue("Unverified party ID; displayed as a numeric actor.")
            team = "Party"
        elif isinstance(numeric_id, int) and numeric_id >= 60000:
            count = 1 + sum(actor["team"] == "Enemy" for actor in actors)
            match = self.enemy_names.get(pointer)
            if match and match["numericId"] != numeric_id:
                match = None
            name, team = (match["name"] if match else f"? Enemy {count} (ID {numeric_id})"), "Enemy"
            provenance = ("unique-stat-signature/exact-English-t_status"
                          if match else "unresolved")
            unit_id = match["unitId"] if match else None
        else:
            name, team = f"Actor {len(actors) + 1} (ID unknown)", "Other"
            provenance = "unresolved"
            unit_id = None
            self.issue("An actor had no verified team or name.")
        actors.append({"id": key, "name": name, "team": team,
                       "nameProvenance": provenance,
                       "runtimeStatusId": numeric_id,
                       "lookupUnitId": unit_id,
                       "nameLookupStatus": (self.enemy_lookup.get(pointer, {}).get("status", "unobserved")
                                            if team == "Enemy" else None),
                       "nameLookupCandidateCount": (self.enemy_lookup.get(pointer, {}).get("candidateCount")
                                                    if team == "Enemy" else None),
                       "nameLookupSignature": (self.enemy_lookup.get(pointer, {}).get("signature")
                                               if team == "Enemy" else None),
                       "nameLookupCandidates": (self.enemy_lookup.get(pointer, {}).get("candidates")
                                                if team == "Enemy" else None)})
        return key

    def observe_enemy_status(self, pointer, raw, expected_id):
        if not pointer or not raw or not self.table_rows:
            return False
        try:
            status_bytes = bytes.fromhex(raw)
            numeric_id = int.from_bytes(status_bytes[:4], "little")
            if numeric_id < 60000:
                return False
            if expected_id is not None and numeric_id != expected_id:
                self.issue(f"Enemy lookup ID mismatch: observed {numeric_id}, context {expected_id}.")
                return False
            signature, candidates = match_status(status_bytes, self.table_rows)
        except (TypeError, ValueError):
            self.issue("An enemy status snapshot could not be decoded for lookup.")
            return False
        previous = self.enemy_names.get(pointer)
        if previous and previous["numericId"] != numeric_id:
            self.issue(f"Enemy status pointer reused for ID {numeric_id}; old name discarded.")
            self.enemy_names.pop(pointer, None)
            previous = None
        if len(candidates) == 1:
            row = candidates[0]
            if previous and previous["unitId"] != row["unitId"]:
                self.issue(f"Enemy lookup conflict for ID {numeric_id}; name left unresolved.")
                self.enemy_names.pop(pointer, None)
                status = "conflict"
            else:
                self.enemy_names[pointer] = {"name": row["name"], "unitId": row["unitId"],
                                             "numericId": numeric_id}
                status = "matched"
                self.issue("Enemy names from unique exact stat signatures are provisional metadata.")
        else:
            status = "ambiguous" if candidates else "missing"
            if previous:
                # Buffs can alter a later stat signature; retain an earlier exact match.
                status = "matched-earlier"
            else:
                self.issue(f"Enemy lookup {status} for ID {numeric_id} ({len(candidates)} candidate rows).")
        candidate_labels = [{"unitId": row["unitId"], "name": row["name"]}
                            for row in candidates]
        signature_fields = dict(zip(("level", "exp", "ep", "def", "adf", "mov"),
                                    signature))
        self.enemy_lookup[pointer] = {"status": status, "candidateCount": len(candidates),
                                      "signature": signature_fields,
                                      "candidates": candidate_labels}
        key = self.actor_key(pointer)
        changed = False
        for actor_index, actor in enumerate(self.current["actors"]):
            if actor["id"] != key or actor["team"] != "Enemy" or actor["runtimeStatusId"] != numeric_id:
                continue
            match = self.enemy_names.get(pointer)
            ordinal = sum(a["team"] == "Enemy" for a in self.current["actors"][:actor_index + 1])
            name = match["name"] if match else f"? Enemy {ordinal} (ID {numeric_id})"
            fields = {"name": name,
                      "nameProvenance": ("unique-stat-signature/exact-English-t_status"
                                         if match else "unresolved"),
                      "lookupUnitId": match["unitId"] if match else None,
                      "nameLookupStatus": status,
                      "nameLookupCandidateCount": len(candidates),
                      "nameLookupSignature": signature_fields,
                      "nameLookupCandidates": candidate_labels}
            for field, value in fields.items():
                if actor.get(field) != value:
                    actor[field] = value
                    changed = True
        return changed

    def observe_identity(self, record):
        if self.current is None:
            return
        changed = False
        observed = set()
        for role in ("source", "target"):
            pointer = record.get(f"{role}_status_ptr")
            raw = record.get(f"{role}_status_256")
            if pointer and raw:
                changed |= self.observe_enemy_status(pointer, raw, record.get(f"{role}_actor_id"))
                observed.add(pointer)
        for snapshot in record.get("identity_snapshots", []):
            pointer = snapshot.get("status_ptr")
            if pointer not in observed:
                role = snapshot.get("role")
                changed |= self.observe_enemy_status(pointer, snapshot.get("status_2a0"),
                                                     record.get(f"{role}_actor_id"))
        if changed:
            self.save()

    def issue(self, reason):
        if self.current is not None and reason not in self.current["issues"]:
            self.current["issues"].append(reason)

    def save(self):
        if self.current is None:
            return
        self.store_dir.mkdir(parents=True, exist_ok=True)
        filename = hashlib.sha256(self.current["id"].encode()).hexdigest().upper() + ".json"
        target = self.store_dir / filename
        temporary = self.store_dir / (filename + "." + uuid.uuid4().hex + ".tmp")
        try:
            temporary.write_text(json.dumps(self.current, indent=2) + "\n", encoding="utf-8")
            for attempt in range(5):
                try:
                    os.replace(temporary, target)
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(0.025 * (attempt + 1))
        finally:
            temporary.unlink(missing_ok=True)
        self.changed += 1

    def start(self, record, issue=None):
        if self.current is not None:
            if self.pending_wipe is not None:
                self.issue("A full-party knockout preceded the next battle entry; defeat is inferred.")
                self.current["outcome"] = "Defeat"
                self.current["label"] = (
                    f"Command battle {datetime.fromisoformat(self.current['startedAt']):%H:%M:%S} · defeat (inferred)")
            else:
                self.issue("Another BattleInit arrived before an end; prior encounter interrupted.")
                self.current["outcome"] = "Interrupted"
                self.current["label"] += " · interrupted"
            self.save()
        self.pending.clear()
        self.knocked_out_party.clear()
        self.pending_wipe = None
        self.observed_party_hp.clear()
        self.reset_actors.clear()
        self.reset_window_at = None
        self.enemy_names.clear()
        self.enemy_lookup.clear()
        stamp = record["at"]
        self.encounter_index += 1
        stable_id = uuid.uuid5(uuid.NAMESPACE_URL,
                               f"sora2-details:{self.raw_trace_name}:{self.encounter_index}")
        self.current = {
            "id": "live-" + stable_id.hex,
            "label": f"Command battle {datetime.fromisoformat(stamp):%H:%M:%S} · in progress",
            "startedAt": stamp,
            "outcome": "InProgress",
            "isComplete": False,
            "actors": [], "events": [],
            "issues": [PARTIAL_ISSUE, f"Raw trace: {self.raw_trace_name}"] +
                      ([issue] if issue else []),
        }
        self.save()

    def end(self, record):
        if self.current is None:
            return
        if self.pending:
            self.issue(f"{len(self.pending)} attack call(s) had no paired HP write at battle end.")
            self.pending.clear()
        self.issue("BattleEnd callback observed; victory, Escape, and defeat are not yet decoded.")
        self.current["outcome"] = "Unknown"
        self.current["label"] = (
            f"Command battle {datetime.fromisoformat(self.current['startedAt']):%H:%M:%S} · result unknown")
        self.save()
        self.current = None
        self.last_end_at = datetime.fromisoformat(record["at"])

    def interrupt(self, reason):
        if self.current is None:
            return
        self.issue(reason)
        self.current["outcome"] = "Interrupted"
        self.current["label"] = (
            f"Command battle {datetime.fromisoformat(self.current['startedAt']):%H:%M:%S} · interrupted")
        self.save()
        self.current = None
        self.pending.clear()

    def infer_retry(self, record, evidence):
        self.issue(f"Full-party knockout followed by {evidence}; Retry boundary inferred. Result and exact entry time remain unverified.")
        self.current["outcome"] = "Defeat"
        self.current["label"] = (
            f"Command battle {datetime.fromisoformat(self.current['startedAt']):%H:%M:%S} · defeat (inferred)")
        self.save()
        self.current = None
        self.start(record, f"Retry entry inferred from a full-party knockout and {evidence}; opening events during the gap may be missing.")

    def observe_retry_attack(self, record):
        """A party member last seen at zero HP cannot attack in that attempt."""
        actor_id = record.get("source_actor_id")
        pointer = record.get("source_status_ptr")
        if (self.pending_wipe is None or actor_id not in self.knocked_out_party or
                not pointer or self.observed_party_hp.get(pointer) != 0 or
                (datetime.fromisoformat(record["at"]) - self.pending_wipe).total_seconds() < 2):
            return False
        self.infer_retry(record, "a party attack from a member last observed at zero HP")
        return True

    def observe_party_hp(self, record):
        """Recognize a retry after a four-member wipe and direct HP reset.

        Walter's Retry bypassed both lifecycle hooks and restored party status
        without an HP-setter call. The first later setter may already see a
        damaged party member, rather than full HP. A normal revive passes
        through the setter with hp_before=0 and stays in this encounter.
        """
        actor_id = record.get("status_actor_id")
        pointer = record.get("status_ptr")
        before = record.get("hp_before")
        maximum = record.get("hp_max")
        requested = record.get("requested_hp")
        if not (isinstance(actor_id, int) and actor_id in range(8) and pointer and
                all(isinstance(value, int) for value in (before, maximum, requested)) and
                maximum > 0):
            return False
        observed_at = datetime.fromisoformat(record["at"])
        if (self.pending_wipe is not None and
                (observed_at - self.pending_wipe).total_seconds() >= 2 and
                self.observed_party_hp.get(pointer) == 0 and 0 < before <= maximum):
            pending_attack = self.pending.get(record.get("tid"))
            if (pending_attack is not None and
                    (pending_attack.get("target_status_ptr") != pointer or
                     datetime.fromisoformat(pending_attack["at"]) <= self.pending_wipe)):
                pending_attack = None
            self.infer_retry(record, "an unwatched positive HP reset")
            if pending_attack is not None:
                self.pending[record.get("tid")] = pending_attack
                self.observe_identity(pending_attack)
            return True
        after = max(0, min(maximum, requested))
        self.observed_party_hp[pointer] = after
        if after > 0:
            # A watched revive means the command battle continued. Keep other
            # knocked-out members, whose deaths may have occurred turns earlier.
            self.knocked_out_party.discard(actor_id)
            if before == 0 and self.pending_wipe is not None:
                self.pending_wipe = None
        elif before > 0:
            self.knocked_out_party.add(actor_id)
            if len(self.knocked_out_party) >= 4 and self.pending_wipe is None:
                self.pending_wipe = observed_at
        return False

    def observe_outside_battle_hp(self, record):
        """Mark a broad party-status reset after a fight, without opening an encounter.

        Retry/load can clear party status records without calling BattleInit yet.
        A single zero HP write can also be ordinary field activity, so require
        four distinct party IDs in a one-second initialization wave.
        """
        if self.encounter_index == 0 or record.get("requested_hp") != 0:
            return
        actor_id = record.get("status_actor_id")
        before = record.get("hp_before")
        maximum = record.get("hp_max")
        if not isinstance(actor_id, int) or actor_id not in range(8) or not (
                isinstance(before, int) and before > 0 and
                isinstance(maximum, int) and maximum > 0):
            return
        observed_at = datetime.fromisoformat(record["at"])
        if self.last_end_at is None or (observed_at - self.last_end_at).total_seconds() < 2:
            return
        if self.reset_window_at is None or (observed_at - self.reset_window_at).total_seconds() > 1:
            self.reset_window_at = observed_at
            self.reset_actors.clear()
        self.reset_actors.add(actor_id)
        if len(self.reset_actors) < 4 or self.last_reset_at == self.reset_window_at:
            return
        self.last_reset_at = self.reset_window_at
        if self.reset_path is not None:
            self.reset_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.reset_path.with_name(self.reset_path.name + "." + uuid.uuid4().hex + ".tmp")
            try:
                temporary.write_text(json.dumps({"at": record["at"],
                    "reason": "party_status_reset_outside_battle"}) + "\n", encoding="utf-8")
                os.replace(temporary, self.reset_path)
            finally:
                temporary.unlink(missing_ok=True)

    def add_effect(self, record, kind, source, target, amount, before, after,
                   resolved=None, move=None, move_name=None, raw_result_flags=None,
                   raw_effect=None, raw_source_context_flags=None,
                   raw_target_status_7c=None, move_lookup_reason=None):
        if self.current is None or target is None:
            return
        events = self.current["events"]
        damage_class, provenance = (damage_class_for_attack(move, raw_result_flags)
                                    if kind == "Damage" else ("Unknown", None))
        if provenance == CLASS_PROVENANCE:
            self.issue("Physical class uses the exact result flag validated on ordinary Attacks; other patterns remain unknown.")
        elif provenance == TABLE_CLASS_PROVENANCE:
            self.issue("Effect-code damage classes are provisional matches from player-controlled comparisons.")
        events.append({
            "sequence": len(events) + 1,
            "observedAt": record["at"],
            "actionId": None,
            "sourceId": source,
            "targetId": target,
            "moveId": move["id"] if move else None,
            "moveName": move["name"] if move else move_name,
            "moveNameProvenance": move["provenance"] if move else None,
            "moveLookupReason": move_lookup_reason,
            "moveRawParam30": move["rawParam30"] if move else None,
            "rawEffectId": raw_effect["id"] if raw_effect else None,
            "rawEffectCode": raw_effect["rawParam30"] if raw_effect else None,
            "kind": kind,
            "effectiveAmount": amount,
            "hpBefore": before,
            "hpAfter": after,
            "damageClass": damage_class,
            "damageClassProvenance": provenance,
            "resolvedAmount": resolved,
            "rawResultFlags": raw_result_flags,
            "isCritical": None,
            "rawSourceContextFlags": raw_source_context_flags,
            "rawTargetStatus7C": raw_target_status_7c,
        })
        if kind in ("Damage", "HpLoss") and before is not None and before > 0 and after == 0:
            actor = next(actor for actor in self.current["actors"] if actor["id"] == target)
            if actor["team"] == "Party":
                events.append({
                    "sequence": len(events) + 1,
                    "observedAt": record["at"], "actionId": None,
                    "sourceId": source, "targetId": target,
                    "moveId": move["id"] if move else None,
                    "moveName": move["name"] if move else None,
                    "moveNameProvenance": move["provenance"] if move else None,
                    "moveLookupReason": move_lookup_reason,
                    "moveRawParam30": move["rawParam30"] if move else None,
                    "rawEffectId": raw_effect["id"] if raw_effect else None,
                    "rawEffectCode": raw_effect["rawParam30"] if raw_effect else None,
                    "kind": "Knockout", "effectiveAmount": None,
                    "hpBefore": before, "hpAfter": 0,
                    "damageClass": damage_class, "resolvedAmount": None,
                    "rawResultFlags": raw_result_flags, "isCritical": None,
                    "rawSourceContextFlags": raw_source_context_flags,
                    "rawTargetStatus7C": raw_target_status_7c,
                    "damageClassProvenance": provenance,
                })
        self.save()

    def hp_write(self, record):
        if self.current is None:
            return
        pointer = record.get("status_ptr")
        before, maximum, requested = (record.get(key) for key in
                                      ("hp_before", "hp_max", "requested_hp"))
        if not pointer or not all(isinstance(value, int) for value in
                                  (before, maximum, requested)) or maximum <= 0:
            self.issue("Unreadable HP setter observation.")
            self.save()
            return
        after = max(0, min(maximum, requested))
        target = self.actor(pointer, record.get("status_actor_id"))
        attack = self.pending.get(record.get("tid"))
        if attack is not None and attack.get("target_status_ptr") == pointer and after <= before:
            self.pending.pop(record.get("tid"), None)
            source = self.actor(attack.get("source_status_ptr"), attack.get("source_actor_id"))
            amount = attack.get("candidate_resolved_amount")
            if not isinstance(amount, int) or amount < 0 or requested >= 0 and amount != before - requested:
                self.issue("Attack amount and HP request disagreed; resolved amount left unknown.")
                amount = None
            kind = "Damage" if before > after or amount else "Unknown"
            raw_effect = observed_effect_descriptor(attack)
            move, move_lookup_reason = lookup_live_move_with_reason(attack, self.skill_lookup)
            if move is None:
                source_id = attack.get("source_actor_id")
                if isinstance(source_id, int) and source_id >= 60000:
                    move, move_lookup_reason = self.lookup_enemy_move_with_reason(attack, raw_effect)
            self.add_effect(record, kind, source, target,
                            before - after if kind == "Damage" else None,
                            before, after, resolved=amount, move=move,
                            raw_effect=raw_effect,
                            raw_result_flags=attack.get("candidate_result_flags"),
                            raw_source_context_flags=source_context_flags(attack),
                            raw_target_status_7c=target_status_7c(attack),
                            move_lookup_reason=move_lookup_reason)
            return
        if attack is not None:
            self.issue("An unrelated HP write occurred while an attack result was pending; the attack remains pending.")
        self.issue("An HP write had no verified source or move.")
        kind = "Healing" if after > before else "HpLoss" if after < before else "Unknown"
        amount = abs(after - before) if kind != "Unknown" else None
        self.add_effect(record, kind, None, target, amount, before, after,
                        move_name="Unattributed HP write",
                        move_lookup_reason="hp-write-without-attack-result")

    def handle(self, record):
        if record.get("kind") == "hit":
            name = record.get("name")
            if name == "BattleInit":
                self.start(record)
            elif name == "BattleEnd":
                self.end(record)
            elif name == "AttackEffectCall" and self.current is not None:
                self.observe_retry_attack(record)
                self.observe_identity(record)
                tid = record.get("tid")
                if tid in self.pending:
                    self.issue("An attack call was overwritten before an HP write.")
                    self.save()
                self.pending[tid] = record
            elif name == "HpSet":
                if self.current is None:
                    self.observe_outside_battle_hp(record)
                else:
                    if self.observe_party_hp(record):
                        # The direct restoration happened outside this hook.
                        if record.get("hp_before") == record.get("hp_max"):
                            return
                    self.hp_write(record)
        elif record.get("kind") == "hit_limit":
            self.issue("Probe hit limit reached; capture may have dropped later results.")
            self.save()
        elif record.get("kind") in ("detached", "detached_after_error", "target_exited"):
            self.interrupt("Probe stopped before a verified encounter end.")


def consume(trace_path, store_dir, follow=False, max_wait_seconds=3600,
            table_rows=None, name_rows=None, skill_rows=None, enemy_ai_index=None):
    trace_path = Path(trace_path)
    bridge = LiveBridge(store_dir, trace_path.name, table_rows, name_rows,
                        skill_rows, enemy_ai_index,
                        reset_path=trace_path.with_suffix(".reset.json"))
    deadline = time.monotonic() + max_wait_seconds
    while not trace_path.exists():
        if not follow or time.monotonic() >= deadline:
            raise FileNotFoundError(trace_path)
        time.sleep(0.1)
    with trace_path.open("r", encoding="utf-8") as stream:
        while True:
            line = stream.readline()
            if line:
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    bridge.interrupt("Malformed raw observation line.")
                    raise
                bridge.handle(record)
                if record.get("kind") in ("detached", "detached_after_error", "target_exited"):
                    break
            elif not follow:
                break
            elif time.monotonic() >= deadline:
                bridge.interrupt("Live bridge timed out before probe detach.")
                break
            else:
                time.sleep(0.1)
    if not follow:
        bridge.interrupt("Raw trace ended before probe detach.")
    return bridge


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--store-dir", type=Path, default=(
        Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
        / "Sora2 Details" / "encounters"))
    parser.add_argument("--follow", action="store_true")
    parser.add_argument("--table-pac", type=Path,
                        help="Exact English table_en.pac for provisional enemy-name matches")
    parser.add_argument("--script-pac", type=Path,
                        help="Exact English script_en.pac for provisional enemy AI move names")
    parser.add_argument("--max-wait-seconds", type=int, default=3600)
    args = parser.parse_args()
    table_rows = read_rows(args.table_pac) if args.table_pac else None
    name_rows = read_name_rows(args.table_pac) if args.table_pac else None
    skill_rows = read_skill_rows(args.table_pac) if args.table_pac else None
    enemy_ai_index = EnemyAiSkillIndex(args.script_pac) if args.script_pac else None
    result = consume(args.trace, args.store_dir, args.follow,
                     args.max_wait_seconds, table_rows, name_rows, skill_rows,
                     enemy_ai_index)
    print(f"Saved {result.changed} encounter snapshot(s) to {args.store_dir}")


if __name__ == "__main__":
    main()
