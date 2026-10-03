using Sora2.Details.Core;

ResearchTranscriptChecks.Run();

var path = Path.Combine(AppContext.BaseDirectory, "samples", "command-battles.json");
var encounters = EncounterReplay.Load(path);
var fight = encounters.Single(e => e.Id == "sample-001");
var markedBosses = new HashSet<string> { fight.Id };
var markedRegular = new HashSet<string> { "sample-002" };
var noMarks = new HashSet<string>();
var bossFocused = EncounterHistoryView.Visible(encounters, true, markedBosses, markedRegular);
Check(bossFocused.Count == encounters.Count - 1 &&
      bossFocused.Any(e => e.Id == fight.Id) &&
      bossFocused.Any(e => e.Id == "sample-003") &&
      bossFocused.All(e => e.Id != "sample-002"),
    "boss-focused history keeps unknown fights visible and hides marked regular fights");
Check(EncounterHistoryView.Visible(encounters, false, markedBosses, markedRegular).Count == encounters.Count,
    "all-fights history retains every encounter");
var newestSavedEncounter = encounters.OrderByDescending(encounter => encounter.StartedAt).First();
Check(EncounterHistoryView.FollowNewest(encounters, captureActive: false,
          currentCaptureEncounter: null)?.Id == newestSavedEncounter.Id,
    "follow-newest selects the latest saved fight after capture detaches");
Check(EncounterHistoryView.FollowNewest(encounters, captureActive: true,
          currentCaptureEncounter: null) is null,
    "follow-newest waits for the active capture instead of showing an older fight");
Check(EncounterHistoryView.FollowNewest(encounters, captureActive: true,
          currentCaptureEncounter: fight)?.Id == fight.Id,
    "follow-newest selects the encounter linked to the active capture");
Check(EncounterHistoryView.Describe(fight, BossClassification.MarkedBoss).Contains("CONFIRMED BOSS") &&
      EncounterHistoryView.Describe(fight, BossClassification.MarkedBoss).Contains("Wolf A") &&
      EncounterHistoryView.Describe(fight, BossClassification.MarkedBoss).Contains("Wolf B"),
    "boss history label includes marker and enemy name");
var walterFight = fight with { Id = "walter-candidate", Actors = [new Actor("walter", "Walter", CombatTeam.Enemy,
    LookupUnitId: "chr0120_e00")] };
Check(EncounterHistoryView.Classify(walterFight, noMarks, noMarks) == BossClassification.CatalogBossCandidate,
    "catalog boss name is highlighted from exact English table label");
var plusFight = fight with { Id = "plus-candidate", Actors = [new Actor("slug", "Sticky Slug+", CombatTeam.Enemy)] };
Check(EncounterHistoryView.Classify(plusFight, noMarks, noMarks) == BossClassification.PlusMiniBossCandidate,
    "plus-suffixed enemy is a mini-boss candidate");
var unknownCandidateFight = fight with { Id = "unknown-fight", Actors = [new Actor("unknown", "? Enemy 1 (ID 60001)", CombatTeam.Enemy)] };
var failOpenHistory = EncounterHistoryView.Visible([walterFight, plusFight, unknownCandidateFight], true,
    noMarks, noMarks);
Check(failOpenHistory.Count == 3 && failOpenHistory.Any(e => e.Id == walterFight.Id) &&
      failOpenHistory.Any(e => e.Id == plusFight.Id) &&
      failOpenHistory.Any(e => e.Id == unknownCandidateFight.Id),
    "boss-focused history keeps candidates and unknown fights visible by default");
var likelyBossHistory = EncounterHistoryView.Visible([walterFight, plusFight, unknownCandidateFight],
    HistoryFilterMode.LikelyBosses, noMarks, noMarks);
Check(likelyBossHistory.Count == 2 && likelyBossHistory.Any(e => e.Id == walterFight.Id) &&
      likelyBossHistory.Any(e => e.Id == plusFight.Id) &&
      likelyBossHistory.All(e => e.Id != unknownCandidateFight.Id),
    "likely-boss mode keeps boss-name and plus candidates while hiding unclassified fights");
var markedPlusRegular = new HashSet<string> { plusFight.Id };
var confirmedModeHistory = EncounterHistoryView.Visible([walterFight, plusFight, unknownCandidateFight],
    HistoryFilterMode.Confirmed, noMarks, markedPlusRegular);
Check(confirmedModeHistory.Count == 2 && confirmedModeHistory.Any(e => e.Id == walterFight.Id) &&
      confirmedModeHistory.Any(e => e.Id == unknownCandidateFight.Id) &&
      confirmedModeHistory.All(e => e.Id != plusFight.Id),
    "confirmed fail-open mode hides only explicitly marked regular fights");
var unfilteredHistory = EncounterHistoryView.Visible([walterFight, plusFight, unknownCandidateFight],
    HistoryFilterMode.Unfiltered, noMarks, markedPlusRegular);
Check(unfilteredHistory.Count == 3 && unfilteredHistory.Any(e => e.Id == plusFight.Id),
    "unfiltered mode includes explicitly marked regular fights");
Check(EncounterHistoryView.Visible([unknownCandidateFight], true,
    new HashSet<string> { unknownCandidateFight.Id }, noMarks)
    .Single().Id == unknownCandidateFight.Id, "manual boss mark keeps an otherwise unknown fight visible");
Check(EncounterHistoryView.Visible([unknownCandidateFight], HistoryFilterMode.LikelyBosses,
    new HashSet<string> { unknownCandidateFight.Id }, noMarks).Single().Id == unknownCandidateFight.Id,
    "likely-boss mode keeps manually confirmed bosses");
Check(EncounterHistoryView.Visible([walterFight], true, noMarks, new HashSet<string> { walterFight.Id }).Count == 0,
    "manual regular mark excludes a catalog boss candidate");
Check(EncounterHistoryView.Classify(walterFight, noMarks, new HashSet<string> { walterFight.Id }) ==
      BossClassification.MarkedRegular, "manual regular mark overrides catalog candidate");
var repeatedEnemies = fight with { Actors = [
    new Actor("wolf-1", "Wolf", CombatTeam.Enemy),
    new Actor("wolf-2", "Wolf", CombatTeam.Enemy),
    new Actor("unknown-1", "? Enemy 3 (ID 60003)", CombatTeam.Enemy)] };
Check(EncounterHistoryView.EnemySummary(repeatedEnemies) == "Wolf ×2, Unknown enemy",
    "history groups repeated and unresolved enemies");
var bossWithAdds = fight with { Id = "confirmed-boss-with-adds", Actors = [
    new Actor("walter", "Walter", CombatTeam.Enemy),
    new Actor("add", "Wolf", CombatTeam.Enemy)] };
Check(EncounterHistoryView.Describe(bossWithAdds, BossClassification.MarkedBoss).Contains("Walter") &&
      !EncounterHistoryView.Describe(bossWithAdds, BossClassification.MarkedBoss).Contains("Wolf"),
    "confirmed boss entry names the known boss without its adds");
var plusWithAdds = plusFight with { Actors = [
    new Actor("slug", "Sticky Slug+", CombatTeam.Enemy),
    new Actor("add", "Wolf", CombatTeam.Enemy)] };
Check(EncounterHistoryView.Describe(plusWithAdds, BossClassification.PlusMiniBossCandidate)
          .Contains("Sticky Slug+") &&
      !EncounterHistoryView.Describe(plusWithAdds, BossClassification.PlusMiniBossCandidate).Contains("Wolf"),
    "plus-candidate entry names the plus mob without its adds");

var playerDealt = EncounterProjection.Rows(fight, MeterMode.PlayerDamage).ToDictionary(row => row.Key);
var enemyDealt = EncounterProjection.Rows(fight, MeterMode.EnemyDamage).ToDictionary(row => row.Key);
Check(playerDealt.Values.Sum(row => row.Value) == 380 &&
      enemyDealt.Values.Sum(row => row.Value) == 140 &&
      enemyDealt["wolf-1"].Value == 60 && enemyDealt["wolf-2"].Value == 80,
    "player and enemy damage dealt remain separate");
Check(EncounterProjection.Rows(fight, MeterMode.Healing).Single().Value == 70, "effective healing");
var playerTaken = EncounterProjection.Rows(fight, MeterMode.PlayerTaken).ToDictionary(row => row.Key);
Check(playerTaken["estelle"].Value == 60 && playerTaken["joshua"].Value == 80,
    "player damage taken groups by victim");
var enemyTaken = EncounterProjection.Rows(fight, MeterMode.EnemyTaken).ToDictionary(row => row.Key);
Check(enemyTaken["wolf-1"].Value == 300 && enemyTaken["wolf-2"].Value == 80,
    "enemy damage taken groups by victim");
var wolfAttackers = EncounterProjection.Attackers(fight, MeterMode.EnemyTaken, "wolf-1")
    .ToDictionary(row => row.Key);
Check(wolfAttackers["estelle"].Value == 180 && wolfAttackers["joshua"].Value == 120,
    "enemy victim drills into party attackers");
Check(EncounterProjection.Rows(fight, MeterMode.Deaths).Single().Value == 1, "knockout count");
Check(EncounterProjection.MoveGroups(fight, MeterMode.PlayerTaken, "joshua", "wolf-2")
    .Single().DamageClass == DamageClass.Arts, "taken damage keeps move class");
Check(EncounterProjection.DeathRecap(fight, 5).Select(e => e.Sequence).SequenceEqual([4, 5]), "death recap");
var longFight = fight with { Events = Enumerable.Range(1, 25)
    .Select(sequence => fight.Events[0] with { Sequence = sequence }).Reverse().ToArray() };
Check(EncounterProjection.FullTimeline(longFight).Select(e => e.Sequence)
    .SequenceEqual(Enumerable.Range(1, 25).Select(value => (long)value)),
    "full combat log includes ordered results beyond twenty");
var hpCost = new CombatEvent(3, fight.StartedAt, null, null, "joshua", null,
    "HP loss (source unverified)", CombatEventKind.HpLoss, 20, 100, 80);
var costThenKnockout = fight with { Events = [hpCost, fight.Events[3], fight.Events[4]] };
Check(EncounterProjection.Rows(costThenKnockout, MeterMode.PlayerTaken).Single().Value == 80,
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

// Live Agate HP observation is deliberately partial: the attacker remains unknown.
var researchPath = Path.Combine(AppContext.BaseDirectory, "samples", "research",
    "command-result-20260926.partial.json");
var research = EncounterReplay.Load(researchPath).Single();
Check(!research.IsComplete && research.Outcome == EncounterOutcome.Victory,
    "live research replay remains partial despite reported victory");
Check(research.Events.Count == 4, "four observed in-battle HP changes");
Check(EncounterProjection.Rows(research, MeterMode.PlayerTaken).Single().Value == 1408,
    "observed Agate HP losses reconcile to taken meter");
Check(EncounterProjection.Rows(research, MeterMode.Healing).Single().Value == 304,
    "observed Agate HP gain reconciles to healing meter");
Check(EncounterProjection.Rows(research, MeterMode.PlayerDamage).Count == 0 &&
      EncounterProjection.Rows(research, MeterMode.EnemyDamage).Count == 0 &&
      EncounterProjection.Attackers(research, MeterMode.PlayerTaken, "observed-agate")
          .Single().Key == "unknown",
    "unknown damage source stays visible under its victim without a guessed team");

var fullHpPath = Path.Combine(AppContext.BaseDirectory, "samples", "research",
    "full-hp-path-20260926.partial.json");
var fullHpResearch = EncounterReplay.Load(fullHpPath).Single();
Check(!fullHpResearch.IsComplete && fullHpResearch.Events.Count == 18,
    "all-actor HP research replay stays partial");
Check(EncounterProjection.Rows(fullHpResearch, MeterMode.PlayerDamage).Count == 0 &&
      EncounterProjection.Rows(fullHpResearch, MeterMode.EnemyDamage).Count == 0 &&
      EncounterProjection.Rows(fullHpResearch, MeterMode.EnemyTaken).Sum(row => row.Value) == 57680,
    "unknown-source enemy HP losses remain under enemy victims");
Check(EncounterProjection.Rows(fullHpResearch, MeterMode.PlayerTaken).Sum(row => row.Value) == 2113,
    "observed party HP losses reconcile to taken meter");
Check(EncounterProjection.Rows(fullHpResearch, MeterMode.Healing).Single().Value == 1043,
    "observed party HP gains reconcile to healing meter");

var attributedPath = Path.Combine(AppContext.BaseDirectory, "samples", "research",
    "attributed-attack-20260926.partial.json");
var attributed = EncounterReplay.Load(attributedPath).Single();
var attributedRows = EncounterProjection.Rows(attributed, MeterMode.PlayerDamage)
    .ToDictionary(row => row.Name, row => row.Value);
Check(!attributed.IsComplete && attributed.Events.Count == 13,
    "attributed live attack path remains partial");
Check(attributedRows["Estelle"] == 32535 && attributedRows["Agate"] == 20284 &&
      attributedRows["Scherazard"] == 4991 && attributedRows["Tita"] == 2076,
    "observed live damage reconciles by character");
Check(attributedRows.Values.Sum() == 59886,
    "effective damage equals two observed enemy HP pools");
var estelleId = attributed.Actors.Single(actor => actor.Name == "Estelle").Id;
var estelleResults = EncounterProjection.ResultsForRow(attributed, MeterMode.PlayerDamage, estelleId);
Check(estelleResults.Count > 1 && estelleResults.Sum(effect => effect.EffectiveAmount ?? 0) == attributedRows["Estelle"] &&
      estelleResults.Zip(estelleResults.Skip(1)).All(pair => pair.First.Sequence < pair.Second.Sequence),
    "unknown live moves remain distinct ordered results and reconcile to Estelle's meter row");
Check(EncounterProjection.Moves(attributed, MeterMode.PlayerDamage, estelleId)
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
var actionRows = EncounterProjection.Rows(actionProbe, MeterMode.PlayerDamage)
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
Check(EncounterProjection.Rows(unknownFight, MeterMode.PlayerDamage).Count == 0 &&
      EncounterProjection.Rows(unknownFight, MeterMode.EnemyDamage).Count == 0,
    "unknown source is not assigned to a damage-dealt team");
Check(EncounterProjection.MoveGroups(unknownFight, MeterMode.EnemyTaken, "wolf-1", "unknown")
    .Single().Value == 100, "unknown-source move breakdown reconciles under victim");
Check(EncounterProjection.Attackers(unknownFight, MeterMode.EnemyTaken, "wolf-1")
    .Single().Key == "unknown", "enemy victim retains unknown attacker");
var sharedVictim = fight with { Events = [fight.Events[3],
    fight.Events[2] with { Sequence = 10, TargetId = "joshua", EffectiveAmount = 20 }] };
var joshuaAttackers = EncounterProjection.Attackers(sharedVictim, MeterMode.PlayerTaken, "joshua")
    .ToDictionary(row => row.Key);
Check(joshuaAttackers["wolf-2"].Value == 80 && joshuaAttackers["wolf-1"].Value == 20 &&
      EncounterProjection.ResultsForRow(sharedVictim, MeterMode.PlayerTaken, "joshua", "wolf-1")
          .Single().EffectiveAmount == 20,
    "player victim drills into individual attackers without mixing their moves");
var groupedFight = fight with { Events = [
    fight.Events[0] with { Sequence = 21, MoveName = "Shatter Break", EffectiveAmount = 100 },
    fight.Events[0] with { Sequence = 22, MoveName = "Shatter Break", EffectiveAmount = 80 },
    fight.Events[0] with { Sequence = 23, MoveName = null, EffectiveAmount = 30 },
    fight.Events[0] with { Sequence = 24, MoveName = null, EffectiveAmount = 20 }
] };
var drillGroups = EncounterProjection.MoveGroups(groupedFight, MeterMode.PlayerDamage, fight.Events[0].SourceId!);
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
Check(finished.IsComplete && EncounterProjection.Rows(finished, MeterMode.PlayerDamage).Single().Value == 100,
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
    store.Save(balmFight with { Events = [balmFight.Events.Single() with {
        MoveLookupReason = "hp-write-without-attack-result" }] });
    Check(store.LoadAll().Single(e => e.Id == "balm-check").Events.Single().ResolvedAmount == 1500,
        "resolved amount survives storage");
    Check(store.LoadAll().Single(e => e.Id == "balm-check").Events.Single().MoveLookupReason ==
        "hp-write-without-attack-result", "lookup reason survives storage");
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
    var healthyCount = store.LoadAll().Count;
    File.WriteAllText(Path.Combine(directory, "corrupt.json"), "{broken");
    File.WriteAllText(Path.Combine(directory, "wrong-filename.json"), "{\"id\":\"wrong-id\",\"actors\":[],\"events\":[]}");
    Check(store.LoadAll().Count == healthyCount && store.LoadIssues.Count == 2,
        "corrupt history files preserve healthy encounters and produce visible diagnostics");
    Check(File.Exists(Path.Combine(directory, "corrupt.json")), "bad history evidence remains intact");
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
