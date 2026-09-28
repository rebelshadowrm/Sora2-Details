using System.IO;
using System.Windows;
using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public partial class TimelineWindow : Window
{
    private readonly string _placementFile;
    private static readonly Brush DamageBrush = Brush("#F28B82");
    private static readonly Brush HealingBrush = Brush("#8ED49B");
    private static readonly Brush NeutralBrush = Brush("#C7CCD3");
    private static readonly Brush PhysicalBrush = Brush("#FFAA60");
    private static readonly Brush ArtsBrush = Brush("#7FC5FF");
    private static readonly Brush PhysicalBackground = Brush("#573820");
    private static readonly Brush ArtsBackground = Brush("#233F59");
    private static readonly Brush HealingBackground = Brush("#28513A");
    private static readonly Brush NeutralBackground = Brush("#3B4149");

    public TimelineWindow(Encounter encounter, long? knockoutSequence = null)
    {
        InitializeComponent();
        _placementFile = knockoutSequence is null ? "combat-log-window.json" : "death-recap-window.json";
        Title = knockoutSequence is null ? $"Combat log — {encounter.Label}" : $"Death recap — {encounter.Label}";
        if (WindowPlacement.Load(_placementFile) is { } placement)
        {
            WindowStartupLocation = WindowStartupLocation.Manual;
            Left = placement.Left;
            Top = placement.Top;
            Width = placement.Width;
            Height = placement.Height;
        }
        Closing += (_, _) => SavePlacement();

        var events = knockoutSequence is { } sequence
            ? EncounterProjection.DeathRecap(encounter, sequence)
            : EncounterProjection.FullTimeline(encounter);
        var actors = encounter.Actors.ToDictionary(actor => actor.Id);
        Heading.Text = knockoutSequence is null
            ? $"Full recorded combat log · {events.Count:N0} entries"
            : $"Death recap · {events.Count:N0} entries";
        Coverage.Text = encounter.IsComplete
            ? "Recorded encounter events in order"
            : "PARTIAL CAPTURE · Missing actions and effects may not appear";
        Coverage.ToolTip = encounter.Issues is { Count: > 0 }
            ? string.Join(Environment.NewLine, encounter.Issues) : null;
        Entries.ItemsSource = events.Select(effect => Format(effect, actors)).ToArray();
    }

    private void SavePlacement()
    {
        var bounds = WindowState == WindowState.Normal
            ? new Rect(Left, Top, ActualWidth, ActualHeight)
            : RestoreBounds;
        try { WindowPlacement.Save(_placementFile, bounds); }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            // Window preferences are optional.
        }
    }

    private static TimelineEntry Format(CombatEvent effect, IReadOnlyDictionary<string, Actor> actors)
    {
        var source = effect.SourceId is not null && actors.TryGetValue(effect.SourceId, out var actor)
            ? actor.Name : "Unknown source";
        var target = actors.TryGetValue(effect.TargetId, out var victim) ? victim.Name : effect.TargetId;
        var move = effect.MoveName ?? (effect.Kind == CombatEventKind.Damage ? "Move unknown" : effect.Kind.ToString());
        var color = effect.Kind switch
        {
            CombatEventKind.Damage or CombatEventKind.Knockout => DamageBrush,
            CombatEventKind.Healing or CombatEventKind.Revival => HealingBrush,
            _ => NeutralBrush
        };
        var badge = effect.Kind switch
        {
            CombatEventKind.Damage when effect.DamageClass == DamageClass.Physical => "⚔",
            CombatEventKind.Damage when effect.DamageClass == DamageClass.Arts => "✦",
            CombatEventKind.Damage => "?",
            CombatEventKind.Healing => "+",
            CombatEventKind.Knockout => "×",
            CombatEventKind.Revival => "+",
            _ => "·"
        };
        var badgeForeground = effect.Kind switch
        {
            CombatEventKind.Damage when effect.DamageClass == DamageClass.Physical => PhysicalBrush,
            CombatEventKind.Damage when effect.DamageClass == DamageClass.Arts => ArtsBrush,
            _ => color
        };
        var badgeBackground = effect.Kind switch
        {
            CombatEventKind.Damage when effect.DamageClass == DamageClass.Physical => PhysicalBackground,
            CombatEventKind.Damage when effect.DamageClass == DamageClass.Arts => ArtsBackground,
            CombatEventKind.Healing or CombatEventKind.Revival => HealingBackground,
            _ => NeutralBackground
        };
        var amounts = DamageAmounts.From(effect);
        var details = new List<string> { $"#{effect.Sequence}", effect.Kind.ToString() };
        if (effect.Kind == CombatEventKind.Damage)
            details.Add(effect.DamageClass == DamageClass.Unknown ? "type unknown" : effect.DamageClass.ToString());
        if (amounts.Total is { } total) details.Add($"total {total:N0}");
        if (amounts.Overkill is > 0) details.Add($"overkill {amounts.Overkill:N0}");
        if (effect.IsCritical == true) details.Add("CRITICAL");
        if (effect.HpBefore is { } before && effect.HpAfter is { } after)
            details.Add($"HP {before:N0} → {after:N0}");
        var amount = effect.Kind is CombatEventKind.Damage or CombatEventKind.Healing or CombatEventKind.HpLoss
            ? effect.EffectiveAmount is { } effective ? $"{effective:N0} effective" : "amount unknown"
            : "";
        var summary = $"{source} · {move} → {target}";
        var detail = string.Join(" · ", details);
        return new TimelineEntry(effect.ObservedAt.ToLocalTime().ToString("HH:mm:ss.fff"), badge,
            badgeForeground, badgeBackground, color, summary, detail, amount,
            $"{summary}\n{detail}" + (amount.Length > 0 ? $"\n{amount}" : ""));
    }

    private static Brush Brush(string hex)
    {
        var brush = (SolidColorBrush)new BrushConverter().ConvertFromString(hex)!;
        brush.Freeze();
        return brush;
    }
}

internal sealed record TimelineEntry(string Time, string Badge, Brush BadgeForeground,
    Brush BadgeBackground, Brush EventBrush, string Summary, string Details, string Amount,
    string Tooltip);
