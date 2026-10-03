# Command-battle log is the primary product

Updated 2026-09-27 after the player's scope correction. The objective is a faithful, ordered record of **every observable action and outcome in each command battle**. Damage, Healing, Taken, Deaths, and the compact meter are projections of that record. A plausible total is not evidence that the record is complete.

## Coverage contract

Capture starts at a verified command-battle entry, records the roster and starting HP/status, and ends at a verified victory, Escape, defeat, or interruption. Quick-battle actions on the field must never enter a command-battle log. Escape and re-entry are separate command intervals even if the same field enemies persist; they may later be linked as attempts of one broader fight.

Within an interval, record each executed action **once**, including actor instance, move/item ID when observed, order, and execution/cancellation state. Attach each per-target outcome to that action: damage, healing, resource changes, status/buff changes, miss/evade/guard/zero result, shield/absorption/reflection, knockout/revival, and any other effect the game exposes. Preserve multi-hit and multi-target results individually and their shared parent action. Environmental/status ticks may have no current actor; keep their origin unknown unless verified. A command with no HP write still belongs in the log.

Store raw observed IDs/codes, source and target instance keys, timestamps/order, and before/after values alongside any decoded labels. Distinguish engine-resolved amount from effective HP delta and table metadata from live evidence. An unsupported effect code must remain in the transcript as an unknown result, rather than vanish or become zero damage. If a hook, queue, or decoder can miss a class of events, mark the encounter partial with a specific coverage gap. Never label a recording complete because the enemy HP pool or meter total happened to reconcile.

## Current implementation gap

Encounter schema v2 persists separate ActionObserved, ResourceChange, Healing, HpLoss, and StateWriteObserved rows, raw effect/property keys, move lookup provenance, and enemy status-lookup candidates. The standard Live profile opens a partial encounter at the first BattleCommandBegin and records AttackEffectCall, BattleEnd, and the shared HP/EP/CP setter. HealingResearch also starts the encounter bridge and projects NumericEffectCall observations to history; it omits BattleEnd, so the result stays unknown after capture stops. A callback records only the observed effect stage, not selected-command identity or execution/cancellation state. Non-damaging action coverage, status outcomes, interrupts, misses, guards, the exact battle outcome, and some effect routes remain unresolved. The UI must show the partial-coverage gaps and must not claim full command-battle coverage.

Do not force unverified game semantics into a guessed enum just to fill this gap. Schema v2 additions preserve observed callback stages, set/add requests, calculated pre-write outcomes, raw property codes, and lookup provenance. The raw JSONL remains the source record; encounter rows are enrichments that point back to it. Future additions should keep a stable sequence and action/target relationship, raw key, observation provenance, and explicit unknown/gap records. Do not give calculated setter outcomes the same certainty as a post-write read.

## Downstream stat-change projection

After authoritative action and outcome capture is established, observe party and
enemy stats across buff/debuff application, refresh, stacking, expiration and
removal. Preserve the application event separately from stat snapshots and
derived differences. Display a verified before/after stat change when observed;
otherwise display the application alone, with an unknown stat effect. A static
buff definition is not evidence that the target's stat changed. Preserve caps,
resistance and ambiguous overlapping causes rather than attributing every nearby
change to the latest condition. This is downstream work, not a reason to defer
capture of unnamed application events.

## Work order and evidence gates

1. **Boundary and scope:** prove command-battle active state and outcome across entry, victory, Escape/re-entry, and one quick-battle negative control. Snapshot the baseline roster/HP at entry.
2. **Action stream:** find an execution-level action signal independent of HP changes. Verify one normal Attack, one support/no-damage action, one multi-target or multi-hit action, and an interrupted/missed action if available. Compare count, order, actor, and ID against player notes.
3. **Outcome stream:** identify all result application routes, not only the verified attack/HP route. Reconcile each action's target outcomes with HP/EP/CP/status writes and explicit zero/miss/guard cases; preserve unmatched raw codes and mark gaps. Verify healing, enemy damage, knockouts, revival, status effects, and reflection when available.
4. **Durable transcript:** record a representative command battle to a versioned log with per-record sequence, actor/action linkage, observed raw fields, enrichment/provenance, and explicit partial coverage. Keep the raw JSONL and the log linked. Replay must reproduce the same action/result count and order after restart.
5. **Meter projection:** derive totals, timelines, and death recaps from that transcript; prove that every projected number links back to specific log entries and that unsupported events remain visible rather than silently affecting totals.

For each test fight, maintain a coverage ledger: visible action count, captured execution count, captured per-target result count, HP/resource/status transitions, unmatched records, and dropped/unknown codes. The ledger separates **observed complete for tested event classes** from **full command-battle coverage not yet demonstrated**. A controlled battle with no missed records is necessary but not sufficient; repeat across action classes, outcomes, animation speed, and same-name enemy instances before calling the logger complete.

The [2026-09-27 live boundary and support-action probe](LIVE-LOG-GATE-20260927.md) observed two command entries, a victory end burst, a field-only negative control for watched boundary callbacks, and turn transitions around a no-HP support move. A later [action-context probe](ACTION-ID-PROBE-20260927.md) paired 19 attack results to HP writes and generated a partial damage replay, but found no verified move ID or unique action record. The next capture should identify both, plus the status/resource result of support actions. Static [table joins](TABLE-LINKAGE-AUDIT.md) can label verified IDs later; they cannot establish that every action or result was captured.
