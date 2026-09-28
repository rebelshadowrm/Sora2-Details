using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows;
using Microsoft.Win32;
using Velopack;
using Velopack.Sources;
using Velopack.Locators;

namespace Sora2.Details.Desktop;

public partial class MainWindow
{
    private UpdateManager? _updateManager;
    private UpdateInfo? _availableUpdate;
    private bool _updateBusy;
    private bool _captureBusy;
    private bool _captureStarting;
    private bool _captureStopping;
    private string? _captureStatusError;

    private static string AppVersion => VelopackLocator.Current.CurrentlyInstalledVersion?.ToString()
        ?? "development build";

    private void SetCaptureError(string message)
    {
        _captureStatusError = message;
        RefreshCaptureStatus();
    }

    private void RefreshCaptureStatus()
    {
        var active = CaptureMayBeActive();
        var missingBridge = active && ActiveTraceName() is null;
        if (!_captureBusy) CaptureButton.Content = active ? "■" : "●";
        var state = _researchMode ? "Research" :
            _captureStatusError is not null || _captureError is not null || missingBridge ? "Error" :
            _captureStopping ? "Stopping" : _captureStarting ? "Starting" :
            active ? "Capturing" : "Ready";
        DataSourceLabel.Text = state;
        DataSourceLabel.Foreground = state == "Error" ? Brushes.OrangeRed :
            state == "Capturing" ? Brushes.LightGreen : Brushes.Goldenrod;
        var detail = _captureStatusError ?? _captureError ?? (missingBridge
            ? "The bridge is no longer running, but probe detachment is unconfirmed. Click ■ to request a clean stop."
            : state switch
        {
            "Capturing" => "Live capture is running. Close the meter to stop and exit, or click ■ to stop.",
            "Stopping" => "Waiting for the external probe to detach.",
            "Starting" => "Starting capture; approve the Windows administrator prompt if shown.",
            "Research" => "Showing a research replay; no live capture is attached.",
            _ => _sampleMode
                ? "Sample replay is shown. Start the game, then click ● if capture did not start automatically."
                : "Saved encounters are shown. Start the game, then click ● if capture did not start automatically."
        });
        DataSourceLabel.ToolTip = $"Sora 2 Details {AppVersion}\n{state}: {detail}\nClick for details.";
    }

    private void CaptureStatus_Click(object sender, MouseButtonEventArgs e)
    {
        var detail = _captureStatusError ?? _captureError ?? DataSourceLabel.ToolTip?.ToString();
        MessageBox.Show(this, $"Sora 2 Details {AppVersion}\n\n{detail}", "Capture status",
            MessageBoxButton.OK, _captureStatusError is not null || _captureError is not null
                ? MessageBoxImage.Warning : MessageBoxImage.Information);
    }

    private async void CaptureButton_Click(object sender, RoutedEventArgs e)
    {
        if (_captureBusy) return;
        if (CaptureButton.Content?.ToString() == "■")
        {
            _captureBusy = true;
            _captureStopping = true;
            CaptureButton.ToolTip = "Detaching capture...";
            RefreshCaptureStatus();
            try
            {
                var detached = await EnsureCaptureDetachedAsync();
                CaptureButton.ToolTip = detached ? "Capture detached." : "Capture did not detach; try Stop-Sora2Details.cmd.";
                if (detached)
                {
                    CaptureButton.Content = "●";
                    _captureStatusError = null;
                    ReloadHistory();
                }
                else SetCaptureError("Capture did not detach within 30 seconds. Try Stop again or use Stop-Sora2Details.cmd.");
            }
            catch (Exception exception) { SetCaptureError($"Stop failed: {exception.Message}"); }
            finally
            {
                _captureBusy = false;
                _captureStopping = false;
                RefreshCaptureStatus();
                if (_closeWhenReady) Close();
            }
            return;
        }
        await StartCaptureAsync();
    }

    private async Task StartCaptureAsync()
    {
        if (_captureBusy || ActiveTraceName() is not null) return;
        if (CaptureMayBeActive())
        {
            SetCaptureError("An earlier probe has no confirmed detach record. Click Stop before starting another capture.");
            return;
        }
        var launcher = FindLauncher();
        if (launcher is null)
        {
            CaptureButton.ToolTip = "Capture launcher is missing from this package.";
            SetCaptureError(CaptureButton.ToolTip.ToString()!);
            return;
        }
        var games = Process.GetProcessesByName("sora_2nd");
        string? gameDirectory;
        try
        {
            if (games.Length != 1)
            {
                CaptureButton.ToolTip = games.Length == 0
                    ? "Start the game before beginning capture."
                    : "Capture needs exactly one running game process.";
                if (games.Length > 1) SetCaptureError(CaptureButton.ToolTip.ToString()!);
                return;
            }
            gameDirectory = ResolveGameDirectory(games[0]);
        }
        finally
        {
            foreach (var game in games) game.Dispose();
        }
        if (gameDirectory is null)
        {
            var picker = new OpenFileDialog
            {
                Title = "Locate Trails in the Sky 2nd Chapter",
                Filter = "Game executable (sora_2nd.exe)|sora_2nd.exe",
                FileName = "sora_2nd.exe",
                CheckFileExists = true
            };
            if (picker.ShowDialog(this) != true)
            {
                CaptureButton.ToolTip = "Capture not started. Select sora_2nd.exe to locate the game.";
                SetCaptureError(CaptureButton.ToolTip.ToString()!);
                return;
            }
            gameDirectory = Path.GetDirectoryName(picker.FileName);
        }
        if (gameDirectory is null) return;
        _captureBusy = true;
        _captureStarting = true;
        CaptureButton.ToolTip = "Starting capture; Windows may request administrator approval.";
        RefreshCaptureStatus();
        try
        {
            var start = new ProcessStartInfo("powershell.exe")
            {
                UseShellExecute = false,
                CreateNoWindow = true,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                WorkingDirectory = Path.GetDirectoryName(launcher)!
            };
            foreach (var argument in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", launcher,
                         "-CaptureOnly", "-GameDirectory", gameDirectory })
                start.ArgumentList.Add(argument);
            using var process = Process.Start(start) ?? throw new IOException("PowerShell did not start.");
            var stdout = process.StandardOutput.ReadToEndAsync();
            var stderr = process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();
            var output = (await stdout).Trim();
            var error = (await stderr).Trim();
            CaptureButton.ToolTip = process.ExitCode == 0
                ? "Partial command-battle capture is running. Start before entering a fight."
                : $"Capture could not start: {(string.IsNullOrEmpty(error) ? output : error)}";
            if (process.ExitCode == 0)
            {
                RememberGameDirectory(gameDirectory);
                _captureStatusError = null;
                _followNewest = true;
                ReloadHistory();
            }
            else SetCaptureError(CaptureButton.ToolTip.ToString()!);
            CaptureButton.Content = process.ExitCode == 0 ? "■" : "●";
        }
        catch (Exception exception)
        {
            CaptureButton.ToolTip = $"Capture could not start: {exception.Message}";
            SetCaptureError(CaptureButton.ToolTip.ToString()!);
        }
        finally
        {
            _captureBusy = false;
            _captureStarting = false;
            RefreshCaptureStatus();
            if (_closeWhenReady) Close();
        }
    }

    private static string? ResolveGameDirectory(Process game)
    {
        try
        {
            var runningExe = game.MainModule?.FileName;
            if (runningExe is not null && File.Exists(runningExe))
                return Path.GetDirectoryName(runningExe);
        }
        catch (Exception exception) when (exception is System.ComponentModel.Win32Exception or
                                           InvalidOperationException or UnauthorizedAccessException)
        {
            // Windows may hide the executable path until the probe is elevated.
        }
        var saved = ReadGameDirectory();
        if (saved is not null) return saved;
        const string originalInstall = @"C:\Games\Trails in the Sky 2nd Chapter";
        return File.Exists(Path.Combine(originalInstall, "sora_2nd.exe")) ? originalInstall : null;
    }

    private static string? ReadGameDirectory()
    {
        try
        {
            var path = GameDirectorySettingPath();
            if (!File.Exists(path)) return null;
            var directory = File.ReadAllText(path).Trim();
            return File.Exists(Path.Combine(directory, "sora_2nd.exe")) ? directory : null;
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or ArgumentException)
        {
            return null;
        }
    }

    private static void RememberGameDirectory(string directory)
    {
        try
        {
            var path = GameDirectorySettingPath();
            Directory.CreateDirectory(Path.GetDirectoryName(path)!);
            File.WriteAllText(path, directory);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            // A protected settings folder should not prevent this capture attempt.
        }
    }

    private static string GameDirectorySettingPath() => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "Sora2 Details", "game-directory.txt");

    private static string? FindLauncher()
    {
        var directory = new DirectoryInfo(AppContext.BaseDirectory);
        for (var depth = 0; depth < 7 && directory is not null; depth++, directory = directory.Parent)
        {
            var path = Path.Combine(directory.FullName, "Start-Sora2Details.ps1");
            if (File.Exists(path)) return path;
        }
        return null;
    }

    private async Task CheckForUpdatesAsync()
    {
        try
        {
            _updateManager ??= new UpdateManager(new GithubSource(
                "https://github.com/rebelshadowrm/Sora2-Details", accessToken: null, prerelease: true));
            _availableUpdate = await _updateManager.CheckForUpdatesAsync();
            UpdateButton.Content = _availableUpdate is null ? "↻" : "↑";
            UpdateButton.ToolTip = _availableUpdate is null
                ? "No newer preview release found; click to check again."
                : "New preview available. Click to download and restart after capture detaches.";
        }
        catch (Exception exception)
        {
            UpdateButton.ToolTip = $"Update check unavailable: {exception.Message}";
        }
    }

    private async void UpdateButton_Click(object sender, RoutedEventArgs e)
    {
        if (_updateBusy) return;
        _updateBusy = true;
        UpdateButton.IsEnabled = false;
        try
        {
            if (_availableUpdate is null)
            {
                await CheckForUpdatesAsync();
                return;
            }
            if (_availableUpdate is null || _updateManager is null) return;
            UpdateButton.ToolTip = "Downloading verified update package...";
            await _updateManager.DownloadUpdatesAsync(_availableUpdate);
            UpdateButton.ToolTip = "Waiting for capture to detach...";
            if (!await EnsureCaptureDetachedAsync())
            {
                UpdateButton.ToolTip = "Update downloaded, but capture did not detach. Stop capture and try again.";
                SetCaptureError(UpdateButton.ToolTip.ToString()!);
                return;
            }
            _updateManager.ApplyUpdatesAndRestart(_availableUpdate);
        }
        catch (Exception exception)
        {
            UpdateButton.ToolTip = $"Update failed: {exception.Message}";
        }
        finally
        {
            _updateBusy = false;
            UpdateButton.IsEnabled = true;
        }
    }

    private static async Task<bool> EnsureCaptureDetachedAsync()
    {
        var currentPath = CurrentCapturePath();
        if (!File.Exists(currentPath)) return true;
        using var json = JsonDocument.Parse(await File.ReadAllTextAsync(currentPath));
        var current = json.RootElement;
        var stopFile = current.GetProperty("stopFile").GetString();
        var trace = current.GetProperty("trace").GetString();
        var bridgePid = current.TryGetProperty("bridgePid", out var bridgeProperty)
            ? bridgeProperty.GetInt32() : 0;
        if (string.IsNullOrWhiteSpace(stopFile) || string.IsNullOrWhiteSpace(trace)) return false;
        Directory.CreateDirectory(Path.GetDirectoryName(stopFile)!);
        await File.WriteAllTextAsync(stopFile, "stop", Encoding.ASCII);
        for (var attempt = 0; attempt < 150; attempt++)
        {
            if (TraceShowsDetach(trace) && !IsProcessRunning(bridgePid)) return true;
            await Task.Delay(200);
        }
        return false;
    }

    private static bool IsProcessRunning(int pid)
    {
        if (pid <= 0) return false;
        try
        {
            using var process = Process.GetProcessById(pid);
            return !process.HasExited;
        }
        catch (Exception exception) when (exception is ArgumentException or
                                        System.ComponentModel.Win32Exception or InvalidOperationException)
        {
            return false;
        }
    }

    private void RefreshCaptureButton()
    {
        RefreshCaptureStatus();
    }

    private static bool CaptureMayBeActive()
    {
        try
        {
            var path = CurrentCapturePath();
            if (!File.Exists(path)) return false;
            using var json = JsonDocument.Parse(File.ReadAllText(path));
            var trace = json.RootElement.GetProperty("trace").GetString();
            return !string.IsNullOrWhiteSpace(trace) && !TraceShowsDetach(trace);
        }
        catch (Exception exception) when (exception is IOException or JsonException or InvalidOperationException or
                                        UnauthorizedAccessException or KeyNotFoundException)
        {
            return File.Exists(CurrentCapturePath());
        }
    }

    private string? ActiveTraceName()
    {
        try
        {
            var path = CurrentCapturePath();
            if (!File.Exists(path)) return null;
            using var json = JsonDocument.Parse(File.ReadAllText(path));
            var root = json.RootElement;
            var trace = root.GetProperty("trace").GetString();
            if (string.IsNullOrWhiteSpace(trace) || TraceShowsDetach(trace)) return null;
            var bridgePid = root.GetProperty("bridgePid").GetInt32();
            using var bridge = Process.GetProcessById(bridgePid);
            return bridge.HasExited ? null : Path.GetFileName(trace);
        }
        catch (Exception exception) when (exception is IOException or JsonException or InvalidOperationException or
                                        ArgumentException or System.ComponentModel.Win32Exception)
        {
            return null;
        }
    }

    private DateTimeOffset? ActiveSessionResetAt()
    {
        try
        {
            var traceName = ActiveTraceName();
            if (traceName is null) return null;
            var marker = Path.Combine(Path.GetDirectoryName(CurrentCapturePath())!,
                Path.ChangeExtension(traceName, ".reset.json"));
            if (!File.Exists(marker)) return null;
            using var json = JsonDocument.Parse(File.ReadAllText(marker));
            var at = json.RootElement.GetProperty("at").GetString();
            return DateTimeOffset.TryParse(at, out var parsed) ? parsed : null;
        }
        catch (Exception exception) when (exception is IOException or JsonException or
                                        InvalidOperationException or UnauthorizedAccessException or KeyNotFoundException)
        {
            return null;
        }
    }

    private static string CurrentCapturePath()
    {
        var dataDir = Environment.GetEnvironmentVariable("SORA2_DETAILS_DATA_DIR")
            ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Sora2 Details");
        return Path.Combine(dataDir, "live", "current.json");
    }

    private static bool TraceShowsDetach(string path)
    {
        try
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
            var length = (int)Math.Min(stream.Length, 65536);
            stream.Seek(-length, SeekOrigin.End);
            var buffer = new byte[length];
            stream.ReadExactly(buffer);
            var tail = Encoding.UTF8.GetString(buffer);
            return tail.Contains("\"kind\": \"detached\"", StringComparison.Ordinal)
                || tail.Contains("\"kind\": \"detached_after_error\"", StringComparison.Ordinal)
                || tail.Contains("\"kind\": \"target_exited\"", StringComparison.Ordinal);
        }
        catch (IOException) { return false; }
    }
}
