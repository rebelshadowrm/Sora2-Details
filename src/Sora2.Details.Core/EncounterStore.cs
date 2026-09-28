using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Sora2.Details.Core;

/// <summary>Durable, one-file-per-encounter history. Each update replaces one snapshot atomically.</summary>
public sealed class EncounterStore(string directory)
{
    private static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() },
        WriteIndented = true
    };

    public void Save(Encounter encounter)
    {
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
        if (!Directory.Exists(directory)) return [];
        var encounters = new List<Encounter>();
        foreach (var path in Directory.EnumerateFiles(directory, "*.json"))
        {
            using var stream = new FileStream(path, FileMode.Open, FileAccess.Read,
                FileShare.ReadWrite | FileShare.Delete);
            var encounter = JsonSerializer.Deserialize<Encounter>(stream, Options)
                ?? throw new InvalidDataException($"Empty encounter file: {path}");
            if (PathFor(encounter.Id) != path)
                throw new InvalidDataException($"Encounter ID does not match filename: {path}");
            encounters.Add(encounter);
        }
        return encounters.OrderByDescending(item => item.StartedAt).ToArray();
    }

    private string PathFor(string id)
    {
        if (string.IsNullOrWhiteSpace(id)) throw new ArgumentException("Encounter ID is required.", nameof(id));
        var hash = Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(id)));
        return Path.Combine(directory, hash + ".json");
    }
}
