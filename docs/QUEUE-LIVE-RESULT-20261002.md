# Queue comparison: live result, October 2, 2026

## Outcome

The raw probe observed Forte and Saint at both the descriptor store and resume
sites. Each pair has the same thread, actor pointer, descriptor pointer and all
0xB0 inline descriptor bytes. Wild Rage II effects occurred between Saint's
store and resume observations. This supplies evidence for retaining one pending
cast across an intervening action instead of counting queue and resume as two
actions. It does not establish a universal execution hook or interruption route.

Morale EX, Wild Rage II and Dragon Dive also reached the effect dispatcher.
They did not appear at the watched queue sites. That is a scoped route contrast,
not proof that no other queue mechanism exists. No more controls are needed for
this batch; further analysis can proceed from the saved trace.

## Capture and preservation

- Batch: `633a0e3489de45bca8ff3cb62e9f67a1`; game PID 13292.
- Executable SHA-256: `D8B2911D1576216BDC22D070550E4F531E105DE7ED2981885849669F4ACF8AAF`.
- Armed: `2026-10-02T12:30:01.200-05:00`.
- Disarmed: `2026-10-02T12:35:01.250-05:00`; detached at `12:35:01.574`.
- Raw trace: `%LOCALAPPDATA%/Sora2 Details/research/action-stream/action-stream-633a0e3489de45bca8ff3cb62e9f67a1.jsonl`.
- Raw SHA-256: `759A37FCCCF384BF4BEAE50F93F682DCCA2C9222F87D829645A486C4C7B784E8`.

The bounded five-minute capture ended without a hit-limit or error marker.
Probe and launcher processes were absent afterward. All 154 hits remain in the
original raw file and are referenced in a separate analysis JSON: 140 effect
dispatches, two stores, two resumes, and ten condition post-call observations.
Unknown keys, selectors and pointers remain preserved. The profile did not run
the encounter bridge or update the meter; this is not desktop UI validation or
a complete encounter capture. Detachment does not establish desktop shutdown.

## Controls and observed order

The player reported Agate guarding with a suspected support proc, then a second
turn to cast Forte on Estelle. An enemy hit Agate before Estelle used Morale EX.
Kevin queued Saint, with its recipient unreported, and Agate's turn intervened.
The player planned Wild Rage, Saint resolution, then Dragon Dive to finish the
pack. Raw continuation observations below corroborate those move descriptors;
victory and the final affected targets were not independently confirmed.

| Local observation time | Route | Descriptor evidence |
| --- | --- | --- |
| 12:31:07.184 | Store, sequence 11 | Forte `0xFFFF008D`, actor `0x1DBF42C0BB0`, proposed pending descriptor |
| 12:31:07.864 | Resume, sequence 12 | Same actor and exact pending Forte descriptor bytes |
| 12:31:08.417 | Effect dispatch | Forte |
| 12:32:22.098 | Effect dispatch | Morale EX `0x000007D1` |
| 12:32:54.575 | Store, sequence 45 | Saint `0xFFFF00C3`, actor `0x1DBF44DD850` |
| 12:33:55.366 | Effect dispatch | Wild Rage II `0x000509C5`, between Saint store and resume |
| 12:33:56.665 | Resume, sequence 58 | Same actor and exact pending Saint descriptor bytes |
| 12:33:57.200 | Effect dispatch | Saint |
| 12:34:09.100 | Effect dispatch | Dragon Dive `0x000509CE` |

These are local observation timestamps, not measured game cast durations;
menus and player pauses can occur between observations. A store snapshot is
before its write instruction. The matching later pending descriptor supports
the relationship. Research queue candidate IDs retain the batch and store
sequence; they are not yet production action IDs. Repeated effect rows represent
dispatch work, not additional player actions: Dragon Dive has 90 such rows.

Names use unique exact-English table matches over descriptor ranges
0x00..0x07, 0x10..0x17 and 0x20..0x8F. Runtime-dependent ranges 0x08..0x0F and
0x18..0x1F are excluded and remain raw. Table payload SHA-256 is
`AE81526BEF7E1DEDC601145961A0786DF48FB1B2C96407D4571E1F3BAE3BFE8A`.
This is research enrichment rather than a general production semantic map.

## Conditions and unresolved semantics

Forte's watched post-call collection contained raw key 27. Morale EX supplied
multiple recipient collections with keys including 27 and 28, plus preexisting
22 in some collections. Wild Rage II's two watched post-call collections both
contained `[22,27,28]`; equal keys do not establish unchanged values or no effect.
Saint's post-call collection contained `[27,22,28,29,30,31,32]`.

These keys are not named stat buffs yet. A post-call observation shows collection
state; attribution of every member to that call requires request and before/after
evidence. This profile does not observe resource setters or verified combat
stats, so actual CP/EP amounts, regeneration and stat deltas remain unresolved.

Unknown descriptors `0xFFFF057F` and `0xEA8B03E8` are retained. A separate table
candidate, Heat Up II `0xFFFF2721`, also reached dispatch. The player's suspected
support proc remains an annotation: this name alone does not prove its owner,
trigger or relationship to guarding.

## Next implementation boundary

The [offline reconciler and replay results](ACTION-STREAM-OFFLINE-RESULT-20261002.md)
now implement the candidate linkage described below and preserve all raw records.
The [next setup capture packet](ACTION-SETUP-CAPTURE-PACKET-20261002.md) targets
the remaining action-boundary and actor-pointer evidence.

Use these matched queue observations to develop a ledger that preserves pending
casts across other actions and associates their later effects without duplicating
actions. Retain unmatched observations and raw keys. Expand and verify coverage
before calling it the authoritative action stream. Explicit cancellation or
interrupt evidence is still required before assigning those outcomes; a cleared
pointer or missing effect is insufficient. Stat and resource projections remain
downstream of that ledger and verified identity mapping.
