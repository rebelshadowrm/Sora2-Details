# Actor stages live result, October 2

Batch `015c4a4e82414a8dae169f8e841d3395`, PID 29960, module base
`0x7FF6D4480000`, supported EXE hash. Raw file is under
`%LOCALAPPDATA%/Sora2 Details/research/action-stream/action-stream-015c4a4e82414a8dae169f8e841d3395.jsonl`.
SHA-256: `8e78e3ba4396701f850754f4ff6e2ea8006dc15426df0f647cadec38d498a465`.

Armed 13:49:38.961, disarmed 13:58:16.501, detached 13:58:16.825, UTC-05:00.
Explicit sentinel stop followed the finished player report and verification of
late Dragon Dive/Chain observations. There was no timer/hit cutoff. The game
remained running. Raw research was not displayed in the desktop meter.

All 1,394 records are preserved, with 1,387 hits: 215 first-state observations,
348 animation queue-call returns, 530 broad effect rows and 294 resource setter
entries. Replay yields 29 linked launch candidates, 41 dispatch-run candidates,
two pending/resume cast links and no sequence issues. These are not action counts.
Unknown descriptors remain unnamed. Player annotations are separately preserved
in `batch-<id>.json`; ledger and analysis JSON accompany the raw file.

## Controlled observations in order

Numbers are raw hit sequences. Actor associations are research-scoped, supported
by inline normal-attack owner IDs, linked status IDs and player controls.

| Sequence | Observation |
| --- | --- |
| 96, 103 | Agate Guard twice: identical descriptor, separate first defend-handler visits. Both launched; static animation bypass remains untested. |
| 113 | Estelle normal attack 1. |
| 370 | Exact Resurgence candidate on Estelle's support completion, effects source context Estelle and target Agate. Trigger/equipped ownership unverified. |
| 377 | Agate Guard. |
| 457 | Estelle normal attack 2; critical is player-reported. |
| 522, 530 | Kevin Guard, Agate Guard. |
| 556 | Exact Heat Up II candidate on Agate's support completion, self-context effects. |
| 570, 573 | Estelle Saint preparation/pending. |
| 577 | Kevin attack between Saint pending/resume; no linked effect run. Miss is player-reported, not inferred from absence. |
| 605 | Exact Gralsritter's Grace EX candidate on Kevin's support completion. |
| 610, 612 | Saint resume/main handler; pending pointer and all descriptor bytes match 573. |
| 642 | Estelle normal attack 3. |
| 701, 703 | Agate Clock Up EX immediate/resume path and main handler, without observed pending state. No-cast-time quartz is reported; intrinsic spell speed is not concluded. |
| 734 | Estelle normal attack 4; noncritical is player-reported. |
| 821, 823 | Estelle Orbal Down preparation/pending. |
| 831 | Agate normal attack between Orbal Down pending/resume. |
| 894, 896 | Orbal Down resume/main handler; pending pointer/bytes match 823; Panda-context effects follow. Stat magnitude not decoded. |
| 913 | Estelle Wheel of Time. Overdrive remains unassigned. |
| 1024 | Kevin Grail Sphere, multiple recipient runs retained. |
| 1084 | Estelle Morale EX, multiple recipient runs retained. |
| 1126 | Agate Dragon Dive. Overdrive/critical semantics unassigned. |
| 1199 | Estelle Chain: exact `0xFFFF0045`, handler `0x68D40`, five subsequent broad effect rows. Individual chain-hit outcomes not reconstructed. |

The report "Agate attacked and countered" is ambiguous; no extra normal attack
is fabricated there. Reaction handler `0x6CDB0` is observed with retained Guard
descriptor, but automatic counter classification is not verified.

## Resources and recorder correction

Agate status ID 5: HP setter sequence 332 requests -1 from pre-value 99; 361
requests 583 from zero; 372 requests 2,916 from 583. That later pre-value
corroborates the earlier 583 write, not the final 2,916 post-value. The Resurgence
source/target graph supplies an attribution candidate, not just timestamp proximity.
Resource caller `0x6AC64`, within actor handler `0x6AA80`, requests CP -200 on
several dying actors including enemies. It must not be labeled Overdrive.

The launch inspector mistakenly assumed RBX retained the entry context at
`0x21558F`; exact disassembly shows EBX overwritten at `0x2153A8`. Saved caller
registers recover owners for verified callers: `0x686F1` uses saved RSI at stack
+0x60; `0x68E8B`/`0x69638` use saved RBX at +0x70; `0x69311` uses saved RBX
minus 0xC70. A matching prior first-handler snapshot and actor pointers are
required. Unknown frames stay unassigned. Twenty-nine launch candidates were
recovered without modifying raw rows. Recovered descriptors come from the prior
handler snapshot, explicitly marked as not launch-time reads. Future snapshots
use the corrected caller-scoped owner recovery, which itself awaits live read
validation; this batch's saved-frame recovery is verified offline.

Replay now links pending state, resume, subsequent main handler and effects,
without treating preparation and main handler as extra player actions. It
distinguishes a stored-descriptor observation from observing its store instruction.

Ten snapshot and 24 reconciliation checks, synthetic lifecycle/manual stop,
bridge checks and core checks pass. Release build has zero warnings/errors.
Live evidence validates these first-state routes, not universal event coverage
or desktop ingestion. Overdrive, general crit/miss/counter detection, support
triggers, interrupts, chain-hit results and stat deltas remain unverified.

## Follow-up: Quick and ordered action projection

The player clarified that an earlier Clock Up EX was cast without cast-time
investment or a zero-AT bonus and placed its recipient at zero delay. This is
positive player evidence for intrinsic Quick semantics, separate from the
quartz-assisted example above. A decoded engine Quick flag remains unverified.

`action_stream_timeline.py` projects an ordered timeline into each derived ledger's
`actionTimeline`. One candidate represents each first main, defend, or chain
handler; pending/resume stages share their eventual main-handler candidate ID.
Effects inherit established queue/launch links only. Unmatched observations
remain ordered with unknown attribution; critical/result classifications stay
null. Latest replay has 25 main/defend/chain candidates (including unnamed enemy
descriptors) and all 1,394 observations. Support stages are retained but not
promoted to extra actions using a potentially stale descriptor. Chain effects
remain unlinked pending a verified parent route.

Two focused projection checks pass alongside the 24 reconciliation checks and
Release/core checks. All four saved batches replay without dropping or reordering
raw observations. Older profiles without the first-handler hook receive zero
primary action candidates, rather than retroactively invented actions.
