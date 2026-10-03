---
name: sora2-effect-lookup
description: Confirm game memory identities and map observed actor, action, item, skill, and resource keys to exact Sora 2 tables. Use before implementing or reviewing an effect lookup; use sora2-meter-test for validation-only meter work.
---

# Confirm runtime identity before enrichment

Read [evidence practice](../../../docs/EFFECT-TRACE-AND-LOOKUP-PRACTICE.md), [the research workflow](../../../docs/RESEARCH-WORKFLOW.md), and [table linkage](../../../docs/TABLE-LINKAGE-AUDIT.md). Use meter-lookup for parser/integration work and effect-tracing when new live evidence is necessary.

Prove the chain: executable/table fingerprint, verified callback and field role, inline observed key/bytes, exact unique table row, persisted provenance, displayed label. Keep actor instances, status IDs, unit keys, packed skill IDs, item IDs and condition keys distinct. Pointer equality across captures, timing, amount patterns and player names do not establish a join.

Require relevant positive and negative controls. Scope a mapping to its verified callers and descriptor layout. Full SkillParam matching, generated item matching, condition-table lookup and animation-string candidates are different evidence classes; do not promote one into another. Preserve ambiguous rows, raw pointers, bytes and failed lookups.

Enemy runtime IDs are not template keys. Unique stat signatures remain provisional. Do not invent a global low-ID offset when a named craft's effect ID differs from its AI entry. Accepted animation matches can supply a visibly marked name candidate while the original native ID remains unresolved.

Direct numeric healing pairing requires the verified same-thread/target path, setter caller `+0xE4DB1` and matching requested delta. Inline R14 lookup is limited to verified callers; generic owner 65535 does not identify a support owner. Calculated after-values are not post-write reads.

Validate the complete recording-to-display path and negative/duplicate cases. Re-enrichment must preserve every raw observation and order. Keep production totals independent of research candidates. Record evidence and limits in a result document; never silently rewrite historical raw data.
