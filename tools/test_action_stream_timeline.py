import unittest
import struct
import importlib.util
from pathlib import Path

from action_stream_timeline import project_timeline
# Embedded Python deliberately excludes the checkout from sys.path. Load only
# the test fixtures by file; application imports still use the packaged tools.
spec = importlib.util.spec_from_file_location('timeline_fixtures',
    Path(__file__).with_name('test_reconcile_action_stream.py'))
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
launch_replay, dispatch, hit, descriptor = (fixtures.launch_replay,
    fixtures.dispatch, fixtures.hit, fixtures.descriptor)


class TimelineChecks(unittest.TestCase):
    def test_animation_candidate_does_not_replace_descriptor_identity(self):
        ledger = launch_replay(fixtures.ReconcileChecks.state(),
            fixtures.launch('accepted', '0x1400686f1'), dispatch())
        candidate = dict(nameCandidate='Diamond Dust', provenance='accepted-animation-only')
        ledger['launchCandidates'][0]['animationLookupCandidate'] = candidate
        action = project_timeline(ledger)['actionCandidates'][0]
        self.assertEqual(candidate, action['animationLookupCandidate'])
        self.assertIsNone(action['descriptor']['nameCandidate'])
        self.assertEqual('0xFFFF00C3', action['descriptor']['rawPackedId'])
        ledger['launchCandidates'][0]['acceptedObservationId'] = None
        self.assertNotIn('animationLookupCandidate', project_timeline(ledger)['actionCandidates'][0])

    def test_unfamiliar_record_kind_stays_unknown_instead_of_becoming_a_capture_marker(self):
        ledger = launch_replay(dict(kind='future-game-event', payload={'newKey': 42}))
        timeline = project_timeline(ledger)['timeline']
        unknown = next(o for o in ledger['observations'] if o['raw'].get('kind') == 'future-game-event')
        self.assertEqual('UnknownObservation', next(r['kind'] for r in timeline if r['observationId'] == unknown['observationId']))
        self.assertEqual({'newKey': 42}, unknown['raw']['payload'])

    def test_targets_preserve_distinct_instances_and_unresolved_names(self):
        status = struct.pack('<I', 60016).hex()
        ledger = launch_replay(fixtures.ReconcileChecks.state(),
            dict(dispatch(), dispatch_rcx_first_ptr='0x500', dispatch_rcx_first_raw=status),
            dict(dispatch(), dispatch_rcx_first_ptr='0x501', dispatch_rcx_first_raw=status))
        targets = project_timeline(ledger)['actionCandidates'][0]['targetCandidates']
        self.assertEqual(2, len(targets))
        self.assertTrue(all(t['rawStatusId'] == 60016 and t['nameCandidate'] is None for t in targets))

    def test_cast_stages_share_one_action_and_intervening_actor_stays_separate(self):
        pending = dict(fixtures.ReconcileChecks.state('0x68f00'), actor_state_owner_c78_ptr='0x200',
                       actor_state_owner_c78_raw=descriptor())
        resume = dict(pending, actor_state_handler_ptr_raw='0x140068ff0')
        other = dict(fixtures.ReconcileChecks.state(), actor_state_owner_ptr='0x101')
        ledger = launch_replay(pending, other, dispatch(descriptor(123)), resume,
                               fixtures.ReconcileChecks.state(), dispatch())
        result = project_timeline(ledger)
        self.assertEqual(2, len(result['actionCandidates']))
        cast = result['actionCandidates'][1]
        self.assertEqual(3, len(cast['stageObservationIds']))
        self.assertEqual(1, len(cast['effectObservationIds']))
        self.assertEqual(len(ledger['observations']), len(result['timeline']))
        self.assertIsNone(result['actionCandidates'][0]['result'])

    def test_repeated_guards_without_effects_and_unknown_observations_are_retained(self):
        ledger = launch_replay(fixtures.ReconcileChecks.state('0x69570'), fixtures.ReconcileChecks.state('0x69570'),
                               hit('ResourceSetEntry', rawProperty='unknown'),
                               dict(kind='hit', name='UnfamiliarHook', tid=7, rva='0x123'))
        result = project_timeline(ledger)
        self.assertEqual(2, len(result['actionCandidates']))
        self.assertNotEqual(*[a['actionCandidateId'] for a in result['actionCandidates']])
        resource = next(e for e in result['timeline'] if e['kind'] == 'ResourceWriteObserved')
        self.assertIsNone(resource['actionCandidateId'])
        self.assertTrue(any(e['kind'] == 'UnknownObservation' for e in result['timeline']))
        self.assertFalse(result['completeActionStream'])


if __name__ == '__main__':
    unittest.main()
