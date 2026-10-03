# Audit and capture readiness protocol

## Application identity and completion

Record the source revision and dirty changes, shortcut target, executable version/hash, data directory, running PID, profile and helper PIDs. A source build does not update an installed shortcut. A raw-only research launcher does not prove that the desktop received any events. A detached probe does not prove that the app exited.

For a defect, trace and repair the failing path, add a focused regression check and verify that path. Separate source, package, installation, simulated desktop and real-game results in the report. Preserve original raw traces. Back up derived encounters before reprojecting them. Missing original evidence must be reported rather than recreated from chat.

## Lookup evidence

Capture the key and complete candidate row during the observed callback. Match executable/table hashes, verified call path, row key and companion parameters to one exact row. The separately recorded key must agree with the bytes. A pointer in a later trace is a candidate lead, even when executable hashes and addresses match: object identity and lifetime have not been established.

For the current supported executable, direct numeric HP pairing requires both verified hooks, the same thread and target, a maximum 0.5-second interval, setter caller RVA `+0xE4DB1`, and agreement between result amount and requested HP delta. CP row lookup is limited to setter caller `+0xE1FAD` with inline R14 bytes. Generic owner 65535 does not identify the support owner. Cap-derived after-values remain calculated; they are not post-write reads. Never infer critical, interrupt, miss or buff application from a missing HP change.

## Required checks

Run these explicitly from the repository; broad Python unittest discovery misses standalone main-based checks:

```powershell
dotnet build Sora2.Details.sln -c Release
dotnet run --project tests/Sora2.Details.Checks -c Release --no-build
dotnet run --project tests/Sora2.Details.Desktop.Checks -c Release --no-build -- .research-deps/desktop-audit
python tools/test_elevated_probe_session.py
python tools/test_lifecycle_probe.py
python tools/test_live_capture_bridge.py
python tools/check_table_linkage.py "C:\Games\Trails in the Sky 2nd Chapter\pac\steam\table_en.pac"
python tools/test_enemy_ai_skill_index.py "C:\Games\Trails in the Sky 2nd Chapter\pac\steam\script_en.pac"
python tools/audit_capture_history.py --output .research-deps/history-audit.json
```

The desktop harness exercises real WPF settings, saved-file refresh, open timelines and X/tray exit using simulated capture helpers. It does not attach to the game or validate Windows elevation. Package checks must exercise the bundled runtime. Inventory warnings for missing old traces are evidence limits, not permission to discard records.

## One prepared live batch

Follow [the current research workflow](RESEARCH-WORKFLOW.md) and
[manual-stop policy](LIVE-RESEARCH-STOP-POLICY.md). Complete offline investigation
autonomously before requesting a minimal new contrast.

1. Finish saved-trace analysis and define the unresolved fields, hook budget, expected contrasts and stop condition first.
2. Verify the exact launched build, profile, target hash/PID, raw `armed` marker, living bridge and writable encounter path. Prove that one observed event persists while idle and reaches the open desktop log before telling the player capture is ready. An armed marker alone is insufficient.
3. Collect the smallest controls needed for the unresolved contrast. Profile coverage differs: HealingResearch omits BattleEnd and uses one battle; action-stream profiles have their own documented boundaries and gaps.
4. Record player annotations independently from raw keys. Align actual timestamps before assigning a report to a trace; chat order alone cannot prove an action was captured or missed.
5. Keep capture armed until the player's completion report and inspection of the saved sequence, then stop via its manual sentinel and verify detach and owned helper exits. No duration/hit cutoff, keyword or further stop approval. Release the player from additional controls, then process lookups and reconcile outcomes offline. Do not ask for repeat controls already answered by saved evidence.

Complete combat coverage requires independently observed selected/executed/cancelled actions, effect results and encounter boundaries. The current four-hook profiles only observe subsets and must continue displaying partial coverage.
