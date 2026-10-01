using System.Windows;
using System.Windows.Controls;

namespace Sora2.Details.Desktop;

public partial class SettingsWindow : Window
{
    private readonly MeterDisplaySettings _current;

    internal SettingsWindow(MeterDisplaySettings current, bool trayAvailable)
    {
        InitializeComponent();
        _current = current;
        CloseBehaviorChoice.SelectedIndex = current.CloseToTray ? 0 : 1;
        AlwaysOnTopChoice.IsChecked = current.AlwaysOnTop;
        LockPositionChoice.IsChecked = current.LockPosition;
        ClickThroughChoice.IsEnabled = trayAvailable;
        ClickThroughChoice.IsChecked = trayAvailable && current.ClickThrough;
        PopulateOpacityChoices(current.Opacity);
        PopulateFontSizeChoices(current.FontSize);
    }

    internal MeterDisplaySettings UpdatedSettings => _current with
    {
        CloseToTray = CloseBehaviorChoice.SelectedIndex == 0,
        AlwaysOnTop = AlwaysOnTopChoice.IsChecked == true,
        LockPosition = LockPositionChoice.IsChecked == true,
        ClickThrough = ClickThroughChoice.IsChecked == true,
        Opacity = SelectedDouble(OpacityChoice, _current.Opacity),
        FontSize = SelectedInt(FontSizeChoice, _current.FontSize)
    };

    private void PopulateOpacityChoices(double current)
    {
        var choices = new[] { 1d, 0.9d, 0.75d, 0.6d };
        if (!choices.Any(value => Math.Abs(value - current) < 0.001))
            choices = choices.Append(current).OrderByDescending(value => value).ToArray();
        foreach (var value in choices)
        {
            var item = new ComboBoxItem { Content = $"{value:P0}", Tag = value };
            OpacityChoice.Items.Add(item);
            if (Math.Abs(value - current) < 0.001) OpacityChoice.SelectedItem = item;
        }
    }

    private void PopulateFontSizeChoices(int current)
    {
        var choices = new[] { 10, 12, 14, 16 };
        if (!choices.Contains(current))
            choices = choices.Append(current).OrderBy(value => value).ToArray();
        foreach (var value in choices)
        {
            var item = new ComboBoxItem { Content = $"{value} pt", Tag = value };
            FontSizeChoice.Items.Add(item);
            if (value == current) FontSizeChoice.SelectedItem = item;
        }
    }

    private static double SelectedDouble(ComboBox choice, double fallback) =>
        choice.SelectedItem is ComboBoxItem { Tag: double value } ? value : fallback;

    private static int SelectedInt(ComboBox choice, int fallback) =>
        choice.SelectedItem is ComboBoxItem { Tag: int value } ? value : fallback;

    private void Save_Click(object sender, RoutedEventArgs e) => DialogResult = true;
}
