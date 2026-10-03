# Action-stream research workflow

The goal is a durable authoritative action/event stream with unknown observations
preserved, followed by progressively verified enrichment. Meter totals are a
projection; matching HP totals does not establish action or outcome coverage.

## Prepare, capture, finish offline

1. Inspect saved traces and player annotations first. Identify one unresolved
   field or contrast. Do not repeat an action that existing evidence answers.
2. Prepare a packet with executable/table fingerprints, hook locations, bounded
   reads, four hardware slots, expected raw fields, projection/viewer ownership,
   exact player controls and cleanup path. Static leads are not verified hooks.
3. Use `tools/run_action_stream_probe.ps1` manual-stop mode for player research.
   Verify the armed marker, living helpers and first committed projection in the
   viewer before declaring readiness. Transcript owns the normal app manifest and
   bridge; focused profiles need their own explicit projection/viewer ownership.
4. Keep capture armed until the player reports completion and the saved sequence
   has been inspected. Write the unique stop sentinel and verify detach and all
   owned helper exits. Completion authorizes cleanup; no keyword or further
   approval is required. No duration or hit ceiling unless explicitly requested.
   Startup/viewer readiness waits do not limit an armed research batch. Capture
   errors and game exit remain distinct outcomes.
5. Release the player from further controls. Back up derived records before
   re-enrichment, reconcile immutable raw objects and order, and verify the saved
   WPF view. Continue analysis, implementation and checks without milestone
   approvals. Request new live input only after independent work is exhausted.

See [the stop policy](LIVE-RESEARCH-STOP-POLICY.md) for the failed timed batch and
its independently tested correction. Historical packets describe their original
configuration; this workflow governs new player batches.

## Evidence classes

| Observation | Supported enrichment | Limit |
| --- | --- | --- |
| Inline full descriptor on a verified path | Unique exact SkillParam row | Scope to that caller/layout; pointer equality in later captures is insufficient |
| Generated item descriptor and original item field | Exact item identity | Static power is not observed healing; item boosts need independent attribution |
| Accepted animation with matching actor/descriptor | Unique animation name candidate | Retain unresolved native move ID; not a full skill-row identity or damage class |
| Exact condition key and complete vector | Name and before/after transition candidates | Raw parameters/timers are not effective stat deltas |
| Paired condition request/common return | Native returned record or null | Null alone does not prove immunity; preserve active-vector context |
| Paired removal and verified caller | Expiry/cure/Overdrive cause candidates | Keep failed removals and unrelated bulk cleanup distinct |
| Runtime enemy ID or unique stat signature | Instance identity or provisional name | Not a direct unit key; ambiguous template/AI joins stay unknown |
| Resource setter arguments | Requested change and calculated outcome | Not post-write/clamp readback; do not infer kills from negative setter values |

Preserve raw pointers, keys, complete bounded bytes, hashes, thread/sequence and
caller evidence. Pairing must reset at gaps. Chat order, trace time and player
annotations are separate clocks. Do not infer critical, miss, cancellation,
interrupt or support ownership from magnitude or absent resource writes. Do not
shift every AI low ID to reconcile one named craft.

## Current research and production boundary

`action_transcript_bridge.py` atomically projects complete JSONL lines into a
schema-1 research ledger. `ResearchTranscript` verifies the committed source
hash/length and one-to-one raw/timeline order. Future kinds remain unknown
observations. The viewer preserves its last valid snapshot during a malformed
update. These candidates remain separate from encounter history and meter totals.

Completed controls now cover no-HP actions, queue/resolution and an interrupt,
generated item identity, condition insertion/stacking/expiry, Curia removal,
immunity context and Overdrive cleansing. The latest enemy Diamond Dust capture
links accepted execution to three targets and supplies an animation-only name
candidate. See the dated result documents for exact evidence and limitations.

The new descriptor text-slot snapshots are bounded neutral raw fields and still
need a live named enemy craft plus known Guard contrast. Complete critical/miss
decoding, direct enemy unit keys, general support ownership, effective-stat
deltas and unified selected/executed/cancelled coverage remain open. No current
four-slot profile captures every family at once.

## Verification layers

Run standalone lifecycle and live-bridge scripts explicitly; unittest discovery
does not execute their main checks. Run focused action snapshot, reconciliation,
timeline, transcript bridge, item and host-readiness tests plus Core checks.
Run Desktop.Checks through its EXE for correct child helper mode. Ordinary WPF
shutdown checks use simulated helpers; saved-game replay proves saved evidence
and display, not a new game attachment. Package checks exercise embedded Python.
Keep installed/UAC/update, source, simulated, replay and live claims separate.

For publication, use the publish skill and verify the public workflow, release
assets and update feed. User authorization to publish persists through offline
checks, packaging, commit/tag/push and final verification.
