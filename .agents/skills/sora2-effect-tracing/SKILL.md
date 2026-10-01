---
name: sora2-effect-tracing
description: Plan and capture live command-battle effects from action execution through resource or status outcomes, including healing, no-damage casts, interrupts, HP, EP, and CP. Use for live probes, raw event correlation, and effect-log coverage; use sora2-meter-lookup for table-join implementation.
---

# Trace game effects into the log

Work in Sora2-Details. Follow the required [effect tracing and lookup evidence practice](../../../docs/EFFECT-TRACE-AND-LOOKUP-PRACTICE.md) and the [combat log coverage contract](../../../docs/COMBAT-LOG-PRIORITY.md). Read [the capture protocol](../../../docs/CAPTURE-PROTOCOL.md) and relevant entries in [the hook research handoff](../../../docs/HOOK-RESEARCH-HANDOFF.md) before changing a live profile.

When a user reports a capture or logging defect, follow the [problem-solving protocol](../../../docs/PROBLEM-SOLVING-PROTOCOL.md). Trace the failing mode end to end, use saved traces first, and do not confuse helper detach with desktop-app exit.

Before requesting an in-game action, inspect all saved traces and user-confirmed controls. State the missing evidence, the exact profile/hooks that will collect it, and verify the trace reports `armed`. Do not ask the player to repeat an action that the existing trace can answer. After a probe/profile change, ask only for a control needed to distinguish the remaining hypotheses.

Keep raw observation and semantic interpretation separate. Correlate command/action entry to each effect and resource write with stable IDs and sequence evidence; preserve source, target, amount, and action as unknown where unresolved. A resource write does not prove which command caused it, and absence of a write does not prove an action was a miss, canceled, interrupted, or harmless.

Use a coverage ledger with one row per effect class: hook candidate, observed raw event, actor/action correlation, table lookup, persisted record, and displayed projection. Include healing sources, no-HP actions, interrupts, HP/EP/CP changes, status outcomes, and multi-target effects. Mark tested classes and remaining gaps explicitly. Preserve the exact executable fingerprint, trace path, start/stop evidence, and any capture gaps.

When a raw action, actor, item, skill, or resource key needs a table join, hand off to [sora2-effect-lookup](../sora2-effect-lookup/SKILL.md). Do not wire a candidate pointer, amount pattern, or table value into the production event label.
