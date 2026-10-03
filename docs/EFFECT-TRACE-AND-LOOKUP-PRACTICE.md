# Effect tracing and lookup evidence practice

Use this gate for live command-battle events, memory fields, action attribution, and any mapping from captured IDs to game-table labels. The standard live profile uses `BattleCommandBegin` to open an encounter at the first observed command callback and watches the shared `+0xF8DB0` resource setter so HP, EP, and CP requests enter the same event path. A mid-battle attach therefore produces a partial encounter from the next command callback, without earlier actions or entry state. `+0xE4530` and the healing-only profile remain research routes, not general action-start hooks.

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

## Feature plan and lookup keys

The lookup chain is: live actor status ID → exact English `t_name`; live packed skill ID → exact `t_skill` row; live item ID → exact `t_item` row; live resource-property or condition key → its runtime field/table. Keep the raw key and lookup match count with every projected name. An animation label or player annotation can guide a test, but does not substitute for observing the runtime key.

| Feature | Runtime lookup principle | Current evidence / next control |
| --- | --- | --- |
| Damage, AoE, Burst follow-ups | Read the packed skill ID and companion raw parameters from the result descriptor; join all fields to a unique `t_skill` row. Keep a parent action and one result per target/hit. | The `+0xE3E55` attack-result path already joins controlled True Comet and Shatter Break to exact rows. Burst parent/child grouping and full multi-target coverage remain partial. |
| HP, EP (MP), and CP changes | Hook the common status-property setter at `+0xF8DB0`; retain actor ID, property code, requested value, before/max fields, and caller. Static dispatch maps codes `7/8` to status offsets `+0x0C/+0x10`, `9/10` to `+0x14/+0x18`, and `11/12` to `+0x1C/+0x20` (set/add pairs). | The Oct. 1 trace records Kevin's EP request of `-16`, Agate's `+1,997 HP`, and two CP `+40` requests. Later same-address snapshots suggest `Dauntless Courage EX` and `Heat Up II`, but the older trace lacks inline row bytes and those names remain candidates. Agate began at `200/200`; the setter request therefore projects to no CP gain. The production profile now captures all six resource properties. |
| Healing source and amount | Correlate a selected skill/item action key to each HP property write; keep requested total, capped/effective delta, and post-write value distinct. Join skills through t_skill and items through t_item. | The player annotated Kevin's Tear; the verified NumericEffectCall/HP path pairs Kevin (119) with Agate (5) for +1,997. Tear is static row 156 / packed ID 0xFFFF0076 / skill 118, but this older trace omitted the row bytes and cannot establish its live key. The current HealingResearch bridge writes both the observed effect call and the paired healing row to encounter history. Names are emitted only from inline row bytes with a unique exact-table match; later same-address snapshots cannot supply authoritative labels. Tear Balm remains without a live item key; support heals remain open. |
| Support healing | Capture the passive/effect key at the effect caller and resource setter; identify the source actor separately. Let a naturally occurring proc provide the positive control when the player cannot trigger it on demand. | Kevin's likely label is **Supreme First Aid**, static candidate `0xFFFF2712` / skill 10002, row 223. No live support-heal row has been captured; keep this unknown and use a passive capture window rather than asking the player to force a random proc. |
| Support CP effects | Capture the triggering support key and recipient at the CP setter. Keep direct CP gain separate from gradual recovery ticks, and keep recipient distinct from support owner. | Later snapshots suggest these candidate names for the user's two pre-Tear `+40` requests: `Dauntless Courage EX`, `0xFFFF2717` / skill 10007 / row 228 on Estelle, and `Heat Up II`, `0xFFFF2721` / skill 10017 / row 238 on Agate. Agate's request was capped at `200/200`; its candidate effective gain is zero. Both rows have generic owner 65535, so source ownership remains unknown. |
| Non-damaging casts and status effects | Capture the executed action key independently of resource writes; record raw condition/property IDs and state before/after; identify the exact condition table and unique row from the game archive before naming a status. | Clock Up EX (0xFFFF00AA, skill 170) is a player-reported control and a static t_skill candidate, not yet a live selected-action join. HealingResearch now projects each observed NumericEffectCall as ActionObserved and joins the exact R14 row where present. This observes an effect call, not selected-command identity or proven application. No applied-condition key is available yet. |
| Interrupts and cancelled actions | Capture the targeted action key, actor/target, queued action state, and explicit interrupt/cancel result. Compare a known interrupt with the same enemy action allowed to complete. Do not infer an interrupt from a missing damage result. | No validated interrupt-result field exists yet. First identify a safe enemy command that can be interrupted and inspect command-state/result callbacks around both outcomes. |
| Resource costs and Burst CP | Link every CP setter event to its action parent/child and separately record costs, gain effects, support actions, and follow-ups. Reconcile the whole CP sequence rather than attributing a final total to Burst alone. | The current trace contains the two support CP requests and Kevin's EP cost, but no Burst control. The live logger now records all CP property writes; action parentage and Burst/follow-up grouping are still open. |

Use one prepared capture batch for the controllable checks: Estelle Tear on a damaged ally, Kevin Sacred Breath II on a damaged ally, Clock Up EX with no HP change, a known enemy move interrupted and then allowed to resolve, and a Burst with CP values recorded around it. Include a passive window for random support heals and CP procs. The player can leave the battle when the capture stops; process all trace and table joins afterward. Only promote an action label when the live key joins uniquely to the exact-build table row.

## Event-ledger behavior and batch-capture procedure

The standard Live logger writes ActionObserved for AttackEffectCall, resource outcomes for property codes 7?12, and StateWriteObserved for other raw property-setter codes. HealingResearch also writes ActionObserved for NumericEffectCall and shares its actionId with a uniquely paired same-thread, same-target HP restoration. A paired HP damage result shares its actionId with the AttackEffectCall. Unpaired calls remain visible with their raw key and lookup result; they are not relabeled as a miss, interrupt, or harmless cast. Resource writes preserve the raw set/add operation, requested value, pre-write value, cap, and a separately marked calculated result. The calculation is not an independent post-write read.

The bounded HealingResearch profile is the broad one-battle event batch. Its four breakpoints are BattleCommandBegin +0x1175B8 (raw turn context), AttackEffectCall +0xE3E55 (effect descriptor and actor data), NumericEffectCall +0xE1A67 (numeric effect and candidate skill row), and ResourceSetEntry +0xF8DB0 (HP/EP/CP and other property writes). The launcher starts the bridge, so these observations are projected into history while the status reads Capturing. It omits BattleEnd; after detach the result remains Unknown unless explicitly supplied by the player, and the encounter stays partial. Stop after the planned events are present rather than leaving this profile running across multiple battles. It does not prove selected-command identity or detect an interrupt by absence of a result.

At the shared setter, exact caller RVA +0xE1FAD plus its captured R14 row is a verified lookup route for the two observed CP support rows. The result's recipient comes from the status pointer; ownerId=65535 means the row alone does not identify the support owner. Older traces stored an absolute caller address and R14 pointer without row bytes. Do not assign labels from later snapshots at the same address: neither row identity nor immutable lifetime is proven. Preserve those snapshots as candidate research; require inline row bytes for a label. Direct Tear's key uses NumericEffectCall +0xE1A67 and is now projected by HealingResearch; standard Live still does not include that hook.

For an enemy move, the durable reference is the observed source runtime status ID plus the raw packed effect ID. The packed key's high half must match that runtime ID; use the low half with the uniquely identified enemy unit's exact English AI script. If status stats match multiple unit rows, keep the candidate list and raw effect key; the player does not need to know the enemy skill name in advance. The logger's provisional enemy names retain a `?` prefix and lookup provenance.

Before the next live test, finish the lookup/parser review from saved traces and prepare one capture packet containing the exact executable hash, hook list, target actions, expected raw fields, lookup inputs, and stop condition. Collect the controllable checks and passive support window in one armed interval where the hook budget allows; stop capture as soon as the needed raw events are present. Let the player leave the battle before doing table joins and event reconciliation. If a hook gap still requires another capture, name that gap and the precise contrast it will resolve before asking for another in-game setup. Do not make the player wait in a battle while analysis runs.

The exact-build disassembly distinguishes the helper's arguments: at `+0xE4530`, `EDX` is an effect-kind code, `R8D` is the numeric argument, and `R9B` is a flag consumed by the helper. The earlier probe field `signed_delta` was therefore misnamed; use `effect_kind_candidate`, `amount_argument_candidate`, and `apply_flag_candidate` for new captures. The old `+0xE1A67` breakpoint is at a call site for the numeric-effect routine `+0xE4A60`, not at a function carrying a packed skill ID. Keep its stack-top value raw; it is not a caller return address.

For the hash-identified Oct. 1 executable, live controls found a callsite-specific lookup route: `R14` points to a candidate `t_skill` row at `NumericEffectCall` `+0xE1A67` and at `ResourceSetEntry` when its caller is `+0xE1FAD`. Snapshot the pointer and complete `0xB0` row while the process is paused; join its first `u32` through exact-build English `t_skill`. Later snapshots make Tear and the two CP rows plausible candidates. New records must capture row bytes inline to establish each exact key. Treat the route as limited to these call paths; do not assume other helper, item, support-heal, non-damaging, or interrupt paths use `R14`.

## Audit correction, 2026-10-02

Cross-trace row labels have been removed from the bridge and the 31-row historical projection. Its raw trace is unchanged; the original derived record is backed up. Direct numeric HP pairing requires the verified setter caller +0xE4DB1, same thread/target, at most 0.5 seconds and matching requested delta. Resource after-values remain calculated. See [the audit protocol](AUDIT-AND-CAPTURE-READINESS.md) for checks and readiness gates.
