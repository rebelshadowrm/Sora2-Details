using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Sora2.Details.Core;

/// <summary>Durable, one-file-per-encounter history. Each update replaces one snapshot atomically.</summary>
public sealed class EncounterStore(string directory)
{
    public IReadOnlyList<string> LoadIssues { get; private set; } = [];
    private static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() },
        WriteIndented = true
    };

    public void Save(Encounter encounter)
    {
        Validate(encounter);
        Directory.CreateDirectory(directory);
        var path = PathFor(encounter.Id);
        var temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
        try
        {
            using (var stream = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            {
                JsonSerializer.Serialize(stream, encounter, Options);
                stream.Flush(flushToDisk: true);
            }
            // Windows can briefly deny replacement while a reader or scanner has the
            // previous snapshot open. Keep the source file until replacement succeeds.
            for (var attempt = 0; ; attempt++)
            {
                try
                {
                    File.Move(temporary, path, overwrite: true);
                    break;
                }
                catch (Exception exception) when (attempt < 4 &&
                    exception is IOException or UnauthorizedAccessException)
                {
                    Thread.Sleep(25 * (attempt + 1));
                }
            }
        }
        finally
        {
            if (File.Exists(temporary)) File.Delete(temporary);
        }
    }

    public IReadOnlyList<Encounter> LoadAll()
    {
        LoadIssues = [];
        if (!Directory.Exists(directory)) return [];
        var encounters = new List<Encounter>();
        var issues = new List<string>();
        foreach (var path in Directory.EnumerateFiles(directory, "*.json"))
        {
            try
            {
                using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete);
                var encounter = JsonSerializer.Deserialize<Encounter>(stream, Options)
                    ?? throw new InvalidDataException("Empty encounter file.");
                Validate(encounter);
                if (!string.Equals(PathFor(encounter.Id), path, StringComparison.OrdinalIgnoreCase))
                    throw new InvalidDataException("Encounter ID does not match filename.");
                encounters.Add(encounter);
            }
            catch (Exception exception) when (exception is IOException or UnauthorizedAccessException or
                                              JsonException or InvalidDataException)
            {
                issues.Add($"History file {Path.GetFileName(path)} could not be loaded: {exception.Message}");
            }
        }
        LoadIssues = issues;
        return encounters.OrderByDescending(item => item.StartedAt).ToArray();
    }

    private static void Validate(Encounter encounter)
    {
        if (string.IsNullOrWhiteSpace(encounter.Id) || encounter.Actors is null || encounter.Events is null)
            throw new InvalidDataException("Encounter identity, actors, or events are missing.");
        if (encounter.SchemaVersion is < 1 or > 2)
            throw new InvalidDataException($"Unsupported encounter schema {encounter.SchemaVersion}.");
        if (encounter.Actors.Any(actor => actor is null || string.IsNullOrWhiteSpace(actor.Id)) ||
            encounter.Actors.Select(actor => actor.Id).Distinct(StringComparer.Ordinal).Count() != encounter.Actors.Count)
            throw new InvalidDataException("Actor identities must be unique and nonempty.");
        if (encounter.Events.Any(effect => effect is null || string.IsNullOrWhiteSpace(effect.TargetId)) ||
            encounter.Events.Select(effect => effect.Sequence).Distinct().Count() != encounter.Events.Count)
            throw new InvalidDataException("Event targets must be present and sequences unique.");
    }

    private string PathFor(string id)
    {
        if (string.IsNullOrWhiteSpace(id)) throw new ArgumentException("Encounter ID is required.", nameof(id));
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(id)));
        return Path.Combine(directory, hash + ".json");
    }
}
