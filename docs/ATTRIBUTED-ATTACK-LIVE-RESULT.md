# First character-attributed live damage meter result

Observed 2026-09-26 on `sora_2nd.exe` SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`, PID 25876, module base `0x7FF6807D0000`. The bounded [raw trace](../samples/research/attack-source-20260926.jsonl) detached cleanly and the game remained responsive. The player confirmed a command-battle **victory**. This test selected the later, controlled command interval from 21:50:49.737 through the victory end burst at 21:52:48.011 local time; an earlier Escape/re-entry and uncertain field activity are excluded.

At RVA `0xE3E55`, immediately before a call into the effect helper, the probe observed a candidate source context in `r12`, a target context in `rsi`, and an amount in `edi`. Reading the contexts' first pointers yielded source and target status instances. In the selected interval, **13 attack-call records paired in order with 13 HP-setter records on the same thread**. Every pair had the same target status pointer. For the nine nonlethal requests, the candidate amount exactly equaled `HP before − requested HP`. The remaining four used a `-1` requested-HP sentinel during lethal or already-zero-HP hits; the setter clamps those to zero. This supports the source/target/amount interpretation on this attack path, while other effect paths remain untested.

The independent control was Agate's player-reported **normal Attack** at 21:52:10.488. The probe recorded Agate's known status pointer as source, a 28,840-max-HP enemy pointer as target, and amount **10,452**. The paired HP setter changed that enemy from **28,840 to 18,388**, also **10,452**. The player saw **“104xx”** on screen; a critical indicator obscured the last two digits. The probe supplied the exact digits the visual effect hid. The move label is player-reported, not read from a game move ID.

The [partial attributed replay](../samples/research/attributed-attack-20260926.partial.json) maps the four party status pointers to the player-confirmed roster and retains two unnamed enemy instances. The [pointer map](../samples/research/attributed-actor-map-20260926.json) is version/session-specific research data, not a stable game schema. The meter's **Damage Done** mode shows effective HP loss:

| Party member | Effective damage |
| --- | ---: |
| Estelle | 32,535 |
| Agate | 20,284 |
| Scherazard | 4,991 |
| Tita | 2,076 |
| **Total** | **59,886** |

The total reconciles exactly to the two observed enemy HP pools, **28,840 + 31,046 = 59,886**. Two later attack results targeted an already-zero-HP enemy and contribute **zero effective damage** to the meter. A separate lethal result contributes only the HP actually remaining, so overkill does not inflate the default totals. The timeline preserves all 13 paired results, including zero-effective results. The controlled Agate Attack is labeled `Normal Attack (player-reported)`; every other move and all damage classes stay unknown. This is a damage **total** meter, not DPS; no validated time base exists.

Rebuild the exact replay:

```powershell
python tools/build_attributed_research_replay.py samples/research/attack-source-20260926.jsonl samples/research/attributed-actor-map-20260926.json samples/research/attributed-attack-20260926.partial.json --start-at 2026-09-26T21:50:49.737-05:00 --end-at 2026-09-26T21:52:48.011-05:00 --outcome Victory --known-move-at 2026-09-26T21:52:10.488-05:00 --known-move 'Normal Attack (player-reported)'
```

To view the replay without adding it to normal history:

```powershell
$env:SORA2_DETAILS_RESEARCH_REPLAY = (Resolve-Path samples/research/attributed-attack-20260926.partial.json).Path
dotnet run --project src/Sora2.Details.Desktop -c Release
```

The window displays `RESEARCH` and `PARTIAL`; drag its encounter line or footer to move it. The .NET checks assert the four character totals, 59,886 aggregate, 13 paired results, two zero-effective hits, and the controlled 10,452 result. The solution builds without warnings and the checks pass.

This is **one real, attributed attack-path example**, not a complete automatic combat log. The selected interval was manually bounded. The game-side adapter still needs a reliable command-battle start and all outcomes, action/move IDs, physical-versus-Arts classification, healing and non-attack effects, dropped-event detection, and a quick-battle negative control for this attack path. Unknown fields remain unknown in the replay. Do not use these pointers or RVAs for another executable hash without revalidation.
