using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace Sora2.Details.Desktop;

public partial class MainWindow
{
    private void ApplyDisplaySettings(bool resizeToRows)
    {
        Topmost = _displaySettings.AlwaysOnTop;
        Opacity = _displaySettings.Opacity;
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
        if (resizeToRows)
            Height = Math.Min(SystemParameters.VirtualScreenHeight,
                Math.Max(MinHeight, 71 + _displaySettings.VisibleRows * (rowHeight + 1)));
    }

    private void SetDisplaySettings(MeterDisplaySettings settings, bool resizeToRows = false)
    {
        _displaySettings = settings;
        ApplyDisplaySettings(resizeToRows);
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
            }, resizeToRows: true);
            textSize.Items.Add(choice);
        }
        menu.Items.Add(textSize);

        var visibleRows = new MenuItem { Header = "Visible rows" };
        foreach (var count in new[] { 4, 6, 8, 10, 12, 15 })
        {
            var choice = new MenuItem { Header = count.ToString(), IsCheckable = true,
                IsChecked = _displaySettings.VisibleRows == count };
            choice.Click += (_, _) => SetDisplaySettings(_displaySettings with
            {
                VisibleRows = count
            }, resizeToRows: true);
            visibleRows.Items.Add(choice);
        }
        menu.Items.Add(visibleRows);
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
