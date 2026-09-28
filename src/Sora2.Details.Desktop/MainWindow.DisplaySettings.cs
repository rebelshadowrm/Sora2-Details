using System.IO;
using System.ComponentModel;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace Sora2.Details.Desktop;

public partial class MainWindow
{
    private void ApplyDisplaySettings()
    {
        Topmost = _displaySettings.AlwaysOnTop;
        // A transparent WPF window applies opacity to the entire meter surface.
        Opacity = _displaySettings.Opacity;
        ApplyWindowAppearance();
        FontSize = _displaySettings.FontSize;
        var rowHeight = Math.Max(23, _displaySettings.FontSize + 11);
        MeterRows.Tag = (double)rowHeight;
        var cursor = _displaySettings.LockPosition ? Cursors.Arrow : Cursors.SizeAll;
        HeaderDragArea.Cursor = cursor;
        EncounterHeader.Cursor = cursor;
        FooterDragArea.Cursor = cursor;
        var dragHint = _displaySettings.LockPosition ? "Position locked" : "Drag to move the meter";
        HeaderDragArea.ToolTip = $"{dragHint} · right-click for display settings";
        EncounterHeader.ToolTip = dragHint;
        FooterDragArea.ToolTip = dragHint;
    }

    private void SetDisplaySettings(MeterDisplaySettings settings)
    {
        var previous = _displaySettings;
        _displaySettings = settings;
        try { ApplyDisplaySettings(); }
        catch (Exception exception) when (exception is Win32Exception or InvalidOperationException)
        {
            _displaySettings = previous;
            try { ApplyDisplaySettings(); }
            catch (Win32Exception) { }
            MessageBox.Show(this, $"Display settings could not be applied: {exception.Message}",
                "Display settings", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }
        try { _displaySettings.Save(); }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            MessageBox.Show(this, $"Display settings could not be saved: {exception.Message}",
                "Display settings", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    private MenuItem BuildDisplaySettingsMenu()
    {
        var menu = new MenuItem { Header = "Display settings" };
        var lockPosition = new MenuItem { Header = "Lock position", IsCheckable = true,
            IsChecked = _displaySettings.LockPosition };
        lockPosition.Click += (_, _) => SetDisplaySettings(_displaySettings with
        {
            LockPosition = lockPosition.IsChecked
        });
        menu.Items.Add(lockPosition);

        var clickThrough = new MenuItem
        {
            Header = "Click-through (restore from tray)",
            IsCheckable = true,
            IsChecked = _displaySettings.ClickThrough,
            IsEnabled = _trayIcon?.Visible == true,
            ToolTip = "Pass all mouse clicks to the game; use the tray icon to restore interaction"
        };
        clickThrough.Click += (_, _) => SetDisplaySettings(_displaySettings with
        {
            ClickThrough = clickThrough.IsChecked
        });
        menu.Items.Add(clickThrough);

        var alwaysOnTop = new MenuItem { Header = "Always on top", IsCheckable = true,
            IsChecked = _displaySettings.AlwaysOnTop };
        alwaysOnTop.Click += (_, _) => SetDisplaySettings(_displaySettings with
        {
            AlwaysOnTop = alwaysOnTop.IsChecked
        });
        menu.Items.Add(alwaysOnTop);

        var opacity = new MenuItem { Header = "Opacity" };
        foreach (var percent in new[] { 100, 90, 75, 60 })
        {
            var choice = new MenuItem { Header = $"{percent}%", IsCheckable = true,
                IsChecked = Math.Abs(_displaySettings.Opacity - percent / 100d) < 0.001 };
            choice.Click += (_, _) => SetDisplaySettings(_displaySettings with
            {
                Opacity = percent / 100d
            });
            opacity.Items.Add(choice);
        }
        menu.Items.Add(opacity);

        var textSize = new MenuItem { Header = "Text size" };
        foreach (var size in new[] { 10, 12, 14, 16 })
        {
            var choice = new MenuItem { Header = $"{size} pt", IsCheckable = true,
                IsChecked = _displaySettings.FontSize == size };
            choice.Click += (_, _) => SetDisplaySettings(_displaySettings with
            {
                FontSize = size
            });
            textSize.Items.Add(choice);
        }
        menu.Items.Add(textSize);

        return menu;
    }

    private void Header_MouseRightButtonUp(object sender, MouseButtonEventArgs e)
    {
        var menu = new ContextMenu();
        menu.Items.Add(BuildDisplaySettingsMenu());
        menu.PlacementTarget = HeaderDragArea;
        menu.Placement = System.Windows.Controls.Primitives.PlacementMode.MousePoint;
        menu.IsOpen = true;
        e.Handled = true;
    }
}
