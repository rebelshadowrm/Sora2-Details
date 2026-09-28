using System.IO;

namespace Sora2.Details.Desktop;

internal static class MeterDataDirectory
{
    public static string PathName => Environment.GetEnvironmentVariable("SORA2_DETAILS_DATA_DIR")
        ?? Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "Sora2 Details");
}
