using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Interop;
using Forms = System.Windows.Forms;

namespace Sora2.Details.Desktop;

public partial class MainWindow
{
    private const int GwlExStyle = -20;
    private const long WsExTransparent = 0x00000020;
    private const long WsExNoActivate = 0x08000000;
    private const uint SwpNoSize = 0x0001;
    private const uint SwpNoMove = 0x0002;
    private const uint SwpNoZOrder = 0x0004;
    private const uint SwpNoActivate = 0x0010;
    private const uint SwpFrameChanged = 0x0020;

    private Forms.NotifyIcon? _trayIcon;
    private Forms.ContextMenuStrip? _trayMenu;
    private Forms.ToolStripMenuItem? _trayClickThrough;
    private Forms.ToolStripMenuItem? _trayShowMeter;
    private Forms.ToolStripMenuItem? _trayHideMeter;
    private Forms.ToolStripMenuItem? _trayStartCapture;
    private Forms.ToolStripMenuItem? _trayStopCapture;
    private Forms.ToolStripMenuItem? _trayRestoreInteraction;

    private void InitializeWindowInteraction()
    {
        try
        {
            _trayMenu = new Forms.ContextMenuStrip();
            _trayShowMeter = new Forms.ToolStripMenuItem("Show meter");
            _trayShowMeter.Click += (_, _) => Dispatcher.BeginInvoke(ShowMeterFromTray);
            _trayMenu.Items.Add(_trayShowMeter);
            _trayHideMeter = new Forms.ToolStripMenuItem("Hide meter");
            _trayHideMeter.Click += (_, _) => Dispatcher.BeginInvoke(HideMeterToTray);
            _trayMenu.Items.Add(_trayHideMeter);
            _trayMenu.Items.Add(new Forms.ToolStripSeparator());
            _trayStartCapture = new Forms.ToolStripMenuItem("Start/attach capture");
            _trayStartCapture.Click += (_, _) => Dispatcher.BeginInvoke(StartCaptureFromTray);
            _trayMenu.Items.Add(_trayStartCapture);
            _trayStopCapture = new Forms.ToolStripMenuItem("Stop/detach capture");
            _trayStopCapture.Click += (_, _) => Dispatcher.BeginInvoke(() => _ = StopCaptureAsync());
            _trayMenu.Items.Add(_trayStopCapture);
            _trayMenu.Items.Add(new Forms.ToolStripSeparator());
            var history = new Forms.ToolStripMenuItem("View previous logs/history");
            history.Click += (_, _) => Dispatcher.BeginInvoke(OpenHistoryFromTray);
            _trayMenu.Items.Add(history);
            _trayClickThrough = new Forms.ToolStripMenuItem("Click-through")
            {
                CheckOnClick = false
            };
            _trayClickThrough.Click += (_, _) => Dispatcher.BeginInvoke(() =>
                SetDisplaySettings(_displaySettings with { ClickThrough = !_displaySettings.ClickThrough }));
            _trayMenu.Items.Add(_trayClickThrough);
            _trayRestoreInteraction = new Forms.ToolStripMenuItem("Restore interaction / disable click-through");
            _trayRestoreInteraction.Click += (_, _) => Dispatcher.BeginInvoke(RestoreInteractionFromTray);
            _trayMenu.Items.Add(_trayRestoreInteraction);
            var settings = new Forms.ToolStripMenuItem("Settings");
            settings.Click += (_, _) => Dispatcher.BeginInvoke(OpenSettingsFromTray);
            _trayMenu.Items.Add(settings);
            _trayMenu.Items.Add(new Forms.ToolStripSeparator());
            var exit = new Forms.ToolStripMenuItem("Exit Sora 2 Details");
            exit.Click += (_, _) => Dispatcher.BeginInvoke(RequestFullExit);
            _trayMenu.Items.Add(exit);
            _trayIcon = new Forms.NotifyIcon
            {
                Icon = System.Drawing.SystemIcons.Application,
                Text = "Sora 2 Details",
                ContextMenuStrip = _trayMenu,
                Visible = true
            };
            _trayIcon.DoubleClick += (_, _) => Dispatcher.BeginInvoke(ShowMeterFromTray);
            _trayIcon.BalloonTipClicked += (_, _) => Dispatcher.BeginInvoke(StartCaptureFromTray);
            ApplyWindowAppearance();
            UpdateTrayState();
        }
        catch (Exception exception) when (exception is Win32Exception or InvalidOperationException or
                                         ExternalException)
        {
            // Never start in click-through mode without a usable tray escape.
            DisposeTray();
            _displaySettings = _displaySettings with { ClickThrough = false };
            try { ApplyWindowAppearance(); }
            catch (Win32Exception) { }
            MessageBox.Show(this, $"Window interaction could not be configured: {exception.Message}",
                "Display settings", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    private void RestoreInteractionFromTray()
    {
        if (_displaySettings.ClickThrough)
            SetDisplaySettings(_displaySettings with { ClickThrough = false });
        ShowMeterFromTray();
    }

    private void ShowMeterFromTray()
    {
        if (WindowState == WindowState.Minimized) WindowState = WindowState.Normal;
        Show();
        Activate();
    }

    private void HideMeterToTray()
    {
        if (_trayIcon?.Visible == true)
        {
            Hide();
            return;
        }
        if (WindowState != WindowState.Minimized) WindowState = WindowState.Minimized;
    }

    private void ShowGameDetectedNotification()
    {
        if (_trayIcon?.Visible != true) return;
        _trayIcon.ShowBalloonTip(8000, "Trails detected — Start capture?",
            "Click this notification or choose Start/attach capture from the Sora 2 Details tray menu.",
            Forms.ToolTipIcon.Info);
    }

    private void StartCaptureFromTray()
    {
        ShowMeterFromTray();
        _ = StartCaptureAsync(_currentGamePid);
    }

    private void OpenHistoryFromTray()
    {
        ShowMeterFromTray();
        if (_encounters.Count == 0)
        {
            MessageBox.Show(this, "No saved encounters are available yet.", "Sora 2 Details history",
                MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }
        var history = new HistoryWindow(_encounters, _historySettings) { Owner = this };
        if (history.ShowDialog() == true)
        {
            _followNewest = false;
            SelectEncounter(history.SelectedEncounter);
        }
    }

    private void OpenSettingsFromTray()
    {
        ShowMeterFromTray();
        var menu = new System.Windows.Controls.ContextMenu();
        menu.Items.Add(BuildDisplaySettingsMenu());
        menu.PlacementTarget = HeaderDragArea;
        menu.Placement = System.Windows.Controls.Primitives.PlacementMode.MousePoint;
        menu.IsOpen = true;
    }

    private void RefreshTrayCommands()
    {
        UpdateTrayState();
    }

    private void UpdateTrayState()
    {
        if (_trayClickThrough is not null)
            _trayClickThrough.Checked = _displaySettings.ClickThrough;
        if (_trayRestoreInteraction is not null)
            _trayRestoreInteraction.Enabled = _displaySettings.ClickThrough || !IsVisible;
        if (_trayShowMeter is not null) _trayShowMeter.Enabled = !IsVisible;
        if (_trayHideMeter is not null) _trayHideMeter.Enabled = IsVisible;
        var pids = GetGamePids();
        if (_trayStartCapture is not null)
            _trayStartCapture.Enabled = pids.Length == 1 && !_researchMode && !_captureBusy && !_updateBusy && !CaptureMayBeActive();
        if (_trayStopCapture is not null)
            _trayStopCapture.Enabled = !_captureBusy && !_updateBusy && CaptureMayBeActive();
        if (_trayIcon is not null)
            _trayIcon.Text = _displaySettings.ClickThrough
                ? "Sora 2 Details - click-through; tray restores interaction"
                : CaptureMayBeActive() ? "Sora 2 Details - capturing" : "Sora 2 Details - waiting in tray";
    }

    private void DisposeTray()
    {
        if (_trayIcon is not null)
        {
            _trayIcon.Visible = false;
            _trayIcon.Dispose();
            _trayIcon = null;
        }
        _trayMenu?.Dispose();
        _trayMenu = null;
        _trayClickThrough = null;
        _trayShowMeter = null;
        _trayHideMeter = null;
        _trayStartCapture = null;
        _trayStopCapture = null;
        _trayRestoreInteraction = null;
    }

    private void ApplyWindowAppearance()
    {
        var handle = new WindowInteropHelper(this).Handle;
        if (handle == IntPtr.Zero) return;
        if (_displaySettings.ClickThrough && _trayIcon?.Visible != true)
            throw new InvalidOperationException("Click-through requires the tray icon.");

        var previous = GetWindowLongPtr(handle, GwlExStyle).ToInt64();
        var desired = previous;
        desired = _displaySettings.ClickThrough
            ? desired | WsExTransparent | WsExNoActivate
            : desired & ~(WsExTransparent | WsExNoActivate);
        if (desired != previous)
        {
            Marshal.SetLastPInvokeError(0);
            var oldStyle = SetWindowLongPtr(handle, GwlExStyle, new IntPtr(desired));
            if (oldStyle == IntPtr.Zero && Marshal.GetLastPInvokeError() != 0)
                throw new Win32Exception(Marshal.GetLastPInvokeError(), "Could not set meter window style");
            if (!SetWindowPos(handle, IntPtr.Zero, 0, 0, 0, 0,
                    SwpNoMove | SwpNoSize | SwpNoZOrder | SwpNoActivate | SwpFrameChanged))
                throw new Win32Exception(Marshal.GetLastPInvokeError(), "Could not refresh meter window style");
        }
        UpdateTrayState();
    }

    [DllImport("user32.dll", EntryPoint = "GetWindowLongPtrW", SetLastError = true)]
    private static extern IntPtr GetWindowLongPtr(IntPtr window, int index);

    [DllImport("user32.dll", EntryPoint = "SetWindowLongPtrW", SetLastError = true)]
    private static extern IntPtr SetWindowLongPtr(IntPtr window, int index, IntPtr value);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetWindowPos(IntPtr window, IntPtr insertAfter, int x, int y,
        int width, int height, uint flags);
}
