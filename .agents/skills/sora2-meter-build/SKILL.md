---
name: sora2-meter-build
description: Build the Sora 2 Details command-battle combat log and its meter projections, including capture, storage, and WPF UI. Use for implementation work in this repository; use sora2-meter-test for validation-only requests.
---

# Build the durable combat log

The [combat log](../../../docs/COMBAT-LOG-PRIORITY.md) is primary; meters derive from its ordered events. Read current code and relevant [build plan](../../../BUILD-PLAN.md) sections before treating planned architecture as implemented. Follow [the problem-solving protocol](../../../docs/PROBLEM-SOLVING-PROTOCOL.md) for defects.

Use effect-tracing and effect-lookup for native hooks and semantic changes. Read [the research workflow](../../../docs/RESEARCH-WORKFLOW.md) before integrating action-stream research. Keep `ResearchTranscript` and its candidate timeline separate from verified encounter history and meter totals. Preserve one row per raw observation, explicit gaps and unknown/future events; no-HP actions must not depend on damage writes.

For encounter events, preserve actor instances, action grouping and per-target results, raw IDs, nullable critical status, resolved versus effective amount, and provenance. Same names do not merge instances. Calculated setter outcomes are not readback. Neither damage magnitude nor the current context/result words is a general critical detector. Do not infer physical/Arts class from animation.

Keep command-battle boundaries distinct from field combat. A profile lacking boundaries cannot claim victory/escape or complete coverage. Attach-mid-battle encounters remain partial. Conditions, status parameters and timer changes are not observed effective-stat changes.

Inspect the whole capture chain: launcher, probe, bridge, atomic persistence, current-session manifest, desktop selection/refresh and cleanup. Keep source data durable outside the replaceable install directory. A hidden window, detached probe, exited helper, closed viewer and exited desktop are distinct results. Never restart or update over active capture.

Use meter-test for focused source/replay/WPF checks and meter-publish for authorized packaging/publication. Finish offline repairs and verification without approval between milestones. Ask for one prepared live contrast only after independent work is exhausted.
