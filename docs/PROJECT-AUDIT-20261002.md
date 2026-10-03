# Project audit — October 2, 2026

## Conclusion

The audit and supported repairs are complete. The application passes build, persistence, lookup, capture simulation and actual WPF regression checks. The normal local installation has been updated to **0.2.0-preview.20**, including these fixes. **The overall goal of a comprehensive advanced combat log is not yet achieved.** The current capture observes a subset of actions and effects and must continue marking encounters partial.[^remaining]

There was no running game during this audit. Windows startup approval, real debugger attachment, field exclusion and a complete battle through the newly installed app were not exercised. The desktop tests use simulated capture helpers; they establish the real settings, projection and shutdown paths without claiming game coverage.

Source baseline: `274879fc9ba9078b42a60774088cc532578f4c42` plus the existing thread changes and audit repairs, still uncommitted. The tested installed desktop SHA-256 is `0BC7091697E5E5AC59754F673EFD3598E8E2954EAB7857319AF3B14650641046`. The supported game SHA-256 remains `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.

## Problems corrected

| Finding | Correction and evidence |
| --- | --- |
| A final event could stay in bridge memory until another callback or detach. | Flush pending events at idle EOF. A single CP event now persists without another action; a split JSONL append is retried until complete. |
| An already-open combat log could stay on an old snapshot. | Refresh owned timelines when history changes. Actual WPF checks save a second event and confirm the open timeline and meter footer update. |
| The UI could lose the newest encounter after capture ended. | Preserve newest saved selection after the active trace disappears; periodically reload history even without a reset notification. |
| Research capture and displayed capture were previously confused. | HealingResearch starts the encounter bridge; the UI distinguishes Capturing from Raw trace. The tray now offers Live and one-battle Effect research modes while stopped. |
| Failed attachment metadata could leave misleading capture state. | Recognize a finished failure before attach and expose its error. Failed-attach X and tray shutdown cases pass; the original failed raw trace remains preserved. |
| Dark checkbox text and slider construction could fail. | Use readable close-dialog checkbox text and guard slider initialization before its value label exists. WPF checks verify contrast, 60–100% range and persisted 73% opacity. |
| One corrupt history file could prevent healthy history from loading. | Validate files individually, retain broken evidence and show warnings. Core checks confirm healthy entries survive two invalid files. |
| Some historical healing/support labels came from later snapshots at the same pointers. | Remove this authoritative fallback. Matching addresses and executable hashes do not prove object identity/lifetime. New labels require inline row bytes, consistent keys and a unique exact-table match. |
| Numeric HP attribution could consume a nearby unrelated effect. | Require verified hook paths, same thread/target, caller RVA +0xE4DB1, at most 0.5 seconds and matching requested delta. Wrong caller and wrong amount tests stay unattributed. Attack pairing also checks age and amount consistency. |
| Developer tests and the normal shortcut launched different builds. | Verify the actual OneDrive desktop shortcut, package the source fixes and update its installed target through Velopack without restarting the app. |
| General Python test discovery omitted standalone capture checks. | Run bridge and lifecycle scripts explicitly in the package builder and audit protocol. Disable bytecode creation in lifecycle test subprocesses so packaging checks do not introduce caches. |
| The sample launcher could activate an existing app instead of its promised isolated replay. | Refuse that launch with a clear instruction to exit the running instance first. Also correct forwarding of the boolean meter-only argument. |

## Historical evidence

The inventory covers **651 encounters, 14,447 events and 63 raw trace files** across available local capture/research locations. After correcting derived records it reports **zero integrity errors and six evidence warnings** for older referenced traces that cannot be located. This is structural validation, not proof that every game event was captured.

Two recovered projections contain 31 and 83 rows respectively. The 31-row window retains Kevin-to-Agate numeric HP pairing for +1,997, EP and CP requests, but its missing inline skill bytes no longer acquire names from later memory snapshots. The 83-row window retains observed attack/resource rows and the separately identified player-confirmed Victory annotation; it remains incomplete. Resource after-values are calculated from entry values, requests and caps, not independent post-write reads.

Original derived records are backed up under `%LOCALAPPDATA%\Sora2 Details\research\audit-20261002\derived-backups`. Raw traces were preserved. Audit JSON and UI screenshots are under `.research-deps\audit-20261002` in this checkout.

Final deployment verification matched **60 installed package files** against the portable artifact and confirmed all **63 inventoried raw trace hashes** unchanged. Detailed hashes and paths are recorded in `.research-deps\audit-20261002\deployment.json`.

The Agate-opening Clock Up EX/Saint report has no confidently aligned trace window. Earlier assertions that it definitely occurred after capture stopped were unsupported and have been corrected. The 22:50 failed attach is real; its relationship to that particular report is unproven.

## Validation performed

- Release solution build: **zero warnings and zero errors**.
- Core replay, totals, projections, recorder, pipe, atomic persistence and corrupt-history checks: **passed**.
- Standalone bridge and lifecycle checks: **passed**, including idle/split-write persistence and negative attribution controls.
- Probe readiness checks: **two passed**.
- Exact local English table linkage and enemy AI archive controls: **passed**.
- Actual WPF harness: **five passed** — X and tray exit during simulated active capture, both exits after failed attachment, and X during raw-only capture. Desktop closure and helper exit were confirmed, with completion in approximately 0.02–0.32 seconds. Settings, capture-mode guards, saved event visibility and open timeline refresh also passed.
- New audit skill and four revised skills: **validated**. PowerShell tools parse cleanly.
- Self-contained installer/portable package: **built**, bundled Python checks passed, host argument/package checks passed, and archive contents inspected for private raw/history data. The public sample fixture is included.
- Local installed runtime: **readiness, lifecycle and bridge checks passed**. Velopack confirms preview 18 → preview 20 applied successfully, and the normal shortcut resolves to preview 20. Installed executable/runtime source bytes are checked against the delivered portable package; generated caches are excluded from that comparison.

The local candidate is in `releases\audit-preview20-final`. It has not been published to GitHub or the update feed. The app was left closed. Installation success and simulated shutdown checks do not establish interactive elevation or a battle on the installed build.

## Coverage against the original goals

| Goal | Current result | Remaining evidence |
| --- | --- | --- |
| Healing amounts | Positive HP requests and calculated capped outcomes recorded. Direct numeric source/target pairing supported on one verified path. | Independently observed post-write values and broad path coverage. |
| Healing ability names | Exact skill lookup available when a verified callback captures inline row bytes. | New real controls proving direct Art, item and support keys; older missing bytes cannot be recovered by pointer equality. |
| HP / EP / CP | Shared setter records all six set/add resource properties and preserves requests, caps and recipients. | Action causality, support owner, actual after-values and paths bypassing the setter. |
| Support skills | Some inline CP rows can be named; generic owner 65535 remains source-unknown. | Support activation/owner and passive healing keys. |
| No-damage casts / buffs | Raw numeric calls and property writes remain visible even without damage. | Selected/executed action identity and applied condition keys. An observed effect call is not a complete cast record. |
| Interrupts / cancellations | No validated general outcome route. | Queued action identity and explicit cancellation/interrupt state. |
| Enemy moves | Some exact per-unit AI names; stat-derived unit identity remains provisional and ambiguous matches stay unknown. | Direct runtime unit key and unmatched move routes. |
| Critical / modifiers | Raw candidates preserved; automatic critical flag remains unknown. | Per-result decision path and controlled modifier comparisons. |
| Burst / chains / multiple targets | Individual observed results/resources recorded. | Common action parent, follow-up/support relationships and complete resource reconciliation. |
| Battle lifecycle | Live uses command callback, attack effect, resource setter and BattleEnd. Research adds numeric effect and omits BattleEnd. | Verified command-only scope, entry snapshot and decoded end outcomes; research must stop after one battle. |
| Visualization | Meter totals plus full event timeline, raw/candidate distinctions, entry counts and live refresh. | Extend semantic views as independently verified event types become available. |

## Protocols established

The new [project audit skill](../.agents/skills/sora2-project-audit/SKILL.md) and [audit/capture readiness protocol](AUDIT-AND-CAPTURE-READINESS.md) require application identity checks, end-to-end display evidence, negative lookup controls, explicit test entry points and separate validation scopes. Build, test, tracing and lookup skills now reflect the actual elevation model and prohibit unsupported cross-trace labels.

The next game session must be a prepared bounded batch. Establish the launched version, armed probe, working bridge, durable idle save and displayed log before requesting actions. Collect the controls, stop capture, let the player leave combat, then analyze offline. A new random proc is not a substitute for tracing its activation route.

[^remaining]: **Remaining steps to finish the project, in order:** (1) Validate startup approval and one real battle on installed preview 20, confirming raw capture → bridge → durable encounter → open timeline, including both exit routes while actual capture is active. (2) Capture inline keys for controlled Art and item heals plus a natural support window; verify source/recipient/owner separately and keep unsupported labels unknown. (3) Establish an independent selected/executed/cancelled action stream and authoritative command-battle boundaries/outcomes so no-damage actions, misses and completed casts are represented. (4) Trace applied status/buff/debuff keys and explicit interrupt/cancellation results with positive and contrast controls. (5) Observe actual HP/EP/CP after-values and link costs, support procs, chains, Burst and repeated/multiple-target effects to shared action parents; reconcile complete sequences. (6) Verify the true per-result critical/modifier path and direct enemy unit identity, then expand enemy skill lookup without guessed names. (7) Validate completeness against full annotated batches, field exclusion, accelerated play, same-name actors, retry/escape/defeat and attach/disconnect/update/shutdown transitions; expose dropped events and gaps. (8) Extend timeline/grouping and projections for the newly verified semantics, commit the reviewed changes, publish a fresh preview and verify its update feed and prior-version upgrade. Signing remains a separate distribution task once the pending identity/configuration is available. These are implementation and live-evidence tasks; the current passing audit does not complete them.
