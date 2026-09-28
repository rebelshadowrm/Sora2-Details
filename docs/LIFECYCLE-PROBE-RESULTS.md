# First runtime command-battle lifecycle probe

Observed 2026-09-26 on `sora_2nd.exe` SHA-256 `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`, PID 25876, loaded module base `0x7FF6807D0000`. This is the first **runtime** check of four previously static RVA leads. The complete 56-hit trace is [here](../samples/research/lifecycle-20260926.jsonl); reproduce its burst summary with:

```powershell
python tools/summarize_lifecycle_probe.py samples/research/lifecycle-20260926.jsonl
```

The probe attached at 20:50:15 local time and detached at 20:51:45. All hits below occurred on thread 9356. The game process remained running and responsive afterward.

| Candidate | RVA | Runtime hits in this observation | Interpretation limit |
| --- | ---: | --- | --- |
| `btlsys.BattleStart` | `0xB8410` | 35 hits, 20:50:58.367–20:50:58.733 | Correlates with entering command combat, but repeats rapidly; one hit is not one encounter. |
| `btlsys.BattlePreEnd` | `0xBA405` | 0 | Not observed in this battle path. |
| `btlsys.BattleDead` | `0xBCE10` | 2 hits at 20:51:14.270; 1 at 20:51:21.097 | Fired despite **no party knockouts**; it is not a party-death event by itself. It may relate to enemy deaths or another script state, unverified. |
| `btlsys.BattleEnd` | `0xBA659` | 18 hits, 20:51:22.642–20:51:22.832 | Correlates with this victory's end, but repeats rapidly; other outcomes remain untested. |

The player reported a field attack and stun that led into a follow-up command opener, followed by Wild Rage, Final Break on Agate, and Shatter Break on Estelle. The battle ended in a **visible victory**, with **no party knockouts**. Those facts were player-reported, not read from game memory. The probe did not observe a standalone field attack that stayed in field combat, so field exclusion is **not** yet validated. No actor identity, HP result, move, or outcome field was read by this lifecycle probe.

## Quick-battle control capture

Here, **quick battle** means combat resolved in the field without entering the command battle screen. The meter's encounter scope remains command battles only.

A second 90-second capture on the same process and executable hash ran from 21:01:14.282 to 21:02:44.622 local time. The four candidate addresses were armed at 21:01:14.286. The [raw trace](../samples/research/lifecycle-field-only-20260926.jsonl) contains **zero hits**, followed by `disarmed` and `detached`; the game was still responsive afterward. The player confirmed they **missed this window**, so this is an idle-field control, not evidence that the hooks exclude field-only attacks.

A third 180-second capture ran from 21:06:09.119 to 21:09:09.519 local time, with breakpoints armed at 21:06:09.123. During the active window, the player reported engaging and killing a monster. The [raw trace](../samples/research/lifecycle-field-kill-20260926.jsonl) contains **zero hits** and a clean detach; the game remained responsive. Awaiting player confirmation that the monster died entirely in field play, without a command-battle transition. If confirmed, this is one successful negative control for these four candidate paths; it still does not prove every field action is excluded.

A fourth 180-second capture ran from 21:11:17.579 to 21:14:18.007 local time, armed at 21:11:17.584. The player explicitly confirmed making a **quick-battle attack without entering command battle** during the armed window, then staying in the field. The [raw trace](../samples/research/lifecycle-field-only-confirmed-20260926.jsonl) contains **zero hits** on all four candidate paths and a clean detach. The game remained responsive. This is one observed negative control: these addresses did not fire for that quick-battle attack. Combined with the earlier visible victory trace, it supports using these paths to research command-battle boundaries, subject to further start/end and outcome validation.

## Escape and re-entry observation

In a later [action-context trace](../samples/research/action-context-escape-reentry-20260926.jsonl), the player reported using the **Escape command**, returning to the field, re-entering command battle, and then winning. `BattleEnd` fired **once at 21:45:16** around Escape and **18 times at 21:45:39** around the victory. Earlier shorthand that it did not fire on Escape was incorrect; the single hit was easy to miss when examining only bursts. The trace does not expose an outcome value, so hit count alone is not an outcome classifier.

Three enemy status pointers and Agate's pointer were present on both sides of Escape/re-entry. For each, the first observed HP after re-entry equaled its last observed HP before Escape. This is strong evidence that the same field combat state persisted in this case. History may eventually group the two command attempts under one broader fight, while retaining separate command intervals for totals. Automatic grouping still needs a verified shared state/identity marker and a way to exclude any quick-battle effects between attempts.

A separate full-fight [HP-path test](FULL-HP-PATH-LIVE-RESULT.md) recorded **zero `BattleStart` hits** despite a player-confirmed command battle and victory. Therefore `BattleStart` at RVA `0xB8410` is not yet a reliable automatic start gate. The later [attributed attack-path test](ATTRIBUTED-ATTACK-LIVE-RESULT.md) demonstrates a real per-character Damage Done replay, still manually bounded.

`tools/lifecycle_probe.py` checks the target executable hash, sets up to four x64 hardware execution breakpoints, logs hits, clears the breakpoints, and detaches after a bounded interval. It does not patch code or game files, but attaching a debugger temporarily suspends the process. A shutdown race found by repeated synthetic tests was fixed by resuming execution breakpoints with RF and draining queued breakpoint exceptions before detach. `tools/test_lifecycle_probe.py` exercised all four slots and a newly created thread against a disposable synthetic process; 25 repeated runs confirmed that the target remained alive after detach. This tests the probe mechanism, not the meaning of the game's candidate paths.

Next, correlate another visible command-battle start and end against a new trace, ideally an escape or defeat when convenient. A production adapter must collapse repeated hits into observed transitions and reject unsupported executable hashes. Do not emit `EncounterStarted` or `EncounterEnded` from a single raw hit until boundaries and outcomes are validated across more than this one case.
