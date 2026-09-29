using System.IO;
using System.Text.Json;

namespace Sora2.Details.Desktop;

internal sealed class EncounterHistorySettings
{
    public bool BossFocused { get; set; }
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
            var settings = JsonSerializer.Deserialize<EncounterHistorySettings>(File.ReadAllText(PathName));
            return settings is { BossEncounterIds: not null, RegularEncounterIds: not null }
                ? settings : new();
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
