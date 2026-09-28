using System.Diagnostics;
using System.IO;
using System.Text;
using System.Text.Json;
using System.Windows;
using Velopack;
using Velopack.Sources;

namespace Sora2.Details.Desktop;

public partial class MainWindow
{
    private UpdateManager? _updateManager;
    private UpdateInfo? _availableUpdate;
    private bool _updateBusy;
    private bool _captureBusy;

    private async void CaptureButton_Click(object sender, RoutedEventArgs e)
    {
        if (_captureBusy) return;
        if (CaptureButton.Content?.ToString() == "■")
        {
            _captureBusy = true;
            CaptureButton.ToolTip = "Detaching capture...";
            try
            {
                var detached = await EnsureCaptureDetachedAsync();
                CaptureButton.ToolTip = detached ? "Capture detached." : "Capture did not detach; try Stop-Sora2Details.cmd.";
                if (detached) CaptureButton.Content = "●";
            }
            catch (Exception exception) { CaptureButton.ToolTip = $"Stop failed: {exception.Message}"; }
            finally { _captureBusy = false; }
            return;
        }
        var launcher = FindLauncher();
        if (launcher is null)
        {
            CaptureButton.ToolTip = "Capture launcher is missing from this package.";
            return;
        }
        _captureBusy = true;
        CaptureButton.ToolTip = "Starting capture; Windows may request administrator approval.";
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
            foreach (var argument in new[] { "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", launcher, "-CaptureOnly" })
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
            CaptureButton.Content = process.ExitCode == 0 ? "■" : "●";
        }
        catch (Exception exception)
        {
            CaptureButton.ToolTip = $"Capture could not start: {exception.Message}";
        }
        finally { _captureBusy = false; }
    }

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
            if (_availableUpdate is null) await CheckForUpdatesAsync();
            if (_availableUpdate is null || _updateManager is null) return;
            UpdateButton.ToolTip = "Downloading verified update package...";
            await _updateManager.DownloadUpdatesAsync(_availableUpdate);
            UpdateButton.ToolTip = "Waiting for capture to detach...";
            if (!await EnsureCaptureDetachedAsync())
            {
                UpdateButton.ToolTip = "Update downloaded, but capture did not detach. Stop capture and try again.";
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
        if (string.IsNullOrWhiteSpace(stopFile) || string.IsNullOrWhiteSpace(trace)) return false;
        Directory.CreateDirectory(Path.GetDirectoryName(stopFile)!);
        await File.WriteAllTextAsync(stopFile, "stop", Encoding.ASCII);
        for (var attempt = 0; attempt < 150; attempt++)
        {
            if (TraceShowsDetach(trace)) return true;
            await Task.Delay(200);
        }
        return false;
    }

    private void RefreshCaptureButton()
    {
        try
        {
            var path = CurrentCapturePath();
            if (!File.Exists(path)) return;
            using var json = JsonDocument.Parse(File.ReadAllText(path));
            var trace = json.RootElement.GetProperty("trace").GetString();
            if (trace is null || TraceShowsDetach(trace)) return;
            CaptureButton.Content = "■";
            CaptureButton.ToolTip = "Stop the current capture cleanly.";
        }
        catch (Exception) { /* An old or partial session record is not a live capture. */ }
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
                || tail.Contains("\"kind\": \"detached_after_error\"", StringComparison.Ordinal);
        }
        catch (IOException) { return false; }
    }
}
