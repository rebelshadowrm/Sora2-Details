using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public sealed record MeterDisplayRow(
    string Key,
    string RankLabel,
    string Name,
    string Initial,
    string ValueLabel,
    string Tooltip,
    double BarPercent,
    Brush BarBrush,
    Brush AvatarBrush)
{
    public MeterPreview? Preview { get; init; }
    public object HoverContent => (object?)Preview ?? Tooltip;
    public Brush InitialBrush { get; init; } = Brushes.White;
    public ImageSource? IconSource { get; init; }

    private static readonly string[] BarColors =
    [
        "#575528", "#87432D", "#725C20", "#774A26", "#423D72", "#5E306D", "#436038", "#586A27"
    ];

    internal static MeterDisplayRow From(MeterRow row, int index, int maximum, MeterMode mode,
        CharacterTheme? theme = null)
    {
        var color = theme?.Bar ?? (Brush)new BrushConverter().ConvertFromString(BarColors[index % BarColors.Length])!;
        var label = mode == MeterMode.Deaths
            ? $"{row.Value} ({row.Share:P0})"
            : $"{FormatAmount(row.Value)} ({row.Share:P0})";
        return new MeterDisplayRow(
            row.Key,
            $"{index + 1}.",
            row.Name,
            string.IsNullOrEmpty(row.Name) ? "?" : row.Name[..1].ToUpperInvariant(),
            label,
            $"{row.Name}: {row.Value:N0} ({row.Share:P1})",
            maximum == 0 ? 0 : 100.0 * row.Value / maximum,
            color,
            theme?.Avatar ?? color)
        {
            InitialBrush = theme?.Initial ?? Brushes.White,
            IconSource = theme?.Portrait
        };
    }

    internal static MeterDisplayRow Breakdown(string key, string name, int value, int index,
        int maximum, string tooltip, MeterPreview? preview = null, CharacterTheme? theme = null,
        ImageSource? icon = null)
    {
        var color = theme?.Bar ?? (Brush)new BrushConverter().ConvertFromString(BarColors[index % BarColors.Length])!;
        return new MeterDisplayRow(key, $"{index + 1}.", name,
            string.IsNullOrEmpty(name) ? "?" : name[..1].ToUpperInvariant(),
            FormatAmount(value), tooltip, maximum == 0 ? 0 : 100.0 * value / maximum,
            color, theme?.Avatar ?? color)
        {
            Preview = preview,
            InitialBrush = theme?.Initial ?? Brushes.White,
            IconSource = icon ?? theme?.Portrait
        };
    }

    private static string FormatAmount(int value) => value switch
    {
        >= 1_000_000 => $"{value / 1_000_000.0:0.##}M",
        >= 10_000 => $"{value / 1_000.0:0.#}K",
        _ => value.ToString("N0")
    };
}

public sealed record MeterPreview(string Title, IReadOnlyList<MeterDisplayRow> Rows);
