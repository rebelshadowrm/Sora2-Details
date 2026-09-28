using System.IO;
using System.Text.Json;
using System.Windows;

namespace Sora2.Details.Desktop;

internal sealed record MeterWindowPlacement(double Left, double Top, double Width, double Height)
{
    private static readonly string SettingsPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Sora2 Details", "meter-window.json");

    public static MeterWindowPlacement? Load()
    {
        try
        {
            if (!File.Exists(SettingsPath)) return null;
            var placement = JsonSerializer.Deserialize<MeterWindowPlacement>(File.ReadAllText(SettingsPath));
            return placement is not null && placement.IsValid() ? placement.FitToDesktop() : null;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException)
        {
            return null;
        }
    }

    public static void Save(Rect bounds)
    {
        var placement = new MeterWindowPlacement(bounds.Left, bounds.Top, bounds.Width, bounds.Height);
        if (!placement.IsValid()) return;

        Directory.CreateDirectory(Path.GetDirectoryName(SettingsPath)!);
        var temporaryPath = SettingsPath + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            File.WriteAllText(temporaryPath, JsonSerializer.Serialize(placement));
            File.Move(temporaryPath, SettingsPath, overwrite: true);
        }
        finally
        {
            if (File.Exists(temporaryPath)) File.Delete(temporaryPath);
        }
    }

    private bool IsValid() =>
        double.IsFinite(Left) && double.IsFinite(Top) &&
        double.IsFinite(Width) && double.IsFinite(Height) &&
        Width >= 300 && Height >= 170 && Width <= 10000 && Height <= 10000;

    private MeterWindowPlacement FitToDesktop()
    {
        var desktop = new Rect(SystemParameters.VirtualScreenLeft, SystemParameters.VirtualScreenTop,
            SystemParameters.VirtualScreenWidth, SystemParameters.VirtualScreenHeight);
        var visible = Rect.Intersect(desktop, new Rect(Left, Top, Width, Height));
        if (!visible.IsEmpty && visible.Width >= 40 && visible.Height >= 40) return this;

        var workArea = SystemParameters.WorkArea;
        var width = Math.Min(Width, workArea.Width);
        var height = Math.Min(Height, workArea.Height);
        return this with
        {
            Left = workArea.Left + (workArea.Width - width) / 2,
            Top = workArea.Top + (workArea.Height - height) / 2,
            Width = width,
            Height = height
        };
    }
}
