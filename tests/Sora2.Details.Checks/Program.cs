using Sora2.Details.Core;

var path = Path.Combine(AppContext.BaseDirectory, "samples", "command-battles.json");
var encounters = EncounterReplay.Load(path);
var fight = encounters.Single(e => e.Id == "sample-001");

Check(EncounterProjection.Rows(fight, MeterMode.Damage).Sum(r => r.Value) == 380, "party damage");
Check(EncounterProjection.Rows(fight, MeterMode.Healing).Single().Value == 70, "effective healing");
Check(EncounterProjection.Rows(fight, MeterMode.Taken).Sum(r => r.Value) == 140, "damage taken");
Check(EncounterProjection.Rows(fight, MeterMode.Deaths).Single().Value == 1, "knockout count");
Check(EncounterProjection.Moves(fight, MeterMode.Taken, "wolf-2").Single().DamageClass == DamageClass.Arts, "damage class");
Check(EncounterProjection.DeathRecap(fight, 5).Select(e => e.Sequence).SequenceEqual([4, 5]), "death recap");
var longFight = fight with { Events = Enumerable.Range(1, 25)
    .Select(sequence => fight.Events[0] with { Sequence = sequence }).Reverse().ToArray() };
Check(EncounterProjection.FullTimeline(longFight).Select(e => e.Sequence)
    .SequenceEqual(Enumerable.Range(1, 25).Select(value => (long)value)),
    "full combat log includes ordered results beyond twenty");
var hpCost = new CombatEvent(3, fight.StartedAt, null, null, "joshua", null,
    "HP loss (source unverified)", CombatEventKind.HpLoss, 20, 100, 80);
var costThenKnockout = fight with { Events = [hpCost, fight.Events[3], fight.Events[4]] };
Check(EncounterProjection.Rows(costThenKnockout, MeterMode.Taken).Single().Value == 80,
    "unattributed HP loss does not inflate damage taken");
Check(EncounterProjection.DeathRecap(costThenKnockout, 5).Select(e => e.Kind)
    .SequenceEqual([CombatEventKind.HpLoss, CombatEventKind.Damage, CombatEventKind.Knockout]),
    "HP loss appears in the victim's death recap");
Check(EncounterProjection.Recent(encounters).First().Id == "sample-003", "newest encounter");

var many = Enumerable.Range(0, 12)
    .Select(i => fight with { Id = $"extra-{i}", StartedAt = fight.StartedAt.AddMinutes(i) })
    .ToArray();
Check(EncounterProjection.Recent(many).Count == 10, "recent fight limit");
Check(many.Length == 12, "full history retained");

// Live Agate HP observation is deliberately partial: only taken/healing can be projected.
var researchPath = Path.Combine(AppContext.BaseDirectory, "samples", "research",
    "command-result-20260926.partial.json");
var research = EncounterReplay.Load(researchPath).Single();
Check(!research.IsComplete && research.Outcome == EncounterOutcome.Victory,
    "live research replay remains partial despite reported victory");
Check(research.Events.Count == 4, "four observed in-battle HP changes");
Check(EncounterProjection.Rows(research, MeterMode.Taken).Single().Value == 1408,
    "observed Agate HP losses reconcile to taken meter");
Check(EncounterProjection.Rows(research, MeterMode.Healing).Single().Value == 304,
    "observed Agate HP gain reconciles to healing meter");
Check(EncounterProjection.Rows(research, MeterMode.Damage).Count == 0,
    "unwatched enemy HP must not create damage-done totals");

var fullHpPath = Path.Combine(AppContext.BaseDirectory, "samples", "research",
    "full-hp-path-20260926.partial.json");
var fullHpResearch = EncounterReplay.Load(fullHpPath).Single();
Check(!fullHpResearch.IsComplete && fullHpResearch.Events.Count == 18,
    "all-actor HP research replay stays partial");
Check(EncounterProjection.Rows(fullHpResearch, MeterMode.Damage).Single().Value == 57680,
    "two observed enemy HP losses reconcile to unknown-source damage");
Check(EncounterProjection.Rows(fullHpResearch, MeterMode.Taken).Single().Value == 2113,
    "observed party HP losses reconcile to taken meter");
Check(EncounterProjection.Rows(fullHpResearch, MeterMode.Healing).Single().Value == 1043,
    "observed party HP gains reconcile to healing meter");

var attributedPath = Path.Combine(AppContext.BaseDirectory, "samples", "research",
    "attributed-attack-20260926.partial.json");
var attributed = EncounterReplay.Load(attributedPath).Single();
var attributedRows = EncounterProjection.Rows(attributed, MeterMode.Damage)
    .ToDictionary(row => row.Name, row => row.Value);
Check(!attributed.IsComplete && attributed.Events.Count == 13,
    "attributed live attack path remains partial");
Check(attributedRows["Estelle"] == 32535 && attributedRows["Agate"] == 20284 &&
      attributedRows["Scherazard"] == 4991 && attributedRows["Tita"] == 2076,
    "observed live damage reconciles by character");
Check(attributedRows.Values.Sum() == 59886,
    "effective damage equals two observed enemy HP pools");
var estelleId = attributed.Actors.Single(actor => actor.Name == "Estelle").Id;
var estelleResults = EncounterProjection.ResultsForRow(attributed, MeterMode.Damage, estelleId);
Check(estelleResults.Count > 1 && estelleResults.Sum(effect => effect.EffectiveAmount ?? 0) == attributedRows["Estelle"] &&
      estelleResults.Zip(estelleResults.Skip(1)).All(pair => pair.First.Sequence < pair.Second.Sequence),
    "unknown live moves remain distinct ordered results and reconcile to Estelle's meter row");
Check(EncounterProjection.Moves(attributed, MeterMode.Damage, estelleId)
      .Count(move => move.Name.StartsWith("Move unknown · result #", StringComparison.Ordinal)) ==
      estelleResults.Count(effect => string.IsNullOrWhiteSpace(effect.MoveName)),
    "unknown move results are not merged by damage type");
Check(attributed.Events.Single(effect => effect.MoveName == "Normal Attack (player-reported)")
    .EffectiveAmount == 10452, "controlled Agate normal Attack matches the observed HP delta");
Check(attributed.Events.Count(effect => effect.EffectiveAmount == 0) == 2,
    "hits on an already-zero-HP target do not inflate the meter");

var actionProbePath = Path.Combine(AppContext.BaseDirectory, "samples", "research",
    "action-id-attack-20260927.partial.json");
var actionProbe = EncounterReplay.Load(actionProbePath).Single();
var actionRows = EncounterProjection.Rows(actionProbe, MeterMode.Damage)
    .ToDictionary(row => row.Name, row => row.Value);
Check(!actionProbe.IsComplete && actionProbe.Events.Count == 19 &&
      actionProbe.Issues!.Any(issue => issue.Contains("4 HP writes")),
    "second live fight keeps unmatched HP writes visible as a coverage gap");
Check(actionRows["Agate"] == 5432 && actionRows["Scherazard"] == 48276 &&
      actionRows["Estelle"] == 23942 && actionRows.GetValueOrDefault("Tita") == 0,
    "paired damage results reconcile by source instance");
Check(actionRows.Values.Sum() == 2 * 38825,
    "effective damage equals both observed enemy HP pools");
Check(actionProbe.Events.Count(effect => effect.EffectiveAmount == 0) == 6,
    "six post-knockout results remain in the timeline without inflating totals");
Check(actionProbe.Events.Single(effect => effect.MoveName == "Normal Attack (player-reported)")
    .ResolvedAmount == 5432, "controlled Agate Attack preserves the observed result amount");

// Live research example: Agate recovered only 81 HP from a displayed 1,500 Tear Balm heal.
var balm = new CombatEvent(1, fight.StartedAt, "balm-1", null, "agate",
    "tear-balm", "Tear Balm", CombatEventKind.Healing, 81, 6601, 6682,
    ResolvedAmount: 1500);
var balmFight = new Encounter("balm-check", "Tear Balm", fight.StartedAt,
    EncounterOutcome.Victory, true,
    [new Actor("agate", "Agate", CombatTeam.Party)],
    [balm]);
Check(EncounterProjection.Rows(balmFight, MeterMode.Healing).Single().Value == 81,
    "overheal excluded from effective healing meter");
Check(balmFight.Events.Single().ResolvedAmount == 1500, "resolved heal preserved separately");
var overkillHit = fight.Events[0] with { EffectiveAmount = 100, ResolvedAmount = 150 };
Check(DamageAmounts.From(overkillHit) == new DamageAmounts(150, 100, 50),
    "hit total and effective amount expose fifty overkill");
Check(DamageAmounts.From(overkillHit with { ResolvedAmount = null }).Overkill is null &&
      DamageAmounts.From(overkillHit with { ResolvedAmount = 90 }).Overkill is null &&
      DamageAmounts.From(balm).Overkill is null,
    "unobserved or inconsistent results do not invent overkill");

var unknownHit = fight.Events[0] with { SourceId = null, MoveId = null, MoveName = null,
    DamageClass = DamageClass.Unknown };
var unknownFight = fight with { Events = [unknownHit] };
Check(EncounterProjection.Rows(unknownFight, MeterMode.Damage).Single().Key == "unknown",
    "enemy HP damage with unknown source remains visible");
Check(EncounterProjection.Moves(unknownFight, MeterMode.Damage, "unknown").Single().Value == 100,
    "unknown-source move breakdown reconciles");
var groupedFight = fight with { Events = [
    fight.Events[0] with { Sequence = 21, MoveName = "Shatter Break", EffectiveAmount = 100 },
    fight.Events[0] with { Sequence = 22, MoveName = "Shatter Break", EffectiveAmount = 80 },
    fight.Events[0] with { Sequence = 23, MoveName = null, EffectiveAmount = 30 },
    fight.Events[0] with { Sequence = 24, MoveName = null, EffectiveAmount = 20 }
] };
var drillGroups = EncounterProjection.MoveGroups(groupedFight, MeterMode.Damage, fight.Events[0].SourceId!);
Check(drillGroups.Count == 3 && drillGroups.Single(group => group.Name == "Shatter Break").Hits.Count == 2 &&
      drillGroups.Sum(group => group.Value) == 230,
    "drilldown groups named hits and keeps unknown hits separate without losing damage");

var start = new EncounterStarted("recorded-1", fight.StartedAt, fight.Actors);
var assembler = new EncounterAssembler();
Check(!assembler.Accept(start).Single().IsComplete, "active encounter is provisional");
var first = fight.Events[0];
Check(assembler.Accept(new EffectObserved(start.EncounterId, first)).Single().Events.Count == 1, "first effect recorded");
Check(assembler.Accept(new EffectObserved(start.EncounterId, first)).Single().Events.Count == 1, "identical retransmission deduplicated");
var finished = assembler.Accept(new EncounterEnded(start.EncounterId, fight.StartedAt.AddMinutes(1), EncounterOutcome.Victory)).Single();
Check(finished.IsComplete && EncounterProjection.Rows(finished, MeterMode.Damage).Single().Value == 100,
    "assembled damage survives battle end");

var gapStart = start with { EncounterId = "gap-check" };
assembler.Accept(gapStart);
assembler.Accept(new EffectObserved(gapStart.EncounterId, fight.Events[1]));
var gapped = assembler.Accept(new EncounterEnded(gapStart.EncounterId, fight.StartedAt.AddMinutes(1), EncounterOutcome.Victory)).Single();
Check(!gapped.IsComplete && gapped.Issues!.Any(issue => issue.Contains("Missing event")), "sequence gap flagged");

var captureGapStart = start with { EncounterId = "capture-gap-check" };
assembler.Accept(captureGapStart);
assembler.Accept(new CaptureGap(captureGapStart.EncounterId, "queue overflow"));
Check(!assembler.Accept(new EncounterEnded(captureGapStart.EncounterId, fight.StartedAt.AddMinutes(1), EncounterOutcome.Victory))
    .Single().IsComplete, "capture gap flagged");

var encoded = CaptureMessageCodec.Serialize(new EffectObserved(start.EncounterId, first));
var decoded = (EffectObserved)CaptureMessageCodec.Deserialize(encoded);
Check(decoded.EncounterId == start.EncounterId && decoded.Effect.EffectiveAmount == 100,
    "capture wire format round trip");
var flagged = first with { RawResultFlags = 0x42000, IsCritical = null,
    DamageClass = DamageClass.Physical,
    DamageClassProvenance = "exact-result-flag/player-controlled-live-comparison" };
var flaggedDecoded = (EffectObserved)CaptureMessageCodec.Deserialize(
    CaptureMessageCodec.Serialize(new EffectObserved(start.EncounterId, flagged)));
Check(flaggedDecoded.Effect.RawResultFlags == 0x42000 &&
      flaggedDecoded.Effect.IsCritical is null &&
      flaggedDecoded.Effect.DamageClass == DamageClass.Physical &&
      flaggedDecoded.Effect.DamageClassProvenance == flagged.DamageClassProvenance,
    "raw result and class provenance survive capture without guessing critical status");
var contextObserved = flagged with { RawSourceContextFlags = 3, RawTargetStatus7C = 0 };
var contextDecoded = (EffectObserved)CaptureMessageCodec.Deserialize(
    CaptureMessageCodec.Serialize(new EffectObserved(start.EncounterId, contextObserved)));
Check(contextDecoded.Effect.IsCritical is null && contextDecoded.Effect.RawSourceContextFlags == 3 &&
      contextDecoded.Effect.RawTargetStatus7C == 0,
    "candidate source and target context survive capture without claiming a critical hit");
var rejectedOrphan = false;
try { assembler.Accept(new EffectObserved("missing", first)); }
catch (InvalidDataException) { rejectedOrphan = true; }
Check(rejectedOrphan, "orphan effect rejected rather than silently lost");
var unknownStart = start with { EncounterId = "unknown-check" };
assembler.Accept(unknownStart);
assembler.Accept(new EffectObserved(unknownStart.EncounterId, unknownHit));
Check(!assembler.Accept(new EncounterEnded(unknownStart.EncounterId, fight.StartedAt.AddMinutes(1),
    EncounterOutcome.Victory)).Single().IsComplete, "unknown attribution marks encounter partial");
var duplicateEncounterRejected = false;
try { assembler.Accept(unknownStart); }
catch (InvalidDataException) { duplicateEncounterRejected = true; }
Check(duplicateEncounterRejected, "encounter ID cannot be reused in one capture session");

var directory = Path.Combine(Path.GetTempPath(), "sora2-details-checks-" + Guid.NewGuid().ToString("N"));
try
{
    var store = new EncounterStore(directory);
    var recorder = new EncounterRecorder(store);
    await recorder.RunAsync(new FixtureSource([
        start, new EffectObserved(start.EncounterId, first),
        new EncounterEnded(start.EncounterId, fight.StartedAt.AddMinutes(1), EncounterOutcome.Victory)
    ]), CancellationToken.None);
    Check(store.LoadAll().Single().Events.Single().EffectiveAmount == 100, "record and reopen encounter");
    var historyCollisionRejected = false;
    try { await new EncounterRecorder(store).RunAsync(new FixtureSource([start]), CancellationToken.None); }
    catch (InvalidDataException) { historyCollisionRejected = true; }
    Check(historyCollisionRejected && store.LoadAll().Single().IsComplete,
        "restarted capture cannot overwrite a saved encounter ID");
    store.Save(balmFight);
    Check(store.LoadAll().Single(e => e.Id == "balm-check").Events.Single().ResolvedAmount == 1500,
        "resolved amount survives storage");
    await recorder.RunAsync(new FixtureSource([
        new EncounterStarted("recorded-2", fight.StartedAt.AddMinutes(2), fight.Actors)
    ]), CancellationToken.None);
    Check(store.LoadAll().Single(e => e.Id == "recorded-2").Outcome == EncounterOutcome.Interrupted,
        "source disconnect interrupts active encounter");

    var pipeName = "sora2-details-checks-" + Guid.NewGuid().ToString("N");
    using var pipeCancellation = new CancellationTokenSource();
    var pipeTask = Task.Run(() => new EncounterRecorder(store)
        .RunAsync(new CapturePipeSource(pipeName, allowFixture: true), pipeCancellation.Token));
    try
    {
        await SendPipeAsync(pipeName, [
            new EncounterStarted("pipe-complete", fight.StartedAt, fight.Actors),
            new EffectObserved("pipe-complete", first),
            new EncounterEnded("pipe-complete", fight.StartedAt.AddMinutes(1), EncounterOutcome.Victory)
        ]);
        await WaitForAsync(() => store.LoadAll().Any(e => e.Id == "pipe-complete" && e.IsComplete));
        await SendPipeAsync(pipeName, [
            new EncounterStarted("pipe-interrupted", fight.StartedAt.AddMinutes(2), fight.Actors),
            new EffectObserved("pipe-interrupted", first)
        ]);
        await WaitForAsync(() => store.LoadAll().Any(e => e.Id == "pipe-interrupted"
            && e.Outcome == EncounterOutcome.Interrupted));
    }
    finally
    {
        pipeCancellation.Cancel();
        try { await pipeTask; }
        catch (OperationCanceledException) { }
    }

    var badPipeName = "sora2-details-bad-build-" + Guid.NewGuid().ToString("N");
    var rejectedBuild = Task.Run(async () =>
    {
        await foreach (var _ in new CapturePipeSource(badPipeName).ReadAsync(CancellationToken.None)) { }
    });
    await using (var client = new System.IO.Pipes.NamedPipeClientStream(".", badPipeName,
        System.IO.Pipes.PipeDirection.Out, System.IO.Pipes.PipeOptions.Asynchronous))
    {
        await client.ConnectAsync(CancellationToken.None).WaitAsync(TimeSpan.FromSeconds(5));
        await using var writer = new StreamWriter(client) { AutoFlush = true };
        await writer.WriteLineAsync(CaptureMessageCodec.SerializeHello(new CaptureHello(
            CapturePipeSource.ProtocolVersion, CaptureOrigin.Game, "BAD-HASH",
            new CaptureCapabilities(true, true, true, true, true))));
    }
    var badBuildRejected = false;
    try { await rejectedBuild.WaitAsync(TimeSpan.FromSeconds(5)); }
    catch (InvalidDataException exception) when (exception.Message.Contains("Unsupported game executable"))
    { badBuildRejected = true; }
    Check(badBuildRejected, "unsupported executable rejected before capture");

    var replacement = finished with { Id = "replacement-stress" };
    var writerTask = Task.Run(() =>
    {
        for (var index = 0; index < 30; index++)
            store.Save(replacement with { Label = $"snapshot-{index}" });
    });
    while (!writerTask.IsCompleted)
    {
        var observed = store.LoadAll().FirstOrDefault(e => e.Id == "replacement-stress");
        if (observed is not null) Check(observed.Events.Count == 1, "concurrent snapshot is whole");
        await Task.Delay(1);
    }
    await writerTask;
    Check(store.LoadAll().Single(e => e.Id == "replacement-stress").Label == "snapshot-29",
        "latest atomic replacement persists");
}
finally
{
    if (Directory.Exists(directory)) Directory.Delete(directory, recursive: true);
}

Console.WriteLine("Replay, projection, recorder, and persistence checks passed.");

static void Check(bool condition, string name)
{
    if (!condition) throw new Exception($"Check failed: {name}");
}

static async Task SendPipeAsync(string name, IReadOnlyList<CaptureMessage> messages)
{
    await using var client = new System.IO.Pipes.NamedPipeClientStream(".", name,
        System.IO.Pipes.PipeDirection.Out, System.IO.Pipes.PipeOptions.Asynchronous);
    await client.ConnectAsync(CancellationToken.None).WaitAsync(TimeSpan.FromSeconds(5));
    await using var writer = new StreamWriter(client) { AutoFlush = true };
    await writer.WriteLineAsync(CaptureMessageCodec.SerializeHello(new CaptureHello(
        CapturePipeSource.ProtocolVersion, CaptureOrigin.Fixture, null,
        new CaptureCapabilities(true, true, true, true, true))));
    foreach (var message in messages)
        await writer.WriteLineAsync(CaptureMessageCodec.Serialize(message));
}

static async Task WaitForAsync(Func<bool> condition)
{
    using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(5));
    while (!condition())
        await Task.Delay(20, timeout.Token);
}

sealed class FixtureSource(IReadOnlyList<CaptureMessage> messages) : ICombatCaptureSource
{
    public CaptureCapabilities Capabilities => new(true, true, true, true, true);

    public async IAsyncEnumerable<CaptureMessage> ReadAsync(
        [System.Runtime.CompilerServices.EnumeratorCancellation] CancellationToken cancellationToken)
    {
        foreach (var message in messages)
        {
            cancellationToken.ThrowIfCancellationRequested();
            yield return message;
            await Task.Yield();
        }
    }
}
