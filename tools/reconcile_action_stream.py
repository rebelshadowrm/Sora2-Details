"""Replay raw action research into a lossless, deliberately partial evidence ledger.

No game attachment or meter writes. Queue links and dispatch runs are candidates,
not a claim that the observed routes cover every executed action.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import struct
import uuid
from action_stream_snapshots import accepted_launch_owner
from action_stream_timeline import project_timeline
from item_action_lookup import ItemActionLookup, corroborate_original_item_id, PAYLOAD_SHA256 as ITEM_PAYLOAD_SHA256
from condition_table_index import read_rows as read_conditions, PAYLOAD_SHA256 as CONDITION_PAYLOAD_SHA256
from name_table_index import read_rows as read_name_rows, unique_id_lookup, PAYLOAD_SHA256 as NAME_PAYLOAD_SHA256

from skill_table_index import (PAYLOAD_OFFSET, PAYLOAD_SHA256, ROW_SIZE,
                              ROW_START, read_rows)

EXE_SHA256 = "d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf"
HOOKS = {"DescriptorStoreSite": 0x68E20, "DescriptorResumeSite": 0x69111,
         "ActionSetupEntry": 0x68F80,
         "AnimationLaunchEntry": 0x215320, "AnimationLaunchAccepted": 0x21558F,
         "ResourceSetEntry": 0xF8DB0,
         "ActorStateDispatchCall": 0x7A68B,
         "EffectDispatchEntry": 0xDBE40, "ConditionReturnSite": 0xDE962,
         "ConditionRequestEntry": 0x7F750, "ConditionInsertReturnSite": 0x7FD63,
         "ConditionRemoveEntry": 0x80730, "ConditionRemoveReturnSite": 0x80780,
         "ConditionRequestReturnSite": 0x7FDE7}
RANGES = ((0, 8), (0x10, 0x18), (0x20, 0x90))
EXIT_OUTCOME_CANDIDATES = {
    1: ('Victory', 'player-confirmed-victory/063063bef9fb42528ffa998b5eae3a70'),
    3: ('Escape', 'player-confirmed-Wild-Rage-II-then-escape/5423e162d9bf4f9caa0a27e5d75b41de')}


def raw_bytes(value):
    try:
        return bytes.fromhex(value) if isinstance(value, str) else b""
    except ValueError:
        return b""


def pointer(value):
    try:
        number = int(value, 0) if isinstance(value, str) else int(value or 0)
        return hex(number) if number > 0 else None
    except (TypeError, ValueError):
        return None


class DescriptorLookup:
    def __init__(self, pac):
        rows = read_rows(pac)  # Validates the exact localized payload first.
        with pac.open("rb") as stream:
            stream.seek(PAYLOAD_OFFSET + ROW_START)
            data = stream.read(len(rows) * ROW_SIZE)
        self.rows = [(row, data[i * ROW_SIZE:(i + 1) * ROW_SIZE])
                     for i, row in enumerate(rows)]
        self.items = ItemActionLookup(pac)
        self.conditions = read_conditions(pac)

    def describe_animation(self, raw):
        data = raw_bytes(raw)
        if len(data) != 0x100 or b'\0' not in data:
            return None
        try:
            animation = data.split(b'\0', 1)[0].decode('utf-8')
        except UnicodeDecodeError:
            return None
        matches = [row for row, _ in self.rows if animation and row['animation'] == animation]
        return dict(animationLabel=animation, candidateRows=[r['row'] for r in matches],
            nameCandidate=matches[0]['name'] if len(matches) == 1 else None,
            lookupState='unique-animation-candidate' if len(matches) == 1 else 'ambiguous' if matches else 'unknown',
            tablePayloadSha256=PAYLOAD_SHA256,
            provenance='inline-accepted-animation/exact-English-skill-animation-label',
            meaning='animation-name-candidate; not-an-exact-SkillParam-or-runtime-unit-key-join')

    def describe(self, raw):
        result = describe(raw)
        data = raw_bytes(raw)
        matches = [row for row, candidate in self.rows if len(data) == ROW_SIZE
                   and all(data[a:b] == candidate[a:b] for a, b in RANGES)]
        items = self.items.match(data) if getattr(self, 'items', None) else []
        count = len(matches) + len(items)
        result.update(candidateRows=[row["row"] for row in matches],
                      itemCandidateRows=[row['row'] for row in items],
                      lookupState="unique-candidate" if count == 1 else
                      "ambiguous" if count else "unknown")
        if count == 1:
            row = (matches or items)[0]
            result['nameCandidate'] = row['name']
            result['lookupNamespace'] = 'GeneratedItemAction' if items else 'SkillTable'
            if items:
                result.update(itemIdCandidate=row['itemId'], itemTableRow=row['row'],
                    itemIdentityProvenance='inline-B0/native-23E760-generated-descriptor/exact-English-item-table-candidate',
                    itemTablePayloadSha256=ITEM_PAYLOAD_SHA256)
        return result


def describe(raw):
    data = raw_bytes(raw)
    return {"rawPackedId": f"0x{struct.unpack_from('<I', data)[0]:08X}"
            if len(data) >= 4 else None, "inlineRaw": raw,
            "nameCandidate": None, "lookupState": "not-requested"}


def status_identity_candidate(raw, status_pointer, party_names):
    data = raw_bytes(raw)
    status_id = struct.unpack_from('<I', data)[0] if len(data) >= 4 else None
    row = (party_names or {}).get(status_id) if len(data) == 0x2A0 and status_id is not None and status_id < 60000 else None
    return {'statusPointer': pointer(status_pointer), 'rawStatusId': status_id,
            'nameCandidate': row.get('name') if row else None,
            'provenance': 'inline-status/exact-English-name-table-candidate' if row else 'inline-status; name-unresolved'}


def condition_summary(record, previous=None, lookup=None):
    count = record.get("condition_vector_count_raw")
    data = raw_bytes(record.get("condition_vector_raw"))
    complete = (isinstance(count, int) and not isinstance(count, bool)
                and 0 <= count <= 16 and len(data) == count * 0x48
                and not record.get("condition_vector_invalid")
                and not record.get("condition_vector_truncated"))
    rows = [{"rawKey": struct.unpack_from('<I', data, offset)[0],
             "inlineRaw": data[offset:offset + 0x48].hex()}
            for offset in range(0, len(data) - 0x47, 0x48)]
    for row in rows:
        metadata = (getattr(lookup, 'conditions', None) or {}).get(row['rawKey'])
        row.update(metadata or {'nameCandidate': None, 'lookupState': 'unknown'})
        if metadata:
            row['lookupState'] = 'unique-candidate'
    result = {"collectionComplete": complete, "records": rows,
              "returnedRecordIndex": None, "returnedRawKey": None,
              "changesSincePreviousSnapshot": None,
              "comparisonMeaning": "raw-observed-differences-between-snapshots; not-stat-deltas-or-call-attribution"}
    start = pointer(record.get("condition_vector_ptr"))
    returned = pointer(record.get("condition_return_rax_ptr"))
    returned_data = raw_bytes(record.get("condition_return_rax_raw"))
    if start and returned and len(returned_data) == 0x48:
        offset = int(returned, 16) - int(start, 16)
        if 0 <= offset <= len(data) - 0x48 and offset % 0x48 == 0 and data[offset:offset + 0x48] == returned_data:
            result.update(returnedRecordIndex=offset // 0x48,
                          returnedRawKey=struct.unpack_from('<I', returned_data)[0])
    if complete and previous and previous['collectionComplete']:
        before = {row['rawKey']: row['inlineRaw'] for row in previous['records']}
        after = {row['rawKey']: row['inlineRaw'] for row in rows}
        # Duplicate raw keys do not provide a unique identity for comparison.
        if len(before) == len(previous['records']) and len(after) == len(rows):
            result['changesSincePreviousSnapshot'] = [
                {'rawKey': key, 'beforeRaw': before.get(key), 'afterRaw': after.get(key)}
                for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)]
    return result


def condition_transition_candidate(request, returned, summary):
    """Adjacent exact-route before/after evidence; never an inferred stat delta."""
    before = request.get('raw', {}) if request else {}
    after = returned['raw']
    key = after.get('condition_insert_key_raw')
    sequence = before.get('observation_sequence')
    if (before.get('name') != 'ConditionRequestEntry' or
        not isinstance(key, int) or isinstance(key, bool) or not 0 <= key <= 0xFFFFFFFF or
        not isinstance(before.get('tid'), int) or isinstance(before.get('tid'), bool) or
        not isinstance(sequence, int) or isinstance(sequence, bool) or
        after.get('observation_sequence') != sequence + 1 or
        before.get('tid') != after.get('tid') or
        not pointer(before.get('condition_manager_ptr')) or
        pointer(before.get('condition_manager_ptr')) != pointer(after.get('condition_manager_ptr')) or
        before.get('condition_r9_u32') != key or summary['returnedRawKey'] != key or
        not summary['collectionComplete']):
        return None
    pre = request.get('conditionSnapshot')
    if not pre or not pre['collectionComplete']:
        return None
    old = {r['rawKey']: r['inlineRaw'] for r in pre['records']}
    new = {r['rawKey']: r['inlineRaw'] for r in summary['records']}
    if len(old) != len(pre['records']) or len(new) != len(summary['records']):
        return None
    descriptor = raw_bytes(before.get('condition_r8_raw'))
    if (descriptor != raw_bytes(after.get('condition_insert_descriptor_raw')) or
        len(descriptor) not in (0, ROW_SIZE) or
        pointer(before.get('condition_r8_ptr')) != pointer(after.get('condition_insert_descriptor_ptr'))):
        return None
    change = 'RecordAdded' if key not in old else 'PayloadUpdated' if old[key] != new[key] else 'PayloadUnchanged'
    return dict(requestObservationId=request['observationId'], returnObservationId=returned['observationId'],
        managerPointer=pointer(after.get('condition_manager_ptr')), rawKey=key,
        beforeRaw=old.get(key), afterRaw=new[key], changeCandidate=change,
        provenance='adjacent-same-thread/native-7F750-to-7FD63/complete-collection-and-returned-record',
        meaning='observed-condition-record-transition; not-measured-stat-delta-or-complete-lifetime')


def condition_removal_route(removal, request_raw, module_base):
    """Known native zero-counter sweep vs bulk clear, with byte corroboration."""
    before = raw_bytes(removal.get('beforeRaw'))
    after = raw_bytes(removal.get('afterRaw'))
    caller = pointer(request_raw.get('condition_remove_caller_raw'))
    base = pointer(module_base)
    rva = int(caller, 16) - int(base, 16) if caller and base else None
    result = dict(callerReturnRvaRaw=hex(rva) if rva is not None and rva >= 0 else None,
                  lifecycleCandidate=None, lifecycleProvenance=None)
    if len(before) == 0x48:
        result.update(remainingCounterBeforeRaw=struct.unpack_from('<I', before, 0x2C)[0],
                      initialCounterBeforeRaw=struct.unpack_from('<I', before, 0x30)[0])
    disabled = (len(before) == len(after) == 0x48 and removal.get('nativeReturnAlRaw') == 1 and
        struct.unpack_from('<I', before, 4)[0] != 0 and struct.unpack_from('<I', after, 4)[0] == 0 and
        before[:4] == after[:4] and before[8:] == after[8:])
    if disabled and rva == 0x813BE and result['remainingCounterBeforeRaw'] == 0 and before[0x45] == 0:
        result.update(lifecycleCandidate='Expired',
            lifecycleProvenance='native-813A6-zero-counter-gate/813B9-removal-call/inline-disabled-record')
    elif disabled and rva == 0xE6932:
        result.update(lifecycleCandidate='BulkClear',
            lifecycleProvenance='native-E6910-collection-clear-loop/E692D-removal-call/inline-disabled-record')
    # Cure loops pass R8B=1, so 80730 erases via 80A07 before returning.
    # Expiry/clear loops instead erase the disabled row in their caller.
    erased = (len(before) == 0x48 and removal.get('afterRaw') is None and
        removal.get('nativeReturnAlRaw') == 1 and struct.unpack_from('<I', before, 4)[0] != 0 and
        request_raw.get('condition_remove_r8b_raw') == 1)
    if (disabled or erased) and rva in (0xDF127, 0xDF207):
        result.update(lifecycleCandidate='Dispelled',
            lifecycleProvenance='native-dispatch-selector-95-or-96/cure-list-removal-call/inline-disabled-or-erased-record')
    elif (disabled or erased) and rva in (0xE8F4F, 0xE8FBF) and request_raw.get('condition_remove_r8b_raw') == 1:
        # E8E40 first requests key 53, then removes the two debuff table lists.
        # E8EE8 is a different call removing key 52; it is not a debuff cure.
        result.update(lifecycleCandidate='Dispelled', removalCauseCandidate='Overdrive',
            lifecycleProvenance='native-E8E40-key-53-success/debuff-table-list-loop/inline-disabled-or-erased-record')
    return result


def condition_rejection_context(request, summary, attempt):
    """Report protective records around a null return, without guessing its cause."""
    pre = request.get('conditionSnapshot', {})
    if (attempt.get('nativeResultCandidate') != 'NullReturn' or
        not pre.get('collectionComplete') or not summary.get('collectionComplete')):
        return None
    before = {r['rawKey']: r['inlineRaw'] for r in pre['records']}
    after = {r['rawKey']: r['inlineRaw'] for r in summary['records']}
    if (len(before) != len(pre['records']) or len(after) != len(summary['records']) or
        before != after or attempt['rawKey'] in before):
        return None
    immunity = raw_bytes(before.get(43))
    if len(immunity) != 0x48 or struct.unpack_from('<I', immunity, 4)[0] == 0:
        return None
    reflect = raw_bytes(before.get(18))
    return dict(contextCandidate='DebuffImmunityPresent', rawConditionKey=43,
        immunityRecordRaw=before[43], reflectArtsActiveCandidate=(len(reflect) == 0x48 and
            struct.unpack_from('<I', reflect, 4)[0] != 0),
        provenance='paired-native-null-return/complete-unchanged-unique-collection/active-key-43',
        meaning='protective-condition-context-observed; exact-native-rejection-branch-unobserved')


def reconcile(records, batch, lookup=None, party_names=None):
    observations, queues, runs, issues = [], [], [], []
    pending, resumed = {}, {}
    condition_snapshots = {}
    condition_remove_requests = {}
    condition_attempt_requests = {}
    launches, launch_requests, accepted_launches = [], {}, {}
    state_entries, latest_states = [], {}
    interrupt_candidates, pending_impede = [], {}
    effect_states = {}
    module_base = None
    active_run = last_dispatch = None
    last_sequence = None
    armed = verified = False
    intervals, current_interval = [], None

    def reset(reason):
        nonlocal active_run, last_dispatch, current_interval
        if current_interval and reason != 'observed-command-exit':
            current_interval['state'] = 'scope-correlation-reset'
            current_interval['unresolvedReason'] = reason
            current_interval = None
        for item in pending.values():
            item["unresolvedReason"] = reason
        pending.clear()
        resumed.clear()
        condition_snapshots.clear()
        condition_remove_requests.clear()
        condition_attempt_requests.clear()
        for item in launch_requests.values():
            item['unresolvedReason'] = reason
        launch_requests.clear()
        accepted_launches.clear()
        latest_states.clear()
        effect_states.clear()
        pending_impede.clear()
        active_run = last_dispatch = None

    for index, record in enumerate(records, 1):
        # Every input record, including unfamiliar markers/hooks, stays embedded.
        oid = f"{batch}:record:{index}"
        observation = {"observationId": oid, "raw": record,
                       "candidateActionId": None, "dispatchRunId": None,
                       "launchCandidateId": None, "stateCandidateId": None,
                       'commandIntervalCandidateId': current_interval['id'] if current_interval else None}
        observations.append(observation)
        kind = record.get("kind")
        if kind == "executable":
            reset("executable-marker")
            verified = str(record.get("sha256", "")).lower() == EXE_SHA256
            armed = False
            module_base = None
        elif kind == 'module':
            module_base = pointer(record.get('base'))
            if armed:
                reset('module-marker-inside-interval')
                armed = False
            continue
        elif kind == "armed":
            reset("new-armed-interval")
            armed = True
        elif kind != "hit":
            # Module/attach metadata before arming is harmless. All markers
            # during an interval end correlation; no links cross a capture gap.
            if armed:
                reset(f"capture-marker:{kind}")
                armed = False
            continue
        else:
            sequence = record.get("observation_sequence")
            valid_sequence = isinstance(sequence, int) and not isinstance(sequence, bool)
            if not valid_sequence or (last_sequence is not None and sequence != last_sequence + 1):
                reset("observation-sequence-gap")
                issues.append({"observationId": oid, "reason": "observation-sequence-gap"})
            last_sequence = sequence if valid_sequence else None
            name = record.get("name")
            mode_route = (name == 'BattleModeWrite' and module_base
                          and pointer(record.get('rva')) in ('0xc35ad', '0xc5753', '0xc4a5b', '0xc4a6d', '0xc4aa4')
                          and pointer(record.get('pointer_root_slot')) == hex(int(module_base, 16) + 0xC5D768)
                          and pointer(record.get('pointer_root_at_arm')) == pointer(record.get('pointer_root_now'))
                          and pointer(record.get('pointer_root_now'))
                          and pointer(record.get('pointer_offset')) == '0x2d30'
                          and pointer(record.get('address')) == hex(int(pointer(record.get('pointer_root_now')), 16) + 0x2D30)
                          and (pointer(record.get('rva')) != '0xc4aa4'
                               or (isinstance(record.get('before'), int) and isinstance(record.get('after'), int)
                                   and record['before'] & 0xFF == record['after'] & 0xFF)))
            if not armed or not verified or (not mode_route and pointer(record.get("rva")) != hex(HOOKS.get(name, 0))):
                reset("unverified-or-unwatched-route")
                observation["linkReason"] = "unverified-or-unwatched-route"
                continue
            tid = record.get("tid")
            if not isinstance(tid, int):
                reset("missing-thread")
                continue
            label = lookup.describe if lookup else describe
            if mode_route:
                before, after = record.get('before'), record.get('after')
                valid_values = all(isinstance(v, int) and not isinstance(v, bool) for v in (before, after))
                observation['stage'] = 'engine-mode-write-candidate'
                if valid_values and record.get('rva', '').lower() == '0xc35ad' and before & 0xFF == 0 and after & 0xFF == 1:
                    reset('observed-command-entry')
                    current_interval = {'id': f'{batch}:command-interval:{index}', 'startObservationId': oid,
                                        'endObservationId': None, 'state': 'open', 'outcome': 'Unknown',
                                        'boundaryEvidence': 'exact-writer-and-root-matched-byte-transition',
                                        'scope': 'UnclassifiedEngineBattle',
                                        'commandStageObservationIds': [],
                                        'initializerFlagSnapshots': [], 'rosterSnapshots': [],
                                        'liveBoundaryValidationComplete': False}
                    intervals.append(current_interval)
                    observation['commandIntervalCandidateId'] = current_interval['id']
                    observation['stage'] = 'command-entry-candidate'
                if current_interval:
                    mode_raw = raw_bytes(record.get('mode_root_2ce0_raw'))
                    if len(mode_raw) == 0x80:
                        current_interval['initializerFlagSnapshots'].append({'observationId': oid,
                            'rawFlags': struct.unpack_from('<I', mode_raw, 12)[0],
                            'meaning': 'initializer-flags-unresolved; not-command-mode'})
                    roster = record.get('mode_roster_candidates')
                    if isinstance(roster, list) and roster:
                        count = record.get('mode_roster_count_raw')
                        complete = (isinstance(count, int) and not isinstance(count, bool)
                                    and 0 <= count <= 16 and count == len(roster)
                                    and not record.get('mode_roster_truncated'))
                        actors = []
                        for candidate_index, candidate in enumerate(roster[:16]):
                            if not isinstance(candidate, dict):
                                complete = False
                                continue
                            actor = pointer(candidate.get('actor_ptr'))
                            status = pointer(candidate.get('status_ptr'))
                            data = raw_bytes(candidate.get('status_raw'))
                            actor_id = struct.unpack_from('<I', data)[0] if len(data) >= 4 else None
                            name_row = (party_names or {}).get(actor_id) if actor_id is not None and actor_id < 60000 else None
                            complete = complete and actor is not None and status is not None and len(data) == 0x2A0
                            actors.append({'actorInstanceCandidateId': current_interval['id'] + ':actor:' + (actor or f'unknown-row-{candidate_index}'),
                                'actorPointer': actor, 'statusPointer': status, 'rawStatusId': actor_id,
                                'nameCandidate': name_row.get('name') if name_row else None,
                                'statusInlineRaw': candidate.get('status_raw'),
                                'provenance': 'inline-roster-linked-status/exact-English-name-table-candidate' if name_row else 'inline-roster-linked-status; name-unresolved'})
                        current_interval['rosterSnapshots'].append({'observationId': oid,
                            'observedAt': record.get('at'), 'collectionComplete': bool(complete), 'actors': actors,
                            'timing': 'observed-at-mode-write; not-verified-pristine-entry-state'})
                if (valid_values and record.get('rva', '').lower() == '0xc5753'
                      and before & 0xFF == 1 and after & 0xFF == 0 and current_interval):
                    observation['commandIntervalCandidateId'] = current_interval['id']
                    current_interval.update(endObservationId=oid, state='entry-and-exit-observed')
                    # Exact exit route restores the function's incoming EDX
                    # into R14D immediately before this write. Names remain
                    # scoped research candidates from controlled player reports.
                    try:
                        value = record.get('r14')
                        exit_argument = int(value, 0) if isinstance(value, str) else value
                    except ValueError:
                        exit_argument = None
                    if not isinstance(exit_argument, int) or isinstance(exit_argument, bool) or not 0 <= exit_argument <= 0xFFFFFFFF:
                        exit_argument = None
                    current_interval['rawExitArgumentCandidate'] = exit_argument
                    outcome = EXIT_OUTCOME_CANDIDATES.get(exit_argument)
                    current_interval['outcomeCandidate'] = outcome[0] if outcome else None
                    current_interval['outcomeCandidateProvenance'] = outcome[1] if outcome else None
                    reset('observed-command-exit')
                    current_interval = None
                    observation['stage'] = 'command-exit-candidate'
                active_run = last_dispatch = None
                continue
            # Older Stages traces incorrectly used overwritten EBX as context.
            # Recover only a saved caller owner that exactly matches a prior
            # first handler. Derived fields never replace the embedded raw row.
            if name == 'AnimationLaunchAccepted' and not pointer(record.get('launch_actor_ptr')):
                caller = pointer(record.get('launch_caller_raw'))
                caller_rva = int(caller, 16) - int(module_base, 16) if caller and module_base else None
                recovered = accepted_launch_owner(caller_rva, raw_bytes(record.get('launch_stack_raw')))
                state = latest_states.get((tid, hex(recovered))) if recovered else None
                owner_bytes = raw_bytes(next((o['raw'].get('actor_state_owner_raw') for o in reversed(observations[:-1])
                                             if state and o['observationId'] == state['observationId']), None))
                if (state and len(owner_bytes) == 0x1000
                        and pointer(struct.unpack_from('<Q', owner_bytes, 0x328)[0]) == state['contextPointer']
                        and pointer(struct.unpack_from('<Q', owner_bytes, 0xC70)[0]) == state['descriptorPointer']):
                    derived = {'launch_actor_ptr': hex(recovered), 'launch_context_ptr': state['contextPointer'],
                               'launch_context_1d90_ptr': state['effectSourceContextPointerCandidate'],
                               'launch_actor_c70_ptr': state['descriptorPointer'],
                               'launch_actor_c70_raw': state['descriptor']['inlineRaw'],
                               'launch_owner_link_matches': True}
                    observation['derivedLaunchRecovery'] = {
                        'basis': 'verified-caller-saved-owner-and-preceding-first-handler-snapshot',
                        'stateObservationId': state['observationId'],
                        'descriptorSnapshotAtLaunch': False, 'fields': derived}
                    record = dict(record, **derived)
            if name == 'ActorStateDispatchCall':
                active_run = last_dispatch = None
                actor = pointer(record.get('actor_state_owner_ptr'))
                handler = pointer(record.get('actor_state_handler_ptr_raw'))
                item = {'stateCandidateId': f'{batch}:state:{index}',
                        'observationId': oid, 'thread': tid, 'actorPointer': actor,
                        'handlerRva': hex(int(handler, 16) - int(module_base, 16))
                        if handler and module_base else None,
                        'rawStateId': record.get('actor_state_id_rax_raw'),
                        'firstUpdateCandidate': record.get('actor_state_first_update_candidate'),
                        'descriptorPointer': pointer(record.get('actor_state_owner_c70_ptr')),
                        'descriptor': corroborate_original_item_id(label(record.get('actor_state_owner_c70_raw')),
                            record.get('actor_state_owner_c70_item_record_raw')),
                        'contextPointer': pointer(record.get('actor_state_owner_328_ptr')),
                        'effectSourceContextPointerCandidate': pointer(record.get('actor_state_context_1d90_ptr')),
                        'stage': 'actor-handler-entry-candidate', 'executionConfirmed': False}
                actor_status = raw_bytes(record.get('actor_state_linked_first_raw'))
                status_id = struct.unpack_from('<I', actor_status)[0] if len(actor_status) >= 4 else None
                item['rawLinkedStatusId'] = status_id
                name_row = (party_names or {}).get(status_id) if status_id is not None and status_id < 60000 else None
                item['actorNameCandidate'] = name_row.get('name') if name_row else None
                item['actorNameProvenance'] = 'inline-actor-linked-status/exact-English-name-table-candidate' if name_row else None
                if (current_interval and item['firstUpdateCandidate'] is True
                        and item['handlerRva'] in ('0x68320', '0x69570', '0x68f00', '0x68ff0', '0x68d40')):
                    current_interval['commandStageObservationIds'].append(oid)
                    current_interval['scope'] = 'CommandStagesObservedCandidate'
                # Pending first entry is an observation of a stored descriptor,
                # not observation of the earlier write instruction itself.
                state_key = tid, actor
                impede = pending_impede.pop(state_key, None)
                owner_raw = raw_bytes(record.get('actor_state_owner_raw'))
                post_flags = struct.unpack_from('<I', owner_raw, 0xE24)[0] if len(owner_raw) >= 0xE28 else None
                status_raw = raw_bytes(record.get('actor_state_linked_first_raw'))
                post_hp = struct.unpack_from('<i', status_raw, 12)[0] if len(status_raw) >= 16 else None
                if (impede and item['firstUpdateCandidate'] is True
                        and item['handlerRva'] == '0x67ad0'
                        and record.get('actor_state_owner_c78_ptr') is None
                        and post_flags is not None and post_flags & 0x1000
                        and impede['beforeActorFlags'] & 0x1000 == 0
                        and post_hp is not None and post_hp > 0):
                    evidence = {'interruptCandidateId': f'{batch}:interrupt:{index}',
                                'pendingActionCandidateId': impede['queue']['candidateActionId'],
                                'effectObservationId': impede['observationId'], 'postObservationId': oid,
                                'targetActorPointer': actor, 'beforeActorFlags': impede['beforeActorFlags'],
                                'afterActorFlags': post_flags, 'postHpObserved': post_hp,
                                'state': 'native-impede-route-corroborated',
                                'evidence': 'selector-47; pending-descriptor; cancel-flag-rise; pending-null; living-idle-target',
                                'directCancelCallbackObserved': False}
                    interrupt_candidates.append(evidence)
                    observation['interruptCandidateId'] = evidence['interruptCandidateId']
                    impede['queue'].update(state='pending-cleared-on-corroborated-impede-route',
                                           interruptCandidateId=evidence['interruptCandidateId'], unresolvedReason=None)
                    pending.pop(state_key, None)
                pending_ptr = pointer(record.get('actor_state_owner_c78_ptr'))
                pending_raw = record.get('actor_state_owner_c78_raw')
                if actor and item['firstUpdateCandidate'] is True:
                    if item['handlerRva'] == '0x68f00' and pending_ptr and len(raw_bytes(pending_raw)) == ROW_SIZE:
                        resumed.pop(state_key, None)
                        if state_key in pending:
                            pending.pop(state_key)['unresolvedReason'] = 'another-pending-stage-before-resume'
                        q = {'candidateActionId': f'{batch}:queue:{index}', 'thread': tid,
                             'actorPointer': actor, 'descriptorPointer': pending_ptr,
                             'descriptor': label(pending_raw), 'storeObservationId': None,
                             'pendingStageObservationId': oid, 'resumeObservationId': None,
                             'setupObservationIds': [], 'dispatchRunIds': [],
                             'state': 'pending-stage-observed', 'unresolvedReason': None}
                        queues.append(q)
                        pending[state_key] = q
                        observation['candidateActionId'] = q['candidateActionId']
                    elif item['handlerRva'] == '0x68ff0':
                        q = pending.pop(state_key, None)
                        if (q and pending_ptr == q['descriptorPointer']
                                and len(raw_bytes(pending_raw)) == ROW_SIZE
                                and pending_raw == q['descriptor']['inlineRaw']):
                            q.update(resumeObservationId=oid, state='resume-stage-observed',
                                     pairEvidence='same-thread-actor-pending-pointer-and-all-inline-bytes')
                            resumed[state_key] = q
                            observation['candidateActionId'] = q['candidateActionId']
                        elif q:
                            q['unresolvedReason'] = 'resume-stage-descriptor-mismatch-or-incomplete'
                            resumed.pop(state_key, None)
                    elif item['handlerRva'] == '0x68320':
                        q = resumed.get(state_key)
                        if (q and q['descriptorPointer'] == item['descriptorPointer']
                                and len(raw_bytes(item['descriptor']['inlineRaw'])) == ROW_SIZE
                                and q['descriptor']['inlineRaw'] == item['descriptor']['inlineRaw']):
                            q['executionHandlerObservationId'] = oid
                            item['candidateActionId'] = q['candidateActionId']
                            observation['candidateActionId'] = q['candidateActionId']
                state_entries.append(item)
                observation['stateCandidateId'] = item['stateCandidateId']
                accepted_launches.pop((tid, actor), None)
                latest_states.pop((tid, actor), None)
                effect_states.pop((tid, actor), None)
                if actor and item['firstUpdateCandidate'] is True:
                    latest_states[(tid, actor)] = item
                    if (item['handlerRva'] in ('0x68320', '0x69570', '0x68d40')
                            and item['descriptorPointer'] and len(raw_bytes(item['descriptor']['inlineRaw'])) == ROW_SIZE
                            and item['effectSourceContextPointerCandidate']):
                        effect_states[(tid, actor)] = item
            elif name in ('AnimationLaunchEntry', 'AnimationLaunchAccepted'):
                active_run = last_dispatch = None
                context = pointer(record.get('launch_context_ptr'))
                actor = pointer(record.get('launch_actor_ptr'))
                script_ptr = pointer(record.get('launch_script_ptr'))
                caller = pointer(record.get('launch_caller_raw'))
                stack = pointer(record.get('launch_entry_stack_pointer_raw'))
                key = tid, context, script_ptr, caller, stack
                valid = all(key) and len(raw_bytes(record.get('launch_script_raw'))) == 0x100
                if name == 'AnimationLaunchEntry':
                    accepted_launches.pop((tid, actor), None)
                    if key in launch_requests:
                        launch_requests.pop(key)['unresolvedReason'] = 'repeated-request-without-acceptance'
                    caller_rva = (hex(int(caller, 16) - int(module_base, 16))
                                  if caller and module_base else None)
                    item = {'launchCandidateId': f'{batch}:launch:{index}',
                            'requestObservationId': oid, 'acceptedObservationId': None,
                            'thread': tid, 'actorPointer': actor, 'contextPointer': context,
                            'effectSourceContextPointerCandidate': pointer(record.get('launch_context_1d90_ptr')),
                            'descriptorPointer': pointer(record.get('launch_actor_c70_ptr')),
                            'descriptor': label(record.get('launch_actor_c70_raw')),
                            'scriptPointer': script_ptr, 'scriptInlineRaw': record.get('launch_script_raw'),
                            'callerRva': caller_rva, 'state': 'launch-request-observed',
                            'executionConfirmed': False, 'dispatchRunIds': [],
                            'unresolvedReason': None if valid else 'incomplete-launch-request',
                            'ownerLinkMatches': record.get('launch_owner_link_matches') is True}
                    launches.append(item)
                    observation['launchCandidateId'] = item['launchCandidateId']
                    if valid:
                        launch_requests[key] = item
                else:
                    item = launch_requests.pop(key, None) if valid else None
                    state = latest_states.get((tid, actor))
                    caller_rva = hex(int(caller, 16) - int(module_base, 16)) if caller and module_base else None
                    state_match = (valid and state
                                   and {'0x68320': '0x686f1', '0x68da0': '0x68e8b',
                                        '0x68ff0': '0x69311', '0x69570': '0x69638'}.get(state['handlerRva']) == caller_rva
                                   and state['contextPointer'] == context
                                   and state['descriptorPointer'] == pointer(record.get('launch_actor_c70_ptr'))
                                   and len(raw_bytes(state['descriptor']['inlineRaw'])) == ROW_SIZE
                                   and state['descriptor']['inlineRaw'] == record.get('launch_actor_c70_raw')
                                   and state['effectSourceContextPointerCandidate'] == pointer(record.get('launch_context_1d90_ptr'))
                                   and record.get('launch_recovered_owner_matches') is not False
                                   and record.get('launch_owner_link_matches') is True)
                    if item is None and state_match:
                        item = {'launchCandidateId': f'{batch}:launch:{index}',
                                'requestObservationId': None, 'acceptedObservationId': None,
                                'thread': tid, 'actorPointer': actor, 'contextPointer': context,
                                'effectSourceContextPointerCandidate': state['effectSourceContextPointerCandidate'],
                                'descriptorPointer': state['descriptorPointer'], 'descriptor': state['descriptor'],
                                'scriptPointer': script_ptr, 'scriptInlineRaw': record.get('launch_script_raw'),
                                'callerRva': caller_rva, 'state': 'queue-call-observed',
                                'executionConfirmed': False, 'dispatchRunIds': [], 'unresolvedReason': None,
                                'ownerLinkMatches': True, 'stateCandidateId': state['stateCandidateId']}
                        item['descriptorSnapshotOrigin'] = ('preceding-first-handler; saved-launch-owner-matched'
                                                            if observation.get('derivedLaunchRecovery') else 'launch-inline')
                        launches.append(item)
                    matched = (item and item['scriptInlineRaw'] == record.get('launch_script_raw')
                               and record.get('launch_recovered_owner_matches') is not False
                               and item['actorPointer'] == actor
                               and item['descriptorPointer'] == pointer(record.get('launch_actor_c70_ptr'))
                               and item['descriptor']['inlineRaw'] == record.get('launch_actor_c70_raw'))
                    if matched:
                        if lookup and hasattr(lookup, 'describe_animation'):
                            item['animationLookupCandidate'] = lookup.describe_animation(record.get('launch_script_raw'))
                        latest_states.pop((tid, actor), None)
                        item.update(acceptedObservationId=oid, state='queue-call-observed',
                                    pairEvidence='same-thread-first-handler-context-caller-and-inline-descriptor'
                                    if item.get('stateCandidateId') else
                                    'same-thread-call-frame-context-caller-script-and-inline-descriptor')
                        observation['launchCandidateId'] = item['launchCandidateId']
                        observation['stateCandidateId'] = item.get('stateCandidateId')
                        # Eligible caller routes load the actor descriptor before
                        # launching it. Cast preparation and generic wait/damage
                        # animations are not eligible effect parents.
                        if (item['callerRva'] in ('0x686f1', '0x69311', '0x69638')
                                and item['ownerLinkMatches']
                                and record.get('launch_owner_link_matches') is True
                                and item['effectSourceContextPointerCandidate']
                                == pointer(record.get('launch_context_1d90_ptr'))):
                            accepted_launches[(tid, actor)] = item
                        else:
                            accepted_launches.pop((tid, actor), None)
                    else:
                        observation['linkReason'] = 'unmatched-launch-acceptance'
                        if item:
                            item['unresolvedReason'] = 'acceptance-inline-snapshot-mismatch'
            elif name == 'ResourceSetEntry':
                # Preserve independently. Resource/action causality must come
                # from verified setter frames, not the latest accepted launch.
                observation['stage'] = 'resource-set-entry; action-attribution-unresolved'
                active_run = last_dispatch = None
            elif name in ("DescriptorStoreSite", "DescriptorResumeSite"):
                active_run = last_dispatch = None
                actor = pointer(record.get("queue_actor_ptr"))
                prefix = "queue_store_r9" if name == "DescriptorStoreSite" else "queue_actor_c78"
                desc_ptr = pointer(record.get(prefix + "_ptr"))
                data = raw_bytes(record.get(prefix + "_raw"))
                key = (tid, actor)
                valid = actor and desc_ptr and len(data) == ROW_SIZE
                if name == "DescriptorStoreSite":
                    if key in pending:
                        pending.pop(key)["unresolvedReason"] = "another-store-before-resume"
                    resumed.pop(key, None)
                    item = {"candidateActionId": f"{batch}:queue:{index}",
                            "thread": tid, "actorPointer": actor,
                            "descriptorPointer": desc_ptr,
                            "descriptor": label(record.get(prefix + "_raw")),
                            "storeObservationId": oid, "resumeObservationId": None,
                            "setupObservationIds": [], "dispatchRunIds": [], "state": "store-observed",
                            "unresolvedReason": None if valid else "incomplete-store-snapshot"}
                    queues.append(item)
                    observation["candidateActionId"] = item["candidateActionId"]
                    if valid:
                        pending[key] = item
                else:
                    item = pending.pop(key, None)
                    if (valid and item and item["descriptorPointer"] == desc_ptr
                            and raw_bytes(item["descriptor"]["inlineRaw"]) == data):
                        item.update(resumeObservationId=oid, state="resume-observed",
                                    unresolvedReason=None,
                                    pairEvidence="same-thread-actor-pointer-descriptor-pointer-and-all-inline-bytes")
                        observation["candidateActionId"] = item["candidateActionId"]
                        resumed[key] = item
                    else:
                        if item:
                            item["unresolvedReason"] = "resume-descriptor-mismatch-or-incomplete"
                        observation["linkReason"] = "unmatched-resume"
                        resumed.pop(key, None)
            elif name == "ActionSetupEntry":
                active_run = last_dispatch = None
                observation['stage'] = 'target-setup-entry; execution-unverified'
                actor = pointer(record.get('setup_actor_ptr'))
                desc_ptr = pointer(record.get('setup_rdx_ptr'))
                data = raw_bytes(record.get('setup_rdx_raw'))
                key = tid, actor
                item = resumed.get(key) or pending.get(key)
                matched = (item and actor and desc_ptr and len(data) == ROW_SIZE
                           and item['descriptorPointer'] == desc_ptr
                           and raw_bytes(item['descriptor']['inlineRaw']) == data)
                if matched:
                    item['setupObservationIds'].append(oid)
                    observation['candidateActionId'] = item['candidateActionId']
                # A setup for another actor/descriptor ends a resumed effect
                # window; pending casts on other actors remain intact.
                for existing in list(resumed):
                    if existing[0] == tid and not (existing == key and matched):
                        del resumed[existing]
            elif name == "EffectDispatchEntry":
                observation['effectIdentityCandidates'] = {
                    'sourceContextStatus': status_identity_candidate(record.get('dispatch_rdx_first_raw'), record.get('dispatch_rdx_first_ptr'), party_names),
                    'targetContextStatus': status_identity_candidate(record.get('dispatch_rcx_first_raw'), record.get('dispatch_rcx_first_ptr'), party_names),
                    'descriptor': corroborate_original_item_id(label(record.get('dispatch_r8_raw')),
                        record.get('dispatch_r8_item_record_raw')),
                    'meaning': 'observed-effect-call-identities; not-executed-action-or-resolved-outcome'}
                data = raw_bytes(record.get("dispatch_r8_raw"))
                desc_ptr = pointer(record.get("dispatch_r8_ptr"))
                # Context identities remain raw roles. No actor name or source
                # semantics are inferred from these pointers or packed owner ID.
                signature = (tid, desc_ptr, data, pointer(record.get("dispatch_rcx_ptr")),
                             pointer(record.get("dispatch_rdx_ptr")))
                valid = desc_ptr and len(data) == ROW_SIZE and all(signature[3:])
                if not valid:
                    active_run = last_dispatch = None
                    observation["linkReason"] = "incomplete-dispatch-snapshot"
                    continue
                if record.get('dispatch_r9_u32') == 47:
                    for key, q in pending.items():
                        s = latest_states.get(key)
                        snapshot = next((o['raw'] for o in reversed(observations[:-1])
                                         if s and o['observationId'] == s['observationId']), {})
                        raw_owner = raw_bytes(snapshot.get('actor_state_owner_raw'))
                        flags = struct.unpack_from('<I', raw_owner, 0xE24)[0] if len(raw_owner) >= 0xE28 else None
                        if (s and key[0] == tid and s['effectSourceContextPointerCandidate'] == signature[3]
                                and flags is not None and flags & 0x1000 == 0
                                and pointer(snapshot.get('actor_state_owner_c78_ptr')) == q['descriptorPointer']
                                and snapshot.get('actor_state_owner_c78_raw') == q['descriptor']['inlineRaw']):
                            pending_impede[key] = {'queue': q, 'beforeActorFlags': flags, 'observationId': oid}
                if active_run is None or active_run[0] != signature:
                    run = {"dispatchRunId": f"{batch}:dispatch-run:{index}",
                           "candidateActionId": None, "descriptor": corroborate_original_item_id(label(record.get("dispatch_r8_raw")),
                               record.get('dispatch_r8_item_record_raw')),
                           "launchCandidateId": None,
                           "stateCandidateId": None,
                           "thread": tid, "rcxContextPointer": signature[3],
                           "rdxContextPointer": signature[4], "observationIds": [],
                           "conditionObservationIds": [], "rawSelectors": [],
                           "grouping": "contiguous-identical-descriptor-and-context-candidate"}
                    # Descriptor identity links only the first subsequent matching
                    # run after a resume. Unrelated dispatches close this window.
                    candidates = [q for q in resumed.values() if q["thread"] == tid
                                  and q["descriptorPointer"] == desc_ptr
                                  and raw_bytes(q["descriptor"]["inlineRaw"]) == data]
                    if len(candidates) == 1:
                        item = candidates[0]
                        run["candidateActionId"] = item["candidateActionId"]
                        item["dispatchRunIds"].append(run["dispatchRunId"])
                        item["state"] = "resume-and-effect-route-observed"
                    launch_candidates = [item for item in accepted_launches.values()
                                         if item['thread'] == tid and item['descriptorPointer'] == desc_ptr
                                         and raw_bytes(item['descriptor']['inlineRaw']) == data
                                         and item['effectSourceContextPointerCandidate'] == signature[4]]
                    if len(launch_candidates) == 1:
                        item = launch_candidates[0]
                        run['launchCandidateId'] = item['launchCandidateId']
                        item['dispatchRunIds'].append(run['dispatchRunId'])
                    state_candidates = [s for s in effect_states.values()
                                        if s['thread'] == tid and s['descriptorPointer'] == desc_ptr
                                        and raw_bytes(s['descriptor']['inlineRaw']) == data
                                        and s['effectSourceContextPointerCandidate'] == signature[4]]
                    if len(state_candidates) == 1:
                        run['stateCandidateId'] = state_candidates[0]['stateCandidateId']
                    for key in list(resumed):
                        if key[0] == tid:
                            del resumed[key]
                    runs.append(run)
                    active_run = signature, run
                run = active_run[1]
                run["observationIds"].append(oid)
                run["rawSelectors"].append(record.get("dispatch_r9_u32"))
                observation.update(dispatchRunId=run["dispatchRunId"],
                                   candidateActionId=run["candidateActionId"],
                                   stateCandidateId=run['stateCandidateId'],
                                   launchCandidateId=run['launchCandidateId'])
                last_dispatch = signature, run
            elif name in ("ConditionRequestEntry", "ConditionReturnSite", "ConditionInsertReturnSite", "ConditionRequestReturnSite",
                          "ConditionRemoveEntry", "ConditionRemoveReturnSite"):
                manager = pointer(record.get('condition_manager_ptr'))
                summary = condition_summary(record, condition_snapshots.get(manager) if manager else None, lookup)
                observation['conditionSnapshot'] = summary
                if manager:
                    condition_snapshots[manager] = summary
                if name in ('ConditionRemoveEntry', 'ConditionRemoveReturnSite'):
                    frame = pointer(record.get('condition_remove_frame_raw'))
                    signature = (tid, frame, manager)
                    observation['conditionRemoveTargetCandidate'] = status_identity_candidate(
                        record.get('condition_remove_target_status_raw'), record.get('condition_remove_target_status_ptr'), party_names)
                    if name == 'ConditionRemoveEntry':
                        remove_key = record.get('condition_remove_key_raw')
                        if frame and manager and isinstance(remove_key, int) and not isinstance(remove_key, bool) and 0 <= remove_key <= 0xFFFFFFFF:
                            condition_remove_requests[signature] = observation
                        observation['stage'] = 'condition-remove-request-observed; result-unresolved'
                        identity_route = record.get('condition_remove_identity_route')
                        if (identity_route in ('0xdf127', '0xdf207') and module_base and
                            pointer(record.get('condition_remove_caller_raw')) == hex(int(module_base, 16) + int(identity_route, 16)) and
                            pointer(record.get('condition_remove_dispatch_manager_ptr')) == manager):
                            observation['conditionIdentityCandidates'] = {
                                'sourceContextStatus': status_identity_candidate(record.get('condition_remove_source_status_raw'),
                                    record.get('condition_remove_source_status_ptr'), party_names),
                                'targetContextStatus': observation['conditionRemoveTargetCandidate'],
                                'descriptor': label(record.get('condition_remove_descriptor_raw'))}
                    else:
                        request = condition_remove_requests.pop(signature, None)
                        observation['stage'] = 'condition-remove-return-observed; cause-unresolved'
                        observation['conditionRemovalCandidate'] = None
                        if request and summary['collectionComplete'] and request['conditionSnapshot']['collectionComplete']:
                            key = request['raw'].get('condition_remove_key_raw')
                            before = [r for r in request['conditionSnapshot']['records'] if r['rawKey'] == key]
                            after = [r for r in summary['records'] if r['rawKey'] == key]
                            if len(before) <= 1 and len(after) <= 1:
                                observation['conditionRemovalCandidate'] = dict(rawKey=key,
                                    requestObservationId=request['observationId'], returnObservationId=oid,
                                    beforeRaw=before[0]['inlineRaw'] if before else None,
                                    afterRaw=after[0]['inlineRaw'] if after else None,
                                    nativeReturnAlRaw=record.get('condition_remove_return_al_raw'),
                                    provenance='same-thread-manager-original-stack-frame/native-80730-to-80780',
                                    meaning='native-removal-route-observed; expiry-dispel-and-battle-cleanup-cause-unresolved')
                                removal = observation['conditionRemovalCandidate']
                                removal.update(condition_removal_route(removal, request['raw'], module_base))
                                metadata = (getattr(lookup, 'conditions', None) or {}).get(key)
                                removal['nameCandidate'] = metadata.get('nameCandidate') if metadata else None
                                removal['conditionTablePayloadSha256'] = metadata.get('tablePayloadSha256') if metadata else None
                                if request.get('conditionIdentityCandidates'):
                                    observation['conditionIdentityCandidates'] = request['conditionIdentityCandidates']
                    active_run = last_dispatch = None
                    continue
                if name == 'ConditionRequestEntry':
                    key = record.get('condition_r9_u32')
                    frame = pointer(record.get('condition_request_frame_raw'))
                    if frame and manager:
                        condition_attempt_requests[(tid, frame, manager)] = observation
                    observation['requestedConditionCandidate'] = (getattr(lookup, 'conditions', None) or {}).get(key)
                    observation['stage'] = 'condition-request-observed; application-unresolved'
                    continue
                if name == 'ConditionRequestReturnSite':
                    observation['stage'] = 'condition-request-return-observed; rejection-cause-unresolved'
                    frame = pointer(record.get('condition_request_frame_raw'))
                    request = condition_attempt_requests.pop((tid, frame, manager), None)
                    observation['conditionAttemptCandidate'] = None
                    if (request and record.get('condition_insert_key_raw') == request['raw'].get('condition_r9_u32') and
                        pointer(record.get('condition_insert_descriptor_ptr')) == pointer(request['raw'].get('condition_r8_ptr')) and
                        raw_bytes(record.get('condition_insert_descriptor_raw')) == raw_bytes(request['raw'].get('condition_r8_raw'))):
                        observation['conditionAttemptCandidate'] = {
                            'requestObservationId': request['observationId'], 'returnObservationId': oid,
                            'rawKey': record.get('condition_insert_key_raw'),
                            'nativeReturnPointerRaw': record.get('condition_return_rax_ptr'),
                            'nativeReturnEaxRaw': record.get('condition_return_eax_raw'),
                            'provenance': 'same-thread-manager-original-stack-frame-key-full-descriptor/native-7F750-to-7FDE7',
                            'meaning': 'observed-native-return; immunity-and-other-rejection-causes-unresolved'}
                        attempt = observation['conditionAttemptCandidate']
                        metadata = (getattr(lookup, 'conditions', None) or {}).get(attempt['rawKey'])
                        attempt['nameCandidate'] = metadata.get('nameCandidate') if metadata else None
                        attempt['conditionTablePayloadSha256'] = metadata.get('tablePayloadSha256') if metadata else None
                        attempt['nativeResultCandidate'] = ('NullReturn' if
                            record.get('condition_return_rax_ptr') is None and record.get('condition_return_eax_raw') == 0
                            else 'ConditionRecordReturned' if summary['collectionComplete'] and
                            summary['returnedRawKey'] == attempt['rawKey'] else 'UnresolvedReturn')
                        attempt['rejectionContextCandidate'] = condition_rejection_context(request, summary, attempt)
                    observation['conditionIdentityCandidates'] = {
                        'sourceContextStatus': status_identity_candidate(record.get('condition_insert_source_status_raw'), record.get('condition_insert_source_status_ptr'), party_names),
                        'targetContextStatus': status_identity_candidate(record.get('condition_insert_target_status_raw'), record.get('condition_insert_target_status_ptr'), party_names),
                        'descriptor': label(record.get('condition_insert_descriptor_raw'))}
                    active_run = last_dispatch = None
                    continue
                if name == 'ConditionInsertReturnSite':
                    observation['stage'] = 'condition-insert-return-observed; action-attribution-unresolved'
                    observation['conditionIdentityCandidates'] = {
                        'sourceContextStatus': status_identity_candidate(record.get('condition_insert_source_status_raw'),
                            record.get('condition_insert_source_status_ptr'), party_names),
                        'targetContextStatus': status_identity_candidate(record.get('condition_insert_target_status_raw'),
                            record.get('condition_insert_target_status_ptr'), party_names),
                        'descriptor': label(record.get('condition_insert_descriptor_raw'))}
                    observation['conditionTransitionCandidate'] = condition_transition_candidate(
                        observations[-2] if len(observations) > 1 else None, observation, summary)
                    active_run = last_dispatch = None
                    continue
                # Nonvolatile registers on the verified post-call route must
                # agree with the dispatch descriptor AND both context pointers.
                signature = (tid, pointer(record.get("condition_return_r14_ptr")),
                             raw_bytes(record.get("condition_return_r14_raw")),
                             pointer(record.get("condition_return_r13_ptr")),
                             pointer(record.get("condition_return_rsi_ptr")))
                if last_dispatch and signature == last_dispatch[0]:
                    run = last_dispatch[1]
                    run["conditionObservationIds"].append(oid)
                    observation.update(dispatchRunId=run["dispatchRunId"],
                                       candidateActionId=run["candidateActionId"],
                                       launchCandidateId=run['launchCandidateId'])
                else:
                    observation["linkReason"] = "unmatched-condition-return"
                    active_run = last_dispatch = None
    reset("capture-ended-without-observed-resume")
    return {"schemaVersion": 1, "origin": "RawResearchLedger", "batchId": batch,
            "completeActionStream": False, "observations": observations,
            "queueCandidates": queues, "dispatchRuns": runs, "issues": issues,
            "launchCandidates": launches,
            "stateEntryCandidates": state_entries,
            "interruptCandidates": interrupt_candidates,
            'commandIntervalCandidates': intervals,
            "coverageGaps": ["No universal action execution boundary",
                             "Interrupt route corroborated only for captured impede evidence; other cancellation causes unresolved",
                             "Command battle boundaries await live field/battle contrast; resource writes are observations, not complete stat outcomes",
                             "Dispatch runs are not action counts; unmatched records remain unknown"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skill-pac", type=Path)
    args = parser.parse_args()
    if args.trace.resolve() == args.output.resolve():
        parser.error("Derived output must not overwrite the raw trace")
    raw = args.trace.read_bytes()
    records = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
    names = unique_id_lookup(read_name_rows(args.skill_pac)) if args.skill_pac else None
    result = reconcile(records, args.trace.stem, DescriptorLookup(args.skill_pac) if args.skill_pac else None, names)
    result['actionTimeline'] = project_timeline(result, names)
    result.update(tracePath=str(args.trace.resolve()), traceSha256=hashlib.sha256(raw).hexdigest(),
                  lookupProvenance={"tablePayloadSha256": PAYLOAD_SHA256,
                                    "nameTablePayloadSha256": NAME_PAYLOAD_SHA256,
                                    "conditionTablePayloadSha256": CONDITION_PAYLOAD_SHA256,
                                    "comparedRanges": [[a, b] for a, b in RANGES],
                                    "excludedRanges": [[8, 0x10], [0x18, 0x20]],
                                    "researchCandidatesOnly": True} if args.skill_pac else None)
    temporary = args.output.with_name(args.output.name + '.tmp-' + uuid.uuid4().hex)
    try:
        with temporary.open('x', encoding='utf-8') as stream:
            stream.write(json.dumps(result, indent=2) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, args.output)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({"output": str(args.output), "recordsPreserved": len(records),
                      "queueStates": dict(Counter(q["state"] for q in result["queueCandidates"])),
                      "dispatchRuns": len(result["dispatchRuns"]), "issues": len(result["issues"])}))


if __name__ == "__main__":
    main()
