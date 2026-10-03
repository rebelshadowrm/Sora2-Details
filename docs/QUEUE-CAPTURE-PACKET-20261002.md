# Next queue/CP buff comparison packet, October 2, 2026

Prepared from the [live condition result](ACTION-STREAM-LIVE-RESULT-20261002.md).
The profile below was implemented and tested synthetically, then used in the
[live queue comparison](QUEUE-LIVE-RESULT-20261002.md). That batch is complete;
no repeat of these controls is needed on the unchanged profile.

## Why change the observation

The player reports Saint as a queued cast and Clock Up EX as immediate. Saved
Saint snapshots show the same inline descriptor enter actor +0xC78 between two
stages, then disappear before effects. Exact-build disassembly ties a +0xC70
to +0xC78 store to the casting-animation path. Watching that write and its
resume path will distinguish stage observations more precisely than repeating
the old frame-driven callback.

All RVAs below require executable SHA-256
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
Snapshot names preserve observed memory paths; they are not execution enums.

| Hook | RVA | Observation position and raw evidence |
| --- | --- | --- |
| DescriptorStoreSite | +0x68E20 | Before `[RBX+0xC78] = R9`; snapshot actor, +C70/+C78/+C88 and proposed R9 descriptor |
| DescriptorResumeSite | +0x69111 | Before restoring arguments/clearing +C78; snapshot actor in RBP and its pending/current descriptors |
| EffectDispatchEntry | +0xDBE40 | Function entry: descriptor, raw effect selector, contexts, parameter block and stack |
| ConditionReturnSite | +0xDE962 | After one watched application call: collection, returned record, nonvolatile R14 descriptor and RSI context |

The two queue sites are mid-function. Raw stack bytes are not a verified
backtrace. A store observation is before the instruction writes; confirm its
relationship to later state rather than claiming it is an independently read
post-write value. Resume can be reached with +C78 null; it is not automatically
proof that a queued cast completed. Different cleanup/interrupt routes also
clear +C78 and are not watched by this four-slot profile.

## Available player controls and smallest batch

The player offers Saint and Kevin's similarly buffing move as a same-outcome
comparison, Forte/Sylphen Guard/Crest as ordinary queued Arts, and Estelle's
Morale as an immediate CP action with strength/CP-regeneration effects. These
are player-reported semantics until linked to observed keys and applications.

The smallest next batch is one readily available queued Art and Morale:

1. Cast Forte or Crest on one known ally; record caster, target and execution
   order. Verify descriptor store -> pending/resume observations -> effect path.
2. Use Estelle's Morale, recording whether its on-screen name is Morale or
   Morale EX and the affected party. Compare its observed route with the Art;
   absence from a watched queue route alone does not prove no queue exists.
3. Kevin's equivalent buff is optional afterward if CP/state make it convenient.
   Compare its observed condition keys with the saved Saint baseline. Do not
   require another Saint merely to obtain the baseline again.

The exact English table contains Saint `0xFFFF00C3`, Forte `0xFFFF008D`, Crest
`0xFFFF006B`, Sylphen Guard `0xFFFF009B`, Morale `0x000007D0`, Morale EX
`0x000007D1`, and Kevin's Sacrifice Arrow `0x00770C81` / Sacred Breath variants
`0x00770C82` and `0x00770C83`. It has no row literally named Sacred Arrow.
The player's offered Kevin move remains an annotation until its exact runtime
key identifies it; do not silently equate similar names or buff descriptions.
English skill payload SHA-256:
`AE81526BEF7E1DEDC601145961A0786DF48FB1B2C96407D4571E1F3BAE3BFE8A`.

Do not force a support proc or interrupt during this batch. Stop once the
queued/immediate contrast is durable and analyze offline; preserve all unknown
effects and unresolved queue records. The profile does not observe the resource
setter, so it cannot verify actual CP/EP costs or a complete CP-regeneration
outcome from metadata or player notes alone. Stat deltas remain downstream.

## Launcher and validation

Use `tools/run_action_stream_probe.ps1 -TargetPid <PID> -CaptureFocus Queue`
from an authorized elevated session. The launcher is raw-only, refuses concurrent
capture helpers, verifies the executable before attachment, writes a unique
trace under `%LOCALAPPDATA%/Sora2 Details/research/action-stream`, and prints an
stop sentinel. The launcher now runs until explicit stop with no duration or
hit-count cutoff. Read the fresh `armed` marker before requesting the controls.
This route does not start the encounter bridge or update the meter.

Six offline snapshot checks, the synthetic lifecycle check exercising both new
queue inspector flags, standalone bridge checks and PowerShell syntax checks
pass. Unknown keys, null snapshots and bounds remain serialized. Existing
Conditions focus remains available; the new queue profile is not a validated
production execution stream.

## Later interrupt control

The player will look for a suitable enemy-cast fight for future testing; not all
enemies cast. No special fight is required for the current queue comparison.
Before asking for that fight, trace and instrument explicit interruption or
cancellation state and the alternate descriptor-clear path. Then contrast a
completed enemy cast with an interrupted cast on that same path, retaining
pending actor/action identity, cause/source, and whether effects applied.
An interrupted/canceled action must remain in the ordered ledger. Missing
effects or a null pending pointer must never become an inferred interrupt.
