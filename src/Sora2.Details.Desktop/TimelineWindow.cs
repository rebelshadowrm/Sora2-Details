using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public sealed class TimelineWindow : Window
{
    public TimelineWindow(Encounter encounter, long? knockoutSequence = null)
    {
        Title = knockoutSequence is null ? $"Timeline — {encounter.Label}" : $"Death recap — {encounter.Label}";
        Width = 720;
        Height = 470;
        Background = new SolidColorBrush(Color.FromRgb(27, 30, 35));
        Foreground = Brushes.White;
        var actors = encounter.Actors.ToDictionary(actor => actor.Id);
        var events = knockoutSequence is { } sequence
            ? EncounterProjection.DeathRecap(encounter, sequence)
            : EncounterProjection.RecentTimeline(encounter);
        var panel = new DockPanel { Margin = new Thickness(14) };
        var heading = new TextBlock
        {
            Text = knockoutSequence is null ? "Most recent 20 recorded effects" : "Last 10 effects on the knocked-out character",
            FontSize = 15,
            Margin = new Thickness(0, 0, 0, 10)
        };
        DockPanel.SetDock(heading, Dock.Top);
        panel.Children.Add(heading);
        var list = new ListBox
        {
            Background = new SolidColorBrush(Color.FromRgb(38, 42, 49)),
            Foreground = Brushes.White,
            BorderThickness = new Thickness(0)
        };
        list.ItemsSource = events.Select(effect =>
        {
            var source = effect.SourceId is not null && actors.TryGetValue(effect.SourceId, out var actor)
                ? actor.Name : "Unknown source";
            var target = actors.TryGetValue(effect.TargetId, out var victim) ? victim.Name : effect.TargetId;
            var amount = effect.Kind is CombatEventKind.Damage or CombatEventKind.Healing or CombatEventKind.HpLoss
                ? effect.EffectiveAmount is { } value ? $"  •  {value:N0} effective" : "  •  amount unknown"
                : "";
            var resolved = effect.ResolvedAmount is { } displayed && displayed != effect.EffectiveAmount
                ? $" (displayed {displayed:N0})" : "";
            var damageClass = effect.Kind == CombatEventKind.Damage
                ? $"  •  {(effect.DamageClass == DamageClass.Unknown ? "type unknown" : effect.DamageClass)}"
                : "";
            var critical = effect.IsCritical == true ? "  •  CRITICAL" : "";
            var hp = effect.HpBefore is { } before && effect.HpAfter is { } after ? $"  HP {before} → {after}" : "";
            return $"#{effect.Sequence}  {source}  •  {effect.MoveName ?? effect.Kind.ToString()}  →  {target}{amount}{resolved}{damageClass}{critical}{hp}";
        }).ToArray();
        panel.Children.Add(list);
        Content = panel;
    }
}
