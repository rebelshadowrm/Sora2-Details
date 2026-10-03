---
name: sora2-meter-test
description: Test or audit Sora 2 Details command-battle meter correctness, including replay totals, history, timelines, and live game capture. Use for validation, regression, or capture-feasibility requests in this repository; use sora2-meter-build for implementation work.
---

# Validate capture, replay and desktop behavior

Read [the audit protocol](../../../docs/AUDIT-AND-CAPTURE-READINESS.md), [the research workflow](../../../docs/RESEARCH-WORKFLOW.md), and relevant existing tests. Follow [problem solving](../../../docs/PROBLEM-SOLVING-PROTOCOL.md) for failures. Use build for implementation and effect-lookup before changing labels.

Build the Release solution and run Core checks. Run Desktop.Checks through its EXE so child helper mode uses the correct executable. Its ordinary seven shutdown cases use simulated helpers; saved-transcript mode validates actual WPF replay, not game attachment. `--capture-lifecycle` needs an elevated process and an already-running supported game; do not substitute a meter-only test for active-capture shutdown.

Run standalone `test_lifecycle_probe.py` and `test_live_capture_bridge.py` explicitly: unittest discovery does not execute their main checks. Run focused action snapshot, reconcile, timeline, transcript bridge, item lookup and host-readiness checks. Exact archive linkage/AI checks prove static joins, not runtime identity.

Check replay totals and drill-down consistency, effective HP changes, unknown attribution, duplicate-name instances, KO/revival, partial/gapped encounters and durable history. Exercise idle persistence, split JSONL writes, corrupt-file isolation, already-open timeline refresh, settings and X/tray cleanup when relevant.

For research replay, compare every raw object and observation order with the committed source prefix; verify its hash and length. Unknown future kinds must survive. Malformed replacement snapshots must leave the last valid view visible. Re-enrichment cannot alter raw records or promote candidate events into meter totals.

Live tests follow effect-tracing's manual-stop protocol. Use independently reported execution order and relevant contrasts, not total damage alone. Preserve player annotations separately. Critical detection, enemy unit-key attribution, misses and cancellations remain unknown unless their exact path is proved. Do not request a new battle to answer an existing trace.

Report source, synthetic, saved-game replay, packaged, installed and new live evidence separately, with concrete failures and missing fields. Inventory warnings about missing old traces are evidence limits; preserve the records. Continue independent checks and repairs until a genuine live-input dependency remains.
