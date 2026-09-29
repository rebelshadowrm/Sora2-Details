using System.Diagnostics;
using System.Security.Principal;

namespace Sora2.Details.CaptureHost;

internal static class Program
{
    // Fixed packaged child entry point, not a general elevated command runner.
    // It inherits the app's startup-approved token and never self-elevates.
    private static int Main(string[] args)
    {
        var root = AppContext.BaseDirectory;
        var python = Path.Combine(root, "python", "python.exe");
        var script = Path.Combine(root, "tools", "elevated_probe_session.py");
        if (!File.Exists(python) || !File.Exists(script)) return 2;
        if (args is ["--check-package"]) return 0;
        if (args.Length != 3 || !int.TryParse(args[0], out var pid) || pid <= 0 ||
            !int.TryParse(args[1], out var minutes) || minutes is < 1 or > 1500 ||
            !Path.IsPathFullyQualified(args[2])) return 3;
        using var identity = WindowsIdentity.GetCurrent();
        if (!new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator)) return 4;
        try
        {
            var dataDirectory = Path.GetFullPath(args[2]);
            var start = new ProcessStartInfo(python)
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                WorkingDirectory = root
            };
            // Explicitly preserve the initiating user's data location across credential UAC.
            start.Environment["SORA2_DETAILS_DATA_DIR"] = dataDirectory;
            start.Environment["SORA2_DETAILS_HOST_PID"] = Environment.ProcessId.ToString();
            foreach (var argument in new[] { "-B", script, "--session-dir",
                         Path.Combine(dataDirectory, "probe-session"), "serve", "--pid",
                         pid.ToString(), "--minutes", minutes.ToString() })
                start.ArgumentList.Add(argument);
            using var child = Process.Start(start);
            if (child is null) return 5;
            child.WaitForExit();
            return child.ExitCode;
        }
        catch (Exception exception) when (exception is IOException or
                   System.ComponentModel.Win32Exception or UnauthorizedAccessException or ArgumentException)
        {
            return 5;
        }
    }
}
