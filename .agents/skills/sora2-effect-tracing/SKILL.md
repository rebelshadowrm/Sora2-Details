---
name: sora2-effect-tracing
description: Plan and capture live command-battle effects from action execution through resource or status outcomes, including healing, no-damage casts, interrupts, HP, EP, and CP. Use for live probes, raw event correlation, and effect-log coverage; use sora2-meter-lookup for table-join implementation.
---

# Trace action and effect observations

Read [the research workflow](../../../docs/RESEARCH-WORKFLOW.md), [evidence practice](../../../docs/EFFECT-TRACE-AND-LOOKUP-PRACTICE.md), and the relevant capture packet before changing hooks. Use effect-lookup when interpreting keys.

Finish saved-trace analysis before requesting live controls. Prepare the exact executable hash, four-slot hook budget, bounded memory reads, raw fields, missing contrast, projection path, and cleanup ownership. Pick the smallest sequence that distinguishes the remaining hypotheses; do not repeat controls already answered by saved evidence.

Use `tools/run_action_stream_probe.ps1` in manual-stop mode for player research. Verify the raw armed marker, helper PIDs, first committed projection and viewer before announcing readiness. Keep capture armed through the player's completion report and inspection of the saved sequence, then write its sentinel and verify detach and helper exit. No duration/hit cutoff, special keyword, or additional stop approval. Genuine capture errors and game exit are separate outcomes. Continue offline analysis autonomously afterward.

`Transcript` registers an app-owned session and starts the research bridge. Focused profiles require explicit projection/viewer ownership; a raw launcher alone is not proof of display. `HealingResearch` projects partial encounter history; `HealingCrossCheck` is raw-only. Preserve these distinctions.

Persist one observation for every raw record, including unknown kinds and failed calls. Keep action execution, queued/resumed descriptors, effect dispatches, resource setters, condition requests/returns, and outcomes separate. Correlate only on verified path, thread, actor/target and inline descriptor evidence. Reset pending links across gaps. Chat order, player annotations and trace timestamps are independent evidence.

Disassemble the exact hash before interpreting registers, frame offsets or caller RVAs. Mid-function stack values are not automatically return addresses. Capture complete inline bytes while paused; later reads of the same pointer do not prove identity or lifetime. Missing writes cannot prove a miss, interrupt or immunity.

After completion, back up derived records, reproject from immutable raw data, reconcile observation count/order and inspect the WPF view. Report positive evidence, unresolved attribution and the one next missing control. Downstream effective-stat deltas require runtime before/after reads; table values and condition parameters alone are insufficient.
