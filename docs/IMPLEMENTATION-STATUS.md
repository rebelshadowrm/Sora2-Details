# Combat log and meter implementation status

Updated 2026-09-27. Scope remains **command battles only**.

Priority correction on 2026-09-27: the [advanced combat log](COMBAT-LOG-PRIORITY.md) is the product; the meter is a projection. The current effect-centric model cannot yet log an executed action with no HP change or prove coverage of misses, buffs, and other non-HP outcomes. The live research below validates partial paths only.

Current live update, 3:42 PM Central: the running partial logger now captures the result effect descriptor. Its packed skill ID and three raw fields matched exact English `t_skill` rows for the player's confirmed True Comet and Shatter Break, allowing automatic move-name lookup on uniquely matched damaging hits. The bridge provisionally maps validated row codes `0xC`/`0xE` to Physical and `0xF` to Arts. Later live hits automatically named Normal Attack, Follow-Up, Sylphen Whip II, and Jamming Ray II. Unmatched enemy effect IDs are retained raw; no-HP support actions, misses, and full outcome attribution are still absent. See [session logger](SESSION-LOGGER.md) and [table audit](TABLE-LINKAGE-AUDIT.md). Older sections below describe the earlier gates at the time they were measured.

## Implemented

- `EncounterAssembler` accepts start, effect, gap, and end messages. It deduplicates exact retransmissions, keeps event order, and marks missing sequences, inconsistent HP transitions, unknown actor IDs, and source interruption as incomplete.
- `EncounterRecorder` consumes any `ICombatCaptureSource`, saves each changed snapshot, and marks an open encounter interrupted if the source stops.
- `EncounterStore` writes each encounter to a separate JSON file using a temporary file and atomic replacement. Reopening the app restores saved history. The WPF window watches `%LOCALAPPDATA%\Sora2 Details\encounters`; sample data is shown only when that folder has no encounters.
- `CapturePipeSource` and `CaptureMessageCodec` receive version-gated local messages. A game-origin client must identify the known executable SHA-256 before it may send data; fixture-origin clients are accepted only by an explicit test receiver. The desktop runs the receiver in the background. Pipe disconnects interrupt open encounters.
- The existing Damage, Healing, Taken, Deaths, history, breakdown, and timeline UI uses the same `Encounter` model. Incomplete records show `PARTIAL` in the footer.
- Unknown-source damage to an enemy remains visible as an Unknown source row. Timelines show damage class and both displayed/resolved and effective amounts when available. Replay, pipe, version rejection, recorder, and store checks pass. These use invented fixture data and do **not** validate game capture.

## Live research gate

The running `sora_2nd` process was observed with PID 25876 on 2026-09-26. The installed executable SHA-256 was rechecked as `d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`, matching [the static handoff](HOOK-RESEARCH-HANDOFF.md). The player reported Agate at 6682/6682 HP at a command menu. A read-only `OpenProcess` request for `PROCESS_VM_READ` initially returned Windows error 5 (access denied); `PROCESS_QUERY_LIMITED_INFORMATION` succeeded. The current tool process runs at medium integrity. A user-approved elevated probe overcame this access boundary. The early single-actor HP observation is described below; later tests verified an attributed attack-result path as described in the next section. No game file was changed.

`tools/hp_memory_probe.py` can search read-only process memory for an adjacent current/max HP pair:

```powershell
python tools/hp_memory_probe.py (Get-Process sora_2nd).Id CURRENT_HP MAX_HP
```

Pause at a command menu and note one actor's displayed current/max HP. Run the probe, then observe one controlled HP change, record the new displayed value, and compare candidate addresses across the two states. A matching address must be confirmed across further changes and a battle transition before using it for a write watchpoint. The probe only finds candidate values; it does not identify attacker, target, move, damage class, or a capture-ready event. The remaining runtime sequence is in [the hook research handoff](HOOK-RESEARCH-HANDOFF.md).

The probe's full scan was checked against a synthetic adjacent current/max pair allocated in its own process; it found the expected address. With the player's approval, an elevated read-only scan of the game completed and found five distinct nearby 6682/6682 pairs (ten directional matches because current HP equals max HP). Candidate addresses were `0x16C039751D0/1D4`, `0x16C50EE5594/598`, `0x16C510F12E4/2E8`, `0x16C515256F4/6F8`, and `0x16FFC48B30C/34C`. The probe's `--read` mode checked these exact addresses after a known HP change without rescanning all memory.

### Controlled Agate HP observation

The player kept the same command battle open. After Agate took a hit, the game displayed **6601/6682**. Reading the ten candidate addresses showed that only `0x16C50EE5594` changed to 6601; `0x16C50EE5598` remained 6682. The other four pairs stayed at 6682/6682. A 50 ms read-only watcher then recorded a baseline of 6601/6682 at 19:48:09 local time and a transition to 6682/6682 at 19:48:30. The player identified the recovery as a **Tear Balm** showing **1,500** healing. Thus this battle's memory field tracks Agate's effective HP, and this recovery had **81 effective HP** versus **1,500 displayed/resolved healing** (1,419 excess). The tool did not observe the item name, user, attack source, or resolved amount; those came from the player. Neither the offset within the actor structure nor address stability across battles has been established.

`CombatEvent.ResolvedAmount` now preserves a separately observed displayed/resolved value, while the default Healing meter continues to sum `EffectiveAmount`. A focused replay test uses the 81/1,500 case. This is model validation based on one manually annotated live observation, not a working game adapter.

## Next implementation gate

The [2026-09-27 boundary and support-action test](LIVE-LOG-GATE-20260927.md) observed `BattleInit` once at each of two player-confirmed entries, a repeated `BattleEnd` burst at a confirmed victory, and no watched boundary callbacks for a player-confirmed field-only hit. A no-HP Sylphen Wing coincided with turn transitions but no candidate attack-effect call. The turn path repeated for the same actor object, so these callbacks cannot yet be emitted as one-action-per-hit log records. The final crit-triggered follow-ups in that fight were player-reported after the probe detached.

The later [action-context and attack-path probe](ACTION-ID-PROBE-20260927.md) paired 19 attack-effect calls with 19 enemy HP writes in a player-confirmed victory; effective damage reconciled exactly to two 38,825-HP enemies. The [partial research replay](../samples/research/action-id-attack-20260927.partial.json) preserves six post-knockout zero-effective results and flags four other HP writes without an attack-call partner. A controlled Agate normal Attack resolved for 5,432. Tita's Clock Up EX and Agate's La Crest were no-HP support controls. The context dump linked command callbacks to actor status pointers but did **not** yield a verified move ID or unique one-callback-per-action execution marker.

The [attributed live attack-path test](ATTRIBUTED-ATTACK-LIVE-RESULT.md) now provides a **player-confirmed, real command-battle Damage Done replay**. Thirteen source/target attack records paired with thirteen HP setter results; effective totals reconcile by Estelle, Agate, Scherazard and Tita to both enemy HP pools. A controlled Agate normal Attack recorded 10,452 damage and the player independently saw `104xx` despite the last digits being obscured. The meter displays the result in `RESEARCH / PARTIAL` mode. This verifies one damage path, not complete capture. The [all-actor HP-path test](FULL-HP-PATH-LIVE-RESULT.md) also exercises partial Taken and Healing views.

A later [source-name lookup test](SOURCE-NAMES-AND-CRITS.md) matched four party actors by observed status IDs and three live enemy instances by unique exact status-table signatures: one Emeronecider and two separate Lily Movers. This is a research lookup and is not wired into a production adapter. It does not establish a direct runtime unit-key pointer or a critical-hit flag. A time-limited elevated helper now handles planned probe requests after one administrator prompt, rather than prompting once per follow-up read.

The [lifecycle probe results](LIFECYCLE-PROBE-RESULTS.md) now include visible command-battle victories and a separately confirmed **quick-battle** attack (field combat without a command-battle transition). Candidate start/end paths fired during one victory but produced **zero hits** during quick battle. Later, the candidate `BattleStart` path did not fire in another confirmed command battle, and `BattleEnd` fired once around Escape versus a burst around victory. This is useful boundary research, not yet a production encounter detector: exact start/end state and outcome values remain unverified.

Next, locate a reliable command-battle state and outcome, then trace a selected command to a unique execution record and runtime move/item ID. Expand capture to healing, status effects, knockouts, and other HP writes, and test the attack path against quick battle. Only after those checks should a version-gated native adapter feed `EncounterRecorder` through a versioned [capture protocol](CAPTURE-PROTOCOL.md). Treat all unproven fields as unknown and emit `CaptureGap` for any loss.

The next live gate is **deduplicated command-battle lifecycle plus an action execution record**. The recorder understands `EncounterStarted` and `EncounterEnded`, but no game adapter emits them yet. `BattleInit` is a promising entry candidate in two observed fights; `BattleStart` is disproven as a universal boundary because it produced zero hits in another confirmed battle. Trace a state transition that separates command combat from the field, including Escape and re-entry, and identify the outcome value on exit. A callback name or hit count alone is insufficient evidence. The receiver must not start a fight merely because it is connected to the game.

HP addresses and status pointers have already been observed across multiple fights, including one Escape/re-entry, but they are session-specific instances rather than permanent addresses. A production adapter should derive actor identity from current game structures instead of hardcoding those pointers. The verified attack-result path must also receive a quick-battle negative control before it can be gated to command encounters.
