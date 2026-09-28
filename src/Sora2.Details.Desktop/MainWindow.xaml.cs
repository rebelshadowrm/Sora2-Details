using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Threading;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public partial class MainWindow : Window
{
    private readonly EncounterStore _store;
    private readonly FileSystemWatcher _historyWatcher;
    private readonly CancellationTokenSource _captureCancellation = new();
    private readonly Task _captureTask;
    private IReadOnlyList<Encounter> _encounters = [];
    private bool _sampleMode = true;
    private readonly bool _researchMode;
    private string? _captureError;
    private Encounter? _selectedEncounter;
    private bool _followNewest = true;
    private MeterMode _mode = MeterMode.Damage;
    private string? _sourceKey;
    private string? _moveKey;
    private readonly DispatcherTimer _placementSaveTimer = new() { Interval = TimeSpan.FromMilliseconds(400) };
    private bool _placementReady;

    public MainWindow()
    {
        InitializeComponent();
        if (MeterWindowPlacement.Load() is { } placement)
        {
            WindowStartupLocation = WindowStartupLocation.Manual;
            Left = placement.Left;
            Top = placement.Top;
            Width = placement.Width;
            Height = placement.Height;
        }
        _placementSaveTimer.Tick += (_, _) =>
        {
            _placementSaveTimer.Stop();
            SavePlacement();
        };
        Loaded += (_, _) => _placementReady = true;
        LocationChanged += (_, _) => QueuePlacementSave();
        SizeChanged += (_, _) => QueuePlacementSave();
        Closing += (_, _) =>
        {
            _placementSaveTimer.Stop();
            SavePlacement();
        };
        var historyPath = System.IO.Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Sora2 Details", "encounters");
        System.IO.Directory.CreateDirectory(historyPath);
        _store = new EncounterStore(historyPath);
        var samplePath = System.IO.Path.Combine(AppContext.BaseDirectory, "samples", "command-battles.json");
        var researchPath = Environment.GetEnvironmentVariable("SORA2_DETAILS_RESEARCH_REPLAY");
        _researchMode = !string.IsNullOrWhiteSpace(researchPath);
        _encounters = EncounterReplay.Load(_researchMode ? researchPath! : samplePath);
        ReloadHistory();
        _historyWatcher = new FileSystemWatcher(historyPath, "*.json") { EnableRaisingEvents = true };
        _historyWatcher.Created += (_, _) => Dispatcher.BeginInvoke(ReloadHistory);
        _historyWatcher.Changed += (_, _) => Dispatcher.BeginInvoke(ReloadHistory);
        _historyWatcher.Renamed += (_, _) => Dispatcher.BeginInvoke(ReloadHistory);
        _captureTask = _researchMode ? Task.CompletedTask : Task.Run(ReceiveCaptureAsync);
        Closed += (_, _) =>
        {
            _captureCancellation.Cancel();
            _captureTask.GetAwaiter().GetResult();
            _captureCancellation.Dispose();
            _historyWatcher.Dispose();
        };
    }

    private void QueuePlacementSave()
    {
        if (!_placementReady || WindowState != WindowState.Normal) return;
        _placementSaveTimer.Stop();
        _placementSaveTimer.Start();
    }

    private void SavePlacement()
    {
        if (!_placementReady) return;
        var bounds = WindowState == WindowState.Normal
            ? new Rect(Left, Top, ActualWidth, ActualHeight)
            : RestoreBounds;
        try { MeterWindowPlacement.Save(bounds); }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            // Window preferences are optional; a protected settings folder must not close the meter.
        }
    }

    private async Task ReceiveCaptureAsync()
    {
        try
        {
            var recorder = new EncounterRecorder(_store);
            await recorder.RunAsync(new CapturePipeSource(), _captureCancellation.Token);
        }
        catch (OperationCanceledException) when (_captureCancellation.IsCancellationRequested) { }
        catch (Exception exception)
        {
            _captureError = exception.Message;
            if (!Dispatcher.HasShutdownStarted) _ = Dispatcher.BeginInvoke(RenderMeter);
        }
    }

    private void ReloadHistory()
    {
        if (_researchMode)
        {
            DataSourceLabel.Text = "RESEARCH";
            DataSourceLabel.ToolTip = "Partial research replay of observed live HP changes; see the encounter issues for coverage limits.";
            SelectEncounter(_encounters.FirstOrDefault(e => e.Id == _selectedEncounter?.Id)
                ?? _encounters.OrderByDescending(e => e.StartedAt).FirstOrDefault());
            return;
        }
        IReadOnlyList<Encounter> recorded;
        try { recorded = _store.LoadAll(); }
        catch (System.IO.IOException) { return; } // A writer may still be replacing a snapshot.
        if (recorded.Count > 0)
        {
            _encounters = recorded;
            _sampleMode = false;
        }
        DataSourceLabel.Text = _captureError is not null ? "ERROR" : _sampleMode ? "SAMPLE" : "RECORDED";
        DataSourceLabel.ToolTip = _captureError ?? (_sampleMode
            ? "Sample replay. No game capture adapter is connected."
            : "Saved encounter history.");
        var newest = _encounters.OrderByDescending(e => e.StartedAt).FirstOrDefault();
        SelectEncounter(_followNewest ? newest :
            _encounters.FirstOrDefault(e => e.Id == _selectedEncounter?.Id) ?? newest);
    }

    private void SelectEncounter(Encounter? encounter)
    {
        if (_selectedEncounter?.Id != encounter?.Id) ResetDrill();
        _selectedEncounter = encounter;
        RenderMeter();
    }

    private void ResetDrill()
    {
        _sourceKey = null;
        _moveKey = null;
    }

    private void RenderMeter()
    {
        if (_captureError is not null)
        {
            DataSourceLabel.Text = "ERROR";
            DataSourceLabel.ToolTip = _captureError;
        }
        ModeButton.Content = _mode switch
        {
            MeterMode.Damage => "Damage Done  ▾",
            MeterMode.Healing => "Healing Done  ▾",
            MeterMode.Taken => "Damage Taken  ▾",
            MeterMode.Deaths => "Deaths  ▾",
            _ => "Meter  ▾"
        };
        EncounterLabel.Text = _selectedEncounter?.Label ?? "No encounter selected";
        if (_selectedEncounter is null)
        {
            MeterRows.ItemsSource = null;
            FooterLabel.Text = "No encounters";
            return;
        }

        var rows = EncounterProjection.Rows(_selectedEncounter, _mode);
        var livePartial = !_researchMode && _selectedEncounter.Issues?.Any(issue =>
            issue.StartsWith("Live partial capture:", StringComparison.Ordinal)) == true;
        if (livePartial && _captureError is null)
        {
            DataSourceLabel.Text = "LIVE / PARTIAL";
            DataSourceLabel.ToolTip = "Observed game results with known coverage gaps. Open the timeline or footer for details.";
        }
        IReadOnlyList<MeterDisplayRow> displayRows;
        var displayedTotal = rows.Sum(row => row.Value);
        var selectedSource = rows.FirstOrDefault(row => row.Key == _sourceKey);
        if (_sourceKey is not null && selectedSource is null) ResetDrill();
        if (selectedSource is null || _mode == MeterMode.Deaths)
        {
            var maximum = rows.Count == 0 ? 0 : rows.Max(row => row.Value);
            displayRows = rows.Select((row, index) => MeterDisplayRow.From(row, index, maximum, _mode,
                    ThemeForSource(row.Key))
                with { Preview = _mode == MeterMode.Deaths ? null :
                    new MeterPreview($"{row.Name} · moves", BuildMoveRows(row.Key)) }).ToArray();
        }
        else
        {
            var groups = EncounterProjection.MoveGroups(_selectedEncounter, _mode, _sourceKey!);
            var selectedGroup = groups.FirstOrDefault(group => group.Key == _moveKey);
            if (_moveKey is not null && selectedGroup is null) _moveKey = null;
            displayRows = selectedGroup is null ? BuildMoveRows(_sourceKey!)
                : BuildHitRows(selectedGroup, ThemeForSource(_sourceKey!), SkillIcons.For(selectedGroup));
            displayedTotal = selectedGroup?.Value ?? selectedSource.Value;
            EncounterLabel.Text += selectedGroup is null
                ? $" · {selectedSource.Name}"
                : $" · {selectedSource.Name} · {selectedGroup.Name}";
        }
        BackButton.Visibility = _sourceKey is null ? Visibility.Collapsed : Visibility.Visible;
        MeterRows.ItemsSource = displayRows;
        var quality = _selectedEncounter.Outcome == EncounterOutcome.InProgress
            ? livePartial ? "  ·  LIVE PARTIAL" : "  ·  IN PROGRESS"
            : _selectedEncounter.IsComplete ? "" : "  ·  PARTIAL";
        FooterLabel.Text = $"{displayedTotal:N0} total{quality}  ·  " +
            (_moveKey is not null ? "right-click to go back" : "hover to preview · click to enter");
        FooterLabel.ToolTip = _selectedEncounter.Issues is { Count: > 0 }
            ? string.Join(Environment.NewLine, _selectedEncounter.Issues)
            : _selectedEncounter.Outcome == EncounterOutcome.InProgress ? "Encounter is still in progress." : null;
    }

    private void ModeButton_Click(object sender, RoutedEventArgs e)
    {
        var menu = new ContextMenu();
        foreach (var mode in Enum.GetValues<MeterMode>())
        {
            var choice = new MenuItem { Header = mode switch
            {
                MeterMode.Damage => "Damage Done",
                MeterMode.Healing => "Healing Done",
                MeterMode.Taken => "Damage Taken",
                _ => "Deaths"
            }, IsCheckable = true, IsChecked = mode == _mode };
            choice.Click += (_, _) => { _mode = mode; ResetDrill(); RenderMeter(); };
            menu.Items.Add(choice);
        }
        OpenMenu(menu, (Button)sender);
    }

    private void HistoryButton_Click(object sender, RoutedEventArgs e)
    {
        var menu = new ContextMenu();
        foreach (var encounter in EncounterProjection.Recent(_encounters))
        {
            var choice = new MenuItem { Header = encounter.Label, IsCheckable = true,
                IsChecked = encounter.Id == _selectedEncounter?.Id };
            choice.Click += (_, _) =>
            {
                _followNewest = encounter.Id == _encounters.OrderByDescending(e => e.StartedAt).First().Id;
                SelectEncounter(encounter);
            };
            menu.Items.Add(choice);
        }
        menu.Items.Add(new Separator());
        var more = new MenuItem { Header = "More…" };
        more.Click += (_, _) =>
        {
            var history = new HistoryWindow(_encounters) { Owner = this };
            if (history.ShowDialog() == true)
            {
                _followNewest = history.SelectedEncounter?.Id ==
                    _encounters.OrderByDescending(e => e.StartedAt).FirstOrDefault()?.Id;
                SelectEncounter(history.SelectedEncounter);
            }
        };
        menu.Items.Add(more);
        OpenMenu(menu, (Button)sender);
    }

    private static void OpenMenu(ContextMenu menu, Button owner)
    {
        menu.PlacementTarget = owner;
        menu.Placement = System.Windows.Controls.Primitives.PlacementMode.Bottom;
        menu.IsOpen = true;
    }

    private void MeterRow_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedEncounter is null || ((Button)sender).DataContext is not MeterDisplayRow row) return;
        if (_mode == MeterMode.Deaths)
        {
            new BreakdownWindow(_selectedEncounter, _mode, row.Key) { Owner = this }.ShowDialog();
            return;
        }
        if (_sourceKey is null) _sourceKey = row.Key;
        else if (_moveKey is null) _moveKey = row.Key;
        else return;
        RenderMeter();
    }

    private void MeterRow_RightClick(object sender, MouseButtonEventArgs e)
    {
        e.Handled = true;
        NavigateBack();
    }

    private void BackButton_Click(object sender, RoutedEventArgs e) => NavigateBack();

    private void NavigateBack()
    {
        if (_moveKey is not null) _moveKey = null;
        else _sourceKey = null;
        RenderMeter();
    }

    private IReadOnlyList<MeterDisplayRow> BuildMoveRows(string sourceKey)
    {
        if (_selectedEncounter is null) return [];
        var groups = EncounterProjection.MoveGroups(_selectedEncounter, _mode, sourceKey);
        var maximum = groups.Count == 0 ? 0 : groups.Max(group => group.Value);
        var theme = ThemeForSource(sourceKey);
        return groups.Select((group, index) =>
        {
            var icon = SkillIcons.For(group);
            return MeterDisplayRow.Breakdown(group.Key,
                $"{group.Name} ({group.Hits.Count})", group.Value, index, maximum,
                $"{group.Name}: {group.Value:N0} effective · {group.DamageClass} · {group.Hits.Count} hit(s)",
                new MeterPreview($"{group.Name} · hits", BuildHitRows(group, theme, icon)), theme, icon);
        }).ToArray();
    }

    private CharacterTheme? ThemeForSource(string sourceKey)
    {
        var actor = _selectedEncounter?.Actors.FirstOrDefault(item => item.Id == sourceKey);
        return actor is null ? null : CharacterThemes.For(actor.Name, actor.Team);
    }

    private IReadOnlyList<MeterDisplayRow> BuildHitRows(MoveGroup group, CharacterTheme? theme,
        System.Windows.Media.ImageSource? icon)
    {
        if (_selectedEncounter is null) return [];
        var actors = _selectedEncounter.Actors.ToDictionary(actor => actor.Id);
        var maximum = group.Hits.Count == 0 ? 0 : group.Hits.Max(hit => hit.EffectiveAmount ?? 0);
        return group.Hits.Select((hit, index) =>
        {
            var target = actors.TryGetValue(hit.TargetId, out var actor) ? actor.Name : hit.TargetId;
            var name = $"{hit.ObservedAt.ToLocalTime():HH:mm:ss.fff} → {target}";
            var tooltip = $"Result #{hit.Sequence} · {group.Name} → {target}\n" +
                $"Effective: {hit.EffectiveAmount?.ToString("N0") ?? "unknown"} · Type: {hit.DamageClass}\n" +
                $"Critical: {(hit.IsCritical is null ? "unverified" : hit.IsCritical.Value ? "yes" : "no")}\n" +
                $"HP: {hit.HpBefore?.ToString("N0") ?? "?"} → {hit.HpAfter?.ToString("N0") ?? "?"}\n" +
                $"Raw flags: {(hit.RawResultFlags is { } flags ? $"0x{flags:X}" : "unavailable")}\n" +
                $"Source context +0x30: {(hit.RawSourceContextFlags is { } contextFlags ? $"0x{contextFlags:X}" : "unavailable")}\n" +
                $"Target status +0x7C: {(hit.RawTargetStatus7C is { } status7C ? $"0x{status7C:X}" : "unavailable")}\n" +
                $"Raw effect: {hit.RawEffectId ?? "unavailable"}" +
                (hit.RawEffectCode is { } code ? $" · code 0x{code:X}" : "");
            return MeterDisplayRow.Breakdown($"hit:{hit.Sequence}", name, hit.EffectiveAmount ?? 0,
                index, maximum, tooltip, theme: theme, icon: icon);
        }).ToArray();
    }

    private void TimelineButton_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedEncounter is not null) new TimelineWindow(_selectedEncounter) { Owner = this }.ShowDialog();
    }

    private void Header_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        var source = e.OriginalSource as DependencyObject;
        while (source is not null)
        {
            if (source is System.Windows.Controls.Primitives.ButtonBase) return;
            source = System.Windows.Media.VisualTreeHelper.GetParent(source);
        }
        if (e.ButtonState == MouseButtonState.Pressed) DragMove();
    }

    private void MinimizeButton_Click(object sender, RoutedEventArgs e) => WindowState = WindowState.Minimized;
    private void CloseButton_Click(object sender, RoutedEventArgs e) => Close();
}
