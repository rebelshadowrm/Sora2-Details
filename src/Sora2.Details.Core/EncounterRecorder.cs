namespace Sora2.Details.Core;

/// <summary>Consumes a capture stream and durably publishes each changed snapshot.</summary>
public sealed class EncounterRecorder(EncounterStore store)
{
    private readonly EncounterAssembler _assembler = new();
    private readonly HashSet<string> _persistedIds = store.LoadAll()
        .Select(encounter => encounter.Id).ToHashSet(StringComparer.Ordinal);

    public event Action<Encounter>? EncounterChanged;

    public async Task RunAsync(ICombatCaptureSource source, CancellationToken cancellationToken)
    {
        try
        {
            await foreach (var message in source.ReadAsync(cancellationToken))
            {
                if (message is EncounterStarted start && _persistedIds.Contains(start.EncounterId))
                    throw new InvalidDataException($"Encounter ID already exists in history: {start.EncounterId}");
                Publish(_assembler.Accept(message));
            }
        }
        finally
        {
            Publish(_assembler.InterruptOpen("Capture source stopped before encounter end."));
        }
    }

    private void Publish(IReadOnlyList<Encounter> encounters)
    {
        foreach (var encounter in encounters)
        {
            store.Save(encounter);
            EncounterChanged?.Invoke(encounter);
        }
    }
}
