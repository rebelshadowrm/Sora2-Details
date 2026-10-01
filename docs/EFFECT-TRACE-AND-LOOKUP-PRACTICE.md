# Effect tracing and lookup evidence practice

Use this gate for live command-battle effects, memory fields, action attribution, and any mapping from captured IDs to game-table labels. The current `+0xE4530` helper and `HpSet` snapshots are research leads; they are not yet a general healing adapter.

## Keep four identities separate

1. **Code location:** record the exact executable SHA-256, module base, RVA, hook name, and caller/return address when available. An RVA is build-specific; an absolute address is process-specific.
2. **Memory object and field:** record the pointer, field offset, raw bytes/value, and the observed role (source, target, action context, status/resource object). Keep the role `candidate` until independent runtime evidence confirms it. Pointer proximity and plausible-looking bytes do not establish identity.
3. **Runtime game key:** record actor instance IDs, action/item/skill codes, and resource IDs exactly as observed. Do not treat a status pointer, status instance ID, unit key, packed skill ID, or item ID as interchangeable.
4. **Static lookup:** record the exact archive, locale, payload hash, table/key/row, and match count. Static names and effect values enrich a captured key; they do not prove which live object or action produced it.

## Evidence states

Use explicit states in notes and log provenance:

- **Candidate:** static disassembly, guessed field, effect amount pattern, or pointer relationship only.
- **Observed:** raw value or event was read from a hash-identified live build.
- **Correlated:** the event was joined to an action, actor, target, or resource using a shared stable key and ordering evidence.
- **Verified:** a controlled positive example and a relevant negative/contrast example distinguish the proposed meaning from competing explanations.
- **Ambiguous / unknown:** evidence does not uniquely identify the meaning. Preserve the raw record and candidates; do not emit a guessed label.

Do not promote Candidate directly to Correlated or Verified because an amount matches a table value, a move name sounds plausible, or the write happened near a command.

## Capture and log contract

Before asking for another in-game action, inspect the saved trace and prior notes. Reuse existing user-confirmed actions as controls. Request a new action only when a changed hook or a missing contrast can answer a specific unresolved question. State the exact capture profile and say when it is armed before asking the player to begin.

For each raw observation retain:

- capture/session ID, local timestamp, monotonic sequence, thread, executable SHA-256, module base, hook name, RVA, registers, and bounded relevant memory snapshots;
- encounter/action IDs or explicit unknowns, source/target actor-instance keys, raw action/item/skill/effect codes, and the evidence used to correlate them;
- resource kind and the raw field semantics, before value, written/requested value, observed after value, maximum/cap when available, and effective delta;
- locale/archive/table hashes, matched table key and row, number of candidates, and lookup state;
- dropped-event, probe-limit, restart, and partial-capture markers.

Keep action execution separate from effect application. Emit an action record even when it causes no HP/EP/CP write. Emit one result per target and resource application, preserving multi-hit/multi-target parentage. Never infer a miss, cancellation, interrupt, support action, heal source, or no-effect cast from the absence of a watched HP write. Preserve raw observations append-only; store derived labels and totals as enrichments.

Do not assume a watched field is a delta or an absolute value. Confirm its semantics against before/after values and an independently reported control before computing requested or effective amounts. For HP, distinguish the engine's requested value from the capped effective change; use equivalent evidence for EP and CP rather than copying HP assumptions.

## Memory-to-lookup confirmation gate

Before wiring a memory field or lookup into capture code, provide all applicable evidence below in the research note or code review:

1. Exact executable hash and module-relative hook location.
2. Disassembly/calling-convention evidence for the observation point and the raw register/field being read.
3. A controlled live observation showing the same candidate object/field across a known actor or action, with before and after values.
4. Evidence that distinguishes source from target, actor instance from table/template identity, and the selected action from a nearby or prior command.
5. An exact table join for the observed numeric key, including locale/build hash, row, and uniqueness. If the table key was not observed live, keep the label provisional.
6. A positive control and a negative or contrasting control for the proposed meaning. For healing, contrast HP/EP/CP and command/item/support sources as relevant; percentage or repeated-amount patterns are candidate signatures only.
7. A serialized raw field and provenance path so future decoders can revise the label without rewriting the observation.

If any required distinction is missing, code should preserve the raw value and return an explicit unknown/ambiguous result. Add a verified mapping only after the evidence gate is met; do not fill gaps with inferred defaults.

## Coverage ledger for effect research

Track each feature as `hook candidate → live raw event → actor/action correlation → table join → serialized log → projection`. Mark each stage `verified`, `partial`, or `unknown` and list a concrete example. Keep separate rows for healing, non-damaging casts, interrupts, HP, EP, CP, status changes, misses/guards, and multi-target outcomes. A working HP setter proves only that setter path, not complete action or effect coverage.
