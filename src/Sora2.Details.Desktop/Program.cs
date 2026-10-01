using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Security.Principal;
using System.Text;
using System.Windows;
using Velopack;

namespace Sora2.Details.Desktop;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        // Velopack install/update/uninstall hooks must run at the original
        // integrity level and must never trigger an app-startup elevation prompt.
        VelopackApp.Build().SetAutoApplyOnStartup(false).Run();
        var (dataDirectory, applicationArgs, startupArgs) = ParseArguments(args);
        Environment.SetEnvironmentVariable("SORA2_DETAILS_DATA_DIR", dataDirectory);
        foreach (var (name, value) in startupArgs)
            Environment.SetEnvironmentVariable(name, value);

        if (!IsAdministrator())
        {
            if (AppActivation.TryActivateExisting()) return;
            if (AnotherApplicationInstanceIsRunning()) return;
            if (StartElevated(dataDirectory, applicationArgs, startupArgs)) return;
            return;
        }

        var userSid = WindowsIdentity.GetCurrent().User?.Value ?? "current-user";
        using var instanceMutex = new Mutex(true, $"Local\\Sora2Details.Desktop.{userSid}", out var createdNew);
        if (!createdNew)
        {
            AppActivation.TryActivateExisting();
            return;
        }
        var app = new App();
        app.Run();
    }

    private static bool AnotherApplicationInstanceIsRunning()
    {
        foreach (var process in Process.GetProcessesByName("Sora2.Details.Desktop"))
        {
            using (process)
            {
                if (process.Id != Environment.ProcessId) return true;
            }
        }
        return false;
    }

    private static (string DataDirectory, string[] ApplicationArgs,
        Dictionary<string, string?> StartupArgs) ParseArguments(string[] args)
    {
        string? dataDirectory = Environment.GetEnvironmentVariable("SORA2_DETAILS_DATA_DIR");
        var applicationArgs = new List<string>(args.Length);
        var startupArgs = new Dictionary<string, string?>(StringComparer.OrdinalIgnoreCase);
        for (var index = 0; index < args.Length; index++)
        {
            if (args[index].Equals("--data-dir", StringComparison.OrdinalIgnoreCase) &&
                index + 1 < args.Length)
            {
                dataDirectory = args[++index];
                continue;
            }
            if (args[index].Equals("--capture-hours", StringComparison.OrdinalIgnoreCase) &&
                index + 1 < args.Length)
            {
                var value = args[++index];
                if (int.TryParse(value, out var hours) && hours is >= 2 and <= 12)
                    startupArgs["SORA2_DETAILS_CAPTURE_HOURS"] = hours.ToString();
                continue;
            }
            if (args[index].Equals("--capture-profile", StringComparison.OrdinalIgnoreCase) &&
                index + 1 < args.Length)
            {
                var value = args[++index];
                if (value.Equals("Live", StringComparison.OrdinalIgnoreCase) ||
                    value.Equals("HealingResearch", StringComparison.OrdinalIgnoreCase))
                    startupArgs["SORA2_DETAILS_CAPTURE_PROFILE"] = value;
                continue;
            }
            if (args[index].Equals("--game-directory", StringComparison.OrdinalIgnoreCase) &&
                index + 1 < args.Length)
            {
                startupArgs["SORA2_DETAILS_GAME_DIRECTORY"] = args[++index];
                continue;
            }
            if (args[index].Equals("--python-path", StringComparison.OrdinalIgnoreCase) &&
                index + 1 < args.Length)
            {
                startupArgs["SORA2_DETAILS_PYTHON_PATH"] = args[++index];
                continue;
            }
            if (args[index].Equals("--meter-only", StringComparison.OrdinalIgnoreCase))
            {
                startupArgs["SORA2_DETAILS_METER_ONLY"] = "1";
                continue;
            }
            applicationArgs.Add(args[index]);
        }

        dataDirectory ??= Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Sora2 Details");
        return (Path.GetFullPath(dataDirectory), applicationArgs.ToArray(), startupArgs);
    }

    private static bool IsAdministrator()
    {
        using var identity = WindowsIdentity.GetCurrent();
        return new WindowsPrincipal(identity).IsInRole(WindowsBuiltInRole.Administrator);
    }

    private static bool StartElevated(string dataDirectory, string[] applicationArgs,
        IReadOnlyDictionary<string, string?> startupArgs)
    {
        var executable = Environment.ProcessPath ?? Process.GetCurrentProcess().MainModule?.FileName;
        if (string.IsNullOrWhiteSpace(executable))
        {
            MessageBox.Show("Sora 2 Details could not locate its executable to request startup approval.",
                "Sora 2 Details", MessageBoxButton.OK, MessageBoxImage.Error);
            return false;
        }

        var forwardedArgs = new List<string>(applicationArgs);
        foreach (var (name, value) in startupArgs)
        {
            var argumentName = name switch
            {
                "SORA2_DETAILS_CAPTURE_HOURS" => "--capture-hours",
                "SORA2_DETAILS_CAPTURE_PROFILE" => "--capture-profile",
                "SORA2_DETAILS_GAME_DIRECTORY" => "--game-directory",
                "SORA2_DETAILS_PYTHON_PATH" => "--python-path",
                "SORA2_DETAILS_METER_ONLY" => "--meter-only",
                _ => null
            };
            if (argumentName is not null)
            {
                forwardedArgs.Add(argumentName);
                if (value is not null) forwardedArgs.Add(value);
            }
        }
        forwardedArgs.Add("--data-dir");
        forwardedArgs.Add(dataDirectory);
        var start = new ProcessStartInfo(executable)
        {
            UseShellExecute = true,
            Verb = "runas",
            WorkingDirectory = Environment.CurrentDirectory,
            Arguments = string.Join(" ", forwardedArgs.Select(QuoteWindowsArgument))
        };
        try
        {
            using var elevatedProcess = Process.Start(start);
            return elevatedProcess is not null;
        }
        catch (Win32Exception exception) when (exception.NativeErrorCode == 1223)
        {
            return false;
        }
        catch (Win32Exception exception)
        {
            MessageBox.Show($"Sora 2 Details could not request startup approval: {exception.Message}",
                "Sora 2 Details", MessageBoxButton.OK, MessageBoxImage.Error);
            return false;
        }
    }

    private static string QuoteWindowsArgument(string value)
    {
        if (value.Length > 0 && !value.Any(character => char.IsWhiteSpace(character) || character == '"'))
            return value;

        var quoted = new StringBuilder("\"");
        var backslashes = 0;
        foreach (var character in value)
        {
            if (character == '\\')
            {
                backslashes++;
                continue;
            }
            if (character == '"')
            {
                quoted.Append('\\', backslashes * 2 + 1).Append('"');
                backslashes = 0;
                continue;
            }
            quoted.Append('\\', backslashes).Append(character);
            backslashes = 0;
        }
        quoted.Append('\\', backslashes * 2).Append('"');
        return quoted.ToString();
    }
}
