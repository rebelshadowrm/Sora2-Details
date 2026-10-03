# Real game-to-viewer recording

Batch `fcbcdb7d1ad644faaea1d69e4d604973` captured the player's Agate Guard,
reported support proc, and Dragon Dive victory. The unchanged Transcript hooks
ran against executable SHA-256
`d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`.

The actual WPF viewer followed the ledger while the probe remained armed. Its
audit recorded 204 displayed observations and both action candidates before
stop, with raw-source verification true. Execution order was Agate Guard at
17:01:04.239, then Agate Dragon Dive at 17:01:08.746 (local UTC-05). Five effect
dispatch observations uniquely matched Heat Up II, and 90 matched Dragon Dive.
These are dispatch calls, not independent proc counts or hit counts. The two
Dragon Dive targets remain separate unnamed status instances 60047 and 60048.

One observed engine interval closed with exact-route exit argument 1, enriched
as Victory candidate and corroborated by this player's report. Verified outcome
and comprehensive command-only boundary coverage remain unresolved. The support
descriptor match does not establish its trigger logic or individual CP outcome.

After checking the player's finished sequence, the probe's manual sentinel was
written. Disarmed appeared at 17:01:59.128 and detached at 17:01:59.457. The
launcher and bridge exited. The viewer applied the final 206-record ledger with
two action candidates and source hash
`72098c0c548606e601809a0848b99fd770ba9b5389cefa445c9ba5b6d5857cb7`.
The separate viewer sentinel then produced a closed audit marker at
17:02:31.963; its PID 29412 exited. Game PID 29960 stayed running.

Evidence lives under `%LOCALAPPDATA%\Sora2 Details\research\action-stream`:
`action-stream-<batch>.jsonl`, `ledger-<batch>.json`, `control-<batch>.json`,
`viewer-audit-<batch>.jsonl` and its inspected PNG. The final screenshot shows
both ordered action candidates, 206 observations, and "Raw source verified".

## Live failure resolved on the same recording

The first viewer attempt failed because `File.ReadAllBytes` opened the raw file
without sharing write access while PowerShell still held its recording handle.
The probe stayed armed while the reader was repaired. The reader now opens both
ledger and raw source with read/write/delete sharing and verifies exactly the
ledger's committed newline-complete prefix, rather than a racing file tail.
The restarted viewer verified the same growing source and reached the final
hash/count above. Initial failure stderr is preserved separately from the empty
retry stderr. A focused Windows writer-open regression also passes.

## Desktop integration

The tray now offers Action stream (partial), starts a separate registered manual
recording owner, and opens the active ledger in an owned auto-refreshing viewer.
The starter returns after arming; it does not keep the desktop busy until the
recording finishes. Normal Stop/Exit writes the sentinel and requires observed
detach plus launcher/bridge exit before cleaning the active manifest. The mode
does not feed candidate observations into verified meter totals.

Seven simulated desktop shutdown cases pass, including X and tray Exit with
Transcript helpers active. Release build, core persistence/source checks,
32 reconciliation checks and 18 snapshot/timeline/bridge checks pass. Real
desktop startup/stop verification is tracked separately from those simulations
and from the live observer result above.

The elevated real-game lifecycle check then exercised the normal `MainWindow`
start, active-transcript open, manual Stop and full Exit handlers. Final batch
`8bd99f3c95e04e139c29e566dd5a19e2` has eight source-verified lifecycle observations,
including armed/disarmed/detached; no player actions were requested. The owned
viewer and desktop closed, both registered helpers exited, current.json was
removed, and game PID 29960 survived. Launcher and bridge stderr are empty.
The harness log and screenshot are in
`.research-deps/action-stream-20261002/app-lifecycle-elevated`.

The first lifecycle run exposed a separate PowerShell process-bookkeeping
defect: `Start-Process -PassThru` did not retain an exit code for the short-lived
bridge, so null was treated as a projection failure after successful detach and
publication. Holding its process handle immediately after launch fixes this.
The repeat checked error logs and failure records as well as the final ledger;
the original failure batch `379c3b157ea14a2fb73ae1a7a0e253a5` remains preserved.
The earlier non-elevated harness attempts never armed or attached. Capture
helpers now explicitly reject that context rather than requesting another UAC.

The pinned embedded Python runtime, with only the installer's declared runtime
files copied to an isolated directory, also reproduces the finalized 206-record
live ledger exactly. This verifies the new dependency list without publishing
or replacing the installed preview.

Remaining project work includes comprehensive action/outcome semantics, exact
enemy identity, per-target results/critical flags, pristine entry-state timing,
production command-only boundaries, and ingestion into the shared combat-log
protocol. This test establishes durable live research display, not a complete
combat adapter.
