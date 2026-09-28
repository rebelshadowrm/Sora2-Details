# Installation scan — 2026-09-25

## Scope and method

Read-only inspection of `C:\Games\Trails in the Sky 2nd Chapter`: recursive file listing, executable version metadata and PE header, executable ASCII strings, archive headers/indexes, and selected table payload strings. No executable or archive was modified; no third-party binary was downloaded or run. No matching `sora`, `ed6`, or `trails` process was found by the process-name check at inspection time. No live event capture was attempted.

The workspace `E:\Git\Sora2-Details` was empty at the start. No applicable `AGENTS.md` was found in that directory or its checked parent directories. Python, ripgrep, and dotnet commands are available locally; compiler/SDK suitability has not been validated.

## Confirmed local evidence

| Item | Observation |
| --- | --- |
| Installed files | 81 files; 54,771,044,291 bytes total |
| Executable | `sora_2nd.exe`, 13,464,576 bytes |
| Product/File description | `Trails in the Sky 2nd Chapter` |
| File/Product version | `1.3.2.0` |
| PE architecture | Machine `0x8664`, optional-header magic `0x20b`: x64 PE32+ |
| EXE SHA-256 | `d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf` |
| Resource layout | `pac\steam\*.pac`, with base and localized table/script archives |
| Archive signature | `FPAC` |
| English tables | `table_en.pac`: 10,500,699 bytes, 315 indexed entries |
| English scripts | `script_en.pac`: 81,829,615 bytes, 1,082 indexed entries |
| Candidate combat logs | No obvious combat-log file found in the install tree |

Directory contents and product metadata identify the current remake target. Avoid assuming compatibility with the original Trails in the Sky SC executable or its tooling. The version and SHA identify this local file; they do not certify distribution authenticity or a Steam build ID.

DLL names found as executable strings include `d3d11.dll`, `dxgi.dll`, `XINPUT1_4.dll`, and `steam_api64.dll`. This string scan alone is not an import-table verification or proof of a particular rendering path. A bundled license filename mentioning Unity is likewise insufficient to identify the engine.

The FPAC index layout documented by [FPACker](https://github.com/coinkillerl/FPACker) was sufficient to enumerate both English archives. Filename offsets and payload bounds were checked for their entries. Only selected payloads were read; the entire installation was not extracted or hashed.

## Combat metadata candidates

| Archive entry | Bytes | Observed evidence |
| --- | --- | --- |
| `table_en/t_skill.tbl` | 96,935 | `#TBL` header; `SkillParam`, `SkillPowerIcon`, `SkillGetParam`; readable move names including Aqua Bleed and Teara, descriptions, and animation identifiers |
| `table_en/t_status.tbl` | 546,548 | `#TBL` header; `StatusParam` strings |
| `table_en/t_name.tbl` | 255,068 | Later offline follow-up decoded direct numeric IDs and English names for four live-verified party members; see [name lookup result](SOURCE-NAMES-AND-CRITS.md) |
| `table_en/t_condition_info.tbl` | 8,963 | `#TBL` header; `ConditionInfoTableData`, `ConditionTypeParam`, `OverDriveEffect`; physical/Arts reflection labels |
| `table_en/t_item.tbl` | 472,790 | Indexed entry present; candidate item metadata |
| `table_en/t_text.tbl` | 107,779 | Indexed entry present; candidate labels |
| `script_en/ani/btlcom.dat` | 381,073 | Indexed entry present; candidate shared combat animation/script logic |
| `script_en/battle/btlsys.dat` | 45,874 | Indexed entry present; candidate battle lifecycle script |

Numeric table schemas, enum meanings, actor-to-name links, and runtime skill IDs were not decoded. Readable terminology proves labels exist, not that damage classification can already be extracted reliably. Script payloads were not decompiled.

## Executable navigation leads

The ASCII string scan found the following references, among others:

- `btlsys.BattleInit`, `btlsys.BattleStart`, `btlsys.BattlePreEnd`, `btlsys.BattleEnd`, `btlsys.BattleDead`.
- `btlsys.BattleTurnBegin`, `btlsys.BattleCommandBegin`, `btlsys.BattleTurnEnd`.
- `btlcom.OnAttackHit`, `btlcom.AniBtlDamageTargetsSkip`, `btlcom.AniBtlRegene`, `btlcom.AniBtlAttrAbsorbEffect`.
- `btlcom.OnFieldAttackReflect` and other field-combat references.
- Build-source path strings ending in `battle_chara.cpp`, `battle_condition.cpp`, `battle_manager.cpp`, `battle_status.cpp`, and `battle_turn_state.cpp`.
- A build-machine PDB path ending in `sora_deploy_steam.pdb`. No matching PDB file was present in the install listing.

These are search anchors for disassembly and runtime investigation. They are not confirmed callable exports, available source code, public debug symbols, or event notifications. Their names do not establish when an action actually applies damage.

## External research leads

1. [FPACker](https://github.com/coinkillerl/FPACker) explicitly lists Sky 2nd Chapter and documents its archive structure. Local enumeration independently confirmed the relevant index layout.
2. [sora2looseload](https://github.com/lmaple0/sora2looseload) is a native loose-file-loader project for this title. The directly opened README lists an executable 1.3.2.0 static target and explicitly says that target still needs a fresh in-game smoke test. This supports investigating native integration, not assuming runtime compatibility or combat-event support. Search snippets showed older target information; use the repository itself when implementing. Its [target verifier](https://github.com/lmaple0/sora2looseload/blob/main/tools/verify_target.py) is a useful validation reference, not something executed in this scan.
3. [KuroTools](https://github.com/nnguyen259/KuroTools) supports table/script work for related Falcom games and lists Sky 1st Chapter with partial script compatibility. Treat its table schemas and parsers as research leads; Sky 2nd support was not established here.

## Unresolved questions

- Does the game retain resolved combat events or expose a sufficiently detailed logger? User-data locations outside the install tree were not searched.
- Which runtime structure carries attacker, victim, skill ID, actual HP delta, and damage class together?
- How are repeated hits, skipped animations, status ticks, counters, shields, and instant knockouts represented?
- Can command-battle boundaries and outcomes be identified reliably, including retries and transitions?
- Can capture use a read-only retained result buffer, or is a native observer necessary?
- How well do signatures and schemas survive updates to this executable?

Conclusion: there are concrete metadata and code-navigation leads for a feasibility prototype. Complete combat capture remains unproven.

Follow-up on 2026-09-27: the sora2looseload verifier was run on this exact executable, and its debug logger was assessed separately. See [sora2looseload assessment](SORA2LOOSELOAD-ASSESSMENT.md). This follow-up does not change the read-only scope or results of the original 2026-09-25 installation scan.
