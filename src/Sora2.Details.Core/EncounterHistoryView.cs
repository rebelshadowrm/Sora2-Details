namespace Sora2.Details.Core;

public enum BossClassification
{
    Unclassified,
    MarkedBoss,
    CatalogBossCandidate,
    PlusMiniBossCandidate,
    MarkedRegular
}

public static class EncounterHistoryView
{
    // Exact names occur in the hash-checked English t_status table and in the
    // linked Sky SC boss roster. This positive list is not complete for the remake.
    private static readonly HashSet<string> BossNames = new(StringComparer.OrdinalIgnoreCase)
    {
        "Bleublanc", "Walter", "Luciola", "Renne", "Loewe", "Weissmann",
        "Angel Weissmann", "Pater-Mater", "Gilbert", "New Gilbert",
        "Grant", "Anelace"
    };

    public static BossClassification Classify(Encounter encounter,
        IReadOnlySet<string> bossIds, IReadOnlySet<string> regularIds)
    {
        if (bossIds.Contains(encounter.Id)) return BossClassification.MarkedBoss;
        if (regularIds.Contains(encounter.Id)) return BossClassification.MarkedRegular;
        var enemies = encounter.Actors.Where(actor => actor.Team == CombatTeam.Enemy).ToArray();
        if (enemies.Any(actor => BossNames.Contains(actor.Name)))
            return BossClassification.CatalogBossCandidate;
        if (enemies.Any(actor => actor.Name.Contains('+')))
            return BossClassification.PlusMiniBossCandidate;
        return BossClassification.Unclassified;
    }

    public static IReadOnlyList<Encounter> Visible(IEnumerable<Encounter> encounters,
        bool bossFocused, IReadOnlySet<string> bossIds, IReadOnlySet<string> regularIds) =>
        encounters.Where(encounter => !bossFocused ||
            Classify(encounter, bossIds, regularIds) != BossClassification.MarkedRegular)
            .OrderByDescending(encounter => encounter.StartedAt).ToArray();

    public static string EnemySummary(Encounter encounter)
    {
        var enemies = encounter.Actors.Where(actor => actor.Team == CombatTeam.Enemy).ToArray();
        if (enemies.Length == 0) return "Enemy not observed";
        var named = enemies.Where(actor => !string.IsNullOrWhiteSpace(actor.Name) &&
                                           !actor.Name.StartsWith("? Enemy", StringComparison.Ordinal))
            .GroupBy(actor => actor.Name, StringComparer.Ordinal)
            .Select(group => group.Count() == 1 ? group.Key : $"{group.Key} ×{group.Count()}")
            .ToArray();
        var unknown = enemies.Length - enemies.Count(actor =>
            !string.IsNullOrWhiteSpace(actor.Name) &&
            !actor.Name.StartsWith("? Enemy", StringComparison.Ordinal));
        return string.Join(", ", named.Concat(unknown == 0 ? [] :
            [unknown == 1 ? "Unknown enemy" : $"Unknown enemies ×{unknown}"]));
    }

    public static string Describe(Encounter encounter, BossClassification classification)
    {
        var marker = classification switch
        {
            BossClassification.MarkedBoss => "★ BOSS · ",
            BossClassification.CatalogBossCandidate => "★ Boss candidate · ",
            BossClassification.PlusMiniBossCandidate => "✦ Mini-boss candidate · ",
            BossClassification.Unclassified => "? Unclassified · ",
            _ => "Regular · "
        };
        var quality = encounter.IsComplete ? "" : " · PARTIAL";
        return $"{marker}{encounter.StartedAt.ToLocalTime():g} · {EnemySummary(encounter)} · " +
            $"{encounter.Outcome}{quality}";
    }
}
