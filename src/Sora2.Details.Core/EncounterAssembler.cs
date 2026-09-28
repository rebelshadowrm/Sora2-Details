namespace Sora2.Details.Core;

/// <summary>Turns ordered capture messages into immutable encounter snapshots.</summary>
public sealed class EncounterAssembler
{
    private readonly Dictionary<string, State> _active = new(StringComparer.Ordinal);
    private readonly HashSet<string> _seenEncounterIds = new(StringComparer.Ordinal);

    public IReadOnlyList<Encounter> Accept(CaptureMessage message)
    {
        var changed = new List<Encounter>();
        switch (message)
        {
            case EncounterStarted start:
                if (string.IsNullOrWhiteSpace(start.EncounterId))
                    throw new ArgumentException("Encounter ID is required.");
                if (start.Actors.Any(actor => string.IsNullOrWhiteSpace(actor.Id)) ||
                    start.Actors.Select(actor => actor.Id).Distinct(StringComparer.Ordinal).Count() != start.Actors.Count)
                    throw new InvalidDataException("Encounter actors need unique, nonempty IDs.");
                if (!_seenEncounterIds.Add(start.EncounterId))
                    throw new InvalidDataException($"Encounter ID was reused: {start.EncounterId}");
                foreach (var previous in _active.Values.ToArray())
                {
                    previous.Issues.Add("Capture started another encounter before this one ended.");
                    changed.Add(previous.Snapshot(EncounterOutcome.Interrupted));
                }
                _active.Clear();
                var startedState = new State(start);
                _active.Add(start.EncounterId, startedState);
                changed.Add(startedState.Snapshot());
                break;

            case EffectObserved observed when _active.TryGetValue(observed.EncounterId, out var effectState):
                effectState.Add(observed.Effect);
                changed.Add(effectState.Snapshot());
                break;

            case CaptureGap gap when _active.TryGetValue(gap.EncounterId, out var gapState):
                gapState.Issues.Add($"Capture gap: {gap.Reason}");
                changed.Add(gapState.Snapshot());
                break;

            case EncounterEnded end when _active.Remove(end.EncounterId, out var endedState):
                changed.Add(endedState.Snapshot(end.Outcome));
                break;

            case CaptureSourceInterrupted interrupted:
                changed.AddRange(InterruptOpen(interrupted.Reason));
                break;

            default:
                throw new InvalidDataException("Capture message refers to an encounter that is not active.");
        }
        return changed;
    }

    public IReadOnlyList<Encounter> InterruptOpen(string reason)
    {
        var interrupted = _active.Values.Select(state =>
        {
            state.Issues.Add(reason);
            return state.Snapshot(EncounterOutcome.Interrupted);
        }).ToArray();
        _active.Clear();
        return interrupted;
    }

    private sealed class State(EncounterStarted start)
    {
        private readonly Dictionary<long, CombatEvent> _events = [];
        private readonly HashSet<string> _actorIds = start.Actors.Select(actor => actor.Id).ToHashSet(StringComparer.Ordinal);
        internal readonly List<string> Issues = [];

        internal void Add(CombatEvent effect)
        {
            if (_events.TryGetValue(effect.Sequence, out var prior))
            {
                if (prior != effect) Issues.Add($"Conflicting duplicate sequence {effect.Sequence}.");
                return;
            }
            if (effect.Sequence < 1) Issues.Add($"Invalid sequence {effect.Sequence}.");
            if (!_actorIds.Contains(effect.TargetId)) Issues.Add($"Unknown target ID at sequence {effect.Sequence}.");
            if (effect.SourceId is not null && !_actorIds.Contains(effect.SourceId))
                Issues.Add($"Unknown source ID at sequence {effect.Sequence}.");
            if (effect.Kind is CombatEventKind.Damage or CombatEventKind.Healing)
            {
                if (effect.EffectiveAmount is null) Issues.Add($"Unknown effective amount at sequence {effect.Sequence}.");
                if (effect.EffectiveAmount < 0) Issues.Add($"Negative effective amount at sequence {effect.Sequence}.");
                if (effect.SourceId is null) Issues.Add($"Unknown source at sequence {effect.Sequence}.");
                if (effect.MoveId is null && effect.MoveName is null)
                    Issues.Add($"Unknown move at sequence {effect.Sequence}.");
                if (effect.HpBefore is int before && effect.HpAfter is int after &&
                    effect.EffectiveAmount is int amount &&
                    amount != (effect.Kind == CombatEventKind.Damage ? before - after : after - before))
                    Issues.Add($"HP transition mismatch at sequence {effect.Sequence}.");
            }
            if (effect.Kind == CombatEventKind.Damage && effect.DamageClass == DamageClass.Unknown)
                Issues.Add($"Unknown damage class at sequence {effect.Sequence}.");
            _events.Add(effect.Sequence, effect);
        }

        internal Encounter Snapshot(EncounterOutcome outcome = EncounterOutcome.InProgress)
        {
            var ordered = _events.OrderBy(pair => pair.Key).Select(pair => pair.Value).ToArray();
            var issues = Issues.ToList();
            if (ordered.Select((effect, index) => effect.Sequence != index + 1L).Any(missing => missing))
                issues.Add("Missing event sequence(s).");
            return new Encounter(start.EncounterId,
                $"Command battle {start.At:HH:mm:ss} · {outcome}",
                start.At, outcome, (outcome is EncounterOutcome.Victory or
                EncounterOutcome.Escape or EncounterOutcome.Defeat) && issues.Count == 0,
                start.Actors.ToArray(), ordered, issues);
        }
    }
}
