namespace Sora2.Details.Core;

public enum CombatTeam { Party, Enemy, Other }
public enum CombatEventKind { Damage, Healing, Knockout, Revival, Status, Unknown, HpLoss }
public enum DamageClass { Unknown, Physical, Arts, Other }
public enum MeterMode { Damage, Healing, Taken, Deaths }
public enum EncounterOutcome { InProgress, Victory, Escape, Defeat, Interrupted, Unknown }

public sealed record Actor(string Id, string Name, CombatTeam Team,
    string? NameProvenance = null, int? RuntimeStatusId = null, string? LookupUnitId = null);

// A result is one resolved effect on one target, not one animation frame.
// A nullable amount or HP value means that the capture source did not observe it.
public sealed record CombatEvent(
    long Sequence,
    DateTimeOffset ObservedAt,
    string? ActionId,
    string? SourceId,
    string TargetId,
    string? MoveId,
    string? MoveName,
    CombatEventKind Kind,
    int? EffectiveAmount,
    int? HpBefore,
    int? HpAfter,
    DamageClass DamageClass = DamageClass.Unknown,
    int? ResolvedAmount = null,
    int? RawResultFlags = null,
    bool? IsCritical = null,
    string? DamageClassProvenance = null,
    string? RawEffectId = null,
    int? RawEffectCode = null,
    int? RawSourceContextFlags = null,
    int? RawTargetStatus7C = null);

public sealed record Encounter(
    string Id,
    string Label,
    DateTimeOffset StartedAt,
    EncounterOutcome Outcome,
    bool IsComplete,
    IReadOnlyList<Actor> Actors,
    IReadOnlyList<CombatEvent> Events,
    IReadOnlyList<string>? Issues = null);

public sealed record MeterRow(string Key, string Name, int Value, double Share);

public sealed record MoveRow(string Name, int Value, DamageClass DamageClass);
public sealed record MoveGroup(string Key, string Name, int Value, DamageClass DamageClass,
    IReadOnlyList<CombatEvent> Hits);

public sealed record CaptureCapabilities(
    bool SourceIdentity,
    bool MoveIdentity,
    bool EffectiveHpChange,
    bool DamageClass,
    bool EncounterBoundary);

public enum CaptureOrigin { Game, Fixture }

public sealed record CaptureHello(
    int ProtocolVersion,
    CaptureOrigin Origin,
    string? ExecutableSha256,
    CaptureCapabilities Capabilities);

// A game adapter emits observed lifecycle and result messages through this seam.
public abstract record CaptureMessage;
public sealed record EncounterStarted(string EncounterId, DateTimeOffset At, IReadOnlyList<Actor> Actors) : CaptureMessage;
public sealed record EffectObserved(string EncounterId, CombatEvent Effect) : CaptureMessage;
public sealed record EncounterEnded(string EncounterId, DateTimeOffset At, EncounterOutcome Outcome) : CaptureMessage;
public sealed record CaptureGap(string EncounterId, string Reason) : CaptureMessage;
public sealed record CaptureSourceInterrupted(string Reason) : CaptureMessage;

public interface ICombatCaptureSource
{
    CaptureCapabilities Capabilities { get; }
    IAsyncEnumerable<CaptureMessage> ReadAsync(CancellationToken cancellationToken);
}
