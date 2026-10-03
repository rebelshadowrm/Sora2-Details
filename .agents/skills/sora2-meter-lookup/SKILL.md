---
name: sora2-meter-lookup
description: Develop or audit Sora 2 Details metadata lookup from game table IDs to actor, move, and item labels. Use for table parsing, cross-table joins, and wiring verified IDs into the capture adapter; use sora2-meter-test for validation-only meter checks.
---

# Implement metadata joins without losing evidence

Read [table linkage](../../../docs/TABLE-LINKAGE-AUDIT.md), [the research workflow](../../../docs/RESEARCH-WORKFLOW.md), and effect-lookup before changing semantics. Static rows enrich observed keys; they cannot establish the runtime object or complete event coverage.

Inspect the hash-gated extractors in `tools`: name, status, skill, item, condition and enemy AI indices. Recheck the exact installed build/locale archive before extending offsets. Require full companion parameters for duplicate skill IDs. Preserve actor instance identity, raw keys, candidates, resolved/ambiguous/unknown state and lookup provenance through serialization and display.

Direct party status IDs and enemy runtime instance IDs are different namespaces. Unique six-stat enemy matches remain provisional; multiple unit keys stay unknown. A plausible AI low-ID name does not resolve a missing unit key. Do not globally shift AI skill IDs to fit a named action.

Generated item descriptors require their verified constructor/original-item fields. Condition names require exact condition keys. Animation-only lookup must stay visibly marked as a candidate and retain the unresolved native move ID; it cannot establish full SkillParam identity, class or effective amount.

UI element/category/portrait metadata is presentation evidence, not a damage or critical decoder. Keep human-readable names, templates, model keys and portraits separate. Never substitute table healing power for an observed resource result.

Test positive, missing, duplicate, parameter-mismatch and hash-mismatch cases, then the recording-to-WPF path. Reproject derived records with backups and compare all raw observations/order. Run Core checks after integration. Use effect-tracing only for the remaining live identity contrast.
