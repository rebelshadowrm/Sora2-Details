# Transcript field/battle contrast result

Correction from [the subsequent multi-attempt capture](MODE-FLAGS-LIVE-RESULT-20261002.md):
the extra code-3 interval must not be identified as a quick kill solely from
the player's report. Its final snapshots show living enemies, as does a later
code-3 interval. Per-event timing and the exit enum remain unresolved. The
original quick-battle inference below is historical and superseded by this
correction; raw data and unresolved result codes are unchanged.

Batch `063063bef9fb42528ffa998b5eae3a70`, supported executable SHA-256
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
Armed 15:07:54.283, manually disarmed 15:10:44.166 and detached
15:10:44.494 (UTC-05:00), no duration/hit cutoff. Raw SHA-256
`9503e82a2fbd1d3b53aa6d98e78c5d11f4c014a03dbc0ace699b1f3e966f9c90`.
487 records: 479 hits, eight markers; 83 first actor state updates,
215 effect calls, 175 resource setters and six watched writes.
Raw/ledger/player-report metadata remain in the local research directory.

## Controls and retained sequence

Player reports Agate Guard twice; Estelle critical normal attack plus selected
follow-up; Kevin Saint on Agate queued and resolved; Agate Dragon Dive; victory.
Then a field quick battle in which Agate took one hit and attacked/killed Mars
Gel. Enemy name, critical and victory remain player reports, not automatic labels.

The transcript contains six primary candidates in order:

| Time | Actor candidate | Move candidate | Evidence |
| --- | --- | --- | --- |
| 15:08:29.322 | Agate | Guard | First guard handler |
| 15:08:30.742 | Agate | Guard | Distinct first guard handler |
| 15:08:33.906 | Estelle | Normal Attack | Main handler, 40 effect calls |
| 15:08:35.356 | Kevin | Raw `FFFF0044` | Chain handler, five effect calls |
| 15:08:57.911 | Kevin | Saint | Pending/resume/main/effect linked, five calls |
| 15:09:08.627 | Agate | Dragon Dive | Main handler, 90 effect calls |

Follow-up variant remains unresolved despite the observed chain handler.
All quick battle and outside-interval records remain in the raw timeline;
absence of a primary action candidate does not mean those events were dropped.

## The flag is broader than command combat

Root `0x21a919161b0` remained stable. Baseline `+2D30` was zero. Both battles
used entry writer ending `C35AD` and exit writer ending `C5753`:

| Player control | Entry hit/time | Exit hit/time | Exit argument candidate |
| --- | --- | --- | --- |
| Command fight | 1 / 15:08:26.722 | 253 / 15:09:12.791 | 1 |
| Quick field fight | 348 / 15:10:10.410 | 375 / 15:10:18.365 | 3 |

The initial interpretation was that the flag alone could not enforce command-only capture. Reconciliation
now annotates the first interval `CommandStagesObservedCandidate`; the second
remains `UnclassifiedEngineBattle`, without inferring mode from absent stages.
Neither becomes a verified command encounter or meter total.

The exit argument is supported by exact-build native code: `C4E30` stores its
incoming EDX at stack `+50`; `C5700` restores it into R14D before flag clear.
The observed values differ between these two player controls. Their enum and
meaning across defeat/escape/other outcomes remain unresolved. No automatic
Victory/QuickBattle enum was introduced.

The four-byte aligned watch also saw a neighboring-byte write ending `C4AA4`.
At `C4A9C` the native instruction clears root `+2D31`, leaving `+2D30` unchanged.
This previously reset framing as an unknown route. The fix accepts this exact
root/writer only when the low byte is unchanged, preserving the interval and
raw observation. Tests reject a mismatched root or inconsistent low-byte change.
Replaying the same saved trace now closes both intervals with no issues.

## Persistence, display, and next evidence

The research bridge published committed-prefix snapshots while the raw file grew
and finalized after detach without stderr errors. Saved WPF replay displays six
candidates and all 487 observations with raw selection; refresh and invalid-update
retention checks pass. Desktop display during this actual game recording was not
validated; saved replay is distinct from end-to-end live UI validation.

The revised probe snapshots bounded root bytes `+2CE0..+2D5F` at mode writes,
including raw initializer flags at `+2CEC`, plus at most 16 roster entries from
`+2448`/signed count `+2450` and linked raw status bytes. Native `C2750` stores
incoming R9D at `+2CEC`, but the current trace did not read these bytes inline.
Later memory cannot reconstruct them. The snapshots are raw candidates, not
validated mode enums or complete entry-state snapshots.

The next live dependency is one short command/quick contrast with these additional
inline fields. It can use one Guard then a finisher in command combat, followed by
one field quick kill. No cast or interrupt repetition is needed. This contrast
tests actual mode flags and initial roster/status timing, rather than repeating
the same inadequate flag-only watch. Do not arm until the player is ready.
