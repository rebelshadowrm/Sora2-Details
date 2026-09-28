using System.IO.Pipes;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;

namespace Sora2.Details.Core;

/// <summary>Local transport for a future, separately verified game capture adapter.</summary>
public sealed class CapturePipeSource(
    string pipeName = CapturePipeSource.DefaultPipeName,
    bool allowFixture = false) : ICombatCaptureSource
{
    public const string DefaultPipeName = "sora2-details-capture-v1";
    public const int ProtocolVersion = 1;
    public const string SupportedExecutableSha256 = "D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF";
    private const int MaximumLineLength = 1024 * 1024;

    public CaptureCapabilities Capabilities { get; private set; } = new(false, false, false, false, false);

    public async IAsyncEnumerable<CaptureMessage> ReadAsync(
        [EnumeratorCancellation] CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            await using var pipe = new NamedPipeServerStream(pipeName, PipeDirection.In, 1,
                PipeTransmissionMode.Byte, PipeOptions.Asynchronous);
            await pipe.WaitForConnectionAsync(cancellationToken);
            using var reader = new StreamReader(pipe, new UTF8Encoding(false, true),
                detectEncodingFromByteOrderMarks: false, leaveOpen: true);
            var helloLine = await reader.ReadLineAsync(cancellationToken)
                ?? throw new InvalidDataException("Capture client disconnected before hello.");
            if (helloLine.Length > MaximumLineLength)
                throw new InvalidDataException("Capture hello exceeds the 1 MiB limit.");
            var hello = CaptureMessageCodec.DeserializeHello(helloLine);
            if (hello.ProtocolVersion != ProtocolVersion)
                throw new InvalidDataException($"Unsupported capture protocol version {hello.ProtocolVersion}.");
            if (!Enum.IsDefined(hello.Origin) || hello.Capabilities is null)
                throw new InvalidDataException("Invalid capture hello message.");
            if (hello.Origin == CaptureOrigin.Fixture && !allowFixture)
                throw new InvalidDataException("Fixture capture is disabled in the desktop receiver.");
            if (hello.Origin == CaptureOrigin.Game &&
                !string.Equals(hello.ExecutableSha256, SupportedExecutableSha256, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Unsupported game executable build; capture stopped.");
            Capabilities = hello.Capabilities;
            string? line;
            while ((line = await reader.ReadLineAsync(cancellationToken)) is not null)
            {
                if (line.Length > MaximumLineLength)
                    throw new InvalidDataException("Capture message exceeds the 1 MiB limit.");
                CaptureMessage message;
                try { message = CaptureMessageCodec.Deserialize(line); }
                catch (JsonException exception)
                {
                    throw new InvalidDataException("Malformed capture message.", exception);
                }
                yield return message;
            }
            yield return new CaptureSourceInterrupted("Capture client disconnected.");
            Capabilities = new(false, false, false, false, false);
        }
    }
}
