# All-actor HP-path command-battle test

Observed 2026-09-26 on the same running `sora_2nd.exe` SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`, PID 25876, module base `0x7FF6807D0000`. The [raw trace](../samples/research/full-hp-path-20260926.jsonl) was armed at 21:34:27.522 local time and detached at 21:39:27.914; the game remained responsive. The player entered a **command battle from the field**, reported **no quick-battle hits before entry**, fought **two enemies**, and confirmed a **victory**.

The probe watched the HP-setting branch at RVA `0xF8EB3`, the Agate HP field, and candidate battle start/end paths. It recorded **19 HP-setter calls** across five actor pointers, **19 `BattleEnd` hits** in a burst at 21:35:33, and **zero `BattleStart` hits**. Thus the candidate start hook is not reliable as an automatic gate in this path. The battle interval in this report is manually bounded by the armed window and the player-confirmed command battle; the end burst supports the visible victory but does not expose an outcome value.

At RVA `0xF8EB3`, disassembly and live registers show a status pointer in `rsi`, current HP at `rsi+0xC`, maximum HP at `rsi+0x10`, and a requested new HP value in `r14d`. The code clamps that request to `[0, max HP]` before writing current HP. Agate's independent write watchpoint matched all four changed setter results for his pointer; a fifth post-result write left HP unchanged. The other pointers' after-values are derived from the observed request and clamp, and each subsequent setter's before-value reconciles with the prior after-value. Final zero values for the two enemy pointers are consistent with the visible victory, but there is no independent write watchpoint for them.

| Actor mapping | Setter calls | Effective HP lost | Effective HP gained | Evidence |
| --- | ---: | ---: | ---: | --- |
| Enemy 1 (`28,840` max HP) | 6 | 28,840 | 0 | Separate status pointer; reached zero. Name unknown. |
| Enemy 2 (`28,840` max HP) | 4 | 28,840 | 0 | Separate status pointer; reached zero. Name unknown. |
| Agate (`6,682` max HP) | 4 | 2,024 | 1,002 | Max HP and four writes independently cross-checked. |
| Tita (`6,904` max HP) | 4 | 89 | 41 | Player confirmed 6,904 max HP and 6,856 current HP after fight, matching final setter value. |
| Scherazard (`5,973` max HP) | 1 | 0 | 0 | Player confirmed max HP; one setter request was clamped to no HP change. |

Estelle was in the party but had no observed HP-setter call, so no status pointer was assigned to her. The player supplied party names/max HP and confirmed two enemies; the pointer-to-team mapping is still research evidence, not a decoded game roster. The [actor map](../samples/research/command-hp-actor-map-20260926.json) records this provisional mapping.

The [partial research replay](../samples/research/full-hp-path-20260926.partial.json) contains the **18 changed HP-setter results**. In the desktop meter's **RESEARCH** mode it shows:

| Meter | Observed effective total | Attribution |
| --- | ---: | --- |
| Damage Done | 57,680 | Unknown party source, across two enemy HP instances. |
| Damage Taken | 2,113 | Other / unknown source, across Agate and Tita. |
| Healing | 1,043 | Unknown source, across Agate and Tita. |
| Deaths | No observed party knockout | Only this HP-setter path was watched. |

The replay is deliberately `PARTIAL`. It does not establish which party member dealt damage, which enemy attacked, the move used, physical versus Arts class, displayed/resolved amounts, or that every combat-result path uses this setter. One setter call may reflect an aggregate change rather than one visible hit. The observed values **must not** be presented as a complete DPS ranking. The meter now proves that a real fight's observed HP changes can flow through Damage, Taken, Healing and Timeline projections, with uncertainty visible rather than silently inferred.

Rebuild the replay from the exact trace and map:

```powershell
python tools/build_hp_set_research_replay.py samples/research/full-hp-path-20260926.jsonl samples/research/command-hp-actor-map-20260926.json samples/research/full-hp-path-20260926.partial.json --start-at 2026-09-26T21:34:27.522-05:00 --end-at 2026-09-26T21:35:33.468-05:00 --outcome Victory
```

To view it without adding it to normal saved history:

```powershell
$env:SORA2_DETAILS_RESEARCH_REPLAY = (Resolve-Path samples/research/full-hp-path-20260926.partial.json).Path
dotnet run --project src/Sora2.Details.Desktop -c Release
```

The relevant .NET checks assert 18 results, partial status, and the three numeric totals. The revised debugger probe passed its synthetic attach/hit/detach check; the game trace detached cleanly. The next capture gate is **action/source attribution**: correlate the HP setter's target pointer with verified command/action context, then identify the actual attacker, move and damage class at the resolved effect. A separate lifecycle gate must find a reliable command-battle start state because `BattleStart` did not fire here. Quick-battle HP setter behavior also needs its own negative control before an automatic adapter can use this path.
