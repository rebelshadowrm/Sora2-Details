# Sora 2 Details 0.2.0 preview 19

## Shutdown, settings, and effect research

- Fixed Exit during live capture: both **X ? Exit** and tray **Exit Sora 2 Details** now close the application after the capture helpers detach. The owner confirmed both routes on the rebuilt active-capture path.
- Settings now use readable checkbox text, a 60?100% opacity slider, and a remembered X action.
- Added bounded raw capture and lookup guidance for healing and other combat effects. These traces help correlate actions with HP, EP, CP, interrupts, and non-damaging results; the combat log remains partial and unknown effects remain unverified.
- Healing Research Test and ordinary live capture share the corrected shutdown path.

## Preview 18

## Launch, settings, and capture

- Fixed a startup issue that could keep the app from opening after Windows approval. If preview 17 will not launch, install preview 18 with the Setup executable from this release.
- The meter now shows capture state without a separate capture button. Start and stop capture from the tray menu.
- The status reads **Starting capture** while connecting and **Capturing** once the session is active.
- Launching the EXE while Sora 2 Details is already running restores the existing meter from the tray.
- Settings opens in a window and lets you choose whether X hides to the tray or closes the app.
- The system tray icon now uses the app icon.
- Startup no longer shows a separate information dialog before Windows asks for approval.
- Live command-battle capture remains partial; support actions, misses, some move names, and critical status are not fully captured.

## Preview 15

### Boss history filters and lookup refinements

- Encounter history now has **Likely bosses (best effort)**, **Confirmed (fail-open)**, and **Unfiltered** modes. Confirmed is the default; uncertain encounters stay visible unless explicitly marked Regular.
- Exact-name and `+` enemy candidates are labeled tentative. Confirmed boss entries name recognized boss actors without their adds; `+` candidate entries name the `+` actors. Manual encounter marks and the selected mode stay local.
- The live lookup names a narrowly corroborated Counter result. Heal writes without a verified source remain unattributed, and the combat log remains partial.

### Code signing policy

See the [Code signing policy](CODE-SIGNING-POLICY.md) for current signing status, roles, privacy and network behavior, build provenance, and capture security. This Windows preview is unsigned while SignPath Foundation approval and configuration are pending. See [uninstall instructions](README.md#uninstall) in the project README.

### Resident tray lifecycle

- Sora 2 Details requests administrator approval once at startup and remains resident in the system tray as the capture owner. CaptureHost, Python, the bridge, and the updater inherit its approved process token.
- A game already running at startup starts capture after approval. If Trails starts later, the tray notification offers **Start capture?** and waits for the player to choose Start; game exit detaches helpers and returns to a waiting tray state.
- Closing or minimizing the meter hides it to the tray. Tray commands show or hide the meter, start or stop capture, open saved history and settings, restore interaction after click-through, and explicitly exit the application.
- An update during capture explains the detach and restart, waits for confirmed helper cleanup, then updates and restarts with the launch arguments and data directory preserved.
- Production no longer fills an empty meter with sample replay rows. Saved history remains available from the tray when no live session is active.

### Capture improvements in preview 13

- Encounter history can focus on boss and unclassified fights, while preserving marked regular fights under All fights. Candidate labels remain cautious; manual Boss and Regular marks are available and persist across app updates.
- The app explains the live-capture requirement and requests Windows administrator approval at startup, before the main meter appears. The capture host, Python probe, bridge, and updater inherit the approved process context without separate prompts.
- Standard-user-first probing is available only through the explicit diagnostic switch. Normal release startup does not wait for a later process-access error before elevation.
- Update installation now confirms before stopping active capture, waits for a clean detach, and restarts through the existing elevated process chain.
- Installer builds support release signing and a `-RequireSigning` gate. This preview is unsigned, so Windows may show Unknown publisher or SmartScreen warnings.
- Added packaging/readiness checks and a distribution UX audit. Interactive UAC and installed update validation were not available in the build environment.

### What changed in preview 15

- Unresolved move results now retain a specific lookup reason in saved encounters and result details.
- The raw capture records bounded extra memory for positive HP writes, unreadable effect descriptors, and enemy stat signatures with no unique table match. This research evidence may help identify missing heal and enemy links; those labels remain unverified.

**Preview 15 download:** `Sora2.Details-win-x64-preview-Setup.exe` from the preview 15 release.

### Using the preview

This Windows preview provides a compact meter and durable **partial** command-battle combat log. It records observed HP changes and some attributed damaging hits; support actions, misses, some move names, and critical status remain incomplete. It is not yet a complete combat log.

The installer bundles the .NET app and Python 3.13.15, so no separate runtime install is needed. Run `tools/start_probe_session.ps1 -TryUnprivileged` from a standard-user shell only for diagnostic access checks.

Start the supported game, then open the meter. A short note appears before Windows asks for startup approval. Capture starts automatically when the game is already running; otherwise the app waits in the tray. Use **Stop capture** in the tray menu to end a session. Start capture before entering a command battle; an already-open fight cannot be reconstructed. The meter displays saved encounters when the game is closed.

The **↻** control checks GitHub for newer previews; **↑** downloads one; if capture is active, a confirmation explains that the app will detach and restart. The updater reuses the startup-approved process session without a second prompt. Capture refuses an unverified game executable hash. Encounters, meter placement, and raw traces are kept under `%LOCALAPPDATA%\Sora2 Details` so updates preserve them. The combat log remains partial: support actions, misses, some move names, and critical status are not yet fully captured.

### Earlier preview changes

Preview 12 split player and enemy damage dealt, and grouped taken damage by victim with attacker and move breakdowns.

Preview 11 improved Retry detection after a full-party wipe, retaining the first observed attack in the new partial attempt.

Preview 10 added the in-meter knockout list and one-click death recaps. It also recognized a retry after a full-party wipe when the first later HP read was full.

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
