# Live event-ledger verification packet, 2026-10-01

## Armed session

- App: Release build from this workspace; `dotnet build Sora2.Details.sln -c Release` succeeded with no warnings or errors. Existing replay, projection, recorder, and persistence checks passed.
- Game: `sora_2nd.exe`, SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
- Capture profile: standard `Live`; armed at `2026-10-01T22:12:03.191-05:00`.
- Session/request: `9fe78cac828c4e679bdaa025fa39a93c` / `faa773f9470342869bd86dc7ef6ae614`.
- Raw trace: `%LOCALAPPDATA%\Sora2 Details\live\probe-session-faa773f9470342869bd86dc7ef6ae614.jsonl`.
- Hooks: `BattleInit +0xC2750`, `BattleEnd +0xBA659`, `AttackEffectCall +0xE3E55`, `ResourceSetEntry +0xF8DB0`.

## Action batch

Use one command battle and capture a small, known sequence:

1. Let Estelle and Agate pass/block turns if needed to reproduce the previously observed support CP requests; record recipients and any visible CP change.
2. Have Kevin cast Tear on a damaged ally.
3. Use one ordinary attack and observe one enemy action, to check action/effect and per-target HP pairing in both directions.
4. If practical in that battle, cast Clock Up EX or another known no-HP action. Its absence from this profile cannot establish that it was not executed; the test only checks whether an observed callback is emitted.
5. Finish or leave the command battle once these events are captured. Stop the probe promptly afterward so analysis can happen outside combat.

An S-Craft/Burst is optional if CP and the battle state make it convenient. Do not wait in battle to force a random support heal or interruption; existing traces already establish useful controls, and those classes need a different explicit action-state hook.

## Expected fields and limits

The raw trace should preserve timestamps, thread IDs, actor status pointers/IDs, attack-effect descriptor and candidate amount, resource property code, set/add request, pre-write value, maximum, setter caller, and the CP-path `R14` row when its verified caller is present. The bridge should save an ordered partial encounter with action-effect observations and HP/EP/CP/property rows. After-values remain calculated candidates unless separately read.

At the time of this session, Live did not include NumericEffectCall or BattleCommandBegin. The recovered trace could verify attacks and HP/EP/CP writes, but not direct Tear key identity or command selection. The current standard Live profile now uses BattleCommandBegin, BattleEnd, AttackEffectCall, and ResourceSetEntry. The HealingResearch profile adds NumericEffectCall and starts the encounter bridge; it still omits BattleEnd.

## Result and projection repair

The player-reported command sequence ended in victory at about `22:22:29-05:00`. The saved trace is intact, but it contains no `BattleInit` or `BattleCommandBegin`: it has 8 `AttackEffectCall`, 75 `ResourceSetEntry`, and 72 repeated `BattleEnd` callbacks. The bridge waited for `BattleInit`, so it wrote no encounter. After detach, the desktop's follow-newest path also selected null when `ActiveTraceName()` became null, even if an encounter file existed. These were separate causes of an empty meter.

The bridge now opens a clearly partial live encounter at the first `BattleCommandBegin`; that hook replaces `BattleInit` in the four-slot standard profile, with `BattleEnd`, `AttackEffectCall`, and `ResourceSetEntry` retained. A capture attached mid-battle will join at the next command callback, and the UI marks earlier actions and entry state as missing. An opt-in `--recover-first-attack` mode is limited to offline recovery of a user-confirmed older trace.

Offline recovery created encounter live-399949f16ea55020b284b29eb1d0df7f from the intact trace. It contains 83 rows: 8 ActionObserved, 8 paired Damage, 30 ResourceChange, 36 StateWriteObserved, and one unattributed Healing. The user-reported Victory is now recorded as player-confirmed, while isComplete remains false because the raw BattleEnd outcome code is undecoded. The resolved action names include Estelle's Normal Attack and Chain, Kevin's Follow-Up, and Agate's Normal Attack. At 22:17:59.184, Agate's Heat Up II row requested +40 CP while already at 200/200, so the calculated effective gain is zero. The 22:19:54.803 restoration is 5,952 HP to enemy instance 60029 (27,700 -> 33,652); its source and action remain unknown. Player-reported critical labels remain annotations; captured critical state is null.

The later Agate-opening report lacks a timestamp that can be aligned confidently to an armed interval. No saved raw window has been confidently identified for the full reported sequence. Chat order alone cannot prove it occurred after capture stopped. The 22:50:32 Live attempt failed before attachment with access denied and captured no game callbacks, but this does not prove it caused that particular missing UI sequence. The failed raw trace is preserved.

The failed attempt's current.json record remains stale, but its result is failed and its trace has neither attached nor armed. The updated capture-state cleanup recognizes that case as safely finished and the next launcher run can clear the stale metadata once all helper PIDs are gone.

## Additional saved trace recovery and UI projection

The 20:42:14-20:47:14 trace (probe-session-8275256d3e7e4832b7b1cf1c7952a36a.jsonl) had no battle-entry, command-begin, or BattleEnd hook. Offline recovery starts at its first resource setter and marks the record as an Observed event window, not a complete encounter.

The recovered encounter contains 31 rows: CP requests, Kevin's EP request, one numeric effect observation and the paired Kevin-to-Agate +1,997 HP restoration. Previously assigned skill names from later same-address R14 snapshots have been removed because historical row identity was not proven. Actor and amount observations remain; missing inline row bytes produce unknown names. Raw traces are unchanged and the original derived record is backed up. Resource after-values are calculated candidates.

The HealingResearch launcher starts the bridge after the probe arms. Updated desktop projection, open timeline refresh and both exit routes passed actual WPF checks on Oct 2 using simulated helpers. This does not establish game attachment or the reported Agate-opening sequence. Its capture timing remains unknown; one prepared game batch must establish armed probe, bridge, saved encounter and displayed log. HealingCrossCheck remains raw-only.

## Audit correction, 2026-10-02

The numeric and CP labels previously recovered from later same-address R14 snapshots are candidates only and have been removed from the old 31-row projection. Require inline row bytes for authoritative labels. The audit also verified open-timeline refresh and both desktop exit routes with simulated helpers, and fixed idle bridge persistence. See [the current audit](PROJECT-AUDIT-20261002.md) and [lookup practice](EFFECT-TRACE-AND-LOOKUP-PRACTICE.md).
