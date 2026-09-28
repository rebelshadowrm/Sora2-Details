# Sora 2 Details 0.2.0 preview 11

## What changed in this preview

- Retry detection now starts a new partial attempt when, after four observed party knockouts, a member last seen at zero HP attacks or appears with positive HP without an observed revive. The opening observed attack stays in the new attempt.
- The in-meter knockout list and one-click death recap from preview 10 remain included.

**Normal-user download:** `Sora2.Details-win-x64-preview-Setup.exe` from this release. Existing users can apply preview 11 with the meter's update button.

## Using the preview

This Windows preview provides a compact meter and durable **partial** command-battle combat log. It records observed HP changes and some attributed damaging hits; support actions, misses, some move names, and critical status remain incomplete. It is not yet a complete combat log.

The installer bundles the .NET app and Python 3.13.15, so no separate runtime install is needed.

Start the supported game, then open the meter. It automatically starts a 12-hour read-only command-battle capture and requests Windows administrator approval. Click **■** to detach early or **●** to retry capture. Start capture before entering a command battle; an already-open fight cannot be reconstructed. The meter displays saved encounters when the game is closed.

The **↻** control checks GitHub for newer previews; **↑** downloads one and restarts after capture detaches. Capture refuses an unverified game executable hash. Encounters, meter placement, and raw traces are kept under `%LOCALAPPDATA%\Sora2 Details` so updates preserve them. The combat log remains partial: support actions, misses, some move names, and critical status are not yet fully captured.

## Earlier preview changes

Preview 10 added the in-meter knockout list and one-click death recaps. It also recognized a retry after a full-party wipe when the first later HP read was full; preview 11 expands that detection to the earlier observed party attack and partial-HP reads.

Preview 9 applied opacity to the whole window, added tray-controlled click-through, and removed the Visible rows setting.

Preview 8 added clean capture detach on exit, persistent capture state and version, richer encounter history, position lock, always-on-top, text size, and a local retry-splitting fallback verified against the Walter trace. It also reduced installed runtime files to those needed for capture and updating.

Preview 2 also recognizes a game-exit trace as a completed capture, so it does not wait for a detach record when the game has already closed.

Preview 3 makes the update control two-step: **↻** checks, and **↑** starts the download and restart. Checking alone leaves a running capture untouched.

The meter stays on top of the game. Clicking it gives it keyboard focus; click the game to return control. Its startup no longer activates the window over the game. If game input behaves unexpectedly, use Stop and wait for the probe to detach before continuing.

The installer is unsigned, so Windows may display an unfamiliar-publisher warning. The 0.1.0 ZIP is still available for users who need its earlier launcher behavior.

Preview 4 saves the exact English-table candidate names and observed stat signature when an enemy name remains ambiguous. Its raw HP-setter trace also saves bounded stack/frame context to investigate ability and support-proc heals. Heals still display as unattributed until their source is verified. An intervening heal no longer discards a pending damage result.

Preview 5 makes the pop-out combat log show every recorded event in the selected fight, with damage in red, healing in green, and orange Physical / blue Arts icons. It remembers the log window's position and size. The deepest meter rows keep effective damage as the bar value, show known overkill beside it, and reveal total hit, effective damage, and overkill on hover. Death recaps remain short and separate from the full log.

Preview 6 automatically uses the running game's installation path. If Windows does not reveal that path, the Capture button asks the player to select `sora_2nd.exe` and remembers the location after capture starts successfully. The installer no longer relies on the developer's game folder for another player's installation.

Preview 7 starts capture when the meter opens while the game is running. An armed session with no command-battle entry now says it is waiting instead of displaying an older fight as though it were current. The encounter menu has **Current / live** so you can return to the active session after viewing history. Opening the meter while the game is closed still shows saved fights; use **●** after starting the game.
