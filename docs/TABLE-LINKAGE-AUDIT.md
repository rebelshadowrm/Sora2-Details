# English table linkage audit — 2026-09-27

Read-only audit of `C:\Games\Trails in the Sky 2nd Chapter\pac\steam\table_en.pac` on the exact game EXE build recorded in the [hook handoff](HOOK-RESEARCH-HANDOFF.md). The four extractors below check SHA-256 of their embedded table payloads before trusting offsets. This maps **static metadata relationships**, not a live action/monster lookup API.

| Table | Indexed payload | Rows | Static key observed |
| --- | --- | ---: | --- |
| `t_name.tbl` | `0x35BBD0`, 255,068 bytes, SHA-256 `6101d18a87112e351c2ba1009933cc77b660630a0497c33d9119a81a9916c548` | 1,583 | Numeric character ID → display name and status unit key |
| `t_status.tbl` | `0x647B9F`, 546,548 bytes, SHA-256 `71c3f47d5a2393d5efac262bd4db1da2283bef55dbb85169d54a118c213a0822` | 503 | Unique unit key → name and base/scaling stats |
| `t_mon_mp0000.tbl` | `0x286FEB`, 62,457 bytes, SHA-256 `0d00dbadefbb5004d56613e277b86825f7efaa109ea8768c8d7679a9a59cdf1e` | 252 | Monster-setting row → unit key; many rows share a key |
| `t_skill.tbl` | `0x6300F8`, 96,935 bytes, SHA-256 `ae81526bef7e1dedc601145961a0786df48fb1b2c96407d4571e1f3bae3bfe8a` | 415 `SkillParam` | Packed owner/skill ID → move name, description, animation |
| `t_item.tbl` | `0x1A7CD4`, 472,790 bytes, SHA-256 `16a8703a01e02ec9782d2d36dbdf1f3b150ba96982cf141c6a49f301a351abea` | 1,382 `ItemTableData` | Unique item ID → name, description, animation, candidate effect fields |

## Actor and monster links

The `t_name` rows contain separate face-model and character-model keys at row offsets `0x18` and `0x20`. Estelle's `chr5000_face` joins to a `.mdl` face model; her `chr5000` character-model key joins by numeric suffix to `at_c5000.dds` in `image.pac`. The latter is a 256×128 AT turn-bar face strip with a usable 128×128 central portrait. The same exact-build join resolves Estelle, Joshua, Scherazard, Olivier, Kloe, Agate, Tita, Zin, Anelace, Kevin, and Josette. [The asset extractor](../tools/extract_meter_icons.py) checks the English name-table hash, image archive index hash, and each portrait payload hash before cropping. These are static asset joins; they do not establish runtime actor identity. Julia and Mueller have no verified rows in this English table and retain letter tiles.

The four **live-observed party status IDs** `0`, `2`, `5`, and `6` exactly match unique numeric rows in `t_name`: Estelle → `chr5000p`, Scherazard → `chr5002p`, Agate → `chr0005p`, Tita → `chr5006p`. Those four unit keys also exist with the same names in `t_status`. This is a direct table chain for these four party actors, stronger than the earlier `t_status` row-position inference. It still requires reading the live status ID for each current actor; a name table does not identify a pointer by itself. See the [live name result](SOURCE-NAMES-AND-CRITS.md).

All 1,570 nonempty status-key references in `t_name` resolve to `t_status`, but they cover only **58 distinct keys**. The generic `npc` status key accounts for 1,339 of those rows. Thus `t_name` is broad as a character-name table but cannot provide a distinct combat stat row for every named character. Numeric ID `65535` is reused 404 times for variants/costumes, and ID `108` appears twice. [name_table_index.py](../tools/name_table_index.py) rejects duplicate IDs in its unique-ID lookup.

`t_mon_mp0000` has 252 setting rows using 36 distinct unit keys; **all 252** keys resolve in `t_status`. Rows `41` and `82` use `mon5014_c02` / Emeronecider. Twenty-two rows use `mon5003` / Lily Mover, including row `51`. The duplicates mean a setting row or unit key is not a unique live enemy. The observed enemy status IDs `60050`–`60052` are instance IDs and do not equal those row numbers or appear in `t_name`. A future capture could seek a unit-key reference in the live monster setting/actor graph; this table proves the metadata join exists, not that we have found that runtime pointer. Until then the [unique stat-signature fallback](SOURCE-NAMES-AND-CRITS.md) remains provisional.

## Move and item links

For meter icons, `SkillParam` word `rawParam10` partitions exact English rows into shared categories: `0x1` Attack, `0x2` Craft, `0x3` S-Craft, and `0x104` through `0x704` for Earth, Water, Fire, Wind, Time, Space, and Mirage Arts. `0x9` continuation rows share the same packed ID and Craft name as their `0x2` row; the icon map uses Craft for both. Unknown or conflicting IDs receive no icon. This field selects a visual category only, not damage type. The `SkillPowerIcon` section, despite its name, maps thresholds 80â€“350 to power-rank letters Eâ€“SS rather than mapping individual moves to picture files. The game image archive's validated `icons.dds`, `btl001.dds`, and `btl002.dds` contain the corresponding element and battle-category symbols. [The icon map generator](../tools/build_skill_icon_map.py) emits 270 unambiguous packed-ID categories, and [the extractor](../tools/extract_meter_icons.py) writes cropped symbols to LocalAppData from this exact archive.

The `SkillParam` rows are 176 bytes each. A 32-bit value at row start splits into a high 16-bit owner ID and low 16-bit skill ID. For 15 owner IDs, including the eight main party IDs `0`–`7`, the high half joins to a unique `t_name` ID. The pattern is supported by separate owner-specific Normal Attack rows. It is an **interpretation of static table fields**; no live action field has yet been shown to carry this packed value.

| Static move row | Packed ID | Owner / skill ID | Name-table owner |
| --- | ---: | --- | --- |
| Final Break | `0x000509CC` | `5` / `2508` | Agate |
| Shatter Break | `0x000007D5` | `0` / `2005` | Estelle |
| Zodiac | `0xFFFF00C8` | `65535` / `200` | Shared marker, no unique actor |
| Agate Normal Attack | `0x0005003E` | `5` / `62` | Agate |

The table has 415 rows but 408 distinct packed IDs. Seven IDs occur twice, often as a main move row plus an indented continuation row. A packed ID alone is therefore not always a unique *row* selector. A low 16-bit skill ID alone is weaker: `62` is shared by many owner-specific Normal Attack rows. A production lookup should keep all candidate rows and resolve only when the game provides enough action context. The animation string (for example `AniBtlSCraft00`) and static description help validate a move name but do **not** establish whether a resulting hit is physical, Arts, critical, or even damaging.

`ItemTableData` uses a unique 32-bit item ID. Tear Balm is item ID `1`, row `143`, with candidate effect code `122` and candidate value **1,500** at row offset `0x40`. Teara Balm and Tearal Balm share code `122` with values 3,000 and 6,000. The Tear Balm value agrees with the player's earlier 1,500 displayed heal; the effective HP gain was only 81 because Agate was near full HP. This agreement is useful validation, not proof that every item or modifier uses that field as the displayed amount. The live item ID and effect type have not been captured.

### Damage-class field lead from a same-actor comparison

The exact archive contains Estelle's Shatter Break (`0x000007d5`), True Comet (`0x000007d7`), and the shared Lightning Art (`0xffff0099`). Their `SkillParam` rows contain more numeric fields than the packed ID and strings. The raw 32-bit words at offsets `0x10`, `0x20`, and `0x30` are `0x2/0x126/0xe` for Shatter Break, `0x2/0x1124/0xf` for True Comet, and `0x404/0x116/0xf` for Lightning. These are **uninterpreted row words**, not established damage-class codes. `0x10` matches for both Crafts but differs for the Art; `0x30` matches for the two Arts-damage examples but may encode target geometry or another property. Other Craft rows share some values across move families. A table-only rule would therefore be premature.

A full named-row scan strengthens offset `0x30` as a **candidate effect-kind code**: all 40 named offensive rows whose animation begins `btlmagic.` have `0xF`, while non-damaging Arts such as Crest, Clock Up EX, and Tear have different values. Twenty-two named non-`btlmagic.` rows also have `0xF`, including True Comet, Sylphen Whip, and several other Crafts. Shatter Break has `0xE`, ordinary Attack `0xC`, and some other Crafts `0xD` or `0x11`. This cross-family pattern is compatible with `0xF` meaning an Arts-damage effect, but animation grouping and three player reports are insufficient to prove it; some Craft damage types have not been independently checked. `tools/skill_table_index.py` now exposes these words as `rawParam10/20/30` so a verified live skill ID can be joined without re-parsing the archive.

In the initial live trace, all three moves produced at least one `0x52000` result. A saved pointer at result-frame offset `0x70` (the result function's entry `r8`) was constant across True Comet's three target results and different for the other two moves. Disassembly at `0xE343B` reads a 32-bit word from that object's offset `+8` while building the result flags. That led to the bounded `--inspect-effect-descriptor` option, which saves 256 bytes of this object. The first session could not gain that snapshot retroactively; the restarted 3:40 PM capture below did. Do not attach table labels to hits based only on descriptor address or raw result flag.

The expanded capture at 3:42 PM **did** establish the direct join: descriptor offset zero held packed IDs `0x000007D7` and `0x000007D5`, and offsets `0x10`, `0x20`, `0x30` matched the corresponding exact English rows. The player independently confirmed True Comet then Shatter Break. The live bridge now requires this four-field match before naming a hit; duplicate or missing matches remain unnamed. It provisionally projects `rawParam30` values `0xC`/`0xE` as Physical and `0xF` as Arts with provenance. This is a result lookup, not yet an executed-action stream for buffs, misses, or canceled moves.

An enemy hit at 3:46:53 had raw descriptor ID `0xEA7E03E8`: the high half `0xEA7E` equals the live enemy instance ID `60030`, and the low half is `1000`. No exact `t_skill` row matches, so the bridge preserves the raw ID/code but no move name. Enemy move metadata may reside in another table or monster setting; investigate that link independently rather than forcing the ID through party skill rows.

The exact English `script_en.pac` (SHA-256 `6ee144495df231a17803b8e61fb68060f53924ca9c33b463280f49873682b286`) contains 316 `script_en/ai/ai_mon*.dat` files. Their `#scp` `SkillTable` data carries tagged low skill IDs and name pointers. `tools/enemy_ai_skill_index.py` hash-checks this archive, verifies FPAC payload bounds, and extracts candidate ID/name lists. For the three exact stat-signature candidates of runtime enemy `60030`, low ID `1000` maps to **Snow Breath** in `mon5036`/Giant Foot, **Fate Saber** in `mon5031`/Fate Spinner, or **Force of Nature** in `mon5023`/Wisdom. Because those three share the same six-stat signature, the bridge keeps that enemy unnamed; the player did not see its name. The code requires a **unique** unit-key match and a **unique** AI-script ID/name match before displaying an enemy move, prefixed `?` to mark the provisional stat-signature provenance. Duplicate IDs with different names remain unresolved.

A later live Millipede Ball uniquely matched `mon5029`. Its raw enemy IDs `0xEA7703E8` and `0xEA7703ED` have low IDs `1000` and `1005`; the exact AI script maps both to **Millipede Odor**. The live bridge replay labeled those hits `? Millipede Odor` and preserved both raw IDs. The two variants carried descriptor effect codes `0xC` and `0xF`, which the bridge provisionally projects as Physical and Arts respectively. This is an automatic archive join, not a player-verified enemy move-name reading or proof that every enemy script follows the same layout. The separate actor stat-signature ambiguity and action-completeness gates remain.

## Capture implications

1. For the four verified party IDs, read live status ID → `t_name` name/unit key → `t_status` metadata; keep the status pointer as the current actor instance.
2. For enemies, look for a live unit key or monster-setting reference that joins to `t_status`. Do not translate runtime IDs `60050`–`60052` directly into table rows, and do not merge two Lily Movers because their keys or names match.
3. For moves, capture a live packed skill ID (or owner plus skill ID), compare with an independently reported action, and handle seven duplicate packed IDs. Keep action category and damage class unknown until the result path proves them.
4. For items, capture a live item ID and separate the table's candidate value from both the actual resolved effect and the effective HP delta.

Reproduce the key lookups without starting the game:

```powershell
$pac = 'C:\Games\Trails in the Sky 2nd Chapter\pac\steam\table_en.pac'
python tools/name_table_index.py $pac 0 2 5 6 60050
python tools/status_name_index.py $pac mon5014_c02 mon5003
python tools/monster_setting_index.py $pac Emeronecider 'Lily Mover'
python tools/skill_table_index.py $pac 'Final Break' 'Shatter Break' Zodiac
python tools/item_table_index.py $pac 'Tear Balm'
python tools/check_table_linkage.py $pac
```
