using System.IO;
using System.Text.Json;
using System.Windows;
using Microsoft.Win32;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public partial class MainWindow
{
    private static bool IsCurrentTranscriptCapture()
    {
        try
        {
            if (!File.Exists(CurrentCapturePath())) return false;
            using var json = JsonDocument.Parse(File.ReadAllText(CurrentCapturePath()));
            return json.RootElement.TryGetProperty("captureProfile", out var profile) &&
                profile.GetString() == "Transcript";
        }
        catch (Exception error) when (error is IOException or JsonException or UnauthorizedAccessException or InvalidOperationException)
        { return false; }
    }

    private async Task OpenResearchTranscriptAsync()
    {
        if (IsCurrentTranscriptCapture() && CaptureMayBeActive())
        {
            try
            {
                using var current = JsonDocument.Parse(await File.ReadAllTextAsync(CurrentCapturePath()));
                if (current.RootElement.TryGetProperty("ledgerPath", out var ledger) && ledger.GetString() is { } path)
                {
                    await ShowResearchTranscriptAsync(path);
                    return;
                }
            }
            catch (Exception error) when (error is IOException or JsonException or UnauthorizedAccessException or InvalidOperationException)
            { /* Capture may have stopped between reading its profile and its ledger path. Open saved history instead. */ }
        }
        var dialog = new OpenFileDialog { Title = "Open recorded action stream",
            Filter = "Research ledger (ledger-*.json)|ledger-*.json|JSON files|*.json" };
        var directory = Path.Combine(Environment.GetEnvironmentVariable("SORA2_DETAILS_DATA_DIR")
            ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Sora2 Details"),
            "research", "action-stream");
        if (Directory.Exists(directory)) dialog.InitialDirectory = directory;
        if (dialog.ShowDialog(this) != true) return;
        await ShowResearchTranscriptAsync(dialog.FileName);
    }

    private async Task ShowResearchTranscriptAsync(string path)
    {
        try
        {
            var transcript = await Task.Run(() => ResearchTranscript.Load(path));
            new ResearchTranscriptWindow(transcript, path) { Owner = this }.Show();
        }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or
            JsonException or InvalidOperationException or KeyNotFoundException or FormatException)
        {
            MessageBox.Show(this, $"Could not open recorded stream: {exception.Message}",
                "Recorded action stream", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }
}
