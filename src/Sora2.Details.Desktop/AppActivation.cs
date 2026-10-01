using System.Runtime.InteropServices;

namespace Sora2.Details.Desktop;

internal static class AppActivation
{
    private const string MainWindowTitle = "Sora 2 Details";
    private const string ActivationMessageName = "Sora2.Details.Desktop.ActivateMeter.v1";
    private const int ShowRestore = 9;

    internal static uint ActivationMessage { get; } = RegisterWindowMessage(ActivationMessageName);

    internal static bool TryActivateExisting()
    {
        if (ActivationMessage == 0) return false;
        var window = FindWindow(null, MainWindowTitle);
        if (window == IntPtr.Zero) return false;

        GetWindowThreadProcessId(window, out var processId);
        if (processId != 0) AllowSetForegroundWindow(processId);
        ShowWindowAsync(window, ShowRestore);
        SetForegroundWindow(window);
        return PostMessage(window, ActivationMessage, IntPtr.Zero, IntPtr.Zero);
    }

    internal static bool AllowActivationMessage(IntPtr window)
    {
        if (ActivationMessage == 0 || window == IntPtr.Zero) return false;
        var changeInfo = new ChangeFilterStruct { Size = (uint)Marshal.SizeOf<ChangeFilterStruct>() };
        return ChangeWindowMessageFilterEx(window, ActivationMessage, MessageFilterAllow, ref changeInfo);
    }

    private const uint MessageFilterAllow = 1;

    [StructLayout(LayoutKind.Sequential)]
    private struct ChangeFilterStruct
    {
        public uint Size;
        public uint ExtStatus;
    }

    [DllImport("user32.dll", EntryPoint = "RegisterWindowMessageW", CharSet = CharSet.Unicode)]
    private static extern uint RegisterWindowMessage(string messageName);

    [DllImport("user32.dll", EntryPoint = "FindWindowW", CharSet = CharSet.Unicode)]
    private static extern IntPtr FindWindow(string? className, string windowName);

    [DllImport("user32.dll", EntryPoint = "PostMessageW", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PostMessage(IntPtr window, uint message, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", EntryPoint = "GetWindowThreadProcessId")]
    private static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);

    [DllImport("user32.dll", EntryPoint = "AllowSetForegroundWindow")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool AllowSetForegroundWindow(uint processId);

    [DllImport("user32.dll", EntryPoint = "ShowWindowAsync")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ShowWindowAsync(IntPtr window, int command);

    [DllImport("user32.dll", EntryPoint = "SetForegroundWindow")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetForegroundWindow(IntPtr window);

    [DllImport("user32.dll", EntryPoint = "ChangeWindowMessageFilterEx", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool ChangeWindowMessageFilterEx(IntPtr window, uint message, uint action,
        ref ChangeFilterStruct changeInfo);
}
