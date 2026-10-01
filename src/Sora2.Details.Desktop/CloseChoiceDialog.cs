using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;

namespace Sora2.Details.Desktop;

internal sealed class CloseChoiceDialog : Window
{
    private readonly CheckBox _rememberChoice;

    internal CloseWindowChoice? Choice { get; private set; }
    internal bool RememberChoice => _rememberChoice.IsChecked == true;

    internal CloseChoiceDialog()
    {
        Title = "Close Sora 2 Details";
        Width = 410;
        Height = 220;
        ResizeMode = ResizeMode.NoResize;
        ShowInTaskbar = false;
        WindowStartupLocation = WindowStartupLocation.CenterOwner;
        Background = new SolidColorBrush(Color.FromRgb(23, 25, 29));
        Foreground = Brushes.White;
        FontFamily = new FontFamily("Segoe UI");

        var panel = new StackPanel { Margin = new Thickness(20) };
        panel.Children.Add(new TextBlock
        {
            Text = "What should X do?",
            FontSize = 17,
            FontWeight = FontWeights.SemiBold
        });
        panel.Children.Add(new TextBlock
        {
            Text = "Hide the meter and keep Sora 2 Details in the tray, or exit the app?",
            TextWrapping = TextWrapping.Wrap,
            Foreground = new SolidColorBrush(Color.FromRgb(191, 195, 200)),
            Margin = new Thickness(0, 8, 0, 0)
        });
        _rememberChoice = new CheckBox
        {
            Content = "Remember this choice",
            Margin = new Thickness(0, 14, 0, 12)
        };
        panel.Children.Add(_rememberChoice);

        var buttons = new StackPanel
        {
            Orientation = Orientation.Horizontal,
            HorizontalAlignment = HorizontalAlignment.Right
        };
        var hide = new Button
        {
            Content = "Hide to tray",
            MinWidth = 92,
            Height = 30,
            IsDefault = true
        };
        hide.Click += (_, _) => Choose(CloseWindowChoice.HideToTray);
        buttons.Children.Add(hide);
        var exit = new Button
        {
            Content = "Exit app",
            MinWidth = 76,
            Height = 30,
            Margin = new Thickness(8, 0, 0, 0)
        };
        exit.Click += (_, _) => Choose(CloseWindowChoice.Exit);
        buttons.Children.Add(exit);
        var cancel = new Button
        {
            Content = "Cancel",
            MinWidth = 76,
            Height = 30,
            Margin = new Thickness(8, 0, 0, 0),
            IsCancel = true
        };
        buttons.Children.Add(cancel);
        panel.Children.Add(buttons);
        Content = panel;
    }

    private void Choose(CloseWindowChoice choice)
    {
        Choice = choice;
        DialogResult = true;
    }
}
