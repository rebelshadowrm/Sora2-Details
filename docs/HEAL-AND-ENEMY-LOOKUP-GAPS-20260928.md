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

Static table values do not finish the join: `t_item` lists Tear Balm/Teara Balm/Tearal Balm at 1,500/3,000/6,000, while the captured pre-cap increases were 3,058 and 7,645. The static `Tear` skill row identifies packed ID `0xFFFF00F6`, but no skill ID or item ID was captured alongside these HP writes. These values can reject a simple exact-value match to a Balm tier; they cannot rule out modifiers, another item, an Art, or a support effect. Keep both later events unattributed and do not infer that they are Crafts.

The lookup gap is now clearer: the HP setter exposes effective HP and a correlated pre-cap amount, but the `+0xE458B` handler is shared by the item-adjacent and support-proc examples. A bounded follow-up needs to capture the candidate `+0xE4530` helper arguments plus command/action context and the HP setter in one trace. Repeat one exact item or Art while below the HP cap, then capture a player-confirmed support proc; join a live item/skill ID only after it appears in those runtime arguments or action context.

### Repeating percentage-heal signature and level-up timing, 2026-10-01

The still-running trace contains repeated pre-cap HP increases equal to 20% of the recipient's max HP, rounded down: Estelle `3,495 / 17,479`, Anelace `3,058 / 15,290`, later Estelle `3,510 / 17,553`, and Anelace `3,073 / 15,366`. The positive-change snapshots repeatedly contain candidate return address `+0xE458B`. The player-confirmed Estelle support-proc-associated write at 14:37:16 is one of the 20% cases (`3,495` requested, `628` effective due to the cap). The unexplained Anelace +3,058 at 14:43:57 matches that amount formula and code path exactly. Additional full-HP +3,058 requests match the 20% arithmetic, but had no deep stack snapshot. This is strong evidence that these 20% writes are the same support-heal effect family. Keep the individual action label provisional because the runtime support-skill ID is still absent. In particular, the Balm-adjacent +3,058 at 14:34:57 may be a coincident support proc; it does not match Tear Balm's static 1,500 value.

The 14:44:19 Anelace write is a separate amount pattern: its pre-cap amount `7,645` is exactly 50% of max HP `15,290`, with +2,936 effective after the cap. It uses the shared helper path but does not match the 20% support-heal signature. It remains unattributed; the static item values do not identify it, and a live Arts/item/support ID was not captured.

The user's level-up hypothesis does not fit these two mid-battle writes: the battle began at 14:43:10.304 and did not end until 14:44:41.478, while both occurred before that end and both snapshots reported Anelace max HP `15,290`. The longer trace does show later max-HP steps between fights (`15,290` to `15,366`, then `15,366` to `15,442`), consistent with the player's recollection that level-ups occur after command battles. Those later changes do not explain the earlier +3,058 or +7,645 writes.

### Focused healing profile prepared, 2026-10-01

The fixed probe service now has a `healing_capture` profile with four observations in one bounded run: `BattleInit`, `BattleCommandBegin` plus its raw turn context, candidate `HealingEffectHelper` at RVA `0xE4530` plus its arguments/context, and the HP setter at RVA `0xF8EB3`. The app launcher can select `HealingResearch`; that profile runs for 30 minutes by default and preserves its raw JSONL trace beside the existing capture files.

This profile is prepared but **not yet armed**. The running capture already attached its four hardware breakpoints and cannot add or replace them in place. The earlier trace remains intact and should be used as the existing Tear, Balm-adjacent, and support-proc controls. A new run should begin only after the app is relaunched with the healing profile; then request only a fresh control that distinguishes an unresolved source, rather than replaying the old sequence by default. Treat `0xE4530` as a candidate shared effect helper until its observed arguments are tied to resource writes and action keys.
