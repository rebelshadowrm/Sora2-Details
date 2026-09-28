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

    private void InitializeWindowInteraction()
    {
        try
        {
            _trayMenu = new Forms.ContextMenuStrip();
            _trayClickThrough = new Forms.ToolStripMenuItem("Click-through")
            {
                CheckOnClick = false
            };
            _trayClickThrough.Click += (_, _) => Dispatcher.BeginInvoke(() =>
                SetDisplaySettings(_displaySettings with { ClickThrough = !_displaySettings.ClickThrough }));
            _trayMenu.Items.Add(_trayClickThrough);
            var restore = new Forms.ToolStripMenuItem("Restore interaction and show meter");
            restore.Click += (_, _) => Dispatcher.BeginInvoke(RestoreInteractionFromTray);
            _trayMenu.Items.Add(restore);
            _trayIcon = new Forms.NotifyIcon
            {
                Icon = System.Drawing.SystemIcons.Application,
                Text = "Sora 2 Details",
                ContextMenuStrip = _trayMenu,
                Visible = true
            };
            _trayIcon.DoubleClick += (_, _) => Dispatcher.BeginInvoke(RestoreInteractionFromTray);
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
        if (WindowState == WindowState.Minimized) WindowState = WindowState.Normal;
        Show();
        Activate();
    }

    private void UpdateTrayState()
    {
        if (_trayClickThrough is not null)
            _trayClickThrough.Checked = _displaySettings.ClickThrough;
        if (_trayIcon is not null)
            _trayIcon.Text = _displaySettings.ClickThrough
                ? "Sora 2 Details - click-through (double-click to restore)"
                : "Sora 2 Details";
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
