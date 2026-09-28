using System.IO;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

internal sealed record CharacterTheme(Brush Bar, Brush Avatar, Brush Initial, ImageSource? Portrait);

internal static class CharacterThemes
{
    private static readonly IReadOnlyDictionary<string, (string Bar, string Avatar, string Initial)> Colors =
        new Dictionary<string, (string, string, string)>(StringComparer.OrdinalIgnoreCase)
        {
            ["Estelle"] = ("#A95D23", "#D78032", "#FFFFFF"),
            ["Joshua"] = ("#35415F", "#222A40", "#FFFFFF"),
            ["Scherazard"] = ("#873F83", "#A3549A", "#FFFFFF"),
            ["Olivier"] = ("#81796A", "#E1D8C2", "#27231E"),
            ["Kloe"] = ("#355AA0", "#5077C4", "#FFFFFF"),
            ["Agate"] = ("#932F3C", "#BE4050", "#FFFFFF"),
            ["Tita"] = ("#A54261", "#D36183", "#FFFFFF"),
            ["Zin"] = ("#8B6525", "#B99040", "#FFFFFF"),
            ["Anelace"] = ("#968332", "#D1B946", "#222017"),
            ["Kevin"] = ("#34794E", "#4EA76D", "#FFFFFF"),
            ["Josette"] = ("#61733C", "#879A50", "#FFFFFF"),
            ["Julia"] = ("#2E7980", "#51A4A7", "#FFFFFF"),
            ["Mueller"] = ("#553B79", "#74559F", "#FFFFFF")
        };

    private static readonly Dictionary<string, CharacterTheme> Cache = new(StringComparer.OrdinalIgnoreCase);

    public static CharacterTheme? For(string name, CombatTeam? team)
    {
        if (team != CombatTeam.Party || !Colors.TryGetValue(name, out var colors)) return null;
        if (Cache.TryGetValue(name, out var cached)) return cached;
        var theme = new CharacterTheme(Brush(colors.Bar), Brush(colors.Avatar), Brush(colors.Initial),
            LoadPortrait(name));
        Cache[name] = theme;
        return theme;
    }

    private static Brush Brush(string hex)
    {
        var brush = (SolidColorBrush)new BrushConverter().ConvertFromString(hex)!;
        brush.Freeze();
        return brush;
    }

    private static ImageSource? LoadPortrait(string name)
    {
        // Locally extracted AT portraits and user-supplied replacements share this path.
        var path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Sora2 Details", "portraits", name + ".png");
        if (!File.Exists(path)) return null;
        try
        {
            var bitmap = new BitmapImage();
            bitmap.BeginInit();
            bitmap.CacheOption = BitmapCacheOption.OnLoad;
            bitmap.UriSource = new Uri(path);
            bitmap.EndInit();
            bitmap.Freeze();
            return bitmap;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or NotSupportedException)
        {
            return null;
        }
    }
}
