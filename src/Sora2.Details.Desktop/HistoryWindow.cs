using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public sealed class HistoryWindow : Window
{
    private sealed record HistoryItem(Encounter Encounter, string Display);
    private readonly ListBox _list;
    public Encounter? SelectedEncounter => (_list.SelectedItem as HistoryItem)?.Encounter;

    public static string Describe(Encounter encounter)
    {
        var quality = encounter.IsComplete ? "" : " · PARTIAL";
        return $"{encounter.StartedAt.ToLocalTime():g} · {encounter.Outcome}{quality} · {encounter.Label}";
    }

    public HistoryWindow(IReadOnlyList<Encounter> encounters)
    {
        Title = "All encounters";
        Width = 480;
        Height = 400;
        Background = new SolidColorBrush(Color.FromRgb(27, 30, 35));
        Foreground = Brushes.White;
        var panel = new DockPanel { Margin = new Thickness(14) };
        var open = new Button { Content = "Open encounter", Margin = new Thickness(0, 10, 0, 0), Padding = new Thickness(8) };
        DockPanel.SetDock(open, Dock.Bottom);
        open.Click += (_, _) => OpenSelection();
        panel.Children.Add(open);
        _list = new ListBox
        {
            DisplayMemberPath = nameof(HistoryItem.Display),
            Background = new SolidColorBrush(Color.FromRgb(38, 42, 49)),
            Foreground = Brushes.White,
            BorderThickness = new Thickness(0)
        };
        _list.ItemsSource = encounters.OrderByDescending(encounter => encounter.StartedAt)
            .Select(encounter => new HistoryItem(encounter, Describe(encounter))).ToArray();
        _list.MouseDoubleClick += (_, _) => OpenSelection();
        panel.Children.Add(_list);
        Content = panel;
    }

    private void OpenSelection()
    {
        if (SelectedEncounter is not null) DialogResult = true;
    }
}
