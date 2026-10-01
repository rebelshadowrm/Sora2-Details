using System.IO;
using System.ComponentModel;
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
    private readonly bool _researchMode;
    private string? _captureError;
    private Encounter? _selectedEncounter;
    private bool _followNewest = true;
    private MeterMode _mode = MeterMode.PlayerDamage;
    private string? _sourceKey;
    private string? _attackerKey;
    private string? _moveKey;
    private readonly DispatcherTimer _placementSaveTimer = new() { Interval = TimeSpan.FromMilliseconds(400) };
    private readonly DispatcherTimer _captureStatusTimer = new() { Interval = TimeSpan.FromSeconds(3) };
    private readonly DispatcherTimer _gameDetectionTimer = new() { Interval = TimeSpan.FromSeconds(2) };
    private MeterDisplaySettings _displaySettings = MeterDisplaySettings.Load();
    private readonly EncounterHistorySettings _historySettings = EncounterHistorySettings.Load();
    private bool _placementReady;
    private bool _exitAfterDetach;
    private bool _exitRequested;
    private bool _closeWhenReady;
    private bool _gameExitDetachRunning;
    private HashSet<int> _observedGamePids = [];
    private readonly HashSet<int> _notifiedGamePids = [];
    private int? _currentGamePid;
    private DateTimeOffset? _observedResetAt;

    public MainWindow()
    {
        InitializeComponent();
        if (WindowPlacement.Load("meter-window.json") is { } placement)
        {
            WindowStartupLocation = WindowStartupLocation.Manual;
            Left = placement.Left;
            Top = placement.Top;
            Width = placement.Width;
            Height = placement.Height;
        }
        ApplyDisplaySettings();
        SourceInitialized += (_, _) => InitializeWindowInteraction();
        _placementSaveTimer.Tick += (_, _) =>
        {
            _placementSaveTimer.Stop();
            SavePlacement();
        };
        _captureStatusTimer.Tick += (_, _) =>
        {
            RefreshCaptureStatus();
            var resetAt = ActiveSessionResetAt();
            if (resetAt == _observedResetAt) return;
            _observedResetAt = resetAt;
            if (resetAt is not null) _followNewest = true;
            ReloadHistory();
        };
        Loaded += (_, _) => _placementReady = true;
        Loaded += async (_, _) => await CheckForUpdatesAsync();
        Loaded += async (_, _) =>
        {
            RefreshCaptureStatus();
            ReloadHistory();
            _captureStatusTimer.Start();
            _observedGamePids = GetGamePids().ToHashSet();
            _notifiedGamePids.UnionWith(_observedGamePids);
            _currentGamePid = _observedGamePids.Count == 1 ? _observedGamePids.Single() : null;
            _gameDetectionTimer.Tick += GameDetectionTimer_Tick;
            _gameDetectionTimer.Start();
            if (!LiveCaptureDisabled)
            {
                if (_observedGamePids.Count == 1)
                    await StartCaptureAsync(_currentGamePid);
                else if (_observedGamePids.Count == 0)
                    HideMeterToTray();
                else
                    SetCaptureError("More than one supported game process is running. Close the extra process, then start capture from the tray.");
            }
            RefreshTrayCommands();
        };
        LocationChanged += (_, _) => QueuePlacementSave();
        SizeChanged += (_, _) => QueuePlacementSave();
        StateChanged += (_, _) =>
        {
            if (WindowState == WindowState.Minimized) HideMeterToTray();
        };
        Closing += MainWindow_Closing;
        var historyPath = System.IO.Path.Combine(MeterDataDirectory.PathName, "encounters");
        System.IO.Directory.CreateDirectory(historyPath);
        _store = new EncounterStore(historyPath);
        var researchPath = Environment.GetEnvironmentVariable("SORA2_DETAILS_RESEARCH_REPLAY");
        _researchMode = !string.IsNullOrWhiteSpace(researchPath);
        _encounters = _researchMode ? EncounterReplay.Load(researchPath!) : [];
        ReloadHistory();
        _historyWatcher = new FileSystemWatcher(historyPath, "*.json") { EnableRaisingEvents = true };
        _historyWatcher.Created += (_, _) => Dispatcher.BeginInvoke(ReloadHistory);
        _historyWatcher.Changed += (_, _) => Dispatcher.BeginInvoke(ReloadHistory);
        _historyWatcher.Renamed += (_, _) => Dispatcher.BeginInvoke(ReloadHistory);
        _captureTask = _researchMode ? Task.CompletedTask : Task.Run(ReceiveCaptureAsync);
        Closed += (_, _) =>
        {
            DisposeTray();
            _captureStatusTimer.Stop();
            _gameDetectionTimer.Stop();
            _placementSaveTimer.Stop();
            SavePlacement();
            _captureCancellation.Cancel();
            _captureTask.GetAwaiter().GetResult();
            _captureCancellation.Dispose();
            _historyWatcher.Dispose();
        };
    }

    private async void MainWindow_Closing(object? sender, CancelEventArgs e)
    {
        if (!_exitRequested)
        {
            if (_displaySettings.CloseToTray)
            {
                e.Cancel = true;
                HideMeterToTray();
                return;
            }
            _exitRequested = true;
        }
        if (_exitAfterDetach || !File.Exists(CurrentCapturePath()) && !_captureBusy) return;
        e.Cancel = true;
        if (_captureBusy)
        {
            _closeWhenReady = true;
            return;
        }
        _captureBusy = true;
        _captureStopping = true;
        RefreshCaptureStatus();
        try
        {
            if (await EnsureCaptureDetachedAsync())
            {
                _exitAfterDetach = true;
                Close();
                return;
            }
            SetCaptureError("Capture did not fully detach within 30 seconds. Sora 2 Details will stay in the tray so cleanup can be retried.");
        }
        catch (Exception exception)
        {
            SetCaptureError($"Capture could not detach: {exception.Message}. The meter remains open; try Stop again.");
        }
        finally
        {
            _captureStopping = false;
            _captureBusy = false;
            _closeWhenReady = false;
            RefreshCaptureStatus();
        }
        _exitRequested = false;
        MessageBox.Show(this, _captureStatusError ?? "Capture cleanup could not be confirmed.",
            "Sora 2 Details remains running", MessageBoxButton.OK, MessageBoxImage.Warning);
        HideMeterToTray();
    }

    private async void GameDetectionTimer_Tick(object? sender, EventArgs e)
    {
        if (_gameExitDetachRunning || _researchMode || _updateBusy) return;
        var current = GetGamePids().ToHashSet();
        _observedGamePids = current;
        foreach (var exitedPid in _notifiedGamePids.Where(pid => !current.Contains(pid)).ToArray())
            _notifiedGamePids.Remove(exitedPid);

        var capturePid = CurrentCaptureTargetPid();
        if (capturePid is null && CaptureMayBeActive()) capturePid = _currentGamePid;
        if (capturePid is { } attachedPid && !current.Contains(attachedPid))
        {
            await DetachAfterGameExitAsync(attachedPid);
            RefreshTrayCommands();
            return;
        }

        if (_currentGamePid is { } previousPid && !current.Contains(previousPid))
        {
            _currentGamePid = null;
            _selectedEncounter = null;
            _followNewest = true;
            RenderMeter();
            HideMeterToTray();
        }

        var newlyDetected = current.FirstOrDefault(pid => !_notifiedGamePids.Contains(pid));
        if (newlyDetected != 0 && !CaptureMayBeActive() && !_captureBusy && !_updateBusy &&
            Environment.GetEnvironmentVariable("SORA2_DETAILS_METER_ONLY") != "1")
        {
            _currentGamePid = newlyDetected;
            _notifiedGamePids.Add(newlyDetected);
            _captureStatusError = null;
            ShowGameDetectedNotification();
        }
        RefreshTrayCommands();
    }

    private async Task DetachAfterGameExitAsync(int gamePid)
    {
        if (_gameExitDetachRunning || _captureBusy) return;
        _gameExitDetachRunning = true;
        _captureBusy = true;
        _captureStopping = true;
        RefreshCaptureStatus();
        try
        {
            if (await EnsureCaptureDetachedAsync())
            {
                _captureStatusError = null;
                _captureError = null;
                _currentGamePid = null;
                _selectedEncounter = null;
                _followNewest = true;
                ReloadHistory();
                RenderMeter();
                HideMeterToTray();
            }
            else
            {
                SetCaptureError($"The game (PID {gamePid}) exited, but capture cleanup is not confirmed. Sora 2 Details remains resident and will retry.");
                if (_trayIcon?.Visible == true)
                    _trayIcon.ShowBalloonTip(5000, "Capture cleanup pending",
                        "Sora 2 Details is still waiting for the capture helpers to detach.",
                        System.Windows.Forms.ToolTipIcon.Warning);
            }
        }
        catch (Exception exception)
        {
            SetCaptureError($"The game exited, but capture cleanup failed: {exception.Message}");
        }
        finally
        {
            _captureStopping = false;
            _captureBusy = false;
            _gameExitDetachRunning = false;
            RefreshCaptureStatus();
            RefreshTrayCommands();
            if (_closeWhenReady)
            {
                _closeWhenReady = false;
                _ = Dispatcher.BeginInvoke(Close);
            }
        }
    }

    private void RequestFullExit()
    {
        if (_updateBusy)
        {
            ShowMeterFromTray();
            MessageBox.Show(this, "Wait for the update to finish before exiting Sora 2 Details.",
                "Update in progress", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }
        _exitRequested = true;
        Close();
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
        try { WindowPlacement.Save("meter-window.json", bounds); }
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
            _captureError = $"Capture listener failed: {exception.Message}. Restart the meter to retry.";
            if (!Dispatcher.HasShutdownStarted) _ = Dispatcher.BeginInvoke(RefreshCaptureStatus);
        }
    }

    private void ReloadHistory()
    {
        if (_researchMode)
        {
            SelectEncounter(_encounters.FirstOrDefault(e => e.Id == _selectedEncounter?.Id)
                ?? _encounters.OrderByDescending(e => e.StartedAt).FirstOrDefault());
            return;
        }
        IReadOnlyList<Encounter> recorded;
        try { recorded = _store.LoadAll(); }
        catch (System.IO.IOException) { return; } // A writer may still be replacing a snapshot.
        _encounters = recorded;
        var activeTrace = ActiveTraceName();
        var newest = _encounters.OrderByDescending(e => e.StartedAt).FirstOrDefault();
        var resetAt = activeTrace is null ? null : ActiveSessionResetAt();
        var current = activeTrace is null ? null : _encounters.FirstOrDefault(e =>
            e.Issues?.Contains($"Raw trace: {activeTrace}") == true &&
            (resetAt is null || e.StartedAt > resetAt.Value));
        SelectEncounter(_followNewest ? current :
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
        _attackerKey = null;
        _moveKey = null;
    }

    private static bool IsTakenMode(MeterMode mode) =>
        mode is MeterMode.PlayerTaken or MeterMode.EnemyTaken;

    private void RenderMeter()
    {
        RefreshCaptureStatus();
        ModeButton.Content = _mode switch
        {
            MeterMode.PlayerDamage => "Player Damage Dealt  ▾",
            MeterMode.EnemyDamage => "Enemy Damage Dealt  ▾",
            MeterMode.PlayerTaken => "Player Damage Taken  ▾",
            MeterMode.EnemyTaken => "Enemy Damage Taken  ▾",
            MeterMode.Healing => "Healing Done  ▾",
            MeterMode.Deaths => "Deaths  ▾",
            _ => "Meter  ▾"
        };
        var waiting = _selectedEncounter is null && ActiveTraceName() is not null && _followNewest;
        var resetWaiting = waiting && ActiveSessionResetAt() is not null;
        var encounterClassification = _selectedEncounter is { } currentEncounter
            ? EncounterHistoryView.Classify(currentEncounter, _historySettings.BossEncounterIds,
                _historySettings.RegularEncounterIds) : BossClassification.Unclassified;
        EncounterLabel.Text = _selectedEncounter is { } shown
            ? (encounterClassification == BossClassification.Unclassified
                ? "" : EncounterHistoryView.ClassificationMarker(encounterClassification)) + shown.Label :
            (resetWaiting ? "Session reset · waiting for battle" :
                waiting ? "Waiting for next command battle" : "No encounter selected");
        if (_selectedEncounter is null)
        {
            MeterRows.ItemsSource = null;
            BackButton.Visibility = Visibility.Collapsed;
            FooterLabel.Text = resetWaiting ? "Previous fight is in history · awaiting battle entry" :
                waiting ? "Capture armed · enter a new command battle" :
                CaptureMayBeActive() ? "No encounter yet · capture is waiting for a command battle" :
                "Saved history is available from the tray";
            FooterLabel.ToolTip = waiting
                ? "A battle already open when capture starts cannot be reconstructed. Open the encounter menu for saved fights."
                : null;
            return;
        }

        var rows = EncounterProjection.Rows(_selectedEncounter, _mode);
        var livePartial = !_researchMode && _selectedEncounter.Issues?.Any(issue =>
            issue.StartsWith("Live partial capture:", StringComparison.Ordinal)) == true;
        IReadOnlyList<MeterDisplayRow> displayRows;
        var displayedTotal = rows.Sum(row => row.Value);
        var selectedSource = rows.FirstOrDefault(row => row.Key == _sourceKey);
        if (_sourceKey is not null && selectedSource is null) ResetDrill();
        if (selectedSource is null)
        {
            var maximum = rows.Count == 0 ? 0 : rows.Max(row => row.Value);
            displayRows = rows.Select((row, index) => MeterDisplayRow.From(row, index, maximum, _mode,
                    ThemeForSource(row.Key))
                with { Preview = _mode == MeterMode.Deaths
                    ? new MeterPreview($"{row.Name} · deaths", BuildDeathRows(row.Key))
                    : IsTakenMode(_mode)
                    ? new MeterPreview($"{row.Name} · attackers", BuildAttackerRows(row.Key))
                    : new MeterPreview($"{row.Name} · moves", BuildMoveRows(row.Key)) }).ToArray();
        }
        else if (_mode == MeterMode.Deaths)
        {
            displayRows = BuildDeathRows(_sourceKey!);
            displayedTotal = selectedSource.Value;
            EncounterLabel.Text += $" · {selectedSource.Name}";
        }
        else
        {
            IReadOnlyList<MeterRow> attackers = IsTakenMode(_mode)
                ? EncounterProjection.Attackers(_selectedEncounter, _mode, _sourceKey!) : [];
            var selectedAttacker = attackers.FirstOrDefault(row => row.Key == _attackerKey);
            if (_attackerKey is not null && selectedAttacker is null)
            {
                _attackerKey = null;
                _moveKey = null;
            }
            if (IsTakenMode(_mode) && selectedAttacker is null)
            {
                displayRows = BuildAttackerRows(_sourceKey!);
                displayedTotal = selectedSource.Value;
                EncounterLabel.Text += $" · {selectedSource.Name}";
            }
            else
            {
                var groups = EncounterProjection.MoveGroups(_selectedEncounter, _mode, _sourceKey!, _attackerKey);
                var selectedGroup = groups.FirstOrDefault(group => group.Key == _moveKey);
                if (_moveKey is not null && selectedGroup is null) _moveKey = null;
                displayRows = selectedGroup is null ? BuildMoveRows(_sourceKey!, _attackerKey)
                    : BuildHitRows(selectedGroup, ThemeForSource(_attackerKey ?? _sourceKey!), SkillIcons.For(selectedGroup));
                displayedTotal = selectedGroup?.Value ?? selectedAttacker?.Value ?? selectedSource.Value;
                EncounterLabel.Text += $" · {selectedSource.Name}" +
                    (selectedAttacker is null ? "" : $" · {selectedAttacker.Name}") +
                    (selectedGroup is null ? "" : $" · {selectedGroup.Name}");
            }
        }
        BackButton.Visibility = _sourceKey is null ? Visibility.Collapsed : Visibility.Visible;
        MeterRows.ItemsSource = displayRows;
        var quality = _selectedEncounter.Outcome == EncounterOutcome.InProgress
            ? livePartial ? "  ·  LIVE PARTIAL" : "  ·  IN PROGRESS"
            : _selectedEncounter.IsComplete ? "" : "  ·  PARTIAL";
        FooterLabel.Text = $"{displayedTotal:N0} total{quality}  ·  " +
            (_mode == MeterMode.Deaths && _sourceKey is not null
                ? "click a death for recap · right-click to go back"
                : _moveKey is not null ? "right-click to go back" : "hover to preview · click to enter");
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
                MeterMode.PlayerDamage => "Player Damage Dealt",
                MeterMode.EnemyDamage => "Enemy Damage Dealt",
                MeterMode.PlayerTaken => "Player Damage Taken",
                MeterMode.EnemyTaken => "Enemy Damage Taken",
                MeterMode.Healing => "Healing Done",
                _ => "Deaths"
            }, IsCheckable = true, IsChecked = mode == _mode };
            choice.Click += (_, _) => { _mode = mode; ResetDrill(); RenderMeter(); };
            menu.Items.Add(choice);
        }
        menu.Items.Add(new Separator());
        var settings = new MenuItem { Header = "Settings…" };
        settings.Click += (_, _) => OpenSettingsWindow();
        menu.Items.Add(settings);
        OpenMenu(menu, (Button)sender);
    }

    private void HistoryButton_Click(object sender, RoutedEventArgs e)
    {
        var menu = new ContextMenu();
        var activeTrace = ActiveTraceName();
        if (activeTrace is not null)
        {
            var current = new MenuItem { Header = "Current / live", IsCheckable = true,
                IsChecked = _followNewest };
            current.Click += (_, _) => { _followNewest = true; ReloadHistory(); };
            menu.Items.Add(current);
            menu.Items.Add(new Separator());
        }
        var show = new MenuItem { Header = "History view" };
        foreach (var mode in Enum.GetValues<HistoryFilterMode>())
        {
            var choice = new MenuItem
            {
                Header = EncounterHistoryView.FilterModeLabel(mode),
                IsCheckable = true,
                IsChecked = _historySettings.FilterMode == mode
            };
            choice.Click += (_, _) => SetHistoryFilterMode(mode);
            show.Items.Add(choice);
        }
        menu.Items.Add(show);
        if (_selectedEncounter is { } selected)
        {
            var classify = new MenuItem { Header = "Classify selected fight" };
            foreach (var (header, mark) in new[] {
                ("Confirm boss", BossClassification.MarkedBoss),
                ("Mark regular", BossClassification.MarkedRegular),
                ("Clear manual mark", BossClassification.Unclassified) })
            {
                var choice = new MenuItem { Header = header,
                    IsEnabled = mark != BossClassification.Unclassified ||
                        _historySettings.BossEncounterIds.Contains(selected.Id) ||
                        _historySettings.RegularEncounterIds.Contains(selected.Id) };
                choice.Click += (_, _) => MarkSelectedEncounter(mark);
                classify.Items.Add(choice);
            }
            menu.Items.Add(classify);
        }
        menu.Items.Add(new Separator());
        var visible = EncounterHistoryView.Visible(_encounters, _historySettings.FilterMode,
            _historySettings.BossEncounterIds, _historySettings.RegularEncounterIds);
        foreach (var encounter in EncounterProjection.Recent(visible))
        {
            var choice = new MenuItem { Header = HistoryWindow.Describe(encounter,
                EncounterHistoryView.Classify(encounter, _historySettings.BossEncounterIds,
                    _historySettings.RegularEncounterIds)), IsCheckable = true,
                IsChecked = (activeTrace is null || !_followNewest) &&
                    encounter.Id == _selectedEncounter?.Id };
            choice.Click += (_, _) =>
            {
                _followNewest = activeTrace is null &&
                    encounter.Id == _encounters.OrderByDescending(e => e.StartedAt).First().Id;
                SelectEncounter(encounter);
            };
            menu.Items.Add(choice);
        }
        menu.Items.Add(new Separator());
        var more = new MenuItem { Header = $"More history… ({visible.Count} fights)" };
        more.Click += (_, _) =>
        {
            var history = new HistoryWindow(_encounters, _historySettings) { Owner = this };
            if (history.ShowDialog() == true)
            {
                _followNewest = activeTrace is null && history.SelectedEncounter?.Id ==
                    _encounters.OrderByDescending(e => e.StartedAt).FirstOrDefault()?.Id;
                SelectEncounter(history.SelectedEncounter);
            }
            RenderMeter();
        };
        menu.Items.Add(more);
        OpenMenu(menu, (Button)sender);
    }

    private void SetHistoryFilterMode(HistoryFilterMode mode)
    {
        _historySettings.FilterMode = mode;
        SaveHistorySettings();
        RenderMeter();
    }

    private void MarkSelectedEncounter(BossClassification mark)
    {
        if (_selectedEncounter is not { } selected) return;
        if (mark == BossClassification.MarkedBoss) _historySettings.MarkBoss(selected.Id);
        else if (mark == BossClassification.MarkedRegular) _historySettings.MarkRegular(selected.Id);
        else _historySettings.ClearMark(selected.Id);
        SaveHistorySettings();
        RenderMeter();
    }

    private void SaveHistorySettings()
    {
        try { _historySettings.Save(); }
        catch (Exception exception) when (exception is IOException or UnauthorizedAccessException)
        {
            MessageBox.Show(this, $"History preference could not be saved: {exception.Message}",
                "Encounter history", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
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
            if (_sourceKey is null)
            {
                _sourceKey = row.Key;
                RenderMeter();
            }
            else if (row.Key.StartsWith("death:", StringComparison.Ordinal) &&
                long.TryParse(row.Key["death:".Length..], out var sequence))
            {
                new TimelineWindow(_selectedEncounter, sequence) { Owner = this }.ShowDialog();
            }
            return;
        }
        if (_sourceKey is null) _sourceKey = row.Key;
        else if (IsTakenMode(_mode) && _attackerKey is null) _attackerKey = row.Key;
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
        else if (_attackerKey is not null) _attackerKey = null;
        else _sourceKey = null;
        RenderMeter();
    }

    private IReadOnlyList<MeterDisplayRow> BuildAttackerRows(string victimKey)
    {
        if (_selectedEncounter is null) return [];
        var attackers = EncounterProjection.Attackers(_selectedEncounter, _mode, victimKey);
        var maximum = attackers.Count == 0 ? 0 : attackers.Max(row => row.Value);
        return attackers.Select((row, index) => MeterDisplayRow.From(row, index, maximum, _mode,
                ThemeForSource(row.Key)) with
            { Preview = new MeterPreview($"{row.Name} · moves", BuildMoveRows(victimKey, row.Key)) })
            .ToArray();
    }

    private IReadOnlyList<MeterDisplayRow> BuildMoveRows(string sourceKey, string? attackerKey = null)
    {
        if (_selectedEncounter is null) return [];
        var groups = EncounterProjection.MoveGroups(_selectedEncounter, _mode, sourceKey, attackerKey);
        var maximum = groups.Count == 0 ? 0 : groups.Max(group => group.Value);
        var theme = ThemeForSource(attackerKey ?? sourceKey);
        return groups.Select((group, index) =>
        {
            var icon = SkillIcons.For(group);
            return MeterDisplayRow.Breakdown(group.Key,
                $"{group.Name} ({group.Hits.Count})", group.Value, index, maximum,
                $"{group.Name}: {group.Value:N0} effective · {group.DamageClass} · {group.Hits.Count} hit(s)",
                new MeterPreview($"{group.Name} · hits", BuildHitRows(group, theme, icon)), theme, icon);
        }).ToArray();
    }

    private IReadOnlyList<MeterDisplayRow> BuildDeathRows(string victimKey)
    {
        if (_selectedEncounter is null) return [];
        var actors = _selectedEncounter.Actors.ToDictionary(actor => actor.Id);
        var deaths = _selectedEncounter.Events
            .Where(effect => effect.Kind == CombatEventKind.Knockout && effect.TargetId == victimKey)
            .OrderBy(effect => effect.Sequence)
            .ToArray();
        var theme = ThemeForSource(victimKey);
        return deaths.Select((death, index) =>
        {
            var source = death.SourceId is not null && actors.TryGetValue(death.SourceId, out var actor)
                ? actor.Name : "Unknown source";
            var cause = death.MoveName ?? "Unknown cause";
            return MeterDisplayRow.Breakdown($"death:{death.Sequence}",
                $"{death.ObservedAt.ToLocalTime():HH:mm:ss} · {source}", 1, index, 1,
                $"Death #{index + 1} · event #{death.Sequence}\n{source} · {cause}\nClick for recent recap",
                theme: theme) with { ValueLabel = cause };
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
            var source = hit.SourceId is not null && actors.TryGetValue(hit.SourceId, out var attacker)
                ? attacker.Name : "Unknown source";
            var name = $"{hit.ObservedAt.ToLocalTime():HH:mm:ss.fff} · {source} → {target}";
            var amounts = DamageAmounts.From(hit);
            var isDamage = hit.Kind == CombatEventKind.Damage;
            var tooltip = $"Result #{hit.Sequence} · {source} · {group.Name} → {target}\n" +
                $"{(isDamage ? "Total hit" : "Total result")}: {amounts.Total?.ToString("N0") ?? "unknown"}\n" +
                $"Effective: {amounts.Effective?.ToString("N0") ?? "unknown"}\n" +
                (isDamage ? $"Overkill: {amounts.Overkill?.ToString("N0") ?? "unknown"}\n" : "") +
                $"Type: {hit.DamageClass}\n" +
                $"Critical: {(hit.IsCritical is null ? "unverified" : hit.IsCritical.Value ? "yes" : "no")}\n" +
                $"HP: {hit.HpBefore?.ToString("N0") ?? "?"} → {hit.HpAfter?.ToString("N0") ?? "?"}\n" +
                $"Raw flags: {(hit.RawResultFlags is { } flags ? $"0x{flags:X}" : "unavailable")}\n" +
                $"Source context +0x30: {(hit.RawSourceContextFlags is { } contextFlags ? $"0x{contextFlags:X}" : "unavailable")}\n" +
                $"Target status +0x7C: {(hit.RawTargetStatus7C is { } status7C ? $"0x{status7C:X}" : "unavailable")}\n" +
                $"Raw effect: {hit.RawEffectId ?? "unavailable"}" +
                (hit.RawEffectCode is { } code ? $" · code 0x{code:X}" : "") +
                (hit.MoveLookupReason is { } reason ? $"\nMove lookup: {reason}" : "");
            var row = MeterDisplayRow.Breakdown($"hit:{hit.Sequence}", name, hit.EffectiveAmount ?? 0,
                index, maximum, tooltip, theme: theme, icon: icon);
            return amounts.Overkill is > 0
                ? row with { ValueLabel = $"{MeterDisplayRow.FormatAmount(hit.EffectiveAmount ?? 0)} (+{MeterDisplayRow.FormatAmount(amounts.Overkill.Value)} over)" }
                : row;
        }).ToArray();
    }

    private void TimelineButton_Click(object sender, RoutedEventArgs e)
    {
        if (_selectedEncounter is not null) new TimelineWindow(_selectedEncounter) { Owner = this }.ShowDialog();
    }

    private void Header_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (_displaySettings.LockPosition) return;
        var source = e.OriginalSource as DependencyObject;
        while (source is not null)
        {
            if (source is System.Windows.Controls.Primitives.ButtonBase) return;
            source = System.Windows.Media.VisualTreeHelper.GetParent(source);
        }
        if (e.ButtonState == MouseButtonState.Pressed) DragMove();
    }

    private void MinimizeButton_Click(object sender, RoutedEventArgs e) => HideMeterToTray();
    private void CloseButton_Click(object sender, RoutedEventArgs e)
    {
        if (_displaySettings.CloseToTray) HideMeterToTray();
        else RequestFullExit();
    }
}
