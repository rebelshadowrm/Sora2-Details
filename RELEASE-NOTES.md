# Sora 2 Details 0.2.0 preview 7

This Windows preview provides a compact meter and durable **partial** command-battle combat log. It records observed HP changes and some attributed damaging hits; support actions, misses, some move names, and critical status remain incomplete. It is not yet a complete combat log.

Install once from `Sora2.Details-win-x64-preview-Setup.exe`, then open Sora 2 Details from the desktop or Start menu. The installer bundles the .NET app and Python 3.13.15, so no separate runtime install is needed. The portable ZIP remains available.

Start the supported game, then open the meter. It automatically starts a 12-hour read-only command-battle capture and requests Windows administrator approval. Click **■** to detach early or **●** to retry capture. Start capture before entering a command battle; an already-open fight cannot be reconstructed. The meter displays saved encounters when the game is closed.

The **↻** control checks GitHub for newer previews; **↑** downloads one and restarts after capture detaches. Capture refuses an unverified game executable hash. Encounters, meter placement, and raw traces are kept under `%LOCALAPPDATA%\Sora2 Details` so updates preserve them.

Preview 2 also recognizes a game-exit trace as a completed capture, so it does not wait for a detach record when the game has already closed.

Preview 3 makes the update control two-step: **↻** checks, and **↑** starts the download and restart. Checking alone leaves a running capture untouched.

The meter stays on top of the game. Clicking it gives it keyboard focus; click the game to return control. Its startup no longer activates the window over the game. If game input behaves unexpectedly, use Stop and wait for the probe to detach before continuing.

The installer is unsigned, so Windows may display an unfamiliar-publisher warning. The 0.1.0 ZIP is still available for users who need its earlier launcher behavior.

Preview 4 saves the exact English-table candidate names and observed stat signature when an enemy name remains ambiguous. Its raw HP-setter trace also saves bounded stack/frame context to investigate ability and support-proc heals. Heals still display as unattributed until their source is verified. An intervening heal no longer discards a pending damage result.

Preview 5 makes the pop-out combat log show every recorded event in the selected fight, with damage in red, healing in green, and orange Physical / blue Arts icons. It remembers the log window's position and size. The deepest meter rows keep effective damage as the bar value, show known overkill beside it, and reveal total hit, effective damage, and overkill on hover. Death recaps remain short and separate from the full log.

Preview 6 automatically uses the running game's installation path. If Windows does not reveal that path, the Capture button asks the player to select `sora_2nd.exe` and remembers the location after capture starts successfully. The installer no longer relies on the developer's game folder for another player's installation.

Preview 7 starts capture when the meter opens while the game is running. An armed session with no command-battle entry now says it is waiting instead of displaying an older fight as though it were current. The encounter menu has **Current / live** so you can return to the active session after viewing history. Opening the meter while the game is closed still shows saved fights; use **●** after starting the game.
