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
        CloseButton.ToolTip = _displaySettings.CloseToTray ? "Hide meter to tray" : "Exit Sora 2 Details";
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
        RefreshTrayCommands();
    }

    private void OpenSettingsWindow()
    {
        var settingsWindow = new SettingsWindow(_displaySettings, _trayIcon?.Visible == true)
        {
            Owner = this
        };
        if (settingsWindow.ShowDialog() == true)
            SetDisplaySettings(settingsWindow.UpdatedSettings);
    }

    private void Header_MouseRightButtonUp(object sender, MouseButtonEventArgs e)
    {
        OpenSettingsWindow();
        e.Handled = true;
    }
}
