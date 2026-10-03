# Offline action reconciliation, October 2, 2026

## Completed work

`tools/reconcile_action_stream.py` now replays saved raw research into a separate
evidence ledger. It does not attach to the game, modify raw traces, write meter
encounters or turn research candidates into production execution events.

Every input record is embedded unchanged, including unfamiliar hooks, markers,
unresolved descriptors and raw condition payloads. The ledger records its input
SHA-256, exact localized table fingerprint and lookup ranges. Stable candidate
IDs use the input batch and physical record position; raw observation sequence
remains available independently. Replaying unchanged input gives identical IDs
and content. No cross-trace pointers are joined.

Queue pairing requires the supported executable marker, an armed interval,
verified hook RVA, same thread and actor pointer, identical descriptor pointer,
and equality of all inline 0xB0 descriptor bytes. A pending cast survives another
actor's effects. A subsequent store, mismatched resume, sequence gap or capture
marker retains the unresolved observation and ends the affected correlation.
None of those cases becomes an inferred interruption or cancellation.

The first matching dispatch run following a matched resume receives a candidate
action link. This requires identical inline bytes and descriptor pointer on the
same thread. Multiple eligible resumes remain ambiguous. An unrelated dispatch
closes the linking window. Runs require contiguous identical descriptor and
context observations, allowing verified matching condition post-call records
between them. These are candidate runs, not action counts or a verified source
actor join. The original raw records make every link independently reviewable.

Condition-return linkage additionally requires the nonvolatile descriptor,
R13 context and RSI context to match both dispatch contexts. Returned record
identity is checked against its aligned address and bytes inside the observed
collection. Complete, uniquely keyed collections can be compared with their
previous observed snapshot. Added/removed keys and changed record bytes remain
raw differences between snapshots; they are not named stat deltas or evidence
that every difference was caused by the current call.

## Saved-trace replay

| Batch | Raw records preserved | Results |
| --- | ---: | --- |
| `633a0e3489de45bca8ff3cb62e9f67a1` | 160 (154 hits plus 6 markers) | Two matched queue/resume/effect candidates, 12 dispatch runs, all 10 condition returns linked, no sequence-gap issues |
| `6d0faa9c57fe4f2d9e522471ce2ecf8c` | 788 (782 hits plus 6 markers) | Prior Conditions capture preserved; 15 conservative dispatch runs; no invented queue records on this profile |

Derived outputs are `ledger-<batch>.json` beside the original research traces
under `%LOCALAPPDATA%/Sora2 Details/research/action-stream`. Forte and Saint each
have one candidate queue link. Wild Rage II remains separate between Saint's
store and resume. Morale EX has three recipient runs; Dragon Dive has two
45-row runs. None of these callback counts is treated as the number of actions.
The original queue trace hash remains
`759A37FCCCF384BF4BEAE50F93F682DCCA2C9222F87D829645A486C4C7B784E8`.

Wild Rage II returned records with raw keys 27 and 28. Their payloads changed
relative to earlier observations of the same collection, although the key set
remained `[22,27,28]`. In both records the raw word at +0x04 changed from 1 to 3.
That demonstrates why recording application/update payloads matters; the word's
meaning and any resulting stat changes are not assigned yet.

Example replay (from repository root):

```powershell
C:/Python313/python.exe -B tools/reconcile_action_stream.py <raw-trace.jsonl> --output <derived-ledger.json> --skill-pac 'C:/Games/Trails in the Sky 2nd Chapter/pac/steam/table_en.pac'
```

Omit `--skill-pac` to retain raw descriptors without name enrichment. The command
rejects using the raw trace itself as the output. Lookup requires a unique
exact-table match over the documented compared ranges; unknown and ambiguous
descriptors keep their raw bytes and key.

## Next live gate

The current saved data cannot prove a universal, one-observation-per-execution
boundary, or link the queue actor to the effect source through a captured pointer
graph. Offline disassembly identifies +0x68F80 as a shared descriptor/target setup
entry, reached from the immediate route at +0x68F6D and the resume route at
+0x6911E. Its arguments are RCX actor and RDX descriptor. The helper branches on
descriptor +0x20 and actor target fields; it is not yet an execution event.

The new `Setup` profile and bounded inline actor/context/status snapshots are
implemented and tested synthetically. The [next capture packet](ACTION-SETUP-CAPTURE-PACKET-20261002.md)
specifies the live contrast required to validate or reject this lead. No game
attachment occurred during this offline work. Interrupt and stat-change tests
are not required for the next batch.

## Verification

Twelve reconciler checks cover intervening actions, descriptor reuse and byte
mismatch, store replacement, unresolved casts, ambiguous matches, sequence gaps,
unsupported hashes, context mismatch, unknown preservation, exact lookup gates,
condition updates without a key change, and retaining a candidate link through
the newly prepared setup observation. Seven snapshot checks and the
synthetic lifecycle attach/hit/detach check cover the prepared setup inspector.
Standalone bridge checks, launcher syntax, Release solution build, and core
replay/projection/recorder/persistence checks pass. Saved-trace replays validate
this research path; they do not validate live Setup coverage or desktop display.
