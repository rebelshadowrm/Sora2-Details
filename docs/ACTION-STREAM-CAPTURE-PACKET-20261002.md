# Action stream discovery batch, October 2, 2026

Objective: locate an execution observation independent of damage, preserve raw
unknowns, then enrich verified runtime keys offline. This batch is discovery
evidence, not a claim that an authoritative universal stream has been found.

## Evidence and changed observation

The October 2 audit inventories 63 raw traces and 651 encounter projections.
Existing Clock Up EX and La Crest controls have no watched HP/result calls.
BattleTurnEnd repeats, the candidate active-command pointer was zero, and the
shared +0x4CC190 script dispatcher failed to reveal selected moves. Repeating
those unchanged probes would not settle execution identity.

Executable SHA-256, independently rechecked before this batch:
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.

Exact-build disassembly at +0x1175B8 shows a mid-function observation, followed
by reads of [RCX+0x328], [RDI+0x2C30], [RBX+0xF0] and the latter object's
+0x328 link. The eventual callback arguments are populated after this hook.
The revised probe preserves bounded raw RBX/RSI/RDI objects, stack bytes, and
the two consumed links inline. These are candidates, not selected commands,
actor identities, execution states, or native stack-unwind results.

## Profile and controls

Use the workspace HealingResearch launcher and bridge, one battle only:

| Hook | RVA | Observations |
| --- | --- | --- |
| BattleCommandBegin | +0x1175B8 | Existing context plus new inline raw objects/links/stack |
| AttackEffectCall | +0xE3E55 | Result descriptor and source/target snapshots |
| NumericEffectCall | +0xE1A67 | Numeric call and inline candidate skill row |
| ResourceSetEntry | +0xF8DB0 | Raw property, request, pre-write value/cap, caller |

Before entry, verify a fresh armed trace, correct game PID and living bridge.
After the first observed command, verify encounter persistence. Desktop display
requires player confirmation separately; an armed probe is not UI evidence.

1. Same character: normal Attack, then a known no-damage buff such as Clock Up
   EX or La Crest. Note actor, move, target and order after each execution.
2. Controlled direct heal on a damaged ally, if available. Note caster/recipient.
3. A multi-target action and enemy turn if convenient; avoid forcing random procs.

Stop when the contrast and heal observations are durable, or when the player
needs to leave. Do not wait in battle for decoding. This profile omits BattleEnd;
capture is partial and end outcome remains unknown unless separately annotated.
No miss/cancel/interrupt semantics may be inferred from absent writes.

## Offline work

Compare same-actor raw objects against existing controls; trace changing fields
through exact-build disassembly into the action dispatch/application routes.
Keep raw observation order and provenance durable, with unsupported codes and
unmatched writes retained. Require positive/contrast controls before naming a
field or joining it as a selected/executed action. Determine whether execution,
result application and cancellation require several streams. Add verified
semantic enrichment only after this evidence, then validate replay counts/order.

Runtime trace/session IDs, armed/disarmed times, action annotations and saved
encounter linkage must be appended after the capture; this packet is not proof
of attachment or of any live event.

## Completed batch

The workspace desktop launched HealingResearch against PID 31032, module base
`0x7FF733240000`. Request `a205c465a46145d0a71928686ca8588a`, session
`e6cedaa526cf4b40af2c639bcf402162`. The trace armed at
`2026-10-02T00:55:31.758-05:00`, disarmed at `01:01:00.640-05:00`, and detached
at `01:01:00.962-05:00`. Server/probe/bridge PIDs were absent afterward; desktop
closure was not requested or established.

Raw trace: `%LOCALAPPDATA%/Sora2 Details/live/probe-session-a205c465a46145d0a71928686ca8588a.jsonl`.
SHA-256: `CFCB87E9837EA5BFC2037D64DD9CCCB2A8D1CCD57AB25F4818DCC9F6BFF92BAB`.
It contains 9 command callbacks, 2 attack-effect calls, 98 property-setter calls
and 1 numeric-effect call, with no hit-limit marker. New inline command-object
snapshots were present. This does not establish complete coverage or no losses
outside the watched routes.

Player-reported order (chat timestamps do not establish exact event times):
Agate normal Attack; Kevin defended; enemy hit Agate, then Agate countered;
Agate consumed EP Charge II after lacking EP; Estelle cast Clock Up EX on Agate
and Kevin's arts buff proc occurred; Agate cast Clock Up EX on Estelle; Estelle
cast Tear. Preserve these as annotations, not captured item/condition identities.

Tear at `01:00:28.532-05:00` has inline packed key `0xFFFF0076`, source ID 0
(Estelle), target ID 5 (Agate), and a paired HP-set request. The bridge persists
Tear and a calculated effective HP gain of 2,957. This is not an independent
post-write HP read. Neither Clock Up EX application nor Kevin's buff activation
has a verified applied-condition key in this batch.

Encounter `live-515ced392a9457998acc1982df8432d8`, saved as
`3884022DB79596201751400528B390728F53B62C8333E66FF5A0DCA1CEE8DD62.json`,
links to this trace and contains 101 rows: 3 ActionObserved, 2 Damage,
15 ResourceChange, 80 StateWriteObserved, and 1 Healing. Desktop display remains
unconfirmed by the player; durable persistence and display are distinct claims.

Research artifacts in `.research-deps/action-stream-20261002` retain player
annotations, candidate command-state comparisons, exact-build disassembly and
capture hashes/markers. The inline state object contains a function-pointer
table with candidates +0x117550, +0x117840, +0x1179A0, +0x117C30, +0x117E00.
The observed command-stage index at +0xCC was zero in the inspected callbacks;
RSI was also zero. These are observed raw values, not execution/cancellation
semantics. No packed Clock Up EX key was found in the inspected command blobs.
Follow the table's state transitions and the actor's +0xC78 linked-object read
statically before choosing a new execution/condition hook. The latter pointer
was not captured live; it remains a disassembly lead.

Synthetic lifecycle attach/hit/detach, bridge and core checks passed. The normal
Release build encountered DLL locks because the workspace desktop was running;
a Release build with a separate artifacts directory passed with zero warnings
and errors. This build check did not restart or interrupt capture.

Next live gate: prepare a new candidate execution/status-application observation
first, then compare a known buff with a no-buff control and an accessible debuff
if its route is relevant. Do not ask for more actions on the unchanged four hooks
solely to name buffs or prove their application.
