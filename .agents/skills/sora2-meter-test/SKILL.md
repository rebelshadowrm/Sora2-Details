---
name: sora2-meter-test
description: Test or audit Sora 2 Details command-battle meter correctness, including replay totals, history, timelines, and live game capture. Use for validation, regression, or capture-feasibility requests in this repository; use sora2-meter-build for implementation work.
---

# Test the command-battle meter

The [combat log](../../../docs/COMBAT-LOG-PRIORITY.md) is the primary artifact; meter totals are projections. A test fight passes capture completeness only when action and per-target outcome counts/order reconcile with independent observations and all unsupported or dropped classes are marked. An HP-total match by itself does not pass.

Read [the build plan's validation matrix](../../../BUILD-PLAN.md) and the current tests in `tests/Sora2.Details.Checks`. For capture tests, read [the hook research handoff](../../../docs/HOOK-RESEARCH-HANDOFF.md). Separate fixture evidence from live-game evidence in the result; the current sample JSON is invented data.

## Replay and application checks

Build and run the existing checks:

```powershell
dotnet build Sora2.Details.sln -c Release
dotnet run --project tests/Sora2.Details.Checks -c Release
```

For a changed behavior, add an independent expected result, not a test that repeats the implementation. Check totals and drill-down reconciliation across Damage, Healing, Taken, and Deaths; effective HP versus resolved damage/healing when both exist; same-name actor instances; action grouping across multi-hit and AoE; unknown attribution/class; KO, revival, and repeated KO recaps; incomplete encounters and event gaps. Verify that the eleventh fight stays in full history while the quick menu shows ten. Exercise the compact WPF window at a usable size and its mode, history, row, and timeline controls when UI behavior changes.

If DPS is added, test its declared time base against paused menus and changed animation speed. A correct damage total does not by itself validate a per-second rate.

## Live capture checks

Treat the documented RVAs as hypotheses. Verify the executable hash and loaded module base, then note a controlled command battle by hand while recording observed source, move, target, HP before/after, and action order. Compare the adapter's raw events to those observations before comparing aggregate meters. Test a physical hit, an Art, a heal, a lethal hit, and an enemy HP change; repeat with multi-target/multi-hit, miss or zero damage, absorption/reflection, status damage, animation skip/acceleration, and same-name enemies where accessible. Check victory, escape, defeat, retry, and attach/disconnect boundaries. Confirm field combat does not create or pollute a command encounter.

For each candidate hook, record whether it fired, when relative to the HP write, which arguments were verified, and what remained unknown. A callback that fires is not sufficient evidence of complete capture. Reconcile HP deltas and event counts; flag mismatches and dropped events as incomplete rather than passing the fight silently.

For source names, test the pointer-to-ID-to-localized-name chain against at least two live actors, including one enemy if available; distinguish a stable actor ID from a reused memory address and preserve duplicate-name instances. For critical hits, compare a player-confirmed normal result and critical result on the same verified effect path, including the raw flag or field, paired HP write, and one ambiguous case; use unknown when the flag is not proven. Do not retroactively mark earlier hits critical from a large damage amount.

The [Agate critical control](../../../docs/DAMAGE-TYPE-AND-CRIT-20260927.md) spans two fights: his exact `0x0005003E` Normal Attack had source-context `+0x30 = 3` on reported crits and `1` on reported non-crits, all with result flag `0x42000`. A later confirmed critical Stone Hammer with a triggered follow-up had `+0x30 = 1`, just like a non-critical Stone Hammer. Test that the bridge preserves this raw context but keeps `IsCritical` null. The extra ambiguous `0x62000` Agate result must not be assigned a crit label. Trace the actual critical calculation/display decision before expanding labels.

The [post-critical Stone Hammer counterexample](../../../docs/DAMAGE-TYPE-AND-CRIT-20260927.md) has a player-confirmed non-crit ending a fight with source `+0x30 = 3` and target `+0x7C = 3`. Test that both raw words survive replay and still do not set `IsCritical`. The two earlier reported critical hits were not captured during the restart gap; do not fabricate their raw values.

The [result comparison](../../../docs/DAMAGE-TYPE-AND-CRIT-20260927.md) disproved raw `0x52000` => Arts: both Shatter Break and True Comet used it. The current bridge first joins a captured effect descriptor to a unique exact-English skill row; it then provisionally maps raw effect codes `0xC`/`0xE` to Physical and `0xF` to Arts. Test that named hits have the correct live packed ID, matching table parameters, player-reported order, and class provenance; an absent or parameter-mismatched descriptor must stay unnamed. Check that raw result flags and raw effect IDs/codes survive replay. A confirmed critical `0x42000` hit is **not** automatically marked critical; a player annotation must state its provenance.

For the four already verified party IDs, cross-check the exact-English `t_name.tbl` direct ID/name/status-key rows with `tools/name_table_index.py` and the observed status IDs. Treat duplicate table IDs and unknown enemy IDs as unresolved. The [name lookup result](../../../docs/SOURCE-NAMES-AND-CRITS.md) records the first cross-check; it does not prove every party variant or any enemy unit key.

When testing table-derived move or item labels, verify the table payload hash and the separately captured live effect ID. `t_skill` has duplicate packed IDs; require a unique ID-plus-parameter row match. The exact English enemy AI archive has per-monster `SkillTable` names, but an enemy's live instance ID is not its unit key. Require a unique stat-signature-to-unit-key match and a unique AI-script low-ID/name match; keep the provisional `?` prefix. The runtime enemy `60030` control has three exact stat candidates and must stay unnamed. `t_mon_mp0000` repeats unit keys; preserve actor instances. Treat Tear Balm's static 1,500 parameter as a comparison value, not as a substitute for a captured resolved amount or effective HP change. See [the table linkage audit](../../../docs/TABLE-LINKAGE-AUDIT.md).

Run `python tools/test_live_capture_bridge.py`, `python tools/check_table_linkage.py "C:\Games\Trails in the Sky 2nd Chapter\pac\steam\table_en.pac"`, and `python tools/test_enemy_ai_skill_index.py "C:\Games\Trails in the Sky 2nd Chapter\pac\steam\script_en.pac"` for this exact local build. These checks do not replace player validation of a newly named enemy move.

When testing the current enemy stat-signature fallback, require a unique exact table match and compare at least two different on-screen names plus two same-name instances. Change or remove one signature field to verify that ambiguous/missing matches stay unknown; test buffs and difficulty before claiming general coverage. The [current live lookup result](../../../docs/SOURCE-NAMES-AND-CRITS.md) is the baseline.

Batch planned live observations into one bounded elevation and capture window when possible. Report whether the probe was armed and detached; a canceled Windows prompt is not a negative game-data result. Respect a player request to stop repeated prompts.

## Report

State which checks passed, which failed, and which could not run because no live game state or reproducible fight was available. Give a field-availability result for encounter boundary, actor identity, human-readable name, action/move, effective amount, resolved amount, critical status, damage class, and knockout cause. Include concrete reproduction steps for failures. Do not describe fixture-only success as a validated live DPS meter.
