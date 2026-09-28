using System.IO;
using System.Text.Json;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

internal static class SkillIcons
{
    private const string TablePayloadSha256 =
        "ae81526bef7e1dedc601145961a0786df48fb1b2c96407d4571e1f3bae3bfe8a";
    private static readonly IReadOnlyDictionary<string, string> Kinds = LoadKinds();
    private static readonly Dictionary<string, ImageSource?> Images = new(StringComparer.Ordinal);

    public static ImageSource? For(MoveGroup group)
    {
        string? selectedKind = null;
        foreach (var hit in group.Hits)
        {
            if (hit.MoveId is null || !Kinds.TryGetValue(hit.MoveId, out var kind)) return null;
            if (selectedKind is not null && selectedKind != kind) return null;
            selectedKind = kind;
        }
        if (selectedKind is null) return null;
        if (Images.TryGetValue(selectedKind, out var cached)) return cached;
        var path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Sora2 Details", "icons", selectedKind + ".png");
        if (!File.Exists(path)) return Images[selectedKind] = null;
        try
        {
            var bitmap = new BitmapImage();
            bitmap.BeginInit();
            bitmap.CacheOption = BitmapCacheOption.OnLoad;
            bitmap.UriSource = new Uri(path);
            bitmap.EndInit();
            bitmap.Freeze();
            return Images[selectedKind] = bitmap;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or NotSupportedException)
        {
            return Images[selectedKind] = null;
        }
    }

    private static IReadOnlyDictionary<string, string> LoadKinds()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "assets", "skill-icon-map.json");
        try
        {
            using var document = JsonDocument.Parse(File.ReadAllText(path));
            var root = document.RootElement;
            if (root.GetProperty("tablePayloadSha256").GetString() != TablePayloadSha256) return Empty();
            return root.GetProperty("icons").EnumerateObject()
                .ToDictionary(property => property.Name, property => property.Value.GetString()!,
                    StringComparer.OrdinalIgnoreCase);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or JsonException or KeyNotFoundException)
        {
            return Empty();
        }
    }

    private static IReadOnlyDictionary<string, string> Empty() =>
        new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
}
