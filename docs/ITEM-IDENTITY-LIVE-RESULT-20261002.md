# Item action identity from the completed recording

Batch `01ce27de69a64798b464f1c5e8c19e5a`, exact executable SHA-256
`d8b2911d1576216bdc22d070550e4f531e105de7ed2981885849669f4acf8aaf`.
The player lacked EP Charge II, so EP Charge I was approved before controls.
Reported order: Estelle used Tear Balm on Agate, then EP Charge I on Estelle.
The player subsequently confirmed the fight was finished. No further player
actions are needed to reconstruct this batch.

## Captured sequence and raw resources

| Observation | Local time (UTC-05) | Actor / move / target | Evidence |
| --- | --- | --- | --- |
| 120 | 17:22:59.834 | Estelle / generated key FFFF057A / Agate | First main handler 68320; five linked dispatch calls |
| 121 | 17:22:59.920 | Estelle / selector 122 / Agate | Inline descriptor and source/target status |
| 122–123 | 17:22:59.921 | Agate HP 6872 → 8822 | Setter 7 requested 8822; next dispatch reads 8822 at same status pointer |
| 248 | 17:23:16.670 | Estelle / generated key FFFF057E / Estelle | First main handler 68320; five linked dispatch calls |
| 249 | 17:23:16.764 | Estelle / selector 124 / Estelle | Inline descriptor and source/target status |
| 250–251 | 17:23:16.765 | Estelle EP 1880 → 2075 | Setter 10 requested +195; next dispatch reads 2075 at same status pointer |
| 465 | 17:23:33.587 | Observed engine interval ended | Exact C5753 write, raw exit argument 1 / Victory candidate |

HP gain 1950 and EP gain 195 are observed status differences, not the static
table values 1500 and 150. Their 30% difference does not identify a modifier or
prove its source. Selector calls are not individual hit/application counts.
Other guards, supports, enemy actions and the normal-attack finish remain saved.

## Native item-to-action construction

The descriptor IDs are generated action keys, not item IDs. Native constructor
`23E760` loads ItemTableData, and `258400` parses its flag string. A table row is
eligible when parsed flags include mask C0000 (B/M), or any of five effect-code
words at item+3C,4C,5C,6C,7C is nonzero. In original file order it emits records
with low-word key `578 + eligible ordinal` and owner FFFF (`23EACA–23EB04`).
Only eligible rows advance the ordinal (`23ED28`); the later item-table sort
does not change generated record order. The two photo rows precede Tear Balm,
so subtracting 578 or 579 from the key cannot produce a general item ID.

Each generated record is B8 bytes: a B0 skill-shaped descriptor plus original
item ID at B0. Native `23EB08–23EBB1` maps item parameters, five effect blocks,
target fields and relocated string pointers into the descriptor. `23EC29` takes
the original ID from item[0], and `23ED21` appends it. Item-use handler `69670`
matches the selected descriptor key over this B8-stride array, reads the
original ID at `69736`, then calls exact item lookup `23EF20` at `69744`.

The fingerprinted offline reconstruction yields 398 generated records. Comparing
the captured B0 bytes over ranges 00:08,10:18,20:90 gives unique matches:
FFFF057A → item ID 1 / row 143 / Tear Balm, and FFFF057E → item ID 5 / row 147 /
EP Charge I. Both independently match the player's controls and captured target
identities. Item payload SHA-256 is
`16a8703a01e02ec9782d2d36dbdf1f3b150ba96982cf141c6a49f301a351abea`.
The original item ID was outside the old B0 snapshot and remains unobserved in
this batch. Labels explicitly retain generated-item candidate provenance.

`item_action_lookup.py` implements the exact constructor fields and eligibility
rules, not numeric coincidences or amount/name matching. The reconciler keeps
generated action key, item ID candidate, row and table hash separate. Any
skill/item namespace ambiguity stays unnamed. Altered parameters, partial bytes
and unknown keys do not gain item names. Raw recording bytes are unchanged.

## Projection failure and completed cleanup

While the raw probe kept recording, the first bridge failed on WinError 5 during
atomic ledger replacement. The last valid 161-record ledger was retained. The
bridge now retries transient PermissionError on the same complete temporary
snapshot and still raises on persistent denial. A real Windows reader denying
delete sharing reproduces the fault and passes the retry regression. Persistent
denial retains the previous ledger without truncating it.

A replacement bridge projected the same uninterrupted raw recording to 465
records while armed; the actual WPF audit verified that prefix. Its PID is saved
in the session recovery manifest. The original launcher still referenced the
failed bridge and therefore reported that real failure on final exit; original
stderr/result records are preserved, not relabelled successful.

After the finished report, manual stop yielded disarmed at 17:28:06.751 and
detached at 17:28:07.077. Original/replacement bridges and launcher all exited;
the replacement stderr is empty. The viewer applied the final 467 records,
10 action candidates, and source hash
`0a71539450ebbc27e2d510577fed4dfbb045f376415b4a056ae1b51e2a6f6e45`.
Its closed audit marker is 17:28:53.190; viewer PID 31132 exited. Game PID 29960
survived. The completed session manifest is archived, current.json removed.

Evidence is under `%LOCALAPPDATA%\Sora2 Details\research\action-stream`, using
the batch ID above. The pre-enrichment ledger is preserved separately. The
enriched ledger retains the same raw hash and 467 observations. Saved WPF checks
verify Tear Balm/EP Charge I labels, source proof, filters, refresh and malformed
update retention. Release build, core checks, 32 reconciliation checks,
22 snapshot/timeline/bridge checks and four item lookup checks pass.

## Direct-ID gate completed

The [follow-up live result](DIRECT-ITEM-ID-LIVE-RESULT-20261002.md) now closes
this gate: Agate used Tear Balm, and independently captured B8 records agree on
native item ID 1. The preparation below describes the change tested there;
another item use is no longer required for this identity gate.

Actor C70 and effect R8 snapshots now conditionally collect B8 companion bytes
for only the generated-item key range and kind 6. Other skills retain B0 reads;
unreadable companions stay null. Interpretation requires equal B0 prefix and
agreement between the native original ID and reconstructed table identity.
Conflicts clear the name. This new companion field requires one live item use;
the finished capture cannot supply memory bytes it never recorded.

Any available healing item, preferably one not used in this batch, is sufficient.
No more EP items are required. Arm the prepared Transcript profile, verify source
proof, have the player use that one item and report actor/name/target, then finish.
Completion authorizes manual stop after inspection, without a keyword or another
approval. Item/profile slots and manual-stop policy otherwise remain unchanged.
