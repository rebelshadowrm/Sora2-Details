namespace Sora2.Details.Core;

public static class EncounterProjection
{
    public static IReadOnlyList<MeterRow> Rows(Encounter encounter, MeterMode mode)
    {
        var actors = encounter.Actors.ToDictionary(actor => actor.Id);
        var totals = new Dictionary<string, int>();
        foreach (var effect in encounter.Events)
        {
            if (!actors.TryGetValue(effect.TargetId, out var target)) continue;
            var source = effect.SourceId is not null && actors.TryGetValue(effect.SourceId, out var found)
                ? found : null;
            string? key = mode switch
            {
                MeterMode.Damage when effect.Kind == CombatEventKind.Damage && target.Team == CombatTeam.Enemy
                    && source?.Team == CombatTeam.Party => source.Id,
                MeterMode.Damage when effect.Kind == CombatEventKind.Damage && target.Team == CombatTeam.Enemy
                    && source is null => "unknown",
                MeterMode.Healing when effect.Kind == CombatEventKind.Healing && target.Team == CombatTeam.Party
                    => source?.Id ?? "unknown",
                MeterMode.Taken when effect.Kind == CombatEventKind.Damage && target.Team == CombatTeam.Party
                    => source?.Team == CombatTeam.Enemy ? source.Id : "other",
                MeterMode.Deaths when effect.Kind == CombatEventKind.Knockout && target.Team == CombatTeam.Party
                    => target.Id,
                _ => null
            };
            if (key is null) continue;
            var amount = mode == MeterMode.Deaths ? 1 : effect.EffectiveAmount ?? 0;
            totals[key] = totals.GetValueOrDefault(key) + amount;
        }

        var sum = totals.Values.Sum();
        return totals.Select(pair => new MeterRow(
                pair.Key,
                actors.TryGetValue(pair.Key, out var actor) ? actor.Name : pair.Key == "other" ? "Other / unknown source" : "Unknown source",
                pair.Value,
                sum == 0 ? 0 : (double)pair.Value / sum))
            .OrderByDescending(row => row.Value)
            .ThenBy(row => row.Name)
            .ToArray();
    }

    public static IReadOnlyList<MoveRow> Moves(Encounter encounter, MeterMode mode, string rowKey)
        => MoveGroups(encounter, mode, rowKey)
            .Select(group => new MoveRow(group.Name, group.Value, group.DamageClass)).ToArray();

    public static IReadOnlyList<MoveGroup> MoveGroups(Encounter encounter, MeterMode mode, string rowKey)
    {
        var results = ResultsForRow(encounter, mode, rowKey);
        var named = results.Where(effect => !string.IsNullOrWhiteSpace(effect.MoveName))
            .GroupBy(effect => (effect.MoveName!, effect.DamageClass))
            .Select(group => new MoveGroup($"named:{group.Key.Item1.Length}:{group.Key.Item1}:{group.Key.DamageClass}",
                group.Key.Item1, group.Sum(effect => effect.EffectiveAmount ?? 0), group.Key.DamageClass,
                group.OrderBy(effect => effect.Sequence).ToArray()))
            .ToArray();
        var unnamed = results.Where(effect => string.IsNullOrWhiteSpace(effect.MoveName))
            .Select(effect => new MoveGroup($"result:{effect.Sequence}", $"Move unknown · result #{effect.Sequence}",
                effect.EffectiveAmount ?? 0, effect.DamageClass, [effect]));
        return named.Concat(unnamed)
            .OrderByDescending(row => row.Value)
            .ThenBy(row => row.Name)
            .ToArray();
    }

    // Preserve each observed result when move identity is unavailable. Grouping
    // all unknown moves by damage class would make several Crafts look like one.
    public static IReadOnlyList<CombatEvent> ResultsForRow(Encounter encounter, MeterMode mode, string rowKey)
    {
        var actors = encounter.Actors.ToDictionary(actor => actor.Id);
        var selected = encounter.Events.Where(effect =>
        {
            if (!actors.TryGetValue(effect.TargetId, out var target)) return false;
            var source = effect.SourceId is not null && actors.TryGetValue(effect.SourceId, out var found) ? found : null;
            return mode switch
            {
                MeterMode.Damage => effect.Kind == CombatEventKind.Damage && target.Team == CombatTeam.Enemy
                    && (source?.Team == CombatTeam.Party ? source.Id : source is null ? "unknown" : null) == rowKey,
                MeterMode.Healing => effect.Kind == CombatEventKind.Healing && target.Team == CombatTeam.Party && (source?.Id ?? "unknown") == rowKey,
                MeterMode.Taken => effect.Kind == CombatEventKind.Damage && target.Team == CombatTeam.Party && (source?.Team == CombatTeam.Enemy ? source.Id : "other") == rowKey,
                _ => false
            };
        });
        return selected.OrderBy(effect => effect.Sequence)
            .ToArray();
    }

    public static IReadOnlyList<CombatEvent> RecentTimeline(Encounter encounter, int count = 20) =>
        encounter.Events.OrderBy(effect => effect.Sequence).TakeLast(count).ToArray();

    public static IReadOnlyList<CombatEvent> DeathRecap(Encounter encounter, long knockoutSequence, int preceding = 10)
    {
        var ordered = encounter.Events.OrderBy(effect => effect.Sequence).ToArray();
        var deathIndex = Array.FindIndex(ordered, effect => effect.Sequence == knockoutSequence && effect.Kind == CombatEventKind.Knockout);
        if (deathIndex < 0) return [];
        var victim = ordered[deathIndex].TargetId;
        return ordered.Take(deathIndex).Where(effect => effect.TargetId == victim)
            .TakeLast(preceding).Append(ordered[deathIndex]).ToArray();
    }

    public static IReadOnlyList<Encounter> Recent(IReadOnlyList<Encounter> encounters, int count = 10) =>
        encounters.Where(encounter => encounter.Outcome != EncounterOutcome.InProgress)
            .OrderByDescending(encounter => encounter.StartedAt).Take(count).ToArray();
}
