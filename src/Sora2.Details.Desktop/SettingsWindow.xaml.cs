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
        CloseChoiceStatus.Text = current.RememberedCloseChoice switch
        {
            CloseWindowChoice.HideToTray => "Saved choice: hide to the system tray.",
            CloseWindowChoice.Exit => "Saved choice: close Sora 2 Details.",
            _ => "You will be asked each time."
        };
        AskAgainChoice.IsEnabled = current.RememberedCloseChoice is not null;
        AlwaysOnTopChoice.IsChecked = current.AlwaysOnTop;
        LockPositionChoice.IsChecked = current.LockPosition;
        ClickThroughChoice.IsEnabled = trayAvailable;
        ClickThroughChoice.IsChecked = trayAvailable && current.ClickThrough;
        OpacityChoice.Value = Math.Clamp(current.Opacity,
            MeterDisplaySettings.MinimumOpacity, MeterDisplaySettings.MaximumOpacity);
        OpacityValue.Text = $"{OpacityChoice.Value:P0}";
        PopulateFontSizeChoices(current.FontSize);
    }

    internal MeterDisplaySettings UpdatedSettings => _current with
    {
        RememberedCloseChoice = AskAgainChoice.IsChecked == true
            ? null : _current.RememberedCloseChoice,
        AlwaysOnTop = AlwaysOnTopChoice.IsChecked == true,
        LockPosition = LockPositionChoice.IsChecked == true,
        ClickThrough = ClickThroughChoice.IsChecked == true,
        Opacity = OpacityChoice.Value,
        FontSize = SelectedInt(FontSizeChoice, _current.FontSize)
    };

    private void OpacityChoice_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        OpacityValue.Text = $"{e.NewValue:P0}";
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

    private static int SelectedInt(ComboBox choice, int fallback) =>
        choice.SelectedItem is ComboBoxItem { Tag: int value } ? value : fallback;

    private void Save_Click(object sender, RoutedEventArgs e) => DialogResult = true;
}
