# Healing attribution and ambiguous enemy lookup, 2026-09-28

The 02:54:42 command battle in the local encounter store contains nine effective
healing events. Every one has `sourceId: null` and `moveName: "Unattributed HP
write"`. The 02:54 fight also contains an unnamed main enemy, runtime ID
`60014`, whose six-stat signature matched **two** exact English `t_status`
rows. Its Broken Piece E and Guard Minion E adds matched unique rows. A second
fight at 02:57:29 similarly left main enemy `60016` ambiguous with two rows
while naming both Broken Piece E adds. Runtime IDs are battle-instance IDs,
not stable table keys.

The encounter snapshots record these observations, but their referenced raw
trace `probe-session-9cdd7363e4eb4354b300e219cfc51d90.jsonl` could not be
located during this audit. The old snapshot retained only `candidateCount`,
so the exact two candidate names for these historical fights cannot be
recovered from the snapshot. A player-reported on-screen name would identify
the historical instance, but would not prove an automatic runtime lookup.

The current `AttackEffectCall` hook verifies damaging results when paired to
the HP setter on the same thread. The HP setter reports target and before/after
HP but no verified healer, item, move, or support-proc identity. Therefore the
bridge preserves these healing events as unattributed. It must not assign the
nearest attack or prior command as the source. The bridge now leaves a pending
attack in place when an unrelated HP write occurs, so that a later matching
damage write can still be paired.

Future captures retain the observed six-stat signature and every exact table
candidate (`unitId`, `name`) on the enemy actor in encounter JSON. The HP
setter's raw JSONL record now includes 64 bytes of stack context and a frame
return **candidate**, for grouping healing paths offline. These fields are raw
research evidence only; they are not displayed as a verified source or move.

The next controlled live check needs one known ability heal and, if practical,
one random support-proc heal with user-reported actor/move/recipient. Compare
their HP setter frame context to one ordinary attack and to each other, then
trace back to a stable executed-action or effect descriptor. For the unnamed
enemy, capture its displayed name and inspect its two saved candidate keys;
seek a direct runtime unit key if both remain stat-identical. Any future
source/move join needs a second independent live validation before enabling
automatic attribution.

The probe can retain extra evidence at the HP setter before its memory changes.
For the first 16 positive HP writes per `BattleInit`, its raw JSONL record now
includes a `diagnostic_snapshot` with 256 bytes around the current stack and
frame, tagged `hp-write-without-attack-result`. This is a bounded research
snapshot; stack words are candidate pointers, not verified healer or move IDs.
Short live captures now retain the attack effect descriptor as well, so a later
`effect-descriptor-missing` or table mismatch can be reviewed against the raw
observation. If the descriptor itself cannot be read, the first eight such
results per battle also retain the bounded 512-byte result frame at the hook.
Enemy identity captures retain first-seen status/context and linked-object
bytes for each battle. The hash-gated exact English table is now loaded before
the probe attaches. If a live enemy signature matches zero or multiple unit
keys, the probe records candidate keys and a wider, bounded context/link/actor
snapshot while the attack breakpoint is paused (at most eight enemy pointers
per battle). This preserves evidence for a direct runtime key search; it does
not choose a name. A later bridge lookup result cannot safely request memory
after the breakpoint has resumed. AI-skill-ID failures still need a separate
action-context hypothesis before expanding their memory reads.

## Latest-session follow-up, 2026-09-30

The latest local trace was `probe-session-834a83dee4a249168a703c35ff7f8cbd.jsonl`; it ended with `target_exited` at 03:23:30 Central. Its latest encounter ran 03:10:17–03:19:02 and contains 119 projected events. All 11 actor instances have labels, including seven enemies with unique exact English stat-signature matches. The unresolved actor-source cases are the HP setter writes: 18 events still carry `sourceId: null` and `hp-write-without-attack-result`.

The captured stack snapshots for those HP writes share the setter path but do not contain a verified healer, move, or item ID. Repeated heal amounts and caller addresses are useful grouping clues, not attribution evidence. These events remain source-unknown. The same encounter has 21 enemy damage results whose low IDs are absent from the exact matched unit's AI `SkillTable`, plus eight derived knockout rows carrying those same lookup failures. It also has three party results using packed ID `0xFFFF05F8`, which has no exact English `t_skill` row. They remain unnamed; IDs from other monsters' scripts are not interchangeable.

Three Brute Angler results did resolve to `? Lightning Splash` through the unique `mon5244` AI row for ID 1000. The `?` remains because the actor unit key comes from the provisional stat-signature match.

## Local encounter review, 2026-10-01

The local encounter store now contains 628 snapshots, with the latest saved battle at 00:35 Central on Oct 1. Across those snapshots, 535 enemy damage/knockout results were marked `enemy-ai-skill-id-absent`. The lookup tool had only accepted `mon...` unit keys, while the same hash-checked English script archive also contains exact `ai_chr...` and `ai_rob...` files.

Joining each saved raw effect ID's low 16-bit skill ID to the AI script selected by that actor's already unique exact stat-signature unit key yields 161 single-name results across 28 unit/skill pairs. Examples include **Body-Split**, **Dead Emperor Sword**, **Abracadabra**, **Calamity Throw**, and **Donkey Missile**. Those matches remain provisional and are shown with `?` because the unit key itself comes from a stat-signature match, not a directly observed runtime unit pointer. A further 27 results have multiple script labels, 39 have only script-internal `◆` labels, and 308 have no matching per-unit `SkillTable` row; all stay unresolved.

The bridge now supports exact safe unit keys from the archive, keeps duplicate labels ambiguous, and leaves `◆` script-internal labels unresolved. This closes a lookup coverage gap for future captures. Existing encounter snapshots are not rewritten by this code change; their raw traces remain available for a later replay if desired.

A separate review of 128 results with ambiguous enemy unit keys found 11 where every exact candidate AI script agreed on the same English move label. Both Mirror Flagger variants map low IDs `1000` and `1001` to **Chariot Dasher** and **Cannon Ball**. The bridge now records a move only for this unanimous candidate case; the actor identity remains ambiguous and the move keeps the `?` marker.

The full store has 1,063 healing events without a verified source, including the newest captures. Their HP changes and stack snapshots still do not identify a healer, item, move, or passive effect. The source remains unknown; healing attribution still needs a player-confirmed control capture.

## Player-guided healing capture, 2026-10-01

A long-running read-only session was already attached when the controlled healing check began. It targeted `sora_2nd.exe` SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`, PID `37700`, module base `0x7ff7613e0000`. The raw trace is `%LOCALAPPDATA%\Sora2 Details\live\probe-session-e8abbfec45bf41e4afbf2d9149e87c2b.jsonl`. It watched `BattleInit`, `BattleEnd`, `AttackEffectCall`, and the HP setter. The HP setter took a bounded stack/frame snapshot for the first 16 positive HP writes per battle.

Live actor ID `101` resolved through exact English `t_name` to **Anelace** (`chr5101p`). The current command interval began at 14:29:14.288 Central. The player reported Estelle casting Tear on Anelace, with a displayed amount remembered as about 2,089; then using a Tear Balm without seeing its displayed amount (expected base amount 1,500); and later an Estelle support-skill proc believed to heal.

The raw HP observations for that interval were:

| Time (Central) | Target | HP before → requested | Effective HP gained | Research note |
|---|---|---:|---:|---|
| 14:33:43.500 | Anelace | 4,322 → 6,391 | 2,069 | Close to the player's approximate Tear number; likely related, but the player did not timestamp the action. |
| 14:33:44.873 | Anelace | 6,391 → 9,449 | 3,058 | Separate positive write; exact cause not reported. |
| 14:34:07.774 | Anelace | 9,449 → 11,399 | 1,950 | Separate positive write; exact cause not reported. |
| 14:34:57.945 | Anelace | 11,399 → 14,457 | 3,058 | Followed the player's Tear Balm report. The live item ID and any proc/modifier remain unknown. |
| 14:37:16.818 | Estelle | 16,851 → 20,346 (max 17,479) | 628 | The player associated the latest action with Estelle's support-skill proc. Requested HP exceeded the cap; the setter observed only 628 effective HP. |

The memory snapshots separate at least two observed code-context patterns. The 3,058 Tear Balm-adjacent write and the 628 effective support-proc write share candidate module pointers `+0xE4DB1` and `+0xE458B`; the latter lies inside the previously noted candidate shared numeric-effect helper at `+0xE4530`–`+0xE4617`. The 2,069 and 1,950 writes instead include `+0xE1A6C` and different caller candidates. These are useful stack/frame grouping clues, not verified source IDs or decoded action links. In particular, the shared `+0xE458B` pattern does not distinguish an item from a support proc.

All five effects still have `actionId: null`, `sourceId: null`, and `moveName: "Unattributed HP write"` in the bridge output. The current long-session profile does not observe `BattleCommandBegin` or the candidate numeric-effect helper entry. A next targeted probe should capture the command context, the candidate `+0xE4530` entry arguments, and HP writes in one bounded run, then repeat a player-reported heal. Keep item ID, requested amount, and effective HP change separate; the user-reported action and popup remain annotations until a live action/effect key confirms them.

A second command interval began at 14:43:10.304. It captured two more Anelace gains: **9,296 → 12,354** (+3,058 effective) at 14:43:57.326 and **12,354 → 19,999 requested** (+2,936 effective, capped at 15,290) at 14:44:19.116. Both snapshots again contain candidate pointers `+0xE4DB1` and `+0xE458B`. Their actions were not player-annotated, so retain them as unattributed healing observations.

That interval also contains four Estelle HP setter calls while she was already at maximum HP 17,479: requested values were 26,218, 31,192, 20,974, and 40,515. They produced no effective HP change and the bridge kept them as `Unknown`; their intent and cause are unresolved. The deep positive-write snapshot is not collected for a zero-effective change, so these events have less memory context than the capped +628 observation.

### Comparison against the player-guided examples, 2026-10-01

Decoded the first eight bytes at `RSP+0x20` from each of the seven positive HP-setter snapshots above. For these samples, that stack word equals `requested_hp - hp_before`, making it a strong candidate for the pre-cap HP increase passed through this setter path. It preserves the amount when the target is near full HP: Estelle's support-proc-associated write carried 3,495 before the cap allowed +628 effective HP, and the 14:44:19 Anelace write carried 7,645 before the cap allowed +2,936. The 14:43:57 write carried 3,058 and was not capped. Treat this as a validated correlation for these samples, not a universal argument definition until another controlled source is observed.

Both later Anelace writes contain the same candidate `+0xE458B` return address as the earlier Tear-Balm-adjacent +3,058 write and Estelle support-proc-associated +628 write. The two later records therefore match that shared numeric-effect path. The known Tear-associated +2,069 write instead contains `+0xE1A6C` and different caller candidates; it does not match the later helper-path signature. The repeated +3,058 amount also appears once before the Balm report, so amount plus stack pattern cannot uniquely identify the item. The +7,645 request has the same shared path but no exact match to the earlier known amounts.

Static table values do not finish the join: `t_item` lists Tear Balm/Teara Balm/Tearal Balm at 1,500/3,000/6,000, while the captured pre-cap increases were 3,058 and 7,645. The exact English `Tear` skill row is packed ID `0xFFFF0076` (skill ID 118), but no skill ID or item ID was captured alongside these HP writes. These values reject a simple exact-value match to a Balm tier; they cannot identify a modified item or distinguish an Art from a support effect. Keep the exact actions unattributed and do not infer that they are Crafts.

The lookup gap is now clearer: the HP setter exposes effective HP and a correlated pre-cap amount, but the `+0xE458B` handler is shared by the item-adjacent and support-proc examples. A bounded follow-up needs to capture the candidate `+0xE4530` helper arguments plus command/action context and the HP setter in one trace. Repeat one exact item or Art while below the HP cap, then capture a player-confirmed support proc; join a live item/skill ID only after it appears in those runtime arguments or action context.

### Repeating percentage-heal signature and level-up timing, 2026-10-01

The still-running trace contains repeated pre-cap HP increases equal to 20% of the recipient's max HP, rounded down: Estelle `3,495 / 17,479`, Anelace `3,058 / 15,290`, later Estelle `3,510 / 17,553`, and Anelace `3,073 / 15,366`. The positive-change snapshots repeatedly contain candidate return address `+0xE458B`. The player-confirmed Estelle support-proc-associated write at 14:37:16 is one of the 20% cases (`3,495` requested, `628` effective due to the cap). The unexplained Anelace +3,058 at 14:43:57 matches that amount formula and code path exactly. Additional full-HP +3,058 requests match the 20% arithmetic, but had no deep stack snapshot. This is strong evidence that these 20% writes are the same support-heal effect family. Keep the individual action label provisional because the runtime support-skill ID is still absent. In particular, the Balm-adjacent +3,058 at 14:34:57 may be a coincident support proc; it does not match Tear Balm's static 1,500 value.

The 14:44:19 Anelace write is a separate amount pattern: its pre-cap amount `7,645` is exactly 50% of max HP `15,290`, with +2,936 effective after the cap. It uses the shared numeric-effect helper path but does not match the 20% support-heal signature. Its effect family, skill/item key, and source actor remain unknown.

The user's level-up hypothesis does not fit these two mid-battle writes: the battle began at 14:43:10.304 and did not end until 14:44:41.478, while both occurred before that end and both snapshots reported Anelace max HP `15,290`. The longer trace does show later max-HP steps between fights (`15,290` to `15,366`, then `15,366` to `15,442`), consistent with the player's recollection that level-ups occur after command battles. Those later changes do not explain the earlier +3,058 or +7,645 writes.

### Focused healing profile prepared, 2026-10-01

The earlier `healing_capture` profile watched `BattleCommandBegin` plus raw turn context, the candidate action-script dispatcher at `+0x4CC190` filtered to `AniBtl` names, `HealingEffectHelper` at `+0xE4530`, and the HP setter at `+0xF8EB3`. This profile omitted `BattleInit` to fit the four hardware breakpoints. `HealingResearch` preserved its raw JSONL trace beside existing capture files.

At the time of this entry, this profile was prepared but **not yet armed**. The running capture already attached its four hardware breakpoints and could not add or replace them in place. The profile was later armed in the session below. Treat `0xE4530` as a candidate shared effect helper until its observed arguments are tied to resource writes and action keys.

### HealingResearch capture during Tear and Sacred Breath II, 2026-10-01

The later `HealingResearch` session armed at 18:20:35.505 Central against `sora_2nd.exe` PID `37700`, SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`, module base `0x7ff7613e0000`. Its raw trace is `%LOCALAPPDATA%\Sora2 Details\live\probe-session-66f7a355142b4d369c0faf2ae14f3569.jsonl`. It observed `BattleInit`, `BattleCommandBegin`, `HealingEffectHelper` (`+0xE4530`), and HP writes (`+0xF8EB3`). At review time it was still attached and had recorded through 18:23:00.050; no detach marker was present.

The player annotated this sequence: Estelle began Tear on Agate; Kevin used Sacred Breath II on Agate; Estelle's cast then resolved; a Moth Flyer damaged Estelle, followed by Kevin's support-heal proc. Exact English `t_name` joins identify actor IDs `0 = Estelle`, `5 = Agate`, and `119 = Kevin`. The capture did not decode a selected skill/item ID, so those action names remain player annotations and are not yet joined to the raw writes.

| Time (Central) | Actor | Raw HP setter observation | Interpretation |
|---|---|---|---|
| 18:22:55.636 | Kevin (119) | 41,400 / 41,400 → requested 60,030 | No effective gain is supported by the full-HP snapshot; request exceeds max. |
| 18:22:55.636 | Estelle (0) | 25,923 / 25,923 → requested 37,588 | No effective gain is supported by the full-HP snapshot; request exceeds max. |
| 18:22:55.636 | Agate (5) | 6,161 / 11,666 → requested 11,410 | Observed requested-total delta +5,249; below cap. |
| 18:22:57.254 | Agate (5) | 11,410 / 11,666 → requested 13,634 | Requested-total delta +2,224; at most +256 HP fits before the maximum. This is a pre-write request, not a post-write snapshot. |
| 18:22:58.832 | Estelle (0) | 25,923 / 25,923 → requested 23,228 | HP loss request −2,695, aligned with the player's Moth Flyer annotation. The hook does not identify the attacker. |
| 18:22:59.618 | Estelle (0) | 23,228 / 25,923 → requested 32,301 | Pre-cap request delta +9,073; at most +2,695 fits before max HP. The timing follows the player-reported Kevin support proc, but the hook does not identify its source and did not read the post-write value. |

Two helper observations do not close the action join. With the corrected register interpretation, the 18:22:55.992 hit is effect kind `6`, numeric argument `+25`, return RVA `+0x821E4`; its target pointer matches Kevin's status pointer after the simultaneous HP writes. The 18:22:58.182 hit is effect kind `6`, numeric argument `+50`, return RVA `+0x11557E`; its context (`0x1fab54e13d0`) matches the following `BattleCommandBegin.r9`, but its target pointer (`0x1fab54e1090`) is not the subsequent Estelle HP-status pointer. Neither helper hit includes a move ID or proves which resource write it produced. Preserve them as raw correlations.

### Action-name lookup path

The exact English `t_skill` rows are **Tear** `0xFFFF0076` (row 156, skill 118, animation `btlmagic.AniBtlArtsWater03`) and **Sacred Breath II** `0x00770C83` (row 367, owner 119, skill 3203, animation `AniBtlCraft03B`). The Tear animation is unique in `t_skill`. `AniBtlCraft03B` is shared by nine rows, but `(ownerId=119, animation=AniBtlCraft03B)` is unique and the exact `t_name` join maps actor 119 to Kevin. The runtime key to test is the observed script animation name plus the actor owner ID; animation name alone is insufficient for Sacred Breath II.

### Follow-up capture with Agate's Wild Rage and Estelle's Tear, 2026-10-01

The raw trace `%LOCALAPPDATA%\Sora2 Details\live\probe-session-e220ed15fbd74bc9961c613a37f47901.jsonl` armed at 19:07:13 Central against the same PID and executable hash. The player reported the opener as Agate's Wild Rage twice, then Clock Up EX on Estelle, then Estelle's Tear on Agate. Only `btlcom.AniBtlEncount` appeared at the candidate script dispatcher; it did not observe the move animation keys. Searching the captured JSON and memory snapshots found no packed or low-word key for Tear, Sacred Breath II, or the later Supreme First Aid hypothesis. This disproved the `+0x4CC190` animation-name hook as the needed selected-action lookup for these controls.

The trace correlates actor and target around the 19:09 Tear without identifying its action key. `BattleCommandBegin` at 19:08:55.716 carried Estelle's status pointer (`0x1fae1f545c8`) in the first word of its turn context. At 19:09:06.962, the HP setter observed Agate (status ID `5`, pointer `0x1fae1f55588`) at `4,668 / 11,666` with requested HP `7,529` (`+2,861`). The player confirmed Estelle's Tear on Agate had resolved by 19:09. Treat this as player-confirmed action attribution correlated to a live actor/target pair; the exact skill ID was absent. The earlier Agate HP requests went `11,666 → 8,167 → 4,668` in two `−3,499` steps, consistent with the reported double Wild Rage but not sufficient to identify its CP cost.

Static disassembly then identified the better resource observation point at `+0xF8DB0`. It is the common property setter entry; its dispatch table routes property codes `7/8`, `9/10`, and `11/12` to status value/max pairs at offsets `+0x0C/+0x10`, `+0x14/+0x18`, and `+0x1C/+0x20` respectively. The pairs are set/add branches. Existing live probes confirmed the first pair as HP; EP and CP remain to be confirmed with controlled live changes. The positive heal's captured stack also returned through `+0xE1A6C`, directly after a call at `+0xE1A67`; the revised profile now reads the effect-row pointer there, plus the generic setter and numeric helper.

The revised profile armed at 19:23:53 Central with `BattleCommandBegin`, `EffectRowApply` (`+0xE1A67`), `HealingEffectHelper` (`+0xE4530`), and `ResourceSetEntry` (`+0xF8DB0`). Raw trace: `%LOCALAPPDATA%\Sora2 Details\live\probe-session-62fbccdbcd6240c99ce6050f9acb4f17.jsonl`. It was waiting for a repeat Tear control at the time this note was written; no action result had yet been appended.

The player's likely label for Kevin's support proc is **Supreme First Aid**. The exact English `t_skill` candidate is row 223, packed ID `0xFFFF2712`, owner `65535`, skill ID `10002`, with no animation string. This static row does not identify Kevin as the runtime owner or prove it caused a heal. A scan of the previous raw trace found neither the packed key nor the low-word skill ID in its captured JSON/context fields. Check the candidate against a controlled Kevin support proc and preserve the raw runtime key before naming the heal.

Static disassembly of the exact executable shows the shared script dispatcher at RVA `0x4CC190` passes its `R8` name argument to the resolver at `0x4CC9A0`. A prior control capture saw only `btlcom.AniBtlEncount`, not move animation keys, and an exhaustive scan found neither packed action key nor low-word skill ID. Its `BattleCommandBegin` records also had a zero candidate active-command pointer. The animation-dispatch and active-command-pointer approaches therefore did not identify the selected heal; they were later replaced in the focused profile after the 20:00 cross-check.

At the time of that run, the raw-only capture proved it could observe HP setter writes but did not project them into encounter history. The current HealingResearch path starts the event bridge and displays its ActionObserved and resource rows. HealingCrossCheck remains raw-only. Selected-command identity, some status outcomes, support-heal ownership, and interrupt results remain open.

The meter displayed Error during the earlier raw-only capture because its current metadata had bridgePid=0. The bridge-status handling and launcher are now corrected: HealingResearch starts a bridge and the UI shows Capturing when that bridge is running; Raw trace means no projection bridge is active. The historical encounter files below were reprojected from their preserved JSONL.

### HealingCrossCheck with live Tear and support-CP report, 2026-10-01

The first attempt to start `HealingCrossCheck` failed before queuing because `healing_modifier_capture` was missing from the probe sender's accepted action list and duration-default list. Both lists are now registered. Re-running the same launcher path armed the profile for 300 seconds, with no request for the player to reproduce an uncontrolled support proc.

Raw trace: `%LOCALAPPDATA%\Sora2 Details\live\probe-session-ffe36b90fb334e8c8f491f02f666190c.jsonl`. The profile attached to `sora_2nd.exe` PID `37700`, SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`, module base `0x7ff7613e0000`. It watched `EffectRowApply` (`+0xE1A67`), `HealingEffectHelper` (`+0xE4530`), `CriticalPopup` (`+0x116EE0`), and `ResourceSetEntry` (`+0xF8DB0`). It armed at 19:59:42.223, disarmed at 20:04:42.241, and detached at 20:04:42.563 Central.

At 20:00:07.189, `ResourceSetEntry` observed actor 0 with property code 10, an EP-add candidate, requesting `-10` from `2,010 / 2,375`. At 20:00:07.957, `EffectRowApply` observed source actor 0 and target actor 5, amount `2,862`, result type `4`, and flags `0`; the matching HP setter requested `7,572` from Agate's `4,710 / 11,666`, an effective gain of `+2,862`. The exact actor-name table maps actor 0 to Estelle and actor 5 to Agate. This correlates the source, target, and amount. It does not contain a packed skill ID or critical-popup hit. The result flags are zero for this sample. The conversation annotation "kevin on a tear" is ambiguous against captured source actor 0 (Estelle); retain both until the annotation is clarified.

The player reported Agate's support proc for `+40 CP` around two closely spaced elevation/capture starts, then noted it may have happened on the preceding probe. The exact in-game time is not available. The 19:59:42-20:04:42 JSONL contains no code 11/12 CP setter event, no CP-related `HealingEffectHelper` hit, and no second effect-row hit. The older `HealingResearch` profile did not hook the common CP setter, so it cannot confirm or rule out a CP change. The intervening `HealingCrossCheck` did hook it and recorded Agate code 12 requests of `+90` at the `200` CP cap, not `+40`. A scan of the saved raw JSONL files found no Agate `+40` CP setter record. The support proc remains player-observed but unresolved in memory; the current and prior traces do not establish whether it fell outside a window or used a route the probes did not observe.

Static lookup found **Heat Up II** in the exact English `t_skill` payload (SHA-256 `ae81526bef7e1dedc601145961a0786df48fb1b2c96407d4571e1f3bae3bfe8a`): row 238, packed ID `0xFFFF2721`, owner `65535`, skill ID `10017`. The row has no animation or description, and its owner does not identify the runtime actor. Current player references independently fit the reported name/effect: [Kamigame's Agate page](https://kamigame.jp/soranokiseki2nd/page/414754229140379187.html) lists Agate's level 8 Heat Up II as CP `+40` plus four turns of gradual CP recovery; [Silver Intention's support list](https://silver-intention.com/sora_2nd/support-ability/) lists the same level/effect; [Raider King's review](https://raiderking.com/trails-in-the-sky-2nd-chapter-review-an-s-rank-adventure/) describes Agate's passive support as granting `+40 CP` at turn end. The exact name/effect is therefore a strong static candidate for the player's report. The packed key was absent from every saved live trace, so this remains a lookup candidate rather than a runtime-verified support identity.

The underlying join principle for support abilities is: live actor status ID -> exact `t_name` actor row; live support/effect key -> exact `t_skill` row; resource property code -> raw setter event and before/after values. `ownerId=65535` requires the live actor or support activation context to establish who used a generic support row. Because the observed proc did not appear in the CP setter stream, the next probe must first locate the support trigger/application route and correlate it with the relevant turn boundary; no repeat of a random player action is required to document the current gap.

### Helper argument and effect-row caller disassembly, 2026-10-01

Static disassembly of the exact executable hash `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF` corrected two probe assumptions. RVA `+0xE4530` is a helper entry whose switch reads `EDX` as an effect-kind code, `R8D` as the numeric argument, and `R9B` as an apply flag. Historical JSONL records stored `RDX` as `signed_delta`; that value is the effect kind, not the heal/resource amount. The raw register record also stored `R8`, so the actual numeric argument can be re-read from saved traces. New traces use `effect_kind_candidate`, `amount_argument_candidate`, and `apply_flag_candidate`.

The prior `EffectRowApply` breakpoint at `+0xE1A67` is at a call instruction to numeric-effect routine `+0xE4A60`; it captures the effect context and calculated amount, not a skill-table ID. Its saved stack-top qword is a caller-frame local at that point, not a native return address. New traces call this location `NumericEffectCall` and preserve the stack qword without return-address semantics.

The helper's observed return RVA `+0x1155FA` lands immediately after a type-4 helper call at `+0x1155F5`. That caller reads an effect-row type and candidate values, then overwrites `RCX` with the target effect context before calling the helper. The revised profile adds a breakpoint at `+0x1155D7`, before the row pointer is lost, and records the row bytes, lookup byte, target actor candidate, and amount operands. These remain candidate fields until correlated to an exact `t_skill` row or another table.

The static English lookup is already exact for the known action: Tear is `t_skill` row 156, packed ID `0xFFFF0076`, skill 118. The outstanding task is to find that key (or a different item/support key) in the live action/effect path and correlate it with the resource setter. No further random support proc is needed to justify this static lookup; one controlled Tear after the revised profile is armed can validate the direct-heal path.

### Pass-turn and Tear candidates: audit correction, 2026-10-02

The 20:42:14-20:47:14 trace `probe-session-8275256d3e7e4832b7b1cf1c7952a36a.jsonl` records Estelle's +40 CP request from 39/200, Agate's +40 CP request at 200/200, Kevin's -16 EP request and a direct numeric result pairing Kevin (119) with Agate (5) for +1,997 HP. These actor, amount and call-path observations remain supported.

The earlier analysis assigned Dauntless Courage EX, Heat Up II, Wild Rage II and Tear using later memory snapshots at the same R14 addresses. That did not prove that the earlier objects were the same immutable rows. The original trace has no inline row bytes. Those skill labels are candidate leads, not observed keys, and have been removed from its 31-row derived encounter. Raw traces are unchanged; the original projection is backed up under `%LOCALAPPDATA%\Sora2 Details\research\audit-20261002\derived-backups`.

New captures snapshot the candidate row during the callback and require a unique exact-table key-plus-parameter match. Numeric HP attribution additionally requires the verified same-thread/target call path, setter caller +0xE4DB1 and matching requested delta within 0.5 seconds. CP row naming is limited to caller +0xE1FAD with inline bytes; generic owner 65535 does not identify the support owner. These routes do not prove item healing, passive support healing, non-damaging action selection or interrupts. The no-boundary historical window remains partial with Unknown outcome and calculated resource after-values.

### Recheck of Anelace's earlier uncategorized heals

The saved encounter `live-32bedcb846fd5585a9500c282102828d` and its raw trace `probe-session-e8abbfec45bf41e4afbf2d9149e87c2b.jsonl` contain the reported writes for actor status ID `101` (Anelace). At `14:43:57.326`, HP went from `9,296` with a request of `12,354`, a `+3,058` candidate restore. This is exactly 20% of Anelace's `15,290` max HP and its stack includes the same candidate `+0xE458B` helper path as Estelle's controlled 20% support-heal-associated write. This strongly supports the same support-heal effect family, but the exact skill row and source actor were not captured, so the individual proc label remains provisional. At `14:44:19.116`, HP was `12,354` with a request of `19,999`; the `15,290` cap leaves `+2,936` effective HP from a `+7,645` request (50% max HP). That write shares a broader numeric-effect helper path, but has no unique skill/item lookup and remains unattributed. Both are unpaired positive HP writes and both occurred during the battle, before it ended at `14:44:41.478`; neither is explained by an after-battle level-up. Keep the first as a likely support-heal-family event with unknown exact skill/source, and the second as an unknown heal.
