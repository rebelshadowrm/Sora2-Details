using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Threading;
using System.IO;
using System.Text.Json;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public sealed class ResearchTranscriptWindow : Window
{
    public event Action<ResearchTranscript>? SnapshotApplied;
    public ResearchTranscriptWindow(ResearchTranscript transcript, string? ledgerPath = null)
    {
        Title = $"Recorded action stream — {transcript.BatchId}";
        Width = 1050; Height = 650; MinWidth = 650; MinHeight = 400;
        Background = new SolidColorBrush(Color.FromRgb(27, 30, 35));
        Foreground = Brushes.White;
        var layout = new DockPanel { Margin = new Thickness(12) };
        var heading = new TextBlock
        {
            Text = $"PARTIAL RESEARCH · {transcript.Actions.Count} action candidates · {transcript.Entries.Count:N0} observations\n" +
                   (transcript.SourceVerified ? "Raw source verified" : "Embedded observations; raw source unavailable"),
            Margin = new Thickness(0, 0, 0, 10), Foreground = Brushes.Khaki,
            ToolTip = string.Join(Environment.NewLine, transcript.CoverageGaps)
        };
        DockPanel.SetDock(heading, Dock.Top); layout.Children.Add(heading);
        var intervalChoice = new ComboBox { Name = "ResearchIntervalChoice", Margin = new Thickness(0, 0, 0, 8) };
        DockPanel.SetDock(intervalChoice, Dock.Top); layout.Children.Add(intervalChoice);
        string? selectedInterval = null;
        bool Matches(string? id) => selectedInterval is null ||
            (selectedInterval == "$unframed" ? id is null : id == selectedInterval);
        void IntervalChoices()
        {
            intervalChoice.Items.Clear();
            intervalChoice.Items.Add(new ComboBoxItem { Content = "All records (including unframed)", Tag = null });
            intervalChoice.Items.Add(new ComboBoxItem { Content = "Outside recorded engine intervals / unframed", Tag = "$unframed" });
            foreach (var interval in transcript.Intervals)
                intervalChoice.Items.Add(new ComboBoxItem { Tag = interval.Id,
                    Content = $"{interval.StartedAt?.ToLocalTime():HH:mm:ss}–{interval.EndedAt?.ToLocalTime():HH:mm:ss} · " +
                        (interval.Scope == "CommandStagesObservedCandidate" ? "Command stages observed (candidate)" : "Unclassified engine battle") +
                        $" · raw flags {interval.RawInitializerFlags ?? "unknown"} · exit argument {interval.RawExitArgument?.ToString() ?? "unknown"}" +
                        (interval.OutcomeCandidate is { } outcome ? $" · {outcome} (candidate)" : "") });
            intervalChoice.SelectedItem = intervalChoice.Items.Cast<ComboBoxItem>().FirstOrDefault(i => (string?)i.Tag == selectedInterval)
                ?? intervalChoice.Items[0];
        }
        var rawDetails = new TextBox { IsReadOnly = true, AcceptsReturn = true, TextWrapping = TextWrapping.NoWrap,
            Height = 160, VerticalScrollBarVisibility = ScrollBarVisibility.Auto,
            HorizontalScrollBarVisibility = ScrollBarVisibility.Auto, FontFamily = new FontFamily("Consolas") };
        DockPanel.SetDock(rawDetails, Dock.Bottom); layout.Children.Add(rawDetails);
        var tabs = new TabControl();
        var actions = Grid();
        actions.Name = "ActionEntries";
        object[] ActionRows() => transcript.Actions.Where(a => Matches(a.IntervalId)).Select(a => new
        {
            Time = transcript.Entries.First(e => e.Id == a.ObservationId).At?.ToLocalTime().ToString("HH:mm:ss.fff"),
            Actor = a.ActorNameCandidate ?? a.ActorPointer ?? "Unknown actor", Move = a.MoveNameCandidate is { } name ? $"{name} (candidate)" : a.RawMoveId ?? "Unknown move",
            Targets = string.IsNullOrWhiteSpace(a.Targets) ? "Unknown" : a.Targets,
            Stage = a.Stage, EffectCalls = a.EffectObservationCount, ActionId = a.Id, a.ObservationId
        }).ToArray();
        actions.ItemsSource = ActionRows();
        actions.SelectionChanged += (_, _) =>
        {
            if (actions.SelectedItem is not { } selected) return;
            var id = selected.GetType().GetProperty("ActionId")!.GetValue(selected) as string;
            rawDetails.Text = string.Join(Environment.NewLine, transcript.Entries.Where(e => e.ActionCandidateId == id)
                .Select(e => e.Raw.GetRawText()));
        };
        var observations = Grid();
        observations.Name = "ObservationEntries";
        object[] ObservationRows() => transcript.Entries.Where(e => Matches(e.IntervalId)).Select(e => new
        {
            e.Sequence, Time = e.At?.ToLocalTime().ToString("HH:mm:ss.fff"), e.Kind,
            SourceCandidate = e.SourceCandidate ?? "Unknown", MoveCandidate = e.MoveCandidate ?? "Unknown", TargetCandidate = e.TargetCandidate ?? "Unknown",
            ConditionsCandidate = e.ConditionsCandidate ?? "Unknown",
            ConditionChangeCandidate = e.ConditionChangeCandidate ?? "Unknown",
            Hook = e.Hook ?? "Capture marker", Action = e.ActionCandidateId ?? "Unassigned", e.Id
        }).ToArray();
        observations.ItemsSource = ObservationRows();
        observations.SelectionChanged += (_, _) =>
        {
            if (observations.SelectedItem is not { } selected) return;
            var id = selected.GetType().GetProperty("Id")!.GetValue(selected) as string;
            rawDetails.Text = transcript.Entries.First(e => e.Id == id).Raw.GetRawText();
        };
        tabs.Items.Add(new TabItem { Header = "Action candidates", Content = actions });
        tabs.Items.Add(new TabItem { Header = "All observations", Content = observations });
        layout.Children.Add(tabs); Content = layout;
        intervalChoice.SelectionChanged += (_, _) =>
        {
            selectedInterval = (intervalChoice.SelectedItem as ComboBoxItem)?.Tag as string;
            actions.ItemsSource = ActionRows();
            observations.ItemsSource = ObservationRows();
            rawDetails.Clear();
        };
        IntervalChoices();
        if (ledgerPath is not null)
        {
            var timer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(1) };
            var busy = false;
            var closed = false;
            var lastWrite = File.GetLastWriteTimeUtc(ledgerPath);
            timer.Tick += async (_, _) =>
            {
                if (busy || File.GetLastWriteTimeUtc(ledgerPath) == lastWrite) return;
                busy = true;
                try
                {
                    var stamp = File.GetLastWriteTimeUtc(ledgerPath);
                    var updated = await Task.Run(() => ResearchTranscript.Load(ledgerPath));
                    if (closed) return;
                    var actionIndex = actions.SelectedIndex;
                    var observationIndex = observations.SelectedIndex;
                    transcript = updated;
                    var previousInterval = selectedInterval;
                    IntervalChoices();
                    intervalChoice.SelectedItem = intervalChoice.Items.Cast<ComboBoxItem>().FirstOrDefault(i => (string?)i.Tag == previousInterval)
                        ?? intervalChoice.Items[0];
                    actions.ItemsSource = ActionRows();
                    observations.ItemsSource = ObservationRows();
                    actions.SelectedIndex = actionIndex;
                    observations.SelectedIndex = observationIndex;
                    heading.Text = $"PARTIAL RESEARCH · {transcript.Actions.Count} action candidates · {transcript.Entries.Count:N0} observations\n" +
                        (transcript.SourceVerified ? "Raw source verified" : "Embedded observations; raw source unavailable");
                    heading.ToolTip = string.Join(Environment.NewLine, transcript.CoverageGaps);
                    lastWrite = stamp;
                    SnapshotApplied?.Invoke(transcript);
                }
                catch (Exception error) when (error is IOException or UnauthorizedAccessException or JsonException or
                    InvalidOperationException or KeyNotFoundException or FormatException)
                {
                    if (!closed) heading.ToolTip = $"Last valid snapshot retained. Refresh failed: {error.Message}";
                }
                finally { busy = false; }
            };
            Closed += (_, _) => { closed = true; timer.Stop(); };
            timer.Start();
        }
    }

    private static DataGrid Grid()
    {
        var grid = new DataGrid { IsReadOnly = true, AutoGenerateColumns = true,
            CanUserAddRows = false, CanUserDeleteRows = false, EnableRowVirtualization = true,
            SelectionMode = DataGridSelectionMode.Single };
        grid.AutoGeneratingColumn += (_, e) =>
        {
            if (e.PropertyName is "ActionId" or "ObservationId" or "Id") e.Cancel = true;
            if (e.PropertyName == "EffectCalls") e.Column.Header = "Effect calls";
        };
        return grid;
    }
}
