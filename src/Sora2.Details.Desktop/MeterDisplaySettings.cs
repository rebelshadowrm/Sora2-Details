using System.IO;
using System.Text.Json;

namespace Sora2.Details.Desktop;

internal enum CloseWindowChoice
{
    HideToTray,
    Exit
}

internal sealed record MeterDisplaySettings(
    bool LockPosition = false,
    bool AlwaysOnTop = true,
    double Opacity = 1,
    int FontSize = 12)
{
    internal const double MinimumOpacity = 0.6;
    internal const double MaximumOpacity = 1;

    public bool ClickThrough { get; init; }
    public CloseWindowChoice? RememberedCloseChoice { get; init; }

    private static string PathName => Path.Combine(MeterDataDirectory.PathName, "meter-display.json");

    public static MeterDisplaySettings Load()
    {
        try
        {
            if (!File.Exists(PathName)) return new();
            var value = JsonSerializer.Deserialize<MeterDisplaySettings>(File.ReadAllText(PathName));
            if (value is null || !value.IsValid()) return new();
            return value with { Opacity = Math.Clamp(value.Opacity, MinimumOpacity, MaximumOpacity) };
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
        FontSize is >= 10 and <= 16 &&
        (RememberedCloseChoice is null || Enum.IsDefined(typeof(CloseWindowChoice), RememberedCloseChoice.Value));
}
