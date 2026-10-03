# Mode flags and repeated-attempt capture result

Batch `5423e162d9bf4f9caa0a27e5d75b41de`; supported EXE SHA-256
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
Armed 15:20:42.400, manually disarmed 15:25:42.546, detached 15:25:42.874
(UTC-05:00); no duration/hit cutoff. Game remained running. Raw SHA-256
`8750e1d1612b8b686d9c3ac1d1927014748e5a2760c152b9d84a85a8773cdbbe`.
Raw, ledger and player-report metadata remain in the local research directory.

2,310 records: eight markers, 2,302 hits (15 mode writes, 316 first actor updates,
1,460 effects, 511 resource setters). Reconciliation preserves every record,
28 primary candidates and five completed engine intervals, with zero issues.
These are observations, not complete action or damage counts.

Player reports several mistaken attempts and enemy-advantage openings, then a
command pack of two Pinchy Bubblers and Mars Gel followed by a plant-like field
quick kill. Earlier individual controls/timestamps are unresolved. Final control
aligns by ordered Guard/Dragon Dive and subsequent field activity. Player names
remain separate from automatic unit labels.

## Retained attempts

| Interval | Entry–exit | Raw flags | Exit argument | Primary candidates |
| --- | --- | --- | --- | --- |
| 1 | 15:20:55–15:20:59 | 0x11 | 3 | Agate Wild Rage II |
| 2 | 15:21:09–15:21:16 | 0x11 | 1 | Agate Guard, Dragon Dive |
| 3 | 15:21:22–15:21:48 | 0x34 | 1 | 16 candidates: guards, attacks, enemies, follow-ups |
| 4 | 15:22:25–15:22:43 | 0x34 | 1 | Seven candidates including Sacrifice Arrow and attacks |
| 5 | 15:22:59–15:23:40 | 0x11 | 1 | Agate Guard, Dragon Dive |

Flags are read inline at root `+2CEC`; native `C2750` stores incoming R9D there.
They remain unchanged across writes within each interval. First opening handler
`67270` accompanies 0x11; `65ED0` accompanies 0x34 in these samples. Player
reports enemy-advantage mistakes without exact per-attempt timing. These are
opening-pattern candidates, not a verified advantage or combat-mode enum.

First attempt's enemies still have HP 28767, 28767 and 25890 in cleanup before
exit argument 3. The player subsequently confirmed entering intentionally to
gain CP with Wild Rage II, then escaping to prepare the next Guard/Dragon Dive
fight. This supplies the missing controlled Escape example. The earlier field/battle capture also has living enemies at its
code-3 exit. The previous inference that this extra interval necessarily meant
a quick kill is withdrawn. Chat report order does not establish native timing.

Static `118860` writes result slot `+E8 = 3` on first update. `BAC1C` reads the
slot from root `+C8` into EDX before `C4E30`; `C5700` restores that argument into
R14D before clearing root `+2D30`. This explains the raw value without naming
it from native instructions alone. The confirmed Escape control supplies a
research candidate name for 3; the earlier explicitly reported Victory control
supplies a contrasting candidate for 1. Other codes stay unknown. Candidate names
are scoped to the supported EXE, stable root and exact verified exit writer;
malformed/oversized register values and neighboring writes cannot supply them.
The ledger's verified `outcome` remains Unknown; `outcomeCandidate` and control
provenance are separate. The viewer explicitly displays Escape/Victory as candidates.

## Final control and field data

Final Guard at 15:23:01.251 and Dragon Dive at 15:23:39.465 are distinct;
exit is 15:23:40.705. Dragon Dive targets statuses 60043, 60044, 60045,
retained separately. Ready roster has Estelle/Agate/Kevin candidates and these
three unnamed enemies. Enemy stat-signature fallback found no unique exact-table
matches; no nearest match or player-pack guess is used.

After exit, 185 effects and 69 resource writes remain unframed. Effect contexts
include enemy status 60046 toward Agate/Kevin, then party contexts toward 60046
(145 calls Agate, 20 Estelle, ten Kevin). These are effect-call counts, not
attacks, hits or confirmed damage. Field descriptors and plant unit name remain
unknown. No later mode entry occurs; these records stay outside the selected
command fight and are not added to its meter totals.

## Persistence and display

Intervals retain flag snapshots and raw roster/status snapshots. Initial flag
entry has zero roster count. Neighboring-byte write ending `C4AA4` gives one
complete bounded roster per interval (six, six, six, five, six entries). This
is observed initialization timing, not verified pristine pre-effect entry stats.
Actor candidate IDs include interval identity, preventing cross-attempt pointer
reuse from merging actors.

Core and WPF retain/validate interval observation references. The selector offers
all records, each interval, and outside/unframed records. Refresh preserves
selection; an unframed append does not contaminate the selected fight. Invalid
updates retain the last valid snapshot. Original raw data remains available.

Effect rows gain source/target status and move candidates from inline snapshots,
including calls without a primary parent action. Exact party lookup requires
full 0x2A0 status bytes. Unknown enemies/moves, incomplete reads, absent parents
and unverified outcomes remain explicit; no executed action is invented.

Release solution build has zero warnings/errors. Core checks, 31 reconciliation
checks and 17 snapshot/timeline/bridge checks pass. Saved WPF replay shows all
28 candidates and 2,310 observations, isolates the final two candidates, separates
unframed data and passes refresh/invalid-update checks. Actual live desktop
display during this batch remains unvalidated. Detach and running game are
separate verified outcomes.

No additional action repetition is currently required. The first Wild Rage II
attempt's Escape control is now confirmed and recorded in batch metadata. Production
ingestion, complete action/outcome coverage and live desktop validation remain
project gates; this is a partial research path.

The next prepared live dependency is [recording-to-viewer verification](LIVE-TRANSCRIPT-DISPLAY-PACKET-20261002.md),
not another mechanics discovery batch. A standalone offscreen observer displays
all saved rows, verifies the source, waits for its manual sentinel and exits
cleanly. The desktop's read-only `--recorded-stream` path opens this viewer
without starting capture or conflicting with the installed meter. Real live
producer-to-viewer validation remains unperformed until the player is available.
