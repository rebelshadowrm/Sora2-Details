---
name: sora2-effect-lookup
description: Confirm game memory identities and map observed actor, action, item, skill, and resource keys to exact Sora 2 tables. Use before implementing or reviewing an effect lookup; use sora2-meter-test for validation-only meter work.
---

# Confirm memory identity before lookup

Follow the required [effect tracing and lookup evidence practice](../../../docs/EFFECT-TRACE-AND-LOOKUP-PRACTICE.md). Read the [table linkage audit](../../../docs/TABLE-LINKAGE-AUDIT.md), plus [source-name research](../../../docs/SOURCE-NAMES-AND-CRITS.md) when actor identity is involved. Use [sora2-meter-lookup](../sora2-meter-lookup/SKILL.md) for existing table parser conventions and the [hook research handoff](../../../docs/HOOK-RESEARCH-HANDOFF.md) for executable-specific locations.

Establish the evidence chain in order: exact executable hash and module-relative code location → raw pointer/field and its runtime role → stable observed actor/action/resource key → exact locale/build table row → serialized provenance and user-visible label. Keep memory addresses, runtime instance IDs, template/unit keys, packed action IDs, item IDs, and table row IDs as separate fields unless a verified join proves their relationship.

Before adding a semantic mapping, verify the field meaning and calling convention, capture a controlled live value change, distinguish source from target and current action from nearby commands, and prove the static join is exact and unique. Use a positive example and a relevant negative/contrast example. Amounts, names, pointer proximity, and timing alone are not confirmation. Preserve the raw values and lookup candidates when evidence is incomplete; return explicit `unknown` or `ambiguous` rather than a guessed label.

Review the code path that records the raw key, performs the table join, serializes provenance, and presents the label. Confirm that unknowns remain representable and that a mapping change does not rewrite the raw event. Record the capture path and evidence note in the code review or research document. Use [sora2-effect-tracing](../sora2-effect-tracing/SKILL.md) when the missing evidence requires another live capture.
