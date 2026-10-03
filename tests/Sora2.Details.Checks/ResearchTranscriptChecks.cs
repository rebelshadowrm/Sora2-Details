using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Sora2.Details.Core;

internal static class ResearchTranscriptChecks
{
    public static void Run()
    {
        var directory = Path.Combine(Path.GetTempPath(), "sora2-transcript-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(directory);
        try
        {
            var source = Path.Combine(directory, "raw.jsonl");
            var ledgerPath = Path.Combine(directory, "ledger.json");
            var unknown = new { kind = "hit", name = "UnfamiliarFutureEvent", observation_sequence = 1,
                payload = new { rawKey = "0xDEADBEEF", values = new[] { 3, 9, 11 } } };
            File.WriteAllText(source, JsonSerializer.Serialize(unknown) + "\n", new UTF8Encoding(false));
            var ledger = JsonSerializer.SerializeToNode(new
            {
                schemaVersion = 1, origin = "RawResearchLedger", completeActionStream = false,
                batchId = "fixture", tracePath = source,
                traceSha256 = Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(source))),
                observations = new[] { new { observationId = "one", raw = unknown } },
                coverageGaps = new[] { "No verified boundaries" },
                actionTimeline = new { completeActionStream = false, actionCandidates = Array.Empty<object>(),
                    timeline = new[] { new { observationId = "one", kind = "UnknownObservation" } } }
            })!;
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            var transcript = ResearchTranscript.Load(ledgerPath);
            Require(transcript.SourceVerified && transcript.Entries.Count == 1 && transcript.Actions.Count == 0,
                "unknown observations survive with no invented actions");
            Require(transcript.Entries[0].Raw.GetProperty("payload").GetProperty("values")[2].GetInt32() == 11,
                "arbitrary payload remains readable after document disposal");
            ledger["observations"]![0]!["conditionSnapshot"] = new JsonObject
            {
                ["records"] = new JsonArray(new JsonObject { ["rawKey"] = 31, ["nameCandidate"] = "SPD UP" },
                    new JsonObject { ["rawKey"] = 9999, ["nameCandidate"] = null })
            };
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            var named = ResearchTranscript.Load(ledgerPath);
            Require(named.SourceVerified && named.Entries[0].ConditionsCandidate == "SPD UP (candidate), Condition #9999",
                "condition metadata and unknown keys display without modifying raw source");
            ledger["observations"]![0]!["conditionRemoveTargetCandidate"] = new JsonObject
            {
                ["rawStatusId"] = 5, ["nameCandidate"] = "Agate"
            };
            ledger["observations"]![0]!["conditionRemovalCandidate"] = new JsonObject
            {
                ["rawKey"] = 31, ["nativeReturnAlRaw"] = 0
            };
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            var removal = ResearchTranscript.Load(ledgerPath);
            Require(removal.SourceVerified && removal.Entries[0].TargetCandidate == "Agate" &&
                removal.Entries[0].ConditionChangeCandidate == "Condition #31: removal return 0 (candidate)",
                "failed native removal return stays visible without implying expiration");
            ledger["observations"]![0]!["conditionRemovalCandidate"]!["nameCandidate"] = "Pommify";
            ledger["observations"]![0]!["conditionRemovalCandidate"]!["lifecycleCandidate"] = "Dispelled";
            ledger["observations"]![0]!["conditionRemovalCandidate"]!["removalCauseCandidate"] = "Overdrive";
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            Require(ResearchTranscript.Load(ledgerPath).Entries[0].ConditionChangeCandidate ==
                "Pommify: Dispelled via Overdrive (candidate)", "native removal cause displays with its evidence classification");
            ledger["observations"]![0]!.AsObject().Remove("conditionRemovalCandidate");
            ledger["observations"]![0]!["conditionAttemptCandidate"] = new JsonObject
            {
                ["rawKey"] = 55, ["nativeReturnPointerRaw"] = null, ["nativeReturnEaxRaw"] = 0
            };
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            var attempt = ResearchTranscript.Load(ledgerPath);
            Require(attempt.SourceVerified && attempt.Entries[0].ConditionChangeCandidate ==
                "Condition #55: native return 0; cause unresolved (candidate)",
                "null condition return remains visible without asserting immunity");
            ledger["observations"]![0]!["conditionAttemptCandidate"]!["nameCandidate"] = "Pommify";
            ledger["observations"]![0]!["conditionAttemptCandidate"]!["rejectionContextCandidate"] = new JsonObject
            {
                ["contextCandidate"] = "DebuffImmunityPresent", ["reflectArtsActiveCandidate"] = false
            };
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            var protectedAttempt = ResearchTranscript.Load(ledgerPath);
            Require(protectedAttempt.SourceVerified && protectedAttempt.Entries[0].ConditionChangeCandidate ==
                "Pommify: native return 0; Debuff Immunity present (candidate)",
                "protective context displays separately from a proved rejection cause");
            ledger["commandIntervalCandidates"] = new JsonArray(new JsonObject
            {
                ["id"] = "interval", ["startObservationId"] = "one", ["scope"] = "UnclassifiedEngineBattle",
                ["endObservationId"] = null, ["rawExitArgumentCandidate"] = null
            });
            ledger["actionTimeline"]!["timeline"]![0]!["commandIntervalCandidateId"] = "interval";
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            var framed = ResearchTranscript.Load(ledgerPath);
            Require(framed.Intervals.Count == 1 && framed.Entries[0].IntervalId == "interval" && framed.Intervals[0].RawExitArgument is null,
                "open unclassified interval keeps unknown outcome and observation association");
            ledger["actionTimeline"]!["timeline"]![0]!["commandIntervalCandidateId"] = "missing";
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            Reject(() => ResearchTranscript.Load(ledgerPath), "unknown interval references rejected");
            ledger.AsObject().Remove("commandIntervalCandidates");
            ledger["actionTimeline"]!["timeline"]![0]!.AsObject().Remove("commandIntervalCandidateId");
            ledger["observations"]![0]!["raw"]!["payload"]!["rawKey"] = "tampered";
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            Reject(() => ResearchTranscript.Load(ledgerPath), "tampered embedded raw data rejected");
            ledger["observations"]![0]!["raw"]!["payload"]!["rawKey"] = "0xDEADBEEF";
            ledger["actionTimeline"]!["timeline"]![0]!["observationId"] = "wrong";
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            Reject(() => ResearchTranscript.Load(ledgerPath), "reordered raw references rejected");
            ledger["actionTimeline"]!["timeline"]![0]!["observationId"] = "one";
            ledger["traceCommittedLength"] = new FileInfo(source).Length;
            File.AppendAllText(source, "{\"kind\":\"next-observation\"}\n");
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            var prefix = ResearchTranscript.Load(ledgerPath);
            Require(prefix.SourceVerified && prefix.Entries.Count == 1 && prefix.CoverageGaps.Count == 2,
                "committed prefix remains verifiable while capture appends");
            using (var activeWriter = new FileStream(source, FileMode.Append, FileAccess.Write, FileShare.Read))
            {
                var livePrefix = ResearchTranscript.Load(ledgerPath);
                Require(livePrefix.SourceVerified && livePrefix.Entries.Count == 1,
                    "source prefix verifies while the capture writer holds the file open");
            }
            ledger["traceCommittedLength"] = new FileInfo(source).Length - 1;
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            Reject(() => ResearchTranscript.Load(ledgerPath), "incomplete committed line rejected");
            ledger.AsObject().Remove("traceCommittedLength");
            File.WriteAllText(ledgerPath, ledger.ToJsonString());
            File.Delete(source);
            var portable = ResearchTranscript.Load(ledgerPath);
            Require(!portable.SourceVerified && portable.Entries.Count == 1 && portable.CoverageGaps.Count == 2,
                "portable embedded observations survive missing companion with explicit gap");
            if (Environment.GetEnvironmentVariable("SORA2_DETAILS_TRANSCRIPT_CHECK_PATH") is { Length: > 0 } real)
            {
                var saved = ResearchTranscript.Load(real);
                Require(saved.SourceVerified && saved.Entries.Count > 0,
                    "saved batch loads with independently verified raw source");
                if (saved.BatchId.EndsWith("015c4a4e82414a8dae169f8e841d3395", StringComparison.Ordinal))
                    Require(saved.Actions.Count == 25 && saved.Entries.Count == 1394,
                        "saved Stages batch retains expected observation count");
                if (saved.BatchId.EndsWith("c96528cbd8894c4a848b8de92d73b9e7", StringComparison.Ordinal))
                    Require(saved.Entries.Count == 679 && saved.Entries.Any(e => e.SourceCandidate == "Estelle" &&
                        e.TargetCandidate == "Agate" && e.MoveCandidate == "Forte" &&
                        e.ConditionChangeCandidate == "Condition #27: PayloadUpdated (candidate)"),
                        "saved repeated Forte transition reaches core with source, target, and raw count intact");
                if (saved.BatchId.EndsWith("53a210c438994ec5901f9cb3e6436993", StringComparison.Ordinal))
                    Require(saved.Entries.Count == 457 && saved.Entries.Any(e => e.TargetCandidate == "Agate" &&
                        e.ConditionChangeCandidate == "STR UP: Expired (candidate)") &&
                        saved.Entries.Any(e => e.TargetCandidate == "Estelle" && e.ConditionChangeCandidate == "STR UP: BulkClear (candidate)"),
                        "saved removal batch keeps Agate expiry separate from later bulk clearing");
                if (saved.BatchId.EndsWith("5e1f55e98ab34a38831dd07cf0b32a1c", StringComparison.Ordinal))
                {
                    var cast = saved.Actions.Single(a => a.RawMoveId == "0xEA8C0406");
                    Require(saved.Entries.Count == 1092 && cast.MoveNameCandidate == "Diamond Dust (animation candidate)" &&
                        cast.EffectObservationCount == 15 && cast.Targets == "Estelle, Agate, Kevin",
                        "enemy cast preserves generated ID, animation-only name provenance, and all three effect targets");
                }
            }
        }
        finally { Directory.Delete(directory, recursive: true); }
    }

    private static void Require(bool condition, string message)
    {
        if (!condition) throw new InvalidOperationException(message);
    }

    private static void Reject(Action read, string message)
    {
        try { read(); }
        catch (InvalidDataException) { return; }
        throw new InvalidOperationException(message);
    }
}
