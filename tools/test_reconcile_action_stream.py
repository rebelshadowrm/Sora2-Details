import struct
import unittest

from reconcile_action_stream import EXE_SHA256, HOOKS, DescriptorLookup, condition_summary, reconcile, condition_transition_candidate, condition_removal_route, condition_rejection_context


def descriptor(key=0xFFFF00C3):
    data = bytearray(0xB0)
    struct.pack_into('<I', data, 0, key)
    return data.hex()


def hit(name, **fields):
    return dict(kind='hit', name=name, tid=7, rva=hex(HOOKS[name]), **fields)


def store(actor='0x100', raw=None):
    return hit('DescriptorStoreSite', queue_actor_ptr=actor,
               queue_store_r9_ptr='0x200', queue_store_r9_raw=raw or descriptor())


def resume(actor='0x100', raw=None):
    return hit('DescriptorResumeSite', queue_actor_ptr=actor,
               queue_actor_c78_ptr='0x200', queue_actor_c78_raw=raw or descriptor())


def dispatch(raw=None):
    return hit('EffectDispatchEntry', dispatch_r8_ptr='0x200',
               dispatch_r8_raw=raw or descriptor(), dispatch_rcx_ptr='0x300',
               dispatch_rdx_ptr='0x400', dispatch_r9_u32=96)


def condition():
    return hit('ConditionReturnSite', condition_return_r14_ptr='0x200',
               condition_return_r14_raw=descriptor(), condition_return_r13_ptr='0x300',
               condition_return_rsi_ptr='0x400', condition_vector_raw='010203')


def launch(site, caller='0x140069311', stack='0x900', actor='0x100'):
    return hit('AnimationLaunchEntry' if site == 'request' else 'AnimationLaunchAccepted',
               launch_context_ptr='0x600', launch_actor_ptr=actor,
               launch_context_1d90_ptr='0x400', launch_script_ptr='0x700',
               launch_script_raw=('416e6942746c4172747300' + '00' * 245),
               launch_caller_raw=caller, launch_entry_stack_pointer_raw=stack,
               launch_owner_link_matches=True, launch_actor_c70_ptr='0x200',
               launch_actor_c70_raw=descriptor())


def launch_replay(*events):
    records = [dict(kind='executable', sha256=EXE_SHA256),
               dict(kind='module', base='0x140000000'), dict(kind='armed')]
    records.extend(dict(observation_sequence=i, **event) for i, event in enumerate(events, 1))
    records.append(dict(kind='disarmed'))
    return reconcile(records, 'launch-fixture')


def replay(*hits, fingerprint=EXE_SHA256):
    records = [dict(kind='executable', sha256=fingerprint), dict(kind='armed')]
    for i, event in enumerate(hits, 1):
        records.append(dict(observation_sequence=i, **event))
    records.extend([dict(kind='disarmed'), dict(kind='detached')])
    return reconcile(records, 'fixture')


class ReconcileChecks(unittest.TestCase):
    def test_animation_names_remain_separate_from_full_descriptor_lookup(self):
        lookup = DescriptorLookup.__new__(DescriptorLookup)
        lookup.rows = [(dict(row=155, name='Diamond Dust', animation='btlmagic.AniBtlArtsWater02'), b'')]
        raw = (b'btlmagic.AniBtlArtsWater02\0' + b'\0' * 256)[:256].hex()
        candidate = lookup.describe_animation(raw)
        self.assertEqual('Diamond Dust', candidate['nameCandidate'])
        self.assertIn('not-an-exact-SkillParam', candidate['meaning'])
        self.assertIsNone(lookup.describe_animation(raw[:-2]))
        self.assertIsNone(lookup.describe_animation('ff' * 256))
        lookup.rows *= 2
        self.assertEqual('ambiguous', lookup.describe_animation(raw)['lookupState'])
        self.assertIsNone(lookup.describe_animation(raw)['nameCandidate'])
    def test_null_return_context_requires_active_immunity_and_complete_unchanged_collection(self):
        immunity = bytearray(0x48)
        struct.pack_into('<II', immunity, 0, 43, 1)
        snapshot = condition_summary(dict(condition_vector_count_raw=1, condition_vector_raw=immunity.hex()))
        attempt = dict(nativeResultCandidate='NullReturn', rawKey=55)
        context = condition_rejection_context(dict(conditionSnapshot=snapshot), snapshot, attempt)
        self.assertEqual('DebuffImmunityPresent', context['contextCandidate'])
        self.assertFalse(context['reflectArtsActiveCandidate'])
        self.assertIn('branch-unobserved', context['meaning'])
        for summary in [dict(snapshot, collectionComplete=False), dict(snapshot, records=[]),
                        dict(snapshot, records=snapshot['records']*2)]:
            self.assertIsNone(condition_rejection_context(dict(conditionSnapshot=snapshot), summary, attempt))
        struct.pack_into('<I', immunity, 4, 0)
        inactive = condition_summary(dict(condition_vector_count_raw=1, condition_vector_raw=immunity.hex()))
        self.assertIsNone(condition_rejection_context(dict(conditionSnapshot=inactive), inactive, attempt))
        self.assertIsNone(condition_rejection_context(dict(conditionSnapshot=snapshot), snapshot,
            dict(attempt, nativeResultCandidate='ConditionRecordReturned')))

    def test_condition_common_return_pairs_across_insert_and_preserves_unknown_rejection(self):
        request = hit('ConditionRequestEntry', condition_manager_ptr='0x100',
            condition_request_frame_raw='0x900', condition_r9_u32=55,
            condition_r8_ptr='0x200', condition_r8_raw=descriptor())
        returned = hit('ConditionRequestReturnSite', condition_manager_ptr='0x100',
            condition_request_frame_raw='0x900', condition_insert_key_raw=55,
            condition_insert_descriptor_ptr='0x200', condition_insert_descriptor_raw=descriptor(),
            condition_return_rax_ptr=None, condition_return_eax_raw=0)
        observed = replay(request, returned)['observations'][3]
        self.assertEqual(55, observed['conditionAttemptCandidate']['rawKey'])
        self.assertEqual(0, observed['conditionAttemptCandidate']['nativeReturnEaxRaw'])
        self.assertEqual('NullReturn', observed['conditionAttemptCandidate']['nativeResultCandidate'])
        self.assertIn('rejection-causes-unresolved', observed['conditionAttemptCandidate']['meaning'])
        inserted = hit('ConditionInsertReturnSite', condition_manager_ptr='0x100')
        self.assertIsNotNone(replay(request, inserted, returned)['observations'][4]['conditionAttemptCandidate'])
        for changes in [dict(tid=8), dict(condition_request_frame_raw='0x999'),
                        dict(condition_manager_ptr='0x999'), dict(condition_insert_key_raw=1),
                        dict(condition_insert_descriptor_raw=descriptor(999))]:
            self.assertIsNone(replay(request, dict(returned, **changes))['observations'][3]['conditionAttemptCandidate'])
        gap = reconcile([dict(kind='executable', sha256=EXE_SHA256), dict(kind='armed'),
            dict(request, observation_sequence=1), dict(returned, observation_sequence=3)], 'gap')
        self.assertIsNone(gap['observations'][3]['conditionAttemptCandidate'])
        record = bytearray(0x48)
        struct.pack_into('<II', record, 0, 55, 1)
        success = dict(returned, condition_return_rax_ptr='0x300', condition_return_eax_raw=0x300,
            condition_vector_count_raw=1, condition_vector_ptr='0x300', condition_vector_raw=record.hex(),
            condition_return_rax_raw=record.hex())
        applied = replay(request, inserted, success)['observations'][4]['conditionAttemptCandidate']
        self.assertEqual('ConditionRecordReturned', applied['nativeResultCandidate'])
        malformed = dict(success, condition_vector_truncated=True)
        self.assertEqual('UnresolvedReturn', replay(request, malformed)['observations'][3]['conditionAttemptCandidate']['nativeResultCandidate'])

    def test_expiry_requires_exact_caller_zero_counter_and_disabled_record(self):
        before = bytearray(0x48)
        struct.pack_into('<II', before, 0, 27, 1)
        struct.pack_into('<I', before, 0x30, 5)
        after = bytearray(before)
        struct.pack_into('<I', after, 4, 0)
        removal = dict(beforeRaw=before.hex(), afterRaw=after.hex(), nativeReturnAlRaw=1)
        request = dict(condition_remove_caller_raw='0x1400813BE')
        self.assertEqual('Expired', condition_removal_route(removal, request, '0x140000000')['lifecycleCandidate'])
        self.assertIsNone(condition_removal_route(dict(removal, nativeReturnAlRaw=0), request, '0x140000000')['lifecycleCandidate'])
        self.assertIsNone(condition_removal_route(removal, request, None)['lifecycleCandidate'])
        self.assertIsNone(condition_removal_route(removal, dict(condition_remove_caller_raw='0x1400813BF'), '0x140000000')['lifecycleCandidate'])
        struct.pack_into('<I', before, 0x2C, 3)
        struct.pack_into('<I', after, 0x2C, 3)
        nonzero = dict(removal, beforeRaw=before.hex(), afterRaw=after.hex())
        self.assertIsNone(condition_removal_route(nonzero, request, '0x140000000')['lifecycleCandidate'])
        clear = condition_removal_route(nonzero, dict(condition_remove_caller_raw='0x1400E6932'), '0x140000000')
        self.assertEqual('BulkClear', clear['lifecycleCandidate'])
        self.assertEqual(3, clear['remainingCounterBeforeRaw'])
        dispel = condition_removal_route(nonzero, dict(condition_remove_caller_raw='0x1400DF127'), '0x140000000')
        self.assertEqual('Dispelled', dispel['lifecycleCandidate'])
        erased = dict(nonzero, afterRaw=None)
        cure = dict(condition_remove_caller_raw='0x1400DF127', condition_remove_r8b_raw=1)
        self.assertEqual('Dispelled', condition_removal_route(erased, cure, '0x140000000')['lifecycleCandidate'])
        for caller in ('0x1400E8F4F', '0x1400E8FBF'):
            overdrive = condition_removal_route(erased, dict(cure, condition_remove_caller_raw=caller), '0x140000000')
            self.assertEqual('Overdrive', overdrive['removalCauseCandidate'])
            self.assertEqual('Dispelled', overdrive['lifecycleCandidate'])
        self.assertIsNone(condition_removal_route(erased, dict(cure, condition_remove_caller_raw='0x1400E8EE8'), '0x140000000')['lifecycleCandidate'])
        self.assertIsNone(condition_removal_route(erased, dict(cure, condition_remove_r8b_raw=0), '0x140000000')['lifecycleCandidate'])
        self.assertIsNone(condition_removal_route(dict(erased, nativeReturnAlRaw=0), cure, '0x140000000')['lifecycleCandidate'])

    def test_condition_remove_pair_requires_matching_frame_and_preserves_failed_return(self):
        raw = bytearray(0x48)
        struct.pack_into('<I', raw, 0, 27)
        entry = hit('ConditionRemoveEntry', condition_manager_ptr='0x100', condition_remove_frame_raw='0x600',
            condition_remove_key_raw=27, condition_vector_count_raw=1, condition_vector_raw=raw.hex())
        returned = hit('ConditionRemoveReturnSite', condition_manager_ptr='0x100', condition_remove_frame_raw='0x600',
            condition_remove_return_al_raw=1, condition_vector_count_raw=0, condition_vector_raw=None)
        result = replay(entry, returned)
        observed = next(o for o in result['observations'] if o['raw'].get('name') == 'ConditionRemoveReturnSite')
        removal = observed['conditionRemovalCandidate']
        self.assertEqual(raw.hex(), removal['beforeRaw'])
        self.assertIsNone(removal['afterRaw'])
        self.assertEqual(1, removal['nativeReturnAlRaw'])
        mismatch = replay(entry, dict(returned, condition_remove_frame_raw='0x999'))
        self.assertIsNone(mismatch['observations'][3]['conditionRemovalCandidate'])
        failure = replay(entry, dict(returned, condition_remove_return_al_raw=0,
            condition_vector_count_raw=1, condition_vector_raw=raw.hex()))
        self.assertEqual(0, failure['observations'][3]['conditionRemovalCandidate']['nativeReturnAlRaw'])
        self.assertEqual(raw.hex(), failure['observations'][3]['conditionRemovalCandidate']['afterRaw'])
        gap = reconcile([dict(kind='executable', sha256=EXE_SHA256), dict(kind='armed'),
            dict(entry, observation_sequence=1), dict(returned, observation_sequence=9)], 'gap')
        self.assertIsNone(gap['observations'][3]['conditionRemovalCandidate'])

    def test_condition_insert_transition_requires_matching_complete_adjacent_evidence(self):
        raw = bytearray(0x48)
        struct.pack_into('<II', raw, 0, 27, 1)
        before = dict(name='ConditionRequestEntry', observation_sequence=1, tid=7,
            condition_manager_ptr='0x100', condition_r9_u32=27,
            condition_r8_ptr='0x200', condition_r8_raw=descriptor(),
            condition_vector_count_raw=0, condition_vector_raw=None)
        after = dict(name='ConditionInsertReturnSite', observation_sequence=2, tid=7,
            condition_manager_ptr='0x100', condition_insert_key_raw=27,
            condition_insert_descriptor_ptr='0x200', condition_insert_descriptor_raw=descriptor(),
            condition_vector_count_raw=1, condition_vector_raw=raw.hex(),
            condition_vector_ptr='0x300', condition_return_rax_ptr='0x300', condition_return_rax_raw=raw.hex())
        request = dict(observationId='before', raw=before, conditionSnapshot=condition_summary(before))
        returned = dict(observationId='after', raw=after)
        summary = condition_summary(after)
        result = condition_transition_candidate(request, returned, summary)
        self.assertEqual('RecordAdded', result['changeCandidate'])
        self.assertEqual(raw.hex(), result['afterRaw'])
        self.assertIsNone(result['beforeRaw'])
        for mismatch in [dict(tid=8), dict(observation_sequence=3), dict(condition_manager_ptr='0x999'),
                         dict(condition_insert_key_raw=28), dict(condition_insert_descriptor_raw=descriptor(999)),
                         dict(condition_insert_descriptor_ptr='0x999')]:
            self.assertIsNone(condition_transition_candidate(request, dict(returned, raw=dict(after, **mismatch)), summary))
        partial = condition_summary(dict(after, condition_vector_truncated=True))
        self.assertIsNone(condition_transition_candidate(request, returned, partial))
        struct.pack_into('<I', raw, 4, 2)
        request['conditionSnapshot'] = condition_summary(dict(before, condition_vector_count_raw=1,
            condition_vector_raw=raw.hex()))
        updated = condition_transition_candidate(request, returned, summary)
        self.assertEqual('PayloadUpdated', updated['changeCandidate'])
        request['conditionSnapshot'] = summary
        self.assertEqual('PayloadUnchanged', condition_transition_candidate(request, returned, summary)['changeCandidate'])

    def test_effect_identity_candidates_enrich_unlinked_calls_without_inventing_actions(self):
        source = bytearray(0x2A0)
        target = bytearray(0x2A0)
        struct.pack_into('<I', source, 0, 5)
        struct.pack_into('<I', target, 0, 60043)
        event = dict(dispatch(), dispatch_rdx_first_raw=source.hex(), dispatch_rdx_first_ptr='0x500',
                     dispatch_rcx_first_raw=target.hex(), dispatch_rcx_first_ptr='0x600')
        records = [dict(kind='executable', sha256=EXE_SHA256), dict(kind='armed'), dict(event, observation_sequence=1)]
        result = reconcile(records, 'effect-fixture', party_names={5: {'name': 'Agate'}})
        observation = result['observations'][-1]
        identity = observation['effectIdentityCandidates']
        self.assertEqual('Agate', identity['sourceContextStatus']['nameCandidate'])
        self.assertIsNone(identity['targetContextStatus']['nameCandidate'])
        self.assertEqual(60043, identity['targetContextStatus']['rawStatusId'])
        self.assertIsNone(observation['candidateActionId'])
        self.assertEqual(dict(event, observation_sequence=1), observation['raw'])
        records[-1] = dict(records[-1], dispatch_rdx_first_raw=source[:4].hex())
        incomplete = reconcile(records, 'effect-fixture', party_names={5: {'name': 'Agate'}})
        self.assertIsNone(incomplete['observations'][-1]['effectIdentityCandidates']['sourceContextStatus']['nameCandidate'])

    @staticmethod
    def mode(rva, before, after, **extra):
        return dict(kind='hit', name='BattleModeWrite', tid=7, rva=rva, before=before, after=after,
                    pointer_root_slot='0x140c5d768', pointer_root_at_arm='0x10000',
                    pointer_root_now='0x10000', pointer_offset='0x2d30', address='0x12d30', **extra)

    def test_battle_mode_framing_ignores_temporary_writes_and_keeps_field_rows(self):
        result = launch_replay(self.state(), self.mode('0xc35ad', 0, 1), self.state(),
                               self.mode('0xc4a5b', 1, 0), self.mode('0xc4a6d', 0, 1),
                               dispatch(), self.mode('0xc5753', 1, 0), self.state())
        self.assertEqual(1, len(result['commandIntervalCandidates']))
        interval = result['commandIntervalCandidates'][0]
        self.assertEqual('entry-and-exit-observed', interval['state'])
        self.assertEqual('Unknown', interval['outcome'])
        rows = [o for o in result['observations'] if o['raw'].get('kind') == 'hit']
        self.assertIsNone(rows[0]['commandIntervalCandidateId'])
        self.assertTrue(all(o['commandIntervalCandidateId'] == interval['id'] for o in rows[1:-1]))
        self.assertIsNone(rows[-1]['commandIntervalCandidateId'])

    def test_battle_mode_requires_writer_root_and_byte_transition(self):
        for begin in (self.mode('0xc35ad', 1, 1), self.mode('0xc4a6d', 0, 1),
                      dict(self.mode('0xc35ad', 0, 1), pointer_root_now='0x20000'),
                      dict(self.mode('0xc35ad', 0, 1), address='0x12d34')):
            result = launch_replay(begin, self.state())
            self.assertEqual([], result['commandIntervalCandidates'])
        open_scope = launch_replay(self.mode('0xc35ad', 0, 1), self.state())
        self.assertIsNone(open_scope['commandIntervalCandidates'][0]['endObservationId'])
        self.assertFalse(open_scope['completeActionStream'])
    def test_exit_outcome_candidates_require_valid_exact_exit_route_and_keep_verified_outcome_unknown(self):
        for code, name in ((1, 'Victory'), (3, 'Escape'), (0, None), (4, None)):
            result = launch_replay(self.mode('0xc35ad', 0, 1), dict(self.mode('0xc5753', 1, 0), r14=hex(code)))
            interval = result['commandIntervalCandidates'][0]
            self.assertEqual(code, interval['rawExitArgumentCandidate'])
            self.assertEqual(name, interval['outcomeCandidate'])
            self.assertEqual('Unknown', interval['outcome'])
        for invalid in (True, -1, 'invalid', '0x100000003', None):
            result = launch_replay(self.mode('0xc35ad', 0, 1), dict(self.mode('0xc5753', 1, 0), r14=invalid))
            self.assertIsNone(result['commandIntervalCandidates'][0]['outcomeCandidate'])
        result = launch_replay(self.mode('0xc35ad', 0, 1), dict(self.mode('0xc4aa4', 1, 1), r14='0x3'))
        self.assertNotIn('outcomeCandidate', result['commandIntervalCandidates'][0])
    def test_adjacent_byte_write_preserves_engine_interval_without_claiming_command_scope(self):
        result = launch_replay(self.mode('0xc35ad', 0, 1), self.mode('0xc4aa4', 1, 1),
                               dict(self.mode('0xc5753', 1, 0), r14='0x3'))
        interval = result['commandIntervalCandidates'][0]
        self.assertEqual('entry-and-exit-observed', interval['state'])
        self.assertEqual('UnclassifiedEngineBattle', interval['scope'])
        self.assertEqual(3, interval['rawExitArgumentCandidate'])
        self.assertFalse(interval['liveBoundaryValidationComplete'])
        command = launch_replay(self.mode('0xc35ad', 0, 1), self.state(), self.mode('0xc5753', 1, 0))
        self.assertEqual('CommandStagesObservedCandidate', command['commandIntervalCandidates'][0]['scope'])
        inconsistent = launch_replay(self.mode('0xc35ad', 0, 1), self.mode('0xc4aa4', 1, 0))
        self.assertEqual('scope-correlation-reset', inconsistent['commandIntervalCandidates'][0]['state'])
    def test_roster_snapshots_keep_unknown_actors_and_scope_pointer_identity_to_interval(self):
        flags = bytearray(0x80)
        struct.pack_into('<I', flags, 12, 0x34)
        status = bytearray(0x2A0)
        struct.pack_into('<I', status, 0, 60043)
        row = {'actor_ptr': '0x500', 'status_ptr': '0x600', 'status_raw': status.hex()}
        snapshot = dict(self.mode('0xc4aa4', 1, 1), mode_root_2ce0_raw=flags.hex(),
                        mode_roster_count_raw=1, mode_roster_candidates=[row])
        result = launch_replay(self.mode('0xc35ad', 0, 1), snapshot, self.mode('0xc5753', 1, 0),
                               self.mode('0xc35ad', 0, 1), snapshot, self.mode('0xc5753', 1, 0))
        a, b = result['commandIntervalCandidates']
        first, second = [i['rosterSnapshots'][0] for i in (a, b)]
        self.assertTrue(first['collectionComplete'])
        self.assertEqual(60043, first['actors'][0]['rawStatusId'])
        self.assertIsNone(first['actors'][0]['nameCandidate'])
        self.assertNotEqual(first['actors'][0]['actorInstanceCandidateId'], second['actors'][0]['actorInstanceCandidateId'])
        self.assertEqual(0x34, a['initializerFlagSnapshots'][0]['rawFlags'])
        incomplete = dict(snapshot, mode_roster_candidates=[{}])
        result = launch_replay(self.mode('0xc35ad', 0, 1), incomplete)
        self.assertFalse(result['commandIntervalCandidates'][0]['rosterSnapshots'][0]['collectionComplete'])
    def test_interrupt_requires_scoped_selector_live_target_and_flag_transition(self):
        owner = bytearray(0x1000)
        pending = dict(self.state('0x68f00'), actor_state_owner_raw=owner.hex(),
                       actor_state_owner_c78_ptr='0x200', actor_state_owner_c78_raw=descriptor())
        post_owner = bytearray(owner)
        struct.pack_into('<I', post_owner, 0xE24, 0x1000)
        status = bytearray(0x2A0)
        struct.pack_into('<i', status, 12, 100)
        post = dict(self.state('0x67ad0'), actor_state_owner_raw=post_owner.hex(),
                    actor_state_owner_c78_ptr=None, actor_state_linked_first_raw=status.hex())
        effect = dict(dispatch(), dispatch_r9_u32=47, dispatch_rcx_ptr='0x400')
        valid = launch_replay(pending, effect, post)
        self.assertEqual(1, len(valid['interruptCandidates']))
        self.assertFalse(valid['interruptCandidates'][0]['directCancelCallbackObserved'])
        self.assertEqual('pending-cleared-on-corroborated-impede-route', valid['queueCandidates'][0]['state'])
        dead = bytearray(status)
        struct.pack_into('<i', dead, 12, 0)
        cases = [(pending, dict(effect, dispatch_r9_u32=45), post),
                 (pending, dict(effect, dispatch_rcx_ptr='0x999'), post),
                 (pending, effect, dict(post, actor_state_linked_first_raw=dead.hex())),
                 (dict(pending, actor_state_owner_raw=post_owner.hex()), effect, post),
                 (pending, effect, dict(post, actor_state_owner_c78_ptr='0x200')),
                 (pending, effect, dict(post, actor_state_owner_raw=owner.hex()))]
        for events in cases:
            self.assertEqual([], launch_replay(*events)['interruptCandidates'])
    def test_direct_state_effect_parent_requires_descriptor_source_and_current_stage(self):
        result = launch_replay(self.state(), dispatch(), dict(dispatch(), dispatch_rcx_ptr='0x301'))
        self.assertTrue(all(r['stateCandidateId'] is not None for r in result['dispatchRuns']))
        for effect in (dispatch(descriptor(123)), dict(dispatch(), dispatch_rdx_ptr='0x999')):
            invalid = launch_replay(self.state(), effect)
            self.assertIsNone(invalid['dispatchRuns'][0]['stateCandidateId'])
        stale = launch_replay(self.state(), self.state('0x6c5a0'), dispatch())
        self.assertIsNone(stale['dispatchRuns'][0]['stateCandidateId'])
    @staticmethod
    def state(handler='0x68320', first=True):
        return hit('ActorStateDispatchCall', actor_state_owner_ptr='0x100',
                   actor_state_handler_ptr_raw=hex(0x140000000 + int(handler, 16)),
                   actor_state_id_rax_raw='0x12', actor_state_first_update_candidate=first,
                   actor_state_owner_c70_ptr='0x200', actor_state_owner_c70_raw=descriptor(),
                   actor_state_owner_328_ptr='0x600', actor_state_context_1d90_ptr='0x400')

    def test_first_state_links_accepted_only_profile_to_multiple_recipients(self):
        result = launch_replay(self.state(), launch('accepted', '0x1400686f1'),
                               dispatch(), dict(dispatch(), dispatch_rcx_ptr='0x301'))
        self.assertEqual(1, len(result['stateEntryCandidates']))
        item = result['launchCandidates'][0]
        self.assertIsNone(item['requestObservationId'])
        self.assertEqual(result['stateEntryCandidates'][0]['stateCandidateId'], item['stateCandidateId'])
        self.assertEqual(2, len(item['dispatchRunIds']))
        self.assertFalse(item['executionConfirmed'])

    def test_guard_bypass_and_unknown_states_remain_without_invented_launch(self):
        result = launch_replay(self.state('0x69570'), self.state('0x12345', None), dispatch())
        self.assertEqual(2, len(result['stateEntryCandidates']))
        self.assertEqual([], result['launchCandidates'])
        self.assertIsNone(result['dispatchRuns'][0]['launchCandidateId'])

    def test_state_match_rejects_wrong_handler_owner_descriptor_and_phase(self):
        variants = [self.state('0x68da0'), self.state(first=None), self.state(first=False),
                    dict(self.state(), actor_state_owner_ptr='0x101'),
                    dict(self.state(), actor_state_owner_c70_raw=descriptor(123)),
                    dict(self.state(), actor_state_context_1d90_ptr='0x999')]
        for state in variants:
            result = launch_replay(state, launch('accepted', '0x1400686f1'), dispatch())
            self.assertEqual([], result['launchCandidates'])
            self.assertIsNone(result['dispatchRuns'][0]['launchCandidateId'])

    def test_repeated_state_clears_previous_effect_parent(self):
        result = launch_replay(self.state(), launch('accepted', '0x1400686f1'), dispatch(),
                               self.state(), dispatch())
        self.assertIsNotNone(result['dispatchRuns'][0]['launchCandidateId'])
        self.assertIsNone(result['dispatchRuns'][1]['launchCandidateId'])

    def test_state_preparation_launch_is_preserved_but_not_effect_parent(self):
        result = launch_replay(self.state('0x68da0'), launch('accepted', '0x140068e8b'), dispatch())
        self.assertEqual(1, len(result['launchCandidates']))
        self.assertIsNone(result['dispatchRuns'][0]['launchCandidateId'])

    def test_pending_state_survives_other_actor_and_pairs_resume_inline(self):
        pending = dict(self.state('0x68f00'), actor_state_owner_c78_ptr='0x200',
                       actor_state_owner_c78_raw=descriptor())
        resume = dict(pending, actor_state_handler_ptr_raw='0x140068ff0')
        other = dict(self.state(), actor_state_owner_ptr='0x101')
        result = launch_replay(pending, other, dispatch(descriptor(123)), resume, self.state(), dispatch())
        q = result['queueCandidates'][0]
        self.assertIsNone(q['storeObservationId'])
        self.assertEqual('resume-and-effect-route-observed', q['state'])
        self.assertIsNotNone(q['executionHandlerObservationId'])
        self.assertIsNone(result['dispatchRuns'][0]['candidateActionId'])
        self.assertEqual(q['candidateActionId'], result['dispatchRuns'][1]['candidateActionId'])
        mismatch = launch_replay(pending, dict(resume, actor_state_owner_c78_raw=descriptor(123)), dispatch())
        self.assertIsNone(mismatch['queueCandidates'][0]['resumeObservationId'])

    def test_legacy_saved_owner_recovery_preserves_original_mistaken_fields(self):
        state = self.state()
        owner = bytearray(0x1000)
        struct.pack_into('<Q', owner, 0x328, 0x600)
        struct.pack_into('<Q', owner, 0xC70, 0x200)
        state['actor_state_owner_raw'] = owner.hex()
        stack = bytearray(0x80)
        struct.pack_into('<Q', stack, 0x60, 0x100)
        accepted = dict(launch('accepted', '0x1400686f1'), launch_context_ptr='0x26',
                        launch_actor_ptr=None, launch_actor_c70_ptr=None,
                        launch_actor_c70_raw=None, launch_owner_link_matches=None,
                        launch_stack_raw=stack.hex())
        result = launch_replay(state, accepted, dispatch())
        row = result['observations'][4]
        self.assertEqual('0x26', row['raw']['launch_context_ptr'])
        self.assertFalse(row['derivedLaunchRecovery']['descriptorSnapshotAtLaunch'])
        self.assertIsNotNone(result['dispatchRuns'][0]['launchCandidateId'])
        invalid = launch_replay(dict(state, actor_state_owner_raw='00' * 0x1000), accepted, dispatch())
        self.assertEqual([], invalid['launchCandidates'])

    def test_accepted_launch_links_multiple_recipient_runs_by_descriptor_and_source(self):
        result = launch_replay(launch('request'), launch('accepted'), dispatch(),
                               dict(dispatch(), dispatch_rcx_ptr='0x301'),
                               hit('ResourceSetEntry', payload='unknown resource'),
                               dict(dispatch(), dispatch_rcx_ptr='0x302'))
        item = result['launchCandidates'][0]
        self.assertEqual('queue-call-observed', item['state'])
        self.assertFalse(item['executionConfirmed'])
        self.assertEqual(3, len(item['dispatchRunIds']))
        self.assertTrue(all(r['launchCandidateId'] == item['launchCandidateId'] for r in result['dispatchRuns']))
        resource = next(o for o in result['observations'] if o['raw'].get('name') == 'ResourceSetEntry')
        self.assertIsNone(resource['launchCandidateId'])

    def test_preparation_and_unaccepted_requests_cannot_parent_effects(self):
        for caller, accepted in [('0x140068e8b', True), ('0x140069311', False)]:
            events = [launch('request', caller)]
            if accepted:
                events.append(launch('accepted', caller))
            events.append(dispatch())
            result = launch_replay(*events)
            self.assertIsNone(result['dispatchRuns'][0]['launchCandidateId'])

    def test_launch_acceptance_requires_same_frame_and_inline_descriptor(self):
        for accepted in (launch('accepted', stack='0x901'),
                         dict(launch('accepted'), launch_actor_c70_raw=descriptor(1)),
                         dict(launch('accepted'), launch_owner_link_matches=False)):
            result = launch_replay(launch('request'), accepted, dispatch())
            self.assertIsNone(result['dispatchRuns'][0]['launchCandidateId'])

    def test_repeated_launch_with_same_descriptor_gets_new_candidate(self):
        result = launch_replay(launch('request'), launch('accepted'), dispatch(),
                               launch('request'), launch('accepted'), dispatch())
        self.assertEqual(2, len(result['launchCandidates']))
        self.assertNotEqual(result['dispatchRuns'][0]['launchCandidateId'], result['dispatchRuns'][1]['launchCandidateId'])
        pending = launch_replay(launch('request'), launch('accepted'), dispatch(), launch('request'), dispatch())
        self.assertIsNone(pending['dispatchRuns'][1]['launchCandidateId'])

    def test_source_context_mismatch_keeps_dispatch_unparented(self):
        result = launch_replay(launch('request'), launch('accepted'),
                               dict(dispatch(), dispatch_rdx_ptr='0x999'))
        self.assertIsNone(result['dispatchRuns'][0]['launchCandidateId'])

    def test_new_setup_observation_keeps_matching_resume_window_as_candidate(self):
        setup = hit('ActionSetupEntry', setup_actor_ptr='0x100',
                    setup_rdx_ptr='0x200', setup_rdx_raw=descriptor())
        result = replay(store(), resume(), setup, dispatch())
        queue = result['queueCandidates'][0]
        self.assertEqual(1, len(queue['setupObservationIds']))
        self.assertEqual(queue['candidateActionId'], result['dispatchRuns'][0]['candidateActionId'])
        self.assertFalse(result['completeActionStream'])

    def test_condition_record_update_without_key_change_is_preserved(self):
        before = bytearray(0x48)
        struct.pack_into('<II', before, 0, 27, 1)
        record = dict(condition_vector_count_raw=1, condition_vector_raw=before.hex(),
                      condition_vector_ptr='0x100', condition_return_rax_ptr='0x100',
                      condition_return_rax_raw=before.hex())
        first = condition_summary(record)
        self.assertEqual(27, first['returnedRawKey'])
        after = bytearray(before)
        struct.pack_into('<I', after, 4, 3)
        second = condition_summary(dict(record, condition_vector_raw=after.hex(),
                                        condition_return_rax_raw=after.hex()), first)
        self.assertEqual(27, second['changesSincePreviousSnapshot'][0]['rawKey'])
        self.assertEqual(before.hex(), second['changesSincePreviousSnapshot'][0]['beforeRaw'])
        self.assertEqual(after.hex(), second['changesSincePreviousSnapshot'][0]['afterRaw'])
        partial = condition_summary(dict(record, condition_vector_truncated=True), first)
        self.assertIsNone(partial['changesSincePreviousSnapshot'])
        mismatched = condition_summary(dict(record, condition_return_rax_raw='00' * 0x48))
        self.assertIsNone(mismatched['returnedRawKey'])

    def test_condition_labels_preserve_unknown_keys_and_raw_bytes(self):
        from types import SimpleNamespace
        raw = bytearray(0x90)
        struct.pack_into('<I', raw, 0, 31)
        struct.pack_into('<I', raw, 0x48, 9999)
        lookup = SimpleNamespace(conditions={31: dict(rawKey=31, nameCandidate='SPD UP', tableRow=37)})
        result = condition_summary(dict(condition_vector_count_raw=2, condition_vector_raw=raw.hex()), lookup=lookup)
        self.assertEqual('SPD UP', result['records'][0]['nameCandidate'])
        self.assertEqual(raw[:0x48].hex(), result['records'][0]['inlineRaw'])
        self.assertIsNone(result['records'][1]['nameCandidate'])
        self.assertEqual(9999, result['records'][1]['rawKey'])
        self.assertIsNone(result['returnedRawKey'])

    def test_condition_request_snapshot_does_not_claim_application(self):
        result = replay(hit('ConditionRequestEntry', condition_r9_u32=31,
            condition_vector_count_raw=0, condition_vector_raw=None, condition_manager_ptr='0x100'))
        observed = next(o for o in result['observations'] if o['raw'].get('name') == 'ConditionRequestEntry')
        self.assertTrue(observed['conditionSnapshot']['collectionComplete'])
        self.assertIsNone(observed['conditionSnapshot']['returnedRawKey'])
        self.assertIsNone(observed['requestedConditionCandidate'])
        self.assertIn('application-unresolved', observed['stage'])
        self.assertFalse(result['completeActionStream'])

    def test_pending_cast_survives_intervening_action_without_stealing_effects(self):
        result = replay(store(), dispatch(descriptor(0x509C5)), resume(), dispatch(),
                        condition(), dispatch())
        queue = result['queueCandidates'][0]
        self.assertEqual('resume-and-effect-route-observed', queue['state'])
        self.assertIsNone(result['dispatchRuns'][0]['candidateActionId'])
        self.assertEqual(queue['candidateActionId'], result['dispatchRuns'][1]['candidateActionId'])
        self.assertEqual(2, len(result['dispatchRuns'][1]['observationIds']))
        self.assertEqual(1, len(result['dispatchRuns'][1]['conditionObservationIds']))
        self.assertEqual(10, len(result['observations']))
        self.assertFalse(result['completeActionStream'])

    def test_all_records_retained_including_unknown_hooks_and_markers(self):
        unknown = dict(kind='hit', name='UnknownHook', tid=7, rva='0x123', payload={'raw': 99})
        result = replay(unknown, dispatch(descriptor(0x12345678)))
        self.assertEqual(unknown['payload'], result['observations'][2]['raw']['payload'])
        self.assertEqual('0x12345678', result['dispatchRuns'][0]['descriptor']['rawPackedId'])
        self.assertIsNone(result['dispatchRuns'][0]['descriptor']['nameCandidate'])

    def test_pointer_reuse_with_changed_bytes_does_not_match(self):
        changed = bytearray.fromhex(descriptor())
        changed[8] = 1  # Excluded from table lookup, still required for queue identity.
        result = replay(store(), resume(raw=changed.hex()), dispatch(raw=changed.hex()))
        self.assertIsNone(result['queueCandidates'][0]['resumeObservationId'])
        self.assertIsNone(result['dispatchRuns'][0]['candidateActionId'])

    def test_overwrite_keeps_old_store_without_inventing_cancellation(self):
        result = replay(store(), store(), resume())
        self.assertEqual(2, len(result['queueCandidates']))
        self.assertEqual('another-store-before-resume', result['queueCandidates'][0]['unresolvedReason'])
        self.assertEqual('resume-observed', result['queueCandidates'][1]['state'])

    def test_missing_resume_stays_unresolved_even_with_matching_effects(self):
        result = replay(store(), dispatch())
        self.assertEqual('store-observed', result['queueCandidates'][0]['state'])
        self.assertIsNone(result['dispatchRuns'][0]['candidateActionId'])
        self.assertEqual('capture-marker:disarmed', result['queueCandidates'][0]['unresolvedReason'])

    def test_no_links_across_sequence_gap_thread_or_wrong_hash(self):
        cases = [dict(resume(), observation_sequence=9), dict(resume(), tid=8)]
        for event in cases:
            # Direct records permit a deliberately gapped input sequence.
            records = [dict(kind='executable', sha256=EXE_SHA256), dict(kind='armed'),
                       dict(store(), observation_sequence=1), dict(event, observation_sequence=event.get('observation_sequence', 2))]
            result = reconcile(records, 'fixture')
            self.assertIsNone(result['queueCandidates'][0]['resumeObservationId'])
        result = replay(store(), resume(), dispatch(), fingerprint='unsupported')
        self.assertEqual([], result['queueCandidates'])
        self.assertEqual(7, len(result['observations']))

    def test_condition_requires_descriptor_and_both_contexts(self):
        result = replay(dispatch(), dict(condition(), condition_return_rsi_ptr='0x999'))
        self.assertEqual([], result['dispatchRuns'][0]['conditionObservationIds'])
        self.assertEqual('unmatched-condition-return', result['observations'][3]['linkReason'])

    def test_ambiguous_resumes_do_not_assign_effects(self):
        result = replay(store('0x100'), store('0x101'), resume('0x100'), resume('0x101'), dispatch())
        self.assertIsNone(result['dispatchRuns'][0]['candidateActionId'])

    def test_unrelated_effect_after_resume_closes_link_window(self):
        result = replay(store(), resume(), dispatch(descriptor(123)), dispatch())
        self.assertTrue(all(run['candidateActionId'] is None for run in result['dispatchRuns']))

    def test_lookup_requires_unique_compared_bytes_and_preserves_excluded_bytes(self):
        lookup = DescriptorLookup.__new__(DescriptorLookup)
        data = bytes.fromhex(descriptor())
        lookup.rows = [({'row': 1, 'name': 'Saint'}, data)]
        changed = bytearray(data)
        changed[8] = 1
        self.assertEqual('Saint', lookup.describe(changed.hex())['nameCandidate'])
        self.assertEqual(changed.hex(), lookup.describe(changed.hex())['inlineRaw'])
        changed[0x20] = 1
        self.assertIsNone(lookup.describe(changed.hex())['nameCandidate'])
        lookup.rows *= 2
        self.assertEqual('ambiguous', lookup.describe(data.hex())['lookupState'])
        self.assertIsNone(lookup.describe(data.hex())['nameCandidate'])


if __name__ == '__main__':
    unittest.main()
