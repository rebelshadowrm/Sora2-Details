# Sora 2 Details 0.1.0 preview

This Windows preview provides a compact meter and durable **partial** command-battle combat log. It records observed HP changes and some attributed damaging hits; support actions, misses, some move names, and critical status remain incomplete. It is not yet a complete combat log.

Unzip the release to a writable folder. Start the game, then double-click `Start-Sora2Details.cmd`. The launcher opens the meter and starts a 12-hour read-only capture after one Windows administrator prompt. Start it before entering a command battle. Double-click `Stop-Sora2Details.cmd` to detach the capture cleanly; closing the meter window does not itself detach the probe. With the game closed, the Start command opens saved encounters without capture. `Start-Sora2Details.cmd -MeterOnly` does the same while the game is running.

The meter is a self-contained Windows x64 app. Live capture needs **64-bit Python 3.11 or newer** on `PATH`, or `C:\Python313\python.exe`. The default supported game location is `C:\Games\Trails in the Sky 2nd Chapter`; pass `-GameDirectory` to the PowerShell launcher for another location. Capture refuses an unverified executable hash. Recorded encounters are stored under `%LOCALAPPDATA%\Sora2 Details\encounters`; raw probe traces are under `.research-deps\live` beside this launcher.

The meter stays on top of the game. Clicking it gives it keyboard focus; click the game to return control. Its startup no longer activates the window over the game. If game input behaves unexpectedly, use Stop and wait for the probe to detach before continuing.
