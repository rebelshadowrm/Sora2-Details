using System.Text.Json;
using System.Text.Json.Serialization;

namespace Sora2.Details.Core;

public static class EncounterReplay
{
    private static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() }
    };

    public static IReadOnlyList<Encounter> Load(string path)
    {
        using var stream = File.OpenRead(path);
        var encounters = JsonSerializer.Deserialize<List<Encounter>>(stream, Options)
            ?? throw new InvalidDataException("Replay contains no encounters.");
        foreach (var encounter in encounters)
        {
            if (string.IsNullOrWhiteSpace(encounter.Id) || encounter.Actors is null || encounter.Events is null)
                throw new InvalidDataException("Replay has an incomplete encounter.");
            if (encounter.Events.Select(effect => effect.Sequence).Distinct().Count() != encounter.Events.Count)
                throw new InvalidDataException($"Encounter {encounter.Id} repeats an event sequence.");
        }
        return encounters;
    }
}
