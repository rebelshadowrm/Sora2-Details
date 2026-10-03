using System.IO;
using System.Windows;
using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public partial class TimelineWindow : Window
{
    private readonly string _placementFile;
    private readonly long? _knockoutSequence;
    internal string EncounterId { get; }
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
        EncounterId = encounter.Id;
        _knockoutSequence = knockoutSequence;
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
        RefreshEncounter(encounter);
    }

    internal void RefreshEncounter(Encounter encounter)
    {
        if (encounter.Id != EncounterId) return;
        var events = _knockoutSequence is { } sequence
            ? EncounterProjection.DeathRecap(encounter, sequence)
            : EncounterProjection.FullTimeline(encounter);
        var actors = encounter.Actors.ToDictionary(actor => actor.Id);
        Heading.Text = _knockoutSequence is null
            ? $"Full recorded combat log · {events.Count:N0} entries"
            : $"Death recap · {events.Count:N0} entries";
        Coverage.Text = encounter.IsComplete
            ? "Recorded encounter events in order"
            : "PARTIAL CAPTURE · Missing actions and effects may not appear";
        Coverage.ToolTip = encounter.Issues is { Count: > 0 }
            ? string.Join(Environment.NewLine, encounter.Issues) : null;
        Entries.ItemsSource = events.Select(effect => Format(effect, actors)).ToArray();
        Title = _knockoutSequence is null ? $"Combat log — {encounter.Label}" : $"Death recap — {encounter.Label}";
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
        var move = effect.MoveName ?? (effect.Kind switch
        {
            CombatEventKind.Damage => "Move unknown",
            CombatEventKind.ActionObserved => "Observed action effect",
            CombatEventKind.ResourceChange => $"{effect.Resource ?? "Resource"} change",
            CombatEventKind.StateWriteObserved => "Unresolved property write",
            _ => effect.Kind.ToString()
        });
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
        if (effect.Kind == CombatEventKind.ActionObserved)
        {
            details.Add($"{effect.EventStage ?? "effect-call"} observed");
            if (effect.CandidateAmount is { } candidateAmount)
                details.Add($"candidate amount {candidateAmount:N0}");
        }
        if (effect.Kind == CombatEventKind.Healing && effect.CandidateAmount is { } candidateHeal)
            details.Add($"pre-cap heal amount {candidateHeal:N0} (candidate)");
        if (effect.Resource is { } resource)
        {
            if (effect.ResourceBefore is { } resourceBefore &&
                effect.ResourceCandidateAfter is { } resourceAfter &&
                effect.ResourceMaximum is { } resourceMaximum)
                details.Add($"{resource} {resourceBefore:N0} → {resourceAfter:N0} / {resourceMaximum:N0} (calculated)");
            if (effect.ResourceCandidateDelta is { } candidateDelta)
                details.Add($"calculated change {candidateDelta.ToString("+0;-0;0")}");
            if (effect.RequestedResourceValue is { } requested)
            {
                var request = effect.ResourceOperation == "add"
                    ? requested.ToString("+0;-0;0")
                    : requested.ToString("N0");
                details.Add($"{effect.ResourceOperation ?? "set"} request {request}");
            }
        }
        if (effect.ResourceSetterCallerRva is { } callerRva)
            details.Add($"setter caller {callerRva}");
        if (effect.Kind == CombatEventKind.StateWriteObserved)
            details.Add($"raw property {effect.RawPropertyCode?.ToString() ?? "unknown"}, value {effect.RawPropertyRequestedValue?.ToString("N0") ?? "unknown"}");
        if (effect.MoveNameProvenance is { } moveProvenance)
            details.Add($"move lookup: {moveProvenance}");
        if (effect.RawEffectId is { } rawEffectId)
            details.Add($"raw effect key {rawEffectId}");
        if (effect.MoveLookupReason is { } lookupReason && effect.MoveName is null)
            details.Add($"lookup: {lookupReason}");
        if (effect.SourceId is not null && actors.TryGetValue(effect.SourceId, out var sourceActor) &&
            sourceActor.Team == CombatTeam.Enemy)
        {
            if (sourceActor.RuntimeStatusId is { } runtimeId)
                details.Add($"enemy runtime status ID {runtimeId}");
            if (sourceActor.LookupUnitId is { } unitId)
                details.Add($"enemy table key {unitId}");
            if (sourceActor.NameLookupCandidates is { Count: > 0 } candidates)
                details.Add($"enemy lookup candidates: {string.Join(", ", candidates.Select(candidate => $"{candidate.UnitId} {candidate.Name}"))}");
        }
        if (effect.HpBefore is { } before && effect.HpAfter is { } after)
            details.Add($"HP {before:N0} → {after:N0}" +
                (effect.ResourceCandidateProvenance is null ? "" : " (calculated)"));
        var amount = effect.Kind is CombatEventKind.Damage or CombatEventKind.Healing or CombatEventKind.HpLoss
            ? effect.EffectiveAmount is { } effective ? $"{effective:N0} " +
                (effect.ResourceCandidateProvenance is null ? "effective" : "calculated") : "amount unknown"
            : "";
        var summary = effect.SourceId is null &&
            (effect.Kind is CombatEventKind.ResourceChange or CombatEventKind.StateWriteObserved)
            ? $"{move} → {target}"
            : $"{source} · {move} → {target}";
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
