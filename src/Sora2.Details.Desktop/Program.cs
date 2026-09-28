using Velopack;

namespace Sora2.Details.Desktop;

internal static class Program
{
    [STAThread]
    private static void Main(string[] args)
    {
        VelopackApp.Build().SetAutoApplyOnStartup(false).Run();
        var app = new App();
        app.Run();
    }
}
