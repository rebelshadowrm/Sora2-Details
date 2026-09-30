namespace Sora2.Details.Core;

public enum BossClassification
{
    Unclassified,
    MarkedBoss,
    CatalogBossCandidate,
    PlusMiniBossCandidate,
    MarkedRegular
}

public enum HistoryFilterMode
{
    LikelyBosses,
    Confirmed,
    Unfiltered
}

public static class EncounterHistoryView
{
    // These exact English-table names are actor-name candidates only. The
    // current-remake guides and the older SC roster give us useful leads, but
    // only a player's manual Boss mark confirms a fight.
    private static readonly HashSet<string> BossNames = new(StringComparer.OrdinalIgnoreCase)
    {
        "Bleublanc", "Walter", "Luciola", "Renne", "Loewe", "Weissmann",
        "Angel Weissmann", "Pater-Mater", "Gilbert", "New Gilbert",
        "Grant", "Anelace", "Jaeger", "Female Jaeger", "Deen", "Rais",
        "Rocco", "Kurt", "Jabbabba King", "Hapilsag", "Ash Saber", "Storm Bringer",
        "Divine Pengu", "Major Vander", "Master Cryon", "Armored Hydra", "Ragnard"
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

    // Fail open: hide a fight only when the player explicitly marked it Regular.
    public static IReadOnlyList<Encounter> Visible(IEnumerable<Encounter> encounters,
        HistoryFilterMode mode, IReadOnlySet<string> bossIds, IReadOnlySet<string> regularIds) =>
        encounters.Where(encounter => IsVisible(encounter, mode, bossIds, regularIds))
            .OrderByDescending(encounter => encounter.StartedAt).ToArray();

    // Compatibility for callers that used the former two-mode setting.
    public static IReadOnlyList<Encounter> Visible(IEnumerable<Encounter> encounters,
        bool bossFocused, IReadOnlySet<string> bossIds, IReadOnlySet<string> regularIds) =>
        Visible(encounters, bossFocused ? HistoryFilterMode.Confirmed : HistoryFilterMode.Unfiltered,
            bossIds, regularIds);

    private static bool IsVisible(Encounter encounter, HistoryFilterMode mode,
        IReadOnlySet<string> bossIds, IReadOnlySet<string> regularIds)
    {
        var classification = Classify(encounter, bossIds, regularIds);
        return mode switch
        {
            // Aggressive best effort: show name-list and '+' candidates, plus
            // explicit Boss marks. Hide unknowns and explicit Regular marks.
            HistoryFilterMode.LikelyBosses => classification is BossClassification.MarkedBoss or
                BossClassification.CatalogBossCandidate or BossClassification.PlusMiniBossCandidate,
            // Fail positive: only explicit Regular marks are hidden. Unknown
            // and tentative fights stay visible for review.
            HistoryFilterMode.Confirmed => classification != BossClassification.MarkedRegular,
            HistoryFilterMode.Unfiltered => true,
            _ => true
        };
    }

    public static string FilterModeLabel(HistoryFilterMode mode) => mode switch
    {
        HistoryFilterMode.LikelyBosses => "Likely bosses (best effort)",
        HistoryFilterMode.Confirmed => "Confirmed (fail-open)",
        _ => "Unfiltered"
    };

    public static string EnemySummary(Encounter encounter) =>
        FormatEnemySummary(encounter.Actors.Where(actor => actor.Team == CombatTeam.Enemy).ToArray());

    public static string EnemySummary(Encounter encounter, BossClassification classification)
    {
        var enemies = encounter.Actors.Where(actor => actor.Team == CombatTeam.Enemy).ToArray();
        if (classification == BossClassification.MarkedBoss)
        {
            // A manual encounter mark confirms the fight. When a known boss
            // actor is present, name it without its regular adds.
            var knownBosses = enemies.Where(actor => BossNames.Contains(actor.Name)).ToArray();
            if (knownBosses.Length > 0) return FormatEnemySummary(knownBosses);

            // A single enemy is identifiable from the encounter-level mark.
            if (enemies.Length == 1) return FormatEnemySummary(enemies);
        }
        if (classification is BossClassification.PlusMiniBossCandidate or BossClassification.MarkedBoss)
        {
            // A '+' variant has an explicit name in the game's enemy label.
            var plusEnemies = enemies.Where(actor => actor.Name.Contains('+')).ToArray();
            if (plusEnemies.Length > 0) return FormatEnemySummary(plusEnemies);
        }

        // Tentative boss candidates and unclassified/Regular fights keep the
        // full observed pack so the entry does not imply an unverified target.
        return FormatEnemySummary(enemies);
    }

    private static string FormatEnemySummary(IReadOnlyList<Actor> enemies)
    {
        if (enemies.Count == 0) return "Enemy not observed";
        var named = enemies.Where(actor => !string.IsNullOrWhiteSpace(actor.Name) &&
                                           !actor.Name.StartsWith("? Enemy", StringComparison.Ordinal))
            .GroupBy(actor => actor.Name, StringComparer.Ordinal)
            .Select(group => group.Count() == 1 ? group.Key : $"{group.Key} ×{group.Count()}")
            .ToArray();
        var unknown = enemies.Count - enemies.Count(actor =>
            !string.IsNullOrWhiteSpace(actor.Name) &&
            !actor.Name.StartsWith("? Enemy", StringComparison.Ordinal));
        return string.Join(", ", named.Concat(unknown == 0 ? [] :
            [unknown == 1 ? "Unknown enemy" : $"Unknown enemies ×{unknown}"]));
    }

    public static string ClassificationMarker(BossClassification classification) => classification switch
    {
        BossClassification.MarkedBoss => "✓ CONFIRMED BOSS · ",
        BossClassification.CatalogBossCandidate => "? TENTATIVE BOSS · ",
        BossClassification.PlusMiniBossCandidate => "? TENTATIVE + MOB · ",
        BossClassification.Unclassified => "? UNCLASSIFIED · ",
        _ => "REGULAR · "
    };

    public static string Describe(Encounter encounter, BossClassification classification)
    {
        var quality = encounter.IsComplete ? "" : " · PARTIAL";
        return $"{ClassificationMarker(classification)}{encounter.StartedAt.ToLocalTime():g} · " +
            $"{EnemySummary(encounter, classification)} · " +
            $"{encounter.Outcome}{quality}";
    }
}
