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
    private string? _captureStartCancelPath;
    private string? _captureStatusError;

    private bool LiveCaptureDisabled => _researchMode ||
        Environment.GetEnvironmentVariable("SORA2_DETAILS_METER_ONLY") == "1";

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
        var traceName = ActiveTraceName();
        var missingBridge = active && traceName is null && !_captureStarting;
        var capturing = active && traceName is not null;
        var gameRunning = GetGamePids().Length > 0;
        var state = _researchMode ? "Replay" :
            Environment.GetEnvironmentVariable("SORA2_DETAILS_METER_ONLY") == "1" ? "Meter only" :
            _captureStatusError is not null || _captureError is not null || missingBridge ? "Error" :
            _captureStopping ? "Stopping capture" : capturing ? "Capturing" :
            _captureStarting || active ? "Starting capture" : gameRunning ? "Ready" : "Waiting for game";
        DataSourceLabel.Text = state;
        DataSourceLabel.Foreground = state == "Error" ? Brushes.OrangeRed :
            state == "Capturing" ? Brushes.LightGreen : Brushes.Goldenrod;
        var detail = _captureStatusError ?? _captureError ?? (missingBridge
            ? "Capture may still be attached. Choose Stop capture from the tray to finish cleanup."
            : state switch
        {
            "Capturing" => "Capturing partial command-battle data. Manage capture from the Sora 2 Details tray menu.",
            "Stopping capture" => "Stopping capture and disconnecting from the game.",
            "Starting capture" => "Connecting to the game to begin capture.",
            "Replay" => "Showing a saved replay. Live capture is off.",
            "Meter only" => "Meter-only mode is on. Live capture is off.",
            "Ready" => "The game is running. Choose Start capture from the Sora 2 Details tray menu.",
            _ => "Waiting for Trails in the Sky 2nd Chapter. Saved encounters remain available from the tray."
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

    private async Task StopCaptureAsync()
    {
        if (_captureBusy || _updateBusy) return;
        _captureBusy = true;
        _captureStopping = true;
        RefreshCaptureStatus();
        try
        {
            var detached = await EnsureCaptureDetachedAsync();
            if (detached)
            {
                _captureStatusError = null;
                _selectedEncounter = null;
                _followNewest = true;
                ReloadHistory();
                RenderMeter();
            }
            else SetCaptureError("Capture did not fully detach within 30 seconds. Try Stop again after the helper exits.");
        }
        catch (Exception exception) { SetCaptureError($"Stop failed: {exception.Message}"); }
        finally
        {
            _captureBusy = false;
            _captureStopping = false;
            RefreshCaptureStatus();
            RefreshTrayCommands();
            if (_closeWhenReady)
            {
                _closeWhenReady = false;
                _ = Dispatcher.BeginInvoke(Close);
            }
        }
    }

    private async Task StartCaptureAsync(int? expectedPid = null)
    {
        if (_updateBusy) return;
        if (_captureBusy || ActiveTraceName() is not null) return;
        if (LiveCaptureDisabled) return;
        if (CaptureMayBeActive())
        {
            SetCaptureError("The previous capture hasn't finished closing. Choose Stop capture from the tray and try again.");
            return;
        }
        var launcher = FindLauncher();
        if (launcher is null)
        {
            SetCaptureError("Capture could not start because a required file is missing.");
            return;
        }
        var games = Process.GetProcessesByName("sora_2nd");
        string? gameDirectory;
        var targetPid = 0;
        try
        {
            if (games.Length != 1)
            {
                if (games.Length > 1)
                    SetCaptureError("More than one game process is running. Close the extra one and try again.");
                else
                    RefreshCaptureStatus();
                return;
            }
            targetPid = games[0].Id;
            if (expectedPid is { } expected && expected != targetPid)
            {
                SetCaptureError("The game changed before capture could start. Try again from the tray.");
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
                SetCaptureError("The game location wasn't selected, so capture didn't start.");
                return;
            }
            gameDirectory = Path.GetDirectoryName(picker.FileName);
        }
        if (gameDirectory is null) return;
        _captureBusy = true;
        _captureStarting = true;
        _currentGamePid = targetPid;
        RefreshCaptureStatus();
        try
        {
            var liveDirectory = Path.Combine(MeterDataDirectory.PathName, "live");
            Directory.CreateDirectory(liveDirectory);
            _captureStartCancelPath = Path.Combine(liveDirectory, $"start-cancel-{Guid.NewGuid():N}");
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
            if (int.TryParse(Environment.GetEnvironmentVariable("SORA2_DETAILS_CAPTURE_HOURS"), out var hours) &&
                hours is >= 2 and <= 12)
            {
                start.ArgumentList.Add("-Hours");
                start.ArgumentList.Add(hours.ToString());
            }
            var pythonPath = Environment.GetEnvironmentVariable("SORA2_DETAILS_PYTHON_PATH");
            if (!string.IsNullOrWhiteSpace(pythonPath))
            {
                start.ArgumentList.Add("-PythonPath");
                start.ArgumentList.Add(pythonPath);
            }
            start.Environment["SORA2_DETAILS_CAPTURE_START_CANCEL_FILE"] = _captureStartCancelPath;
            using var process = new Process { StartInfo = start };
            var outputBuilder = new StringBuilder();
            var errorBuilder = new StringBuilder();
            var outputEnded = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
            var errorEnded = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
            process.OutputDataReceived += (_, eventArgs) =>
            {
                if (eventArgs.Data is null) outputEnded.TrySetResult(true);
                else lock (outputBuilder) outputBuilder.AppendLine(eventArgs.Data);
            };
            process.ErrorDataReceived += (_, eventArgs) =>
            {
                if (eventArgs.Data is null) errorEnded.TrySetResult(true);
                else lock (errorBuilder) errorBuilder.AppendLine(eventArgs.Data);
            };
            if (!process.Start()) throw new IOException("PowerShell did not start.");
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            // WaitForExitAsync also waits for redirected output EOF. A long-lived probe child
            // can inherit those pipe handles, so watch the launcher process itself instead.
            while (!process.HasExited) await Task.Delay(50);
            // Drain briefly for final lines, then cancel reads instead of waiting for child EOF.
            await Task.WhenAny(Task.WhenAll(outputEnded.Task, errorEnded.Task), Task.Delay(250));
            process.CancelOutputRead();
            process.CancelErrorRead();
            string output;
            string error;
            lock (outputBuilder) output = outputBuilder.ToString().Trim();
            lock (errorBuilder) error = errorBuilder.ToString().Trim();
            if (process.ExitCode == 0)
            {
                RememberGameDirectory(gameDirectory);
                _captureStatusError = null;
                _followNewest = true;
                ReloadHistory();
            }
            else if (!CaptureStartCancellationRequested())
                SetCaptureError($"Capture could not start: {(string.IsNullOrEmpty(error) ? output : error)}");
        }
        catch (Exception exception)
        {
            if (!CaptureStartCancellationRequested())
                SetCaptureError($"Capture could not start: {exception.Message}");
        }
        finally
        {
            if (_captureStartCancelPath is { } cancelPath)
            {
                try { File.Delete(cancelPath); }
                catch (IOException) { }
                catch (UnauthorizedAccessException) { }
            }
            _captureStartCancelPath = null;
            _captureBusy = false;
            _captureStarting = false;
            RefreshCaptureStatus();
            RefreshTrayCommands();
            if (_closeWhenReady)
            {
                _closeWhenReady = false;
                _ = Dispatcher.BeginInvoke(Close);
            }
        }
    }

    private bool CaptureStartCancellationRequested()
    {
        try { return _captureStartCancelPath is { } path && File.Exists(path); }
        catch (IOException) { return false; }
        catch (UnauthorizedAccessException) { return false; }
    }

    private static int[] GetGamePids()
    {
        Process[] processes;
        try { processes = Process.GetProcessesByName("sora_2nd"); }
        catch (System.ComponentModel.Win32Exception) { return []; }
        try
        {
            var ids = new List<int>(processes.Length);
            foreach (var process in processes)
            {
                try { ids.Add(process.Id); }
                catch (InvalidOperationException) { }
            }
            return ids.ToArray();
        }
        finally { foreach (var process in processes) process.Dispose(); }
    }

    private static string? ResolveGameDirectory(Process game)
    {
        var configuredDirectory = Environment.GetEnvironmentVariable("SORA2_DETAILS_GAME_DIRECTORY");
        if (!string.IsNullOrWhiteSpace(configuredDirectory) &&
            File.Exists(Path.Combine(configuredDirectory, "sora_2nd.exe")))
            return configuredDirectory;
        try
        {
            var runningExe = game.MainModule?.FileName;
            if (runningExe is not null && File.Exists(runningExe))
                return Path.GetDirectoryName(runningExe);
        }
        catch (Exception exception) when (exception is System.ComponentModel.Win32Exception or
                                           InvalidOperationException or UnauthorizedAccessException)
        {
            // Use a saved path or ask the player if Windows still hides this process path.
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
                : "New preview available. Click again to update after confirming capture will stop and the app will restart.";
        }
        catch (Exception exception)
        {
            UpdateButton.ToolTip = $"Update check unavailable: {exception.Message}";
        }
    }

    private async void UpdateButton_Click(object sender, RoutedEventArgs e)
    {
        if (_captureBusy || _updateBusy)
        {
            UpdateButton.ToolTip = "Wait for capture or another update operation to finish before updating.";
            return;
        }
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
            var captureActive = CaptureMayBeActive();
            if (captureActive)
            {
                var answer = MessageBox.Show(this,
                    "Updating now will stop capture, install the update, and restart Sora 2 Details. " +
                    "Capture will resume if the game is still running. You can wait until the current battle ends.\n\n" +
                    "Update now?",
                    "Update Sora 2 Details", MessageBoxButton.YesNo, MessageBoxImage.Warning,
                    MessageBoxResult.No);
                if (answer != MessageBoxResult.Yes) return;
            }
            UpdateButton.ToolTip = "Waiting for capture to detach...";
            if (!await EnsureCaptureDetachedAsync())
            {
                UpdateButton.ToolTip = "Capture cleanup could not be confirmed. The update was not installed.";
                SetCaptureError(UpdateButton.ToolTip.ToString()!);
                return;
            }
            UpdateButton.ToolTip = "Downloading verified update package...";
            await _updateManager.DownloadUpdatesAsync(_availableUpdate);
            _updateManager.ApplyUpdatesAndRestart(_availableUpdate,
                BuildRestartArguments());
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

    private static string[] BuildRestartArguments()
    {
        var arguments = new List<string> { "--data-dir", MeterDataDirectory.PathName };
        var hours = Environment.GetEnvironmentVariable("SORA2_DETAILS_CAPTURE_HOURS");
        if (int.TryParse(hours, out var captureHours) && captureHours is >= 2 and <= 12)
            arguments.AddRange(["--capture-hours", captureHours.ToString()]);
        var captureProfile = Environment.GetEnvironmentVariable("SORA2_DETAILS_CAPTURE_PROFILE");
        if (captureProfile is "Live" or "HealingResearch")
            arguments.AddRange(["--capture-profile", captureProfile]);
        var gameDirectory = Environment.GetEnvironmentVariable("SORA2_DETAILS_GAME_DIRECTORY");
        if (!string.IsNullOrWhiteSpace(gameDirectory))
            arguments.AddRange(["--game-directory", gameDirectory]);
        var pythonPath = Environment.GetEnvironmentVariable("SORA2_DETAILS_PYTHON_PATH");
        if (!string.IsNullOrWhiteSpace(pythonPath))
            arguments.AddRange(["--python-path", pythonPath]);
        if (Environment.GetEnvironmentVariable("SORA2_DETAILS_METER_ONLY") == "1")
            arguments.Add("--meter-only");
        return arguments.ToArray();
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
        var serverPid = current.TryGetProperty("serverPid", out var serverProperty)
            ? serverProperty.GetInt32() : 0;
        var hostPid = current.TryGetProperty("hostPid", out var hostProperty)
            ? hostProperty.GetInt32() : 0;
        var sessionId = current.TryGetProperty("sessionId", out var sessionProperty)
            ? sessionProperty.GetString() : null;
        var requestId = current.TryGetProperty("requestId", out var requestProperty)
            ? requestProperty.GetString() : null;
        if (string.IsNullOrWhiteSpace(stopFile) || string.IsNullOrWhiteSpace(trace)) return false;
        Directory.CreateDirectory(Path.GetDirectoryName(stopFile)!);
        try { await File.WriteAllTextAsync(stopFile, "stop", Encoding.ASCII); }
        catch (IOException) when (TraceShowsDetach(trace)) { }
        for (var attempt = 0; attempt < 150; attempt++)
        {
            var safelyFinished = TraceShowsDetach(trace) || ProbeFailedBeforeAttach(requestId, trace);
            if (safelyFinished && !IsProcessRunning(bridgePid) &&
                !IsProcessRunning(serverPid) && !IsProcessRunning(hostPid))
            {
                if (!TryDelete(currentPath)) return false;
                TryDelete(stopFile);
                DeleteReadyRecord(sessionId);
                return true;
            }
            await Task.Delay(200);
        }
        return false;
    }

    private static bool TryDelete(string path)
    {
        try
        {
            File.Delete(path);
            return !File.Exists(path);
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            return !File.Exists(path);
        }
    }

    private static void DeleteReadyRecord(string? sessionId)
    {
        if (string.IsNullOrWhiteSpace(sessionId)) return;
        try
        {
            var readyPath = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(CurrentCapturePath())!, "..",
                "probe-session", "ready.json"));
            if (!File.Exists(readyPath)) return;
            using var ready = JsonDocument.Parse(File.ReadAllText(readyPath));
            if (ready.RootElement.TryGetProperty("sessionId", out var id) &&
                id.GetString() == sessionId && ready.RootElement.TryGetProperty("stopped", out var stopped) &&
                stopped.GetBoolean())
                TryDelete(readyPath);
        }
        catch (Exception exception) when (exception is IOException or JsonException or UnauthorizedAccessException or InvalidOperationException)
        {
            // The next launch validates the PID/session record before reuse.
        }
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

    private static bool CaptureMayBeActive()
    {
        try
        {
            var path = CurrentCapturePath();
            if (!File.Exists(path)) return false;
            using var json = JsonDocument.Parse(File.ReadAllText(path));
            var trace = json.RootElement.GetProperty("trace").GetString();
            var bridgePid = json.RootElement.TryGetProperty("bridgePid", out var bridge)
                ? bridge.GetInt32() : 0;
            var serverPid = json.RootElement.TryGetProperty("serverPid", out var server)
                ? server.GetInt32() : 0;
            var hostPid = json.RootElement.TryGetProperty("hostPid", out var host)
                ? host.GetInt32() : 0;
            var requestId = json.RootElement.TryGetProperty("requestId", out var request)
                ? request.GetString() : null;
            var safelyFinished = TraceShowsDetach(trace ?? "") || ProbeFailedBeforeAttach(requestId, trace ?? "");
            return !string.IsNullOrWhiteSpace(trace) &&
                (!safelyFinished || IsProcessRunning(bridgePid) ||
                 IsProcessRunning(serverPid) || IsProcessRunning(hostPid));
        }
        catch (Exception exception) when (exception is IOException or JsonException or InvalidOperationException or
                                        UnauthorizedAccessException or KeyNotFoundException)
        {
            return File.Exists(CurrentCapturePath());
        }
    }

    private static bool ProbeFailedBeforeAttach(string? requestId, string tracePath)
    {
        if (string.IsNullOrWhiteSpace(requestId) || File.Exists(tracePath)) return false;
        try
        {
            var resultsPath = Path.GetFullPath(Path.Combine(Path.GetDirectoryName(CurrentCapturePath())!, "..",
                "probe-session", "results", requestId + ".json"));
            if (!File.Exists(resultsPath)) return false;
            using var result = JsonDocument.Parse(File.ReadAllText(resultsPath));
            return result.RootElement.TryGetProperty("ok", out var ok) && ok.ValueKind == JsonValueKind.False;
        }
        catch (Exception exception) when (exception is IOException or JsonException or UnauthorizedAccessException or InvalidOperationException)
        {
            return false;
        }
    }

    private static int? CurrentCaptureTargetPid()
    {
        try
        {
            var path = CurrentCapturePath();
            if (!File.Exists(path)) return null;
            using var json = JsonDocument.Parse(File.ReadAllText(path));
            return json.RootElement.TryGetProperty("targetPid", out var pid) ? pid.GetInt32() : null;
        }
        catch (Exception exception) when (exception is IOException or JsonException or UnauthorizedAccessException or InvalidOperationException)
        {
            return null;
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
