"""Ordered research projection; raw ledger observations remain the source record."""
import struct

CAPTURE_MARKERS = {'executable', 'attached', 'capture_policy', 'module', 'write_baseline',
                   'armed', 'disarmed', 'detached', 'hit_limit', 'process_exit'}


def project_timeline(ledger, party_names=None):
    observations = ledger['observations']
    states = {s['observationId']: s for s in ledger.get('stateEntryCandidates', [])}
    queues = {q.get('executionHandlerObservationId'): q for q in ledger['queueCandidates']
              if q.get('executionHandlerObservationId')}
    actions, action_by_state, action_by_queue = [], {}, {}
    # These are observed native stages, not universal semantic execution states.
    roles = {'0x68320': 'main-descriptor-handler', '0x69570': 'defend-handler',
             '0x68d40': 'chain-handler'}
    for observation in observations:
        oid = observation['observationId']
        state = states.get(oid)
        if not state or state['firstUpdateCandidate'] is not True or state['handlerRva'] not in roles:
            continue
        q = queues.get(oid)
        action_id = q['candidateActionId'] if q else state['stateCandidateId'] + ':action'
        item = {'actionCandidateId': action_id, 'observationId': oid,
                'observedAt': observation['raw'].get('at'), 'stage': roles[state['handlerRva']],
                'actorPointer': state['actorPointer'], 'descriptor': state['descriptor'],
                'actorNameCandidate': state.get('actorNameCandidate'),
                'actorNameProvenance': state.get('actorNameProvenance'),
                'stageObservationIds': [oid], 'effectObservationIds': [],
                'executionConfirmed': False, 'isCritical': None, 'result': None}
        if q:
            item['stageObservationIds'] = [key for key in
                (q.get('storeObservationId'), q.get('pendingStageObservationId'),
                 q.get('resumeObservationId'), oid) if key]
            action_by_queue[q['candidateActionId']] = action_id
        actions.append(item)
        action_by_state[state['stateCandidateId']] = action_id
    actions_by_id = {a['actionCandidateId']: a for a in actions}
    interrupts = ledger.get('interruptCandidates', [])
    interrupt_posts = {i['postObservationId']: i for i in interrupts}
    for interrupt in interrupts:
        q = next(q for q in ledger['queueCandidates'] if q['candidateActionId'] == interrupt['pendingActionCandidateId'])
        oid = q.get('pendingStageObservationId') or q['storeObservationId']
        observation = next(o for o in observations if o['observationId'] == oid)
        item = {'actionCandidateId': q['candidateActionId'], 'observationId': oid,
                'observedAt': observation['raw'].get('at'), 'stage': 'pending-cast-interruption-corroborated',
                'actorPointer': q['actorPointer'], 'descriptor': q['descriptor'],
                'actorNameCandidate': states.get(oid, {}).get('actorNameCandidate'),
                'actorNameProvenance': states.get(oid, {}).get('actorNameProvenance'),
                'stageObservationIds': [oid, interrupt['postObservationId']], 'effectObservationIds': [],
                'executionConfirmed': False, 'isCritical': None, 'result': None,
                'interruptCandidateId': interrupt['interruptCandidateId']}
        actions.append(item)
        actions_by_id[item['actionCandidateId']] = item
    order = {o['observationId']: i for i, o in enumerate(observations)}
    actions.sort(key=lambda a: order[a['observationId']])
    launch_actions = {launch['launchCandidateId']: action_by_state[launch['stateCandidateId']]
                      for launch in ledger.get('launchCandidates', [])
                      if launch.get('stateCandidateId') in action_by_state}
    for launch in ledger.get('launchCandidates', []):
        action_id = launch_actions.get(launch['launchCandidateId'])
        candidate = launch.get('animationLookupCandidate')
        if action_id and launch.get('acceptedObservationId') and candidate:
            actions_by_id[action_id]['animationLookupCandidate'] = candidate
    links = {}
    for action in actions:
        for oid in action['stageObservationIds']:
            links[oid] = action['actionCandidateId']
    for observation in observations:
        oid = observation['observationId']
        action_id = (action_by_queue.get(observation.get('candidateActionId'))
                     or action_by_state.get(observation.get('stateCandidateId'))
                     or launch_actions.get(observation.get('launchCandidateId')))
        if action_id:
            links[oid] = action_id
            if observation['raw'].get('name') in ('EffectDispatchEntry', 'ConditionReturnSite'):
                actions_by_id[action_id]['effectObservationIds'].append(oid)
    timeline = []
    for action in actions:
        targets = {}
        for observation in observations:
            if observation['observationId'] not in action['effectObservationIds']:
                continue
            raw = observation['raw']
            status = raw.get('dispatch_rcx_first_raw')
            ptr = raw.get('dispatch_rcx_first_ptr')
            try:
                data = bytes.fromhex(status) if isinstance(status, str) else b''
            except ValueError:
                data = b''
            if ptr and len(data) >= 4:
                status_id = struct.unpack_from('<I', data)[0]
                name = (party_names or {}).get(status_id, {}).get('name') if status_id < 60000 else None
                targets[ptr] = {'statusPointer': ptr, 'rawStatusId': status_id, 'nameCandidate': name}
        action['targetCandidates'] = list(targets.values())
    for observation in observations:
        raw = observation['raw']
        name = raw.get('name')
        if raw.get('kind') in CAPTURE_MARKERS:
            kind = 'CaptureMarker'
        elif raw.get('kind') != 'hit':
            kind = 'UnknownObservation'
        elif name == 'ResourceSetEntry':
            kind = 'ResourceWriteObserved'
        elif name == 'EffectDispatchEntry':
            kind = 'EffectCallObserved'
        elif name in ('ConditionRequestEntry', 'ConditionReturnSite', 'ConditionInsertReturnSite', 'ConditionRequestReturnSite',
                      'ConditionRemoveEntry', 'ConditionRemoveReturnSite'):
            kind = 'ConditionSnapshotObserved'
        elif name in ('ActorStateDispatchCall', 'AnimationLaunchEntry', 'AnimationLaunchAccepted',
                      'DescriptorStoreSite', 'DescriptorResumeSite', 'ActionSetupEntry'):
            kind = 'ActionStageObserved'
        else:
            kind = 'UnknownObservation'
        if observation['observationId'] in interrupt_posts:
            kind = 'CastInterruptCorroborated'
        timeline.append({'observationId': observation['observationId'],
                         'sequence': raw.get('observation_sequence'), 'observedAt': raw.get('at'),
                         'kind': kind, 'rawHook': name,
                         'commandIntervalCandidateId': observation.get('commandIntervalCandidateId'),
                         'actionCandidateId': links.get(observation['observationId'])})
    return {'schemaVersion': 1, 'origin': 'ResearchActionTimeline',
            'completeActionStream': False, 'actionCandidates': actions, 'timeline': timeline,
            'coverageGaps': ledger['coverageGaps']}
