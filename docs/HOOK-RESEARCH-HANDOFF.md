# Combat hook research handoff

Prepared 2026-09-25. Scope: **command battles only** in the Windows remake of *Trails in the Sky 2nd Chapter*. This began as a static, read-only map. Later bounded runtime observations are documented in the [lifecycle probe results](LIFECYCLE-PROBE-RESULTS.md), [all-actor HP result](FULL-HP-PATH-LIVE-RESULT.md), and [attributed attack result](ATTRIBUTED-ATTACK-LIVE-RESULT.md). They prove one real damage path and a partial research meter replay; they are **not** a complete automatic capture adapter.

## Read this first

The static starting points are native code references to battle lifecycle and turn script names. Later live tests verified one resolved attack route: at RVA `0xE3E55`, candidate source and target context pointers and an amount paired with the HP setter at RVA `0xF8EB3` for 13 results in one controlled command interval. A player-reported Agate normal Attack produced an independently matching 10,452 HP loss. See [the attributed result](ATTRIBUTED-ATTACK-LIVE-RESULT.md) for evidence and limits. The route does not yet cover every effect, identify move IDs or damage class, or provide reliable automatic encounter boundaries.
The [source-name and critical-hit gate](SOURCE-NAMES-AND-CRITS.md) records the current evidence and the controlled comparisons needed to decode a live actor ID and a per-result critical flag.
The [2026-09-27 boundary/support probe](LIVE-LOG-GATE-20260927.md) observed two command entries, a repeated victory end callback, and no watched boundary callbacks during a field-only hit. The later [action-context probe](ACTION-ID-PROBE-20260927.md) paired 19 attack results to HP writes across a player-confirmed victory and produced a partial replay; it did not identify a live move ID or complete support/status outcomes. These newer observations supersede the original next-step ordering below where they overlap.
The [English table linkage audit](TABLE-LINKAGE-AUDIT.md) decodes this build's static character/status, monster-setting/status, owner/skill, and item-ID relationships. It does not identify a live action ID or direct enemy unit-key pointer.
The [sora2looseload assessment](SORA2LOOSELOAD-ASSESSMENT.md) verifies its three signatures on this EXE and explains why its optional diagnostic logger is not yet a combat-event source. Its XInput/Detours design is a possible reference for a future native observer.

The next agent should build on the verified attack/HP pairing: trace action/move IDs and battle state/outcome, then check healing, status effects, knockouts, and quick-battle exclusion for the attack route. The meter and replay projections already exist in `src/Sora2.Details.Core`; do not redesign the UI to compensate for uncertain capture data.

## Exact build fingerprint

| Property | Observed value |
| --- | --- |
| Target | `C:\Games\Trails in the Sky 2nd Chapter\sora_2nd.exe` |
| Product/file version | `1.3.2.0` |
| SHA-256 | `d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf` |
| File size | 13,464,576 bytes |
| PE machine | AMD64 (`0x8664`) |
| Preferred image base | `0x140000000` |
| Entry point RVA | `0x7c9d8c` |
| PE timestamp field | `0x6aace513` (identity field only; no release-date inference) |
| `.text` | RVA `0x1000`, virtual size `0x8b900e` |
| `.rdata` | RVA `0x8bb000`, virtual size `0x3366f0` |
| Runtime function entries | 27,199 x64 exception/unwind entries |
| CodeView PDB ID | GUID `7ab37f1d-82ea-43a5-8d0f-85114e93be98`, age `1` |
| Embedded PDB path | `d:\JenkinsRemoteFS\workspace\sora_sc_steam\bin\sora_deploy_steam.pdb` |

Every address below is an **RVA**. At runtime use `loaded sora_2nd.exe module base + RVA`; the preferred image base is not guaranteed because of ASLR. Check the full SHA-256 before applying any build-specific probe or signature. The embedded PDB path identifies the build's symbol file, but no matching PDB was present in the game installation scan.

The executable has 14 named exports, all `ffx...` graphics/FSR functions. It has no named combat export. Imports include `XINPUT1_4.dll` ordinals 2 and 3, which is relevant to the existing [sora2looseload](https://github.com/lmaple0/sora2looseload) integration research; it is not an existing combat hook.

## Reproducible static scan

`tools/static_hook_scan.py` enumerates candidate ASCII strings, finds direct x64 RIP-relative `lea` references in `.text`, verifies their instruction alignment with Capstone, and reports the containing x64 unwind range. It reads the EXE only. Dependencies are isolated locally by the first command and ignored by `.gitignore`:

```powershell
python -m pip install --target .research-deps pefile capstone
python tools/static_hook_scan.py 'C:\Games\Trails in the Sky 2nd Chapter\sora_2nd.exe'
```

The scan was run successfully against the hash above. `pefile` 2024.8.26 and Capstone 5.0.9 were used. An unwind range is a binary function-boundary clue, not proof of a source-level function name. Disassembly, calling convention, object layout, and runtime behavior still require validation.

## Candidate code map

`String` is the address of a name used by the code. `Reference` is the `lea` instruction that loads it. `Range` is the enclosing unwind entry. The names below label **references**, not exported/native functions.

| Lead | String RVA | Reference RVA | Enclosing range | Suggested runtime question |
| --- | ---: | ---: | ---: | --- |
| `btlsys.BattleInit` | `0xaead90` | `0xc43bc` | `0xc2750`–`0xc4c29` | Does this mark command-battle setup or repeat within a fight? |
| `btlsys.BattleStart` | `0xaeae08` | `0xb89de` | `0xb8410`–`0xb8e70` | Is this the command encounter's reliable start boundary? |
| `btlsys.BattlePreEnd` | `0xaeadb8` | `0xba489` | `0xba405`–`0xba4b2` | Does it precede victory, defeat, escape, and retry? |
| `btlsys.BattleEnd` | `0xaeae58` | `0xbaa22` | `0xba659`–`0xbab48` | Does it fire once with a usable outcome? |
| `btlsys.BattleDead` | `0xaeae30` | `0xbce36` | `0xbce10`–`0xbd04e` | What “dead” state does this represent? Never assume party knockout from the name. |
| `btlsys.BattleTurnBegin` | `0xaeca08` | `0x1172cb` | `0x1172c4`–`0x117300` | Does it identify an action/turn sequence? |
| `btlsys.BattleCommandBegin` | `0xaeca30` | `0x117664` | `0x1175b8`–`0x117693` | Does it carry the acting character and chosen move? |
| `btlsys.BattleTurnEnd` | `0xaeca68` | `0x1184f4` | `0x1184d4`–`0x118526` | Can it close an action group after all effects? |
| `BattleCheckResult` | `0xaecaa0` | `0x1181f3` | `0x1181c0`–`0x118233` | Does it expose battle outcome or only request a script check? |
| `btlcom.OnAttackHit` | `0xaeb968` | `0xe332b` | `0xe2b60`–`0xe452c` | What does this script callback observe; is HP already changed? |
| `btlcom.AniBtlDamageTargetsSkip` | `0xaec268` | `0xf829d` | `0xf8272`–`0xf8377` | Is it only an animation-skip route? Do not count this as a hit by name. |
| `btlcom.AniBtlRegene` | `0xae98d8` | `0x82075` | `0x81d70`–`0x822c6` | Which resource changes, and can the original source be traced? |
| `btlcom.AniBtlAttrAbsorbEffect` | `0xae9978` | `0x83e19` | `0x83495`–`0x840a3` | Does it represent HP absorption, shield, or only presentation? |
| `btlcom.OnFieldAttackReflect` | `0xafdac8` | `0x220682` | `0x220654`–`0x220bcb` | Negative control: must not enter a command-battle encounter. |

### What the disassembly actually establishes

- At `0xb89de`, `btlsys.BattleStart` is loaded into `r8`; the enclosing path calls `0x4cc190` at `0xb89fa`. `BattlePreEnd` and `BattleEnd` use the same shared call at `0xba4a5` and `0xbaa40` respectively. Turn begin/command begin/end also reach that shared call. This is strong evidence for a common script invocation path, **not** proof that the string-load instruction is the ideal hook point.
- `0x4cc190` has unwind range `0x4cc190`–`0x4cc2b1`. Its early instructions pass the name through to `0x4cc9a0` (`call` at `0x4cc1e8`). `0x4cc9a0` has range `0x4cc9a0`–`0x4ccd7f`; it appears to resolve a script name. A general probe here will see many unrelated calls and should filter by name and command-battle state.
- At `0xe332b`, `btlcom.OnAttackHit` is loaded into `r15` and supplied as `rdx` to `0x4cc9a0` at `0xe3338`. The enclosing function is large (6,604 bytes) and may perform more than one logical step. The name is a **lookup key** in this observed path.
- `btlsys.BattleDead` is loaded near the start of `0xbce10`; the code then reads an object from `[rdx+0x328]` and calls the shared lookup path. The meaning of the event and `rdx` object is unverified.
- `BattleCheckResult` at `0x1181f3` is followed by a call to `0xce620` at `0x11820f`. The `0xce620` range is `0xce620`–`0xce704` and is also called at turn-related sites. Its return and side effects require runtime study before using it for outcome detection.
- The short unwind range beginning at `0xba405` starts with an address load/call rather than an obvious standalone prologue. Treat unwind ranges as navigation coordinates; assess safe interception points after disassembling full control flow.

### Effect/resource path worth probing, with low confidence

`0xe4530`–`0xe4617` is a helper reached from the regeneration path (`0x82070`, `0x82095`, `0x82142`, `0x821df`), other effect paths (`0xb264e`, `0xb2846`), and three nearby action-result paths (`0x115579`, `0x1155b7`, `0x1155f5`). Its first four arguments appear in Windows x64 registers `rcx`, `edx`, `r8d`, `r9b`; the code branches on `edx` values `1`, `3`, `4`, `5`, and `6`. Values `1`/`3` negate the amount before calls, while `4` passes a positive amount into `0xe4a60`–`0xe4dda`; values `5`/`6` use `0xe4de0`/`0xe4ed0`.

This shows a common numeric effect route, **not** what resource it changes. It may include HP, EP, CP, or other state. Do not label it a damage hook or treat `edx` as a known enum without a live before/after comparison. If a watched HP value leads here, record the caller stack and object identity; if not, discard it as a damage candidate. Its optional later call at `0xe45ee` into `0xe8a00` also needs interpretation.

## Resource/metadata leads

The game resources are indexed, uncompressed FPAC archives. The following entries were located without modifying or extracting the game; `data offset` is within its PAC file. Hashes identify the exact embedded payloads scanned.

| PAC entry | Data offset | Bytes | Payload SHA-256 | Use |
| --- | ---: | ---: | --- | --- |
| `table_en.pac`: `table_en/t_skill.tbl` | `0x6300f8` | 96,935 | `ae81526bef7e1dedc601145961a0786df48fb1b2c96407d4571e1f3bae3bfe8a` | Candidate skill IDs, names, category/class metadata |
| `table_en.pac`: `table_en/t_status.tbl` | `0x647b9f` | 546,548 | `71c3f47d5a2393d5efac262bd4db1da2283bef55dbb85169d54a118c213a0822` | Candidate actor/status metadata |
| `table_en.pac`: `table_en/t_name.tbl` | `0x35bbd0` | 255,068 | `6101d18a87112e351c2ba1009933cc77b660630a0497c33d9119a81a9916c548` | Direct ID/name/status-key rows for four live-verified party actors; see [lookup result](SOURCE-NAMES-AND-CRITS.md) |
| `table_en.pac`: `table_en/t_mon_mp0000.tbl` | `0x286feb` | 62,457 | `0d00dbadefbb5004d56613e277b86825f7efaa109ea8768c8d7679a9a59cdf1e` | Monster-setting rows carrying unit keys that join to `t_status` |
| `table_en.pac`: `table_en/t_item.tbl` | `0x1a7cd4` | 472,790 | `16a8703a01e02ec9782d2d36dbdf1f3b150ba96982cf141c6a49f301a351abea` | Item IDs, names, and candidate effect fields |
| `table_en.pac`: `table_en/t_condition_info.tbl` | `0x13f659` | 8,963 | `89d228d22acdb8bf3f064e4e0f921d29ca97d67dae17794ca457d8987639c96bb5908289` | Includes readable physical/Arts reflection labels |
| `script_en.pac`: `script_en/battle/btlsys.dat` | `0x229ec38` | 45,874 | `41fb7accc36f81b2b39fbdc9dde8d8cd793b776c18de13360d3f1f9fa6cccb04` | Battle script investigation |
| `script_en.pac`: `script_en/ani/btlcom.dat` | `0x288559` | 381,073 | `6b6c41cca0b7c392347a4092092214de8a15fb146869dd1c7c041988b9318089` | Combat callback/script investigation |

The tables start with `#TBL`; the scripts above start with `#scp`. `t_skill.tbl` contains readable names and descriptions, but its numeric schema and runtime ID mapping were **not decoded** in this scan. A skill name or animation name alone does not establish physical versus Arts damage. See [the broader installation scan](INSTALLATION-SCAN.md) for additional archive entries and tool references. Do not use data from the original SC game as if it were the remake's runtime schema.

Follow-up on 2026-09-27: [table linkage research](TABLE-LINKAGE-AUDIT.md) decoded `SkillParam` packed owner/skill IDs and the item's numeric ID field statically. The live action-to-ID mapping and damage class remain unverified; the preceding paragraph describes the original 2026-09-25 scan.

## Runtime verification sequence for the next agent

1. **Record the build identity and environment.** Recheck EXE SHA-256. Note existing proxy DLLs/mods and the loaded module base. Use read-only debugger observation first; no game files need to be changed for this gate.
2. **Confirm command-battle boundaries.** Observe `module+0xb8410`, `+0xba405`, `+0xba659`, `+0xbce10`, and `+0x1181c0` during one normal victory, then escape/defeat/retry if accessible. Log count, order, thread, and relevant object pointers. Confirm field combat does not create an encounter.
3. **Confirm action context.** Observe `module+0x1175b8` and `+0x1172c4`/`+0x1184d4`; correlate actor IDs and command/skill IDs against a manually noted turn. Do not use turn callbacks as damage results.
4. **Find the resolved HP write.** In a reproducible fight, locate a party member's current HP in memory, verify it across two changes, then watch writes during one enemy physical hit, one Art, one heal, and one lethal hit. Record the native call stack, before/after HP, attacker/target pointers, action/skill ID, and any damage-class flag at the write or its caller. Repeat for enemy HP. Distinguish resolved amount from effective HP delta/overkill.
5. **Evaluate candidate effect paths.** Compare the HP-write stack with `module+0xe2b60` and `module+0xe4530`. A hit callback that fires without a matching HP write is presentation-only or incomplete. A shared numeric helper without source/skill context needs a parent action correlation mechanism.
6. **Test edge cases before choosing a hook.** Multi-hit/AoE, miss/zero damage, regeneration, absorption/reflect, counter, KO/revival, animation skip/accelerate, and same-name enemies. Capture each target result once. Record what remains unknown rather than inferring from graphics.
7. **Produce a small attributed raw recording.** For each resolved effect, preserve event sequence, encounter/action IDs, source and target instance IDs, move ID, event kind, observed/resolved/effective amount, HP before/after, class and provenance. Compare every recorded result with manually noted actions and HP transitions. Mark gaps and partial encounters.

Successful exit evidence is a **single command battle replay with exact actor/target attribution and reconciled HP deltas**, plus a field availability table for physical/Arts class, healing, KO, and boundary outcomes. If that cannot be achieved, keep the UI in sample mode and report which data is unavailable. Do not promote the static RVAs here into a versioned capture adapter solely because a breakpoint fires.

## Integration seam and current limitations

`src/Sora2.Details.Core/CombatModels.cs` defines `ICombatCaptureSource` and lifecycle messages (`EncounterStarted`, `EffectObserved`, `EncounterEnded`). The current WPF app has a capture pipe, encounter assembler, durable store and projections. It can also open the player-verified but partial [attributed research replay](../samples/research/attributed-attack-20260926.partial.json) with `SORA2_DETAILS_RESEARCH_REPLAY`; that replay is deliberately separate from normal saved history. No game adapter emits complete automatic messages yet.

Quick battle (field combat) is outside the current meter scope. Start a command encounter with an HP/status baseline and include only effects observed after a verified command-battle start. Preserve unknown source/class and any dropped event indicators in the eventual adapter. `CombatEvent` now separates resolved and effective amount, but per-field evidence provenance and monotonic capture time remain future work.

## Scan boundary

The original 2026-09-25 static scan used the installed executable and PACs read-only; it did not launch the game, attach a debugger, or resolve a real HP address. No `sora_2nd` process was running during that scan. Later bounded runtime probes are documented above; they used read-only inspection and hardware breakpoints without modifying game files. A scoped check of common user-data directories found no combat log for this title; an empty `AppData\Roaming\FALCOM` directory existed.
