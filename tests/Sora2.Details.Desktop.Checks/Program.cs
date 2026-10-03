using System.Diagnostics;
using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Security.Cryptography;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Threading;
using Sora2.Details.Core;
using Sora2.Details.Desktop;

internal static class DesktopChecks
{
    private const BindingFlags Private = BindingFlags.Instance | BindingFlags.NonPublic;
    [STAThread]
    private static int Main(string[] args)
    {
        if (args.Length > 0 && args[0] == "--helper")
        {
            File.WriteAllText(args[1], "{\"kind\":\"armed\"}\n".Replace(":", ": "));
            while (!File.Exists(args[2])) Thread.Sleep(20);
            File.AppendAllText(args[1], "{\"kind\": \"detached\"}\n");
            return 0;
        }
        if (args.Length == 4 && args[0] == "--observe-transcript")
            return ObserveTranscript(args[1], args[2], args[3]);
        var output = Path.GetFullPath(args.Length > 0 ? args[0] : ".research-deps/desktop-audit");
        Directory.CreateDirectory(output);
        Velopack.VelopackApp.Build().Run();
        var application = new System.Windows.Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        var code = 0;
        application.Dispatcher.BeginInvoke(new Action(async () =>
        {
            try
            {
                if (args.Contains("--capture-lifecycle"))
                {
                    await RunActionStreamLifecycle(output);
                    Console.WriteLine("Action-stream app start, live source verification, manual stop, helper exit and desktop close passed (real game attachment; no player actions). ");
                    return;
                }
                if (!args.Contains("--transcript-only"))
                    foreach (var mode in new[] { "x-active", "tray-active", "x-failed", "tray-failed", "x-raw", "x-transcript", "tray-transcript" })
                        await RunCase(output, mode);
                if (Environment.GetEnvironmentVariable("SORA2_DETAILS_TRANSCRIPT_CHECK_PATH") is { Length: > 0 } transcript)
                    await RunTranscript(output, transcript);
                Console.WriteLine(args.Contains("--transcript-only")
                    ? "Research transcript desktop checks passed (saved replay; no game attachment)."
                    : "Desktop settings, live file projection, timeline refresh, X dialog, and tray shutdown checks passed (simulated capture; no game attachment).");
            }
            catch (Exception e) { code = 1; Console.Error.WriteLine(e); }
            finally { application.Shutdown(); }
        }));
        application.Run();
        return code;
    }

    private static object Field(object target, string name) =>
        target.GetType().GetField(name, Private)!.GetValue(target)!;
    private static object? Call(object target, string name, params object?[] args) =>
        target.GetType().GetMethod(name, Private)!.Invoke(target, args);

    private static async Task RunActionStreamLifecycle(string output)
    {
        Check(new System.Security.Principal.WindowsPrincipal(System.Security.Principal.WindowsIdentity.GetCurrent())
            .IsInRole(System.Security.Principal.WindowsBuiltInRole.Administrator),
            "real capture lifecycle checks require an elevated process, like the production desktop");
        var game = Process.GetProcessesByName("sora_2nd").Single();
        using (game)
        {
            var data = Path.Combine(output, "capture-lifecycle-" + Guid.NewGuid().ToString("N"));
            Environment.SetEnvironmentVariable("SORA2_DETAILS_DATA_DIR", data);
            Environment.SetEnvironmentVariable("SORA2_DETAILS_CAPTURE_PROFILE", "Transcript");
            Environment.SetEnvironmentVariable("SORA2_DETAILS_RESEARCH_REPLAY", null);
            Environment.SetEnvironmentVariable("SORA2_DETAILS_METER_ONLY", "1");
            var window = new MainWindow("sora2-action-lifecycle-" + Guid.NewGuid().ToString("N"))
            { ShowActivated = false, WindowStartupLocation = WindowStartupLocation.Manual, Left = 10000, Top = 10000 };
            window.Show();
            await Task.Delay(100);
            ((DispatcherTimer)Field(window, "_gameDetectionTimer")).Stop();
            Environment.SetEnvironmentVariable("SORA2_DETAILS_METER_ONLY", null);
            try
            {
                await (Task)Call(window, "StartCaptureAsync", game.Id)!;
                var label = (TextBlock)window.FindName("DataSourceLabel");
                Check(label.Text == "Capturing", "normal app starts action recording: " + label.ToolTip);
                var current = Path.Combine(data, "live", "current.json");
                using var manifest = JsonDocument.Parse(File.ReadAllText(current));
                var ledger = manifest.RootElement.GetProperty("ledgerPath").GetString()!;
                await Wait(() => File.Exists(ledger), "live ledger published");
                var transcript = ResearchTranscript.Load(ledger);
                Check(transcript.SourceVerified && transcript.Entries.Any(e => e.Raw.GetProperty("kind").GetString() == "armed"),
                    "actual armed stream is source verified");
                await (Task)Call(window, "OpenResearchTranscriptAsync")!;
                var viewer = System.Windows.Application.Current.Windows.OfType<ResearchTranscriptWindow>().Single();
                Check(viewer.Owner == window, "live tray viewer belongs to desktop");
                Render(window, Path.Combine(output, "action-stream-app.png"));
                var bridge = manifest.RootElement.GetProperty("bridgePid").GetInt32();
                var server = manifest.RootElement.GetProperty("serverPid").GetInt32();
                await (Task)Call(window, "StopCaptureAsync")!;
                Check(!File.Exists(current), "manual stop verifies detach and removes active session");
                Check(!Process.GetProcesses().Any(p => p.Id == bridge || p.Id == server), "both recording helpers exited");
                var batch = manifest.RootElement.GetProperty("requestId").GetString()!;
                Check(!File.Exists(Path.Combine(data, "probe-session", "results", batch + ".json")),
                    "launcher reported no projection failure");
                var directory = Path.GetDirectoryName(ledger)!;
                Check(File.ReadAllText(Path.Combine(directory, $"launcher-{batch}.stderr.log")).Length == 0 &&
                    File.ReadAllText(Path.Combine(directory, $"bridge-{batch}.stderr.log")).Length == 0,
                    "launcher and bridge stderr are empty after cleanup");
                transcript = ResearchTranscript.Load(ledger);
                Check(transcript.SourceVerified && transcript.Entries.Last().Raw.GetProperty("kind").GetString() == "detached",
                    "final saved stream retains verified detach");
                Call(window, "RequestFullExit");
                await Wait(() => !window.IsVisible && !viewer.IsVisible, "desktop and owned viewer closed");
                Check(!game.HasExited, "game survives app cleanup");
                Console.WriteLine($"Verified final ledger: {ledger}; {transcript.Entries.Count} observations");
            }
            finally
            {
                // Never kill the game or a debugger. Request the existing graceful cleanup on failure.
                await (Task)Call(window, "StopCaptureAsync")!;
            }
        }
    }

    private static int ObserveTranscript(string path, string stopPath, string auditPath)
    {
        Velopack.VelopackApp.Build().Run();
        var app = new System.Windows.Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        // The bridge publishes its first snapshot after capture arms. This is
        // viewer startup readiness, not a limit on the armed research interval.
        var readiness = System.Diagnostics.Stopwatch.StartNew();
        while (!File.Exists(path) && readiness.Elapsed < TimeSpan.FromSeconds(30))
        {
            if (File.Exists(stopPath)) return 0;
            Thread.Sleep(100);
        }
        var transcript = ResearchTranscript.Load(path);
        var window = new ResearchTranscriptWindow(transcript, path)
        {
            ShowActivated = false, WindowStartupLocation = WindowStartupLocation.Manual, Left = 10000, Top = 10000
        };
        void Audit(ResearchTranscript snapshot)
        {
            var grids = LogicalDescendants(window).OfType<DataGrid>().ToArray();
            File.AppendAllText(auditPath, JsonSerializer.Serialize(new
            {
                at = DateTimeOffset.Now, kind = "research-viewer-snapshot", pid = Environment.ProcessId,
                snapshot.BatchId, snapshot.SourceSha256, snapshot.SourceVerified,
                displayedActions = grids.Single(g => g.Name == "ActionEntries").Items.Count,
                displayedObservations = grids.Single(g => g.Name == "ObservationEntries").Items.Count,
                intervalCount = snapshot.Intervals.Count, latestObservationId = snapshot.Entries.LastOrDefault()?.Id
            }) + "\n");
        }
        window.SnapshotApplied += Audit;
        window.Show();
        Audit(transcript);
        var stop = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(500) };
        stop.Tick += (_, _) =>
        {
            if (!File.Exists(stopPath)) return;
            stop.Stop();
            Render(window, Path.ChangeExtension(auditPath, ".png"));
            window.Close();
            File.AppendAllText(auditPath, JsonSerializer.Serialize(new { at = DateTimeOffset.Now, kind = "research-viewer-closed" }) + "\n");
            app.Shutdown();
        };
        stop.Start();
        app.Run();
        return 0;
    }

    private static async Task RunTranscript(string output, string path)
    {
        var transcript = await Task.Run(() => ResearchTranscript.Load(path));
        var refreshPath = Path.Combine(output, "refresh-ledger.json");
        File.Copy(path, refreshPath, overwrite: true);
        var window = new ResearchTranscriptWindow(transcript, refreshPath)
        {
            ShowActivated = false, WindowStartupLocation = WindowStartupLocation.Manual,
            Left = 10000, Top = 10000
        };
        try
        {
            window.Show();
            await Task.Delay(100);
            var grids = LogicalDescendants(window).OfType<DataGrid>().ToArray();
            var actions = grids.Single(g => g.Name == "ActionEntries");
            var observations = grids.Single(g => g.Name == "ObservationEntries");
            Check(actions.Items.Count == transcript.Actions.Count, "transcript displays all action candidates");
            Check(observations.Items.Count == transcript.Entries.Count, "transcript displays every raw observation");
            var conditionCells = observations.Items.Cast<object>().Select(row =>
                row.GetType().GetProperty("ConditionsCandidate")!.GetValue(row)?.ToString()).ToArray();
            foreach (var entry in transcript.Entries.Where(e => !string.IsNullOrEmpty(e.ConditionsCandidate)))
                Check(conditionCells.Contains(entry.ConditionsCandidate), "condition candidates reach actual WPF observation rows");
            var changeCells = observations.Items.Cast<object>().Select(row =>
                row.GetType().GetProperty("ConditionChangeCandidate")!.GetValue(row)?.ToString()).ToArray();
            foreach (var entry in transcript.Entries.Where(e => e.ConditionChangeCandidate is not null))
                Check(changeCells.Contains(entry.ConditionChangeCandidate), "condition transitions reach actual WPF observation rows");
            if (transcript.Actions.Any(a => a.MoveNameCandidate == "Tear Balm"))
            {
                var itemNames = actions.Items.Cast<object>().Select(row => row.GetType().GetProperty("Move")!.GetValue(row)?.ToString()).ToArray();
                foreach (var name in new[] { "Tear Balm", "EP Charge I" }.Where(name => transcript.Actions.Any(a => a.MoveNameCandidate == name)))
                    Check(itemNames.Contains(name + " (candidate)"),
                        "native-generated item name reaches the actual WPF action rows: " + name);
            }
            var intervalChoice = LogicalDescendants(window).OfType<ComboBox>().Single(c => c.Name == "ResearchIntervalChoice");
            Check(intervalChoice.Items.Count == transcript.Intervals.Count + 2, "all engine intervals and unframed scope available");
            intervalChoice.SelectedIndex = 1;
            Check(observations.Items.Count == transcript.Entries.Count(e => e.IntervalId is null), "unframed filter retains outside-interval records");
            if (transcript.Intervals.Count > 0)
            {
                intervalChoice.SelectedIndex = intervalChoice.Items.Count - 1;
                var lastInterval = transcript.Intervals[^1].Id;
                Check(actions.Items.Count == transcript.Actions.Count(a => a.IntervalId == lastInterval), "last fight action filter isolates its candidates");
                Check(observations.Items.Count == transcript.Entries.Count(e => e.IntervalId == lastInterval), "last fight raw filter isolates its evidence");
                Render(window, Path.Combine(output, "research-last-interval.png"));
            }
            intervalChoice.SelectedIndex = 0;
            actions.SelectedIndex = 0;
            var details = LogicalDescendants(window).OfType<TextBox>().Single();
            if (transcript.Actions.Count > 0)
            {
                var firstHook = transcript.Entries.First(e => e.Id == transcript.Actions[0].ObservationId).Hook;
                Check(firstHook is not null && details.Text.Contains(firstHook), "action selection exposes linked raw evidence");
            }
            var tabs = LogicalDescendants(window).OfType<TabControl>().Single();
            tabs.SelectedIndex = 1;
            observations.SelectedIndex = 0;
            Check(details.Text.Contains("executable"), "marker selection exposes original raw marker");
            Render(window, Path.Combine(output, "research-observations.png"));
            var conditionEntry = transcript.Entries.FirstOrDefault(e => e.TargetCandidate == "Agate" &&
                e.ConditionChangeCandidate == "STR UP: Expired (candidate)") ??
                transcript.Entries.FirstOrDefault(e => e.ConditionChangeCandidate is not null);
            if (conditionEntry is not null)
            {
                observations.SelectedIndex = transcript.Entries.ToList().IndexOf(conditionEntry);
                observations.ScrollIntoView(observations.SelectedItem);
                await Task.Delay(100);
                Render(window, Path.Combine(output, "research-condition-transition.png"));
            }
            tabs.SelectedIndex = 0;
            actions.SelectedIndex = transcript.Actions.Count - 1;
            Render(window, Path.Combine(output, "research-actions.png"));
            Console.WriteLine($"Research transcript WPF check: {actions.Items.Count} candidates, {observations.Items.Count} observations, raw evidence selection passed.");
            var ledger = JsonNode.Parse(File.ReadAllText(path))!.AsObject();
            var source = Path.Combine(output, "refresh-source.jsonl");
            var extra = new JsonObject { ["kind"] = "future-marker", ["unknownPayload"] = "retained" };
            File.WriteAllBytes(source, File.ReadAllBytes(transcript.SourcePath));
            File.AppendAllText(source, extra.ToJsonString() + "\n");
            ledger["tracePath"] = Path.GetFullPath(source);
            ledger["traceSha256"] = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(source)));
            ledger.Remove("traceCommittedLength");
            ledger["observations"]!.AsArray().Add(new JsonObject { ["observationId"] = "refresh:unknown", ["raw"] = extra });
            ledger["actionTimeline"]!["timeline"]!.AsArray().Add(new JsonObject { ["observationId"] = "refresh:unknown", ["kind"] = "UnknownObservation" });
            if (transcript.Intervals.Count > 0) intervalChoice.SelectedIndex = intervalChoice.Items.Count - 1;
            File.WriteAllText(refreshPath, ledger.ToJsonString());
            File.SetLastWriteTimeUtc(refreshPath, DateTime.UtcNow.AddSeconds(2));
            if (transcript.Intervals.Count > 0)
            {
                var heading = LogicalDescendants(window).OfType<TextBlock>().First(t => t.Text.StartsWith("PARTIAL RESEARCH"));
                await Wait(() => heading.Text.Contains($"{transcript.Entries.Count + 1:N0} observations"), "filtered research window follows ledger updates");
                Check(intervalChoice.SelectedIndex == intervalChoice.Items.Count - 1, "refresh preserves selected engine interval");
                Check(observations.Items.Count == transcript.Entries.Count(e => e.IntervalId == transcript.Intervals[^1].Id),
                    "unframed append does not contaminate selected fight");
                intervalChoice.SelectedIndex = 0;
            }
            await Wait(() => observations.Items.Count == transcript.Entries.Count + 1, "research window follows atomic ledger updates");
            File.WriteAllText(refreshPath, "{broken");
            File.SetLastWriteTimeUtc(refreshPath, DateTime.UtcNow.AddSeconds(4));
            await Task.Delay(1200);
            Check(observations.Items.Count == transcript.Entries.Count + 1, "failed refresh retains the last valid evidence snapshot");
            Console.WriteLine("Research transcript refresh and malformed-update retention passed.");
        }
        finally { window.Close(); }
    }

    private static async Task RunCase(string output, string mode)
    {
        var data = Path.Combine(output, mode + "-" + Guid.NewGuid().ToString("N"));
        var live = Path.Combine(data, "live");
        Directory.CreateDirectory(live);
        Environment.SetEnvironmentVariable("SORA2_DETAILS_DATA_DIR", data);
        Environment.SetEnvironmentVariable("SORA2_DETAILS_RESEARCH_REPLAY", null);
        Environment.SetEnvironmentVariable("SORA2_DETAILS_METER_ONLY", "1");
        var transcriptMode = mode.EndsWith("transcript");
        Environment.SetEnvironmentVariable("SORA2_DETAILS_CAPTURE_PROFILE", transcriptMode ? "Transcript" : "HealingResearch");
        var trace = Path.Combine(live, "probe-session-audit.jsonl");
        var stop = Path.Combine(live, "stop-audit");
        Process? helper = null;
        try
        {
            var failed = mode.Contains("failed");
            if (failed)
            {
                File.WriteAllText(trace, "{\"kind\": \"executable\"}\nTraceback: access denied\n");
                var results = Path.Combine(data, "probe-session", "results");
                Directory.CreateDirectory(results);
                File.WriteAllText(Path.Combine(results, "audit.json"), "{\"ok\":false}");
            }
            else
            {
                var start = new ProcessStartInfo(Environment.ProcessPath!) { UseShellExecute = false, CreateNoWindow = true };
                foreach (var arg in new[] { "--helper", trace, stop }) start.ArgumentList.Add(arg);
                helper = Process.Start(start)!;
                await Wait(() => File.Exists(trace), "simulated probe armed");
            }
            var current = Path.Combine(live, "current.json");
            File.WriteAllText(current, JsonSerializer.Serialize(new
            {
                trace, stopFile = stop, requestId = "audit", serverPid = helper?.Id ?? 0,
                bridgePid = mode.EndsWith("raw") ? 0 : helper?.Id ?? 0,
                hostPid = 0, targetPid = 0, captureProfile = transcriptMode ? "Transcript" : "HealingResearch"
            }));
            var store = new EncounterStore(Path.Combine(data, "encounters"));
            var actor = new Actor("estelle", "Estelle", CombatTeam.Party);
            var effect = new CombatEvent(1, DateTimeOffset.Now, "a1", "estelle", "estelle", null,
                "Observed test effect", CombatEventKind.ActionObserved, null, null, null);
            var encounter = new Encounter("audit", "Audit event window", DateTimeOffset.Now,
                EncounterOutcome.InProgress, false, [actor], [effect], [$"Raw trace: {Path.GetFileName(trace)}"], 2);
            store.Save(encounter);
            var window = new MainWindow("sora2-desktop-check-" + Guid.NewGuid().ToString("N"));
            window.Show();
            await Task.Delay(100);
            ((DispatcherTimer)Field(window, "_gameDetectionTimer")).Stop();
            Environment.SetEnvironmentVariable("SORA2_DETAILS_METER_ONLY", null);
            Call(window, "RefreshCaptureStatus");
            Call(window, "ReloadHistory");
            var label = (TextBlock)window.FindName("DataSourceLabel");
            Check(label.Text == (failed ? "Error" : mode.EndsWith("raw") ? "Raw trace" : "Capturing"),
                mode + " truthful capture status: " + label.Text);

            var liveChoice = (System.Windows.Forms.ToolStripMenuItem)Field(window, "_liveProfileChoice");
            var researchChoice = (System.Windows.Forms.ToolStripMenuItem)Field(window, "_researchProfileChoice");
            var transcriptChoice = (System.Windows.Forms.ToolStripMenuItem)Field(window, "_transcriptProfileChoice");
            Call(window, "RefreshTrayCommands");
            Check(researchChoice.Checked == !transcriptMode && transcriptChoice.Checked == transcriptMode &&
                !liveChoice.Checked, "capture mode reflects launch profile");
            if (transcriptMode)
            {
                typeof(MainWindow).GetField("_captureError", Private)!.SetValue(window, "unused meter pipe warning");
                Call(window, "RefreshCaptureStatus");
                Check(label.Text == "Capturing" && label.ToolTip.ToString()!.Contains("partial action stream"),
                    "transcript reports its own active recording despite unrelated meter listener warning");
            }
            Check(liveChoice.Enabled == failed, "mode change blocked while capture may be active");
            if (failed)
            {
                liveChoice.PerformClick();
                await Wait(() => Environment.GetEnvironmentVariable("SORA2_DETAILS_CAPTURE_PROFILE") == "Live",
                    "tray switches to Live after failed attachment");
                Check(liveChoice.Checked && !researchChoice.Checked, "tray checks selected Live mode");
                researchChoice.PerformClick();
                await Wait(() => Environment.GetEnvironmentVariable("SORA2_DETAILS_CAPTURE_PROFILE") == "HealingResearch",
                    "tray switches back to effect research");
            }

            var settings = (Window)Activator.CreateInstance(typeof(SettingsWindow), Private, null,
                [Field(window, "_displaySettings"), true], null)!;
            settings.Owner = window;
            settings.Show();
            var check = (CheckBox)settings.FindName("AlwaysOnTopChoice");
            var color = ((SolidColorBrush)check.Foreground).Color;
            Check(color.R > 200 && color.G > 200 && color.B > 200, "checkbox text contrasts with dark settings");
            var slider = (Slider)settings.FindName("OpacityChoice");
            Check(slider.Minimum == 0.6 && slider.Maximum == 1, "opacity range 60-100 percent");
            slider.Value = 0.73;
            var updated = settings.GetType().GetProperty("UpdatedSettings", Private)!.GetValue(settings)!;
            Call(window, "SetDisplaySettings", updated);
            Check(Math.Abs(window.Opacity - 0.73) < 0.001, "slider applies opacity");
            using (var saved = JsonDocument.Parse(File.ReadAllText(Path.Combine(data, "meter-display.json"))))
                Check(Math.Abs(saved.RootElement.GetProperty("Opacity").GetDouble() - 0.73) < 0.001, "opacity persisted");
            if (mode == "x-active") Render(settings, Path.Combine(output, "settings.png"));
            settings.Close();

            var timeline = new TimelineWindow(encounter) { Owner = window };
            timeline.Show();
            store.Save(encounter with { Events = [effect, effect with { Sequence = 2, Kind = CombatEventKind.ResourceChange, Resource = "CP" }] });
            await Wait(() => ((TextBlock)timeline.FindName("Heading")).Text.Contains("2 entries"), "open timeline refreshes after saved event");
            Check(((TextBlock)window.FindName("FooterLabel")).Text.Contains("2 log entries"), "meter shows observed event count");
            if (mode == "x-active") Render(timeline, Path.Combine(output, "timeline.png"));
            timeline.Close();

            var closed = false;
            window.Closed += (_, _) => closed = true;
            var chooseExit = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(20) };
            chooseExit.Tick += (_, _) =>
            {
                var dialog = System.Windows.Application.Current.Windows.Cast<Window>()
                    .FirstOrDefault(w => w.GetType().Name == "CloseChoiceDialog");
                if (dialog is null) return;
                var remember = (CheckBox)Field(dialog, "_rememberChoice");
                Check(((SolidColorBrush)remember.Foreground).Color == Colors.White, "close dialog checkbox readable");
                var exit = LogicalDescendants(dialog).OfType<Button>().Single(button => Equals(button.Content, "Exit app"));
                exit.RaiseEvent(new RoutedEventArgs(Button.ClickEvent));
            };
            chooseExit.Start();
            var watch = Stopwatch.StartNew();
            if (mode.StartsWith("tray"))
            {
                var menu = (System.Windows.Forms.ContextMenuStrip)Field(window, "_trayMenu");
                menu.Items.OfType<System.Windows.Forms.ToolStripMenuItem>()
                    .Single(item => item.Text == "Exit Sora 2 Details").PerformClick();
            }
            else window.Close();
            await Wait(() => closed, mode + " completes desktop shutdown", 8);
            chooseExit.Stop();
            Check(!File.Exists(current), "completed capture metadata cleaned");
            Check(helper is null || helper.HasExited, "capture helper actually exited");
            Console.WriteLine($"{mode}: desktop closed and capture cleaned in {watch.Elapsed.TotalSeconds:F2}s");
        }
        finally
        {
            if (helper is not null && !helper.HasExited)
            {
                File.WriteAllText(stop, "stop");
                await helper.WaitForExitAsync().WaitAsync(TimeSpan.FromSeconds(3));
            }
            helper?.Dispose();
        }
    }

    private static IEnumerable<DependencyObject> LogicalDescendants(DependencyObject obj)
    {
        foreach (var child in LogicalTreeHelper.GetChildren(obj).OfType<DependencyObject>())
        {
            yield return child;
            foreach (var descendant in LogicalDescendants(child)) yield return descendant;
        }
    }
    private static void Render(Window window, string path)
    {
        window.UpdateLayout();
        var bitmap = new RenderTargetBitmap((int)window.ActualWidth, (int)window.ActualHeight, 96, 96, PixelFormats.Pbgra32);
        bitmap.Render(window);
        var encoder = new PngBitmapEncoder(); encoder.Frames.Add(BitmapFrame.Create(bitmap));
        using var stream = File.Create(path); encoder.Save(stream);
    }
    private static async Task Wait(Func<bool> condition, string message, int seconds = 5)
    {
        var timer = Stopwatch.StartNew();
        while (!condition() && timer.Elapsed.TotalSeconds < seconds) await Task.Delay(20);
        Check(condition(), message);
    }
    private static void Check(bool passed, string message)
    {
        if (!passed) throw new InvalidOperationException(message);
    }
}
