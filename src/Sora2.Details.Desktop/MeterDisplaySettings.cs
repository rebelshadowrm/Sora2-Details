using System.IO;
using System.Text.Json;

namespace Sora2.Details.Desktop;

internal sealed record MeterDisplaySettings(
    bool LockPosition = false,
    bool AlwaysOnTop = true,
    double Opacity = 1,
    int FontSize = 12)
{
    public bool ClickThrough { get; init; }
    public bool CloseToTray { get; init; } = true;

    private static string PathName => Path.Combine(MeterDataDirectory.PathName, "meter-display.json");

    public static MeterDisplaySettings Load()
    {
        try
        {
            if (!File.Exists(PathName)) return new();
            var value = JsonSerializer.Deserialize<MeterDisplaySettings>(File.ReadAllText(PathName));
            return value is not null && value.IsValid() ? value : new();
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException)
        {
            return new();
        }
    }

    public void Save()
    {
        if (!IsValid()) return;
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

    private bool IsValid() => double.IsFinite(Opacity) && Opacity is >= 0.55 and <= 1 &&
        FontSize is >= 10 and <= 16;
}
