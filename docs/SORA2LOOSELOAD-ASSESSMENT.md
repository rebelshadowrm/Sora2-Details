# sora2looseload assessment — 2026-09-27

The [sora2looseload repository](https://github.com/lmaple0/sora2looseload) is useful as a **native loading and signature-verification reference** for this exact game build. Its optional debug log is **not an established combat-event feed**. The existing meter still needs a verified result/action hook, actor and move lookup, command-battle boundaries, and an adapter to the [capture pipe](CAPTURE-PROTOCOL.md).

## Source behavior

At reviewed commit `745cf903bee976b72ad84c200a71e9137d666261`, the loader uses an `xinput1_4.dll` proxy and Microsoft Detours to intercept the game's file check and locale handler, allowing language-specific loose resources. Its optional `DebugLogger` hook is attached only when `[Logging] Enabled=1` or `SORA2LOOSELOAD_LOG=1`. It formats the logger's variadic message and appends `[LOG]` text to `sora2looseload.log`; it does not call its saved original logger function. The loader's own `[MOD]` lines describe file-path checks and hook startup. Logging is off by default and the file is replaced at each game launch. These facts come from the [README](https://github.com/lmaple0/sora2looseload#logging) and [hook implementation](https://github.com/lmaple0/sora2looseload/blob/main/dllmain.cpp).

The logger provides formatted diagnostics, not a structured callback containing source, target, move, resolved amount, HP delta, or critical flag. It is unsuitable as the meter's sole capture source without a separate live demonstration of those fields. The hook's lack of forwarding also makes copying it directly into a combat adapter an unexamined behavior change.

## Exact local target check

The repository's [read-only verifier](https://github.com/lmaple0/sora2looseload/blob/main/tools/verify_target.py) was run against `C:\Games\Trails in the Sky 2nd Chapter\sora_2nd.exe` with `--with-log-hook`. It returned success for the exact local SHA-256 `d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`, x64 machine `0x8664`, and XInput imports at ordinals 2 and 3. Each required pattern matched once:

| Pattern | RVA |
| --- | ---: |
| Initial file check | `0x654640` |
| Debug logger | `0x57C1D0` |
| Locale handler | `0x5B1CC0` |

This is **static signature compatibility**, not a successful DLL load, in-game smoke test, or evidence that the log emits combat results. No `xinput1_4.dll` proxy or `sora2looseload.log` was present in the checked game root; nothing was installed or changed there. Installation would require a full game restart, per the loader's README.

## What the debug logger appears to print

A read-only disassembly of this exact EXE found 65 direct `call` instructions targeting logger RVA `0x57C1D0`. For those direct call sites, their nearby format-string arguments concerned invalid or out-of-range IDs, missing resources, animation errors, and similar diagnostics. None had a combat-result, damage, action, battle lifecycle, or critical-hit format. This supports the inference that the debug logger is unlikely to replace our result hook. It is **not exhaustive**: indirect callers, script-generated messages, and runtime behavior were not ruled out. A live logging trial could further test it, but a restart and DLL installation are not justified by this evidence alone.

One diagnostic says it could not obtain a character 2D image filename and asks to check `t_name` and `t_status`. This was a useful navigation clue: an independent scan of this game's English `t_name.tbl` found direct numeric ID-to-name rows for the four live-verified party IDs. See the [name lookup result](SOURCE-NAMES-AND-CRITS.md). The examined KuroTools `t_name` schemas describe other Falcom games; this table's layout was checked directly against the installed payload. Enemy instance IDs `60050`–`60052` do not occur there, so this does not resolve enemy names or turn the debug logger into a name event.

## Practical integration path

1. Keep the current external WPF meter, encounter store, and version-gated pipe. Do not parse `sora2looseload.log` as a source of damage totals.
2. Use the loader's XInput proxy/Detours pattern and verifier as a reference if a native in-process observer becomes necessary. Check this EXE's hash and unique signatures before attaching anything. A fork or compatible combined proxy would need its own runtime smoke test and must account for any other XInput proxy already installed.
3. Observe the already identified [resolved attack/HP route](ATTRIBUTED-ATTACK-LIVE-RESULT.md) alongside action context and command-battle start/end. Only emit pipe events when source, target, amount, and battle membership reconcile with an independently observed fight; leave move, damage class, and critical status unknown until proven.
4. Use the decoded `t_name` ID rows for the four live-verified party IDs; investigate a direct runtime unit key or table association for enemies. Preserve separate instances for the two same-name Lily Movers.

No live test is needed from the player for this source review. A later native-adapter smoke test would require a planned restart and one controlled command battle.
