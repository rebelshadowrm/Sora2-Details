using System.Text.Json;
using System.Text.Json.Serialization;

namespace Sora2.Details.Core;

/// <summary>One UTF-8 JSON object per line on the local capture pipe.</summary>
public static class CaptureMessageCodec
{
    private static readonly JsonSerializerOptions Options = new(JsonSerializerDefaults.Web)
    {
        Converters = { new JsonStringEnumConverter() }
    };

    public static string Serialize(CaptureMessage message) => message switch
    {
        EncounterStarted value => Pack("start", value),
        EffectObserved value => Pack("effect", value),
        EncounterEnded value => Pack("end", value),
        CaptureGap value => Pack("gap", value),
        CaptureSourceInterrupted value => Pack("interrupted", value),
        _ => throw new ArgumentException("Unsupported capture message.", nameof(message))
    };

    public static string SerializeHello(CaptureHello hello) => Pack("hello", hello);

    public static CaptureHello DeserializeHello(string line)
    {
        using var document = JsonDocument.Parse(line);
        if (document.RootElement.GetProperty("type").GetString() != "hello")
            throw new InvalidDataException("Capture connection must begin with a hello message.");
        return document.RootElement.GetProperty("message").Deserialize<CaptureHello>(Options)
            ?? throw new InvalidDataException("Empty capture hello message.");
    }

    public static CaptureMessage Deserialize(string line)
    {
        using var document = JsonDocument.Parse(line);
        var root = document.RootElement;
        var type = root.GetProperty("type").GetString();
        var payload = root.GetProperty("message");
        return type switch
        {
            "start" => Read<EncounterStarted>(payload),
            "effect" => Read<EffectObserved>(payload),
            "end" => Read<EncounterEnded>(payload),
            "gap" => Read<CaptureGap>(payload),
            "interrupted" => Read<CaptureSourceInterrupted>(payload),
            _ => throw new InvalidDataException($"Unknown capture message type: {type}")
        };
    }

    private static string Pack<T>(string type, T message) =>
        JsonSerializer.Serialize(new { type, message }, Options);

    private static T Read<T>(JsonElement payload) where T : CaptureMessage =>
        payload.Deserialize<T>(Options) ?? throw new InvalidDataException("Empty capture message.");
}
