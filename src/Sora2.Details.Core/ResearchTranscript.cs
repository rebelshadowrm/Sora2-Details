using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Sora2.Details.Core;

public sealed record ResearchTranscriptAction(string Id, string ObservationId, string? ActorPointer,
    string? MoveNameCandidate, string? RawMoveId, string Stage, int EffectObservationCount,
    string? ActorNameCandidate = null, string? Targets = null, string? IntervalId = null);

public sealed record ResearchTranscriptEntry(string Id, long? Sequence, DateTimeOffset? At,
    string Kind, string? Hook, string? ActionCandidateId, JsonElement Raw, string? IntervalId = null,
    string? SourceCandidate = null, string? MoveCandidate = null, string? TargetCandidate = null,
    string? ConditionsCandidate = null, string? ConditionChangeCandidate = null);

public sealed record ResearchTranscriptInterval(string Id, DateTimeOffset? StartedAt,
    DateTimeOffset? EndedAt, string Scope, string? RawInitializerFlags, int? RawExitArgument,
    string? OutcomeCandidate = null);

/// <summary>A durable research stream, kept separate from verified encounter history.</summary>
public sealed record ResearchTranscript(string BatchId, string SourcePath, string SourceSha256,
    IReadOnlyList<ResearchTranscriptAction> Actions, IReadOnlyList<ResearchTranscriptEntry> Entries,
    IReadOnlyList<string> CoverageGaps, bool SourceVerified)
{
    public IReadOnlyList<ResearchTranscriptInterval> Intervals { get; init; } = [];

    public static ResearchTranscript Load(string path)
    {
        using var ledgerStream = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
        using var ledgerReader = new StreamReader(ledgerStream);
        using var document = JsonDocument.Parse(ledgerReader.ReadToEnd());
        var root = document.RootElement;
        if (root.GetProperty("schemaVersion").GetInt32() != 1 ||
            root.GetProperty("origin").GetString() != "RawResearchLedger" ||
            root.GetProperty("completeActionStream").GetBoolean())
            throw new InvalidDataException("Expected a partial raw research ledger, schema 1.");
        var batch = Required(root, "batchId");
        var sourcePath = Required(root, "tracePath");
        var hash = Required(root, "traceSha256");
        if (hash.Length != 64 || !hash.All(Uri.IsHexDigit))
            throw new InvalidDataException("Missing or invalid raw source hash.");
        var timeline = root.GetProperty("actionTimeline");
        if (timeline.GetProperty("completeActionStream").GetBoolean())
            throw new InvalidDataException("Research timeline cannot claim complete coverage.");
        var actions = timeline.GetProperty("actionCandidates").EnumerateArray().Select(a =>
            new ResearchTranscriptAction(Required(a, "actionCandidateId"), Required(a, "observationId"),
                Optional(a, "actorPointer"), Optional(a.GetProperty("descriptor"), "nameCandidate") ??
                    (a.TryGetProperty("animationLookupCandidate", out var animation) &&
                     Optional(animation, "nameCandidate") is { } animationName ? $"{animationName} (animation candidate)" : null),
                Optional(a.GetProperty("descriptor"), "rawPackedId"), Required(a, "stage"),
                a.GetProperty("effectObservationIds").GetArrayLength(), Optional(a, "actorNameCandidate"),
                a.TryGetProperty("targetCandidates", out var targets) ? string.Join(", ", targets.EnumerateArray()
                    .Select(t => Optional(t, "nameCandidate") ?? $"Status #{t.GetProperty("rawStatusId").GetInt32()}")) : null)).ToArray();
        if (actions.Select(a => a.Id).Distinct(StringComparer.Ordinal).Count() != actions.Length)
            throw new InvalidDataException("Duplicate action candidate identity.");
        var actionIds = actions.Select(a => a.Id).ToHashSet(StringComparer.Ordinal);
        var raw = root.GetProperty("observations").EnumerateArray().ToArray();
        var rows = timeline.GetProperty("timeline").EnumerateArray().ToArray();
        if (raw.Length != rows.Length)
            throw new InvalidDataException("Timeline dropped raw observations.");
        var entries = new List<ResearchTranscriptEntry>(raw.Length);
        var ids = new HashSet<string>(StringComparer.Ordinal);
        for (var i = 0; i < rows.Length; i++)
        {
            var row = rows[i];
            var id = Required(row, "observationId");
            if (!ids.Add(id) || id != Required(raw[i], "observationId"))
                throw new InvalidDataException("Timeline reordered or duplicated observations.");
            var action = Optional(row, "actionCandidateId");
            if (action is not null && !actionIds.Contains(action))
                throw new InvalidDataException("Unknown action candidate reference.");
            var value = raw[i].GetProperty("raw");
            long? sequence = value.TryGetProperty("observation_sequence", out var seq) && seq.TryGetInt64(out var n) ? n : null;
            var at = DateTimeOffset.TryParse(Optional(value, "at"), out var time) ? time : (DateTimeOffset?)null;
            string? sourceCandidate = null, moveCandidate = null, targetCandidate = null;
            if (raw[i].TryGetProperty("effectIdentityCandidates", out var effect) ||
                raw[i].TryGetProperty("conditionIdentityCandidates", out effect))
            {
                sourceCandidate = StatusLabel(effect.GetProperty("sourceContextStatus"));
                targetCandidate = StatusLabel(effect.GetProperty("targetContextStatus"));
                var descriptor = effect.GetProperty("descriptor");
                moveCandidate = Optional(descriptor, "nameCandidate") ?? Optional(descriptor, "rawPackedId");
            }
            string? conditionsCandidate = null;
            string? changeCandidate = null;
            if (raw[i].TryGetProperty("conditionSnapshot", out var conditions))
                conditionsCandidate = string.Join(", ", conditions.GetProperty("records").EnumerateArray().Select(c =>
                    Optional(c, "nameCandidate") is { } name ? $"{name} (candidate)" : $"Condition #{c.GetProperty("rawKey").GetUInt32()}"));
            if (raw[i].TryGetProperty("conditionTransitionCandidate", out var transition) && transition.ValueKind == JsonValueKind.Object)
                changeCandidate = $"Condition #{transition.GetProperty("rawKey").GetUInt32()}: {Optional(transition, "changeCandidate")} (candidate)";
            if (raw[i].TryGetProperty("conditionAttemptCandidate", out var attempt) && attempt.ValueKind == JsonValueKind.Object)
            {
                var identity = Optional(attempt, "nameCandidate") ?? $"Condition #{attempt.GetProperty("rawKey").GetUInt32()}";
                changeCandidate = $"{identity}: native return {Optional(attempt, "nativeReturnPointerRaw") ?? "0"}; cause unresolved (candidate)";
                if (attempt.TryGetProperty("rejectionContextCandidate", out var context) && context.ValueKind == JsonValueKind.Object &&
                    Optional(context, "contextCandidate") == "DebuffImmunityPresent")
                    changeCandidate = $"{identity}: native return 0; Debuff Immunity present (candidate)";
            }
            if (raw[i].TryGetProperty("conditionRemoveTargetCandidate", out var removalTarget))
                targetCandidate = StatusLabel(removalTarget);
            if (raw[i].TryGetProperty("conditionRemovalCandidate", out var removal) && removal.ValueKind == JsonValueKind.Object)
            {
                var identity = Optional(removal, "nameCandidate") ?? $"Condition #{removal.GetProperty("rawKey").GetUInt32()}";
                var lifecycle = Optional(removal, "lifecycleCandidate");
                changeCandidate = lifecycle is null ? $"{identity}: removal return {removal.GetProperty("nativeReturnAlRaw")} (candidate)" :
                    $"{identity}: {lifecycle} (candidate)";
                if (lifecycle is not null && Optional(removal, "removalCauseCandidate") is { } cause)
                    changeCandidate = $"{identity}: {lifecycle} via {cause} (candidate)";
            }
            entries.Add(new(id, sequence, at, Required(row, "kind"), Optional(value, "name"), action, value.Clone(),
                Optional(row, "commandIntervalCandidateId"), sourceCandidate, moveCandidate, targetCandidate, conditionsCandidate, changeCandidate));
        }
        if (actions.Any(a => !ids.Contains(a.ObservationId)))
            throw new InvalidDataException("Action candidate has no raw observation.");
        var entryById = entries.ToDictionary(e => e.Id, StringComparer.Ordinal);
        var intervals = new List<ResearchTranscriptInterval>();
        if (root.TryGetProperty("commandIntervalCandidates", out var intervalRows))
            foreach (var interval in intervalRows.EnumerateArray())
            {
                var startId = Required(interval, "startObservationId");
                var endId = Optional(interval, "endObservationId");
                if (!entryById.TryGetValue(startId, out var start) || endId is not null && !entryById.ContainsKey(endId))
                    throw new InvalidDataException("Interval boundary has no raw observation.");
                string? flags = null;
                if (Optional(start.Raw, "mode_root_2ce0_raw") is { } rawFlags)
                {
                    try
                    {
                        var bytes = Convert.FromHexString(rawFlags);
                        if (bytes.Length >= 16) flags = $"0x{System.Buffers.Binary.BinaryPrimitives.ReadUInt32LittleEndian(bytes.AsSpan(12)):X}";
                    }
                    catch (FormatException) { }
                }
                intervals.Add(new(Required(interval, "id"), start.At, endId is null ? null : entryById[endId].At,
                    Optional(interval, "scope") ?? "UnclassifiedEngineBattle", flags,
                    interval.TryGetProperty("rawExitArgumentCandidate", out var argument) && argument.ValueKind == JsonValueKind.Number
                        && argument.TryGetInt32(out var n) ? n : null, Optional(interval, "outcomeCandidate")));
            }
        var intervalIds = intervals.Select(i => i.Id).ToHashSet(StringComparer.Ordinal);
        if (intervalIds.Count != intervals.Count || entries.Any(e => e.IntervalId is not null && !intervalIds.Contains(e.IntervalId)))
            throw new InvalidDataException("Duplicate interval identity or unknown interval reference.");
        actions = actions.Select(a => a with { IntervalId = entryById[a.ObservationId].IntervalId }).ToArray();
        var gaps = root.GetProperty("coverageGaps").EnumerateArray().Select(g => g.GetString() ?? "Unknown gap").ToList();
        var verified = false;
        if (File.Exists(sourcePath))
        {
            using var sourceStream = new FileStream(sourcePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
            var sourceLength = sourceStream.Length;
            var readLength = sourceLength;
            if (root.TryGetProperty("traceCommittedLength", out var length))
            {
                if (length.ValueKind != JsonValueKind.Number || !length.TryGetInt32(out var committed) || committed <= 0 || committed > sourceLength)
                    throw new InvalidDataException("Invalid committed raw source prefix.");
                readLength = committed;
                if (committed < sourceLength)
                    gaps.Add("Verified committed source prefix; newer observations await projection.");
            }
            if (readLength > int.MaxValue) throw new InvalidDataException("Research source snapshot exceeds the reader limit.");
            var bytes = new byte[(int)readLength];
            sourceStream.ReadExactly(bytes);
            if (root.TryGetProperty("traceCommittedLength", out _) && bytes[^1] != (byte)'\n')
                throw new InvalidDataException("Invalid committed raw source prefix.");
            if (!Convert.ToHexString(SHA256.HashData(bytes)).Equals(hash, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Raw source hash changed.");
            var lines = System.Text.Encoding.UTF8.GetString(bytes).TrimStart('\uFEFF')
                .Split('\n').Where(s => !string.IsNullOrWhiteSpace(s)).ToArray();
            if (lines.Length != entries.Count)
                throw new InvalidDataException("Embedded raw record count differs from source.");
            for (var i = 0; i < lines.Length; i++)
                if (!JsonNode.DeepEquals(JsonNode.Parse(lines[i]), JsonNode.Parse(entries[i].Raw.GetRawText())))
                    throw new InvalidDataException("Embedded raw observation differs from source.");
            verified = true;
        }
        else gaps.Add("Raw source file unavailable; embedded observations retained, source hash not independently checked.");
        return new(batch, sourcePath, hash, actions, entries, gaps, verified) { Intervals = intervals };
    }

    private static string Required(JsonElement value, string key) => Optional(value, key)
        is { Length: > 0 } text ? text : throw new InvalidDataException($"Missing {key}.");
    private static string? Optional(JsonElement value, string key) =>
        value.TryGetProperty(key, out var found) && found.ValueKind == JsonValueKind.String ? found.GetString() : null;

    private static string? StatusLabel(JsonElement status) => Optional(status, "nameCandidate") ??
        (status.TryGetProperty("rawStatusId", out var id) && id.ValueKind == JsonValueKind.Number && id.TryGetUInt32(out var n)
            ? $"Status #{n}" : null);
}
