# Action and condition stream research, October 2, 2026

## Result

Tonight's [controlled capture](ACTION-STREAM-CAPTURE-PACKET-20261002.md) provides
new command-object snapshots, player annotations and a directly identified Tear
effect. It does **not** identify a universal authoritative execution stream.
The supported next step is a bounded observation of command descriptors, the
broader effect dispatcher, and condition requests plus post-call state. Names
and stat deltas follow verified runtime observations rather than driving capture.

No further live actions were requested after the batch. The probe disarmed and
detached cleanly. Unknown property writes remain in the saved 101-row partial
encounter; raw command callbacks remain in the linked JSONL. The meter's display
was not separately confirmed by the player.

## Exact-build static findings

All addresses below are RVAs for executable SHA-256
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
These findings are static candidates; none of the newly proposed hooks has been
observed in the game. Research disassembly is saved under
`.research-deps/action-stream-20261002`.

### Command descriptors

The observed state object's function-pointer table includes +0x117550,
+0x117840, +0x1179A0, +0x117C30 and +0x117E00. These callbacks read the state
index at +0xCC and its actor object at +0xF0. The +0x1179A0 entry is a candidate
later stage: its first-run branch calls +0x642A0 and subsequently reads the actor's
+0xC70 descriptor. +0x642A0 invokes a script lookup named
`OnTurnBattleCommandEnd`, reads descriptor offsets +0x84/+0x86/+0x98, and
contains move-state logic. This proves neither execution start nor cancellation.
Do not interpret a callback's name or function-table index as a game event enum.

The next snapshot captures the actor object through +0x1000 and inline descriptor
candidates at +0xC70, +0xC78 and +0xC88. Tonight's +0x400 actor snapshots did not
reach those fields. Record the raw descriptor before following its lifetime;
a later same-address read cannot supply a missing historical action identity.

### Broad effect dispatch

Following chained unwind metadata identifies +0xE17D0 as the real function entry
for the existing numeric-healing observation at +0xE1A67. A direct-call scan
finds its callers, and the related +0xE1D30 resource route's callers, in
+0xDBE40..+0xE0281. The shared +0xDBE40 function retains entry RCX/RDX/R8 in
R13/RSI/R14 and R9D as a raw dispatch selector. At +0xDBF8F..+0xDBFDA it branches
on that selector using a byte-index table at +0xE0154 and RVA table at +0xDFF64.
The function accesses an additional parameter block supplied at entry [RSP+0x28].

Capture entry contexts, descriptor bytes, raw selector, parameter block and
stack arguments. Their source/target/action relationships require live controls.
This is a broader **effect-dispatch** candidate, not automatically one callback
per executed action; zero-effect commands and cancellations may bypass it.

### Clock Up EX and applied conditions

Hash-checked English `t_skill.tbl` payload:
`AE81526BEF7E1DEDC601145961A0786DF48FB1B2C96407D4571E1F3BAE3BFE8A`.
Clock Up EX is row 193, packed key `0xFFFF00AA`. Its raw 16-byte slots at
+0x30/+0x40/+0x50/+0x60 begin with keys 96, 46, 84 and 85. La Crest has slots
96, 81, 83 and 129; Tear has slot 128. Static slot definitions do not prove that
an action applied, or which stats actually changed.

For selectors 84 and 85, the dispatch table reaches +0xDEA44 and +0xDEA6B.
Those branches set R9D to 31 and 32 and converge at +0xDE923; the call at
+0xDE95D invokes +0x7F750 with an object loaded from [R13+0x598], the R8
descriptor, and slot parameters. Keys 31/32 are **raw condition candidates**,
not decoded Speed/AT labels. The precise link between table slots and live R9D
still needs capture.

+0x7F750 reads a collection pointer/count at object +0x908/+0x910, scans records
with stride +0x48, applies checks and modifiers, and can call +0x7FE10. It can
also return zero without inserting a record. The latter routine manipulates
the collection and returns a record pointer on some paths. A request therefore
does not prove an application.

At +0xDE962, immediately after the specific +0xDE95D call, R13 still supplies
the collection owner through +0x598. Capture the collection again and full RAX
plus bounded returned bytes before the following instruction overwrites EAX.
Retain unknown/ambiguous return values. This post-call site covers the converged
branch only; other +0x7F750 callers do not have matching after snapshots here.

## Prepared next packet

The source research launcher is [run_action_stream_probe.ps1](../tools/run_action_stream_probe.ps1).
It is raw-only, does not run an encounter bridge, refuses a concurrent existing
capture helper, requires an inherited elevated session, hash-checks before
attachment and stops after 30–300 seconds or 3,000 hits. An early-stop sentinel
is printed before attachment. It has **not** been attached to the game.

| Observation | RVA | Raw evidence |
| --- | --- | --- |
| CommandStageEntry | +0x1179A0 | State/actor objects, inline +C70/+C78/+C88 descriptors |
| EffectDispatchEntry | +0xDBE40 | Contexts, descriptor, selector, parameter block, entry stack |
| ConditionRequestEntry | +0x7F750 | Raw condition key/arguments and bounded collection before request |
| ConditionReturnSite | +0xDE962 | Collection after this specific call, full RAX and candidate record |

All hits preserve observation sequence, monotonic time, local timestamp, thread,
RVA and raw registers. Collection snapshots retain the original count, bound
reads to 16 records, and flag truncation or invalid layout. Unknown selectors
and missing snapshots remain serialized. Do not drop them during later decoding.

When the player is next available, first verify armed state on this revised
profile; use one battle and stop immediately once the controls are present:

1. A normal Attack by the character who will cast Clock Up EX. This distinguishes
   the submitted descriptor and effect slots from a nearby damaging action.
2. Clock Up EX on one known ally: correlate the live descriptor and effect codes,
   then compare the condition collection before and after the candidate calls.
3. A contrasting buff such as La Crest if available: distinguish shared setup
   effects from condition-specific keys. A debuff is optional only if convenient
   and the prepared route is relevant; do not force random support activations.

Keep player notes separate from trace time. End once the contrast is durable;
decode offline. Do not wait in battle for analysis. This packet omits authoritative
boundaries, attack-result/resource-setter hooks, explicit cancellation and general
condition expiration/removal. It cannot claim full action/result coverage or
desktop display. If the command descriptor is absent or the route bypassed, trace
its writers statically and revise the packet before asking for another battle.

## Validation and next integration gate

Five offline snapshot checks cover bounded reads, invalid counts, unknown keys,
inline descriptor pointers, and the post-call preserved-register path. The
synthetic lifecycle test exercises all four new inspector flags and verifies
sequence/monotonic ordering across hardware slots and threads; bridge checks
still pass. The runtime package's dependency list includes the new snapshot
module, and packaging runs its offline checks. No installer was published.

The new raw inspector/profile is prepared, not live-validated. After the next
positive/contrast batch, add verified observations to the durable event schema
with raw trace references, explicit unknowns and provenance, keeping command
stage, effect request, accepted/application record and outcome distinct. Derive
names and downstream stat-change views only from that ledger. The future
[stat projection requirement](COMBAT-LOG-PRIORITY.md#downstream-stat-change-projection)
preserves buff/debuff application separately from observed before/after stats.
