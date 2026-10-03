# Command descriptors and condition collections: live result, October 2, 2026

## Outcome

The revised raw-only probe observed inline descriptors for Guard, Estelle's
Normal Attack and Clock Up EX, and Kevin's Saint. Clock Up EX's effect dispatch
and condition request/return records show its target collection grow from zero
to two records with raw keys 31 and 32. Saint supplies a contrasting descriptor,
request set and collection growth. These observations establish a useful
non-damage route for further logging work; they do not establish a complete,
one-record-per-execution action stream, decoded condition names or stat changes.

The player need not repeat these controls on the unchanged profile.

## Capture identity and preservation

- Executable SHA-256: `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
- Game PID: 19224. Module base: `0x7FF745C70000`.
- Batch: `6d0faa9c57fe4f2d9e522471ce2ecf8c`.
- Armed: `2026-10-02T08:34:50.962-05:00`.
- Disarmed: `2026-10-02T08:37:58.080-05:00`.
- Detached: `2026-10-02T08:37:58.402-05:00`; probe and launcher PIDs absent afterward.
- Raw trace: `%LOCALAPPDATA%/Sora2 Details/research/action-stream/action-stream-6d0faa9c57fe4f2d9e522471ce2ecf8c.jsonl`.
- Raw SHA-256: `1CCB6BB2EF8E98053843B3D4ADC2F435615294F0818A903E968D4308D219BDC1`.

Hooks: CommandStageEntry +0x1179A0, EffectDispatchEntry +0xDBE40,
ConditionRequestEntry +0x7F750 and ConditionReturnSite +0xDE962. The trace has
782 raw hits: 604 command-stage, 165 effect-dispatch, 10 condition-request and
3 post-call observations. There is no hit-limit marker. The absence of a limit
does not prove complete coverage outside these routes.

This profile does not run the encounter bridge or project into the desktop.
These are persisted raw research observations, not a complete captured encounter
or UI validation. The original raw file remains unchanged. Batch metadata,
player annotations and a separate analysis JSON are saved beside it. All 782
hits are accounted for in analysis; unknown keys and unresolved rows are retained.

## Player controls

The player reported guarding until Estelle's turn, followed by:

1. Estelle -> Normal Attack -> Gourd Boar.
2. Estelle -> Clock Up EX -> Kevin.
3. Kevin -> Saint -> Estelle (La Crest unavailable).

The guard count and exact execution times were not reported. Chat order is an
annotation; trace sequence/timestamps are the observation clock. Gourd Boar is
player-reported and has not been joined to a verified runtime enemy unit key here.

## Descriptor evidence

The state actor's inline +0xC70 snapshot carries packed keys `0x0000003E`
(Estelle Normal Attack), `0xFFFF00AA` (Clock Up EX), and `0xFFFF00C3` (Saint).
They resolve to unique exact-English `t_skill` rows 261, 193 and 206. Guard's
`0xFFFF003F` also has a unique matching row. Enemy and unrecognized keys remain
unknown; +0xC88 bytes are not assumed to identify the current action.

English table payload SHA-256:
`AE81526BEF7E1DEDC601145961A0786DF48FB1B2C96407D4571E1F3BAE3BFE8A`.
Full byte equality across the first +0x90 bytes failed. Live offsets
+0x08..+0x0F and +0x18..+0x1F differ from static row data. For the controlled
descriptors, the remaining ranges +0x00..+0x07, +0x10..+0x17 and +0x20..+0x8F
match the respective unique row exactly. This includes the previously used
raw parameters +0x10/+0x20/+0x30. Research enrichment records both the compared
and excluded ranges. It does not assign new meanings to those differing fields,
or enable a general production label from a candidate pointer.

The reciprocal buff controls support the context roles at EffectDispatchEntry:
Clock Up EX records RCX's first linked object's raw ID 119 and RDX's first linked
object's ID 0, while Saint records 0 and 119 respectively. This matches the
reported Estelle-to-Kevin and Kevin-to-Estelle direction. Treat the interpretation
as scoped to these paths; preserve both raw pointer graphs and IDs.

## Condition requests and observed collection changes

| Sequence | Observation | Raw evidence |
| --- | --- | --- |
| 562–564 | Clock Up EX effect dispatch | Inline key `0xFFFF00AA`; selectors 96, 46, 84; linked IDs 119/0 |
| 565 | Clock Up EX condition request | Key 31; manager `0x23B37EB7310`; pre-call count 0 |
| 566 | Post-call collection | Count 1, records `[31]`; returned pointer `0x23B37EB7318` |
| 567–568 | Next dispatch/request | Selector 85; key 32; pre-call collection `[31]` |
| 569 | Post-call collection | Count 2, records `[31, 32]`; returned pointer `0x23B37EB7360` |
| 724–725 | Saint effect dispatch | Inline key `0xFFFF00C3`; selectors 96 and 92; linked IDs 0/119 |
| 726–731 | Saint condition requests | Keys 27, 28, 29, 30, 31, 32; observed pre-call collections grow from `[]` through `[27, 28, 29, 30, 31]` |
| 732 | Post-call collection | Manager `0x23B34331130`; count 6, records `[27, 28, 29, 30, 31, 32]` |
| 733–734 | Saint additional dispatch/request | Selector 57, condition key 56; pre-call collection still has six records |

No post-call snapshot for Saint key 56 exists on the watched +0xDE962 path;
do not claim that key was applied. A separate earlier key-22 request matches
Heat Up II's static descriptor fields in research, but it has no watched return
collection and no explicit player annotation. Preserve it without inventing a
support owner or completed activation.

The return pointers are consistent with the collection's +0x48 record stride.
Clock Up EX has independently read collections on both sides of each watched
call, rather than a calculated post-write count. This supports application of
two raw records on this path. It does **not** decode keys 31/32 as Speed/AT,
identify duration/modifier units or demonstrate a stat delta.

## Repeated stages are not repeated actions

The command-stage callback runs repeatedly, with its active row's +0xA0 raw
value advancing across observations. Eleven observations have that value zero;
the rest show larger values. Filtering to zero gives promising first-run stage
observations, but the single reported Saint action produces two such records,
at sequences 622 and 675, for the same actor and descriptor. Therefore neither
every callback nor every zero-valued stage can be counted as one executed action.

The normal Attack and Clock Up EX first-run observations occur at sequences 263
and 506; Saint's candidates occur at 622 and 675. The shared state object is
`0x23B29B30340`. Preserve raw stage observations, frame/phase state and descriptors
separately until transition/queue identity proves the parent relationship.
Do not silently deduplicate identical commands: two real consecutive casts can
have the same descriptor, while one cast can traverse multiple stages.

## Follow-up: instant versus queued casting

The player subsequently explained that Clock Up EX appears to have no cast
time and resolves immediately, whereas Saint has a normal queued cast sequence.
This is a mechanics annotation and a useful competing explanation for the two
Saint stages, not a runtime state label by itself.

Saved inline snapshots support that explanation:

- Saint's first zero-valued stage, sequence 622 at `08:37:15.332`, has +0xC70
  pointing at the Saint descriptor and +0xC78 null.
- At sequence 624, `08:37:15.353`, +0xC78 points at that same inline-identified
  Saint descriptor. It remains present at the second zero-valued stage, sequence
  675 at `08:37:16.067`.
- At sequence 678, `08:37:16.101`, +0xC78 is null again. Saint's effect dispatch
  then occurs at `08:37:16.622`. These are observed pointer transitions, not
  proof that clearing the pointer always means success or completion.
- Clock Up EX has no +0xC78 pointer in its observed command-stage snapshots.
  This does not rule out a transient state between watched callbacks or a
  different pending-action route.

Exact-build static disassembly provides a stronger targeted lead. At +0x68E19,
the actor's +0xC70 pointer is loaded into R9; +0x68E20 stores it at +0xC78.
The same path subsequently selects `AniBtlAria` / `AniBtlCharge` before calling
the animation route at +0x68E86. Another path at +0x690FB loads +0xC78,
conditionally restores it into +0xC70 at +0x6910E, clears +0xC78 at +0x69117,
then calls +0x68F80 at +0x6911E. Other actor paths also clear +0xC78, so a clear
alone cannot distinguish resolution, interruption, cleanup or cancellation.

The earlier broad search also found +0xC78 writes in unrelated functions;
offset equality is not object identity. Only the actor paths with the verified
adjacent object graph and instruction context are useful leads. Writer
disassembly is preserved in `.research-deps/action-stream-20261002/cast-c78-writers.txt`.

Working hypothesis: the two Saint observations represent different cast stages
that should eventually share one parent action. Preserve both observations;
do not label the second a duplicate or deduplicate by descriptor/time alone.
The next execution probe should observe the descriptor store, resume path and
alternate clears directly, comparing a queued cast with an immediate cast and
an interrupted cast when practical. Existing snapshots already answer the
current positive/contrast question; no repeat on the unchanged profile is needed.

## Next work

1. Trace the state-row resets/transition writer and command queue identity from
   saved snapshots and exact-build disassembly. Explain Saint's two first-run
   stages before adopting an execution count or action-parent algorithm.
2. Extend the ordered ledger with separate stage, dispatch, condition-request
   and observed collection-change records, raw keys, stable observation references
   and explicit unknowns. The research profile's observations must not be recast
   as complete command-battle coverage.
3. Trace general condition insertion/refresh/removal to cover callers that bypass
   +0xDE962, including the unresolved key-56 request. Decode condition names and
   duration/value units only after a verified runtime/table join.
4. Prepare a changed probe before requesting another control. Useful later
   contrasts are re-casting the same buff, a convenient debuff, and an interrupted
   cast, once the relevant queue/application/state hooks are ready.

The [downstream stat-change projection](COMBAT-LOG-PRIORITY.md#downstream-stat-change-projection)
remains separate from these raw applications. No additional live action was
needed for this batch, and the player was released from combat before analysis.
