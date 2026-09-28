# Live command-battle HP result (partial)

Observed 2026-09-26 in running `sora_2nd.exe` SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`, PID 25876. The [raw debugger trace](../samples/research/command-result-20260926.jsonl) spans 21:25:10–21:30:10 local time and detached cleanly. The game remained responsive. The probe watched Agate's previously verified current-HP address `0x16C50EE5594` (max HP at `+4`) plus three candidate code paths. An elevated read immediately before this test confirmed **5105/6682**, matching the player's command-menu reading.

The player used Final Break and won the first battle while capture was active. `BattleEnd` fired 16 times at 21:25:46.340–.522. Agate's HP was rewritten afterward without changing (5105→5105). No `BattleCommandBegin` or `EffectHelper` hit occurred in that short remaining part of the fight. Enemy HP and Final Break damage were **not** watched, so no Damage Done amount can be derived from this fight.

The player then entered a second command battle, which ended in a player-confirmed **victory**. `BattleCommandBegin` fired nine times and `BattleEnd` fired 17 times at 21:29:34.745–.939. The monitored HP address yielded these changes:

| Local time | Agate HP | Effective change | Treatment |
| --- | --- | ---: | --- |
| 21:26:34.110 | 5105→6441 | +1336 | Before the first observed command callback, cause unknown; **excluded** from the research replay. |
| 21:26:36.375 | 6441→6378 | −63 | In-battle HP loss; player remembered seeing about 51 damage and possibly another hit. The probe cannot separate visible hits at this write. |
| 21:28:57.121 | 6378→6682 | +304 | In-battle HP gain; source and move unobserved. |
| 21:29:02.495 | 6682→6174 | −508 | In-battle HP loss; source and move unobserved. |
| 21:29:04.125 | 6174→5337 | −837 | In-battle HP loss; source and move unobserved. |
| 21:29:36.104 | 5337→5337 | 0 | Post-result rewrite; excluded. |

This establishes **1,408 observed effective HP lost by Agate** and **304 observed HP gained by Agate** inside the selected command interval. It does **not** establish that these are the whole party's Taken total, which enemies caused them, whether each write represents one visible hit, or any party Damage Done. The trace has no enemy HP watchpoint. The first command callback is a lower-bound start marker, not a validated battle-start transition. The victory label comes from the player; the probe saw the correlated end burst but did not read an outcome enum.

The [partial research replay](../samples/research/command-result-20260926.partial.json) contains only those four changed in-battle HP writes. It marks unknown sources/moves/class, omits the uncertain pre-command gain, and sets `isComplete=false`. Generate it with:

```powershell
python tools/build_hp_research_replay.py samples/research/command-result-20260926.jsonl samples/research/command-result-20260926.partial.json --start-at 2026-09-26T21:26:34.121-05:00 --end-at 2026-09-26T21:29:34.939-05:00 --outcome Victory
```

Run the desktop with `SORA2_DETAILS_RESEARCH_REPLAY` set to that JSON path to view it under the **RESEARCH** label without adding it to normal history. Its Taken mode totals 1,408 under Other / unknown source; Healing totals 304 under Unknown source; Damage Done has no rows. The timeline shows each observed HP transition. The .NET checks independently assert those totals and the partial flag.

Static disassembly places the changed HP write at RVA `0xF8EC4` (`mov dword ptr [rsi+0xC], eax`), with the debugger stopping at the next instruction `0xF8EC7`. The containing function begins at RVA `0xF8DB0`, receives a status pointer in `rcx`, a property code in `edx`, and a proposed value in `r8d`; this is a **code hypothesis** based on disassembly, not a verified actor/result contract. The first probe accidentally requested only control/debug context, so its logged integer registers are zero and cannot attribute these writes. The probe now requests integer context too, and synthetic tests pass. The next live probe watches the HP-specific branch at RVA `0xF8EB3` to observe status pointers, before/max HP and proposed values for more than Agate. Those fields must be checked against visible actor HP before using them as meter events. Source, move, and damage class remain separate research gates.

Quick-battle numbers are a later concern. A prior confirmed quick-battle attack produced zero hits on the lifecycle paths, but the HP setter has not yet been checked against quick-battle effects. Do not turn setter hits into command encounters without a verified battle-state gate.
