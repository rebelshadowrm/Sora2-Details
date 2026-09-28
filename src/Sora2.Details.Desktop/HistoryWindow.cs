using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public sealed class HistoryWindow : Window
{
    private readonly ListBox _list;
    public Encounter? SelectedEncounter => _list.SelectedItem as Encounter;

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
            DisplayMemberPath = nameof(Encounter.Label),
            Background = new SolidColorBrush(Color.FromRgb(38, 42, 49)),
            Foreground = Brushes.White,
            BorderThickness = new Thickness(0)
        };
        _list.ItemsSource = encounters.OrderByDescending(encounter => encounter.StartedAt).ToArray();
        _list.MouseDoubleClick += (_, _) => OpenSelection();
        panel.Children.Add(_list);
        Content = panel;
    }

    private void OpenSelection()
    {
        if (SelectedEncounter is not null) DialogResult = true;
    }
}
