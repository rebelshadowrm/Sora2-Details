using System.IO;
using System.Text.Json;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

internal sealed class EncounterHistorySettings
{
    public HistoryFilterMode FilterMode { get; set; } = HistoryFilterMode.Confirmed;
    public HashSet<string> BossEncounterIds { get; set; } = [];
    public HashSet<string> RegularEncounterIds { get; set; } = [];

    private static string PathName => Path.Combine(MeterDataDirectory.PathName, "encounter-history.json");

    public void MarkBoss(string encounterId)
    {
        RegularEncounterIds.Remove(encounterId);
        BossEncounterIds.Add(encounterId);
    }

    public void MarkRegular(string encounterId)
    {
        BossEncounterIds.Remove(encounterId);
        RegularEncounterIds.Add(encounterId);
    }

    public void ClearMark(string encounterId)
    {
        BossEncounterIds.Remove(encounterId);
        RegularEncounterIds.Remove(encounterId);
    }

    public static EncounterHistorySettings Load()
    {
        try
        {
            if (!File.Exists(PathName)) return new();
            var json = File.ReadAllText(PathName);
            var settings = JsonSerializer.Deserialize<EncounterHistorySettings>(json);
            if (settings is not { BossEncounterIds: not null, RegularEncounterIds: not null }) return new();

            using var document = JsonDocument.Parse(json);
            var root = document.RootElement;
            if (!root.TryGetProperty(nameof(FilterMode), out _) &&
                root.TryGetProperty("BossFocused", out var legacyBossFocused) &&
                legacyBossFocused.ValueKind is JsonValueKind.True or JsonValueKind.False)
            {
                settings.FilterMode = legacyBossFocused.GetBoolean()
                    ? HistoryFilterMode.Confirmed : HistoryFilterMode.Unfiltered;
            }
            if (!Enum.IsDefined(typeof(HistoryFilterMode), settings.FilterMode))
                settings.FilterMode = HistoryFilterMode.Confirmed;
            return settings;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException)
        {
            return new();
        }
    }

    public void Save()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(PathName)!);
        var temporary = PathName + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            File.WriteAllText(temporary, JsonSerializer.Serialize(this));
            File.Move(temporary, PathName, overwrite: true);
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }
}
