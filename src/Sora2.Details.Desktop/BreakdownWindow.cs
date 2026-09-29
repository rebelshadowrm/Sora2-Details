using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public sealed class BreakdownWindow : Window
{
    private readonly Encounter _encounter;

    public BreakdownWindow(Encounter encounter, MeterMode mode, string rowKey)
    {
        _encounter = encounter;
        var actor = encounter.Actors.FirstOrDefault(item => item.Id == rowKey);
        Title = $"{actor?.Name ?? "Unknown source"} — {mode}";
        Width = 720;
        Height = 440;
        MinWidth = 500;
        MinHeight = 250;
        Background = new SolidColorBrush(Color.FromRgb(27, 30, 35));
        Foreground = Brushes.White;

        var panel = new DockPanel { Margin = new Thickness(14) };
        var results = mode == MeterMode.Deaths
            ? []
            : EncounterProjection.ResultsForRow(encounter, mode, rowKey);
        var showIndividualResults = results.Any(effect => string.IsNullOrWhiteSpace(effect.MoveName));
        var heading = new TextBlock
        {
            Text = mode == MeterMode.Deaths ? "Knockouts — double-click for recap"
                : showIndividualResults ? "Recorded results in order" : "Move breakdown",
            FontSize = 16,
            FontWeight = FontWeights.SemiBold,
            Margin = new Thickness(0, 0, 0, 12)
        };
        DockPanel.SetDock(heading, Dock.Top);
        panel.Children.Add(heading);

        if (showIndividualResults)
        {
            var note = new TextBlock
            {
                Text = "Move IDs are not captured yet. Each line is one hit, not one move.",
                Foreground = Brushes.LightGray,
                TextWrapping = TextWrapping.Wrap,
                Margin = new Thickness(0, 0, 0, 10)
            };
            DockPanel.SetDock(note, Dock.Top);
            panel.Children.Add(note);
        }

        var list = new ListBox
        {
            Background = new SolidColorBrush(Color.FromRgb(38, 42, 49)),
            Foreground = Brushes.White,
            BorderThickness = new Thickness(0)
        };
        if (mode == MeterMode.Deaths)
        {
            list.ItemsSource = encounter.Events
                .Where(effect => effect.Kind == CombatEventKind.Knockout && effect.TargetId == rowKey)
                .OrderBy(effect => effect.Sequence)
                .Select(effect => new DeathChoice(effect.Sequence, $"Event #{effect.Sequence}  •  {effect.MoveName ?? "Unknown cause"}"))
                .ToArray();
            list.MouseDoubleClick += (_, _) =>
            {
                if (list.SelectedItem is DeathChoice death)
                    new TimelineWindow(_encounter, death.Sequence) { Owner = this }.ShowDialog();
            };
        }
        else
        {
            if (showIndividualResults)
            {
                var actors = encounter.Actors.ToDictionary(item => item.Id);
                list.ItemsSource = results.Select(effect =>
                {
                    var target = actors.TryGetValue(effect.TargetId, out var victim)
                        ? victim.Name : effect.TargetId;
                    var amount = effect.EffectiveAmount is { } value ? $"{value:N0} effective" : "amount unknown";
                    var damageClass = effect.Kind == CombatEventKind.Damage
                        ? effect.DamageClass == DamageClass.Unknown ? "type unknown" : effect.DamageClass.ToString()
                        : effect.Kind.ToString();
                    var label = $"#{effect.Sequence}  {effect.ObservedAt.ToLocalTime():HH:mm:ss.fff}  " +
                        $"{effect.MoveName ?? "Move unknown"} → {target}  •  {amount}  •  {damageClass}";
                    var raw = effect.RawResultFlags is { } flags ? $"Raw result flags: 0x{flags:X}" : "Raw result flags unavailable";
                    var effectKey = effect.RawEffectId is { } id
                        ? $"Raw effect ID: {id}" + (effect.RawEffectCode is { } code ? $"; code: 0x{code:X}" : "")
                        : "Raw effect ID unavailable";
                    var hp = effect.HpBefore is { } before && effect.HpAfter is { } after
                        ? $"HP {before:N0} → {after:N0}" : "HP trail unavailable";
                    var critical = effect.IsCritical is null ? "Critical: unverified"
                        : $"Critical: {(effect.IsCritical.Value ? "yes" : "no")}";
                    var context = effect.RawSourceContextFlags is { } contextFlags
                        ? $"Source context +0x30: 0x{contextFlags:X}" : "Source context unavailable";
                    var targetStatus = effect.RawTargetStatus7C is { } status7C
                        ? $"Target status +0x7C: 0x{status7C:X}" : "Target status +0x7C unavailable";
                    var lookup = effect.MoveLookupReason is { } reason ? $"\nMove lookup: {reason}" : "";
                    return new ListBoxItem { Content = label, ToolTip = $"{critical}\n{context}\n{targetStatus}\n{raw}\n{effectKey}\n{hp}{lookup}" };
                }).ToArray();
            }
            else
            {
                list.ItemsSource = EncounterProjection.Moves(encounter, mode, rowKey)
                    .Select(move => $"{move.Name,-24}  {move.Value:N0}  •  {move.DamageClass}")
                    .ToArray();
            }
        }
        panel.Children.Add(list);
        Content = panel;
    }

    private sealed record DeathChoice(long Sequence, string Label)
    {
        public override string ToString() => Label;
    }
}
