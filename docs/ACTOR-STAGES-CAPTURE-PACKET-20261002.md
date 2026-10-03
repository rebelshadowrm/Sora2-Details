# Actor stages capture packet

Status: captured; see [live result](ACTOR-STAGES-LIVE-RESULT-20261002.md).
The launch register defect was corrected after capture. Future snapshots use
caller-scoped saved-owner recovery. Older raw rows remain unchanged, with derived
recovery explicitly separated where the saved evidence supports it.
This is raw research; the desktop meter does not display this probe's battle.

Exact executable SHA-256:
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.

## Four observation sites

| RVA | Observation | Evidence purpose |
| --- | --- | --- |
| `0x7A68B` | Actor state callback, first update candidates | Observe handler stages even when Guard bypasses animation launch; retain unknown layouts. |
| `0x21558F` | Return from animation script queue call | Correlate native caller, owner graph, script bytes and descriptor with a preceding first handler entry. This is not independently confirmed execution. |
| `0xDBE40` | Broad effect dispatch | Preserve target/source context roles, raw selectors and descriptors; distinguish multiple recipients from multiple actions. |
| `0xF8DB0` | Resource setter entry | Preserve raw resource observations for separate caller/ownership analysis; no latest-action causality assumption. |

Registered actor handlers seen in exact-build constructor: `0x68320` main
descriptor path, `0x68DA0` preparation, `0x68F00` pending update, `0x68FF0`
resume/immediate path, `0x69570` defend path, and `0x6D230` special descriptor
path with unverified reaction/support meaning. Static native return sites
`0x686F1`, `0x68E8B`, `0x69311`, `0x69638` correlate the first four applicable
handlers with animation launch. Preparation is excluded from effect-parent links.
Unknown handlers and unmatched launches remain raw and unassigned.

## Player sequence

Use a durable enemy and report the actual execution order, including enemy turns:

1. Guard twice on the same actor, if turn order permits. This checks both ordinary
   and already-defending paths; report any support proc or counter separately.
2. Make two normal attacks with the same actor on the same enemy, if it survives.
   Report hit/miss and critical result without requiring a particular outcome.
3. Queue Saint or Forte. Have another actor Guard or attack before it resolves,
   if turn order permits. Report preparation and resolution separately.
4. Use Clock Up EX once to compare an immediate spell with the queued path.

These are boundary tests, not another attempt to infer crit or buff semantics
from names. Adapt naturally if an enemy dies; finish and report rather than
starting an unannounced second fight. Additional fights can stay in the same
capture if needed because there is no timer.

## Operator sequence

Wait for player readiness. Verify the game PID/build and absence of a competing
capture before attaching. From the inherited elevated session run:

```powershell
./tools/run_action_stream_probe.ps1 -TargetPid <game-pid> -CaptureFocus Stages
```

Confirm `attached`, manual `capture_policy`, module and `armed` markers in the
saved raw trace before requesting player actions. Do not use a duration/hit cutoff.
After the player's finished report, inspect observations for the complete stated
interval before writing the launcher's unique stop sentinel. Verify disarmed and
detached separately from game/app shutdown. Preserve the raw file and player
annotations. Replay with `tools/reconcile_action_stream.py`, exact table lookup,
and a distinct derived output path. Require evidence for repeated-state
separation, the Guard bypass, pending-versus-resume stages, source/context links,
and unknown retention before moving these candidates into production capture.
