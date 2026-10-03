# Shared action setup capture packet, October 2, 2026

This batch is complete. The [live result](ACTION-SETUP-LIVE-RESULT-20261002.md)
rejects the shared setup helper as a universal execution boundary. Do not repeat
the unchanged profile to obtain an action count.

## Missing evidence and readiness

The [offline reconciler](ACTION-STREAM-OFFLINE-RESULT-20261002.md) links the saved
queued Arts and their effects. It cannot count all actions from repeated dispatch
rows or prove the queue actor is the effect source through a captured pointer
graph. The next batch tests a newly instrumented shared setup entry. Repeating
selected controls is necessary only because earlier profiles did not watch this
entry or collect its inline linked contexts. No interrupt fight is needed.

The `Setup` profile is implemented, syntax checked and exercised in synthetic
attach/hit/detach tests. It has not been armed against the game. Verify a fresh
`armed` marker before asking the player to act; do not start it while another
capture helper is active. Keep the interval armed until the player reports the
batch finished and the saved observations have been checked, then explicitly
stop. There is no duration or hit-count cutoff. Stop once the planned
observations are durable. The player need not wait in combat for analysis.

## Exact build and hook budget

Executable SHA-256:
`D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
All four hardware slots are used:

| Hook | RVA | Evidence |
| --- | --- | --- |
| DescriptorStoreSite | +0x68E20 | Before pending write: actor and proposed descriptor bytes |
| DescriptorResumeSite | +0x69111 | Before clear: actor and pending descriptor bytes |
| ActionSetupEntry | +0x68F80 | Function entry: RCX actor, RDX descriptor, current/pending descriptors, actor+328 context, context+1D90 linked context, first linked status and entry return address |
| EffectDispatchEntry | +0xDBE40 | Descriptor, raw selector, both contexts and linked statuses |

Exact-build disassembly shows +0x68F80 consuming RDX+0x20 and RCX target fields,
and calls from +0x68F6D and +0x6911E. Unlike the earlier mid-function queue sites,
its entry stack top is a native return address. Preserve it raw and derive RVAs
using this capture's module base. Do not call this setup helper universal execution
until the controlled observations establish its multiplicity and coverage.

Launch from an authorized elevated session:

```powershell
tools/run_action_stream_probe.ps1 -TargetPid <game-pid> -CaptureFocus Setup
```

This profile saves raw JSONL under `%LOCALAPPDATA%/Sora2 Details/research/action-stream`.
It does not update the installed meter or start an encounter bridge. It replaces
the condition-return slot with setup; condition collections, resource writes,
actual stat changes and encounter outcomes are outside this profile.

## Smallest useful controls

In an ordinary command battle with a target that can survive two weak attacks:

1. The same actor uses Normal Attack on the same enemy twice on separate turns.
   This distinguishes a repeated action with reused descriptor data from repeated
   callbacks belonging to one action. Guard as needed between those turns.
2. Report one deliberate Guard and its actor. This tests a no-effect control and
   whether setup has meaningful coverage beyond damaging actions.
3. Queue one normal Art such as Kevin's Saint on a known ally, avoiding a turn
   bonus that removes cast time. Record any intervening actor/action and allow
   the Art to resolve. Compare store, setup, resume and dispatch pointer graphs.
4. Estelle uses Morale EX once, recording affected allies. This tests whether one
   immediate action's setup anchor can associate multiple recipient dispatch runs.

The exact order can follow available turns; report actor -> move -> target in
execution order and distinguish queuing from resolution. Do not force a support
proc, finish with an S-break, or find a casting enemy for this batch.

Stop after the two normal attacks, guard contrast, one queued Art and one Morale
EX have been observed and the player reports completion. Missing observations remain
unknown; do not infer a miss, interruption or cancellation from absence.

## Decision after replay

Compare the new setup actor pointer and inline linked status with both effect
contexts, keeping IDs and pointers separate. Verify setup count and ordering
against the two same-actor attacks, the guard control, queued/resumed Art and
multi-recipient Morale. If setup is repeated or excludes a control, retain it as
a scoped observation and trace its caller/state transition further. Only promote
action identity and grouping once the evidence distinguishes execution from
selection, target setup and per-target effect dispatch.
